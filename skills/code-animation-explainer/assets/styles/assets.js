// 素材對齊（assets.js）：照片、圖示、插畫放進畫面前，先依風格卡的 assets 欄處理，才不會「畫面是水墨、照片是手機原圖」。
// 載入順序：tokens.js → rough.js → sketch.js → assets.js。
//
// 用法（標記後一次處理）：
//   <img data-as="photo" src="leaf.jpg" alt="葉片">
//   <svg data-as="icon" id="s2-ic-leaf" viewBox="0 0 24 24">…Lucide 圖示的 path…</svg>
//   <svg data-as="illus" viewBox="…">…unDraw 插畫…</svg>
//   <script>AS.apply();</script>          // 或 AS.photo(el)／AS.icon(el)／AS.recolor(el) 單獨處理
// 手寫類風格（icon.mode = "rough"）的圖示會用 Rough.js 重畫，可以用 SK.draw(tl, "#s2-ic-leaf", AT("葉片")) 一筆一筆畫出來。
// 所有處理都是固定參數、不用亂數，逐格渲染每次結果一樣。
(function () {
  const ST = window.STYLE || {}, A = ST.assets || {}, NS = "http://www.w3.org/2000/svg";
  const TOKENS = ["ink", "ink-2", "primary", "accent", "accent-2", "hl", "bg", "surface"];
  const ctx = document.createElement("canvas").getContext("2d");

  function cssVar(k) { return getComputedStyle(document.documentElement).getPropertyValue("--" + k).trim(); }
  function toRGB(c) {                         // 任何 CSS 顏色（含 var(--x)、token 名稱）→ [r,g,b] 0–1
    if (TOKENS.includes(c)) c = (ST.color && ST.color[c]) || cssVar(c);
    else if (c && c.startsWith("var(--")) c = cssVar(c.slice(6, -1));
    ctx.fillStyle = "#000"; ctx.fillStyle = c || "#000";
    const v = ctx.fillStyle;                  // 瀏覽器正規化成 #rrggbb 或 rgba()
    if (v[0] === "#") return [1, 3, 5].map(i => parseInt(v.slice(i, i + 2), 16) / 255);
    return v.match(/[\d.]+/g).slice(0, 3).map(x => +x / 255);
  }
  const f = n => n.toFixed(4);

  // ── 照片濾鏡：顏色來自風格 tokens，注入一次到文件裡 ──
  function filters() {
    const P = A.photo || {}, [d, l] = (P.tones || ["ink", "bg"]).map(toRGB);
    const ink = toRGB("ink");
    const lum = '<feColorMatrix type="matrix" values="0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0 0 0 1 0"/>';
    const duo = (a, b) => `<feComponentTransfer><feFuncR type="table" tableValues="${f(a[0])} ${f(b[0])}"/><feFuncG type="table" tableValues="${f(a[1])} ${f(b[1])}"/><feFuncB type="table" tableValues="${f(a[2])} ${f(b[2])}"/></feComponentTransfer>`;
    // 線稿：亮度 → 邊緣偵測 → 只留線，線的顏色＝ink（深底風格的 ink 是淺色，所以粉筆、藍圖會是淺色線）
    const edges = `<feGaussianBlur stdDeviation="2.4"/>${lum}<feConvolveMatrix order="3" kernelMatrix="-1 -1 -1 -1 8 -1 -1 -1 -1" preserveAlpha="true"/>` +
      `<feColorMatrix type="matrix" values="0 0 0 0 ${f(ink[0])}  0 0 0 0 ${f(ink[1])}  0 0 0 0 ${f(ink[2])}  9 9 9 0 -0.55" result="e"/>`;
    return `<svg xmlns="${NS}" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<filter id="as-duotone" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${lum}${duo(d, l)}</filter>
<filter id="as-halftone" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${lum}<feComponentTransfer><feFuncR type="linear" slope="1.4" intercept="-0.2"/><feFuncG type="linear" slope="1.4" intercept="-0.2"/><feFuncB type="linear" slope="1.4" intercept="-0.2"/></feComponentTransfer>${duo(d, l)}</filter>
<filter id="as-ink" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${lum}<feComponentTransfer><feFuncR type="gamma" exponent="1.6"/><feFuncG type="gamma" exponent="1.6"/><feFuncB type="gamma" exponent="1.6"/></feComponentTransfer>${duo(d, l).replace("<feComponentTransfer>", '<feComponentTransfer result="t">')}<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="t" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G"/><feGaussianBlur stdDeviation="0.6"/></filter>
<filter id="as-silhouette" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${lum}<feComponentTransfer><feFuncR type="discrete" tableValues="0 1"/><feFuncG type="discrete" tableValues="0 1"/><feFuncB type="discrete" tableValues="0 1"/></feComponentTransfer><feColorMatrix type="matrix" values="0 0 0 0 ${f(d[0])}  0 0 0 0 ${f(d[1])}  0 0 0 0 ${f(d[2])}  -1 0 0 1 0"/></filter>
<filter id="as-lines" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${edges}</filter>
<filter id="as-chalk" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">${edges}<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="2" result="g"/><feComposite in="e" in2="g" operator="arithmetic" k1="0" k2="1" k3="-0.4" k4="0"/></filter>
<filter id="as-soft" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0.6"/><feComponentTransfer><feFuncR type="linear" slope="0.85" intercept="0.12"/><feFuncG type="linear" slope="0.85" intercept="0.1"/><feFuncB type="linear" slope="0.8" intercept="0.08"/></feComponentTransfer></filter>
</defs></svg>`;
  }
  const FILTER = { duotone: "as-duotone", halftone: "as-halftone", ink: "as-ink", silhouette: "as-silhouette", chalk: "as-chalk", blueprint: "as-lines", soft: "as-soft" };

  const AS = {
    init() {
      if (document.getElementById("as-filters")) return;
      const box = document.createElement("div"); box.id = "as-filters"; box.innerHTML = filters();
      document.body.prepend(box);
    },

    // 照片：套風格濾鏡＋外框（外框樣式在 kit.css 的 .as-photo--* / .as-frame--*）
    photo(target) {
      AS.init();
      const P = A.photo || {};
      els(target).forEach(img => {
        if (img.closest(".as-photo")) return;
        if (P.allowed === false) console.warn("[assets] 這個風格不用照片：", ST.id, img.src, "→", P.instead || "改用圖示或程式繪製");
        const fig = document.createElement("figure");
        fig.className = `as-photo as-photo--${P.treatment || "none"} as-frame--${P.frame || "none"}`;
        img.replaceWith(fig); fig.appendChild(img);
        const id = FILTER[P.treatment];
        if (id) img.style.filter = `url(#${id})`;
        if (img.alt && (P.frame === "shot" || P.frame === "polaroid")) {
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
        if (I.mode === "rough" && window.SK) return roughen(svg, n, I);
        svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse").forEach(p => {
          ["stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill"].forEach(a => p.removeAttribute(a));
        });
        ["stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "fill"].forEach(a => svg.removeAttribute(a));
      });
    },

    // 插畫：每個顏色換成最接近的風格色（依亮度與色相距離），顏色數量上限依 illustration.max_colors
    recolor(target, map = {}) {
      const keep = TOKENS.slice(0, Math.max(2, (A.illustration && A.illustration.max_colors) || 8) + 2);
      const pal = keep.map(k => [k, toRGB(k)]);
      els(target).forEach(svg => {
        svg.classList.add("as-illus");
        svg.querySelectorAll("[fill],[stroke],[style]").forEach(el => {
          ["fill", "stroke"].forEach(prop => {
            const v = el.getAttribute(prop) || el.style[prop];
            if (!v || v === "none" || v.startsWith("url(") || v === "currentColor") return;
            const tok = map[v.toLowerCase()] || nearest(toRGB(v), pal);
            el.removeAttribute(prop); el.style[prop] = `var(--${tok})`;
          });
        });
      });
    },

    // 一次處理畫面上所有 data-as 標記
    apply(root = document) {
      AS.photo(root.querySelectorAll('img[data-as="photo"]'));
      AS.icon(root.querySelectorAll('svg[data-as="icon"]'));
      AS.recolor(root.querySelectorAll('svg[data-as="illus"]'));
    },
  };

  function nearest(c, pal) {
    let best = pal[0][0], bd = 1e9;
    for (const [k, p] of pal) {
      const dl = (0.2126 * (c[0] - p[0]) + 0.7152 * (c[1] - p[1]) + 0.0722 * (c[2] - p[2])) * 2;
      const d = dl * dl + (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2;
      if (d < bd) { bd = d; best = k; }
    }
    return best;
  }

  // 手寫重畫：24 格的圖示座標很小，Rough.js 預設抖動（2 單位）會太大，所以縮小抖動幅度
  function roughen(svg, n, I) {
    const id = svg.id || `as-icon-${n}`;
    const shapes = [...svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse")];
    const g = document.createElementNS(NS, "g"); g.setAttribute("id", id + "-r"); g.classList.add("sk");
    const o = (k) => ({ id: `${id}-${k}`, stroke: I.color || "ink", width: I.stroke || 2, parent: g, rough: { maxRandomnessOffset: 0.6, roughness: ((ST.sketch && ST.sketch.roughness) || 1) * 0.5, bowing: 0.6 } });
    shapes.forEach((s, k) => {
      const a = s.getAttribute.bind(s), num = x => parseFloat(a(x) || 0);
      const t = s.tagName.toLowerCase();
      if (t === "path") SK.path(svg, a("d"), o(k));
      else if (t === "circle") SK.circle(svg, num("cx"), num("cy"), num("r") * 2, o(k));
      else if (t === "ellipse") SK.ellipse(svg, num("cx"), num("cy"), num("rx") * 2, num("ry") * 2, o(k));
      else if (t === "rect") SK.rect(svg, num("x"), num("y"), num("width"), num("height"), o(k));
      else if (t === "line") SK.line(svg, num("x1"), num("y1"), num("x2"), num("y2"), o(k));
      else SK.polyline(svg, a("points").trim().split(/[\s,]+/).map(Number).reduce((r, v, i, arr) => (i % 2 ? r : [...r, [v, arr[i + 1]]]), []), o(k));
      s.remove();
    });
    svg.appendChild(g);
    svg.setAttribute("fill", "none");
  }
  function els(t) { return typeof t === "string" ? [...document.querySelectorAll(t)] : t instanceof Element ? [t] : [...t]; }

  window.AS = AS;
})();
