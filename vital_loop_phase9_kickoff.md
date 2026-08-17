# Vital Loop — Claude Code Kickoff Prompt
### Phase 9: per-student sessions, SIADH, and student worksheets

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M31.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 9 opener:** read `BUILDLOG.md` end to end before touching anything.
Confirm the standing kit is in place (it is — this repo is eight phases old),
and lead with any open bugs logged there (none at phase start). This is the
first phase since Phase 6 to touch `engine/`, so the regression guards
(h)/(k)/(n)/(s) in `tests/test_invariants.py` matter again — read them before
changing a constant, and when a record grows, convert subset-hash guards the
M17 way: subset hashing over the old fields, hash VALUE unchanged, proving
shape-only growth.

## 1 — What we're building (and why)

Phase 9 turns the projector sandbox into a lab. Until now one teacher drove
three shared bodies on one screen; after this phase every student device on
the room's wifi gets its **own** three bodies to break, while all scored runs
still land on one shared leaderboard. Alongside that, the water loop gains
its missing disease — **SIADH**, deferred since M23 because it needs a new
engine knob — and the class leaves with paper: **worksheets** printed from
the app itself, keyed to the same exports and vocabulary the app already
uses. Priorities unchanged: the biology must be right > the loop structure
must be explicit on screen > aesthetics. One new clause: "hard to wedge" now
means thirty browsers at once, not one.

## 2 — Locked-in design decisions

**Scope.** Three items: per-student sessions, SIADH + an ADH-override knob,
student worksheets. **Cross-loop coupling (mellitus polyuria) is explicitly
deferred again** — it stays on the candidate list for Phase 10.

**Assumptions — chosen by default when the kickoff interview went
unanswered; easy to change any time BEFORE the milestone that builds them:**

- **LAN + cookie sessions, no join screen.** The app keeps running on the
  teacher's machine; students browse to the teacher's IP on port 5083. Each
  browser gets its own session via an anonymous random-id cookie on first
  visit — no accounts, no landing page. The existing team-name box (M27) is
  how runs get labeled.
- **Leaderboard only — no teacher dashboard this phase.** The attempts log
  is already shared and keyed by label; scores from every device land on the
  same leaderboard. A live "who's stuck" dashboard is a Phase 10 candidate
  if class use shows the need.
- **Worksheets are printable app routes** (print from the browser, print
  CSS), not Word/PDF files — so they can never drift from the app's numbers
  and vocabulary, and the invariants suite can test them.
- **Verbal class direction — no mode gating.** Student sessions get the full
  app; the teacher tells the room what to do. Blind cases still can't leak:
  M28's redaction is server-side and per-session.

**Settled (not assumptions):**

- **One set of three Runners per session; the teacher's browser is just
  another session.** Phase 8 was built so game state hangs off the `Runner`
  — this is the plumbing change it promised, not a rewrite.
- **The attempts log stays GLOBAL.** One room, one leaderboard, one
  `data/attempts.json`, one lock. Session state is runtime-only and
  in-memory by design: killing the server drops sessions but never scores.
- **Session hygiene is a hard requirement, not polish.** An idle-session
  eviction policy plus a hard cap on live sessions, and a wrong click on one
  device must never touch another device's body. Refusals stay plain-English.
- **Privacy stands (Phase 8 §2):** labels are team names, the cookie is a
  random id, and nothing about a student is stored beyond it.
- **SIADH is a preset row + banner in the existing Diseases card** (the
  Phase 5 architecture: names in the table, mechanisms in the engine), plus
  a **fifth blind water case** so the disease enters the diagnosis game.
- **`adh_override` must NOT be added to the redaction allowlist.** The
  allowlist fails closed on purpose (M28 decision 1) — the new field being
  withheld while blind is the design working, not a bug to fix.
- **Engine determinism is untouched.** Cookies, session ids, and eviction
  clocks are app-layer; `engine/` still never reads the clock or randomness.
- **Port 5083 stays.** The app binds localhost until the milestone that
  opens the doors; LAN binding is a deliberate, logged step with its own
  checkpoint, not a side effect.

## 3 — Tech stack

No new dependencies — this phase is proof the eight-phase architecture holds.

- **Sessions:** a plain random-id cookie (`secrets.token_hex`) set by Flask,
  looked up in an in-memory registry dict behind one lock. No `flask.session`
  signed-cookie machinery, no database — there is nothing worth signing, and
  server-side state is what we already trust.
- **SIADH:** one knob in `engine/water.py`, same pattern as `set_fever` /
  `set_insulin_sensitivity` (M17).
- **Worksheets:** Jinja templates + print CSS. The browser's print dialog is
  the whole toolchain.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M31 — SIADH: contract + engine knob + console demo.**
  `set_adh_override(level)` in `engine/water.py`: while set, ADH secretion
  ignores the osmoreceptors and sits at `level` — that is the whole disease,
  secretion that is *inappropriate* to the stimulus. `None` clears it. The
  record grows `adh_override` (appended; convert the water subset-hash guard
  the M17 way, value unchanged). Hand-derive against the pins BEFORE writing
  the contract, then pin at least: the SIADH signature — with the override
  high and ordinary drinking continuing, osmolarity falls BELOW the 285
  floor while urine stays scant and concentrated (the inappropriate
  combination: dilute blood, concentrated urine); the same override with
  drinking withheld barely moves — **water restriction, the real first-line
  treatment, must fall out of the model as the discoverable fix**; thirst
  correctly reads LOW while it happens (the loop's own alarm is silent —
  that's why the disease is dangerous); knob validation; determinism; the
  no-override path byte-identical to Phase 6 histories. Extend the console
  demo with the SIADH beat.
  ✅ *Checkpoint: the demo shows the signature in numbers — ADH pinned high,
  osmolarity sliding under 285, urine concentrated, thirst silent.*
- **M32 — SIADH on the page.** A fourth row in the water Diseases card
  (Central DI / Nephrogenic DI / **SIADH** / Healthy again) through the
  existing preset table — story and banner name the syndrome and the
  inappropriate-secretion mechanism. Charts already carry everything needed
  (ADH high while osmolarity slides is the picture). Healthy clears it, no
  teleport. Then the **fifth blind water case** built on the knob: brief,
  warm-up sweep-checked for visible evidence, answer/role wiring, teaching
  note — and a pinned check that neither `adh_override` nor the preset name
  reaches a blind page or `/state`.
  ✅ *Checkpoint: I click SIADH live — banner up, ADH pinned, osmolarity
  sliding, water restriction visibly the fix — then play case 5 blind and
  the reveal grades it.*
- **M33 — Sessions under the hood.** The registry: cookie id → that
  browser's three Runners, created on first sight, behind one lock; every
  route (`/state`, `/control`, `/export.csv`, `/compare`, the page) resolves
  its Runners through it. The attempts log stays global. Idle eviction (a
  session untouched for a generous idle window is dropped; touching the app
  re-creates it fresh) and a hard session cap with a plain-English refusal
  page when the room is full. Pin at least: two sessions cannot see or move
  each other's state (a control POST in one changes nothing in the other);
  a reload keeps your session; an evicted id gets a fresh healthy sandbox,
  not an error; the cap refuses politely; attempts from two sessions
  interleave safely into one log. `verify.py` still passes — it is a session
  like any other.
  ✅ *Checkpoint: two different browsers on this machine hold two different
  bodies at once — one frozen, one feverish — and both runs land on the one
  leaderboard.*
- **M34 — Open the doors.** `run.bat` gains the LAN launch (bind 0.0.0.0,
  same port 5083), with the teacher-facing story printed at startup: the
  URL to write on the board (`http://<this-machine's-IP>:5083/`), and a
  plain-English note about the one-time Windows firewall prompt. A small
  footer line shows how many sessions are live, so the teacher can see the
  room arriving. Localhost behavior, `verify.py`, and every earlier phase
  are untouched.
  ✅ *Checkpoint: my phone, on the room wifi, runs its own body while the
  laptop runs another.*
- **M35 — Student worksheets.** Three printable routes (one per loop), each
  a one-period worksheet: the loop diagram to label with the curriculum
  vocabulary (stimulus, receptor/sensor, control center, effector, response,
  set point, negative feedback — exactly), a table whose blanks are filled
  from the student's own run (reading their charts / CSV columns by their
  frozen names), and a challenge/diagnosis debrief block keyed to the report
  card and attempts log. Print CSS so it lands on one or two clean pages.
  Pin at least: every field name a worksheet cites exists in the frozen
  records; the seven vocabulary terms appear exactly; the worksheet pages
  carry no answers.
  ✅ *Checkpoint: I print one from the browser and it's a worksheet I would
  actually hand out.*
- **M36 — The lab pass, and the phase closes.** The M30 full pass, at room
  scale: a crowd of concurrent sessions driven through the production routes
  (script-driven — every mode exercised across sessions, wrong clicks
  included), nothing wedges, no session ever sees another's state, the
  sandbox stays gameless per-session, a reload loses nothing, eviction and
  the cap behave, and the leaderboard aggregates the room. `BUILDLOG.md`
  records the phase closed and the Phase 10 candidates (cross-loop coupling
  and the teacher dashboard lead the list).
  ✅ *Checkpoint: a simulated class period — many devices, all four modes,
  one leaderboard — and nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 10.**

## 5 — Notes / data products

- **The session registry is runtime state on purpose** — in memory, never on
  disk. The one durable product remains `data/attempts.json`; sessions dying
  must never take a score with them (finalize already lives inside the
  runner lock — keep it there).
- **Worksheets create NO new data products.** They read the same frozen
  record fields and attempts entries everything else reads — that is the
  point, and the invariant that pins their field names to the frozen schemas
  is what keeps them honest.
- **`adh_override` joins the record schema** (appended, like every growth
  since M12) and the water CSV columns; it must never join
  `VISIBLE_DURING_CASE`.
