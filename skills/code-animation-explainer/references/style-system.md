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

## 1. 風格卡的 7 層參數

風格卡放在 `assets/styles/<id>.json`。每層都要有具體數值；寫不出數值的層，代表那個風格還沒想清楚。

| 層 | 欄位 | 決定什麼 | 例（Vox 紙張拼貼） |
|---|---|---|---|
| ① 色彩 | `color`（8 色）＋`color_semantics` | 每個顏色**代表什麼意義**，不只是好看 | primary＝概念、accent＝紅筆批註、hl＝螢光筆 |
| ② 字型 | `type.display／body／mono／hand`、`scale`、行高、字距 | 字型家族、9 級字級（h1…caption） | Noto Serif TC 900／Noto Sans TC 500；h1 96 |
| ③ 版面 | `layout`：安全邊界、字幕區、圓角、線寬、陰影、傾斜、`composition` | 構圖慣例與容器形狀 | 邊界 96、圓角 4、截圖傾斜 −1.5° |
| ④ 材質 | `texture`、`components` | 背景質感與招牌元件（`kit.css`） | 紙紋＋暈影；截圖卡＋膠帶＋螢光筆 |
| ⑤ 動態 | `motion.ease／dur／stagger／idle／signature` | 5 種 easing 與時長、錯開、閒置運動、招牌動作 | enter expo.out 0.6；螢光筆從左畫到右 |
| ⑥ 運鏡 | `camera`、`transition` | 推近上限、鏡頭預算、轉場語法 | 最多 1.45x；章節用斜切色塊掃過 |
| ⑦ 聲音 | `sound` | 配樂類型、音效密度與種類 | bgm.py 輕快和弦；1–3 個音效／10 秒 |

另外每張卡有 `fits`（適合的科目）、`avoid_for`、`benchmarks`（標杆作品）、`rationale`（色彩為什麼是這樣）、`do／dont`。

## 2. 工作流程：選 → 套 → 用 → 驗

```
選風格（方向板）→ style_apply.py 產生 tokens → 每幕只用 token 寫 → style_lint.py 驗 → 截圖逐幀看
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
4. **動態只用 `M`**：`tl.to(el, M.in({ y: 0 }), AT("關鍵字"))`、`M.out()`、`M.pop()`、`M.move()`、`M.draw({ "--draw": 1 })`；錯開用 `M.stagger`、懸停用 `M.hold`、推拉時長用 `M.zoomDur(1, 1.4)`。
5. **顏色要照語意用**：`color_semantics` 說 accent＝錯誤，就不能拿 accent 標正確答案。同一個概念全片同一色。
6. **每幕至少用一個招牌動作**（`motion.signature`）與該風格的轉場；完全沒用到的幕，就是在做通用動畫。

### 2.4 驗
```bash
python scripts/style_lint.py style/tokens.json compositions/
```
錯誤一定要修到 0：色碼不在色票、寫死字型、字級低於下限、linear easing、Math.random。警告逐條看：多半是寫死秒數、非風格 easing、CSS transition、`<br>`、emoji。確定是刻意的那一行加 `lint-ok` 註解。

lint 只管「有沒有偏離參數」；「好不好看」仍要逐幀截圖看（`qa-checklist.md`）。另外做一次**風格辨識測試**：把任一幕截圖遮掉文字，能不能一眼認出是哪個風格？認不出來就是招牌元素用得不夠。

## 3. 自訂新風格（使用者有自己的品牌或想要新風格）

複製最接近的風格卡改，不要從零寫。色彩用**三步推導**，不要直接抄別人的 hex：

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
- 內文只在黑體、宋體、楷體裡選；圓體、手寫體只當標題或少量註記。一幕最多兩個中文字型家族。
- **西文字型放前面**：`"Newsreader", "Noto Serif TC", serif`。中文字型自帶的英文多半不好看，西文放前面才會接住英文與數字。
- 數字用 `.t-num`（`tabular-nums`），跳動的數字才不會左右晃。
- **中文沒有斜體**：不要用 italic；強調改用字重、螢光筆底色（`.hl`）、著重號（`text-emphasis: dot`）或換成楷體。`kit.css` 已設 `font-synthesis: none` 禁止假斜體、假粗體。
- 引號用「」『』；標題用 `text-wrap: balance`、內文用 `pretty`，避免最後一行只剩一個字。
- 中文字距：標題 0.02–0.08em、內文 0.02–0.06em；圓體與楷體可再寬一點。
- 渲染用的字型要固定：正式渲染前用 `pyftsubset` 依實際用字做子集，改成 `@font-face` 本機載入（見 `engines.md`）。

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
色彩推導、文化語境、反 AI slop 清單與中文排印方法改寫自 [huashu-design](https://github.com/alchaincyf/huashu-design)（MIT © alchaincyf）的 `design-styles.md`、`typography.md`、`content-guidelines.md`。
