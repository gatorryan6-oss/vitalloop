# Vital Loop — Claude Code Kickoff Prompt
### Phase 13: the repair — one kidney, one law, and the paper gets sharper

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M52.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 13 opener:** read `BUILDLOG.md` end to end before touching anything.
**This phase changes engine code — the first time since Phase 10.** Before
editing `engine/water.py` or `engine/body.py`, record the regression hashes of
their scripted runs FROM THE COMMITTED CODE, the way M31 and M37 did. A hash
taken after the edit proves nothing. The old hashes stay in `BUILDLOG.md` as
history when the new ones replace them.

## 1 — What we're building (and why)

Twelve phases have added loops, then a room, then paper. Phase 13 pays off the
two places the model is knowingly wrong, and then sharpens the paper with the
best number still sitting unused in the log.

The kidney is the repair that matters. A real nephron cannot concentrate urine
past about 1200 mOsm/L, so solute that must leave drags water out with it —
that is osmotic diuresis, and it is why a salty meal makes you pee more, not
less. Phase 10 taught the app exactly this law, but only for sugar arriving
from another loop; the water loop's own salt was left un-ceilinged at M20 and
deliberately not fixed at M37 because Phase 6 was not Phase 10's to rewrite.
It is Phase 13's. After this, there is one kidney obeying one law, whatever
the solute is.

Priorities unchanged and, this phase, decisive: **the biology must be right** >
the loop structure must be explicit on screen > aesthetics. That ordering is
the whole reason this phase outranks another feature.

## 2 — Locked-in design decisions

**Scope.** Three things: the concentrating ceiling, hemoconcentration, and two
app-level additions to the paper (role analysis, gradebook CSV).

**Settled in the kickoff interview (2026-08-19):**

- **The ceiling is 1200 mOsm/L**, confirmed by the human as the figure the
  curriculum uses. The constant `MAX_URINE_OSM = 1200.0` already exists in
  `engine/water.py` (added at M37) and already carries that value.
- **Apply the fix everywhere and re-record the hashes.** One physiology,
  correct in every scenario — no flag, no second kidney. Sweep FIRST and show
  which scenarios move and by how much; keep the superseded hashes in the
  build log as history.
- **The gradebook CSV is long format**: one row per team per challenge (and
  per case), so a team playing three challenges never produces ragged columns.

**Settled by reading the code (the arithmetic below was run, not recalled):**

- **The defect is one line.** `engine/water.py` obligates flow from
  `self._tubular_load` only — the foreign solute — and never from the loop's
  own `excretion`. With ADH high and a salt bolus aboard, `urine_osm` sails
  past 1200 because the flow never rises to carry the salt out.
- **The correct law is the one Phase 10's kickoff already wrote down:**
  `urine_rate = max(what ADH allows, what the TOTAL solute obligates)`. M37
  implemented an ADDITIVE approximation of it for the foreign solute alone.
  Replacing that with the real law is the fix, and it is a change to BOTH
  engines — the coupled body's mellitus numbers move too. Expect to re-record
  both hashes, not just water's.
- **Everyday runs will not move, and here is why.** At rest, metabolic waste
  (0.45 mOsm/min) obligates 0.38 mL/min, while ADH already allows 0.5–12
  mL/min — so the ceiling binds only once excretion passes ~0.6 mOsm/min,
  which takes a salt load with ADH high. **Confirm this by sweep; do not take
  it on trust from this document.**
- **Hemoconcentration belongs to the coupled body only.** The standalone
  glucose loop has no water compartment to concentrate into, so there is
  nothing to add there and nothing about Phase 2 changes.

**Standing rules restated for this phase:**

- **A pinned behavior that genuinely conflicts is a conversation, not a
  loosening** (CLAUDE.md). If the ceiling breaks an M20/M31/M37/M38 pin, show
  the human the conflict and stop. Re-recording a HASH is expected and
  approved; quietly weakening an assertion about physiology is not.
- **Sweep before pinning.** It has overturned a guess in six phases now,
  including M38's own measurement of the effect M53 is about to add.
- **Frozen record shapes grow by APPENDING** (the rule since M12).
- **The report is a data product** (M48): the role analysis and the CSV both
  read `class_report()`, and the CSV computes nothing the page does not.

## 3 — Tech stack

No new dependencies. Engine work is plain Python in `engine/`; the CSV reuses
the `/export.csv` streaming pattern; the role analysis extends `report.py` and
its catalog seam.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M52 — One kidney, one law.** Record both regression hashes from committed
  code FIRST. Then sweep: for a rest day, a salty snack, a desert run, DI,
  SIADH, and an untreated mellitus body, report `urine_osm` and `urine_rate`
  before and after the change, and say plainly which scenarios move. Then
  replace the additive term with
  `urine_rate = max(adh_allows, total_solute / MAX_URINE_OSM * 1000)` and let
  `urine_osm` fall out of it. Pin at least: `urine_osm` never exceeds
  MAX_URINE_OSM in ANY scenario (the whole point); a rest day is unchanged;
  a salt bolus now produces MORE urine, not less, with the concentration
  pinned at the ceiling; the M37 mellitus signature survives (flooding urine,
  loaded with solute, ADH at maximum); DI still floods DILUTE. Re-record both
  hashes, keeping the old ones in the log.
  ✅ *Checkpoint: `python -m engine.water_demo` — the salty lunch now makes
  the body pee more, and the urine stops being physically impossible.*
- **M53 — Hemoconcentration: the sugar in less water.** M38 measured this at
  +3 to +9 mg/dL over a class period and deferred it. Sweep again first — the
  ceiling may have changed the water numbers it depends on. Then the coupled
  body reports glucose as measured in the water that is actually left. Pin:
  with water within reach the effect stays small and the body still
  compensates; with water withheld it is visible and makes the M38 spiral
  worse, monotonically; an uncoupled glucose run is byte-identical.
  ✅ *Checkpoint: `python -m engine.body_demo` — dehydration now nudges the
  sugar up, and I can see how much.*
- **M54 — Which part of the loop the class cannot spot.** The report's debrief
  groups missed cases by ROLE — receptor / control center / effector — so the
  sheet says "this class could not spot a broken effector (4 of 6 teams)"
  rather than only naming individual cases. Roles come through the M48 catalog
  seam; `report.py` stays pure. Honest about thin samples, as M50/M50.5 set
  the standard, and silent when there is nothing to say.
  ✅ *Checkpoint: I read one line and know which box of the loop to reteach.*
- **M55 — The gradebook CSV.** `/report/<period>.csv` behind the same teacher
  PIN: one row per team per challenge and per case — team, period, date, loop,
  what they played, best score, medal, runs, and for cases whether the first
  answer was right. Frozen column order, pinned. It reads `class_report()`,
  so the sheet and the spreadsheet can never disagree.
  ✅ *Checkpoint: I open it in Excel and the scores are ready to paste.*
- **M56 — The full pass, and the phase closes.** Drive everything through the
  production routes: all four loops, the repaired kidney in sandbox and in
  challenges and in blind cases, the report and its CSV across two periods,
  the PIN gate, the answer-key leak check. Confirm Phases 11–12 are untouched
  (join, boards, dashboard, sheets) and that the four loops still carry the
  whole lesson grammar. `BUILDLOG.md` records the phase closed, both new
  hashes, the superseded ones, and the Phase 14 candidates.
  ✅ *Checkpoint: a rehearsed day on a correct kidney, and nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 14.**

## 5 — Notes / data products

- **`urine_osm` and `urine_rate` keep their frozen names and meanings** — this
  phase changes what the model COMPUTES, never what the fields are called. The
  CSVs and worksheets that cite them keep working untouched.
- **Any new field is APPENDED** (M12 rule) and joins the water or body frozen
  schema in `tests/test_invariants.py`, plus that loop's CSV column list at
  the end.
- **The superseded regression hashes stay in `BUILDLOG.md`.** They are the
  record of what the model used to do and why it changed; deleting them would
  erase the only evidence that the change was deliberate.
- **The CSV is a view of `class_report()`**, never a second computation. If a
  number is wanted in the spreadsheet that the report does not carry, it gets
  added to the report first.
- **Engine purity holds**: `engine/` imports no web framework, reads no clock,
  uses no randomness. The repair is arithmetic, not plumbing.
