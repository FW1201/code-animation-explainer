# 視覺資源：元件庫與開放授權素材

## 1. 元件庫 `assets/styles/kit.css`

所有元件只讀 `tokens.css` 的變數，換風格不用改程式。動畫進度用 CSS 變數讓 GSAP 補間（`--p`、`--draw`），不用 CSS transition。

| 類別 | class | 用途 | 動畫方式 |
|---|---|---|---|
| 舞台 | `.stage` `.safe` `.layer` | 1920×1080 舞台、安全區（已扣字幕區）、全幅疊層 | — |
| 字級 | `.t-h1 .t-h2 .t-h3 .t-body .t-label .t-mono .t-hand .t-num` `.line` | 只用這幾級；`.line` 手動分行 | — |
| 幕別標籤 | `.kicker` | 「02 近義介詞」 | `M.in({x:0})` |
| 材質 | `.tex-paper` `.tex-chalk` `.tex-watercolor` `.tex-vignette` `.tex-blueprint` `.tex-dotgrid` `.tex-halftone` `.tex-backlight` `.tex-circuit` | 掛在 `.stage` 上；風格卡 `texture` 欄指定預設組合 | 靜態；需要漂移時對 `.layer` 做位移 |
| 地面線 | `.ground` | 讓角色、物件有落點，畫面不飄 | — |
| 容器 | `.card` `.card--cutout` `.card--ghost` | 一般卡、剪紙位移陰影卡、只有框線 | `M.pop({scale:1})` |
| 截圖卡 | `.shot` `.shot .src` `.tape` | 真實截圖＋白邊＋傾斜＋膠帶＋來源 | 甩入＋Ken Burns |
| 標籤 | `.chip` `.callout`（`--lead` 引線長） | 分類標籤、帶引線的註解 | `M.in()` |
| 大數字 | `.stat`（內含 `<small>` 單位） | 關鍵數值 | 數字跑到實際值（tabular-nums） |
| 螢光筆／底線 | `.hl` `.ul` | 重點字 | `M.draw({"--p":1})`，初始 `--p:0` |
| 手繪線 | `.ink`（SVG 元素加 `pathLength="1"`）`.ink.is-accent` | 箭頭、圈選、連線、尺寸線 | `M.draw({"--draw":1})`，初始 `--draw:0` |
| 呼吸字卡 | `.breath` | 2–8 字大字＋留白 | 進場後停留 ≥1.5s |
| 圖形統計 | `.picto-row`（子元素設 `--picto: url(icon.svg)`） | ISOTYPE 重複圖示 | `M.pop()`＋`stagger` |
| 字幕條 | `.caption-bar` `.kw` | 燒錄字幕、關鍵詞變色 | 由字幕子合成控制 |
| 專屬筆觸 | `.chalk`（粉筆字）`.silhouette`（皮影填色） | 黑板、皮影風 | — |

GSAP 寫法範例：
```js
// 初始狀態一律先 set 好，再用 to（避免 from／fromTo 的 immediateRender 讓元素提前出現）
gsap.set("#s2 .card", { autoAlpha: 0, scale: 0.92 });
gsap.set("#s2 .hl", { "--p": 0 });
gsap.set("#s2 .ink path", { "--draw": 0 });
tl.to("#s2 .card", M.pop({ autoAlpha: 1, scale: 1 }), AT("方向"))
  .to("#s2 .ink path", M.draw({ "--draw": 1, stagger: M.stagger }), ">")
  .to("#s2 .hl", M.draw({ "--p": 1 }), `>+${M.hold}`);
```

要新增元件時：只用變數、不寫色碼，並在這張表補一行。

## 2. 開放授權素材來源

使用前確認授權條款仍有效，並把來源網址與擷取日期記進 `facts.md` 與片尾出處頁。

| 類型 | 來源 | 授權 | 適合的風格 |
|---|---|---|---|
| 線條圖示 | Lucide、Tabler Icons、Phosphor | ISC／MIT | 全部（ISOTYPE 用實心版） |
| 人物插畫 | Open Peeps、Humaaans | CC0 | flat-geo、picture-book |
| 情境插圖 | unDraw（可改色） | unDraw License（可商用、不可轉售素材） | vox-paper、neon-circuit |
| 歷史圖像、古畫、器物 | 國立故宮博物院 Open Data（CC BY 4.0）、Wikimedia Commons、The Met Open Access（CC0） | 依單張標示 | puppet-shadow、vox-paper |
| 臺灣文化資產 | 國家文化記憶庫（依單筆授權） | 多為 CC BY | puppet-shadow |
| 自然與生物插畫 | Biodiversity Heritage Library、Wikimedia Commons | 多為公共領域 | picture-book、flat-geo |
| 醫學、細胞示意 | Servier Medical Art | CC BY 4.0 | flat-geo、data-journal |
| 地圖 | Natural Earth（公共領域）、OpenStreetMap（ODbL，需標註） | — | data-journal、isotype |
| 照片 | Unsplash、Pexels | 各自授權（可商用、免標註但建議標） | vox-paper、magazine |
| 開放資料 | 政府資料開放平臺（data.gov.tw）、教育部統計處 | 政府資料開放授權 | data-journal、isotype |
| 字型 | Google Fonts（見 `style-system.md` §4） | OFL | 全部 |
| 配樂 | `scripts/bgm.py`、`scripts/bgm_qin.py` 程式合成 | 無授權問題 | 全部 |

**取圖的誠實測試**：「拿掉這張圖，資訊有沒有少？」沒少就是裝飾，不要放。內容必需的圖（講鳥就要有鳥、講器物就要有器物）一定要用真圖，不要用色塊或自己畫的 SVG 代替；真的取不到就放誠實的佔位並告訴使用者「這張圖待補」。

## 3. 圖表與數學工具

| 需求 | 工具 | 影片化重點 |
|---|---|---|
| 圖表轉換 | D3.js | transition 進度由時間軸驅動，不用 d3 自己的計時器 |
| 公式 | KaTeX（輕量）、MathJax | 先渲染成 DOM，再由 GSAP 控制各符號 |
| 數學動畫 | Manim | 顏色用風格卡的 primary／accent／accent-2 hex |
| 流程圖初稿 | Mermaid → 匯出 SVG | 匯出後手動加 class，不要直接用預設配色 |
| 3D | Three.js | 材質顏色讀 `M.color("primary")` |
