// 逐格渲染（單一 HTML＋GSAP 路線）：用 Playwright 開頁面，一格一格 seek、截圖，直接串給 ffmpeg 編成 MP4。
// 畫面只由時間 t 決定，所以每次渲染結果都一樣，也不會因為電腦慢而掉格。
//
// 頁面要提供：
//   window.__duration   影片總長（秒）
//   window.__seek(t)    把畫面設成第 t 秒（例：tl.seek(t) 再更新字幕）
//   window.__ready      true 之後才開始截圖（字型、圖片、Rough.js 都畫好）
//
// 用法：
//   node render_seek.mjs compositions/demo.html out/video.mp4 [--fps 30] [--size 1920x1080] [--from 0] [--to 秒] [--audio mix.wav] [--crf 18]
//   node render_seek.mjs compositions/demo.html out/stills/ --at 3,12.5,40      # 只截指定時間點（檢查用），輸出 PNG
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
if (!pw) { console.error('找不到 playwright：npm i playwright（或設定 PLAYWRIGHT_PATH）'); process.exit(1); }

const args = process.argv.slice(2);
const [page_, out] = args;
if (!page_ || !out) { console.error('用法：node render_seek.mjs page.html out.mp4 [--fps 30] [--size 1920x1080] [--audio mix.wav]'); process.exit(1); }
const opt = (k, d) => { const i = args.indexOf('--' + k); return i > 0 ? args[i + 1] : d; };
const fps = +opt('fps', 30), [W, H] = opt('size', '1920x1080').split('x').map(Number);
const at = opt('at');

const browser = await pw.chromium.launch({ args: ['--hide-scrollbars', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('頁面錯誤：', e.message));
await page.goto('file://' + path.resolve(page_));
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.__duration);

if (at) {                                             // 只截指定時間點
  fs.mkdirSync(out, { recursive: true });
  for (const t of at.split(',').map(Number)) {
    await page.evaluate(t => window.__seek(t), t);
    await page.screenshot({ path: path.join(out, `t${t.toFixed(1).padStart(6, '0')}.png`) });
  }
  console.log(`已截 ${at.split(',').length} 張 → ${out}`);
  await browser.close(); process.exit(0);
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
for (let f = 0; f < frames; f++) {
  await page.evaluate(t => window.__seek(t), t0 + f / fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % (fps * 5) === 0) process.stdout.write(`\r${(f / fps).toFixed(0)}／${(t1 - t0).toFixed(0)} 秒`);
}
ff.stdin.end();
await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg 失敗：' + c)))));
await browser.close();
console.log(`\n完成 ${frames} 格（${((Date.now() - started) / 1000).toFixed(0)} 秒）→ ${out}`);
