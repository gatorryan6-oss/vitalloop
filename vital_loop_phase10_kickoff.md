# Vital Loop — Claude Code Kickoff Prompt
### Phase 10: cross-loop coupling — the first time two loops meet

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M37.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 10 opener:** read `BUILDLOG.md` end to end before touching anything.
This phase changes BOTH the glucose and the water engine, so the regression
guards matter more than in any phase since Phase 6. Before editing either
engine, record a subset hash of its scripted run FROM THE COMMITTED CODE, the
way M31 did for water — a hash taken after the edit proves nothing.

## 1 — What we're building (and why)

Nine phases have taught three loops one at a time. Phase 10 lets two of them
talk. When blood glucose climbs past the kidney's threshold, sugar spills into
the urine — and osmoles drag water with them. That single link explains the
classic presentation of untreated diabetes: passing liters of urine, unable to
drink fast enough to keep up, dehydrating while a perfectly good ADH system
does everything right. It also pays off a promise the app made back in M23:
the class learned as WORDS that *insipidus* means tasteless and *mellitus*
means honey-sweet, two siphons with different broken loops. Now they see why —
the sugar is actually in the urine, and it is what is pulling the water out.

Priorities unchanged: the biology must be right > the loop structure must be
explicit on screen > aesthetics. One clause added for this phase: **a coupled
model must never quietly rewrite an uncoupled lesson.** Phases 1–9 stay
byte-identical.

## 2 — Locked-in design decisions

**Scope.** Cross-loop coupling only. The teacher dashboard and the period
codes / join screen stay on the candidate list for Phase 11.

**Settled in the kickoff interview (2026-08-17):**

- **A coupled `Body` lives in `engine/`** — `engine/body.py` owns one glucose
  sim and one water sim and steps them in lockstep, passing the coupling term
  each tick. Physiology stays out of the web layer and stays testable in
  pytest with no server. Both engines keep running standalone exactly as
  today.
- **A fourth "Whole body" tab.** Temperature / Glucose / Water are untouched;
  the coupling gets its own surface, so the three single-loop lessons keep
  teaching one variable at a time.

**Settled by reading the code (M6 already did half the work):**

- **The glucose engine has spilled sugar above 180 mg/dL since Phase 2**
  (`RENAL_THRESHOLD = 180.0`, `RENAL_COEF = 2.0`), folded into `uptake`. This
  phase CONNECTS that existing mechanism; it does not invent one. The glucose
  side therefore needs **no behavior change at all**.
- **`uptake` keeps its exact current meaning and value** (everything leaving
  the blood, spill included). The record grows a `renal_loss` field that
  REPORTS the spill component. A readout, not a re-plumbing — which is what
  makes byte-identical glucose behavior structural rather than merely hoped
  for.
- **The new physics is on the water side:** spilled glucose is osmotically
  active in the tubule, and the kidney cannot concentrate past ~1200 mOsm/L,
  so those osmoles obligate water out with them. Urine flow becomes
  `max(what ADH allows, what the solute load obligates)`.
- **This contrast is what makes the lesson land.** In diabetes insipidus urine
  is copious AND dilute (no ADH signal). In mellitus it is copious AND loaded
  with solute while ADH is MAXIMAL — the hormone is working perfectly and the
  water leaves anyway. Same polyuria, opposite mechanism, and the urine
  concentration trace is what tells them apart.

**Standing rules restated for this phase:**

- **Coupling is OFF unless a `Body` turns it on.** `WaterSimulation` gains a
  public method the `Body` calls; never called, nothing changes. Every Phase
  2–9 pin and both regression hashes must still pass untouched.
- **The single-loop tabs and the coupled tab will disagree, and we say so on
  screen.** The same untreated type 1 shows a different curve with the water
  loop attached, because the single-loop model leaves something out. That
  discrepancy is a science lesson about models, not a bug to hide — the
  Whole-body tab names it in a line of text.
- **Frozen record shapes grow by APPENDING** (the rule since M12), and the
  coupled body's own record is a new frozen schema in the invariants file.
- **Sandbox first, game second** (kickoff §2): coupling must be explorable
  before it is scored.

## 3 — Tech stack

No new dependencies. `engine/body.py` is plain Python beside the three
engines; the fourth tab reuses the M21 chart kit, the M22 diagram kit, and the
M33 per-session Runner machinery unchanged.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M37 — The coupling: contract, `engine/body.py`, console demo.**
  Record BOTH regression hashes from committed code FIRST. Then: `renal_loss`
  appended to the glucose record (reporting only, `uptake` unchanged);
  `set_tubular_load()` plus the obligated-flow law on the water side; a `Body`
  that steps both sims in lockstep and carries mg/dL·min of spilled glucose
  across as mOsm/min of tubular solute. Derive that unit conversion honestly
  and show the arithmetic in the build log — do not hand-wave it. Pin at
  least: both engines byte-identical uncoupled; a coupled untreated type 1
  passing liters a day of SOLUTE-LOADED urine while ADH sits at maximum (the
  mellitus signature); a coupled HEALTHY body showing no coupling effect at
  all, because normal glucose never crosses the threshold — the link must be a
  threshold, not a leak; determinism; and the DI contrast (dilute flood vs
  concentrated flood) as one pinned comparison.
  `python -m engine.body_demo`: untreated type 1 for a day, the classic triad
  in numbers.
  ✅ *Checkpoint: the console shows sugar in the urine dragging water out, and
  the body drinking to keep up.*
- **M38 — The spiral closes: dehydration feeds back on the sugar.** The return
  leg — as body water falls, the glucose that remains is dissolved in less of
  it and concentrates, which spills more, which pulls more water.
  **Sweep BEFORE pinning** (§2, and it has overturned a guess in five separate
  phases): if the feedback is too weak to see, or so strong it runs away in
  minutes, say so, log the numbers, and either tune it or defer the return leg
  with the finding written down. Pins: with water within reach the body
  compensates and holds; with water withheld the spiral is visible and
  monotone.
  ✅ *Checkpoint: I take the water bottle away from a hyperglycemic body and
  watch the two loops make each other worse.*
- **M39 — The Whole body tab.** A fourth loop in the app (a fourth Runner per
  session — M33 makes this cheap), charts for both variables plus the spill
  and urine traces, readouts that name the triad, and a CSV with its own
  frozen column list. Every earlier tab untouched.
  ✅ *Checkpoint: one screen, both loops, and I can drive the story live.*
- **M40 — Two loops, one arrow.** The diagram kit draws both loops with the
  renal spill arrow between them, lit only when glucose is above threshold and
  scaled by how hard it is spilling. The M23 naming payoff, made visible: the
  urine box carries the sugar, and the caption finally earns the word
  *mellitus*.
  ✅ *Checkpoint: the arrow lights as glucose crosses 180 and dies when
  insulin brings it back.*
- **M41 — The coupled body joins the lesson grammar.** Parity with what M30
  pinned for the other three loops: a preset (untreated mellitus, banner
  naming the mechanism), a challenge (keep them alive — the class must treat
  the sugar AND the water, and treating only one must lose), and a blind case
  whose whole difficulty is mellitus vs central DI on the urine trace.
  Calibrate the challenge by sweep before pinning the medals.
  ✅ *Checkpoint: I can hand a team a coupled body and a scoreboard.*
- **M42 — The full pass, and the phase closes.** Drive everything through the
  production routes across sessions: all four loops, every mode, wrong clicks,
  the coupled tab included. Confirm Phases 1–9 are untouched (both regression
  hashes green, the three single-loop tabs unchanged), sessions still
  isolated, worksheets still print. `BUILDLOG.md` records the phase closed and
  the Phase 11 candidates.
  ✅ *Checkpoint: a full period on four loops, and nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 11.**

## 5 — Notes / data products

- **The coupled body's history is a data product like every other**
  (kickoff §5): tick-by-tick records behind an accessor, its own frozen field
  list in `tests/test_invariants.py`, its own CSV columns. The Whole-body tab
  computes nothing the CSV wouldn't also contain.
- **`renal_loss` (glucose) and the tubular-load / obligated-flow fields
  (water) are appended** to those loops' frozen schemas, and appear in their
  CSVs at the end of the existing column order.
- **A new field that names a diagnosis must join `ANSWER_KEY_FIELDS`** in the
  invariants contract, and must NOT be added to `VISIBLE_DURING_CASE` — the
  M28 allowlist fails closed on purpose.
- **Neither engine may import the other.** The `Body` owns both and passes
  numbers between them; that keeps each loop independently testable and keeps
  "loop-agnostic where cheap" true.
