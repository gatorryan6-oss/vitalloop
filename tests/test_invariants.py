"""Invariant tests for Vital Loop — the checkable rules from kickoff §2/§5.

The kickoff settles decisions that must never silently break. Prose in a spec
stops working the moment it falls out of Claude Code's context window; these
tests don't. They guard:

  (a) verify.py and run.bat agree on this project's dedicated port (5083),
      and that port collides with no other project on this machine,
  (b) the identity marker is set: MUST_CONTAIN[0] == "Vital Loop",
  (c) the set point is 37.0 °C — the number the whole lesson hangs on,
  (d) the sim is deterministic: same inputs -> byte-identical history, so a
      demo rehearsed at home behaves identically in class,
  (e) disabling ALL effectors removes ALL regulation — a cold room drives
      core temp steadily down with no secret stabilizer. This is the
      curriculum punchline (no feedback, no homeostasis) and it must be true
      in the model, not just claimed in the UI,
  (f) with effectors on, a resting body in a 22 °C room holds 37 ± 0.5 °C,
      and recovers to that band after a cold disturbance,
  (g) the run-history accessor returns records with the FROZEN field names
      from kickoff §5 — the strip charts, CSV export, and any future
      quiz/challenge layer all read this one shape,
  (h) the core package engine/ imports no web framework, so the model stays
      testable without starting a server.

These tests are also the CONTRACT for the engine API (built at M1):

    from engine.sim import Simulation
    sim = Simulation()          # 22 °C room, resting, everything enabled
    Simulation.SET_POINT        # 37.0
    sim.step(n)                 # advance n fixed-size ticks
    sim.set_env_temp(c)         # disturbances
    sim.set_exercise(bool)
    sim.set_effector_enabled(name, bool)   # name in {"sweat","shiver","vaso"}
    sim.set_sensor_enabled(bool)           # "sensor damage" (armed at M5)
    sim.state()                 # newest record (dict, frozen fields)
    sim.history()               # every record since reset, oldest first
    sim.reset()

--- Phase 2 (kickoff: vital_loop_phase2_kickoff.md) adds the glucose loop ---

  (i) GlucoseSimulation.SET_POINT == 90.0 mg/dL, deterministic, frozen
      record fields, state() == history()[-1],
  (j) pinned glucose physiology: a resting fasted body holds 90 +/- 15;
      a 60 g meal peaks between 110 and 180 and returns to 70-110 within
      3 sim-hours; BETA CELLS OFF + meal -> glucose rises above 180 and
      STAYS above 180 (the type 1 signature, with no secret uptake);
      ALPHA CELLS OFF + a 12 h fast -> glucose falls below 70 (no secret
      liver rescue),
  (k) REGRESSION GUARD: Phase 2 must not change Phase 1 - the
      thermoregulation scripted run's history hashes to the exact value
      recorded when M5 shipped. If this fails, Phase 1 was rebuilt, which
      standing rule 3 forbids.

The glucose engine API contract (built at M6):

    from engine.glucose import GlucoseSimulation
    sim = GlucoseSimulation()   # fasted, resting, everything working
    GlucoseSimulation.SET_POINT # 90.0 (mg/dL)
    sim.step(n)                 # advance n fixed 1 s ticks
    sim.eat(grams, rate_g_per_min)         # carbs into the gut
    sim.set_exercise(bool)
    sim.set_effector_enabled(name, bool)   # name in {"beta","alpha","liver"}
    sim.set_sensor_enabled(bool)
    sim.state() / sim.history() / sim.reset()   # as in the thermo engine

--- Phase 3 (kickoff: vital_loop_phase3_kickoff.md) adds injection dosing ---

  (l) the frozen glucose record GROWS four fields (injected_insulin,
      total_insulin, iob_units, basal_rate); the Phase 2 fields keep their
      exact meaning — `insulin` stays beta-cell output alone,
  (m) pinned dosing physiology: a bolus is NOT instant (peak effect 30-90
      sim-minutes after injection, under 30% of peak in the first 5 min,
      under 25% of peak 4 h later); beta cells off, a 60 g meal + 4 U at
      mealtime returns glucose to 70-110 within 5 h and never drops below
      65 within 8 h (replacement works); beta cells off, fasted, 10 U
      drives glucose below 70 within 3 h even though glucagon and the
      liver fight back (overdose is dangerous — no secret floor); beta
      cells off + 1.0 U/h basal holds a 12 h fast inside 70-180 (basal
      holds the fasting line),
  (n) REGRESSION GUARD: with zero injections and zero basal, the Phase 2
      scripted glucose run's PHASE 2 FIELD SUBSET is byte-identical to the
      M10 baseline hash — Phase 3 grows the record shape but must not
      change one recorded value of the old behavior,
  (o) determinism now includes injections and basal changes.

The dosing API contract (built at M11):

    sim.inject(units)             # subcutaneous bolus, units > 0
    sim.set_basal_rate(u_per_hr)  # continuous drip, >= 0
    sim.doses()                   # bolus event log: [{"t":..., "units":...}]
                                  # oldest first, cleared by reset()

--- Phase 4 (kickoff: vital_loop_phase4_kickoff.md) adds the pump --------

  (p) the frozen glucose record GROWS two fields (pump_enabled, pump_rate);
      pump insulin flows through the SAME depot/plasma/IOB fields as
      Phase 3 boluses — no parallel accounting,
  (q) pinned pump physiology: beta cells off + pump on holds a 12 h fast
      inside 70-140 with no manual help; a 60 g meal handled by the pump
      ALONE peaks above 140 (the subcutaneous lag is honest) but returns
      to 70-140 within 4 h and never dips below 65; with the sensors
      disabled the pump keeps blindly infusing its set-point rate while
      the sensor-frozen alpha cells cannot defend, and glucose crashes
      below 54 within 3 h — the artificial loop fails at the same box as
      the biological one, and the blind failure mode is OVER-delivery,
  (r) the pump decides every 5 sim-minutes and holds its rate between
      decisions - the recorded pump_rate is a staircase, not a ramp,
  (s) REGRESSION GUARD: with the pump never enabled, the Phase 3 scripted
      dosing run's PHASE 2+3 FIELD SUBSET is byte-identical to the M13
      baseline hash; the thermo and Phase 2 hashes stay untouched,
  (t) determinism includes pump on/off mid-run.

The pump API contract (built at M14):

    sim.set_pump_enabled(bool)    # closed-loop pump on/off; while on, the
                                  # pump's rate (not the manual basal)
                                  # feeds the depot; off -> pump_rate 0.0

--- Phase 5 (kickoff: vital_loop_phase5_kickoff.md) adds disease knobs ---

  (u) the thermo record GROWS fever_offset; the glucose record GROWS
      insulin_sensitivity. Guard (k) switches to hashing the PHASE 1
      FIELD SUBSET - its pinned VALUE must not change, which proves the
      amendment is shape-only (the subset serializes today's records
      identically to the old full-record hash),
  (v) FEVER IS A MOVED SET POINT, NOT A BROKEN LOOP: set_fever(2.0) in a
      22 C room settles core at 39 +/- 0.5 and HOLDS it; during onset
      there is a stretch with core ABOVE 37 and shivering active (chills
      while already hot); after clearing there is a stretch with core
      above 37 and sweating active (the sweat of a breaking fever).
      Simulation.SET_POINT stays 37.0 - fever is runtime state,
  (w) INSULIN RESISTANCE deafens every insulin action at once: at
      sensitivity 0.05, a fasted 8 h body parks above 110 mg/dL WITH
      insulin at 0.5+ and glucagon inappropriately high (0.25+) - both
      numbers high is the type 2 signature, and the fasting
      hyperglycemia comes from the unrestrained alpha cells driving the
      liver (real pathophysiology, emergent); a 60 g meal peaks above
      250 and is still above 110 three hours later,
  (x) validation: set_fever takes any float; set_insulin_sensitivity
      only (0, 1] - 0 would be type 1 by another name, use the beta
      toggle for that,
  (y) REGRESSION: offset 0.0 and sensitivity 1.0 leave every pinned
      hash untouched (fever adds to the error term, sensitivity
      multiplies actions - both are exact identities at their defaults),
  (z) determinism includes both new controls exercised mid-run.

The disease-knob API contract (built at M17):

    sim.set_fever(offset_c)               # thermo; 0.0 clears
    sim.set_insulin_sensitivity(s)        # glucose; s in (0, 1]

--- Phase 6 (kickoff: vital_loop_phase6_kickoff.md) adds the water loop ---

  (aa) WaterSimulation.SET_POINT == 290.0 mOsm/L, deterministic, frozen
       record fields, state() == history()[-1], engine purity,
  (bb) pinned osmoregulation physiology: resting with water access the
       loop holds 290 +/- 5 for 12 h BY DRINKING (the behavioral
       effector closes the loop); in the desert (no access + sweating)
       osmolarity passes 305 in 2.5-5 h with urine pinned near the
       floor (ADH conserving, and conserving is not enough); central DI
       (ADH off) WITH access stays under 300 for 6 h while passing more
       than 3 L of urine (flooding AND surviving); ADH off AND the
       desert passes 305 within 2.5 h (the layered failure); a 3 L chug
       drives osmolarity below 280, ADH to ~0, urine above 8 mL/min at
       under 150 mOsm/L, and back into the band within 6 h; there is a
       sensed range where ADH > 0.3 while thirst == 0 (conserve first,
       drink second - the staged thresholds),
  (cc) the drink event log drinks() records {"t","ml","auto"} with
       auto-drinks marked, cleared by reset(),
  (dd) the three existing regression hashes stay untouched - the water
       loop is a NEW module riding the kit, not a change to any engine.

--- Phase 8 (kickoff: vital_loop_phase8_kickoff.md) adds the game layer ---

  (ee) score_report(entry, report) is PURE: fed a crafted report it returns
       exact points and tier and never mutates its input. Every challenge
       scores out of 100, and an INTEGRITY row (the "you cheated" lines)
       zeroes the run rather than docking it,
  (ff) every challenge carries all three medal thresholds, strictly
       ordered gold > silver > bronze and all inside 0..max,
  (gg) the attempts log round-trips (save -> load -> identical), starts
       EMPTY AND LOUD on a missing or corrupt file instead of crashing,
       preserves a corrupt file instead of overwriting it, keeps only the
       most recent 500, writes atomically (no temp file left behind), and
       RAISES rather than pretending a failed write saved,
  (hh) an attempt carries the frozen fields from kickoff SS5, and data/ is
       gitignored - student scores are runtime data, not source.

  (ii) M27 head-to-head: a team label is free text, TIDIED and CAPPED
       server-side, and an empty or non-string one stores as None (it is
       a TEAM name, never a student's - kickoff SS2),
  (jj) compare_attempts(a, b) is PURE and SYMMETRIC: swap the two runs
       and every winner flips, an equal row has NO winner, a row with no
       points goes to the honest run, and the overall winner is simply
       the higher total. It reads the log and computes no physiology,
  (kk) the leaderboard is one line per run, best first, ties to the
       EARLIER run, capped, and never mixes in another challenge's runs,
  (ll) an attempt GROWS `score_rows` and `zeroed` (appended at M27, so
       M26 records still load) - and an attempt logged without them must
       still compare rather than crash.

  (mm) M28 diagnosis: every CASES entry carries what the card, the reveal
       and the grader need, its `answer` names a role and a part that are
       both in that loop's ANSWER_OPTIONS, and its setup is built only
       from the preset/breaker vocabulary the app already applies,
  (nn) REDACTION IS AN ALLOWLIST, NOT A BLOCKLIST. While a case is live
       and unanswered the snapshot ships only VISIBLE_DURING_CASE[loop]:
       no `*_enabled` flag, no water_access, no fever_offset, no
       insulin_sensitivity, no preset. A blocklist fails OPEN - a field
       added by a later phase would leak the answer silently - so the
       gate is a list of what the charts and the diagram need, every name
       on it really exists in that engine's record, and anything else is
       withheld until somebody lists it on purpose,
  (oo) grade_answer(case, answer) is PURE: role AND part right is
       correct, role right with the wrong part is partial credit, a wrong
       role is wrong. Role "none" normalizes its own part, so a form that
       leaves a stale part selected can never mark a right answer wrong,
  (pp) THE REVEAL RELEASES EVERYTHING, and the released history is
       IDENTICAL to the same case run un-blinded (kickoff SS5: "verify
       that, don't assume it"). Redaction is a delivery gate, never data
       loss - the engine recorded every field all along,
  (qq) a diagnosis attempt carries mode "diagnosis" plus the submitted
       answer and whether it was right (appended fields, kickoff SS5),
       and never appears on a challenge leaderboard,
  (rr) THE ANSWER NEVER REACHES THE PAGE: no case identifier is rendered
       into the HTML at all (the picker sends an INDEX, so there is
       nothing to map), /state's case block carries the truth and the
       teaching note only after the class has committed, and
       /export.csv refuses while a case is blind - a spreadsheet of
       `sensor_enabled` is the answer key in a column.

  (ss) M29 crisis: one crisis challenge per loop, each carrying an
       `events` schedule of (sim-time offset, action, plain-English line).
       Offsets climb and land inside the window, every action is a method
       the loop's own engine already exposes (kickoff SS0 again: an ambush
       goes through the SAME public API the buttons call), and every
       crisis names hard-stop lines that SCORING zeroes,
  (tt) AN AMBUSH LANDS ON SIM-TIME, NOT ON POLL TIMING. The same crisis
       stepped one tick at a time and in chunks of 991 must produce
       byte-identical history and an identical feed - that is what makes
       the run a teacher rehearses the run the class gets. A challenge
       with no events steps exactly as a plain sim.step() run, so M24-M28
       are untouched,
  (uu) A HARD STOP CLOSES THE WINDOW, IT NEVER STOPS THE BODY: t_end is
       pulled back to the tick the line was crossed, the simulation runs
       on, the report card carries a `stopped` row saying what happened
       and when, and the score is zero with a reason in words. Zeroed
       because a truncated window scores a FLATTERING percentage, and
       crashing early must not out-score playing it out,
  (vv) THE SCHEDULE IS NOT A TIMETABLE: /state carries only what has
       already landed (sim-time, offset, words - never the action), no
       event line is rendered into the page, ambushes stop firing when the
       window closes, and the feed is APPENDED to the attempt record so a
       later phase can ask what a team was hit with.

  (ww) M30 close: every loop carries every verb of the lesson grammar —
       a disease to name and a way back, a plain challenge to score and
       race, a crisis to survive, cases to diagnose, a CSV and an answer
       vocabulary,
  (xx) THE SANDBOX STAYS GAMELESS. With no challenge and no case running
       there is no game block in /state at all, no preset, nothing
       redacted and the CSV works — a teacher who wants to explore for
       forty minutes never has to dismiss a game (kickoff SS2),
  (yy) A RELOAD MID-GAME LOSES NOTHING, because game state hangs off the
       Runner and never off the page: the label, the stamp and the event
       feed all come back from server state, a reloaded page asking
       `since=-1` gets the whole run to redraw from, and a blind case is
       still blind afterwards,
  (zz) NOTHING WEDGES. Every action the UI can send — plus the malformed
       and wrong-loop versions of each — fired at all three loops must
       answer 200 or a plain-English 400, never a 500 and never a hang,
       and every loop must still be teaching afterwards. It runs on a
       projector in a classroom; a wrong click cannot cost the lesson.

  The engines are untouched by this entire phase (kickoff SS0: "no engine
  file changes in this phase at all"); guards (h), (k), (n), (s) above are
  the proof, and they are not repeated here.

The game-layer API contract (built at M26):

    app.score_report(entry, report)   # -> {"points","max","medal","rows",
                                      #     "zeroed"}; entry needs
                                      # "metrics" + "medals"
    app.SCORING[metrics]              # per-row weights, twin of EVALUATORS
    app.build_attempt(loop, name, report, score, label=None)
    app.clean_label(raw)              # -> a short team name, or None
    app.leaderboard(loop, name)       # -> compact lines, best first (M27)
    app.compare_attempts(a, b)        # -> merged rows + winners (M27)

The diagnosis API contract (built at M28):

    app.CASES[loop][case_id]          # {brief, setup, start_actions,
                                      #  speed, warmup_s, answer, note}
    app.ANSWER_OPTIONS[loop]          # {"roles": [...], "parts": [...]},
                                      # each entry {"key","label"} - the
                                      # form's vocabulary, safe to render
    app.VISIBLE_DURING_CASE[loop]     # the redaction ALLOWLIST
    app.redact_record(loop, record)   # -> the record minus the answer key
    app.grade_answer(case, answer, options=None)
                                      # -> {"verdict","correct","points",
                                      #     "rows","truth","note","answer"}
    app.build_case_attempt(loop, case_id, grade, label=None)

The crisis API contract (built at M29):

    CHALLENGES[loop][cid]["events"]    # [{"at": offset_s,
                                      #   "do": (method, args_tuple),
                                      #   "line": "what just hit you"}]
    app.STOPS[metrics]                # [{"key","line","test": record->bool}]
    app.start_challenge(runner, loop, name, label=None)
                                      # arms a challenge on a runner: the
                                      # ONE definition of what starting one
                                      # means (routes, tests and the sweep
                                      # all take this path)
    runner._step(n)                   # n ticks, split at every event and
                                      # watched for stops; lock held
    runner.challenge["feed"]          # what has landed: {"t","at","line"}
    runner.challenge["stopped"]       # {"key","line","t"} or None

    import attempts
    attempts.load(path) / attempts.save(records, path)
    attempts.append(record, path)     # load, append, cap, save atomically
    attempts.last_warning()           # the loud bit, for the UI to show
    attempts.MAX_ATTEMPTS == 500

The water engine API contract (built at M20):

    from engine.water import WaterSimulation
    sim = WaterSimulation()     # 290 mOsm/L, resting, water within reach
    WaterSimulation.SET_POINT   # 290.0 (mOsm/L)
    sim.step(n)                 # advance n fixed 1 s ticks
    sim.drink(ml)               # water into the gut (manual)
    sim.eat_salt(mosm)          # solute bolus (salty snack)
    sim.set_exercise(bool)      # sweating: hypotonic loss
    sim.set_effector_enabled(name, bool)   # {"adh","kidney","access"}
    sim.set_sensor_enabled(bool)
    sim.drinks()                # intake event log, oldest first
    sim.state() / sim.history() / sim.reset()   # as in the other engines

The rooms API contract (built at M43, Phase 11):

    import periods
    periods.load_periods(path=PERIODS_FILE)
                                      # -> [names], teacher's order, deduped;
                                      # missing/empty file -> [] = joining
                                      # QUIETLY OFF (no overlay, no error)
    app.PERIODS                       # the launch-time list the page renders
    registry.runners_for(sid, period=None, team=None)
                                      # None = no claim (changes nothing);
                                      # "" = a real claim: Unassigned.
                                      # The COOKIE is the source of truth -
                                      # the registry only mirrors it, so
                                      # sweeps and restarts cost nothing.
    registry.identity(sid)            # -> {"period","team"} or None.
                                      # READ-ONLY: never seats a session,
                                      # never touches last_seen.

    (M44) an attempt carries "period", stamped at build time from the
    requesting session's cookie ("" = Unassigned; pre-M44 records have
    no key and read the same). challenge_runs / leaderboard /
    best_attempt grew a period=... kwarg: a name scopes to that class,
    None means everyone, and the DEFAULT scopes to the request's own
    viewer — Unassigned viewers (the projector) and non-request callers
    see everyone. /state carries "board_period" so the page can say
    which scope it is showing. compare_attempts stays cross-period ON
    PURPOSE: racing another class is a feature.

    (M45) app.TEACHER_PIN — minted per launch (VL_TEACHER_PIN pins it
    for tests/rehearsal); /teacher GET shows the PIN form or the room,
    POST with a wrong pin is a 403 IN WORDS, a right one sets the
    cookie (the app's ONE deliberate server-set identity) and lands on
    the room. registry.room() -> [{sid, period, team, idle_s, runners}]
    — sweeps the idle but never seats, never touches last_seen, never
    steps a sim; rendering the dashboard leaves every session's history
    byte-identical. The room page names a blind case BY NUMBER ONLY
    (it may be projected), and "/teacher" appears in no student-facing
    payload.

    (M46) who's-stuck. Challenge stamps and case stamps grow a
    wall-clock "wall_start" (app-level, never the engine's); Runner
    grows `tries` (per challenge name: [{points, medal}], this
    session's finished runs — the LOG stays the scores' one truth).
    STUCK_BLIND_S == 300, STUCK_QUIET_S == 180, STUCK_ZEROES == 2 —
    swept policy, tunable WITH their pins. _stuck_reason checks every
    runner (a blind case on a background tab still counts), one reason
    per row: blind > zeroes > quiet. Stuck rows sort FIRST.
    /teacher/room.json: the same rows as data, same PIN gate, still
    read-only.

    (M46.5) "name your team once": an attempt built with NO card label
    inherits the requesting session's join-screen team name (through
    clean_label, like every name); an explicit card label always wins;
    outside a request nothing changes. The page pre-fills empty label
    boxes from the cookie, still editable per run.

    (M47) the Phase 11 close. Two classes and a projector through the
    production routes: attempts land stamped with their class, boards
    scope per viewer, the dashboard watches a blind case by number
    with the teacher signed in — and a server restart (a fresh
    registry) costs a device nothing because its cookies re-present
    everything. The cookieless world gained exactly ONE key
    (board_period, always None for it) and no period/team/stuck
    anywhere — verify.py, curl and ten phases of tests keep meaning
    what they meant. Engines untouched all phase: the two regression
    hashes are the proof and are not repeated here.

The class report API contract (built at M48, Phase 12):

    import report
    report.class_report(attempts, period, date, catalog=None)
                                      # -> {"period","date","teams",
                                      #     "team_count","run_count",
                                      #     "answer_count","aggregate"}
    report.attempts_for(attempts, period, date)   # the day's runs
    report.TEAMLESS / report.THIN_SAMPLE

    PURE: the log and the DATE arrive as arguments - no clock read, no
    Flask, no app import - so the paper is reproducible from a crafted
    log. period "" is the Unassigned pile, and a pre-M44 record (no
    period key) belongs to it. An empty day is a VALID report, never an
    error. A team row keeps its BEST run of a challenge; a case row
    keeps both first_correct and ever_correct, because grading policy
    is the teacher's. The debrief counts FIRST answers per team only.
    `catalog` carries titles and right answers in from app.py (which
    imports Flask), shape:
      {"challenges": {(loop, name): title},
       "cases": {(loop, name): {"title", "answer_line"}}}

Tests whose inputs don't exist yet SKIP with a loud reason naming the
milestone that arms them. Do not delete the skips; just build the milestones.

Run: python -m pytest tests/test_invariants.py -q
"""

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ENGINE_PKG = ROOT / "engine"

# ---------------- CONFIG (from kickoff §2 and §5) ----------------
# Ports already owned by other projects on this machine (read from their
# verify.py / run.bat files at M0, 2026-08-13).
FORBIDDEN_PORTS = {5000, 5050, 5055, 5057, 5077, 5078, 5079, 5080, 5081,
                   5082, 8000, 8501, 8503, 8504}
PROJECT_PORT = 5083
IDENTITY_MARKER = "Vital Loop"
SET_POINT = 37.0

# Kickoff §5: the frozen record shape. Everything downstream — strip charts,
# CSV export, future quiz layers — reads exactly these fields.
HISTORY_FIELDS = {
    "t",                # sim time, seconds
    "core_temp",        # °C — the controlled variable
    "env_temp",         # °C — the main disturbance
    "exercise",         # bool — metabolic-heat disturbance
    "error",            # core_temp - set point, as the controller sees it
    "sweat",            # effector activity, 0..1
    "shiver",           # effector activity, 0..1
    "vaso",             # skin blood flow, -1 (constricted) .. +1 (dilated)
    "sweat_enabled",    # the break-the-loop toggles (armed at M5's UI,
    "shiver_enabled",   # but modeled from M1 so the physiology tests
    "vaso_enabled",     # below can prove they matter)
    "sensor_enabled",
    # -- grown at M17 (Phase 5 kickoff SS5), a deliberate contract amendment:
    "fever_offset",     # degC the thermostat is shifted; 0.0 = no fever
}

# The Phase 1 record shape as frozen at M0 — guard (k) hashes exactly this
# subset of the scripted run, and its pinned value predates the growth.
PHASE1_THERMO_FIELDS = sorted(HISTORY_FIELDS - {"fever_offset"})
# -----------------------------------------------------------------


def _engine():
    """Import the engine, or SKIP loudly if it isn't built yet (M1)."""
    if not ENGINE_PKG.exists():
        pytest.skip("engine/ doesn't exist yet - it arrives at M1")
    from engine.sim import Simulation
    return Simulation


# ---------------------------------------------------------------- (a) ports

def test_verify_port_is_this_projects_own():
    import verify
    assert verify.PORT == PROJECT_PORT, (
        f"verify.py PORT is {verify.PORT}, but this project's dedicated "
        f"port is {PROJECT_PORT}")
    assert verify.PORT not in FORBIDDEN_PORTS, (
        f"Port {verify.PORT} belongs to another project on this machine")


def test_run_bat_uses_the_same_port():
    text = (ROOT / "run.bat").read_text(encoding="utf-8")
    m = re.search(r"^set PORT=(\d+)\s*$", text, re.MULTILINE)
    assert m, "run.bat must contain a 'set PORT=<n>' line"
    assert int(m.group(1)) == PROJECT_PORT, (
        f"run.bat sets PORT={m.group(1)} but verify.py expects {PROJECT_PORT} "
        "- they must always agree")


# ------------------------------------------------------- (b) identity marker

def test_identity_marker_is_set():
    import verify
    assert verify.MUST_CONTAIN, "MUST_CONTAIN may never be empty"
    assert verify.MUST_CONTAIN[0] == IDENTITY_MARKER, (
        f"MUST_CONTAIN[0] is {verify.MUST_CONTAIN[0]!r}; the identity marker "
        f"must be {IDENTITY_MARKER!r} - this app's pages and no other's")


# ------------------------------------------------------------ (c) set point

def test_set_point_is_37():
    Simulation = _engine()
    assert Simulation.SET_POINT == SET_POINT


# ---------------------------------------------------------- (d) determinism

def _scripted_run(Simulation):
    """A run that exercises every control, for the determinism check."""
    sim = Simulation()
    sim.step(300)
    sim.set_env_temp(5.0)
    sim.step(600)
    sim.set_exercise(True)
    sim.step(300)
    sim.set_exercise(False)
    sim.set_env_temp(40.0)
    sim.set_effector_enabled("sweat", False)
    sim.step(600)
    return sim.history()


def test_same_inputs_same_history():
    Simulation = _engine()
    a = _scripted_run(Simulation)
    b = _scripted_run(Simulation)
    assert a == b, (
        "Two identical scripted runs produced different histories - the sim "
        "must be deterministic (kickoff SS2: rehearsed at home == in class)")


# ------------------------------------- (e) no feedback -> no homeostasis

def test_all_effectors_disabled_means_no_regulation():
    Simulation = _engine()
    sim = Simulation()
    for name in ("sweat", "shiver", "vaso"):
        sim.set_effector_enabled(name, False)
    sim.set_env_temp(5.0)
    sim.step(3600)
    temps = [r["core_temp"] for r in sim.history()]
    assert all(b <= a + 1e-9 for a, b in zip(temps, temps[1:])), (
        "With every effector disabled in a 5 degC room, core temp must fall "
        "monotonically - something is secretly stabilizing it")
    assert temps[-1] < 36.0, (
        f"After an hour at 5 degC with no effectors, core temp is only down "
        f"to {temps[-1]:.2f} degC - the failure must be visible, not cosmetic")


# ----------------------------------------------- (f) homeostasis physiology

def test_resting_body_holds_set_point():
    Simulation = _engine()
    sim = Simulation()
    sim.step(3600)
    temps = [r["core_temp"] for r in sim.history()]
    bad = [t for t in temps if abs(t - SET_POINT) > 0.5]
    assert not bad, (
        f"At rest in a 22 degC room, core temp left the 37 +/- 0.5 band "
        f"({len(bad)} of {len(temps)} ticks; worst {max(bad, key=lambda t: abs(t - SET_POINT)):.2f})")


def test_recovers_from_cold_disturbance():
    Simulation = _engine()
    sim = Simulation()
    sim.step(300)
    sim.set_env_temp(5.0)
    sim.step(5400)
    final = sim.state()["core_temp"]
    assert abs(final - SET_POINT) <= 0.5, (
        f"90 min after stepping into a 5 degC room, core temp is "
        f"{final:.2f} degC - the loop must pull it back to 37 +/- 0.5")


# ------------------------------------------------- (g) frozen record shape

def test_history_records_have_the_frozen_fields():
    Simulation = _engine()
    sim = Simulation()
    sim.step(5)
    records = sim.history()
    assert records, "history() returned nothing after stepping"
    for r in (records[0], records[-1], sim.state()):
        assert set(r.keys()) == HISTORY_FIELDS, (
            f"Record fields {sorted(r.keys())} != frozen set "
            f"{sorted(HISTORY_FIELDS)} (kickoff SS5) - downstream readers "
            "depend on exactly this shape")


def test_state_is_the_newest_history_record():
    Simulation = _engine()
    sim = Simulation()
    sim.step(10)
    assert sim.state() == sim.history()[-1]


# ------------------------------------------------------ (h) engine purity

# ======================= Phase 2: the glucose loop =======================

GLUCOSE_SET_POINT = 90.0
HEALTHY_BAND = (70.0, 110.0)
HYPER_LINE = 180.0

# Kickoff Phase 2 SS5: the frozen glucose record shape.
GLUCOSE_FIELDS = {
    "t",                # sim time, seconds
    "glucose",          # mg/dL - the controlled variable
    "gut_carbs",        # g still being absorbed - the disturbance in flight
    "exercise",         # bool - muscles burning glucose
    "error",            # glucose - set point, as the islet cells see it
    "insulin",          # hormone activity, 0..1  (beta cells)
    "glucagon",         # hormone activity, 0..1  (alpha cells)
    "uptake",           # mg/dL/min leaving the blood (tissues + kidneys)
    "liver_flux",       # mg/dL/min entering the blood from the liver
    "beta_enabled",     # the break-the-loop toggles (armed at M10's UI,
    "alpha_enabled",    # modeled from M6 so the physiology tests below
    "liver_enabled",    # can prove they matter)
    "sensor_enabled",
    # -- grown at M11 (Phase 3 kickoff SS5), a deliberate contract amendment:
    "injected_insulin", # exogenous plasma activity, 0..1 (same scale as
                        # insulin; `insulin` stays beta-cell output ALONE)
    "total_insulin",    # clamp(insulin + injected_insulin) — what the body
                        # actually responds to; recorded, never JS-derived
    "iob_units",        # "insulin on board": U still working (depot+plasma)
    "basal_rate",       # MANUAL drip setting, U/h (the pump has its own)
    # -- grown at M14 (Phase 4 kickoff SS5), the next amendment:
    "pump_enabled",     # closed-loop pump on/off
    "pump_rate",        # U/h the pump algorithm chose this tick; 0.0 off
    # -- grown at M17 (Phase 5 kickoff SS5):
    "insulin_sensitivity",  # 0..1, how well tissues hear insulin; 1 healthy
    # -- grown at M37 (Phase 10 kickoff SS5): the kidney spill, named so
    # the water loop can read it. It was ALREADY happening (M6 folded it
    # into `uptake`, where it still is) — this reports the component.
    "renal_loss",       # mg/dL/min leaving in the urine above 180 mg/dL
}

PHASE3_FIELDS_ADDED = {"injected_insulin", "total_insulin", "iob_units",
                       "basal_rate"}
PHASE4_FIELDS_ADDED = {"pump_enabled", "pump_rate"}
PHASE5_FIELDS_ADDED = {"insulin_sensitivity"}
PHASE10_FIELDS_ADDED = {"renal_loss"}

# The record shapes as frozen at each phase's end — the stacked regression
# guards (n) and (s) hash exactly these subsets of their scripted runs.
PHASE2_GLUCOSE_FIELDS = sorted(GLUCOSE_FIELDS - PHASE3_FIELDS_ADDED
                               - PHASE4_FIELDS_ADDED - PHASE5_FIELDS_ADDED
                               - PHASE10_FIELDS_ADDED)
PHASE23_GLUCOSE_FIELDS = sorted(GLUCOSE_FIELDS - PHASE4_FIELDS_ADDED
                                - PHASE5_FIELDS_ADDED - PHASE10_FIELDS_ADDED)

# (k) sha256 of json.dumps(_scripted_run(Simulation), sort_keys=True),
# recorded 2026-08-13 with M5 committed — the last Phase 1 state.
THERMO_HISTORY_SHA256 = (
    "9c83fe86705f76eef3c6693f010b79b965fdd89915667a07f78b0381841539f8")


def _glucose():
    """Import the glucose engine, or SKIP loudly if not built yet (M6)."""
    if not (ENGINE_PKG / "glucose.py").exists():
        pytest.skip("engine/glucose.py doesn't exist yet - it arrives at M6")
    from engine.glucose import GlucoseSimulation
    return GlucoseSimulation


def test_glucose_set_point_is_90():
    GlucoseSimulation = _glucose()
    assert GlucoseSimulation.SET_POINT == GLUCOSE_SET_POINT


def _scripted_glucose_run(GlucoseSimulation):
    sim = GlucoseSimulation()
    sim.step(1800)
    sim.eat(60, 1.0)
    sim.step(3600)
    sim.set_exercise(True)
    sim.step(1800)
    sim.set_exercise(False)
    sim.set_effector_enabled("beta", False)
    sim.eat(40, 1.5)
    sim.step(3600)
    return sim.history()


def test_glucose_same_inputs_same_history():
    GlucoseSimulation = _glucose()
    a = _scripted_glucose_run(GlucoseSimulation)
    b = _scripted_glucose_run(GlucoseSimulation)
    assert a == b, "The glucose sim must be deterministic (kickoff SS2)"


def test_glucose_resting_fasted_holds_band():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.step(2 * 3600)
    values = [r["glucose"] for r in sim.history()]
    bad = [g for g in values if abs(g - GLUCOSE_SET_POINT) > 15.0]
    assert not bad, (
        f"Resting fasted glucose left 90 +/- 15 mg/dL "
        f"({len(bad)} of {len(values)} ticks; worst "
        f"{max(bad, key=lambda g: abs(g - GLUCOSE_SET_POINT)):.1f})")


def test_meal_peaks_in_range_and_returns():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.step(1800)                      # settle to the fasted equilibrium
    sim.eat(60, 1.0)
    sim.step(3 * 3600)
    values = [r["glucose"] for r in sim.history()]
    peak = max(values)
    assert 110.0 < peak < 180.0, (
        f"A 60 g meal should peak between 110 and 180 mg/dL, peaked at "
        f"{peak:.1f}")
    final = values[-1]
    assert HEALTHY_BAND[0] <= final <= HEALTHY_BAND[1], (
        f"3 h after a 60 g meal glucose should be back in 70-110, it is "
        f"{final:.1f}")


def test_beta_cells_off_meal_hyperglycemia_persists():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.step(600)
    sim.eat(60, 1.0)
    sim.step(4 * 3600)
    tail = [r["glucose"] for r in sim.history()[-1800:]]
    assert min(tail) > HYPER_LINE, (
        f"With beta cells disabled a 60 g meal must leave glucose above "
        f"{HYPER_LINE:.0f} mg/dL for good - the type 1 signature - but the "
        f"last 30 min dipped to {min(tail):.1f}. No secret uptake allowed.")


def test_alpha_cells_off_fasting_hypoglycemia():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("alpha", False)
    sim.step(12 * 3600)
    final = sim.state()["glucose"]
    assert final < HEALTHY_BAND[0], (
        f"With alpha cells disabled, a 12 h fast must drop glucose below "
        f"{HEALTHY_BAND[0]:.0f} mg/dL (no secret liver rescue); it is "
        f"{final:.1f}")


def test_glucose_records_have_the_frozen_fields():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.step(5)
    records = sim.history()
    assert records, "history() returned nothing after stepping"
    for r in (records[0], records[-1], sim.state()):
        assert set(r.keys()) == GLUCOSE_FIELDS, (
            f"Record fields {sorted(r.keys())} != frozen set "
            f"{sorted(GLUCOSE_FIELDS)} (Phase 2 kickoff SS5)")


def test_glucose_state_is_newest_record():
    GlucoseSimulation = _glucose()
    sim = GlucoseSimulation()
    sim.step(10)
    assert sim.state() == sim.history()[-1]


def test_thermo_history_unchanged_since_phase1():
    """(k), amended at M17 per invariant (u): hash the PHASE 1 FIELD
    SUBSET so the record may grow. The pinned VALUE is the one recorded
    at M5 — subset serialization is byte-identical to the old full-record
    hash for any run whose values didn't change, so a pass here proves
    the growth was shape-only."""
    import hashlib
    import json
    from engine.sim import Simulation
    records = _scripted_run(Simulation)
    subset = [{k: r[k] for k in PHASE1_THERMO_FIELDS} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == THERMO_HISTORY_SHA256, (
        "The thermoregulation engine's scripted-run history changed. "
        "Later phases must EXTEND Phase 1, never rebuild it (standing "
        "rule 3). If this change was ordered by the human, re-record the "
        "hash and say so in BUILDLOG.md.")


# ================= Phase 3: insulin-injection dosing =====================

# (n) sha256 of json.dumps of the PHASE 2 FIELD SUBSET of
# _scripted_glucose_run's records, recorded 2026-08-13 with M10 committed —
# the last Phase 2 state. Phase 3 grows the record but must not change one
# recorded value of the old behavior.
GLUCOSE_PHASE2_SUBSET_SHA256 = (
    "d81402f2c46b1533ba55067f53b7937b94340e8f4ccdf32047aa9e1d24890e39")

HYPO_LINE = 70.0


def _dosing():
    """The glucose engine once it speaks the dosing API, or SKIP (M11)."""
    GlucoseSimulation = _glucose()
    if not hasattr(GlucoseSimulation, "inject"):
        pytest.skip("inject() doesn't exist yet - it arrives at M11")
    return GlucoseSimulation


def test_bolus_is_not_instant():
    """(m) The subcutaneous delay IS the teaching mechanic: little effect in
    the first minutes, peak 30-90 min out, essentially spent by 4 h."""
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    sim.step(600)                        # settle, then inject at t0
    t0 = sim.state()["t"]
    sim.inject(2)                        # small dose: activity stays unclamped
    sim.step(4 * 3600)
    after = [r for r in sim.history() if r["t"] > t0]
    activity = [r["injected_insulin"] for r in after]
    peak = max(activity)
    assert peak > 0.0, "A 2 U bolus produced no injected insulin activity"
    peak_minutes = (after[activity.index(peak)]["t"] - t0) / 60.0
    assert 30.0 <= peak_minutes <= 90.0, (
        f"Injected insulin peaked {peak_minutes:.0f} min after the bolus; "
        "rapid-acting analog peak must land 30-90 sim-minutes out")
    at_5min = next(r["injected_insulin"] for r in after if r["t"] >= t0 + 300)
    assert at_5min < 0.30 * peak, (
        f"5 min after the bolus activity is already {at_5min / peak:.0%} of "
        "peak - injections must not act instantly")
    at_4h = after[-1]["injected_insulin"]
    assert at_4h < 0.25 * peak, (
        f"4 h after the bolus activity is still {at_4h / peak:.0%} of peak - "
        "a rapid-acting bolus must be essentially spent")


def test_replacement_bolus_controls_a_type1_meal():
    """(m) Beta cells off, 60 g meal + 4 U at mealtime: the manual dose does
    what the missing beta cells would have - lands the spike back in the
    healthy band without overshooting into a hypo."""
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.step(600)
    t0 = sim.state()["t"]
    sim.eat(60, 1.0)
    sim.inject(4)
    sim.step(8 * 3600)
    after = [r for r in sim.history() if r["t"] > t0]
    glucoses = [r["glucose"] for r in after]
    peak_i = glucoses.index(max(glucoses))
    assert glucoses[peak_i] > HEALTHY_BAND[1], (
        "The 60 g meal never spiked above the band - nothing to control")
    in_band_at = next(
        (r["t"] - t0 for r in after[peak_i:]
         if HEALTHY_BAND[0] <= r["glucose"] <= HEALTHY_BAND[1]), None)
    assert in_band_at is not None and in_band_at <= 5 * 3600, (
        "With beta cells off, a 60 g meal + 4 U bolus must bring the spike "
        "back into 70-110 within 5 sim-hours"
        + ("" if in_band_at is None else f" (took {in_band_at / 3600:.1f} h)"))
    nadir = min(r["glucose"] for r in after)
    assert nadir > 65.0, (
        f"The 4 U replacement bolus overshot to {nadir:.1f} mg/dL - a "
        "correctly sized dose must not cause a hypo")


def test_overdose_causes_hypoglycemia():
    """(m) Beta cells off, fasted, 10 U: glucagon and the liver fight back
    and LOSE. No secret floor - the acute danger must be real."""
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.step(600)
    sim.inject(10)
    sim.step(3 * 3600)
    low = min(r["glucose"] for r in sim.history())
    assert low < HYPO_LINE, (
        f"10 U into a fasted body only reached {low:.1f} mg/dL - an overdose "
        f"must drive glucose below {HYPO_LINE:.0f} (no secret rescue)")


def test_basal_holds_the_fasting_line():
    """(m) Beta cells off + 1.0 U/h basal: a 12 h fast stays inside 70-180.
    (Phase 2 already proved beta-off with NO basal climbs past 180.)"""
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.set_basal_rate(1.0)
    sim.step(12 * 3600)
    values = [r["glucose"] for r in sim.history()]
    assert max(values) < HYPER_LINE, (
        f"With 1.0 U/h basal a fasted type 1 body must stay under "
        f"{HYPER_LINE:.0f} mg/dL; it reached {max(values):.1f}")
    assert min(values) > HYPO_LINE, (
        f"1.0 U/h basal must not hypo a fasted body; it fell to "
        f"{min(values):.1f} mg/dL")


def test_doses_log_is_a_data_product():
    """(l) Bolus events are recorded state, not chart decoration."""
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    sim.step(60)
    sim.inject(4)
    sim.step(600)
    sim.inject(2)
    doses = sim.doses()
    assert [d["units"] for d in doses] == [4.0, 2.0]
    assert doses[0]["t"] < doses[1]["t"]
    assert all(set(d.keys()) == {"t", "units"} for d in doses)
    sim.reset()
    assert sim.doses() == [], "reset() must clear the dose log"


def test_dosing_rejects_nonsense():
    GlucoseSimulation = _dosing()
    sim = GlucoseSimulation()
    with pytest.raises(ValueError):
        sim.inject(0)
    with pytest.raises(ValueError):
        sim.inject(-3)
    with pytest.raises(ValueError):
        sim.set_basal_rate(-0.5)


def _scripted_dosing_run(GlucoseSimulation):
    """Exercises every Phase 3 control, for the determinism check (o)."""
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.step(1800)
    sim.set_basal_rate(1.0)
    sim.step(3600)
    sim.eat(60, 1.0)
    sim.inject(4)
    sim.step(3600)
    sim.inject(2)
    sim.set_basal_rate(0.5)
    sim.step(3600)
    return sim.history(), sim.doses()


def test_dosing_same_inputs_same_history():
    GlucoseSimulation = _dosing()
    assert (_scripted_dosing_run(GlucoseSimulation)
            == _scripted_dosing_run(GlucoseSimulation)), (
        "Two identical dosing runs diverged - injections and basal must be "
        "deterministic (kickoff SS2)")


def test_glucose_phase2_subset_unchanged_by_phase3():
    """(n) Zero injections, zero basal -> the Phase 2 fields of the Phase 2
    scripted run are byte-identical to the M10 baseline."""
    import hashlib
    import json
    GlucoseSimulation = _dosing()
    records = _scripted_glucose_run(GlucoseSimulation)
    subset = [{k: r[k] for k in PHASE2_GLUCOSE_FIELDS} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == GLUCOSE_PHASE2_SUBSET_SHA256, (
        "The glucose engine's Phase 2 behavior changed. Phase 3 must EXTEND "
        "Phase 2, never rebuild it (standing rule 3). If this change was "
        "ordered by the human, re-record the hash and say so in BUILDLOG.md.")


# ================= Phase 4: the closed-loop pump ==========================

# (s) sha256 of json.dumps of the PHASE 2+3 FIELD SUBSET of
# _scripted_dosing_run's records, recorded 2026-08-14 with M13 committed —
# the last Phase 3 state.
GLUCOSE_PHASE23_SUBSET_SHA256 = (
    "43f5e607bca69944d08cfca97b8e7e9e0890a82aa8a5c54ea90de5d12db37e93")

SEVERE_HYPO_LINE = 54.0
PUMP_FASTING_BAND = (70.0, 140.0)


def _pump():
    """The glucose engine once it speaks the pump API, or SKIP (M14)."""
    GlucoseSimulation = _glucose()
    if not hasattr(GlucoseSimulation, "set_pump_enabled"):
        pytest.skip("set_pump_enabled() doesn't exist yet - it arrives "
                    "at M14")
    return GlucoseSimulation


def test_pump_holds_the_fasting_line():
    """(q) Beta cells off + pump on: the artificial loop does what the
    biological one did - 12 h fasted, no manual help, inside 70-140."""
    GlucoseSimulation = _pump()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.set_pump_enabled(True)
    sim.step(12 * 3600)
    values = [r["glucose"] for r in sim.history()]
    lo, hi = min(values), max(values)
    assert PUMP_FASTING_BAND[0] < lo and hi < PUMP_FASTING_BAND[1], (
        f"Pump-managed fasted type 1 glucose ran [{lo:.1f}, {hi:.1f}] - it "
        f"must stay inside {PUMP_FASTING_BAND} with no manual dosing")


def test_pump_survives_a_meal_alone():
    """(q) No announcement, no manual bolus: the pump chases a 60 g meal
    through the subcutaneous lag. Honest spike, safe landing."""
    GlucoseSimulation = _pump()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.set_pump_enabled(True)
    sim.step(2 * 3600)                   # let the loop settle first
    t0 = sim.state()["t"]
    sim.eat(60, 1.0)
    sim.step(8 * 3600)
    after = [r for r in sim.history() if r["t"] > t0]
    peak = max(r["glucose"] for r in after)
    assert peak > PUMP_FASTING_BAND[1], (
        f"A 60 g meal only peaked at {peak:.1f} - the subcutaneous lag "
        "should make the spike real; something is secretly fast")
    nadir = min(r["glucose"] for r in after)
    assert nadir > 65.0, (
        f"The pump overshot the meal to {nadir:.1f} mg/dL - a sane gain "
        "must not hypo the patient it manages")
    peak_t = next(r["t"] for r in after if r["glucose"] == peak)
    back = next((r["t"] - t0 for r in after
                 if r["t"] > peak_t
                 and PUMP_FASTING_BAND[0] <= r["glucose"]
                 <= PUMP_FASTING_BAND[1]), None)
    assert back is not None and back <= 4 * 3600, (
        "The pump must bring a 60 g meal back into 70-140 within 4 h"
        + ("" if back is None else f" (took {back / 3600:.1f} h)"))


def test_blind_pump_overdelivers_into_hypo():
    """(q) Sensors dead: the pump infuses its set-point rate forever while
    the sensor-frozen alpha cells can't ramp glucagon. The artificial loop
    fails at the SAME box as the biological one - and the machine's blind
    failure mode is over-delivery, a crash below 54."""
    GlucoseSimulation = _pump()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.set_pump_enabled(True)
    sim.step(2 * 3600)                   # a working artificial loop...
    settled = sim.state()["glucose"]
    assert settled > 70.0, "Pump should be holding the line before blinding"
    sim.set_sensor_enabled(False)        # ...then the sensor dies
    t0 = sim.state()["t"]
    sim.step(3 * 3600)
    low = min(r["glucose"] for r in sim.history() if r["t"] > t0)
    assert low < SEVERE_HYPO_LINE, (
        f"A blind pump only reached {low:.1f} mg/dL in the 3 h after its "
        "sensor died - it must over-deliver into severe hypoglycemia (no "
        "secret safety net)")


def test_pump_rate_is_a_staircase():
    """(r) Decisions every 5 sim-minutes, held in between."""
    GlucoseSimulation = _pump()
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.set_pump_enabled(True)
    sim.step(1800)
    sim.eat(60, 1.0)                     # force the rate to move
    sim.step(2 * 3600)
    h = [r for r in sim.history() if r["pump_enabled"]]
    changes = [b["t"] for a, b in zip(h, h[1:])
               if b["pump_rate"] != a["pump_rate"]]
    assert len(changes) >= 3, (
        "The pump rate never moved through a meal - the controller is "
        "not controlling")
    gaps = [b - a for a, b in zip(changes, changes[1:])]
    assert all(g % 300.0 == 0 for g in gaps), (
        f"Pump rate changed off the 5-minute grid (gaps {sorted(set(gaps))[:5]}) "
        "- decisions must hold for 300 s (kickoff SS2: a staircase)")


def test_pump_off_zeroes_rate_and_restores_manual_basal():
    """(p) One basal source at a time, and pump_rate reads 0.0 when off."""
    GlucoseSimulation = _pump()
    sim = GlucoseSimulation()
    sim.set_basal_rate(1.0)
    sim.set_pump_enabled(True)
    sim.step(1200)
    assert sim.state()["pump_enabled"] is True
    assert sim.state()["pump_rate"] > 0.0
    sim.set_pump_enabled(False)
    sim.step(600)
    s = sim.state()
    assert s["pump_enabled"] is False and s["pump_rate"] == 0.0
    assert s["basal_rate"] == 1.0, (
        "Switching the pump off must leave the manual basal setting "
        "untouched - it was only overridden, not erased")


def _scripted_pump_run(GlucoseSimulation):
    """Exercises the pump on/off mid-run, for the determinism check (t)."""
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    sim.step(1800)
    sim.set_pump_enabled(True)
    sim.step(3600)
    sim.eat(60, 1.0)
    sim.step(3600)
    sim.set_pump_enabled(False)
    sim.set_basal_rate(1.0)
    sim.step(1800)
    sim.set_pump_enabled(True)
    sim.step(1800)
    return sim.history(), sim.doses()


def test_pump_same_inputs_same_history():
    GlucoseSimulation = _pump()
    assert (_scripted_pump_run(GlucoseSimulation)
            == _scripted_pump_run(GlucoseSimulation)), (
        "Two identical pump runs diverged - the pump must be deterministic "
        "(kickoff SS2)")


def test_glucose_phase23_subset_unchanged_by_phase4():
    """(s) Pump never enabled -> the Phase 2+3 fields of the Phase 3
    scripted dosing run are byte-identical to the M13 baseline."""
    import hashlib
    import json
    GlucoseSimulation = _pump()
    records, _ = _scripted_dosing_run(GlucoseSimulation)
    subset = [{k: r[k] for k in PHASE23_GLUCOSE_FIELDS} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == GLUCOSE_PHASE23_SUBSET_SHA256, (
        "The glucose engine's Phase 2+3 behavior changed. Phase 4 must "
        "EXTEND, never rebuild (standing rule 3). If this change was "
        "ordered by the human, re-record the hash and say so in "
        "BUILDLOG.md.")


# ================= Phase 5: disease knobs =================================

T2_SENSITIVITY = 0.05    # the preset's value; pins below hold at this knob


def _fever():
    """The thermo engine once it speaks set_fever, or SKIP (M17)."""
    Simulation = _engine()
    if not hasattr(Simulation, "set_fever"):
        pytest.skip("set_fever() doesn't exist yet - it arrives at M17")
    return Simulation


def _resistance():
    """The glucose engine once it has sensitivity, or SKIP (M17)."""
    GlucoseSimulation = _glucose()
    if not hasattr(GlucoseSimulation, "set_insulin_sensitivity"):
        pytest.skip("set_insulin_sensitivity() doesn't exist yet - M17")
    return GlucoseSimulation


def test_fever_is_a_moved_set_point_not_a_broken_loop():
    """(v) The loop still regulates - it just defends the wrong number."""
    Simulation = _fever()
    sim = Simulation()
    sim.step(600)
    sim.set_fever(2.0)
    sim.step(2 * 3600)
    settled = sim.state()["core_temp"]
    assert abs(settled - 39.0) <= 0.5, (
        f"With a 2.0 degC fever the loop must defend 39 +/- 0.5; core is "
        f"{settled:.2f} - either the offset is dead or regulation broke")
    tail = [r["core_temp"] for r in sim.history()[-1800:]]
    assert max(tail) - min(tail) < 0.3, (
        "Fever core temp is not HOLDING - the loop must still regulate, "
        "just at the shifted number")
    assert Simulation.SET_POINT == 37.0, (
        "SET_POINT itself moved - fever must be runtime state, never a "
        "change to the constant the whole lesson hangs on")


def test_fever_onset_brings_chills_while_already_hot():
    """(v) The freaky fact: shivering at 38 degC, because 38 is BELOW the
    new set point. This is why fevers start with chills."""
    Simulation = _fever()
    sim = Simulation()
    sim.step(600)
    sim.set_fever(2.0)
    sim.step(2 * 3600)
    onset = [r for r in sim.history() if r["t"] > 600]
    chills = [r for r in onset
              if r["core_temp"] > 37.2 and r["shiver"] > 0.05]
    assert len(chills) > 60, (
        f"Only {len(chills)} ticks of shivering-while-hot during fever "
        "onset - the chills must be a visible stretch, not a blip")


def test_breaking_a_fever_brings_sweats_while_cooling():
    """(v) Clear the fever at 39: suddenly 39 is 2 degrees TOO HOT and
    the loop sweats it back down."""
    Simulation = _fever()
    sim = Simulation()
    sim.step(600)
    sim.set_fever(2.0)
    sim.step(2 * 3600)
    sim.set_fever(0.0)
    cleared_at = sim.state()["t"]
    sim.step(2 * 3600)
    cooling = [r for r in sim.history() if r["t"] > cleared_at]
    sweats = [r for r in cooling
              if r["core_temp"] > 37.2 and r["sweat"] > 0.05]
    assert len(sweats) > 60, (
        f"Only {len(sweats)} ticks of sweating-while-hot after the fever "
        "broke - the classic drenched-sheets cooldown must be visible")
    assert abs(sim.state()["core_temp"] - 37.0) <= 0.5, (
        "Two hours after the fever broke, core must be back near 37")


def test_insulin_resistance_shows_the_type2_signature():
    """(w) BOTH numbers high at once: glucose above the band WITH insulin
    pouring out - beta cells shouting at deaf tissues, and the
    unrestrained alpha cells driving the liver. Contrast with type 1's
    insulin of exactly zero."""
    GlucoseSimulation = _resistance()
    sim = GlucoseSimulation()
    sim.set_insulin_sensitivity(T2_SENSITIVITY)
    sim.step(8 * 3600)
    s = sim.state()
    assert s["glucose"] > 110.0, (
        f"Fasted type 2 glucose is {s['glucose']:.0f}; resistance at "
        f"sensitivity {T2_SENSITIVITY} must park it above 110")
    assert s["insulin"] >= 0.5, (
        f"Fasted type 2 insulin is {s['insulin']:.2f}; the signature is "
        "HIGH insulin with high glucose (compensating beta cells)")
    assert s["glucagon"] >= 0.25, (
        f"Fasted type 2 glucagon is {s['glucagon']:.2f}; the deaf "
        "paracrine brake must leave it inappropriately high")
    t0 = s["t"]
    sim.eat(60, 1.0)
    sim.step(3 * 3600)
    post = [r for r in sim.history() if r["t"] > t0]
    peak = max(r["glucose"] for r in post)
    assert peak > 250.0, (
        f"A 60 g meal peaked at {peak:.0f} in a type 2 body; deaf "
        "tissues must let it climb past 250")
    final = sim.state()["glucose"]
    assert final > 110.0, (
        f"3 h after the meal glucose is {final:.0f}; a type 2 body must "
        "still be above 110 - tall and slow is the shape")


def test_disease_knob_validation():
    """(x)"""
    GlucoseSimulation = _resistance()
    sim = GlucoseSimulation()
    for bad in (0.0, -0.2, 1.5):
        with pytest.raises(ValueError):
            sim.set_insulin_sensitivity(bad)
    sim.set_insulin_sensitivity(1.0)     # healthy is legal
    Simulation = _fever()
    Simulation().set_fever(-1.0)         # any float is legal (anesthesia!)


def _scripted_disease_run():
    """Exercises both knobs mid-run, for the determinism check (z)."""
    Simulation = _fever()
    GlucoseSimulation = _resistance()
    t = Simulation()
    t.step(600)
    t.set_fever(1.5)
    t.step(3600)
    t.set_fever(0.0)
    t.step(600)
    g = GlucoseSimulation()
    g.step(600)
    g.set_insulin_sensitivity(0.4)
    g.eat(60, 1.0)
    g.step(3600)
    g.set_insulin_sensitivity(1.0)
    g.step(600)
    return t.history(), g.history()


def test_disease_knobs_are_deterministic():
    assert _scripted_disease_run() == _scripted_disease_run(), (
        "Two identical disease-knob runs diverged (kickoff SS2)")


# ================= Phase 6: the water/ADH loop ============================

WATER_SET_POINT = 290.0
WATER_BAND = (285.0, 295.0)
DEHYDRATION_LINE = 305.0
OVERHYDRATION_LINE = 280.0

# Kickoff Phase 6 SS5: the frozen water record shape.
WATER_FIELDS = {
    "t",                # sim time, seconds
    "osmolarity",       # mOsm/L - the controlled variable
    "water_liters",     # L of body water
    "gut_water",        # mL drunk but not yet absorbed
    "exercise",         # bool - sweating (hypotonic loss)
    "error",            # osmolarity - set point, as the receptors see it
    "adh",              # hormone activity, 0..1
    "thirst",           # drive to drink, 0..1
    "urine_rate",       # mL/min leaving via the kidneys
    "urine_osm",        # mOsm/L of that urine - concentrated vs dilute
    "adh_enabled",      # the break-the-loop toggles (armed at M22's UI,
    "kidney_enabled",   # modeled from M20 so the physiology tests below
    "water_access",     # can prove they matter)
    "sensor_enabled",
    "adh_override",     # grown at M31 (Phase 9): the SIADH knob — appended,
                        # like every record growth since M12
    "tubular_load",     # grown at M37 (Phase 10): mOsm/min arriving in the
                        # tubule from ANOTHER loop; 0.0 = uncoupled
    "foreign_osm",      # grown at M38: mOsm/L of PLASMA osmoles another
}                       # loop owns (the sugar); 0.0 = uncoupled


def _water():
    """Import the water engine, or SKIP loudly if not built yet (M20)."""
    if not (ENGINE_PKG / "water.py").exists():
        pytest.skip("engine/water.py doesn't exist yet - it arrives at M20")
    from engine.water import WaterSimulation
    return WaterSimulation


def test_water_set_point_is_290():
    WaterSimulation = _water()
    assert WaterSimulation.SET_POINT == WATER_SET_POINT


def test_water_records_have_the_frozen_fields():
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.step(5)
    records = sim.history()
    assert records, "history() returned nothing after stepping"
    for r in (records[0], records[-1], sim.state()):
        assert set(r.keys()) == WATER_FIELDS, (
            f"Record fields {sorted(r.keys())} != frozen set "
            f"{sorted(WATER_FIELDS)} (Phase 6 kickoff SS5)")


def test_water_state_is_newest_record():
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.step(10)
    assert sim.state() == sim.history()[-1]


def test_resting_body_holds_band_by_drinking():
    """(bb) The loop closes through BEHAVIOR: nobody touches anything for
    12 h and osmolarity stays in the band because the body drinks."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.step(12 * 3600)
    values = [r["osmolarity"] for r in sim.history()]
    bad = [v for v in values if not
           (WATER_BAND[0] <= v <= WATER_BAND[1])]
    assert not bad, (
        f"Resting osmolarity left 285-295 mOsm/L ({len(bad)} of "
        f"{len(values)} ticks; worst "
        f"{max(bad, key=lambda v: abs(v - WATER_SET_POINT)):.1f})")
    assert any(d["auto"] for d in sim.drinks()), (
        "12 h passed and the body never auto-drank - the behavioral "
        "effector must be doing the work, not initial conditions")


def _time_to_dehydration(sim, hours):
    sim.step(int(hours * 3600))
    return next((r["t"] for r in sim.history()
                 if r["osmolarity"] > DEHYDRATION_LINE), None)


def test_desert_dehydrates_despite_conservation():
    """(bb) No water + sweating: ADH pins urine near the floor and the
    body STILL dehydrates - the kidney can only slow losses, never
    refill. No secret water."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.set_effector_enabled("access", False)
    sim.set_exercise(True)
    crossed = _time_to_dehydration(sim, 5)
    assert crossed is not None and 2.5 * 3600 <= crossed <= 5 * 3600, (
        "In the desert osmolarity must pass 305 between 2.5 and 5 h"
        + ("" if crossed is None else f" (crossed at {crossed / 3600:.1f} h)"
           ) + " - too fast means ADH isn't conserving, too slow means "
        "the failure isn't visible in a lesson")
    last_hour = sim.history()[-3600:]
    assert max(r["urine_rate"] for r in last_hour) <= 1.0, (
        "Dehydrating urine must be pinned near the floor - ADH at full "
        "conservation")


def test_central_di_compensates_through_the_water_bottle():
    """(bb) ADH off but water within reach: urine floods AND the person
    survives, because thirst closes the loop the hormone abandoned."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.set_effector_enabled("adh", False)
    sim.step(6 * 3600)
    records = sim.history()
    assert max(r["osmolarity"] for r in records) < 300.0, (
        "With water available, central DI must stay under 300 mOsm/L - "
        "drinking compensates")
    litres = sum(r["urine_rate"] for r in records) / 60.0 / 1000.0
    assert litres > 3.0, (
        f"Central DI passed only {litres:.1f} L of urine in 6 h - the "
        "polyuria must be dramatic (real DI floods 15+ L/day)")


def test_di_plus_desert_is_the_killer_combination():
    """(bb) Break the hormone AND the behavior: dehydration arrives far
    faster than with conservation intact."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.set_effector_enabled("adh", False)
    sim.set_effector_enabled("access", False)
    sim.set_exercise(True)
    crossed = _time_to_dehydration(sim, 3)
    assert crossed is not None and crossed <= 2.5 * 3600, (
        "DI plus the desert must pass 305 within 2.5 h"
        + ("" if crossed is None else f" (took {crossed / 3600:.1f} h)"))


def test_overhydration_reflex_dumps_dilute_urine():
    """(bb) A 3 L chug: ADH dies, the kidneys flood dilute, the band is
    regained within 6 h."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.step(3600)
    t0 = sim.state()["t"]
    sim.drink(3000)
    sim.step(6 * 3600)
    after = [r for r in sim.history() if r["t"] > t0]
    nadir = min(r["osmolarity"] for r in after)
    assert nadir < OVERHYDRATION_LINE, (
        f"3 L only diluted osmolarity to {nadir:.1f}; the dip below 280 "
        "is the stimulus the class must see")
    flooding = [r for r in after
                if r["urine_rate"] > 8.0 and r["urine_osm"] < 150.0]
    assert len(flooding) > 600, (
        f"Only {len(flooding)} ticks of dilute flooding after the chug - "
        "the kidneys must visibly dump the excess")
    assert any(r["adh"] < 0.05 for r in after), (
        "ADH never shut off after the chug")
    back = next((r["t"] - t0 for r in after
                 if r["osmolarity"] >= WATER_BAND[0]
                 and r["t"] - t0 > 1800), None)
    assert back is not None and back <= 6 * 3600, (
        "Osmolarity must climb back into the band within 6 h of the chug")


def test_conserve_first_drink_second():
    """(bb) The staged thresholds: a stretch where the hormone is already
    working while thirst hasn't woken - the cheap response leads."""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.set_effector_enabled("access", False)   # let osmolarity drift up
    sim.step(6 * 3600)
    staged = [r for r in sim.history()
              if r["adh"] > 0.3 and r["thirst"] == 0.0]
    assert len(staged) > 600, (
        f"Only {len(staged)} ticks with ADH > 0.3 and thirst still 0 - "
        "conserve-first/drink-second must be a visible stage, not a blip")


def test_drinks_log_is_a_data_product():
    """(cc)"""
    WaterSimulation = _water()
    sim = WaterSimulation()
    sim.step(60)
    sim.drink(500)
    manual = [d for d in sim.drinks() if not d["auto"]]
    assert len(manual) == 1 and manual[0]["ml"] == 500.0
    assert all(set(d.keys()) == {"t", "ml", "auto"} for d in sim.drinks())
    sim.reset()
    assert sim.drinks() == [], "reset() must clear the drink log"


def test_water_rejects_nonsense():
    WaterSimulation = _water()
    sim = WaterSimulation()
    with pytest.raises(ValueError):
        sim.drink(0)
    with pytest.raises(ValueError):
        sim.drink(-100)
    with pytest.raises(ValueError):
        sim.eat_salt(-5)
    with pytest.raises(KeyError):
        sim.set_effector_enabled("bladder", False)


def _scripted_water_run(WaterSimulation):
    """Exercises every control, for the determinism check."""
    sim = WaterSimulation()
    sim.step(1800)
    sim.eat_salt(300)
    sim.step(3600)
    sim.drink(1000)
    sim.set_exercise(True)
    sim.step(3600)
    sim.set_exercise(False)
    sim.set_effector_enabled("adh", False)
    sim.step(3600)
    sim.set_effector_enabled("adh", True)
    sim.set_effector_enabled("access", False)
    sim.step(1800)
    return sim.history(), sim.drinks()


def test_water_same_inputs_same_history():
    WaterSimulation = _water()
    assert (_scripted_water_run(WaterSimulation)
            == _scripted_water_run(WaterSimulation)), (
        "The water sim must be deterministic (kickoff SS2)")


# ================= Phase 7: scenario challenges ===========================
# App-level machinery only (kickoff SS2): a table, a pure evaluator, no
# engine changes — the regression hashes above prove the engines idle.


def _challenges():
    """Import the challenge layer, or SKIP loudly if not built (M24)."""
    import app as vital_app
    if not hasattr(vital_app, "CHALLENGES"):
        pytest.skip("CHALLENGES doesn't exist yet - it arrives at M24")
    return vital_app


def test_challenge_table_shape():
    """(a) Every entry carries what the card, report, and tests need."""
    vital_app = _challenges()
    required = {"title", "story", "goal", "duration_s", "speed",
                "setup", "metrics"}
    assert vital_app.CHALLENGES, "the challenge table is empty"
    for loop, entries in vital_app.CHALLENGES.items():
        assert loop in vital_app.runners, f"unknown loop {loop!r}"
        for cid, entry in entries.items():
            missing = required - set(entry)
            assert not missing, f"{loop}/{cid} lacks {sorted(missing)}"
            assert entry["duration_s"] > 0, f"{loop}/{cid} duration"
            assert entry["metrics"] in vital_app.EVALUATORS, (
                f"{loop}/{cid} names evaluator {entry['metrics']!r} "
                "which doesn't exist")


def _glucose_window(values, beta_off=True):
    """Craft a minimal challenge-window history for the evaluator."""
    return [{"t": float(i), "glucose": g, "beta_enabled": not beta_off}
            for i, g in enumerate(values)]


def test_t1_shift_evaluator_arithmetic():
    """(b) Exact percentages and extremes from a crafted history —
    test the arithmetic, not the vibes."""
    vital_app = _challenges()
    ev = vital_app.EVALUATORS["t1_shift"]
    # 80 ticks in range at 100, 20 out at 200 -> exactly 80 %
    report = ev(_glucose_window([100.0] * 80 + [200.0] * 20))
    rows = {r["label"]: r for r in report["rows"]}
    in_range = rows["time in 70-180 mg/dL"]
    assert "80%" in in_range["value"] and in_range["met"] is True
    assert rows["lowest glucose"]["met"] is True
    assert report["met"] is True
    # 60 % in range -> the target line must fail
    report = ev(_glucose_window([100.0] * 60 + [200.0] * 40))
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["time in 70-180 mg/dL"]["met"] is False
    assert report["met"] is False
    # one dip to 60 -> the hypo line must fail even at 99 % in range
    report = ev(_glucose_window([100.0] * 99 + [60.0]))
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["lowest glucose"]["met"] is False
    assert report["met"] is False


def test_cold_store_evaluator_arithmetic():
    """(b) The heat-budget challenge grades ends, floors, and the
    exhaustion cap exactly."""
    vital_app = _challenges()
    ev = vital_app.EVALUATORS["cold_store"]

    def rec(core, ex):
        return {"core_temp": core, "exercise": ex, "env_temp": -10.0,
                "shiver_enabled": False, "vaso_enabled": False}

    # 40% duty, ends warm, floor safe -> met
    window = [rec(36.5, i % 5 < 2) for i in range(100)]
    report = ev(window)
    assert report["met"] is True
    # 60% duty -> the exhaustion cap fails even though the body is warm
    window = [rec(36.5, i % 5 < 3) for i in range(100)]
    report = ev(window)
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["exercise used"]["met"] is False
    assert report["met"] is False
    # warming the room -> the door line fails
    window = [rec(36.5, False) for _ in range(99)]
    window.append({**rec(36.5, False), "env_temp": 22.0})
    rows = {r["label"]: r for r in ev(window)["rows"]}
    assert rows["the door stayed shut (room at -5 °C or colder)"][
        "met"] is False


def test_aid_station_evaluator_arithmetic():
    """(b) The osmoreceptor-replacement challenge grades range time and
    the overhydration kill exactly."""
    vital_app = _challenges()
    ev = vital_app.EVALUATORS["aid_station"]

    def rec(osm):
        return {"osmolarity": osm, "exercise": True,
                "sensor_enabled": False, "urine_rate": 3.0}

    # 95% inside -> met
    report = ev([rec(290.0)] * 95 + [rec(302.0)] * 5)
    assert report["met"] is True
    # 85% inside -> the range target fails
    report = ev([rec(290.0)] * 85 + [rec(302.0)] * 15)
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["time inside 280-300 mOsm/L"]["met"] is False
    # one dip to 273 -> the overhydration line fails at 99% in range
    report = ev([rec(290.0)] * 99 + [rec(273.0)])
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["lowest osmolarity"]["met"] is False
    assert report["met"] is False


def test_t1_shift_integrity_line():
    """(c) Flip the guarded flag mid-window and the report says so."""
    vital_app = _challenges()
    ev = vital_app.EVALUATORS["t1_shift"]
    window = _glucose_window([100.0] * 50)
    window += [{"t": 50.0 + i, "glucose": 100.0, "beta_enabled": True}
               for i in range(50)]
    report = ev(window)
    rows = {r["label"]: r for r in report["rows"]}
    integrity = rows["beta cells stayed off"]
    assert integrity["met"] is False, (
        "Switching the pancreas back on mid-shift must be REPORTED")
    assert report["met"] is False


# ================= Phase 8: the game layer ================================
# Still app-level only (kickoff SS0: "no engine file changes in this phase
# at all") — the regression guards above are what prove the engines idle.
# The evaluator says WHAT HAPPENED; the scorer says WHAT IT'S WORTH. Two
# functions, two responsibilities, both pure, both tested on crafted rows.


def _game():
    """Import the game layer, or SKIP loudly if not built yet (M26)."""
    import app as vital_app
    if not hasattr(vital_app, "score_report"):
        pytest.skip("score_report doesn't exist yet - it arrives at M26")
    return vital_app


def _attempts_module():
    """Import the attempts log, or SKIP loudly if not built yet (M26)."""
    if not (ROOT / "attempts.py").exists():
        pytest.skip("attempts.py doesn't exist yet - it arrives at M26")
    import attempts
    return attempts


# Kickoff SS5: the frozen fields of one attempt. Fields are added by
# APPENDING (M28's diagnosis answer, M44's period), never by renaming —
# a worksheets phase or a gradebook export reads this file, not a
# screenshot.
ATTEMPT_FIELDS = {"id", "wall_time", "loop", "mode", "name", "label",
                  "points", "medal", "met", "rows", "period"}

# One crafted record per evaluator, enough for it to produce every row.
CRAFTED_RECORD = {
    "t1_shift": {"t": 0.0, "glucose": 100.0, "beta_enabled": False},
    "cold_store": {"core_temp": 36.5, "exercise": False, "env_temp": -10.0,
                   "shiver_enabled": False, "vaso_enabled": False},
    "aid_station": {"osmolarity": 290.0, "exercise": True,
                    "sensor_enabled": False, "urine_rate": 3.0},
    # M29's crisis variants. `t` matters here: a stop row reports the
    # sim-time a line was crossed at.
    "blast_freezer": {"t": 1.0, "core_temp": 37.0, "exercise": False,
                      "env_temp": -5.0, "shiver_enabled": False,
                      "vaso_enabled": False},
    "crisis_shift": {"t": 1.0, "glucose": 100.0, "beta_enabled": False},
    "race_day": {"t": 1.0, "osmolarity": 290.0, "exercise": True,
                 "sensor_enabled": False, "urine_rate": 3.0},
    # M41's coupled body. Both loops' numbers, because the ward
    # evaluator reads both — and `water_access` False, because the
    # admission's integrity rule is that the patient still cannot
    # drink for themselves.
    "ward_round": {"t": 1.0, "glucose": 130.0, "osmolarity": 290.0,
                   "renal_loss": 0.0, "urine_rate": 1.0,
                   "water_access": False},
    "ward_crisis": {"t": 1.0, "glucose": 130.0, "osmolarity": 290.0,
                    "renal_loss": 0.0, "urine_rate": 1.0,
                    "water_access": False},
}


def _crafted_report(vital_app, metrics, fraction, integrity_ok=True):
    """A report whose every graded row earns exactly `fraction` of its
    weight — so the expected points are arithmetic, not vibes."""
    rows = []
    for key, rule in vital_app.SCORING[metrics].items():
        if rule.get("integrity"):
            rows.append({"key": key, "label": key, "value": "crafted",
                         "met": integrity_ok, "n": None})
        else:
            span = rule["full_at"] - rule["zero_at"]
            rows.append({"key": key, "label": key, "value": "crafted",
                         "met": True, "n": rule["zero_at"] + fraction * span})
    return {"met": integrity_ok, "rows": rows}


# ------------------------------------------------------ (ee) the scorer

def test_score_report_grades_exactly():
    """Fed a crafted report, the scorer returns exact points."""
    vital_app = _game()
    for loop, entries in vital_app.CHALLENGES.items():
        for cid, entry in entries.items():
            metrics = entry["metrics"]
            full = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, 1.0))
            assert full["max"] == 100, (
                f"{loop}/{cid} scores out of {full['max']}, not 100 - every "
                "challenge is out of 100 so medals mean the same thing "
                "everywhere")
            assert full["points"] == pytest.approx(100.0), (
                f"{loop}/{cid}: a run at every ceiling must score full marks")
            half = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, 0.5))
            assert half["points"] == pytest.approx(50.0), (
                f"{loop}/{cid}: halfway between floor and ceiling on every "
                f"row must score exactly half, got {half['points']}")
            none = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, 0.0))
            assert none["points"] == pytest.approx(0.0), (
                f"{loop}/{cid}: a run at every floor must score zero")
            # Overshooting the ceiling earns no bonus; undershooting the
            # floor is not negative - a graded row is clamped to 0..weight.
            over = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, 3.0))
            under = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, -2.0))
            assert over["points"] == pytest.approx(100.0)
            assert under["points"] == pytest.approx(0.0)


def test_score_report_is_pure():
    """Same input -> same output, and the report is never mutated."""
    import json
    vital_app = _game()
    entry = vital_app.CHALLENGES["glucose"]["t1_shift"]
    report = _crafted_report(vital_app, entry["metrics"], 0.7)
    before = json.dumps(report, sort_keys=True)
    first = vital_app.score_report(entry, report)
    second = vital_app.score_report(entry, report)
    assert first == second, "the scorer is not a pure function"
    assert json.dumps(report, sort_keys=True) == before, (
        "score_report() mutated the report it was given - the Phase 7 card "
        "must come out exactly as the evaluator wrote it")


def test_score_report_tiers_on_the_thresholds():
    """The medal is a lookup on points, boundaries inclusive."""
    vital_app = _game()
    entry = {"metrics": "t1_shift",
             "medals": {"gold": 90, "silver": 75, "bronze": 55}}
    metrics = entry["metrics"]

    def medal_at(fraction):
        return vital_app.score_report(
            entry, _crafted_report(vital_app, metrics, fraction))["medal"]

    assert medal_at(1.0) == "gold"          # 100 points
    assert medal_at(0.9) == "gold"          # exactly 90 - the line counts
    assert medal_at(0.8) == "silver"
    assert medal_at(0.75) == "silver"       # exactly 75
    assert medal_at(0.6) == "bronze"
    assert medal_at(0.55) == "bronze"       # exactly 55
    assert medal_at(0.5) is None            # 50 - no medal, still a report


def test_integrity_failure_zeroes_the_run():
    """Switching a broken part back on isn't a deduction, it's no score."""
    vital_app = _game()
    for loop, entries in vital_app.CHALLENGES.items():
        for cid, entry in entries.items():
            metrics = entry["metrics"]
            if not any(r.get("integrity")
                       for r in vital_app.SCORING[metrics].values()):
                continue
            score = vital_app.score_report(
                entry, _crafted_report(vital_app, metrics, 1.0,
                                       integrity_ok=False))
            assert score["points"] == 0 and score["medal"] is None, (
                f"{loop}/{cid}: a perfect run that cheated must score 0 "
                f"with no medal, got {score['points']} / {score['medal']}")
            assert score["zeroed"], (
                f"{loop}/{cid}: a zeroed run must SAY why, in words")


def test_scoring_keys_match_the_rows_the_evaluator_emits():
    """A typo in a scoring key would silently score zero forever."""
    vital_app = _game()
    for metrics, evaluator in vital_app.EVALUATORS.items():
        report = evaluator([CRAFTED_RECORD[metrics]])
        keys = [r["key"] for r in report["rows"]]
        assert len(keys) == len(set(keys)), f"{metrics}: duplicate row keys"
        unknown = set(vital_app.SCORING[metrics]) - set(keys)
        assert not unknown, (
            f"SCORING[{metrics!r}] scores rows {sorted(unknown)} that the "
            "evaluator never emits")


# ------------------------------------------------------- (ff) the medals

def test_every_challenge_has_ordered_medals():
    vital_app = _game()
    for loop, entries in vital_app.CHALLENGES.items():
        for cid, entry in entries.items():
            medals = entry.get("medals")
            assert medals and set(medals) == {"gold", "silver", "bronze"}, (
                f"{loop}/{cid} must carry all three medal thresholds")
            gold, silver, bronze = (medals["gold"], medals["silver"],
                                    medals["bronze"])
            assert gold > silver > bronze, (
                f"{loop}/{cid} medals must be strictly ordered gold > "
                f"silver > bronze, got {medals}")
            top = vital_app.score_report(entry, {"met": True, "rows": []})
            assert 0 < bronze and gold <= top["max"], (
                f"{loop}/{cid}: thresholds must sit inside 0..{top['max']}")


# -------------------------------------------------- (gg) the attempts log

def _attempt(n=1):
    return {"id": n, "wall_time": "2026-08-16T09:30:00", "loop": "glucose",
            "mode": "challenge", "name": "t1_shift", "label": "Team 3",
            "points": 88.0, "medal": "silver", "met": True,
            "rows": [{"key": "in_range", "label": "time in range",
                      "value": "88%", "met": True, "n": 88.0}]}


def test_attempts_log_round_trips(tmp_path):
    attempts = _attempts_module()
    path = tmp_path / "attempts.json"
    records = [_attempt(1), _attempt(2)]
    attempts.save(records, path)
    assert attempts.load(path) == records, (
        "an attempt did not survive save -> load unchanged")
    # Atomic write: temp file + replace, nothing left lying around.
    assert [p.name for p in tmp_path.iterdir()] == ["attempts.json"]


def test_attempts_append_assigns_ids_and_persists(tmp_path):
    attempts = _attempts_module()
    path = tmp_path / "attempts.json"
    first = attempts.append({**_attempt(), "id": None}, path)
    second = attempts.append({**_attempt(), "id": None}, path)
    assert first["id"] == 1 and second["id"] == 2, (
        "append() must assign the next id itself")
    assert len(attempts.load(path)) == 2


def test_attempts_missing_file_starts_empty(tmp_path):
    attempts = _attempts_module()
    assert attempts.load(tmp_path / "not_there.json") == [], (
        "a missing log is a fresh classroom, not a crash")


def test_attempts_corrupt_file_is_loud_and_preserved(tmp_path):
    attempts = _attempts_module()
    path = tmp_path / "attempts.json"
    path.write_text("{ half a file, written as the power went ou",
                    encoding="utf-8")
    assert attempts.load(path) == [], "a corrupt log must not crash the class"
    warning = attempts.last_warning()
    assert warning and "attempts.json" in warning, (
        "a corrupt log must produce a LOUD plain-English warning naming the "
        f"file, got {warning!r}")
    assert list(tmp_path.glob("*.corrupt.json")), (
        "the corrupt file must be kept aside, not silently overwritten")


def test_attempts_unreadable_log_is_never_overwritten(tmp_path):
    """A log we can't READ may be the morning's scores.

    Junk we can read is safe to set aside; a file we never saw inside is
    not. Antivirus or an open editor locking it for a moment must not
    cost a class its results, so the app starts empty, says so, and
    refuses to write until the file can be read.
    """
    attempts = _attempts_module()
    path = tmp_path / "attempts.json"
    path.mkdir()                      # exists; unreadable as a file
    assert attempts.load(path) == [], "an unreadable log must not crash"
    warning = attempts.last_warning()
    assert warning and "could not be read" in warning, (
        f"an unreadable log must say so plainly, got {warning!r}")
    assert not list(tmp_path.glob("*.corrupt.json")), (
        "an unreadable file must be left exactly where it is")
    with pytest.raises(attempts.AttemptsError):
        attempts.save([_attempt()], path)


def test_attempts_log_caps_at_the_most_recent_500(tmp_path):
    attempts = _attempts_module()
    assert attempts.MAX_ATTEMPTS == 500
    path = tmp_path / "attempts.json"
    attempts.save([{**_attempt(i), "id": i} for i in range(1, 621)], path)
    kept = attempts.load(path)
    assert len(kept) == 500, f"the cap kept {len(kept)} attempts"
    assert kept[0]["id"] == 121 and kept[-1]["id"] == 620, (
        "the cap must drop the OLDEST attempts, never the newest")


def test_attempts_write_failure_raises_instead_of_pretending(tmp_path):
    attempts = _attempts_module()
    blocked = tmp_path / "attempts.json"
    blocked.mkdir()          # a directory where the file should be
    with pytest.raises(attempts.AttemptsError):
        attempts.save([_attempt()], blocked)


# ------------------------------------------- (hh) the attempt data product

def test_attempt_record_has_the_frozen_fields():
    import datetime
    vital_app = _game()
    entry = vital_app.CHALLENGES["glucose"]["t1_shift"]
    report = vital_app.EVALUATORS["t1_shift"]([CRAFTED_RECORD["t1_shift"]])
    score = vital_app.score_report(entry, report)
    att = vital_app.build_attempt("glucose", "t1_shift", report, score)
    missing = ATTEMPT_FIELDS - set(att)
    assert not missing, f"an attempt lacks the frozen fields {sorted(missing)}"
    assert att["mode"] == "challenge"
    assert att["rows"] == report["rows"], (
        "the attempt stores the report card VERBATIM - a later phase reads "
        "this file, not a screenshot")
    datetime.datetime.fromisoformat(att["wall_time"])   # raises if not ISO


# ================= M27: head-to-head =======================================
# Two teams, the same deterministic challenge, and the log put side by
# side. Nothing new is computed here — every number was already a data
# product, which is exactly what makes the comparison fair.


def _h2h():
    """Import the head-to-head layer, or SKIP loudly (M27)."""
    import app as vital_app
    if not hasattr(vital_app, "compare_attempts"):
        pytest.skip("compare_attempts doesn't exist yet - it arrives at M27")
    return vital_app


def _run(points, medal, met, cells, label="Team A", rid=1,
         when="2026-08-16T10:00:00", loop="water", name="aid_station"):
    """One logged attempt; cells are (key, value, met, points, max)."""
    return {
        "id": rid, "wall_time": when, "loop": loop, "mode": "challenge",
        "name": name, "label": label, "points": points, "medal": medal,
        "met": met,
        "rows": [{"key": k, "label": k, "value": v, "met": m, "n": None}
                 for k, v, m, _, _ in cells],
        "score_rows": [{"key": k, "label": k, "points": p, "max": mx}
                       for k, _, _, p, mx in cells if p is not None],
        "zeroed": None,
    }


def _pair():
    a = _run(80, "silver", True,
             [("in_band", "95%", True, 50.0, 60),
              ("lowest", "287.4", True, 20.0, 20),
              ("moving", "yes", True, None, None)])
    b = _run(66, None, False,
             [("in_band", "82%", False, 32.0, 60),
              ("lowest", "290.0", True, 20.0, 20),
              ("moving", "no", False, None, None)],
             label="Team B", rid=2, when="2026-08-16T10:30:00")
    return a, b


# ------------------------------------------------------- (ii) team labels

def test_team_label_is_tidied_and_capped():
    vital_app = _h2h()
    clean = vital_app.clean_label
    assert clean("  Period 2   Red  ") == "Period 2 Red", (
        "a team name is tidied, not stored with the teacher's stray spaces")
    assert clean("") is None and clean("    ") is None
    assert clean(None) is None and clean(42) is None
    assert len(clean("T" * 500)) == vital_app.MAX_LABEL_CHARS, (
        "a label must be capped short server-side, not just in the box")


# -------------------------------------------------------- (jj) the compare

def test_compare_attempts_is_pure_and_symmetric():
    import json
    vital_app = _h2h()
    a, b = _pair()
    before = json.dumps([a, b], sort_keys=True)
    ab = vital_app.compare_attempts(a, b)
    ba = vital_app.compare_attempts(b, a)
    assert json.dumps([a, b], sort_keys=True) == before, (
        "compare_attempts() mutated the log records it was handed")
    assert ab == vital_app.compare_attempts(a, b), "the compare is not pure"
    assert ab["winner"] == "a" and ba["winner"] == "b"
    wins = {r["key"]: r["winner"] for r in ab["rows"]}
    assert wins["in_band"] == "a"      # 50.0 beats 32.0
    assert wins["lowest"] is None      # 20 == 20: a tie is a tie
    assert wins["moving"] == "a"       # no points -> the honest run wins
    flip = {r["key"]: r["winner"] for r in ba["rows"]}
    mirror = {"a": "b", "b": "a", None: None}
    for key, side in wins.items():
        assert flip[key] == mirror[side], (
            f"row {key!r} changed its mind when the teams swapped sides")


def test_compare_carries_both_teams_numbers_row_for_row():
    """The class must see WHERE one team beat the other, not just that."""
    vital_app = _h2h()
    a, b = _pair()
    cmp = vital_app.compare_attempts(a, b)
    row = next(r for r in cmp["rows"] if r["key"] == "in_band")
    assert row["a"]["value"] == "95%" and row["b"]["value"] == "82%"
    assert row["a"]["points"] == 50.0 and row["b"]["points"] == 32.0
    assert row["a"]["max"] == row["b"]["max"] == 60
    assert row["a"]["met"] is True and row["b"]["met"] is False
    assert cmp["a"]["label"] == "Team A" and cmp["b"]["label"] == "Team B"
    assert cmp["a"]["points"] == 80 and cmp["b"]["medal"] is None
    assert [r["key"] for r in cmp["rows"]] == ["in_band", "lowest", "moving"], (
        "the compare keeps the report card's row order")


def test_compare_ties_have_no_winner():
    vital_app = _h2h()
    a, _ = _pair()
    twin = {**a, "id": 9, "label": "Team B"}
    cmp = vital_app.compare_attempts(a, twin)
    assert cmp["winner"] is None, "an identical run is a draw, not a win"
    assert all(r["winner"] is None for r in cmp["rows"])


def test_compare_tolerates_an_attempt_logged_before_score_rows():
    """(ll) M26 wrote no per-row points; those runs must still compare."""
    vital_app = _h2h()
    a, b = _pair()
    old = {k: v for k, v in b.items() if k not in ("score_rows", "zeroed")}
    cmp = vital_app.compare_attempts(a, old)
    assert cmp["winner"] == "a", "the totals still compare"
    row = next(r for r in cmp["rows"] if r["key"] == "in_band")
    assert row["b"]["points"] is None and row["b"]["value"] == "82%"


# ---------------------------------------------------- (kk) the leaderboard

def test_leaderboard_is_best_first_with_ties_to_the_earlier_run(monkeypatch):
    vital_app = _h2h()
    log = [
        _run(70, None, False, [], label="Later 70", rid=1,
             when="2026-08-16T11:00:00"),
        _run(91, "gold", True, [], label="Best", rid=2,
             when="2026-08-16T12:00:00"),
        _run(70, None, False, [], label="Earlier 70", rid=3,
             when="2026-08-16T09:00:00"),
        _run(88, "gold", True, [], label="Another challenge", rid=4,
             when="2026-08-16T09:30:00", loop="temp", name="cold_store"),
    ]
    monkeypatch.setattr(vital_app, "ATTEMPTS", log)
    board = vital_app.leaderboard("water", "aid_station")
    assert [e["label"] for e in board] == ["Best", "Earlier 70", "Later 70"], (
        "best first, and a tie goes to the run that got there first")
    assert all(set(e) >= {"id", "label", "points", "medal", "met",
                          "wall_time"} for e in board)
    assert len(vital_app.leaderboard("water", "aid_station", limit=2)) == 2
    assert vital_app.best_attempt("water", "aid_station")["runs"] == 3, (
        "the run count is every run of THIS challenge and no other")


def test_attempt_grows_the_score_breakdown():
    """(ll) Stored, not recomputed: what a run was worth THAT DAY stays
    true even if a later phase swaps the scorer for an honors section."""
    vital_app = _h2h()
    entry = vital_app.CHALLENGES["glucose"]["t1_shift"]
    report = vital_app.EVALUATORS["t1_shift"]([CRAFTED_RECORD["t1_shift"]])
    score = vital_app.score_report(entry, report)
    att = vital_app.build_attempt("glucose", "t1_shift", report, score,
                                  label="Team 3")
    assert att["label"] == "Team 3"
    assert att["score_rows"] == score["rows"]
    assert att["zeroed"] == score["zeroed"]


def test_attempts_data_dir_is_gitignored():
    """Student scores are runtime data, not source (kickoff SS2)."""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert "data/" in ignored, (
        "data/ must be gitignored - a file of team scores is never committed")


# ================= M28: the diagnosis game =================================
# The one genuinely new verb in Phase 8. Every phase so far taught MANAGING
# a loop; this one tests READING one, which is the skill the exam actually
# asks for. That makes the redaction gate the whole milestone: a case is
# only a game if the answer isn't in the page, and the working assumption
# is that a student opens devtools, because one will.


def _diag():
    """Import the diagnosis layer, or SKIP loudly (M28)."""
    import app as vital_app
    if not hasattr(vital_app, "CASES"):
        pytest.skip("CASES doesn't exist yet - it arrives at M28")
    return vital_app


# Fields that NAME the answer rather than describe the physiology. The
# `*_enabled` flags are caught by their suffix; these are the ones that
# aren't. (`adh_override` joined at M31 — a new knob is a new answer key.)
ANSWER_KEY_FIELDS = {"water_access", "fever_offset", "insulin_sensitivity",
                     "adh_override"}

# What the strip charts, the readouts, the tooltip and the diagram read on
# each page. Redaction must leave ALL of this in place: it withholds the
# answer, never the evidence.
CHART_KEYS = {
    "temp": {"t", "core_temp", "env_temp", "exercise", "error",
             "sweat", "shiver", "vaso"},
    "glucose": {"t", "glucose", "gut_carbs", "exercise", "error", "insulin",
                "glucagon", "uptake", "liver_flux", "injected_insulin",
                "total_insulin", "iob_units", "basal_rate"},
    "water": {"t", "osmolarity", "water_liters", "gut_water", "exercise",
              "error", "adh", "thirst", "urine_rate", "urine_osm"},
    "body": {"t", "glucose", "insulin", "glucagon", "renal_loss",
             "tubular_load", "glucose_osm", "osmolarity", "water_liters",
             "adh", "thirst", "urine_rate", "urine_osm"},
}


@pytest.fixture
def diag_client(monkeypatch):
    """A test client whose scores never touch the teacher's real log.

    `attempts.append(record, path=DEFAULT_PATH)` binds the path at def
    time, so patching the module attribute would do nothing — patch the
    app's own logger instead, and keep what it was handed so the tests can
    inspect the attempt without a disk anywhere near them.
    """
    vital_app = _diag()
    logged = []

    def fake_log(record):
        logged.append(record)
        return {**record, "id": len(logged)}, None

    monkeypatch.setattr(vital_app, "log_attempt", fake_log)
    yield vital_app, vital_app.app.test_client(), logged
    # These drive the REAL shared runners (the projector model has exactly
    # one per loop). Put them back the way they were found.
    for runner in vital_app.runners.values():
        runner.sim.reset()
        runner.case = None
        runner.case_index = 0
        runner.challenge = None
        runner.preset = None


# ------------------------------------------------------ (mm) the cases

def test_case_table_shape():
    """Every entry carries what the card, the grader and the reveal need."""
    vital_app = _diag()
    required = {"brief", "setup", "speed", "warmup_s", "answer", "note"}
    assert vital_app.CASES, "the cases table is empty"
    for loop, entries in vital_app.CASES.items():
        assert loop in vital_app.runners, f"unknown loop {loop!r}"
        options = vital_app.ANSWER_OPTIONS[loop]
        roles = {o["key"] for o in options["roles"]}
        parts = {o["key"] for o in options["parts"]}
        assert entries, f"the {loop} loop has no cases"
        for cid, case in entries.items():
            missing = required - set(case)
            assert not missing, f"{loop}/{cid} lacks {sorted(missing)}"
            assert case["answer"]["role"] in roles, (
                f"{loop}/{cid} answers {case['answer']['role']!r}, which "
                "isn't one of the roles the form offers - an answer nobody "
                "can select is a case nobody can win")
            assert case["answer"]["part"] in parts, (
                f"{loop}/{cid} answers part {case['answer']['part']!r}, "
                "which isn't in that loop's parts list")
            assert case["warmup_s"] >= 0 and case["speed"] in (1, 4, 16)
            assert case["note"].strip(), (
                f"{loop}/{cid} has no teaching note - the reveal is the "
                "lesson, not the verdict")


def test_every_loop_can_answer_nothing_is_broken():
    """A loop where "intact" is never right teaches the wrong reflex."""
    vital_app = _diag()
    for loop, entries in vital_app.CASES.items():
        roles = {o["key"] for o in vital_app.ANSWER_OPTIONS[loop]["roles"]}
        assert roles == {"receptor", "control", "effector", "none"}, (
            f"{loop} offers {sorted(roles)} - the four answers are the "
            "curriculum vocabulary and they are the same on every loop")
        assert any(c["answer"]["role"] == "none" for c in entries.values()), (
            f"{loop} has no intact case: if 'nothing is broken' is never "
            "the answer here, the class rules it out for free and stops "
            "reading the charts")


def test_case_order_does_not_give_the_pattern_away():
    """Same four answers everywhere, deliberately in different orders."""
    vital_app = _diag()
    seen = {}
    for loop, entries in vital_app.CASES.items():
        order = tuple(c["answer"]["role"] for c in entries.values())
        assert order not in seen, (
            f"{loop} asks its roles in the same order as {seen[order]} - a "
            "class that plays a few cases would learn the position instead "
            "of the physiology")
        seen[order] = loop


# --------------------------------------------------- (nn) the redaction

def test_redaction_allowlist_covers_the_charts_and_nothing_else():
    vital_app = _diag()
    for loop, keep in vital_app.VISIBLE_DURING_CASE.items():
        record = vital_app.runners[loop].sim.state()
        unknown = keep - set(record)
        assert not unknown, (
            f"VISIBLE_DURING_CASE[{loop!r}] lists {sorted(unknown)}, which "
            "the engine never records - a typo here silently blanks a chart")
        withheld = CHART_KEYS[loop] - keep
        assert not withheld, (
            f"the {loop} page draws {sorted(withheld)} and redaction would "
            "withhold it - the gate hides the ANSWER, never the evidence")
        leaks = {k for k in keep if k.endswith("_enabled")} | (
            keep & ANSWER_KEY_FIELDS)
        assert not leaks, (
            f"VISIBLE_DURING_CASE[{loop!r}] would ship {sorted(leaks)}, "
            "which names the broken part outright")


def test_redaction_fails_closed_on_a_field_nobody_listed():
    """An allowlist, not a blocklist: tomorrow's field is withheld until
    somebody lists it on purpose."""
    vital_app = _diag()
    for loop in vital_app.VISIBLE_DURING_CASE:
        record = dict(vital_app.runners[loop].sim.state())
        record["phase_9_field"] = "which part is broken"
        out = vital_app.redact_record(loop, record)
        assert "phase_9_field" not in out, (
            f"the {loop} gate passed a field it had never heard of - a "
            "blocklist fails OPEN and this must not be one")
        assert all(out[k] == record[k] for k in out), (
            "redaction changed a value it kept - it may only drop keys")


def test_a_live_case_ships_no_answer_anywhere(diag_client):
    """(nn)(rr) Drive every case through the production routes and read
    the payload the way a student with devtools open would."""
    vital_app, client, _ = diag_client
    for loop, entries in vital_app.CASES.items():
        for n in range(1, len(entries) + 1):
            started = client.post(f"/control?loop={loop}",
                                  json={"action": "diagnose", "value": n})
            assert started.status_code == 200, started.get_json()
            polled = client.get(f"/state?loop={loop}").get_json()
            for j in (started.get_json(), polled):
                for record in [j["now"], *j["points"]]:
                    banned = sorted(k for k in record
                                    if k.endswith("_enabled")
                                    or k in ANSWER_KEY_FIELDS)
                    assert not banned, (
                        f"{loop} case {n} ships {banned} while the case is "
                        "blind - that IS the answer key")
                assert j["preset"] is None, (
                    "the disease banner names the diagnosis in words")
                case = j["case"]
                assert case["answered"] is False
                assert case["n"] == n and case["of"] == len(entries)
                for key in ("answer", "truth", "note", "setup", "id"):
                    assert key not in case, (
                        f"the case block ships {key!r} before the class has "
                        "committed to an answer")
            refused = client.get(f"/export.csv?loop={loop}")
            assert refused.status_code != 200, (
                "a CSV of the enabled flags is the answer key in a column")
            assert "case" in refused.get_json()["error"].lower(), (
                "the refusal must say WHY, in plain English")


def test_the_reveal_releases_a_history_identical_to_an_unblinded_run(
        diag_client):
    """(pp) Redaction is a delivery gate, never data loss (kickoff SS5:
    "verify that, don't assume it")."""
    from engine.sim import Simulation
    vital_app, client, _ = diag_client
    loop, n = "temp", 1
    cid = list(vital_app.CASES[loop])[n - 1]
    case = vital_app.CASES[loop][cid]

    client.post(f"/control?loop={loop}",
                json={"action": "diagnose", "value": n})
    blind = client.get(f"/state?loop={loop}").get_json()
    assert "sensor_enabled" not in blind["now"]
    truth = case["answer"]
    answered = client.post(f"/control?loop={loop}",
                           json={"action": "answer", "role": truth["role"],
                                 "part": truth["part"]})
    assert answered.status_code == 200, answered.get_json()
    shown = client.get(f"/state?loop={loop}").get_json()
    assert "sensor_enabled" in shown["now"], (
        "the reveal must release the flags it was holding")
    assert shown["case"]["answered"] is True
    assert shown["case"]["grade"]["note"] == case["note"], (
        "the reveal is where the teaching note finally arrives")

    ref = Simulation()
    vital_app._apply_preset(ref, case["setup"])
    for method, args in case.get("start_actions", []):
        getattr(ref, method)(*args)
    ref.step(case["warmup_s"])
    want = ref.history()
    got = vital_app.runners[loop].sim.history()[:len(want)]
    assert got == want, (
        "the released history differs from the same case run un-blinded - "
        "the engine must have recorded every field all along")


# ---------------------------------------------------- (oo) the grading

def test_grade_answer_is_pure_and_gives_partial_credit():
    import json
    vital_app = _diag()
    case = {"answer": {"role": "effector", "part": "sweat"},
            "note": "the sweat glands never fired"}
    before = json.dumps(case, sort_keys=True)
    right = vital_app.grade_answer(case, {"role": "effector", "part": "sweat"})
    near = vital_app.grade_answer(case, {"role": "effector", "part": "shiver"})
    wrong = vital_app.grade_answer(case, {"role": "receptor",
                                          "part": "sensor"})
    assert json.dumps(case, sort_keys=True) == before, (
        "grade_answer() mutated the case it was handed")
    assert right == vital_app.grade_answer(case, {"role": "effector",
                                                  "part": "sweat"}), (
        "the grader is not a pure function")
    assert (right["verdict"], right["correct"]) == ("correct", True)
    assert (near["verdict"], near["correct"]) == ("partial", False)
    assert (wrong["verdict"], wrong["correct"]) == ("wrong", False)
    assert right["points"] > near["points"] > wrong["points"] == 0, (
        "naming the right part of the loop and the wrong component is worth "
        "more than missing both")
    assert all(g["note"] == case["note"] for g in (right, near, wrong)), (
        "the teaching note is the point of the reveal - it shows either way")


def test_none_normalizes_its_part_so_a_stale_select_cannot_hurt():
    vital_app = _diag()
    intact = {"answer": {"role": "none", "part": "none"}, "note": "-"}
    assert vital_app.grade_answer(
        intact, {"role": "none", "part": "sweat"})["correct"] is True, (
        "answering 'nothing is broken' with a part left selected in the "
        "second box is still the right answer")
    broken = {"answer": {"role": "effector", "part": "sweat"}, "note": "-"}
    missed = vital_app.grade_answer(broken, {"role": "none", "part": "sweat"})
    assert missed["correct"] is False and missed["verdict"] == "wrong", (
        "...and it must not accidentally match on the part alone")


def test_grade_rows_read_like_every_other_report_card():
    vital_app = _diag()
    case = {"answer": {"role": "effector", "part": "sweat"}, "note": "x"}
    grade = vital_app.grade_answer(case, {"role": "receptor",
                                          "part": "sensor"})
    assert all({"key", "label", "value", "met"} <= set(r)
               for r in grade["rows"]), (
        "a diagnosis report is drawn by the same renderer as every other "
        "report card, so its rows must have the same shape")
    assert [r["met"] for r in grade["rows"][:2]] == [False, False]


# --------------------------------------------- (qq) the diagnosis attempt

def test_diagnosis_attempt_is_a_logged_data_product(diag_client):
    vital_app, client, logged = diag_client
    loop = "water"
    cid = list(vital_app.CASES[loop])[0]
    truth = vital_app.CASES[loop][cid]["answer"]
    client.post(f"/control?loop={loop}",
                json={"action": "diagnose", "value": 1,
                      "label": "  Period 2   Red  "})
    client.post(f"/control?loop={loop}",
                json={"action": "answer", "role": truth["role"],
                      "part": truth["part"]})
    assert len(logged) == 1, "one answered case is one attempt"
    att = logged[0]
    missing = ATTEMPT_FIELDS - set(att)
    assert not missing, f"a diagnosis attempt lacks {sorted(missing)}"
    assert att["mode"] == "diagnosis"
    assert att["loop"] == loop and att["name"] == cid
    assert att["label"] == "Period 2 Red", "the team label is tidied here too"
    assert att["met"] is True and att["correct"] is True
    assert att["answer"] == {"role": truth["role"], "part": truth["part"]}, (
        "the submitted answer is part of the record (kickoff SS5) - a "
        "worksheets phase reads this file, not a screenshot")


def test_a_diagnosis_never_lands_on_a_challenge_leaderboard(monkeypatch):
    vital_app = _diag()
    intruder = {"id": 1, "wall_time": "2026-08-17T09:00:00", "loop": "water",
                "mode": "diagnosis", "name": "aid_station", "label": "Team 3",
                "points": 100, "medal": None, "met": True, "rows": []}
    monkeypatch.setattr(vital_app, "ATTEMPTS", [intruder])
    assert vital_app.leaderboard("water", "aid_station") == [], (
        "a perfect diagnosis is not a 100-point aid station run")


# ------------------------------------------------ (rr) nothing in the page

def test_no_case_identifier_reaches_the_page():
    vital_app = _diag()
    html = vital_app.app.test_client().get("/").get_data(as_text=True)
    for loop, entries in vital_app.CASES.items():
        for cid, case in entries.items():
            assert cid not in html, (
                f"case id {cid!r} is rendered into the page - the picker "
                "sends an INDEX so that there is nothing in the DOM to map "
                "back to a case")
            assert case["note"] not in html and case["brief"] not in html, (
                f"{loop}/{cid} leaks its text into the page before it runs")


# --------------------------------------------- the case, driven like a class

def test_next_case_rotates_in_a_fixed_order_and_wraps(diag_client):
    """No randomness, ever (kickoff SS2) - a replayed case is rehearsal."""
    vital_app, client, _ = diag_client
    loop = "temp"
    total = len(vital_app.CASES[loop])
    seen = []
    for _ in range(total + 1):
        client.post(f"/control?loop={loop}", json={"action": "diagnose"})
        seen.append(client.get(f"/state?loop={loop}").get_json()["case"]["n"])
    assert seen == list(range(1, total + 1)) + [1]
    assert client.post(f"/control?loop={loop}",
                       json={"action": "diagnose", "value": total + 1}
                       ).status_code == 400


def test_a_nonsense_answer_is_refused_not_graded(diag_client):
    vital_app, client, logged = diag_client
    client.post("/control?loop=temp", json={"action": "diagnose", "value": 1})
    bad = client.post("/control?loop=temp",
                      json={"action": "answer", "role": "the vibes",
                            "part": "sweat"})
    assert bad.status_code == 400
    assert not logged, "a refused answer must not be logged as an attempt"
    assert client.get("/state?loop=temp").get_json()["case"]["answered"] \
        is False, "the case is still live and still blind"
    good = {"action": "answer", **vital_app.CASES["temp"]["case1"]["answer"]}
    assert client.post("/control?loop=temp", json=good).status_code == 200
    twice = client.post("/control?loop=temp", json=good)
    assert twice.status_code == 400 and "answered" in \
        twice.get_json()["error"], "one commitment per case, said plainly"


def test_answering_with_no_case_running_is_refused(diag_client):
    _, client, _ = diag_client
    r = client.post("/control?loop=temp",
                    json={"action": "answer", "role": "receptor",
                          "part": "sensor"})
    assert r.status_code == 400 and "case" in r.get_json()["error"].lower()


def test_the_game_modes_are_mutually_exclusive(diag_client):
    """A challenge and a blind case are different lessons; one clears the
    other, and clearing a case un-redacts the snapshot."""
    vital_app, client, _ = diag_client
    client.post("/control?loop=temp", json={"action": "diagnose", "value": 1})
    client.post("/control?loop=temp",
                json={"action": "challenge", "value": "cold_store"})
    j = client.get("/state?loop=temp").get_json()
    assert "case" not in j and "sweat_enabled" in j["now"]
    client.post("/control?loop=temp", json={"action": "diagnose", "value": 1})
    j = client.get("/state?loop=temp").get_json()
    assert "challenge" not in j, "starting a case must clear a challenge"
    client.post("/control?loop=temp", json={"action": "reset"})
    j = client.get("/state?loop=temp").get_json()
    assert "case" not in j and "sweat_enabled" in j["now"], (
        "reset ends the game and gives the sandbox back")


# ================= M29: crisis mode ========================================
# A challenge that ambushes you on a schedule. Three things make that fair
# rather than arbitrary:
#
#   * events fire at stamped SIM-TIME offsets through the same public API
#     the buttons already call, so the run a teacher rehearses at home is
#     the run the class gets — no matter how the browser's polls fell,
#   * nothing that has not yet happened reaches the page. The schedule is
#     an ambush, and an ambush you can read in devtools is a timetable,
#   * a hard stop CLOSES THE WINDOW and reports; it never splashes a game
#     over across the projector (kickoff SS2).


def _crisis():
    """Import the crisis layer, or SKIP loudly (M29)."""
    import app as vital_app
    if not hasattr(vital_app, "STOPS"):
        pytest.skip("STOPS doesn't exist yet - it arrives at M29")
    return vital_app


def _crises(vital_app):
    """Every challenge that carries an ambush schedule."""
    return [(loop, cid, entry)
            for loop, entries in vital_app.CHALLENGES.items()
            for cid, entry in entries.items() if entry.get("events")]


def _armed(vital_app, loop, cid):
    """A Runner of OUR OWN, armed with one challenge.

    Never the shared projector runners: these tests drive whole sim-hours
    and would leave a class's screen somewhere strange.
    """
    runner = vital_app.Runner(type(vital_app.runners[loop].sim)(), loop)
    vital_app.start_challenge(runner, loop, cid)
    return runner


# ------------------------------------------------- (ss) the ambush table

def _game_loops(vital_app):
    """Loops that claim to teach the WHOLE lesson grammar.

    A loop may be deliberately sandbox-only for a while (kickoff §2:
    "coupling must be explorable before it is scored"), but the app has
    to SAY SO in `SANDBOX_ONLY_LOOPS` — the exception lives in the code,
    not in a quietly narrowed test. M42 pins that the set is empty again.
    """
    declared = getattr(vital_app, "SANDBOX_ONLY_LOOPS", set())
    return [l for l in vital_app.runners if l not in declared]


def test_a_sandbox_only_loop_is_declared_and_still_works():
    """An undeclared loop with no game is a gap; a declared one is a
    decision. Either way it must still teach as a sandbox."""
    vital_app = _crisis()
    client = vital_app.app.test_client()
    for loop in getattr(vital_app, "SANDBOX_ONLY_LOOPS", set()):
        assert loop in vital_app.runners, (
            f"{loop!r} is declared sandbox-only but is not a loop")
        assert loop not in vital_app.CHALLENGES, (
            f"{loop!r} is declared sandbox-only but HAS a challenge - "
            "delete it from SANDBOX_ONLY_LOOPS")
        assert client.get(f"/state?loop={loop}").status_code == 200
        assert client.get(f"/export.csv?loop={loop}").status_code == 200, (
            "a sandbox loop still owes the class its spreadsheet")


def test_every_loop_has_a_crisis():
    """Kickoff M29: one crisis variant for each of the three loops."""
    vital_app = _crisis()
    loops = {loop for loop, _, _ in _crises(vital_app)}
    want = set(_game_loops(vital_app))
    assert loops == want, (
        f"crisis challenges exist for {sorted(loops)} - M29 is one variant "
        f"for each of {sorted(want)}")


def test_crisis_event_shape():
    """Every ambush is (sim-time offset, action, plain-English line)."""
    vital_app = _crisis()
    for loop, cid, entry in _crises(vital_app):
        sim = vital_app.runners[loop].sim
        last = -1.0
        for ev in entry["events"]:
            assert set(ev) == {"at", "do", "line"}, (
                f"{loop}/{cid} event carries {sorted(ev)} - an event is a "
                "sim-time offset, an action, and the words the class reads")
            assert last < ev["at"] < entry["duration_s"], (
                f"{loop}/{cid} fires at +{ev['at']}s: offsets must climb and "
                f"land inside the {entry['duration_s']}s window (an event at "
                "0 is a setup, and one at the buzzer never happens)")
            last = ev["at"]
            method, args = ev["do"]
            assert callable(getattr(sim, method, None)), (
                f"{loop}/{cid} fires {method!r}, which the {loop} engine "
                "does not have - an ambush must go through the SAME public "
                "API the buttons call (kickoff SS0: no engine changes)")
            assert isinstance(args, tuple), f"{loop}/{cid} args must be a tuple"
            assert ev["line"].strip(), (
                f"{loop}/{cid} has an unnamed event - the class must be told "
                "what just hit them")


def test_every_crisis_ends_in_a_report_not_a_game_over():
    """Each crisis names hard stops, and each stop is a scored integrity
    line — because a window truncated at 20 minutes would score a
    FLATTERING percentage, and crashing early must never out-score
    playing it out."""
    vital_app = _crisis()
    for loop, cid, entry in _crises(vital_app):
        metrics = entry["metrics"]
        stops = vital_app.STOPS.get(metrics)
        assert stops, f"{loop}/{cid} has no hard-stop line"
        for stop in stops:
            assert set(stop) == {"key", "line", "test"}, (
                f"{loop}/{cid} stop carries {sorted(stop)}")
            assert stop["line"].strip() and callable(stop["test"])
        rule = vital_app.SCORING[metrics].get("stopped")
        assert rule and rule.get("integrity"), (
            f"SCORING[{metrics!r}] must zero a run that ended early - "
            "otherwise the shorter the window, the better the percentage")


def test_a_stop_reads_the_same_line_in_the_runner_and_the_report():
    """ONE definition of "the patient is in the ER": the table the stepper
    watches is the table the report card quotes."""
    vital_app = _crisis()
    for loop, cid, entry in _crises(vital_app):
        metrics = entry["metrics"]
        clean = dict(vital_app.runners[loop].sim.state())
        clean["t"] = 60.0
        rows = {r["key"]: r
                for r in vital_app.EVALUATORS[metrics]([clean])["rows"]}
        assert rows["stopped"]["met"] is True, (
            f"{loop}/{cid}: a run nobody stopped must report so")
        for stop in vital_app.STOPS[metrics]:
            assert stop["test"](clean) is False, (
                f"{loop}/{cid}: stop {stop['key']!r} fires on a healthy "
                "resting record - that would end every run at tick one")


# ----------------------------------------------- (tt) firing on sim-time

def test_events_fire_on_sim_time_not_on_poll_timing():
    """THE M29 invariant. Two identical runs, stepped in wildly different
    chunks — one tick at a time against chunks of 991 — must produce
    byte-identical history AND an identical feed. A browser poll's timing
    may never move an ambush."""
    vital_app = _crisis()
    for loop, cid, entry in _crises(vital_app):
        span = entry["duration_s"]
        fine = _armed(vital_app, loop, cid)
        for _ in range(span):
            fine._step(1)
        coarse = _armed(vital_app, loop, cid)
        left = span
        while left > 0:
            chunk = min(left, 991)
            coarse._step(chunk)
            left -= chunk
        assert fine.sim.history() == coarse.sim.history(), (
            f"{loop}/{cid}: the same crisis stepped in different chunks "
            "produced different physiology - an ambush is landing on poll "
            "timing instead of sim-time")
        assert (fine.challenge["feed"] == coarse.challenge["feed"]
                and len(fine.challenge["feed"]) == len(entry["events"])), (
            f"{loop}/{cid}: the event feeds disagree")


def test_an_event_lands_at_its_stamped_offset_and_does_something():
    """The feed's clock is the schedule's clock, and the action really
    reached the engine."""
    vital_app = _crisis()
    for loop, cid, entry in _crises(vital_app):
        runner = _armed(vital_app, loop, cid)
        t0 = runner.challenge["t_start"]
        for ev in entry["events"]:
            runner._step(int(t0 + ev["at"] - runner.sim.state()["t"]))
            before = runner.sim.state()
            runner._step(1)               # the tick the ambush lands on
            fired = runner.challenge["feed"][-1]
            assert fired["t"] == t0 + ev["at"] and fired["at"] == ev["at"], (
                f"{loop}/{cid} fired {fired['t']} for an offset of "
                f"+{ev['at']}s from {t0}")
            assert fired["line"] == ev["line"]
            after = runner.sim.state()
            changed = [k for k in after
                       if k != "t" and after[k] != before.get(k)]
            assert changed, (
                f"{loop}/{cid}: {ev['do'][0]} at +{ev['at']}s changed nothing "
                "in the record - an ambush nobody can see is not an ambush")


def test_a_challenge_with_no_events_steps_exactly_as_before():
    """M24-M28's three challenges must be untouched by the new stepper
    (standing rule 3: extend, never rebuild)."""
    vital_app = _crisis()
    for loop, entries in vital_app.CHALLENGES.items():
        for cid, entry in entries.items():
            if entry.get("events"):
                continue
            span = 900
            runner = _armed(vital_app, loop, cid)
            left = span
            while left > 0:                       # ragged chunks on purpose
                chunk = min(left, 137)
                runner._step(chunk)
                left -= chunk
            ref = type(vital_app.runners[loop].sim)()
            vital_app._apply_preset(ref, entry["setup"])
            for method, args in entry.get("start_actions", []):
                getattr(ref, method)(*args)
            ref.step(span)
            assert runner.sim.history() == ref.history(), (
                f"{loop}/{cid} no longer matches a plain sim.step() run")


# --------------------------------------------------- (uu) the hard stops

def test_a_hard_stop_closes_the_window_early_and_zeroes_the_run():
    """The classic: fifteen units into a type 1 patient. The window ends
    where the patient did, the report says so, and the score is zero with
    a reason in words."""
    vital_app = _crisis()
    loop, cid = "glucose", "crisis_shift"
    entry = vital_app.CHALLENGES[loop][cid]
    runner = _armed(vital_app, loop, cid)
    runner.sim.inject(15.0)
    runner.sim.inject(15.0)
    runner._step(entry["duration_s"])
    c = runner.challenge
    assert c["stopped"], "a double overdose must cross a hard-stop line"
    assert c["t_end"] == c["stopped"]["t"] < c["t_start"] + entry["duration_s"], (
        "the window must end on the tick the line was crossed")
    assert runner.sim.state()["t"] == c["t_start"] + entry["duration_s"], (
        "the SIMULATION must carry on - a fail state is a report, never a "
        "frozen screen (kickoff SS2)")
    window = [r for r in runner.sim.history()
              if c["t_start"] < r["t"] <= c["t_end"]]
    report = vital_app.EVALUATORS[entry["metrics"]](window)
    rows = {r["key"]: r for r in report["rows"]}
    assert rows["stopped"]["met"] is False and report["met"] is False
    score = vital_app.score_report(entry, report)
    assert score["points"] == 0 and score["medal"] is None and score["zeroed"]


def test_the_ambushes_stop_when_the_run_does():
    """Nothing fires after the window has closed — including a window a
    hard stop closed early."""
    vital_app = _crisis()
    loop, cid = "glucose", "crisis_shift"
    entry = vital_app.CHALLENGES[loop][cid]
    runner = _armed(vital_app, loop, cid)
    runner.sim.inject(15.0)
    runner.sim.inject(15.0)
    runner._step(entry["duration_s"])
    assert len(runner.challenge["feed"]) < len(entry["events"]), (
        "this run ended in the ER before its last ambush - the feed must "
        "not go on announcing events at a run that is over")


# ------------------------------------------ (vv) the feed, as it reaches
#                                                 the class and the log

@pytest.fixture
def crisis_client(monkeypatch):
    """A test client whose scores never touch the teacher's real log."""
    vital_app = _crisis()
    logged = []

    def fake_log(record):
        logged.append(record)
        return {**record, "id": len(logged)}, None

    monkeypatch.setattr(vital_app, "log_attempt", fake_log)
    yield vital_app, vital_app.app.test_client(), logged
    for runner in vital_app.runners.values():
        runner.sim.reset()
        runner.challenge = None
        runner.case = None
        runner.preset = None


def test_the_feed_never_announces_what_has_not_happened_yet(crisis_client):
    """Read it the way a student with devtools open would."""
    import json
    vital_app, client, _ = crisis_client
    loop, cid = "water", "race_day"
    entry = vital_app.CHALLENGES[loop][cid]
    client.post(f"/control?loop={loop}",
                json={"action": "challenge", "value": cid})
    runner = vital_app.runners[loop]
    j = client.get(f"/state?loop={loop}").get_json()
    assert j["challenge"]["events"] == [], "nothing has happened yet"
    text = json.dumps(j)
    for ev in entry["events"]:
        assert ev["line"] not in text, (
            "the whole ambush schedule is in the snapshot - that is a "
            "timetable, not a crisis")
    with runner.lock:
        runner._step(int(entry["events"][0]["at"]) + 1)
    j = client.get(f"/state?loop={loop}").get_json()
    feed = j["challenge"]["events"]
    assert [f["line"] for f in feed] == [entry["events"][0]["line"]], (
        "the feed must carry exactly what has landed, in order")
    assert all({"t", "at", "line"} == set(f) for f in feed), (
        "a feed entry is a sim-time, an offset and the words - no action, "
        "nothing to reverse-engineer the rest of the schedule from")


def test_the_feed_is_part_of_the_attempt_record(crisis_client):
    """Kickoff SS5: fields are APPENDED. A worksheets phase must be able
    to ask what this team was ambushed with."""
    vital_app, client, logged = crisis_client
    loop, cid = "water", "race_day"
    entry = vital_app.CHALLENGES[loop][cid]
    client.post(f"/control?loop={loop}",
                json={"action": "challenge", "value": cid, "label": "Team 3"})
    runner = vital_app.runners[loop]
    with runner.lock:
        runner._step(entry["duration_s"])
    j = client.get(f"/state?loop={loop}").get_json()
    assert j["challenge"]["done"] is True and j["challenge"]["report"]
    assert len(logged) == 1, "one finished run is one attempt"
    lines = [e["line"] for e in logged[0]["events"]]
    assert lines == [ev["line"] for ev in entry["events"]], (
        f"the attempt logged {lines} - every ambush belongs in the record")


def test_no_ambush_is_written_into_the_page():
    """Same rule as a blind case: it isn't a surprise if it's in the
    HTML."""
    vital_app = _crisis()
    html = vital_app.app.test_client().get("/").get_data(as_text=True)
    for loop, cid, entry in _crises(vital_app):
        for ev in entry["events"]:
            assert ev["line"] not in html, (
                f"{loop}/{cid} renders its ambush into the page")
        for stop in vital_app.STOPS[entry["metrics"]]:
            assert stop["line"] not in html, (
                f"{loop}/{cid} renders a hard-stop line into the page")


# ================= M30: the full pass ======================================
# The phase closes on a whole period taught off this thing: disturb, break,
# name, challenge, score, race, diagnose, survive. Three claims from the
# kickoff are checkable rather than merely demonstrable, so they are pinned
# here — the sandbox stays gameless when no game is running, a reload
# mid-game loses nothing, and nothing wedges.


@pytest.fixture
def period(monkeypatch):
    """A client for a whole class period, with the scores kept off disk.

    Like `diag_client`, this drives the REAL shared runners — the
    projector model has exactly one per loop — so it puts them back the
    way it found them.
    """
    vital_app = _crisis()
    logged = []

    def fake_log(record):
        logged.append(record)
        return {**record, "id": len(logged)}, None

    monkeypatch.setattr(vital_app, "log_attempt", fake_log)
    yield vital_app, vital_app.app.test_client(), logged
    for runner in vital_app.runners.values():
        runner.sim.reset()
        runner.challenge = None
        runner.case = None
        runner.case_index = 0
        runner.preset = None
        runner.attempt_error = None


def test_a_challenge_starts_from_the_same_body_every_time(period):
    """(vv) M30.1. Two teams running the identical challenge must get the
    identical run — that is the whole basis of the head-to-head, and the
    starting body is an input like any other.

    Found by the M30 full pass: the same 40 % duty play on cold_store
    scored 88 from a fresh app and 21 straight after a freezer demo.
    """
    vital_app, client, _ = period
    loop, cid = "temp", "cold_store"
    runs = []
    for lead_in in (lambda r: None, lambda r: r._step(1800)):
        runner = vital_app.runners[loop]
        with runner.lock:
            runner.sim.reset()
            # ...whatever the previous class left on the projector
            for part in ("sweat", "shiver", "vaso"):
                runner.sim.set_effector_enabled(part, False)
            runner.sim.set_env_temp(-10.0)
            lead_in(runner)
        client.post(f"/control?loop={loop}",
                    json={"action": "challenge", "value": cid})
        with runner.lock:
            runner._step(600)
        runs.append(runner.sim.history())
    assert runs[0] == runs[1], (
        "the same challenge produced different physiology depending on "
        "what the sandbox had been doing beforehand - two teams' report "
        "cards are not comparable unless the run starts the same way")
    assert runs[0][0]["t"] == 0.0, "a challenge starts a fresh run"


def test_every_loop_can_teach_the_whole_lesson():
    """(ww) Every verb of the lesson grammar exists on every loop."""
    vital_app = _crisis()
    for loop in _game_loops(vital_app):
        presets = vital_app.PRESETS[loop]
        assert "healthy" in presets and len(presets) >= 2, (
            f"{loop} has no disease to name, or no way back")
        entries = vital_app.CHALLENGES[loop]
        assert any(not e.get("events") for e in entries.values()), (
            f"{loop} has no plain challenge to score and race")
        assert any(e.get("events") for e in entries.values()), (
            f"{loop} has no crisis to survive")
        assert len(vital_app.CASES[loop]) >= 2, f"{loop} has too few cases"
        assert vital_app.CSV_FIELDS[loop] and vital_app.ANSWER_OPTIONS[loop]


def test_the_sandbox_is_gameless_when_no_game_is_running(period):
    """(xx) Kickoff SS2: with no game started this is exactly the Phase 7
    sandbox. A teacher who wants to explore for forty minutes must never
    have to dismiss a game."""
    vital_app, client, _ = period
    for loop in _game_loops(vital_app):
        # Play a bit of every mode first, then hand the sandbox back.
        cid = list(vital_app.CHALLENGES[loop])[0]
        client.post(f"/control?loop={loop}",
                    json={"action": "challenge", "value": cid})
        client.post(f"/control?loop={loop}",
                    json={"action": "diagnose", "value": 1})
        client.post(f"/control?loop={loop}", json={"action": "reset"})
        j = client.get(f"/state?loop={loop}").get_json()
        assert "challenge" not in j and "case" not in j, (
            f"{loop} still has a game block after reset")
        assert j["preset"] is None, f"{loop} still names a disease"
        flags = [k for k in j["now"] if k.endswith("_enabled")]
        assert flags, (
            f"{loop} is still redacting with no case running - the "
            "breaker card would have nothing to mirror")
        assert client.get(f"/export.csv?loop={loop}").status_code == 200, (
            f"{loop}'s spreadsheet must come back when the game ends")


def test_a_reload_mid_game_loses_nothing(period):
    """(yy) Game state hangs off the Runner, never off the page — so the
    projector can be refreshed mid-lesson without losing the run."""
    vital_app, client, _ = period
    loop = "glucose"
    cid = [c for c, e in vital_app.CHALLENGES[loop].items()
           if e.get("events")][0]
    client.post(f"/control?loop={loop}",
                json={"action": "challenge", "value": cid,
                      "label": "Period 4 Red"})
    runner = vital_app.runners[loop]
    with runner.lock:
        runner._step(60 * 60)              # an hour in, mid-ambush
    before = client.get(f"/state?loop={loop}").get_json()
    assert client.get("/").status_code == 200          # <- the reload
    after = client.get(f"/state?loop={loop}&since=-1").get_json()
    assert after["challenge"]["label"] == "Period 4 Red"
    assert after["challenge"]["t_start"] == before["challenge"]["t_start"]
    assert after["challenge"]["events"] == before["challenge"]["events"], (
        "the event feed must come back from server state, not from a "
        "buffer in the page")
    assert after["points"][0]["t"] == 0.0, (
        "a reloaded page asks for the whole run and must get it - the "
        "charts redraw from server history, not from what the old page "
        "happened to be holding")

    # ...and the same for a blind case, which must still be blind.
    client.post(f"/control?loop={loop}",
                json={"action": "diagnose", "value": 1})
    assert client.get("/").status_code == 200
    j = client.get(f"/state?loop={loop}&since=-1").get_json()
    assert j["case"]["answered"] is False
    assert not [k for k in j["now"] if k.endswith("_enabled")], (
        "a reload during a blind case must not un-redact it")


# Every action the UI can send, plus the malformed versions of each. A
# wrong-loop action is a 400 with words, never a 500 and never a wedge.
ALL_CONTROL_CALLS = [
    {"action": "pause"}, {"action": "resume"}, {"action": "reset"},
    {"action": "speed", "value": 16}, {"action": "speed", "value": 7},
    {"action": "speed"}, {"action": "env_temp", "value": 40.0},
    {"action": "env_temp", "value": "warm"}, {"action": "env_temp"},
    {"action": "exercise", "value": True}, {"action": "exercise"},
    {"action": "effector", "name": "sweat", "value": False},
    {"action": "effector", "name": "gills", "value": False},
    {"action": "effector"}, {"action": "sensor", "value": False},
    {"action": "eat", "grams": 60, "rate": 1.0}, {"action": "eat"},
    {"action": "eat", "grams": "lots"}, {"action": "inject", "units": 4},
    {"action": "inject", "units": -1}, {"action": "inject"},
    {"action": "basal", "value": 1.0}, {"action": "basal", "value": 99},
    {"action": "pump", "value": True}, {"action": "drink", "ml": 250},
    {"action": "drink", "ml": "some"}, {"action": "drink"},
    {"action": "salty", "mosm": 300}, {"action": "salty", "mosm": "salty"},
    {"action": "preset", "value": "healthy"},
    {"action": "preset", "value": "consumption"},
    {"action": "challenge", "value": "cold_store"},
    {"action": "challenge", "value": "a_nice_walk"},
    {"action": "diagnose", "value": 1}, {"action": "diagnose"},
    {"action": "diagnose", "value": 99}, {"action": "diagnose", "value": "x"},
    {"action": "answer", "role": "receptor", "part": "sensor"},
    {"action": "answer", "role": "the vibes", "part": "sensor"},
    {"action": "answer"}, {"action": "scenario", "value": "freezer"},
    {"action": "scenario", "value": "a_lie_down"}, {"action": "scenario"},
    {"action": "sudo"}, {}, {"action": None},
]


def test_nothing_wedges(period):
    """(zz) The checkpoint, as a test: fire every action at every loop —
    including all the ones that belong to a different loop — and the app
    must answer every one of them and still be teaching afterwards.

    It runs on the projector in a classroom, so a wrong click is a
    plain-English 400, never a 500 and never a hang.
    """
    vital_app, client, _ = period
    for loop in vital_app.runners:
        for call in ALL_CONTROL_CALLS:
            r = client.post(f"/control?loop={loop}", json=call)
            assert r.status_code in (200, 400), (
                f"{loop} answered {r.status_code} to {call} - every refusal "
                "is a 400 with words")
            if r.status_code == 400:
                assert r.get_json()["error"].strip(), (
                    f"{loop} refused {call} without saying why")
    # Unknown loops, and the read-only routes with nonsense on them.
    assert client.get("/state?loop=spleen").status_code == 400
    assert client.post("/control?loop=spleen",
                       json={"action": "pause"}).status_code == 400
    assert client.get("/export.csv?loop=spleen").status_code == 400
    assert client.get("/compare?loop=temp&name=cold_store").status_code == 400
    assert client.get("/compare?loop=temp&name=cold_store&a=1&b=99999"
                      ).status_code == 400
    assert client.get("/compare?loop=temp&name=nope&a=1&b=2").status_code == 400
    # ...and after all of that, every loop is still answering.
    for loop in vital_app.runners:
        client.post(f"/control?loop={loop}", json={"action": "reset"})
        assert client.get(f"/state?loop={loop}").status_code == 200
        assert client.get(f"/export.csv?loop={loop}").status_code == 200
    assert client.get("/").status_code == 200


# ================= Phase 9: SIADH =========================================
# The first engine change since Phase 6, so the water loop gets what the
# other two engines got at M17: a hash of the OLD field subset, recorded
# from the code BEFORE the knob existed, proving the growth is shape-only.
#
# SIADH is the mirror image of the two insipidus presets: not too little
# ADH but ADH that will not stop — secretion inappropriate to the
# stimulus. The kidney obeys a hormone that shouldn't be there, ordinary
# drinking dilutes the blood, and the loop's own alarm (thirst) stays
# silent because low osmolarity is exactly what thirst does NOT respond
# to. The treatment that falls out of the model is the real first-line
# treatment: restrict water.

# (aaa) sha256 of json.dumps of the PHASE 6 FIELD SUBSET of
# _scripted_water_run's records, recorded 2026-08-17 with M30 committed —
# the last Phase 6-era state of engine/water.py.
PHASE6_WATER_FIELDS = [
    "t", "osmolarity", "water_liters", "gut_water", "exercise", "error",
    "adh", "thirst", "urine_rate", "urine_osm", "adh_enabled",
    "kidney_enabled", "water_access", "sensor_enabled"]
WATER_PHASE6_HASH = \
    "d884ef86eed5de7f60225ec7226541efb905bc1545a87c1efe0438e0c509137e"


def _siadh():
    """The water engine once it speaks set_adh_override, or SKIP (M31)."""
    WaterSimulation = _water()
    if not hasattr(WaterSimulation, "set_adh_override"):
        pytest.skip("set_adh_override() doesn't exist yet - it arrives "
                    "at M31")
    return WaterSimulation


def test_water_phase6_subset_unchanged_by_phase9():
    """(aaa) Byte-identical old behavior: the knob, unset, changes nothing."""
    import hashlib
    import json
    WaterSimulation = _water()
    records, _ = _scripted_water_run(WaterSimulation)
    subset = [{k: r[k] for k in PHASE6_WATER_FIELDS} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == WATER_PHASE6_HASH, (
        "The Phase 6 subset of the scripted water run changed - Phase 9 "
        "may only APPEND to the record, never alter recorded behavior")


def test_siadh_dilutes_a_body_that_drinks_normally():
    """(bbb) The signature: ordinary drinking + a hormone that won't stop
    = dilutional hyponatremia. Dilute blood, concentrated urine — the
    inappropriate combination — while thirst never says a word."""
    WaterSimulation = _siadh()
    sim = WaterSimulation()
    sim.set_adh_override(1.0)
    for _ in range(8):                     # a glass every 30 min, 4 h —
        sim.drink(250)                     # ordinary intake, not a chug
        sim.step(1800)
    records = [r for r in sim.history() if r["t"] > 0]
    crossed = next((r["t"] for r in records if r["osmolarity"] < 285.0),
                   None)
    assert crossed is not None and 3600 <= crossed <= 9000, (
        "SIADH + normal drinking must slide osmolarity under 285 between "
        "1 and 2.5 h"
        + ("" if crossed is None else f" (crossed at {crossed / 3600:.1f} h)")
        + " - too fast isn't 'ordinary drinking', too slow won't fit a "
        "lesson")
    assert min(r["osmolarity"] for r in records) < 282.0, (
        "4 h of ordinary drinking must reach genuine hyponatremia, "
        "not a wobble")
    assert max(r["urine_rate"] for r in records) <= 1.0, (
        "SIADH urine must stay scant - the kidney is obeying a hormone "
        "that shouldn't be there")
    assert min(r["urine_osm"] for r in records) >= 600.0, (
        "SIADH urine must stay CONCENTRATED while the blood dilutes - "
        "that mismatch is the diagnosis")
    assert all(r["thirst"] == 0.0 for r in records), (
        "Thirst spoke during SIADH - the loop's alarm must stay silent, "
        "because LOW osmolarity is what thirst doesn't answer")
    assert not any(d["auto"] for d in sim.drinks()), (
        "The body auto-drank during SIADH - every glass here is the "
        "patient's own habit, which is the point of the restriction fix")
    assert all(r["adh"] == 1.0 for r in records), (
        "ADH left the override level - the knob must pin secretion no "
        "matter what the receptors say")


def test_water_restriction_is_the_treatment():
    """(bbb) The same disease with the water bottle taken away barely
    moves - restriction, the real first-line treatment, falls out of
    the physics instead of being scripted."""
    WaterSimulation = _siadh()
    sim = WaterSimulation()
    sim.set_adh_override(1.0)
    sim.step(4 * 3600)
    osm = [r["osmolarity"] for r in sim.history()]
    assert max(osm) - min(osm) < 3.0, (
        f"Osmolarity drifted {max(osm) - min(osm):.1f} mOsm/L under "
        "restriction - SIADH with no water coming in should barely move")
    assert all(WATER_BAND[0] <= v <= WATER_BAND[1] for v in osm[1:]), (
        "Restricted SIADH left the band - the class must see the slide "
        "STOP when the drinking stops")


def test_healthy_kidneys_shrug_off_the_same_drinking():
    """(bbb) The control arm: the identical glass-every-30-min habit in a
    healthy body never leaves the band, because ADH dies and the kidneys
    flood the excess away dilute. Same input, opposite fate - the
    difference IS the disease."""
    WaterSimulation = _siadh()
    sim = WaterSimulation()
    for _ in range(8):
        sim.drink(250)
        sim.step(1800)
    records = [r for r in sim.history() if r["t"] > 0]
    assert min(r["osmolarity"] for r in records) >= 285.0, (
        "A healthy body diluted below 285 on a glass every 30 min - "
        "ordinary drinking must be something working kidneys shrug off")
    assert max(r["urine_rate"] for r in records) > 5.0, (
        "Healthy kidneys never flooded while absorbing the glasses - the "
        "dumped excess is the contrast the SIADH lesson needs")
    assert min(r["urine_osm"] for r in records) < 150.0, (
        "Healthy urine never turned dilute during the drinking - "
        "dilute-and-flooding is the working kidney's answer")


def test_adh_override_validation():
    """(ccc) Zero isn't SIADH (that's central DI by another name), and the
    override is an activity level, not a free number."""
    WaterSimulation = _siadh()
    sim = WaterSimulation()
    for bad in (0.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            sim.set_adh_override(bad)
    sim.set_adh_override(0.9)
    sim.step(10)
    assert sim.state()["adh"] == 0.9
    sim.set_adh_override(None)             # the disease clears
    sim.step(10)
    s = sim.state()
    assert s["adh_override"] is None and abs(s["adh"] - 0.5) < 0.2, (
        "Clearing the override must hand ADH back to the osmoreceptors "
        "(resting osmolarity ~290 reads ~0.5 on the staged curve)")


def _scripted_siadh_run():
    """Sets, exercises, and clears the knob mid-run, for determinism."""
    WaterSimulation = _siadh()
    sim = WaterSimulation()
    sim.step(600)
    sim.set_adh_override(1.0)
    sim.drink(500)
    sim.step(3600)
    sim.set_exercise(True)
    sim.step(1800)
    sim.set_exercise(False)
    sim.set_adh_override(None)
    sim.step(1800)
    return sim.history(), sim.drinks()


def test_siadh_is_deterministic():
    assert _scripted_siadh_run() == _scripted_siadh_run(), (
        "Two identical SIADH runs diverged (kickoff SS2)")


# ================= M33: per-student sessions ==============================
# The projector becomes a lab: a browser that presents a `vl_sid` cookie
# gets its OWN three Runners; a client that presents none (verify.py,
# THIS SUITE, curl) drives the same module-level `runners` it always
# has, which is what keeps every test above meaning what it meant. The
# id is minted by the page's JS — the server only reads it — and the
# attempts log stays global: one room, one leaderboard.

def _m33():
    """The app once sessions exist, or SKIP (M33)."""
    import app as vital_app
    if not hasattr(vital_app, "registry"):
        pytest.skip("the session registry doesn't exist yet - M33")
    return vital_app


@pytest.fixture
def fresh_registry(monkeypatch):
    """A registry no other test has seated anyone in."""
    from sessions import SessionRegistry
    vital_app = _m33()
    monkeypatch.setattr(
        vital_app, "registry",
        SessionRegistry(vital_app._make_runners, max_sessions=40,
                        idle_s=1800))
    return vital_app


def test_two_sessions_cannot_touch_each_others_state(fresh_registry):
    """(eee) The whole point: a wrong click on one device must never
    move another device's body."""
    vital_app = fresh_registry
    default_speed = vital_app.runners["temp"].speed
    a = vital_app.app.test_client()
    a.set_cookie("vl_sid", "team-a")
    b = vital_app.app.test_client()
    b.set_cookie("vl_sid", "team-b")
    r = a.post("/control?loop=temp", json={"action": "speed", "value": 16})
    assert r.status_code == 200
    assert a.get("/state?loop=temp").get_json()["speed"] == 16
    assert b.get("/state?loop=temp").get_json()["speed"] == 1, (
        "device B saw device A's speed - sessions are not isolated")
    assert vital_app.runners["temp"].speed == default_speed, (
        "a session's action reached the DEFAULT runners - verify.py and "
        "the projector would be at the mercy of every student device")


def test_a_reload_keeps_your_session(fresh_registry):
    """(eee) The cookie is the session: a new page (new client, same
    cookie) finds the same body mid-story."""
    vital_app = fresh_registry
    before = vital_app.app.test_client()
    before.set_cookie("vl_sid", "period5-green")
    before.post("/control?loop=temp", json={"action": "speed", "value": 16})
    reloaded = vital_app.app.test_client()
    reloaded.set_cookie("vl_sid", "period5-green")
    assert reloaded.get("/state?loop=temp").get_json()["speed"] == 16, (
        "a reload lost the session - the cookie must be the key, not "
        "the client")


def test_an_unknown_sid_gets_a_fresh_healthy_sandbox(fresh_registry):
    """(eee) An evicted or never-seen id is not an error: it is seated
    with a fresh healthy sandbox, which is also what makes a server
    restart harmless to a class."""
    vital_app = fresh_registry
    c = vital_app.app.test_client()
    c.set_cookie("vl_sid", "someone-who-was-evicted")
    j = c.get("/state?loop=water").get_json()
    assert "case" not in j and "challenge" not in j and j["preset"] is None
    flags = {k: v for k, v in j["now"].items() if k.endswith("_enabled")}
    assert flags and all(flags.values()), (
        "a fresh session arrived with parts already broken")


def test_the_room_is_capped_with_words(monkeypatch):
    """(fff) Seat N devices and the N+1th is refused in plain English —
    on the API and on the page — while everyone seated keeps playing."""
    from sessions import SessionRegistry
    vital_app = _m33()
    monkeypatch.setattr(
        vital_app, "registry",
        SessionRegistry(vital_app._make_runners, max_sessions=2,
                        idle_s=1800))
    for sid in ("seat-1", "seat-2"):
        c = vital_app.app.test_client()
        c.set_cookie("vl_sid", sid)
        assert c.get("/state?loop=temp").status_code == 200
    late = vital_app.app.test_client()
    late.set_cookie("vl_sid", "seat-3")
    refused = late.get("/state?loop=temp")
    assert refused.status_code == 503
    assert "full" in refused.get_json()["error"].lower()
    page = late.get("/")
    assert page.status_code == 503 and b"full" in page.data, (
        "the PAGE must refuse a full room in words too - a student's "
        "first sight of the app cannot be a stack trace")
    seated = vital_app.app.test_client()
    seated.set_cookie("vl_sid", "seat-1")
    assert seated.get("/state?loop=temp").status_code == 200, (
        "a full room broke a seated device - the cap must only refuse "
        "NEW sessions")


def test_idle_sessions_are_evicted_and_return_fresh():
    """(fff) The sweep, driven by a fake clock so the test needs no
    sleeping: touched sessions live, idle ones are dropped, and a
    dropped id is quietly re-seated fresh."""
    from sessions import SessionRegistry
    made = []
    def factory():
        made.append(object())
        return made[-1]
    t = {"now": 0.0}
    reg = SessionRegistry(factory, max_sessions=5, idle_s=100,
                          clock=lambda: t["now"])
    first = reg.runners_for("kid")
    t["now"] = 90
    assert reg.runners_for("kid") is first, "a touched session was swept"
    t["now"] = 180
    assert reg.runners_for("kid") is first, (
        "touching must reset the idle clock")
    t["now"] = 281
    fresh = reg.runners_for("kid")
    assert fresh is not first and len(made) == 2, (
        "an idle session must be swept and its id re-seated fresh")
    assert reg.count() == 1


def test_sessions_share_the_one_attempts_log(fresh_registry):
    """(ggg) One room, one leaderboard: every session reads the same
    bests, because the log is global and keyed by team label."""
    vital_app = fresh_registry
    a = vital_app.app.test_client()
    a.set_cookie("vl_sid", "team-a")
    cookieless = vital_app.app.test_client()
    j_a = a.get("/state?loop=temp").get_json()
    j_default = cookieless.get("/state?loop=temp").get_json()
    assert j_a["bests"] == j_default["bests"], (
        "two sessions see different bests - the attempts log must be "
        "shared, or the head-to-head means nothing")


# ================= M34: the doors =========================================

def test_the_double_click_opens_the_doors_but_python_stays_home():
    """(hhh) run.bat serves the room; a plain `python app.py` (and so
    verify.py, and every earlier phase's habits) binds loopback only.
    Opening the doors is a deliberate act, not a default."""
    vital_app = _m33()
    if not hasattr(vital_app, "_serve_host"):
        pytest.skip("_serve_host doesn't exist yet - M34")
    bat = (ROOT / "run.bat").read_text(encoding="utf-8")
    assert "VITAL_LOOP_HOST=0.0.0.0" in bat, (
        "run.bat no longer opens the app to the room (M34)")
    import os
    old = os.environ.pop("VITAL_LOOP_HOST", None)
    try:
        assert vital_app._serve_host() == "127.0.0.1", (
            "without run.bat's say-so the app must stay loopback-only")
        os.environ["VITAL_LOOP_HOST"] = "0.0.0.0"
        assert vital_app._serve_host() == "0.0.0.0"
    finally:
        if old is None:
            os.environ.pop("VITAL_LOOP_HOST", None)
        else:
            os.environ["VITAL_LOOP_HOST"] = old


def test_state_carries_the_room_count(fresh_registry):
    """(hhh) The teacher watches the room arrive: /state says how many
    devices hold a session, and the cookieless default isn't one."""
    vital_app = fresh_registry
    cookieless = vital_app.app.test_client()
    assert cookieless.get("/state?loop=temp").get_json()["sessions"] == 0
    device = vital_app.app.test_client()
    device.set_cookie("vl_sid", "first-arrival")
    device.get("/state?loop=temp")
    assert cookieless.get("/state?loop=temp").get_json()["sessions"] == 1, (
        "a seated device must show up in the room count")


# ================= M35: student worksheets ================================
# Printable pages rendered from one server table — never documents in
# the repo — so they cannot drift from the app. The pins keep them
# honest three ways: the curriculum vocabulary appears EXACTLY, every
# field they cite exists in the frozen record schemas, and the pages
# ask questions without ever answering them.

WORKSHEET_VOCAB = ["stimulus", "receptor", "control center", "effector",
                   "response", "set point", "negative feedback"]


def _m35():
    """The app once worksheets exist, or SKIP (M35)."""
    import app as vital_app
    if not hasattr(vital_app, "WORKSHEETS"):
        pytest.skip("worksheets don't exist yet - M35")
    return vital_app


def test_every_loop_has_a_printable_worksheet():
    """(iii) Three loops, three worksheets, and nonsense is refused in
    words."""
    vital_app = _m35()
    client = vital_app.app.test_client()
    assert set(vital_app.WORKSHEETS) == set(vital_app.runners)
    for loop in vital_app.runners:
        r = client.get(f"/worksheet/{loop}")
        assert r.status_code == 200 and b"Vital Loop" in r.data
    refused = client.get("/worksheet/spleen")
    assert refused.status_code == 400
    assert refused.get_json()["error"].strip()


def test_worksheet_vocabulary_is_exact():
    """(iii) Kickoff §1: curriculum vocabulary, used exactly — all seven
    terms, on every loop's worksheet."""
    vital_app = _m35()
    client = vital_app.app.test_client()
    for loop in vital_app.WORKSHEETS:
        page = client.get(f"/worksheet/{loop}").data.decode("utf-8").lower()
        missing = [t for t in WORKSHEET_VOCAB if t not in page]
        assert not missing, (
            f"the {loop} worksheet is missing the curriculum terms "
            f"{missing} - the vocabulary is the lesson's spine")


def test_worksheets_cite_only_frozen_fields():
    """(iii) Every code-word a worksheet sends a student to grep their
    CSV for must exist in that loop's frozen record — a typo here is a
    student staring at a spreadsheet that lacks the column."""
    vital_app = _m35()
    client = vital_app.app.test_client()
    for loop, ws in vital_app.WORKSHEETS.items():
        record = vital_app.runners[loop].sim.state()
        ghosts = set(ws["fields"]) - set(record)
        assert not ghosts, (
            f"the {loop} worksheet cites {sorted(ghosts)}, which the "
            "engine never records")
        page = client.get(f"/worksheet/{loop}").data.decode("utf-8")
        for f in ws["fields"]:
            assert f"<code>{f}</code>" in page, (
                f"the {loop} worksheet lists {f!r} but never actually "
                "shows it - a field cited nowhere teaches nothing")


def test_worksheets_carry_no_answers():
    """(iii) The worksheet asks; the student's own run answers. No case
    text, no disease banner, no teaching note may leak onto paper."""
    vital_app = _m35()
    client = vital_app.app.test_client()
    for loop in vital_app.WORKSHEETS:
        page = client.get(f"/worksheet/{loop}").data.decode("utf-8")
        for cloop, entries in vital_app.CASES.items():
            for cid, case in entries.items():
                assert case["brief"] not in page, (
                    f"{cloop}/{cid}'s brief is on the {loop} worksheet")
                assert case["note"] not in page, (
                    f"{cloop}/{cid}'s teaching note is on the {loop} "
                    "worksheet - that's the reveal, printed in advance")
        for ploop, presets in vital_app.PRESETS.items():
            for name, preset in presets.items():
                if preset["banner"]:
                    assert preset["banner"] not in page, (
                        f"the {ploop}/{name} banner is on the {loop} "
                        "worksheet")


# ================= M36: the lab pass ======================================
# Phase 9 closes the way Phase 8 did — the whole promise, checkable:
# a room of devices, every mode, wrong clicks included, one shared
# leaderboard, and nobody's body moved by anybody else's hand.

@pytest.fixture
def lab(fresh_registry, monkeypatch):
    """A fresh room whose scores never touch the teacher's real log."""
    vital_app = fresh_registry
    logged = []

    def fake_log(record):
        logged.append(record)
        return {**record, "id": len(logged)}, None

    monkeypatch.setattr(vital_app, "log_attempt", fake_log)
    yield vital_app, logged
    for runner in vital_app.runners.values():
        runner.sim.reset()
        runner.case = None
        runner.case_index = 0
        runner.challenge = None
        runner.preset = None


def _device(vital_app, sid):
    c = vital_app.app.test_client()
    c.set_cookie("vl_sid", sid)
    return c


def test_the_lab_pass_every_mode_across_a_room(lab):
    """(jjj) Six devices, four modes, wrong clicks, one log — and the
    projector untouched throughout."""
    vital_app, logged = lab

    # Device 1 demonstrates: freezer + fever, in ITS sandbox only.
    d1 = _device(vital_app, "d1")
    assert d1.post("/control?loop=temp", json={
        "action": "scenario", "value": "freezer"}).status_code == 200
    assert d1.post("/control?loop=temp", json={
        "action": "preset", "value": "fever"}).status_code == 200
    d2 = _device(vital_app, "d2")
    j2 = d2.get("/state?loop=temp").get_json()
    assert j2["preset"] is None and j2["now"]["env_temp"] == 22.0, (
        "device 1's demo reached device 2's body")

    # Devices 2 and 3 race the same challenge with different plays.
    for sid, plays in (("d2", True), ("d3", False)):
        c = _device(vital_app, sid)
        assert c.post("/control?loop=temp", json={
            "action": "challenge", "value": "cold_store",
            "label": sid}).status_code == 200
        runner = vital_app.registry.runners_for(sid)["temp"]
        window = runner.challenge["t_end"] - runner.challenge["t_start"]
        with runner.lock:
            if plays:                      # rest, then work the back half
                runner._step(int(window // 2))
            else:                          # rest the whole hour
                runner._step(int(window // 2))
        if plays:
            c.post("/control?loop=temp", json={"action": "exercise",
                                               "value": True})
        runner = vital_app.registry.runners_for(sid)["temp"]
        with runner.lock:
            runner._step(int(window - window // 2) + 60)
        report = c.get("/state?loop=temp").get_json()["challenge"]
        assert report.get("report"), f"{sid} finished with no report card"
    scores = {a["label"]: a["points"] for a in logged
              if a.get("name") == "cold_store"}
    assert set(scores) == {"d2", "d3"}, (
        "both teams' runs must land in the one shared log")
    assert scores["d2"] > scores["d3"], (
        "the team that worked the back half must out-score the team "
        "that rested - or the room's scores mean nothing")

    # Device 4 goes blind on water; device 5's spreadsheet stays open.
    d4 = _device(vital_app, "d4")
    assert d4.post("/control?loop=water", json={
        "action": "diagnose", "value": 5}).status_code == 200
    assert d4.get("/export.csv?loop=water").status_code == 409
    d5 = _device(vital_app, "d5")
    assert d5.get("/export.csv?loop=water").status_code == 200, (
        "device 4's blindfold covered device 5's eyes")
    # A RELOAD mid-case (new client, same cookie) is still mid-case,
    # still blind.
    d4_reloaded = _device(vital_app, "d4")
    j4 = d4_reloaded.get("/state?loop=water").get_json()
    assert j4["case"]["answered"] is False
    assert not any(k.endswith("_enabled") for k in j4["now"])
    answered = d4_reloaded.post("/control?loop=water", json={
        "action": "answer", "role": "control", "part": "pituitary"})
    assert answered.status_code == 200
    assert d4_reloaded.get("/state?loop=water").get_json(
        )["case"]["grade"]["verdict"] == "correct"

    # Device 6 clicks every wrong thing; the room keeps teaching.
    d6 = _device(vital_app, "d6")
    for bad in ({"action": "speed", "value": 7},
                {"action": "effector", "name": "gills", "on": False},
                {"action": "preset", "value": "consumption"},
                {"action": "diagnose", "value": 99},
                {}, {"action": None}):
        r = d6.post("/control?loop=temp", json=bad)
        assert r.status_code == 400 and r.get_json()["error"].strip()
    for sid in ("d1", "d2", "d3", "d4", "d5"):
        assert _device(vital_app, sid).get(
            "/state?loop=temp").status_code == 200

    # Every device hands its sandbox back, per-session.
    for sid in ("d1", "d2", "d3", "d4", "d5", "d6"):
        c = _device(vital_app, sid)
        for loop in vital_app.runners:
            c.post(f"/control?loop={loop}", json={"action": "reset"})
            j = c.get(f"/state?loop={loop}").get_json()
            assert "challenge" not in j and "case" not in j
            assert j["preset"] is None
            # Only loops that can BE blinded prove they are not.
            if loop in vital_app.CASES:
                assert any(k.endswith("_enabled") for k in j["now"])

    # And the projector never felt a thing.
    for loop, runner in vital_app.runners.items():
        assert runner.preset is None and runner.challenge is None, (
            f"the default {loop} runner was touched by the room")


def test_a_room_polling_at_once_never_errors(fresh_registry):
    """(jjj) Eight devices hammering the routes concurrently: every
    answer is a 200 (or a worded 400 for the deliberate wrong click),
    never a 500, and every session still teaches afterwards."""
    import threading as _threading
    vital_app = fresh_registry
    failures = []

    def storm(sid):
        c = _device(vital_app, sid)
        for i in range(15):
            r1 = c.get("/state?loop=temp")
            r2 = c.post("/control?loop=glucose",
                        json={"action": "speed", "value": 16})
            r3 = c.get("/export.csv?loop=water")
            r4 = c.post("/control?loop=temp",
                        json={"action": "speed", "value": 7})   # wrong
            for r, ok in ((r1, {200}), (r2, {200}), (r3, {200}),
                          (r4, {400})):
                if r.status_code not in ok:
                    failures.append((sid, i, r.status_code))

    threads = [_threading.Thread(target=storm, args=(f"storm-{n}",))
               for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not failures, f"the storm broke something: {failures[:5]}"
    for n in range(8):
        j = _device(vital_app, f"storm-{n}").get(
            "/state?loop=glucose").get_json()
        assert j["speed"] == 16, "a session lost its state in the storm"


def test_siadh_preset_is_a_complete_diagnosis():
    """(ddd) M32: SIADH is a row in the Phase 5 preset table — a full
    configuration on a healthy chassis, named in a banner, and CLEARED
    by Healthy like every disease before it. Diseases never stack
    (M18 decision 1)."""
    vital_app = _diag()
    WaterSimulation = _siadh()
    entry = vital_app.PRESETS["water"].get("siadh")
    assert entry is not None, "the water loop has no SIADH preset"
    assert entry["adh_override"] == 1.0
    assert "inappropriate" in entry["banner"].lower(), (
        "the banner must name the mechanism - secretion inappropriate "
        "to the stimulus IS the disease")
    sim = WaterSimulation()
    vital_app._apply_preset(sim, entry)
    sim.step(10)
    assert sim.state()["adh_override"] == 1.0
    vital_app._apply_preset(sim, vital_app.PRESETS["water"]["healthy"])
    sim.step(10)
    assert sim.state()["adh_override"] is None, (
        "Healthy left the SIADH knob set - a preset is a COMPLETE "
        "diagnosis and Healthy is the way back")


def test_siadh_is_in_the_diagnosis_game():
    """(ddd) M32: the disease the class can name is also a case they
    can be handed blind."""
    vital_app = _diag()
    siadh_cases = [c for c in vital_app.CASES["water"].values()
                   if c["setup"].get("adh_override")]
    assert siadh_cases, "no blind water case uses the SIADH knob"
    case = siadh_cases[0]
    assert case["answer"] == {"role": "control", "part": "pituitary"}, (
        "SIADH is a control-center failure - the machinery is intact "
        "and the signal is wrong, fever's pattern in a new loop")


# ================= Phase 10: the loops meet ===============================
# The first coupling in the project, and the rules that keep it honest:
#
#   * it is a THRESHOLD, not a leak. A healthy body's water loop must be
#     byte-identical coupled or not, because healthy glucose never crosses
#     180 mg/dL. If normal physiology feels the link at all, the link is
#     wrong;
#   * it may not rewrite an uncoupled lesson. Both engines carry a hash of
#     their FULL Phase 9 record, recorded from committed code before the
#     coupling was written;
#   * mellitus and insipidus must stay tellable apart. Both flood. One
#     floods DILUTE because the ADH signal is gone; the other floods
#     CONCENTRATED while ADH is maximal, because osmoles are dragging
#     water out. That contrast is the whole lesson and it is pinned.

# (aaaa) sha256 of json.dumps of the FULL Phase 9 record of
# _scripted_dosing_run / _scripted_water_run, both recorded 2026-08-17
# with M36 committed — the last state before the loops met.
GLUCOSE_PHASE9_HASH = \
    "58b550b44b95fc620f7f88f5fb70d2ff1f1ae8e267ef14fc7488cf1a4075330d"
WATER_PHASE9_HASH = \
    "edb2469f464dc41dfc858816f35e6a33ab78cf7c5cbb2370d34f6398ad53bdc6"

# Kickoff Phase 10 SS5: the frozen coupled-body record shape.
BODY_FIELDS = {
    "t",                # sim time, seconds
    "glucose",          # mg/dL - the sugar loop's controlled variable
    "insulin",
    "glucagon",
    "renal_loss",       # mg/dL/min spilling into the urine (the SOURCE)
    "tubular_load",     # mOsm/min arriving in the tubule (LINK 1, M37)
    "glucose_osm",      # mOsm/L the sugar adds to plasma (LINK 2, M38)
    "osmolarity",       # mOsm/L - the water loop's controlled variable
    "water_liters",
    "adh",
    "thirst",
    "urine_rate",       # mL/min - where the coupling shows up
    "urine_osm",        # mOsm/L - and what tells mellitus from insipidus
    # -- grown at M41: both loops' breaker flags, so a challenge can spot
    # a part being quietly switched back on and a case has something to
    # withhold. Never in VISIBLE_DURING_CASE.
    "beta_enabled", "alpha_enabled", "liver_enabled",
    "adh_enabled", "kidney_enabled", "water_access", "sensor_enabled",
}


def _body():
    """The coupled body, or SKIP loudly if not built yet (M37)."""
    if not (ENGINE_PKG / "body.py").exists():
        pytest.skip("engine/body.py doesn't exist yet - it arrives at M37")
    from engine.body import Body
    return Body


def _diabetic_day(Body, hours=12, meals=(2, 6, 10), grams=75, setup=None):
    """An untreated day: three ordinary meals, no insulin."""
    b = Body()
    if setup:
        setup(b)
    meal_ticks = {int(h * 3600) for h in meals}
    for tick in range(int(hours * 3600)):
        if tick in meal_ticks:
            b.eat(grams, 1.0)
        b.step(1)
    return b


def test_glucose_phase9_record_unchanged_by_phase10():
    """(aaaa) The spill readout may not move one recorded value."""
    import hashlib
    import json
    GlucoseSimulation = _glucose()
    records, _ = _scripted_dosing_run(GlucoseSimulation)
    fields = sorted(set(records[0]) - PHASE10_FIELDS_ADDED)
    subset = [{k: r[k] for k in fields} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == GLUCOSE_PHASE9_HASH, (
        "the Phase 9 glucose record changed - naming the kidney spill must "
        "be a READOUT, not a re-plumbing; `uptake` still includes it")


def test_water_phase9_record_unchanged_by_phase10():
    """(aaaa) And the water loop, uncoupled, is the loop it always was."""
    import hashlib
    import json
    WaterSimulation = _water()
    records, _ = _scripted_water_run(WaterSimulation)
    fields = sorted(set(records[0]) - {"tubular_load", "foreign_osm"})
    subset = [{k: r[k] for k in fields} for r in records]
    digest = hashlib.sha256(
        json.dumps(subset, sort_keys=True).encode()).hexdigest()
    assert digest == WATER_PHASE9_HASH, (
        "the Phase 9 water record changed - an uncoupled water loop must "
        "behave exactly as it did before Phase 10 existed")


def test_body_records_have_the_frozen_fields():
    Body = _body()
    b = Body()
    b.step(5)
    records = b.history()
    assert records, "history() returned nothing after stepping"
    for r in (records[0], records[-1], b.state()):
        assert set(r.keys()) == BODY_FIELDS, (
            f"Record fields {sorted(r.keys())} != frozen set "
            f"{sorted(BODY_FIELDS)} (Phase 10 kickoff SS5)")


def test_the_spill_is_a_threshold_not_a_leak():
    """(bbbb) LINK 1 has a threshold and must respect it absolutely: a
    healthy body, meals included, spills exactly nothing. If normal
    physiology loses sugar in its urine, the threshold is wrong."""
    Body = _body()
    b = _diabetic_day(Body, hours=6, meals=(1, 3), grams=75)   # healthy
    assert max(r["renal_loss"] for r in b.history()) == 0.0, (
        "a healthy body spilled sugar - normal glucose never crosses the "
        "180 mg/dL threshold, meals included")
    assert max(r["tubular_load"] for r in b.history()) == 0.0, (
        "a healthy body sent solute into the tubule from the sugar loop")


def test_a_body_at_the_set_point_is_exactly_the_standalone_loop():
    """(bbbb) The structural check on BOTH links at once. With glucose
    sitting at its set point neither link has anything to carry, and the
    coupled water loop must then be tick-for-tick the loop Phase 6 built.

    Note what this deliberately does NOT claim: that a FED healthy body
    matches too. Link 2 has no threshold and should not have one — a real
    post-meal glucose of 140 mg/dL really does add ~3 mOsm/L to plasma
    osmolarity, and pretending otherwise to keep a test tidy would be
    modelling the test instead of the body.
    """
    Body = _body()
    WaterSimulation = _water()
    b = Body()
    b.step(6 * 3600)            # fasting: glucose parked at 90
    solo = WaterSimulation()
    solo.step(6 * 3600)
    fields = [k for k in solo.state()
              if k not in ("tubular_load", "foreign_osm")]
    for i, (a, c) in enumerate(zip(solo.history(), b.water.history())):
        for k in fields:
            assert a[k] == c[k], (
                f"tick {i}: coupled water {k}={c[k]!r} but standalone "
                f"{k}={a[k]!r} - with nothing to couple, the water loop "
                "must be byte-identical to the one that has no sugar loop "
                "attached at all")


def test_a_healthy_fed_body_feels_only_a_whisper_of_the_sugar():
    """(bbbb) Link 2's honest bound: real, but small enough that the
    three single-loop lessons still hold. If an ordinary lunch moved
    plasma osmolarity appreciably, the coupling would be too strong."""
    Body = _body()
    b = _diabetic_day(Body, hours=6, meals=(1, 3), grams=75)   # healthy
    share = max(r["glucose_osm"] for r in b.history())
    assert 0.0 < share < 5.0, (
        f"a healthy fed body's sugar contributed {share:.1f} mOsm/L to "
        "plasma osmolarity - it should be a whisper (a few mOsm/L), "
        "neither absent nor loud")
    assert max(r["osmolarity"] for r in b.history()) < 296.0, (
        "an ordinary lunch pushed plasma osmolarity out of its normal "
        "range - the sugar term must not dominate a healthy body")


def test_untreated_mellitus_floods_with_sugar_loaded_urine():
    """(bbbb) The signature: copious urine that is MAXIMALLY concentrated,
    while ADH is high and working. The kidney is not failing to hold
    water - it is being forced to let water go with the sugar."""
    Body = _body()
    b = _diabetic_day(Body, setup=lambda s:
                      s.set_effector_enabled("beta", False))
    h = b.history()
    assert max(r["glucose"] for r in h) > 250.0, (
        "an untreated day never got hyperglycemic enough to spill")
    # Judged on ticks the SPILL is actually driving. A body that has just
    # had a drink floods too, dilutely, and so does a healthy one — so
    # "lots of urine" alone names nothing.
    spilling = [r for r in h if r["renal_loss"] > 2.0]
    signature = [r for r in spilling if r["urine_rate"] > 2.0
                 and r["urine_osm"] > 800.0 and r["adh"] > 0.5]
    assert len(signature) > 3600, (
        f"only {len(signature)} ticks of copious-AND-concentrated urine at "
        f"high ADH (out of {len(spilling)} spilling) - the mellitus "
        "signature must be a stretch of the lesson, not a blip")
    # And the water actually leaves: more urine than a healthy twin passes.
    healthy = _diabetic_day(Body)
    litres = sum(r["urine_rate"] for r in h) / 60.0 / 1000.0
    healthy_litres = sum(r["urine_rate"] for r in healthy.history()) \
        / 60.0 / 1000.0
    assert litres > healthy_litres * 1.4, (
        f"the diabetic body passed {litres:.2f} L against the healthy "
        f"body's {healthy_litres:.2f} L - the polyuria must be visible")


def test_insipidus_and_mellitus_flood_differently():
    """(bbbb) The M23 naming payoff, as a check. Both diseases pass water;
    the urine tells them apart, which is exactly why one was tasted and
    called tasteless and the other tasted and called honey-sweet."""
    Body = _body()
    mellitus = _diabetic_day(Body, setup=lambda s:
                             s.set_effector_enabled("beta", False))
    insipidus = _diabetic_day(Body, setup=lambda s:
                              s.set_effector_enabled("adh", False))

    # Mellitus is judged while the sugar is driving; insipidus has no
    # spill to judge by, so its flood is the whole flood.
    m_flood = [r for r in mellitus.history() if r["renal_loss"] > 1.0]
    i_flood = [r for r in insipidus.history() if r["urine_rate"] > 2.0]
    assert m_flood and i_flood, "both diseases must actually flood"

    m_osm = sum(r["urine_osm"] for r in m_flood) / len(m_flood)
    i_osm = sum(r["urine_osm"] for r in i_flood) / len(i_flood)
    assert m_osm > 800.0, (
        f"mellitus urine averaged {m_osm:.0f} mOsm/L while flooding - it "
        "must be LOADED, because solute is what is dragging the water")
    assert i_osm < 200.0, (
        f"insipidus urine averaged {i_osm:.0f} mOsm/L while flooding - it "
        "must be DILUTE, because nothing is telling the kidney to hold on")

    m_adh = sum(r["adh"] for r in m_flood) / len(m_flood)
    assert m_adh > 0.4, (
        "mellitus must flood WITH its ADH working - a broken hormone is "
        "the other disease, and confusing them is the mistake this case "
        "exists to prevent")


def test_the_spill_conversion_is_derived_not_typed():
    """(cccc) The mg/dL/min -> mOsm/min factor must fall out of the pool
    size the glucose engine already declares, so changing that pool
    changes the coupling honestly instead of silently disagreeing."""
    _body()
    from engine import body
    from engine.glucose import CARB_TO_MGDL
    assert body.GLUCOSE_SPACE_DL == pytest.approx(1000.0 / CARB_TO_MGDL), (
        "the glucose space must be READ from CARB_TO_MGDL, not retyped")
    assert body.MGDL_MIN_TO_MOSM_MIN == pytest.approx(
        body.GLUCOSE_SPACE_DL / body.GLUCOSE_MW)
    assert body.MGDL_MIN_TO_MOSM_MIN == pytest.approx(1.0, abs=0.05), (
        "the factor should land near 1 mOsm per mg/dL/min for a ~180 dL "
        "pool and a ~180 mg/mmol sugar - if it has drifted far from that, "
        "one of the two numbers is wrong")


def test_tubular_load_rejects_nonsense():
    """(cccc)"""
    WaterSimulation = _water()
    sim = WaterSimulation()
    with pytest.raises(ValueError):
        sim.set_tubular_load(-1.0)
    sim.set_tubular_load(0.0)      # uncoupled is legal
    sim.set_tubular_load(3.0)
    sim.step(10)
    assert sim.state()["tubular_load"] == 3.0


def test_body_rejects_an_unknown_part():
    Body = _body()
    b = Body()
    with pytest.raises(KeyError):
        b.set_effector_enabled("pancreas_ish", False)
    b.set_effector_enabled("beta", False)      # a sugar part
    b.set_effector_enabled("kidney", False)    # and a water part


def _scripted_body_run():
    """Exercises both loops and the link, for the determinism check."""
    Body = _body()
    b = Body()
    b.step(600)
    b.set_effector_enabled("beta", False)
    b.eat(90, 1.0)
    b.step(3600)
    b.drink(500)
    b.set_exercise(True)
    b.step(1800)
    b.set_exercise(False)
    b.inject(4)
    b.step(3600)
    return b.history(), b.doses(), b.drinks()


def test_body_is_deterministic():
    assert _scripted_body_run() == _scripted_body_run(), (
        "Two identical coupled runs diverged (kickoff SS2)")


# ---------------- M38: the second link, and the spiral ----------------
# Sugar does not only leave — while it is still in the blood it is an
# OSMOLE, and the osmoreceptors can feel it. That is the "hyperosmolar"
# in hyperosmolar hyperglycemic state, and it is what makes an untreated
# diabetic thirsty. Without it the M37 body passed extra urine and barely
# asked for a drink, which is not the disease anybody recognises.

def test_sugar_in_the_blood_is_an_osmole_the_receptors_feel():
    """(eeee) The derived factor, and that it reaches the sensors."""
    _body()
    from engine import body
    assert body.MGDL_TO_MOSM_L == pytest.approx(10.0 / body.GLUCOSE_MW)
    assert body.MGDL_TO_MOSM_L == pytest.approx(1.0 / 18.0, abs=0.002), (
        "a mg/dL of glucose should be about 1/18 of a mOsm/L - the "
        "clinical formula's 'glucose over 18', which this must agree with")
    Body = _body()
    b = _diabetic_day(Body, hours=4, meals=(1,), grams=100,
                      setup=lambda s: s.set_effector_enabled("beta", False))
    h = b.history()
    assert max(r["glucose_osm"] for r in h) > 5.0, (
        "hyperglycemia added almost nothing to plasma osmolarity - the "
        "second link is not connected")
    peak = max(h, key=lambda r: r["glucose_osm"])
    assert peak["glucose_osm"] == pytest.approx(
        (peak["glucose"] - 90.0) * body.MGDL_TO_MOSM_L), (
        "the sugar's osmolar share must be the EXCESS above the normal "
        "fasting level, not the whole of it - the water loop's 290 "
        "baseline already has ordinary sugar dissolved in it")


def test_untreated_mellitus_is_thirsty():
    """(eeee) Polydipsia, the third leg of the classic triad. The measure
    is how often the body reaches for a glass by itself - thirst itself
    is a sawtooth capped by the drinking threshold (M20), so the DRINKING
    is the signal, not the thirst number."""
    Body = _body()
    mellitus = _diabetic_day(Body, setup=lambda s:
                             s.set_effector_enabled("beta", False))
    healthy = _diabetic_day(Body)
    m_l = sum(d["ml"] for d in mellitus.drinks()) / 1000.0
    h_l = sum(d["ml"] for d in healthy.drinks()) / 1000.0
    assert m_l > 2.0 * h_l, (
        f"the diabetic body drank {m_l:.2f} L against the healthy body's "
        f"{h_l:.2f} L - polydipsia must be unmistakable, not marginal")


def test_the_loop_compensates_until_it_cannot():
    """(eeee) The spiral, and the fact that it is a spiral ONLY when the
    behavioral arm is cut. With a bottle in reach the loop defends
    osmolarity and pays for it in liters; take the bottle away and the
    same body runs past the dehydration line."""
    Body = _body()
    coping = _diabetic_day(Body, setup=lambda s:
                           s.set_effector_enabled("beta", False))
    stranded = _diabetic_day(Body, setup=lambda s: (
        s.set_effector_enabled("beta", False),
        s.set_effector_enabled("access", False)))

    coping_peak = max(r["osmolarity"] for r in coping.history())
    assert coping_peak < 300.0, (
        f"a diabetic body WITH water peaked at {coping_peak:.1f} mOsm/L - "
        "while it can still drink, the loop is supposed to hold the line "
        "(and the cost shows up as liters, not as osmolarity)")

    h = stranded.history()
    stranded_peak = max(r["osmolarity"] for r in h)
    assert stranded_peak > DEHYDRATION_LINE, (
        f"a diabetic body with NO water only reached {stranded_peak:.1f} "
        "mOsm/L - the spiral must actually cross 305")
    assert max(r["thirst"] for r in h) == pytest.approx(1.0), (
        "a body this dry must be maximally thirsty - the alarm works, it "
        "just has nothing to reach for")
    # And it is one-way: the last hour is drier than the first.
    early = [r["osmolarity"] for r in h[:3600]]
    late = [r["osmolarity"] for r in h[-3600:]]
    assert min(late) > max(early), (
        "the stranded body's osmolarity must climb monotonically enough "
        "that its last hour is drier than its first - a spiral, not a "
        "wobble")


def test_foreign_osmoles_reject_nonsense():
    """(eeee)"""
    WaterSimulation = _water()
    sim = WaterSimulation()
    with pytest.raises(ValueError):
        sim.set_foreign_osmoles(-1.0)
    sim.set_foreign_osmoles(0.0)
    sim.set_foreign_osmoles(13.8)
    sim.step(1)
    assert sim.state()["foreign_osm"] == 13.8
    assert sim.state()["osmolarity"] > 300.0, (
        "foreign osmoles must show up in the osmolarity this loop "
        "reports - they are part of the real number, not an annotation")


# ---------------- M41: the coupled body joins the lesson grammar ----------

def _ward_play(vital_app, cid, doses=(), glass_every=0):
    """Drive a ward challenge through the PRODUCTION path, using only
    moves the buttons actually offer: 4 U doses and 250 mL glasses."""
    from engine.body import Body
    runner = vital_app.Runner(Body(), "body")
    vital_app.start_challenge(runner, "body", cid, None)
    total = int(runner.challenge["t_end"] - runner.challenge["t_start"])
    moves = [(int(m * 60), lambda s: s.inject(4)) for m in doses]
    if glass_every:
        moves += [(int(m * 60), lambda s: s.drink(250))
                  for m in range(0, 180, glass_every)]
    done = 0
    for at, fn in sorted(moves, key=lambda m: m[0]):
        at = min(at, total)
        if at > done:
            with runner.lock:
                runner._step(at - done)
            done = at
        fn(runner.sim)
    with runner.lock:
        runner._step(total + 60 - done)
    block = runner.snapshot(-1)["challenge"]
    return block["score"], block["report"]


def test_the_ward_round_needs_BOTH_loops_treated():
    """(ffff) The whole reason this challenge exists. Insulin alone and
    fluids alone must both fall short of the play that does both — or
    the coupled body is just the glucose loop with extra charts."""
    vital_app = _game()
    if "body" not in vital_app.CHALLENGES:
        pytest.skip("the ward round doesn't exist yet - M41")
    both, both_rep = _ward_play(vital_app, "ward_round", doses=(0,),
                                glass_every=30)
    sugar_only, sugar_rep = _ward_play(vital_app, "ward_round", doses=(0,))
    water_only, water_rep = _ward_play(vital_app, "ward_round",
                                       glass_every=30)
    nothing, nothing_rep = _ward_play(vital_app, "ward_round")

    assert both_rep["met"], (
        "treating the sugar AND replacing the water must actually pass - "
        "a challenge nobody can win teaches nothing")
    assert not sugar_rep["met"], (
        "insulin alone met the goal - then the water half of this "
        "patient is decoration")
    assert not water_rep["met"], "fluids alone met the goal"
    assert both["points"] > sugar_only["points"], (
        f"treating both scored {both['points']} against insulin alone's "
        f"{sugar_only['points']} - doing the whole job must pay")
    assert both["points"] > water_only["points"]
    assert min(sugar_only["points"], water_only["points"]) >         nothing["points"], "half a treatment must still beat none"
    assert both["medal"] == "gold" and sugar_only["medal"] != "gold", (
        "gold must be unreachable without treating both loops (M26's "
        "calibration rule)")


def test_over_dosing_the_ward_patient_is_punished():
    """(ffff) The other half of the lesson: more insulin is not better
    treatment. Three doses in three hours drives them hypo."""
    vital_app = _game()
    if "body" not in vital_app.CHALLENGES:
        pytest.skip("M41")
    good, _ = _ward_play(vital_app, "ward_round", doses=(0,),
                         glass_every=30)
    heavy, heavy_rep = _ward_play(vital_app, "ward_round",
                                  doses=(0, 45, 90), glass_every=30)
    lo = {r["key"]: r for r in heavy_rep["rows"]}["lowest"]
    assert not lo["met"], (
        "three doses of insulin in three hours left the patient safe - "
        "the easiest way to kill this patient must still be insulin")
    assert heavy["points"] < good["points"] - 20, (
        f"over-dosing scored {heavy['points']} against {good['points']} - "
        "it has to cost real marks")


def test_mellitus_and_insipidus_are_tellable_apart_in_the_cases():
    """(gggg) The two cases share a brief WORD FOR WORD, so the urine is
    the only thing that separates them. Pin that it really does."""
    vital_app = _game()
    if "body" not in getattr(vital_app, "CASES", {}):
        pytest.skip("M41")
    cases = vital_app.CASES["body"]
    mel = cases["case1"]
    ins = cases["case2"]
    assert mel["brief"] == ins["brief"], (
        "the two diabetes cases must read identically - reading the "
        "story instead of the charts has to earn nothing")
    assert mel["answer"] != ins["answer"]

    from engine.body import Body
    out = {}
    for name, case in (("mellitus", mel), ("insipidus", ins)):
        sim = Body()
        vital_app._apply_preset(sim, case["setup"])
        for method, args in case.get("start_actions", []):
            getattr(sim, method)(*args)
        sim.step(case["warmup_s"])
        h = [r for r in sim.history() if r["t"] > case["warmup_s"] / 2]
        flood = [r for r in h if r["urine_rate"] > 2.0]
        assert flood, f"{name} never actually floods - no case to solve"
        out[name] = (sum(r["urine_osm"] for r in flood) / len(flood),
                     max(r["glucose"] for r in h))
    assert out["mellitus"][0] > 600.0, (
        f"mellitus urine averaged {out['mellitus'][0]:.0f} mOsm/L while "
        "flooding - it must be LOADED")
    assert out["insipidus"][0] < 200.0, (
        f"insipidus urine averaged {out['insipidus'][0]:.0f} mOsm/L - it "
        "must be nearly pure water")
    assert out["mellitus"][1] > 250.0 and out["insipidus"][1] < 150.0, (
        "the glucose traces must separate them too - that is the second "
        "half of the evidence")


def test_a_blind_body_case_withholds_the_breaker_flags():
    """(gggg) The coupled body records both loops' flags now (M41), so
    the allowlist has real work to do here."""
    vital_app = _game()
    if "body" not in getattr(vital_app, "CASES", {}):
        pytest.skip("M41")
    keep = vital_app.VISIBLE_DURING_CASE["body"]
    from engine.body import Body
    record = Body().state()
    assert set(keep) < set(record), (
        "the body allowlist must be a STRICT subset of its record - "
        "there are flags in there that name the answer")
    out = vital_app.redact_record("body", record)
    assert not [k for k in out if k.endswith("_enabled")]
    assert "water_access" not in out


def test_the_sandbox_only_exception_is_over():
    """(gggg) M39 declared the coupled body sandbox-only and time-boxed
    it to M41. This is the box."""
    vital_app = _game()
    assert getattr(vital_app, "SANDBOX_ONLY_LOOPS", set()) == set(), (
        "a loop is still declared sandbox-only - every loop was supposed "
        "to carry the whole lesson grammar by the end of Phase 10")


def test_neither_engine_imports_the_other():
    """(dddd) The Body owns both loops and passes one number between them.
    If the engines start importing each other, each loop stops being
    independently testable and 'loop-agnostic where cheap' is over."""
    if not (ENGINE_PKG / "body.py").exists():
        pytest.skip("engine/body.py doesn't exist yet - M37")
    pairs = [("glucose.py", "water"), ("water.py", "glucose")]
    for filename, forbidden in pairs:
        tree = ast.parse((ENGINE_PKG / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert forbidden not in name, (
                    f"engine/{filename} imports {name} - the two loops must "
                    "stay independent; engine/body.py is what joins them")


# ================= M42: the full pass, four loops ==========================
# Phase 10 closes the way 8 and 9 did — the whole promise, checkable. The
# new claim this phase has to answer for is the one the kickoff put in
# capitals: a coupled model must never quietly rewrite an uncoupled
# lesson. So the pass drives all FOUR loops and then goes back and looks
# at the three that were here before.

def test_the_whole_period_on_four_loops(lab):
    """(hhhh) Every loop, every mode, one room — and the three
    single-loop lessons still exactly as Phase 9 left them."""
    vital_app, logged = lab
    client = vital_app.app.test_client()

    # 1. Every loop teaches every verb (M30's grammar, now four wide).
    for loop in vital_app.runners:
        assert loop in vital_app.PRESETS and "healthy" in vital_app.PRESETS[loop]
        entries = vital_app.CHALLENGES[loop]
        assert any(not e.get("events") for e in entries.values())
        assert any(e.get("events") for e in entries.values())
        assert len(vital_app.CASES[loop]) >= 2
        assert vital_app.CSV_FIELDS[loop] and vital_app.ANSWER_OPTIONS[loop]
        assert loop in vital_app.WORKSHEETS

    # 2. Disturb, break, name, diagnose — driven through the routes.
    for loop in vital_app.runners:
        disease = next(k for k in vital_app.PRESETS[loop] if k != "healthy")
        assert client.post(f"/control?loop={loop}",
                           json={"action": "preset",
                                 "value": disease}).status_code == 200
        assert client.get(f"/state?loop={loop}").get_json()["preset"]
        n_cases = len(vital_app.CASES[loop])
        for n in range(1, n_cases + 1):
            assert client.post(f"/control?loop={loop}",
                               json={"action": "diagnose",
                                     "value": n}).status_code == 200
            j = client.get(f"/state?loop={loop}").get_json()
            banned = sorted(k for k in j["now"]
                            if k.endswith("_enabled") or k in ANSWER_KEY_FIELDS)
            assert not banned, f"{loop} case {n} leaked {banned}"
            assert client.get(f"/export.csv?loop={loop}").status_code == 409
            truth = list(vital_app.CASES[loop].values())[n - 1]["answer"]
            assert client.post(f"/control?loop={loop}",
                               json={"action": "answer", **truth}
                               ).status_code == 200
            j = client.get(f"/state?loop={loop}").get_json()
            assert j["case"]["grade"]["verdict"] == "correct"
        client.post(f"/control?loop={loop}", json={"action": "reset"})
        assert client.get(f"/export.csv?loop={loop}").status_code == 200

    # 3. And every loop hands back a gameless sandbox.
    for loop in vital_app.runners:
        j = client.get(f"/state?loop={loop}").get_json()
        assert "challenge" not in j and "case" not in j
        assert j["preset"] is None
        assert any(k.endswith("_enabled") for k in j["now"])


def test_phases_1_to_9_are_untouched():
    """(hhhh) The kickoff's capitalised promise, as a check. Both engine
    hashes are asserted elsewhere; this is the APP-level half — the three
    single-loop pages still offer exactly what they offered."""
    vital_app = _game()
    client = vital_app.app.test_client()
    page = client.get("/").data.decode("utf-8")
    for marker in ('data-loop="temp"', 'data-loop="glucose"',
                   'data-loop="water"', 'data-preset="fever"',
                   'data-preset="type1"', 'data-preset="central_di"',
                   'data-preset="siadh"', 'id="page-temp"',
                   'id="page-glucose"', 'id="page-water"'):
        assert marker in page, (
            f"{marker} vanished from the page - Phase 10 was supposed to "
            "ADD a loop, not edit the three that were already teaching")
    # The three original loops' challenges and cases are all still there.
    assert len(vital_app.CASES["temp"]) == 4
    assert len(vital_app.CASES["glucose"]) == 4
    assert len(vital_app.CASES["water"]) == 5
    for loop, names in (("temp", {"cold_store", "blast_freezer"}),
                        ("glucose", {"t1_shift", "crisis_shift"}),
                        ("water", {"aid_station", "race_day"})):
        assert set(vital_app.CHALLENGES[loop]) == names, (
            f"the {loop} loop's challenges changed in Phase 10")


def test_a_coupled_run_is_still_deterministic_through_the_routes(lab):
    """(hhhh) The promise the whole game layer rests on, extended to the
    loop that has two engines in it: same challenge, same play, byte-
    identical history — no matter what the sandbox was doing first."""
    vital_app, _ = lab
    runs = []
    for lead_in in (lambda r: None,
                    lambda r: (r.sim.eat(80, 1.0), r.sim.step(900))):
        runner = vital_app.registry.runners_for("determinism-probe")["body"]
        runner.sim.reset()
        lead_in(runner)
        vital_app.start_challenge(runner, "body", "ward_round", None)
        with runner.lock:
            runner._step(1800)
        runs.append(runner.sim.history())
    assert runs[0] == runs[1], (
        "the same ward round produced different physiology depending on "
        "what the tab had been doing beforehand - two teams' report "
        "cards are only comparable if the run starts the same way")
    assert runs[0][0]["t"] == 0.0


WEB_MODULES = {"flask", "jinja2", "werkzeug"}


def test_engine_imports_no_web_framework():
    if not ENGINE_PKG.exists():
        pytest.skip("engine/ doesn't exist yet - it arrives at M1")
    offenders = []
    for path in ENGINE_PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".")[0] in WEB_MODULES:
                    offenders.append(f"{path.name}: {name}")
    assert not offenders, (
        "engine/ must stay pure Python (kickoff SS3) but imports web "
        f"frameworks: {offenders}")


# ================= M43: periods and the join screen ========================
# Phase 11 begins: a device may claim a class period and a team name. The
# claims ride in cookies the page sets and the server only reads (the
# vl_sid pattern), the teacher's list lives in periods.txt, and the whole
# feature must switch itself OFF quietly when that file is missing or
# empty — the join step can never block the lesson (Phase 11 kickoff SS2).

def _periods_module():
    if not (ROOT / "periods.py").exists():
        pytest.skip("periods.py doesn't exist yet - it arrives at M43")
    import periods
    return periods


def _rooms_app():
    import app as vital_app
    if not hasattr(vital_app, "PERIODS"):
        pytest.skip("app.PERIODS doesn't exist yet - it arrives at M43")
    return vital_app


def test_periods_file_parses_comments_blanks_dupes_and_order(tmp_path):
    periods = _periods_module()
    f = tmp_path / "periods.txt"
    f.write_text("# the teacher's list\n\nP1\n  P3  \nP1\nP7\n# done\n",
                 encoding="utf-8")
    assert periods.load_periods(f) == ["P1", "P3", "P7"], (
        "comments and blanks ignored, whitespace stripped, duplicates "
        "dropped, and the teacher's order kept - the join screen renders "
        "this list verbatim")


def test_missing_or_empty_periods_file_turns_joining_off(tmp_path):
    periods = _periods_module()
    assert periods.load_periods(tmp_path / "not_there.txt") == [], (
        "a missing periods.txt must mean [] - joining quietly off, "
        "never an exception at launch")
    f = tmp_path / "comments_only.txt"
    f.write_text("# nothing today\n\n", encoding="utf-8")
    assert periods.load_periods(f) == [], (
        "a file of nothing but comments is an empty list too")


def test_the_join_overlay_renders_only_when_joining_is_on(monkeypatch):
    vital_app = _rooms_app()
    client = vital_app.app.test_client()
    monkeypatch.setattr(vital_app, "PERIODS", ["P1", "P4"])
    page = client.get("/").data.decode("utf-8")
    assert 'id="joinOverlay"' in page and 'data-period="P4"' in page, (
        "with periods on the list, the page must carry the join screen "
        "and a button per period")
    monkeypatch.setattr(vital_app, "PERIODS", [])
    page = client.get("/").data.decode("utf-8")
    assert 'id="joinOverlay"' not in page, (
        "an empty periods.txt must remove the join screen from the page "
        "entirely - quietly off, not an empty overlay")


def test_a_session_wears_its_period_and_team(fresh_registry, monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "PERIODS"):
        pytest.skip("app.PERIODS doesn't exist yet - it arrives at M43")
    monkeypatch.setattr(vital_app, "PERIODS", ["P1", "P3"])
    c = vital_app.app.test_client()
    c.set_cookie("vl_sid", "badge-kid")
    c.set_cookie("vl_period", "P3")
    c.set_cookie("vl_team", "The%20Mongooses")   # JS encodeURIComponent
    assert c.get("/state?loop=temp").status_code == 200
    assert vital_app.registry.identity("badge-kid") == {
        "period": "P3", "team": "The Mongooses"}, (
        "the session must mirror the cookies' period and team - the "
        "room views (M45) read this")


def test_a_period_off_the_list_counts_as_unassigned(fresh_registry,
                                                    monkeypatch):
    """Last year's cookie, or hand-edited junk: never an error on a
    student's phone, just Unassigned."""
    vital_app = fresh_registry
    if not hasattr(vital_app, "PERIODS"):
        pytest.skip("app.PERIODS doesn't exist yet - it arrives at M43")
    monkeypatch.setattr(vital_app, "PERIODS", ["P1"])
    c = vital_app.app.test_client()
    c.set_cookie("vl_sid", "stale-kid")
    c.set_cookie("vl_period", "P9")
    assert c.get("/state?loop=temp").status_code == 200
    assert vital_app.registry.identity("stale-kid")["period"] == "", (
        'a period that is not on the teacher\'s list must land as "" '
        "(Unassigned), not as a made-up period of one")


def test_the_cookieless_world_never_joins_anything(fresh_registry):
    """verify.py, pytest and curl present no vl_sid - a period cookie
    alone must seat nobody, and the default session stays periodless,
    which is what keeps eleven phases of tests meaning what they meant."""
    vital_app = fresh_registry
    c = vital_app.app.test_client()
    c.set_cookie("vl_period", "P1")              # note: no vl_sid
    assert c.get("/state?loop=temp").status_code == 200
    assert vital_app.registry.count() == 0, (
        "a period claim without a session id seated someone in the "
        "registry - the cookieless world must stay the module-level "
        "default session, untouched")


def test_a_swept_session_gets_its_period_back_from_the_cookie():
    """Eviction and restarts stay free BECAUSE the cookie is the source
    of truth: the browser re-presents its claims on the next request."""
    from sessions import SessionRegistry
    t = {"now": 0.0}
    reg = SessionRegistry(lambda: {"temp": object()}, max_sessions=5,
                          idle_s=100, clock=lambda: t["now"])
    reg.runners_for("kid", period="P3", team="The Mongooses")
    t["now"] = 500.0                             # long past idle_s
    reg.runners_for("kid", period="P3", team="The Mongooses")
    assert reg.identity("kid") == {"period": "P3",
                                   "team": "The Mongooses"}, (
        "a swept session that rejoined with the same cookies lost its "
        "period - eviction must cost a student nothing")
    # And a touch with NO claims (None) must never erase a real one.
    reg.runners_for("kid")
    assert reg.identity("kid")["period"] == "P3", (
        "a claimless touch (period=None) erased a stored period - None "
        'means "no claim", only "" and real names are claims')


def test_identity_is_read_only_and_never_seats_anyone():
    from sessions import SessionRegistry
    if not hasattr(SessionRegistry, "identity"):
        pytest.skip("SessionRegistry.identity doesn't exist yet - M43")
    reg = SessionRegistry(lambda: {"temp": object()}, max_sessions=5,
                          idle_s=100)
    assert reg.identity("ghost") is None, (
        "asking about an unknown sid must answer None, not create it")
    assert reg.count() == 0, (
        "identity() seated a session - the room views must be read-only")


# ================= M44: the leaderboard learns periods =====================
# An attempt now says whose CLASS it was, and the board a device sees is
# its own class's — while the projector, having skipped the join screen,
# keeps showing everyone. Old logs have no period key and must keep
# loading and displaying: "" and "no key" read identically (Unassigned).

def _m44():
    vital_app = _h2h()
    if "period" not in vital_app.build_attempt(
            "temp", "cold_store", {"met": True, "rows": []},
            {"points": 0, "medal": None, "rows": [], "zeroed": None}):
        pytest.skip("attempts don't carry period yet - it arrives at M44")
    return vital_app


def test_an_attempt_is_stamped_with_the_requesters_period(monkeypatch):
    vital_app = _m44()
    monkeypatch.setattr(vital_app, "PERIODS", ["P1", "P3"])
    report = {"met": True, "rows": []}
    score = {"points": 50, "medal": None, "rows": [], "zeroed": None}
    with vital_app.app.test_request_context(
            "/", headers={"Cookie": "vl_period=P3"}):
        att = vital_app.build_attempt("water", "aid_station", report, score)
    assert att["period"] == "P3", (
        "an attempt built during a P3 session's request must be stamped "
        "P3 - stamped at build time, never inferred later")
    att = vital_app.build_attempt("water", "aid_station", report, score)
    assert att["period"] == "", (
        'outside any request (tests, console) the stamp is "" - '
        "Unassigned, same as a pre-M44 record reads")
    grade = {"points": 100, "correct": True, "rows": [],
             "answer": {"role": "receptor", "part": "beta"}}
    with vital_app.app.test_request_context(
            "/", headers={"Cookie": "vl_period=P3"}):
        catt = vital_app.build_case_attempt("glucose", "case_1", grade)
    assert catt["period"] == "P3", "diagnosis attempts carry the class too"


def test_the_board_scopes_by_period_and_old_records_survive(monkeypatch):
    vital_app = _m44()
    log = [
        _run(70, None, False, [], label="Old World", rid=1),   # no key at all
        {**_run(88, "gold", True, [], label="Third Period", rid=2,
                when="2026-08-18T10:00:00"), "period": "P3"},
        {**_run(95, "gold", True, [], label="Fifth Period", rid=3,
                when="2026-08-18T11:00:00"), "period": "P5"},
    ]
    monkeypatch.setattr(vital_app, "ATTEMPTS", log)
    names = lambda board: [e["label"] for e in board]
    assert names(vital_app.leaderboard("water", "aid_station",
                                       period=None)) == \
        ["Fifth Period", "Third Period", "Old World"], (
        "period=None is everyone - including records from before M44")
    assert names(vital_app.leaderboard("water", "aid_station",
                                       period="P3")) == ["Third Period"], (
        "a scoped board shows that class's runs and no other")
    assert names(vital_app.leaderboard("water", "aid_station",
                                       period="")) == ["Old World"], (
        'the "" scope is the Unassigned class, and a pre-M44 record '
        "(no key) belongs to it - old logs must keep displaying")
    best = vital_app.best_attempt("water", "aid_station", period="P3")
    assert best["label"] == "Third Period" and best["runs"] == 1, (
        "the card's best-so-far line scopes like the board: your "
        "class's best, not the school's")


def test_state_carries_the_scoped_board_and_names_its_scope(
        fresh_registry, monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "PERIODS"):
        pytest.skip("app.PERIODS doesn't exist yet - it arrives at M43")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3", "P5"])
    monkeypatch.setattr(vital_app, "ATTEMPTS", [
        {**_run(88, "gold", True, [], label="Third Period", rid=1),
         "period": "P3"},
        {**_run(95, "gold", True, [], label="Fifth Period", rid=2),
         "period": "P5"},
    ])
    c = vital_app.app.test_client()
    c.set_cookie("vl_sid", "p3-kid")
    c.set_cookie("vl_period", "P3")
    j = c.get("/state?loop=water").get_json()
    assert j["board_period"] == "P3", (
        "/state must say whose board it is carrying - the page renders "
        "this label, it never guesses")
    assert [e["label"] for e in j["leaderboard"]["aid_station"]] == \
        ["Third Period"], "a P3 device's poll carries P3's board only"
    projector = vital_app.app.test_client()   # cookieless: the projector
    j = projector.get("/state?loop=water").get_json()
    assert j["board_period"] is None
    assert [e["label"] for e in j["leaderboard"]["aid_station"]] == \
        ["Fifth Period", "Third Period"], (
        "the Unassigned viewer (the projector) sees everyone - that "
        "symmetry is the design, not a fallback")


# ================= M45: /teacher - the PIN and the room list ===============
# The teacher's door. Three promises: the PIN actually gates it, LOOKING
# at the room never moves anybody's simulation, and the page is safe to
# project - a blind case shows by number, never by name.

def _teacher_app():
    import app as vital_app
    if not hasattr(vital_app, "TEACHER_PIN"):
        pytest.skip("TEACHER_PIN doesn't exist yet - it arrives at M45")
    return vital_app


def test_the_pin_gates_the_room(monkeypatch):
    vital_app = _teacher_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    c = vital_app.app.test_client()
    page = c.get("/teacher")
    assert page.status_code == 200
    body = page.data.decode("utf-8")
    assert 'name="pin"' in body, "no cookie must mean the PIN form"
    assert "PIN-SENTINEL-XYZ" not in body, (
        "the PIN is printed in the CONSOLE, never in a page")
    wrong = c.post("/teacher", data={"pin": "0000"})
    assert wrong.status_code == 403
    assert "match this launch" in wrong.data.decode("utf-8"), (
        "a wrong PIN is refused in words, not a bare status code")
    right = c.post("/teacher", data={"pin": "PIN-SENTINEL-XYZ"})
    assert right.status_code == 302
    room = c.get("/teacher")          # the client keeps the cookie
    assert room.status_code == 200
    assert 'name="pin"' not in room.data.decode("utf-8"), (
        "the right PIN must land on the room, not the form again")


def test_the_pin_is_per_launch_but_pinnable(monkeypatch):
    vital_app = _teacher_app()
    monkeypatch.setenv("VL_TEACHER_PIN", "7777")
    assert vital_app._mint_pin() == "7777", (
        "VL_TEACHER_PIN must pin the PIN - a rehearsed lesson needs a "
        "rehearsable login")
    monkeypatch.delenv("VL_TEACHER_PIN")
    minted = vital_app._mint_pin()
    assert len(minted) == 4 and minted.isdigit(), (
        "an unforced PIN is four digits a teacher can read off a "
        "console and type on a phone")


def test_looking_at_the_room_moves_no_simulation(fresh_registry,
                                                 monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "TEACHER_PIN"):
        pytest.skip("TEACHER_PIN doesn't exist yet - it arrives at M45")
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    kid = _device(vital_app, "watched-kid")
    assert kid.get("/state?loop=temp").status_code == 200
    runners = vital_app.registry.runners_for("watched-kid")
    before = {loop: list(r.sim.history()) for loop, r in runners.items()}
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    assert teacher.get("/teacher").status_code == 200
    after = {loop: list(r.sim.history()) for loop, r in runners.items()}
    assert before == after, (
        "rendering the dashboard changed a student's history - the room "
        "view must be READ-ONLY, byte for byte")


def test_a_blind_case_shows_by_number_never_by_name(fresh_registry,
                                                    monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "TEACHER_PIN"):
        pytest.skip("TEACHER_PIN doesn't exist yet - it arrives at M45")
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    kid = _device(vital_app, "blind-kid")
    assert kid.post("/control?loop=temp",
                    json={"action": "diagnose", "value": 1,
                          "label": "Team Screen"}).status_code == 200
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    body = teacher.get("/teacher").data.decode("utf-8")
    assert "case 1 of" in body and "blind" in body, (
        "the teacher must SEE that a device is mid-case and unanswered")
    for label in ("Fever", "Heat stroke", "Hypothermia"):
        assert label not in body, (
            f'"{label}" is on the projected teacher page while a temp '
            "case is BLIND - a diagnosis name on screen ends the game")


def test_teacher_appears_in_no_student_surface(monkeypatch):
    vital_app = _teacher_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    c = vital_app.app.test_client()
    assert "/teacher" not in c.get("/").data.decode("utf-8"), (
        "the student page must not advertise the teacher's door")
    state = c.get("/state?loop=temp").data.decode("utf-8")
    assert "/teacher" not in state and "PIN-SENTINEL-XYZ" not in state, (
        "the PIN and the teacher route belong to the console and the "
        "teacher's own device, never to a student payload")


def test_room_never_touches_last_seen():
    from sessions import SessionRegistry
    if not hasattr(SessionRegistry, "room"):
        pytest.skip("SessionRegistry.room doesn't exist yet - M45")
    t = {"now": 0.0}
    reg = SessionRegistry(lambda: {"temp": object()}, max_sessions=5,
                          idle_s=100, clock=lambda: t["now"])
    reg.runners_for("kid")                       # seated at t=0
    t["now"] = 90.0
    assert len(reg.room()) == 1, "an active session is in the room"
    t["now"] = 101.0                             # 101 s since the SEAT
    assert reg.room() == [], (
        "the room() call at t=90 kept the session alive - a room view "
        "must never touch last_seen, or closed tabs live forever")


# ================= M46: who's stuck ========================================
# The dashboard learns judgment. Three flags, swept before pinning (the
# M38 lesson): a blind case unanswered past 5 min (a decisive team reads
# the charts in 2-4), a device quiet past 3 min (a live page polls at
# 4 Hz; phones auto-sleep inside 2 min), and a SECOND zero-medal run of
# one challenge (at 11+ wall-min a run, the second is when to walk over).

def _stuck_app():
    import app as vital_app
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("the stuck thresholds don't exist yet - M46")
    return vital_app


def test_the_stuck_thresholds_are_pinned_policy():
    vital_app = _stuck_app()
    assert vital_app.STUCK_BLIND_S == 300
    assert vital_app.STUCK_QUIET_S == 180
    assert vital_app.STUCK_ZEROES == 2, (
        "tunable policy, but tuned WITH this pin - the reasoning lives "
        "beside the constants in app.py")


def test_game_stamps_carry_wall_start(fresh_registry):
    vital_app = fresh_registry
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M46")
    kid = _device(vital_app, "stamp-kid")
    assert kid.post("/control?loop=temp",
                    json={"action": "diagnose",
                          "value": 1}).status_code == 200
    runner = vital_app.registry.runners_for("stamp-kid")["temp"]
    assert runner.case.get("wall_start", 0) > 0, (
        "a case must stamp when the class went blind - the stuck flag "
        "counts from here")
    vital_app.start_challenge(runner, "temp", "cold_store", None)
    assert runner.challenge.get("wall_start", 0) > 0


def test_a_long_blind_case_flags_stuck(fresh_registry, monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M46")
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    kid = _device(vital_app, "stalled-kid")
    assert kid.post("/control?loop=water",
                    json={"action": "diagnose",
                          "value": 1}).status_code == 200
    runner = vital_app.registry.runners_for("stalled-kid")["water"]
    rows = vital_app._room_rows()
    assert rows[0]["stuck"] is None, (
        "a case the class JUST started is not stuck - the flag needs "
        f"{vital_app.STUCK_BLIND_S} quiet seconds first")
    runner.case["wall_start"] -= vital_app.STUCK_BLIND_S + 60
    rows = vital_app._room_rows()
    assert rows[0]["stuck"] and "blind" in rows[0]["stuck"], (
        "a blind case past the threshold must flag, even though the "
        "device is still polling merrily")
    # ...and the flag reaches the teacher's page, sorted to the top.
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    body = teacher.get("/teacher").data.decode("utf-8")
    assert "blind case" in body and "room-stuck" in body


def test_repeated_zero_medal_runs_flag_and_a_medal_clears(fresh_registry):
    vital_app = fresh_registry
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M46")
    kid = _device(vital_app, "zeroes-kid")
    assert kid.get("/state?loop=temp").status_code == 200
    runner = vital_app.registry.runners_for("zeroes-kid")["temp"]
    runner.tries["cold_store"] = [{"points": 10, "medal": None},
                                  {"points": 20, "medal": None}]
    rows = vital_app._room_rows()
    assert rows[0]["stuck"] and "no medal" in rows[0]["stuck"], (
        "two zero-medal runs of one challenge is the walk-over signal")
    runner.tries["cold_store"].append({"points": 70, "medal": "silver"})
    assert vital_app._room_rows()[0]["stuck"] is None, (
        "a team that just medaled is not stuck, whatever came before")


def test_a_quiet_device_flags_and_stuck_sorts_first(monkeypatch):
    vital_app = _stuck_app()
    from sessions import SessionRegistry
    t = {"now": 0.0}
    reg = SessionRegistry(vital_app._make_runners, max_sessions=5,
                          idle_s=30 * 60, clock=lambda: t["now"])
    monkeypatch.setattr(vital_app, "registry", reg)
    reg.runners_for("sleepy", period="P3", team="Gone Quiet")
    t["now"] = vital_app.STUCK_QUIET_S + 30.0
    reg.runners_for("awake", period="P1", team="Still Here")
    rows = vital_app._room_rows()
    assert [r["team"] for r in rows] == ["Gone Quiet", "Still Here"], (
        "stuck rows sort FIRST - P1 before P3 everywhere else, but the "
        "flagged team outranks the alphabet")
    assert "quiet" in rows[0]["stuck"] and rows[1]["stuck"] is None


def test_room_json_is_gated_and_reads_without_stepping(fresh_registry,
                                                       monkeypatch):
    vital_app = fresh_registry
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M46")
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    kid = _device(vital_app, "json-kid")
    assert kid.get("/state?loop=body").status_code == 200
    runners = vital_app.registry.runners_for("json-kid")
    before = {loop: list(r.sim.history()) for loop, r in runners.items()}
    nosy = vital_app.app.test_client()
    assert nosy.get("/teacher/room.json").status_code == 403, (
        "the data feed needs the PIN exactly like the page does")
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    j = teacher.get("/teacher/room.json").get_json()
    assert j["count"] == 1 and j["rows"][0]["loop"] == "body"
    assert {"period", "team", "doing", "idle", "stuck"} <= set(j["rows"][0])
    after = {loop: list(r.sim.history()) for loop, r in runners.items()}
    assert before == after, (
        "the auto-refresh feed stepped a student's simulation - every "
        "room view must be read-only")


# ============ M46.5: the join name reaches the scoreboard ==================
# Found at M47's room pass: the join screen said "name your team once",
# but the boards only knew names typed on the cards. The fallback keeps
# the promise; the explicit card label still wins.

def test_a_blank_label_inherits_the_join_team_name(monkeypatch):
    vital_app = _m44()
    monkeypatch.setattr(vital_app, "PERIODS", ["P3"])
    report = {"met": True, "rows": []}
    score = {"points": 50, "medal": None, "rows": [], "zeroed": None}
    cookie = "vl_period=P3; vl_team=The%20Mongooses"
    with vital_app.app.test_request_context("/",
                                            headers={"Cookie": cookie}):
        att = vital_app.build_attempt("water", "aid_station", report, score)
        named = vital_app.build_attempt("water", "aid_station", report,
                                        score, label="Card Name")
    assert att["label"] == "The Mongooses", (
        'the join screen said "name your team once" - a run started '
        "with a blank label box must inherit that name")
    assert named["label"] == "Card Name", "an explicit card label wins"
    att = vital_app.build_attempt("water", "aid_station", report, score)
    assert att["label"] is None, (
        "outside a request (tests, console) nothing changed")


# ================= M47: the full pass, and Phase 11 closes =================
# Like M42, the close is half regression check by design: a rooms phase's
# real risk is not that the new thing fails - it is that the cookieless
# world, the four loops, or the game's secrecy change quietly underneath.

def test_the_room_pass_with_periods(lab, monkeypatch):
    """(M47) Two classes and a projector, join to scoreboard, all
    through production routes, with the dashboard watching."""
    vital_app, logged = lab
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M43-M46 aren't all here yet - M47 is the close")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3", "P5"])
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "ATTEMPTS", [])

    def device(sid, period, team):
        c = vital_app.app.test_client()
        c.set_cookie("vl_sid", sid)
        c.set_cookie("vl_period", period)
        c.set_cookie("vl_team", team)
        return c

    a = device("m47-a", "P3", "Third%20Shift")
    b = device("m47-b", "P5", "Fifth%20Gear")
    projector = vital_app.app.test_client()
    projector.set_cookie("vl_sid", "m47-projector")
    projector.set_cookie("vl_period", "")            # skipped, on purpose

    # 1. Each class plays the same temp challenge through the routes,
    #    and each attempt lands stamped with ITS class.
    for client, sid in ((a, "m47-a"), (b, "m47-b")):
        assert client.post("/control?loop=temp",
                           json={"action": "challenge",
                                 "value": "cold_store"}).status_code == 200
        runner = vital_app.registry.runners_for(sid)["temp"]
        with runner.lock:
            runner._step(int(runner.challenge["t_end"]
                             - runner.challenge["t_start"]) + 1)
        assert client.get("/state?loop=temp").status_code == 200
    assert [r["period"] for r in logged] == ["P3", "P5"], (
        "an attempt must land stamped with the class that played it")

    # 2. The boards scope per viewer: a class sees itself, the
    #    projector sees the school.
    monkeypatch.setattr(vital_app, "ATTEMPTS",
                        [dict(r, id=i + 1) for i, r in enumerate(logged)])
    ja = a.get("/state?loop=temp").get_json()
    assert ja["board_period"] == "P3"
    assert {e["label"] for e in ja["leaderboard"]["cold_store"]} == \
        {"Third Shift"}, "a P3 device's board is P3's alone"
    jp = projector.get("/state?loop=temp").get_json()
    assert jp["board_period"] is None
    assert {e["label"] for e in jp["leaderboard"]["cold_store"]} == \
        {"Third Shift", "Fifth Gear"}, "the projector shows everyone"

    # 3. A blind case with the teacher watching: the student payload
    #    leaks nothing (the M42 check, on the coupled loop), and the
    #    dashboard names it by number, never by disease.
    assert a.post("/control?loop=body",
                  json={"action": "diagnose",
                        "value": 1}).status_code == 200
    state = a.get("/state?loop=body").get_json()
    banned = sorted(k for k in state["now"]
                    if k.endswith("_enabled") or k in ANSWER_KEY_FIELDS)
    assert not banned and state["preset"] is None
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    page = teacher.get("/teacher").data.decode("utf-8")
    assert "case 1 of" in page and "blind" in page
    assert "mellitus" not in page.lower(), (
        "a disease name reached the projected teacher page while the "
        "body case is BLIND")
    assert "P3" in page and "Third Shift" in page, (
        "the row wears its class and team")

    # 4. Worksheets still print for all four loops.
    for loop in vital_app.WORKSHEETS:
        assert vital_app.app.test_client().get(
            f"/worksheet/{loop}").status_code == 200

    # 5. A restart costs nothing: the server reborn (fresh registry),
    #    the same cookies land the same class.
    from sessions import SessionRegistry
    monkeypatch.setattr(vital_app, "registry",
                        SessionRegistry(vital_app._make_runners, 40, 1800))
    assert a.get("/state?loop=temp").status_code == 200
    assert vital_app.registry.identity("m47-a") == \
        {"period": "P3", "team": "Third Shift"}, (
        "after a restart the cookie re-presents everything - eviction "
        "and reboots stay free")


def test_the_cookieless_world_gained_only_the_scope_label(fresh_registry):
    """(M47) verify.py, pytest and curl drive the same default session
    they have since M7. Phase 11 added them exactly one /state key -
    board_period, always None - and nothing else."""
    vital_app = fresh_registry
    if not hasattr(vital_app, "STUCK_BLIND_S"):
        pytest.skip("M43-M46 aren't all here yet - M47 is the close")
    c = vital_app.app.test_client()
    j = c.get("/state?loop=temp").get_json()
    assert j["board_period"] is None
    assert not ({"period", "team", "stuck"} & set(j)), (
        "rooms-phase keys crept into the cookieless payload")
    assert vital_app.registry.count() == 0, (
        "a cookieless request seated a session - the default world "
        "must stay the module-level runners")


# ================= M48: the class report, as data ==========================
# Phase 12 opens: the attempts log becomes teacher paper. The report is a
# DATA PRODUCT (kickoff SS5) - one pure function that the printable page
# renders and a later gradebook export can read, so the paper can never
# disagree with what the class saw on screen. Nothing here is inferred:
# every number must come out of a stored attempt.

def _report_module():
    if not (ROOT / "report.py").exists():
        pytest.skip("report.py doesn't exist yet - it arrives at M48")
    import report
    return report


REPORT_TODAY = "2026-08-19"
REPORT_YESTERDAY = "2026-08-18"


def _rrun(rid, team, period, day, name="cold_store", points=50, medal=None,
          at="09:00:00", loop="temp"):
    """One finished challenge run. period=None writes NO period key at
    all - a pre-M44 record, which the log is still full of."""
    rec = {"id": rid, "wall_time": f"{day}T{at}", "loop": loop,
           "mode": "challenge", "name": name, "label": team,
           "points": points, "medal": medal, "met": True, "rows": []}
    if period is not None:
        rec["period"] = period
    return rec


def _ranswer(rid, team, period, day, name="case1", correct=True,
             at="09:30:00", loop="temp"):
    rec = {"id": rid, "wall_time": f"{day}T{at}", "loop": loop,
           "mode": "diagnosis", "name": name, "label": team,
           "points": 100 if correct else 0, "medal": None, "met": correct,
           "rows": [], "correct": correct}
    if period is not None:
        rec["period"] = period
    return rec


def test_the_report_filters_by_period_and_by_date():
    report = _report_module()
    log = [
        _rrun(1, "Mine", "P3", REPORT_TODAY),
        _rrun(2, "Other Class", "P5", REPORT_TODAY),
        _rrun(3, "Yesterday", "P3", REPORT_YESTERDAY),
    ]
    rep = report.class_report(log, "P3", REPORT_TODAY)
    assert [t["team"] for t in rep["teams"]] == ["Mine"], (
        "one sheet is ONE class on ONE day - another period's runs and "
        "yesterday's runs must both stay off it")
    assert rep["period"] == "P3" and rep["date"] == REPORT_TODAY
    assert rep["run_count"] == 1


def test_a_pre_m44_record_lands_in_unassigned_never_in_a_period():
    """The log is full of records written before periods existed. They
    belong to the Unassigned pile - and must never be quietly counted
    as some class's work."""
    report = _report_module()
    log = [_rrun(1, "Before Periods", None, REPORT_TODAY)]
    assert report.class_report(log, "P3", REPORT_TODAY)["teams"] == [], (
        "a keyless record was counted as a period's run")
    unassigned = report.class_report(log, "", REPORT_TODAY)
    assert [t["team"] for t in unassigned["teams"]] == ["Before Periods"]


def test_an_empty_period_is_a_valid_report_not_an_error():
    report = _report_module()
    rep = report.class_report([], "P7", REPORT_TODAY)
    assert rep["teams"] == [] and rep["team_count"] == 0
    assert rep["run_count"] == 0 and rep["answer_count"] == 0
    assert rep["aggregate"]["hardest_cases"] == []
    assert rep["aggregate"]["medal_less"] == [], (
        "a period nobody played must print a page that says nobody "
        "played - never raise on the teacher's laptop")


def test_teams_sort_alphabetically_with_the_unnamed_team_last():
    report = _report_module()
    log = [
        _rrun(1, "zebra squad", "P3", REPORT_TODAY),
        _rrun(2, None, "P3", REPORT_TODAY),
        _rrun(3, "Alpha", "P3", REPORT_TODAY),
    ]
    rep = report.class_report(log, "P3", REPORT_TODAY)
    assert [t["team"] for t in rep["teams"]] == \
        ["Alpha", "zebra squad", report.TEAMLESS], (
        "a grading sheet is read by NAME - case-insensitive alphabetical, "
        "with the unnamed team last")


def test_a_team_row_keeps_the_best_run_not_the_last():
    report = _report_module()
    log = [
        _rrun(1, "Kestrel", "P3", REPORT_TODAY, points=88, medal="gold",
              at="09:05:00"),
        _rrun(2, "Kestrel", "P3", REPORT_TODAY, points=41, at="09:20:00"),
    ]
    rep = report.class_report(log, "P3", REPORT_TODAY)
    row = rep["teams"][0]["challenges"][0]
    assert row["runs"] == 2
    assert row["best_points"] == 88 and row["best_medal"] == "gold", (
        "the scorecard reports a team's BEST run of a challenge, the way "
        "the leaderboard always has - not whichever one happened last")


def test_the_debrief_counts_first_answers_only():
    """A team that gets there on the second try still got it wrong the
    first time, and that is the number worth reteaching from."""
    report = _report_module()
    log = [
        _ranswer(1, "Kestrel", "P3", REPORT_TODAY, correct=False,
                 at="09:30:00"),
        _ranswer(2, "Kestrel", "P3", REPORT_TODAY, correct=True,
                 at="09:38:00"),
        _ranswer(3, "Mongooses", "P3", REPORT_TODAY, correct=True,
                 at="09:31:00"),
    ]
    rep = report.class_report(log, "P3", REPORT_TODAY)
    hard = rep["aggregate"]["hardest_cases"]
    assert len(hard) == 1 and hard[0]["wrong"] == 1 and hard[0]["teams"] == 2, (
        "the debrief must count one wrong FIRST answer out of two teams - "
        "a retry is not a second team, and a team is not counted twice")
    kestrel = next(t for t in rep["teams"] if t["team"] == "Kestrel")
    case = kestrel["cases"][0]
    assert case["first_correct"] is False and case["ever_correct"] is True, (
        "the scorecard keeps BOTH: what the team committed to, and "
        "whether they got there in the end. Grading policy is the "
        "teacher's, so the paper reports both rather than choosing")
    assert rep["aggregate"]["teams_reaching_a_case"] == 2


def test_medal_less_lists_only_the_challenges_nobody_medaled():
    report = _report_module()
    log = [
        _rrun(1, "A", "P3", REPORT_TODAY, name="cold_store", points=88,
              medal="gold"),
        _rrun(2, "B", "P3", REPORT_TODAY, name="blast_freezer", points=30),
        _rrun(3, "A", "P3", REPORT_TODAY, name="blast_freezer", points=22),
    ]
    agg = report.class_report(log, "P3", REPORT_TODAY)["aggregate"]
    assert [r["name"] for r in agg["medal_less"]] == ["blast_freezer"], (
        "a challenge somebody medaled is not something to reteach")
    row = agg["medal_less"][0]
    assert row["runs"] == 2 and row["teams"] == 2 and row["best_points"] == 30


def test_a_thin_day_says_so_instead_of_claiming_a_trend():
    report = _report_module()
    log = [_ranswer(1, "A", "P3", REPORT_TODAY, correct=False)]
    assert report.class_report(log, "P3", REPORT_TODAY)["aggregate"]["thin"]
    many = [_ranswer(i, f"T{i}", "P3", REPORT_TODAY, correct=False)
            for i in range(1, report.THIN_SAMPLE + 1)]
    assert not report.class_report(many, "P3",
                                   REPORT_TODAY)["aggregate"]["thin"], (
        "one team having a bad afternoon is an anecdote; the page must "
        "say which one it is showing")


def test_the_report_is_pure_no_web_framework_and_no_clock():
    """(kickoff SS2, Phase 12) The date arrives as an ARGUMENT. A report
    that reads the clock cannot be tested against a crafted log, and
    every claim on the paper stops being reproducible."""
    if not (ROOT / "report.py").exists():
        pytest.skip("report.py doesn't exist yet - it arrives at M48")
    tree = ast.parse((ROOT / "report.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            root = name.split(".")[0]
            assert root not in WEB_MODULES, (
                f"report.py imports {name} - the report must stay "
                "testable with a crafted log and no server")
            assert root not in {"app", "time", "datetime"}, (
                f"report.py imports {name} - the log and the DATE are "
                "arguments; only the route knows what today is")


# ================= M49: the scorecard, printable ===========================
# The report reaches paper. Same PIN as the dashboard - and unlike the
# dashboard this page NAMES diagnoses, so it is an answer key and says so.

def _paper_app():
    import app as vital_app
    if not hasattr(vital_app, "_report_catalog"):
        pytest.skip("the report page doesn't exist yet - it arrives at M49")
    return vital_app


def test_the_report_page_needs_the_teacher_pin(monkeypatch):
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3"])
    nosy = vital_app.app.test_client()
    refused = nosy.get("/report/P3")
    assert refused.status_code == 403
    body = refused.data.decode("utf-8")
    assert "answer key" in body and 'name="pin"' in body, (
        "the report must be refused in words, with the way in - and it "
        "must say WHY it is gated: it names the diagnoses")
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    assert teacher.get("/report/P3").status_code == 200


def test_an_unknown_period_is_plain_english_not_a_stack_trace(monkeypatch):
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3", "P5"])
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    out = teacher.get("/report/P9")
    assert out.status_code == 400
    body = out.data.decode("utf-8")
    assert "periods.txt" in body and "P3" in body, (
        "a mistyped period must say what the list actually holds")
    assert "Traceback" not in body


def test_the_unassigned_pile_has_a_page_too(monkeypatch):
    """The projector and everyone who skipped the join screen land in
    "" - a real bucket in this app's model, so it gets a real sheet."""
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3"])
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    page = teacher.get(f"/report/{vital_app.UNASSIGNED_SLUG}")
    assert page.status_code == 200
    assert "Unassigned" in page.data.decode("utf-8")


def test_an_empty_day_prints_a_page_that_says_so(monkeypatch):
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3"])
    monkeypatch.setattr(vital_app, "ATTEMPTS", [])
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    body = teacher.get("/report/P3").data.decode("utf-8")
    assert "No team finished a run" in body, (
        "a period nobody played must print a sheet that says nobody "
        "played - never a blank page, never an error")
    assert "Answer key" in body, "the caution rides on every printing"


def test_the_scorecard_carries_the_days_teams(monkeypatch):
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3"])
    today = vital_app._today()
    monkeypatch.setattr(vital_app, "ATTEMPTS", [
        _rrun(1, "The Mongooses", "P3", today, name="cold_store",
              points=88, medal="gold"),
        _rrun(2, "Other Class", "P5", today, name="cold_store", points=95,
              medal="gold"),
        _ranswer(3, "The Mongooses", "P3", today, name="case1",
                 correct=False),
    ])
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    body = teacher.get("/report/P3").data.decode("utf-8")
    assert "The Mongooses" in body and "88/100" in body
    assert "Other Class" not in body, (
        "another period's team reached P3's sheet")
    assert "wrong" in body, "a first answer that missed must read as missed"
    assert "once they finish a run" in body, (
        "the page must state its own limit: nothing here records "
        "attendance, so a short roster is not a full one")


def test_the_teacher_page_links_a_report_per_period(monkeypatch):
    vital_app = _paper_app()
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", ["P3", "P5"])
    teacher = vital_app.app.test_client()
    teacher.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    body = teacher.get("/teacher").data.decode("utf-8")
    for href in ('href="/report/P3"', 'href="/report/P5"',
                 'href="/report/unassigned"'):
        assert href in body, f"the teacher page is missing {href}"


def test_the_catalog_titles_a_case_the_way_the_class_met_it():
    """The paper must quote the sentence the class was shown when they
    answered - one phrasing, two readers (M49's _truth_line)."""
    vital_app = _paper_app()
    catalog = vital_app._report_catalog()
    loop, cid = "temp", list(vital_app.CASES["temp"])[2]     # case 3
    entry = catalog["cases"][(loop, cid)]
    assert entry["title"] == "Temperature case 3", (
        "a case is titled the way the student met it (case 3 of 4), "
        "never by its internal id")
    truth = vital_app.CASES[loop][cid]["answer"]
    graded = vital_app.grade_answer(vital_app.CASES[loop][cid], truth,
                                    vital_app.ANSWER_OPTIONS[loop])
    assert entry["answer_line"] == graded["truth"]["line"], (
        "the report's answer line and the reveal the class saw must be "
        "the SAME sentence, or the paper and the screen disagree")
    key = ("temp", "cold_store")
    assert catalog["challenges"][key] == \
        vital_app.CHALLENGES["temp"]["cold_store"]["title"]


def test_the_loop_labels_match_the_tabs_students_read():
    """LOOP_LABELS names the loops for the paper; the page has named
    them since M7. Pinned together so they cannot drift."""
    vital_app = _paper_app()
    page = vital_app.app.test_client().get("/").data.decode("utf-8")
    for loop, label in vital_app.LOOP_LABELS.items():
        assert f'data-loop="{loop}"' in page
        assert label in page, (
            f"the report calls the {loop} loop {label!r} but the page "
            "does not use that word - the paper and the tabs must agree")


def test_report_py_is_a_served_source():
    """A stale server holding last edit's report code must fail
    verification by name, not hand back a green PASS (the M43 rule)."""
    import verify
    assert "report.py" in verify.SERVED_SOURCES


# ================= M50: the debrief =========================================
# The bottom half of the sheet: what to reteach tomorrow, in the
# curriculum's own words. Every line must be readable off the log - and
# a day with two answers in it must not be dressed up as a class trend.

def _debrief_client(vital_app, log, monkeypatch, periods=("P3",)):
    monkeypatch.setattr(vital_app, "TEACHER_PIN", "PIN-SENTINEL-XYZ")
    monkeypatch.setattr(vital_app, "PERIODS", list(periods))
    monkeypatch.setattr(vital_app, "ATTEMPTS", log)
    c = vital_app.app.test_client()
    c.set_cookie("vl_teacher", "PIN-SENTINEL-XYZ")
    return c


def test_the_debrief_names_the_case_and_quotes_the_real_answer(monkeypatch):
    vital_app = _paper_app()
    today = vital_app._today()
    cid = list(vital_app.CASES["temp"])[2]            # case 3
    log = [_ranswer(1, "Kestrel", "P3", today, name=cid, correct=False),
           _ranswer(2, "Row 4", "P3", today, name=cid, correct=False),
           _ranswer(3, "Mongooses", "P3", today, name=cid, correct=True)]
    body = _debrief_client(vital_app, log,
                           monkeypatch).get("/report/P3").data.decode("utf-8")
    assert "What the class found hard" in body
    assert "2 of 3" in body and "Temperature case 3" in body, (
        "the debrief must say how many teams missed it on their FIRST "
        "answer, and name the case the way the class met it")
    truth = vital_app.CASES["temp"][cid]["answer"]
    line = vital_app._truth_line(truth, vital_app.ANSWER_OPTIONS["temp"])[2]
    assert line.split(" ")[0] in body, (
        "the right answer must appear in the curriculum's own words - "
        "the same sentence the class saw at the reveal")


def test_a_medal_less_challenge_is_named_as_something_to_reteach(monkeypatch):
    vital_app = _paper_app()
    today = vital_app._today()
    log = [
        _rrun(1, "A", "P3", today, name="cold_store", points=88,
              medal="gold"),
        _rrun(2, "B", "P3", today, name="blast_freezer", points=30),
        _rrun(3, "A", "P3", today, name="blast_freezer", points=22),
    ]
    body = _debrief_client(vital_app, log,
                           monkeypatch).get("/report/P3").data.decode("utf-8")
    assert "No team earned a medal on" in body
    assert vital_app.CHALLENGES["temp"]["blast_freezer"]["title"] in body
    assert "set point" in body, (
        "the reteach line must speak the curriculum's vocabulary - a "
        "medal-less challenge is a loop nobody held near its set point")
    # ...and the challenge somebody DID medal is not on the reteach list.
    reteach = body.split("What the class found hard")[1]
    assert vital_app.CHALLENGES["temp"]["cold_store"]["title"] not in reteach


def test_a_thin_day_is_labelled_an_anecdote_on_the_page(monkeypatch):
    vital_app = _paper_app()
    today = vital_app._today()
    log = [_rrun(1, "A", "P3", today, points=40),
           _ranswer(2, "A", "P3", today, correct=False)]
    body = _debrief_client(vital_app, log,
                           monkeypatch).get("/report/P3").data.decode("utf-8")
    assert "anecdotes, not as a class trend" in body, (
        "one team having a bad afternoon must not read as a finding")


def test_a_clean_day_says_there_is_nothing_to_reteach(monkeypatch):
    vital_app = _paper_app()
    today = vital_app._today()
    log = [_rrun(1, "A", "P3", today, points=91, medal="gold"),
           _ranswer(2, "A", "P3", today, correct=True)]
    body = _debrief_client(vital_app, log,
                           monkeypatch).get("/report/P3").data.decode("utf-8")
    assert "nothing on this page needs" in body, (
        "a class that got everything right deserves to be told so, not "
        "handed an empty heading")
    assert "1 of 1" in body, "the reach line still reports"


def test_the_debrief_is_absent_when_nobody_played(monkeypatch):
    vital_app = _paper_app()
    body = _debrief_client(vital_app, [],
                           monkeypatch).get("/report/P3").data.decode("utf-8")
    assert "What the class found hard" not in body, (
        "an empty day gets the 'nobody played' line, not a debrief "
        "heading with nothing under it")
