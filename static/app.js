/* Vital Loop front end. The browser is only a display: it polls /state,
   buffers the records the server hands back, and redraws. All physiology
   numbers come from engine history records — nothing is computed here that
   the CSV export wouldn't also contain (kickoff §5). */

"use strict";

const POLL_MS = 250;
const WINDOW_S = 600;            // visible strip: the last 10 sim-minutes
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

let pts = [];                    // engine records, oldest first
let lastT = -1;
let running = true;
let speed = 1;

/* ---------------- polling ---------------- */

async function poll() {
  let j;
  try {
    const r = await fetch("/state?since=" + lastT);
    j = await r.json();
  } catch (e) {
    return;                      // server briefly away; next poll retries
  }
  if (j.now.t < lastT) {         // sim was reset behind our back
    pts = [];
    lastT = -1;
    return;
  }
  pts.push(...j.points);
  lastT = j.now.t;
  applyServerState(j);
  // Trim the buffer: keep the visible window plus slack. Full history for
  // the CSV lives on the server; the browser only needs what it draws.
  const cutoff = lastT - WINDOW_S * 1.2;
  let firstKeep = 0;
  while (firstKeep < pts.length && pts[firstKeep].t < cutoff) firstKeep++;
  if (firstKeep > 0) pts = pts.slice(firstKeep);
  updateReadouts(j.now);
  if (window.updateDiagram) window.updateDiagram(j.now);
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

function updateReadouts(now) {
  document.getElementById("coreReadout").textContent =
    now.core_temp.toFixed(2) + " °C";
  document.getElementById("envReadout").textContent =
    now.env_temp.toFixed(1) + " °C";
  const s = Math.floor(now.t);
  const mm = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  document.getElementById("clockReadout").textContent = `${mm}:${ss}`;

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

  // Break-the-loop buttons mirror the engine's enabled flags.
  partEnabled = {
    sweat: now.sweat_enabled,
    shiver: now.shiver_enabled,
    vaso: now.vaso_enabled,
    sensor: now.sensor_enabled,
  };
  document.querySelectorAll(".breaker").forEach(b => {
    const on = partEnabled[b.dataset.part];
    b.classList.toggle("broken", !on);
    b.textContent = BREAKER_LABELS[b.dataset.part] +
      (on ? "" : " — DISABLED");
  });
}

/* ---------------- controls ---------------- */

async function control(body) {
  try {
    const r = await fetch("/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    applyServerState(await r.json());
  } catch (e) { /* next poll re-syncs the buttons */ }
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

/* --- break the loop (M5) --- */

const BREAKER_LABELS = {
  sweat: "Sweating",
  shiver: "Shivering",
  vaso: "Vessel control",
  sensor: "Temperature sensors",
};
let partEnabled = { sweat: true, shiver: true, vaso: true, sensor: true };

document.querySelectorAll(".breaker").forEach(b =>
  b.addEventListener("click", () => {
    const part = b.dataset.part;
    const wantEnabled = !partEnabled[part];
    control(part === "sensor"
      ? { action: "sensor", value: wantEnabled }
      : { action: "effector", name: part, value: wantEnabled });
  }));

/* ---------------- charts ---------------- */

/* One strip-chart panel bound to an <svg>. Series share the rolling time
   axis; y-range is fixed per panel so the eye can trust vertical position. */
function makeChart(svgId, { yMin, yMax, yStep, series, refLines = [] }) {
  const svg = document.getElementById(svgId);
  const view = svg.viewBox.baseVal;
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
    const t0 = Math.max(0, t1 - WINDOW_S);
    const tEnd = Math.max(t1, WINDOW_S);   // fill the frame from sim start

    // recessive grid: hairlines + muted tick labels
    for (let v = yMin; v <= yMax + 1e-9; v += yStep) {
      el("line", { x1: M.left, x2: view.width - M.right, y1: y(v), y2: y(v),
                   stroke: COLOR_GRID, "stroke-width": 1,
                   "vector-effect": "non-scaling-stroke" });
      el("text", { x: M.left - 8, y: y(v) + 4, "text-anchor": "end",
                   fill: COLOR_MUTED, "font-size": 12 },
         yStep < 1 ? v.toFixed(1) : v.toFixed(0));
    }
    const xTickEvery = 120;                // a label every 2 sim-minutes
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

    for (const s of series) {
      const visible = records.filter(r => r.t >= t0);
      const path = visible
        .map(r => `${x(r.t, t0, tEnd).toFixed(1)},${y(clampY(r[s.key])).toFixed(1)}`)
        .join(" ");
      if (path) {
        el("polyline", { points: path, fill: "none", stroke: s.color,
                         "stroke-width": 2, "stroke-linejoin": "round",
                         "vector-effect": "non-scaling-stroke" });
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
    if (!pts.length) return;
    const rect = svg.getBoundingClientRect();
    const t1 = Math.max(lastT, WINDOW_S);
    const t0 = Math.max(0, lastT - WINDOW_S);
    const frac = (ev.clientX - rect.left) / rect.width;
    const tCursor = t0 + Math.max(0, Math.min(1,
      (frac * view.width - M.left) / (view.width - M.left - M.right)))
      * (t1 - t0);
    let best = pts[0];
    for (const p of pts) {
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
  tooltip.innerHTML =
    `<strong>t = ${mm}:${ss}</strong><br>` +
    `core ${r.core_temp.toFixed(2)} °C<br>` +
    `room ${r.env_temp.toFixed(1)} °C<br>` +
    `sweat ${r.sweat.toFixed(2)} · shiver ${r.shiver.toFixed(2)}<br>` +
    `vessels ${r.vaso >= 0 ? "+" : ""}${r.vaso.toFixed(2)}` +
    (r.exercise ? "<br>exercising" : "");
  tooltip.hidden = false;
  const pad = 14;
  tooltip.style.left = Math.min(ev.clientX + pad,
    window.innerWidth - tooltip.offsetWidth - pad) + "px";
  tooltip.style.top = (ev.clientY + pad) + "px";
}

function hideTooltip() { tooltip.hidden = true; }

const coreChart = makeChart("coreChart", {
  yMin: 33, yMax: 41, yStep: 2,
  series: [{ key: "core_temp", color: COLOR_CORE }],
  refLines: [{ y: 37, label: "set point 37.0" }],
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

function drawAll() {
  const t1 = Math.max(lastT, WINDOW_S);
  coreChart.draw(pts, t1);
  envChart.draw(pts, t1);
  effectorChart.draw(pts, t1);
}

setInterval(poll, POLL_MS);
poll();
