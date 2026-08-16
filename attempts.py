"""The attempts log — Phase 8's data product (kickoff SS5).

One JSON file of finished runs: `data/attempts.json`. Every score the
class earns lands here, and a later phase (worksheets, a gradebook
export, a per-class comparison) reads THIS file — never a screenshot,
never a scrape of the DOM.

Three promises, because a classroom machine gets treated roughly:

  * written ATOMICALLY (temp file beside the target, then os.replace), so
    a crash mid-write cannot corrupt the morning's scores,
  * capped at the most recent MAX_ATTEMPTS, so it never fills the disk,
  * LOUD on failure. A log that can't be read starts empty AND says so;
    a log that can't be written raises instead of letting the UI pretend
    the score saved. Stale or lost data passing as fine is the worst
    failure mode there is.

Attempt labels are TEAM names, never student names (kickoff SS2): a file
of named minors on a teacher's laptop is a thing we don't create.

No Flask in here, and no engine either — it's a file and a list.
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PATH = ROOT / "data" / "attempts.json"

# Roughly a semester of class periods. Old attempts fall off the front.
MAX_ATTEMPTS = 500

_last_warning = None
_blocked = None          # a log we could not READ, and so must not
                         # overwrite: it may be the morning's scores


class AttemptsError(RuntimeError):
    """A save that did NOT happen. Never swallowed — the UI shows it."""


def last_warning():
    """The most recent plain-English complaint from load(), or None.

    The app puts this on screen: if the morning's scores were unreadable,
    the teacher finds out from the app, not from a missing leaderboard.
    """
    return _last_warning


def load(path=DEFAULT_PATH):
    """Every attempt on disk, oldest first. Never raises.

    Three ways this goes, and the difference matters:

      * missing        -> [], no complaint. A fresh classroom.
      * read but JUNK  -> [], a loud warning, and the file moved aside to
                          `<name>.corrupt.json`. We have seen the
                          contents, so we know they aren't scores.
      * cannot be READ -> [], a loud warning, and the file LEFT ALONE. It
                          may be a perfectly good log that antivirus or
                          an open editor has locked for the moment;
                          renaming it or writing over it would destroy
                          the morning's scores over a transient error.
                          save() refuses until it can be read.
    """
    global _last_warning, _blocked
    path = Path(path)
    _blocked = None
    if not path.exists():
        _last_warning = None
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _blocked = path
        _last_warning = (
            f"{path.name} exists but could not be read ({exc}). Scores are "
            "starting from an empty log, and NOTHING will be saved until "
            "that file can be read or is moved out of the way — the app "
            "will not write over a log it cannot see inside.")
        return []
    try:
        records = json.loads(text)
        if not isinstance(records, list):
            raise ValueError("the file holds a "
                             f"{type(records).__name__}, not a list of runs")
    except ValueError as exc:
        _last_warning = _set_aside(path, exc)
        return []
    _last_warning = None
    return records


def _set_aside(path, exc):
    """Preserve an unreadable log and describe the damage in English."""
    aside = path.with_suffix(".corrupt.json")
    try:
        os.replace(path, aside)
        kept = f"It has been kept as {aside.name}."
    except OSError as move_exc:                      # locked, read-only...
        kept = (f"It could not even be moved aside ({move_exc}) — do not "
                "let the app overwrite it.")
    return (f"{path.name} could not be read ({exc}). Scores are starting "
            f"from an empty log. {kept}")


def save(records, path=DEFAULT_PATH):
    """Write the log atomically, keeping only the most recent attempts.

    Raises AttemptsError if the write fails — the caller must NOT report
    a saved score it didn't save.
    """
    path = Path(path)
    if _blocked is not None and path == _blocked:
        raise AttemptsError(_last_warning)     # see load(): don't destroy
                                               # a log we couldn't read
    records = list(records)[-MAX_ATTEMPTS:]
    tmp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(records, indent=1), encoding="utf-8")
        os.replace(tmp, path)          # atomic on Windows and POSIX alike
    except OSError as exc:
        try:
            tmp.unlink()
        except OSError:
            pass                       # nothing more we can do; the raise
        raise AttemptsError(           # below is the part that matters
            f"the attempts log could not be saved to {path} ({exc}). "
            "THE SCORE WAS NOT RECORDED.") from exc
    return records


def append(record, path=DEFAULT_PATH):
    """Add one attempt, giving it the next id. Returns the stored record.

    Disk is the source of truth: this re-reads before appending, so two
    loops finishing near each other can't lose one another's run.
    """
    records = load(path)
    next_id = max((r.get("id") or 0 for r in records), default=0) + 1
    stored = {**record, "id": next_id}
    records.append(stored)
    save(records, path)
    return stored
