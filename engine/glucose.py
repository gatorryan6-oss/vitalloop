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


class GlucoseSimulation:
    """One body, one glucose pool, fixed 1-second ticks."""

    SET_POINT = 90.0             # mg/dL
    DT = 1.0                     # seconds of sim time per tick

    def __init__(self):
        self.reset()

    def reset(self):
        """Fresh start: fasted, resting, everything working."""
        self._glucose = self.SET_POINT
        self._gut_carbs = 0.0
        self._absorb_rate = 1.0          # g/min; set by the last meal
        self._exercise = False
        self._enabled = {"beta": True, "alpha": True, "liver": True}
        self._sensor_enabled = True
        self._t = 0.0
        self._history = []
        self._append_record(error=0.0, insulin=0.0, glucagon=0.0,
                            uptake=0.0, liver_flux=0.0)

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

    # ------------------------------- the loop -------------------------------

    def _islets(self, sensed_glucose):
        """The controller: sensed mg/dL in, two opposing hormones out."""
        insulin = _clamp(
            (sensed_glucose - INSULIN_START) / (INSULIN_FULL - INSULIN_START),
            0.0, 1.0)
        if not self._enabled["beta"]:
            insulin = 0.0
        drive = _clamp(
            (GLUCAGON_START - sensed_glucose) / (GLUCAGON_START - GLUCAGON_FULL),
            0.0, 1.0)
        # Paracrine disinhibition: ACTUAL insulin is the local brake on the
        # alpha cells; when it vanishes, glucagon tone appears regardless of
        # what the blood glucose says. This is what makes type 1 stick.
        disinhibition = PARACRINE_GLUCAGON * _clamp(
            1.0 - insulin / PARACRINE_INSULIN_SCALE, 0.0, 1.0)
        glucagon = _clamp(drive + disinhibition, 0.0, 1.0)
        if not self._enabled["alpha"]:
            glucagon = 0.0
        return insulin, glucagon

    def step(self, n=1):
        """Advance n ticks. Each tick: sense -> decide -> act -> record."""
        minutes = self.DT / 60.0
        for _ in range(int(n)):
            sensed = (self._glucose if self._sensor_enabled
                      else self.SET_POINT)
            error = sensed - self.SET_POINT
            insulin, glucagon = self._islets(sensed)

            # Into the blood: gut absorption + hepatic output.
            absorbed_g = min(self._absorb_rate * minutes, self._gut_carbs)
            self._gut_carbs -= absorbed_g
            gut_flux = absorbed_g * CARB_TO_MGDL / minutes   # mg/dL/min
            if self._enabled["liver"]:
                liver_flux = _clamp(
                    LIVER_BASE + GLUCAGON_BOOST * glucagon
                    - INSULIN_SUPPRESS * insulin, 0.0, LIVER_MAX)
            else:
                liver_flux = 0.0

            # Out of the blood: tissues, exercise, kidneys.
            uptake = BASAL_UPTAKE * self._glucose / self.SET_POINT
            uptake += INSULIN_DISPOSAL_MAX * insulin
            if self._exercise:
                uptake += EXERCISE_UPTAKE
            if self._glucose > RENAL_THRESHOLD:
                uptake += RENAL_COEF * (self._glucose - RENAL_THRESHOLD) / 100.0

            net = (gut_flux + liver_flux - uptake) * minutes
            self._glucose = max(0.0, self._glucose + net)
            self._t += self.DT
            self._append_record(error=error, insulin=insulin,
                                glucagon=glucagon, uptake=uptake,
                                liver_flux=liver_flux)

    # ---------------- the data product (Phase 2 kickoff SS5) ----------------

    def _append_record(self, error, insulin, glucagon, uptake, liver_flux):
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
        })

    def history(self):
        """Every record since reset, oldest first — THE source of truth."""
        return [dict(r) for r in self._history]

    def state(self):
        """The newest record."""
        return dict(self._history[-1])
