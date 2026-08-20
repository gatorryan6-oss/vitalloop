# Vital Loop — Claude Code Kickoff Prompt
### Phase 15: how it broke — the third question a diagnosis has to answer

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M61.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 15 opener:** read `BUILDLOG.md` end to end before touching anything.
This phase changes **no engine file** — the physiology is already there. What
changes is the app's answer vocabulary, its grader, and every one of the 16
existing cases. Engine hashes must all come back untouched.

## 1 — What we're building (and why)

A diagnosis in this app currently answers two questions: which box of the loop
failed, and which component. Phase 14 broke that. Insulinoma is beta-cell
tissue secreting regardless of the sensor; type 1 diabetes is beta-cell tissue
that stopped. Same box, same component, opposite direction, opposite chart —
and identical answers. The app cannot tell them apart, which means it cannot
ask about them.

Phase 15 adds the third question: **how did it fail?** Not working, stuck on,
or too slow. That single dimension turns Phase 14's three diseases into blind
cases, and it names a distinction the curriculum already makes — loss of
function, gain of function, and mistiming are different kinds of broken.

Priorities unchanged: the biology must be right > the loop structure must be
explicit on screen > aesthetics.

## 2 — Locked-in design decisions

**Scope.** The direction dimension and the three cases it unlocks. Still on
the candidate list, untouched: multi-day scenarios, persistent assignments,
the wide-format gradebook.

**Settled in the kickoff interview (2026-08-19):**

- **A third dropdown**, not a longer component list. A case asks which box,
  which component, and how it failed. Keeping the three ideas separate is the
  point; folding mode into the component list would roughly double a list
  students already scroll and would conflate "which part" with "what went
  wrong".
- **All three must match to be correct.** Getting the box and the component
  right while calling an insulinoma a type 1 is exactly the error this phase
  exists to catch, so it cannot still score 100. Existing cases barely get
  harder because their mode is "not working", which is also the default
  selection.
- **All three Phase 14 diseases become cases**: insulinoma, reactive
  hypoglycemia, and treated mellitus.

**Settled by reading the code:**

- **Sixteen cases exist and every one of them is "not working" or "nothing
  is broken"** — twelve parts-switched-off and four intact loops. The
  migration is mechanical and bounded, and after it every existing case must
  still grade exactly as it does today.
- **`grade_answer` already normalizes the "nothing is broken" role**, forcing
  its part to `none` so a stray dropdown does not mark a class down. The mode
  must be normalized the same way, for the same reason.
- **Treated mellitus has the same answer as untreated mellitus** — control
  centre, beta cells, not working — and that IS its lesson. The numbers look
  better because insulin is being given; the broken part has not changed. The
  trap the case sets is answering "nothing is broken", and the teaching note
  should say so.
- **Case counts are pinned in several "Phase N untouched" tests** (temp 4,
  glucose 4, water 5). Glucose goes to 6 and body to 4 this phase. Those pins
  move DELIBERATELY, in the same commit, with the change named in the message
  — they are not obstacles to route around.

**Standing rules restated for this phase:**

- **The redaction stays fail-closed.** The mode vocabulary is rendered in the
  page exactly as roles and parts already are (M28: the vocabulary is safe,
  the ANSWER is not). No new record field may enter `VISIBLE_DURING_CASE`.
- **Verdict tiers stay three.** Correct / partial / wrong, with `partial`
  still meaning "right box, not the rest". Adding a fourth tier for
  "right box and part, wrong mode" is tempting and is NOT in scope; if it
  turns out to be needed, say so and log it rather than slipping it in.
- **Frozen shapes grow by APPENDING** (M12). A case's stored `answer` gains a
  key; the attempt record's fields do not change shape otherwise.
- **Calibrate the new cases by playing them.** A case is only a case if its
  chart actually distinguishes it — drive each one and show the numbers that
  make it diagnosable before pinning it.

## 3 — Tech stack

No new dependencies, no engine changes. Vocabulary and cases are tables in
`app.py`; the third dropdown is one more `<select>` in the diagnose card the
M28 macro already builds.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M61 — The third question.** `ANSWER_OPTIONS` gains `modes` (not working /
  stuck on / too slow / nothing is broken); every existing case's answer gains
  its mode; `grade_answer` compares all three, normalizes mode for the
  intact-loop answer, and `_truth_line` says the mode in words so the reveal
  and the class report keep quoting the same sentence. The diagnose card grows
  a third dropdown defaulting to "not working". Pin: all 16 existing cases
  still grade CORRECT when answered as they always were; right box + right
  component + wrong mode is no longer correct; the intact-loop answer still
  ignores stray dropdowns; every engine hash unchanged.
  ✅ *Checkpoint: I answer an old case exactly as before and still score 100,
  and I can now get one wrong in a new way.*
- **M62 — The three cases the dimension unlocks.** Insulinoma and reactive
  hypoglycemia on the glucose loop, treated mellitus on the coupled body —
  each with a brief, a warmup, a speed, an answer and a teaching note in the
  app's own vocabulary. Play each one first and report what makes it
  diagnosable: for insulinoma, the sugar falling and staying down with
  glucagon pinned; for reactive hypoglycemia, the high peak and the dip two
  hours later; for treated mellitus, better numbers with the same broken part.
  Move the case-count pins deliberately.
  ✅ *Checkpoint: I run insulinoma and type 1 back to back and the charts tell
  me which is which.*
- **M63 — The full pass, and the phase closes.** Every case in the app driven
  through the production routes and answered with its truth, the new ones
  included; the blind-case redaction still holding under a student's devtools;
  Phase 14's assignment layer still handing out sets that name nothing (the
  role analysis groups by BOX, which the new dimension must not disturb); the
  report, CSV and dashboard all still honest. Confirm Phases 11–14 otherwise
  untouched and all engine hashes unchanged. `BUILDLOG.md` records the phase
  closed and the Phase 16 candidates.
  ✅ *Checkpoint: sixteen old cases and three new ones, all diagnosable, and
  nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 16.**

## 5 — Notes / data products

- **The stored answer grows a key, it does not change shape.** A case's
  `answer` becomes `{role, part, mode}`; the attempt record's `answer` follows
  it, and everything that reads attempts keeps working.
- **The role analysis (M54) still groups by BOX.** Mode is a new dimension for
  grading, not a new grouping — "this class cannot spot an effector" must keep
  meaning what it means, and Phase 14's assignment sets must keep being built
  from the role alone.
- **One phrasing, still.** `_truth_line` is the single sentence the reveal and
  the report both quote; the mode joins that sentence rather than getting a
  second wording somewhere else.
- **No engine file changes in this phase.** If a milestone seems to need one,
  stop and say so.
