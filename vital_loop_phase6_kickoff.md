# Vital Loop — Claude Code Kickoff Prompt
### Phase 6: The water/ADH loop — osmoregulation, and the effector that is a behavior

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M19 are committed
(five phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Earlier phases are **extended, never rebuilt** (CLAUDE.md standing
rule 3) — the water loop is a NEW engine module and a NEW tab riding the
existing kit (Runner, chart kit, breaker pattern, preset table, CSV
plumbing); it touches no earlier engine. The working agreement in
`~/.claude/CLAUDE.md` still governs: explain before doing, small runnable
increments, STOP at the phase checkpoint, patch with decimal milestones,
commit per milestone, append to `BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

The third homeostatic loop: **plasma osmolarity**, held near 290 mOsm/L by
antidiuretic hormone (ADH) and thirst. Two new teaching points earn this
loop its phase. First, **one of the effectors is a behavior**: the kidneys
(under ADH) can only SLOW water losses — no organ can create water — so
the loop's other arm reaches out through thirst and makes the organism
drink. Second, the response arms are staged like Phase 1's cheap-first
ordering: ADH engages at a lower osmolarity than thirst — conserve first,
drink second. And the loop carries the great naming story: diabetes
INSIPIDUS (tasteless urine, a broken water loop) versus diabetes MELLITUS
(honey-sweet urine, the broken glucose loop the class already knows) —
same word "diabetes" (siphon), because both flood the chamber pot. Same
priorities as ever: biology right > loop structure explicit > aesthetics.

## 2 — Locked-in design decisions

(Chosen as my recommendations, Phase 2 precedent — flagged for easy
revisit before M20 starts. Everything not listed carries over unchanged.)

- **Model: a two-pool budget** — body water (liters, ~40 L) and total
  solutes (mOsm, ~11,600); osmolarity = solutes / water. Set point
  290 mOsm/L, healthy band 285–295 on the chart, danger lines at 275
  (water intoxication / hyponatremia) and 305 (dehydration).
- **Controller thresholds are staggered, like real physiology**: ADH
  rises from ~285 (full by ~295); thirst only wakes above ~293. The
  hormone is the cheap response; the behavior is the expensive one.
- **Drinking is an automatic effector with a supply line.** When thirst
  crosses a threshold and the gut isn't already full, the body drinks a
  deterministic 250 mL (absorbed over minutes, like eat()). Its
  break-the-loop toggle is **water access** — the behavioral arm is the
  only effector that needs the ENVIRONMENT to cooperate, and "stranded
  without water" is its failure mode. Manual drink buttons exist too
  (a glass, a liter, way too much) as disturbances.
- **Four breakers, four different boxes**: osmoreceptors (sensor), ADH
  release (control center / posterior pituitary — central diabetes
  insipidus emerges), kidney response to ADH (the tissue is deaf —
  NEPHROGENIC diabetes insipidus, the type-2-style failure the class
  has already met), and water access (the behavioral arm).
- **The urine tells the story on screen**: urine flow (mL/min) and urine
  concentration are both charted — concentrated-and-scant versus
  dilute-and-flooding is how the kidney's obedience to ADH is SEEN.
  Full-ADH flow ~0.5 mL/min; zero-ADH flow ~12 mL/min (DI patients
  really do pass 15+ liters a day).
- **Disturbances**: drink buttons (250 mL / 1000 mL / 3000 mL — the last
  one dips osmolarity below 280 and the kidneys visibly dump dilute
  urine), a salty snack (solute bolus), an exercise/heat toggle (sweat:
  hypotonic loss — water leaves faster than solute, osmolarity climbs),
  and scenarios "A day in the desert" (sweat on + water access off +
  16×) and "Water-drinking contest" (3 L fast).
- **Disease presets ride the Phase 5 table**: Central DI (ADH release
  off — and the class watches thirst COMPENSATE: osmolarity holds
  near-band while intake and urine both flood, the classic
  "DI is survivable if you can drink" story), Nephrogenic DI (kidney
  deaf, ADH high and ignored), Healthy again. SIADH (ADH stuck high) is
  DEFERRED — it needs an override knob; logged as a Phase 7 candidate.
- **Loops stay independent.** The glucose loop's renal spill above 180
  is the true cause of mellitus polyuria, but cross-loop coupling breaks
  the one-Runner-per-loop architecture; the connection is told in a
  banner line, not simulated. Deferred, deliberately.
- **Timescale**: hours, like glucose. Default chart window 4 sim-hours;
  scenarios run 16×.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. New
pure module `engine/water.py` (`WaterSimulation`, `SET_POINT = 290.0`)
reusing the budget discipline; third Runner ("water"), third tab, third
diagram from the same kit. New `/control` actions `drink` and `salty`,
water-loop-only, mirroring `eat`.

## 4 — Milestones

Continue Phase 5's numbering. Each milestone ends runnable; a milestone is
only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M20 — Water invariants + engine + console demo.** FIRST extend
  `tests/test_invariants.py` with the water contract: API
  (`WaterSimulation`, `SET_POINT == 290.0`, `step/reset/state/history`,
  `drink(ml)`, `eat_salt(mosm)`, `set_exercise`,
  `set_effector_enabled(name)` for `{"adh","kidney","access"}`,
  `set_sensor_enabled`, `drinks()` event log with `{"t","ml","auto"}`),
  frozen record fields (`t, osmolarity, water_liters, gut_water,
  exercise, error, adh, thirst, urine_rate, urine_osm, adh_enabled,
  kidney_enabled, water_access, sensor_enabled`), and pinned physiology:
  (a) resting with water access, 12 h holds 290 ± 5 (auto-drinking does
  the work — the loop closes through behavior); (b) **water access off →
  dehydration** — osmolarity climbs past 305 with urine flow pinned near
  the floor (ADH conserving, and conserving is not enough: no secret
  water); (c) **central DI compensates** — ADH off WITH water access:
  6 h stays under 300 while total urine output exceeds 3 L (flooding
  AND surviving); (d) **layered failure** — ADH off AND access off →
  osmolarity passes 305 at least twice as fast as (b); (e) **the
  overhydration reflex** — a 3 L chug drives osmolarity below 280, ADH
  to ~0, urine flow above 8 mL/min with urine_osm under 150, and back
  inside 285–295 within 6 h; (f) staged thresholds — there is a sensed
  range where ADH > 0.3 while thirst == 0; (g) determinism, engine
  purity, and the three existing regression hashes untouched. Then the
  engine and `python -m engine.water_demo`: salty lunch → conserve →
  drink → chug → flood → desert → rescue, in numbers.
  ✅ *Checkpoint: the demo table shows urine swinging concentrated-scant
  to dilute-flooding as ADH moves; all invariants pass.*
- **M21 — Third tab + charts + disturbances + CSV.** Water tab wired to
  its own Runner (`/state?loop=water`); readouts (osmolarity, body
  water L); chart panels: osmolarity (285–295 band, set point, 275/305
  lines), ADH + thirst (0–1), urine flow (mL/min), urine concentration
  (mOsm/L); drink markers from `drinks()` (auto-drinks drawn
  distinguishably from manual ones); disturbance card (three drink
  buttons, salty snack, exercise toggle, both scenarios);
  `/export.csv?loop=water` with the frozen columns.
  ✅ *Checkpoint: I chug 3 L on the projector and watch ADH die and the
  urine chart flood dilute; the desert scenario parches the body live.*
- **M22 — Break the loop + the third diagram.** Breaker card
  (osmoreceptors, ADH release, kidney response, water access) with the
  usual status colors and grayed-dashed diagram parts. Third SVG
  diagram: Stimulus (osmolarity changes) → Receptor (osmoreceptors) →
  Control center (hypothalamus → posterior pituitary, releases ADH) →
  Effectors: Kidneys (retain water) AND Thirst → drinking, drawn
  visibly as a BEHAVIOR (its own visual treatment and an arrow that
  passes through the outside world) → Response → feedback return.
  ✅ *Checkpoint: I break the kidney and watch ADH scream at a deaf
  organ — high hormone line, flooding urine — the type 2 pattern in a
  new loop, visible in the diagram.*
- **M23 — The two insipidus presets + the naming story.** Diseases card
  on the water page: Central DI, Nephrogenic DI, Healthy again — table
  rows in the Phase 5 preset table, banners telling WHICH box broke and
  the insipidus/mellitus naming story ("both siphons — one tasteless,
  one sweet"). Full projector pass: healthy day → central DI
  (compensating through the water bottle) → nephrogenic DI (hormone
  ignored) → desert on top of DI (the killer combination) → healthy.
  ✅ *Checkpoint: all three loops now run the same lesson grammar —
  disturb, break, name — and the water page's banners complete the
  three-loop disease taxonomy.*

**STOP at the end of this phase and wait for my confirmation before
Phase 7.** (Phase 7 candidates, decided then: scenario challenges, game
layer, SIADH + an ADH-override knob, cross-loop coupling.)

## 5 — Notes / data products

- **Frozen water record fields** (units in comments, same discipline):
  osmolarity (mOsm/L), water_liters (L), gut_water (mL not yet
  absorbed), adh/thirst (0..1), urine_rate (mL/min), urine_osm
  (mOsm/L, derived from solute excretion / flow — recorded, never
  computed in JS).
- **`drinks()` is the intake event log** — `{"t", "ml", "auto"}`, auto
  vs manual distinguished so the charts can show the loop drinking by
  itself; cleared by reset(); carried in `/state` like `doses()`.
- **Solute bookkeeping is deliberately simple**: baseline solute intake
  and excretion cancel; salty snacks are boluses; sweat is hypotonic
  (loses proportionally more water than solute). Urine concentration is
  derived (excretion / flow) and that derivation lives in the ENGINE.
- **The preset table stays the single source** for the two DI entries;
  the engine never learns the word "insipidus".
- **Port 5083, identity marker "Vital Loop", both unchanged** — same
  app, third loop.
