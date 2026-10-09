# 風格構築系統：讓「風格參數」真的影響每一幀

## 問題：為什麼風格常常沒有作用

使用者說「用 Vox 風」，成品卻像通用簡報。原因有四個，每一個都對應一條規則：

| 失效原因 | 症狀 | 對策（本文件） |
|---|---|---|
| 風格只是一段形容詞 | 模型各幕自己發明顏色、字型、秒數 | 風格寫成**機器可讀的風格卡**（7 層參數），產生 `tokens.css／tokens.js` |
| 參數只在第一幕讀過 | 越後面的幕越偏離，回到模型預設（Inter、藍紫、0.3s ease） | 每一幕**只能用 token**，不准寫死值；`style_lint.py` 把關 |
| 只調了顏色 | 換了色但版面、節奏、轉場、聲音全一樣，看起來像換皮 | 風格卡**同時定義**色彩、字型、版面、材質、動態、運鏡、聲音 |
| 預設值太安全 | 沒指定就退回白底＋藍色＋圓角卡片 | 先出**方向板**讓使用者用眼睛選（`direction-boards.md`），每個風格有「招牌動作」與「不要做」清單 |

一句話：**風格是一組會被程式讀取、被檢查的參數，不是一段描述。**

## 1. 風格卡：參數層＋風格語法

### 1.1 參數層（數值）

風格卡放在 `assets/styles/<id>.json`。每層都要有具體數值；寫不出數值的層，代表那個風格還沒想清楚。

| 層 | 欄位 | 決定什麼 | 例（Vox 紙張拼貼） |
|---|---|---|---|
| ① 色彩 | `color`（8 色）＋`color_semantics` | 每個顏色**代表什麼意義**，不只是好看 | primary＝概念、accent＝紅筆批註、hl＝螢光筆 |
| ② 字型 | `type.display／body／mono／hand`、`scale`、行高、字距 | 字型家族、9 級字級（h1…caption） | Noto Serif TC 900／Noto Sans TC 500；h1 96 |
| ③ 版面 | `layout`：安全邊界、字幕區、圓角、線寬、陰影、傾斜、`composition` | 構圖慣例與容器形狀 | 邊界 96、圓角 4、截圖傾斜 −1.5° |
| ④ 材質 | `texture`、`components` | 背景質感與招牌元件（`kit.css`） | 紙紋＋暈影；截圖卡＋膠帶＋螢光筆 |
| ⑤ 動態 | `motion.ease／dur／stagger／idle／signature` | 5 種 easing 與時長、錯開、閒置運動、招牌動作 | enter expo.out 0.6；螢光筆從左畫到右 |
| ⑥ 運鏡 | `camera`、`transition` | 推近上限、鏡頭預算、轉場語法 | 最多 1.45x；章節用斜切色塊掃過 |
| ⑦ 聲音 | `sound`（含 `foley` 材質音、`palette` 樂器） | 配樂類型、音效密度與種類 | bgm.py 輕快和弦；1–3 個音效／10 秒 |
| ⑧ 素材 | `assets` | 照片、圖示、插畫、圖表、文字元素怎麼處理才屬於這個世界 | 截圖卡＋線條圖示 2.5＋名牌標籤＋螢光筆強調（`visual-resources.md` §2） |
| ⑨ 手寫感（選用） | `sketch` | Rough.js 的 roughness、bowing、填色方式、seed | 白板 0.8 單線；粉筆 1.4 鋸齒填色（`sketch-layer.md`） |

另外每張卡有 `fits`（適合的科目）、`avoid_for`、`benchmarks`（標杆作品）、`rationale`（色彩為什麼是這樣）、`do／dont`。

### 1.2 風格語法（這個媒材「是什麼、能做什麼、會踩什麼坑」）

數值管得住顏色與秒數，管不住「這一幕像不像這個風格」。所以每張卡還有一層語法，`style_apply.py` 會檢查它齊不齊：

| 欄位 | 內容 | 寫分鏡時怎麼用 |
|---|---|---|
| `essence` | 3–5 條辨識特徵：一眼認出這個風格的關鍵 | 每幕截圖遮掉文字，至少要看得出其中兩條 |
| `not` | 容易混淆的風格與界線（黑板≠白板≠手繪草圖） | 發現畫面往另一個風格靠時，照這條拉回來 |
| `native_moves` | 只有這個媒材做得到的招式，每招附 ≥3 個適合的教學內容 | 全片的情緒高點或概念轉折，放一個原生招式；分鏡卡的 `native_move` 欄寫用哪一招 |
| `camera_vocab` | 運鏡詞彙：動作／表達什麼／適合哪種教學時刻 | 分鏡卡的 `camera` 欄只從這張表選；表上沒有的動作代表這個媒材不擅長 |
| `pitfalls` | 這個媒材特有的陷阱與修法 | 寫程式前讀一次；QA 時逐條檢查 |
| `variation` | 三種結構、三種開場、三種結尾 | 方向板與三候選結構從這裡出發，避免同風格每支片都一樣（`direction-boards.md`） |
| `caption.world` | 字幕在這個風格世界裡是什麼（題跋、地圖標籤、粉筆槽字幕條） | 字幕是風格的一部分，不是通用黑條 |
| `sound.foley`、`sound.palette` | 這個媒材的材質音與樂器 | 混音時用風格自己的聲音，不用通用鋼琴弦樂（`audio-design.md`） |

### 1.3 細節層 `detail`（物件質感＋外部素材處理）

參數層管顏色和秒數，語法層管「做什麼」，細節層管「每一樣東西摸起來像什麼」：卡片的紙紋、邊緣是撕的還是筆刷的、影子是軟的還是貼紙那種硬邊、外面收集來的照片要調成什麼色調、加多少顆粒。少了這層，畫面常常是「背景很有風格、上面的東西都是預設」。

| 欄位 | 選項 | 作用在哪 |
|---|---|---|
| `object.surface` | `flat`／`paper` 紙紋／`grain` 顆粒／`hatch` 斜線／`halftone` 網點／`chalk` 粉筆灰／`wash` 水彩暈／`glass` 半透明／`blueprint` 格線／`scan` 掃描線 | `.card`、`.obj` 的底 |
| `object.edge` | `clean`／`rough` 手繪抖動／`brush` 筆刷／`torn` 撕紙 | 物件輪廓（CSS 遮罩；手繪類風格另由 `AS.objects()` 用 Rough.js 畫外框） |
| `object.border` | `none`／`hair` 細線／`ink` 墨線／`chalk` 粉筆線／`double`／`dashed` | 物件外框 |
| `object.shadow` | `none`／`soft` 柔影／`lift` 貼紙下緣／`hard` 偏移硬影／`long` 長影／`glow` 光暈 | 物件影子（不規則邊緣也跟著形狀走） |
| `object.grain` | 0–0.3 | 物件上的雜訊量 |
| `photo.mode` | `color` 只調色／`map` 色調映射／`halftone` 真網點／`posterize` 色階（向量插畫感）／`lines` 線稿／`chalk` 粉筆／`ink` 水墨／`silhouette` 剪影 | 外部照片的主處理 |
| `photo.map`、`map_mix` | 由暗到亮的風格色（可寫 `mix(primary,surface,0.5)`）；映射混合比例 | 照片顏色換成風格色 |
| `photo.tone` | `saturation`、`contrast`、`brightness`、`warmth` | 先統一色調再處理 |
| `photo.halftone`、`grain`、`paper` | 網點大小（px）、顆粒量、紙紋量 | 印刷感與材質 |
| `photo.edge` | `none`／`rounded`／`circle` 圓框／`soft` 暈邊／`brush` 筆刷邊／`torn` 撕邊 | 照片輪廓 |
| `photo.blend`、`overlay` | `multiply`／`screen`；`scan` 掃描線／`grid` 格線 | 照片和底的關係 |
| `illustration.mode` | `palette` 換成最近風格色／`duotone` 兩色／`mono` 單色深淺／`outline` 只留線／`rough` Rough.js 重畫 | 外部多色插畫 |

**驗證**：`python scripts/style_proof.py <id>` 產生校樣頁，左上是原始素材（真實照片、Lucide 圖示、多色插畫，來源見 `assets/proof/SOURCES.md`），下方與右側是處理後的樣子，旁邊放程式畫的卡片、流程方塊、長條圖與字幕條。看截圖時問：「哪一個東西看起來是從別支影片剪過來的？」有就調 `detail`。16 種風格的校樣在 `assets/styles/previews/proof/`。換成自己的素材：`--photos a.jpg b.jpg c.jpg d.jpg`。

**語法是邊界，不是劇本**：招式、運鏡、結構都是選單，選你的內容需要的；故事、順序、例子永遠從使用者的主題來。

## 2. 工作流程：選 → 套 → 用 → 驗

```
選風格（方向板）→ style_apply.py 產生 tokens → 讀風格語法 → 每幕只用 token 寫 → style_lint.py 驗 → 截圖逐幀看
```

### 2.1 選
- 依科目與年級先從 `style-library.md` 篩出候選，再做三張方向板（`direction-boards.md`）。
- 方向板直接用 `style_apply.py` 產生的 `board.html`，把真實腳本內容放進 `--sample`：
  ```bash
  python scripts/style_apply.py chalkboard --sample sample.json --out design-demos/A
  npx playwright screenshot --viewport-size=1920,1080 --wait-for-timeout=2000 file://$PWD/design-demos/A/board.html design-demos/A.png
  ```
- 混搭：`--colors-from`（換整組色彩）、`--type-from`（換整組字型）、`--set 路徑=值`（改單一參數）。
  例：「B 的版面，A 的顏色」→ `style_apply.py data-journal --colors-from vox-paper`。

### 2.2 套
選定後，在專案根目錄產生 `style/`，並把風格 id 寫進 `storyboard.json` 的 `style`、`direction-approved.md` 記下指令：
```bash
python scripts/style_apply.py vox-paper --out style/
```
每一幕（HyperFrames 子合成、Remotion 元件、單一 HTML）一律先載入：
```html
<link rel="stylesheet" href="../style/tokens.css">
<link rel="stylesheet" href="../style/kit.css">
<script src="../style/tokens.js"></script>
```
`tokens.css` 開頭有一行註解寫著這個風格預設的材質 class，舞台照抄：`<div class="stage tex-paper tex-vignette">`。

### 2.3 用：寫場景時的 6 條硬規則
1. **顏色只用 `var(--…)`**：要淡一點用 `color-mix(in oklab, var(--ink) 30%, transparent)`，不要自己寫 hex 或 rgba。
2. **字級只用 class 或變數**：`.t-h1 .t-h2 .t-h3 .t-body .t-label`、`.stat`、`var(--fs-…)`。標題用 `<span class="line">` 手動分行。
3. **字型只用變數**：`var(--font-display／body／mono／hand)`。
   標題分兩類：**手寫類風格**（風格卡有 `sketch` 區塊：sketch-board、whiteboard、chalkboard、picture-book）的標題與重點詞用 `SK.write` 照筆順寫出，全片所有標題（含疊加標題、CTA、角標）都用它；**其他風格**的標題用 `.t-h1／.t-h2`＋風格卡 display 字型，不用 `SK.write`（楷書筆順字會變成第三種中文字型）。
4. **動態只用 `M`**：`tl.to(el, M.in({ y: 0 }), AT("關鍵字"))`、`M.out()`、`M.pop()`、`M.move()`、`M.draw({ "--draw": 1 })`；錯開用 `M.stagger`、懸停用 `M.hold`、推拉時長用 `M.zoomDur(1, 1.4)`。
5. **顏色要照語意用**：`color_semantics` 說 accent＝錯誤，就不能拿 accent 標正確答案。同一個概念全片同一色。
6. **每幕至少用一個招牌動作**（`motion.signature`）與該風格的轉場；完全沒用到的幕，就是在做通用動畫。
7. **手寫線條只用 `SK.*`**（有 `sketch` 欄的風格）：每個圖形給 id，seed 才固定；不要直接呼叫 `rough.svg()`（`sketch-layer.md`）。
8. **素材與文字元素只透過 `AS.*` 與 `.el-*` 進畫面**：照片、圖示、插畫先經 `AS.apply()`；標籤、數字、引文、強調只用 `.el-label／.el-num／.el-quote／.el-emph`。直接放原圖、自己寫一套標籤樣式，就是素材沒跟風格對齊。

### 2.4 驗
```bash
python scripts/style_lint.py style/tokens.json compositions/
```
錯誤一定要修到 0：色碼不在色票、寫死字型、字級低於下限、linear easing、Math.random。警告逐條看：多半是寫死秒數、非風格 easing、CSS transition、`<br>`、emoji。確定是刻意的那一行加 `lint-ok` 註解。

lint 只管「有沒有偏離參數」；「好不好看」仍要逐幀截圖看（`qa-checklist.md`）。另外做一次**風格辨識測試**：把任一幕截圖遮掉文字，能不能一眼認出是哪個風格？認不出來就是招牌元素用得不夠。

## 3. 自訂新風格（使用者有自己的品牌或想要新風格）

複製最接近的風格卡改，不要從零寫，**語法層（§1.2）也要一起改寫**：辨識特徵、不是什麼、原生招式寫不出來，代表這個風格還沒想清楚。寫好後跑 `python scripts/style_catalog.py --render` 更新風格庫與預覽。色彩用**三步推導**，不要直接抄別人的 hex：

| 步驟 | 做什麼 | 檢查 |
|---|---|---|
| 1. 採樣 | 從三個來源取色：①使用者的品牌／學校識別 ②內容本身的真實素材（實驗器材、史料、課本插圖）③文化語境（下表） | 每個顏色說得出來源 |
| 2. 收斂 | 壓到 2–3 個有彩色＋一組中性色（bg、surface、ink、ink-2）。有彩色之間色相差 ≥60° 或明度差明顯 | 色票 ≤8 色 |
| 3. 論證 | 寫一句 `rationale`：「主色取自課本封面的墨綠，壓低彩度像印刷」 | 寫不出來＝在抄配方 |

**彩度（像印刷品而不是螢光幕）**：大面積底色用很低彩度（oklch chroma 0.01–0.04）；主色與強調 0.08–0.15；只有小面積點睛才用到 0.15–0.22。整片高彩度會有廉價的螢光感。

**文化語境速查（臺灣教學常用）**

| 色相 | 語境 A | 語境 B |
|---|---|---|
| 紅 | 朱紅、印泥（偏橙、帶灰）→ 傳統、古文、節慶 | 正紅 → 警告、錯誤 |
| 綠 | 黑板綠、苔綠（低彩度）→ 教室、自然 | 螢光綠 → 終端機、駭客（少用） |
| 藍 | 藍染、曬圖藍 → 工藝、工程 | 科技藍 #0066FF 系 → 模型最愛的預設，用之前先問自己是不是在抽籤 |
| 黃 | 藤黃、粉筆黃 → 板書、重點 | 警示黃 → 注意、危險 |
| 白 | 米白紙 → 書本、溫暖 | 純白 → 實驗室、資料圖表 |

新風格卡跑一次 `style_apply.py`：它會檢查欄位齊不齊，並列出對比度不足的顏色（文字至少 4.5:1，大字與圖形至少 3:1）。只當色塊、不當文字色的顏色列進 `graphic_only`；文字其實放在 surface 上（例如皮影幕布）就寫 `layout.text_on: "surface"`。

## 4. 中文字型與排印

**Google Fonts 上可直接用的繁體中文字型**（皆可免費商用）：

| 字型 | 類別 | 氣質 | 適合 |
|---|---|---|---|
| Noto Sans TC（思源黑體） | 黑體 | 中性、可靠，萬用內文 | 內文預設 |
| Noto Serif TC（思源宋體） | 宋體 | 出版、正式；900 可當大標 | 標題、人文 |
| Chiron Hei HK（昭源黑體） | 黑體 | 比思源黑更有個性、字面現代 | 科普、科技大標 |
| Chiron Sung HK（昭源宋體） | 宋體 | 傳統字形細節多 | 古文、歷史 |
| LXGW WenKai TC（霞鶩文楷） | 楷體 | 手寫溫度、親切 | 板書、繪本、引文 |
| Iansui（芫荽） | 手寫楷 | 像老師寫的字 | 黑板、手寫註記 |
| Huninn（jf open 粉圓） | 圓體 | 可愛、低年級友善 | 國小、繪本 |
| Cactus Classical Serif（仙人掌明體） | 明體 | 古籍刻本感 | 古典文學 |

**規則**
- 內文只在黑體、宋體、楷體裡選；圓體、手寫體只當標題或少量註記。例外：手寫類風格（whiteboard、sketch-board、chalkboard）內文可用芫荽 Iansui，它是楷體骨架、長句也讀得順。一幕最多兩個中文字型家族。
- **西文字型放前面**：`"Newsreader", "Noto Serif TC", serif`。中文字型自帶的英文多半不好看，西文放前面才會接住英文與數字。
- 數字用 `.t-num`（`tabular-nums`），跳動的數字才不會左右晃。
- **中文沒有斜體**：不要用 italic；強調改用字重、螢光筆底色（`.hl`）、著重號（`text-emphasis: dot`）或換成楷體。`kit.css` 已設 `font-synthesis: none` 禁止假斜體、假粗體。
- 引號用「」『』；標題用 `text-wrap: balance`、內文用 `pretty`，避免最後一行只剩一個字。
- 中文字距：標題 0.02–0.08em、內文 0.02–0.06em；圓體與楷體可再寬一點。
- 渲染用的字型要固定：正式渲染前跑 `python scripts/font_subset.py --style style/tokens.json --text script.md storyboard.json compositions/ --out fonts/`，只下載用到的字（通常 100–300 KB／字型），場景改載入 `fonts/fonts.css`，渲染時不連網。腳本改字後要重跑。

## 5. 反 AI 模板感（風格的下限）

這些是模型預設最常產生、而且**不帶任何風格資訊**的東西。除非風格卡明確要求，一律不要：

| 不要 | 為什麼 | 改用 |
|---|---|---|
| 紫藍漸層背景 | 所有 AI 產品頁的萬用公式 | 風格卡的 bg＋材質 |
| emoji 當圖示 | 看起來像沒設計 | Lucide／Tabler／Phosphor，或乾脆不用圖示 |
| 每個標題前面配一個圖示 | 裝飾大於內容 | 只在圖示帶資訊時才用 |
| 圓角卡片＋左側彩色粗邊 | 2020 年代網頁模板 | 風格卡的容器形狀（剪紙卡、截圖卡、細線框…） |
| 用 SVG 畫寫實人臉 | 五官一定歪 | 風格化角色（皮影、幾何角色）、真實照片，或誠實的佔位 |
| 深灰藍底 #0D1117＋青色霓虹光暈 | AI 落地頁的偷懶組合 | 有作者意圖的深色（3B1B 炭黑、Neon Circuit 走線母題） |
| 編造的裝飾數字、假統計 | 學生會當真 | 沒有資料就只畫方向（見 `review-gates.md`） |
| Inter／Arial 當中文標題 | 退回系統預設 | 風格卡的 display 字型 |
| 所有元素同樣 0.3s ease 淡入 | 沒有節奏 | 風格卡的 5 種 easing＋招牌動作 |

**品牌例外**：使用者自己的品牌系統（例如 Neon Circuit）用到上表的元素時，可以保留，因為那是品牌識別而不是預設值；但仍要加上品牌自己的母題，不要只剩色彩。

**誠實的佔位比爛實作好**：缺真實截圖、照片時，放一個標「真實截圖放這裡」的灰框（`board.html` 的 Vox 範例就是這樣），不要畫一個假的。

## 6. 可讀性底線（任何風格都不能破）

- 1080p 畫面：內文 ≥ 風格卡 `body`（多數 36–46px），最小字 ≥ `small`（24px 以上）；字幕 ≥ 42px。
- 對比度：文字 ≥ 4.5:1，大字（≥ 48px）與圖形 ≥ 3:1。`style_apply.py` 會列出不足的組合。
- 留白要是構圖，不是內容不見了：每一幀都要有明確的視覺焦點（`storyboard-craft.md` 規則 1）。
- 3 公尺測試：關鍵幀縮到手機大小，最大的字仍讀得出來。

---
風格語法層（辨識特徵、原生招式、運鏡詞彙、媒材陷阱、變化空間）改寫自 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)（MIT © LemoLab）的 STYLE.md 結構。色彩推導、文化語境、反 AI slop 清單與中文排印方法改寫自 [huashu-design](https://github.com/alchaincyf/huashu-design)（MIT © alchaincyf）的 `design-styles.md`、`typography.md`、`content-guidelines.md`。
