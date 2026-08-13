"""The blood glucose loop: antagonistic hormonal control (Phase 2, M6).

Same discipline as the thermoregulation engine (engine/sim.py): a budget.
Every tick, glucose entering the blood (gut absorption, liver output) and
glucose leaving it (tissue uptake, exercise, kidney spill above 180) are
summed; blood glucose moves by the net. The pancreatic islets are the
controller — but unlike the hypothalamus's one-sided pushes, this loop has
TWO opposing hands with overlapping active ranges:

  insulin  (beta cells)  rises above ~80 mg/dL, drives tissue uptake and
                         SUPPRESSES liver output;
  glucagon (alpha cells) rises below ~100 mg/dL, drives liver output.

Near the 90 set point BOTH are partly active — the set point is held by
their balance, not by silence. That is the Phase 2 teaching point.

One piece of real physiology is load-bearing here: insulin also restrains
the alpha cells directly (paracrine suppression). With beta cells disabled
that brake is gone, glucagon runs inappropriately high, and the liver keeps
feeding glucose into already-hyperglycemic blood — which is why type 1
hyperglycemia PERSISTS instead of drifting back down. It emerges from the
mechanism; nothing here special-cases "diabetes".

Phase 3 (M11) adds INJECTED insulin: a bolus goes into a subcutaneous
depot and is absorbed through a two-compartment first-order chain
(depot -> plasma -> cleared), so it acts on a delay — nothing for minutes,
peak effect nearly an hour out, spent by ~4 h. A basal drip feeds the same
depot continuously. The body cannot tell insulins apart: endogenous +
injected are summed into ONE total activity that drives tissue uptake,
suppresses the liver, and works the paracrine brake on the alpha cells —
which is why injections re-restrain a type 1 liver, honestly.

API and record fields are FROZEN by tests/test_invariants.py.
Deterministic: no clock reads, no randomness.
"""

from engine.sim import _clamp

# ---- Pool and flows (mg/dL per minute, ~70 kg adult, ~18 L glucose space) --
CARB_TO_MGDL = 5.56              # 1 g absorbed carbs -> mg/dL in the pool
BASAL_UPTAKE = 1.2               # brain + resting tissues at 90 mg/dL,
                                 # scales with G/90 (mass action)
INSULIN_DISPOSAL_MAX = 3.5       # muscle/fat uptake at full insulin
EXERCISE_UPTAKE = 2.5            # working muscles, insulin-independent
RENAL_COEF = 2.0                 # kidney spill: 2.0 * (G - 180)/100 above 180
RENAL_THRESHOLD = 180.0

LIVER_BASE = 0.5                 # hepatic output with no hormonal input
GLUCAGON_BOOST = 3.8             # + per unit glucagon
INSULIN_SUPPRESS = 3.0           # - per unit insulin
LIVER_MAX = 6.0

# ---- Islet controller tuning ----
INSULIN_START, INSULIN_FULL = 80.0, 140.0      # mg/dL
GLUCAGON_START, GLUCAGON_FULL = 100.0, 70.0    # mg/dL (downhill)
PARACRINE_GLUCAGON = 0.55        # alpha-cell tone when insulin's brake is
PARACRINE_INSULIN_SCALE = 0.1    # gone (fades in as insulin falls below this)

# ---- Injected insulin (Phase 3): subcutaneous rapid-acting analog ----
# Equal-rate two-compartment chain makes a unit bolus's plasma level an
# Erlang-2 curve peaking 1/K_INJ minutes after injection: ~55 min out, ~23%
# of peak in the first 5 min, ~15% left at 4 h — the shape the kinetics
# invariant pins. The delay is the teaching mechanic, not a detail.
K_INJ = 1.0 / 55.0               # per minute, depot->plasma and plasma->gone
ACTIVITY_PER_UNIT = 0.35         # plasma U-equivalents -> activity (0..1);
                                 # sized so ~4 U covers a 60 g meal (the
                                 # classic 1 U : 15 g) and 1.0 U/h basal
                                 # holds a fasted type 1 body near the band


class GlucoseSimulation:
    """One body, one glucose pool, fixed 1-second ticks."""

    SET_POINT = 90.0             # mg/dL
    DT = 1.0                     # seconds of sim time per tick

    def __init__(self):
        self.reset()

    def reset(self):
        """Fresh start: fasted, resting, everything working, no insulin
        on board and no basal running."""
        self._glucose = self.SET_POINT
        self._gut_carbs = 0.0
        self._absorb_rate = 1.0          # g/min; set by the last meal
        self._exercise = False
        self._enabled = {"beta": True, "alpha": True, "liver": True}
        self._sensor_enabled = True
        self._depot_units = 0.0          # U waiting under the skin
        self._plasma_units = 0.0         # U absorbed and circulating
        self._basal_rate = 0.0           # U/h continuous drip
        self._doses = []                 # bolus event log: {"t", "units"}
        self._t = 0.0
        self._history = []
        self._append_record(error=0.0, insulin=0.0, glucagon=0.0,
                            uptake=0.0, liver_flux=0.0,
                            injected=0.0, total=0.0)

    # ---------------- disturbances and break-the-loop toggles ---------------

    def eat(self, grams, rate_g_per_min):
        """Carbs into the gut; they absorb into the blood over sim-minutes.
        A fast rate is a sugary drink, a slow one a balanced meal."""
        grams, rate = float(grams), float(rate_g_per_min)
        if grams <= 0 or rate <= 0:
            raise ValueError("eat() needs positive grams and a positive "
                             "absorption rate (g/min)")
        self._gut_carbs += grams
        self._absorb_rate = rate         # the newest meal sets the pace

    def set_exercise(self, on):
        self._exercise = bool(on)

    def set_effector_enabled(self, name, on):
        if name not in self._enabled:
            raise KeyError(
                f"Unknown part {name!r}; expected one of "
                f"{sorted(self._enabled)}")
        self._enabled[name] = bool(on)

    def set_sensor_enabled(self, on):
        self._sensor_enabled = bool(on)

    def inject(self, units):
        """A subcutaneous bolus. It cannot be un-injected: absorption runs
        on its own clock no matter what glucose does next — that delay and
        commitment is the whole Phase 3 lesson."""
        units = float(units)
        if units <= 0:
            raise ValueError("inject() needs a positive number of units")
        self._depot_units += units
        self._doses.append({"t": self._t, "units": units})

    def set_basal_rate(self, u_per_hr):
        """Continuous drip into the same depot the boluses use (think
        insulin pump). 0 switches it off."""
        rate = float(u_per_hr)
        if rate < 0:
            raise ValueError("set_basal_rate() needs a rate >= 0 U/h")
        self._basal_rate = rate

    def doses(self):
        """The bolus event log, oldest first — a data product, like
        history(). Chart markers and any quiz layer read THIS, never
        wiggles in a curve."""
        return [dict(d) for d in self._doses]

    # ------------------------------- the loop -------------------------------

    def _islets(self, sensed_glucose, injected):
        """The controller: sensed mg/dL in, two opposing hormones out.
        `injected` joins endogenous insulin in ONE total activity — the
        alpha cells' paracrine brake can't tell the insulins apart."""
        insulin = _clamp(
            (sensed_glucose - INSULIN_START) / (INSULIN_FULL - INSULIN_START),
            0.0, 1.0)
        if not self._enabled["beta"]:
            insulin = 0.0
        total = _clamp(insulin + injected, 0.0, 1.0)
        drive = _clamp(
            (GLUCAGON_START - sensed_glucose) / (GLUCAGON_START - GLUCAGON_FULL),
            0.0, 1.0)
        # Paracrine disinhibition: ACTUAL insulin is the local brake on the
        # alpha cells; when it vanishes, glucagon tone appears regardless of
        # what the blood glucose says. This is what makes type 1 stick —
        # and why an injection visibly re-restrains the liver.
        disinhibition = PARACRINE_GLUCAGON * _clamp(
            1.0 - total / PARACRINE_INSULIN_SCALE, 0.0, 1.0)
        glucagon = _clamp(drive + disinhibition, 0.0, 1.0)
        if not self._enabled["alpha"]:
            glucagon = 0.0
        return insulin, glucagon, total

    def step(self, n=1):
        """Advance n ticks. Each tick: sense -> decide -> act -> record."""
        minutes = self.DT / 60.0
        for _ in range(int(n)):
            # Subcutaneous kinetics: the basal drip feeds the same depot the
            # boluses use, then first-order depot -> plasma -> cleared.
            self._depot_units += self._basal_rate / 60.0 * minutes
            transfer = K_INJ * self._depot_units * minutes
            self._depot_units -= transfer
            self._plasma_units += transfer - K_INJ * self._plasma_units * minutes
            injected = _clamp(ACTIVITY_PER_UNIT * self._plasma_units, 0.0, 1.0)

            sensed = (self._glucose if self._sensor_enabled
                      else self.SET_POINT)
            error = sensed - self.SET_POINT
            insulin, glucagon, total = self._islets(sensed, injected)

            # Into the blood: gut absorption + hepatic output.
            absorbed_g = min(self._absorb_rate * minutes, self._gut_carbs)
            self._gut_carbs -= absorbed_g
            gut_flux = absorbed_g * CARB_TO_MGDL / minutes   # mg/dL/min
            if self._enabled["liver"]:
                liver_flux = _clamp(
                    LIVER_BASE + GLUCAGON_BOOST * glucagon
                    - INSULIN_SUPPRESS * total, 0.0, LIVER_MAX)
            else:
                liver_flux = 0.0

            # Out of the blood: tissues, exercise, kidneys.
            uptake = BASAL_UPTAKE * self._glucose / self.SET_POINT
            uptake += INSULIN_DISPOSAL_MAX * total
            if self._exercise:
                uptake += EXERCISE_UPTAKE
            if self._glucose > RENAL_THRESHOLD:
                uptake += RENAL_COEF * (self._glucose - RENAL_THRESHOLD) / 100.0

            net = (gut_flux + liver_flux - uptake) * minutes
            self._glucose = max(0.0, self._glucose + net)
            self._t += self.DT
            self._append_record(error=error, insulin=insulin,
                                glucagon=glucagon, uptake=uptake,
                                liver_flux=liver_flux,
                                injected=injected, total=total)

    # ---------------- the data product (Phase 2 kickoff SS5) ----------------

    def _append_record(self, error, insulin, glucagon, uptake, liver_flux,
                       injected, total):
        self._history.append({
            "t": self._t,
            "glucose": self._glucose,
            "gut_carbs": self._gut_carbs,
            "exercise": self._exercise,
            "error": error,
            "insulin": insulin,
            "glucagon": glucagon,
            "uptake": uptake,
            "liver_flux": liver_flux,
            "beta_enabled": self._enabled["beta"],
            "alpha_enabled": self._enabled["alpha"],
            "liver_enabled": self._enabled["liver"],
            "sensor_enabled": self._sensor_enabled,
            "injected_insulin": injected,
            "total_insulin": total,
            "iob_units": self._depot_units + self._plasma_units,
            "basal_rate": self._basal_rate,
        })

    def history(self):
        """Every record since reset, oldest first — THE source of truth."""
        return [dict(r) for r in self._history]

    def state(self):
        """The newest record."""
        return dict(self._history[-1])
