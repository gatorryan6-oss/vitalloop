"""Vital Loop — the Flask app. Routes and the sim runner; no physiology here.

The engine ticks LAZILY: every /state poll measures wall time since the last
poll, multiplies by the speed setting, and steps the sim that many 1 s ticks.
The engine never reads the clock, so it stays deterministic; the app only
decides HOW MANY ticks to run. No background thread to wedge mid-class.

If the tab is hidden for a while (polls stop), catch-up is capped at
MAX_CATCHUP_TICKS and the rest of the wall time is dropped — the sim resumes
smoothly instead of freezing the server chewing through an hour of ticks.
"""

import csv
import datetime
import io
import threading
import time

from flask import Flask, Response, jsonify, render_template, request

import attempts
from engine.glucose import GlucoseSimulation
from engine.sim import Simulation
from engine.water import WaterSimulation

app = Flask(__name__)

MAX_CATCHUP_TICKS = 2000     # ~2 sim-minutes at 16x; beyond that, drop time
MAX_POINTS_PER_RESPONSE = 1500   # downsample /state payloads beyond this


class Runner:
    """One simulation and its play/pause/speed state. Each loop gets its
    own Runner — pause and speed are PER LOOP (the simpler choice; logged
    in BUILDLOG at M7)."""

    def __init__(self, sim, loop):
        self.lock = threading.Lock()
        self.sim = sim
        self.loop = loop         # which loop this Runner drives — the
                                 # attempts log keys off it (M26)
        self.running = True
        self.speed = 1
        self.preset = None       # active disease name (app-level; M18) —
                                 # the engine only ever sees mechanisms
        self.challenge = None    # active challenge stamp (M24):
                                 # {loop, name, t_start, t_end, report,
                                 #  score, attempt, label}
        self.attempt_error = None   # a score that did NOT save (M26);
                                    # /state carries it to the screen
        self._last_wall = time.monotonic()
        self._tick_debt = 0.0    # fractional ticks owed, carried between polls

    def advance(self):
        """Step the sim by however much wall time has passed (times speed)."""
        now = time.monotonic()
        with self.lock:
            elapsed = now - self._last_wall
            self._last_wall = now
            if not self.running:
                self._tick_debt = 0.0
                return
            self._tick_debt += elapsed * self.speed
            n = int(self._tick_debt)
            if n > MAX_CATCHUP_TICKS:
                n, self._tick_debt = MAX_CATCHUP_TICKS, 0.0
            else:
                self._tick_debt -= n
            if n:
                self.sim.step(n)

    def _finish_challenge(self, records, state):
        """The challenge block for /state — and, the one time the window
        closes, the report, its score, and the logged attempt.

        Call with self.lock HELD: two polls can land in the same instant
        (the browser's and a /control reply's), and one run must never
        produce two attempts in the log.
        """
        if self.challenge is None:
            return None
        c = self.challenge
        entry = CHALLENGES[c["loop"]][c["name"]]
        done = state["t"] >= c["t_end"]
        if done and c["report"] is None:
            # Evaluate ONCE, from the engine's records over exactly the
            # stamped window — the report is a data product.
            window = [r for r in records
                      if c["t_start"] < r["t"] <= c["t_end"]]
            c["report"] = EVALUATORS[entry["metrics"]](window)
            # ...and score it separately (M26): the evaluator said what
            # happened, the scorer says what it was worth.
            c["score"] = score_report(entry, c["report"])
            c["attempt"], self.attempt_error = log_attempt(
                build_attempt(c["loop"], c["name"], c["report"], c["score"],
                              label=c.get("label")))
        return {
            "name": c["name"],
            "title": entry["title"],
            "goal": entry["goal"],
            "t_start": c["t_start"],
            "t_end": c["t_end"],
            "done": done,
            "report": c["report"],
            "score": c.get("score"),
            "attempt": c.get("attempt"),
        }

    def snapshot(self, since):
        """Current state + history records newer than sim-time `since`."""
        with self.lock:
            records = self.sim.history()
            state = records[-1]
            # Dose/drink events are data products (Phase 3/6 kickoffs):
            # chart markers read the engine's logs, never infer from curves.
            doses = self.sim.doses() if hasattr(self.sim, "doses") else None
            drinks = (self.sim.drinks()
                      if hasattr(self.sim, "drinks") else None)
            challenge = self._finish_challenge(records, state)
        points = [r for r in records if r["t"] > since]
        if len(points) > MAX_POINTS_PER_RESPONSE:
            stride = -(-len(points) // MAX_POINTS_PER_RESPONSE)  # ceil div
            # Keep the newest point exact so the readout matches the chart.
            points = points[::stride] + [points[-1]]
        out = {
            "running": self.running,
            "speed": self.speed,
            "preset": self.preset,
            "now": state,
            "points": points,
        }
        if doses is not None:
            out["doses"] = doses
        if drinks is not None:
            out["drinks"] = drinks
        if challenge is not None:
            out["challenge"] = challenge
        # The card's "best so far" line, and any complaint from the log —
        # a score that failed to save says so on screen (M26).
        out["bests"] = {cid: best_attempt(self.loop, cid)
                        for cid in CHALLENGES.get(self.loop, {})}
        out["attempts_error"] = self.attempt_error or ATTEMPTS_WARNING
        return out


runners = {
    "temp": Runner(Simulation(), "temp"),
    "glucose": Runner(GlucoseSimulation(), "glucose"),
    "water": Runner(WaterSimulation(), "water"),
}


def _runner():
    """The Runner the request addresses (?loop=temp|glucose, default temp),
    or None for an unknown loop name."""
    return runners.get(request.args.get("loop", "temp"))


@app.route("/")
def index():
    # The challenge table rides into the page via the template, so the
    # card's story/goal text has ONE source (kickoff SS5).
    return render_template("index.html", challenges=CHALLENGES)


@app.route("/state")
def state():
    runner = _runner()
    if runner is None:
        return jsonify({"error": "unknown loop"}), 400
    runner.advance()
    since = request.args.get("since", -1.0, type=float)
    return jsonify(runner.snapshot(since))


ENV_TEMP_MIN, ENV_TEMP_MAX = -10.0, 45.0   # the slider's range, enforced

# One-click classroom setups: name -> (env_temp, exercise)
SCENARIOS = {
    "freezer": (-10.0, False),   # step into a freezer
    "hot_run": (38.0, True),     # run a mile on a hot day
}

# Insulin dosing (M12): the UI offers real-world sizes; the cap is policy.
MAX_SINGLE_DOSE_U = 15.0
ALLOWED_BASAL_RATES = {0, 0.5, 1.0, 1.5, 2.0}   # U/h, matching the buttons

# Water intake (M21): same idea — the engine is a model, the cap is policy.
MAX_SINGLE_DRINK_ML = 3000.0
MAX_SALT_MOSM = 600.0

# Disease presets (M18): ONE table is the source for what each disease
# means mechanically (Phase 5 kickoff SS5) — buttons, banner, and any
# future quiz layer read this, never their own copy. A preset is a
# COMPLETE diagnosis: it sets the whole loop configuration so diseases
# never stack, and it never resets the run — the class watches the
# transition. The engine never sees a disease name.
HEALTHY_TEMP = {"fever": 0.0, "exercise": False, "sensor": True,
                "effectors": {"sweat": True, "shiver": True, "vaso": True}}
HEALTHY_GLUCOSE = {"sensitivity": 1.0, "exercise": False, "sensor": True,
                   "effectors": {"beta": True, "alpha": True, "liver": True},
                   "pump": False, "basal": 0.0}
HEALTHY_WATER = {"exercise": False, "sensor": True,
                 "effectors": {"adh": True, "kidney": True, "access": True}}

PRESETS = {
    "temp": {
        "healthy": {"label": "Healthy", "banner": None, "speed": 1,
                    **HEALTHY_TEMP},
        "fever": {
            "label": "Fever",
            "banner": "the set point moved to 39.0 °C — the loop is "
                      "WORKING, defending the wrong number. Chills on "
                      "the way up, sweats when it breaks.",
            "speed": 16, **{**HEALTHY_TEMP, "fever": 2.0, "env": 22.0}},
        "heat_stroke": {
            "label": "Heat stroke",
            "banner": "a hot run and the sweat effector has failed — "
                      "heat pours in with no way out (effector failure).",
            "speed": 4,
            **{**HEALTHY_TEMP, "exercise": True, "env": 40.0,
               "effectors": {"sweat": False, "shiver": True, "vaso": True}}},
        "hypothermia": {
            "label": "Hypothermia",
            "banner": "a freezing room and no shivering — the responses "
                      "that remain cannot keep up (effector overwhelmed).",
            "speed": 4,
            **{**HEALTHY_TEMP, "env": -10.0,
               "effectors": {"sweat": True, "shiver": False, "vaso": True}}},
    },
    "glucose": {
        "healthy": {"label": "Healthy", "banner": None, "speed": 1,
                    **HEALTHY_GLUCOSE},
        "type1": {
            "label": "Type 1 diabetes",
            "banner": "the beta cells are destroyed — no insulin is made "
                      "at all (control-center failure). Treat with the "
                      "syringe or the pump.",
            "speed": 16, **{**HEALTHY_GLUCOSE,
                            "effectors": {"beta": False, "alpha": True,
                                          "liver": True}}},
        "type2": {
            "label": "Type 2 diabetes",
            "banner": "insulin is made — lots of it — but the tissues "
                      "barely listen (target-tissue resistance). Both "
                      "numbers run high at once.",
            "speed": 16, **{**HEALTHY_GLUCOSE, "sensitivity": 0.05}},
    },
    "water": {
        "healthy": {"label": "Healthy", "banner": None, "speed": 1,
                    **HEALTHY_WATER},
        "central_di": {
            "label": "Central diabetes insipidus",
            "banner": "no ADH is released — the kidneys never hear "
                      "'hold water' and pass liters of TASTELESS urine "
                      "(control-center failure). Survivable while "
                      "thirst can reach water. Insipidus = tasteless; "
                      "the glucose loop's mellitus = honey-sweet. Two "
                      "siphons, two different broken loops.",
            "speed": 16,
            **{**HEALTHY_WATER,
               "effectors": {"adh": False, "kidney": True,
                             "access": True}}},
        "nephrogenic_di": {
            "label": "Nephrogenic diabetes insipidus",
            "banner": "ADH is released — and the kidneys cannot hear it "
                      "(deaf-tissue failure, type 2's pattern in a new "
                      "loop). Hormone high, urine flooding anyway.",
            "speed": 16,
            **{**HEALTHY_WATER,
               "effectors": {"adh": True, "kidney": False,
                             "access": True}}},
    },
}


# Scenario challenges (M24): setup + duration + metrics + targets +
# story, one table (kickoff SS2). The REPORT is a data product: computed
# here from history records over the challenge window, never in JS — the
# strip charts and the report card can never disagree. No points, no
# stars: MET / NOT MET and the numbers.

def _eval_t1_shift(records):
    """Five hours as the pancreas: time in range, no hypos, no cheating."""
    n = max(1, len(records))
    in_range = sum(1 for r in records if 70.0 <= r["glucose"] <= 180.0)
    pct = 100.0 * in_range / n
    lo = min((r["glucose"] for r in records), default=0.0)
    hi = max((r["glucose"] for r in records), default=0.0)
    beta_stayed_off = all(not r["beta_enabled"] for r in records)
    rows = [
        {"key": "in_range", "label": "time in 70-180 mg/dL",
         "value": f"{pct:.0f}% (target: at least 75%)", "met": pct >= 75.0,
         "n": pct},
        {"key": "lowest", "label": "lowest glucose",
         "value": f"{lo:.0f} mg/dL (target: never below 65)",
         "met": lo >= 65.0, "n": lo},
        {"key": "highest", "label": "highest glucose",
         "value": f"{hi:.0f} mg/dL", "met": None, "n": hi},
        {"key": "beta_off", "label": "beta cells stayed off",
         "value": "yes" if beta_stayed_off
                  else "no — the pancreas came back on mid-shift",
         "met": beta_stayed_off, "n": None},
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


def _eval_cold_store(records):
    """An hour locked in at -10 with severe-hypothermia physiology:
    the rescue is a heat BUDGET, and exhaustion caps the spend."""
    n = max(1, len(records))
    end = records[-1]["core_temp"] if records else 0.0
    lo = min((r["core_temp"] for r in records), default=0.0)
    duty = 100.0 * sum(1 for r in records if r["exercise"]) / n
    door_shut = max((r["env_temp"] for r in records), default=-10.0) <= -5.0
    stayed_failed = all(not r["shiver_enabled"] and not r["vaso_enabled"]
                        for r in records)
    rows = [
        {"key": "end_core", "label": "core at the hour's end",
         "value": f"{end:.2f} °C (target: at least 36.0)",
         "met": end >= 36.0, "n": end},
        {"key": "lowest", "label": "lowest core",
         "value": f"{lo:.2f} °C (target: never below 35.0)",
         "met": lo >= 35.0, "n": lo},
        {"key": "duty", "label": "exercise used",
         "value": f"{duty:.0f}% of the hour (exhaustion cap: 50%)",
         "met": duty <= 50.0, "n": duty},
        {"key": "door", "label": "the door stayed shut (room at -5 °C or "
                                 "colder)",
         "value": "yes" if door_shut else "no — the room was warmed",
         "met": door_shut, "n": None},
        {"key": "parts", "label": "shivering and vessel control stayed "
                                  "failed",
         "value": "yes" if stayed_failed else "no — a broken part came "
                  "back mid-rescue", "met": stayed_failed, "n": None},
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


def _eval_aid_station(records):
    """Four hours as someone else's osmoreceptor: read the charts,
    pour the drinks, don't commit the aid station's classic kill."""
    n = max(1, len(records))
    inside = sum(1 for r in records if 280.0 <= r["osmolarity"] <= 300.0)
    pct = 100.0 * inside / n
    lo = min((r["osmolarity"] for r in records), default=0.0)
    hi = max((r["osmolarity"] for r in records), default=0.0)
    kept_moving = all(r["exercise"] for r in records)
    sensor_dead = all(not r["sensor_enabled"] for r in records)
    urine_l = sum(r["urine_rate"] for r in records) / 60.0 / 1000.0
    rows = [
        {"key": "in_band", "label": "time inside 280-300 mOsm/L",
         "value": f"{pct:.0f}% (target: at least 90%)", "met": pct >= 90.0,
         "n": pct},
        {"key": "lowest", "label": "lowest osmolarity",
         "value": f"{lo:.1f} mOsm/L (target: never below 275 - "
                  "overhydration kills at aid stations)", "met": lo >= 275.0,
         "n": lo},
        {"key": "highest", "label": "highest osmolarity",
         "value": f"{hi:.1f} mOsm/L (target: never above 305)",
         "met": hi <= 305.0, "n": hi},
        {"key": "urine", "label": "urine passed",
         "value": f"{urine_l:.1f} L", "met": None, "n": urine_l},
        {"key": "moving", "label": "the runner kept moving",
         "value": "yes" if kept_moving else "no — exercise was switched "
                  "off", "met": kept_moving, "n": None},
        {"key": "sensor", "label": "the osmoreceptors stayed dead",
         "value": "yes" if sensor_dead else "no — the sensor came back",
         "met": sensor_dead, "n": None},
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


EVALUATORS = {
    "t1_shift": _eval_t1_shift,
    "cold_store": _eval_cold_store,
    "aid_station": _eval_aid_station,
}


# Scoring (M26): the evaluator's job is to say WHAT HAPPENED; the
# scorer's job is to say WHAT IT'S WORTH (Phase 8 kickoff SS5). Two
# functions, two responsibilities — the honest MET / NOT MET card is
# untouched and the points ride on top of the same rows.
#
# Every challenge is out of 100 so a medal means the same thing on every
# loop. Three kinds of row:
#
#   graded    — partial credit: `points` scaled between `zero_at` (worth
#               nothing) and `full_at` (worth all of it), clamped at both
#               ends. Which end is "better" comes from the numbers, so
#               "lower is better" rows just put full_at below zero_at. A
#               graded row may also carry `hard`: going PAST zero_at
#               isn't a bad play, it's not playing the challenge, and it
#               zeroes the run the way an integrity row does.
#   integrity — pass/fail, and failing ZEROES the whole run rather than
#               docking it. You didn't play the challenge.
#   info      — absent from this table: printed on the card, worth zero.
#
# The floors and ceilings below were SET FROM THE M26 STRATEGY SWEEP
# (numbers in BUILDLOG), not guessed — and the sweep overturned the first
# two guesses. Notice the bands are tight around the goal on purpose: a
# scale that runs from "dead" to "perfect" gives a near-miss almost full
# marks, so these start earning at roughly the point where the run stops
# being a medical emergency.
SCORING = {
    "t1_shift": {
        "in_range": {"points": 50, "zero_at": 40.0, "full_at": 95.0},
        # 35 points on the hypo line: the sweep found an 8 U play that
        # spent 81 % of the shift in range and still scored 60 after
        # bottoming out at 6.5 mg/dL. A run that nearly kills the patient
        # must not medal, whatever the average looked like.
        "lowest": {"points": 35, "zero_at": 55.0, "full_at": 75.0},
        "highest": {"points": 15, "zero_at": 300.0, "full_at": 180.0},
        "beta_off": {"integrity": "the pancreas came back on — the shift "
                                  "doesn't count"},
    },
    "cold_store": {
        "end_core": {"points": 55, "zero_at": 35.5, "full_at": 36.2},
        "lowest": {"points": 25, "zero_at": 34.5, "full_at": 35.5},
        # Exercise is a BUDGET: economy is worth real points, but only
        # inside the exhaustion cap. Past 50 % of the hour this body
        # physically couldn't keep going, so the run doesn't count.
        "duty": {"points": 20, "zero_at": 50.0, "full_at": 25.0,
                 "hard": "exercise ran past exhaustion — this body "
                         "couldn't have kept moving that long"},
        "door": {"integrity": "the room was warmed — that's not the "
                              "cold store"},
        "parts": {"integrity": "a broken part came back on — that's not "
                               "the rescue"},
    },
    "aid_station": {
        "in_band": {"points": 60, "zero_at": 55.0, "full_at": 100.0},
        # Graded to the SET POINT, not to the band edge: six different
        # drinking rhythms all held 100 % of the window, and the class
        # deserves to see which one held the runner closest to 290.
        "lowest": {"points": 20, "zero_at": 270.0, "full_at": 285.0},
        "highest": {"points": 20, "zero_at": 310.0, "full_at": 295.0},
        "moving": {"integrity": "the runner stopped — that's not the "
                                "race"},
        "sensor": {"integrity": "the osmoreceptors came back — the class "
                                "stopped being the sensor"},
    },
}

MEDAL_TIERS = ("gold", "silver", "bronze")   # best first; the lookup order


def _grade(n, zero_at, full_at):
    """A raw number as 0..1 of a row's points, clamped at both ends.

    Overshooting the ceiling earns no bonus and undershooting the floor
    is never negative — one bad row can't eat another row's marks.
    """
    if full_at == zero_at:
        return 1.0 if n == full_at else 0.0
    return max(0.0, min(1.0, (n - zero_at) / (full_at - zero_at)))


def _past(n, zero_at, full_at):
    """True when a number is beyond the worthless end of its band — the
    wrong side of a `hard` row's line. The line itself is still legal:
    a 50 % exhaustion cap allows exactly 50 %."""
    return n < zero_at if full_at > zero_at else n > zero_at


def score_report(entry, report):
    """PURE: what one finished report card is worth. Never mutates it.

    Takes a CHALLENGES entry (for its `metrics` and `medals`) and the
    report the evaluator already produced, and returns points, the medal
    tier, and the per-row breakdown that M27's side-by-side view reads.
    """
    rules = SCORING[entry["metrics"]]
    rows = {r.get("key"): r for r in report.get("rows", ())}
    earned, possible, breakdown, zeroed = 0.0, 0, [], None
    for key, rule in rules.items():
        row = rows.get(key)
        if rule.get("integrity"):
            if row is not None and row.get("met") is False:
                zeroed = rule["integrity"]
            continue
        possible += rule["points"]
        got = 0.0
        if row is not None and row.get("n") is not None:
            if rule.get("hard") and _past(row["n"], rule["zero_at"],
                                          rule["full_at"]):
                zeroed = rule["hard"]
            got = rule["points"] * _grade(row["n"], rule["zero_at"],
                                          rule["full_at"])
        earned += got
        breakdown.append({"key": key,
                          "label": row["label"] if row else key,
                          "points": round(got, 1), "max": rule["points"]})
    if zeroed:
        return {"points": 0, "max": possible, "medal": None,
                "rows": [{**b, "points": 0.0} for b in breakdown],
                "zeroed": zeroed}
    points = round(earned)
    medal = next((t for t in MEDAL_TIERS
                  if points >= entry["medals"][t]), None)
    return {"points": points, "max": possible, "medal": medal,
            "rows": breakdown, "zeroed": None}


# The attempts log (M26): every finished run, on disk, so a best score
# survives closing the app — and so a worksheets or gradebook phase has a
# real file to read. Loaded once at startup and kept in memory for the
# "best so far" line; disk stays the source of truth on every write.
ATTEMPTS = attempts.load()
ATTEMPTS_WARNING = attempts.last_warning()   # loud if the file was junk
_log_lock = threading.Lock()                 # two loops can finish at once


def build_attempt(loop, name, report, score, label=None, mode="challenge"):
    """One finished run as a log record (Phase 8 kickoff SS5 fields).

    Wall-clock time is app-level and that's fine: a leaderboard needs a
    real timestamp to sort by, and the ENGINE still never reads the clock.
    """
    return {
        "id": None,               # assigned by the log on append
        "wall_time": datetime.datetime.now().isoformat(timespec="seconds"),
        "loop": loop,
        "mode": mode,             # "challenge" now; "diagnosis" at M28
        "name": name,
        "label": label,           # a TEAM name, never a student's (M27)
        "points": score["points"],
        "medal": score["medal"],
        "met": report["met"],
        "rows": report["rows"],   # the report card, verbatim
    }


def log_attempt(record):
    """Append one attempt. Returns (stored, error).

    A failed write returns the plain-English reason instead of raising:
    the class shouldn't lose the running sim because a disk was full —
    but the message goes on screen, because a score that didn't save must
    never look saved.
    """
    global ATTEMPTS
    with _log_lock:
        try:
            stored = attempts.append(record)
        except attempts.AttemptsError as exc:
            return None, str(exc)
        ATTEMPTS = attempts.load()
        return stored, None


def best_attempt(loop, name):
    """The best run of one challenge so far, for the card's line.

    Ties go to the earlier run — to take the top spot you have to BEAT
    it, not match it.
    """
    runs = [a for a in ATTEMPTS
            if a.get("loop") == loop and a.get("name") == name
            and a.get("mode") == "challenge"]
    if not runs:
        return None
    best = max(runs, key=lambda a: a.get("points") or 0)
    return {"points": best.get("points"), "medal": best.get("medal"),
            "met": best.get("met"), "label": best.get("label"),
            "wall_time": best.get("wall_time"), "runs": len(runs)}

CHALLENGES = {
    "temp": {
        "cold_store": {
            "title": "Cold-store lock-in",
            "story": "The door shut behind you: -10 °C for one sim-hour. "
                     "This body is past shivering and its vessel "
                     "response has failed (severe hypothermia really "
                     "does both). Movement is the only heat you have — "
                     "and exhaustion caps exercise at half the hour. "
                     "Spend it well.",
            "goal": "Core at 36.0 °C or better when the door opens, "
                    "never below 35.0, exercise at most 50% of the "
                    "hour. The room stays at -5 °C or colder.",
            "duration_s": 3600,
            "speed": 4,
            "setup": {"fever": 0.0, "exercise": False, "sensor": True,
                      "env": -10.0,
                      "effectors": {"sweat": True, "shiver": False,
                                    "vaso": False}},
            "start_actions": [],
            "metrics": "cold_store",
            # M26 sweep: 40 % duty 88, 45 % 84, 50 % 80 (all MET); the
            # near misses 35 % 67 and 30 % 63; resting 20. Gold is the
            # CHEAP rescue — spending the whole allowance is silver.
            "medals": {"gold": 84, "silver": 76, "bronze": 60},
        },
    },
    "glucose": {
        "t1_shift": {
            "title": "The type 1 shift",
            "story": "Your patient's beta cells are gone, breakfast "
                     "(60 g) just landed, and for the next five "
                     "sim-hours YOU are the control center. Boluses, "
                     "basal, juice boxes — even the pump, if you decide "
                     "a machine should take the shift.",
            "goal": "At least 75% of the window in 70-180 mg/dL, never "
                    "below 65. Beta cells stay off.",
            "duration_s": 5 * 3600,
            "speed": 16,
            "setup": {**HEALTHY_GLUCOSE,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True}},
            "start_actions": [("eat", (60, 1.0))],
            "metrics": "t1_shift",
            # M26 sweep: 4 U with the meal 91, 4 U + basal 0.5 87, the
            # split 2+2 86, 2 U + basal 85, 2 U alone 84, basal-only 72,
            # a late 4 U 66 — and every run that went hypo (54, 52, 34)
            # lands under bronze, whatever its average looked like.
            "medals": {"gold": 85, "silver": 72, "bronze": 60},
        },
    },
    "water": {
        "aid_station": {
            "title": "Aid station",
            "story": "Your runner's thirst has gone silent (hard "
                     "exercise really does mute it) and their ADH sits "
                     "frozen mid-range — the charts are the only "
                     "osmoreceptor left, and you are reading them. Four "
                     "sim-hours of sweating: pour the drinks at the "
                     "right rhythm. Remember the aid station's classic "
                     "kill is too MUCH water.",
            "goal": "At least 90% of the window inside 280-300 mOsm/L, "
                    "never below 275 or above 305. The runner keeps "
                    "moving; the sensor stays dead.",
            "duration_s": 4 * 3600,
            "speed": 16,
            "setup": {"exercise": True, "sensor": False,
                      "effectors": {"adh": True, "kidney": True,
                                    "access": True}},
            "start_actions": [],
            "metrics": "aid_station",
            # M26 sweep: 250 mL every 15 min 100, every 20 min 99, 1 L
            # hourly 98, 1 L every 45 min 96, every 12 min 94 — gold is
            # the rhythm that stays nearest 290. Every over-pour (the
            # 3 L chug 58, 250 mL every 10 min 37) misses a medal.
            "medals": {"gold": 95, "silver": 80, "bronze": 60},
        },
    },
}


def _apply_preset(sim, p):
    """Push a preset's full configuration through the engine's public
    API. Only keys present in the entry are touched."""
    for name, on in p.get("effectors", {}).items():
        sim.set_effector_enabled(name, on)
    if "sensor" in p:
        sim.set_sensor_enabled(p["sensor"])
    if "exercise" in p:
        sim.set_exercise(p["exercise"])
    if "env" in p:
        sim.set_env_temp(p["env"])
    if "fever" in p:
        sim.set_fever(p["fever"])
    if "sensitivity" in p:
        sim.set_insulin_sensitivity(p["sensitivity"])
    if "pump" in p:
        sim.set_pump_enabled(p["pump"])
    if "basal" in p:
        sim.set_basal_rate(p["basal"])


@app.route("/control", methods=["POST"])
def control():
    """Play/pause/reset/speed + disturbances + toggles, per loop.
    Loop-specific actions (env_temp on temp, eat on glucose) 400 cleanly
    if sent to the wrong loop."""
    runner = _runner()
    if runner is None:
        return jsonify({"error": "unknown loop"}), 400
    cmd = request.get_json(force=True, silent=True) or {}
    action = cmd.get("action")
    runner.advance()   # settle time owed under the OLD settings first
    with runner.lock:
        if action == "pause":
            runner.running = False
        elif action == "resume":
            runner.running = True
        elif action == "reset":
            runner.sim.reset()
            runner.running = True
            runner.preset = None
            runner.challenge = None
            runner.attempt_error = None
        elif action == "speed":
            value = cmd.get("value")
            if value not in (1, 4, 16):
                return jsonify({"error": f"speed must be 1, 4 or 16, "
                                         f"got {value!r}"}), 400
            runner.speed = value
        elif action == "env_temp":
            if not hasattr(runner.sim, "set_env_temp"):
                return jsonify({"error": "env_temp is a temperature-loop "
                                         "action"}), 400
            try:
                value = float(cmd.get("value"))
            except (TypeError, ValueError):
                return jsonify({"error": "env_temp needs a number"}), 400
            value = max(ENV_TEMP_MIN, min(ENV_TEMP_MAX, value))
            runner.sim.set_env_temp(value)
        elif action == "exercise":
            runner.sim.set_exercise(bool(cmd.get("value")))
        elif action == "effector":
            name = cmd.get("name")
            try:
                runner.sim.set_effector_enabled(name, bool(cmd.get("value")))
            except KeyError as e:
                return jsonify({"error": str(e)}), 400
        elif action == "sensor":
            runner.sim.set_sensor_enabled(bool(cmd.get("value")))
        elif action == "eat":
            if not hasattr(runner.sim, "eat"):
                return jsonify({"error": "eat is a glucose-loop action"}), 400
            try:
                runner.sim.eat(float(cmd.get("grams", 60)),
                               float(cmd.get("rate", 1.0)))
            except (TypeError, ValueError) as e:
                return jsonify({"error": str(e)}), 400
            runner.running = True   # a meal should visibly happen
        elif action == "inject":
            if not hasattr(runner.sim, "inject"):
                return jsonify({"error": "inject is a glucose-loop "
                                         "action"}), 400
            try:
                units = float(cmd.get("units"))
            except (TypeError, ValueError):
                return jsonify({"error": "inject needs a number of "
                                         "units"}), 400
            # Sane single-dose cap is server policy; the engine is a model
            # and accepts any positive dose (BUILDLOG M11 decision 4).
            units = min(units, MAX_SINGLE_DOSE_U)
            try:
                runner.sim.inject(units)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            runner.running = True   # an injection should visibly happen
        elif action == "basal":
            if not hasattr(runner.sim, "set_basal_rate"):
                return jsonify({"error": "basal is a glucose-loop "
                                         "action"}), 400
            if runner.sim.state().get("pump_enabled"):
                return jsonify({"error": "the pump is running and owns "
                                         "the basal - switch it off "
                                         "first"}), 400
            value = cmd.get("value")
            if value not in ALLOWED_BASAL_RATES:
                return jsonify({"error": f"basal rate must be one of "
                                         f"{sorted(ALLOWED_BASAL_RATES)}, "
                                         f"got {value!r}"}), 400
            runner.sim.set_basal_rate(float(value))
            runner.running = True   # so is a basal change
        elif action == "pump":
            if not hasattr(runner.sim, "set_pump_enabled"):
                return jsonify({"error": "pump is a glucose-loop "
                                         "action"}), 400
            runner.sim.set_pump_enabled(bool(cmd.get("value")))
            runner.running = True   # switching the pump should be visible
        elif action == "drink":
            if not hasattr(runner.sim, "drink"):
                return jsonify({"error": "drink is a water-loop "
                                         "action"}), 400
            try:
                ml = float(cmd.get("ml"))
            except (TypeError, ValueError):
                return jsonify({"error": "drink needs a number of mL"}), 400
            ml = min(ml, MAX_SINGLE_DRINK_ML)   # server policy, like doses
            try:
                runner.sim.drink(ml)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            runner.running = True   # a drink should visibly happen
        elif action == "salty":
            if not hasattr(runner.sim, "eat_salt"):
                return jsonify({"error": "salty is a water-loop "
                                         "action"}), 400
            try:
                mosm = float(cmd.get("mosm", 300))
            except (TypeError, ValueError):
                return jsonify({"error": "salty needs a number of "
                                         "mOsm"}), 400
            mosm = min(mosm, MAX_SALT_MOSM)
            try:
                runner.sim.eat_salt(mosm)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            runner.running = True   # so should a salty snack
        elif action == "preset":
            loop = request.args.get("loop", "temp")
            name = cmd.get("value")
            entry = PRESETS.get(loop, {}).get(name)
            if entry is None:
                return jsonify({"error": f"unknown preset {name!r} for "
                                         f"the {loop} loop"}), 400
            _apply_preset(runner.sim, entry)
            runner.speed = entry["speed"]
            # Healthy clears the banner; a disease raises it. Manual
            # breaker flips afterwards do NOT clear it — the teacher is
            # dissecting the disease, not curing it (kickoff SS2).
            runner.preset = (None if entry["banner"] is None else
                             {"name": name, "label": entry["label"],
                              "banner": entry["banner"]})
            runner.running = True   # a diagnosis should visibly happen
        elif action == "challenge":
            loop = request.args.get("loop", "temp")
            name = cmd.get("value")
            entry = CHALLENGES.get(loop, {}).get(name)
            if entry is None:
                return jsonify({"error": f"unknown challenge {name!r} "
                                         f"for the {loop} loop"}), 400
            _apply_preset(runner.sim, entry["setup"])
            for method, args in entry.get("start_actions", []):
                getattr(runner.sim, method)(*args)
            runner.speed = entry["speed"]
            t0 = runner.sim.state()["t"]
            runner.challenge = {"loop": loop, "name": name,
                                "t_start": t0,
                                "t_end": t0 + entry["duration_s"],
                                "report": None, "score": None,
                                "attempt": None,
                                "label": None}   # team name arrives M27
            runner.attempt_error = None
            runner.preset = None   # the challenge card owns the story now
            runner.running = True
        elif action == "scenario":
            # Dispatch by LOOP NAME (M21): three loops now share this
            # action, and hasattr-sniffing can't tell glucose from water.
            loop = request.args.get("loop", "temp")
            name = cmd.get("value")
            if loop == "temp":
                if name not in SCENARIOS:
                    return jsonify({"error": f"unknown scenario {name!r}"}), 400
                env_temp, exercise = SCENARIOS[name]
                runner.sim.set_env_temp(env_temp)
                runner.sim.set_exercise(exercise)
            elif loop == "glucose" and name == "fast":
                # A fast is the absence of eating: nothing to inject, just
                # stop exercising and make hours pass quickly on screen.
                # (Anything still in the gut keeps absorbing - you can't
                # un-eat.)
                runner.sim.set_exercise(False)
                runner.speed = 16
            elif loop == "glucose" and name == "t1_morning":
                # Type 1 morning (M13): the beta cells are gone and the
                # day starts moving. Basal, breakfast, and boluses are the
                # class's decisions from here — this button only sets the
                # stage, it never resets the run.
                runner.sim.set_effector_enabled("beta", False)
                runner.sim.set_exercise(False)
                runner.speed = 16
            elif loop == "glucose" and name == "pump_day":
                # Artificial pancreas day (M16): same broken pancreas,
                # but the machine loop takes the shift. Never resets.
                runner.sim.set_effector_enabled("beta", False)
                runner.sim.set_exercise(False)
                runner.sim.set_pump_enabled(True)
                runner.speed = 16
            elif loop == "water" and name == "desert":
                # A day in the desert (M21): sweating, nothing to drink.
                # ADH will conserve heroically and lose anyway.
                runner.sim.set_effector_enabled("access", False)
                runner.sim.set_exercise(True)
                runner.speed = 16
            elif loop == "water" and name == "contest":
                # Water-drinking contest: 3 L, fast. The kidneys will
                # have opinions.
                runner.sim.drink(3000)
                runner.sim.set_exercise(False)
                runner.speed = 16
            else:
                return jsonify({"error": f"unknown scenario {name!r} for "
                                         f"the {loop} loop"}), 400
            runner.running = True   # a scenario should visibly happen
        else:
            return jsonify({"error": f"unknown action {action!r}"}), 400
    return jsonify(runner.snapshot(since=float("inf")))


# Column order for the CSVs: the frozen record fields (kickoff SS5), time
# first, then the story left to right. The values come straight from
# engine history — the spreadsheet a student opens matches the charts.
CSV_FIELDS = {
    "temp": ["t", "core_temp", "env_temp", "exercise", "error",
             "sweat", "shiver", "vaso", "sweat_enabled", "shiver_enabled",
             "vaso_enabled", "sensor_enabled",
             # grown at M17 with the Phase 5 disease fields — appended so
             # earlier spreadsheets keep their column positions
             "fever_offset"],
    "glucose": ["t", "glucose", "gut_carbs", "exercise", "error",
                "insulin", "glucagon", "uptake", "liver_flux",
                "beta_enabled", "alpha_enabled", "liver_enabled",
                "sensor_enabled",
                # grown at M12 with the Phase 3 dosing fields — appended so
                # Phase 2 spreadsheets keep their column positions
                "injected_insulin", "total_insulin", "iob_units",
                "basal_rate",
                # grown at M15 with the Phase 4 pump fields, same rule
                "pump_enabled", "pump_rate",
                # grown at M17 with the Phase 5 disease knob, same rule
                "insulin_sensitivity"],
    "water": ["t", "osmolarity", "water_liters", "gut_water", "exercise",
              "error", "adh", "thirst", "urine_rate", "urine_osm",
              "adh_enabled", "kidney_enabled", "water_access",
              "sensor_enabled"],
}


@app.route("/export.csv")
def export_csv():
    loop = request.args.get("loop", "temp")
    runner = runners.get(loop)
    if runner is None:
        return jsonify({"error": "unknown loop"}), 400
    runner.advance()
    with runner.lock:
        records = runner.sim.history()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS[loop])
    writer.writeheader()
    for r in records:
        row = dict(r)
        for k, v in row.items():
            if isinstance(v, bool):
                row[k] = 1 if v else 0        # spreadsheet-friendly bools
            elif isinstance(v, float):
                row[k] = round(v, 4)
        writer.writerow(row)
    return Response(buf.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition":
            f"attachment; filename=vital_loop_{loop}_run.csv"})


if __name__ == "__main__":
    # run.bat lands here. Port is this project's own — see CLAUDE.md.
    app.run(port=5083)
