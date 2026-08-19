# Vital Loop — Claude Code Kickoff Prompt
### Phase 14: the loop closes on the teacher — assign what the class missed

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M58.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 14 opener:** read `BUILDLOG.md` end to end before touching anything.
**This phase changes `engine/glucose.py`** (two new knobs, both idle by
default), so record that engine's regression hashes FROM THE COMMITTED CODE
before editing, the way M52 did. Idle-by-default means those hashes must come
back UNCHANGED — if one moves, the knob is not idle and that is a bug, not a
re-recording.

## 1 — What we're building (and why)

Phase 12 gave the teacher a record of the day. Phase 13 taught that record to
say *which box of the loop* a class cannot spot. Phase 14 does the obvious
next thing: lets you act on it in the same lesson. One click on "this class
cannot spot an effector" hands every device in that period a targeted set of
exactly those cases — measure, reteach, re-measure, without typing anything on
the board.

Alongside it, three diseases for the two loops that are thin: **insulinoma**
(an effector stuck ON — a failure mode this app has never shown), **reactive
hypoglycemia** (secretion that overshoots), and **treated-but-poorly-
controlled mellitus** for the coupled body, which has had exactly one disease
since Phase 10.

Priorities unchanged: the biology must be right > the loop structure must be
explicit on screen > aesthetics.

## 2 — Locked-in design decisions

**Scope.** The assignment layer plus the three diseases. Not in scope, and on
the candidate list: the wide-format gradebook (wait until the long one
actually annoys) and multi-day scenarios.

**Settled in the kickoff interview (2026-08-19):**

- **Assignments broadcast to a PERIOD.** You click assign on P3's report;
  every device that joined P3 picks the set up on its next poll. No codes, no
  new student flow — it reuses the Phase 11 period plumbing. A device that
  skipped joining does not get one, exactly as it does not get a scoped
  leaderboard.
- **One click from the debrief.** The line that already says "this class
  cannot spot an effector" grows a button that assigns every case with that
  answer, across all four loops. No case-picking UI this phase.
- **Three diseases**, chosen by the human: insulinoma, reactive hypoglycemia
  (both glucose), and treated-but-poorly-controlled mellitus (coupled body).

**THE RULE THAT MAKES OR BREAKS THIS PHASE:**

- **An assignment must never name the box it is about.** The set exists
  *because* the answer to every case in it is "effector" — so telling a
  student that is handing them the answer key. The teacher's screen names the
  role; **the student's payload carries a neutral label and case INDICES and
  nothing else** ("Follow-up set — 3 cases"). This is the M28 gate applied to
  a new surface, the working assumption is still that a student opens
  devtools, and it gets pinned as an invariant before the feature is built.

**Settled by reading the code:**

- **Two new engine knobs, both idle by default.** `_islets()` computes
  `insulin` from sensed glucose and zeroes it when the beta cells are off.
  Insulinoma is a FLOOR on that value that ignores the sensor
  (`set_autonomous_insulin`, default 0.0); reactive hypoglycemia is a GAIN on
  it before clamping (`set_insulin_gain`, default 1.0). Never called → both
  idle → every glucose hash unchanged.
- **The third disease needs no engine change at all**: beta cells off plus a
  too-small basal rate are both knobs that already exist. It is a PRESET, and
  saying so is the point — treatment that changes the curve without fixing
  the loop.
- **The new diseases are presets, not cases, this phase.** A case asking
  "which part failed" cannot currently distinguish an effector switched OFF
  from one stuck ON — both answer "effector / beta cells". Giving the answer
  vocabulary a DIRECTION is a real design question and belongs to its own
  phase, not smuggled in here.

**Standing rules restated for this phase:**

- **Sweep before pinning.** It has now overturned a guess in seven phases,
  most recently M53's tenfold. Calibrate both new diseases by sweep and show
  the numbers before pinning any medal, threshold or teaching claim.
- **Frozen shapes grow by APPENDING** (M12), and any new `/state` block is
  designed for a student reading it in devtools.
- **Assignments are live-room state**, like the registry: they live in memory
  and a restart clears them, which is consistent with how every other
  in-class thing behaves (M33). Say so on screen if it matters.

## 3 — Tech stack

No new dependencies. Engine work is plain Python; the assignment is a small
server-side table plus one `/state` block and one banner, all reusing the
period machinery from Phase 11 and the case machinery from M28.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M57 — Three diseases, two knobs.** Record the glucose hashes from
  committed code FIRST. Add `set_autonomous_insulin` (a floor the sensor
  cannot argue with) and `set_insulin_gain` (secretion that overshoots), both
  idle by default. Sweep both: how low does insulinoma drive the sugar, how
  long does it take, and does reactive hypoglycemia actually produce a dip a
  class can SEE a few hours after a meal — report the numbers before choosing
  the preset values. Then the three presets, with banners in the app's
  existing disease vocabulary. Pin: every glucose hash UNCHANGED (idle knobs);
  insulinoma drives glucose below the hypo line and keeps it there while the
  sensor reads fine; reactive hypoglycemia overshoots DOWNWARD after a meal
  and recovers; poorly-controlled mellitus is measurably better than untreated
  and measurably worse than healthy.
  ✅ *Checkpoint: `python -m engine.disease_demo` (or a new demo) tells all
  three stories in numbers.*
- **M58 — Assignments exist, and they give nothing away.** Server-side
  assignment per period; a button on the debrief's role line; `/state` carries
  a NEUTRAL block (label + case indices + how many are done) to devices in
  that period; a student banner offering the next unanswered case, which
  starts through the existing M28 case flow so attempts log normally. Pin the
  gate FIRST: no role name, no answer vocabulary, nothing about *why* these
  cases, anywhere in the student payload or page.
  ✅ *Checkpoint: I click one button on P3's sheet and a phone in P3 shows a
  follow-up set that never says the word "effector".*
- **M59 — Did it work?** The teacher can see the assignment land: the
  dashboard shows per-device progress through the set, and the report shows
  the same cases answered again — including whether the class got them right
  the SECOND time, which is the whole point of the loop this phase closes.
  Read from the attempts log, which already stamps period and case.
  ✅ *Checkpoint: I assign, they answer, and the sheet shows me whether the
  reteach took.*
- **M60 — The full pass, and the phase closes.** Everything through the
  production routes: three new diseases in sandbox and on the four tabs,
  assignment broadcast to two periods without crossing over, the no-spoiler
  gate under a student's devtools, progress on both teacher surfaces, and the
  CSV/report still honest. Confirm Phases 11–13 untouched, all glucose hashes
  unchanged, the repaired kidney still capped, and the lesson grammar intact.
  `BUILDLOG.md` records the phase closed and the Phase 15 candidates.
  ✅ *Checkpoint: a rehearsed period that measures, reteaches and re-measures,
  and nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 15.**

## 5 — Notes / data products

- **The assignment is a data product**, not a UI state: a small structure the
  teacher's surfaces and the student payload both read, with the student's
  view a strict REDACTION of it (label + indices), never a different object
  assembled by hand.
- **Progress is computed from the attempts log**, not tracked separately —
  the log already carries period, case and correctness, and a second source of
  truth about who answered what is exactly the drift this project keeps
  refusing to build.
- **Both new knobs are idle by default and must stay that way.** Their being
  idle is what keeps Phases 2–13 byte-identical, and it is pinned by the
  existing glucose hashes rather than by hope.
- **New preset entries join `PRESETS`** with banners in the same vocabulary as
  fever / type 1 / central DI, and the invariants suite's grammar checks apply
  to them automatically.
- **No new answer-key field may enter `VISIBLE_DURING_CASE`.** The allowlist
  fails closed; leave it that way.
