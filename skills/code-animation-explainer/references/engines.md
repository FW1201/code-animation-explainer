# 動畫引擎選擇

| 引擎 | 寫法 | 適合 | 需求 |
|---|---|---|---|
| **HyperFrames** | HTML＋CSS＋GSAP，`data-start/duration` 宣告片段，子合成拆幕 | 解說影片、需要真實截圖與字幕、要 CLI 檢查與渲染 | Node 22+、ffmpeg；`npx hyperframes init` |
| **Remotion** | React 元件，`useCurrentFrame()` | 已熟 React、需要資料驅動 | Node、ffmpeg |
| **Manim** | Python，數學物件動畫 | 公式推導、幾何、圖形 | Python、LaTeX（選用） |
| **單一 HTML＋GSAP** | 一個檔案、瀏覽器播放 | 沒有本機環境、只要快速示意 | 瀏覽器；以螢幕錄影輸出 |

## 共通原則（任何引擎）
- **時間軸驅動**：畫面只由時間 t 決定，可任意 seek。GSAP 用 `gsap.timeline({ paused: true })`；Remotion 用 frame；Manim 用 `self.play` 時長。
- **決定性**：禁止 `Math.random()`（要亂數就用固定種子）、`Date.now()`、網路請求、無限 `repeat: -1`。
- **一幕一檔**：每幕獨立的樣式／標記／腳本，用建置腳本組裝；主合成只負責排順序、轉場、字幕與背景音樂。
- **ID 前綴**：每幕的 id 加上幕號前綴（`#s3-title`），避免多幕同時載入時選擇器互相干擾。
- **字型**：用 `@font-face` 載入本機字型檔；中文字型很大，建議依實際用字做子集（fonttools `pyftsubset` 轉 woff2），常可從 12MB 降到 200KB。

## HyperFrames 要點
- 主合成 `index.html`：每幕一個 `data-composition-src="compositions/scene-XX.html"` 的宿主，字幕另做一個子合成並加 `data-track-kind="captions"`。
- 子合成內容必須包在 `<template>` 裡（樣式、腳本也在裡面），時間軸註冊在 `window.__timelines["<composition-id>"]`。
- 每個 `<audio>` 需要 `id`；配音放在各幕子合成內用場景內時間，前導留白可直接墊在音檔裡（ffmpeg `adelay`）。
- 常用：`npx hyperframes lint`、`check`（版面／對比度）、`snapshot --at 12,30,45`（截圖檢查）、`render -o out.mp4`。
- 不要對 `.clip` 元素做 visibility／autoAlpha 動畫，改對子元素做 opacity；不要用 `<br>` 斷行，改用 `display:block` 的 span。

## 轉場
Vox 風可用一片斜切色塊掃過畫面（在主合成時間軸於每幕交界 −0.45s 起跑、1 秒掃完）。注意位移距離要讓色塊完全離開畫面，否則會殘留在邊緣。
