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
            # Dose events are a data product (Phase 3 kickoff SS5): the
            # chart markers read the engine's log, never infer from curves.
            doses = self.sim.doses() if hasattr(self.sim, "doses") else None
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
        return out


runners = {
    "temp": Runner(Simulation()),
    "glucose": Runner(GlucoseSimulation()),
}


def _runner():
    """The Runner the request addresses (?loop=temp|glucose, default temp),
    or None for an unknown loop name."""
    return runners.get(request.args.get("loop", "temp"))


@app.route("/")
def index():
    return render_template("index.html")


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
        elif action == "scenario":
            name = cmd.get("value")
            if hasattr(runner.sim, "set_env_temp"):
                if name not in SCENARIOS:
                    return jsonify({"error": f"unknown scenario {name!r}"}), 400
                env_temp, exercise = SCENARIOS[name]
                runner.sim.set_env_temp(env_temp)
                runner.sim.set_exercise(exercise)
            elif name == "fast":
                # A fast is the absence of eating: nothing to inject, just
                # stop exercising and make hours pass quickly on screen.
                # (Anything still in the gut keeps absorbing - you can't
                # un-eat.)
                runner.sim.set_exercise(False)
                runner.speed = 16
            elif name == "t1_morning":
                # Type 1 morning (M13): the beta cells are gone and the
                # day starts moving. Basal, breakfast, and boluses are the
                # class's decisions from here — this button only sets the
                # stage, it never resets the run.
                runner.sim.set_effector_enabled("beta", False)
                runner.sim.set_exercise(False)
                runner.speed = 16
            elif name == "pump_day":
                # Artificial pancreas day (M16): same broken pancreas,
                # but the machine loop takes the shift. Never resets.
                runner.sim.set_effector_enabled("beta", False)
                runner.sim.set_exercise(False)
                runner.sim.set_pump_enabled(True)
                runner.speed = 16
            else:
                return jsonify({"error": f"unknown scenario {name!r}"}), 400
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
