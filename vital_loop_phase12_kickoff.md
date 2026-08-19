# Vital Loop — Claude Code Kickoff Prompt
### Phase 12: the paper trail — one page per class period

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M49.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 12 opener:** read `BUILDLOG.md` end to end before touching anything.
Like Phase 11, this phase touches **no engine file at all** — it is teacher
paper, built on data products that already exist. If a milestone seems to need
an engine change, stop and say so: that is a scope conversation, not a patch.

## 1 — What we're building (and why)

Phase 11 made the room visible while class is happening. Phase 12 makes it
leave a record after class is over. One printable page per class period —
"P3's day, on one sheet" — with a team scorecard on top (who played, what they
scored, which diagnoses they got right) and a class debrief underneath (which
case tripped the most teams, which challenge nobody medaled). It reads the
same attempts log the leaderboards read, so the paper can never disagree with
what the class saw on screen.

Priorities unchanged: the biology must be right > the loop structure must be
explicit on screen > aesthetics. The clause for this phase: **the paper
reports finished work, and says so.** No inference, no reconstruction, no
number on the page that the log did not already contain.

## 2 — Locked-in design decisions

**Scope.** The per-period report only. Still deferred, unchanged and on the
candidate list: the `urine_osm` concentrating ceiling (M20/M37) and
hemoconcentration (M38). Both are physiology debts in Phase 6 code and neither
is Phase 12's to touch.

**Settled in the kickoff interview (2026-08-19):**

- **Both halves on one page.** Top: a grade-ready team scorecard. Bottom: a
  short "what the class found hard" debrief. One sheet does the grading and
  starts tomorrow's conversation.
- **Today only.** One report covers one date — the period's runs from that
  day. No date picker in the UI.
- **A printable page, and only that.** `/report/<period>` renders and you
  Ctrl+P it, exactly the M35 worksheet pattern. No CSV export and no
  all-periods sheet this phase.

**Settled by reading the code:**

- **The report reads the ATTEMPTS LOG, never the live room.** A session is
  swept 30 minutes after its tab closes (M33), so by the time anyone prints,
  the room accessor is empty — the log is the only thing that survives the
  day. `period` has been stamped on every attempt since M44 and `wall_time` is
  a local ISO stamp, so "P3, this date" is a clean filter over data that is
  already there.
- **A team appears once it FINISHES a run.** Nothing in the app records
  attendance — a team that joined and never completed a challenge or answered
  a case leaves no record at all. That is a real limit, it is not worth
  inventing an attendance system to close, and **the page must say so in
  words** rather than let a teacher read a short roster as a full one.
- **The date is an ARGUMENT, not a clock read.** The report builder takes the
  date it is reporting on; only the route reads today's date. That keeps the
  data product deterministic and testable, and means a later phase can expose
  a date picker for free.
- **PIN-gated, like the dashboard** (my call, stated here so it is not
  re-litigated): it is teacher paper, and `/teacher`'s PIN already exists.
  The report links from the teacher page, one per period on `periods.txt`.
- **This page is an ANSWER KEY.** It names diagnoses in words, so unlike the
  dashboard it is NOT safe to project while a case is live. The page says
  that on itself, above the fold.

**Standing rules restated for this phase:**

- **The report is a data product, not a template** (kickoff §5). A pure
  function returns the whole report as plain data; the template only renders
  it. A future gradebook CSV reads that same function, never the HTML.
- **Frozen schemas grow by APPENDING** (the rule since M12). This phase should
  need no new attempt field at all — if one seems necessary, say why first.
- **Nothing invented.** Every number on the paper comes out of a stored
  attempt. Where the log cannot answer something, the page says the log cannot
  answer it.

## 3 — Tech stack

No new dependencies. `report.py` beside `attempts.py` / `periods.py` (plain
Python, no Flask, so pytest can drive it with a crafted log and no server);
the page is one self-contained Jinja template styled like `worksheet.html`,
which already carries the serif print look and the `@media print` rules.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M48 — The report as data, and a console demo.** `report.py`:
  `class_report(attempts, period, date)` -> the whole report as plain data —
  per-team rows (runs played, best score and medal per challenge, cases
  answered and whether each was right) plus the aggregate half. PURE: takes
  the log and the date as arguments, reads no clock, no Flask import. Pin at
  least: the period and date filters (including a pre-M44 keyless record
  landing in Unassigned, never in P3); a period with no runs returning an
  empty-but-valid report rather than raising; teams sorted stably; and the
  aggregate counting what it claims to count.
  `python -m report_demo`: a seeded two-period day printed in the console.
  ✅ *Checkpoint: I can read P3's day in text before any HTML exists.*
- **M49 — The scorecard, printable.** `/report/<period>` behind the teacher
  PIN, rendering the top half: the identity block (period, date, how many
  teams), the team table, and the "teams appear here once they finish a run"
  line. Links from `/teacher`, one per period. Styled and print-ruled like the
  M35 worksheets. Pin: the PIN gate refuses in words; an unknown period is a
  plain-English 400, not a stack trace; the page renders with zero runs.
  ✅ *Checkpoint: I print P3's scorecard and could grade from it.*
- **M50 — The debrief.** The bottom half: which case the class got wrong most
  often (and what the right answer was), which challenges went medal-less,
  and how many teams got as far as a case at all — each line phrased as
  something to reteach, in the curriculum vocabulary the app has used since
  M0. Where a claim needs more runs than the log holds to be meaningful, the
  line says so instead of overstating a sample of two.
  ✅ *Checkpoint: I read the bottom of the sheet and know what to open
  tomorrow's class with.*
- **M51 — The full pass, and the phase closes.** Drive it through production
  routes: two periods on one day, a period with nothing, an Unassigned pile, a
  date boundary (yesterday's runs must not appear on today's sheet), the PIN
  gate, and a report printed while a case is still blind elsewhere in the room
  (it is an answer key — confirm nothing about it reaches a STUDENT payload).
  Regression: both engine hashes untouched, the cookieless world unchanged,
  Phase 11's join / boards / dashboard exactly as M47 left them, all four tabs
  and their grammar intact, worksheets still print. `BUILDLOG.md` records the
  phase closed and the Phase 13 candidates.
  ✅ *Checkpoint: a rehearsed day, four periods, four sheets, and nothing
  wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 13.**

## 5 — Notes / data products

- **`class_report()` is the accessor** (kickoff §5): one pure function
  returning the whole report as plain data, so the printable page, a future
  gradebook CSV and any later per-period view all read one source and can
  never drift apart. The template computes nothing.
- **No new attempt fields are expected.** `period` (M44), `label` (M27),
  `wall_time`, `points`, `medal`, `mode`, `name`, `correct` and `answer`
  already carry everything the paper needs.
- **The date filter is `wall_time[:10]`**, local and naive, matching how the
  stamps were written since M26 — not a timezone conversion invented at read
  time.
- **Team names are TEAM names** (kickoff §2): the paper carries what the join
  screen and the cards recorded, and no student names are introduced by this
  phase.
- **No engine file changes in this phase.**
