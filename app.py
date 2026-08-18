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
import re
import threading
import time
from urllib.parse import unquote

from flask import Flask, Response, jsonify, render_template, request

import attempts
import periods
from engine.glucose import GlucoseSimulation
from engine.sim import Simulation
from engine.body import Body
from engine.water import WaterSimulation
from sessions import RoomFull, SessionRegistry

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
        self.case = None         # active diagnosis case (M28):
                                 # {loop, name, grade, attempt, label}.
                                 # While its grade is None the snapshot
                                 # is REDACTED — see redact_record().
        self.case_index = 0      # the rotation counter (kickoff SS2: a
                                 # fixed order, never a die roll)
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
                self._step(n)

    # ---------------- crisis mode (M29) ----------------
    #
    # The wall clock decides HOW MANY ticks to run; the three methods
    # below decide how those ticks are cut up. That distinction is the
    # whole milestone: an ambush stamped at +45 min must land at +45 min
    # whether the browser polled four times a second or once a minute,
    # because the run a teacher rehearses at home has to be the run the
    # class gets.

    def _step(self, n):
        """Advance n ticks, stopping ON THE EXACT TICK of every scheduled
        event. Call with self.lock HELD.

        A challenge with no schedule and no hard stops falls straight
        through to one sim.step(n) — M24-M28 behave exactly as before.
        """
        while n > 0:
            event = self._pending_event()
            t = self.sim.state()["t"]
            if event is not None and event["t"] <= t:
                self._fire_event(event)
                continue
            # max(1, ...) is the anti-wedge: every sim-time in this app is
            # a whole second, so the gap to an event is never fractional —
            # but a chunk of 0 here would spin forever, and "hard to wedge
            # mid-class" outranks trusting that a later phase keeps the
            # tick a whole number. A fractional gap just fires one tick
            # late instead.
            chunk = n if event is None else min(n, max(1, int(event["t"] - t)))
            self._step_watched(chunk)
            n -= chunk

    def _pending_event(self):
        """The next ambush still owed, or None.

        Nothing is owed once the window has closed — a hard stop ends the
        ambushes with it, because a run that finished in the ER is over.
        """
        c = self.challenge
        if c is None or c["stopped"] or c["next_event"] >= len(c["schedule"]):
            return None
        return c["schedule"][c["next_event"]]

    def _fire_event(self, event):
        """One ambush, applied through the SAME public API the buttons
        call — no private engine access and no new engine code (Phase 8
        kickoff SS0), which is why a second breakfast behaves exactly like
        a teacher pressing "eat"."""
        method, args = event["do"]
        getattr(self.sim, method)(*args)
        self.challenge["feed"].append({"t": event["t"], "at": event["at"],
                                       "line": event["line"]})
        self.challenge["next_event"] += 1

    def _live_stops(self):
        """The hard-stop lines being watched right now, if any."""
        c = self.challenge
        if c is None or c["stopped"] or c["report"] is not None:
            return None
        return STOPS.get(CHALLENGES[c["loop"]][c["name"]]["metrics"])

    def _step_watched(self, n):
        """Exactly n ticks, tested against the hard-stop lines on EVERY
        one of them.

        Not once per chunk: the tick a line was crossed on must not depend
        on how the polls happened to fall. Crossing one CLOSES THE WINDOW
        at that tick — and the simulation carries straight on, because a
        fail state here is a report card, never a game-over screen.
        """
        stops = self._live_stops()
        if not stops:
            self.sim.step(n)
            return
        c = self.challenge
        left = n
        while left > 0:
            self.sim.step(1)
            left -= 1
            r = self.sim.state()
            if r["t"] > c["t_end"]:
                break                      # past the buzzer; nothing to watch
            hit = next((s for s in stops if s["test"](r)), None)
            if hit is not None:
                c["stopped"] = {"key": hit["key"], "line": hit["line"],
                                "t": r["t"]}
                c["t_end"] = r["t"]        # the window ended where it ended
                break
        if left:
            self.sim.step(left)

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
                              label=c.get("label"), events=c["feed"]))
        return {
            "name": c["name"],
            "title": entry["title"],
            "goal": entry["goal"],
            "label": c.get("label"),      # whose run this is (M27)
            "t_start": c["t_start"],
            "t_end": c["t_end"],
            "done": done,
            "report": c["report"],
            "score": c.get("score"),
            "attempt": c.get("attempt"),
            # What has ALREADY hit them (M29) — never the schedule. An
            # ambush a student can read in devtools is a timetable.
            "events": c["feed"],
            "stopped": c["stopped"],
        }

    def _case_block(self):
        """The case block for /state — and it is what a student reads in
        devtools, so it names nothing.

        There is no case id in here: the picker sends an INDEX, so the
        payload carries "case 2 of 4" and a neutral brief and that's all.
        The truth and the teaching note arrive only once the class has
        committed to an answer.
        """
        if self.case is None:
            return None
        entries = CASES[self.case["loop"]]
        entry = entries[self.case["name"]]
        grade = self.case["grade"]
        block = {
            "n": list(entries).index(self.case["name"]) + 1,
            "of": len(entries),
            "brief": entry["brief"],
            "warmup_s": entry["warmup_s"],
            "label": self.case.get("label"),
            "answered": grade is not None,
        }
        if grade is not None:
            block["grade"] = grade
            block["attempt"] = self.case.get("attempt")
        return block

    def blind(self):
        """True while a case is running and the class hasn't answered."""
        return self.case is not None and self.case["grade"] is None

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
            case = self._case_block()
            blind = self.blind()
        points = [r for r in records if r["t"] > since]
        if len(points) > MAX_POINTS_PER_RESPONSE:
            stride = -(-len(points) // MAX_POINTS_PER_RESPONSE)  # ceil div
            # Keep the newest point exact so the readout matches the chart.
            points = points[::stride] + [points[-1]]
        if blind:
            # The gate (M28). Redact AFTER downsampling — only what
            # actually leaves needs the treatment — and redact the
            # preset too: the disease banner names the diagnosis in
            # words, which is a more direct answer key than any flag.
            state = redact_record(self.loop, state)
            points = [redact_record(self.loop, r) for r in points]
        out = {
            "running": self.running,
            "speed": self.speed,
            "preset": None if blind else self.preset,
            "now": state,
            "points": points,
        }
        if doses is not None:
            out["doses"] = doses
        if drinks is not None:
            out["drinks"] = drinks
        if challenge is not None:
            out["challenge"] = challenge
        if case is not None:
            out["case"] = case
        # The card's "best so far" line, and any complaint from the log —
        # a score that failed to save says so on screen (M26).
        out["bests"] = {cid: best_attempt(self.loop, cid)
                        for cid in CHALLENGES.get(self.loop, {})}
        out["leaderboard"] = {cid: leaderboard(self.loop, cid)
                              for cid in CHALLENGES.get(self.loop, {})}
        out["attempts_error"] = self.attempt_error or ATTEMPTS_WARNING
        return out


def _make_runners():
    """One fresh set of the three loops — the unit a session owns (M33)."""
    return {
        "temp": Runner(Simulation(), "temp"),
        "glucose": Runner(GlucoseSimulation(), "glucose"),
        "water": Runner(WaterSimulation(), "water"),
        # M39: the coupled body — two loops on one clock.
        "body": Runner(Body(), "body"),
    }


# Loops that are DELIBERATELY sandbox-only for now: explorable, but with
# no challenge, case or preset yet. Declared here rather than hidden in a
# test, because the lesson grammar (M30) is a real promise and an
# exception to it should be visible in the app. The coupled body joins
# the grammar at M41 and this set goes empty again — pinned at M42.
# M41 filled the coupled body's grammar in, so the exception is over.
SANDBOX_ONLY_LOOPS = set()


# The DEFAULT session: any client that presents no session id (verify.py,
# pytest, curl) drives these, exactly as it has since M7 — which is what
# keeps eight phases of tests meaning what they meant. The projector is
# just the teacher's browser now, and that browser carries a sid like
# everyone else's.
runners = _make_runners()

# Per-device sessions (M33). The cap bounds worst-case memory (history
# is a data product and grows all period); the idle sweep returns a
# closed tab's memory within half an hour. Both are app policy, tunable.
MAX_SESSIONS = 40
SESSION_IDLE_S = 30 * 60
registry = SessionRegistry(_make_runners, MAX_SESSIONS, SESSION_IDLE_S)


# The teacher's period list (M43), read once at launch — periods.txt is
# in verify.py's SERVED_SOURCES, so a server holding last year's list
# fails verification by name instead of quietly serving stale periods.
PERIODS = periods.load_periods()


def _cookie_period():
    """The period this request claims: a name off the teacher's list,
    "" for Unassigned (skipped, or a stale cookie naming a period that
    is no longer on the list — never an error on a student's phone),
    or None for no claim at all (cookieless clients, and every client
    from before M43)."""
    raw = request.cookies.get("vl_period")
    if raw is None:
        return None
    claimed = unquote(raw)
    return claimed if claimed in PERIODS else ""


def _cookie_team():
    """The team name this request claims, through the same hygiene as
    the challenge cards' labels (M27), or None for no claim."""
    raw = request.cookies.get("vl_team")
    if raw is None:
        return None
    return clean_label(unquote(raw))


def _session_runners():
    """The runners this REQUEST addresses: its session's own, or the
    default set for a client with no session id. May raise RoomFull.
    A session's period/team claims (M43) refresh on every touch — the
    cookie is the source of truth, the registry only mirrors it."""
    sid = request.cookies.get("vl_sid")
    if not sid:
        return runners
    return registry.runners_for(sid[:64], period=_cookie_period(),
                                team=_cookie_team())


def _runner():
    """The Runner the request addresses (?loop=temp|glucose, default temp),
    or None for an unknown loop name."""
    return _session_runners().get(request.args.get("loop", "temp"))


@app.errorhandler(RoomFull)
def _room_full(exc):
    """The cap, refused in plain English — never a stack trace on a
    student's phone."""
    if request.path == "/":
        return (f"<h1>Vital Loop</h1><p>{exc}</p>", 503)
    return jsonify({"error": str(exc)}), 503


@app.route("/")
def index():
    _session_runners()   # a full room refuses the PAGE in words (M33)
    # The challenge table rides into the page via the template, so the
    # card's story/goal text has ONE source (kickoff SS5).
    #
    # CASES deliberately does NOT: the page gets the answer VOCABULARY
    # (the dropdown menus, identical for every case) and a count of how
    # many cases each loop has, and nothing else. Passing the table here
    # would put every setup and every answer in the HTML, one careless
    # {{ case.answer }} away from ending the game (M28).
    return render_template("index.html", challenges=CHALLENGES,
                           answers=ANSWER_OPTIONS,
                           case_counts={loop: len(entries)
                                        for loop, entries in CASES.items()},
                           # M43: an empty list removes the join screen
                           # from the page entirely — joining quietly off.
                           periods=PERIODS)


@app.route("/state")
def state():
    runner = _runner()
    if runner is None:
        return jsonify({"error": "unknown loop"}), 400
    runner.advance()
    since = request.args.get("since", -1.0, type=float)
    out = runner.snapshot(since)
    out["sessions"] = registry.count()   # the room, arriving (M34)
    return jsonify(out)


# Student worksheets (M35). Printable pages, NOT documents in the repo:
# they render from this one table, so they can never drift from the
# app's vocabulary, and the invariants suite pins every field name they
# cite to the frozen record schemas. The worksheet asks; it never
# answers — the student's own run (charts, CSV, report card) is the
# answer key, which is the entire point.
#
# The seven curriculum terms appear on every worksheet EXACTLY
# (kickoff §1: curriculum vocabulary used exactly).
WORKSHEET_TERMS = [
    ("stimulus", "What changed, and in which direction?"),
    ("receptor", "Which sensor noticed, and where in the body is it?"),
    ("control center", "What compares the reading to the set point, "
                       "and what signal does it send?"),
    ("effector", "Name every effector this loop can use, and what "
                 "each one does."),
    ("response", "Which way does the controlled variable move when "
                 "the effectors act?"),
    ("set point", "The number this loop defends (with units):"),
    ("negative feedback", "Why is this loop called NEGATIVE feedback? "
                          "What happens to the responses as the "
                          "controlled variable returns to the set "
                          "point?"),
]

WORKSHEETS = {
    "temp": {
        "title": "The thermoregulation loop",
        "variable": "core body temperature (core_temp, °C)",
        "before": "Run the freezer demo — or your Cold-store lock-in "
                  "run — and keep your charts (or the CSV export) in "
                  "front of you.",
        "fields": ["t", "core_temp", "env_temp", "error",
                   "sweat", "shiver", "vaso"],
        "read": [
            "Your starting core_temp (the t = 0 row): ______ °C",
            "env_temp once the disturbance began: ______ °C",
            "The most extreme core_temp your run reached: ______ °C",
            "On the first tick where shiver rose above 0, what did "
            "error read? ______",
            "While the body defended itself, which way was vaso "
            "pinned — toward +1 (vessels open, dumping heat) or −1 "
            "(clamped, keeping it)? ______",
            "What did sweat read for the whole cold stretch — and "
            "why does the loop leave that effector alone here? ______",
        ],
    },
    "glucose": {
        "title": "The blood-glucose loop",
        "variable": "blood glucose (glucose, mg/dL)",
        "before": "Eat a 60 g meal in the sandbox — or use your Type 1 "
                  "shift run — and keep your charts (or the CSV "
                  "export) in front of you.",
        "fields": ["t", "glucose", "gut_carbs", "insulin", "glucagon",
                   "uptake"],
        "read": [
            "Fasting glucose before the meal: ______ mg/dL",
            "Peak glucose after the meal: ______ mg/dL, at "
            "t = ______",
            "What did insulin do as glucose climbed? ______",
            "What did glucagon do over the same stretch — and why "
            "does the loop silence it? ______",
            "While gut_carbs drained toward zero, what happened to "
            "uptake — where was the sugar going? ______",
            "About how long did the body take to bring glucose back "
            "under 140 mg/dL? ______",
        ],
    },
    "water": {
        "title": "The water/ADH loop",
        "variable": "plasma osmolarity (osmolarity, mOsm/L)",
        "before": "Eat the salty snack and wait — or use your Aid "
                  "station run — and keep your charts (or the CSV "
                  "export) in front of you.",
        "fields": ["osmolarity", "adh", "thirst", "urine_rate",
                   "urine_osm"],
        "read": [
            "Resting osmolarity before the disturbance: ______ "
            "mOsm/L",
            "The most extreme osmolarity your run reached: ______",
            "adh at that moment: ______ — and urine_rate: ______ "
            "mL/min",
            "urine_osm while the body was CONSERVING water: ______ — "
            "and while it was FLOODING the excess: ______",
            "Which woke first, adh or thirst — and why does the loop "
            "reach for the cheaper response before the behavior? "
            "______",
            "Did the body ever drink with nobody at the keyboard? "
            "What on the chart tells you? ______",
        ],
    },
}


@app.template_filter("replace_fields")
def _mark_fields(text, fields):
    """Wrap a worksheet question's cited column names in <code>, so the
    words a student greps their CSV for look like what they'll find."""
    from markupsafe import Markup, escape
    out = str(escape(text))
    for f in sorted(set(fields), key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(f)}\b", f"<code>{f}</code>", out)
    return Markup(out)


WORKSHEETS["body"] = {
    "title": "Two loops, one body",
    "variable": "blood glucose AND plasma osmolarity, at the same time",
    "before": "Open the Whole body tab, switch the beta cells off, and "
              "feed the body a meal. Let it run until the urine "
              "readings change, and keep your charts (or the CSV "
              "export) in front of you.",
    "fields": ["glucose", "renal_loss", "tubular_load", "glucose_osm",
               "osmolarity", "urine_rate", "urine_osm", "thirst"],
    "read": [
        "The glucose reading at the moment renal_loss first rose above "
        "zero: ______ mg/dL. Why that number and not some other? ______",
        "At the peak: renal_loss ______ mg/dL/min, and the "
        "tubular_load it became: ______ mOsm/min",
        "urine_rate before the spill started: ______ mL/min, and at the "
        "peak of it: ______ mL/min",
        "urine_osm during the spill: ______ mOsm/L. Is that urine "
        "dilute or concentrated? ______",
        "What was adh doing at that same moment — and what does that "
        "tell you about whether the water loop is broken? ______",
        "glucose_osm is the sugar's own share of plasma osmolarity. At "
        "the peak it was ______ mOsm/L. Which receptors feel that, and "
        "what did thirst do about it? ______",
        "How much did this body drink, compared with a healthy one? "
        "______ (Count the drink markers on the chart.)",
    ],
}


@app.route("/worksheet/<loop>")
def worksheet(loop):
    entry = WORKSHEETS.get(loop)
    if entry is None:
        return jsonify({"error": f"no worksheet for {loop!r} — the "
                                 "loops are temp, glucose and "
                                 "water"}), 400
    return render_template("worksheet.html", loop=loop, ws=entry,
                           terms=WORKSHEET_TERMS)


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
                 "effectors": {"adh": True, "kidney": True, "access": True},
                 "adh_override": None}   # M31 knob: every water preset
                                         # clears it — diseases never stack

HEALTHY_BODY = {"exercise": False, "sensor": True,
                "effectors": {"beta": True, "alpha": True, "liver": True,
                              "adh": True, "kidney": True, "access": True},
                "sensitivity": 1.0, "pump": False, "basal": 0.0,
                "adh_override": None}

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
        "siadh": {
            "label": "SIADH",
            "banner": "ADH pours out no matter what the receptors say — "
                      "Syndrome of Inappropriate ADH secretion, the "
                      "mirror image of insipidus (a control center "
                      "defending nothing). The kidneys obey a hormone "
                      "that shouldn't be there, so every ordinary glass "
                      "now dilutes the blood — and thirst never warns, "
                      "because a loop can't feel holding too much. "
                      "First-line treatment: restrict water.",
            "speed": 16,
            **{**HEALTHY_WATER, "adh_override": 1.0}},
    },
    "body": {
        "healthy": {"label": "Healthy", "banner": None, "speed": 1,
                    **HEALTHY_BODY},
        "untreated_mellitus": {
            "label": "Untreated diabetes mellitus",
            "banner": "no insulin, and now BOTH loops are in it. Sugar "
                      "climbs past what the kidney can hold onto, spills "
                      "into the urine, and drags water out with it — "
                      "while the sugar still in the blood pulls on the "
                      "osmoreceptors directly. Polyuria, polydipsia, and "
                      "a water loop working perfectly and still losing. "
                      "Mellitus = honey-sweet: that urine really does "
                      "carry the sugar.",
            "speed": 16,
            **{**HEALTHY_BODY,
               "effectors": {"beta": False, "alpha": True, "liver": True,
                             "adh": True, "kidney": True, "access": True}}},
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


def _eval_ward(records, metrics="ward_round"):
    """Both loops at once (M41). The sugar is only half the job: this
    patient is not drinking for themselves, so every liter the osmotic
    diuresis takes has to be put back by hand. Treat one and lose."""
    n = max(1, len(records))
    end = records[-1] if records else {}
    lo_g = min((r["glucose"] for r in records), default=0.0)
    hi_osm = max((r["osmolarity"] for r in records), default=0.0)
    lo_osm = min((r["osmolarity"] for r in records), default=0.0)
    end_g = end.get("glucose", 0.0)
    end_osm = end.get("osmolarity", 0.0)
    spilled = sum(r["renal_loss"] for r in records) / 60.0   # mg/dL total
    urine_l = sum(r["urine_rate"] for r in records) / 60.0 / 1000.0
    # The patient cannot drink for themselves — if that comes back on,
    # the class stopped being the one keeping them alive.
    stayed_nbm = all(not r.get("water_access", False) for r in records)         if any("water_access" in r for r in records) else True
    rows = [
        # Scored on DISTANCE from the middle of the target band, not on
        # the raw number. Graded monotonically ("lower is better") a
        # patient crashed to 1 mg/dL would take full marks for the row —
        # the first sweep found exactly that, scoring a lethal hypo the
        # same as doing nothing.
        {"key": "end_glucose", "label": "glucose at the end",
         "value": f"{end_g:.0f} mg/dL (target: 80-180)",
         "met": 80.0 <= end_g <= 180.0, "n": abs(end_g - 130.0)},
        {"key": "lowest", "label": "lowest glucose",
         "value": f"{lo_g:.0f} mg/dL (target: never below 70 - insulin "
                  "is the easy way to kill this patient)",
         "met": lo_g >= 70.0, "n": lo_g},
        {"key": "end_osm", "label": "osmolarity at the end",
         "value": f"{end_osm:.1f} mOsm/L (target: 285-295)",
         "met": 285.0 <= end_osm <= 295.0, "n": abs(end_osm - 290.0)},
        # Graded at 315, not at the healthy 305: this patient ARRIVES
        # hyperosmolar, and the class is answerable for where they take
        # them, not for the state they were handed (M29's rule about not
        # grading past what the scenario itself imposes).
        {"key": "highest_osm", "label": "highest osmolarity",
         "value": f"{hi_osm:.1f} mOsm/L (target: never above 315 - they "
                  "arrived dry, so this row is about not making it "
                  "worse)",
         "met": hi_osm <= 315.0, "n": hi_osm},
        {"key": "lowest_osm", "label": "lowest osmolarity",
         "value": f"{lo_osm:.1f} mOsm/L (target: never below 280 - "
                  "fluids can be overdone too)",
         "met": lo_osm >= 280.0, "n": lo_osm},
        {"key": "sugar_lost", "label": "sugar passed into the urine",
         "value": f"{spilled:.0f} mg/dL of pool", "met": None, "n": spilled},
        {"key": "urine", "label": "urine passed",
         "value": f"{urine_l:.2f} L", "met": None, "n": urine_l},
        {"key": "nbm", "label": "the patient still could not drink alone",
         "value": "yes" if stayed_nbm else "no - water access came back",
         "met": stayed_nbm, "n": None},
    ]
    if metrics in STOPS:
        rows.append(_stop_row(records, metrics))
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


def _eval_ward_crisis(records):
    """The same reading of the same two loops, plus the hard-stop line
    the crisis adds. One evaluator, so the plain round and the crisis
    can never start disagreeing about what a good outcome is."""
    return _eval_ward(records, "ward_crisis")


# ================= Crisis mode (M29) =====================================
#
# A challenge that ambushes you on a schedule. Two pieces of machinery,
# both app-level like everything else in Phase 8:
#
#   EVENTS — (sim-time offset, action, plain-English line) on a challenge
#     entry. The Runner fires them through the same public API the buttons
#     call, ON THE EXACT TICK, so the run a teacher rehearses is the run
#     the class gets. The class sees a live feed of what has landed; the
#     schedule of what HASN'T is never shipped.
#
#   STOPS — hard lines that close the window early. The patient going to
#     the ER ends the run being graded; it does not end the simulation and
#     it never splashes a game over (kickoff SS2 — fail states report).
#
# One table per metrics name, so the stepper that WATCHES a line and the
# report card that QUOTES it can never drift apart. The predicates are
# pure functions of one history record, tested as such.
STOPS = {
    "blast_freezer": [
        {"key": "collapse",
         "line": "the core fell to 34.0 °C — moderate hypothermia, and "
                 "whoever opened that door found somebody confused and "
                 "sitting down",
         "test": lambda r: r["core_temp"] <= 34.0},
    ],
    "crisis_shift": [
        {"key": "er_hypo",
         "line": "glucose fell to 40 mg/dL — severe hypoglycemia, and "
                 "the shift ended in the ER",
         "test": lambda r: r["glucose"] <= 40.0},
        {"key": "er_hyper",
         "line": "glucose reached 400 mg/dL — the patient was admitted "
                 "before the shift was over",
         "test": lambda r: r["glucose"] >= 400.0},
    ],
    "ward_crisis": [
        {"key": "er_hypo",
         "line": "glucose fell to 40 mg/dL — severe hypoglycemia, and "
                 "the insulin you gave is what caused it",
         "test": lambda r: r["glucose"] <= 40.0},
        {"key": "hhs",
         "line": "osmolarity reached 330 mOsm/L — hyperosmolar "
                 "hyperglycemic state, and this patient is now "
                 "unconscious",
         "test": lambda r: r["osmolarity"] >= 330.0},
    ],
    "race_day": [
        {"key": "hyponatremia",
         "line": "osmolarity fell to 265 mOsm/L — water intoxication, "
                 "the aid station's classic kill",
         "test": lambda r: r["osmolarity"] <= 265.0},
        {"key": "collapse",
         "line": "osmolarity reached 320 mOsm/L — your runner collapsed "
                 "dehydrated at the roadside",
         "test": lambda r: r["osmolarity"] >= 320.0},
    ],
}


def _sim_clock(seconds):
    """h:mm of sim-time, the way the challenge clock on the card reads."""
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}"


def _stop_row(records, metrics):
    """Did this window end at a hard-stop line, and where?

    The report card's version of what the stepper was watching — same
    table, so the row can never name a line the runner doesn't enforce.
    A stopped run is scored like an integrity failure (see SCORING): a
    window truncated at twenty minutes would otherwise report a
    flattering percentage, and crashing early must not out-score playing
    the hour out.
    """
    # The window's first record sits one tick after the challenge start.
    start = records[0]["t"] - 1.0 if records else 0.0
    for r in records:
        for stop in STOPS[metrics]:
            if stop["test"](r):
                return {"key": "stopped", "label": "the run went the "
                        "distance", "n": None, "met": False,
                        "value": f"no — {stop['line']} "
                                 f"at {_sim_clock(r['t'] - start)}"}
    return {"key": "stopped", "label": "the run went the distance",
            "value": "yes — nobody was taken out of this one", "met": True,
            "n": None}


def _eval_blast_freezer(records):
    """The cold store again — but this time the room is getting worse
    while the heat budget stays the same size."""
    n = max(1, len(records))
    end = records[-1]["core_temp"] if records else 0.0
    lo = min((r["core_temp"] for r in records), default=0.0)
    duty = 100.0 * sum(1 for r in records if r["exercise"]) / n
    # The ambush is unfixable ON PURPOSE: the compressor takes the store
    # below anything the slider can set, and reaching for the slider at
    # all shows up here. Rising env temp is the tell, not its value —
    # the room the class was given is not the room cold_store gave them.
    warmed = any(b["env_temp"] > a["env_temp"]
                 for a, b in zip(records, records[1:]))
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
        {"key": "door", "label": "the room was never warmed by hand",
         "value": "yes" if not warmed
                  else "no — somebody reached for the thermostat",
         "met": not warmed, "n": None},
        {"key": "parts", "label": "shivering and vessel control stayed "
                                  "failed",
         "value": "yes" if stayed_failed
                  else "no — a broken part came back mid-rescue",
         "met": stayed_failed, "n": None},
        _stop_row(records, "blast_freezer"),
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


def _eval_crisis_shift(records):
    """Three hours as the pancreas, with the day happening TO you."""
    n = max(1, len(records))
    in_range = sum(1 for r in records if 70.0 <= r["glucose"] <= 180.0)
    pct = 100.0 * in_range / n
    lo = min((r["glucose"] for r in records), default=0.0)
    hi = max((r["glucose"] for r in records), default=0.0)
    beta_stayed_off = all(not r["beta_enabled"] for r in records)
    rows = [
        {"key": "in_range", "label": "time in 70-180 mg/dL",
         "value": f"{pct:.0f}% (target: at least 70%)", "met": pct >= 70.0,
         "n": pct},
        {"key": "lowest", "label": "lowest glucose",
         "value": f"{lo:.0f} mg/dL (target: never below 60)",
         "met": lo >= 60.0, "n": lo},
        {"key": "highest", "label": "highest glucose",
         "value": f"{hi:.0f} mg/dL", "met": None, "n": hi},
        {"key": "beta_off", "label": "beta cells stayed off",
         "value": "yes" if beta_stayed_off
                  else "no — the pancreas came back on mid-shift",
         "met": beta_stayed_off, "n": None},
        _stop_row(records, "crisis_shift"),
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


def _eval_race_day(records):
    """Two hours as someone else's osmoreceptor, on a day where other
    people keep handing your runner things."""
    n = max(1, len(records))
    inside = sum(1 for r in records if 280.0 <= r["osmolarity"] <= 300.0)
    pct = 100.0 * inside / n
    lo = min((r["osmolarity"] for r in records), default=0.0)
    hi = max((r["osmolarity"] for r in records), default=0.0)
    sensor_dead = all(not r["sensor_enabled"] for r in records)
    urine_l = sum(r["urine_rate"] for r in records) / 60.0 / 1000.0
    rows = [
        {"key": "in_band", "label": "time inside 280-300 mOsm/L",
         "value": f"{pct:.0f}% (target: at least 80%)", "met": pct >= 80.0,
         "n": pct},
        {"key": "lowest", "label": "lowest osmolarity",
         "value": f"{lo:.1f} mOsm/L (target: never below 272)",
         "met": lo >= 272.0, "n": lo},
        {"key": "highest", "label": "highest osmolarity",
         "value": f"{hi:.1f} mOsm/L (target: never above 310)",
         "met": hi <= 310.0, "n": hi},
        {"key": "urine", "label": "urine passed",
         "value": f"{urine_l:.1f} L", "met": None, "n": urine_l},
        {"key": "sensor", "label": "the osmoreceptors stayed dead",
         "value": "yes" if sensor_dead else "no — the sensor came back",
         "met": sensor_dead, "n": None},
        _stop_row(records, "race_day"),
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


EVALUATORS = {
    "t1_shift": _eval_t1_shift,
    "cold_store": _eval_cold_store,
    "aid_station": _eval_aid_station,
    # M29 — the crisis variants, one per loop
    "blast_freezer": _eval_blast_freezer,
    "crisis_shift": _eval_crisis_shift,
    "race_day": _eval_race_day,
    # M41 — the coupled body, plain and crisis, on one evaluator
    "ward_round": _eval_ward,
    "ward_crisis": _eval_ward_crisis,
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
    # ---- the crisis variants (M29) ----
    #
    # Every one carries a `stopped` line, and it ZEROES rather than docks.
    # Not as a punishment: a hard stop cuts the window short, and a
    # percentage over a truncated window flatters — a run that crashed at
    # twenty minutes would otherwise beat one that played the hour out.
    # Bands here are again from the M29 sweep (numbers in BUILDLOG).
    "blast_freezer": {
        "end_core": {"points": 55, "zero_at": 35.0, "full_at": 36.4},
        "lowest": {"points": 30, "zero_at": 34.2, "full_at": 35.6},
        # Economy still pays — but the band is set where the sweep says
        # survival actually costs, so a team that lives on less than the
        # full allowance is the one that gets the marks for it.
        "duty": {"points": 15, "zero_at": 50.0, "full_at": 32.0,
                 "hard": "exercise ran past exhaustion — this body "
                         "couldn't have kept moving that long"},
        "door": {"integrity": "the thermostat was turned up — that's not "
                              "the freezer you were locked in"},
        "parts": {"integrity": "a broken part came back on — that's not "
                               "the rescue"},
        "stopped": {"integrity": "the hour ended in an ambulance — there "
                                 "is no score for a rescue that needed "
                                 "rescuing"},
    },
    "crisis_shift": {
        "in_range": {"points": 50, "zero_at": 40.0, "full_at": 95.0},
        "lowest": {"points": 35, "zero_at": 50.0, "full_at": 75.0},
        "highest": {"points": 15, "zero_at": 330.0, "full_at": 200.0},
        "beta_off": {"integrity": "the pancreas came back on — the shift "
                                  "doesn't count"},
        "stopped": {"integrity": "the run ended early — there is no score "
                                 "for a shift that finished in the ER"},
    },
    "ward_round": {
        # Distances from the middle of each band: 0 is perfect.
        "end_glucose": {"points": 30, "zero_at": 90.0, "full_at": 25.0},
        "lowest": {"points": 25, "zero_at": 50.0, "full_at": 75.0},
        "end_osm": {"points": 25, "zero_at": 15.0, "full_at": 3.0},
        "highest_osm": {"points": 12, "zero_at": 320.0, "full_at": 305.0},
        "lowest_osm": {"points": 8, "zero_at": 270.0, "full_at": 282.0},
        "nbm": {"integrity": "the patient started drinking for "
                             "themselves — that is not this admission"},
    },
    "ward_crisis": {
        "end_glucose": {"points": 30, "zero_at": 90.0, "full_at": 25.0},
        "lowest": {"points": 25, "zero_at": 50.0, "full_at": 75.0},
        "end_osm": {"points": 25, "zero_at": 15.0, "full_at": 3.0},
        "highest_osm": {"points": 12, "zero_at": 320.0, "full_at": 305.0},
        "lowest_osm": {"points": 8, "zero_at": 270.0, "full_at": 282.0},
        "nbm": {"integrity": "the patient started drinking for "
                             "themselves — that is not this admission"},
        "stopped": {"integrity": "the round ended early — there is no "
                                 "score for a patient who went "
                                 "unconscious on your shift"},
    },
    "race_day": {
        "in_band": {"points": 55, "zero_at": 50.0, "full_at": 100.0},
        # Banded around what the AMBUSHES themselves impose: two liters
        # this class never poured take the best possible run down to
        # 280, and the salt load with no sweating behind it takes it up
        # to 297. Grading past those would dock the class for somebody
        # else's decisions.
        "lowest": {"points": 20, "zero_at": 272.0, "full_at": 280.0},
        "highest": {"points": 25, "zero_at": 302.0, "full_at": 296.0},
        "sensor": {"integrity": "the osmoreceptors came back — the class "
                                "stopped being the sensor"},
        "stopped": {"integrity": "the run ended early — there is no score "
                                 "for a race that finished in the medical "
                                 "tent"},
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


MAX_LABEL_CHARS = 24        # a team name, not an essay


def clean_label(raw):
    """A team name: free text, whitespace tidied, capped short.

    Capped on the SERVER, not just in the box — and it is a TEAM name by
    design (kickoff SS2). A file of named minors on a teacher's laptop is
    a thing we simply don't create.
    """
    if not isinstance(raw, str):
        return None
    return " ".join(raw.split())[:MAX_LABEL_CHARS] or None


def build_attempt(loop, name, report, score, label=None, mode="challenge",
                  events=None):
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
        # -- appended at M27 so the side-by-side can show WHERE a team
        # won. STORED, not recomputed later: if a future phase swaps the
        # scorer for an honors section (kickoff SS5), what this run was
        # worth THAT DAY stays true.
        "score_rows": score["rows"],
        "zeroed": score["zeroed"],
        # -- appended at M29: what the run was AMBUSHED with, and when. A
        # crisis attempt is only readable later if the log says which
        # events the team faced (kickoff SS5).
        "events": list(events or ()),
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


def challenge_runs(loop, name):
    """Every logged run of ONE challenge, best first.

    Ties go to the earlier run — to take the top spot you have to BEAT
    it, not match it.
    """
    runs = [a for a in ATTEMPTS
            if a.get("loop") == loop and a.get("name") == name
            and a.get("mode") == "challenge"]
    return sorted(runs, key=lambda a: (-(a.get("points") or 0),
                                       a.get("wall_time") or ""))


def best_attempt(loop, name):
    """The best run of one challenge so far, for the card's line."""
    runs = challenge_runs(loop, name)
    if not runs:
        return None
    best = runs[0]
    return {"points": best.get("points"), "medal": best.get("medal"),
            "met": best.get("met"), "label": best.get("label"),
            "wall_time": best.get("wall_time"), "runs": len(runs)}


LEADERBOARD_LIMIT = 20      # a class period has teams, not thousands


def leaderboard(loop, name, limit=LEADERBOARD_LIMIT):
    """One compact line per run, best first (M27).

    Read straight off the log — the browser gets the same numbers the
    report cards showed, so a leaderboard can never drift from them.
    """
    return [{"id": a.get("id"), "label": a.get("label"),
             "points": a.get("points"), "medal": a.get("medal"),
             "met": a.get("met"), "wall_time": a.get("wall_time")}
            for a in challenge_runs(loop, name)[:limit]]


def _summary(att):
    """One team's headline, for the top of a compare column."""
    return {"id": att.get("id"), "label": att.get("label"),
            "points": att.get("points"), "medal": att.get("medal"),
            "met": att.get("met"), "wall_time": att.get("wall_time"),
            "zeroed": att.get("zeroed")}


def compare_attempts(a, b):
    """PURE: two finished runs, merged row for row (M27).

    The two teams ran the identical deterministic challenge, so the only
    variable is their physiology — that is what makes this comparison
    fair, and why nothing here recomputes anything. Every number came out
    of the log; this only lines them up and says who took each row.

    A row both teams scored the same is a TIE, not a win. A row carrying
    no points (the integrity lines) goes to whichever team was honest.
    """
    rows_a = {r.get("key"): r for r in a.get("rows") or ()}
    rows_b = {r.get("key"): r for r in b.get("rows") or ()}
    pts_a = {r.get("key"): r for r in a.get("score_rows") or ()}
    pts_b = {r.get("key"): r for r in b.get("score_rows") or ()}
    # The report card's own order — the class reads the same rows in the
    # same sequence they just watched.
    keys = [r.get("key") for r in a.get("rows") or ()]
    keys += [k for k in rows_b if k not in keys]

    def cell(row, scored):
        return {"value": row.get("value") if row else None,
                "met": row.get("met") if row else None,
                "points": scored.get("points") if scored else None,
                "max": scored.get("max") if scored else None}

    merged = []
    for key in keys:
        ra, rb = rows_a.get(key), rows_b.get(key)
        sa, sb = pts_a.get(key), pts_b.get(key)
        winner = None
        if sa and sb and sa["points"] != sb["points"]:
            winner = "a" if sa["points"] > sb["points"] else "b"
        elif not (sa and sb) and ra and rb and ra.get("met") != rb.get("met"):
            if ra.get("met") is not None and rb.get("met") is not None:
                winner = "a" if ra["met"] else "b"
        merged.append({"key": key,
                       "label": (ra or rb or {}).get("label", key),
                       "a": cell(ra, sa), "b": cell(rb, sb),
                       "winner": winner})
    total_a, total_b = a.get("points") or 0, b.get("points") or 0
    return {"a": _summary(a), "b": _summary(b), "rows": merged,
            "winner": None if total_a == total_b
                      else ("a" if total_a > total_b else "b")}

CHALLENGES = {
    "temp": {
        "cold_store": {
            "title": "Cold-store lock-in",
            "start_label": "Lock the door",
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
        "blast_freezer": {
            "title": "The blast freezer",
            "start_label": "Lock the door",
            "crisis": True,
            "story": "The same locked store, the same body — shivering "
                     "gone and the vessel response with it, movement the "
                     "only heat you have, exhaustion still capping it at "
                     "half the hour. One difference: this time you are "
                     "in the part of the warehouse they use for hard "
                     "freezing, and the compressor runs to its own "
                     "schedule. The room is going to get worse. Spend "
                     "accordingly — and watch the feed.",
            "goal": "Core at 36.0 °C or better when the door opens, "
                    "never below 35.0, exercise at most 50% of the hour. "
                    "Don't reach for the thermostat.",
            "duration_s": 3600,
            "speed": 4,
            "setup": {**HEALTHY_TEMP, "env": -5.0,
                      "effectors": {"sweat": True, "shiver": False,
                                    "vaso": False}},
            "start_actions": [],
            "metrics": "blast_freezer",
            "events": [
                {"at": 12 * 60, "do": ("set_env_temp", (-12.0,)),
                 "line": "The compressor cuts in. The store is on its "
                         "way down to −12 °C, and there is nothing left "
                         "in this body that can answer that."},
                {"at": 32 * 60, "do": ("set_env_temp", (-20.0,)),
                 "line": "It drops again — −20 °C, colder than any room "
                         "you could set, and twenty-eight minutes still "
                         "on the clock."},
            ],
            # M29 sweep: 50 % duty spread evenly 85, 48 % 85, the whole
            # allowance banked into the last half 84 (on a lower trough),
            # 45 % 82, 42 % 78, 35 % 69, 30 % 56 — and the SAME 50 %
            # spent in the FIRST half scores 30 and misses. Resting the
            # hour collapses at 0:51. Timing is the crisis lesson here,
            # and it is worth more than fifty points.
            "medals": {"gold": 84, "silver": 72, "bronze": 58},
        },
    },
    "glucose": {
        "t1_shift": {
            "title": "The type 1 shift",
            "start_label": "Start the shift",
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
        "crisis_shift": {
            "title": "The crisis shift",
            "start_label": "Start the shift",
            "crisis": True,
            "story": "The same patient, the same missing beta cells, the "
                     "same 60 g breakfast — and four hours in which you "
                     "do not get to choose what happens next. Dose for "
                     "the day you are given, not the one you planned, "
                     "and remember the juice box is a tool too. Watch "
                     "the feed.",
            "goal": "At least 70% of the window in 70-180 mg/dL, never "
                    "below 60. Beta cells stay off.",
            "duration_s": 4 * 3600,
            "speed": 16,
            "setup": {**HEALTHY_GLUCOSE,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True}},
            "start_actions": [("eat", (60, 1.0))],
            "metrics": "crisis_shift",
            "events": [
                {"at": 55 * 60, "do": ("set_exercise", (True,)),
                 "line": "Gym class, and nobody asked you. Working "
                         "muscle pulls glucose out of the blood whether "
                         "there is insulin on board or not — this drain "
                         "does not need a hormone to work."},
                {"at": 85 * 60, "do": ("set_exercise", (False,)),
                 "line": "They sit back down, and that extra drain stops "
                         "with them."},
                {"at": 130 * 60, "do": ("eat", (40.0, 1.5)),
                 "line": "A visitor brings donuts. Forty grams of fast "
                         "carbohydrate, eaten before anyone can object — "
                         "and this time there is no gym class coming to "
                         "help you with it."},
            ],
            # M29 sweep: 4 U at breakfast + a juice box or two through
            # the gym + 2 U for the donuts scores 86; feeding the gym but
            # ignoring the donuts 83; covering the donuts but never
            # feeding the gym 70 (on a low of 65); 4 U and nothing else
            # 66; over-covering the donuts with 4 U 47; doing nothing 35
            # at a peak of 334. Anything that starts the day with 8 U is
            # in the ER before the gym is over.
            "medals": {"gold": 84, "silver": 72, "bronze": 60},
        },
    },
    "water": {
        "aid_station": {
            "title": "Aid station",
            "start_label": "Take the table",
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
        "race_day": {
            "title": "Race day goes wrong",
            "start_label": "Take the table",
            "crisis": True,
            "story": "Same runner, same silent thirst, same frozen ADH — "
                     "you are still the only osmoreceptor they have. Two "
                     "differences today. They came to the line having "
                     "drunk a liter in the car, so they start the race "
                     "already watered. And other people keep handing "
                     "them things, which you find out about the same "
                     "moment they do. Three hours. Pouring on a rhythm "
                     "will not survive this one — watch the feed.",
            "goal": "At least 80% of the window inside 280-300 mOsm/L, "
                    "never below 272 or above 310. The sensor stays dead.",
            "duration_s": 3 * 3600,
            "speed": 16,
            "setup": {"exercise": True, "sensor": False,
                      "effectors": {"adh": True, "kidney": True,
                                    "access": True}},
            # They arrive over-watered, so the run OPENS on a stretch
            # where the right move is to pour nothing at all — and then
            # sweat slowly turns that around under the class.
            "start_actions": [("drink", (1000.0,))],
            "metrics": "race_day",
            "events": [
                {"at": 45 * 60, "do": ("drink", (1000.0,)),
                 "line": "A spectator hands your runner a full liter of "
                         "plain water and they drink it on the spot, "
                         "before anyone can say otherwise."},
                {"at": 90 * 60, "do": ("set_exercise", (False,)),
                 "line": "They pull up with a torn hamstring and walk "
                         "into the medical tent. The sweating stops with "
                         "them — and everything you had learned about "
                         "their losses just stopped being true."},
                {"at": 140 * 60, "do": ("eat_salt", (600.0,)),
                 "line": "Somebody in the tent gives them electrolyte "
                         "tablets. A whole solute load, swallowed at "
                         "once, into a body that is no longer sweating."},
            ],
            # M29 sweep: reading the feed is worth thirty points here.
            # Wait out the opening load, pour while they run, stop when
            # they pull up: 93. Never pouring at all 54. Every blind
            # rhythm loses — 250 mL/30 min 40, /20 min 36, /15 min 25 —
            # and /10 min drowns the runner outright.
            "medals": {"gold": 85, "silver": 70, "bronze": 55},
        },
    },
    "body": {
        "ward_round": {
            "title": "The ward round",
            "start_label": "Take the patient",
            "story": "Admitted this morning: type 1, and the insulin ran "
                     "out two days ago. Sugar is high and climbing, the "
                     "kidneys are already spilling it, and water is "
                     "going out with it. This patient is too ill to "
                     "drink for themselves — every glass has to come "
                     "from you. Three hours; treat what you can see.",
            "goal": "Glucose 80-180 mg/dL at the end and never below 70; "
                    "osmolarity 285-295 at the end, never above 305 or "
                    "below 280.",
            "duration_s": 3 * 3600,
            "speed": 16,
            "setup": {**HEALTHY_BODY,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True, "adh": True,
                                    "kidney": True, "access": False}},
            "start_actions": [("eat", (100, 2.0)), ("eat_salt", (450,))],
            "metrics": "ward_round",
            # M41 sweep, built only from moves the buttons offer (4 U
            # doses, 250 mL glasses): 4 U + a glass every 30 min 87,
            # every 45 min 86, every 20 min 85 — all three MET. Then the
            # misses: pouring every 15 min 79, insulin alone 77, fluids
            # alone 77, nothing at all 52, and every extra dose of
            # insulin collapses it (two doses 41, four doses 31). Silver
            # sits above the best MISS on purpose.
            "medals": {"gold": 85, "silver": 82, "bronze": 70},
        },
        "ward_crisis": {
            "title": "The ward round goes wrong",
            "start_label": "Take the patient",
            "crisis": True,
            "story": "The same admission, the same two loops — and a day "
                     "that does not leave you alone. Things will happen "
                     "that you did not order. Watch the feed, and "
                     "remember that treating the sugar is only half of "
                     "what this patient is losing.",
            "goal": "Glucose 80-180 mg/dL at the end and never below 70; "
                    "osmolarity 285-295 at the end, never above 305 or "
                    "below 280.",
            "duration_s": 3 * 3600,
            "speed": 16,
            "setup": {**HEALTHY_BODY,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True, "adh": True,
                                    "kidney": True, "access": False}},
            "start_actions": [("eat", (100, 2.0)), ("eat_salt", (450,))],
            "metrics": "ward_crisis",
            "events": [
                {"at": 45 * 60,
                 "do": ("set_insulin_sensitivity", (0.3,)),
                 "line": "The patient spikes a temperature. Illness makes "
                         "tissues deaf to insulin — whatever you have "
                         "given is suddenly worth a fraction of what it "
                         "was, and this is exactly how a ward admission "
                         "turns into an emergency."},
                {"at": 100 * 60,
                 "do": ("eat", (60, 2.0)),
                 "line": "A relative, trying to help, has given them a "
                         "sweet drink because they said they were "
                         "thirsty."},
                {"at": 150 * 60,
                 "do": ("set_exercise", (True,)),
                 "line": "They are moved to a warm side room and start "
                         "sweating — another way out for water you were "
                         "already struggling to replace."},
            ],
            # A HIGHER ladder than the plain round, and the sweep is
            # why: the +150 min sweating ambush takes water back out, so
            # pouring every 15 min — an over-pour that misses in the
            # plain round — scores 88 here. On the plain ladder that
            # would have been a MISS taking gold. 4 U + a glass every
            # 30 min 96, /45 95, /20 94 (all MET); best miss 88.
            "medals": {"gold": 92, "silver": 90, "bronze": 70},
        },
    },
}


# ================= The diagnosis game (M28) ==============================
#
# Every phase so far taught MANAGING a loop. This one tests READING one:
# the app breaks something, refuses to say what, and the class names it
# from the charts and the diagram alone. Three things make that a game
# rather than a quiz:
#
#   * the answer is in curriculum vocabulary — receptor / control center
#     / effector, and WHICH one — so "it's broken" is not an answer and
#     neither is "the temperature is too high",
#   * "nothing is broken" is always on the menu, because a healthy loop
#     working flat out against a big disturbance looks alarming. A class
#     that can't tell those two apart hasn't learned the loop yet,
#   * the disturbance controls stay live while a case runs. Warm the room
#     and see whether it starts sweating: provocative testing is how the
#     diagnosis is actually made, and it's the best thing in this mode.
#
# The breaker card, the disease banner and the CSV all go away while a
# case is blind — see VISIBLE_DURING_CASE below. Assume a student opens
# devtools, because one will.

ANSWER_ROLES = [
    {"key": "receptor", "label": "Receptor — the sensor"},
    {"key": "control", "label": "Control center"},
    {"key": "effector", "label": "Effector"},
    {"key": "none", "label": "Nothing is broken — the loop is working"},
]

# The same four roles on every loop (that's the point — the class learns
# the ROLES, not three unrelated lists), each with that loop's own parts
# in diagram order. Safe to render into the page: it is the menu, not the
# answer.
ANSWER_OPTIONS = {
    "temp": {"roles": ANSWER_ROLES, "parts": [
        {"key": "none", "label": "Nothing is broken"},
        {"key": "sensor", "label": "Thermoreceptors"},
        {"key": "hypothalamus", "label": "Hypothalamus"},
        {"key": "sweat", "label": "Sweat glands"},
        {"key": "shiver", "label": "Skeletal muscles (shivering)"},
        {"key": "vaso", "label": "Skin blood vessels"},
    ]},
    "glucose": {"roles": ANSWER_ROLES, "parts": [
        {"key": "none", "label": "Nothing is broken"},
        {"key": "sensor", "label": "The islets' glucose sensors"},
        {"key": "beta", "label": "Beta cells (insulin)"},
        {"key": "alpha", "label": "Alpha cells (glucagon)"},
        {"key": "muscle", "label": "Muscle & fat (take up glucose)"},
        {"key": "liver", "label": "Liver (releases glucose)"},
    ]},
    # The coupled body (M41): both loops' parts on one menu, because the
    # question is no longer "which part" but "WHICH LOOP" — and the two
    # diseases that pass liters of urine live in different loops.
    "body": {"roles": ANSWER_ROLES, "parts": [
        {"key": "none", "label": "Nothing is broken"},
        {"key": "beta", "label": "Beta cells (insulin)"},
        {"key": "pituitary", "label": "ADH release (hypothalamus → "
                                      "pituitary)"},
        {"key": "kidney", "label": "Kidneys (retain water)"},
        {"key": "thirst", "label": "Thirst → drinking"},
    ]},
    "water": {"roles": ANSWER_ROLES, "parts": [
        {"key": "none", "label": "Nothing is broken"},
        {"key": "sensor", "label": "Osmoreceptors"},
        {"key": "pituitary", "label": "ADH release (hypothalamus → "
                                      "pituitary)"},
        {"key": "kidney", "label": "Kidneys (retain water)"},
        {"key": "thirst", "label": "Thirst → drinking"},
    ]},
}


# THE REDACTION GATE. An ALLOWLIST of what a blind case may ship, not a
# blocklist of what it may not — a blocklist fails OPEN, and the field a
# later phase adds would leak the answer with nobody noticing. Everything
# here is evidence the class reads: the controlled variable, the
# disturbance, the hormone and effector traces, the sensed error. What's
# missing is every `*_enabled` flag (which names the broken part
# outright), `water_access`, and the two disease knobs `fever_offset` and
# `insulin_sensitivity` (which name the diagnosis).
#
# Note the pump fields are absent too. No case uses the pump, and the
# rule "nothing ending in _enabled goes out during a case" is worth more
# than a readout that would say "off" anyway.
VISIBLE_DURING_CASE = {
    "temp": {"t", "core_temp", "env_temp", "exercise", "error",
             "sweat", "shiver", "vaso"},
    "glucose": {"t", "glucose", "gut_carbs", "exercise", "error", "insulin",
                "glucagon", "uptake", "liver_flux", "injected_insulin",
                "total_insulin", "iob_units", "basal_rate"},
    "water": {"t", "osmolarity", "water_liters", "gut_water", "exercise",
              "error", "adh", "thirst", "urine_rate", "urine_osm"},
    # The coupled body (M41) records no breaker flags and no disease
    # knobs at all — every field it keeps is a measurement a clinician
    # would actually have. So the allowlist is the whole record, and
    # redaction here is a no-op BY CONSTRUCTION rather than by trust.
    # The gate still runs, and still fails closed on anything a later
    # phase adds without listing it here on purpose.
    "body": {"t", "glucose", "insulin", "glucagon", "renal_loss",
             "tubular_load", "glucose_osm", "osmolarity", "water_liters",
             "adh", "thirst", "urine_rate", "urine_osm"},
}


def redact_record(loop, record):
    """One history record with the answer key withheld.

    A DELIVERY gate, never data loss (kickoff SS5): the engine went on
    recording every field the whole time, and the reveal hands the lot
    over. This only decides what leaves the building.
    """
    keep = VISIBLE_DURING_CASE[loop]
    return {k: v for k, v in record.items() if k in keep}


# Each case: a setup drawn from the preset/breaker vocabulary the app
# already applies, a NEUTRAL brief (the setting, never the machinery),
# how much of the opening to fast-forward, the correct answer, and the
# one-line teaching note that lands at the reveal.
#
# Two deliberate choices in this table:
#
#   1. Cases that share a loop often share a BRIEF, word for word. The
#      same freezing room, the same breakfast, the same long walk — with
#      opposite answers. A class that reads the story instead of the
#      charts gets nothing, which is the entire skill being taught.
#   2. The roles appear in a DIFFERENT order on each loop. Play a few and
#      you learn the physiology; you can't learn that "case 3 is always
#      the control center", because it isn't.
#
# Case ids never leave the server — the picker sends an index — so a
# readable name here costs nothing.
CASES = {
    "temp": {
        # 1 intact · 2 receptor · 3 control center · 4 effector
        "case1": {
            "brief": "The room is at −10 °C, and this body has been "
                     "standing in it for a while.",
            "setup": {**HEALTHY_TEMP, "env": -10.0},
            "speed": 4,
            "warmup_s": 1800,
            "answer": {"role": "none", "part": "none"},
            "note": "Nothing was broken. The skin vessels clamped down "
                    "and shivering settled in at about half drive, and "
                    "between them they held the core within two tenths "
                    "of the set point — in a freezing room, steadily, "
                    "for as long as you care to watch. A loop under "
                    "stress is not a loop that has failed, and telling "
                    "those two apart is the whole skill.",
        },
        "case2": {
            "brief": "The room is at −10 °C, and this body has been "
                     "standing in it for a while.",
            "setup": {**HEALTHY_TEMP, "env": -10.0, "sensor": False},
            "speed": 4,
            "warmup_s": 1800,
            "answer": {"role": "receptor", "part": "sensor"},
            "note": "The thermoreceptors were reporting 'all is well'. "
                    "Look at what DIDN'T happen: sweat, shivering and "
                    "vessel tone all sat at zero while the core fell "
                    "away, because the control center was never told "
                    "there was a problem. A variable moving with a "
                    "silent loop behind it is a sensing failure — "
                    "compare it with the same freezing room met by a "
                    "body shivering flat out.",
        },
        "case3": {
            "brief": "An ordinary 22 °C room. Nothing unusual about the "
                     "surroundings at all.",
            "setup": {**HEALTHY_TEMP, "fever": 2.0, "env": 22.0},
            "speed": 4,
            "warmup_s": 600,
            "answer": {"role": "control", "part": "hypothalamus"},
            "note": "Nothing is damaged — the hypothalamus is defending "
                    "39 °C instead of 37. Pyrogens moved the set point, "
                    "they didn't break the machinery, which is why this "
                    "body SHIVERS while it is already hot: by its own "
                    "reckoning it isn't hot enough yet. Then it settles "
                    "just under 39 and HOLDS there, and a broken loop "
                    "holds nothing steady. That is a fever: the control "
                    "center answering a different question, perfectly.",
        },
        "case4": {
            "brief": "A 40 °C day, and this body has been exercising in "
                     "it.",
            "setup": {**HEALTHY_TEMP, "env": 40.0, "exercise": True,
                      "effectors": {"sweat": False, "shiver": True,
                                    "vaso": True}},
            "speed": 4,
            "warmup_s": 900,
            "answer": {"role": "effector", "part": "sweat"},
            "note": "The sweat glands never fired. Everything upstream "
                    "worked perfectly — the core rose, the receptors "
                    "read it, the control center called for cooling, the "
                    "vessels dilated as far as they go — and the one "
                    "response that could actually dump this much heat "
                    "produced nothing at all. When a loop senses "
                    "correctly and decides correctly and the variable "
                    "still runs away, look at the effector.",
        },
    },
    "glucose": {
        # 1 control center · 2 intact · 3 effector · 4 receptor
        "case1": {
            "brief": "Breakfast — 60 g of carbohydrate — landed a couple "
                     "of hours ago.",
            "setup": {**HEALTHY_GLUCOSE,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True}},
            "start_actions": [("eat", (60, 1.0))],
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "control", "part": "beta"},
            "note": "No insulin was made at all, however high the "
                    "glucose climbed — the beta cells are gone. The "
                    "receptor was fine and the effectors were fine: "
                    "muscle would have taken glucose up if anything had "
                    "asked it to. This is type 1 diabetes, a CONTROL "
                    "CENTER failure — the problem was seen and the "
                    "message was never sent. And notice the liver, "
                    "pouring glucose into a bloodstream that already has "
                    "far too much: insulin is what normally restrains "
                    "the alpha cells, so with none at all the glucagon "
                    "runs high and nobody tells the liver to stop.",
        },
        "case2": {
            "brief": "Breakfast — 60 g of carbohydrate — landed a couple "
                     "of hours ago.",
            "setup": {**HEALTHY_GLUCOSE},
            "start_actions": [("eat", (60, 1.0))],
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "none", "part": "none"},
            "note": "Nothing was broken. Glucose rose after the meal, "
                    "insulin rose to meet it, uptake climbed, the liver "
                    "was suppressed, and the whole excursion came back "
                    "inside the band. A big swing is not a broken loop; "
                    "it is a loop doing its job on a big disturbance. "
                    "Keep this one in mind — it is the picture the other "
                    "glucose cases are missing.",
        },
        "case3": {
            "brief": "Breakfast — 60 g of carbohydrate — landed a couple "
                     "of hours ago.",
            "setup": {**HEALTHY_GLUCOSE, "sensitivity": 0.05},
            "start_actions": [("eat", (60, 1.0))],
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "effector", "part": "muscle"},
            "note": "Insulin was made — railed at maximum for hours, far "
                    "more than the healthy body ever needed — and the "
                    "glucose stayed high anyway. Both numbers high at "
                    "once is the signature: the message was sent, "
                    "loudly, and the target tissue could not hear it. "
                    "Three hours in, this body is running about six "
                    "times the insulin of the healthy case and buying "
                    "barely any more uptake for it. That is type 2 "
                    "diabetes, and the failure is at the EFFECTOR.",
        },
        "case4": {
            "brief": "No breakfast today — this body has been fasting "
                     "all morning.",
            "setup": {**HEALTHY_GLUCOSE, "sensor": False},
            "speed": 16,
            # 1 h, not 4: the tell is flat hormones under a MOVING
            # variable, and the steep part of the slide has to be inside
            # the chart's 2-hour window when the class arrives.
            "warmup_s": 3600,
            "answer": {"role": "receptor", "part": "sensor"},
            "note": "The islets' glucose sensors were stuck reading a "
                    "perfect 90 mg/dL. Insulin and glucagon are frozen "
                    "at exactly the values a body sitting on its set "
                    "point would hold — reasonable numbers, completely "
                    "unresponsive, while the real glucose slid away "
                    "underneath them. Flat "
                    "hormones under a moving variable is a sensing "
                    "failure. In a patient this is hypoglycemia "
                    "unawareness, and it is dangerous precisely because "
                    "nothing looks dramatic.",
        },
    },
    "water": {
        # 1 effector · 2 control center · 3 receptor · 4 intact
        "case1": {
            "brief": "Resting indoors, with a water bottle within reach "
                     "all morning.",
            "setup": {**HEALTHY_WATER,
                      "effectors": {"adh": True, "kidney": False,
                                    "access": True}},
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "effector", "part": "kidney"},
            "note": "ADH was released — the control center did "
                    "everything right — and the kidneys poured water out "
                    "anyway, litres of it, dilute. The hormone was in "
                    "the blood and the target could not hear it: "
                    "nephrogenic diabetes insipidus, the same deafness "
                    "as type 2 diabetes wearing different clothes. This "
                    "person stays alive because the OTHER effector still "
                    "works — thirst keeps sending them back to the "
                    "bottle.",
        },
        "case2": {
            "brief": "Resting indoors, with a water bottle within reach "
                     "all morning.",
            "setup": {**HEALTHY_WATER,
                      "effectors": {"adh": False, "kidney": True,
                                    "access": True}},
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "control", "part": "pituitary"},
            "note": "No ADH was released at all. The osmoreceptors "
                    "sensed correctly and the kidneys were perfectly "
                    "able to hold water — they were simply never asked. "
                    "Central diabetes insipidus, a control-center "
                    "failure. Telling it from deaf kidneys is exactly "
                    "what measuring ADH is for in the clinic, and on "
                    "these charts it is one trace: hormone at zero, or "
                    "hormone high and ignored.",
        },
        "case3": {
            "brief": "A long walk in the heat, sweating steadily, with "
                     "a bottle in the bag.",
            "setup": {**HEALTHY_WATER, "sensor": False, "exercise": True},
            "speed": 16,
            "warmup_s": 10800,
            "answer": {"role": "receptor", "part": "sensor"},
            "note": "The osmoreceptors were dead. ADH sat frozen at a "
                    "middling value and thirst never spoke, while "
                    "sweating drove osmolarity up and up. Nobody in this "
                    "body knows anything is wrong: no thirst, no "
                    "conservation, no alarm. Compare it with a body that "
                    "is desperately thirsty and has nothing to drink — "
                    "there the alarm works perfectly and the effector "
                    "can't reach water. Here the alarm never sounded.",
        },
        "case4": {
            "brief": "A long walk in the heat, sweating steadily, with "
                     "a bottle in the bag.",
            "setup": {**HEALTHY_WATER, "exercise": True},
            "speed": 16,
            "warmup_s": 10800,
            "answer": {"role": "none", "part": "none"},
            "note": "Nothing was broken. Sweating pushed osmolarity up, "
                    "the osmoreceptors caught it, ADH rose, the kidneys "
                    "conserved — and then the loop reached out through "
                    "the OUTSIDE WORLD and drank, with nobody at the "
                    "keyboard. Every green mark on that chart is this "
                    "body deciding to have a glass of water. No other "
                    "effector in this course does anything like it.",
        },
        # M32: the SIADH case. Same brief as cases 1 and 2, word for
        # word — reading the story earns nothing, reading the traces is
        # everything. The morning's ordinary intake arrives as one
        # start_actions load (the race_day precedent) because the
        # "you joined here" marker assumes warm-up time is warmup_s.
        "case5": {
            "brief": "Resting indoors, with a water bottle within reach "
                     "all morning.",
            "setup": {**HEALTHY_WATER, "adh_override": 1.0},
            "start_actions": [("drink", [1500])],
            "speed": 16,
            "warmup_s": 7200,
            "answer": {"role": "control", "part": "pituitary"},
            "note": "Read the mismatch: osmolarity LOW — this body "
                    "brushed the overhydration line — while ADH sat at "
                    "MAXIMUM and the urine stayed scant and "
                    "concentrated. Secretion inappropriate to the "
                    "stimulus: SIADH, the mirror image of case 2. There "
                    "the control center went silent when it should have "
                    "spoken; here it will not stop talking when it "
                    "should. And notice what never fired: thirst — a "
                    "loop has no alarm for holding too much. The "
                    "treatment falls out of the charts: stop the "
                    "glasses, and the slide stops.",
        },
    },
    # The coupled body (M41). All three cases open on somebody passing
    # far too much urine, and the whole question is WHICH LOOP is at
    # fault. For two thousand years that answer came from tasting it;
    # here it comes from the urine concentration trace and the glucose
    # reading — the same evidence, in a form nobody has to swallow.
    "body": {
        # 1 control (the sugar loop) · 2 control (the water loop) · 3 intact
        "case1": {
            "brief": "Passing water far more often than anyone should, "
                     "and thirsty enough to keep a jug by the bed.",
            "setup": {**HEALTHY_BODY,
                      "effectors": {"beta": False, "alpha": True,
                                    "liver": True, "adh": True,
                                    "kidney": True, "access": True}},
            "start_actions": [("eat", (100, 2.0))],
            "speed": 16,
            "warmup_s": 5400,
            "answer": {"role": "control", "part": "beta"},
            "note": "Diabetes MELLITUS. The urine is pouring out and it "
                    "is LOADED — up near the concentrating ceiling — "
                    "while ADH sits high and the kidneys do everything "
                    "they are told. Nothing in the water loop is broken. "
                    "The sugar is what is leaving, and the water is only "
                    "following it out. The glucose trace and the spill "
                    "say where the fault really is: two rooms away, in "
                    "beta cells that are making no insulin at all.",
        },
        "case2": {
            "brief": "Passing water far more often than anyone should, "
                     "and thirsty enough to keep a jug by the bed.",
            "setup": {**HEALTHY_BODY,
                      "effectors": {"beta": True, "alpha": True,
                                    "liver": True, "adh": False,
                                    "kidney": True, "access": True}},
            "speed": 16,
            "warmup_s": 5400,
            "answer": {"role": "control", "part": "pituitary"},
            "note": "Diabetes INSIPIDUS. The same flood, the opposite "
                    "urine: nearly pure water, dilute as it comes, "
                    "because no ADH is being released to tell the "
                    "kidneys to hold any of it back. Glucose is normal "
                    "and nothing is spilling. Insipidus = tasteless. "
                    "Same word 'diabetes' — a siphon — and two entirely "
                    "different broken loops, which is why physicians "
                    "once told them apart by taste and now tell them "
                    "apart by exactly the two traces you just read.",
        },
        "case3": {
            "brief": "Passing water far more often than anyone should, "
                     "and thirsty enough to keep a jug by the bed.",
            "setup": {**HEALTHY_BODY},
            "start_actions": [("drink", (2500,))],
            "speed": 16,
            "warmup_s": 3600,
            "answer": {"role": "none", "part": "none"},
            "note": "Nothing was broken. This person drank two and a "
                    "half liters, and a working water loop did exactly "
                    "what it should: ADH switched off, the kidneys "
                    "dumped the excess, and the urine ran DILUTE and "
                    "fast until the balance came back. Glucose normal, "
                    "nothing spilling, osmolarity already heading home "
                    "on its own. Passing a lot of urine is a symptom, "
                    "not a diagnosis — and a loop working hard is not a "
                    "loop that has failed.",
        },
    },
}


# What a diagnosis is worth. Naming the right part of the loop and the
# wrong component inside it is genuinely half the answer — the class that
# says "an effector has failed" has read the loop correctly and then
# misread one trace, and a gradebook should be able to see the difference.
DIAGNOSIS_POINTS = {"correct": 100, "partial": 50, "wrong": 0}


def _option_label(options, kind, key):
    """The human wording for an answer key, or the key if we weren't
    handed the vocabulary (the grader stays usable without it)."""
    for opt in (options or {}).get(kind, ()):
        if opt["key"] == key:
            return opt["label"]
    return key


def grade_answer(case, answer, options=None):
    """PURE: one submitted answer against one case's truth.

    Three outcomes, because two of them are not the same kind of wrong:
    right role AND right part is correct; the right part of the loop with
    the wrong component inside it is PARTIAL; the wrong role is wrong.

    Role "none" normalizes its own part, so a class that answers "nothing
    is broken" with a component still selected in the second box is not
    marked down for the state of a dropdown.
    """
    truth = case["answer"]
    role = answer.get("role")
    part = "none" if role == "none" else answer.get("part")
    role_ok, part_ok = role == truth["role"], part == truth["part"]
    correct = role_ok and part_ok
    verdict = "correct" if correct else "partial" if role_ok else "wrong"

    # The labels have em-dashes of their own ("Nothing is broken — the
    # loop is working"), so the quotes do the delimiting here.
    def said(kind, mine, theirs, ok):
        mine = _option_label(options, kind, mine)
        return (f'right: you said "{mine}"' if ok else
                f'you said "{mine}" — it was '
                f'"{_option_label(options, kind, theirs)}"')

    role_label = _option_label(options, "roles", truth["role"])
    part_label = _option_label(options, "parts", truth["part"])
    return {
        "verdict": verdict,
        "correct": correct,
        "points": DIAGNOSIS_POINTS[verdict],
        "answer": {"role": role, "part": part},
        # `line` is the one-sentence truth for the top of the reveal; an
        # intact case would otherwise read "Nothing is broken — the loop
        # is working, Nothing is broken".
        "truth": {"role": role_label, "part": part_label,
                  "line": role_label if truth["role"] == "none"
                          else f"{role_label} — {part_label}"},
        "note": case["note"],
        "rows": [
            {"key": "role", "label": "which part of the loop failed",
             "value": said("roles", role, truth["role"], role_ok),
             "met": role_ok, "n": None},
            {"key": "part", "label": "which component",
             "value": said("parts", part, truth["part"], part_ok),
             "met": part_ok, "n": None},
            {"key": "note", "label": "why", "value": case["note"],
             "met": None, "n": None},
        ],
    }


def build_case_attempt(loop, case_id, grade, label=None):
    """One answered case as a log record — the same frozen fields as a
    challenge attempt (kickoff SS5), plus the submitted answer and
    whether it was right, APPENDED the way every field has grown here.

    No medal: a diagnosis is right or it isn't, and medals are for play.
    """
    return {
        "id": None,
        "wall_time": datetime.datetime.now().isoformat(timespec="seconds"),
        "loop": loop,
        "mode": "diagnosis",
        "name": case_id,
        "label": label,
        "points": grade["points"],
        "medal": None,
        "met": grade["correct"],
        "rows": grade["rows"],       # the report card, verbatim
        "answer": grade["answer"],
        "correct": grade["correct"],
    }


def start_challenge(runner, loop, name, label=None):
    """Arm one challenge on one runner: the setup, the opening actions,
    the speed, and the stamped window.

    The ONE definition of what starting a challenge means — /control, the
    invariant tests and the M29 strategy sweep all take this path, so a
    sweep that says a strategy scores 88 is describing the same machinery
    the class will play.

    It starts a FRESH RUN (M30.1). A challenge used to inherit whatever
    body the sandbox had been left in, and the full pass found what that
    costs: the identical 40 % duty play on cold_store scored 88 and gold
    from a fresh app and 21 and no medal when the previous class had
    just finished demonstrating the freezer. Two teams' report cards are
    only comparable if the runs start the same way — "the engine's
    determinism is what makes the comparison fair: same inputs, same
    curves" (kickoff SS1) is a claim about the inputs, and the starting
    body is an input. A case has reset since M28 for the same reason.
    """
    entry = CHALLENGES[loop][name]
    runner.sim.reset()
    _apply_preset(runner.sim, entry["setup"])
    for method, args in entry.get("start_actions", []):
        getattr(runner.sim, method)(*args)
    runner.speed = entry["speed"]
    t0 = runner.sim.state()["t"]
    runner.challenge = {
        "loop": loop, "name": name,
        "t_start": t0, "t_end": t0 + entry["duration_s"],
        "report": None, "score": None, "attempt": None,
        # whose run this is (M27) — a TEAM name
        "label": clean_label(label),
        # The ambush schedule (M29), stamped into ABSOLUTE sim-time here
        # so the stepper never has to do arithmetic mid-run...
        "schedule": [{"at": ev["at"], "t": t0 + ev["at"], "line": ev["line"],
                      "do": ev["do"]} for ev in entry.get("events", ())],
        "next_event": 0,
        "feed": [],        # ...and what has actually landed, for the class
        "stopped": None,   # the hard-stop line, if one gets crossed
    }
    runner.attempt_error = None
    runner.preset = None   # the challenge card owns the story now
    runner.case = None     # ...and a challenge is a different lesson
    runner.running = True  # from a blind case


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
    if "adh_override" in p:
        sim.set_adh_override(p["adh_override"])


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
            runner.case = None       # reset ends the game and hands the
            runner.attempt_error = None   # sandbox back, un-redacted
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
            if CHALLENGES.get(loop, {}).get(name) is None:
                return jsonify({"error": f"unknown challenge {name!r} "
                                         f"for the {loop} loop"}), 400
            start_challenge(runner, loop, name, cmd.get("label"))
        elif action == "diagnose":
            # Start a blind case (M28). "next" (or nothing) walks the
            # rotation; a number picks one outright. The wire carries an
            # INDEX, never an id — there is nothing here for a student to
            # look up.
            loop = request.args.get("loop", "temp")
            entries = CASES.get(loop) or {}
            if not entries:
                return jsonify({"error": f"the {loop} loop has no "
                                         f"diagnosis cases"}), 400
            ids = list(entries)
            value = cmd.get("value")
            if value in (None, "", "next"):
                index = runner.case_index
            else:
                try:
                    index = int(value) - 1
                except (TypeError, ValueError):
                    return jsonify({"error": f"a case is picked by number, "
                                             f"got {value!r}"}), 400
            if not 0 <= index < len(ids):
                return jsonify({"error": f"there are {len(ids)} cases on "
                                         f"the {loop} loop, so there is no "
                                         f"case {index + 1}"}), 400
            runner.case_index = (index + 1) % len(ids)
            name = ids[index]
            entry = entries[name]
            # A case is a self-contained puzzle, so unlike a preset or a
            # challenge it DOES start a fresh run: the evidence on the
            # charts has to be this case's own. Then the opening stretch
            # is fast-forwarded, which is just sim.step() — deterministic,
            # every tick recorded, and the class joins a story already in
            # progress instead of watching an empty chart for ten minutes.
            runner.sim.reset()
            _apply_preset(runner.sim, entry["setup"])
            for method, args in entry.get("start_actions", []):
                getattr(runner.sim, method)(*args)
            if entry["warmup_s"]:
                runner.sim.step(int(entry["warmup_s"]))
            runner.speed = entry["speed"]
            runner.preset = None       # the banner would name the answer
            runner.challenge = None
            runner.attempt_error = None
            runner.case = {"loop": loop, "name": name, "grade": None,
                           "attempt": None,
                           "label": clean_label(cmd.get("label"))}
            runner.running = True
        elif action == "answer":
            # The class commits, the app grades, and everything it was
            # holding back is released (M28).
            if runner.case is None:
                return jsonify({"error": "no case is running — start one "
                                         "first"}), 400
            if runner.case["grade"] is not None:
                return jsonify({"error": "this case has already been "
                                         "answered — start the next "
                                         "one"}), 400
            loop = runner.case["loop"]
            options = ANSWER_OPTIONS[loop]
            submitted = {"role": cmd.get("role"), "part": cmd.get("part")}
            for kind, field in (("roles", "role"), ("parts", "part")):
                if submitted[field] not in {o["key"] for o in options[kind]}:
                    return jsonify({"error": f"{submitted[field]!r} is not "
                                             f"one of the {field} choices "
                                             f"for the {loop} loop"}), 400
            entry = CASES[loop][runner.case["name"]]
            runner.case["grade"] = grade_answer(entry, submitted, options)
            runner.case["attempt"], runner.attempt_error = log_attempt(
                build_case_attempt(loop, runner.case["name"],
                                   runner.case["grade"],
                                   label=runner.case.get("label")))
            # Deliberately NOT touching running/speed: answering is not a
            # physiological event, and the body carries on doing whatever
            # it was doing while the class reads the reveal.
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
                "insulin_sensitivity",
                # grown at M37 with the Phase 10 coupling readout, same rule
                "renal_loss"],
    "water": ["t", "osmolarity", "water_liters", "gut_water", "exercise",
              "error", "adh", "thirst", "urine_rate", "urine_osm",
              "adh_enabled", "kidney_enabled", "water_access",
              "sensor_enabled",
              # grown at M31 with the Phase 9 SIADH knob, same rule
              "adh_override",
              # grown at M37/M38 with the Phase 10 coupling terms
              "tubular_load", "foreign_osm"],
    # The coupled body (M39): both loops and the two links between them,
    # in the order the story is told — sugar, spill, link, water.
    "body": ["t", "glucose", "insulin", "glucagon", "renal_loss",
             "tubular_load", "glucose_osm", "osmolarity", "water_liters",
             "adh", "thirst", "urine_rate", "urine_osm",
             # grown at M41 with the breaker flags, appended as always
             "beta_enabled", "alpha_enabled", "liver_enabled",
             "adh_enabled", "kidney_enabled", "water_access",
             "sensor_enabled"],
}


@app.route("/compare")
def compare():
    """Two finished runs of one challenge, side by side (M27).

    Read-only and computed server-side, like the report card itself: the
    browser draws this, it never works it out.
    """
    loop = request.args.get("loop", "temp")
    name = request.args.get("name")
    if loop not in runners or name not in CHALLENGES.get(loop, {}):
        return jsonify({"error": f"unknown challenge {name!r} for the "
                                 f"{loop} loop"}), 400
    by_id = {a.get("id"): a for a in ATTEMPTS}
    picked = []
    for side in ("a", "b"):
        att = by_id.get(request.args.get(side, type=int))
        if att is None:
            return jsonify({"error": "pick two finished runs to "
                                     "compare"}), 400
        if att.get("loop") != loop or att.get("name") != name:
            return jsonify({"error": "those two runs aren't both from "
                                     "this challenge"}), 400
        picked.append(att)
    return jsonify(compare_attempts(*picked))


@app.route("/export.csv")
def export_csv():
    loop = request.args.get("loop", "temp")
    runner = _runner()   # session-aware (M33): your CSV is YOUR run
    if runner is None:
        return jsonify({"error": "unknown loop"}), 400
    if runner.blind():
        # A spreadsheet of `sensor_enabled` is the answer key in a column
        # (M28). 409, not 400: the request is fine, the moment isn't.
        return jsonify({"error": (
            f"a blind case is running on the {loop} loop, and this "
            "spreadsheet would have a column naming the broken part. "
            "Answer the case and the whole run downloads, complete — "
            "every tick of it, including the part that was hidden.")}), 409
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


def _serve_host():
    """Where to listen (M34). Localhost unless run.bat asks for the LAN —
    a developer's `python app.py`, verify.py, and every earlier phase
    stay loopback-only; opening the doors is a deliberate, visible act."""
    import os
    return os.environ.get("VITAL_LOOP_HOST", "127.0.0.1")


def _lan_addresses():
    """This machine's LAN IPv4 address(es), best effort. The UDP-connect
    trick sends no packets — it just asks the OS which interface would
    route out."""
    import socket
    found = []
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("10.255.255.255", 1))
            found.append(probe.getsockname()[0])
        finally:
            probe.close()
    except OSError:
        pass
    return [a for a in found if not a.startswith("127.")]


if __name__ == "__main__":
    # run.bat lands here. Port is this project's own — see CLAUDE.md.
    host = _serve_host()
    if host != "127.0.0.1":
        print()
        print("=" * 62)
        print("Vital Loop is open to the room (M34).")
        for addr in _lan_addresses() or ["<this machine's wifi IP>"]:
            print(f"  Write this on the board:  http://{addr}:5083/")
        print()
        print("Students: same wifi as this machine, then that address.")
        print("Every device gets its OWN body; scores land on the one")
        print("shared leaderboard.")
        print()
        print("If Windows asks about the firewall the FIRST time: allow")
        print("Python on PRIVATE networks. School wifi sometimes blocks")
        print("device-to-device traffic entirely — if phones can't reach")
        print("the address, that's the network, not the app.")
        print("=" * 62)
        print()
    app.run(host=host, port=5083)
