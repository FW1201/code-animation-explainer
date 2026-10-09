# 動畫類型：幫老師選對「風格＋技術＋輸出方式」

Coding Animation 不是某一套框架，而是「用程式碼控制時間、圖形、狀態與互動」的一大類動畫。底層都是同一條：

**狀態（State）→ 時間（Time）→ 插值（Interpolation）→ 重畫（Render）→ 互動（Interaction）**

HyperFrames、GSAP、D3、p5.js、Three.js 只是分別幫你管理其中幾步。所以選型時先決定「內容需要什麼」，再挑技術。

## 第一步：先問輸出方式

| 輸出方式 | 說明 | 適合 |
|---|---|---|
| **影片（MP4）** | 有配音字幕、固定時間軸，走完整產線 ①–⑧ | 課前預習、YouTube、不能上網的教室 |
| **互動教材（HTML）** | 學生自己捲動、拖拉、點擊；可附配音按鈕 | 課堂操作、探究活動、自學網站 |
| **兩者都要** | 同一份程式：影片版用時間軸自動播放，互動版把時間軸交給捲動或滑桿 | 最省工：先做影片，再開放互動 |

互動類（Scrollytelling、Simulation）的價值在「學生操作」，硬錄成影片會失去重點；若仍要影片，就錄一段「示範操作」。

## 第二步：選教學動畫流派（6 種）

| 流派 | 畫面 | 最適合的科目／內容 | 主要技術 | 影片化難度 |
|---|---|---|---|---|
| **Animated Diagram 動態圖解** | 節點、箭頭、標籤一步步長出，資料沿線流動 | 流程、架構、因果、語法樹、AI 系統 | DOM／SVG＋GSAP | ★ 最容易（本 skill 預設） |
| **Kinetic Typography 動態文字** | 字詞逐字出現、放大、拆解、重組 | 語文、詞彙、概念強調、口號 | DOM＋GSAP | ★ |
| **Data Storytelling 資料敘事** | 同一批資料在圖表間平滑轉換（長條→散點→群聚） | 統計、研究結果、社會議題 | D3.js／SVG | ★★ |
| **Interactive Simulation 互動模擬** | 拖拉參數立即改變結果；重力、碰撞、擺動 | 數學、物理、化學實驗 | Canvas＋物理引擎、p5.js | ★★（需固定步長） |
| **Spatial／3D Explainer 空間解說** | 旋轉、縮放、鏡頭移動 | 天文、地理、分子、人體、工程 | Three.js／WebGL | ★★★ |
| **Generative Visualization 生成視覺** | 粒子、流場、noise、群體運動 | AI 概念（token、attention）、抽象概念、藝術 | Canvas、p5.js、PixiJS、Shader | ★★（需固定種子） |

一支影片可以混搭：主線用 Animated Diagram，關鍵處插一段 Data Storytelling 或 3D。混搭很常見——漂亮的互動教材多半是 HTML＋CSS＋SVG＋Canvas 的組合，而不是某個神祕引擎。

### 視覺風格（和流派正交，可任意搭配）
流派決定「用什麼技術講」，視覺風格決定「長什麼樣子」。風格不要用形容詞指定，一律從 `style-library.md` 的 11 張**風格卡**選（或自訂一張），用 `scripts/style_apply.py` 套成 tokens，見 `style-system.md`。常見搭配：

| 流派 | 常搭的風格卡 |
|---|---|
| Animated Diagram | vox-paper、blueprint、neon-circuit、chalkboard |
| Kinetic Typography | magazine、chalkboard、picture-book |
| Data Storytelling | data-journal、isotype |
| Interactive Simulation | blueprint、math-dark、flat-geo |
| Spatial／3D | flat-geo、blueprint |
| Generative Visualization | neon-circuit、flat-geo、math-dark |

### 輔助手法（可疊在任何流派上）
- **UI Motion**：卡片滑入、淡入、彈跳。CSS 或 Web Animations API 就能做。
- **SVG 描線／形變（Draw／Morph）**：箭頭延伸、路徑移動、圓變方；最適合流程圖與概念轉換。
- **Scrollytelling**：捲動＝時間軸（GSAP ScrollTrigger 的 scrub／pin）。互動版專用。
- **Lottie**：設計師在 After Effects 做好的向量動畫，用程式播放；適合現成吉祥物、圖示動畫。
- **Shader（GLSL）**：液體、光暈、波紋；做背景氛圍，不要拿來承載教學重點。

## 第三步：寫成提示詞

把選擇濃縮成一句，放進 8 參數框架的「⑤ 動畫語彙」：

> **流派＋風格卡 id＋渲染技術＋動作行為（Motion）＋互動方式（Interaction）**

範例：
- 「製作 **Animated Diagram** 教學動畫，風格卡 **blueprint**（只用 style/tokens.css 與 M.*），以 **SVG＋GSAP** 為主，採 **sequential reveal、path drawing**；互動版支援節點 **hover 與 click 展開**。」
- 「**Data Storytelling**：用 **D3** 讓同一批 30 筆資料從長條圖**平滑轉換**成散點圖再依類別**群聚**，每次轉換 1.2 秒 ease-in-out。」
- 「**Interactive Simulation**：**Canvas＋固定步長物理**模擬單擺，學生用**滑桿**調整擺長與重力；影片版以擺長 1m→2m 各跑 5 秒示範。」

## 影片化時的決定性規則
- 粒子、生成、物理類：亂數用**固定種子**（seeded PRNG），物理用**固定時間步長**並依時間 t 重算或預先模擬成關鍵格，才能逐格渲染且每次結果一樣。
- 3D／Shader：時間參數由時間軸提供（uniform `u_time = t`），不要讀系統時鐘。
- 互動元素（hover、拖拉）在影片版改成時間軸上的「示範動作」。

## 給老師的快速選擇
- 講「步驟、流程、關係」→ Animated Diagram
- 講「字詞、定義、口訣」→ Kinetic Typography
- 講「資料、趨勢、比較」→ Data Storytelling
- 講「變因、實驗、如果…會怎樣」→ Interactive Simulation（互動版優先）
- 講「形狀、位置、立體結構」→ Spatial／3D
- 講「看不見的抽象過程」→ Generative Visualization
