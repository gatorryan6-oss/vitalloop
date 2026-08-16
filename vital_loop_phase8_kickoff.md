# Vital Loop — Claude Code Kickoff Prompt
### Phase 8: The game layer — score it, race it, diagnose it, survive it

## 0 — Read state first

Read `BUILDLOG.md` before doing anything: confirm M0–M25 are committed
(seven phases complete), the standing kit exists (`verify.py`, `run.bat`,
`tests/test_invariants.py`, port 5083), and lead with any open bugs logged
there. Earlier phases are **extended, never rebuilt** (CLAUDE.md standing
rule 3). Like Phase 7, this is pure APP-level machinery — tables, pure
functions, one file on disk, one card per mode. **No engine file changes
in this phase at all**, and guards (h), (k), (n), (s) in the invariants
file already prove it. The working agreement in `~/.claude/CLAUDE.md`
still governs: explain before doing, small runnable increments, STOP at
the phase checkpoint, patch with decimal milestones, commit per
milestone, append to `BUILDLOG.md` every milestone.

## 1 — What we're building (and why)

Phase 1 locked "no win/lose, no score" and deferred a game layer. Phase 7
built the machinery it would need — an authored challenge, a stamped sim-time
window, and an honest report card computed server-side from history — and
stopped deliberately at MET / NOT MET. Phase 8 arms it, in four modes that
each ask the class for a different kind of thinking:

- **Score & medals** — the report card gains points and a tier, so a run
  can be *beaten*. Replay becomes worth doing.
- **Head-to-head** — two teams run the identical deterministic challenge
  and the app puts their report cards side by side. The engine's
  determinism is what makes the comparison fair: same inputs, same
  curves, so the only variable is the students' physiology.
- **Diagnosis** — the app hides a broken part and the class must NAME it
  from the charts and the diagram. This is the one genuinely new verb.
  Every phase so far taught *managing* a loop; none has yet tested
  *reading* one, which is the skill the exam actually asks for.
- **Crisis** — a challenge that ambushes you on a schedule: a second meal
  at +45 min, a heat spike, an infection. Same tools, no time to think.

The order matters. Mode 1 builds the scoring substrate and the on-disk
attempts log that modes 2–4 all read, so each later milestone is small.

## 2 — Locked-in design decisions

(Settled in the Phase 8 interview — don't re-litigate. Everything not
listed carries over from Phases 1–7 unchanged.)

- **The game is a layer, not a mode switch.** With no game started the app
  is exactly the Phase 7 sandbox: no points on screen, no medals, no
  leaderboard. A teacher who wants to explore for forty minutes never has
  to dismiss a game. **Scoring never touches the Phase 7 report** —
  `score_report()` is a SECOND pure function reading the same rows the
  evaluator already returns, so the honest MET / NOT MET card stays
  exactly as it is and the points ride on top.
- **Medal thresholds are calibrated by sweep, then pinned — never
  guessed.** M24 pinned targets only after a 12-strategy sweep, and that
  sweep overturned the spec's own guess about the pump. Same rule here:
  before gold/silver/bronze go in the table, sweep real strategies for
  each challenge and set the tiers so the textbook play earns gold and
  sloppy play doesn't. The sweep numbers go in `BUILDLOG.md`. **If the
  sweep contradicts this document, the sweep wins** — amend the spec in
  the log, out loud, the way M24 did.
- **No randomness, anywhere, still.** Determinism is a locked invariant
  and the game layer must not smuggle in a die roll. Diagnosis cases come
  from a fixed `CASES` table advanced by a rotation counter (and the
  teacher can pick a case outright); crisis events fire at stamped
  **sim-time** offsets from the challenge start. A class that replays
  case 3 sees the identical run — that's rehearsal, and it's a feature.
- **The server withholds the answer; the JS is not trusted to hide it.**
  A diagnosis case is only a game if the answer isn't in the page.
  Today's `/state` ships every `*_enabled` flag and the diagram grays out
  the broken box — that IS the answer key. So while a case is live and
  unanswered, the snapshot **redacts** the enabled/preset fields
  server-side and `/export.csv` refuses for that loop with a plain-English
  message. On reveal the full history is released, retroactively and
  complete, including the CSV. Assume a student opens devtools, because
  one will.
- **Fail states report; they never splash.** Crisis mode can end a run
  early ("glucose hit 38 — the patient is in the ER"), but the result is
  a report card that says what happened and at what sim-time, in the same
  grammar as every other report. No game-over screen, no sad noise, no
  red flashing. The tone that has carried seven phases doesn't change
  because there are points now.
- **Results persist as one JSON file** (`data/attempts.json`), written
  atomically (temp file + replace) so a crash mid-write can't corrupt the
  morning's scores, capped at the most recent 500 attempts so a classroom
  machine never fills up, and **loud on failure** — if the file can't be
  written the UI says so plainly rather than pretending the score saved.
  It's a text file, so the Phase 1 "no database" promise holds. `data/`
  is gitignored: student scores are runtime data, not source.
- **Attempt labels are team names, not student names.** Free text, capped
  short, and the placeholder says "Team 3" / "Period 2 Red". A file of
  named minors on a teacher's laptop is a thing we simply don't create.
- **Projector model stays.** One app, teacher drives, class argues — the
  three shared Runners are unchanged. Per-student devices are the Phase 9
  headline candidate, so Phase 8 must not close that door: game state
  hangs off the `Runner` (like `preset` and `challenge` already do) and
  the attempts log is keyed by label, so swapping one global Runner for
  one-per-session later is a plumbing change, not a rewrite.

## 3 — Tech stack

Unchanged: Flask + vanilla JS + hand-drawn SVG, polling `/state`. New in
`app.py`: `MEDALS` thresholds on each `CHALLENGES` entry, a pure
`score_report()`, a `CASES` table for diagnosis, `EVENTS` on crisis
entries, and an attempts-log module (load / append / atomic save). New in
`/control`: `diagnose`, `answer`, and a `label` on challenge start. New in
`/state`: score + medal on the report, the redaction gate, the crisis
event feed. `tests/test_invariants.py` gains the Phase 8 contract. No new
dependencies — `json` and `pathlib` are stdlib.

## 4 — Milestones

Continue Phase 7's numbering. Each milestone ends runnable; a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M26 — Points, medals, and the attempts log.** FIRST extend
  `tests/test_invariants.py` with the Phase 8 contract: (a) `score_report()`
  is pure — fed a crafted report it returns exact points and tier;
  (b) every challenge has all three medal thresholds, strictly ordered
  gold > silver > bronze; (c) the attempts log round-trips (append →
  save → load → identical), starts empty with a loud message on a missing
  or corrupt file instead of crashing, and honors the 500 cap; (d) the
  engines are untouched (guards h/k/n/s). Then sweep each of the three
  challenges for real strategies, set the tiers from the sweep, and build
  it: points and medal on the existing report card, an attempt appended
  when a window closes, and a "best so far" line on each challenge card.
  ✅ *Checkpoint: I play the type 1 shift, get a medal and a number, close
  and relaunch the app, and my best run is still on the card.*

- **M27 — Head-to-head.** A label box next to each challenge's Start
  button ("Team 3"), stamped onto the attempt. A compare view putting two
  finished attempts' report cards side by side, row for row, so the class
  can see WHERE one team beat the other — not just that they did. A
  per-challenge leaderboard reading the log. Nothing new is computed:
  every number on screen was already a data product.
  ✅ *Checkpoint: two teams run the aid station, and the projector shows
  both report cards side by side with the leaderboard under them.*

- **M28 — The diagnosis game.** A `CASES` table per loop (each case = a
  setup drawn from the existing preset/breaker vocabulary + the correct
  answer + a one-line teaching note for the reveal). Server-side
  redaction while a case is live: no enabled flags in `/state`, breaker
  card and disease banner hidden, diagram boxes drawn in a neutral
  "unknown" state rather than grayed, CSV refused with a plain-English
  reason. An answer form in curriculum vocabulary — which part failed
  (receptor / control center / effector, and *which* effector) — graded
  on submit, then the reveal: the truth, the teaching note, the full
  history released, and the CSV back.
  ✅ *Checkpoint: I start a blind case, the class argues from the charts
  alone with nothing in devtools to give it away, we submit "the receptor
  is lying," and the app tells us whether we're right and why.*

- **M29 — Crisis mode.** `EVENTS` on a challenge entry: a list of
  (sim-time offset, action, plain-English announcement), fired by the
  same public API the buttons already call — a second breakfast at
  +45 min, the room jumping 15 °C, a fever arriving mid-shift. A live
  event feed on the card so the class sees what just hit them and when,
  and hard-stop lines that close the window early with an honest report.
  One crisis variant for each of the three loops.
  ✅ *Checkpoint: I run the crisis shift, get ambushed at 45 minutes, see
  it named in the feed as it lands, and read it in the report afterward.*

- **M30 — The full pass and the phase close.** All four modes across all
  three loops on the projector, back to back. Confirm the sandbox is
  still gameless when no game is running (the Phase 7 experience,
  untouched), that a page reload mid-game loses nothing, and that
  relaunching the app preserves the log. `BUILDLOG.md` records the phase
  closed and the Phase 9 candidates.
  ✅ *Checkpoint: I teach a full period off this thing — disturb, break,
  name, challenge, score, race, diagnose, survive — and nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 9.** (Phase 9 candidates, decided then: per-student sessions on
their own devices, SIADH + an ADH-override knob, cross-loop coupling
(mellitus polyuria — the glucose loop finally talking to the water loop),
student worksheets keyed to the CSV and attempts exports.)

## 5 — Notes / data products

- **The attempts log is the phase's data product.** Frozen fields per
  attempt: `id`, `wall_time` (ISO string), `loop`, `mode`
  (challenge | diagnosis), `name`, `label`, `points`, `medal`, `met`,
  `rows` (the report card verbatim), and for diagnosis the submitted
  answer and whether it was right. A worksheets phase, a gradebook
  export, or a per-class comparison all read THIS file — never a
  screenshot, never a scrape of the DOM. Add fields by appending, the way
  the CSV columns have grown since M12.
- **Wall-clock time is app-level, and that's fine.** Attempts need a real
  timestamp to sort a leaderboard, and `app.py` already reads the clock
  for tick pacing. The invariant is that the *engine* never does — nothing
  in `engine/` may read the clock or use randomness, and Phase 8 adds no
  engine code at all.
- **Redaction is a delivery gate, not a data loss.** The engine still
  records every field every tick during a blind case; the app just
  declines to ship the answer until the class has committed to one. The
  released history after a reveal must be complete and identical to what
  an un-blinded run would have produced — verify that, don't assume it.
- **Scoring purity keeps the report honest.** The evaluator's job is to
  say what happened; the scorer's job is to say what it's worth. Two
  functions, two responsibilities, both pure, both tested on crafted
  records. If a future phase wants different tiers for an honors section,
  it swaps the scorer and the physiology never notices.
