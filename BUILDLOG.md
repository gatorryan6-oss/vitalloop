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

- **Committed:** M31 — Phase 9 underway. Spec:
  `vital_loop_phase9_kickoff.md` (scope picked 2026-08-17: per-student
  sessions + SIADH + student worksheets; **cross-loop coupling deferred
  to Phase 10**). The four kickoff-interview questions went unanswered,
  so the spec carries flagged ASSUMPTIONS, changeable before their
  milestones: LAN + cookie sessions (no join screen), leaderboard-only
  (no teacher dashboard), worksheets as printable app routes (no docx),
  verbal class direction (no mode gating).
  Remote: https://github.com/gatorryan6-oss/vitalloop
- **Next up:** M36 — the lab pass and the phase close.
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
