"""Console demo: a type 1 day, told in numbers.

Run:  python -m engine.dosing_demo

The beta cells are off from the start — this body makes no insulin of its
own, so the student is the control center now. The four beats of the
Phase 3 lesson:

  1. Fasted, the disinhibited liver drives glucose UP — no meal in sight.
  2. A 1.0 U/h basal drip re-restrains the liver and holds the fasting line.
  3. Breakfast + a 2 U bolus taken TOGETHER lands the spike — smaller than
     you'd think, because the basal is already covering the background and
     the body only counts TOTAL insulin. Even so, the crest brushes past
     180 for a few minutes: a syringe on a 55-minute delay can't fully
     match a pancreas that answers in seconds.
  4. The very same 2 U with NO meal behind it is an overdose. Same number,
     different context, hypoglycemia — and a 15 g juice box is the rescue.
"""

from engine.glucose import GlucoseSimulation

REPORT_EVERY = 30      # minutes between table rows

BASAL_AT = 120         # after 2 h of fasted climb, the basal goes on
MEAL_AT = 300          # breakfast: 60 g + 2 U bolus, together
NO_MEAL_DOSE_AT = 540  # the same 2 U, nothing to eat behind it
RESCUE_AT = 600        # juice box: 15 g fast carbs
END_AT = 780


def main():
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    print("Vital Loop - insulin dosing demo (fixed 1 s ticks)")
    print("Beta cells OFF throughout: type 1 - the student is the control "
          "center now.\nSet point 90 mg/dL, band 70-110, hypo < 70, "
          "hyper > 180.\n")
    header = (f"{'t (min)':>8} {'glucose':>8} {'gut g':>6} {'IOB U':>6} "
              f"{'inj act':>8} {'glucagon':>9} {'uptake':>7} {'liver':>6}")
    print(header)
    print("-" * len(header))

    events = {
        BASAL_AT: ("--- basal drip on: 1.0 U/h ---",
                   lambda: sim.set_basal_rate(1.0)),
        MEAL_AT: ("--- breakfast 60 g + 2 U bolus, together ---",
                  lambda: (sim.eat(60, 1.0), sim.inject(2))),
        NO_MEAL_DOSE_AT: ("--- the same 2 U bolus, NO meal behind it ---",
                          lambda: sim.inject(2)),
        RESCUE_AT: ("--- hypo! juice box: 15 g fast carbs ---",
                    lambda: sim.eat(15, 1.5)),
    }

    for minute in range(1, END_AT + 1):
        if minute - 1 in events:
            line, act = events[minute - 1]
            print(f"{'':8} {line}")
            act()
        sim.step(60)
        if minute % REPORT_EVERY:
            continue
        s = sim.state()
        flag = " <- HYPO" if s["glucose"] < 70 else (
            " <- HYPER" if s["glucose"] > 180 else "")
        print(f"{s['t'] / 60:>8.0f} {s['glucose']:>8.1f} "
              f"{s['gut_carbs']:>6.1f} {s['iob_units']:>6.1f} "
              f"{s['injected_insulin']:>8.2f} {s['glucagon']:>9.2f} "
              f"{s['uptake']:>7.2f} {s['liver_flux']:>6.2f}{flag}")

    final = sim.state()
    print(f"\nAfter {final['t'] / 3600:.0f} h: glucose "
          f"{final['glucose']:.1f} mg/dL. No beta cells all day - every "
          "landing in the band was a human decision, made on a 55-minute "
          "delay. That is what type 1 management is.")


if __name__ == "__main__":
    main()
