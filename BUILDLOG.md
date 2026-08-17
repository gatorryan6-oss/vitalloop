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

- **Committed:** M27 — Phase 8 underway. Specs: phases 1–7 as before,
  plus `vital_loop_phase8_kickoff.md` (M26–M30). The lesson grammar now
  runs disturb → break → name → challenge → score → RACE.
  Remote: https://github.com/gatorryan6-oss/vitalloop
- **Next up:** M28 — the diagnosis game: a `CASES` table per loop,
  server-side REDACTION while a case is live (no `*_enabled` flags in
  `/state`, breaker card and disease banner hidden, diagram boxes drawn
  "unknown" rather than grayed, CSV refused with a plain-English
  reason), an answer form in curriculum vocabulary, and a reveal that
  releases the full history. Assume a student opens devtools.
  Then M29 crisis, M30 the full pass.
  Deferred to Phase 9: per-student sessions, SIADH + ADH-override knob,
  cross-loop coupling (mellitus polyuria), student worksheets.
- **Port:** 5083 (this project's own; see CLAUDE.md for the machine registry).
- **Open bugs:** none.
- **Standing caution:** the invariants file froze the history record fields
  (kickoff §5) and the engine API before M1 exists. If M1's physiology
  genuinely can't satisfy a pinned behavior (e.g. monotone cooling with
  effectors off), show the human the conflict — don't loosen the test
  silently.

---

## Milestones

## 2026-08-16 — M27: Head-to-head
- Shipped: M27 contract in `tests/test_invariants.py` (label tidying and
  capping, compare purity + SYMMETRY, ties have no winner, row order
  preserved, leaderboard ordering/cap/scoping, tolerance of M26-era
  attempts). `clean_label` + a team box beside every Start button (the
  label rides the challenge stamp onto the attempt and shows on the
  progress clock and the verdict line while the run is live),
  `challenge_runs` / `leaderboard` in `/state`, `compare_attempts` +
  a read-only `GET /compare?loop&name&a&b`. UI: leaderboard table
  (rank, team, points, medal, verdict, when) and a head-to-head picker
  with two selects that repopulate ONLY when the set of runs changes —
  a 4 Hz poll must never yank the teacher's choice mid-sentence. 80
  invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The attempt grows `score_rows` + `zeroed`** (appended, so M26
     records still load). The side-by-side has to show WHERE a team won,
     which needs per-row points; the alternative was recomputing them
     from the stored rows at compare time. Rejected: kickoff SS5 says a
     future phase may swap the scorer for an honors section, and a
     recomputed breakdown would then silently disagree with the total
     the class was shown that day. What a run was worth THAT DAY is now
     part of the record. The compare tolerates their absence, pinned as
     a test, because run #1 in the real log predates them.
  2. **The comparison is computed server-side**, like the report card
     before it — `/compare` returns merged rows and winners, and the JS
     only draws. Keeps it testable in pytest, and honours the standing
     rule that nothing is computed only inside the JS.
  3. Row-winner rules: a row both teams scored the same is a TIE, not a
     win; a row with no points (the integrity lines) goes to whichever
     team was honest; the match goes to the higher total. Symmetry is
     pinned as a test — swap the teams and every winner must flip.
  4. Verified through the production routes: two teams ran the identical
     aid station, "Team 3" (250 mL every 15 min) scoring 100/GOLD and
     "Period 2 Red" (1 L at +1 h and +3 h) 66/bronze/not met, and the
     compare named the rows that decided it — time in band 60 vs 35.8
     and the high end 20 vs 10.3, with the overhydration row a genuine
     20-20 tie. All four click-the-wrong-thing refusals answer with a
     plain-English 400.
  5. VERIFIED LIVE in the browser on real wall-clock: typed the messy
     "  Period 2   Red  " into the team box, locked the door, rested 40
     min and worked the last 20 at 16x. The label came back tidied to
     "Period 2 Red", rode the live progress clock ("Period 2 Red — 0:42
     of 1:00 sim-hours") and the verdict line, and landed in the log as
     attempt #2 — 35.80 °C, NOT MET, 51/100, no medal. Leaderboard drew
     both runs (M26's unlabelled 83 first, shown as "(no team)"), the
     pickers defaulted to the two most recent AND survived 6 polls
     without losing the teacher's choice, and Compare drew the
     side-by-side naming where it was won. Console clean.
     Note the M26-era run has no `score_rows`, so in THAT pairing the
     points columns are blank on its side and the economy row falls back
     to a tie — the documented tolerance path, and it disappears as soon
     as both runs are M27-era (as the aid-station pipeline above shows).

## 2026-08-16 — M26: Points, medals, and the attempts log (Phase 8 starts)
- Shipped: Phase 8 contract in `tests/test_invariants.py` (scorer purity
  + exact arithmetic, out-of-100, integrity zeroing, medal ordering,
  scoring-key/evaluator-row agreement, attempts round-trip, missing +
  corrupt file, 500 cap, atomic write, loud write failure, frozen
  attempt fields, `data/` gitignored). `attempts.py` — load / append /
  atomic save, corrupt file MOVED ASIDE not overwritten. `score_report()`
  + a `SCORING` table (the twin of `EVALUATORS`), `medals` on each
  challenge, `build_attempt` / `log_attempt` / `best_attempt`, the
  finalize moved INSIDE the runner lock (two polls could otherwise log
  one run twice), `bests` + `attempts_error` in `/state`. UI: score line
  + medal chip on the report card, per-row `points / max` so the class
  sees WHERE the marks went, threshold line on each card, "best so far"
  strip, and a red line if a score failed to save. All 73 invariants +
  verify pass; the whole pipeline driven through the production routes
  for winning AND losing plays on all three challenges. VERIFIED LIVE in
  the browser on real wall-clock: locked the door, ran the hour at 16x,
  rested the first half and worked the second (with one short breather
  when the duty was about to cross the exhaustion cap) — GOAL MET,
  36.75 °C at the buzzer, 46% duty, **83 / 100 SILVER**, one point short
  of gold because the breather cost economy marks. Saved as run #1; then
  the app was KILLED AND RESTARTED and the card still read "Best so far:
  83 / 100 SILVER — 1 run so far", straight off the disk.
- Deferred: nothing. Team labels on attempts are M27 as specced (the
  field exists and is written as null).
- Open bugs: none.
- Decisions:
  1. **SWEEP FIRST, and it overturned two guesses** (kickoff SS2's rule).
     22 glucose strategies, 17 temperature, 15 water, all built only from
     moves the UI actually offers (no 5 U bolus — the buttons are 2/4/8).
     - *t1_shift*: an 8 U play that spent 81 % of the shift in range but
       bottomed out at **6.5 mg/dL** scored 60 with the first weights —
       a coma earning a bronze. The hypo line went from 25 to 35 points.
       Final: 4 U with the meal 91 (gold), 4 U + basal 0.5 87, split
       2+2 86, 4 U + a +2 h correction 86, 2 U + basal 85, 2 U alone 84,
       basal-only 72, a late 4 U 66; NOT MET tops out at 65 (basal 0.5),
       then 54 and 52 for the runs that went hypo, pump-from-cold 39,
       do-nothing 35. **The worst goal-met run (66) sits one point above
       the best goal-missed run (65)** — that gap is physiology, not
       tuning. Medals 85 / 72 / 60.
     - *cold_store*: nothing could score above 76 and a run ending at
       35.8 °C (hypothermic, NOT MET) tied the best legal run, because
       economy points paid out for resting. Fix: grade end-core tightly
       around the goal (35.5 → 36.2 instead of 34.0 → 36.5) and cut the
       economy row to 20. Final: 40 % duty 88, 45 % 84, 50 % 80 (MET);
       35 % 67, 30 % 63, 25 % 43, resting 20 (NOT MET). Medals 84 / 76 /
       60 — gold is the CHEAP rescue, spending the whole allowance is
       silver.
     - *aid_station*: six different drinking rhythms all held the band
       100 % of the window and all scored exactly 100 — nothing to
       compare in a head-to-head. Fix: grade the extremes to the SET
       POINT (285/295) rather than the band edge (280/300). Final:
       250 mL/15 min 100, /20 min 99, 1 L hourly 98, 1 L/45 min 96,
       /12 min 94; every over-pour misses a medal (3 L chug 58, 250 mL
       every 10 min 37). Medals 95 / 80 / 60.
     - Calibration criterion, verified in the sweep and worth keeping:
       **gold and silver are unreachable without MET**, and no run that
       went hypo, hypothermic, or overhydrated earns any medal. Bronze
       is the honest "you kept them alive but missed" tier.
  2. **The evaluator's rows grew `key` and `n`** (a slug and the raw
     number), appended the way the CSV columns have grown since M12. A
     scorer cannot grade prose — `"88% (target: at least 75%)"` — without
     a fragile regex, and recomputing from the records would put the
     physiology-reading in two places. The card on screen is unchanged,
     the UI ignores both fields, and the scorer stays a separate pure
     function reading the same rows (kickoff SS5).
  3. **A `hard` row kind**, one line in the table: going past the
     exhaustion cap zeroes the run like an integrity failure, because
     exercising 100 % of the hour isn't a bad play, it's not playing the
     challenge — that body physically couldn't. The sweep is what
     surfaced it (working the whole hour was outscoring legal plays).
  4. Ties on the leaderboard go to the EARLIER run: to take the top spot
     you have to beat it, not match it.
  4.5 **A bug in the first attempts.py, caught by testing the failure
     path instead of assuming it.** `load()` treated ANY read failure as
     corruption and moved the file aside — so a log merely LOCKED for a
     moment (antivirus, OneDrive, the teacher having it open in an
     editor) would have been renamed and the morning's scores lost over
     a transient error. Now the two cases are separate: content we read
     and can't parse is junk we've seen, so it's set aside and the class
     starts fresh; a file we could NOT read is left exactly where it is,
     `save()` refuses until it can be read, and the UI says so. Pinned
     as an invariant. Verified end to end by blocking the path with a
     directory: the run was still scored 38/100, the attempt came back
     None, `bests` stayed empty, the message reached `/state`, and the
     real log survived untouched.
  4.6 `attempts.py` added to verify.py's SERVED_SOURCES — it is app-level
     code the running server imports, so editing it can leave a live
     server stale exactly like editing app.py. Proven live: verify.py
     refused a stale server BY NAME ("started BEFORE the last edit to
     attempts.py") before `--restart` gave the PASS.
  5. `pytest.ini` added: this machine's shared pytest scratch dir
     (`%LOCALAPPDATA%\Temp\pytest-of-gator`, left by another project in
     July) is ACL-locked and `tmp_path` died with WinError 5 before any
     test ran. Basetemp now points at the repo's `.pytest_tmp/`, which
     M0's .gitignore already anticipated. Plain `python -m pytest` still
     needs no flags.

## 2026-08-15 — M25: Cold-store lock-in + Aid station (Phase 7 complete)
- Shipped: two more challenges on the M24 machinery — "Cold-store
  lock-in" (temp: −10 °C, shivering AND vessel control failed — severe
  hypothermia does both — exercise is the only heat and exhaustion
  caps it at 50% of the hour; integrity lines catch warming the room
  or re-enabling parts) and "Aid station" (water: osmoreceptors dead,
  runner sweating for 4 h, the class IS the receptor; the overhydration
  kill is a graded line). Both calibrated by sweep BEFORE pinning:
  cold store — resting ends 34.1 (fail), full-hour sprint blows the
  cap, 38–50% bursts win, wait-20-then-work ends 36.01 (knife-edge
  win); aid station — never-drink peaks 318 (fail), steady rhythms
  score 100%, the 3 L chug scores 76.9% (fail). Both verified through
  the production pipeline (winning and losing plays each) and armed
  live in the browser. ALSO: M24's live type 1 shift completed during
  this milestone through real wall-clock and real UI clicks — GOAL
  MET, 87% in range, lowest 76, beta stayed off; matches the sweep's
  88.5% prediction for the textbook play. 58 invariants + verify pass.
- Deferred: nothing. Phase 8 candidates under Current state.
- Open bugs: none.
- Decisions: evaluator info-rows (urine passed, highest glucose) carry
  no met flag on purpose — debrief numbers, not judgments.

## 2026-08-15 — M24: Challenge framework + the type 1 shift
- Shipped: Phase 7 contract (table shape, evaluator arithmetic on
  crafted histories, integrity-line firing), `CHALLENGES` table +
  pure-function `EVALUATORS` + `Runner.challenge` stamp + `/control
  challenge` + `/state` progress/report block (report computed ONCE,
  server-side, from the exact stamped window — a data product), the
  glucose "Type 1 shift" card (story/goal from the table via Jinja —
  one source), progress bar + clock, report card with ✓/✗/· rows and a
  MET / NOT MET verdict. Verified: pipeline driven end to end in
  Python through the production snapshot path (naive 4U+2U-correction
  play scored 70%/lo 64 — NOT MET, the stacking lesson as a report
  card); progress and report renderers verified live in the browser;
  56 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) SPEC AMENDMENT, pre-completion, logged not silent: the
  kickoff checkpoint guessed the pump would ace the shift; a 12-strategy
  sweep says a COLD-STARTED pump loses to a human dosing 4-5 U with the
  meal (60% in range, lo 63), and a "helper bolus" stacks it to lo 23 —
  this pump has no IOB awareness or meal announcements, so machines
  need run-in. The inversion is the better lesson; checkpoint text
  rewritten. (2) Targets validated by the sweep: 4U→88.5%, 5U→91.5%,
  basal-only→76.9% all MET; 6U (hypo 58), 4U+basal-1.0 (hypo 64),
  nothing (4.7%), pump-cold all NOT MET. Sloppy fails, textbook wins,
  exactly the grading a teacher wants. (3) A challenge start clears the
  disease banner — the challenge card owns the story.

## 2026-08-15 — M23: The two insipidus presets (Phase 6 complete)
- Shipped: water Diseases card (Central DI / Nephrogenic DI / Healthy
  again) as three rows in the Phase 5 preset table; banners carry the
  loop diagnosis AND the naming story (insipidus = tasteless, mellitus
  = honey-sweet, both "siphons"). Verified live end to end: Central DI
  → pituitary gray-dashed, urine flooding 12 mL/min, TWO auto-drinks
  logged and drawn green (the loop surviving on its behavioral arm),
  osm sawtooth ~293–294; desert layered ON TOP of DI → still flooding
  while dying of thirst, dehydrated past 305 in ~65 sim-min, banner
  still naming the disease; Nephrogenic → ADH on + kidney deaf +
  complete-diagnosis semantics clearing the desert; Healthy → machinery
  restored with osm 304.5, and the RESTORED loop drinks its own way
  home (no teleport — sandbox never cheats).
- Deferred: SIADH (needs an ADH-override knob) and cross-loop coupling
  → Phase 7 candidates, per the kickoff.
- Open bugs: none.
- Decisions: nothing new — the phase closed on the Phase 5
  architecture exactly as designed, three table rows and one banner
  div. That the third loop's disease layer cost ~40 lines is the
  payoff of names-in-the-table / mechanisms-in-the-engine.

## 2026-08-15 — M22: Water breakers + the third diagram
- Shipped: water breaker card (Osmoreceptors / ADH release / Kidney
  response / Water access) with the standard status colors and
  DISABLED labels + water CSV export link; third SVG diagram from the
  same kit — Stimulus → Osmoreceptors → Hypothalamus/posterior
  pituitary (ADH) → Kidneys AND "Thirst → drinking", the second
  effector role-labeled "EFFECTOR — A BEHAVIOR" with the caption
  "drinking reaches through the OUTSIDE WORLD — no other effector
  does". Kidney box glows with how loudly it OBEYS the hormone (dark =
  flooding), grays out when deaf. Verified live: kidney breaker →
  nephrogenic tableau — ADH 0.82 with the control box blazing green,
  kidney gray-dashed, urine pinned at 12 mL/min, auto-drinks keeping
  osmolarity ~293 (the loop surviving on its behavioral arm alone).
- Deferred: nothing.
- Open bugs: none.
- Decisions: kidney glow semantics — boxes glow when their LABELED
  action is happening ("retain water"), so a flooding kidney is dark,
  a deaf one is gray. Same grammar as every other box.

## 2026-08-15 — M21: Water tab + charts + disturbances + CSV
- Shipped: third Runner (`/state?loop=water`), Water tab, four panels
  (osmolarity with 285–295 band + 275/305 lines, ADH+thirst, urine
  flow, urine concentration), drink markers colored by AUTHORSHIP
  (green = the loop drank by itself, blue = a human pressed the
  button), disturbance card (three drink sizes, salty snack, exercise/
  heat, desert + contest scenarios), `/control` drink/salty actions
  (server caps 3 L / 600 mOsm), scenario dispatch rewritten to branch
  on LOOP NAME (three loops broke the old hasattr sniffing), water CSV
  with the frozen 14 columns, water readouts with DEHYDRATED /
  OVERHYDRATED status words. Marker machinery generalized to
  {t, label, color}. Verified live through the production path: manual
  glass logged, contest chug slid osmolarity 289 → 274 with ADH dying
  and the kidneys flooding 12 mL/min at 38 mOsm/L, recovery turning;
  desert honestly kept dumping the leftover chug excess (still below
  285) before conserving; CSV header exact.
- Deferred: nothing.
- Open bugs: none.
- Decisions: drink-marker authorship colors are the loop's behavioral
  arm made visible — the classroom can watch the body drink with
  nobody at the keyboard.

## 2026-08-15 — M20: Water invariants + engine + console demo (Phase 6 starts)
- Shipped: water contract in `tests/test_invariants.py` (API, frozen
  14-field record, pins: holds-band-by-drinking, desert dehydrates
  despite conservation, central DI compensates through the water
  bottle, DI+desert killer combination, overhydration reflex, staged
  conserve-first thresholds, drinks() event log, determinism).
  `engine/water.py`: two-pool budget (water L + solutes mOsm; the
  controlled variable is their ratio), quadratic urine-vs-ADH curve
  (0.5–12 mL/min), constant metabolic waste stream making urine
  concentration honest (~900 mOsm/L conserving, ~40 flooding),
  auto-drinking as a deterministic behavioral effector gated by WATER
  ACCESS. `python -m engine.water_demo`: salty lunch → chug → desert →
  rescue, with the body drinking by itself 13 times. All 53 invariants
  + verify pass, all first-run — constants were hand-derived against
  the pins before writing the contract.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) salty snacks add solutes instantly (salt absorbs fast;
  no gut-solute pool — logged simplification). (2) Auto-drink rule:
  thirst ≥ 0.15 AND gut below 100 mL AND access — one deterministic
  250 mL glass; the trigger sits low enough that the resting sawtooth
  peaks ~294.4, inside the ±5 band. (3) Urine concentration is derived
  in the ENGINE (excretion/flow) and can briefly exceed 1200 mOsm/L
  after a salt bolus — physiologic ceiling not enforced, noted.
  (4) Sensor damage leaves ADH frozen mid-range and thirst silent →
  slow dehydration nobody feels (emergent, unpinned — the
  hypernatremia-unawareness parallel to M6's glucose story).

## 2026-08-15 — M19: Diagrams tell the diagnosis (Phase 5 complete)
- Shipped: diagram kit gained setLine() (live box text); the thermo
  control-center box now shows the number the loop is DEFENDING — "set
  point 39.0 °C" in bold hot-red under fever, back to plain 37.0 when
  it clears; glucose downstream effects (muscle glow, insulin→liver
  bar, muscle→response arrow) scale by what the tissues HEAR
  (total_insulin × insulin_sensitivity), so type 2 renders as a blazing
  beta box shouting into a dim muscle box. Verified live across the
  whole taxonomy: fever (set-point label flips to red 39.0, banner up),
  heat stroke (40 °C + exercise + sweat dead), hypothermia (−10 °C +
  shiver dead), temp Healthy (all restored, room untouched by design),
  type 1 (beta off, untreated), type 2 (insulin 0.58 with glucose 114 —
  beta fill 0.34 vs muscle fill 0.13 on screen), glucose Healthy.
- Deferred: nothing. Phase 6 candidates under Current state.
- Open bugs: none.
- Decisions: (1) the a-beta-muscle arrow stays driven by the SIGNAL
  (endogenous insulin) while the boxes/effects dim by what's heard —
  bright arrow into a dim box IS the type 2 picture. (2) Verification
  note, again: read server truth in a separate step after driving the
  UI — a nested-callback probe raced the healthy POST and briefly
  looked like a restore bug that didn't exist.

## 2026-08-15 — M18: The preset buttons + banner
- Shipped: Diseases card on both pages (Fever / Heat stroke /
  Hypothermia / Healthy again; Type 1 / Type 2 / Healthy again),
  `/control` action `preset` driven by ONE server table (full
  configuration + per-preset speed + banner line — buttons, banner, and
  any future quiz layer read this single source), `Runner.preset`
  carried in `/state`, red-accent banner strip rendering the diagnosis,
  active-preset button highlight, reset clears the diagnosis. Verified
  live: Fever click mid-run → offset 2.0 + 16× + banner up with core
  already climbing at t=146 (no reset); Type 2 → sensitivity 0.05 with
  beta cells still ON (resistance, not deficiency); Healthy → sensitivity
  1.0, preset null, banner gone, run continuing at t=515.
- Deferred: nothing.
- Open bugs: none.
- Decisions: (1) a preset is a COMPLETE diagnosis built on a healthy
  baseline — it also switches treatments off (fresh type 1 arrives
  untreated: pump off, basal 0), so diseases never stack and every
  demo starts from the same story beat. (2) Healthy is a door, not a
  state: it never shows as "active", it just clears the banner.
  (3) Manual breaker flips do not clear the banner — dissecting the
  disease is the point; reset does.

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
