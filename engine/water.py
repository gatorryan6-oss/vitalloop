"""The water/ADH loop: osmoregulation (Phase 6, M20).

Same discipline as the other two engines: a budget — two pools this time.
Body water (liters) and total solutes (mOsm) move by their flows every
tick; the controlled variable is their RATIO, plasma osmolarity (mOsm/L,
set point 290). Osmoreceptors in the hypothalamus read it; the posterior
pituitary answers with ADH; the effectors are:

  kidneys (ADH)     can only SLOW water loss — collecting ducts reabsorb
                    water, urine turns concentrated and scant. No organ
                    can create water.
  thirst -> drink   the loop's other arm is a BEHAVIOR: when thirst
                    crosses its threshold (and water is within reach),
                    the body drinks. This is the only way water is ever
                    ADDED — the loop closes through the outside world.

The thresholds are staged like Phase 1's cheap-first ordering: ADH starts
rising at ~285 mOsm/L, thirst only wakes above ~293 — conserve first,
drink second. Urine tells the story: solute excretion is steady (the
kidneys must dump ~650 mOsm of metabolic waste a day regardless), so the
LESS water ADH lets go, the more concentrated the stream: ~900 mOsm/L
fully conserving, ~40 flooding. Break ADH and 17 L/day of tasteless
urine follows — diabetes insipidus — but the loop SURVIVES if drinking
can compensate: break water access too and dehydration wins in hours.

API and record fields are FROZEN by tests/test_invariants.py.
Deterministic: no clock reads, no randomness.
"""

from engine.sim import _clamp

# ---- Pools (a ~70 kg adult) ----
BODY_WATER_L = 40.0              # total body water at the set point
SOLUTES_MOSM = 11600.0           # 290 mOsm/L x 40 L

# ---- Water flows (mL/min) ----
INSENSIBLE_ML_MIN = 0.5          # skin + breath, always
URINE_MIN_ML_MIN = 0.5           # fully concentrated (obligate waste)
URINE_MAX_ML_MIN = 12.0          # no ADH heard: ~17 L/day, real DI range
SWEAT_ML_MIN = 12.0              # while exercising / in the heat
GUT_ABSORB_ML_MIN = 40.0         # drunk water entering the blood

# ---- Solute flows (mOsm/min) ----
MAX_URINE_OSM = 1200.0           # mOsm/L — the concentrating CEILING. The
                                 # kidney can pack this much solute into a
                                 # liter and no more, so solute that must
                                 # leave drags at least this much water with
                                 # it. Idle until something couples in (M37).
WASTE_PRODUCTION = 0.45          # urea etc. made by metabolism, ~650/day
EXCRETION_GAIN = 0.005           # extra clearance per mOsm above normal
EXCRETION_FLOOR, EXCRETION_CAP = 0.05, 3.0
SWEAT_OSM = 50.0                 # sweat is hypotonic: water leaves
                                 # faster than solute, osmolarity RISES

# ---- Controller tuning (mOsm/L) ----
ADH_START, ADH_FULL = 285.0, 295.0
THIRST_START, THIRST_FULL = 293.0, 301.0

# ---- The behavioral effector ----
AUTO_DRINK_THIRST = 0.15         # drink once thirst is genuinely awake
AUTO_DRINK_ML = 250.0            # one glass, every time (deterministic)
GUT_REFRACTORY_ML = 100.0        # don't top up an already-working gut


class WaterSimulation:
    """One body, two pools, fixed 1-second ticks."""

    SET_POINT = 290.0            # mOsm/L
    DT = 1.0                     # seconds of sim time per tick

    def __init__(self):
        self.reset()

    def reset(self):
        """Fresh start: balanced, resting, water within reach."""
        self._water = BODY_WATER_L
        self._solutes = SOLUTES_MOSM
        self._gut_water = 0.0            # mL drunk, not yet absorbed
        self._exercise = False
        self._enabled = {"adh": True, "kidney": True, "access": True}
        self._sensor_enabled = True
        self._adh_override = None        # SIADH knob (M31), None = healthy
        self._tubular_load = 0.0         # mOsm/min arriving from ANOTHER
                                         # loop (M37); 0.0 = uncoupled
        self._foreign_osm = 0.0          # mOsm/L of PLASMA osmoles owned by
                                         # another loop (M38); 0.0 = uncoupled
        self._drinks = []                # {"t", "ml", "auto"}
        self._t = 0.0
        self._history = []
        self._append_record(error=0.0, adh=0.0, thirst=0.0,
                            urine_rate=0.0, urine_osm=0.0)

    # ---------------- disturbances and break-the-loop toggles ---------------

    def drink(self, ml):
        """Water into the gut by hand — a glass, a liter, way too much.
        It absorbs into the blood over minutes, like eat()."""
        ml = float(ml)
        if ml <= 0:
            raise ValueError("drink() needs a positive number of mL")
        self._gut_water += ml
        self._drinks.append({"t": self._t, "ml": ml, "auto": False})

    def eat_salt(self, mosm):
        """A salty snack: solutes straight into the pool. (Salt absorbs
        fast; no gut pool for it — logged simplification, M20.)"""
        mosm = float(mosm)
        if mosm <= 0:
            raise ValueError("eat_salt() needs a positive mOsm load")
        self._solutes += mosm

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

    def set_adh_override(self, level):
        """SIADH (M31): ADH held at `level` no matter what the
        osmoreceptors say — secretion inappropriate to the stimulus,
        which IS the disease. None restores normal control. The source
        is ectopic (a tumor, a drug effect), so it bypasses the
        pituitary toggle too."""
        if level is None:
            self._adh_override = None
            return
        level = float(level)
        if level <= 0.0:
            raise ValueError(
                "an override of 0 isn't SIADH — no hormone at all is "
                "central DI; use the ADH toggle for that")
        if level > 1.0:
            raise ValueError("adh override is a 0-1 activity level")
        self._adh_override = level

    def set_tubular_load(self, mosm_per_min):
        """Osmoles arriving in the tubule from OUTSIDE this loop (M37).

        Phase 10's coupling term: filtered glucose the kidney could not
        reabsorb. They have to be excreted, and because no kidney can
        concentrate past MAX_URINE_OSM, water leaves with them —
        osmotic diuresis. The load is NOT added to the plasma solute
        pool: that sugar was already subtracted from the blood by the
        glucose loop's own budget, and counting it twice would invent
        solute out of nothing.

        0.0 (the default) means uncoupled, and the loop behaves exactly
        as it has since M20.
        """
        mosm_per_min = float(mosm_per_min)
        if mosm_per_min < 0.0:
            raise ValueError(
                "a tubular load is what arrives in the urine, so it "
                "cannot be negative")
        self._tubular_load = mosm_per_min

    def set_foreign_osmoles(self, mosm_per_l):
        """Plasma osmoles this loop does not own (M38).

        Phase 10's second coupling term. Plasma osmolarity is not just
        salt: it is 2 x sodium PLUS glucose PLUS urea, and in
        hyperglycemia the sugar term is large — that is the
        "hyperosmolar" in hyperosmolar hyperglycemic state. Glucose
        without insulin stays outside the cells, so it is an EFFECTIVE
        osmole: the osmoreceptors feel it, and thirst answers it. This
        is why an untreated diabetic is desperately thirsty even before
        losing much water.

        Added to the osmolarity this loop reports AND to what its
        receptors sense, because they are the same number. 0.0 (the
        default) means uncoupled.
        """
        mosm_per_l = float(mosm_per_l)
        if mosm_per_l < 0.0:
            raise ValueError(
                "foreign osmoles are a contribution to plasma "
                "osmolarity, so they cannot be negative")
        self._foreign_osm = mosm_per_l

    def drinks(self):
        """The intake event log, oldest first — a data product, like
        doses(). Auto-drinks are marked: the class can SEE the loop
        drinking by itself."""
        return [dict(d) for d in self._drinks]

    # ------------------------------- the loop -------------------------------

    def step(self, n=1):
        """Advance n ticks. Each tick: sense -> decide -> act -> record."""
        minutes = self.DT / 60.0
        for _ in range(int(n)):
            # Total plasma osmolarity: this loop's own solutes plus
            # any owned by another loop (M38). Zero when uncoupled.
            osm = self._solutes / self._water + self._foreign_osm
            sensed = osm if self._sensor_enabled else self.SET_POINT
            error = sensed - self.SET_POINT

            # The controller: staged thresholds, hormone before behavior.
            adh = _clamp((sensed - ADH_START) / (ADH_FULL - ADH_START),
                         0.0, 1.0)
            if not self._enabled["adh"]:
                adh = 0.0                # central DI: no hormone released
            if self._adh_override is not None:
                adh = self._adh_override   # SIADH: the level ignores both
                                           # the receptors and the pituitary
            thirst = _clamp(
                (sensed - THIRST_START) / (THIRST_FULL - THIRST_START),
                0.0, 1.0)

            # The behavioral effector: drink when genuinely thirsty, the
            # gut isn't already working, and there IS water to reach for.
            if (self._enabled["access"] and thirst >= AUTO_DRINK_THIRST
                    and self._gut_water < GUT_REFRACTORY_ML):
                self._gut_water += AUTO_DRINK_ML
                self._drinks.append({"t": self._t, "ml": AUTO_DRINK_ML,
                                     "auto": True})

            # The kidneys: a deaf kidney (nephrogenic DI) hears adh = 0.
            heard = adh if self._enabled["kidney"] else 0.0
            urine_rate = (URINE_MIN_ML_MIN
                          + (URINE_MAX_ML_MIN - URINE_MIN_ML_MIN)
                          * (1.0 - heard) ** 2)
            excretion = _clamp(
                WASTE_PRODUCTION
                + EXCRETION_GAIN * (self._solutes - SOLUTES_MOSM),
                EXCRETION_FLOOR, EXCRETION_CAP)
            # Solute arriving from ANOTHER loop (M37) drags its OWN water
            # out on top of whatever ADH was already allowing: it cannot
            # be packed tighter than MAX_URINE_OSM, so that much water
            # goes with it whether the body can spare it or not. This is
            # why osmotic diuresis floods while ADH is pinned at maximum —
            # the exact opposite of insipidus.
            #
            # Deliberately ADDITIVE, and deliberately only about the
            # foreign solute: applying the ceiling to this loop's own
            # excretion too would change what a salt bolus does, and
            # Phase 6 is not ours to rewrite (M20 decision 3 knowingly
            # left urine_osm un-ceilinged there). With no load this line
            # is exactly zero and the loop is the loop it always was.
            urine_rate += self._tubular_load / MAX_URINE_OSM * 1000.0
            urine_osm = ((excretion + self._tubular_load)
                         / (urine_rate / 1000.0))

            # Water budget (mL/min -> L per tick).
            absorbed = min(GUT_ABSORB_ML_MIN * minutes, self._gut_water)
            self._gut_water -= absorbed
            out_ml = (urine_rate + INSENSIBLE_ML_MIN
                      + (SWEAT_ML_MIN if self._exercise else 0.0)) * minutes
            self._water = max(1.0, self._water + (absorbed - out_ml) / 1000.0)

            # Solute budget (mOsm per tick).
            self._solutes += WASTE_PRODUCTION * minutes
            self._solutes -= excretion * minutes
            if self._exercise:
                self._solutes -= SWEAT_ML_MIN * SWEAT_OSM / 1000.0 * minutes
            self._solutes = max(0.0, self._solutes)

            self._t += self.DT
            self._append_record(error=error, adh=adh, thirst=thirst,
                                urine_rate=urine_rate, urine_osm=urine_osm)

    # ---------------- the data product (Phase 6 kickoff SS5) ----------------

    def _append_record(self, error, adh, thirst, urine_rate, urine_osm):
        self._history.append({
            "t": self._t,
            "osmolarity": self._solutes / self._water
                          + self._foreign_osm,
            "water_liters": self._water,
            "gut_water": self._gut_water,
            "exercise": self._exercise,
            "error": error,
            "adh": adh,
            "thirst": thirst,
            "urine_rate": urine_rate,
            "urine_osm": urine_osm,
            "adh_enabled": self._enabled["adh"],
            "kidney_enabled": self._enabled["kidney"],
            "water_access": self._enabled["access"],
            "sensor_enabled": self._sensor_enabled,
            "adh_override": self._adh_override,
            "tubular_load": self._tubular_load,
            "foreign_osm": self._foreign_osm,
        })

    def history(self):
        """Every record since reset, oldest first — THE source of truth."""
        return [dict(r) for r in self._history]

    def state(self):
        """The newest record."""
        return dict(self._history[-1])
