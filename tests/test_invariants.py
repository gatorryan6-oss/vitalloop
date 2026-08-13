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
}
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
}

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


def test_thermo_history_unchanged_by_phase2():
    import hashlib
    import json
    from engine.sim import Simulation
    digest = hashlib.sha256(
        json.dumps(_scripted_run(Simulation), sort_keys=True).encode()
    ).hexdigest()
    assert digest == THERMO_HISTORY_SHA256, (
        "The thermoregulation engine's scripted-run history changed. "
        "Phase 2 must EXTEND Phase 1, never rebuild it (standing rule 3). "
        "If this change was ordered by the human, re-record the hash and "
        "say so in BUILDLOG.md.")


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
