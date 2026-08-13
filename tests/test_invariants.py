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
    # -- grown at M11 (Phase 3 kickoff SS5), a deliberate contract amendment:
    "injected_insulin", # exogenous plasma activity, 0..1 (same scale as
                        # insulin; `insulin` stays beta-cell output ALONE)
    "total_insulin",    # clamp(insulin + injected_insulin) — what the body
                        # actually responds to; recorded, never JS-derived
    "iob_units",        # "insulin on board": U still working (depot+plasma)
    "basal_rate",       # continuous drip setting, U/h
}

# The Phase 2 record shape as it was frozen at M6 — the regression guard (n)
# hashes exactly this subset of the scripted run.
PHASE2_GLUCOSE_FIELDS = sorted(GLUCOSE_FIELDS - {
    "injected_insulin", "total_insulin", "iob_units", "basal_rate"})

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
