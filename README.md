# code-animation-explainer

> 用「程式碼」拍教學動畫的完整產線 Skill：選模型 → 腳本與分鏡 JSON → 8 參數提示詞 → 畫面自我修正 → 自然配音 → 字級字幕對齊 → 渲染與出處標註。
> A cross-platform agent skill that guides you from idea to a narrated, captioned, code-rendered explainer video.

很多人在教「用 Claude 寫程式做動畫」，但大多只示範操作。這個 skill 把背後的**製作邏輯**打包起來，讓 Agent 像導演一樣一步步帶你完成，每個階段都有看得到的成果讓你確認。

支援 6 種教學動畫流派（動態圖解、動態文字、資料敘事、互動模擬、3D 空間、粒子生成），可輸出影片或互動教材；中文配音內建讀音檢核，避免 AI 唸錯字。

它來自一支實際做完的影片《用程式碼拍動畫：Claude 做教學動畫的底層邏輯》（7 分 48 秒，Vox 解說風），完整腳本、分鏡與字幕放在 [`examples/`](examples/claude-opus-animation-explainer/)。

## 核心觀念

**影片是時間的函數**：每一格畫面只由「現在是第幾秒」決定。語言模型不必會畫圖，只要寫出「第幾秒、哪個東西、移動到哪裡」，交給瀏覽器逐格畫出、再由 ffmpeg 編成影片。

## 產線

| 步驟 | 做什麼 | 對應檔案 |
|---|---|---|
| ① 釐清需求 | 觀眾、長度、輸出方式（影片／互動）、6 種教學動畫流派、選模型 | `SKILL.md`、`references/animation-styles.md` |
| ② 腳本＋分鏡 | 逐字旁白＋`storyboard.json` | `assets/storyboard.template.json` |
| ③ 配音 | 擺脫機械音、試聽選聲、取回字級時間戳；**讀音檢核**（簡體字形送 TTS、雙 Whisper 拼音比對、多版本擇優） | `references/voice-tts.md`、`scripts/tts_elevenlabs.py`、`scripts/verify_vo.py` |
| ④ 素材 | 真實截圖＋出處紀錄、開放授權圖示字型、程式合成配樂（一般／五聲音階琴音） | `scripts/shoot.mjs`、`scripts/bgm.py`、`scripts/bgm_qin.py` |
| ⑤ 畫面 | 8 參數提示詞、一幕一檔、`AT("關鍵字")` 對時、自我修正迴圈；視覺風格：Vox 解說風、剪紙／皮影戲風 | `references/prompt-framework.md`、`references/engines.md`、`references/vox-style.md`、`references/puppet-style.md` |
| ⑥ 字幕 | 腳本原文＋字級時間、斷句、SRT | `scripts/build_captions.py`、`references/captions-sync.md` |
| ⑦ 檢查渲染 | 截圖聯絡表、對比度、靜音與音量檢查 | `references/qa-checklist.md` |
| ⑧ 交付 | MP4＋SRT＋說明欄（提示詞模板＋出處） | `assets/prompt-template.md` |

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
- 截圖：`puppeteer-core`＋Chrome；字型子集：`fonttools`

## 安全與授權原則

- API key 只放 `.env`，不貼進對話、不進版控。
- 網頁截圖僅作教學評論引用並標註來源；遇到機器人驗證不嘗試繞過。
- 發布、上傳、建立外部資源前，Agent 會先摘要並等你確認。

## License

MIT © 2026 Kevin Wu (FW1201)。範例影片中的第三方截圖著作權屬原網站所有。
