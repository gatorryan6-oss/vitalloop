/* The live loop diagrams (M4 temperature, M9 glucose). Each is built once
   into its <svg>; app.js calls updateDiagram(record) / updateGlucoseDiagram
   (record) every poll with the newest engine record — the diagrams are live
   VIEWS of the running engines, never canned animations.

   Teaching details that matter:
   - The STIMULUS box lights from the TRUE error; RECEPTOR and everything
     downstream light from the SENSED error. With a damaged sensor the
     stimulus stays lit while the chain goes dark — the break is visible
     exactly where it happened.
   - On the glucose diagram the control center is TWO boxes (beta / alpha
     cells): the antagonistic pair, explicit. Insulin's suppression of
     liver release is drawn with an inhibition bar (-|), not an arrowhead —
     the standard biology convention. */

"use strict";

(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";

  const COLD = "#2a78d6";        // diverging pair: below-set-point pole
  const HOT = "#e34948";         // above-set-point pole
  const INK = "#0b0b0b";
  const INK2 = "#52514e";
  const MUTED = "#898781";
  const BASELINE = "#c3c2b7";
  const SURFACE = "#fcfcfb";
  const css = getComputedStyle(document.documentElement);
  const C_SWEAT = css.getPropertyValue("--series-sweat").trim();
  const C_SHIVER = css.getPropertyValue("--series-shiver").trim();
  const C_VASO = css.getPropertyValue("--series-vaso").trim();
  const C_UPTAKE = css.getPropertyValue("--series-uptake").trim();
  const C_PUMP = css.getPropertyValue("--series-env").trim();
  const C_INSULIN = C_SWEAT;     // match the glucose page's chart legend
  const C_GLUCAGON = C_SHIVER;
  const C_LIVER = C_VASO;

  function mix(hex, alpha) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
  }

  /* A small kit bound to one <svg>: boxes, arrows, and the live styling. */
  function makeKit(svgId) {
    const svg = document.getElementById(svgId);
    const boxes = {};
    const arrows = {};

    function el(name, attrs, parent) {
      const node = document.createElementNS(SVG_NS, name);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      (parent || svg).appendChild(node);
      return node;
    }

    // markers get svg-scoped ids so two diagrams on one page never collide
    const defs = el("defs", {});
    const arrowMarker = el("marker", {
      id: `${svgId}-arrow`, viewBox: "0 0 10 10", refX: 9, refY: 5,
      markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse",
    }, defs);
    el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: BASELINE }, arrowMarker);
    const inhibitMarker = el("marker", {
      id: `${svgId}-inhibit`, viewBox: "0 0 6 12", refX: 4, refY: 6,
      markerWidth: 6, markerHeight: 9, orient: "auto-start-reverse",
    }, defs);
    el("path", { d: "M 4 0 L 4 12", stroke: BASELINE, "stroke-width": 2.5,
                 fill: "none" }, inhibitMarker);

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
      boxes[id] = { g, rect };
    }

    function arrow(id, x1, y1, x2, y2, end = "arrow") {
      arrows[id] = el("line", {
        x1, y1, x2, y2, stroke: BASELINE, "stroke-width": 2,
        "marker-end": `url(#${svgId}-${end})`, opacity: 0.5,
      });
    }

    function pathArrow(id, d, dashed) {
      arrows[id] = el("path", {
        d, fill: "none", stroke: BASELINE, "stroke-width": 2,
        "marker-end": `url(#${svgId}-arrow)`, opacity: 0.6,
        ...(dashed ? { "stroke-dasharray": "7 5" } : {}),
      });
    }

    function caption(x, y, text) {
      el("text", { x, y, "text-anchor": "middle", fill: INK2,
                   "font-size": 13, "font-style": "italic" })
        .textContent = text;
    }

    function setGlow(id, activation, color) {
      const b = boxes[id];
      const a = Math.max(0, Math.min(1, activation));
      b.rect.setAttribute("fill",
        a > 0.02 ? mix(color, 0.12 + 0.38 * a) : SURFACE);
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

    function setBroken(id, broken) {
      const b = boxes[id];
      b.g.setAttribute("opacity", broken ? 0.45 : 1);
      if (broken) {
        b.rect.setAttribute("stroke-dasharray", "6 4");
        b.rect.setAttribute("stroke", MUTED);
        b.rect.setAttribute("stroke-width", 1.5);
        b.rect.setAttribute("fill", "#f1f0ec");
      } else {
        b.rect.removeAttribute("stroke-dasharray");
      }
    }

    return { box, arrow, pathArrow, caption, setGlow, setArrow, setBroken };
  }

  /* ================= temperature diagram (M4) ================= */

  const T = makeKit("loopDiagram");

  T.box("stim", 15, 125, 140, 84, "stimulus",
        ["Body temperature", "changes"]);
  T.box("recep", 195, 125, 150, 84, "receptor",
        ["Thermoreceptors", "(skin & core)"]);
  T.box("control", 385, 117, 175, 100, "control center",
        ["Hypothalamus", "compares to", "set point 37.0 °C"]);
  T.box("eff-sweat", 610, 40, 180, 58, "effector", ["Sweat glands"]);
  T.box("eff-shiver", 610, 138, 180, 58, "effector",
        ["Skeletal muscles", "— shiver"]);
  T.box("eff-vaso", 610, 236, 180, 58, "effector", ["Skin blood vessels"]);
  T.box("resp", 830, 125, 120, 84, "response", ["Heat lost,", "made or kept"]);

  T.arrow("a-stim", 155, 167, 193, 167);
  T.arrow("a-recep", 345, 167, 383, 167);
  T.arrow("a-sweat", 560, 140, 608, 78);
  T.arrow("a-shiver", 560, 167, 608, 167);
  T.arrow("a-vaso", 560, 195, 608, 258);
  T.arrow("a-resp-sweat", 790, 69, 845, 122);
  T.arrow("a-resp-shiver", 790, 167, 828, 167);
  T.arrow("a-resp-vaso", 790, 265, 845, 212);
  T.pathArrow("a-feedback", "M 890 209 L 890 322 L 85 322 L 85 213", true);
  T.caption(487, 315,
    "negative feedback — the response counteracts the stimulus");

  window.updateDiagram = function (r) {
    const trueErr = r.core_temp - 37.0;
    const sensed = r.error;
    const dirTrue = trueErr >= 0 ? HOT : COLD;
    const dirSensed = sensed >= 0 ? HOT : COLD;
    const stimAct = Math.abs(trueErr) / 0.5;
    const sensedAct = Math.abs(sensed) / 0.5;

    T.setGlow("stim", stimAct, dirTrue);
    T.setGlow("recep", sensedAct, dirSensed);
    T.setGlow("control", sensedAct, dirSensed);
    T.setGlow("eff-sweat", r.sweat, C_SWEAT);
    T.setGlow("eff-shiver", r.shiver, C_SHIVER);
    T.setGlow("eff-vaso", Math.abs(r.vaso), C_VASO);
    const respAct = Math.max(r.sweat, r.shiver, Math.abs(r.vaso));
    T.setGlow("resp", respAct, respAct > 0.02 ? dirSensed : BASELINE);

    T.setArrow("a-stim", stimAct, dirTrue);
    T.setArrow("a-recep", sensedAct, dirSensed);
    T.setArrow("a-sweat", r.sweat, C_SWEAT);
    T.setArrow("a-shiver", r.shiver, C_SHIVER);
    T.setArrow("a-vaso", Math.abs(r.vaso), C_VASO);
    T.setArrow("a-resp-sweat", r.sweat, C_SWEAT);
    T.setArrow("a-resp-shiver", r.shiver, C_SHIVER);
    T.setArrow("a-resp-vaso", Math.abs(r.vaso), C_VASO);
    T.setArrow("a-feedback", respAct, dirSensed);

    T.setBroken("recep", !r.sensor_enabled);
    T.setBroken("eff-sweat", !r.sweat_enabled);
    T.setBroken("eff-shiver", !r.shiver_enabled);
    T.setBroken("eff-vaso", !r.vaso_enabled);
  };

  /* ================= glucose diagram (M9) ================= */

  const G = makeKit("glucoseDiagram");

  G.box("stim", 15, 155, 140, 84, "stimulus", ["Blood glucose", "changes"]);
  G.box("recep", 185, 155, 150, 84, "receptor",
        ["Islet cells", "(pancreas)"]);
  // Phase 3: the syringe sits OUTSIDE the loop — an exogenous input a
  // person pushes in by hand. Its arrow arcs over the beta cells into the
  // same effector pathway their insulin would have driven. (Nudged left
  // at M16 to make room for the pump — Phase 4 owns this corner.)
  G.box("syringe", 15, 25, 152, 70, "injection — you",
        ["Injected insulin", "bolus & basal"]);
  // Phase 4: the closed-loop pump is a SECOND, machine-made loop drawn
  // over the biological one: it READS the stimulus (CGM) and DOSES into
  // the same muscle pathway. Sensor -> control center -> effector,
  // rebuilt in silicone — the thesis of the whole unit.
  G.box("pump", 450, 25, 190, 70, "injection — machine",
        ["Closed-loop pump", "CGM reads, pump doses"]);
  G.box("beta", 375, 60, 180, 74, "control center",
        ["Beta cells", "release insulin"]);
  G.box("alpha", 375, 260, 180, 74, "control center",
        ["Alpha cells", "release glucagon"]);
  G.box("muscle", 610, 60, 185, 74, "effector",
        ["Muscle & fat", "take up glucose"]);
  G.box("liver", 610, 260, 185, 74, "effector",
        ["Liver", "releases glucose"]);
  G.box("resp", 830, 155, 120, 90, "response",
        ["Glucose falls", "or rises"]);

  G.arrow("a-stim", 155, 197, 183, 197);
  G.arrow("a-r-beta", 335, 180, 373, 105);
  G.arrow("a-r-alpha", 335, 215, 373, 290);
  // the syringe's arc rides the very top corridor into the muscle path
  G.pathArrow("a-inject", "M 167 48 C 320 4, 560 4, 665 52");
  // the machine loop: CGM reading (stimulus -> pump), then the dose
  G.pathArrow("a-cgm", "M 85 153 C 85 95, 290 62, 448 62");
  G.arrow("a-pump-dose", 642, 62, 698, 60);
  G.arrow("a-beta-muscle", 555, 97, 608, 97);
  G.arrow("a-alpha-liver", 555, 297, 608, 297);
  // insulin INHIBITS liver release: bar end, not arrowhead
  G.arrow("a-beta-liver", 540, 134, 640, 258, "inhibit");
  G.arrow("a-muscle-resp", 795, 97, 845, 152);
  G.arrow("a-liver-resp", 795, 297, 845, 248);
  G.pathArrow("a-feedback", "M 890 245 L 890 372 L 85 372 L 85 241", true);
  G.caption(487, 365,
    "negative feedback — insulin and glucagon push in opposite directions");

  window.updateGlucoseDiagram = function (r) {
    const trueErr = r.glucose - 90.0;
    const sensed = r.error;
    const dirTrue = trueErr >= 0 ? HOT : COLD;
    const dirSensed = sensed >= 0 ? HOT : COLD;
    const stimAct = Math.abs(trueErr) / 30.0;   // full glow 30 mg/dL off
    const sensedAct = Math.abs(sensed) / 30.0;
    const liverAct = r.liver_flux / 3.0;

    G.setGlow("stim", stimAct, dirTrue);
    G.setGlow("recep", sensedAct, dirSensed);
    G.setGlow("beta", r.insulin, C_INSULIN);
    G.setGlow("alpha", r.glucagon, C_GLUCAGON);
    G.setGlow("syringe", r.injected_insulin, C_INSULIN);
    // The machine loop: box and dose arrow glow with the pump's chosen
    // rate; the CGM reading arrow goes DARK when the sensors die — the
    // artificial loop breaks at the same box the biological one does.
    const pumpAct = r.pump_enabled ? r.pump_rate / 4.0 : 0;
    // an enabled pump is never invisible: faint floor glow says "awake"
    G.setGlow("pump", r.pump_enabled ? Math.max(0.12, pumpAct) : 0, C_PUMP);
    G.setArrow("a-cgm", r.sensor_enabled ? pumpAct : 0, C_PUMP);
    G.setArrow("a-pump-dose", pumpAct, C_PUMP);
    // Effects downstream of the hormone run on TOTAL insulin — the body
    // can't tell the beta cells' insulin from the syringe's (engine truth,
    // M11). Each SOURCE box still glows with its own output only.
    G.setGlow("muscle", r.total_insulin, C_UPTAKE);
    G.setGlow("liver", liverAct, C_LIVER);
    const respAct = Math.max(r.total_insulin, liverAct);
    G.setGlow("resp", respAct, respAct > 0.02 ? dirSensed : BASELINE);

    G.setArrow("a-stim", stimAct, dirTrue);
    G.setArrow("a-r-beta", r.insulin, C_INSULIN);
    G.setArrow("a-r-alpha", r.glucagon, C_GLUCAGON);
    G.setArrow("a-inject", r.injected_insulin, C_INSULIN);
    G.setArrow("a-beta-muscle", r.insulin, C_INSULIN);
    G.setArrow("a-beta-liver", r.total_insulin, C_INSULIN);
    G.setArrow("a-alpha-liver", r.glucagon, C_GLUCAGON);
    G.setArrow("a-muscle-resp", r.total_insulin, C_UPTAKE);
    G.setArrow("a-liver-resp", liverAct, C_LIVER);
    G.setArrow("a-feedback", respAct, dirSensed);

    G.setBroken("recep", !r.sensor_enabled);
    G.setBroken("beta", !r.beta_enabled);
    G.setBroken("alpha", !r.alpha_enabled);
    G.setBroken("liver", !r.liver_enabled);
  };
})();
