# Vital Loop — Claude Code Kickoff Prompt
### Phase 3: Insulin-injection dosing — when the student becomes the control center

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M10 are committed (both
phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Phase 1 and Phase 2 code is **extended, never rebuilt** (CLAUDE.md
standing rule 3). The working agreement in `~/.claude/CLAUDE.md` still
governs: explain before doing, small runnable increments, STOP at the phase
checkpoint, patch with decimal milestones, commit per milestone, append to
`BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Phase 3 puts the syringe in the student's hand. Phase 1 showed one controller
pushing back; Phase 2 showed two opposing controllers holding a set point
from both sides — and what happens when the beta cells fail (type 1
diabetes). Phase 3 completes that story: with the beta cells gone, **a person
has to BE the control center**, replacing an automatic feedback loop with
manual, open-loop decisions — how many units, and when. The teaching
punchline: manual control is *hard*. Injected insulin acts on a delay, it
cannot be un-injected, too little leaves hyperglycemia, too much causes
hypoglycemia — the acute danger every person with type 1 manages daily.
Same priorities as ever: biology right > loop structure explicit >
aesthetics. Same classroom constraints: one double-click, hard to wedge,
vocabulary exact — and Phase 3 adds the real management vocabulary: *bolus,
basal, insulin on board, fast-acting carbs*.

## 2 — Locked-in design decisions

(Chosen as my recommendations — the working agreement's interview step can't
run in an autonomous session, so these are flagged for easy revisit before
M11 starts. Everything not listed carries over from Phases 1–2 unchanged.)

- **Injected insulin is subcutaneous, not instant.** A bolus goes into a
  skin depot and is absorbed through a two-compartment chain
  (depot → absorbing → plasma activity), giving the real rapid-acting-analog
  shape: little effect in the first minutes, peak effect roughly 30–90 sim-
  minutes after injection, essentially spent by ~4 sim-hours. The delay is
  the load-bearing teaching mechanic — dose *for* the meal, not *at* the
  spike, and doses stack invisibly ("insulin on board").
- **Doses are in real units (U).** Bolus buttons (2 U / 4 U / 8 U, stacking)
  and a basal drip setting (Off / 0.5 / 1.0 / 1.5 / 2.0 U/h — a pump basal
  or long-acting analog, pick the plainer label at build time). Tuning
  target: ~4 U covers a 60 g meal in a beta-off body (≈ the classic
  1 U : 15 g carb ratio), and ~1 U/h basal restores near-normal fasting
  glucose in a beta-off body. Constants are tuned at M11 to hit the pinned
  behaviors; the behaviors are the spec, not the constants.
- **Exogenous insulin IS insulin.** The body responds to total insulin
  activity — endogenous (beta cells) plus injected — in all three places
  the hormone acts: tissue uptake, liver suppression, and the paracrine
  brake on the alpha cells. That last one matters: injecting insulin into
  a type 1 body visibly re-restrains glucagon and the liver, which is real
  physiology and the reason injections work at all. No special-cased
  "diabetes math" anywhere.
- **The frozen record gains fields; existing fields keep their meaning.**
  `insulin` stays "beta-cell output" exactly as in Phase 2. New frozen
  fields: `injected_insulin` (exogenous plasma activity, 0..1),
  `total_insulin` (the clamped sum the body actually responds to — recorded,
  not computed in JS), `iob_units` (units still working: depot + plasma,
  the "insulin on board" readout), `basal_rate` (U/h). The invariants file
  is amended FIRST, deliberately, as M6 did for Phase 2.
- **Dose events are a data product.** The engine keeps a queryable list of
  boluses (`sim.doses()` → `[{"t": ..., "units": ...}, ...]`) so chart
  markers, the CSV story, and any future quiz layer read recorded events —
  never inferred in JS from wiggles in a curve.
- **Injections work on a healthy pancreas too — on purpose.** The dosing
  panel is always available on the glucose page. Injecting into a working
  loop and watching the beta cells throttle back (and glucose still dip) is
  its own lesson: the natural controller adjusts, the syringe never does.
- **Sandbox stays sandbox.** No score, no win/lose. Hypoglycemia is shown
  honestly (glucose below 70, below 54 severe) with status colors, not a
  game-over screen. The challenge/game layer stays deferred.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. The dosing
model lives inside `engine/glucose.py` (it is glucose physiology, not a new
loop); `/control` gains `inject` and `basal` actions that 400 cleanly on the
temperature loop, mirroring how `eat` already behaves.

## 4 — Milestones

Continue Phase 2's numbering. Each milestone ends runnable; a milestone is
only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M11 — Dosing contract + engine + console demo.** FIRST amend
  `tests/test_invariants.py`: extend the frozen glucose field set with the
  four new fields, add the API contract (`sim.inject(units)`,
  `sim.set_basal_rate(u_per_hr)`, `sim.doses()`), and pin the physiology:
  (a) **not instant** — after a bolus, `injected_insulin` peaks between 30
  and 90 sim-minutes, is under 30 % of that peak in the first 5 minutes,
  and is under 25 % of peak 4 h later; (b) **replacement works** — beta
  cells off, 60 g meal + 4 U at mealtime → glucose comes back down into
  70–110 within 5 sim-hours and never drops below 65 within 8 h;
  (c) **overdose is dangerous** — beta cells off, fasted, 10 U →
  glucose falls below 70 within 3 h even though glucagon and the liver
  fight back (no secret rescue, no secret floor); (d) **basal holds the
  fasting line** — beta cells off + 1.0 U/h basal → 12 h fasted stays
  inside 70–180 (contrast: Phase 2 already proved beta-off with no basal
  climbs past 180); (e) **regression guard** — the Phase 2 scripted glucose
  run with zero injections produces byte-identical values on the Phase 2
  fields (hash over that subset), and the thermo hash is untouched;
  (f) determinism including injections. Then build the engine to that
  contract and a console demo (`python -m engine.dosing_demo`): the type 1
  day in numbers — fasted climb, basal catches it, meal + bolus controls
  the spike, overdose shows the hypo.
  ✅ *Checkpoint: demo table tells the type 1 story; all invariants pass.*
- **M12 — The dosing panel.** Glucose page gains an "Insulin" card: bolus
  buttons (2 U / 4 U / 8 U), basal selector, and an **insulin on board**
  readout (U, live). Hormones chart panel adds `injected_insulin` and
  `total_insulin` series (legend + direct labels, palette-consistent);
  bolus markers appear on the time axis from `doses()` data delivered in
  `/state`. The loop diagram gains a syringe box — "Injected insulin" —
  wired into the insulin pathway with its own arrow, glowing ∝ injected
  activity: with beta cells dark, the class SEES the manual controller
  substituting for the missing box. `/export.csv?loop=glucose` gains the
  four new columns (appended; frozen order). An injection auto-resumes a
  paused sim, same rule as eating.
  ✅ *Checkpoint: beta off, sugary drink, 4 U — I watch delay, peak, and
  landing on the projector; the syringe box glows while beta stays dark.*
- **M13 — The type 1 day, one click.** Scenario button "Type 1 morning"
  (beta cells off, exercise off, 16× — the fasted climb starts; the class
  takes it from there with basal, breakfast, boluses) and a "Juice box
  (15 g)" fast-carb rescue button beside the meal buttons — the classic
  hypo treatment, for when a dose runs long. Glucose readout gets status
  coloring (in-band / HYPO below 70, severe below 54 / HYPER above 180) so
  the state of the patient is legible from the back row.
  ✅ *Checkpoint: one click starts the type 1 morning; I rescue a real hypo
  with the juice box; the full lesson runs start to finish on the
  projector.*

**STOP at the end of this phase and wait for my confirmation before
Phase 4.** (Phase 4 candidates, decided then: named disease presets,
water/ADH loop, closed-loop pump — rebuilding the feedback automatically,
the perfect callback — scenario challenges, game layer.)

## 5 — Notes / data products

- **New frozen glucose fields** (units in comments, same discipline as
  Phase 2): `injected_insulin` (0..1 activity), `total_insulin` (0..1,
  what the body responds to), `iob_units` (U outstanding), `basal_rate`
  (U/h). Charts, CSV, and future layers read these from history — nothing
  derived only in JS.
- **`sim.doses()` is the bolus event log** — plain dicts, `{"t", "units"}`,
  cleared by `reset()`. `/state` for the glucose loop carries it so the
  charts can mark injections; the CSV keeps per-tick truth.
- **Server actions**: `inject` (positive units, server-clamped to a sane
  single-dose max ~15 U), `basal` (value from the allowed set), both
  glucose-loop-only (400 on temp, as `eat` does). Scenario `t1_morning`
  follows the existing scenario pattern (set state, force speed, resume —
  never reset).
- **Regression guards are the contract's teeth**: Phase 3 adds fields, so
  the Phase 2 guard hashes the *Phase 2 subset* of each record from the
  scripted no-injection run — proving old behavior is untouched while the
  shape grows. The thermo hash from M6 stays as-is.
