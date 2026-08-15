"""Console demo: two diseases, told in numbers.

Run:  python -m engine.disease_demo

Part 1 — FEVER is a moved set point, not a broken loop. Pyrogens shift
the thermostat to 39; the same hypothalamus defends the new number with
the same effectors. Watch the freaky facts fall out: shivering at 38 degC
(chills — because 38 is BELOW the new set point), a rock-steady hold at
~39, then drenching sweats at 38.5 when the fever breaks (because now
38.5 is far too hot). The loop never once malfunctions.

Part 2 — TWO DIABETES, ONE TELL. The same fast and the same meal run in
two bodies side by side: type 1 (beta cells dead) and type 2 (tissues
deaf — sensitivity 0.05). Both end up hyperglycemic. The INSULIN column
is the diagnosis: type 1 sits at exactly zero; type 2 pours it out and
is ignored. Same symptom, opposite mechanism — that is why the treatment
differs.
"""

from engine.glucose import GlucoseSimulation
from engine.sim import Simulation

FEVER_AT = 30          # minutes; pyrogens arrive
FEVER_BREAKS_AT = 150  # the infection is beaten, thermostat resets
FEVER_END = 270


def fever_story():
    print("PART 1 - fever: the thermostat moves, the loop obeys")
    print(f"{'t (min)':>8} {'core':>7} {'defending':>10} {'shiver':>7} "
          f"{'sweat':>6} {'vaso':>6}")
    print("-" * 50)
    sim = Simulation()
    for minute in range(1, FEVER_END + 1):
        if minute - 1 == FEVER_AT:
            print(f"{'':8} --- pyrogens: set point -> 39.0 degC ---")
            sim.set_fever(2.0)
        if minute - 1 == FEVER_BREAKS_AT:
            print(f"{'':8} --- fever breaks: set point -> 37.0 degC ---")
            sim.set_fever(0.0)
        sim.step(60)
        # rows every 15 min, plus a burst of close-ups right after each
        # event - the chills and the breaking sweat are minutes-fast
        closeup = (minute - FEVER_AT in (2, 4, 6, 8)
                   or minute - FEVER_BREAKS_AT in (2, 4, 6, 8))
        if minute % 15 and not closeup:
            continue
        s = sim.state()
        note = ""
        if s["shiver"] > 0.05 and s["core_temp"] > 37.2:
            note = "  <- chills while HOT"
        if s["sweat"] > 0.05 and s["core_temp"] > 37.2 and not s["fever_offset"]:
            note = "  <- sweating it out"
        print(f"{s['t'] / 60:>8.0f} {s['core_temp']:>7.2f} "
              f"{37.0 + s['fever_offset']:>10.1f} {s['shiver']:>7.2f} "
              f"{s['sweat']:>6.2f} {s['vaso']:>6.2f}{note}")


MEAL_AT = 360          # minutes; after a 6 h fast, the same 60 g meal
DIAB_END = 600


def diabetes_contrast():
    print("\nPART 2 - the same fast, the same meal, two different failures")
    print(f"{'t (min)':>8} | {'T1 gluc':>8} {'T1 insulin':>11} | "
          f"{'T2 gluc':>8} {'T2 insulin':>11}")
    print("-" * 56)
    t1 = GlucoseSimulation()
    t1.set_effector_enabled("beta", False)      # no insulin at all
    t2 = GlucoseSimulation()
    t2.set_insulin_sensitivity(0.05)            # insulin ignored
    for minute in range(1, DIAB_END + 1):
        if minute - 1 == MEAL_AT:
            print(f"{'':8} --- both bodies eat the same 60 g meal ---")
            t1.eat(60, 1.0)
            t2.eat(60, 1.0)
        t1.step(60)
        t2.step(60)
        if minute % 60:
            continue
        a, b = t1.state(), t2.state()
        print(f"{a['t'] / 60:>8.0f} | {a['glucose']:>8.1f} "
              f"{a['insulin']:>11.2f} | {b['glucose']:>8.1f} "
              f"{b['insulin']:>11.2f}")
    print("\nSame symptom (high glucose), opposite insulin columns: the")
    print("control center is silent in type 1, shouting unheard in type 2.")
    print("The diagnosis is a LOOP diagnosis - which box failed.")


def main():
    print("Vital Loop - disease physiology demo (fixed 1 s ticks)\n")
    fever_story()
    diabetes_contrast()


if __name__ == "__main__":
    main()
