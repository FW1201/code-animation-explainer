// 批次擷取網頁截圖（Puppeteer + 本機 Chrome），隱藏 cookie 橫幅但不代為同意任何條款。
// 安裝：npm i puppeteer-core
// 用法：node shoot.mjs shots.json out/          shots.json = [["gsap","https://gsap.com/"], ...]
// 環境變數 CHROME_PATH 可指定瀏覽器路徑。遇到機器人驗證頁請換來源，不要嘗試繞過。
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

const [list, outDir = 'shots'] = process.argv.slice(2);
if (!list) { console.error('用法：node shoot.mjs shots.json out/'); process.exit(1); }
const pairs = JSON.parse(fs.readFileSync(list, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });
const guess = {
  darwin: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  win32: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  linux: '/usr/bin/google-chrome',
}[process.platform];
const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH || guess, headless: true, args: ['--hide-scrollbars'] });
const log = [];
for (const [name, url] of pairs) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1.2 });
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 }).catch(() => {});
    await new Promise((r) => setTimeout(r, 2500));
    await page.evaluate(() => {
      const rx = /cookie|consent|gdpr|onetrust|cc-window|osano/i;
      document.querySelectorAll('body *').forEach((el) => {
        const s = getComputedStyle(el);
        if ((s.position === 'fixed' || s.position === 'sticky') && el.innerText.length < 1500 &&
            (rx.test(el.id) || rx.test(String(el.className)) || rx.test(el.innerText.slice(0, 300)))) el.remove();
      });
    });
    const file = path.join(outDir, `${name}.png`);
    await page.screenshot({ path: file });
    log.push({ name, url, file, captured: new Date().toISOString().slice(0, 10) });
    console.log('ok', name);
  } catch (e) {
    console.log('fail', name, e.message);
  }
  await page.close();
}
await browser.close();
fs.writeFileSync(path.join(outDir, 'sources.json'), JSON.stringify(log, null, 2));
console.log('出處紀錄：', path.join(outDir, 'sources.json'), '（片尾與說明欄請用它）');
