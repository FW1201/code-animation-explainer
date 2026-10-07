# 教學動畫風格庫（11 種）

完整參數在 `assets/styles/<id>.json`，預覽圖在 `assets/styles/previews/<id>.jpg`（同一段內容「近義介詞：跟／對／給」套 11 種風格）。列出全部：`python scripts/style_apply.py --list`。

這個庫是**沒有想法時的起點，不是只能從這裡選**。使用者有自己的品牌、學校識別或參考作品時，從那裡長出風格（`style-system.md` §3）。

## 總表

| id | 風格 | 溫度 | 最適合 | 招牌動作 | 預覽 |
|---|---|---|---|---|---|
| `vox-paper` | Vox 紙張拼貼 | 中性 | 媒體素養、科技、時事、AI 工具 | 螢光筆畫過、紅圈手繪、截圖卡甩入 | `previews/vox-paper.jpg` |
| `data-journal` | 資料新聞 | 安靜 | 統計、研究方法、量化研究、實驗數據 | 資料點在圖表間轉換、數字跑到實際值 | `previews/data-journal.jpg` |
| `chalkboard` | 黑板粉筆 | 中性·暖 | 數學解題、字詞拆解、公式推導 | 一筆一筆寫出、板擦擦去 | `previews/chalkboard.jpg` |
| `flat-geo` | 扁平幾何（Kurzgesagt 式） | 大膽 | 自然科、天文、細胞、抽象概念擬人 | 角色預備動作彈出、三層視差、形狀 morph | `previews/flat-geo.jpg` |
| `blueprint` | 藍圖工程 | 中性 | 科技、機構、程式架構、建築 | 線稿描出、爆炸拆解再組回 | `previews/blueprint.jpg` |
| `puppet-shadow` | 剪紙皮影 | 大膽·暖 | 歷史、典故、成語、民俗節慶 | 關節轉動、燈暗換景、墨跡浮字 | `previews/puppet-shadow.jpg` |
| `math-dark` | 深底數學（3B1B 式） | 大膽·冷靜 | 數學、物理公式、幾何證明、演算法 | 顏色即變數、符號飛到圖形上 | `previews/math-dark.jpg` |
| `picture-book` | 繪本水彩 | 安靜·暖 | 國小、生命教育、生活課程、閱讀 | 水彩暈開、翻頁、逐詞浮現 | `previews/picture-book.jpg` |
| `magazine` | 雜誌撞色編排 | 大膽 | 國語文、議題探究、公民、觀點短片 | 大字砸下、色塊遮罩擦出 | `previews/magazine.jpg` |
| `isotype` | 圖形統計（ISOTYPE） | 中性 | 社會統計、人口、環境、數感 | 圖示逐個堆疊、多出來的部分變色 | `previews/isotype.jpg` |
| `neon-circuit` | Neon Circuit（品牌系統） | 大膽 | AI 與程式教學、期刊系列、工具操作 | 訊號沿走線流動、程式碼逐行亮起 | `previews/neon-circuit.jpg` |

## 依科目與年級挑候選（方向板用）

| 科目 \ 年級 | 國小 | 國中 | 高中以上／教師研習 |
|---|---|---|---|
| 國語文 | picture-book、chalkboard | chalkboard、magazine | magazine、vox-paper |
| 華語文（TOCFL） | picture-book、chalkboard | chalkboard、flat-geo | data-journal（語料量化）、magazine |
| 數學 | chalkboard、isotype | chalkboard、math-dark | math-dark、data-journal |
| 自然科學 | picture-book、flat-geo | flat-geo、blueprint | flat-geo、data-journal |
| 社會（史地公） | puppet-shadow、isotype | puppet-shadow、isotype、vox-paper | vox-paper、data-journal |
| 科技（資訊、生科） | flat-geo、blueprint | blueprint、neon-circuit | neon-circuit、vox-paper |
| 研究方法與統計 | — | isotype | data-journal、math-dark |

挑三個時要**拉開溫度**：一個安靜、一個中性、一個大膽。三個都落在「米白底＋留白＋一個點綴色」是最常見的失敗。

## 方向板輪盤（邏輯 ①）

`date +%S` 取秒數，`秒數 % 11` 對應下表（0 起算）；抽到 `avoid_for` 列有的科目就重抽一次，並說明為什麼重抽。

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| vox-paper | data-journal | chalkboard | flat-geo | blueprint | puppet-shadow | math-dark | picture-book | magazine | isotype | neon-circuit |

## 風格 × 構圖是兩件事

風格全片定一次（色彩、字型、材質、動態都從風格卡來），**構圖每幕換**（置中特寫、左右分欄、三欄並排、對角線、滿版字卡）。任兩幕截圖比較：風格應該看不出差別，構圖應該一眼不同。反過來，就是在每幕換風格、卻每幕用同一個版面。

## 每種風格的實作提醒

- **vox-paper**：截圖要真的截（`scripts/shoot.mjs`），標「來源：網域」；細節見 `vox-style.md`。
- **data-journal**：圖表用 D3 或手寫 SVG，資料綁定後由時間軸驅動轉換；沒有原始數值不畫數值。
- **chalkboard**：文字描寫效果用 SVG 文字外框＋`--draw`，或逐字 clip-path 揭露；速度要穩定。
- **flat-geo**：角色元件化（圓角幾何＋眼睛），前中後景各一層，視差速度 0.35／0.7／1.4。
- **blueprint**：線寬只用兩級；標註一律等寬字；拆解沿單一軸線進行。
- **puppet-shadow**：人物結構與關節工具見 `puppet-style.md`。
- **math-dark**：公式用 KaTeX 或 Manim；同一變數全片同色，寫進 `color_semantics`。
- **picture-book**：一頁一句話，字比其他風格大一級；角色造型全片一致。
- **magazine**：標題寫結論；字級只用三級但差距 ≥6 倍；允許大字出血被裁切。
- **isotype**：一個圖示代表固定數量，圖例先出現；絕對不用放大圖示表示數量。
- **neon-circuit**：作者品牌；主色只給訊號與主角，不加外發光。
