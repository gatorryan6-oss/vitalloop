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

- **Committed:** M17 — Phase 5 (disease presets) in progress. Specs:
  phases 1–4 as before, plus `vital_loop_phase5_kickoff.md` (M17–M19).
  The human chose disease presets on 2026-08-15; the preset-list
  interview went unanswered, so all five ship as the flagged
  recommendation (fever, heat stroke, hypothermia, type 1, type 2).
  Remote: https://github.com/gatorryan6-oss/vitalloop
- **Next up:** M18 — Diseases card per loop, `/control preset` action,
  server preset table (full configuration + speed + banner line),
  banner strip in the UI.
- **Port:** 5083 (this project's own; see CLAUDE.md for the machine registry).
- **Open bugs:** none.
- **Standing caution:** the invariants file froze the history record fields
  (kickoff §5) and the engine API before M1 exists. If M1's physiology
  genuinely can't satisfy a pinned behavior (e.g. monotone cooling with
  effectors off), show the human the conflict — don't loosen the test
  silently.

---

## Milestones

## 2026-08-15 — M17: Disease physiology + contract + console demo
- Shipped: `set_fever(offset)` in the thermo engine (the hypothalamus
  defends SET_POINT + offset; the constant itself untouched) and
  `set_insulin_sensitivity(s)` in the glucose engine (one `effective =
  total × s` scales uptake, liver suppression, AND the paracrine brake).
  Records grew `fever_offset` / `insulin_sensitivity`; thermo guard (k)
  converted to Phase-1-subset hashing with its VALUE unchanged
  (9c83fe86…), proving shape-only growth; glucose subset guards updated
  the same way, values unchanged. Six new pins: fever holds 39 ± 0.5,
  chills-while-hot, sweats-while-cooling, the type 2 both-numbers-high
  signature (fasted 122 mg/dL WITH insulin 0.70 at s = 0.05), knob
  validation, determinism. `python -m engine.disease_demo`: fever story
  with close-up rows at the chills and the breaking sweat, then type 1
  and type 2 side by side (186/0.00 vs 122/0.70 — the insulin column IS
  the diagnosis). 41 invariants + verify pass. CSV columns pulled
  forward from M19: verify.py caught /export.csv 500ing on the grown
  records (DictWriter refuses unknown keys) — the columns belong with
  the fields, logged here.
- Deferred: nothing (M19 sheds the CSV item, absorbed here).
- Open bugs: none.
- Decisions: (1) Type 2 preset sensitivity is 0.05 — sweep showed the
  compensating beta cells defeat milder resistance (fasted ~94 at
  s = 0.3, honest early-T2 compensation), and 0.05 parks fasting at 122
  with the liver driven by unrestrained glucagon, which is the real
  pathophysiology, emergent. (2) The spec's fasted->110 guess survived
  contact with the model only at that knob value; no spec amendment
  needed. (3) set_fever accepts any float (negative = anesthesia
  teaching beat someday); sensitivity rejects 0 ("that's type 1 by
  another name — use the beta toggle").

## 2026-08-14 — M16: The artificial loop, drawn (Phase 4 complete)
- Shipped: pump box in the glucose diagram ("INJECTION — MACHINE",
  orange, faint floor-glow whenever enabled so an idle pump never looks
  off), CGM reading arc from the stimulus box and a dose arrow into the
  muscle pathway, both ∝ pump rate; the reading arc goes DARK when the
  sensors die while the pump box keeps glowing — dosing blind. Phase 3's
  syringe nudged left (sanctioned in the Phase 4 kickoff §0). Scenario
  "Artificial pancreas day" (beta off + pump on + 16×, never resets).
  Verified live end to end: one click started the day at 0.80 U/h;
  sensor kill froze the rate at 0.80 while glucose climbed the paracrine
  hump to 150 then slid to 53 — SEVERE HYPO chip on, CGM arrow gray,
  receptor dashed, pump box still lit. Both loops dead at the same box,
  visible on one screen.
- Deferred: nothing. Phase 5 candidates under Current state.
- Open bugs: none.
- Decisions: blinding an UNSETTLED pump takes the long way to the crash
  (paracrine disinhibition pushes glucose up before the slide) — the
  classroom beat is stronger if the sensor dies after the pump has been
  holding the line a while, which is also how the invariant pins it.

## 2026-08-14 — M15: Pump controls + charts + CSV
- Shipped: "Closed-loop pump" toggle + live rate readout on the Insulin
  card; manual basal selector locks while the pump runs (server refuses
  `basal` with a plain-English 400, UI disables the buttons); "Pump rate
  (U/h)" strip-chart panel between hormones and flows; glucose CSV grew
  `pump_enabled` + `pump_rate` (appended, earlier positions unchanged);
  `/control` action `pump`, glucose-loop-only. Verified live through the
  production path: pump on read 0.80 U/h at fasting (the proportional
  law by hand), a 60 g meal drove the staircase 1.31 → 3.98 U/h and back
  down to 2.82 as the spike landed; 18 recorded rate changes all sat on
  the 300 s grid; basal refusal and button lockout both confirmed; CSV
  header exact with live pump data in the rows.
- Deferred: nothing.
- Open bugs: none.
- Decisions: pump rate charts in the environment-orange slot (unused on
  the glucose page) — the pump is machinery, not hormone; the rate
  readout shows "—" when the pump is off rather than 0.00, so a dead
  pump never reads as a deliberate zero.

## 2026-08-14 — M14: Pump contract + engine + console demo (Phase 4 starts)
- Shipped: Phase 4 contract in `tests/test_invariants.py` (record grows
  `pump_enabled` + `pump_rate`; `set_pump_enabled` API; pins: holds a
  12 h fast in 70–140, survives a 60 g meal alone with nadir > 65 and
  return ≤ 4 h, blind sensor → crash < 54 within 3 h, 5-min staircase,
  determinism, Phase 2+3 subset hash recorded from M13 code BEFORE the
  engine changed). Pump in `engine/glucose.py`: proportional controller
  (base 1.0 U/h + 0.02 U/h per mg/dL over target 100, cap 5, decides
  every 5 sim-min), doses through the SAME depot/lag as Phase 3, reads
  the SAME sensed glucose as the islets. `python -m engine.pump_demo`:
  the M11 day re-run by the machine, ending in CGM death. 35 invariants
  + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) SPEC AMENDMENT, pre-M14, logged not silent: the kickoff
  first pinned blind-sensor failure as runaway hyperglycemia; the model
  (and real CGM-failure physiology) says the blind mode is OVER-delivery
  — pump frozen at set-point rate + sensor-frozen alpha cells → hypo
  crash. Pin (c) rewritten to the honest behavior before the contract
  landed. (2) Gains chosen by sweep: KP 0.05 oscillates through the
  55-min lag into hypos (real delayed-feedback hunting) — kept OUT of
  the default; target 100 runs hypo-shy like commercial systems. (3)
  Pump ON overrides the manual basal (one drip source at a time), never
  erases the stored setting. (4) Blind-crash test blinds AFTER 2 h of
  settled pumping: blinding from t=0 detours through the paracrine
  disinhibition spike first and needs > 3 h to crash (an emergent detail
  the first test run caught).

## 2026-08-13 — M13: The type 1 day, one click (Phase 3 complete)
- Shipped: "Type 1 morning" scenario (beta off + exercise off + 16×, never
  resets the run), "Juice box (15 g) — hypo rescue" eat-preset button,
  patient status on the glucose readout (label gains — HYPO / — SEVERE
  HYPO / — HYPER; value colors red / white-on-red chip / amber; clears on
  the temp loop). Verified live end to end through the production path:
  one click set the stage; sugary drink → HYPER at 200+; 8 U overdose →
  the long delayed plunge (peak 263 before the insulin bit) → SEVERE HYPO
  chip at 37; juice-box rescue took THREE boxes over ~90 sim-min against
  the 8 U tail (glucose sawtoothing, glucagon holding a ~66 plateau until
  the tail decayed) — the 15/15 rule emerged from the model, unscripted.
- Deferred: nothing. Phase 4 candidates listed under Current state.
- Open bugs: none.
- Decisions: severe-hypo line at 54 mg/dL (clinical level-2 threshold);
  status thresholds live only in the UI readout — the engine stays
  judgment-free (sandbox, no win/lose). Flask caches templates outside
  debug mode: after editing templates/, restart the server before
  verifying in the browser (verify.py's staleness check catches exactly
  this; the dev-server restart is the fix, not a bug).
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
