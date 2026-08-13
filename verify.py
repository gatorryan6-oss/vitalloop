"""
verify.py — smoke test: proves the app actually runs and responds ON THIS MACHINE.

A milestone is not done until this passes. It answers one question: if the
human double-clicks run.bat right now, do they see a working app?

How it works, in plain English:
 1. If the app is already running at URL, only test it in place when that
    server can be PROVEN fresh — it must have started after the last edit to
    any file the app serves (SERVED_SOURCES). A server holding pre-edit code
    would hand back a PASS for code that is not on disk any more, which is
    the worst kind of green. Can't prove it? Refuse and say so; `--restart`
    kills the stale server and runs a fresh one in one step.
 2. Otherwise, start it with SERVER_COMMAND, wait for it to come up, test it,
    then shut it down.
 3. PASS  -> prints PASS, exit code 0.
    FAIL  -> prints the reason to stderr, exit code 2.
    (Exit 2 is what makes a Claude Code Stop hook treat this as blocking:
    Claude Code reads the stderr message and keeps working instead of stopping.)

Until the web app is built (milestone M2), APP_FILE (app.py) does not exist
yet, so this test PASSES VACUOUSLY — there is genuinely nothing to serve. That
is by design, not a failure. From M2 on it becomes a real end-to-end check.

Claude Code: update MUST_CONTAIN as milestones add visible features. The
identity marker MUST_CONTAIN[0] = "Vital Loop" must appear in this app's
pages and no other project's — never leave it empty. Stdlib only, no installs.
"""

import argparse
import glob
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Print ASCII or force UTF-8 stdout, so a console with a legacy code page can
# never turn a real failure message into a UnicodeEncodeError. Carried INLINE
# because verify.py is standing-kit material: it must survive being copied
# into a repo that has none of this project's packages.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

# ---------------- CONFIG (edit per project) ----------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_PY = os.path.join(_HERE, ".venv", "Scripts", "python.exe")
PYTHON = _VENV_PY if os.path.exists(_VENV_PY) else sys.executable

PORT = 5083                                    # MUST equal the port in run.bat
                                               # (5000/5050/5055/5057/5077/5078/
                                               # 5079/5080/5081/5082 and 8000/
                                               # 8501/8503/8504 belong to other
                                               # projects on this machine)
SERVER_COMMAND = [PYTHON, "-m", "flask", "--app", "app", "run",
                  "--port", str(PORT)]
APP_FILE = "app.py"                            # doesn't exist until M2 -> vacuous PASS until then
URL = f"http://127.0.0.1:{PORT}/"              # the page a human would open
MUST_CONTAIN = [                               # strings that must appear in the response body
    "Vital Loop",                              # the app identity marker — this app's pages
                                               # and no other project's (never leave empty)
]
EXTRA_PAGES = [                                # (path, must-contain) — more pages to smoke-test
]                                              # /state lands at M2
STARTUP_TIMEOUT_SECONDS = 20
SERVED_SOURCES = [                             # what the running app loads or
    "app.py",                                  # serves — the ONLY files whose
    "engine/**/*.py",                          # edits can make a live server
    "templates/**/*",                          # stale. NOT tests/ or verify.py
    "static/**/*",                             # (they cannot change what a
]                                              # page answers).
# ------------------------------------------------------------


def fetch(url, timeout=5):
    """Return (status_code, body_text) or (None, error_message)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, str(e)


def check_response(status, body):
    """Return a list of failure reasons (empty list = pass)."""
    problems = []
    if status != 200:
        problems.append(f"Expected HTTP 200 from {URL}, got {status}.")
    for needle in MUST_CONTAIN:
        if needle not in body:
            problems.append(f"Response body is missing expected text: {needle!r}")
    return problems


def newest_served_source(root=None, patterns=None):
    """(path, mtime) of the most recently edited file the app serves, or
    (None, None) if there are none. Pure and root-relative so a test can
    prove which files count — the review state the live server writes must
    never make that server look stale to itself."""
    root = root or _HERE
    patterns = SERVED_SOURCES if patterns is None else patterns
    newest_path, newest_mtime = None, None
    for pattern in patterns:
        for path in glob.glob(os.path.join(root, pattern), recursive=True):
            if not os.path.isfile(path):
                continue
            mtime = os.path.getmtime(path)
            if newest_mtime is None or mtime > newest_mtime:
                newest_path, newest_mtime = path, mtime
    return newest_path, newest_mtime


def listening_process_start(port):
    """Epoch seconds at which the process LISTENING on `port` started, or
    None if that can't be determined (no listener, or the platform won't
    say). None means 'cannot vouch', never 'fine'."""
    try:
        if os.name == "nt":
            script = (
                f"$c = Get-NetTCPConnection -LocalPort {port} "
                "-State Listen -ErrorAction SilentlyContinue | "
                "Select-Object -First 1; "
                "if ($c) { $p = Get-Process -Id $c.OwningProcess "
                "-ErrorAction SilentlyContinue; "
                "if ($p) { [int]$p.StartTime.ToUniversalTime()."
                "Subtract([datetime]'1970-01-01').TotalSeconds } }")
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=15)
        else:
            pid = subprocess.run(
                ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=15)
            first = (pid.stdout or "").split()
            if not first:
                return None
            # elapsed seconds since start — portable on Linux and macOS
            out = subprocess.run(["ps", "-o", "etimes=", "-p", first[0]],
                                 capture_output=True, text=True, timeout=15)
            elapsed = (out.stdout or "").strip()
            return time.time() - int(elapsed) if elapsed.isdigit() else None
        text = (out.stdout or "").strip()
        return float(text) if text else None
    except Exception:
        return None


def reuse_decision(server_start, newest_mtime):
    """Can a PASS from the already-running server be trusted?

    Returns "reuse" (it started after the last served-source edit),
    "stale" (an edit landed after it started — its answers are from code
    that is no longer on disk), or "unknown" (we could not read its start
    time, so we cannot vouch for it). Only "reuse" is safe to smoke-test.
    """
    if server_start is None:
        return "unknown"
    if newest_mtime is None or server_start >= newest_mtime:
        return "reuse"
    return "stale"


def stop_pid(pid):
    """Stop a server process we did NOT start (tree-kill on Windows —
    the Store-Python shim leaves orphans holding the port otherwise)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True)
    else:
        subprocess.run(["kill", "-9", str(pid)], capture_output=True)
    time.sleep(1.0)


def listening_pid(port):
    """The PID listening on `port`, or None."""
    try:
        if os.name == "nt":
            script = (
                f"$c = Get-NetTCPConnection -LocalPort {port} "
                "-State Listen -ErrorAction SilentlyContinue | "
                "Select-Object -First 1; if ($c) { $c.OwningProcess }")
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=15)
        else:
            out = subprocess.run(["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
                                 capture_output=True, text=True, timeout=15)
        text = (out.stdout or "").split()
        return int(text[0]) if text else None
    except Exception:
        return None


def stop_process(proc):
    """Shut down the server we started (including children on Windows)."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Smoke-test the app on this machine. Refuses to test "
                    "an already-running server that is holding pre-edit "
                    "code; --restart replaces it.")
    parser.add_argument("--restart", action="store_true",
                        help="stop an already-running server and start a "
                             "fresh one instead of refusing")
    args = parser.parse_args(argv)

    os.chdir(_HERE)

    # Nothing built yet? Then there's nothing to verify — don't block.
    if not os.path.exists(APP_FILE):
        print(f"verify.py: {APP_FILE} doesn't exist yet (it arrives at M2) - "
              "nothing to verify. PASS (vacuous).")
        return 0

    # Case 1: already running (e.g. the human launched run.bat, or an
    # earlier session left one up). Testing it in place is only honest
    # if it started AFTER the last edit to anything the app serves.
    status, body = fetch(URL, timeout=3)
    started_here = None
    if status is not None:
        newest_path, newest_mtime = newest_served_source()
        decision = reuse_decision(listening_process_start(PORT), newest_mtime)
        if decision != "reuse":
            if not args.restart:
                why = (
                    f"a server is already running on port {PORT} and it "
                    f"started BEFORE the last edit to "
                    f"{os.path.relpath(newest_path, _HERE)}"
                    if decision == "stale" else
                    f"a server is already running on port {PORT} and this "
                    "machine would not tell me when it started")
                print(
                    f"FAIL: {why}, so anything it answers may come from "
                    "code that is no longer on disk - a PASS here would "
                    "be meaningless. Re-run with --restart to replace it, "
                    "or stop it yourself and re-run.",
                    file=sys.stderr)
                return 2
            pid = listening_pid(PORT)
            if pid is None:
                print(f"FAIL: --restart could not find the process "
                      f"listening on port {PORT} to stop it.",
                      file=sys.stderr)
                return 2
            print(f"--restart: stopping the {decision} server on port "
                  f"{PORT} (pid {pid}) and starting a fresh one ...")
            stop_pid(pid)
            status, body = None, None
        else:
            print(f"(reusing the server already on port {PORT} - it "
                  "started after the last change to a served file)")
    if status is None:
        # Case 2: not running. Start it ourselves.
        started_here = subprocess.Popen(
            SERVER_COMMAND,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + STARTUP_TIMEOUT_SECONDS
        while time.time() < deadline:
            status, body = fetch(URL, timeout=3)
            if status is not None:
                break
            if started_here.poll() is not None:
                print(
                    f"FAIL: server process exited immediately (code {started_here.returncode}). "
                    f"Run it by hand to see the error: {' '.join(SERVER_COMMAND)}",
                    file=sys.stderr,
                )
                return 2
            time.sleep(0.5)

    try:
        if status is None:
            print(
                f"FAIL: nothing responded at {URL} within {STARTUP_TIMEOUT_SECONDS}s. "
                f"Last error: {body}",
                file=sys.stderr,
            )
            return 2

        problems = check_response(status, body)
        for path, needle in EXTRA_PAGES:
            pstatus, pbody = fetch(URL.rstrip("/") + path, timeout=5)
            if pstatus != 200:
                problems.append(f"Expected HTTP 200 from {path}, got {pstatus}.")
            elif needle not in pbody:
                problems.append(f"{path} is missing expected text: {needle!r}")
        if problems:
            print("FAIL: " + " | ".join(problems), file=sys.stderr)
            return 2

        print(f"PASS: {URL} returned 200 with all {len(MUST_CONTAIN)} markers, "
              f"and {len(EXTRA_PAGES)} extra page(s) answered.")
        return 0
    finally:
        if started_here is not None:
            stop_process(started_here)


if __name__ == "__main__":
    sys.exit(main())
