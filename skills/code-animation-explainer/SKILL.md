---
name: code-animation-explainer
description: 引導使用者（特別是老師）用「程式碼」製作教學／解說動畫影片或互動教材（動態圖解、動態文字、資料敘事、互動模擬、3D、粒子生成；HTML+GSAP、HyperFrames、Remotion、Manim、D3、p5.js、Three.js 皆可），從選模型、寫腳本與分鏡 JSON、三張方向板選風格、把風格寫成可檢查的設計 tokens（16 種教學風格卡：Vox 拼貼、資料新聞、黑板粉筆、白板講解、手繪草圖（Excalidraw 式）、扁平幾何、等距資訊圖、藍圖、皮影、水墨、3B1B 深底數學、繪本、雜誌、ISOTYPE、實機錄屏、Neon Circuit；照片圖示文字自動對齊風格）、生成畫面並自我修正，到自然配音（ElevenLabs 等 TTS）與讀音檢核、字級時間戳字幕對齊、配樂音效混音、渲染 MP4 與標註出處的完整產線。只要使用者提到「用程式碼做動畫」「用 Claude／AI 做教學影片」「Vox 風解說動畫」「程式動畫」「code-based video」「explainer animation」「幫我做一支解說影片」「動畫風格不明顯」「風格跑掉」「畫面很像 PPT」「素材跟風格不搭」「手寫感」「Excalidraw」「配音太機械」「AI 配音唸錯字」「字幕要對齊配音」「互動教材」「動態圖解」「資料動畫」，或想把一篇文章、教材、概念變成有配音字幕的動畫影片，就應該使用這個 skill，即使使用者沒有明說要用程式碼。
---

# 程式動畫解說影片製作（Code Animation Explainer）

這個 skill 把「用程式碼拍教學動畫」拆成一條可重複的產線。核心觀念：**影片是時間的函數**——每一格畫面只由「現在是第幾秒」決定，所以語言模型不必會畫圖，只要寫出「第幾秒、哪個東西、移動到哪裡」，交給瀏覽器（或渲染器）逐格畫出、再用 ffmpeg 編成影片。

第二個核心觀念：**風格是一組會被程式讀取、被檢查的參數，不是一段形容詞。**風格寫在風格卡裡（色彩、字型、版面、材質、動態、運鏡、聲音、素材、手寫感等參數層，加上辨識特徵、原生招式、運鏡詞彙、媒材陷阱等風格語法），套成 `tokens.css／tokens.js`，每一幕只能用 token，`style_lint.py` 把關。這樣風格才不會越做越偏回模型預設。

你的角色是**導演兼製作**：每個階段交付一個看得到的成果讓使用者確認，而不是一口氣做完才給結果。

## 任務路由（先看這張表）

| 訊號 | 走法 |
|---|---|
| 新影片（MP4） | 完整走 ①–⑧ |
| 互動教材（HTML） | ①②②-2④⑤；互動規則見 `references/animation-styles.md` |
| 抽象／學術主題（研究方法、統計、理論） | ① 先給決策選項（`references/review-gates.md` 關卡 0）；風格候選偏 data-journal、math-dark、isotype |
| 歷史、典故、民俗 | 風格候選含 puppet-shadow（`references/puppet-style.md`） |
| 「照片／圖示／標籤跟畫面風格不搭」 | `references/visual-resources.md` §2：風格卡 `assets`＋`detail` 欄、`AS.*`、`.obj`、`.el-*`；用 `scripts/style_proof.py` 拿真實素材做校樣截圖比對 |
| 「要手寫感」「用 Excalidraw 畫的圖做動畫」 | `references/sketch-layer.md`：Rough.js 手寫圖層、`excalidraw_prep.py` |
| 「風格不明顯」「越後面越不像」「很像 PPT」 | 直接做 `references/style-system.md` §2（套 tokens＋lint）與 `references/motion-language.md` §1（hero 貫穿） |
| 「幫我看看／評分」 | `references/critique-guide.md` |
| 使用者說「直接產出」 | 自主模式：不逐步詢問、方向板自己選一張，但 gate 檔照寫，完成後一次回報「做了哪些選擇、為什麼、怎麼改」 |
| 只有對話介面（網頁版聊天） | 見文末「平台適配」 |

## 核心原則 #0：事實先查證

涉及具體產品、版本、年份、統計數字、近年事件時，**先 WebSearch 查證再寫**，不憑記憶斷言。查到的事實與出處寫進專案的 `facts.md`（數字 → 出處 → 擷取日期）。查不到就問使用者，或在畫面上只畫方向、不編數字。

## 產線總覽

```
① 釐清需求 → ② 腳本＋分鏡 JSON → ②-2 方向板 ×3，選風格、產生 tokens → ③ 配音＋讀音檢核 → ④ 素材
   → ⑤ 畫面（分鏡卡、hero 貫穿、只用 tokens、自我修正）→ ⑥ 字幕 → ⑦ 混音＋檢查＋渲染 → ⑧ 交付（＋評審）
```

每一步都有交付物與使用者確認點。使用者說「直接做」時可以合併確認點，但**方向板選擇**與**第一個樣片**仍要停一下：這兩件事最主觀、返工成本最高。

## ① 釐清需求（先問，不要猜）

一次問完、給建議選項：
- **主題與觀眾**：給誰看？（國小、國中、高中、老師、研究生）→ 決定語氣、深淺與字級
- **長度與比例**：預設 16:9、1920×1080、30fps；短影音用 9:16
- **輸出方式與動畫流派**：影片、互動教材，或兩者？依內容推薦流派（流程→動態圖解、字詞→動態文字、數據→資料敘事、變因→互動模擬、立體→3D、抽象過程→粒子生成），見 `references/animation-styles.md`。對老師用「你想讓學生看到什麼變化」來問，不問技術名詞。
- **風格參考**：有沒有品牌、學校識別、喜歡的作品？有就從那裡長出風格；沒有就在 ②-2 用方向板給他看。**不要只問「要什麼風格」**，沒看到畫面的選擇是無效的。
- **配音**：要不要配音？預算？要不要克隆自己的聲音？（見 ③）
- **環境**：平台（Claude Code、Codex、Cursor、網頁版）、有沒有 Node／Python／ffmpeg。

**選模型**（使用者問到時說明）：整支影片從零規劃、多場景、需要自我檢查 → 最強的模型；日常微調 → 中型模型；批次小事 → 小模型。動畫越複雜、迭代越多，越往大模型靠。

## ② 腳本＋分鏡 JSON（最重要的穩定器）

不要直接寫動畫程式。先產出：
1. `script.md`：逐字旁白，每幕附〔畫面〕說明。口語、短句。估時長用**所選聲音的實測語速**（ElevenLabs Lily 約 3.3 字／秒、Bill 約 2.7 字／秒），先用 3 字／秒粗估，選定聲音後以 `--sample` 印出的語速校正。
2. `storyboard.json`：照 `assets/storyboard.template.json`。頂層有 `style`、`hero_elements`；每幕除了 `id／narration／visual_intent／duration_sec` 之外，還有分鏡卡欄位 `role／hero_state／shot／camera／composition／key_motion／signature／transition_out／check_times／sfx`。

分鏡卡怎麼寫（封面測試、景別、教學能量骨架、轉場選型、驗收時間點、**教學資訊出場順序**、**閱讀時間**）見 `references/storyboard-craft.md`。**先擺定格幀，再編排動作。**每幕寫 `task`（定義／步驟／比較／因果／分類／問題→解答），出場順序照它；要學生讀的字寫進 `on_screen`；要用的照片圖示寫進 `assets`。

錄音前過內容關卡（`references/review-gates.md` 關卡 1）：每個數字對回 `facts.md`；**沒有原始數值就只畫方向，不編數字**；自己加的詮釋單獨標出並驗算；多案例先加「案例關係地圖」幕。**讓使用者確認腳本後才花錢生成配音。**

## ②-2 方向板：用眼睛選風格，產生 tokens

細節見 `references/direction-boards.md`，風格庫見 `references/style-library.md`。

1. 依科目與年級從風格庫挑候選，用三套邏輯各做一張：① 秒數輪盤抽內建風格卡 ② 標杆遷移（3Blue1Brown、Kurzgesagt、The Pudding…，先查證）③ 「預算無上限會請誰做」→ 寫一張新風格卡。三張**溫度拉開、版面骨架不同**。
2. 用真實腳本內容產生風格板並截圖：
   ```bash
   python scripts/style_apply.py chalkboard --sample sample.json --out design-demos/A
   npx playwright screenshot --viewport-size=1920,1080 --wait-for-timeout=2000 file://$PWD/design-demos/A/board.html design-demos/A.png
   ```
3. 三張一起給使用者看，**停下等選擇**。可混搭：`--colors-from`、`--type-from`、`--set 路徑=值`。
4. 選定後寫 `direction-approved.md`（三張路徑＋使用者原話＋套用指令），並產生專案的 `style/`：
   ```bash
   python scripts/style_apply.py data-journal --colors-from chalkboard --out style/
   ```
   `style_apply.py` 會列出對比度不足的顏色；處理掉再往下。
5. **讀選定風格卡的語法**（`essence`、`not`、`native_moves`、`camera_vocab`、`pitfalls`、`assets`），並在 `direction-approved.md` 寫 TREATMENT：三個候選結構、選哪一個、和上一支同風格影片的 6 項不重複檢查（`references/direction-boards.md`）。

## ③ 配音：擺脫機械音

先釐清：**Whisper 是語音辨識（STT），不是配音**。機械感主要來自韻律（prosody）太平。選擇與設定見 `references/voice-tts.md`。

預設建議：ElevenLabs `eleven_v3`（支援 `[pause]`、`[breathes]` 等標籤），免費方案約 10k credits／月、不可商用、需標註。流程：
1. 引導使用者自己申請 API key 並寫入 `.env`（**絕不請使用者把 key 貼進對話**）。
2. 用同一段開場旁白生成 2–3 個聲音試聽（`--sample "…" --voice id1 id2 id3`），讓使用者挑。聲音類型也是風格的一部分：知識講解用清亮聲音、故事與皮影用沉穩說書聲。
3. 定案後用 `scripts/tts_elevenlabs.py` 逐幕生成，**同時取回字級時間戳**，這是字幕與動畫對時的來源。中文加 `--t2s`。

### ③-2 讀音檢核（中文必做）

TTS 會安靜地唸錯字（「澱粉」唸成「沼粉」、「鋁箔」唸成「雲薄」）。每一幕配音都要檢核後才進入畫面製作：
1. **預防**：`--t2s` 送簡體字形（字數不變，時間戳逐字對回繁體）。破音字、專有名詞必要時改寫成不會誤讀的說法。
2. **檢核**：`scripts/verify_vo.py` 用兩個 Whisper 模型聽寫、轉無聲調拼音比對；同音字不算錯，兩個模型都聽成別的音才標「疑似唸錯」。
3. **擇優**：`--takes 0.5 1.0` 每幕兩種 stability 各一版，保留疑點最少的。
4. **額度與術語**：錄音前估算用量；中途 401／額度錯誤就停下請使用者處理。術語放進 `verify_vo.py --prompt`。
5. **回報**：每幕檢核結果與剩餘疑點，請使用者試聽標記處。

## ④ 素材與真實截圖

真實截圖讓觀眾相信「這是真的可以做到」。用 `scripts/shoot.mjs` 批次擷取；遇到 cookie／機器人驗證頁就換來源或放棄，不要嘗試繞過。
- 開放授權素材來源（圖示、插畫、故宮 Open Data、Wikimedia、開放資料）與元件庫用法見 `references/visual-resources.md`。
- **素材要跟風格對齊**：照片、圖示、插畫用 `data-as` 標記後 `AS.apply()`，依風格卡 `assets` 自動套濾鏡、外框、線寬、換色（水墨風照片轉水墨、藍圖風轉線稿、手寫風圖示重畫成手繪線）；風格說不用照片就不用。真實截圖是證據，保留原貌、標來源。
- 老師自己在 Excalidraw 畫的圖：`scripts/excalidraw_prep.py` 轉成可逐步畫出的動畫資料（`references/sketch-layer.md`）。
- 內容必需的圖一定用真圖；取不到就放**誠實的佔位**並告訴使用者，不要畫假的。
- 記錄每個素材的來源網址與擷取日期，放進 `facts.md`、片尾出處頁與說明欄。
- 背景音樂用 `scripts/bgm.py`／`bgm_qin.py` 程式合成，沒有授權問題。

## ⑤ 畫面：逐幕產出＋自我修正迴圈

引擎選擇見 `references/engines.md`（有本機環境時推薦 HyperFrames 或 Remotion；純數學用 Manim；最低門檻是單一 HTML＋GSAP）。

**鐵律：不要做成帶配音的 PowerPoint**（`references/motion-language.md`）
1. 選 1–2 個 **hero element** 從頭貫穿到尾，每一幕是它的狀態改變。
2. 換幕用共享元素或風格卡轉場，不整頁淡出淡入。
3. 任一幀都有運動（閒置呼吸、Ken Burns），運動有限次數。
4. easing、錯開、關鍵結果前停留是底線。

**風格規則**（`references/style-system.md` §2.3）：每幕先載入 `style/` 裡的 `tokens.css`、`kit.css`、`tokens.js`、`rough.js`、`sketch.js`、`assets.js`；顏色只用 `var(--…)` 並照語意；字級只用 `.t-h1…`；時長與 easing 只用 `M.*`；每幕至少一個招牌動作，情緒高點放一個風格卡的原生招式；運鏡只從 `camera_vocab` 選；手寫線條用 `SK.*`；外部素材經 `AS.*`、程式畫的方框加 `.obj`（質感來自風格卡 `detail`）；標籤、數字、引文、強調只用 `.el-*`。元件（截圖卡、螢光筆、手繪線、呼吸字卡…）用 `kit.css`，不要每幕重寫。

做法：
- 一幕一檔（樣式／標記／時間軸），用建置腳本組裝；id 加幕號前綴。
- 動畫時間**錨定在配音字級時間**：`AT("關鍵字")`，建置時換成秒數。
- 決定性：禁止 `Math.random()`、`Date.now()`、無限重複；初始狀態用 `gsap.set` 再 `to`。
- **自我修正迴圈**：寫完一幕 → `style_lint.py` 零錯誤 → 在 `check_times` 截圖 → 自己看圖（封面測試：≤3 個活躍元素）→ 修正 → 再截圖。**先做一幕樣片給使用者確認，再量產其他幕。**
- 動畫順序符合概念邏輯：階層由上而下、流程依步驟、因果先因後果。寫完用一句話說出「這個動畫在教什麼」。

## ⑥ 字幕對齊

`scripts/build_captions.py` 把字級時間戳轉成字幕：以腳本原文為準、在句讀處斷句、每行約 16 字、最多 2 行，說完多留 0.6 秒，輸出燒錄 cue 與 `captions.srt`。再跑 `scripts/read_check.py captions/cues.json --storyboard storyboard.json --timeline captions/timeline.json` 檢查字幕與字卡的閱讀時間。字幕樣式屬於風格（風格卡 `caption.world`：題跋、地圖標籤、粉筆槽字幕條…）。字幕條用 `kit.css` 的 `.caption-bar`（樣式來自風格卡 `caption`），關鍵詞用 `.kw` 變色。細節見 `references/captions-sync.md`。

## ⑦ 混音、檢查與渲染

- **混音**：配音＋配樂＋音效三軌，配樂在人聲下壓低、頻段隔離、`amix normalize=0`、loudnorm −16 LUFS；音效密度依風格卡。見 `references/audio-design.md`。
- `python scripts/style_lint.py style/tokens.json compositions/` 零錯誤。
- 字型：`python scripts/font_subset.py --style style/tokens.json --text script.md storyboard.json compositions/ --out fonts/`，只下載用到的字，渲染時不連網。
- 聲音導演：每個動作有材質對的聲音、至少兩次靜默、用風格自己的樂器（`references/audio-design.md`）。
- 引擎檢查（HyperFrames：`npx hyperframes check`），修到零錯誤。單一 HTML＋GSAP 路線用 `node scripts/render_seek.mjs page.html renders/stills --at 秒,秒` 截圖、去掉 `--at` 渲染成 MP4（`references/engines.md`）。
- **重疊零容忍**：`node scripts/render_seek.mjs page.html - --scan 0.25` 掃全片，文字疊文字、物件蓋字、線穿字都要修到 0 個。
- **逐階段截圖**：`build_captions.py` 輸出的 `snapshot-times.txt`（每句結束前、每幕結束前）做聯絡表，照 `references/review-gates.md` 關卡 3 與 `references/qa-checklist.md` 逐張檢查。
- 渲染後用 ffprobe 驗證長度、音軌、解析度；silencedetect 確認沒有意外靜音；volumedetect 確認不破音。
- 配音中途重錄過，重跑讀音檢核與建置（AT 錨點會自動跟上）。

## ⑧ 交付

版本管理：新版做好先保留舊版方便對照，使用者確認後再移到垃圾桶；每次交付逐點對照使用者的修改，附「舊時間點 → 新時間點」。

交給使用者：MP4（或互動 HTML）、`captions.srt`、`影片說明欄.txt`（提示詞模板＋全部出處＋TTS 標註）、讀音檢核結果與剩餘疑點、使用的風格卡與 `direction-approved.md`。回報實際片長、與計劃不同之處、怎麼修改（改風格卡哪個參數、改哪個檔、重新渲染要多久）。可附一份 `references/critique-guide.md` 格式的自評。

## Gate 檔：檔案不在＝這一步沒做

| 檔案 | 對應步驟 | 何時必須存在 |
|---|---|---|
| `facts.md` | 核心原則 #0、關卡 1 | 腳本裡有任何數字、年份、產品、引用時 |
| `storyboard.json`（含分鏡卡欄位） | ② | 寫任何動畫程式之前 |
| `direction-approved.md` | ②-2 | 產生 `style/` 與寫第一幕之前 |
| `style/tokens.json` | ②-2 | 寫第一幕之前；`style_lint.py` 的依據 |

使用者說「繼續」是授權進入下一步，不是跳過 gate。使用者明說跳過時，把原話寫進對應的 gate 檔。

## 平台適配

- **有本機終端（Claude Code、Codex CLI、Cursor）**：完整走 ①–⑧。能開 subagent 時三張方向板可並行做；不能時依序做，每張只讀同一份 spec、不參考前一張。
- **能力或上下文吃緊**：方向板降為「1 張主版＋2 張只換配色字型的變體」（`--colors-from`、`--type-from`）並告訴使用者；references 只讀當前步驟那一份；確認點改成在產出裡列「假設清單」。降級犧牲的是選項數量，不是風格 tokens、讀音檢核與資料正確性。
- **只有對話（網頁版聊天）**：產出單一 HTML＋GSAP 檔，把 `tokens.css`、`kit.css`、`tokens.js` 內嵌進去；使用者用瀏覽器開啟、螢幕錄影輸出；配音與字幕改為給可貼上的 TTS 文字與 SRT。
- 無論哪個平台：寫入外部服務（上傳、發布、建立 repo）前先摘要並等使用者確認。

## References 路由

| 什麼時候 | 讀 |
|---|---|
| 選風格、套 tokens、自訂風格、中文字型、反 AI 模板感 | `references/style-system.md` |
| 16 種風格總覽、依科目年級挑候選、輪盤 | `references/style-library.md`（參數在 `assets/styles/*.json`，預覽在 `assets/styles/previews/`；改卡後跑 `scripts/style_catalog.py --render`） |
| 手寫感圖層、Excalidraw 匯入 | `references/sketch-layer.md` |
| 方向板流程與三套邏輯 | `references/direction-boards.md` |
| 分鏡卡、構圖、景別、教學能量骨架、轉場 | `references/storyboard-craft.md` |
| hero 貫穿、運動語法、運鏡預算、逐格渲染陷阱 | `references/motion-language.md` |
| 元件庫 `kit.css`、素材對齊（`AS.*`、`.el-*`）、開放授權素材 | `references/visual-resources.md` |
| 動畫流派與互動教材 | `references/animation-styles.md` |
| 引擎選擇與 HyperFrames 要點 | `references/engines.md` |
| 8 參數提示詞 | `references/prompt-framework.md`、`assets/prompt-template.md` |
| 配音、讀音檢核 | `references/voice-tts.md` |
| 字幕與音畫同步 | `references/captions-sync.md` |
| 配樂與音效混音 | `references/audio-design.md` |
| Vox 風、皮影風的元素細節 | `references/vox-style.md`、`references/puppet-style.md` |
| 審核關卡、驗收清單 | `references/review-gates.md`、`references/qa-checklist.md` |
| 評審打分 | `references/critique-guide.md` |
