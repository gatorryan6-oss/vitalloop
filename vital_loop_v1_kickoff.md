# Vital Loop — Claude Code Kickoff Prompt
### Phase 1: A live thermoregulation sandbox — one negative-feedback loop, visible and pokeable

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; set up
git early; patch gaps with decimal milestones (M4.5), never regenerate this
document mid-build. Project state lives in `BUILDLOG.md`, not chat history.

## 1 — What we're building (and why)

Vital Loop is an in-class teaching sandbox where students watch a homeostatic
negative-feedback loop work in real time — and break it on purpose to see why
it matters. Phase 1 covers one loop, thermoregulation: a simulated body holds
core temperature near 37 °C while the student disturbs it (cold room, hot day,
exercise) and can disable individual effectors (sweating, shivering,
vasodilation) to watch control fail. The priority order is: **the biology must
be right, the loop structure must be explicit on screen** (stimulus → sensor →
control center → effector → response), and only then aesthetics. It runs on
the teacher machine projected to the class, so it must launch in one
double-click and be hard to wedge.

## 2 — Locked-in design decisions

These were settled before this spec was written — don't re-litigate them.
(The last three were my recommendation accepted by default; if the user asks
to change one early, treat it as a scope change, not a redesign.)

- **Concept:** homeostasis negative-feedback loops. The "vital loop" is the
  control loop itself.
- **Audience:** the user's students, used live in class from the teacher's
  machine. Simple to launch, hard to break, curriculum-aligned vocabulary
  (stimulus, receptor/sensor, control center, effector, response, set point,
  negative feedback).
- **V1 shape:** open sandbox — sliders, toggles, live graphs. **No win/lose,
  no score in Phase 1.** A game/challenge layer is explicitly deferred to a
  later phase.
- **V1 content:** thermoregulation **only**. Blood glucose and water balance
  are deferred to Phase 2+ — but the engine must not hard-code "temperature"
  into its bones (see §5) so new loops slot in later.
- **Interface:** a live loop diagram that lights up as each component
  activates, **plus** scrolling strip-chart graphs of the key variables.
  Both views always visible; the diagram is the teaching object, the graphs
  are the evidence.
- **Stack:** Flask web app in the browser (Python engine server-side),
  matching the user's other projects and standing kit.
- **Simulation style:** deterministic, fixed-timestep. Same inputs → same
  curves, so a demo rehearsed at home behaves identically in class.

## 3 — Tech stack

- **Python 3 + Flask** — the sim engine stays in Python (the user's learning
  language) and the browser is just the display.
- **Vanilla JS + SVG in the browser** — the loop diagram and strip charts are
  hand-drawn SVG updated from polled JSON; no chart library, no build step,
  nothing to install beyond Flask.
- **Polling, not websockets** — the browser fetches `/state` a few times a
  second. Boring, debuggable, and plenty for a ~2 Hz classroom sim.
- **No database** — sim state and history live in memory; the history is
  exportable as CSV (see §5). A page reload mid-class must not lose the run:
  the engine lives in the server process, not the page.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M0 — Repo scaffolding.** Copy the standing files from my kit into the repo
  and configure them for this project: `CLAUDE.md` (project memory),
  `BUILDLOG.md` (seed the Current state section), `run.bat` (this project's
  launch line), `verify.py`, `tests/test_invariants.py` (encode §2's locked
  decisions as checks), `.claude/settings.json` (Sonnet pin + Stop hook).
  **Port: 5083.** (Surveyed on 2026-08-13: 5055, 5077–5082, 8501, 8503, 8504
  are taken by other projects on this machine.) Set it in `verify.py` (`PORT`)
  and `run.bat` so they always agree. **Identity marker:**
  `MUST_CONTAIN[0] = "Vital Loop"` — it must appear in this app's pages and no
  other project's. Leaving it empty is a failure, not a default.
  ✅ *Checkpoint: `python verify.py` passes, and the invariants tests run.*

- **M1 — The loop, in numbers.** Pure-Python engine, no web yet:
  `engine/` package with a fixed-timestep thermoregulation model — core temp
  state, heat gained (metabolism, environment, exercise) vs heat lost
  (radiation, sweating, vasodilation), a hypothalamus controller comparing
  core temp to the 37 °C set point, and effectors (sweat, shiver,
  vasodilate/constrict) each with an `enabled` flag. A demo script
  (`python -m engine.demo`) prints a table: drop the room to 5 °C at t=60 s
  and show core temp dip, effectors kick in, temp return toward set point.
  Invariant tests pin the physiology: at rest in a 22 °C room temp holds
  37 ± 0.5 °C; with **all effectors disabled** a cold room drives temp
  steadily down (no secret stabilizer); the sim is deterministic (two runs,
  identical output).
  ✅ *Checkpoint: I run the demo and watch the numbers tell the recovery
  story.*

- **M2 — It breathes in the browser.** Flask app: engine ticking in the
  server, one page titled "Vital Loop" with a scrolling strip chart of core
  temp (set-point line drawn in) and environment temp, updating live.
  Pause / resume / reset buttons and a sim-speed control (1× / 4× / 16× —
  class time is short).
  ✅ *Checkpoint: I double-click `run.bat` and watch the temperature trace
  hold at 37 °C.*

- **M3 — Disturb it.** Controls to push the system: environment temperature
  slider (−10 °C to 45 °C), exercise on/off (adds metabolic heat), and a
  couple of one-click scenario buttons ("Step into a freezer", "Run a mile on
  a hot day") that set both at once. Strip charts gain a second panel showing
  effector activity (sweat rate, shiver intensity) so cause and effect line
  up vertically on the same time axis.
  ✅ *Checkpoint: I drag the room to 5 °C and watch shivering spike and core
  temp recover on screen.*

- **M4 — The loop made visible.** The SVG loop diagram: labeled boxes for
  Stimulus → Receptor (skin/core thermoreceptors) → Control center
  (hypothalamus) → Effectors (sweat glands, muscles, skin vessels) →
  Response, with arrows closing the loop back to the stimulus. Each box and
  arrow lights up with intensity proportional to its live activity, driven by
  the same `/state` JSON as the graphs — the diagram is a live view of the
  running engine, never a canned animation. Curriculum vocabulary on the
  labels, exactly.
  ✅ *Checkpoint: I chill the room and watch activation flow around the loop
  in sync with the graphs.*

- **M5 — Break the loop.** Per-effector disable toggles (sweating off,
  shivering off, vasomotor off) and a "sensor damage" toggle that blinds the
  hypothalamus. Disabled parts gray out in the diagram; the graphs then show
  runaway temperature — the punchline of the whole unit: *no feedback, no
  homeostasis.* Add a "Export run (CSV)" button so a class run's data can go
  into a spreadsheet for graphing practice.
  ✅ *Checkpoint: I disable sweating on a hot day and watch hyperthermia
  develop, then export the CSV and open it.*

**STOP at the end of this phase and wait for my confirmation before Phase 2.**
(Likely Phase 2 candidates, decided then, not now: blood glucose loop,
water/ADH loop, authored scenario challenges, student-facing game layer.)

## 5 — Notes / data products

- **Run history is a data product, not a picture.** The engine keeps the full
  tick-by-tick history of every run in memory — time, core temp, environment
  temp, each effector's activity and enabled state, controller error — behind
  a clean accessor (`engine.history()` returning plain dicts/lists). The strip
  charts, the CSV export, and any future quiz/challenge layer all read from
  this one source. Never compute something only inside the JS.
- **The engine is loop-agnostic where cheap.** Model "a controlled variable
  with a set point, sensors, a controller, and effectors" as the general
  shape, with thermoregulation as the first concrete instance. Don't
  over-abstract — one working loop beats a framework — but don't weld the
  word "temperature" into the controller either, because glucose is coming
  in Phase 2.
- **Invariants worth encoding from day one** (in
  `tests/test_invariants.py`): set point is 37.0 °C; determinism (same
  inputs → same history); disabling all effectors removes all regulation;
  history accessor returns records with the frozen field names above;
  `verify.py`'s identity marker is `"Vital Loop"` and `PORT == 5083`.
