"""Console demo: a day of water balance, told in numbers.

Run:  python -m engine.water_demo

Watch the urine columns — they are the kidney obeying ADH in real time:
concentrated-and-scant when the body is conserving, dilute-and-flooding
when it has water to burn. And watch the drink markers: nobody presses a
button — thirst is an EFFECTOR, and the loop closes through behavior.

  1. A salty lunch: osmolarity jumps, ADH conserves, thirst wakes, the
     body drinks itself back to the set point.
  2. A 2 L chug: osmolarity dips, ADH dies, the kidneys dump the excess
     as a dilute flood.
  3. The desert: no water, sweating. ADH pins urine at the floor and the
     body dehydrates anyway — conserving is not refilling.
  4. Rescue: water is back within reach. Thirst does the rest.

Act 2 (M31) is SIADH — the mirror image of DI: not too little ADH but
ADH that won't stop. The patient just drinks normally, and that is
enough to poison them; the fix is to stop the drinking.
"""

from engine.water import WaterSimulation

SALTY_AT = 60          # minutes; a 300 mOsm salty lunch
CHUG_AT = 180          # 2 L, fast
DESERT_AT = 420        # no water + sweating
RESCUE_AT = 660        # water again
END_AT = 780


def main():
    sim = WaterSimulation()
    print("Vital Loop - water/ADH demo (fixed 1 s ticks)")
    print("Set point 290 mOsm/L, band 285-295, dehydration > 305, "
          "overhydration < 280.\n")
    header = (f"{'t (min)':>8} {'osm':>6} {'water L':>8} {'ADH':>5} "
              f"{'thirst':>7} {'urine':>6} {'u-osm':>6} {'drank':>6}")
    print(header + "   (urine mL/min; u-osm mOsm/L)")
    print("-" * (len(header) + 3))

    events = {
        SALTY_AT: ("--- salty lunch: +300 mOsm ---",
                   lambda: sim.eat_salt(300)),
        CHUG_AT: ("--- chug 2 L ---", lambda: sim.drink(2000)),
        DESERT_AT: ("--- the desert: no water, sweating ---",
                    lambda: (sim.set_effector_enabled("access", False),
                             sim.set_exercise(True))),
        RESCUE_AT: ("--- rescue: water within reach again ---",
                    lambda: (sim.set_effector_enabled("access", True),
                             sim.set_exercise(False))),
    }

    seen_drinks = 0
    for minute in range(1, END_AT + 1):
        if minute - 1 in events:
            line, act = events[minute - 1]
            print(f"{'':8} {line}")
            act()
        sim.step(60)
        if minute % 30:
            continue
        s = sim.state()
        drinks = sim.drinks()
        new = drinks[seen_drinks:]
        seen_drinks = len(drinks)
        drank = sum(d["ml"] for d in new if d["auto"])
        flag = ""
        if s["osmolarity"] > 305:
            flag = " <- DEHYDRATED"
        elif s["osmolarity"] < 280:
            flag = " <- OVERHYDRATED"
        print(f"{s['t'] / 60:>8.0f} {s['osmolarity']:>6.1f} "
              f"{s['water_liters']:>8.2f} {s['adh']:>5.2f} "
              f"{s['thirst']:>7.2f} {s['urine_rate']:>6.1f} "
              f"{s['urine_osm']:>6.0f} "
              f"{(str(int(drank)) + ' mL') if drank else '-':>6}{flag}")

    auto = sum(1 for d in sim.drinks() if d["auto"])
    print(f"\nThe body drank by itself {auto} times today. The kidney can "
          "only slow the drain;\nonly behavior refills the tank - one "
          "effector of this loop lives in the outside world.")

    siadh_act()


def siadh_act():
    """Act 2: SIADH (M31). ADH pinned at full; the patient drinks a
    perfectly ordinary glass every 30 min - and dilutes."""
    print("\n" + "=" * 66)
    print("Act 2 - SIADH: the hormone that won't stop")
    print("ADH is pinned at 1.00 no matter what the receptors say. The")
    print("patient drinks one 250 mL glass every 30 min - normal habit,")
    print("nothing heroic. Watch osm fall while urine stays concentrated")
    print("and thirst NEVER SPEAKS - low osmolarity is the one thing")
    print("thirst doesn't answer. At 4 h: water restriction.\n")

    sim = WaterSimulation()
    sim.set_adh_override(1.0)
    header = (f"{'t (min)':>8} {'osm':>6} {'ADH':>5} {'thirst':>7} "
              f"{'urine':>6} {'u-osm':>6}")
    print(header)
    print("-" * len(header))

    def row(flag=""):
        s = sim.state()
        auto_flag = flag
        if not auto_flag and s["osmolarity"] < 280:
            auto_flag = " <- OVERHYDRATED (dilutional hyponatremia)"
        print(f"{s['t'] / 60:>8.0f} {s['osmolarity']:>6.1f} {s['adh']:>5.2f} "
              f"{s['thirst']:>7.2f} {s['urine_rate']:>6.1f} "
              f"{s['urine_osm']:>6.0f}{auto_flag}")

    for half_hour in range(8):             # 4 h of ordinary drinking
        sim.drink(250)
        sim.step(1800)
        row()
    print(f"{'':8} --- water restriction: no more glasses ---")
    for _ in range(4):                     # 2 h restricted
        sim.step(1800)
        row()

    print("\nThe slide STOPPED the moment the drinking did - restriction,")
    print("the real first-line treatment, falls out of the physics. And")
    print("the alarm column read 0.00 the whole way down: this loop can't")
    print("feel the failure mode where it holds too much.")


if __name__ == "__main__":
    main()
