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

- **Committed:** M11 — Phase 3 (insulin-injection dosing) in progress.
  Specs: `vital_loop_v1_kickoff.md` (M0–M5), `vital_loop_phase2_kickoff.md`
  (M6–M10), `vital_loop_phase3_kickoff.md` (M11–M13).
- **Next up:** M13 — "Type 1 morning" scenario button, "Juice box (15 g)"
  rescue button, glucose readout status colors (HYPO < 70, severe < 54,
  HYPER > 180). Then the Phase 3 checkpoint STOP.
- **Port:** 5083 (this project's own; see CLAUDE.md for the machine registry).
- **Open bugs:** none.
- **Standing caution:** the invariants file froze the history record fields
  (kickoff §5) and the engine API before M1 exists. If M1's physiology
  genuinely can't satisfy a pinned behavior (e.g. monotone cooling with
  effectors off), show the human the conflict — don't loosen the test
  silently.

---

## Milestones

## 2026-08-13 — M12: The dosing panel
- Shipped: Insulin card on the glucose page (2/4/8 U bolus buttons, basal
  selector Off–2.0 U/h, live insulin-on-board readout), hormone panel now
  draws endogenous insulin, dashed injected insulin, and a wide soft
  total-insulin envelope, bolus markers on the glucose chart read from the
  engine's doses() log via /state, syringe box in the loop diagram
  ("INJECTION — YOU", outside the loop, arcing into the muscle pathway),
  `/control` actions inject (server-capped 15 U) + basal (allowed set),
  glucose CSV grew the four new columns (appended; Phase 2 positions
  unchanged). Verified live through the production poll path: beta off +
  sugary drink + 4 U → spike 219 with injected activity still tiny (the
  delay), activity peaking 0.515 at ~55 min post-dose, glucose landing at
  95 in the band; syringe box glowing green while beta sat gray-dashed;
  both CSV headers exact.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) downstream diagram effects (muscle glow, insulin→liver
  inhibition bar) run on total_insulin while each source box glows with
  its own output — the body can't tell insulins apart, the boxes can.
  (2) Injected insulin draws in the same green as endogenous but dashed —
  same hormone, artificial source; total is a 30 %-opacity width-6
  envelope under both. (3) An injection or basal change auto-resumes a
  paused sim, same rule as eating. (4) Verification note: with the app in
  a hidden pane, in-flight /control fetches abort if the page reloads —
  re-verify server truth after driving the UI, don't trust the click.

## 2026-08-13 — M11: Dosing contract + engine + console demo (Phase 3 starts)
- Shipped: Phase 3 contract in `tests/test_invariants.py` (record grows
  `injected_insulin`, `total_insulin`, `iob_units`, `basal_rate`;
  `inject`/`set_basal_rate`/`doses` API; pinned kinetics, replacement,
  overdose, basal-holds-the-line; Phase-2-subset regression hash recorded
  from M10 code BEFORE the engine changed). `engine/glucose.py` extended:
  subcutaneous depot with Erlang-2 kinetics (K=1/55 per min → peak ~55 min,
  ~23% of peak at 5 min, ~15% left at 4 h; ACTIVITY_PER_UNIT=0.35 ≈ the
  1 U : 15 g carb ratio), basal drips into the same depot (pump framing),
  IOB = depot + plasma. `python -m engine.dosing_demo` tells the type 1
  day. All 28 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) endogenous + injected insulin sum into ONE total activity
  driving all three insulin actions including the paracrine brake — so
  zero-injection runs are byte-identical to Phase 2 (guard hash proves it)
  and injections honestly re-restrain a type 1 liver. (2) `insulin` field
  keeps its Phase 2 meaning (beta output alone); the body responds to
  `total_insulin`. (3) reset() clears basal to 0. (4) Engine accepts any
  positive dose; the sane single-dose cap (~15 U) is server policy, M12.
  (5) Demo tuning surfaced REAL stacking: with 1.0 U/h basal running, the
  right breakfast bolus is 2 U, not 4 U — and the same 2 U with no meal
  behind it is an overdose. Kept as the demo's punchline; expect the same
  stacking live in class (that's the IOB readout's job).

## 2026-08-13 — M10: Break the glucose loop + CSV (Phase 2 complete)
- Shipped: glucose break card (beta/alpha/liver/sensor toggles, status
  colors, grayed dashed diagram parts, breaker selectors scoped per
  page), `/export.csv?loop=` for both loops with per-loop frozen columns
  and filenames. Verified live through the production poll() path: beta
  off + sugary drink → glucose climbing with insulin 0, glucagon
  disinhibited at 0.55, liver pouring 2.59 mg/dL·min — type 1 emerges;
  liver off grays the box and flips the label; both CSV headers exact.
- Deferred: nothing.
- Open bugs: none.
- Decisions: added a visibilitychange → poll() refresh: browsers freeze
  interval timers in hidden tabs (cost a debugging detour this session —
  frozen readouts in a hidden pane are throttling, not an app bug; the
  projected classroom tab is visible and unaffected).

## 2026-08-13 — M9: Glucose loop diagram
- Shipped: `diagram.js` refactored into a per-svg kit (scoped marker ids)
  building BOTH diagrams; temperature behavior unchanged (verified).
  Glucose layout: control center is two boxes — beta and alpha cells —
  with insulin's suppression of liver release drawn as an inhibition bar
  (-|), the biology convention. Verified live: fasted shows both hormone
  boxes lit at once (the antagonistic balance); a sugary drink flips the
  seesaw — beta path lights, alpha and liver go dark.
- Deferred: nothing.
- Open bugs: none.
- Decisions: diagram colors match the glucose page's chart legend
  (insulin aqua, glucagon yellow, liver magenta, uptake violet); stim
  glows full at 30 mg/dL off set point.

## 2026-08-13 — M8: Glucose disturbances
- Shipped: eat buttons (meal 60 g @ 1.0 g/min; sugary drink 40 g @ 1.5;
  balanced 60 g @ 0.4), glucose-page exercise toggle, "Skip meals —
  watch 12 h" scenario (exercise off + 16×; anything in the gut keeps
  absorbing — you can't un-eat). `/control` action `eat` validates and
  400s on the temperature loop. Verified live in the browser.
- Deferred: nothing.
- Open bugs: none.
- Decisions: a fast scenario bumps speed to 16× so the hours are
  watchable; eating auto-resumes a paused sim, same rule as scenarios.

## 2026-08-13 — M7: Loop switcher + glucose charts
- Shipped: two independent Runners server-side (`/state?loop=`,
  `/control?loop=`; loop-specific actions 400 on the wrong loop), header
  tabs Temperature | Glucose with per-loop readouts, per-loop chart
  buffers/windows (temp 10 min, glucose 2 h), three glucose panels:
  blood glucose (shaded 70–110 band, set point + hypo/hyper lines),
  hormones (insulin/glucagon), flows (liver vs uptake — same units, one
  axis). Verified live: tab switching, all panels drawing, glucose at
  16× while temp stayed 1×.
- Deferred: glucose CSV export → M10 (route currently temp-only).
- Open bugs: none.
- Decisions: pause/speed are PER LOOP (header controls act on the active
  tab). Browser polls only the visible loop; the hidden one catches up
  from server history on switch.

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
