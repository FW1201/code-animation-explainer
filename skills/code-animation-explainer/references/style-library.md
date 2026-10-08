# 教學動畫風格庫

完整參數在 `assets/styles/<id>.json`，預覽圖在 `assets/styles/previews/<id>.jpg`（同一段內容「近義介詞：跟／對／給」套不同風格），瀏覽全部：`assets/styles/previews/index.html`。列出全部：`python scripts/style_apply.py --list`。

這個庫是**沒有想法時的起點，不是只能從這裡選**。使用者有自己的品牌、學校識別或參考作品時，從那裡長出風格（`style-system.md` §3）。

## 總表

<!-- catalog:start -->
<!-- 由 scripts/style_catalog.py 產生，請改風格卡再重跑，不要手改 -->
| id | 風格 | 溫度 | 最適合 | 原生招式 | 手寫感 | 預覽 |
|---|---|---|---|---|---|---|
| `blueprint` | 藍圖工程 | 中性 | 科技與工程、生活科技、物理機構 | 爆炸拆解、尺寸標註、線稿描出 | — | `previews/blueprint.jpg` |
| `chalkboard` | 黑板粉筆 | 中性·暖 | 數學解題步驟、國語文字詞拆解、公式推導 | 板書寫出、黃粉筆圈答案、板擦擦掉 | roughness 1.4 | `previews/chalkboard.jpg` |
| `data-journal` | 資料新聞 | 安靜 | 統計、研究方法、社會領域 | 同一批資料換圖、座標軸長出來、其他變灰只留一條 | — | `previews/data-journal.jpg` |
| `flat-geo` | 扁平幾何（Kurzgesagt 式） | 大膽 | 自然科學、天文、生物細胞 | 尺度穿越、擬人角色、形狀 morph | — | `previews/flat-geo.jpg` |
| `ink-wash` | 水墨 | 安靜 | 國文古詩詞、成語與典故意境、書法與漢字 | 一筆就是一切、留白即物、飛白 | — | `previews/ink-wash.jpg` |
| `iso-infographic` | 等距資訊圖 | 中性·明亮 | 自然科學系統（水循環、發電、消化）、社會領域（產業鏈、城市運作）、科技（網路、資料中心） | 剖面、圖示數量、焦點＋脈絡 | — | `previews/iso-infographic.jpg` |
| `isotype` | 圖形統計（ISOTYPE） | 中性 | 社會領域統計、人口與地理、環境議題 | 逐個堆疊、多出來的變色、重新排列 | — | `previews/isotype.jpg` |
| `living-screencast` | 實機錄屏（重繪） | 中性·明亮 | Google 工具教學、AI 工具操作、教師研習 | 聚光燈定格、會動的地板、縮時加標籤 | — | `previews/living-screencast.jpg` |
| `magazine` | 雜誌撞色編排 | 大膽 | 國語文與文學、議題探究、公民 | 大字砸下、色塊擦出、網格換位 | — | `previews/magazine.jpg` |
| `math-dark` | 深底數學（3Blue1Brown 式） | 大膽·冷靜 | 數學、物理公式、幾何證明 | 符號飛到圖形上、代換、曲線描出 | — | `previews/math-dark.jpg` |
| `neon-circuit` | Neon Circuit（品牌系統） | 大膽 | AI 與程式教學、數位敘事力期刊系列、工具操作教學 | 訊號流動、逐行亮起、節點接通 | — | `previews/neon-circuit.jpg` |
| `picture-book` | 繪本水彩 | 安靜·暖 | 國小、生命教育、生活課程 | 水彩暈開、翻頁、蠟筆塗出 | roughness 1.6 | `previews/picture-book.jpg` |
| `puppet-shadow` | 剪紙皮影 | 大膽·暖 | 歷史、典故、成語故事 | 燈暗換景、關節表演、墨跡浮字 | — | `previews/puppet-shadow.jpg` |
| `sketch-board` | 手繪草圖（Excalidraw 式） | 中性·輕鬆 | 概念圖與心智圖、流程與系統、教師研習簡報 | 先描邊再塗色、Excalidraw 匯入、便利貼補充 | roughness 1.0 | `previews/sketch-board.jpg` |
| `vox-paper` | Vox 紙張拼貼 | 中性 | 媒體素養、科技、社會議題 | 證據甩入、紅筆圈起、螢光筆劃過 | — | `previews/vox-paper.jpg` |
| `whiteboard` | 白板講解 | 中性 | 自然科學、「X 怎麼運作」、數學應用題 | 照筆順寫出、筆帶著鏡頭、磁鐵 | roughness 0.8 | `previews/whiteboard.jpg` |
<!-- catalog:end -->

每張卡的**風格語法**（辨識特徵、不是什麼、原生招式、運鏡詞彙、媒材陷阱、變化空間）見 `style-system.md` §1.2；寫分鏡前先讀選定那張卡的這幾欄。

## 依科目與年級挑候選（方向板用）

| 科目 \ 年級 | 國小 | 國中 | 高中以上／教師研習 |
|---|---|---|---|
| 國語文 | picture-book、chalkboard | chalkboard、ink-wash、magazine | ink-wash、magazine、vox-paper |
| 古詩詞、成語、典故 | puppet-shadow、picture-book | ink-wash、puppet-shadow | ink-wash |
| 華語文（TOCFL） | picture-book、sketch-board | chalkboard、whiteboard | data-journal（語料量化）、sketch-board |
| 數學 | chalkboard、isotype | chalkboard、whiteboard、math-dark | math-dark、data-journal |
| 自然科學 | picture-book、flat-geo | whiteboard、iso-infographic、flat-geo | iso-infographic、data-journal |
| 社會（史地公） | puppet-shadow、isotype | iso-infographic、isotype、vox-paper | vox-paper、data-journal |
| 科技（資訊、生科） | flat-geo、sketch-board | blueprint、sketch-board、living-screencast | living-screencast、neon-circuit |
| 數位工具與 AI 研習 | — | living-screencast | living-screencast、sketch-board、neon-circuit |
| 研究方法與統計 | — | isotype | data-journal、math-dark |

挑三個時要**拉開溫度**：一個安靜、一個中性、一個大膽。三個都落在「米白底＋留白＋一個點綴色」是最常見的失敗。容易混淆的幾組（黑板／白板／手繪草圖、藍圖／等距、水墨／繪本）不要同時放進三張方向板，選它們之間差最多的那一個。

## 方向板輪盤（邏輯 ①）

<!-- roulette:start -->
<!-- 由 scripts/style_catalog.py 產生，請改風格卡再重跑，不要手改 -->
`date +%S`，`秒數 % 16` 對照下表（0 起算）：

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| blueprint | chalkboard | data-journal | flat-geo | ink-wash | iso-infographic | isotype | living-screencast | magazine | math-dark | neon-circuit | picture-book | puppet-shadow | sketch-board | vox-paper | whiteboard |
<!-- roulette:end -->

抽到 `avoid_for` 列有的科目就重抽一次，並說明為什麼重抽。

## 風格 × 構圖是兩件事

風格全片定一次（色彩、字型、材質、動態都從風格卡來），**構圖每幕換**（置中特寫、左右分欄、三欄並排、對角線、滿版字卡）。任兩幕截圖比較：風格應該看不出差別，構圖應該一眼不同。

## 每種風格的實作提醒

- **vox-paper**：截圖要真的截（`scripts/shoot.mjs`），標「來源：網域」；細節見 `vox-style.md`。
- **data-journal**：圖表用 D3 或手寫 SVG，資料綁定後由時間軸驅動轉換；沒有原始數值不畫數值。
- **chalkboard**：開了手寫感圖層（zigzag 填色像粉筆塗）；文字描寫用 `SK.text` 逐字出現。
- **whiteboard**：手寫感圖層＋`tex-whiteboard`（反光與殘影）；一支筆一種意義；鏡頭在白板上移動，不剪接。
- **sketch-board**：手寫感圖層的標準示範；老師可以先在 Excalidraw 畫好，用 `excalidraw_prep.py` 匯入（見 `sketch-layer.md`）。
- **flat-geo**：角色元件化（圓角幾何＋眼睛），前中後景各一層，視差速度 0.35／0.7／1.4。
- **iso-infographic**：投影角度永遠不變；積木三面三明度用 `color-mix` 從一個色相推出；先畫路線或引線，東西才動。
- **blueprint**：線寬只用兩級；標註一律等寬字；拆解沿單一軸線進行。
- **puppet-shadow**：人物結構與關節工具見 `puppet-style.md`。
- **ink-wash**：畫面 60–80% 留白；朱紅只用一次；題字直排放在留白處；轉場用墨暈或手卷橫移。
- **math-dark**：公式用 KaTeX 或 Manim；同一變數全片同色，寫進 `color_semantics`。
- **picture-book**：開了手寫感圖層（粗、彎、像蠟筆）；一頁一句話，字比其他風格大一級。
- **magazine**：標題寫結論；字級只用三級但差距 ≥6 倍；允許大字出血被裁切。
- **isotype**：一個圖示代表固定數量，圖例先出現；絕對不用放大圖示表示數量。
- **living-screencast**：每個按鈕、選單名稱都要對照官方說明文件；介面是重畫的，不放真截圖；游標是使用者、像素小助手是軟體。
- **neon-circuit**：作者品牌；主色只給訊號與主角，不加外發光。

新增或修改風格卡後：`python scripts/style_catalog.py --render`（重寫上面兩張表、重產預覽圖與索引頁）。
