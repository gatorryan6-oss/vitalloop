# Vital Loop — project memory

**Read `BUILDLOG.md` before doing anything.** It is the single source of truth
for project state: which milestones are committed, what's deferred, and what
bugs are open. Do not rely on conversation history for any of that.

## What this repo is

An in-class teaching sandbox where students watch a homeostatic
negative-feedback loop work in real time — and break it on purpose. Phase 1 is
one loop, thermoregulation: a simulated body holds core temperature near
37 °C while the student disturbs it (cold room, hot day, exercise) and can
disable individual effectors to watch control fail. The full spec is
`vital_loop_v1_kickoff.md` — read it before proposing changes.

**Priorities in order: the biology must be right > the loop structure must be
explicit on screen > aesthetics.** It runs on the teacher's machine projected
to the class: one double-click to launch, hard to wedge, curriculum vocabulary
(stimulus, receptor/sensor, control center, effector, response, set point,
negative feedback) used exactly.

## Standing rules

1. **A milestone is not done until verification passes.** Before declaring any
   milestone complete: run `python verify.py` (smoke test) and
   `python -m pytest tests/test_invariants.py -q` (architecture checks).
   Both must pass on THIS machine — "the code looks right" doesn't count.
2. **Append to `BUILDLOG.md` at the end of every milestone.** Entry format is
   in that file's header. Log deferrals and open bugs there the moment they
   appear — that is how they survive to the next session.
3. **Extend earlier phases, never rebuild them.** If an earlier phase's code
   seems wrong, say so and stop; don't quietly rewrite it.
4. **Patch, don't regenerate.** Gaps become decimal milestones (M2.5),
   inserted when the build reaches that point. Never rewrite the kickoff
   mid-build.
5. **Commit at every milestone** so any change rolls back cleanly.

## Architecture invariants

Enforced as tests in `tests/test_invariants.py`. If a test blocks something
you're trying to do, the test is right until the human says otherwise. The
test file's docstring is also the frozen CONTRACT for the engine API — build
M1 to match it, don't bend it to match M1.

- **Set point is 37.0 °C.** The number the whole lesson hangs on.
- **Deterministic, fixed-timestep.** Same inputs → byte-identical history, so
  a demo rehearsed at home behaves identically in class. Nothing in the
  engine may read the clock or use randomness.
- **No feedback → no homeostasis, in the model, not just the UI.** Disabling
  all effectors must let a cold room drive core temp monotonically down.
  No secret stabilizers, no clamping that fakes control.
- **Run history is a data product, not a picture (kickoff §5).** The engine
  keeps tick-by-tick history behind `sim.history()`, returning records with
  the FROZEN field names listed in the invariants file. Strip charts, CSV
  export, and any future quiz layer all read this one source. Never compute
  something only inside the JS.
- **Engine purity.** `engine/` imports no web framework — the model stays
  testable without starting a server.
- **Loop-agnostic where cheap.** The engine models "a controlled variable
  with a set point, sensors, a controller, effectors" with thermoregulation
  as the first instance. Don't over-abstract, but don't weld "temperature"
  into the controller — glucose arrives in Phase 2.
- **Sandbox, no win/lose.** No score, no fail state in Phase 1. A
  game/challenge layer is deferred, not forgotten.

## Layout

```
app.py                  Flask app: routes, ticking loop, /state JSON (M2)
engine/                 the pure core — no Flask, no Jinja
  sim.py                Simulation: model + controller + effectors (M1)
  demo.py               console demo: python -m engine.demo (M1)
templates/  static/     the page, hand-drawn SVG + vanilla JS (M2-M5)
tests/test_invariants.py   §2's locked decisions, as checks (M0)
verify.py  run.bat      standing kit — smoke test and one-click launch
```

## How to run

- `run.bat` — one double-click; launches the Flask app on **port 5083**, then
  open http://127.0.0.1:5083/. Until M2 there is no app yet and run.bat says
  so plainly instead of erroring.
- `python -m engine.demo` — (from M1) console demo: cold-room story in numbers.
- `python verify.py` — smoke test: starts the server if needed, hits it,
  checks for the `Vital Loop` identity marker. It reuses an already-running
  server ONLY if that server started after the last edit to anything in
  `SERVED_SOURCES`; otherwise it FAILS by name rather than green-lighting
  stale code. `python verify.py --restart` replaces a stale one. Before M2
  (`app.py` absent) it passes vacuously, by design.
- `python -m pytest tests/test_invariants.py -q` — the architecture checks.
  Tests whose inputs don't exist yet SKIP with the milestone that arms them.
- Dependencies: `pip install -r requirements.txt` (flask, pytest).

Port 5083 is this project's dedicated port. Taken by other projects on this
machine: 5000 (FieldStop), 5050 (Statecraft), 5055 (Garage Lab), 5057 (CFB
Sim), 5077 (Chaos), 5078 (Tsunami), 5079 (TERRANE), 5080 (THE PIT), 5081
(Cooking Sim), 5082 (MCAS Bio Drill), 8000, 8501 (options pricer), 8503
(cipher), 8504 (Placer). Do not collide.
