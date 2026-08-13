"""The Vital Loop engine: one homeostatic negative-feedback loop, in numbers.

The model is a heat budget. Every tick, watts in (metabolism, shivering) and
watts out (skin transfer, sweat evaporation) are summed, and core temperature
moves by net watts / body heat capacity. The hypothalamus is a proportional
controller: it reads the error (core temp - set point) and commands the three
effectors. Vasomotor tone responds to any error; shivering and sweating each
have a small dead band and engage at larger errors - the same ordering as
real physiology (vessels first, then the expensive responses).

Loop-agnostic where cheap (kickoff SS5): the controller is generic - it maps
an error to effector drives via (threshold, gain) pairs and knows nothing
about temperature. The thermal physics lives separately in _heat_flows().
A Phase 2 glucose loop reuses the controller shape with its own physics.

The API and the history record shape are FROZEN by
tests/test_invariants.py - build against that contract, don't bend it.

No randomness, no clock reads: same inputs -> byte-identical history, so a
demo rehearsed at home behaves identically in class.
"""

# ---- Physical constants (SI-ish, sized for a ~70 kg resting adult) ----
BODY_HEAT_CAPACITY = 245_000.0   # J/degC  (~70 kg x 3500 J/kg/degC)
BASAL_METABOLISM = 100.0         # W at rest
EXERCISE_METABOLISM = 400.0      # W added while exercising
SKIN_K_NEUTRAL = 6.5             # W/degC skin<->environment at neutral tone
SKIN_K_VASO_SWING = 3.5          # +/- W/degC from full dilation/constriction
SHIVER_MAX_WATTS = 300.0         # heat added at full shiver
SWEAT_MAX_WATTS = 650.0          # evaporative cooling at full sweat

# ---- Controller tuning: effector = clamp((signed error - threshold) * gain) ----
# vaso responds to any error; shiver/sweat wait out a 0.1 degC dead band and
# reach full drive 0.2 degC later. Thresholds/gains are per-effector so a
# student (or Phase 2) can see "which responses are cheap and fast" as data.
VASO_GAIN = 2.0                  # full constriction/dilation at |error| = 0.5
SHIVER_THRESHOLD = 0.1           # degC below set point before shivering starts
SHIVER_GAIN = 5.0
SWEAT_THRESHOLD = 0.1            # degC above set point before sweating starts
SWEAT_GAIN = 5.0


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Simulation:
    """One body, one loop, fixed 1-second ticks."""

    SET_POINT = 37.0             # degC - the number the whole lesson hangs on
    DT = 1.0                     # seconds of sim time per tick

    def __init__(self):
        self.reset()

    def reset(self):
        """Fresh classroom start: 22 degC room, resting, everything working."""
        self._env_temp = 22.0
        self._exercise = False
        self._enabled = {"sweat": True, "shiver": True, "vaso": True}
        self._sensor_enabled = True
        self._core_temp = self.SET_POINT
        self._t = 0.0
        self._history = []
        self._append_record(error=0.0, sweat=0.0, shiver=0.0, vaso=0.0)

    # ---------------- disturbances and break-the-loop toggles ----------------

    def set_env_temp(self, celsius):
        self._env_temp = float(celsius)

    def set_exercise(self, on):
        self._exercise = bool(on)

    def set_effector_enabled(self, name, on):
        if name not in self._enabled:
            raise KeyError(
                f"Unknown effector {name!r}; expected one of "
                f"{sorted(self._enabled)}")
        self._enabled[name] = bool(on)

    def set_sensor_enabled(self, on):
        self._sensor_enabled = bool(on)

    # ------------------------------- the loop -------------------------------

    def _control(self, error):
        """Hypothalamus: signed error in -> commanded effector drives out.
        Knows nothing about temperature - just thresholds and gains."""
        return {
            "vaso": _clamp(error * VASO_GAIN, -1.0, 1.0),
            "shiver": _clamp((-error - SHIVER_THRESHOLD) * SHIVER_GAIN,
                             0.0, 1.0),
            "sweat": _clamp((error - SWEAT_THRESHOLD) * SWEAT_GAIN, 0.0, 1.0),
        }

    def _heat_flows(self, sweat, shiver, vaso):
        """Net watts into the core, given actual effector activity."""
        watts_in = BASAL_METABOLISM
        if self._exercise:
            watts_in += EXERCISE_METABOLISM
        watts_in += SHIVER_MAX_WATTS * shiver
        skin_k = SKIN_K_NEUTRAL + SKIN_K_VASO_SWING * vaso
        watts_out = skin_k * (self._core_temp - self._env_temp)
        watts_out += SWEAT_MAX_WATTS * sweat
        return watts_in - watts_out

    def step(self, n=1):
        """Advance n ticks. Each tick: sense -> decide -> act -> record."""
        for _ in range(int(n)):
            # Sense. A damaged sensor reports "all is well" - the controller
            # then does nothing, which is exactly the failure students see.
            error = ((self._core_temp - self.SET_POINT)
                     if self._sensor_enabled else 0.0)
            commanded = self._control(error)
            # Act - a disabled effector produces nothing, whatever was asked.
            sweat = commanded["sweat"] if self._enabled["sweat"] else 0.0
            shiver = commanded["shiver"] if self._enabled["shiver"] else 0.0
            vaso = commanded["vaso"] if self._enabled["vaso"] else 0.0
            net_watts = self._heat_flows(sweat, shiver, vaso)
            self._core_temp += (net_watts / BODY_HEAT_CAPACITY) * self.DT
            self._t += self.DT
            self._append_record(error=error, sweat=sweat, shiver=shiver,
                                vaso=vaso)

    # ---------------- the data product (kickoff SS5) ----------------

    def _append_record(self, error, sweat, shiver, vaso):
        self._history.append({
            "t": self._t,
            "core_temp": self._core_temp,
            "env_temp": self._env_temp,
            "exercise": self._exercise,
            "error": error,
            "sweat": sweat,
            "shiver": shiver,
            "vaso": vaso,
            "sweat_enabled": self._enabled["sweat"],
            "shiver_enabled": self._enabled["shiver"],
            "vaso_enabled": self._enabled["vaso"],
            "sensor_enabled": self._sensor_enabled,
        })

    def history(self):
        """Every record since reset, oldest first. THE source of truth -
        charts, CSV export, and future layers all read this, never their
        own copy."""
        return [dict(r) for r in self._history]

    def state(self):
        """The newest record."""
        return dict(self._history[-1])
