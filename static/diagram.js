/* The live loop diagram (M4). Built once into #loopDiagram; app.js calls
   updateDiagram(record) every poll with the newest engine record — the
   diagram is a live VIEW of the running engine, never a canned animation.

   Teaching detail that matters: the STIMULUS box lights from the TRUE
   temperature error, while RECEPTOR and CONTROL CENTER light from the
   SENSED error (the record's `error` field). With a damaged sensor (M5)
   the stimulus stays lit while everything downstream goes dark — the
   diagram shows exactly where the loop is broken. */

"use strict";

(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const svg = document.getElementById("loopDiagram");

  const COLD = "#2a78d6";        // diverging pair: cold pole
  const HOT = "#e34948";         // hot pole
  const INK = "#0b0b0b";
  const INK2 = "#52514e";
  const MUTED = "#898781";
  const BASELINE = "#c3c2b7";
  const SURFACE = "#fcfcfb";
  const css = getComputedStyle(document.documentElement);
  const C_SWEAT = css.getPropertyValue("--series-sweat").trim();
  const C_SHIVER = css.getPropertyValue("--series-shiver").trim();
  const C_VASO = css.getPropertyValue("--series-vaso").trim();

  function el(name, attrs, parent) {
    const node = document.createElementNS(SVG_NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    (parent || svg).appendChild(node);
    return node;
  }

  // arrowhead marker
  const defs = el("defs", {});
  const marker = el("marker", {
    id: "arrowhead", viewBox: "0 0 10 10", refX: 9, refY: 5,
    markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse",
  }, defs);
  el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: BASELINE }, marker);

  const boxes = {};   // id -> {rect, roleText, arrows: []}
  const arrows = {};  // id -> line/path element

  function box(id, x, y, w, h, role, lines) {
    const g = el("g", {});
    const rect = el("rect", {
      x, y, width: w, height: h, rx: 10,
      fill: SURFACE, stroke: BASELINE, "stroke-width": 1.5,
    }, g);
    el("text", {
      x: x + w / 2, y: y + 17, "text-anchor": "middle",
      fill: MUTED, "font-size": 10, "letter-spacing": "0.12em",
      "font-weight": 600,
    }, g).textContent = role.toUpperCase();
    lines.forEach((line, i) => {
      el("text", {
        x: x + w / 2, y: y + 34 + i * 16, "text-anchor": "middle",
        fill: INK, "font-size": 13.5, "font-weight": 500,
      }, g).textContent = line;
    });
    boxes[id] = { rect, x, y, w, h };
  }

  function arrow(id, x1, y1, x2, y2) {
    arrows[id] = el("line", {
      x1, y1, x2, y2, stroke: BASELINE, "stroke-width": 2,
      "marker-end": "url(#arrowhead)", opacity: 0.5,
    });
  }

  /* ---- layout: the pipeline, then the return arrow closing the loop ---- */

  box("stim", 15, 125, 140, 84, "stimulus",
      ["Body temperature", "changes"]);
  box("recep", 195, 125, 150, 84, "receptor",
      ["Thermoreceptors", "(skin & core)"]);
  box("control", 385, 117, 175, 100, "control center",
      ["Hypothalamus", "compares to", "set point 37.0 °C"]);
  box("eff-sweat", 610, 40, 180, 58, "effector", ["Sweat glands"]);
  box("eff-shiver", 610, 138, 180, 58, "effector", ["Skeletal muscles", "— shiver"]);
  box("eff-vaso", 610, 236, 180, 58, "effector", ["Skin blood vessels"]);
  box("resp", 830, 125, 120, 84, "response",
      ["Heat lost,", "made or kept"]);

  arrow("a-stim", 155, 167, 193, 167);
  arrow("a-recep", 345, 167, 383, 167);
  arrow("a-sweat", 560, 140, 608, 78);
  arrow("a-shiver", 560, 167, 608, 167);
  arrow("a-vaso", 560, 195, 608, 258);
  arrow("a-resp-sweat", 790, 69, 845, 122);
  arrow("a-resp-shiver", 790, 167, 828, 167);
  arrow("a-resp-vaso", 790, 265, 845, 212);

  // The negative-feedback return path: response back to stimulus.
  arrows["a-feedback"] = el("path", {
    d: "M 890 209 L 890 322 L 85 322 L 85 213",
    fill: "none", stroke: BASELINE, "stroke-width": 2,
    "stroke-dasharray": "7 5", "marker-end": "url(#arrowhead)",
    opacity: 0.6,
  });
  el("text", {
    x: 487, y: 315, "text-anchor": "middle", fill: INK2,
    "font-size": 13, "font-style": "italic",
  }).textContent =
    "negative feedback — the response counteracts the stimulus";

  /* ---- the live update ---- */

  function mix(hex, alpha) {
    // hex -> rgba string, for fill washes without extra elements
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
  }

  function setGlow(id, activation, color) {
    const b = boxes[id];
    const a = Math.max(0, Math.min(1, activation));
    b.rect.setAttribute("fill", a > 0.02 ? mix(color, 0.12 + 0.38 * a) : SURFACE);
    b.rect.setAttribute("stroke", a > 0.02 ? color : BASELINE);
    b.rect.setAttribute("stroke-width", (1.5 + 2.5 * a).toFixed(2));
  }

  function setArrow(id, activation, color) {
    const a = Math.max(0, Math.min(1, activation));
    const node = arrows[id];
    node.setAttribute("opacity", (0.35 + 0.65 * a).toFixed(2));
    node.setAttribute("stroke", a > 0.05 ? color : BASELINE);
    node.setAttribute("stroke-width", (2 + 2 * a).toFixed(2));
  }

  window.updateDiagram = function (r) {
    const trueErr = r.core_temp - 37.0;       // what is really happening
    const sensed = r.error;                   // what the hypothalamus sees
    const dirTrue = trueErr >= 0 ? HOT : COLD;
    const dirSensed = sensed >= 0 ? HOT : COLD;
    const stimAct = Math.abs(trueErr) / 0.5;  // full glow at 0.5 degC off
    const sensedAct = Math.abs(sensed) / 0.5;

    setGlow("stim", stimAct, dirTrue);
    setGlow("recep", sensedAct, dirSensed);
    setGlow("control", sensedAct, dirSensed);
    setGlow("eff-sweat", r.sweat, C_SWEAT);
    setGlow("eff-shiver", r.shiver, C_SHIVER);
    setGlow("eff-vaso", Math.abs(r.vaso), C_VASO);
    const respAct = Math.max(r.sweat, r.shiver, Math.abs(r.vaso));
    setGlow("resp", respAct, respAct > 0.02 ? dirSensed : BASELINE);

    setArrow("a-stim", stimAct, dirTrue);
    setArrow("a-recep", sensedAct, dirSensed);
    setArrow("a-sweat", r.sweat, C_SWEAT);
    setArrow("a-shiver", r.shiver, C_SHIVER);
    setArrow("a-vaso", Math.abs(r.vaso), C_VASO);
    setArrow("a-resp-sweat", r.sweat, C_SWEAT);
    setArrow("a-resp-shiver", r.shiver, C_SHIVER);
    setArrow("a-resp-vaso", Math.abs(r.vaso), C_VASO);
    setArrow("a-feedback", respAct, dirSensed);
  };
})();
