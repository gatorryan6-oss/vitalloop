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
      const lineNodes = lines.map((line, i) => {
        const node = el("text", {
          x: x + w / 2, y: y + 34 + i * 16, "text-anchor": "middle",
          fill: INK, "font-size": 13.5, "font-weight": 500,
        }, g);
        node.textContent = line;
        return node;
      });
      // The "status withheld" badge (M28), hidden until a blind case
      // turns it on. It sits in the corner and leaves the box's GLOW
      // alone on purpose: how hard this part is working is the evidence,
      // and only whether it is broken is being kept back.
      // `visibility`, not `opacity`: an opacity-0 badge is invisible but
      // still in the text and the accessibility tree, so every box read
      // as "?" to a screen reader and to anything scraping the page.
      const hint = el("g", { visibility: "hidden" }, g);
      el("circle", { cx: x + w - 15, cy: y + 15, r: 9, fill: SURFACE,
                     stroke: MUTED, "stroke-width": 1.5,
                     "stroke-dasharray": "3 2" }, hint);
      el("text", { x: x + w - 15, y: y + 20, "text-anchor": "middle",
                   fill: MUTED, "font-size": 13, "font-weight": 700 },
         hint).textContent = "?";
      boxes[id] = { g, rect, lines: lineNodes, hint };
    }

    function setLine(id, index, text, emphasize) {
      /* live text in a box (M19: the fever set point) - only touches
         the DOM when the string actually changes */
      const node = boxes[id].lines[index];
      if (node.textContent !== text) node.textContent = text;
      node.setAttribute("fill", emphasize ? HOT : INK);
      node.setAttribute("font-weight", emphasize ? 700 : 500);
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

    function setUnknown(id, on) {
      boxes[id].hint.setAttribute("visibility", on ? "visible" : "hidden");
    }

    return { box, arrow, pathArrow, caption, setGlow, setArrow, setBroken,
             setLine, setUnknown };
  }

  /* One box's status. While a blind case runs (M28) the app is not
     saying which parts work, so a box that could be the answer wears a
     "?" instead of graying out — because a grayed box IS the answer. */
  function status(kit, id, broken, blind) {
    kit.setBroken(id, blind ? false : broken);
    kit.setUnknown(id, !!blind);
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

  window.updateDiagram = function (r, blind) {
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

    // The five boxes that are also the five answers on the temp loop.
    status(T, "recep", !r.sensor_enabled, blind);
    status(T, "control", false, blind);
    status(T, "eff-sweat", !r.sweat_enabled, blind);
    status(T, "eff-shiver", !r.shiver_enabled, blind);
    status(T, "eff-vaso", !r.vaso_enabled, blind);

    // Fever (M19): the box shows the number the loop is DEFENDING right
    // now — under fever the label turns hot-red and reads 39.0, and the
    // class sees the machinery obeying a moved thermostat.
    //
    // Which makes it an answer key during a case, and worse, a LIE if it
    // were left to fall back to 37.0 with fever_offset redacted. So it
    // says outright that it isn't saying (M28).
    const defended = 37.0 + (r.fever_offset || 0);
    T.setLine("control", 2,
              blind ? "set point — ?" : `set point ${defended.toFixed(1)} °C`,
              !blind && !!r.fever_offset);
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

  window.updateGlucoseDiagram = function (r, blind) {
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
    // M11) — scaled by how well the tissues HEAR it (M19): under type 2
    // the beta box and its arrows blaze while the muscle box sits dim.
    // Each SOURCE box still glows with its own output only.
    //
    // That reading needs insulin_sensitivity, and a blind case withholds
    // it (M28). Falling back to 1 would paint a muscle box blazing away
    // while the patient's glucose sits at 160 — a lie about the exact
    // case the class is trying to read — so instead the box goes neutral
    // and wears the "?" with the others. `uptake` is no substitute: the
    // M28 sweep found type 2 uptake running slightly ABOVE healthy, mass
    // action making up for what the insulin can't buy.
    const heard = blind ? 0 : r.total_insulin * (r.insulin_sensitivity ?? 1);
    G.setGlow("muscle", heard, C_UPTAKE);
    G.setGlow("liver", liverAct, C_LIVER);
    const respAct = Math.max(heard, liverAct);
    G.setGlow("resp", respAct, respAct > 0.02 ? dirSensed : BASELINE);

    G.setArrow("a-stim", stimAct, dirTrue);
    G.setArrow("a-r-beta", r.insulin, C_INSULIN);
    G.setArrow("a-r-alpha", r.glucagon, C_GLUCAGON);
    G.setArrow("a-inject", r.injected_insulin, C_INSULIN);
    G.setArrow("a-beta-muscle", r.insulin, C_INSULIN);
    G.setArrow("a-beta-liver", heard, C_INSULIN);
    G.setArrow("a-alpha-liver", r.glucagon, C_GLUCAGON);
    G.setArrow("a-muscle-resp", heard, C_UPTAKE);
    G.setArrow("a-liver-resp", liverAct, C_LIVER);
    G.setArrow("a-feedback", respAct, dirSensed);

    // The five boxes that are also the five answers on the glucose loop.
    // Muscle & fat has no breaker behind it — type 2 is a knob, not a
    // switch — but it is an answer, so it wears the badge too.
    status(G, "recep", !r.sensor_enabled, blind);
    status(G, "beta", !r.beta_enabled, blind);
    status(G, "alpha", !r.alpha_enabled, blind);
    status(G, "liver", !r.liver_enabled, blind);
    status(G, "muscle", false, blind);
  };

  /* ================= water diagram (M22) ================= */

  const W = makeKit("waterDiagram");

  W.box("stim", 15, 165, 140, 84, "stimulus",
        ["Blood osmolarity", "changes"]);
  W.box("recep", 185, 165, 150, 84, "receptor",
        ["Osmoreceptors", "(hypothalamus)"]);
  W.box("control", 375, 160, 180, 94, "control center",
        ["Hypothalamus →", "posterior pituitary", "releases ADH"]);
  W.box("kidney", 610, 60, 185, 74, "effector",
        ["Kidneys", "retain water"]);
  // The loop's other arm is a BEHAVIOR - the role label says so, and
  // the caption under it names the catch: this effector only works if
  // the outside world provides something to drink.
  W.box("thirst", 610, 270, 185, 74, "effector — a behavior",
        ["Thirst → drinking", "(needs water nearby)"]);
  W.box("resp", 830, 165, 120, 90, "response",
        ["Water kept", "or gained"]);

  W.arrow("a-stim", 155, 207, 183, 207);
  W.arrow("a-recep", 335, 207, 373, 207);
  W.arrow("a-c-kidney", 555, 180, 608, 105);
  W.arrow("a-c-thirst", 555, 234, 608, 300);
  W.arrow("a-kidney-resp", 795, 97, 845, 162);
  W.arrow("a-thirst-resp", 795, 307, 845, 258);
  W.pathArrow("a-feedback", "M 890 255 L 890 392 L 85 392 L 85 251", true);
  W.caption(700, 372,
    "drinking reaches through the OUTSIDE WORLD — no other effector does");
  W.caption(400, 392,
    "negative feedback — the response counteracts the stimulus");

  const URINE_MAX = 12.0;        // mL/min at full flood (engine ceiling)

  window.updateWaterDiagram = function (r, blind) {
    const trueErr = r.osmolarity - 290.0;
    const sensed = r.error;
    const dirTrue = trueErr >= 0 ? HOT : COLD;    // concentrated runs hot
    const dirSensed = sensed >= 0 ? HOT : COLD;
    const stimAct = Math.abs(trueErr) / 10.0;     // full glow 10 mOsm off
    const sensedAct = Math.abs(sensed) / 10.0;
    // The kidney box glows with how loudly it OBEYS the hormone: dark
    // means flooding — "retain water" is the box's labeled action, and
    // a deaf kidney (nephrogenic DI) grays out instead.
    //
    // A blind case withholds kidney_enabled (M28), so there the box
    // reads the OBSERVABLE instead: a kidney retaining water passes
    // almost none, a flooding one passes 12 mL/min. Deaf kidneys and no
    // ADH at all then look identical — which is honest, because in both
    // the kidney is not holding water, and telling those two apart is
    // the class's job, off the hormone trace.
    const heard = blind
      ? Math.max(0, 1 - r.urine_rate / URINE_MAX)
      : (r.kidney_enabled ? r.adh : 0);

    W.setGlow("stim", stimAct, dirTrue);
    W.setGlow("recep", sensedAct, dirSensed);
    W.setGlow("control", r.adh, C_SWEAT);
    W.setGlow("kidney", heard, C_SWEAT);
    W.setGlow("thirst", r.thirst, C_SHIVER);
    const respAct = Math.max(heard, r.thirst);
    W.setGlow("resp", respAct, respAct > 0.02 ? dirSensed : BASELINE);

    W.setArrow("a-stim", stimAct, dirTrue);
    W.setArrow("a-recep", sensedAct, dirSensed);
    W.setArrow("a-c-kidney", r.adh, C_SWEAT);
    W.setArrow("a-c-thirst", r.thirst, C_SHIVER);
    W.setArrow("a-kidney-resp", heard, C_SWEAT);
    W.setArrow("a-thirst-resp", r.thirst, C_SHIVER);
    W.setArrow("a-feedback", respAct, dirSensed);

    // The four boxes that are also the four answers on the water loop.
    status(W, "recep", !r.sensor_enabled, blind);
    status(W, "control", !r.adh_enabled, blind);
    status(W, "kidney", !r.kidney_enabled, blind);
    status(W, "thirst", !r.water_access, blind);
  };

  /* ================= the coupled body (M40) =================

     Not a third copy of the loop diagram — a picture of the JOIN. The
     top row is the sugar loop's last resort (the kidney), the bottom
     row is the water loop answering, and the two arrows down the middle
     are the whole of Phase 10:

       LINK 1  sugar that could not be reabsorbed spills into the urine
               and drags water out with it (osmotic diuresis);
       LINK 2  sugar still IN the blood is itself an osmole, so the
               receptors feel it directly.

     The spill arrow is DARK below 180 mg/dL. That darkness is the
     lesson: this is a threshold, not a leak, and a healthy body's two
     loops never talk to each other at all. */

  const B = makeKit("bodyDiagram");
  const SPILL_FULL = 3.5;        // mg/dL/min that counts as "wide open"
  const OSM_SHARE_FULL = 15.0;   // mOsm/L of sugar that counts as a lot

  B.box("glucose", 25, 35, 205, 84, "the sugar loop",
        ["Blood glucose", "— mg/dL"]);
  B.box("kidney", 300, 35, 220, 84, "effector — the kidney",
        ["Tubules reabsorb", "the filtered sugar"]);
  B.box("sugarout", 590, 35, 210, 84, "response",
        ["Sugar into the urine", "—"]);
  B.box("waterout", 590, 175, 210, 70, "the link",
        ["Water follows", "the osmoles out"]);
  B.box("osm", 590, 300, 210, 84, "the water loop",
        ["Plasma osmolarity", "— mOsm/L"]);
  B.box("adh", 300, 300, 220, 84, "control center",
        ["ADH holds water,", "thirst asks for more"]);
  B.box("drink", 25, 300, 205, 84, "response",
        ["Drinking", "— and drinking"]);

  B.arrow("a-g-kidney", 232, 77, 297, 77);
  B.arrow("a-spill", 522, 77, 587, 77);
  B.arrow("a-sugar-water", 695, 121, 695, 172);
  B.arrow("a-water-osm", 695, 247, 695, 297);
  B.arrow("a-osm-adh", 587, 342, 523, 342);
  B.arrow("a-adh-drink", 297, 342, 233, 342);
  // Link 2 takes the long way round the outside, so it never pretends
  // to be part of the kidney chain: this sugar never left the blood.
  B.pathArrow("a-osmole", "M 127 121 L 127 262 L 640 262 L 640 296", true);

  B.caption(555, 150, "nothing crosses below 180 mg/dL — a THRESHOLD, not a leak");
  B.caption(360, 255, "link 2: the sugar still in the blood is itself an osmole");
  B.caption(480, 412,
    "two loops, one body — what the sugar loop cannot fix becomes the water loop's problem");

  window.updateBodyDiagram = function (r) {
    const gErr = r.glucose - 90.0;
    const oErr = r.osmolarity - 290.0;
    const dirG = gErr >= 0 ? HOT : COLD;
    const dirO = oErr >= 0 ? HOT : COLD;
    const spill = (r.renal_loss || 0) / SPILL_FULL;
    const share = (r.glucose_osm || 0) / OSM_SHARE_FULL;

    // Live numbers in the boxes, so the picture is also a readout.
    B.setLine("glucose", 1, `${r.glucose.toFixed(0)} mg/dL`, r.glucose > 180);
    B.setLine("sugarout", 1,
      spill > 0.003 ? `${r.renal_loss.toFixed(2)} mg/dL·min` : "nothing, yet",
      spill > 0.003);
    B.setLine("osm", 1, `${r.osmolarity.toFixed(1)} mOsm/L`,
      r.osmolarity > 305);

    B.setGlow("glucose", Math.abs(gErr) / 120, dirG);
    // The kidney glows with how hard it is DUMPING sugar — the box's
    // labelled job is reabsorption, and spilling is that job failing.
    B.setGlow("kidney", spill, C_UPTAKE);
    B.setGlow("sugarout", spill, C_UPTAKE);
    B.setGlow("waterout", spill, C_SWEAT);
    B.setGlow("osm", Math.abs(oErr) / 15, dirO);
    B.setGlow("adh", Math.max(r.adh, r.thirst), C_SWEAT);
    B.setGlow("drink", r.thirst, C_SHIVER);

    B.setArrow("a-g-kidney", Math.abs(gErr) / 120, dirG);
    B.setArrow("a-spill", spill, C_UPTAKE);
    B.setArrow("a-sugar-water", spill, C_SWEAT);
    B.setArrow("a-water-osm", spill, C_SWEAT);
    B.setArrow("a-osm-adh", Math.abs(oErr) / 15, dirO);
    B.setArrow("a-adh-drink", r.thirst, C_SHIVER);
    B.setArrow("a-osmole", share, C_UPTAKE);
  };
})();
