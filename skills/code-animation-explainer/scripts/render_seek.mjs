// 逐格渲染（單一 HTML＋GSAP 路線）：用 Playwright 開頁面，一格一格 seek、截圖，直接串給 ffmpeg 編成 MP4。
// 畫面只由時間 t 決定，所以每次渲染結果都一樣，也不會因為電腦慢而掉格。
//
// 頁面要提供：
//   window.__duration   影片總長（秒）
//   window.__seek(t)    把畫面設成第 t 秒（例：t => { tl.seek(t); 更新字幕; }——用大括號、不要回傳 timeline）
//   window.__ready      true 之後才開始截圖（字型、圖片、Rough.js 都畫好）
//
// 用法：
//   node render_seek.mjs compositions/demo.html out/video.mp4 [--fps 30] [--size 1920x1080] [--from 0] [--to 秒] [--audio mix.wav] [--crf 18]
//   node render_seek.mjs compositions/demo.html out/stills/ --at 3,12.5,40      # 只截指定時間點（檢查用），輸出 PNG
//   node render_seek.mjs compositions/demo.html out/stills/ --at 3,12.5 --overlap   # 截圖＋檢查重疊（文字疊文字、物件壓字、線條穿字、字出畫面）
//   node render_seek.mjs compositions/demo.html - --scan 0.25                   # 不截圖，整支片每 0.25 秒檢查一次重疊
//   刻意的重疊（便利貼貼在視窗上、標籤疊在圖上）在元素上加 data-overlap-ok 就不報；
//   刻意蓋住整個畫面的圖層（片尾卡、全螢幕插入畫面）加 data-cover：它底下被蓋住的字不報，它自己裡面的東西照樣檢查
// 需求：ffmpeg、playwright（npm i playwright；雲端環境可設 PLAYWRIGHT_PATH 指向已安裝的模組）
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
let pw;
for (const m of [process.env.PLAYWRIGHT_PATH, 'playwright', 'playwright-core'].filter(Boolean)) {
  try { pw = require(m); break; } catch { /* 試下一個 */ }
}
if (!pw) { console.error('找不到 playwright：在 scripts/ 資料夾執行 npm i playwright && npx playwright install chromium（或設定 PLAYWRIGHT_PATH）；不確定缺什麼就跑 python doctor.py'); process.exit(1); }

const args = process.argv.slice(2);
const [page_, out] = args;
if (!page_ || !out) { console.error('用法：node render_seek.mjs page.html out.mp4 [--fps 30] [--size 1920x1080] [--audio mix.wav]'); process.exit(1); }
const opt = (k, d) => { const i = args.indexOf('--' + k); return i > 0 ? args[i + 1] : d; };
const fps = +opt('fps', 30), [W, H] = opt('size', '1920x1080').split('x').map(Number);
const at = opt('at'), scan = opt('scan'), overlap = args.includes('--overlap') || !!scan;

const browser = await pw.chromium.launch({ args: ['--hide-scrollbars', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('頁面錯誤：', e.message));
await page.goto('file://' + path.resolve(page_));
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.__duration);

// ── 重疊檢查：在頁面裡量每個看得見的文字框、物件框、線條，回報不該疊在一起的組合 ──
function findOverlaps(edgeCheck) {
  const W = innerWidth, H = innerHeight, out = [];
  const OBJ = '.card,.obj,.note,.chip,.el-label,.ppt,.win,.term,.cap-mock,.step,.caption-bar,img,figure,svg.as-icon,svg.as-illus';
  const alpha = el => { let a = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; a *= +cs.opacity; } return a; };
  const ok = el => !!el.closest('[data-overlap-ok]');
  const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  const area = r => (r.right - r.left) * (r.bottom - r.top);
  const onScreen = r => r.right > 0 && r.bottom > 0 && r.left < W && r.top < H;
  const name = el => (el.id ? '#' + el.id + ' ' : '') + '「' + (el.textContent || el.getAttribute('alt') || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 14) + '」';
  // 文字框：每個直接含文字的元素，用文字本身的範圍（不是整個盒子）
  const texts = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Map();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement; if (!el || el.closest('script,style,#as-filters,[data-text]') || alpha(el) < 0.15) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (r.width < 2 || r.height < 2 || !onScreen(r)) continue;
      const key = el.closest('text') || el;
      const b = seen.get(key) || { el: key, left: 1e9, top: 1e9, right: -1e9, bottom: -1e9, rects: [] };
      b.rects.push({ left: r.left, top: r.top, right: r.right, bottom: r.bottom });
      b.left = Math.min(b.left, r.left); b.top = Math.min(b.top, r.top); b.right = Math.max(b.right, r.right); b.bottom = Math.max(b.bottom, r.bottom);
      seen.set(key, b);
    }
  }
  // SK.write() 寫出來的字是路徑不是文字：用每個字的外框當文字框（只算已經開始寫的字）
  document.querySelectorAll('[data-text]').forEach(g => {
    if (alpha(g) < 0.15 || ok(g)) return;
    const rects = [...g.querySelectorAll('.sk-char, .sk-text')].filter(c => [...c.querySelectorAll('.sk-wstroke, tspan')].some(p => p.tagName === 'tspan' ? +getComputedStyle(p).opacity > 0.1 : +getComputedStyle(p).getPropertyValue('--draw') > 0.05))
      .map(c => { const r = c.getBoundingClientRect(); return { left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }).filter(r => r.right - r.left > 2 && onScreen(r));
    if (!rects.length) return;
    seen.set(g, { el: g, rects, left: Math.min(...rects.map(r => r.left)), top: Math.min(...rects.map(r => r.top)), right: Math.max(...rects.map(r => r.right)), bottom: Math.max(...rects.map(r => r.bottom)) });
  });
  texts.push(...[...seen.values()].filter(b => b.bottom - b.top >= 14));   // 小於 14px 的字（拉遠的全圖）本來就讀不到，不檢查
  const topAt = (x, y) => document.elementFromPoint(Math.min(W - 1, Math.max(0, x)), Math.min(H - 1, Math.max(0, y)));
  // 看得見的字：中心或四角任一點，最上層就是這段字（被整張卡蓋住的不算）
  texts.forEach(tx => {
    const cx = (tx.left + tx.right) / 2, cy = (tx.top + tx.bottom) / 2, dx = (tx.right - tx.left) * 0.3, dy = (tx.bottom - tx.top) * 0.25;
    tx.vis = [[cx, cy], [cx - dx, cy - dy], [cx + dx, cy - dy], [cx - dx, cy + dy], [cx + dx, cy + dy]].some(([x, y]) => { const e = topAt(x, y); return e && (e === tx.el || tx.el.contains(e)); });
  });
  const vis = texts.filter(tx => tx.vis);
  const objs = [...document.querySelectorAll(OBJ)].filter(e => alpha(e) > 0.15).map(e => { const r = e.getBoundingClientRect(); return { el: e, left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }).filter(o => area(o) > 4 && onScreen(o));
  const related = (a, b) => a.contains(b) || b.contains(a);
  // A. 文字疊文字
  for (let i = 0; i < vis.length; i++) for (let j = i + 1; j < vis.length; j++) {
    const a = vis[i], b = vis[j];
    if (related(a.el, b.el) || (ok(a.el) && ok(b.el))) continue;
    // 逐行比，換行的字不會被當成一整塊；字框上下各內縮 18%（字型的上伸／下伸空間比行高大，相鄰兩行的框本來就會碰到）
    const core = r => { const m = (r.bottom - r.top) * 0.18; return { left: r.left, right: r.right, top: r.top + m, bottom: r.bottom - m }; };
    let v = 0; for (const x of a.rects) for (const y of b.rects) v += inter(core(x), core(y));
    const ar = r => r.rects.reduce((s, x) => s + area(x), 0);
    if (v > 0.12 * Math.min(ar(a), ar(b))) out.push(`文字疊文字：${name(a.el)} ✕ ${name(b.el)}`);
  }
  // B. 物件壓住文字（文字不在這個物件裡）
  for (const tx of texts) for (const o of objs) {
    if (related(tx.el, o.el) || ok(tx.el) || ok(o.el)) continue;
    const cv = o.el.closest('[data-cover]'), ct = tx.el.closest('[data-cover]');
    if (cv !== ct) continue;                                         // 一個在蓋版圖層上、一個在底下：本來就是蓋住
    const box = 'figure,.card,.obj,.win,.term,.note';
    if (o.el.closest(box) && o.el.closest(box) === tx.el.closest(box)) continue;   // 同一張卡／同一張圖裡的圖說
    if (inter(tx, o) <= 0.2 * area(tx)) continue;
    const top = topAt((Math.max(tx.left, o.left) + Math.min(tx.right, o.right)) / 2, (Math.max(tx.top, o.top) + Math.min(tx.bottom, o.bottom)) / 2);
    if (top && (o.el === top || o.el.contains(top)) && !tx.el.contains(top)) out.push(`物件蓋住文字：${name(o.el)} ✕ ${name(tx.el)}`);
    else if (top && (tx.el === top || tx.el.contains(top))) out.push(`文字壓在別的物件上：${name(tx.el)} ✕ ${name(o.el)}`);
  }
  // C. 線條穿過文字：沿著看得見的線取樣，落在文字框（內縮 3px）裡的點夠多就報
  const strokes = [...document.querySelectorAll('svg path, svg line, svg polyline, svg ellipse, svg circle')].filter(p => {
    if (!p.getTotalLength || !onScreen(p.getBoundingClientRect()) || p.closest('#as-filters,svg.as-icon,svg.as-illus,defs,mask,clipPath')) return false;
    if (p.classList.contains('sk-hatch') || p.classList.contains('sk-wstroke')) return false;               // 斜線填色是底，不算線條
    const cs = getComputedStyle(p); if (cs.stroke === 'none') return false;
    const d = cs.getPropertyValue('--draw'); if (d !== '' && +d < 0.5) return false;
    return alpha(p) > 0.15 && !ok(p);
  });
  for (const p of strokes) {
    const L = p.getTotalLength(), m = p.getScreenCTM(); if (!m || L < 8) continue;
    const pr = p.getBoundingClientRect(), near = vis.filter(tx => inter(tx, pr) > 0); if (!near.length) continue;
    const step = Math.max(8, L / 400), pts = []; for (let s = 0; s <= L; s += step) { const q = p.getPointAtLength(s); pts.push([m.a * q.x + m.c * q.y + m.e, m.b * q.x + m.d * q.y + m.f]); }
    for (const tx of near) {
      if (p.closest('svg').contains(tx.el) && tx.el.closest('.sk')) continue;
      const hits = pts.filter(([x, y]) => x > tx.left + 3 && x < tx.right - 3 && y > tx.top + 3 && y < tx.bottom - 3);
      const svgEl = p.ownerSVGElement || p.closest('svg');
      // 線在這一點看得見嗎：從最上層往下找到線所在的 svg 之前，不能有不透明的卡片／底色擋住
      const COVER = '.card,.obj,.note,.win,.term,.ppt,.caption-bar,.cap-mock,.chip,.el-label,figure,img';
      const opaque = e => e.matches(COVER) || (() => { const m = getComputedStyle(e).backgroundColor.match(/[\d.]+/g); return m && (m.length < 4 || +m[3] > 0.3) && getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)'; })();
      const seenHits = hits.filter(([x, y]) => {
        for (const e of document.elementsFromPoint(Math.min(W - 1, Math.max(0, x)), Math.min(H - 1, Math.max(0, y)))) {
          if (e === svgEl || svgEl.contains(e)) return true;
          if (e === document.body || e === document.documentElement || e.contains(svgEl)) continue;
          if (opaque(e)) return false;
        }
        return false;
      });
      if (seenHits.length >= 3) out.push(`線條穿過文字：${p.closest('[id]') ? '#' + p.closest('[id]').id : '(線)'} ✕ ${name(tx.el)}`);
    }
  }
  // E. 填色圖形（手繪方框、圓、泡泡…）的邊緣切進文字：字沒有被整個包在圖形裡，卻有一部分壓在圖形上
  const shapes = [...document.querySelectorAll('svg .sk')].filter(g => !g.parentElement.closest('.sk') && g.querySelector('.sk-hatch, .sk-solid') && !ok(g) && alpha(g) > 0.15)
    .filter(g => [...g.querySelectorAll('.sk-line, .sk-hatch')].some(p => { const d = getComputedStyle(p).getPropertyValue('--draw'); return d === '' || +d > 0.5; }))
    .map(g => { const r = g.getBoundingClientRect(); return { el: g, left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }).filter(s => onScreen(s) && area(s) > 400);
  for (const s of shapes) for (const tx of vis) {
    if (s.el.closest('svg').contains(tx.el) || s.el.closest('[data-cover]') !== tx.el.closest('[data-cover]')) continue;
    const v = inter(tx, s), ta = area(tx);
    const dx = Math.min(tx.right, s.right) - Math.max(tx.left, s.left), dy = Math.min(tx.bottom, s.bottom) - Math.max(tx.top, s.top);
    if (v > 0 && v < 0.9 * ta && dx > 6 && dy > 6) out.push(`圖形邊緣壓到文字：#${s.el.id} ✕ ${name(tx.el)}`);
  }
  // D. 文字被畫面邊緣切到（只在定格檢查時看；鏡頭移動中本來就會切）
  if (edgeCheck) for (const tx of vis) {
    const inside = inter(tx, { left: 0, top: 0, right: W, bottom: H });
    if (inside < 0.95 * area(tx) && !ok(tx.el)) out.push(`文字超出畫面：${name(tx.el)}`);
  }
  return [...new Set(out)];
}
let issues = 0;
async function check(t, edge) {
  const r = await page.evaluate(findOverlaps, edge);
  if (r.length) { issues += r.length; console.log(`✗ ${t.toFixed(2)}s`); r.forEach(x => console.log('   ' + x)); }
}

if (at) {                                             // 只截指定時間點
  if (out !== '-') fs.mkdirSync(out, { recursive: true });
  for (const t of at.split(',').map(Number)) {
    await page.evaluate(t => { window.__seek(t); }, t);
    if (out !== '-') await page.screenshot({ path: path.join(out, `t${t.toFixed(1).padStart(6, '0')}.png`) });
    if (overlap) await check(t, true);
  }
  console.log(`已處理 ${at.split(',').length} 個時間點${out !== '-' ? ' → ' + out : ''}${overlap ? `；重疊問題 ${issues} 個` : ''}`);
  await browser.close(); process.exit(overlap && issues ? 1 : 0);
}
if (scan) {                                           // 整支片掃描重疊（不截圖）；只回報持續 ≥0.6 秒的（鏡頭移動中一閃而過的不算）
  const step = +scan, need = Math.max(2, Math.ceil(0.6 / step)), runs = new Map(), found = [];
  for (let t = 0; t <= duration + 1e-6; t += step) {
    await page.evaluate(t => { window.__seek(t); }, t);
    const now = new Set(await page.evaluate(findOverlaps, false));
    for (const k of [...runs.keys()]) if (!now.has(k)) { const r = runs.get(k); if (r.n >= need) found.push([r.t0, t - step, k]); runs.delete(k); }
    for (const k of now) { const r = runs.get(k) || { t0: t, n: 0 }; r.n++; runs.set(k, r); }
  }
  for (const [k, r] of runs) if (r.n >= need) found.push([r.t0, duration, k]);
  found.sort((a, b) => a[0] - b[0]).forEach(([a, b, k]) => console.log(`✗ ${a.toFixed(2)}–${b.toFixed(2)}s  ${k}`));
  issues = found.length;
  console.log(`掃描完成（每 ${scan} 秒）；重疊問題 ${issues} 個`);
  await browser.close(); process.exit(issues ? 1 : 0);
}

const t0 = +opt('from', 0), t1 = Math.min(+opt('to', duration), duration);
const frames = Math.round((t1 - t0) * fps);
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
const audio = opt('audio');
const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  ...(audio ? ['-ss', String(t0), '-i', audio, '-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
  '-c:v', 'libx264', '-preset', 'medium', '-crf', opt('crf', '18'), '-pix_fmt', 'yuv420p', '-r', String(fps), '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });
const started = Date.now();
// 單格逾時：頁面卡住時直接報錯退出，而不是無聲地掛好幾小時
const FRAME_TIMEOUT = +opt('frame-timeout', 30) * 1000;
const guard = (p, what, t) => Promise.race([p, new Promise((_, rej) => setTimeout(() =>
  rej(new Error(`第 ${t.toFixed(3)} 秒的${what}超過 ${FRAME_TIMEOUT / 1000} 秒沒有回應（檢查 __seek 是否有無窮迴圈或回傳大型物件）`)), FRAME_TIMEOUT))]);
for (let f = 0; f < frames; f++) {
  const t = t0 + f / fps;
  // 用大括號丟掉 __seek 的回傳值：若頁面寫成 t => tl.seek(t)，會回傳整個 GSAP timeline，
  // Playwright 序列化這個循環參照的大物件會卡死（曾整夜 0 格輸出）
  await guard(page.evaluate(t => { window.__seek(t); }, t), 'seek', t);
  const buf = await guard(page.screenshot({ type: 'jpeg', quality: 92 }), '截圖', t);
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % (fps * 5) === 0) process.stdout.write(`\r${(f / fps).toFixed(0)}／${(t1 - t0).toFixed(0)} 秒`);
}
ff.stdin.end();
await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg 失敗：' + c)))));
await browser.close();
console.log(`\n完成 ${frames} 格（${((Date.now() - started) / 1000).toFixed(0)} 秒）→ ${out}`);
