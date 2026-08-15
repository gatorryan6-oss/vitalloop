# Vital Loop — Claude Code Kickoff Prompt
### Phase 4: The closed-loop pump — rebuilding the feedback loop by hand

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M13 are committed
(three phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Earlier phases are **extended, never rebuilt** (CLAUDE.md standing
rule 3) — the one sanctioned adjustment: Phase 3's own diagram additions
(the syringe box and its arc) may be repositioned to make room for the
pump, since Phase 4 owns that corner of the drawing. The working agreement
in `~/.claude/CLAUDE.md` still governs: explain before doing, small
runnable increments, STOP at the phase checkpoint, patch with decimal
milestones, commit per milestone, append to `BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Phase 4 is the callback the whole build has been setting up. Phase 1 showed
an automatic feedback loop; Phase 2 showed a two-handed one; Phase 3 broke
it and made the student be the controller — by hand, on a delay, badly.
Phase 4 rebuilds the loop **artificially**: a closed-loop insulin pump (an
"artificial pancreas") whose CGM reads glucose, whose controller decides,
and whose pump doses — sensor → control center → effector, the same three
boxes, now made of silicone and math. The punchline of the entire unit:
**homeostasis is the loop structure, not the tissue.** Any working sensor,
controller, and effector — hypothalamus, islet cell, or microchip — buys
you a set point. Same priorities as ever: biology right > loop structure
explicit > aesthetics; one double-click, hard to wedge, vocabulary exact.

## 2 — Locked-in design decisions

(Chosen as my recommendations after the user picked the pump direction —
flagged for easy revisit before M14 starts. Everything not listed carries
over from Phases 1–3 unchanged.)

- **The pump is a proportional controller, like the hypothalamus.** Every
  5 sim-minutes it reads the SENSED glucose and sets its infusion rate:
  base rate plus gain × (sensed − target), clamped to [0, max]. No PID, no
  prediction — the teaching parallel ("the pump does exactly what the beta
  cells did: more insulin when glucose runs high") beats algorithmic
  sophistication, and the honest steady-state quirks of P-control are a
  feature, as they were in M1. Constants are tuned at M14 to hit the
  pinned behaviors; behaviors are the spec, not the constants.
- **The pump doses through the same subcutaneous machinery as Phase 3.**
  Its insulin enters the same depot with the same ~55-minute Erlang-2 lag.
  That lag is why a pump chasing a meal spike trails a real pancreas — the
  Phase 3 lesson (injected insulin is slow) stays true even when a machine
  does the injecting. Nothing gets a secret faster pathway.
- **The pump reads the model's sensed glucose — so the existing sensor
  breaker blinds it too.** Break the glucose sensors and the artificial
  loop fails exactly like the biological one: the pump freezes at the
  set-point rate while reality drifts. The break-the-loop story extends to
  the machine for free, and that IS the thesis of the phase.
- **Pump ON replaces the manual basal; manual boluses stay live.** One
  basal source at a time (the pump is the basal), so the basal selector
  grays out while the pump runs. The dosing buttons keep working — bolus
  for a meal on top of the pump and you get today's real-world hybrid
  systems; don't, and you watch full closed-loop cope alone with a spike.
  Both classroom stories, no new UI concepts.
- **Full closed loop, no meal announcements.** The pump gets no carb
  entry; a mealtime bolus by hand is the "announcement". (Flagged: if the
  user wants an explicit announce-meal button later, it's a decimal
  milestone, not a redesign.)
- **The frozen record grows two fields**: `pump_enabled` (bool) and
  `pump_rate` (U/h the algorithm chose this tick; 0 when off). `basal_rate`
  keeps meaning the MANUAL setting. The invariants file is amended FIRST,
  and a new regression guard pins that zero-pump runs are byte-identical
  on the Phase 2+3 field subset.
- **Sandbox stays sandbox.** The pump is a toggle, not a level to win.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. The pump
lives inside `engine/glucose.py` (it is glucose physiology's counterpart,
and it shares the islets' sensed input and the depot's kinetics);
`/control` gains a `pump` action that 400s on the temperature loop.

## 4 — Milestones

Continue Phase 3's numbering. Each milestone ends runnable; a milestone is
only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M14 — Pump contract + engine + console demo.** FIRST amend
  `tests/test_invariants.py`: extend the frozen glucose field set with
  `pump_enabled` and `pump_rate`, add the API contract
  (`sim.set_pump_enabled(bool)`), and pin the physiology: (a) **the
  artificial loop holds the line** — beta cells off + pump on, 12 h
  fasted stays inside 70–140 with no manual help; (b) **it survives a
  meal alone** — beta off + pump on, a 60 g meal peaks somewhere real
  (above 140 — the lag is honest) but returns to 70–140 within 4 h and
  never dips below 65; (c) **blind the sensor, break the machine** — beta
  off + pump on + sensors disabled → the pump keeps blindly infusing its
  set-point rate while the sensor-frozen alpha cells cannot defend, and
  glucose CRASHES below 54 within 3 h. (Amended pre-M14: the spec first
  guessed runaway hyperglycemia here; the model — and real CGM-failure
  physiology — says the blind failure mode is over-delivery, a hypo
  crash. Logged in BUILDLOG at M14.); (d) **regression
  guard** — a scripted Phase 3 run with the pump never enabled is
  byte-identical on the Phase 2+3 field subset, and the thermo and
  Phase 2 hashes stay untouched; (e) determinism including pump on/off
  mid-run; (f) pump decisions hold for 5 sim-minutes between updates (the
  recorded pump_rate is a staircase, not a ramp). Then build the pump to
  that contract and a console demo (`python -m engine.pump_demo`): the
  same type 1 day as M11's demo, twice — manual dosing vs pump — ending
  with the sensor-blinded failure.
  ✅ *Checkpoint: the demo table shows the pump living the day the human
  fumbled in M11; all invariants pass.*
- **M15 — Pump controls + charts + CSV.** The Insulin card gains a
  "Closed-loop pump" toggle and a live pump-rate readout; while the pump
  runs, the manual basal selector grays out (server enforces the
  override, UI just shows it). New strip-chart panel "Pump rate (U/h)"
  showing the staircase; the glucose CSV grows the two new columns
  (appended; earlier positions unchanged). `/control` action `pump`
  (on/off), glucose-loop-only.
  ✅ *Checkpoint: beta off, pump on, eat a meal — I watch the staircase
  climb the spike and ease off on the way down; the CSV opens with the
  new columns.*
- **M16 — The artificial loop, drawn + the capstone scenario.** The
  glucose diagram gains the pump as a second, machine-made loop: a CGM/
  pump box wired FROM the stimulus side (it reads glucose) and INTO the
  insulin pathway (it doses), glowing with pump activity; the Phase 3
  syringe elements may shift to fit. Sensor damage grays the pump's
  reading arrow — the machine loop breaks visibly at the same box as the
  biological one. Scenario button "Artificial pancreas day" (beta off +
  pump on + exercise off + 16×). Final story pass on the projector flow:
  Type 1 morning → fumble by hand → pump on → the machine holds the band
  → break the sensor → both loops dead, glucose runs away.
  ✅ *Checkpoint: the full four-phase arc runs start to finish on screen,
  and the class can see that the pump is just the loop diagram again —
  built by engineers.*

**STOP at the end of this phase and wait for my confirmation before
Phase 5.** (Phase 5 candidates, decided then: named disease presets,
water/ADH loop, scenario challenges, game layer.)

## 5 — Notes / data products

- **New frozen glucose fields**: `pump_enabled` (bool), `pump_rate` (U/h
  chosen by the algorithm this tick, 0.0 whenever the pump is off).
  Charts, CSV, and future layers read them from history — nothing derived
  only in JS.
- **Pump insulin is indistinguishable downstream** — it feeds the same
  depot, plasma, `injected_insulin`, `total_insulin`, and `iob_units`
  fields as Phase 3 boluses. No parallel accounting.
- **Server actions**: `pump` (bool value), glucose-loop-only, 400 on temp;
  while `pump_enabled`, `basal` actions are refused with a plain-English
  error (one basal source at a time). Scenario `pump_day` follows the
  existing pattern (set state, force speed, resume — never reset).
- **Regression guards stack, one per phase**: thermo hash (M6), Phase 2
  subset hash (M11), and now a Phase 2+3 subset hash recorded from M13
  code before the pump lands. The record shape may only ever grow.
