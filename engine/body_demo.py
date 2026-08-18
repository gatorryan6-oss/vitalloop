"""Console demo: the day two loops met (Phase 10, M37).

Run:  python -m engine.body_demo

An untreated type 1 body eats three ordinary meals. Nobody touches the
water controls at all — every drink in this story is the body deciding
by itself that it is thirsty.

Watch three columns together, because the diagnosis is in their
combination and in nothing else:

  spill    sugar leaving in the urine, once glucose passes 180 mg/dL
  urine    how fast water is going out with it
  u-osm    how loaded that urine is

Then compare the two floods at the end. Diabetes insipidus and diabetes
mellitus both pass water — that shared "diabetes" is Greek for siphon,
and for centuries the way to tell them apart was to taste the urine.
This demo shows why that worked.
"""

from engine.body import Body

MEALS_AT = (2, 6, 10)      # hours
MEAL_GRAMS = 75
END_AT = 12                # hours


def _run(label, setup=None, hours=END_AT):
    b = Body()
    if setup:
        setup(b)
    meal_ticks = {int(h * 3600) for h in MEALS_AT}
    for tick in range(int(hours * 3600)):
        if tick in meal_ticks:
            b.eat(MEAL_GRAMS, 1.0)
        b.step(1)
    return b


def main():
    print("Vital Loop - the coupled body (fixed 1 s ticks)")
    print("Glucose set point 90 mg/dL; osmolarity set point 290 mOsm/L.")
    print("The kidney starts spilling sugar above 180 mg/dL.\n")

    b = Body()
    b.set_effector_enabled("beta", False)     # untreated type 1
    print("An untreated type 1 body. Three 75 g meals, no insulin, and")
    print("a water bottle within reach. Nobody presses a drink button.\n")

    header = (f"{'t (h)':>6} {'glucose':>8} {'spill':>7} {'urine':>7} "
              f"{'u-osm':>7} {'osm':>7} {'ADH':>5} {'thirst':>7} "
              f"{'drank':>7}")
    print(header)
    print("-" * len(header))

    meal_ticks = {int(h * 3600) for h in MEALS_AT}
    seen_drinks = 0
    for tick in range(END_AT * 3600):
        if tick in meal_ticks:
            b.eat(MEAL_GRAMS, 1.0)
            print(f"{tick / 3600:>6.0f} {'--- a 75 g meal ---':>40}")
        b.step(1)
        if (tick + 1) % 1800:
            continue
        s = b.state()
        drinks = b.drinks()
        new = drinks[seen_drinks:]
        seen_drinks = len(drinks)
        drank = sum(d["ml"] for d in new)
        flag = " <- SPILLING" if s["renal_loss"] > 0.01 else ""
        print(f"{s['t'] / 3600:>6.1f} {s['glucose']:>8.0f} "
              f"{s['renal_loss']:>7.2f} {s['urine_rate']:>7.2f} "
              f"{s['urine_osm']:>7.0f} {s['osmolarity']:>7.1f} "
              f"{s['adh']:>5.2f} {s['thirst']:>7.2f} "
              f"{(str(int(drank)) + ' mL') if drank else '-':>7}{flag}")

    h = b.history()
    litres = sum(r["urine_rate"] for r in h) / 60.0 / 1000.0
    drank_l = sum(d["ml"] for d in b.drinks()) / 1000.0
    healthy = _run("healthy")
    healthy_l = sum(r["urine_rate"] for r in healthy.history()) / 60.0 / 1000.0

    print(f"\nOver {END_AT} h this body passed {litres:.2f} L of urine and "
          f"drank {drank_l:.2f} L back.")
    print(f"A healthy body eating the same three meals passed "
          f"{healthy_l:.2f} L and never spilled a milligram of sugar:")
    print("normal glucose simply never reaches the kidney's threshold, so")
    print("this whole story is a THRESHOLD being crossed, not a leak.")

    print("\n" + "=" * 66)
    print("The two siphons, side by side")
    print("=" * 66)
    ins = _run("insipidus",
               lambda s: s.set_effector_enabled("adh", False))
    mel = b

    def flooding(body, spill_driven):
        recs = [r for r in body.history()
                if (r["renal_loss"] > 1.0 if spill_driven
                    else r["urine_rate"] > 2.0)]
        osm = sum(r["urine_osm"] for r in recs) / len(recs)
        adh = sum(r["adh"] for r in recs) / len(recs)
        return osm, adh

    m_osm, m_adh = flooding(mel, True)
    i_osm, i_adh = flooding(ins, False)
    ins_l = sum(r["urine_rate"] for r in ins.history()) / 60.0 / 1000.0

    print(f"{'':22} {'urine passed':>14} {'urine osm':>11} {'ADH':>7}")
    print(f"{'diabetes MELLITUS':22} {litres:>11.2f} L "
          f"{m_osm:>10.0f} {m_adh:>7.2f}")
    print(f"{'diabetes INSIPIDUS':22} {ins_l:>11.2f} L "
          f"{i_osm:>10.0f} {i_adh:>7.2f}")
    print()
    print("Insipidus passes far MORE water - and it is nearly pure water,")
    print("because no hormone is telling the kidney to hold any of it back.")
    print("Tasteless.")
    print()
    print("Mellitus passes less, but that urine is LOADED, and look at the")
    print("ADH column: the hormone is working hard the whole time. Nothing")
    print("in this loop is broken. The water is leaving because sugar is")
    print("leaving, and solute drags water with it whether the body can")
    print("spare it or not. Honey-sweet.")
    print()
    print("Same siphon, opposite mechanism - and the only way to tell from")
    print("the outside was to taste it. Now you can read it off a chart.")


if __name__ == "__main__":
    main()
