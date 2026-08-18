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

- **Committed:** M46 (see Milestones; earlier summaries kept below) —
  Phase 11 underway. The dashboard has judgment: every row carries
  time-in-mode and runs-so-far, and a stuck flag — blind case past
  5 min, two zero-medal runs of one challenge, or a device quiet past
  3 min — sorts flagged teams to the top of a self-refreshing table.
  Thresholds are swept, named, pinned policy.
- **M45 (for reference):** `/teacher` exists: launch-minted PIN printed
  in the console (VL_TEACHER_PIN pins it for rehearsal), cookie once
  per device, wrong PIN refused in words, and behind it a read-only
  room table — period, team, tab, doing, last-seen — built on
  `registry.room()`, which sweeps but never seats, touches or steps.
  Blind cases show BY NUMBER ONLY: the page is safe to project.
- **M44 (for reference):** Phase 11 underway (spec:
  `vital_loop_phase11_kickoff.md`, scoped 2026-08-18: period codes /
  join screen + teacher dashboard). M43 gave devices periods
  (`periods.txt`, skippable join screen, cookies, badge); M44 made the
  boards mean "us": every attempt is stamped with its class's `period`
  at build time, each device's leaderboard and best-so-far line scope
  to its own class, and the Unassigned viewer — which is exactly what
  the projector is, having skipped the join screen — sees everyone.
  Pre-M44 records (no period key) read as Unassigned and keep
  displaying. The board names its scope on screen.
- **Next up:** M47 — the full pass and the phase close (join / skip /
  rejoin across periods, scoped boards, the dashboard through a blind
  case, leak checks extended, engine hashes + cookieless world
  byte-identical, M42 grammar intact, worksheets print).
- **Phase 10 (for reference):** M42 — **PHASE 10 COMPLETE** (M0–M42). Spec:
  `vital_loop_phase10_kickoff.md`. Two loops now talk: sugar above
  180 mg/dL spills into the urine and drags water out with it, and the
  sugar still in the blood pulls on the osmoreceptors directly. A
  fourth "Whole body" loop carries the full lesson grammar — sandbox,
  disease, diagram, two challenges, three blind cases, worksheet, CSV.
  Phases 1–9 are byte-identical, pinned by two engine hashes recorded
  before the coupling was written and by an app-level check that the
  three original pages still offer what they offered.
  Remote: https://github.com/gatorryan6-oss/vitalloop
- **Deferred candidates (kept from the Phase 11 scope choice):**
  1. **The concentrating ceiling on the water loop's OWN solute.** M20
     knowingly left `urine_osm` un-ceilinged after a salt bolus, and
     M37 deliberately did NOT fix it (Phase 6 is not Phase 10's to
     rewrite). It is a real physiological wrinkle and a small, honest
     piece of work whenever it is wanted.
  2. **Hemoconcentration**, measured and deliberately deferred at M38:
     worth +3 to +9 mg/dL over a class period, which is real and
     invisible. Would matter only if a multi-day scenario ever arrives.
- **Phase 9 (for reference):** M36 — **PHASE 9 COMPLETE** (M0–M36). Spec:
  `vital_loop_phase9_kickoff.md`. The sandbox is now a LAB: every
  device on the room's wifi gets its own three loops (M33) through the
  double-click LAN launch (M34), the water loop carries its fourth
  disease — SIADH, knob + preset + blind case 5 (M31/M32) — and the
  class leaves with paper keyed to their own runs (M35). One shared
  attempts log; the cookieless projector world is byte-for-byte the
  M7–M30 world. NOTE: the phase was built on the kickoff's flagged
  ASSUMPTIONS (cookie sessions / leaderboard-only / printable routes /
  verbal direction) because the interview went unanswered — all four
  held up, but they are one message away from revisiting.
  Remote: https://github.com/gatorryan6-oss/vitalloop
- **Next up:** STOPPED for confirmation before Phase 10. Candidates:
  1. **Cross-loop coupling** (mellitus polyuria — glucose above
     ~180 mg/dL spilling into urine and dragging water with it), now
     deferred twice; the first time two loops would meet.
  2. **Teacher dashboard** — a live who's-stuck view of the room's
     sessions; `registry.count()` and per-session state already exist.
  3. **Period codes / join screen** — grouping sessions by class
     period, if the anonymous-cookie model chafes in real use.
- **User checkpoint outstanding (M34):** a REAL phone on the room's
  wifi against `run.bat`'s printed address — everything short of that
  is verified (see M34 entry). The first launch may show the Windows
  firewall dialog: allow Python on private networks.
- **Port:** 5083 (this project's own; see CLAUDE.md for the machine registry).
- **Open bugs:** none.
- **Standing caution:** the invariants file froze the history record fields
  (kickoff §5) and the engine API before M1 exists. If M1's physiology
  genuinely can't satisfy a pinned behavior (e.g. monotone cooling with
  effectors off), show the human the conflict — don't loosen the test
  silently.

---

## Milestones

## 2026-08-18 — M46.5: The join name reaches the scoreboard
- Shipped: found by M47's room pass, patched as a decimal milestone
  (working agreement): the join screen said "name your team once", but
  attempts only carried names typed on the challenge/case cards — a
  team that joined and never retyped landed on the board as "(no
  team)". Now an attempt built with a BLANK label inherits the
  session's join-screen team name (through `clean_label`, like every
  name in the app); an explicit card label always wins; outside a
  request nothing changed. The page also pre-fills every empty label
  box from the cookie — visible, still editable per run. 1 new
  invariant (188 pass).
- Deferred: nothing.
- Open bugs: none.
- Decisions: the fallback lives in `build_attempt`/`build_case_attempt`
  (the two places a record is born), not in the routes — API callers
  and future modes inherit the promise for free.

## 2026-08-18 — M46: Who's stuck
- Shipped: the M46 contract (6 tests). Challenge and case stamps grew a
  wall-clock `wall_start`; Runner grew `tries` (per-challenge
  [{points, medal}], fed at the one place attempts log — the log stays
  the scores' one truth). Three swept, named, pinned thresholds with
  the reasoning beside them in app.py: `STUCK_BLIND_S = 300` (a
  decisive team reads a case's charts in 2–4 min; 600 would burn a
  third of the period), `STUCK_QUIET_S = 180` (a live page polls at
  4 Hz; phones auto-sleep inside 2 min), `STUCK_ZEROES = 2` (at 11–19
  wall-min per challenge run — measured across all 8 challenges at
  their pinned speeds — the SECOND medal-less run is when to walk
  over). `_stuck_reason` checks EVERY runner (a blind case on a
  background tab still counts), one reason per row, blind > zeroes >
  quiet. Stuck rows sort first, red-flagged; rows carry "· N min in"
  and "· N runs, best X". `/teacher/room.json` (same PIN gate, still
  read-only) feeds a 4-second self-refresh that rebuilds the table
  with textContent only (the M27 rule). 185 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. The tally is IN-MEMORY per session (dies with the sweep) — right
     for a live who's-stuck view; anything historical reads the log.
  2. VERIFIED LIVE with real wall-clock, no backdating: a ghost device
     seated at 02:41:33 flagged "quiet 3 min" at 02:44:37 (184 s); a
     blind case started 02:41:35 flagged "blind case 5 min, no answer"
     at 02:46:44 (309 s), taking priority over that session's own
     quiet state as designed. The teacher page — signed in fresh after
     the restart rotated the PIN (old cookie correctly bounced to the
     form) — raised both rows to red flags BY ITSELF, no reload. Note:
     in this session's hidden preview pane Chrome throttles the 4 s
     timer to ~1/min; on a visible screen it ticks at full rate.
  3. The DOM-read verification style (M39–M42) continues; a human
     should still glance at /teacher on a phone during the M34-style
     real-wifi checkpoint.

## 2026-08-18 — M45: /teacher — the PIN and the room list
- Shipped: `TEACHER_PIN` minted per launch (`secrets`, app-level — the
  engines still never see random; `VL_TEACHER_PIN` pins it so a
  rehearsed lesson has a rehearsable login), printed in the console
  beside the address in both the LAN banner and the localhost line.
  `/teacher`: PIN form → cookie (the app's ONE deliberate server-set
  identity, HttpOnly, rotated out by every restart) → the room. Wrong
  PIN = 403 in plain English. The room table (period / team / tab /
  doing / last-seen) renders from `registry.room()` — a read-only
  accessor that sweeps the idle but never seats anyone, never touches
  `last_seen`, and never steps a sim — plus `_describe_runner`, whose
  "doing" line names a blind case BY NUMBER ONLY. Rows sort period
  first, Unassigned last. 6 new invariants (179 pass) + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. The dashboard page is server-rendered with no polling yet —
     auto-refresh is M46's job, deliberately.
  2. Naming a sandbox PRESET on the teacher page is fine (the student
     clicked it themselves); naming a blind case is not. The describe
     helper's branch order makes that structural: case wins before
     preset can speak.
  3. Jinja autoescaping turned "doesn't" into `doesn&#39;t` and failed
     the wrong-PIN wording test — the pin now asserts an
     apostrophe-free phrase. Caught by the suite, worth remembering.
  4. VERIFIED LIVE in the browser (DOM-read, M39–M42 style): PIN 0907
     read off the preview server's console line; /teacher showed the
     form with the PIN nowhere in the page; wrong PIN → 403 with the
     words; right PIN through the real form → the room, showing the
     seated P3 session as "P3 / Test Rig / temp / sandbox / 17 s ago"
     — "temp" because the student page really was polling its temp
     tab, which is the dashboard telling the truth.

## 2026-08-18 — M44: The leaderboard learns periods
- Shipped: `period` appended to the frozen attempt fields (M27's
  grow-by-appending rule): stamped at `build_attempt` /
  `build_case_attempt` time from the requesting session's cookie —
  never inferred later — "" for Unassigned, and pre-M44 records (no
  key) read identically via `.get(..., "")`. `challenge_runs` /
  `leaderboard` / `best_attempt` grew a `period=` kwarg (None =
  everyone; default = a sentinel meaning "the request's own viewer"),
  so inside a poll the board scopes itself with no plumbing through
  `Runner.snapshot`. `/state` carries `board_period`; the page's board
  title says its scope ("Leaderboard — P3" / "— all periods"), shown
  only when the room actually has periods. 3 new invariants (173 pass)
  + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. `compare_attempts` stays cross-period ON PURPOSE — racing another
     class is a feature, and the compare is picked by id, not by scope.
  2. Attempt-stamp and viewer-scope are two different reads of the same
     cookie: an attempt gets "" when unassigned (a real value in the
     record), a VIEWER gets None (= everyone) — the projector's whole
     job, and also what keeps every pre-M44 test meaning what it meant.
  3. VERIFIED LIVE in the browser (DOM-read, M39–M42 style), against a
     seeded three-record log (one pre-M44 keyless, one P3, one P5;
     teacher's real 730 KB log backed up and restored around the test):
     P3 device → badge "P3 — Test Rig", board "Leaderboard — P3" with
     only Third Period, best-so-far 88 (the class's, not the school's
     95); skipped device → "Unassigned", "— all periods", all three
     rows incl. the keyless record, best 95 across 3 runs. One
     connection-refused burst in the console = the poll riding out the
     server restart (M33), not an app error.
- Shipped: Phase 11 opens (spec committed first: teacher dashboard +
  period codes, interview 2026-08-18, all three recommended options
  taken — skippable join screen / `periods.txt` / teacher PIN).
  `periods.py` (parser: comments, blanks, dupes, order kept, capped at
  12; missing/empty file → `[]` = joining QUIETLY OFF), seed
  `periods.txt` (P1–P7), registry mirrors `period`/`team` claims from
  cookies (`runners_for` grew optional kwargs; new read-only
  `identity(sid)` that never seats or touches `last_seen`), skippable
  first-visit overlay (only rendered when the list is non-empty), and
  the footer badge ("P3 — The Mongooses" / "Unassigned"). `periods.py`
  + `periods.txt` added to verify.py's SERVED_SOURCES — an edited
  period list on a stale server now fails verification by name. 8 new
  invariants (170 total pass) + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. Cookie semantics: ABSENT `vl_period` = never asked (overlay's
     cue); EMPTY = asked-and-skipped (Unassigned, never asked again);
     a name not on the teacher's list (stale year-old cookie) counts
     as Unassigned, never an error. The cookie is the SOURCE OF TRUTH;
     the registry only mirrors it — which is why idle sweeps and
     server restarts still cost a student nothing.
  2. Team names pass through `clean_label` (M27) — one hygiene rule
     for every name in the app.
  3. VERIFIED LIVE in the browser (DOM-read, as at M39–M42: the
     preview pane could not composite): fresh device → overlay with
     all 7 periods, Join disabled until a pick; P3 + "The Mongooses"
     → badge and encoded cookies; reload → no overlay, badge holds;
     cleared cookies → overlay returns; Skip → "Unassigned", empty
     cookie; no console errors; sim still polling underneath.
- Shipped: the M42 contract (3 tests). **The full pass, four loops
  wide** — every loop proved to carry the whole grammar (preset,
  plain challenge, crisis, ≥2 cases, CSV columns, answer vocabulary,
  worksheet), then driven through the production routes: a disease
  named on each, every one of its blind cases started, checked for
  leaks (no `*_enabled`, no answer-key field), CSV refused at 409 while
  blind, answered with the truth and graded correct, CSV released, and
  a gameless sandbox handed back. **Phases 1–9 untouched**, as an
  app-level check to sit beside the two engine hashes: the three
  original pages, their preset buttons (fever / type 1 / central DI /
  SIADH), their exact case counts (4 / 4 / 5) and their exact challenge
  sets are all still there. **Determinism through the routes on a
  two-engine loop**: the same ward round after two different lead-ins
  produces byte-identical history. 162 invariants + verify pass; all
  seven console demos run.
- Deferred: Phase 11 candidates under Current state.
- Open bugs: none.
- Decisions:
  1. The M30/M36 pass checked "every loop"; this one checks "every loop
     AND the loops that were already here". A coupling phase's real risk
     is not that the new thing fails — it is that the old things change
     quietly, so the close is half regression check by design.
  2. VERIFIED LIVE in the browser: all four tabs render complete —
     temp 3 charts / glucose 4 / water 4 / body 5, two challenge cards
     and a diagnose card on every one of them, a live diagram on every
     one, four worksheet links in the footer, and the room counter
     reading "1 device playing". The console's connection-refused burst
     is the poll riding out a verify.py restart (documented at M33), not
     an app error. As at M39/M40 the preview pane could not composite in
     this session, so this was read out of the live DOM rather than
     photographed — **a human should still spend one minute looking at
     the Whole body tab before teaching from it.**

## 2026-08-17 — M41: The coupled body joins the lesson grammar
- Shipped: the fourth loop now teaches every verb. A preset (**Untreated
  diabetes mellitus**, banner naming both links and earning the word
  honey-sweet) with Healthy as the way back; **two challenges** — "The
  ward round" and its crisis variant "The ward round goes wrong" (three
  ambushes: illness making tissues deaf to insulin, a relative bringing
  a sweet drink, a warm side room and sweating) with two hard stops
  (glucose ≤ 40, osmolarity ≥ 330 = HHS); **three blind cases** —
  mellitus, insipidus and an intact body, all three opening on the SAME
  brief word for word; `_eval_ward` + a `SCORING` entry per challenge;
  answer vocabulary and a redaction allowlist for the loop. The body
  record grew both loops' breaker flags so integrity rules and blind
  cases have something to work with. `SANDBOX_ONLY_LOOPS` is empty
  again. 159 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **THE SWEEP OVERTURNED THE SCORING TWICE, and both were real bugs.**
     (a) Grading "glucose at the end" monotonically meant LOWER IS
     ALWAYS BETTER, so a patient crashed to **1 mg/dL took full marks**
     for that row and a lethal hypo tied doing nothing at 70 points.
     Both "end" rows now score DISTANCE from the middle of their band.
     (b) The peak-osmolarity row was graded at the healthy 305 — but
     this patient ARRIVES above it, so every play failed for the state
     they were handed. Moved to 315, which is M29's rule about not
     grading past what the scenario itself imposes, applied to a
     starting condition instead of an ambush.
  2. **The premise "treat one and lose" had to be EARNED, not asserted.**
     The first build let insulin alone pass: treat the sugar promptly
     and the water problem mostly resolves itself, which is honest
     physiology but no challenge. Fixed by making the patient arrive
     already hyperosmolar (a `eat_salt` start action — two days without
     insulin is not a patient who arrives dry-eyed), so the water
     deficit is inherited and must be replaced. Now pinned as a test:
     both-treated MET and gold, insulin-alone and fluids-alone both
     MISS, and both beat doing nothing.
  3. **Medal ladders from the sweep, using ONLY moves the buttons offer**
     (4 U doses, 250 mL glasses — M26's rule). *ward_round*: 4 U + a
     glass every 30 min **87**, every 45 min 86, every 20 min 85 (all
     MET); then the misses — over-pouring every 15 min 79, insulin alone
     77, fluids alone 77, nothing 52, and every extra insulin dose
     collapses it (two 41, four 31). Medals 85 / 82 / 70, with silver
     deliberately above the best MISS.
  4. **The crisis needed its OWN ladder, and the sweep is why.** Its
     sweating ambush takes water back out, so the over-pour that misses
     in the plain round scores 88 there — which on the shared ladder was
     a MISSING run taking GOLD. Crisis medals are 92 / 90 / 70, and a
     sweep across the whole 60-play grid now confirms **no run without
     MET reaches gold or silver on either challenge**.
  5. **The coupled body records both loops' breaker flags now.** Without
     them the "the patient still could not drink alone" integrity rule
     was DEAD CODE — a team could re-enable water access mid-challenge
     and nothing would notice — and a blind case would have had nothing
     to withhold. So the record grew seven flags (appended), the CSV
     grew with it, and `VISIBLE_DURING_CASE["body"]` is now a strict
     subset of the record, pinned as such.
  6. **Two cases with the SAME answer role, on purpose.** Mellitus and
     insipidus are both control-centre failures — in different loops.
     The role repeats; the reasoning cannot, because the only thing
     separating them is the urine (measured: mellitus floods at ~1000
     mOsm/L with glucose above 250, insipidus at ~38 with glucose
     normal) and that contrast is pinned.
  7. **A mistake worth recording: I inserted the two challenges into
     `CASES` instead of `CHALLENGES`** — the closing braces of the two
     tables look identical and my patch matched the wrong one. Caught
     immediately because the app reported `body challenges: []`, and
     moved with a brace-counting script rather than by hand. The lesson
     is the boring one: when patching by exact-match, assert on
     something that identifies the TABLE, not just the punctuation.
  8. Verified through the production routes: preset → banner "Untreated
     diabetes mellitus"; challenge start 200; blind case → zero
     `*_enabled` or `water_access` fields in `/state`, CSV 409; answered
     control/beta → **correct, 100/100**; CSV back to 200 after reset.

## 2026-08-17 — M40: Two loops, one arrow
- Shipped: a fourth diagram on the M4/M22 kit — deliberately NOT a third
  copy of the loop picture but a picture of the JOIN. Seven boxes:
  blood glucose → the kidney tubules → sugar into the urine, down the
  right through "water follows the osmoles out" to plasma osmolarity,
  then right-to-left along the bottom through ADH/thirst to drinking.
  Both links drawn: the spill chain across the top and down, and LINK 2
  as a dashed path taking the long way round the outside (that sugar
  never left the blood, so it must not appear to pass through the
  kidney). Three boxes carry live numbers via `setLine`, so the picture
  doubles as a readout. 154 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The dark arrow IS the lesson.** Below 180 mg/dL the spill arrow
     sits at baseline grey and the response box reads "nothing, yet",
     with the caption "nothing crosses below 180 mg/dL — a THRESHOLD,
     not a leak". A healthy body's two loops are drawn side by side and
     visibly not talking to each other; the coupling only exists when
     the sugar loop has already failed.
  2. **The kidney box glows with SPILLING, not with reabsorbing.** Every
     other box in this project glows when its labelled action is
     happening (M22 decision), and this box's label is "tubules reabsorb
     the filtered sugar" — but a box that blazed while working normally
     and went dark exactly when the interesting thing happened would
     invert the whole lesson. The label was written to match: it glows
     as reabsorption fails. Flagged here because it is the one place the
     project's glow grammar is applied to a failure rather than a
     function.
  3. No `status()` badges on this diagram: the coupled body has no
     breaker flags in its record and no blind case yet. If M41 puts a
     case on this loop, redaction has to be designed for it then — the
     M28 allowlist is per-loop and fails closed, so nothing leaks in the
     meantime.
  4. VERIFIED LIVE (DOM-level again — the preview pane still cannot
     composite in this session, so no screenshot): at rest, glucose
     90 mg/dL, spill arrow `#c3c2b7` at width 2.00 and the box reading
     "nothing, yet". Beta cells off + a 100 g meal at 16×: at 191 mg/dL
     the arrow had turned `#4a3aa7` at width 2.13, and at **252 mg/dL it
     read opacity 0.62 / width 2.83** with the boxes live at "252 mg/dL",
     "1.44 mg/dL·min", "294.1 mOsm/L" and urine at 1051 mOsm/L. Reset,
     and the arrow went back to `#c3c2b7` / 2.00 — lit as glucose
     crossed, dark again when it came home. Console clean.

## 2026-08-17 — M39: The Whole body tab
- Shipped: a FOURTH loop — `Runner(Body(), "body")` in `_make_runners`,
  so every session gets a coupled body alongside its three single
  loops, with its own frozen CSV column list. UI: a "Whole body" tab
  and page — a model-note card naming what the single-loop tabs leave
  out, five panels (glucose with the 180 spill line drawn as a
  reference, the spill itself, plasma osmolarity WITH the sugar's own
  share overlaid, urine flow, urine concentration), disturbance
  controls (meal / glass / 4 U / exercise) and two breakers (beta
  cells, water access), CSV link. Readouts show BOTH controlled
  variables at once and the glucose label flips to "SPILLING SUGAR"
  above threshold. A sixth worksheet route, `/worksheet/body` ("Two
  loops, one body"). 154 invariants + verify pass.
- Deferred: the coupled DIAGRAM to M40 as specced; preset/challenge/
  case to M41.
- Open bugs: none.
- Decisions:
  1. **A fourth loop broke five lesson-grammar tests, and the fix was to
     make the exception VISIBLE rather than to narrow the tests
     quietly.** `test_every_loop_has_a_crisis`, `..._can_teach_the_whole_
     lesson`, `..._sandbox_is_gameless`, the worksheet suite and the M36
     lab pass all assumed every loop in `runners` has the full grammar.
     Rather than weaken them, app.py now DECLARES
     `SANDBOX_ONLY_LOOPS = {"body"}`, the grammar tests iterate the
     loops that are not declared, and a new test asserts a declared
     loop really is game-less AND still serves `/state` and its CSV. The
     exception lives in the app where a reader will find it, is
     time-boxed to M41, and M42 pins the set empty. That is the kickoff's
     own "sandbox first, game second" written down as a check.
  2. The worksheet suite's failure was not an exception at all — the
     coupled body genuinely deserves a worksheet, so it got one, and
     M35's pins (fields exist in the record AND appear on the page,
     vocabulary exact, no answers) applied to it unchanged.
  3. The lab pass's "every loop proves it is not redacting" assertion is
     now scoped to loops that HAVE cases: a loop that cannot be blinded
     has nothing to prove, and the body record carries values rather
     than breaker flags.
  4. `Runner`/`snapshot` needed NO changes for a fourth loop —
     `doses`/`drinks` were already feature-detected and `Body` provides
     both. Every control action was tested against the new loop through
     the routes: eat, drink, inject, exercise, both breakers, speed,
     pause/resume/reset and salty all answer 200, and a temperature
     action aimed at it refuses with "env_temp is a temperature-loop
     action".
  5. VERIFIED LIVE in the browser, at the DOM level: switched to the
     tab, broke the beta cells and fed a 75 g meal through the page's
     own session at 16×, and watched glucose cross the threshold —
     at sim 21.1 min glucose 207, the header readout reading
     **"glucose — SPILLING SUGAR"**, `renal_loss` 0.54 mg/dL/min
     arriving as `tubular_load` 0.54 mOsm/min, urine concentration up at
     1001 mOsm/L, and the sugar contributing 6.5 mOsm/L of a 294.4
     plasma osmolarity. All five panels drew (the osmolarity panel with
     two polylines — plasma and the sugar's share). Console clean.
     **Honest limit of this check:** the preview pane could not
     composite frames in this session, so there is no screenshot and the
     below-the-fold buttons were not clicked with a real mouse — the
     controls were driven through the page's own session and the
     rendering read out of the live DOM. A human eyeball on the tab is
     still worth one minute.

## 2026-08-17 — M38: The second link — sugar is an osmole, and the spiral
- Shipped: `set_foreign_osmoles()` on the water loop (plasma osmoles
  another loop owns, added to reported AND sensed osmolarity), wired in
  `Body` as `(glucose − 90) × MGDL_TO_MOSM_L`; `foreign_osm` appended to
  the water record and CSV, `glucose_osm` to the body record. M38
  contract — 7 tests: the factor derived and agreeing with the clinical
  "glucose over 18"; the share is the EXCESS not the whole; polydipsia
  (the diabetic body must drink more than twice the healthy one); the
  loop compensates with water available (peak osm < 300) and crosses 305
  with thirst pinned at 1.00 without; the stranded body's last hour
  drier than its first; validation. 153 invariants + verify pass.
- Deferred: **hemoconcentration — measured, then deliberately left
  out** (see decision 1). Logged here so it is not silently forgotten:
  it is real, it is just below the resolution of a class period.
- Open bugs: none.
- Decisions:
  1. **SPEC AMENDMENT, logged not silent (the M24/M29 pattern): the
     return leg the kickoff named is too weak to teach, and a different
     link matters more.** The kickoff specced M38 as hemoconcentration —
     falling body water concentrating the remaining sugar. Measured it
     before building it: over 12 h the diabetic body loses 1.3 % of its
     water with a bottle in reach and 4.0 % without, which would raise
     glucose by **+3 and +9 mg/dL**. Real, and invisible; the clinical
     version of that spiral takes days, and this app teaches in
     periods. Built the honest alternative instead — **glucose as a
     plasma osmole**, worth **+13.8 mOsm/L at the sugar peak**, which
     is the literal "hyperosmolar" of hyperosmolar hyperglycemic state.
  2. **It is what the M37 body was visibly missing.** After M37 the
     untreated body passed extra urine and hardly asked for a drink
     (thirst peaking at 0.11) — polyuria without polydipsia, which is
     not a disease any clinician would recognise. With the sugar
     feeding the osmoreceptors: **drinks 4.00 L against a healthy
     1.50 L**, urine 2.46 L against 1.24 L. The triad is now all
     three legs.
  3. **The compensating body's osmolarity reads NORMAL, and that is the
     lesson, not a failure.** Mellitus-with-water peaks at 294.2
     mOsm/L — identical to healthy — while drinking four liters to get
     there. The disease is not visible in the controlled variable; it is
     visible in the EFFORT. Take the bottle away and the same body runs
     to 313.8 with thirst pinned at 1.00. Pinned both ways round.
  4. **LINK 2 HAS NO THRESHOLD, AND MUST NOT.** The M37 invariant said
     "the coupling is a threshold, not a leak" and a healthy FED body
     now fails that as written, because a real post-meal 140 mg/dL
     genuinely does add ~3 mOsm/L to plasma osmolarity. Rather than
     invent a threshold to keep a test tidy, the invariant was split
     into what is actually true: link 1 (the renal spill) is absolute —
     a healthy body spills exactly zero; the byte-identical comparison
     against a standalone water loop now runs on a FASTING body, where
     neither link has anything to carry; and a fed healthy body is
     bounded instead (0 < sugar's share < 5 mOsm/L, total osm < 296).
     Modelling the body, not the test.
  5. Emergent and worth a mention in class: with water freely available
     the compensating body ends slightly water-LOADED (40.0 → 41.2 L),
     so its salt is diluted while total osmolarity reads normal. That is
     translocational hyponatremia — the real reason clinicians "correct"
     sodium for glucose. Nothing models it; it falls out. (This model
     lumps all non-glucose solute into one pool, so it is the right
     phenomenon, not a sodium number to quote.)

## 2026-08-17 — M37: The loops meet (Phase 10 starts)
- Shipped: Phase 10 kickoff (`vital_loop_phase10_kickoff.md`) and
  `engine/body.py` — a `Body` owning one glucose sim and one water sim,
  stepped in lockstep, carrying the kidney spill across each tick.
  Glucose record grows `renal_loss`; water grows `tubular_load` and
  `set_tubular_load()`; both appended to their CSVs. New frozen
  `BODY_FIELDS` schema. `python -m engine.body_demo`: an untreated day,
  then the two siphons side by side. M37 contract — 11 tests: both
  engines' FULL Phase 9 records hashed from committed code BEFORE the
  edit and unchanged after; the coupling is a THRESHOLD not a leak (a
  healthy body's water loop compared tick-for-tick against a standalone
  one, byte-identical); the mellitus signature; the mellitus/insipidus
  contrast; the conversion derived not typed; load validation; unknown
  part refused; determinism; and neither engine importing the other.
  147 invariants + verify pass; all three CSVs still 200.
- Deferred: nothing. The return leg is M38 as specced.
- Open bugs: none.
- Decisions:
  1. **HALF THE COUPLING WAS ALREADY BUILT, and finding that changed the
     milestone.** `engine/glucose.py` has spilled sugar above 180 mg/dL
     since Phase 2 (`RENAL_THRESHOLD`, `RENAL_COEF`) — folded silently
     into `uptake`. So the glucose side needed NO behavior change: M37
     only gives the existing term a name (`renal_loss`) while leaving it
     inside `uptake`. A readout, not a re-plumbing, which is why
     byte-identical Phase 2–9 glucose is structural rather than hoped
     for.
  2. **THE REGRESSION GUARD CAUGHT ME OVERREACHING, exactly as designed.**
     The first implementation made urine flow
     `max(ADH_allows, total_solute / 1200)` — which enforces the
     concentrating ceiling on the water loop's OWN excretion too, and so
     changed what a salt bolus does. Two hashes went red. M20 decision 3
     had knowingly left `urine_osm` un-ceilinged there, and Phase 6 is
     not this phase's to rewrite. Rebuilt as ADDITIVE and foreign-solute
     only: `urine_rate += tubular_load / MAX_URINE_OSM * 1000`. With no
     load the line is exactly zero, both hashes went green, and the
     coupled numbers barely moved (peak flow 3.0 → 3.14 mL/min). The
     un-ceilinged salt-bolus urine osm remains a documented Phase 6
     simplification and a Phase 11 candidate — noted, not silently
     fixed.
  3. **The unit conversion is DERIVED from the engine's own constant,
     not typed.** `CARB_TO_MGDL = 5.56` means 1 g raises the pool
     5.56 mg/dL, so the pool is 1000/5.56 = ~180 dL; glucose is
     ~180 mg/mmol and does not dissociate; so 1 mg/dL/min of spill is
     ~0.998 mOsm/min. The two 180s are a coincidence of THIS model's
     pool size, not a law, so `body.py` computes the factor and a test
     pins it to `CARB_TO_MGDL` — change the pool and the coupling
     follows honestly instead of silently disagreeing.
  4. **SWEEP FIRST, and the calibration needed no tuning at all.**
     Sustained glucose → urine, straight off the mechanism: 250 mg/dL
     → 2.2 L/day, 300 → 3.4, 350 → 4.6, 400 → 5.8, 500 → 8.2. Untreated
     type 1 clinically runs 300–500 mg/dL and passes 3–6 L/day, so the
     model brackets reality using only constants Phase 2 and Phase 6
     chose for unrelated reasons. Nothing was fitted to make that
     happen.
  5. **An honest limit, logged rather than engineered around:** THIS
     model's untreated type 1 averages 229 mg/dL over a fed day (fasting
     plateau ~186), not the 300–500 of a real untreated patient, so its
     12 h output is 1.42 L against a healthy 0.77 L — real polyuria,
     but moderate. The mechanism is right and the disease is mild. Not
     "fixed" by inventing severity: the demo shows the post-meal
     stretches (glucose 330, spill 3.0 mg/dL/min, urine 3.17 mL/min at
     1077 mOsm/L, ADH 0.87) where the story is unmistakable. A real
     severity beat exists for M41 and costs no new physics — a thirsty
     patient reaching for SUGARY drinks, which the app can already
     express as `eat()` + `drink()`.
  6. **Pins are measured, not hoped for.** First draft of the signature
     test asserted mean urine osm > 900 while "flooding"; measured 838,
     because a diabetic body that has just had a drink also floods —
     dilutely — and so does a healthy one. Re-cut to judge only ticks
     the SPILL is driving (`renal_loss > 1.0`): mean 980, min 704, ADH
     never below 0.75. The pin now names the mechanism instead of a
     side effect.
  7. Measured signatures, for the record: MELLITUS 1.42 L/12 h at 980
     mOsm/L with ADH 0.83; INSIPIDUS 8.64 L/12 h at 38 mOsm/L with ADH
     0.00; HEALTHY 0.77 L and not one milligram spilled. Insipidus
     passes six times the water and it is nearly pure — tasteless.
     Mellitus passes less, loaded, with the hormone working the whole
     time — honey-sweet. M23 taught those two words; this milestone is
     where the class can finally read them off a chart.

## 2026-08-17 — M36: The lab pass, and Phase 9 closes
- Shipped: the M36 contract in `tests/test_invariants.py` (2 tests).
  **The lab pass** — six devices driven through the production routes:
  a freezer-plus-fever demo that reached nobody else's body; two teams
  racing the identical cold_store with different plays (the team that
  worked the back half out-scored the team that rested, both runs in
  the one log); a blind SIADH case on one device whose blindfold
  covered nobody else's eyes (its CSV 409 while a neighbour's read
  200), surviving a mid-case reload and graded correct; a device
  clicking every wrong thing and earning only worded 400s while five
  others kept teaching; every device handing back a gameless sandbox
  per-session; and the default runners untouched throughout. **The
  storm** — eight devices hammering /state, /control and /export.csv
  concurrently: every answer a 200 (or the deliberate wrong click's
  400), never a 500, and every session's state intact after. 136
  invariants + verify pass; footer, worksheet links and room count
  confirmed live in the browser.
- Deferred: Phase 10 candidates under Current state.
- Open bugs: none.
- Decisions:
  1. The lab pass is deterministic route-driven interleaving plus ONE
     genuinely-threaded storm with coarse assertions (status codes and
     end-state, never timing) — concurrency in a pinned test earns its
     keep only if it can't flake.
  2. Two payload-shape bugs in the TEST were caught by the app
     refusing them honestly (`points` not `score` in the attempt
     record; exercise takes `value` not `on`) — the contract held, the
     test conformed.

## 2026-08-17 — M35: Student worksheets — three printable routes
- Shipped: `/worksheet/temp|glucose|water` — one Jinja template
  (`worksheet.html`, self-contained with its own print CSS: one sheet,
  no app chrome) over one server table (`WORKSHEETS` +
  `WORKSHEET_TERMS`). Each sheet: name/team/period header, "label the
  loop" (the SEVEN curriculum terms exactly, each with a prompt and a
  write-in), "read your own run" (blanks answered off the student's
  own charts/CSV, cited column names rendered in `<code>` by a
  `replace_fields` filter), and a challenge/diagnosis debrief keyed to
  the report card. Worksheet links in the page footer. Four pins:
  three routes + plain-English 400 for nonsense; vocabulary exact on
  every sheet; **every cited field exists in the frozen records AND
  actually appears on the page**; no case brief, no teaching note, no
  disease banner leaks onto paper. 134 invariants + verify pass; the
  water sheet read live in the browser and reads like a handout.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The cited-fields pin caught three real authoring gaps on its
     first run**: `sweat`, `gut_carbs`/`uptake` and `thirst` were in
     the tables but asked about nowhere. Two became questions worth
     having (sweat flat at zero in the cold = the cheap-first
     ordering; gut_carbs draining into uptake = where the sugar
     went); water's unused `t` was dropped instead of forcing a
     question. The pin is doing exactly what the M28 allowlist does:
     making drift impossible, not just unlikely.
  2. Worksheets create NO data products and read none live — they are
     deliberately session-free static renders, so a printed stack
     works whether or not the room's sessions still exist.
  3. The debrief asks the student to name the report-card row that
     decided their score — the SAME rows M26 made per-row on screen —
     so the paper trail and the screen agree by construction.

## 2026-08-17 — M34: Open the doors — the LAN launch
- Shipped: `run.bat` sets `VITAL_LOOP_HOST=0.0.0.0` before `python
  app.py`, so the double-click serves the room while a PLAIN `python
  app.py` — and therefore verify.py and every earlier habit — stays
  loopback-only (`_serve_host()`, pinned both ways). On a LAN launch
  the app prints the teacher-facing story before serving: the join URL
  built from the machine's real interface (`_lan_addresses()`, the
  UDP-connect trick, no packets sent), the one-time firewall
  instruction, and the school-wifi caveat (client isolation is the
  network's doing, not the app's). `/state` grew `sessions` —
  `registry.count()` — and the page grew a quiet footer: "N devices
  playing", the room arriving in real time. 130 invariants + verify
  pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **Opening the doors is an explicit act, not a default.** The env
     var is the one switch, set only by run.bat; the pinned default is
     loopback. Eight phases of tooling assume a private server, and
     they keep that assumption unless the teacher double-clicks the
     launcher.
  2. The cookieless default session does not count toward the footer —
     it's the projector/tooling seat, not a device.
  3. VERIFIED LIVE as far as one machine can: app launched exactly as
     run.bat does (env var + 0.0.0.0), startup printed "Write this on
     the board: http://192.168.12.223:5083/" with the machine's REAL
     wifi address, the page answered 200 with the identity marker over
     that address (the server log shows the request arriving FROM
     192.168.12.223, not loopback), and a cookie-carrying client over
     the LAN interface was seated with its own fresh body (t = 0.0)
     while the footer count read 2 (browser tab + LAN client). The
     REAL-PHONE checkpoint is the user's — logged under Current state.

## 2026-08-17 — M33: Per-student sessions — the projector becomes a lab
- Shipped: `sessions.py` — `SessionRegistry` (plain Python, no Flask,
  one lock, injectable clock): cookie sid → that browser's OWN three
  Runners, created on first sight, idle-swept at 30 min, capped at 40
  with a plain-English `RoomFull`. App: `_make_runners()` factory, the
  module-level `runners` kept as the DEFAULT session (any cookieless
  client — verify.py, pytest, curl — drives it exactly as since M7),
  `_session_runners()` resolving every route incl. `/export.csv` (your
  CSV is YOUR run) and the PAGE (a full room refuses the page in words,
  never a stack trace), `RoomFull` errorhandler. JS mints the id
  (crypto.randomUUID → `vl_sid` cookie, the server only reads it) and
  the poll now surfaces a server refusal in the server's words instead
  of throwing on `j.now`. `sessions.py` joined verify.py's
  SERVED_SOURCES (M26 4.6 rule). M33 contract: 7 tests — isolation
  (a device's action moves neither another device nor the default
  runners), reload-keeps-session, unknown/evicted sid seats a fresh
  healthy sandbox, the cap refuses API and page in words while seated
  devices keep playing, fake-clock eviction with touch-resets-idle,
  one shared attempts log across sessions. 128 invariants + verify
  pass.
- Deferred: the live-session count footer to M34 (it's the LAN
  milestone's teacher-facing face; `registry.count()` is ready).
- Open bugs: none.
- Decisions:
  1. **The CLIENT mints the session id, the server only reads it.**
     Server-assigned cookies would have seated the pytest client and
     verify.py in throwaway sessions the moment they touched "/",
     silently detaching every fixture that mixes route calls with
     direct `vital_app.runners` access. With client-minted ids the
     cookieless world is byte-for-byte the M7–M30 world — eight phases
     of tests and the standing verify kit run UNCHANGED, which was the
     Phase 8 promise ("a plumbing change, not a rewrite") kept
     literally.
  2. **Sessions are runtime state, ON PURPOSE** (kickoff §5): the
     registry lives in memory, `attempts.json` stays the only durable
     product, and an evicted or unknown id is NOT an error — it's
     seated fresh. That one rule is also the restart story: bounce the
     server mid-class and every device quietly starts over while every
     score survives.
  3. **Cap 40 / idle 30 min are memory policy, not UX**: history is a
     data product that grows all period (~tens of MB per hot session),
     so the cap bounds the worst case and the sweep returns a closed
     tab's memory. Both constants sit together in app.py, tunable.
  4. The existing global `_log_lock` (M26) already made cross-session
     scoring safe — the milestone added zero attempts code, which is
     the M26 design paying out.
  5. VERIFIED LIVE with three real clients on one machine: the browser
     (self-minted sid) ran its temp loop at 16× on its own clock; a
     PowerShell client with a cookie container got a fresh body at
     t = 0.0 and its own hypothermia; the cookieless projector stayed
     at speed 1 / no preset throughout and cleaned up with its own
     reset. Console clean (connection-refused burst during the verify
     restart window, ridden out by the poll's catch).
     *Harness note for future sessions:* Windows PowerShell 5.1
     silently DROPS a `Cookie:` header passed via `-Headers` —
     Invoke-RestMethod needs a `WebRequestSession` cookie container,
     or the "session" you think you're driving is the default one.

## 2026-08-17 — M32: SIADH on the page — preset, banner, and case 5
- Shipped: fourth disease row in the water Diseases card (Central DI /
  Nephrogenic DI / **SIADH** / Healthy again) through the M18 preset
  table — banner names the syndrome and the inappropriate-secretion
  mechanism, `HEALTHY_WATER` grew `adh_override: None` so every water
  preset clears the knob (diseases never stack), `_apply_preset` grew
  the hook. **Case 5**, the fifth blind water case: same brief as cases
  1 and 2 WORD FOR WORD, the morning's 1.5 L arriving as a
  `start_actions` load, 2 h warm-up, answer control/pituitary. Two new
  pins (preset-is-a-complete-diagnosis incl. Healthy clearing it;
  SIADH-is-in-the-diagnosis-game with the control-center answer); every
  M28 contract test picked case 5 up automatically by iterating
  `CASES`, which is the payoff of building the diagnosis game as a
  table. 122 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The case's intake is one `start_actions` load, not interleaved
     drinking**, because the "you joined here" marker and the "first X
     already happened" chip both assume warm-up time equals `warmup_s`
     (app.js reads it directly). `start_actions` CAN advance time (step
     is a sim method), and a case that does so would put the marker in
     the wrong place — noted here so the next case author doesn't.
  2. **Case-5 sweep before wiring** (SS2): join tableau osm 280.3
     (dipped to 279.8, brushing the overhydration line at 37 min), ADH
     1.00, urine 0.5 mL/min at 900 mOsm/L, thirst 0.00, zero
     auto-drinks; the healthy control arm on the same 1.5 L recovered
     to 288 by flooding 12 mL/min at 75 mOsm/L. Same answer as case 2
     (control/pituitary) in the opposite direction — silent vs
     won't-stop — which is deliberate: the role repeats, the reasoning
     can't.
  3. VERIFIED LIVE in the browser on the running server: SIADH click →
     banner up, ADH pinned 1.00 at osm 290 (a healthy pituitary reads
     0.5 there — the inappropriateness visible at rest), a 1 L drink at
     16× slid osm 290 → 285.7 in 25 sim-min with urine locked at
     0.5/900; Healthy → override null, banner gone, and the freed loop
     dumped the excess itself (ADH 0, kidneys 12 mL/min at 37.5
     mOsm/L) — no teleport. Case 5 blind as "Period 6 Gold": no
     `_enabled`/knob fields in `/state`, CSV 409, all six blind-hide
     cards hidden, join tableau matching the sweep to the decimal;
     answered control/pituitary → RIGHT 100/100, note up, fields
     released (override's true value 1.0 arriving only at the reveal),
     CSV 200, cards back. Console clean (the 409 is the deliberate
     blind-CSV probe; the 404 was this session's own wrong URL).
     The "SIADH" string in the page is the Diseases-card BUTTON — menu
     vocabulary, present for every case, same standing as the Fever
     button during the fever case (M28 decision 2's line holds: the
     menu is public, the answer is not).

## 2026-08-17 — M31: SIADH — contract + engine knob + demo (Phase 9 starts)
- Shipped: Phase 9 kickoff (`vital_loop_phase9_kickoff.md`) and the M31
  contract in `tests/test_invariants.py` (7 tests: the PHASE 6 SUBSET
  HASH recorded from M30-committed code BEFORE the engine changed
  (d884ef86…) so the knob, unset, is proven byte-identical; the SIADH
  signature — ordinary drinking (a glass every 30 min) slides osmolarity
  under 285 between 1 and 2.5 h and under 282 by 4 h while urine stays
  ≤ 1 mL/min at ≥ 600 mOsm/L and thirst reads 0.00 the whole way;
  water restriction as the treatment — the same disease with no drinks
  drifts < 3 mOsm/L and never leaves the band; the control arm — a
  healthy body on the identical schedule never dips below 285 because
  the kidneys flood > 5 mL/min at < 150 mOsm/L; knob validation;
  determinism). `set_adh_override(level)` in `engine/water.py`, M17
  pattern; the record and the water CSV grow `adh_override` (appended,
  like every growth since M12); `ANSWER_KEY_FIELDS` in the redaction
  contract grew it too, so the allowlist can never ship it. Act 2 in
  `python -m engine.water_demo`: the slide, the silent alarm, the
  restriction. 120 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The override models ECTOPIC secretion** (tumor, drug effect), so
     it bypasses the pituitary toggle as well as the receptors — SIADH
     stacked on a "broken ADH release" breaker still shows hormone,
     which is physiologically the point.
  2. **An override of 0 is rejected** with "that's central DI by another
     name — use the ADH toggle", mirroring M17's sensitivity-0 refusal.
  3. **Sweep before pins** (SS2 discipline, numbers now in the test
     margins): drinking run 290 → 277.6 crossing 285 at 1.52 h and the
     280 line at 3.05 h; restriction 290 → 291.8 (insensible losses,
     rising not falling); healthy control arm bottomed at 286.5 while
     flooding 8.9 mL/min at 51 mOsm/L. Thirst 0.00 in every SIADH run —
     the alarm-that-cannot-ring is emergent, not scripted.
  4. The water loop had no pinned regression hash (thermo and glucose
     got theirs at M13/M17); recording one from the last committed code
     BEFORE editing was the first act of the milestone.

## 2026-08-17 — M30: The full pass, and Phase 8 closes
- Shipped: the M30 contract in `tests/test_invariants.py` (5 tests: every
  loop carries every verb of the lesson grammar; THE SANDBOX STAYS
  GAMELESS with no game running; A RELOAD MID-GAME LOSES NOTHING,
  including a blind case that must still be blind; NOTHING WEDGES —
  every action the UI can send, plus the malformed and wrong-loop
  version of each, fired at all three loops, must answer 200 or a
  plain-English 400 and leave every loop still teaching; and M30.1's
  fairness pin below). **M30.1 — a challenge now starts a FRESH RUN**,
  the one real defect the full pass found. A whole-period pass driven
  through the production routes: all four modes on all three loops, 18
  attempts, every check green. 114 invariants + verify pass.
- Deferred: nothing. Phase 9 candidates are under Current state.
- Open bugs: none.
- Decisions:
  1. **M30.1 — A CHALLENGE STARTS A FRESH RUN, and this was a real bug.**
     Until now a challenge inherited whatever body the sandbox had been
     left in (only a diagnosis case reset — M28 decision 3 says so
     explicitly). The full pass ran the identical 40 % duty play on
     cold_store from three different lead-ins and got **88 / gold from a
     fresh app, 21 / no medal straight after a freezer demonstration,
     and 88 again after a fever demo**. Two teams' report cards are only
     comparable if the runs start the same way, and the whole head-to-
     head rests on that: "the engine's determinism is what makes the
     comparison fair — same inputs, same curves" (kickoff SS1). The
     starting body IS an input. One line in `start_challenge`
     (`runner.sim.reset()`), pinned as a test that runs the same
     challenge after two different lead-ins and demands byte-identical
     history. Nothing else changes: `reset()` was already the case
     path, the browser already handles a sim reset behind its back
     (M10), and no challenge story ever depended on continuing from
     what came before.
  2. **The "nothing wedges" checkpoint is now a test, not a promise.**
     47 payloads × 3 loops, covering every action the UI can send and
     the broken versions (`speed 7`, `effector gills`, `eat lots`,
     `preset consumption`, `diagnose 99`, `answer the vibes`, `{}`,
     `action: null`), plus unknown loops and `/compare` with nonsense
     ids. Every one answers 200 or a 400 that says why, and every loop
     still serves `/state` and its CSV afterwards. This is a projector
     in a classroom: a wrong click cannot cost the lesson.
  3. **Two script bugs in the pass were worth keeping as notes**, since
     both will bite the next person: (a) a knob set between ticks is not
     in the newest RECORD until the next tick runs — `state()` is
     `history()[-1]`, the last COMPLETED tick — which is invisible live
     because polls step constantly, and (b) this machine's console is
     cp1252, so a verification script that prints the app's own em
     dashes and arrows dies on `UnicodeEncodeError` unless stdout is
     reconfigured to utf-8.
  4. **THE FULL PERIOD, driven end to end through the routes** (`/control`,
     `/state`, `/export.csv`, `/compare`) with sim time advanced by
     `Runner._step`, so nothing was a shortcut around the app:
     - *disturb*: the freezer cools and shivers (36.81 / 0.46), a 60 g
       meal is answered by insulin (143 mg/dL, insulin 1.00), a salt
       load raises ADH (291.4, 0.64);
     - *break*: all three effectors off in a −10 °C room drives the core
       37.00 → 35.53 monotonically, and the CSV exports it;
     - *name*: fever / type 1 / central DI each raise their banner and
       set their mechanism, and Healthy clears all three;
     - *challenge + score + race + survive*: all six entries reported,
       scored and logged — cold_store 88 gold, blast_freezer 85 gold
       (both ambushes fired), t1_shift 91 gold, crisis_shift 86 gold
       (three ambushes), aid_station 100 gold, race_day 57 bronze on a
       deliberately sloppy play. **Every one of those matches its sweep
       number exactly** — the number the sweep predicted is the number
       the class gets, which is the determinism promise paying out
       across the whole game layer;
     - *diagnose*: all 12 cases started blind (nothing ending in
       `_enabled`, no disease knob, CSV 409), answered with the truth,
       graded correct, CSV released;
     - and every loop handed the sandbox back afterwards.
  5. VERIFIED LIVE in the browser, on a server relaunched from cold:
     - **the log survived the relaunch** — "best so far" read straight
       off disk on all three loops (cold_store 83 SILVER over 2 runs,
       race_day 93 GOLD, crisis_shift 0 from the ER run), with attempts
       #1–#7 spanning M26 → M29 and every mode;
     - **the sandbox was gameless** — no challenge block, no case block,
       no preset, every `*_enabled` flag present, CSV 200, on all three;
     - **the head-to-head drew off the real log** — leaderboard ranked
       the two cold_store runs, Compare read "(no team) takes it, 83 to
       51 — row by row, here's where", and the crisis card beside it
       stayed empty, which is the per-card scoping of the M29 refactor
       working;
     - **a reload mid-game lost nothing** — started cold_store as
       "Period 5 Green", turned exercise on, reloaded the page: the team
       label, the progress clock and bar (3.9 %), the exercise button
       and "Shivering — DISABLED" all came back from server state, and
       the chart buffer refilled from t = 0 off server history;
     - **a blind case, live** — case 4 of 4 on temp: nothing leaked,
       both `data-blind-hide` cards gone, CSV 409; answered effector /
       sweat → RIGHT, 100 / 100, teaching note, cards back, CSV 200,
       saved as run #8.
     Console clean (the one error is the 409 from a deliberate CSV
     probe during the blind case — the gate working).

## 2026-08-17 — M29: Crisis mode
- Shipped: M29 contract in `tests/test_invariants.py` (12 tests: one
  crisis per loop, event shape + offsets inside the window + every
  action a method that loop's engine really has, stops exist and are
  scored, the stop table read the same way by the stepper and the report,
  THE DETERMINISM PIN — the same crisis stepped one tick at a time and in
  chunks of 991 must produce byte-identical history AND an identical
  feed — an event landing at its stamped offset and changing something,
  a no-events challenge stepping exactly as a plain `sim.step()` run, a
  hard stop closing the window early and zeroing, ambushes stopping when
  the run does, the feed carrying only what has landed, the feed in the
  attempt record, and no ambush text in the page). `Runner._step` splits
  the tick budget at every event boundary; `_step_watched` tests the
  hard-stop lines on EVERY tick; `_pending_event` / `_fire_event` /
  `_live_stops`; `start_challenge()` as the one definition of arming a
  challenge (routes, tests and the sweep all take it); `STOPS` keyed by
  metrics, `_stop_row`, three evaluators + three SCORING entries + three
  challenges — **Blast freezer** (temp), **The crisis shift** (glucose),
  **Race day goes wrong** (water); `events` + `stopped` in `/state`'s
  challenge block and `events` appended to the attempt record. UI: the
  challenge card is now a Jinja macro over the table (a loop has more
  than one challenge), a live event feed, an AMBUSH chip, and a red
  "Stopped at h:mm" line on a run the crisis ended. 109 invariants +
  verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **An ambush lands on SIM-TIME, not on poll timing.** `advance()`
     still decides how many ticks the wall clock has bought; the new
     `_step` decides how those ticks are cut up, stopping exactly on
     each scheduled event. Without that, an event stamped at +45 min
     would land wherever the browser's poll happened to fall — up to
     2000 ticks late after a hidden tab — and the run a teacher
     rehearsed at home would not be the run the class got. Pinned by
     stepping the same crisis 1 tick at a time and in chunks of 991 and
     demanding byte-identical history and feed.
  2. **Hard stops are tested on every tick, not once per chunk.** Same
     reason: the tick a line was crossed on must not depend on poll
     cadence. Only challenges that HAVE stops pay for it, and a
     challenge with neither events nor stops falls straight through to
     one `sim.step(n)` — pinned, so M24–M28 are untouched.
  3. **A stop closes the WINDOW; it never stops the body.** `t_end` is
     pulled back to the tick the line was crossed, the simulation runs
     on, and the report card gains a row saying what happened and when.
     No game-over screen (kickoff SS2 — fail states report).
  4. **A hard stop ZEROES the run, reusing M26's integrity machinery.**
     Not as punishment: a truncated window scores a FLATTERING
     percentage. A run that crashed twenty minutes in was 100 % in range
     up to then and would have beaten a run that played the whole hour
     out. So the evaluator emits a `stopped` row and SCORING carries an
     integrity rule for it — no new scoring code, and the leaderboard
     shows "NO SCORE" with the reason in words.
  5. **ONE `STOPS` table, read by both sides.** The stepper watches it
     to close the window; the evaluator quotes it to write the row. A
     second copy would eventually name a line nobody enforces. Pinned as
     a test that no stop fires on a healthy resting record — a
     mis-signed comparison would end every run at tick one.
  6. **The schedule never leaves the building.** `/state` ships only the
     events that have LANDED (sim-time, offset, words — never the
     action), and no event line is rendered into the page. An ambush you
     can read in devtools is a timetable. Same working assumption as
     M28's redaction, pinned the same way.
  7. **SWEEP FIRST, and it killed two whole designs before they shipped.**
     - *The kickoff's own example was wrong.* SS4 suggests "a fever
       arriving mid-shift" for the temperature crisis. Built it and
       measured it: with shivering intact, **"drag the room to −10 at
       t=0 and walk away" scored 99 — the top of the table**, because a
       body with a working effector arm defends against anything the
       slider can do, and pre-cooling before a known load is strictly
       optimal. Rebuilt it as an anesthetized patient (all three
       effectors suppressed, which is real physiology) with
       hypermetabolic flares: **still set-and-forget at 91**, because a
       400 W flare outruns the coldest room no matter what, so one
       constant room temperature balances the whole schedule. SPEC
       AMENDMENT, logged not silent, the way M24 amended the pump: the
       temperature crisis is the BLAST FREEZER, because the only lever
       this loop supports is a BUDGET (exercise, capped by exhaustion)
       and an ambush that shrinks what the budget buys.
     - *Glucose: the gym was unsurvivable.* 45 minutes of exercise killed
       every play that dosed any insulin at all — all of them in the ER
       around 1:50. `EXERCISE_UPTAKE` is 2.5 mg/dL·min and
       insulin-independent: 150 mg/dL an hour, whatever the hormones are
       doing. Cut to 30 minutes. Then the ORDER turned out to matter
       more than the length: with the gym after the donuts the exercise
       drain simply cancelled the donut load and ignoring the donuts was
       fine. Gym first, donuts second — two ambushes that pull opposite
       ways — and the window went 3 h → 4 h because a window that is all
       spike and no recovery caps time-in-range at 65 % for everyone.
     - *Water: two hours was too short to dehydrate anybody.* "Never
       pour" scored 96 gold. Lengthened to 3 h, and the runner now
       ARRIVES water-loaded (a `start_actions` liter), so the run opens
       on a stretch where pouring is the wrong move and sweat slowly
       turns that around underneath the class. That one change is what
       made reading the feed worth thirty points instead of nothing.
  8. **The final medal ladders**, all from the sweep, all through
     `start_challenge` + `Runner._step` (the production path):
     - *blast_freezer* (−5 °C, then −12 at +12 min, then −20 at +32;
       shivering and vessel control failed; exercise capped at 50 %):
       50 % duty spread evenly **85**, 48 % 85, the allowance banked into
       the second half 84, 45 % 82, 42 % 78, 35 % 69, 30 % 56 — and the
       SAME 50 % spent in the FIRST half scores **30 and misses**.
       Resting the hour collapses at 0:51. Warming the room or restoring
       a broken part zeroes it; so does 55 % duty. Medals 84 / 72 / 58.
     - *crisis_shift* (type 1, 60 g breakfast, gym +55→+85, donuts +130,
       4 h): 4 U + a juice box in the gym + 2 U for the donuts **86**;
       feeding the gym but ignoring the donuts 83; covering the donuts
       but never feeding the gym 68; 4 U and nothing else 66;
       over-covering the donuts 37; doing nothing 35 at a peak of 334.
       6 U or 8 U up front is in the ER before the gym ends. Medals
       84 / 72 / 60.
     - *race_day* (osmoreceptors dead, arrives with a liter on board,
       spectator's liter +45, pulls up +90, salt tabs +140, 3 h): wait
       out the load, pour while they run, stop when they pull up **93**;
       never pouring 54; every blind rhythm loses — 250 mL/30 min 40,
       /20 min 36, /15 min 25 — and /10 min drowns the runner outright
       (hyponatremia stop). Medals 85 / 70 / 55.
  9. **Two ambushes deliberately reach past what the UI allows**, which
     is what makes them ambushes rather than suggestions: the freezer
     drops the room to −20 °C when the slider's floor is −10, and the
     class cannot undo it — reaching for the thermostat AT ALL trips the
     new `door` integrity row (the row watches for env temp RISING, not
     for a threshold, because the room they were given is not the room
     cold_store gave them). Events go through the same public engine API
     the buttons call; only the app-level policy caps are bypassed.
 10. **The challenge card is now a Jinja macro over `CHALLENGES`.** A
     loop having two challenges broke the per-loop element ids
     (`tempChallengeBest`…), so those became per-card classes and the JS
     finds cards by `data-challenge`. The start-button wording moved
     into the table as `start_label` — it was the last per-challenge
     string still hardcoded in the page.
 10.5 One anti-wedge guard added while reading the stepper back:
     `chunk = min(n, max(1, int(event["t"] - t)))`. Every sim-time in
     this app is a whole second so the gap is never fractional — but a
     chunk of 0 would spin the loop forever, and "hard to wedge
     mid-class" outranks trusting that a later phase keeps the tick a
     whole number. A fractional gap now fires one tick late instead.
 11. VERIFIED LIVE in the browser on real wall-clock, twice.
     *The full run:* "Race day goes wrong" as "Period 4 Blue" at 16×.
     The feed stayed EMPTY through the opening (nothing had happened
     yet), then filled in as things landed — "+0:45 A spectator hands
     your runner a full liter…", "+1:30 They pull up with a torn
     hamstring…", "+2:20 Somebody in the tent gives them electrolyte
     tablets…" (osmolarity 282.7 → 297.6 on that one, a 15 mOsm/L jolt
     in a single tick) — while `document.body` contained no trace of the
     un-fired ambush, checked mid-run. The exercise button flipped
     itself to "off" when the pull-up landed. Held the pour through the
     opening load, poured at +1:13, stopped at the pull-up, covered the
     salt: **GOAL MET, 93 / 100 GOLD**, 100 % in band, saved as run #6,
     feed still on screen beside the report. The sweep predicted 93 for
     that strategy — the number the class gets and the number the sweep
     got are the same number, which is the determinism promise paying
     out. The logged attempt carries all three ambushes at +2700 /
     +5400 / +8400, fired at sim 2737 / 5437 / 8437 against a t_start of
     37: every one exact to the second, through a run driven entirely by
     irregular browser polls.
     *The hard stop:* "The crisis shift" as "Period 4 Red", 8 U up
     front, and the gym at +0:55 finished it — the window closed at
     1:15, the card went red with "Stopped at 1:15 — glucose fell to
     40 mg/dL…", the score read "NO SCORE — …no score for a shift that
     finished in the ER", and the leaderboard logged 0 / 100. Two
     details worth keeping: the SIMULATION carried straight on (glucose
     was 13 at sim 5817 while the graded window had ended at 5287 — the
     body kept going, only the run being graded stopped), and the report
     card shows "✓ time in 70-180 mg/dL: 93%" one line above the ER row.
     That 93 % is exactly the flattering number decision 4 exists to
     stop, sitting there in the classroom as the argument for it.
     Console clean on both runs.
     Note for future sessions: with the preview pane HIDDEN the page's
     poll interval is throttled by the browser (M10's documented
     behavior, not an app bug) — the sim still advances because each
     `/state` request ticks it, but the DOM can lag a poll behind.

## 2026-08-17 — M28: The diagnosis game
- Shipped: M28 contract in `tests/test_invariants.py` (17 tests: case
  table shape, every loop can answer "nothing is broken", the role
  ORDER differs per loop, the redaction allowlist, fail-closed on an
  unlisted field, every case driven through the routes and read the way
  devtools would, the reveal's history identical to an un-blinded run,
  grader purity + partial credit + "none" normalization, the diagnosis
  attempt's frozen fields, no case identifier in the page, rotation
  wrap, refusals). `CASES` (4 per loop, 12 total), `ANSWER_OPTIONS`,
  `VISIBLE_DURING_CASE` + `redact_record`, `grade_answer`,
  `build_case_attempt`, `Runner.case` + `Runner.case_index` + `blind()`,
  `/control diagnose|answer`, the `case` block in `/state`, a 409 from
  `/export.csv` while blind. UI: a Diagnose card per loop (Jinja macro
  ×3), the breaker + Diseases cards hidden while blind, "?" badges on
  exactly the boxes that are also the answers, "set point — ?" on the
  thermo control box, and a "you joined here" marker where the
  fast-forward ended. 97 invariants + verify pass.
- Deferred: nothing.
- Open bugs: none.
- Decisions:
  1. **The redaction gate is an ALLOWLIST, not a blocklist.** A
     blocklist ("hide anything ending in `_enabled`") fails OPEN: the
     field Phase 9 adds leaks the answer and nobody notices. An
     allowlist of what the charts and the diagram actually need fails
     CLOSED — a new field is withheld until somebody lists it on
     purpose. Pinned three ways: every listed name must really exist in
     that engine's record (a typo would silently blank a chart), no
     listed name may end in `_enabled` or be one of `water_access` /
     `fever_offset` / `insulin_sensitivity`, and an unknown field
     injected into a record must not survive the gate.
  2. **A case is picked by INDEX, so no case identifier is in the page
     at all.** `render_template` gets the answer vocabulary and a COUNT,
     never `CASES` — one careless `{{ case.answer }}` would end the
     game. Pinned as a test over the rendered HTML: no case id, no
     brief, no teaching note.
  3. **A case starts a FRESH run and fast-forwards its opening**
     (`sim.reset()` → setup → `start_actions` → `sim.step(warmup_s)`).
     Unlike a preset or a challenge, a case resets: the evidence on the
     charts has to be this case's own. The warm-up is just `step()` —
     deterministic, every tick recorded — and the chart marks where it
     ended, because the class joined a story already in progress and
     should be told so. Type 2 needs ~3 sim-hours to show its signature;
     at 16× that is 11 minutes of class time watching an empty chart.
  4. **The same four answers on every loop, in a DIFFERENT ORDER on
     each.** Cases within a loop often share a brief WORD FOR WORD (the
     same freezing room, the same breakfast, the same long walk) with
     opposite answers, so reading the story instead of the charts earns
     nothing. And the role order is deliberately scrambled across loops
     — pinned as a test — so a class that plays a few can't learn "case
     3 is always the control center".
  5. **"Nothing is broken" is always on the menu, and every loop has an
     intact case** (pinned). A healthy loop working flat out against a
     big disturbance looks alarming; telling that from failure is the
     skill. Fever is the neighbouring case and its answer is CONTROL
     CENTER — the machinery is perfect, the number it defends moved.
  6. **Partial credit: right role, wrong component is 50, not 0.** A
     class that says "an effector has failed" has read the loop
     correctly and then misread one trace, and a gradebook should see
     the difference. Correct 100 / partial 50 / wrong 0, no medal — a
     diagnosis is right or it isn't, and medals are for play. Diagnosis
     attempts never reach a challenge leaderboard (pinned).
  7. **Two places where redaction would have made the DIAGRAM LIE, and
     the fix was to make it say "I'm not telling you" instead.**
     (a) The thermo control box prints the number the loop is defending;
     with `fever_offset` withheld it would have fallen back to "set
     point 37.0 °C" during a fever case — not a hidden answer but a
     false one. It now reads `set point — ?`. (b) The glucose muscle box
     glows with what the tissues HEAR (M19: `total_insulin ×
     insulin_sensitivity`); with the knob withheld it would blaze away
     while the patient sits at 160. It goes neutral and wears the "?".
     **`uptake` is NOT a usable substitute** — the sweep found type 2
     uptake running slightly ABOVE healthy (1.83 vs 1.63) because mass
     action from the high glucose makes up what the insulin can't buy.
     Guessed the other way before measuring. (c) The water kidney box
     needs `kidney_enabled`, so while blind it reads the OBSERVABLE
     instead (`1 − urine_rate/12`): deaf kidneys and no-ADH-at-all then
     look identical, which is honest — in both the kidney isn't holding
     water — and separating them off the hormone trace is the class's
     job. M19/M22's rules are untouched outside a case.
  8. **CASE SWEEP FIRST, and it caught four things.** All 12 cases run
     through their warm-up and read for the evidence a class would have:
     - *temp*: intact at −10 °C settles 36.81 with shiver 0.47 / vaso
       −0.39 and holds; sensor-dead in the SAME room falls 37.00 → 35.53
       in 30 min with all three effectors at exactly 0.00; fever climbs
       through 37.87 with shiver 1.00 (chills while already hot) and
       settles 38.91; sweat-dead on a hot run hits 38.91 with sweat 0.00
       and vaso pinned +1.00.
     - *glucose*, all three meal cases now sharing warm-up AND brief:
       type 1 peaks 315 with insulin **0.00**, stuck at 203; healthy
       peaks 143 with insulin rising to 1.00 and home to 87.9; type 2
       peaks 280 with insulin **railed at 1.00** and still 159 at two
       hours. The hormone trace IS the diagnosis. Sensor-dead: 90 → 68.7
       with insulin 0.17 / glucagon 0.33 dead flat.
     - *water*: deaf kidney and no-ADH are IDENTICAL on osmolarity and
       urine (293.67, 12.00 mL/min at 38 mOsm/L) and differ only in ADH
       (0.87 vs 0.00) — the clinical discrimination, made visible;
       sensor-dead on a walk climbs to 310 with ADH frozen 0.50, thirst
       0.00 and zero self-drinks; intact on the same walk holds ~293 and
       drinks 7 times by itself.
     Fixes the sweep forced: glucose sensor-dead warm-up 4 h → 1 h (the
     steep part of the slide has to be inside the chart's 2-hour
     window), type 2 warm-up 3 h → 2 h (so the peak is visible and it
     matches the other two meal cases), and TWO teaching notes were
     factually wrong — one claimed the type 1 glucagon "behaved
     sensibly" (it runs HIGH, disinhibited, which is the better lesson
     and now what the note says) and one told the class to watch type 2
     uptake "sit low", which it does not.
  9. `visibility`, not `opacity`, for the "?" badge: an opacity-0 badge
     is invisible but still in the text and accessibility tree, so every
     box read as "?" to a screen reader and to anything scraping the
     page. Caught by reading the live page's text, not the pixels.
  10. Fixed in passing: `control()` fed refusal payloads to
     `applyServerState()`, so every 400 flipped the Pause button until
     the next poll put it back. Refusals now leave the controls alone.
     And `makeChart` skips non-finite values, so a series whose field is
     withheld draws an empty panel instead of a polyline of NaN.
  11. VERIFIED LIVE in the browser: the fever case blind — devtools
     showing `core_temp 38.22` with `error −0.78`, `shiver 1`, `vaso −1`
     and nothing naming fever, `set point — ?` on the diagram, badges on
     exactly the 5 answer boxes, breaker + Diseases cards gone, CSV 409.
     Answered control/hypothalamus → RIGHT, 100/100, note, saved as run
     #3, cards back, `set point 39.0 °C` released. Then glucose case 3
     blind (beta box at full glow shouting into a neutral "?" muscle
     box), answered effector/liver → HALF RIGHT 50/100 in amber with
     both components named, CSV back at 200 with all 20 columns
     including `insulin_sensitivity`. A page RELOAD mid-case lost
     nothing (brief, team label, form, hidden cards, badges, marker all
     came back from server state — an M30 checkpoint item, early).
     Console clean; the challenge leaderboards never saw a diagnosis.

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
