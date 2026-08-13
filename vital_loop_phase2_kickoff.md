# Vital Loop — Claude Code Kickoff Prompt
### Phase 2: The blood glucose loop — antagonistic hormonal control

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M5 are committed, the
standing kit exists (`verify.py`, `run.bat`, `tests/test_invariants.py`,
port 5083), and lead with any open bugs logged there. Phase 1's code is
**extended, never rebuilt** (CLAUDE.md standing rule 3). The working
agreement in `~/.claude/CLAUDE.md` still governs: explain before doing,
small runnable increments, STOP at the phase checkpoint, patch with decimal
milestones, commit per milestone, append to `BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Phase 2 adds the second homeostatic loop: **blood glucose**, regulated by the
antagonistic hormone pair insulin/glucagon. That pair is the new teaching
point — thermoregulation showed one controller pushing back against
disturbance; glucose shows **two opposing effectors holding a set point from
both sides** (and what diabetes looks like when one side fails). Same
priorities as Phase 1: biology right > loop structure explicit > aesthetics.
Same classroom constraints: one double-click, hard to wedge, curriculum
vocabulary exact.

## 2 — Locked-in design decisions

(Chosen as my recommendations after the interview questions went unanswered —
flagged here so they're easy to revisit before M6 starts. The rest carries
over from Phase 1 unchanged.)

- **UI: loop switcher.** One loop on screen at a time; a tab control at the
  top switches between Temperature and Glucose. Both sims run independently
  underneath — switching tabs never resets anything.
- **Set point: 90 mg/dL.** Curriculum-standard fasting glucose. The healthy
  band shown on the chart is 70–110 mg/dL; hypo/hyper thresholds 70 and 180.
- **Disturbances: meals, exercise, fasting.** "Eat" delivers a carb bolus
  absorbed from the gut over sim-minutes; scenario buttons contrast a
  sugary drink (fast absorption) with a balanced meal (slow); exercise
  makes muscles burn glucose (the same toggle concept as Phase 1); a
  fasting scenario runs hours of no intake so glucagon's side of the loop
  is visible. **Insulin-injection dosing is deferred** (Phase 3 candidate).
- **Break the loop: cells as parts.** Toggles disable beta cells (no
  insulin), alpha cells (no glucagon), and the liver's response. Type 1
  diabetes *emerges* from switching beta cells off — no named disease
  modes in the UI. A labeled "Type 1" preset is a Phase 3 candidate.
- **Antagonistic control is modeled, not faked.** Insulin and glucagon are
  separate controller outputs with their own thresholds/gains, driving
  separate effectors (muscle/fat uptake + liver storage vs liver release).
  No single signed "hormone" variable — the whole point is two hands.
- Deterministic fixed-timestep, engine purity, history-as-data-product,
  sandbox-no-win/lose: all unchanged from Phase 1.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. The
glucose loop gets its own engine module (`engine/glucose.py`) reusing the
generic controller shape from `engine/sim.py` — extend, don't rebuild.

## 4 — Milestones

Continue Phase 1's numbering. Each milestone ends runnable; a milestone is
only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M6 — Glucose invariants + engine + console demo.** FIRST extend
  `tests/test_invariants.py` with the glucose contract (mirroring how M0
  froze M1's): `engine.glucose.GlucoseSimulation`, `SET_POINT = 90.0`,
  frozen record fields (`t, glucose, gut_carbs, exercise, error, insulin,
  glucagon, uptake, liver_flux, beta_enabled, alpha_enabled, liver_enabled,
  sensor_enabled`), determinism, and the pinned physiology: (a) resting
  fasted body holds 90 ± 15 mg/dL; (b) a 60 g-carb meal peaks glucose
  between 110 and 180 and returns to within 70–110 in ≤ 3 sim-hours;
  (c) **beta cells disabled + meal → glucose rises above 180 and stays
  there** (no secret uptake — the type 1 signature); (d) **alpha cells
  disabled + 12 h fast → glucose falls below 70** (no secret liver rescue);
  (e) engine purity. Then build the engine to that contract and a console
  demo (`python -m engine.glucose_demo`): meal story in numbers.
  ✅ *Checkpoint: demo table shows meal spike → insulin response → return
  to band; all invariants pass.*
- **M7 — Loop switcher + glucose charts.** Tab control (Temperature |
  Glucose); glucose page shows strip charts: blood glucose (healthy band
  70–110 shaded, set-point line at 90, hypo/hyper lines) and a
  hormones/effectors panel (insulin, glucagon, and net liver flux).
  Server runs both sims; `/state?loop=` picks which one the page reads.
  The temperature loop must behave exactly as in Phase 1 — switching back
  shows it undisturbed.
  ✅ *Checkpoint: I flip between loops mid-run and both are live and
  independent.*
- **M8 — Glucose disturbances.** "Eat a meal" button (60 g), scenario
  buttons "Sugary drink" (fast carbs) and "Balanced meal" (slow), exercise
  toggle wired to muscle glucose burn, and a "Skip meals (fast 12 h)"
  scenario. Gut-carbs-remaining readout so absorption is visible.
  ✅ *Checkpoint: sugary drink spikes fast and high; balanced meal is a
  rounded hill; exercise pulls the curve down; fasting shows glucagon
  holding the floor.*
- **M9 — Glucose loop diagram.** Second SVG diagram, same live-glow
  machinery: Stimulus (blood glucose changes) → Receptor (pancreatic islet
  cells) → Control center (pancreas: beta cells / alpha cells as two boxes
  — the antagonistic pair explicit) → Effectors (muscle & fat uptake,
  liver store/release) → Response (glucose removed from / added to blood)
  → negative-feedback return. Insulin and glucagon arrows visibly oppose.
  ✅ *Checkpoint: a meal lights the beta→uptake path; fasting lights the
  alpha→liver path.*
- **M10 — Break the glucose loop + CSV.** Toggles: beta cells, alpha
  cells, liver response, glucose sensors. Broken parts gray out dashed in
  the diagram; `/export.csv?loop=glucose` exports the glucose run with its
  frozen columns. The class watches type 1 diabetes emerge: beta cells
  off + sugary drink → hyperglycemia that never comes down.
  ✅ *Checkpoint: the M6(c) and M6(d) failures are visible on the
  projector, and both loops' CSVs open in a spreadsheet.*

**STOP at the end of this phase and wait for my confirmation before
Phase 3.** (Phase 3 candidates, decided then: insulin-injection dosing,
named disease presets, water/ADH loop, scenario challenges, game layer.)

## 5 — Notes / data products

- **Glucose history mirrors Phase 1's discipline**: tick-by-tick records
  behind `history()` with the frozen field names above; charts, CSV, and
  any future layer read that one source. Units: mg/dL for glucose,
  dimensionless 0–1 for hormone activity, mg/dL·min for fluxes.
- **The two-sim server must stay deterministic per sim.** One `Runner` per
  loop; lazy ticking as in Phase 1. Pausing/speed applies per visible loop
  or globally — pick the simpler implementation and log the choice in
  BUILDLOG.
- **Regression guard**: an invariant should pin that the thermoregulation
  engine's scripted-run history is unchanged by Phase 2 (byte-identical
  records for the M0 determinism script) — proof that extending didn't
  quietly rebuild.
