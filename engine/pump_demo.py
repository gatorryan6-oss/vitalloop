"""Console demo: the same type 1 day, run by the machine.

Run:  python -m engine.pump_demo

M11's dosing demo showed a human working the syringe: right dose at
breakfast, same dose later becoming an overdose, juice boxes. This is the
rematch — a closed-loop pump lives the day instead. Four beats:

  1. Fasted, beta cells off, pump off: the disinhibited liver drives
     glucose up. Nobody is home in the control center.
  2. Pump ON: an artificial pancreas — CGM reads, controller decides,
     pump doses. Sensor -> control center -> effector, same loop as the
     hypothalamus and the islets, rebuilt in silicone. It catches the
     drift and holds the line, deciding every 5 minutes.
  3. Breakfast, 60 g, NO bolus and no announcement: the pump chases the
     spike through the same 55-minute subcutaneous lag a syringe has.
     Honest peak, safe landing, no human involved.
  4. The sensor dies. The pump keeps blindly infusing its set-point rate,
     the sensor-frozen alpha cells cannot ramp glucagon, and glucose
     slides into severe hypoglycemia — the machine loop fails at exactly
     the box the biological loop failed at in Phase 1's sensor-damage
     story. No feedback, no homeostasis. Silicon changes nothing.
"""

from engine.glucose import GlucoseSimulation

REPORT_EVERY = 30      # minutes between table rows

PUMP_ON_AT = 60        # after an hour of fasted climb
MEAL_AT = 300          # breakfast: 60 g, no bolus, no announcement
SENSOR_DIES_AT = 600   # the CGM fails silently
END_AT = 780


def main():
    sim = GlucoseSimulation()
    sim.set_effector_enabled("beta", False)
    print("Vital Loop - closed-loop pump demo (fixed 1 s ticks)")
    print("Beta cells OFF throughout: type 1 - but this time a machine is "
          "the control center.\nSet point 90 mg/dL, band 70-110, hypo < 70, "
          "severe < 54, hyper > 180.\n")
    header = (f"{'t (min)':>8} {'glucose':>8} {'gut g':>6} {'pump U/h':>9} "
              f"{'inj act':>8} {'IOB U':>6} {'glucagon':>9} {'liver':>6}")
    print(header)
    print("-" * len(header))

    events = {
        PUMP_ON_AT: ("--- closed-loop pump ON: sensor -> controller -> "
                     "pump, every 5 min ---",
                     lambda: sim.set_pump_enabled(True)),
        MEAL_AT: ("--- breakfast 60 g. No bolus, no announcement - the "
                  "pump is on its own ---",
                  lambda: sim.eat(60, 1.0)),
        SENSOR_DIES_AT: ("--- the CGM DIES. The pump reads 90 forever "
                         "and keeps infusing ---",
                         lambda: sim.set_sensor_enabled(False)),
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
        flag = (" <- SEVERE" if s["glucose"] < 54 else
                " <- HYPO" if s["glucose"] < 70 else
                " <- HYPER" if s["glucose"] > 180 else "")
        print(f"{s['t'] / 60:>8.0f} {s['glucose']:>8.1f} "
              f"{s['gut_carbs']:>6.1f} {s['pump_rate']:>9.2f} "
              f"{s['injected_insulin']:>8.2f} {s['iob_units']:>6.1f} "
              f"{s['glucagon']:>9.2f} {s['liver_flux']:>6.2f}{flag}")

    final = sim.state()
    print(f"\nAfter {final['t'] / 3600:.0f} h: glucose "
          f"{final['glucose']:.1f} mg/dL, pump still pushing "
          f"{final['pump_rate']:.2f} U/h at a body it cannot see. "
          "The lesson of the whole unit: homeostasis is the LOOP - "
          "sensor, control center, effector - whoever builds it. "
          "Break any box and it does not matter what the rest is made of.")


if __name__ == "__main__":
    main()
