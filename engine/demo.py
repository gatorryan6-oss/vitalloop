"""Console demo: the cold-room story, told in numbers.

Run:  python -m engine.demo

Four minutes resting in a 22 degC room, then the room drops to 5 degC and
stays there for 56 minutes. Watch the columns: core temp dips, the skin
vessels clamp down (vaso goes negative), shivering spikes, and core temp
climbs back toward the 37.0 set point. That arc - disturbance, response,
recovery - is the whole lesson.
"""

from engine.sim import Simulation

COLD_AT = 240          # seconds - when the room drops. MUST be a multiple of
                       # REPORT_EVERY or the trigger below never fires.
COLD_TEMP = 5.0        # degC
TOTAL = 3600           # seconds simulated
REPORT_EVERY = 120     # seconds between table rows


def main():
    sim = Simulation()
    print("Vital Loop - thermoregulation demo (fixed 1 s ticks)")
    print(f"Set point {Simulation.SET_POINT:.1f} degC. Room starts at 22.0 "
          f"degC; at t={COLD_AT} s it drops to {COLD_TEMP:.1f} degC.\n")
    header = (f"{'t (min)':>8} {'room':>6} {'core':>8} {'error':>8} "
              f"{'vaso':>6} {'shiver':>7} {'sweat':>6}")
    print(header)
    print("-" * len(header))

    for t in range(0, TOTAL, REPORT_EVERY):
        if t == COLD_AT:
            print(f"{'':8} --- cold snap: room -> {COLD_TEMP:.0f} degC ---")
            sim.set_env_temp(COLD_TEMP)
        sim.step(REPORT_EVERY)
        s = sim.state()
        print(f"{s['t'] / 60:>8.1f} {s['env_temp']:>6.1f} "
              f"{s['core_temp']:>8.3f} {s['error']:>8.3f} "
              f"{s['vaso']:>6.2f} {s['shiver']:>7.2f} {s['sweat']:>6.2f}")

    final = sim.state()
    print(f"\nAfter {final['t'] / 60:.0f} min: core temp "
          f"{final['core_temp']:.2f} degC "
          f"(set point {Simulation.SET_POINT:.1f}) - the loop held.")


if __name__ == "__main__":
    main()
