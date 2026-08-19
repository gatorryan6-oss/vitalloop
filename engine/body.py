"""One person: the glucose loop and the water loop, stepped together
(Phase 10, M37).

Nine phases taught three loops one at a time. This is where two of them
meet. The link is a single number, and neither engine had to be taught
about the other to make it work:

  * the glucose loop has spilled sugar into the urine above 180 mg/dL
    since Phase 2 (RENAL_THRESHOLD) — it just never said so out loud;
  * the water loop can now be handed osmoles that arrive in the tubule
    from somewhere else (set_tubular_load) and must be carried out with
    water, because no kidney concentrates past ~1200 mOsm/L.

Wire the first to the second and untreated diabetes stops being two
diseases that happen to share a name. The sugar is IN the urine, the
sugar is what is pulling the water out, and the patient drinks and
drinks and cannot keep up. That is the classic triad — polyuria,
polydipsia, thirst that never quits — falling out of two models that
were each built to teach something else.

It is also where the class finally earns the words from M23: insipidus
is TASTELESS urine (water, no sugar, the ADH signal is broken) and
mellitus is HONEY-SWEET urine (sugar, dragging water, while ADH works
perfectly). Same flood, opposite mechanism. The urine concentration
trace is what tells them apart, and here it is a number you can watch.

Neither engine imports the other — this class owns both and passes one
number between them, so each loop stays independently testable and the
three single-loop lessons are untouched.

Deterministic and fixed-timestep like everything else: no clock reads,
no randomness. API and record fields are FROZEN by
tests/test_invariants.py.
"""

from engine.glucose import CARB_TO_MGDL, GlucoseSimulation
from engine.water import WaterSimulation

# ---- The conversion, derived rather than guessed ----
# CARB_TO_MGDL says 1 g (1000 mg) of absorbed carbohydrate raises the pool
# by 5.56 mg/dL, so the pool IS 1000 / 5.56 = ~180 dL of blood-and-tissue
# water. A spill of 1 mg/dL/min therefore leaves the body at
# 1 x 180 dL = ~180 mg/min, and glucose is ~180 mg per mmol and does not
# dissociate, so that is ~1 mOsm/min.
#
# The two 180s are a coincidence of THIS model's pool size, not a law of
# nature, so the factor is computed from the constant instead of typed as
# 1.0 — change the pool and the coupling follows honestly.
GLUCOSE_MW = 180.16                        # mg per mmol
GLUCOSE_SPACE_DL = 1000.0 / CARB_TO_MGDL   # ~180 dL
MGDL_MIN_TO_MOSM_MIN = GLUCOSE_SPACE_DL / GLUCOSE_MW    # ~0.998

# ---- The second link (M38): sugar is an osmole while it is still IN there --
# Plasma osmolarity is 2 x sodium PLUS glucose PLUS urea. 1 mg/dL is
# 10 mg/L, and glucose is ~180 mg/mmol, so 1 mg/dL of glucose is
# 10/180 = ~0.056 mOsm/L — the familiar "glucose over 18" from the
# clinical formula, derived here rather than typed.
MGDL_TO_MOSM_L = 10.0 / GLUCOSE_MW                      # ~1/18

# Which loop owns which breaker, for set_effector_enabled dispatch.
# ---- The third link (M53): the water the sugar is dissolved in ----------
# Dehydration concentrates a fixed sugar mass, which spills more, which
# takes more water - the last leg of the M38 spiral, measured there at
# +3 to +9 mg/dL and deferred until Phase 13 was chartered to close it.
# The glucose pool (~18 L) and total body water (~40 L) are different
# compartments; treating them as shrinking together is this model's
# simplification, stated here rather than hidden.
BASELINE_WATER_L = 40.0                    # WaterSimulation's own start

_GLUCOSE_PARTS = ("beta", "alpha", "liver")
_WATER_PARTS = ("adh", "kidney", "access")


class Body:
    """Two loops, one person, one clock."""

    DT = 1.0                     # seconds of sim time per tick

    def __init__(self):
        self.glucose = GlucoseSimulation()
        self.water = WaterSimulation()
        self.reset()

    def reset(self):
        """Fresh start for both loops, uncoupled until the first tick."""
        self.glucose.reset()
        self.water.reset()
        self.water.set_tubular_load(0.0)
        self._t = 0.0
        self._history = []
        self._append_record()

    # ------------------------- disturbances -------------------------
    # Delegation, so a caller drives ONE person instead of juggling two
    # objects. Only what a body can actually be asked to do.

    def eat(self, grams, rate_g_per_min):
        self.glucose.eat(grams, rate_g_per_min)

    def inject(self, units):
        self.glucose.inject(units)

    def set_basal_rate(self, u_per_hr):
        self.glucose.set_basal_rate(u_per_hr)

    def set_pump_enabled(self, on):
        self.glucose.set_pump_enabled(on)

    def set_autonomous_insulin(self, level):
        """An insulinoma in a coupled body (M57) - forwarded, like every
        other glucose knob, so the sugar loop's diseases all exist here
        too."""
        self.glucose.set_autonomous_insulin(level)

    def set_insulin_gain(self, gain):
        self.glucose.set_insulin_gain(gain)

    def set_insulin_lag(self, seconds):
        self.glucose.set_insulin_lag(seconds)

    def set_insulin_sensitivity(self, s):
        self.glucose.set_insulin_sensitivity(s)

    def drink(self, ml):
        self.water.drink(ml)

    def eat_salt(self, mosm):
        self.water.eat_salt(mosm)

    def set_adh_override(self, level):
        self.water.set_adh_override(level)

    def set_exercise(self, on):
        """One person: exercising burns sugar AND sweats."""
        self.glucose.set_exercise(on)
        self.water.set_exercise(on)

    def set_effector_enabled(self, name, on):
        """Break a part of either loop, by its own name."""
        if name in _GLUCOSE_PARTS:
            self.glucose.set_effector_enabled(name, on)
        elif name in _WATER_PARTS:
            self.water.set_effector_enabled(name, on)
        else:
            raise KeyError(
                f"Unknown part {name!r}; expected one of "
                f"{sorted(_GLUCOSE_PARTS + _WATER_PARTS)}")

    def set_sensor_enabled(self, on):
        """Both sensor sets at once — one body, blinded."""
        self.glucose.set_sensor_enabled(on)
        self.water.set_sensor_enabled(on)

    def doses(self):
        return self.glucose.doses()

    def drinks(self):
        return self.water.drinks()

    # ---------------------------- the loop ----------------------------

    def step(self, n=1):
        """Advance n ticks, glucose first so the water loop sees THIS
        tick's spill rather than last tick's."""
        for _ in range(int(n)):
            # Link 3 (M53): the sugar is dissolved in whatever water is
            # LEFT. Set before the sugar loop steps, from last tick's
            # water level - a one-tick lag, which keeps the two loops in
            # a line instead of in a circle.
            self.glucose.set_pool_scale(
                self.water.state()["water_liters"] / BASELINE_WATER_L)

            self.glucose.step(1)
            g = self.glucose.state()

            # Link 1 (M37): sugar the kidney could not hold onto arrives
            # in the tubule and drags water out with it.
            spill = g["renal_loss"]                         # mg/dL/min
            self.water.set_tubular_load(spill * MGDL_MIN_TO_MOSM_MIN)

            # Link 2 (M38): sugar still IN the blood is an osmole the
            # osmoreceptors can feel. Only the EXCESS above the normal
            # fasting level, because the water loop's 290 baseline
            # already has an ordinary amount of sugar dissolved in it.
            # Clamped at zero: a hypo body is not meaningfully
            # hypo-osmolar, and a negative contribution would be a
            # stranger claim than this model wants to make.
            excess = max(0.0, g["glucose"] - self.glucose.SET_POINT)
            self.water.set_foreign_osmoles(excess * MGDL_TO_MOSM_L)

            self.water.step(1)
            self._t += self.DT
            self._append_record()

    # ------------------- the data product (kickoff SS5) -------------------

    def _append_record(self):
        g = self.glucose.state()
        w = self.water.state()
        self._history.append({
            "t": self._t,
            # the sugar loop
            "glucose": g["glucose"],
            "insulin": g["insulin"],
            "glucagon": g["glucagon"],
            "renal_loss": g["renal_loss"],
            # the two links
            "tubular_load": w["tubular_load"],
            "glucose_osm": w["foreign_osm"],
            # appended at M53: the water the sugar is dissolved in,
            # relative to normal. Below 1.0 the reading is concentrated.
            "pool_scale": w["water_liters"] / BASELINE_WATER_L,
            # the water loop
            "osmolarity": w["osmolarity"],
            "water_liters": w["water_liters"],
            "adh": w["adh"],
            "thirst": w["thirst"],
            "urine_rate": w["urine_rate"],
            "urine_osm": w["urine_osm"],
            # The breaker flags of BOTH loops (M41), so a challenge can
            # tell whether the class quietly un-broke something and a
            # blind case has something to withhold. Redacted during a
            # case by the same allowlist as everywhere else.
            "beta_enabled": g["beta_enabled"],
            "alpha_enabled": g["alpha_enabled"],
            "liver_enabled": g["liver_enabled"],
            "adh_enabled": w["adh_enabled"],
            "kidney_enabled": w["kidney_enabled"],
            "water_access": w["water_access"],
            # set_sensor_enabled() drives both loops together, so one
            # field says it for the body.
            "sensor_enabled": g["sensor_enabled"],
        })

    def history(self):
        """Every coupled record since reset, oldest first. The two sub
        loops keep their own full histories too — this is the join."""
        return [dict(r) for r in self._history]

    def state(self):
        """The newest record."""
        return dict(self._history[-1])
