# 動畫引擎選擇

先依 `animation-styles.md` 選好流派與輸出方式，再從下表挑技術。多數漂亮的成品是混搭：HTML/CSS 做介面動作、SVG 做圖解、Canvas 做粒子、Three.js 做 3D 背景，外面用一條時間軸統一控制。

| 引擎 | 寫法 | 適合 | 需求 |
|---|---|---|---|
| **HyperFrames** | HTML＋CSS＋GSAP，`data-start/duration` 宣告片段，子合成拆幕 | 解說影片、需要真實截圖與字幕、要 CLI 檢查與渲染 | Node 22+、ffmpeg；`npx hyperframes init` |
| **Remotion** | React 元件，`useCurrentFrame()` | 已熟 React、需要資料驅動 | Node、ffmpeg |
| **Manim** | Python，數學物件動畫 | 公式推導、幾何、圖形 | Python、LaTeX（選用） |
| **D3.js** | 資料綁定＋transition 在狀態間插值 | 資料敘事、圖表轉換 | 瀏覽器；影片化時由時間軸驅動 transition 進度 |
| **p5.js／Canvas** | `setup()`＋逐幀 `draw()` | 粒子、生成藝術、簡易物理 | 瀏覽器；影片化需固定種子與步長，改成依 t 計算 |
| **Three.js** | 場景、相機、AnimationMixer | 3D 空間、分子、天文 | 瀏覽器（WebGL）；時間由時間軸提供 |
| **Lottie** | 播放 AE 匯出的 JSON 向量動畫 | 現成角色、圖示動畫 | lottie-web；以 `goToAndStop(frame)` 對時 |
| **單一 HTML＋GSAP** | 一個檔案、主時間軸 paused，頁面提供 `__seek`／`__duration`／`__ready` | 單一連續畫布（鏡頭在大畫布上移動）、不想裝 HyperFrames | 瀏覽器；用 `scripts/render_seek.mjs` 逐格渲染成 MP4 |

## 共通原則（任何引擎）
- **風格 tokens**：每一幕先載入 `style/tokens.css`、`style/kit.css`、`style/tokens.js`（`style_apply.py` 產生）。HyperFrames 子合成把這三個檔放在 `<template>` 內引用；Remotion 在根元件 import CSS、用 `window.STYLE`／`M` 或改 import `tokens.json`；Manim 從 `tokens.json` 讀 hex。
- **時間軸驅動**：畫面只由時間 t 決定，可任意 seek。GSAP 用 `gsap.timeline({ paused: true })`；Remotion 用 frame；Manim 用 `self.play` 時長。
- **決定性**：禁止 `Math.random()`（要亂數就用固定種子）、`Date.now()`、網路請求、無限 `repeat: -1`。
- **一幕一檔**：每幕獨立的樣式／標記／腳本，用建置腳本組裝；主合成只負責排順序、轉場、字幕與背景音樂。
- **ID 前綴**：每幕的 id 加上幕號前綴（`#s3-title`），避免多幕同時載入時選擇器互相干擾。
- **SVG＋GSAP 陷阱**：
  - GSAP 要動的 SVG `<g>` 不可同時帶 `transform` 屬性（會被 GSAP 覆蓋而跑位）；外層包一層只負責定位的 `<g>`，內層交給 GSAP。
  - SVG 內的縮放／旋轉軸心用 `svgOrigin: "x y"`（SVG 座標），不要用 px 的 `transformOrigin`。
  - 關節動作（人物手臂、頭）用 `attr: { transform: "rotate(角度 軸x 軸y)" }` 補間，軸心寫在 `data-p`，可任意 seek。
- **可重用元件**：同一種人物、圖示會在多幕出現時，寫成元件函式（例：Python 產生 SVG 字串），markup 用 `{{ 元件(...) }}` 在建置時展開；id 用「§」佔位、建置時換成各幕前綴。
- **字型**：用 `@font-face` 載入本機字型檔；中文字型很大，建議依實際用字做子集（fonttools `pyftsubset` 轉 woff2），常可從 12MB 降到 200KB。

## HyperFrames 要點
- 主合成 `index.html`：每幕一個 `data-composition-src="compositions/scene-XX.html"` 的宿主，字幕另做一個子合成並加 `data-track-kind="captions"`。
- 子合成內容必須包在 `<template>` 裡（樣式、腳本也在裡面），時間軸註冊在 `window.__timelines["<composition-id>"]`。
- 每個 `<audio>` 需要 `id`；配音放在各幕子合成內用場景內時間，前導留白可直接墊在音檔裡（ffmpeg `adelay`）。
- 常用：`npx hyperframes lint`、`check`（版面／對比度）、`snapshot --at 12,30,45`（截圖檢查）、`render -o out.mp4`。
- 不要對 `.clip` 元素做 visibility／autoAlpha 動畫，改對子元素做 opacity；不要用 `<br>` 斷行，改用 `display:block` 的 span（kit.css 的 `.line`）。
- 逐格 seek 的陷阱（immediateRender 幻影、CSS transition、t=0 首幀、放大字糊、平移露邊）見 `motion-language.md` §4。
- `npx hyperframes check` 的對比度門：淺底資訊型風格要過；深色風格（math-dark、neon-circuit、flat-geo）若被誤報，先確認 `style_apply.py` 的對比度表都過關，再用 `--no-contrast`，其他檢查仍要零錯誤。

## 單一 HTML＋GSAP 要點（`scripts/render_seek.mjs`）
- 頁面提供三個掛鉤：`window.__duration`（總秒數）、`window.__seek(t)`（`tl.seek(t)`＋更新字幕／鏡頭）、`window.__ready = true`（在 `document.fonts.ready` 之後設）。
- 截圖檢查：`node scripts/render_seek.mjs compositions/demo.html renders/stills --at 4,8,16.7` → PNG；成片：`node scripts/render_seek.mjs compositions/demo.html out.mp4 --fps 30 [--audio mix.wav]`。
- 一格一格 seek 再截圖、直接串給 ffmpeg，電腦慢也不掉格，每次結果一樣。需要 playwright（雲端環境可設 `PLAYWRIGHT_PATH` 指到已安裝的模組）與 ffmpeg。
- GSAP 用本機檔（`npm i gsap`），字型用 `font_subset.py` 的本機子集，`style_apply.py --local-fonts` 不寫 Google Fonts @import，渲染全程不連網。
- 時間從 `build.py` 產的 `timing.js` 來（`AT("s3","關鍵字")`），範例見 `examples/handdrawn-skill-demo/`。

## 轉場
Vox 風可用一片斜切色塊掃過畫面（在主合成時間軸於每幕交界 −0.45s 起跑、1 秒掃完）。注意位移距離要讓色塊完全離開畫面，否則會殘留在邊緣。
