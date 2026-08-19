"""The islet's own faults, in numbers - the M57 checkpoint.

    python -m engine.islet_demo

Three diseases the app could not tell before Phase 14:

  Act 1  INSULINOMA. Every disease in this app so far is a part switched
         OFF or a signal missing. This one is STUCK ON: beta-cell tissue
         that stopped listening and secretes anyway. The loop fails in
         the opposite direction - down, not up - and the counter-
         regulation is working perfectly the whole way.
  Act 2  REACTIVE HYPOGLYCEMIA. Nothing is broken at all. The insulin is
         LATE, and a controller acting on stale error overshoots.
  Act 3  TREATED MELLITUS. Insulin is being given, the numbers improve,
         and it is still not control.

All three run on fixed 1 s ticks with no clock and no randomness, so
these numbers are the numbers the class will see.
"""

from engine.body import Body
from engine.glucose import GlucoseSimulation

MEAL_G = 75


def _row(t_s, g, insulin, glucagon, note=""):
    print(f"  {t_s/60:7.0f}  {g:7.1f}  {insulin:7.2f}  {glucagon:8.2f}"
          f"   {note}")


def _head(title, table=True):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)
    if table:
        print("   t(min)  glucose  insulin  glucagon")


def act1_insulinoma():
    _head("Act 1 - INSULINOMA: an effector stuck ON")
    sim = GlucoseSimulation()
    sim.set_autonomous_insulin(0.55)
    for minute in range(0, 361, 30):
        if minute:
            sim.step(30 * 60)
        r = sim.state()
        note = ""
        if r["glucose"] < 70.0:
            note = "<- HYPOGLYCEMIA"
        _row(r["t"], r["glucose"], r["insulin"], r["glucagon"], note)
    print()
    print("  The sugar settles near 55 mg/dL and STAYS there. Glucagon is")
    print("  pinned at maximum - the opposing hormone is doing everything")
    print("  it can and still losing, because the tumour does not answer")
    print("  to the sensor.")
    off = GlucoseSimulation()
    off.set_autonomous_insulin(0.55)
    off.set_effector_enabled("beta", False)
    off.step(6 * 3600)
    print(f"  Switch the NORMAL beta cells off and it still reads "
          f"{off.state()['glucose']:.1f} mg/dL:")
    print("  the tumour is not the islet, and breaking the islet does not")
    print("  break the tumour.")


def act2_reactive():
    _head("Act 2 - REACTIVE HYPOGLYCEMIA: nothing broken, just late")
    sim = GlucoseSimulation()
    sim.set_insulin_lag(1800.0)          # the islet is half an hour behind
    sim.set_insulin_gain(1.4)
    sim.step(1800)
    sim.eat(MEAL_G, 1.0)
    for minute in range(30, 391, 30):
        sim.step(30 * 60)
        r = sim.state()
        note = ""
        if r["glucose"] > 180.0:
            note = "<- peak running high"
        elif r["glucose"] < 70.0:
            note = "<- the overshoot: HYPOGLYCEMIA"
        _row(r["t"], r["glucose"], r["insulin"], r["glucagon"], note)
    h = sim.history()
    peak_i = max(range(len(h)), key=lambda i: h[i]["glucose"])
    after = h[peak_i:]
    trough = min(after, key=lambda r: r["glucose"])
    print()
    print(f"  Sampled every 30 min above; the true peak is "
          f"{h[peak_i]['glucose']:.1f} mg/dL at "
          f"{h[peak_i]['t']/60:.0f} min and the true trough is "
          f"{trough['glucose']:.1f} mg/dL")
    print(f"  at {trough['t']/60:.0f} min - below the 70 line, which a "
          "half-hourly table steps straight over.")
    print()
    print("  A 75 g meal at t=30. The peak runs high because the insulin")
    print("  has not arrived yet; then it arrives, the sugar is already")
    print("  falling, and the loop drives it straight past the set point")
    print("  into hypoglycemia about two hours later. Every box of the")
    print("  loop is intact. The fault is in the TIMING.")


def act3_treated():
    _head("Act 3 - TREATED MELLITUS: better numbers, same broken loop",
          table=False)
    print("  (three 75 g meals over 12 h, in the coupled body)")

    def day(setup):
        b = Body()
        setup(b)
        meals = {int(h * 3600) for h in (2, 6, 10)}
        for tick in range(12 * 3600):
            if tick in meals:
                b.eat(MEAL_G, 1.0)
            b.step(1)
        return b.history()

    def line(label, h):
        g = [r["glucose"] for r in h]
        above = sum(1 for x in g if x > 180.0) / len(g) * 100
        spill = sum(r["renal_loss"] for r in h) / len(h)
        print(f"  {label:24s} mean {sum(g)/len(g):6.1f}  peak {max(g):6.1f}"
              f"  {above:5.1f}% above 180  spill {spill:5.2f}")

    print()
    print(f"  {'':24s} {'':11s} {'':12s} (mg/dL/min)")
    line("healthy", day(lambda b: None))
    line("untreated mellitus",
         day(lambda b: b.set_effector_enabled("beta", False)))

    def treated(b):
        b.set_effector_enabled("beta", False)
        b.set_basal_rate(0.5)
    line("treated, basal 0.5 U/hr", day(treated))
    print()
    print("  Treatment moves the mean from about 230 down to about 140 -")
    print("  a real improvement a class can measure. And a quarter of the")
    print("  day is still above the kidney's threshold, so sugar is still")
    print("  going into the urine and still dragging water with it. The")
    print("  curve changed. The loop did not.")


def main():
    act1_insulinoma()
    act2_reactive()
    act3_treated()
    print()


if __name__ == "__main__":
    main()
