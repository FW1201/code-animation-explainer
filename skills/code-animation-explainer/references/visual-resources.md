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
| 新材質 | `.tex-whiteboard` `.tex-ricepaper` `.tex-isogrid` `.seal` | 白板反光與殘影、宣紙、等距點陣、朱紅印章 | — |
| 錄影元件 | `.win` `.win-bar` `.win-side` `.win-input` `.win-btn` `.cursor` `.hud-key` `.chapter-pill` `.pix` | 重畫的應用程式視窗、游標、按鍵提示、像素小助手 | 游標用 `M.move()` |
| 文字元素 | `.el-label` `.el-num` `.el-quote` `.el-emph` | 標籤、數字、引文、強調；**外觀依風格卡 `assets.text` 自動切換**（§2.3） | `.el-emph` 補間 `--p` |
| 手寫圖形 | `SK.*`（`sketch.js`） | Rough.js 手繪線條、Excalidraw 匯入（`sketch-layer.md`） | `SK.draw()` |
| 素材處理 | `AS.*`（`assets.js`） | 照片濾鏡＋外框、圖示線寬顏色、插畫換色（§2） | 手寫圖示可 `SK.draw()` |

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

## 2. 素材對齊：照片、圖示、插畫、文字元素跟著風格走

背景與動畫都換成了水墨，畫面上卻放一張手機原圖、一個藍色扁平圖示，整個畫面就破功。風格卡的 `assets` 欄規定這個風格怎麼處理每一種素材，`assets.js` 在場景載入時自動處理，同一份場景換風格卡，素材也跟著換。照片、插畫的細部處理（色調映射、網點、色階、紙紋、撕邊…）寫在 `detail` 層（`style-system.md` §1.3）。每種風格用真實照片做的校樣在 `assets/styles/previews/proof/`：同一組外部素材在 16 種風格下處理後的樣子。

### 2.1 風格卡的 `assets` 欄

| 欄位 | 選項 | 意思 |
|---|---|---|
| `icon.mode` | `line` 線條／`solid` 實心／`rough` 手寫重畫／`none` 不用圖示 | 圖示的畫法；`rough` 會用 Rough.js 重畫，可以逐筆畫出 |
| `icon.stroke`、`cap`、`color`、`accent` | 線寬（24 格單位）、端點、顏色 token、強調色 token | 全片圖示一致 |
| `photo.treatment` | （舊欄位）`none`／`duotone`／`halftone`／`ink`／`silhouette`／`chalk`／`blueprint`／`soft` | 沒有 `detail.photo` 時的簡易濾鏡；新卡改寫 `detail.photo`（`style-system.md` §1.3） |
| `photo.frame` | `shot` 截圖卡／`polaroid` 拍立得／`magnet` 磁鐵貼／`rounded` 圓角／`ui` 介面框／`none` | 照片在這個世界裡「被放在哪裡」 |
| `illustration.max_colors` | | 插畫換色時最多用幾個彩色（另含深色兩階、螢光色、表面色） |
| `chart` | `axis`、`grid`、`mark`、`label` | 圖表軸線、格線、標記、標籤的樣式 |
| `text.label` | `plate` 名牌／`pill` 膠囊／`plain` 純文字／`tag` 色塊標籤／`inscription` 題跋（前面一個朱紅小方塊）／`mono` 等寬 | `.el-label` 的外觀 |
| `text.emphasis` | `hl` 螢光筆／`underline` 底線／`circle` 圈起／`seal` 印章底／`color` 換色 | `.el-emph` 的外觀 |
| `text.number` | `stat` 標題字＋主色／`mono` 等寬／`hand` 手寫＋強調色 | `.el-num` 的外觀 |
| `text.quote` | `card` 卡片／`kai` 楷書無框／`rule` 左側直線 | `.el-quote` 的外觀 |
| `avoid` | | 這個風格不准出現的素材（emoji、3D 圖示、彩色漸層插畫…） |

### 2.2 在場景裡用

```html
<script src="../style/tokens.js"></script><script src="../style/rough.js"></script>
<script src="../style/sketch.js"></script><script src="../style/assets.js"></script>

<img data-as="photo" src="../assets/leaf.jpg" alt="葉片" data-src="Wikimedia Commons">
<svg data-as="icon" id="s2-ic-sun" class="is-accent" viewBox="0 0 24 24">…Lucide 的 path…</svg>
<svg data-as="illus" viewBox="0 0 800 600">…unDraw 插畫…</svg>
<span class="el-label">葉綠體</span>
<span class="el-num">3.2<small>倍</small></span>
<p class="el-quote">光合作用把<span class="el-emph">光能</span>變成化學能</p>

<script>
AS.apply();                                            // 處理所有 data-as 標記
gsap.set("#s2 .el-emph", { "--p": 0 });
tl.to("#s2 .el-emph", M.draw({ "--p": 1 }), AT("光能"));  // 螢光筆、底線、印章底用 --p 畫出；圈起、換色的風格改用 M.pop({ scale: 1 })
SK.hide("#s2-ic-sun-r"); SK.draw(tl, "#s2-ic-sun-r", AT("陽光"));  // 手寫類風格：圖示一筆一筆畫出（重畫後的 id 加 -r）
</script>
```

| 函式 | 說明 |
|---|---|
| `AS.apply(root)` | 處理 `root` 裡所有 `data-as="photo|icon|illus"`，以及 `.card`／`.obj` 物件 |
| `AS.photo(target)` | 照片管線：色調 → 映射／網點／色階／線稿… → 顆粒 → 紙紋，再加邊緣、混合、外框 |
| `AS.icon(target)` | 線條圖示改成風格線寬、端點、顏色；`solid` 填實心；`rough` 用 Rough.js 重畫（seed 依 id 固定） |
| `AS.illus(target, map)` | 插畫依 `detail.illustration.mode` 換成風格色；`map` 可指定（`{"#6c63ff": "primary"}`）。舊名 `AS.recolor` 仍可用 |
| `AS.objects(root)` | 手繪類風格（`object.edge = rough`）的 `.card`／`.obj` 用 Rough.js 畫外框（斜線填色也改成 hachure） |

片尾下載卡、重點提示這類要「乾淨」的卡片用 `.card--plain`：純白底、無紋理、無外框，只有柔和影子，任何風格都一樣。

程式自己畫的方框、節點、標籤底，加上 `class="obj"` 就會拿到和卡片同一套底紋、邊緣、影子；不要每幕各寫一個 `border-radius` 和 `box-shadow`。

### 2.3 文字元素為什麼要用 `.el-*`

標籤、數字、引文、強調如果每一幕自己寫樣式，越往後越不一樣，而且換風格時要一幕一幕改。`.el-*` 的外觀全部來自 `tokens.css` 的變數（`--label-*`、`--emph-*`、`--num-*`、`--quote-*`），由風格卡 `assets.text` 決定：同一句 `<span class="el-emph">光能</span>` 在 Vox 是螢光筆、在白板是紅圈、在水墨是朱紅印章底、在資料新聞是換成強調色。

### 2.4 處理不了的素材

- 照片太暗（夜景）或太亮：先在 `detail.photo.tone` 調 `brightness`／`contrast`，再看校樣；映射類處理（色階、網點、剪影）對曝光很敏感。
- 多色寫實插畫換色後變髒：換成線條圖示，或只保留一個主色。
- 真實截圖（證據）：永遠用 `.shot`／`as-frame--shot` 保留原貌並標來源，不套濾鏡；**證據不美化**。

## 3. 開放授權素材來源

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

## 4. 圖表與數學工具

| 需求 | 工具 | 影片化重點 |
|---|---|---|
| 圖表轉換 | D3.js | transition 進度由時間軸驅動，不用 d3 自己的計時器 |
| 公式 | KaTeX（輕量）、MathJax | 先渲染成 DOM，再由 GSAP 控制各符號 |
| 數學動畫 | Manim | 顏色用風格卡的 primary／accent／accent-2 hex |
| 流程圖初稿 | Mermaid → 匯出 SVG | 匯出後手動加 class，不要直接用預設配色 |
| 3D | Three.js | 材質顏色讀 `M.color("primary")` |
