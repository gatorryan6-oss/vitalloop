# Vital Loop — Claude Code Kickoff Prompt
### Phase 5: Disease presets — naming the broken loops

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M16 are committed
(four phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Earlier phases are **extended, never rebuilt** (CLAUDE.md standing
rule 3). One deliberate contract amendment is sanctioned below (§5): the
Phase 1 thermo regression guard changes its COMPUTATION from full-record
hashing to subset hashing so the thermo record can grow — the pinned hash
VALUE must not change, which proves the recorded values didn't either.
The working agreement in `~/.claude/CLAUDE.md` still governs: explain
before doing, small runnable increments, STOP at the phase checkpoint,
patch with decimal milestones, commit per milestone, append to
`BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Phase 2 refused to put disease names in the UI on purpose: type 1 had to
*emerge* from a broken mechanism before it earned a label. Four phases
later the students have seen every mechanism — so Phase 5 finally names
them. One-click presets configure a loop into a named disease and say, in
curriculum vocabulary, WHICH box broke: **fever** (set point shifted — the
loop is working, defending the wrong number), **heat stroke** (effector
failure), **hypothermia** (effector overwhelmed), **type 1 diabetes**
(control-center cells dead), **type 2 diabetes** (target tissues deaf to
the signal). Five diseases, five different loop diagnoses — the phase's
thesis is that *disease names are loop diagnoses*. Same priorities as
ever: biology right > loop structure explicit > aesthetics.

## 2 — Locked-in design decisions

(Chosen as my recommendations — the interview question went unanswered,
Phase 2 precedent — flagged for easy revisit before M17 starts. Everything
not listed carries over from Phases 1–4 unchanged.)

- **All five presets ship**, requiring two small engine extensions:
  - **Fever = a raised set point, not a broken loop.** The thermo engine
    gains `set_fever(offset_c)` (default 0): the hypothalamus defends
    `SET_POINT + offset`. `Simulation.SET_POINT` stays 37.0 — the class
    constant the lesson hangs on is untouched; fever is a runtime shift,
    exactly like the biology (pyrogens move the thermostat). The freaky
    facts must emerge: chills while already hot (shivering on the way UP
    to 39) and sweating while cooling (breaking fever).
  - **Type 2 = insulin resistance.** The glucose engine gains
    `set_insulin_sensitivity(s)` (0 < s ≤ 1, default 1.0): every insulin
    action — tissue uptake, liver suppression, the paracrine brake —
    scales by `s`. The signature must emerge: insulin HIGH and glucose
    HIGH at once (the beta cells shouting at deaf tissues), fasting
    glucose parked above the healthy band, meals tall and slow. The
    paracrine brake weakening with `s` is real type 2 alpha-cell
    dysfunction, kept on purpose.
- **A preset is a complete diagnosis, not a delta.** Each button sets the
  WHOLE loop configuration (every breaker, offset, sensitivity — and the
  disturbances it needs, e.g. heat stroke sets the hot room + exercise):
  presets never stack, so the classroom can never wedge into "type 1 plus
  type 2 with fever". Presets never reset the run — the class watches the
  transition happen in the charts. A **"Healthy"** button per loop is the
  sixth preset: everything restored (room temperature stays where the
  slider is — recovery cures the body, not the weather).
- **Names are app-level; mechanisms are engine-level.** The engine knows
  offsets and sensitivities, never the word "diabetes" (nothing there
  special-cases a disease — Phase 2's rule, still absolute). The server
  Runner holds `preset` (name or none), returned in `/state`, cleared by
  reset or Healthy. A banner on each loop page shows the active disease
  and its one-line loop diagnosis in curriculum terms. Manual breaker
  flips do NOT clear the banner — the teacher is dissecting the disease,
  not curing it.
- **The record grows, one field per engine** (deliberate amendments, M17
  first): thermo gains `fever_offset` (°C); glucose gains
  `insulin_sensitivity` (0..1). Downstream reads them from history — the
  diagram's set-point label and the muscle box's response dim honestly.
- **Per-preset sim speed.** Fever and the diabetes pair develop over
  sim-hours → 16×; heat stroke and hypothermia are minutes-scale → 4×.
  The preset table carries its own speed, like scenarios always have.
- **Sandbox stays sandbox.** A disease is a configuration, not a level.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. Fever
lives in `engine/sim.py`, sensitivity in `engine/glucose.py`; presets are
a server-side table in `app.py` applied through the engines' public API —
one new `/control` action `preset`.

## 4 — Milestones

Continue Phase 4's numbering. Each milestone ends runnable; a milestone is
only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M17 — Disease physiology + contract + console demo.** FIRST amend
  `tests/test_invariants.py`: thermo record gains `fever_offset`, glucose
  gains `insulin_sensitivity`; the thermo guard (k) switches to hashing
  the Phase 1 field subset — its pinned VALUE must stay
  `9c83fe86…` exactly, which proves the change is shape-only; the Phase
  2/2+3 glucose subset guards likewise exclude the new field and keep
  their values. New pinned physiology: (a) **fever holds its number** —
  `set_fever(2.0)` in a 22 °C room settles core at 39 ± 0.5 within
  2 sim-h and HOLDS it (the loop still regulates); (b) **chills going
  up** — during fever onset there is a stretch with core ABOVE 37 and
  shivering active; (c) **sweats coming down** — clear the fever and
  there is a stretch with core above 37 and sweating active while core
  falls back; (d) **type 2 signature** — sensitivity 0.3, fasted 8 h:
  glucose settles above 110 WITH insulin at 0.4+ (contrast with type 1's
  zero insulin is the diagnostic lesson); a 60 g meal peaks above 200
  and is still above 110 three hours later; (e) API validation (offset
  any real, sensitivity in (0, 1]); (f) determinism with both new
  controls exercised; (g) regression — offset 0 and sensitivity 1.0
  leave every existing hash untouched. Then build both extensions and
  `python -m engine.disease_demo`: fever story then type 2 story, in
  numbers, with the type 1 columns printed alongside type 2 for the
  contrast.
  ✅ *Checkpoint: demo shows chills at 38 °C and a type 2 body with both
  numbers high; all invariants pass.*
- **M18 — The preset buttons.** "Diseases" card on each loop page: Fever,
  Heat stroke, Hypothermia + Healthy (temperature); Type 1, Type 2 +
  Healthy (glucose). `/control` action `preset` applies the full
  configuration server-side from one table (each entry: engine settings,
  disturbances, speed, banner line) and stores the active preset name;
  `/state` carries it; reset clears it. The banner strip renders the
  disease name + its one-line loop diagnosis on the page.
  ✅ *Checkpoint: I click Type 2 mid-run and watch the transition — no
  reset, banner up, insulin and glucose both climbing; Healthy brings it
  home.*
- **M19 — Diagrams tell the diagnosis + the taxonomy moment.** The
  thermo control-center box shows the LIVE set point (39.0 °C under
  fever — the number the loop is defending, read from `fever_offset` in
  the record); the glucose muscle/liver response dims by
  `insulin_sensitivity` so type 2's "shouting at deaf tissues" is
  visible: beta box bright, muscle box dim. Final projector pass: walk
  all five diseases + both Healthy recoveries end to end; the banner's
  five diagnoses read as the taxonomy (shifted set point / broken
  effector / overwhelmed effector / dead controller / deaf tissues).
  ✅ *Checkpoint: every preset tells its story on the projector without
  touching a breaker by hand; the five banners together form the "five
  ways a loop fails" summary slide the unit ends on.*

**STOP at the end of this phase and wait for my confirmation before
Phase 6.** (Phase 6 candidates, decided then: water/ADH loop, scenario
challenges, game layer.)

## 5 — Notes / data products

- **New frozen fields**: thermo `fever_offset` (°C, 0.0 = no fever);
  glucose `insulin_sensitivity` (0..1, 1.0 = healthy). Both flow to CSV
  (appended columns) and `/state` like every other field.
- **Guard arithmetic, spelled out**: converting guard (k) to subset
  hashing over exactly the original Phase 1 field set serializes
  today's records identically to the current full-record hash (the
  subset IS the full set today), so the pinned value `9c83fe86…` must
  still pass BEFORE the engine grows — run the suite between the test
  amendment and the engine edit to prove it. If that value ever needs
  re-recording, something actually changed: stop and say so.
- **The preset table is the single source** for what each disease means
  mechanically (settings + speed + banner line). The buttons, the banner,
  and any future quiz layer read that table — no disease logic in JS.
- **Engine purity holds**: no disease names in `engine/`; `set_fever`
  and `set_insulin_sensitivity` are physiology knobs any future scenario
  can also use.
