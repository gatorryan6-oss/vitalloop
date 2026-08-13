"""Console demo: the meal story, told in numbers.

Run:  python -m engine.glucose_demo

Thirty minutes fasted, then a 60 g meal absorbed over an hour. Watch both
hands of the antagonistic pair: insulin rises with the spike and pushes
glucose into tissues while shutting the liver off; as glucose settles back,
insulin fades and glucagon's tone returns to hold the floor. Two opposing
effectors, one set point.
"""

from engine.glucose import GlucoseSimulation

MEAL_AT = 1800         # seconds - when the meal lands
MEAL_GRAMS = 60.0
MEAL_RATE = 1.0        # g/min absorbed
TOTAL = 3 * 3600 + MEAL_AT
REPORT_EVERY = 600     # seconds between table rows (10 min)


def main():
    sim = GlucoseSimulation()
    print("Vital Loop - blood glucose demo (fixed 1 s ticks)")
    print(f"Set point {GlucoseSimulation.SET_POINT:.0f} mg/dL, healthy band "
          f"70-110. At t={MEAL_AT // 60} min: a {MEAL_GRAMS:.0f} g meal, "
          f"absorbed at {MEAL_RATE:.1f} g/min.\n")
    header = (f"{'t (min)':>8} {'glucose':>8} {'gut g':>6} {'insulin':>8} "
              f"{'glucagon':>9} {'uptake':>7} {'liver':>6}")
    print(header)
    print("-" * len(header))

    for t in range(0, TOTAL, REPORT_EVERY):
        if t == MEAL_AT:
            print(f"{'':8} --- meal: {MEAL_GRAMS:.0f} g of carbs ---")
            sim.eat(MEAL_GRAMS, MEAL_RATE)
        sim.step(REPORT_EVERY)
        s = sim.state()
        print(f"{s['t'] / 60:>8.0f} {s['glucose']:>8.1f} "
              f"{s['gut_carbs']:>6.1f} {s['insulin']:>8.2f} "
              f"{s['glucagon']:>9.2f} {s['uptake']:>7.2f} "
              f"{s['liver_flux']:>6.2f}")

    final = sim.state()
    print(f"\nAfter {final['t'] / 60:.0f} min: glucose "
          f"{final['glucose']:.1f} mg/dL - spiked, handled, back in the "
          "band. Both hormones did their half.")


if __name__ == "__main__":
    main()
