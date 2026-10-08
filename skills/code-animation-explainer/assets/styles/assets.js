// 素材對齊（assets.js）：外部收集來的照片、圖示、插畫，以及程式畫的卡片／方框，放進畫面前都依風格卡處理，
// 才不會「畫面是水墨、照片是手機原圖」「卡片是手繪、圖示是別人的線寬」。
// 參數來源：風格卡 detail.photo（照片管線）、detail.illustration（插畫）、detail.object（物件）、assets.icon（圖示）。
// 載入順序：tokens.js → rough.js → sketch.js → assets.js。
//
// 用法（標記後一次處理）：
//   <img data-as="photo" src="leaf.jpg" alt="葉片" data-src="維基共享資源">
//   <svg data-as="icon" id="s2-ic-leaf" viewBox="0 0 24 24">…Lucide 圖示…</svg>
//   <svg data-as="illus" viewBox="…">…多色插畫…</svg>
//   <div class="card">…</div>   <div class="obj">…</div>   // 程式畫的物件：手繪類風格會改用 Rough.js 畫外框
//   <script>AS.apply();</script>          // 或 AS.photo()／AS.icon()／AS.illus()／AS.objects() 單獨處理
// 所有處理都是固定參數、固定種子，逐格渲染每次結果一樣。
(function () {
  const ST = window.STYLE || {}, A = ST.assets || {}, NS = "http://www.w3.org/2000/svg";
  const TOKENS = ["ink", "ink-2", "primary", "accent", "accent-2", "hl", "bg", "surface"];
  const ctx = document.createElement("canvas").getContext("2d");

  function cssVar(k) { return getComputedStyle(document.documentElement).getPropertyValue("--" + k).trim(); }
  function toRGB(c) {                         // 任何 CSS 顏色（含 var(--x)、token 名稱、mix(a,b,0.4)）→ [r,g,b] 0–1
    const mx = /^mix\(\s*([^,]+),\s*([^,]+),\s*([\d.]+)\s*\)$/.exec(c || "");
    if (mx) { const a = toRGB(mx[1]), b = toRGB(mx[2]), p = +mx[3]; return a.map((x, i) => x * p + b[i] * (1 - p)); }
    if (TOKENS.includes(c)) c = (ST.color && ST.color[c]) || cssVar(c);
    else if (c && c.startsWith("var(--")) c = cssVar(c.slice(6, -1));
    ctx.fillStyle = "#000"; ctx.fillStyle = c || "#000";
    const v = ctx.fillStyle;                  // 瀏覽器正規化成 #rrggbb 或 rgba()
    if (v[0] === "#") return [1, 3, 5].map(i => parseInt(v.slice(i, i + 2), 16) / 255);
    return v.match(/[\d.]+/g).slice(0, 3).map(x => +x / 255);
  }
  const f = n => (+n).toFixed(4);
  const lumOf = c => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];

  // 舊風格卡只有 assets.photo.treatment：轉成 detail.photo 的寫法
  const LEGACY = {
    none: { mode: "color" }, soft: { mode: "color", tone: { saturation: 0.7, contrast: 0.9, brightness: 0.06 } },
    duotone: { mode: "map" }, halftone: { mode: "halftone", halftone: 7 }, ink: { mode: "ink" },
    silhouette: { mode: "silhouette" }, chalk: { mode: "chalk" }, blueprint: { mode: "lines" },
  };
  const DP = () => (ST.detail && ST.detail.photo) || Object.assign({ map: (A.photo && A.photo.tones) || ["ink", "bg"] }, LEGACY[(A.photo || {}).treatment || "none"]);

  // ── 照片管線：色調 → 主處理（映射／網點／色階／線稿…）→ 顆粒 → 紙紋。顏色全部來自風格 tokens ──
  const LUM = '<feColorMatrix type="matrix" values="0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0 0 0 1 0"/>';
  const table = (stops, type = "table") => {
    const c = stops.map(toRGB);
    return `<feComponentTransfer>${["R", "G", "B"].map((ch, i) => `<feFunc${ch} type="${type}" tableValues="${c.map(x => f(x[i])).join(" ")}"/>`).join("")}</feComponentTransfer>`;
  };
  function photoFilter(P) {
    const T = P.tone || {}, map = P.map || ["ink", "bg"], out = [];
    const sat = T.saturation ?? 1, con = T.contrast ?? 1, bri = T.brightness ?? 0, w = T.warmth ?? 0;
    out.push(`<feColorMatrix type="saturate" values="${f(sat)}"/>`);
    out.push(`<feComponentTransfer>${["R", "G", "B"].map(ch => `<feFunc${ch} type="linear" slope="${f(con)}" intercept="${f((1 - con) / 2 + bri)}"/>`).join("")}</feComponentTransfer>`);
    out.push(`<feColorMatrix type="matrix" values="${f(1 + w)} 0 0 0 0  0 1 0 0 0  0 0 ${f(1 - w)} 0 0  0 0 0 1 0" result="tone"/>`);
    const ink = toRGB("ink");
    const edges = `<feGaussianBlur in="tone" stdDeviation="2.2"/>${LUM}<feConvolveMatrix order="3" kernelMatrix="-1 -1 -1 -1 8 -1 -1 -1 -1" preserveAlpha="true"/>` +
      `<feColorMatrix type="matrix" values="0 0 0 0 ${f(ink[0])}  0 0 0 0 ${f(ink[1])}  0 0 0 0 ${f(ink[2])}  9 9 9 0 -0.55" result="lines"/>`;
    switch (P.mode) {
      case "map": {
        out.push(LUM + table(map).replace("<feComponentTransfer>", '<feComponentTransfer result="mapped">'));
        const m = P.map_mix ?? 1;
        if (m < 1) out.push(`<feComposite in="mapped" in2="tone" operator="arithmetic" k1="0" k2="${f(m)}" k3="${f(1 - m)}" k4="0"/>`);
        break;
      }
      case "posterize":                       // 色階：先柔化去雜訊，再把亮度切成幾段、每段一個風格色（像向量插畫）
        out.push(`<feGaussianBlur stdDeviation="2.4"/>${LUM}${table(map, "discrete")}`); break;
      case "halftone": {                      // 真的網點：亮度和網點圖比大小，暗處點大、亮處點小
        const d = P.halftone || 7;
        const dot = `data:image/svg+xml;utf8,${encodeURIComponent(`<svg xmlns="${NS}" width="${d}" height="${d}"><defs><radialGradient id="g"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#fff"/></radialGradient></defs><rect width="${d}" height="${d}" fill="#fff"/><circle cx="${d / 2}" cy="${d / 2}" r="${d * 0.72}" fill="url(#g)"/></svg>`)}`;
        out.push(`${LUM.replace("/>", ' result="L"/>')}<feImage href="${dot}" x="0" y="0" width="${d}" height="${d}" result="dot"/><feTile in="dot" result="D"/>` +
          `<feComposite in="L" in2="D" operator="arithmetic" k1="0" k2="1" k3="1" k4="-0.5"/>${table([map[0], map[map.length - 1]], "discrete")}`);
        break;
      }
      case "lines":                           // 線稿：邊緣線＝ink 色（藍圖是淺色線），底下墊一層很淡的明暗，暗的照片才不會整張消失
        out.push(`${LUM.replace("/>", ' in="tone"/>')}${table(map)}<feComponentTransfer result="base"><feFuncA type="linear" slope="${f(P.map_mix ?? 0)}"/></feComponentTransfer>${edges}<feComposite in="lines" in2="base" operator="over"/>`);
        break;
      case "chalk":                           // 粉筆：淡淡的明暗底＋粉筆線，線被顆粒啃掉一些
        out.push(`${LUM.replace("/>", ' in="tone"/>')}${table(map)}<feComponentTransfer result="base"><feFuncA type="linear" slope="${f(P.map_mix ?? 0.5)}"/></feComponentTransfer>` +
          `${edges}<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="2" result="g"/><feComposite in="lines" in2="g" operator="arithmetic" k1="0" k2="1" k3="-0.35" k4="0" result="cl"/>` +
          `<feComposite in="cl" in2="base" operator="over"/>`);
        break;
      case "ink":                             // 水墨：亮度加深、墨暈（位移）、微糊
        out.push(`${LUM}<feComponentTransfer>${["R", "G", "B"].map(ch => `<feFunc${ch} type="gamma" exponent="1.6"/>`).join("")}</feComponentTransfer>${table(map).replace("<feComponentTransfer>", '<feComponentTransfer result="t">')}` +
          `<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="t" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/><feGaussianBlur stdDeviation="0.7"/>`);
        break;
      case "silhouette": {                    // 剪影：暗部變成風格的深色、亮部透明（皮影幕布透光）
        const d = toRGB(map[0]);
        out.push(`${LUM}<feComponentTransfer>${["R", "G", "B"].map(ch => `<feFunc${ch} type="discrete" tableValues="0 1"/>`).join("")}</feComponentTransfer>` +
          `<feColorMatrix type="matrix" values="0 0 0 0 ${f(d[0])}  0 0 0 0 ${f(d[1])}  0 0 0 0 ${f(d[2])}  -1 0 0 1 0"/>`);
        break;
      }
      default: break;                         // color：只調色調
    }
    const g = P.grain || 0;
    if (g) out.push(`<feComponentTransfer result="pre"/><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="1" seed="3"/>` +
      `<feColorMatrix type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1" result="N"/><feComposite in="pre" in2="N" operator="arithmetic" k1="0" k2="1" k3="${f(g)}" k4="${f(-g / 2)}"/><feComposite in2="pre" operator="in"/>`);
    const p = P.paper || 0;
    if (p) out.push(`<feComponentTransfer result="pre2"/><feTurbulence type="fractalNoise" baseFrequency="0.012 0.06" numOctaves="3" seed="11"/>` +
      `<feColorMatrix type="matrix" values="${f(0.4 * p)} 0 0 0 ${f(1 - 0.4 * p)}  ${f(0.4 * p)} 0 0 0 ${f(1 - 0.4 * p)}  ${f(0.4 * p)} 0 0 0 ${f(1 - 0.45 * p)}  0 0 0 0 1" result="P"/><feBlend in="pre2" in2="P" mode="multiply"/>` +
      `<feComposite in2="pre2" operator="in"/>`);
    return `<filter id="as-photo" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${out.join("")}</filter>`;
  }

  const AS = {
    init() {
      if (document.getElementById("as-filters")) return;
      const box = document.createElement("div"); box.id = "as-filters";
      box.innerHTML = `<svg xmlns="${NS}" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>${photoFilter(DP())}</defs></svg>`;
      document.body.prepend(box);
    },

    // 照片：管線濾鏡＋邊緣（撕紙、筆刷、圓形…）＋混合＋外框（樣式在 kit.css 的 .as-*）
    photo(target) {
      AS.init();
      const P = DP(), frame = (A.photo || {}).frame || "none";
      els(target).forEach(img => {
        if (img.closest(".as-photo")) return;
        const fig = document.createElement("figure");
        fig.className = `as-photo as-mode--${P.mode} as-edge--${P.edge || "none"} as-blend--${P.blend || "normal"} as-overlay--${P.overlay || "none"} as-frame--${frame}`;
        img.replaceWith(fig); fig.appendChild(img);
        if (P.mode !== "color" || P.grain || P.paper || (P.tone && Object.keys(P.tone).length)) img.style.filter = "url(#as-photo)";
        if (img.alt && (frame === "shot" || frame === "polaroid")) {
          const cap = document.createElement("figcaption"); cap.textContent = img.dataset.src ? `來源：${img.dataset.src}` : img.alt; fig.appendChild(cap);
        }
      });
    },

    // 圖示：線寬、端點、顏色依風格；mode=solid 填實心；mode=rough 用 Rough.js 重畫成手繪
    icon(target) {
      const I = A.icon || {};
      els(target).forEach((svg, n) => {
        svg.classList.add("as-icon", `as-icon--${I.mode || "line"}`);
        if (I.mode === "none") { svg.style.display = "none"; console.warn("[assets] 這個風格不用圖示：", ST.id, svg.id || ""); return; }
        if (I.mode === "rough" && window.SK) return roughen(svg, n, { stroke: I.color || "ink", width: I.stroke || 2 });
        strip(svg);
      });
    },

    // 插畫（別人畫的多色 SVG）：依 detail.illustration.mode 換成風格色
    //   palette 每個顏色換成最接近的風格色｜duotone 依亮度落在兩個風格色之間｜mono 單色＋深淺
    //   outline 只留風格線條（填色變淡）｜rough 用 Rough.js 重畫（手繪類風格）
    illus(target, map = {}) {
      const I = (ST.detail && ST.detail.illustration) || { mode: (A.illustration && A.illustration.recolor === false) ? "none" : "palette" };
      // 色票：深色兩階＋前 N 個彩色＋螢光與表面色（淺色的面才有地方去，不會全被塞進彩色）
      const keep = ["ink", "ink-2", ...["primary", "accent", "accent-2"].slice(0, (A.illustration && A.illustration.max_colors) || 3), "hl", "surface"];
      const pal = keep.map(k => [k, toRGB(k)]);
      els(target).forEach((svg, n) => {
        svg.classList.add("as-illus", `as-illus--${I.mode}`);
        if (I.mode === "rough" && window.SK) return roughen(svg, n, { fillFrom: v => map[v.toLowerCase()] || nearest(toRGB(v), pal, true), fillOpacity: I.fill_opacity ?? 0.6, stroke: "ink", width: 0.8, multi: false });
        svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse").forEach(el => {
          const fill = el.getAttribute("fill") || el.style.fill || (el.closest("[fill]") || svg).getAttribute("fill") || "#000";
          const c = fill === "none" ? null : toRGB(fill), L = c ? lumOf(c) : 1;
          ["fill", "stroke"].forEach(a => { el.removeAttribute(a); el.style[a] = ""; });
          if (!c) { el.style.fill = "none"; return; }
          if (I.mode === "duotone") {
            const [a, b] = I.tones || ["ink", "primary"], p = Math.round(Math.min(1, Math.max(0, L)) * 3) / 3;
            el.style.fill = `color-mix(in oklab, var(--${b}) ${Math.round(p * 100)}%, var(--${a}))`;
          } else if (I.mode === "mono") {
            el.style.fill = `var(--${I.tone || "ink"})`; el.style.fillOpacity = L < 0.35 ? 1 : L < 0.7 ? 0.62 : 0.28;
          } else if (I.mode === "outline") {
            el.style.fill = `var(--${map[fill.toLowerCase()] || nearest(c, pal)})`; el.style.fillOpacity = I.fill_opacity ?? 0;
            el.style.stroke = "var(--ink)"; el.style.strokeWidth = "var(--icon-stroke)"; el.style.strokeLinejoin = "round"; el.setAttribute("vector-effect", "non-scaling-stroke");
          } else {
            el.style.fill = `var(--${map[fill.toLowerCase()] || nearest(c, pal)})`;
          }
        });
      });
    },
    recolor(target, map) { return AS.illus(target, map); },   // 舊名稱

    // 程式畫的物件（.card／.obj）：detail.object.edge = rough 且有手寫圖層時，用 Rough.js 畫外框與填色
    objects(root = document) {
      const O = (ST.detail && ST.detail.object) || {};
      if (O.edge !== "rough" || !window.SK || O.border === "none") return;   // 沒有外框線的風格：CSS 遮罩已經做出不規則邊緣
      root.querySelectorAll(".card:not(.card--ghost):not(.card--plain), .obj").forEach((el, n) => {
        if (el.classList.contains("is-rough")) return;
        const w = el.offsetWidth, h = el.offsetHeight, id = el.id ? `${el.id}-frame` : `as-obj-${n}`;
        const svg = document.createElementNS(NS, "svg");
        svg.setAttribute("class", "as-obj-frame"); svg.setAttribute("width", w + 16); svg.setAttribute("height", h + 16);
        svg.setAttribute("viewBox", `-8 -8 ${w + 16} ${h + 16}`);
        el.prepend(svg); el.classList.add("is-rough");
        if (O.surface === "hatch") {          // 斜線填色改用 Rough.js 的 hachure（和其他手繪圖形同一種筆觸）
          el.style.setProperty("--obj-bg", "var(--surface)");
          SK.rect(svg, 3, 3, w - 6, h - 6, { id: id + "-h", stroke: "none", fill: "primary-wash", hachureGap: 22, fillWeight: 1.2 }).style.opacity = 0.55;
        }
        SK.rect(svg, 3, 3, w - 6, h - 6, { id, stroke: "ink" });
      });
    },

    // 一次處理畫面上所有素材與物件
    apply(root = document) {
      AS.photo(root.querySelectorAll('img[data-as="photo"]'));
      AS.icon(root.querySelectorAll('svg[data-as="icon"]'));
      AS.illus(root.querySelectorAll('svg[data-as="illus"]'));
      AS.objects(root);
    },
  };

  function strip(svg) {
    svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse").forEach(p => {
      ["stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill"].forEach(a => p.removeAttribute(a));
    });
    ["stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill"].forEach(a => svg.removeAttribute(a));
  }

  // 最接近的風格色：亮度差加權（亮暗結構比色相更重要）；fillable=true 時不選 bg（插畫的面不要和底同色消失）
  function nearest(c, pal, fillable) {
    let best = pal[0][0], bd = 1e9;
    for (const [k, p] of pal) {
      if (fillable && k === "bg") continue;
      const dl = (0.2126 * (c[0] - p[0]) + 0.7152 * (c[1] - p[1]) + 0.0722 * (c[2] - p[2])) * 2;
      const d = dl * dl + (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2;
      if (d < bd) { bd = d; best = k; }
    }
    return best;
  }

  // 手寫重畫：圖示與插畫的座標很小（24／48 格），Rough.js 預設抖動會太大，所以依比例縮小
  function roughen(svg, n, o) {
    const id = svg.id || `as-r-${n}`;
    const vb = (svg.getAttribute("viewBox") || "0 0 24 24").split(/[\s,]+/).map(Number), k = vb[2] / 24;
    const shapes = [...svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse")];
    const g = document.createElementNS(NS, "g"); g.setAttribute("id", id + "-r"); g.classList.add("sk");
    const base = ((ST.sketch && ST.sketch.roughness) || 1) * 0.5;
    shapes.forEach((s, i) => {
      const a = s.getAttribute.bind(s), num = x => parseFloat(a(x) || 0);
      const raw = a("fill") || s.style.fill || (s.closest("[fill]") || svg).getAttribute("fill");
      const fillTok = o.fillFrom && raw && raw !== "none" ? o.fillFrom(raw) : null;
      const opt = { id: `${id}-${i}`, stroke: o.stroke, width: (o.width || 2) * k, parent: g, fill: fillTok,
        fillStyle: ST.sketch && ST.sketch.fill_style, hachureGap: 2.6 * k, fillWeight: 0.7 * k,
        rough: { maxRandomnessOffset: 0.6 * k, roughness: base, bowing: 0.6, ...(o.multi === false ? { disableMultiStroke: true } : {}) } };
      const t = s.tagName.toLowerCase();
      let node;
      if (t === "path") node = SK.path(svg, a("d"), opt);
      else if (t === "circle") node = SK.circle(svg, num("cx"), num("cy"), num("r") * 2, opt);
      else if (t === "ellipse") node = SK.ellipse(svg, num("cx"), num("cy"), num("rx") * 2, num("ry") * 2, opt);
      else if (t === "rect") node = SK.rect(svg, num("x"), num("y"), num("width"), num("height"), opt);
      else if (t === "line") node = SK.line(svg, num("x1"), num("y1"), num("x2"), num("y2"), opt);
      else node = SK.polyline(svg, a("points").trim().split(/[\s,]+/).map(Number).reduce((r, v, j, arr) => (j % 2 ? r : [...r, [v, arr[j + 1]]]), []), opt);
      if (fillTok && node) node.querySelectorAll(".sk-hatch, .sk-solid").forEach(p => (p.style.opacity = o.fillOpacity));
      s.remove();
    });
    svg.querySelectorAll("g:not(.sk)").forEach(x => { if (!x.querySelector(".sk")) x.remove(); });
    svg.appendChild(g);
    svg.setAttribute("fill", "none");
  }
  function els(t) { return typeof t === "string" ? [...document.querySelectorAll(t)] : t instanceof Element ? [t] : [...t]; }

  window.AS = AS;
})();
