# Vital Loop — Claude Code Kickoff Prompt
### Phase 11: the room becomes visible — period codes and the teacher dashboard

## 0 — Working agreement (read this first)

The full working agreement lives in `~/.claude/CLAUDE.md` on this machine and
loads automatically — follow it. The load-bearing points: explain each
significant step in one or two plain-English sentences before doing it; build
in small runnable increments; STOP at phase checkpoints and wait for
confirmation; offer plain-English choices before structural decisions; patch
gaps with decimal milestones (M43.5), never regenerate this document
mid-build. Project state lives in `BUILDLOG.md`, not chat history.

**Phase 11 opener:** read `BUILDLOG.md` end to end before touching anything.
This phase touches **no engine file at all** — it is classroom infrastructure,
app-level only (`app.py`, `sessions.py`, `attempts.py`, templates, static).
The four loops' physiology, records, CSVs, presets, challenges and cases are
all in scope for *regression only*: they must come out byte-identical.

## 1 — What we're building (and why)

Phase 9 gave every device its own body; Phase 10 taught two loops to talk.
Phase 11 is about the *room*. Today every attempt from every class lands on
one shared leaderboard, and the only way to know who's stuck is to walk the
aisles reading phone screens. This phase adds the two things a real classroom
needs: **period codes** — a skippable join screen so a device belongs to a
class and the leaderboard means "us", not "every student all day" — and a
**teacher dashboard** — a PIN-gated live view of every session, readable from
the teacher's phone mid-room, that surfaces who's stuck before hands go up.

Priorities unchanged: the biology must be right > the loop structure must be
explicit on screen > aesthetics. The clause for this phase: **the lesson is
never blocked and never changed by the room plumbing.** A student who skips
the join screen gets the full sandbox; a cookieless client gets exactly the
world it has had since M7; a teacher reading the dashboard must not tick,
pause, or perturb anyone's simulation.

## 2 — Locked-in design decisions

**Scope.** Period codes / join screen + teacher dashboard. Still on the
candidate list for later phases: the `urine_osm` concentrating ceiling (M20)
and hemoconcentration (measured and deferred at M38).

**Settled in the kickoff interview (2026-08-18):**

- **Join screen, skippable.** First visit on a fresh device shows a one-time
  overlay: tap your period (from the teacher's list), type a team name, go —
  or tap **Skip** and land in the sandbox as Unassigned. The join step can
  never block the lesson. Period and team ride in cookies beside `vl_sid`.
- **`periods.txt` in the repo.** One period code per line (`P1`, `P3`, …),
  `#` comments and blank lines ignored, edited in Notepad once a year, read
  at launch. **Missing or empty file = joining quietly off**: the overlay
  never appears, everything is Unassigned, nothing errors — the app must not
  wedge because a file is absent.
- **Teacher PIN.** The server mints a short random PIN at each launch and
  prints it in the console beside the LAN address. `/teacher` asks for it
  once per device and remembers in a cookie, so the dashboard works from the
  teacher's phone while circulating — which is exactly when who's-stuck is
  worth knowing. Restart rotates the PIN.

**Settled by reading the code:**

- **Cookies follow the M33 pattern exactly**: the page's own JS sets
  `vl_period` / `vl_team`, the server only ever reads them. The registry
  mirrors period and team onto its session entry, so an idle-swept session
  that rejoins gets its period back from the cookie without noticing — the
  same property that already makes a server restart harmless to the class.
- **The attempts schema grows by appending, as it has since M27** (invariant
  ll): a `period` field joins `ATTEMPT_FIELDS`, stamped at `build_attempt`
  time from the requesting session, and M26–M42 records with no such field
  must still load. `attempts.py`'s save/load/append contract is otherwise
  untouched.
- **The default no-cookie session joins nothing.** verify.py, pytest and
  curl present no `vl_sid` and therefore no period — they keep driving the
  module-level runners exactly as they have since M7, which is what keeps
  eleven phases of tests meaning what they meant.
- **The dashboard is read-only by construction.** `Runner.advance()` runs on
  student polls; the dashboard must never call it. The registry grows a
  read-only room accessor (per-session facts, no engine stepping), and an
  invariant pins it: rendering the dashboard leaves every session's history
  byte-identical.

**Classroom-reality rules for this phase:**

- **The projector skips.** The teacher's projected browser carries a sid like
  everyone else's (M42), so it will meet the join screen once — Skip is the
  intended answer, and Unassigned viewers see the **all-periods** leaderboard,
  which is precisely what a projector should show. Joined devices see their
  own period's board. That symmetry is the design, not a fallback.
- **The dashboard never names a blind case's diagnosis.** The teacher's
  laptop is often the projector. Rows say "case 3 of 5 — blind, 12 min", by
  number, never by answer, so an accidentally projected dashboard ends no
  game. (The M28 redaction already protects student payloads; this protects
  against the teacher's own screen.)
- **PIN randomness stays app-level and injectable.** Engines stay
  deterministic (§2 of the v1 kickoff); the PIN generator is a seam the
  invariants suite can pin (env var or injectable), never `random` inside
  `engine/`.

## 3 — Tech stack

No new dependencies. The join overlay and dashboard are Jinja templates plus
vanilla JS beside the existing page; `periods.txt` parsing is a few lines of
plain Python; the dashboard polls a new JSON route the way the page has
polled `/state` since M2.

## 4 — Milestones

Build in order. Each milestone ends at a runnable checkpoint, and a milestone
is only done when `python verify.py` and
`python -m pytest tests/test_invariants.py -q` pass on my machine.

- **M43 — Periods exist: `periods.txt`, the join screen, the badge.**
  The parser (comments, blanks, missing-file-off, order preserved), the
  first-visit overlay (period buttons from the file, team name box, Skip),
  the two cookies, registry entries carrying period/team, and a footer badge
  ("P3 — Team Mongoose" / "Unassigned") so the join visibly stuck. Pin at
  least: parser behaviors including the quietly-off rule; the default
  session has no period; a rejoining sid keeps its period; the overlay never
  renders when joining is off.
  ✅ *Checkpoint: two browsers — one joins P3 as a team and wears the badge,
  one skips and reads Unassigned, and a fresh visit on the first shows no
  overlay again.*
- **M44 — The leaderboard learns periods.** `period` appended to
  `ATTEMPT_FIELDS` and stamped from the session at `build_attempt`; old logs
  load unchanged (ll-rule test with a fieldless record). `leaderboard()` and
  `best_attempt()` scope to the viewer's period; Unassigned viewers (the
  projector) see everyone, and the board says which scope it is showing.
  Head-to-head compare (M27) stays cross-period on purpose — comparing your
  run to another class's is a feature.
  ✅ *Checkpoint: attempts logged from two periods; each device's board shows
  only its own class, the projector shows both, and a pre-phase attempts.json
  still loads and displays.*
- **M45 — `/teacher`: the PIN and the room list.** PIN minted at launch,
  printed in the console beside the LAN address, asked once per device,
  remembered in a cookie, rotated on restart. Behind it: one row per live
  session — period, team, last-seen, which loop it last polled, and mode
  (sandbox / challenge / case, by name or number per the no-spoiler rule) —
  rendered from the registry's new read-only room accessor. Pin: wrong PIN
  refused in words; the accessor steps no engine (history byte-identical
  around a dashboard render); the dashboard route appears in no student
  payload.
  ✅ *Checkpoint: my phone, the PIN off the console, and a live row for every
  device in the room.*
- **M46 — Who's stuck.** The dashboard learns judgment. Per row: time in the
  current mode, attempts so far and best score on it, and a stuck flag —
  blind case open past a threshold without an answer, repeated zero-medal
  attempts on one challenge, or gone-quiet mid-class. Thresholds are named
  constants with the reasoning beside them, tuned by a sweep of plausible
  values before pinning (the M38 lesson: sweep before pinning has overturned
  a guess in five phases). Stuck rows sort first; the page auto-refreshes.
  ✅ *Checkpoint: I stage a stuck team on one device and watch its row rise
  and flag on my phone without touching its sim.*
- **M47 — The full pass, and the phase closes.** Drive everything through
  production routes across sessions: join / skip / rejoin, attempts from two
  periods, scoped boards, the dashboard watching a full four-loop lesson
  including a blind case (no diagnosis on the teacher page, no new fields in
  student payloads — extend the M42 leak check). Regression: both engine
  hashes untouched, the cookieless world byte-identical, all four tabs and
  their grammar exactly as M42 pinned them, worksheets still print.
  `BUILDLOG.md` records the phase closed and the Phase 12 candidates.
  ✅ *Checkpoint: a rehearsed class period with periods and a dashboard, and
  nothing wedges.*

**STOP at the end of this phase and wait for my confirmation before
Phase 12.**

## 5 — Notes / data products

- **`period` is part of the attempt record now** — stamped at build time,
  never inferred later, exported in the CSV wherever attempts already
  surface. Empty string for Unassigned, so old and new records sort together.
- **The room view is a data product, not a page-scrape**: the registry's
  read-only accessor returns per-session facts (sid-truncated, period, team,
  last_seen, per-loop mode) as plain data; the dashboard template renders
  that and nothing else. Future phases (a per-period report, a class-history
  view) read the same accessor.
- **`periods.txt` is the single source of period names.** The join screen,
  the badge, the leaderboard scope label and the dashboard all render what
  the file says — no period name is ever hardcoded in a template.
- **Cookies are set by page JS and only read by the server** (`vl_sid`
  pattern, M33). The server never Set-Cookies a student identity; the PIN
  cookie on `/teacher` is the one deliberate exception and is teacher-only.
- **No engine file changes in this phase.** If a milestone seems to need
  one, stop and say so — that is a scope conversation, not a patch.
