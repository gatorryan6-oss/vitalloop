/* Vital Loop front end. The browser is only a display: it polls /state,
   buffers the records the server hands back, and redraws. All physiology
   numbers come from engine history records — nothing is computed here that
   the CSV export wouldn't also contain (kickoff §5). */

"use strict";

const POLL_MS = 250;
// Visible strip per loop: temperature moves in minutes, glucose in
// hours, water over a longer afternoon still.
const WINDOWS = { temp: 600, glucose: 7200, water: 14400, body: 14400 };
const SVG_NS = "http://www.w3.org/2000/svg";

const palette = getComputedStyle(document.documentElement);
const COLOR_CORE = palette.getPropertyValue("--series-core").trim();
const COLOR_ENV = palette.getPropertyValue("--series-env").trim();
const COLOR_SWEAT = palette.getPropertyValue("--series-sweat").trim();
const COLOR_SHIVER = palette.getPropertyValue("--series-shiver").trim();
const COLOR_VASO = palette.getPropertyValue("--series-vaso").trim();
const COLOR_GRID = palette.getPropertyValue("--grid").trim();
const COLOR_BASELINE = palette.getPropertyValue("--baseline").trim();
const COLOR_MUTED = palette.getPropertyValue("--muted").trim();

/* M33: every browser gets its own body. The id is minted HERE — the
   server only ever reads it — so cookieless clients (verify.py, the
   test suite, curl) keep driving the shared default session, and eight
   phases of tests keep their meaning. */
if (!document.cookie.split("; ").some((c) => c.startsWith("vl_sid="))) {
  document.cookie = "vl_sid=" + crypto.randomUUID() +
                    "; path=/; max-age=31536000; SameSite=Lax";
}

let activeLoop = "temp";         // which loop the page is showing
const buffers = {                // engine records per loop, oldest first
  temp: { pts: [], lastT: -1 },
  glucose: { pts: [], lastT: -1, doses: [] },
  water: { pts: [], lastT: -1, drinks: [] },
  body: { pts: [], lastT: -1, doses: [], drinks: [] },
};
let running = true;              // play/speed of the ACTIVE loop's runner
let speed = 1;

/* ---------------- polling ---------------- */

/* A server-level refusal (the room is full, M33) in the server's own
   words. Cleared the moment a poll succeeds again. */
function roomNotice(text) {
  const el = document.getElementById("roomNotice");
  if (!el) return;
  if (text) { el.textContent = text; el.hidden = false; }
  else if (!el.hidden) { el.hidden = true; }
}

async function poll() {
  const loop = activeLoop;       // pin: the tab may switch mid-await
  const buf = buffers[loop];
  let j;
  try {
    const r = await fetch(`/state?loop=${loop}&since=` + buf.lastT);
    j = await r.json();
  } catch (e) {
    return;                      // server briefly away; next poll retries
  }
  if (j.error) {                 // e.g. the room is full (M33): the server
    roomNotice(j.error);         // refused in words — show them and wait
    return;
  }
  roomNotice(null);
  if (j.sessions !== undefined) {  // the room, arriving (M34)
    const el = document.getElementById("sessionCount");
    if (el) {
      el.textContent = j.sessions > 0
        ? `${j.sessions} device${j.sessions === 1 ? "" : "s"} playing`
        : "";
    }
  }
  if (j.now.t < buf.lastT) {     // sim was reset behind our back
    buf.pts = [];
    buf.lastT = -1;
    buf.doses = [];
    buf.drinks = [];
    return;
  }
  buf.pts.push(...j.points);
  buf.lastT = j.now.t;
  if (j.doses) buf.doses = j.doses;     // the engine's bolus event log
  if (j.drinks) buf.drinks = j.drinks;  // ...and the intake event log
  // Trim the buffer: keep the visible window plus slack. Full history for
  // the CSV lives on the server; the browser only needs what it draws.
  const cutoff = buf.lastT - WINDOWS[loop] * 1.2;
  let firstKeep = 0;
  while (firstKeep < buf.pts.length && buf.pts[firstKeep].t < cutoff) {
    firstKeep++;
  }
  if (firstKeep > 0) buf.pts = buf.pts.slice(firstKeep);
  if (loop !== activeLoop) return;   // tab switched while we fetched
  // While a blind case is unanswered the server has already stripped the
  // answer out of these records (M28). Everything downstream is told, so
  // the screen can say "we're not telling you" instead of guessing.
  const blind = !!(j.case && !j.case.answered);
  applyServerState(j);
  updateBanner(loop, j.preset);
  updateChallenge(loop, j.challenge);
  updateCase(loop, j.case, blind);
  updateGameLayer(loop, j);
  updateReadouts(j.now);
  if (loop === "temp" && window.updateDiagram) {
    window.updateDiagram(j.now, blind);
  } else if (loop === "glucose" && window.updateGlucoseDiagram) {
    window.updateGlucoseDiagram(j.now, blind);
  } else if (loop === "water" && window.updateWaterDiagram) {
    window.updateWaterDiagram(j.now, blind);
  } else if (loop === "body" && window.updateBodyDiagram) {
    window.updateBodyDiagram(j.now);
  }
  drawAll();
}

function applyServerState(j) {
  running = j.running;
  speed = j.speed;
  document.getElementById("pauseBtn").textContent =
    running ? "Pause" : "Resume";
  document.getElementById("pauseBtn").classList.toggle("primary-off",
    !running);
  document.querySelectorAll(".speed").forEach(b =>
    b.classList.toggle("active", Number(b.dataset.speed) === speed));
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

/* --- disease banner (M18): the server's preset table is the single
   source; this only renders what /state hands over --- */

const BANNER_IDS = { temp: "tempBanner", glucose: "glucoseBanner",
                     water: "waterBanner" };

function updateBanner(loop, preset) {
  const div = document.getElementById(BANNER_IDS[loop]);
  if (!div) return;
  if (preset) {
    div.hidden = false;
    div.innerHTML = "";
    const name = document.createElement("strong");
    name.textContent = preset.label.toUpperCase();
    div.appendChild(name);
    div.appendChild(document.createTextNode(" — " + preset.banner));
  } else {
    div.hidden = true;
  }
  document.querySelectorAll(`#${PAGE_IDS[loop]} .preset`).forEach(b =>
    b.classList.toggle("active",
      preset ? b.dataset.preset === preset.name : false));
}

/* --- challenge card (M24): the server's stamp and report are the only
   sources; this renders them --- */

/* A loop can have more than one challenge (M29 gave each one a crisis
   variant), so cards are found by ELEMENT and identified by their own
   data-challenge — there is no per-loop id map to keep in step with the
   table any more. */

function challengeCards(loop) {
  return document.querySelectorAll(`#${PAGE_IDS[loop]} .challenge-card`);
}

/* Points and medals (M26). Every number here was computed server-side by
   score_report() from the same rows the report card shows — the JS adds
   nothing, it only draws. */

function medalChip(medal) {
  const chip = document.createElement("span");
  chip.className = "medal-chip medal-" + (medal || "none");
  chip.textContent = medal ? medal.toUpperCase() : "NO MEDAL";
  return chip;
}

function fmtWhen(iso) {          // "2026-08-16T15:10:42" -> "08/16 15:10"
  if (!iso) return "";
  return iso.slice(5, 7) + "/" + iso.slice(8, 10) + " " + iso.slice(11, 16);
}

function fmtSimHours(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}:${String(m).padStart(2, "0")}`;
}

function updateChallenge(loop, c) {
  for (const card of challengeCards(loop)) {
    // Only the card whose challenge is actually running shows anything;
    // the others sit quiet with their story and their leaderboard.
    drawChallenge(card, loop, c && c.name === card.dataset.challenge
      ? c : null);
  }
}

function drawChallenge(card, loop, c) {
  const progress = card.querySelector(".challenge-progress");
  const report = card.querySelector(".challenge-report");
  drawFeed(card.querySelector(".challenge-feed"), c);
  if (!c) {
    progress.hidden = true;
    report.hidden = true;
    return;
  }
  if (!c.done) {
    progress.hidden = false;
    report.hidden = true;
    const total = c.t_end - c.t_start;
    const elapsed = Math.min(total,
      Math.max(0, buffers[loop].lastT - c.t_start));
    progress.querySelector(".challenge-bar span").style.width =
      (100 * elapsed / total).toFixed(1) + "%";
    progress.querySelector(".challenge-clock").textContent =
      (c.label ? `${c.label} — ` : "") +
      `${fmtSimHours(elapsed)} of ${fmtSimHours(total)} sim-hours — ` +
      c.goal;
    return;
  }
  progress.hidden = true;
  if (!c.report) return;
  report.hidden = false;
  report.innerHTML = "";
  const verdict = document.createElement("div");
  verdict.className = "challenge-verdict "
    + (c.report.met ? "verdict-met" : "verdict-missed");
  const whose = c.label ? `${c.title} — ${c.label}` : c.title;
  verdict.textContent = c.report.met
    ? `${whose}: GOAL MET`
    : `${whose}: NOT MET — read the rows, then the charts`;
  report.appendChild(verdict);
  // A run the crisis ended early says so first, and says when (M29).
  if (c.stopped) {
    const halt = document.createElement("div");
    halt.className = "challenge-stopped";
    halt.textContent =
      `Stopped at ${fmtSimHours(c.stopped.t - c.t_start)} — ` +
      `${c.stopped.line}.`;
    report.appendChild(halt);
  }
  // The score rides ON TOP of the verdict, never instead of it (M26).
  const worth = {};
  if (c.score) {
    const line = document.createElement("div");
    line.className = "challenge-score";
    if (c.score.zeroed) {
      line.classList.add("score-zeroed");
      line.textContent = `NO SCORE — ${c.score.zeroed}`;
    } else {
      const pts = document.createElement("strong");
      pts.textContent = `${c.score.points} / ${c.score.max}`;
      line.appendChild(pts);
      line.appendChild(document.createTextNode(" "));
      line.appendChild(medalChip(c.score.medal));
      for (const b of c.score.rows) worth[b.key] = b;
    }
    report.appendChild(line);
  }
  for (const row of c.report.rows) {
    report.appendChild(reportRow(row, worth[row.key]));
  }
  report.appendChild(savedLine(c.attempt));
}

/* The crisis feed (M29): what has already hit this run, and when. The
   server sends only what has LANDED — the rest of the schedule never
   leaves the building — so this can draw everything it is given and the
   ambush stays an ambush. It stays on screen after the buzzer, because
   reading the report means remembering what the run had to survive. */

function drawFeed(feed, c) {
  if (!feed) return;
  const events = (c && c.events) || [];
  feed.hidden = events.length === 0;
  if (!events.length) {
    feed.dataset.count = "0";
    return;
  }
  if (feed.dataset.count === String(events.length)) return;  // 4 Hz poll
  feed.dataset.count = String(events.length);
  feed.innerHTML = "";
  const head = document.createElement("div");
  head.className = "feed-title";
  head.textContent = "What has happened to you";
  feed.appendChild(head);
  events.forEach((e, i) => {
    const row = document.createElement("div");
    row.className = "feed-row" + (i === events.length - 1 ? " feed-new" : "");
    const when = document.createElement("span");
    when.className = "feed-when";
    when.textContent = "+" + fmtSimHours(e.at);
    row.appendChild(when);
    const line = document.createElement("span");
    line.className = "feed-line";
    line.textContent = e.line;
    row.appendChild(line);
    feed.appendChild(row);
  });
}

/* One line of a report card: the ✓/✗/· mark, the label and value the
   server wrote, and — when the row earned points — where they went. A
   diagnosis is graded in exactly this grammar, so it draws with exactly
   this renderer (M28). */

function reportRow(row, worth) {
  const div = document.createElement("div");
  div.className = "challenge-row";
  const mark = document.createElement("span");
  mark.className = row.met === null ? "row-info"
    : row.met ? "row-met" : "row-missed";
  mark.textContent = row.met === null ? "·" : row.met ? "✓" : "✗";
  div.appendChild(mark);
  const text = document.createElement("span");
  text.className = "row-text";
  text.textContent = ` ${row.label}: ${row.value}`;
  div.appendChild(text);
  if (worth) {
    const pts = document.createElement("span");
    pts.className = "row-points";
    pts.textContent = `${worth.points} / ${worth.max}`;
    div.appendChild(pts);
  }
  return div;
}

function savedLine(attempt) {
  const saved = document.createElement("div");
  saved.className = "challenge-saved";
  saved.hidden = !attempt;
  if (attempt) {
    saved.textContent = `Saved to the attempts log as run #${attempt.id}.`;
  }
  return saved;
}

/* --- the diagnosis card (M28): a blind case, an answer in curriculum
   vocabulary, and the reveal. Nothing here knows what the answer is
   until the server sends it, which is the entire point. --- */

const CASE_IDS = { temp: "tempDiagnose", glucose: "glucoseDiagnose",
                   water: "waterDiagnose" };
// Where each loop's fast-forward ended, for the marker on the chart.
const caseWarmup = { temp: null, glucose: null, water: null };

const CASE_HEADLINES = {
  correct: "RIGHT — that is exactly what failed",
  partial: "HALF RIGHT — the right part of the loop, the wrong component",
  wrong: "NOT THIS TIME — read the reveal, then look again",
};
const CASE_VERDICT_CLASS = {
  correct: "verdict-met", partial: "verdict-partial",
  wrong: "verdict-missed",
};

function updateCase(loop, c, blind) {
  const card = document.getElementById(CASE_IDS[loop]);
  if (!card) return;
  caseWarmup[loop] = c && c.warmup_s ? c.warmup_s : null;
  // Put away everything that would name the broken part. The server has
  // already redacted the payload — this only keeps the screen honest
  // about what it's holding back.
  document.querySelectorAll(`#${PAGE_IDS[loop]} [data-blind-hide]`)
    .forEach(el => { el.hidden = blind; });
  const live = card.querySelector(".case-live");
  const verdict = card.querySelector(".case-verdict");
  card.querySelector(".case-start").textContent =
    c ? "Start another case" : "Start a blind case";
  if (!c) {
    live.hidden = true;
    verdict.hidden = true;
    return;
  }
  live.hidden = false;
  const brief = card.querySelector(".case-brief");
  brief.innerHTML = "";
  const which = document.createElement("strong");
  which.textContent = `Case ${c.n} of ${c.of}` +
    (c.label ? ` — ${c.label}` : "") + ": ";
  brief.appendChild(which);
  brief.appendChild(document.createTextNode(c.brief));
  if (c.warmup_s) {
    const skipped = document.createElement("div");
    skipped.className = "case-warmup";
    skipped.textContent =
      `The first ${fmtSimHours(c.warmup_s)} of this story already ` +
      `happened — it is drawn on the charts, left of the marked line.`;
    brief.appendChild(skipped);
  }
  card.querySelector(".case-form").hidden = c.answered;
  if (!c.answered) {
    verdict.hidden = true;
    return;
  }
  drawCaseVerdict(verdict, c);
}

function drawCaseVerdict(out, c) {
  const g = c.grade;
  out.hidden = false;
  out.innerHTML = "";
  const head = document.createElement("div");
  head.className = "challenge-verdict " + CASE_VERDICT_CLASS[g.verdict];
  head.textContent = (c.label ? `${c.label} — ` : "") +
    CASE_HEADLINES[g.verdict];
  out.appendChild(head);
  const score = document.createElement("div");
  score.className = "challenge-score";
  const pts = document.createElement("strong");
  pts.textContent = `${g.points} / 100`;
  score.appendChild(pts);
  score.appendChild(document.createTextNode(
    ` — it was ${g.truth.line}.`));
  out.appendChild(score);
  for (const row of g.rows) {
    if (row.key !== "note") out.appendChild(reportRow(row, null));
  }
  // The note is the lesson, not a row — it gets its own block, and it
  // shows whether the class was right or wrong.
  const note = document.createElement("div");
  note.className = "case-note";
  note.textContent = g.note;
  out.appendChild(note);
  out.appendChild(savedLine(c.attempt));
}

/* --- best so far, the leaderboard, and the head-to-head picker
   (M26/M27). Team names go in with textContent, never innerHTML: the
   teacher types them and the projector shows them back verbatim. --- */

const TEAMLESS = "(no team)";

function updateGameLayer(loop, j) {
  for (const card of challengeCards(loop)) drawGameLayer(card, j);
}

function drawGameLayer(card, j) {
  const cid = card.dataset.challenge;
  const div = card.querySelector(".challenge-best");
  const best = j.bests ? j.bests[cid] : null;
  if (!best) {
    div.hidden = true;
  } else {
    div.hidden = false;
    div.innerHTML = "";
    div.appendChild(document.createTextNode("Best so far: "));
    const pts = document.createElement("strong");
    pts.textContent = `${best.points} / 100`;
    div.appendChild(pts);
    div.appendChild(document.createTextNode(" "));
    div.appendChild(medalChip(best.medal));
    const tail = best.label ? ` — ${best.label}, ` : " — ";
    div.appendChild(document.createTextNode(
      `${tail}${fmtWhen(best.wall_time)} · ` +
      `${best.runs} run${best.runs === 1 ? "" : "s"} so far`));
  }
  const warn = card.querySelector(".attempts-error");
  warn.hidden = !j.attempts_error;
  if (j.attempts_error) warn.textContent = j.attempts_error;
  const board = j.leaderboard ? j.leaderboard[cid] : null;
  drawLeaderboard(card, board || []);
  fillH2HPickers(card, board || []);
}

function drawLeaderboard(card, entries) {
  const div = card.querySelector(".challenge-board");
  div.hidden = entries.length === 0;
  if (!entries.length) return;
  div.innerHTML = "";
  const head = document.createElement("div");
  head.className = "board-title";
  head.textContent = "Leaderboard";
  div.appendChild(head);
  const table = document.createElement("table");
  table.className = "board-table";
  entries.forEach((e, i) => {
    const tr = document.createElement("tr");
    const cells = [
      [`${i + 1}`, "board-rank"],
      [e.label || TEAMLESS, "board-team"],
      [`${e.points} / 100`, "board-points"],
      [null, "board-medal"],                      // filled with a chip
      [e.met ? "goal met" : "not met", e.met ? "row-met" : "row-missed"],
      [fmtWhen(e.wall_time), "board-when"],
    ];
    for (const [text, cls] of cells) {
      const td = document.createElement("td");
      td.className = cls;
      if (text === null) td.appendChild(medalChip(e.medal));
      else td.textContent = text;
      tr.appendChild(td);
    }
    table.appendChild(tr);
  });
  div.appendChild(table);
}

/* Repopulate the two pickers ONLY when the set of runs changes — a poll
   lands four times a second and must never yank the teacher's choice. */

function fillH2HPickers(card, entries) {
  const wrap = card.querySelector(".challenge-h2h");
  wrap.hidden = entries.length < 2;
  if (entries.length < 2) return;
  const signature = entries.map(e => e.id).join(",");
  if (wrap.dataset.signature === signature) return;
  wrap.dataset.signature = signature;
  const selA = wrap.querySelector(".h2h-a");
  const selB = wrap.querySelector(".h2h-b");
  const keep = { a: selA.value, b: selB.value };
  for (const sel of [selA, selB]) {
    sel.innerHTML = "";
    for (const e of entries) {
      const opt = document.createElement("option");
      opt.value = e.id;
      opt.textContent = `${e.label || TEAMLESS} — ${e.points}`;
      sel.appendChild(opt);
    }
  }
  // Default to the two most recent runs, oldest on the left, so the
  // projector reads in the order the class played them.
  const recent = entries.slice().sort(
    (x, y) => (y.wall_time || "").localeCompare(x.wall_time || ""));
  const ids = entries.map(e => String(e.id));
  selA.value = ids.includes(keep.a) ? keep.a : String(recent[1].id);
  selB.value = ids.includes(keep.b) ? keep.b : String(recent[0].id);
}

/* The comparison is computed SERVER-SIDE from the log (M27) — this only
   draws what /compare hands back. */

async function runCompare(loop, card) {
  const wrap = card.querySelector(".challenge-h2h");
  const out = wrap.querySelector(".h2h-out");
  const a = wrap.querySelector(".h2h-a").value;
  const b = wrap.querySelector(".h2h-b").value;
  const name = card.dataset.challenge;
  let j;
  try {
    const r = await fetch(
      `/compare?loop=${loop}&name=${name}&a=${a}&b=${b}`);
    j = await r.json();
    if (j.error) throw new Error(j.error);
  } catch (e) {
    out.innerHTML = "";
    const msg = document.createElement("div");
    msg.className = "attempts-error";
    msg.textContent = e.message || "the comparison could not be loaded";
    out.appendChild(msg);
    return;
  }
  drawCompare(out, j);
}

function teamHead(side) {
  const cell = document.createElement("th");
  cell.className = "h2h-team";
  const name = document.createElement("div");
  name.className = "h2h-name";
  name.textContent = side.label || TEAMLESS;
  cell.appendChild(name);
  const score = document.createElement("div");
  score.className = "h2h-total";
  if (side.zeroed) {
    score.textContent = "NO SCORE";
  } else {
    score.textContent = `${side.points} / 100 `;
    score.appendChild(medalChip(side.medal));
  }
  cell.appendChild(score);
  const verdict = document.createElement("div");
  verdict.className = side.met ? "row-met" : "row-missed";
  verdict.textContent = side.met ? "goal met" : "not met";
  cell.appendChild(verdict);
  return cell;
}

function h2hCell(cell, won) {
  const td = document.createElement("td");
  td.className = "h2h-cell" + (won ? " h2h-win" : "");
  if (cell.value === null) {
    td.textContent = "—";
    return td;
  }
  const mark = document.createElement("span");
  mark.className = cell.met === null ? "row-info"
    : cell.met ? "row-met" : "row-missed";
  mark.textContent = cell.met === null ? "·" : cell.met ? "✓" : "✗";
  td.appendChild(mark);
  const val = document.createElement("span");
  val.className = "h2h-value";
  val.textContent = ` ${cell.value}`;
  td.appendChild(val);
  if (cell.points !== null && cell.points !== undefined) {
    const pts = document.createElement("span");
    pts.className = "row-points";
    pts.textContent = `${cell.points} / ${cell.max}`;
    td.appendChild(pts);
  }
  return td;
}

function drawCompare(out, j) {
  out.innerHTML = "";
  const verdict = document.createElement("div");
  verdict.className = "h2h-verdict";
  const winner = j.winner ? j[j.winner] : null;
  verdict.textContent = winner
    ? `${winner.label || TEAMLESS} takes it, ` +
      `${j.a.points} to ${j.b.points} — row by row, here's where.`
    : `A dead heat at ${j.a.points} — identical runs of an identical ` +
      `challenge.`;
  out.appendChild(verdict);
  const table = document.createElement("table");
  table.className = "h2h-table";
  const head = document.createElement("tr");
  head.appendChild(document.createElement("th"));
  head.appendChild(teamHead(j.a));
  head.appendChild(teamHead(j.b));
  table.appendChild(head);
  for (const row of j.rows) {
    const tr = document.createElement("tr");
    const label = document.createElement("td");
    label.className = "h2h-label";
    label.textContent = row.label;
    tr.appendChild(label);
    tr.appendChild(h2hCell(row.a, row.winner === "a"));
    tr.appendChild(h2hCell(row.b, row.winner === "b"));
    table.appendChild(tr);
  }
  out.appendChild(table);
}

function updateReadouts(now) {
  const s = Math.floor(now.t);
  const mm = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  setText("clockReadout", `${mm}:${ss}`);

  if (activeLoop === "body") {
    // Two controlled variables, side by side — the whole point of the tab.
    setText("r1Label", "glucose"
      + (now.renal_loss > 0.01 ? " — SPILLING SUGAR" : ""));
    setText("r1Value", now.glucose.toFixed(0) + " mg/dL");
    const r1 = document.getElementById("r1Value");
    r1.classList.remove("hypo", "severe", "hyper");
    if (now.glucose > 180) r1.classList.add("hyper");
    if (now.glucose < 70) r1.classList.add("hypo");
    setText("r2Label", "osmolarity"
      + (now.osmolarity > 305 ? " — DEHYDRATED" : ""));
    setText("r2Value", now.osmolarity.toFixed(1) + " mOsm/L");
    const bex = document.getElementById("bExerciseBtn");
    if (bex) {
      bex.textContent = now.exercise ? "Exercise: ON" : "Exercise: off";
      bex.setAttribute("aria-pressed", String(!!now.exercise));
    }
    lastExercise = now.exercise;   // the toggle reads this, like the others
    return;
  }

  if (activeLoop === "water") {
    setText("r1Label", "osmolarity");
    setText("r1Value", now.osmolarity.toFixed(1) + " mOsm/L");
    const r1 = document.getElementById("r1Value");
    r1.classList.remove("hypo", "severe", "hyper");
    if (now.osmolarity > 305) r1.classList.add("hyper");
    if (now.osmolarity < 275) r1.classList.add("hypo");
    setText("r1Label", "osmolarity"
      + (now.osmolarity > 305 ? " — DEHYDRATED"
        : now.osmolarity < 275 ? " — OVERHYDRATED" : ""));
    setText("r2Label", "body water");
    setText("r2Value", now.water_liters.toFixed(1) + " L");
    const wex = document.getElementById("wExerciseBtn");
    wex.textContent = now.exercise
      ? "Exercise / heat: ON" : "Exercise / heat: off";
    wex.setAttribute("aria-pressed", String(now.exercise));
    lastExercise = now.exercise;
    if ("adh_enabled" in now) {   // absent while a case is blind (M28)
      wPartEnabled = {
        adh: now.adh_enabled,
        kidney: now.kidney_enabled,
        access: now.water_access,
        sensor: now.sensor_enabled,
      };
      document.querySelectorAll("#page-water .breaker").forEach(b => {
        const on = wPartEnabled[b.dataset.part];
        b.classList.toggle("broken", !on);
        b.textContent = W_BREAKER_LABELS[b.dataset.part] +
          (on ? "" : " — DISABLED");
      });
    }
    return;
  }

  if (activeLoop === "glucose") {
    // Patient status, legible from the back row (M13): the label carries
    // the word, the value carries the color. Thresholds are the chart's
    // reference lines (70 / 180) plus the clinical severe-hypo line (54).
    const g = now.glucose;
    const status = g < 54 ? "severe" : g < 70 ? "hypo"
                 : g > 180 ? "hyper" : "";
    setText("r1Label", "glucose" + (status === "severe" ? " — SEVERE HYPO"
      : status === "hypo" ? " — HYPO"
      : status === "hyper" ? " — HYPER" : ""));
    setText("r1Value", now.glucose.toFixed(0) + " mg/dL");
    const r1 = document.getElementById("r1Value");
    r1.classList.toggle("hypo", status === "hypo");
    r1.classList.toggle("severe", status === "severe");
    r1.classList.toggle("hyper", status === "hyper");
    setText("r2Label", "gut carbs");
    setText("r2Value", now.gut_carbs.toFixed(0) + " g");
    setText("iobReadout", now.iob_units.toFixed(1) + " U");
    // One basal source at a time: while the pump runs it owns the drip,
    // so the manual selector locks (the server refuses it anyway).
    document.querySelectorAll(".basal").forEach(b => {
      b.classList.toggle("active",
        Number(b.dataset.rate) === now.basal_rate);
      b.disabled = now.pump_enabled;
    });
    lastPump = now.pump_enabled;
    const pumpBtn = document.getElementById("pumpBtn");
    pumpBtn.textContent = now.pump_enabled
      ? "Closed-loop pump: ON" : "Closed-loop pump: off";
    pumpBtn.setAttribute("aria-pressed", String(now.pump_enabled));
    setText("pumpRateReadout", now.pump_enabled
      ? now.pump_rate.toFixed(2) + " U/h" : "—");
    const gex = document.getElementById("gExerciseBtn");
    gex.textContent = now.exercise ? "Exercise: ON" : "Exercise: off";
    gex.setAttribute("aria-pressed", String(now.exercise));
    lastExercise = now.exercise;
    if ("beta_enabled" in now) {   // absent while a case is blind (M28)
      gPartEnabled = {
        beta: now.beta_enabled,
        alpha: now.alpha_enabled,
        liver: now.liver_enabled,
        sensor: now.sensor_enabled,
      };
      document.querySelectorAll("#page-glucose .breaker").forEach(b => {
        const on = gPartEnabled[b.dataset.part];
        b.classList.toggle("broken", !on);
        b.textContent = G_BREAKER_LABELS[b.dataset.part] +
          (on ? "" : " — DISABLED");
      });
    }
    return;
  }

  setText("r1Label", "core temp");
  setText("r1Value", now.core_temp.toFixed(2) + " °C");
  document.getElementById("r1Value")
    .classList.remove("hypo", "severe", "hyper");
  setText("r2Label", "room");
  setText("r2Value", now.env_temp.toFixed(1) + " °C");

  // Reflect the server's truth in the disturbance controls — unless the
  // teacher is mid-drag, in which case their hand wins.
  if (!sliderBusy) {
    envSlider.value = now.env_temp;
    envSliderVal.textContent = now.env_temp.toFixed(1) + " °C";
  }
  const ex = document.getElementById("exerciseBtn");
  ex.textContent = now.exercise ? "Exercise: ON" : "Exercise: off";
  ex.setAttribute("aria-pressed", String(now.exercise));
  lastExercise = now.exercise;

  // Break-the-loop buttons mirror the engine's enabled flags — which a
  // blind case withholds, so there is nothing to mirror (M28).
  if ("sweat_enabled" in now) {
    partEnabled = {
      sweat: now.sweat_enabled,
      shiver: now.shiver_enabled,
      vaso: now.vaso_enabled,
      sensor: now.sensor_enabled,
    };
    document.querySelectorAll("#page-temp .breaker").forEach(b => {
      const on = partEnabled[b.dataset.part];
      b.classList.toggle("broken", !on);
      b.textContent = BREAKER_LABELS[b.dataset.part] +
        (on ? "" : " — DISABLED");
    });
  }
}

/* ---------------- controls ---------------- */

async function control(body) {
  try {
    const r = await fetch(`/control?loop=${activeLoop}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json();
    // A refusal is an {error} payload, not a snapshot — feeding it to
    // applyServerState() flipped the Pause button on every 400 until the
    // next poll put it back. Refusals now leave the controls alone.
    if (r.ok) applyServerState(j);
    return j;
  } catch (e) { return null; }     // next poll re-syncs the buttons
}

document.getElementById("pauseBtn").addEventListener("click", () =>
  control({ action: running ? "pause" : "resume" }));
document.getElementById("resetBtn").addEventListener("click", () =>
  control({ action: "reset" }));
document.querySelectorAll(".speed").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "speed", value: Number(b.dataset.speed) })));

/* --- disturbances (M3) --- */

const envSlider = document.getElementById("envSlider");
const envSliderVal = document.getElementById("envSliderVal");
let sliderBusy = false;          // true while the teacher is dragging
let sliderIdleTimer = null;
let sliderSendTimer = null;
let lastExercise = false;

envSlider.addEventListener("input", () => {
  sliderBusy = true;
  envSliderVal.textContent = Number(envSlider.value).toFixed(1) + " °C";
  clearTimeout(sliderSendTimer);   // debounce: send the resting value only
  sliderSendTimer = setTimeout(() =>
    control({ action: "env_temp", value: Number(envSlider.value) }), 150);
  clearTimeout(sliderIdleTimer);
  sliderIdleTimer = setTimeout(() => { sliderBusy = false; }, 800);
});

document.getElementById("exerciseBtn").addEventListener("click", () =>
  control({ action: "exercise", value: !lastExercise }));

document.querySelectorAll(".scenario").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "scenario", value: b.dataset.scenario })));

/* --- glucose disturbances (M8) --- */

document.querySelectorAll(".eat").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "eat", grams: Number(b.dataset.grams),
              rate: Number(b.dataset.rate) })));
document.getElementById("gExerciseBtn").addEventListener("click", () =>
  control({ action: "exercise", value: !lastExercise }));
document.querySelectorAll(".gscenario").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "scenario", value: b.dataset.scenario })));

/* --- the coupled body (M39) --- */
/* One person: the same actions the single-loop tabs offer, aimed at a
   body that has both loops running. The breakers keep their own local
   state because the coupled record carries values, not flags. */

const bodyBroken = { beta: false, access: false };

function wireBodyBreaker(id, part, label) {
  const btn = document.getElementById(id);
  if (!btn) return;
  btn.addEventListener("click", async () => {
    bodyBroken[part] = !bodyBroken[part];
    const ok = await control({ action: "effector", name: part,
                               on: !bodyBroken[part] });
    if (!ok || ok.error) { bodyBroken[part] = !bodyBroken[part]; return; }
    btn.classList.toggle("broken", bodyBroken[part]);
    btn.textContent = bodyBroken[part] ? `${label} — DISABLED` : label;
  });
}

if (document.getElementById("bEatBtn")) {
  document.getElementById("bEatBtn").addEventListener("click", () =>
    control({ action: "eat", grams: 75, rate: 1.0 }));
  document.getElementById("bDrinkBtn").addEventListener("click", () =>
    control({ action: "drink", ml: 250 }));
  document.getElementById("bInjectBtn").addEventListener("click", () =>
    control({ action: "inject", units: 4 }));
  document.getElementById("bExerciseBtn").addEventListener("click", () =>
    control({ action: "exercise", value: !lastExercise }));
  wireBodyBreaker("bBetaBtn", "beta", "Beta cells (insulin)");
  wireBodyBreaker("bAccessBtn", "access", "Water access");
}

/* --- insulin dosing (M12) --- */

document.querySelectorAll(".dose").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "inject", units: Number(b.dataset.units) })));
document.querySelectorAll(".basal").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "basal", value: Number(b.dataset.rate) })));

/* --- the closed-loop pump (M15) --- */

let lastPump = false;
document.getElementById("pumpBtn").addEventListener("click", () =>
  control({ action: "pump", value: !lastPump }));

/* --- disease presets (M18) --- */

document.querySelectorAll(".preset").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "preset", value: b.dataset.preset })));

/* --- challenges (M24) --- */

document.querySelectorAll(".challenge-start").forEach(b =>
  b.addEventListener("click", () => {
    // Whose run this is (M27). The server tidies and caps it; an empty
    // box just means nobody claimed the run. The card knows which
    // challenge it is — a loop can have several (M29).
    const card = b.closest(".challenge-card");
    control({ action: "challenge", value: card.dataset.challenge,
              label: card.querySelector(".challenge-label").value });
  }));

/* --- head to head (M27) --- */

document.querySelectorAll(".h2h-go").forEach(b =>
  b.addEventListener("click", () =>
    runCompare(activeLoop, b.closest(".challenge-card"))));

/* --- the diagnosis game (M28). The picker sends "next" or a NUMBER;
   there is no case name anywhere in this file, or in the page. --- */

document.querySelectorAll(".case-start").forEach(b =>
  b.addEventListener("click", () => {
    const card = b.closest(".diagnose-card");
    control({ action: "diagnose",
              value: card.querySelector(".case-pick").value,
              label: card.querySelector(".case-label").value });
  }));

document.querySelectorAll(".case-answer").forEach(b =>
  b.addEventListener("click", () => {
    const card = b.closest(".diagnose-card");
    control({ action: "answer",
              role: card.querySelector(".case-role").value,
              part: card.querySelector(".case-part").value });
  }));

/* --- water disturbances (M21) --- */

document.querySelectorAll(".drinkbtn").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "drink", ml: Number(b.dataset.ml) })));
document.getElementById("saltyBtn").addEventListener("click", () =>
  control({ action: "salty", mosm: 300 }));
document.getElementById("wExerciseBtn").addEventListener("click", () =>
  control({ action: "exercise", value: !lastExercise }));
document.querySelectorAll(".wscenario").forEach(b =>
  b.addEventListener("click", () =>
    control({ action: "scenario", value: b.dataset.scenario })));

/* --- break the loop (M5) --- */

const BREAKER_LABELS = {
  sweat: "Sweating",
  shiver: "Shivering",
  vaso: "Vessel control",
  sensor: "Temperature sensors",
};
let partEnabled = { sweat: true, shiver: true, vaso: true, sensor: true };

document.querySelectorAll("#page-temp .breaker").forEach(b =>
  b.addEventListener("click", () => {
    const part = b.dataset.part;
    const wantEnabled = !partEnabled[part];
    control(part === "sensor"
      ? { action: "sensor", value: wantEnabled }
      : { action: "effector", name: part, value: wantEnabled });
  }));

/* --- break the glucose loop (M10) --- */

const G_BREAKER_LABELS = {
  beta: "Beta cells (insulin)",
  alpha: "Alpha cells (glucagon)",
  liver: "Liver response",
  sensor: "Glucose sensors",
};
let gPartEnabled = { beta: true, alpha: true, liver: true, sensor: true };

document.querySelectorAll("#page-glucose .breaker").forEach(b =>
  b.addEventListener("click", () => {
    const part = b.dataset.part;
    const wantEnabled = !gPartEnabled[part];
    control(part === "sensor"
      ? { action: "sensor", value: wantEnabled }
      : { action: "effector", name: part, value: wantEnabled });
  }));

/* --- break the water loop (M22) --- */

const W_BREAKER_LABELS = {
  sensor: "Osmoreceptors",
  adh: "ADH release",
  kidney: "Kidney response",
  access: "Water access",
};
let wPartEnabled = { adh: true, kidney: true, access: true, sensor: true };

document.querySelectorAll("#page-water .breaker").forEach(b =>
  b.addEventListener("click", () => {
    const part = b.dataset.part;
    const wantEnabled = !wPartEnabled[part];
    control(part === "sensor"
      ? { action: "sensor", value: wantEnabled }
      : { action: "effector", name: part, value: wantEnabled });
  }));

/* ---------------- charts ---------------- */

/* One strip-chart panel bound to an <svg>. Series share the rolling time
   axis; y-range is fixed per panel so the eye can trust vertical position. */
function makeChart(svgId, { yMin, yMax, yStep, series, refLines = [],
                            loop = "temp", bands = [], markers = null }) {
  const svg = document.getElementById(svgId);
  const view = svg.viewBox.baseVal;
  const windowS = WINDOWS[loop];
  const hasLabels = series.some(s => s.label);
  const M = { left: 46, right: hasLabels ? 72 : 14, top: 10, bottom: 22 };

  function x(t, t0, t1) {
    return M.left + ((t - t0) / (t1 - t0)) * (view.width - M.left - M.right);
  }
  function y(v) {
    const h = view.height - M.top - M.bottom;
    return M.top + (1 - (v - yMin) / (yMax - yMin)) * h;
  }

  function el(name, attrs, text) {
    const node = document.createElementNS(SVG_NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (text !== undefined) node.textContent = text;
    svg.appendChild(node);
    return node;
  }

  function draw(records, t1) {
    svg.innerHTML = "";
    const t0 = Math.max(0, t1 - windowS);
    const tEnd = Math.max(t1, windowS);    // fill the frame from sim start

    // shaded reference bands (e.g. the healthy 70-110 mg/dL zone) first,
    // so everything else draws on top
    for (const band of bands) {
      el("rect", { x: M.left, width: view.width - M.left - M.right,
                   y: y(band.y1), height: y(band.y0) - y(band.y1),
                   fill: band.color });
    }

    // recessive grid: hairlines + muted tick labels
    for (let v = yMin; v <= yMax + 1e-9; v += yStep) {
      el("line", { x1: M.left, x2: view.width - M.right, y1: y(v), y2: y(v),
                   stroke: COLOR_GRID, "stroke-width": 1,
                   "vector-effect": "non-scaling-stroke" });
      el("text", { x: M.left - 8, y: y(v) + 4, "text-anchor": "end",
                   fill: COLOR_MUTED, "font-size": 12 },
         yStep < 1 ? v.toFixed(1) : v.toFixed(0));
    }
    const xTickEvery = windowS <= 900 ? 120 : 1200;   // 2 min / 20 min
    const firstTick = Math.ceil(t0 / xTickEvery) * xTickEvery;
    for (let t = firstTick; t <= tEnd; t += xTickEvery) {
      el("text", { x: x(t, t0, tEnd), y: view.height - 6,
                   "text-anchor": "middle", fill: COLOR_MUTED,
                   "font-size": 12 }, `${Math.round(t / 60)}m`);
    }
    el("line", { x1: M.left, x2: view.width - M.right,
                 y1: y(yMin), y2: y(yMin), stroke: COLOR_BASELINE,
                 "stroke-width": 1, "vector-effect": "non-scaling-stroke" });

    for (const ref of refLines) {
      el("line", { x1: M.left, x2: view.width - M.right,
                   y1: y(ref.y), y2: y(ref.y), stroke: COLOR_MUTED,
                   "stroke-width": 1, "stroke-dasharray": "5 4",
                   "vector-effect": "non-scaling-stroke" });
      el("text", { x: view.width - M.right, y: y(ref.y) - 5,
                   "text-anchor": "end", fill: COLOR_MUTED,
                   "font-size": 12 }, ref.label);
    }

    // event markers (M12/M21): vertical ticks from the engines' event
    // logs (doses, drinks) — recorded events, never inferred from
    // wiggles in a curve. Each marker: {t, label, color}.
    if (markers) {
      for (const m of markers()) {
        if (m.t < t0 || m.t > tEnd) continue;
        const xd = x(m.t, t0, tEnd);
        const color = m.color || COLOR_SWEAT;
        el("line", { x1: xd, x2: xd, y1: M.top + 14,
                     y2: view.height - M.bottom, stroke: color,
                     "stroke-width": 1.5, "stroke-dasharray": "2 4",
                     "vector-effect": "non-scaling-stroke" });
        el("text", { x: xd, y: M.top + 10, "text-anchor": "middle",
                     fill: color, "font-size": 11,
                     "font-weight": 600 }, m.label);
      }
    }

    for (const s of series) {
      // A series whose field isn't in the record simply doesn't draw:
      // a blind case withholds some fields (M28), and half a polyline
      // of NaN is worse than an empty panel.
      const visible = records.filter(
        r => r.t >= t0 && Number.isFinite(r[s.key]));
      const path = visible
        .map(r => `${x(r.t, t0, tEnd).toFixed(1)},${y(clampY(r[s.key])).toFixed(1)}`)
        .join(" ");
      if (path) {
        el("polyline", { points: path, fill: "none", stroke: s.color,
                         "stroke-width": s.width || 2,
                         "stroke-linejoin": "round",
                         "vector-effect": "non-scaling-stroke",
                         ...(s.dash ? { "stroke-dasharray": s.dash } : {}),
                         ...(s.opacity ? { opacity: s.opacity } : {}) });
      }
      // Direct label at the line's live end: ink text, colored tick mark —
      // the mark carries identity, the text stays readable.
      if (s.label && visible.length) {
        const last = visible[visible.length - 1];
        const yEnd = y(clampY(last[s.key]));
        const xEnd = x(last.t, t0, tEnd);
        el("line", { x1: xEnd + 3, x2: xEnd + 12, y1: yEnd, y2: yEnd,
                     stroke: s.color, "stroke-width": 3,
                     "vector-effect": "non-scaling-stroke" });
        el("text", { x: xEnd + 15, y: yEnd + 4, fill: "#52514e",
                     "font-size": 12 }, s.label);
      }
    }
  }

  function clampY(v) {
    return Math.max(yMin, Math.min(yMax, v));
  }

  // crosshair + tooltip (interaction layer: nearest record to the cursor)
  svg.addEventListener("mousemove", ev => {
    const buf = buffers[loop];
    if (!buf.pts.length) return;
    const rect = svg.getBoundingClientRect();
    const t1 = Math.max(buf.lastT, windowS);
    const t0 = Math.max(0, buf.lastT - windowS);
    const frac = (ev.clientX - rect.left) / rect.width;
    const tCursor = t0 + Math.max(0, Math.min(1,
      (frac * view.width - M.left) / (view.width - M.left - M.right)))
      * (t1 - t0);
    let best = buf.pts[0];
    for (const p of buf.pts) {
      if (Math.abs(p.t - tCursor) < Math.abs(best.t - tCursor)) best = p;
    }
    showTooltip(ev, best);
  });
  svg.addEventListener("mouseleave", hideTooltip);

  return { draw };
}

const tooltip = document.getElementById("tooltip");

function showTooltip(ev, r) {
  const mm = Math.floor(r.t / 60);
  const ss = String(Math.floor(r.t) % 60).padStart(2, "0");
  const body = ("osmolarity" in r)
    ? `osmolarity ${r.osmolarity.toFixed(1)} mOsm/L<br>` +
      `ADH ${r.adh.toFixed(2)} · thirst ${r.thirst.toFixed(2)}<br>` +
      `urine ${r.urine_rate.toFixed(1)} mL/min at ` +
      `${r.urine_osm.toFixed(0)} mOsm/L<br>` +
      `body water ${r.water_liters.toFixed(1)} L · ` +
      `gut ${r.gut_water.toFixed(0)} mL` +
      (r.exercise ? "<br>sweating" : "")
    : ("core_temp" in r)
    ? `core ${r.core_temp.toFixed(2)} °C<br>` +
      `room ${r.env_temp.toFixed(1)} °C<br>` +
      `sweat ${r.sweat.toFixed(2)} · shiver ${r.shiver.toFixed(2)}<br>` +
      `vessels ${r.vaso >= 0 ? "+" : ""}${r.vaso.toFixed(2)}` +
      (r.exercise ? "<br>exercising" : "")
    : `glucose ${r.glucose.toFixed(0)} mg/dL<br>` +
      `insulin ${r.insulin.toFixed(2)} · glucagon ${r.glucagon.toFixed(2)}<br>` +
      `injected ${r.injected_insulin.toFixed(2)} · total ` +
      `${r.total_insulin.toFixed(2)} · IOB ${r.iob_units.toFixed(1)} U<br>` +
      `liver +${r.liver_flux.toFixed(2)} · uptake −${r.uptake.toFixed(2)}<br>` +
      `gut ${r.gut_carbs.toFixed(0)} g` +
      (r.pump_enabled ? `<br>pump ${r.pump_rate.toFixed(2)} U/h` : "") +
      (r.exercise ? "<br>exercising" : "");
  tooltip.innerHTML = `<strong>t = ${mm}:${ss}</strong><br>` + body;
  tooltip.hidden = false;
  const pad = 14;
  tooltip.style.left = Math.min(ev.clientX + pad,
    window.innerWidth - tooltip.offsetWidth - pad) + "px";
  tooltip.style.top = (ev.clientY + pad) + "px";
}

function hideTooltip() { tooltip.hidden = true; }

/* Where a blind case's fast-forward ended (M28). The class joined a story
   already in progress, and the chart says exactly where — the run to the
   left of this line is every bit as real as the rest, it just happened
   in one step instead of ten minutes of wall clock. */
function caseMarker(loop) {
  return caseWarmup[loop]
    ? [{ t: caseWarmup[loop], label: "you joined here", color: COLOR_MUTED }]
    : [];
}

const coreChart = makeChart("coreChart", {
  yMin: 33, yMax: 41, yStep: 2,
  series: [{ key: "core_temp", color: COLOR_CORE }],
  refLines: [{ y: 37, label: "set point 37.0" }],
  markers: () => caseMarker("temp"),
});
const envChart = makeChart("envChart", {
  yMin: -15, yMax: 45, yStep: 15,
  series: [{ key: "env_temp", color: COLOR_ENV }],
});
const effectorChart = makeChart("effectorChart", {
  yMin: -1, yMax: 1, yStep: 0.5,
  series: [
    { key: "sweat", color: COLOR_SWEAT, label: "sweat" },
    { key: "shiver", color: COLOR_SHIVER, label: "shiver" },
    { key: "vaso", color: COLOR_VASO, label: "vessels" },
  ],
  refLines: [{ y: 0, label: "" }],
});

const COLOR_UPTAKE =
  palette.getPropertyValue("--series-uptake").trim();
const HEALTHY_BAND_FILL = "rgba(12, 163, 12, 0.07)";

const glucoseChart = makeChart("glucoseChart", {
  loop: "glucose", yMin: 40, yMax: 360, yStep: 40,
  series: [{ key: "glucose", color: COLOR_CORE }],
  bands: [{ y0: 70, y1: 110, color: HEALTHY_BAND_FILL }],
  refLines: [
    { y: 90, label: "set point 90" },
    { y: 180, label: "hyperglycemia" },
    { y: 70, label: "hypoglycemia" },
  ],
  markers: () => caseMarker("glucose").concat(
    (buffers.glucose.doses || []).map(d => ({
      t: d.t,
      label: `${d.units % 1 ? d.units.toFixed(1) : d.units.toFixed(0)} U`,
    }))),
});
const hormoneChart = makeChart("hormoneChart", {
  loop: "glucose", yMin: 0, yMax: 1, yStep: 0.5,
  series: [
    // total first so the soft envelope draws UNDER the identity lines
    { key: "total_insulin", color: COLOR_SWEAT, width: 6, opacity: 0.3 },
    { key: "insulin", color: COLOR_SWEAT, label: "insulin" },
    { key: "injected_insulin", color: COLOR_SWEAT, dash: "6 4",
      label: "injected" },
    { key: "glucagon", color: COLOR_SHIVER, label: "glucagon" },
  ],
});
const pumpChart = makeChart("pumpChart", {
  loop: "glucose", yMin: 0, yMax: 5, yStep: 1,
  series: [{ key: "pump_rate", color: COLOR_ENV, label: "pump" }],
});
const flowChart = makeChart("flowChart", {
  loop: "glucose", yMin: 0, yMax: 8, yStep: 2,
  series: [
    { key: "liver_flux", color: COLOR_VASO, label: "liver" },
    { key: "uptake", color: COLOR_UPTAKE, label: "uptake" },
  ],
});

// --- the water loop's panels (M21) ---
// Drink markers carry authorship: green = the loop drank by itself
// (the behavioral effector at work), blue = a human pressed the button.
const osmChart = makeChart("osmChart", {
  loop: "water", yMin: 260, yMax: 320, yStep: 10,
  series: [{ key: "osmolarity", color: COLOR_CORE }],
  bands: [{ y0: 285, y1: 295, color: HEALTHY_BAND_FILL }],
  refLines: [
    { y: 290, label: "set point 290" },
    { y: 305, label: "dehydration" },
    { y: 275, label: "overhydration" },
  ],
  markers: () => caseMarker("water").concat(
    (buffers.water.drinks || []).map(d => ({
      t: d.t,
      label: d.ml >= 1000 ? `${(d.ml / 1000).toFixed(1)} L`
                          : `${d.ml.toFixed(0)} mL`,
      color: d.auto ? COLOR_SWEAT : COLOR_CORE,
    }))),
});
const adhChart = makeChart("adhChart", {
  loop: "water", yMin: 0, yMax: 1, yStep: 0.5,
  series: [
    { key: "adh", color: COLOR_SWEAT, label: "ADH" },
    { key: "thirst", color: COLOR_SHIVER, label: "thirst" },
  ],
});
const urineFlowChart = makeChart("urineFlowChart", {
  loop: "water", yMin: 0, yMax: 14, yStep: 7,
  series: [{ key: "urine_rate", color: COLOR_VASO, label: "flow" }],
});
const urineOsmChart = makeChart("urineOsmChart", {
  loop: "water", yMin: 0, yMax: 1600, yStep: 400,
  series: [{ key: "urine_osm", color: COLOR_UPTAKE, label: "conc." }],
});

/* --- the coupled body (M39): both loops on one clock --- */
const bodyGlucoseChart = makeChart("bodyGlucoseChart", {
  loop: "body", yMin: 0, yMax: 400, yStep: 100,
  series: [{ key: "glucose", color: COLOR_CORE }],
  bands: [{ y0: 70, y1: 140, color: HEALTHY_BAND_FILL }],
  refLines: [
    { y: 90, label: "set point 90" },
    { y: 180, label: "kidney spills above here" },
  ],
  markers: () => (buffers.body.doses || []).map(d => ({
    t: d.t, label: `${d.units} U`, color: COLOR_UPTAKE,
  })),
});
const spillChart = makeChart("spillChart", {
  loop: "body", yMin: 0, yMax: 5, yStep: 1,
  series: [{ key: "renal_loss", color: COLOR_UPTAKE, label: "sugar out" }],
});
const bodyOsmChart = makeChart("bodyOsmChart", {
  loop: "body", yMin: 260, yMax: 330, yStep: 10,
  series: [
    { key: "osmolarity", color: COLOR_CORE, label: "plasma" },
    { key: "glucose_osm", color: COLOR_UPTAKE, label: "sugar's share" },
  ],
  bands: [{ y0: 285, y1: 295, color: HEALTHY_BAND_FILL }],
  refLines: [
    { y: 290, label: "set point 290" },
    { y: 305, label: "dehydration" },
  ],
  markers: () => (buffers.body.drinks || []).map(d => ({
    t: d.t,
    label: d.ml >= 1000 ? `${(d.ml / 1000).toFixed(1)} L`
                        : `${d.ml.toFixed(0)} mL`,
    color: d.auto ? COLOR_SWEAT : COLOR_CORE,
  })),
});
const bodyUrineChart = makeChart("bodyUrineChart", {
  loop: "body", yMin: 0, yMax: 14, yStep: 7,
  series: [{ key: "urine_rate", color: COLOR_VASO, label: "flow" }],
});
const bodyUrineOsmChart = makeChart("bodyUrineOsmChart", {
  loop: "body", yMin: 0, yMax: 1600, yStep: 400,
  series: [{ key: "urine_osm", color: COLOR_UPTAKE, label: "conc." }],
});

const chartsByLoop = {
  temp: [coreChart, envChart, effectorChart],
  glucose: [glucoseChart, hormoneChart, pumpChart, flowChart],
  water: [osmChart, adhChart, urineFlowChart, urineOsmChart],
  body: [bodyGlucoseChart, spillChart, bodyOsmChart, bodyUrineChart,
         bodyUrineOsmChart],
};

function drawAll() {
  const buf = buffers[activeLoop];
  const t1 = Math.max(buf.lastT, WINDOWS[activeLoop]);
  for (const chart of chartsByLoop[activeLoop]) chart.draw(buf.pts, t1);
}

/* --- the loop switcher (M7) --- */

const PAGE_IDS = { temp: "page-temp", glucose: "page-glucose",
                   water: "page-water", body: "page-body" };

document.querySelectorAll(".loop-tab").forEach(b =>
  b.addEventListener("click", () => {
    if (activeLoop === b.dataset.loop) return;
    activeLoop = b.dataset.loop;
    document.querySelectorAll(".loop-tab").forEach(x =>
      x.classList.toggle("active", x.dataset.loop === activeLoop));
    for (const [loop, id] of Object.entries(PAGE_IDS)) {
      document.getElementById(id).hidden = loop !== activeLoop;
    }
    poll();                      // refresh the newly visible loop now
  }));

// Browsers freeze timers in hidden tabs; refresh the moment we're back.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) poll();
});

setInterval(poll, POLL_MS);
poll();
