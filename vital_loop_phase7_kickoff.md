# Vital Loop — Claude Code Kickoff Prompt
### Phase 7: Scenario challenges — the sandbox grows goals

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M23 are committed
(six phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Earlier phases are **extended, never rebuilt** (CLAUDE.md standing
rule 3) — challenges are pure APP-level machinery: a table, an evaluator,
one `/control` action, one card per page. **No engine file changes in
this phase at all.** The working agreement in `~/.claude/CLAUDE.md` still
governs: explain before doing, small runnable increments, STOP at the
phase checkpoint, patch with decimal milestones, commit per milestone,
append to `BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Six phases built a sandbox where every loop can be disturbed, broken, and
named. Phase 7 adds the exercise that makes students USE it: authored
challenges. A challenge sets the stage (a disease, a disturbance, a
missing part), states a goal in curriculum vocabulary, runs for a defined
stretch of sim time while the class manages the patient with the tools
the sandbox already has — and then reports honestly what happened,
computed from the run history: time in range, worst excursions, and
whether the goal was met. The three launch challenges each teach a
different meta-lesson: **when an effector fails, something else must
become the effector** (temperature); **being the control center is a
job** (glucose — the Phase 3 lesson, now with a report card); **when the
sensor lies, reading the data IS being the receptor** (water).

## 2 — Locked-in design decisions

(Chosen as my recommendations — flagged for easy revisit before M24
starts. Everything not listed carries over from Phases 1–6 unchanged.)

- **Challenges have success criteria; they still are not a game.** The
  Phase 1 lock ("no win/lose in Phase 1") deferred exactly this layer,
  and picking it now is the human's call to arm it. The report says MET
  or NOT MET per target, with the numbers — no points, no stars, no
  leaderboard, no fail screens. The game layer (if ever) stays a future
  phase.
- **Evaluation is server-side, from history** — the data-product rule
  applied to judgment: the report is computed from the engine's
  tick-by-tick records over the challenge window, by the app, never in
  JS. The strip charts and the report card can never disagree.
- **A challenge is: setup + duration + metrics + targets + story.** One
  server-side table (the Phase 5 preset pattern, again) is the single
  source. Setup reuses the preset/scenario machinery (full
  configuration, never a reset — the challenge window is stamped in sim
  time and the report reads exactly that window).
- **Integrity lines come free from the flags.** Every record carries the
  enabled flags, so the report can say "the pancreas was switched back
  on mid-shift" — toggling the broken part back during a challenge
  isn't forbidden, it's REPORTED. The class polices itself.
- **The three launch challenges:**
  1. **Cold-water rescue** (temp): shivering has failed (severe
     hypothermia does this for real) and the room starts at −10 °C.
     Goal: core back above 36.5 °C within the window and never below
     34. Levers: the room slider (the environment must become the
     effector) and exercise, carefully.
  2. **The type 1 shift** (glucose): beta cells gone, a 60 g breakfast
     lands at the start, 5 sim-hours. Goal: ≥ 75 % of the window in
     70–180 and never below 65. Levers: everything Phase 3–4 built —
     boluses, basal, juice boxes, even the pump (letting the machine do
     it and WATCHING the report improve is its own lesson). Integrity:
     beta cells must stay off.
  3. **Aid station** (water): a long hot effort with a lying sensor —
     osmoreceptors off, so thirst never fires and ADH sits frozen; the
     player drinks by the charts. Goal: osmolarity inside 280–300 for
     the whole 4 sim-hour window. Integrity: sensor stays off.
- **Per-challenge speed defaults 16×** (the windows are hours);
  pause/speed stay free — rehearsal and discussion beat racing a clock.
  The window is SIM time, so pausing to argue about the next dose is
  encouraged, not penalized.
- **One challenge at a time per loop**; starting a new one (or reset)
  replaces the old. The finished report stays on screen until then.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`.
`CHALLENGES` table + pure-Python evaluator functions in `app.py`;
`Runner` gains a challenge stamp (name, start, end, cached report);
`/control` gains a `challenge` action; `/state` carries progress and,
once the window closes, the report. The invariants file gains app-level
checks for the table's shape and the evaluator's arithmetic.

## 4 — Milestones

Continue Phase 6's numbering. Each milestone ends runnable; a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M24 — Challenge framework + the type 1 shift, end to end.** FIRST
  extend `tests/test_invariants.py` with the Phase 7 contract:
  (a) every `CHALLENGES` entry has the required keys (title, story,
  goal text, duration, setup, metrics) and a positive duration on a
  valid loop; (b) the evaluator is a pure function — fed a crafted
  record list it returns exact time-in-range percentages, extremes,
  and met flags (test the arithmetic, not the vibes); (c) integrity
  lines fire when a crafted history flips a guarded flag mid-window;
  (d) the engines are untouched (the three regression hashes already
  guard this — this milestone adds NO engine code). Then build the
  framework (table, evaluator, `/control challenge`, `/state` progress
  + report) and the glucose "Type 1 shift" challenge card: story, goal,
  Start button, live progress readout, report card with per-target
  MET/NOT MET rows and integrity lines.
  ✅ *Checkpoint: I start the shift, dose through breakfast, and when
  the window closes a report card tells me how my pancreas-work went.
  (Amended pre-M24 after a strategy sweep, logged in BUILDLOG: the spec
  first guessed the pump would ace the shift — the model says a
  cold-started pump with no meal announcement LOSES to a human dosing
  4–5 U with the meal, and a "helper bolus" stacks and makes the
  machine worse. That inversion is the better lesson, and the report
  card is how the class discovers it.)*
- **M25 — Cold-water rescue + Aid station + the full pass.** The other
  two challenge cards, sharing every part of M24's machinery. Final
  projector pass across all three loops: disturb → break → name →
  CHALLENGE, the complete lesson grammar; BUILDLOG records the phase
  closed.
  ✅ *Checkpoint: all three challenges run start to report on the
  projector; the temperature rescue is winnable with the room slider,
  the aid station is losable by trusting a dead sensor.*

**STOP at the end of this phase and wait for my confirmation before
Phase 8.** (Phase 8 candidates, decided then: game layer proper, SIADH
+ ADH-override knob, cross-loop coupling, student worksheets keyed to
CSV exports.)

## 5 — Notes / data products

- **The report is a data product**: computed server-side from
  `history()` records in the challenge window, cached on the Runner,
  delivered via `/state`. Anything a future layer wants (per-student
  comparisons, the game layer) reads THIS, never a screenshot.
- **The challenge table is the single source** (titles, stories, goals,
  durations, targets, integrity flags). The card, the report, and the
  tests all read it.
- **No engine changes, provably**: the three regression hashes plus
  engine-purity tests already pin it; the phase's own tests only touch
  app-level logic.
- **Metrics vocabulary matches the charts**: in-range windows use the
  exact thresholds already drawn (70–180 shading, 280–300, 36.5/34) so
  the report card and the picture always tell one story.
