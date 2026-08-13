# Build log — VITAL LOOP

Single source of truth for project state. Newest entry at the top of the
Milestones section. Claude Code: read this whole file at session start; append
an entry at the end of every milestone. Never delete or rewrite old entries.

Entry format:

```
## YYYY-MM-DD — M[n]: [milestone name]
- Shipped: [what now works, one or two lines]
- Deferred: [anything pushed to later, with the milestone it moved to]
- Open bugs: [anything known-broken, even if minor]
- Decisions: [any design/architecture choice made mid-milestone]
```

---

## Current state

- **Committed:** M6. Phase 2 spec is `vital_loop_phase2_kickoff.md`
  (M6–M10): the blood glucose loop.
- **Next up:** M7 — loop switcher tab (Temperature | Glucose), glucose
  strip charts with the 70–110 healthy band, `/state?loop=` param, both
  sims live and independent server-side.
- **Port:** 5083 (this project's own; see CLAUDE.md for the machine registry).
- **Open bugs:** none.
- **Standing caution:** the invariants file froze the history record fields
  (kickoff §5) and the engine API before M1 exists. If M1's physiology
  genuinely can't satisfy a pinned behavior (e.g. monotone cooling with
  effectors off), show the human the conflict — don't loosen the test
  silently.

---

## Milestones

## 2026-08-13 — M6: Glucose invariants + engine + console demo (Phase 2 starts)
- Shipped: glucose contract added to `tests/test_invariants.py` (API,
  frozen fields, 4 pinned physiology behaviors, determinism, and a
  Phase-1 regression guard: thermo scripted-run history sha256 pinned).
  `engine/glucose.py` — antagonistic islet controller with OVERLAPPING
  active ranges (both hormones nonzero at the set point), liver output
  boosted by glucagon / suppressed by insulin, paracrine disinhibition
  (no insulin → alpha cells run high → type 1 hyperglycemia persists
  honestly), renal spill above 180. `engine/glucose_demo.py` meal story.
  All 20 invariants pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions: fasted equilibrium ≈ 88 mg/dL with insulin 0.13 / glucagon
  0.40 both visibly active — the teaching point in the data. Sensor
  damage freezes hormones at their set-point values (sensed G = 90),
  which drifts the body hypo (~51) — hypoglycemia unawareness, honest
  consequence of the model. eat(grams, rate): newest meal sets the
  absorption pace (simplification, logged here on purpose).

## 2026-08-13 — M5: Break the loop + CSV export (Phase 1 complete)
- Shipped: per-effector disable buttons + sensor-damage toggle (status
  colors, "— DISABLED" labels), broken parts gray out dashed in the
  diagram, `/export.csv` streams the full run history (frozen column
  order, 1/0 bools). Verified live: sweating disabled on the hot run →
  core 37.06 → 37.42+ °C in ~160 sim-s (runaway, the punchline); sensor
  damage → sensed error 0 while true error 0.52 (receptor grayed, chain
  dark, stimulus lit); CSV header matches the frozen fields exactly.
- Deferred: Phase 2 candidates listed under Current state.
- Open bugs: none.
- Decisions: CSV bools export as 1/0 for spreadsheet graphing; export is
  a plain link (`download` attr), no JS.

## 2026-08-13 — M4: Live SVG loop diagram
- Shipped: `static/diagram.js` — Stimulus → Receptor → Control center →
  three Effectors → Response, negative-feedback return arrow, curriculum
  vocabulary on the labels. Boxes/arrows glow ∝ live activity from the
  same /state records as the charts. Verified in-browser: neutral at rest;
  freezer turns the sensing chain cold-blue and lights vessels/shiver.
- Deferred: nothing.
- Open bugs: none.
- Decisions: stimulus box lights from the TRUE error, receptor/control
  from the SENSED error — so M5's sensor damage will show the loop broken
  at exactly the right box. Cold/hot tint uses the diverging blue↔red
  pair; effector boxes glow in their chart series colors.

## 2026-08-13 — M3: Disturbance controls + effector panel
- Shipped: env-temp slider (−10…45 °C, debounced send, server-clamped),
  exercise toggle, two scenario buttons (freezer: −10 °C rest; hot run:
  38 °C + exercise — a scenario also auto-resumes a paused sim), and a
  third time-aligned chart panel: sweat/shiver/vessels with legend +
  direct labels (dataviz slots 3–5). Tooltip now shows effector values.
  Exercised live in the browser: both scenarios, slider, UI sync.
- Deferred: nothing.
- Open bugs: none.
- Decisions: UI controls reflect server truth on every poll, except while
  the teacher is mid-drag (their hand wins for 800 ms). Effector panel is
  one axis (−1…+1 dimensionless drive); vessels read +dilated/−constricted.

## 2026-08-13 — M2: Flask app with live strip charts
- Shipped: `app.py` (lazy-ticking runner — engine steps on each poll by
  wall-time × speed, capped catch-up; `/state` since-param JSON;
  `/control` pause/resume/reset/speed), page with core-temp and environment
  strip charts (SVG, dataviz-palette colors, crosshair tooltip), big
  classroom readouts. verify.py now a real end-to-end check incl. `/state`.
  Controls exercised live in the browser: 16× ≈ 32 sim-s per 2 wall-s,
  pause freezes clock, reset clears client buffer, bad speed → 400.
- Deferred: nothing.
- Open bugs: none.
- Decisions: no background thread — determinism and un-wedgeability beat
  smoothness we don't need at 4 Hz polling. Reset keeps the current speed
  setting on purpose. Chart y-ranges fixed (core 33–41, env −15–45) so
  vertical position stays trustworthy across a lesson.

## 2026-08-13 — M1: Thermoregulation engine + console demo
- Shipped: `engine/sim.py` (heat-budget model + proportional hypothalamus,
  frozen history records) and `python -m engine.demo` (cold-snap story:
  dip → vasoconstriction → shiver → recovery). All 11 invariants pass.
- Deferred: nothing.
- Open bugs: none. (One caught pre-commit: demo's cold snap at t=300 never
  fired because the loop stepped in 120 s chunks — trigger must sit on a
  chunk boundary; comment added.)
- Decisions: proportional-only control, so the loop holds a small honest
  steady-state error (~0.15 °C at 5 °C ambient) rather than snapping exactly
  to 37 — kept deliberately, it's real physiology and visible in the data.
  Constants sized for a ~70 kg adult (100 W basal, 245 kJ/°C, sweat max
  650 W, shiver max 300 W).

## 2026-08-13 — M0: Repo scaffolding
- Shipped: standing kit configured (port 5083, marker "Vital Loop");
  `tests/test_invariants.py` pins kickoff §2/§5 AND freezes the M1 engine
  API contract in its docstring. Venv created, git repo, first commit.
- Deferred: nothing.
- Open bugs: none.
- Decisions: engine API + history record fields frozen before the engine
  exists, so tests are the contract, not an afterthought.
