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
}

PHASE3_FIELDS_ADDED = {"injected_insulin", "total_insulin", "iob_units",
                       "basal_rate"}
PHASE4_FIELDS_ADDED = {"pump_enabled", "pump_rate"}
PHASE5_FIELDS_ADDED = {"insulin_sensitivity"}

# The record shapes as frozen at each phase's end — the stacked regression
# guards (n) and (s) hash exactly these subsets of their scripted runs.
PHASE2_GLUCOSE_FIELDS = sorted(GLUCOSE_FIELDS - PHASE3_FIELDS_ADDED
                               - PHASE4_FIELDS_ADDED - PHASE5_FIELDS_ADDED)
PHASE23_GLUCOSE_FIELDS = sorted(GLUCOSE_FIELDS - PHASE4_FIELDS_ADDED
                                - PHASE5_FIELDS_ADDED)

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
}


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
# APPENDING (M28's diagnosis answer), never by renaming — a worksheets
# phase or a gradebook export reads this file, not a screenshot.
ATTEMPT_FIELDS = {"id", "wall_time", "loop", "mode", "name", "label",
                  "points", "medal", "met", "rows"}

# One crafted record per evaluator, enough for it to produce every row.
CRAFTED_RECORD = {
    "t1_shift": {"t": 0.0, "glucose": 100.0, "beta_enabled": False},
    "cold_store": {"core_temp": 36.5, "exercise": False, "env_temp": -10.0,
                   "shiver_enabled": False, "vaso_enabled": False},
    "aid_station": {"osmolarity": 290.0, "exercise": True,
                    "sensor_enabled": False, "urine_rate": 3.0},
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
