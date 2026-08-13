/* Vital Loop front end. The browser is only a display: it polls /state,
   buffers the records the server hands back, and redraws. All physiology
   numbers come from engine history records — nothing is computed here that
   the CSV export wouldn't also contain (kickoff §5). */

"use strict";

const POLL_MS = 250;
// Visible strip per loop: temperature moves in minutes, glucose in hours.
const WINDOWS = { temp: 600, glucose: 7200 };
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

let activeLoop = "temp";         // which loop the page is showing
const buffers = {                // engine records per loop, oldest first
  temp: { pts: [], lastT: -1 },
  glucose: { pts: [], lastT: -1 },
};
let running = true;              // play/speed of the ACTIVE loop's runner
let speed = 1;

/* ---------------- polling ---------------- */

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
  if (j.now.t < buf.lastT) {     // sim was reset behind our back
    buf.pts = [];
    buf.lastT = -1;
    return;
  }
  buf.pts.push(...j.points);
  buf.lastT = j.now.t;
  // Trim the buffer: keep the visible window plus slack. Full history for
  // the CSV lives on the server; the browser only needs what it draws.
  const cutoff = buf.lastT - WINDOWS[loop] * 1.2;
  let firstKeep = 0;
  while (firstKeep < buf.pts.length && buf.pts[firstKeep].t < cutoff) {
    firstKeep++;
  }
  if (firstKeep > 0) buf.pts = buf.pts.slice(firstKeep);
  if (loop !== activeLoop) return;   // tab switched while we fetched
  applyServerState(j);
  updateReadouts(j.now);
  if (loop === "temp" && window.updateDiagram) {
    window.updateDiagram(j.now);
  } else if (loop === "glucose" && window.updateGlucoseDiagram) {
    window.updateGlucoseDiagram(j.now);
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

function updateReadouts(now) {
  const s = Math.floor(now.t);
  const mm = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  setText("clockReadout", `${mm}:${ss}`);

  if (activeLoop === "glucose") {
    setText("r1Label", "glucose");
    setText("r1Value", now.glucose.toFixed(0) + " mg/dL");
    setText("r2Label", "gut carbs");
    setText("r2Value", now.gut_carbs.toFixed(0) + " g");
    const gex = document.getElementById("gExerciseBtn");
    gex.textContent = now.exercise ? "Exercise: ON" : "Exercise: off";
    gex.setAttribute("aria-pressed", String(now.exercise));
    lastExercise = now.exercise;
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
    return;
  }

  setText("r1Label", "core temp");
  setText("r1Value", now.core_temp.toFixed(2) + " °C");
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

  // Break-the-loop buttons mirror the engine's enabled flags.
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

/* ---------------- controls ---------------- */

async function control(body) {
  try {
    const r = await fetch(`/control?loop=${activeLoop}`, {
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

/* ---------------- charts ---------------- */

/* One strip-chart panel bound to an <svg>. Series share the rolling time
   axis; y-range is fixed per panel so the eye can trust vertical position. */
function makeChart(svgId, { yMin, yMax, yStep, series, refLines = [],
                            loop = "temp", bands = [] }) {
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
  const body = ("core_temp" in r)
    ? `core ${r.core_temp.toFixed(2)} °C<br>` +
      `room ${r.env_temp.toFixed(1)} °C<br>` +
      `sweat ${r.sweat.toFixed(2)} · shiver ${r.shiver.toFixed(2)}<br>` +
      `vessels ${r.vaso >= 0 ? "+" : ""}${r.vaso.toFixed(2)}` +
      (r.exercise ? "<br>exercising" : "")
    : `glucose ${r.glucose.toFixed(0)} mg/dL<br>` +
      `insulin ${r.insulin.toFixed(2)} · glucagon ${r.glucagon.toFixed(2)}<br>` +
      `liver +${r.liver_flux.toFixed(2)} · uptake −${r.uptake.toFixed(2)}<br>` +
      `gut ${r.gut_carbs.toFixed(0)} g` +
      (r.exercise ? "<br>exercising" : "");
  tooltip.innerHTML = `<strong>t = ${mm}:${ss}</strong><br>` + body;
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
});
const hormoneChart = makeChart("hormoneChart", {
  loop: "glucose", yMin: 0, yMax: 1, yStep: 0.5,
  series: [
    { key: "insulin", color: COLOR_SWEAT, label: "insulin" },
    { key: "glucagon", color: COLOR_SHIVER, label: "glucagon" },
  ],
});
const flowChart = makeChart("flowChart", {
  loop: "glucose", yMin: 0, yMax: 8, yStep: 2,
  series: [
    { key: "liver_flux", color: COLOR_VASO, label: "liver" },
    { key: "uptake", color: COLOR_UPTAKE, label: "uptake" },
  ],
});

const chartsByLoop = {
  temp: [coreChart, envChart, effectorChart],
  glucose: [glucoseChart, hormoneChart, flowChart],
};

function drawAll() {
  const buf = buffers[activeLoop];
  const t1 = Math.max(buf.lastT, WINDOWS[activeLoop]);
  for (const chart of chartsByLoop[activeLoop]) chart.draw(buf.pts, t1);
}

/* --- the loop switcher (M7) --- */

document.querySelectorAll(".loop-tab").forEach(b =>
  b.addEventListener("click", () => {
    if (activeLoop === b.dataset.loop) return;
    activeLoop = b.dataset.loop;
    document.querySelectorAll(".loop-tab").forEach(x =>
      x.classList.toggle("active", x.dataset.loop === activeLoop));
    document.getElementById("page-temp").hidden = activeLoop !== "temp";
    document.getElementById("page-glucose").hidden =
      activeLoop !== "glucose";
    poll();                      // refresh the newly visible loop now
  }));

// Browsers freeze timers in hidden tabs; refresh the moment we're back.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) poll();
});

setInterval(poll, POLL_MS);
poll();
