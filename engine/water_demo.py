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


if __name__ == "__main__":
    main()
