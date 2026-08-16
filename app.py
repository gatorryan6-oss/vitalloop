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
import io
import threading
import time

from flask import Flask, Response, jsonify, render_template, request

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

    def __init__(self, sim):
        self.lock = threading.Lock()
        self.sim = sim
        self.running = True
        self.speed = 1
        self.preset = None       # active disease name (app-level; M18) —
                                 # the engine only ever sees mechanisms
        self.challenge = None    # active challenge stamp (M24):
                                 # {loop, name, t_start, t_end, report}
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
        if self.challenge is not None:
            c = self.challenge
            entry = CHALLENGES[c["loop"]][c["name"]]
            done = state["t"] >= c["t_end"]
            if done and c["report"] is None:
                # Evaluate ONCE, from the engine's records over exactly
                # the stamped window — the report is a data product.
                window = [r for r in records
                          if c["t_start"] < r["t"] <= c["t_end"]]
                c["report"] = EVALUATORS[entry["metrics"]](window)
            out["challenge"] = {
                "name": c["name"],
                "title": entry["title"],
                "goal": entry["goal"],
                "t_start": c["t_start"],
                "t_end": c["t_end"],
                "done": done,
                "report": c["report"],
            }
        return out


runners = {
    "temp": Runner(Simulation()),
    "glucose": Runner(GlucoseSimulation()),
    "water": Runner(WaterSimulation()),
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
        {"label": "time in 70-180 mg/dL",
         "value": f"{pct:.0f}% (target: at least 75%)", "met": pct >= 75.0},
        {"label": "lowest glucose",
         "value": f"{lo:.0f} mg/dL (target: never below 65)",
         "met": lo >= 65.0},
        {"label": "highest glucose", "value": f"{hi:.0f} mg/dL",
         "met": None},
        {"label": "beta cells stayed off",
         "value": "yes" if beta_stayed_off
                  else "no — the pancreas came back on mid-shift",
         "met": beta_stayed_off},
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
        {"label": "core at the hour's end",
         "value": f"{end:.2f} °C (target: at least 36.0)",
         "met": end >= 36.0},
        {"label": "lowest core",
         "value": f"{lo:.2f} °C (target: never below 35.0)",
         "met": lo >= 35.0},
        {"label": "exercise used",
         "value": f"{duty:.0f}% of the hour (exhaustion cap: 50%)",
         "met": duty <= 50.0},
        {"label": "the door stayed shut (room at -5 °C or colder)",
         "value": "yes" if door_shut else "no — the room was warmed",
         "met": door_shut},
        {"label": "shivering and vessel control stayed failed",
         "value": "yes" if stayed_failed else "no — a broken part came "
                  "back mid-rescue", "met": stayed_failed},
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
        {"label": "time inside 280-300 mOsm/L",
         "value": f"{pct:.0f}% (target: at least 90%)", "met": pct >= 90.0},
        {"label": "lowest osmolarity",
         "value": f"{lo:.1f} mOsm/L (target: never below 275 - "
                  "overhydration kills at aid stations)", "met": lo >= 275.0},
        {"label": "highest osmolarity",
         "value": f"{hi:.1f} mOsm/L (target: never above 305)",
         "met": hi <= 305.0},
        {"label": "urine passed", "value": f"{urine_l:.1f} L", "met": None},
        {"label": "the runner kept moving",
         "value": "yes" if kept_moving else "no — exercise was switched "
                  "off", "met": kept_moving},
        {"label": "the osmoreceptors stayed dead",
         "value": "yes" if sensor_dead else "no — the sensor came back",
         "met": sensor_dead},
    ]
    return {"met": all(r["met"] for r in rows if r["met"] is not None),
            "rows": rows}


EVALUATORS = {
    "t1_shift": _eval_t1_shift,
    "cold_store": _eval_cold_store,
    "aid_station": _eval_aid_station,
}

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
                                "report": None}
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
