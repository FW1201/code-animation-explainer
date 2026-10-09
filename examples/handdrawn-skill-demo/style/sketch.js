// 手寫感圖層（sketch.js）：用 Rough.js 畫出手繪線條，參數來自風格卡的 sketch 欄，顏色來自 tokens。
// 載入順序：tokens.js → vendor/rough.js → sketch.js（gsap 可在前或後）。
//
// 為什麼要包一層：
//   1. 決定性：Rough.js 的 seed 是 0 時會用 Math.random，每一幀線條都會抖。這裡用 id 算出固定 seed。
//   2. 風格一致：roughness、bowing、填色方式都從風格卡讀，不在場景裡寫死。
//   3. 可動畫：每一條線都設 pathLength=1，GSAP 補間 --draw 0→1 就是「一筆一筆畫出來」。
//
// 用法：
//   const g = SK.rect(svg, 100, 80, 320, 180, { id: "s2-box", fill: "primary-wash", stroke: "ink" });
//   SK.arrow(svg, 420, 170, 700, 170, { id: "s2-arr", stroke: "accent" });
//   SK.text(svg, 260, 175, "主語", { id: "s2-t1", size: "h3" });
//   SK.hide("#s2-box, #s2-arr, #s2-t1");                  // 初始狀態：還沒畫
//   SK.draw(tl, "#s2-box", AT("主語"));                    // 一筆一筆畫出
//   SK.draw(tl, "#s2-arr", ">");
// 顏色可以寫 token 名稱（ink、primary、accent、accent-2、hl、primary-wash…）或 var(--…)。
(function () {
  const S = (window.STYLE && window.STYLE.sketch) || {};
  const NS = "http://www.w3.org/2000/svg";
  const STROKE = "#010101", FILL = "#020202"; // 佔位色，畫完換成 CSS 變數

  function hash(str) {                         // 固定、非 0 的 seed
    let h = 2166136261;
    for (const c of String(str)) h = Math.imul(h ^ c.codePointAt(0), 16777619);
    return (h >>> 0) % 2147483646 + 1;
  }
  function col(c) {
    if (!c || c === "none" || c === "transparent") return null;
    return c.startsWith("#") || c.startsWith("var(") || c.includes("(") ? c : `var(--${c})`;
  }
  let auto = 0;
  function opts(o) {
    const id = o.id || `sk-${++auto}`;
    return {
      id,
      rough: {
        roughness: o.roughness ?? S.roughness ?? 1,
        bowing: o.bowing ?? S.bowing ?? 1,
        strokeWidth: o.width ?? S.stroke_width ?? 3,
        fillStyle: o.fillStyle ?? S.fill_style ?? "hachure",
        hachureGap: o.hachureGap ?? S.hachure_gap ?? 10,
        hachureAngle: o.hachureAngle ?? S.hachure_angle ?? -41,
        fillWeight: o.fillWeight ?? S.fill_weight ?? 2,
        disableMultiStroke: o.multiStroke === undefined ? S.multi_stroke === false : !o.multiStroke,
        preserveVertices: (o.roughness ?? S.roughness ?? 1) < 2,
        seed: o.seed || hash(id),
        stroke: STROKE,
        fill: col(o.fill) ? FILL : undefined,
        strokeLineDash: o.dashed ? [12, 10] : undefined,
        ...(o.rough || {}),                      // 其他 Rough.js 參數直接傳入（例：圖示用 maxRandomnessOffset）
      },
    };
  }
  // 把 Rough.js 的輸出換成 CSS 變數顏色，並標上可動畫的 class
  function paint(node, id, o) {
    const stroke = col(o.stroke || "ink"), fill = col(o.fill);
    node.setAttribute("id", id);
    node.classList.add("sk");
    node.querySelectorAll("path").forEach(p => {
      const s = p.getAttribute("stroke"), f = p.getAttribute("fill");
      if (s === STROKE) { p.removeAttribute("stroke"); p.style.stroke = stroke; p.classList.add("sk-line"); p.setAttribute("pathLength", "1"); }
      else if (s === FILL) { p.removeAttribute("stroke"); p.style.stroke = fill; p.classList.add("sk-hatch"); p.setAttribute("pathLength", "1"); }
      if (f === FILL) { p.removeAttribute("fill"); p.style.fill = fill; p.classList.add("sk-solid"); }
    });
    if (o.dashed) node.querySelectorAll(".sk-line").forEach(p => { p.classList.replace("sk-line", "sk-dashed"); p.removeAttribute("pathLength"); });
    // 一個 path 裡有好幾段（Rough.js 每一邊、每一條斜線都是一段 M…）：拆成獨立的 path，
    // 畫的時候才會一筆接一筆（同一個 path 的虛線動畫會讓每一段同時長出來，不像手在畫）
    node.querySelectorAll(".sk-line, .sk-hatch").forEach(p => {
      const segs = (p.getAttribute("d") || "").split(/(?=M)/).filter(s => s.trim());
      if (segs.length < 2) return;
      segs.forEach(d => { const q = p.cloneNode(); q.setAttribute("d", d); p.before(q); });
      p.remove();
    });
    return node;
  }
  function put(svg, node, o) { (o.parent || svg).appendChild(node); return node; }
  function rc(svg) { return rough.svg(svg); }
  function shape(svg, fn, args, o = {}) {
    const { id, rough: r } = opts(o);
    return put(svg, paint(rc(svg)[fn](...args, r), id, o), o);
  }

  const SK = {
    hash,
    rect: (svg, x, y, w, h, o) => shape(svg, "rectangle", [x, y, w, h], o),
    ellipse: (svg, cx, cy, w, h, o) => shape(svg, "ellipse", [cx, cy, w, h], o),
    circle: (svg, cx, cy, d, o) => shape(svg, "circle", [cx, cy, d], o),
    line: (svg, x1, y1, x2, y2, o) => shape(svg, "line", [x1, y1, x2, y2], o),
    polyline: (svg, pts, o) => shape(svg, "linearPath", [pts], o),
    polygon: (svg, pts, o) => shape(svg, "polygon", [pts], o),
    curve: (svg, pts, o) => shape(svg, "curve", [pts], o),
    path: (svg, d, o) => shape(svg, "path", [d], o),
    diamond(svg, x, y, w, h, o) { return SK.polygon(svg, [[x + w / 2, y], [x + w, y + h / 2], [x + w / 2, y + h], [x, y + h / 2]], o); },

    // 箭頭：一條線（或曲線）＋兩撇箭頭，同屬一個群組，畫的順序是先線後頭
    arrow(svg, x1, y1, x2, y2, o = {}) {
      const id = o.id || `sk-${++auto}`;
      const g = document.createElementNS(NS, "g");
      const bend = o.bend || 0;                   // >0 往上彎
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - bend;
      const body = bend ? SK.curve(svg, [[x1, y1], [mx, my], [x2, y2]], { ...o, id: id + "-l", parent: g })
                        : SK.line(svg, x1, y1, x2, y2, { ...o, id: id + "-l", parent: g });
      const ang = Math.atan2(y2 - (bend ? my : y1), x2 - (bend ? mx : x1));
      const len = o.head || 26, spread = 0.45;
      [ang + Math.PI - spread, ang + Math.PI + spread].forEach((a, i) =>
        SK.line(svg, x2, y2, x2 + len * Math.cos(a), y2 + len * Math.sin(a), { ...o, id: `${id}-h${i}`, parent: g }));
      g.setAttribute("id", id); g.classList.add("sk");
      void body;
      return put(svg, g, o);
    },

    // 手寫文字：每個字一個 tspan，SK.draw 時逐字浮現（像在寫）
    text(svg, x, y, str, o = {}) {
      const id = o.id || `sk-${++auto}`;
      const t = document.createElementNS(NS, "text");
      t.setAttribute("id", id); t.classList.add("sk", "sk-text");
      t.setAttribute("x", x); t.setAttribute("y", y);
      t.setAttribute("text-anchor", o.anchor || "middle"); t.setAttribute("dominant-baseline", "central");
      t.style.font = `${o.weight || 400} var(--fs-${o.size || "body"})/1 ${o.font || "var(--font-hand)"}`;
      t.style.fill = col(o.color || "ink");
      for (const ch of str) { const s = document.createElementNS(NS, "tspan"); s.textContent = ch; t.appendChild(s); }
      return put(svg, t, o);
    },

    // 手寫：中文照真正的筆順一筆一筆寫（需要 hanzi_prep.py 產生的 hanzi.js）；英數與標點用 --font-write（楷體）逐字出現，整行字型一致。
    // 回傳 { el, width, x(i) } ：x(i) 是第 i 個字的左緣，配合 SK.marker() 畫重點。字形是楷書（文鼎 AR PL KaitiM）。
    write(svg, x, y, str, o = {}) {
      const id = o.id || `sk-${++auto}`, size = typeof o.size === "number" ? o.size : parseFloat(getComputedStyle(document.documentElement).getPropertyValue(`--fs-${o.size || "h2"}`)) || 72;
      const color = col(o.color || "ink"), gap = (o.tracking ?? 0.04) * size, H = window.HANZI || {};
      const g = document.createElementNS(NS, "g"); g.setAttribute("id", id); g.classList.add("sk", "sk-write"); g.setAttribute("data-text", str);
      put(svg, g, o);
      const xs = []; let cx = 0, n = 0, run = null;
      for (const ch of str) {
        xs.push(cx);
        const d = H[ch];
        if (d) {
          run = null;
          const cg = document.createElementNS(NS, "g"); cg.classList.add("sk-char");
          cg.setAttribute("transform", `translate(${cx} ${-size / 2}) scale(${size / 1024}) translate(0 900) scale(1 -1)`);
          d.s.forEach((outline, i) => {
            const cid = `${id}-c${n}-${i}`, cp = document.createElementNS(NS, "clipPath"); cp.setAttribute("id", cid);
            const op = document.createElementNS(NS, "path"); op.setAttribute("d", outline); cp.appendChild(op); cg.appendChild(cp);
            const m = d.m[i], mp = document.createElementNS(NS, "path");
            mp.setAttribute("d", "M" + m.map(q => q.join(" ")).join(" L"));
            mp.setAttribute("clip-path", `url(#${cid})`); mp.setAttribute("pathLength", "1");
            mp.classList.add("sk-line", "sk-wstroke"); mp.style.stroke = color; mp.style.strokeWidth = 150; mp.style.fill = "none";
            mp.style.strokeLinecap = "round"; mp.style.strokeLinejoin = "round";
            mp.dataset.len = m.slice(1).reduce((s, q, k) => s + Math.hypot(q[0] - m[k][0], q[1] - m[k][1]), 0);
            cg.appendChild(mp);
          });
          g.appendChild(cg); cx += size + gap; n++;
        } else {                                   // 沒有筆順資料（英數、標點）：用楷體字型（--font-write）逐字出現，和筆順字同一種字型
          const t = document.createElementNS(NS, "text"); t.classList.add("sk-text");   // 基線對齊筆順字：1024 字框裡 y=900 是基線
          t.setAttribute("x", cx); t.setAttribute("y", size * (900 / 1024 - 0.5)); t.setAttribute("dominant-baseline", "alphabetic");
          t.style.font = `${o.weight || (/[A-Za-z0-9]/.test(ch) ? 700 : 400)} ${size * (/[A-Za-z0-9]/.test(ch) ? 0.88 : 1)}px ${o.font || "var(--font-write)"}`;   // 英數粗一級、小一號，筆畫粗細和字高才跟楷書字接近 t.style.fill = color;
          const s = document.createElementNS(NS, "tspan"); s.textContent = ch; t.appendChild(s); g.appendChild(t);
          cx += (ch === " " ? size * 0.3 : t.getComputedTextLength()) + gap * 0.5;
        }
      }
      const width = cx - gap, ox = o.anchor === "middle" ? x - width / 2 : o.anchor === "end" ? x - width : x;
      g.setAttribute("transform", `translate(${ox} ${y})`);
      return { el: g, width, size, x: i => ox + (xs[i] ?? width), left: ox, right: ox + width };
    },

    // 螢光筆：在 [x1, x2] 底下畫一筆半透明的粗線（插在 before 元素前面，才會在字的後面）
    marker(svg, x1, x2, y, o = {}) {
      const node = SK.line(svg, x1, y, x2, y + (o.tilt || -3), { width: o.width || 34, stroke: o.color || "hl", roughness: 0.4, bowing: 0.6, multiStroke: false, ...o, id: o.id });
      node.querySelectorAll(".sk-line").forEach(p => { p.style.strokeLinecap = "round"; }); node.style.opacity = o.opacity ?? 0.85;
      if (o.before) svg.insertBefore(node, o.before);
      return node;
    },

    // 初始狀態（還沒畫）。一律在建時間軸前呼叫，避免 from() 的 immediateRender 問題
    hide(target) {
      els(target).forEach(g => {
        g.querySelectorAll(".sk-line, .sk-hatch").forEach(p => p.style.setProperty("--draw", 0));
        g.querySelectorAll(".sk-solid, .sk-dashed, tspan").forEach(p => (p.style.opacity = 0));
      });
    },

    // 畫出來：線條先畫（約 70% 時間），斜線填色後補，實心填色淡入，文字逐字出現
    draw(tl, target, at, o = {}) {
      const M = window.M, dur = o.duration ?? (M ? M.draw().duration : 0.8), ease = o.ease ?? (M ? M.draw().ease : "power1.inOut");
      const label = `sk${++auto}`;
      tl.addLabel(label, at);
      els(target).forEach(g => {
        if (g.classList.contains("sk-write")) return writeOn(tl, g, label, o);
        const lines = g.querySelectorAll(".sk-line"), hatch = g.querySelectorAll(".sk-hatch"), solid = g.querySelectorAll(".sk-solid, .sk-dashed"), chars = g.querySelectorAll("tspan");
        if (lines.length) {                      // 一筆接一筆：每一筆有自己的加速與收筆，筆尖可以跟著（o.track）
          const each = (dur * 0.7) / lines.length;
          lines.forEach((p, i) => { tl.to(p, { "--draw": 1, duration: each * 1.15, ease }, `${label}+=${i * each}`); if (o.track) o.track.push({ path: p, t0: tl.labels[label] + i * each, t1: tl.labels[label] + (i + 1.15) * each }); });
        }
        if (hatch.length) tl.to(hatch, { "--draw": 1, duration: Math.max(0.04, dur * 0.12), ease: "power1.out", stagger: (dur * 0.4) / hatch.length }, `${label}+=${dur * 0.55}`);   // 斜線一條一條塗
        if (solid.length) tl.to(solid, { opacity: 1, duration: dur * 0.4, ease }, `${label}+=${dur * 0.5}`);
        if (chars.length) tl.to(chars, { opacity: 1, duration: 0.01, stagger: Math.min(0.09, dur / chars.length) }, label);
      });
      return tl;
    },
  };
  // 手寫的時間分配：每一筆的時間跟筆畫長度成正比（短的點、長的撇），字與字之間停一下；總長＝o.duration（預設每字 0.32 秒）
  function writeOn(tl, g, label, o) {
    const items = [];
    g.querySelectorAll(".sk-char, .sk-text").forEach(c => {
      if (c.classList.contains("sk-char")) c.querySelectorAll(".sk-wstroke").forEach((p, i) => items.push({ p, w: 0.25 + Math.min(1.2, +p.dataset.len / 600), first: i === 0 }));
      else items.push({ t: c.querySelector("tspan"), w: 0.6, first: true });
    });
    const chars = g.querySelectorAll(".sk-char, .sk-text").length;
    const total = o.duration ?? chars * 0.32, pause = 0.18;           // pause：換字時的停頓（以筆畫權重計）
    const W = items.reduce((s, it) => s + it.w + (it.first ? pause : 0), 0), k = total / W;
    let at = 0;
    const t0 = tl.labels[label];
    items.forEach(it => {
      if (it.first) at += pause * k;
      const d = it.w * k;
      if (it.p) { tl.to(it.p, { "--draw": 1, duration: d, ease: "power1.inOut" }, `${label}+=${at}`); if (o.track) o.track.push({ path: it.p, t0: t0 + at, t1: t0 + at + d }); }
      else tl.to(it.t, { opacity: 1, duration: 0.01 }, `${label}+=${at}`);
      at += d;
    });
    return tl;
  }
  function els(target) {
    if (typeof target === "string") return [...document.querySelectorAll(target)];
    return target instanceof Element ? [target] : [...target];
  }

  // ── Excalidraw：讀 .excalidraw JSON，用每個元素自己的 seed 重畫（長相與 Excalidraw 一致），並轉成風格色 ──
  // 預設色票對應：可用 o.palette 覆寫，例如 { "#1971c2": "accent" }
  const EXCALI = {
    "#1e1e1e": "ink", "#000000": "ink", "#343a40": "ink", "#868e96": "ink-2",
    "#1971c2": "primary", "#e03131": "accent", "#2f9e44": "accent-2", "#f08c00": "accent", "#6741d9": "accent-2", "#0c8599": "primary",
    "#a5d8ff": "primary-wash", "#ffc9c9": "accent-wash", "#b2f2bb": "accent-2-wash", "#ffec99": "hl", "#d0bfff": "accent-2-wash", "#99e9f2": "primary-wash",
    "#ffffff": "surface",
  };
  SK.excalidraw = function (svg, data, o = {}) {
    const map = Object.assign({}, EXCALI, o.palette || {});
    const tone = c => (!c || c === "transparent" ? null : map[c.toLowerCase()] || c);
    const els = (data.elements || data).filter(e => !e.isDeleted);
    const xs = els.flatMap(e => [e.x, e.x + (e.width || 0)]), ys = els.flatMap(e => [e.y, e.y + (e.height || 0)]);
    const pad = o.pad ?? 40, minX = Math.min(...xs) - pad, minY = Math.min(...ys) - pad;
    svg.setAttribute("viewBox", `${minX} ${minY} ${Math.max(...xs) - minX + pad} ${Math.max(...ys) - minY + pad}`);
    const steps = [], byId = {};
    for (const e of els) {
      const base = {
        id: (o.prefix || "ex-") + e.id, seed: e.seed, roughness: e.roughness, width: Math.max(2, (e.strokeWidth || 1) * (o.widthScale || 2)),
        fillStyle: e.fillStyle, stroke: tone(e.strokeColor) || "ink", fill: tone(e.backgroundColor), dashed: e.strokeStyle && e.strokeStyle !== "solid",
      };
      let node;
      const cx = e.x + e.width / 2, cy = e.y + e.height / 2;
      if (e.type === "rectangle") node = SK.rect(svg, e.x, e.y, e.width, e.height, base);
      else if (e.type === "ellipse") node = SK.ellipse(svg, cx, cy, e.width, e.height, base);
      else if (e.type === "diamond") node = SK.diamond(svg, e.x, e.y, e.width, e.height, base);
      else if (e.type === "line" || e.type === "freedraw") {
        const pts = e.points.map(([px, py]) => [e.x + px, e.y + py]);
        node = e.type === "freedraw" ? SK.polyline(svg, pts, { ...base, roughness: 0.4 }) : SK.polyline(svg, pts, base);
      } else if (e.type === "arrow") {
        const pts = e.points.map(([px, py]) => [e.x + px, e.y + py]), a = pts[pts.length - 2], b = pts[pts.length - 1];
        if (pts.length > 2) {
          const g = document.createElementNS(NS, "g");
          SK.curve(svg, pts, { ...base, id: base.id + "-l", parent: g });
          const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
          [ang + Math.PI - 0.45, ang + Math.PI + 0.45].forEach((t, i) => SK.line(svg, b[0], b[1], b[0] + 24 * Math.cos(t), b[1] + 24 * Math.sin(t), { ...base, id: `${base.id}-h${i}`, parent: g }));
          g.setAttribute("id", base.id); g.classList.add("sk"); svg.appendChild(g); node = g;
        } else node = SK.arrow(svg, a[0], a[1], b[0], b[1], base);
      } else if (e.type === "text") {
        const lines = String(e.text).split("\n"), lh = (e.lineHeight || 1.25) * e.fontSize;
        const g = document.createElementNS(NS, "g"); g.setAttribute("id", base.id); g.classList.add("sk", "sk-text");
        const anchor = e.textAlign === "center" ? "middle" : e.textAlign === "right" ? "end" : "start";
        const tx = anchor === "middle" ? cx : anchor === "end" ? e.x + e.width : e.x;
        lines.forEach((ln, i) => {
          const t = SK.text(svg, tx, e.y + lh * (i + 0.5), ln, { id: `${base.id}-${i}`, anchor, color: tone(e.strokeColor) || "ink", parent: g });
          t.style.fontSize = `${e.fontSize * (o.textScale || 1)}px`;
        });
        svg.appendChild(g); node = g;
      } else continue;
      if (e.angle) node.setAttribute("transform", `rotate(${(e.angle * 180) / Math.PI} ${cx} ${cy})`);
      byId[e.id] = node;
      // 綁在容器上的文字併入容器那一步；其他元素各自一步（Excalidraw 的圖層順序＝繪製順序）
      const host = e.type === "text" && e.containerId && byId[e.containerId];
      const step = host && steps.find(s => s.nodes.includes(host));
      if (step) { step.nodes.push(node); step.label = step.label || e.text; }
      else steps.push({ id: e.id, type: e.type, label: e.type === "text" ? e.text : "", nodes: [node] });
    }
    return steps;
  };
  // 依序畫出 Excalidraw 的每一步。anchors 可指定某一步在哪個時間點開始：{ "元素id或文字": AT("關鍵字") }
  SK.play = function (tl, steps, at, o = {}) {
    steps.forEach(s => SK.hide(s.nodes));
    let first = true;
    for (const s of steps) {
      const when = (o.anchors && (o.anchors[s.id] ?? o.anchors[s.label])) ?? (first ? at : `>+=${o.gap ?? 0.15}`);
      SK.draw(tl, s.nodes, when, { duration: o.duration });
      first = false;
    }
    return tl;
  };

  window.SK = SK;
})();
