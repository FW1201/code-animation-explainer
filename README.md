# code-animation-explainer

> 用「程式碼」拍教學動畫的完整產線 Skill：選模型 → 腳本與分鏡 JSON → 三張方向板選風格 → 風格寫成可檢查的 tokens → 畫面自我修正 → 自然配音 → 字級字幕對齊 → 混音、渲染與出處標註。
> A cross-platform agent skill that guides you from idea to a narrated, captioned, code-rendered explainer video.

很多人在教「用 Claude 寫程式做動畫」，但大多只示範操作。這個 skill 把背後的**製作邏輯**打包起來，讓 Agent 像導演一樣一步步帶你完成，每個階段都有看得到的成果讓你確認。

支援 6 種教學動畫流派（動態圖解、動態文字、資料敘事、互動模擬、3D 空間、粒子生成），可輸出影片或互動教材；中文配音內建讀音檢核，避免 AI 唸錯字。

**風格系統**。風格不再是一段形容詞，而是一張機器可讀的**風格卡**：
- **參數層**：色彩、字型、版面、材質、動態、運鏡、聲音、素材、手寫感。`style_apply.py` 把它套成 `tokens.css／tokens.js`，每一幕只能用 token；`style_lint.py` 抓出寫死的色碼、字型、字級、easing。
- **風格語法**：辨識特徵、易混淆界線、原生招式（附適合的教學內容）、運鏡詞彙、媒材陷阱、變化空間。讓每一幕「像這個風格」，而不只是「用了這個風格的顏色」。
- **素材對齊**：照片、圖示、插畫透過 `assets.js` 自動依風格處理（水墨風照片轉水墨、藍圖風轉線稿、手寫風圖示重畫成手繪線），標籤、數字、引文、強調用同一組 class、外觀跟著風格切換。
- **手寫感**：Rough.js（Excalidraw 背後的手繪引擎）包成 `sketch.js`，seed 固定、可逐筆畫出；老師在 Excalidraw 畫好的圖可以直接匯入做成動畫。

內建 16 種教學風格：

| | | |
|---|---|---|
| Vox 紙張拼貼 `vox-paper` | 資料新聞 `data-journal` | 黑板粉筆 `chalkboard` |
| 白板講解 `whiteboard` | 手繪草圖（Excalidraw 式）`sketch-board` | 扁平幾何 `flat-geo` |
| 等距資訊圖 `iso-infographic` | 藍圖工程 `blueprint` | 剪紙皮影 `puppet-shadow` |
| 水墨 `ink-wash` | 深底數學 `math-dark` | 繪本水彩 `picture-book` |
| 雜誌撞色 `magazine` | 圖形統計 `isotype` | 實機錄屏（重繪）`living-screencast` |
| Neon Circuit `neon-circuit` | 自訂：複製一張卡改 | |

預覽（同一段內容套不同風格）在 [`skills/code-animation-explainer/assets/styles/previews/`](skills/code-animation-explainer/assets/styles/previews/)。

![Vox 紙張拼貼風格板](skills/code-animation-explainer/assets/styles/previews/vox-paper.jpg)

它來自一支實際做完的影片《用程式碼拍動畫：Claude 做教學動畫的底層邏輯》（7 分 48 秒，Vox 解說風），完整腳本、分鏡與字幕放在 [`examples/`](examples/claude-opus-animation-explainer/)。

## 核心觀念

**影片是時間的函數**：每一格畫面只由「現在是第幾秒」決定。語言模型不必會畫圖，只要寫出「第幾秒、哪個東西、移動到哪裡」，交給瀏覽器逐格畫出、再由 ffmpeg 編成影片。

## 產線

| 步驟 | 做什麼 | 對應檔案 |
|---|---|---|
| ① 釐清需求 | 觀眾、長度、輸出方式（影片／互動）、6 種教學動畫流派、選模型 | `SKILL.md`、`references/animation-styles.md` |
| ② 腳本＋分鏡 | 逐字旁白＋`storyboard.json`（含分鏡卡：景別、運鏡、構圖、hero、驗收時間點） | `assets/storyboard.template.json`、`references/storyboard-craft.md` |
| ②-2 方向板 | 三套邏輯各出一張風格板（含素材對齊示範），使用者用眼睛選；選定後產生 `style/` tokens，寫三候選結構與不重複檢查 | `references/direction-boards.md`、`references/style-library.md`、`scripts/style_apply.py`、`assets/styles/` |
| ③ 配音 | 擺脫機械音、試聽選聲、取回字級時間戳；**讀音檢核**（簡體字形送 TTS、雙 Whisper 拼音比對、多版本擇優） | `references/voice-tts.md`、`scripts/tts_elevenlabs.py`、`scripts/verify_vo.py` |
| ④ 素材 | 真實截圖＋出處紀錄、開放授權圖示字型、程式合成配樂（一般／五聲音階琴音） | `scripts/shoot.mjs`、`scripts/bgm.py`、`scripts/bgm_qin.py` |
| ⑤ 畫面 | 只用 tokens 與 `M.*` 動態 helper、hero element 貫穿（不做帶配音的 PPT）、原生招式、運鏡預算、手寫圖層 `SK.*`、素材對齊 `AS.*`、`AT("關鍵字")` 對時、`style_lint` 自我修正 | `references/style-system.md`、`references/motion-language.md`、`references/visual-resources.md`、`references/sketch-layer.md`、`assets/styles/kit.css`、`assets/styles/sketch.js`、`assets/styles/assets.js`、`scripts/style_lint.py`、`scripts/excalidraw_prep.py`、`references/prompt-framework.md`、`references/engines.md` |
| ⑥ 字幕 | 腳本原文＋字級時間、斷句、SRT、閱讀時間檢查 | `scripts/build_captions.py`、`scripts/read_check.py`、`references/captions-sync.md` |
| ⑦ 混音、檢查、渲染 | 配音＋配樂＋音效三軌混音、逐階段截圖、容器溢出與重疊、動畫語義、資料出處、對比度、靜音與音量 | `references/audio-design.md`、`references/review-gates.md`、`references/qa-checklist.md` |
| ⑧ 交付 | MP4＋SRT＋說明欄（提示詞模板＋出處）＋6 維度自評 | `assets/prompt-template.md`、`references/critique-guide.md` |

## 安裝

Skill 本體在 `skills/code-animation-explainer/`，是標準的 `SKILL.md` 格式。

**Claude Code**
```bash
git clone https://github.com/FW1201/code-animation-explainer.git
cp -r code-animation-explainer/skills/code-animation-explainer ~/.claude/skills/
```

**Codex CLI／其他支援 Agent Skills 的工具**：把同一個資料夾放進該工具的 skills 目錄（例如 `~/.codex/skills/`），或用 `npx skills add FW1201/code-animation-explainer`。

**Claude.ai／ChatGPT 等只有對話的平台**：上傳 `SKILL.md` 與 `references/` 當作專案知識，或把 `SKILL.md` 內容貼進自訂指令。沒有本機環境時，skill 會改走「單一 HTML＋GSAP，用瀏覽器開啟並錄影」的路線。

安裝後直接說：「幫我把這篇教材做成 3 分鐘的解說動畫，要有配音和字幕」。

## 需要的工具（依路線）

- 必要：瀏覽器
- 本機渲染：Node.js 22+、ffmpeg；引擎擇一：[HyperFrames](https://github.com/heygen-com/hyperframes)、[Remotion](https://www.remotion.dev/)、[Manim](https://www.manim.community/)
- 配音：[ElevenLabs](https://elevenlabs.io/) API key（免費方案可用，需標註），或其他 TTS
- 讀音檢核：[whisper.cpp](https://github.com/ggml-org/whisper.cpp)（large-v3＋medium 模型）、`pip install pypinyin opencc-python-reimplemented`
- 截圖：`puppeteer-core`＋Chrome；風格板截圖：Playwright（`npx playwright screenshot`）；字型子集：`fonttools`
- 風格工具：只需 Python 3（`style_apply.py`、`style_lint.py`、`style_catalog.py`、`read_check.py`、`excalidraw_prep.py`、`font_subset.py` 無第三方套件）

## 安全與授權原則

- API key 只放 `.env`，不貼進對話、不進版控。
- 網頁截圖僅作教學評論引用並標註來源；遇到機器人驗證不嘗試繞過。
- 發布、上傳、建立外部資源前，Agent 會先摘要並等你確認。

## 致謝

- 風格構築方法（方向板、定格幀構圖、hero element 連續敘事、運鏡預算、色彩推導、中文排印、反 AI 模板感、音訊雙軌、評審量表）改寫自 [huashu-design](https://github.com/alchaincyf/huashu-design)（MIT © alchaincyf 花叔）。
- 風格語法層（辨識特徵、原生招式、運鏡詞彙、媒材陷阱、變化空間）、閱讀時間規則、三候選結構與不重複檢查、聲音導演規則，以及白板、等距資訊圖、水墨、實機錄屏四種風格，改寫自 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)（MIT © LemoLab）。
- 手寫圖層使用 [Rough.js](https://github.com/rough-stuff/rough)（MIT © Preet Shihn，已附在 `assets/vendor/`），手寫草圖風格參考 [Excalidraw](https://excalidraw.com)（MIT）；Excalifont 字型為 [OFL-1.1](https://plus.excalidraw.com/excalifont)。

以上皆調整為臺灣教學影片情境。

## License

MIT © 2026 Kevin Wu (FW1201)。範例影片中的第三方截圖著作權屬原網站所有。
