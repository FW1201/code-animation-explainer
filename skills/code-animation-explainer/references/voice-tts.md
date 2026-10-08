# 配音：選擇、設定與讀音校正

## 為什麼 AI 配音像機器
語音合成＝文字 → 韻律（prosody：音高、節奏、停頓）→ 聲學。機械感多半來自韻律太平：沒有起伏、該停不停、沒有呼吸。對策：
1. 選能理解語氣的模型（中文用 `eleven_v3`）
2. 用標點與停頓控制斷句（逗號、句號、`[pause]`）
3. 句子寫短、寫口語；數字、英文縮寫寫成唸法（「0.6 秒」可寫「零點六秒」）

## 方案比較

| 方案 | 特色 | 何時選 |
|---|---|---|
| ElevenLabs `eleven_v3` | 中文聲調最穩、表現力強 | **中文預設**；免費約 10k credits／月（不可商用、需標註「Voice generated with ElevenLabs」） |
| ElevenLabs `eleven_multilingual_v2` | 穩定、便宜一點 | 英文旁白；**中文不建議**（實測一支 9 幕影片唸錯 17 個字：猜→踩、手→受、黑板→黑斑、字幕→字母…） |
| MiniMax Speech／Fish Audio | 中文韻律自然、價格低 | 大量中文、預算有限 |
| CosyVoice 2／F5-TTS（開源） | 本機、可零樣本克隆 | 不想上傳資料、有 GPU |
| 使用者自己錄音 | 最自然 | 有時間、有安靜環境；用 `align_audio.py --asr` 對時 |

## 接上 ElevenLabs：兩條路

先問使用者用哪一種 Claude，再挑一條路。**一般使用者優先走 A**。

### A. 連接器（不需要 API key，推薦）
適用：Claude 桌面版、claude.ai、Claude Code（雲端／桌面）。使用者只要做一次：
1. 打開 Claude →「設定 Settings」→「連接器 Connectors」→ 找到 **ElevenLabs** →「連接 Connect」，用 ElevenLabs 帳號登入授權（沒有帳號就免費註冊一個）。
2. 回到對話說「好了」。之後配音全部由 Agent 透過連接器完成。

Agent 端流程：
1. `creative_list_voices`（`languages: ["zh"]`）挑聲音；台灣華語可選 Tiffy（女、年輕、中英夾雜自然）或 IAN（男）。讓使用者試聽 2–3 個再決定。
2. `creative_create_flow` 建一個 flow，整支影片都放同一個 flow。
3. 每幕一次 `creative_generate_speech`：`model_id: "eleven_v3"`、送**繁體原文**（或 storyboard 的 `tts` 欄位，見下方）。第一次先 `estimate_only: true` 估價（中文約每字 1 credit）。
   - 一般幕 `generations_count: 1`；曾經唸錯的幕用 `2`，一次拿兩版挑。
   - **不要為了重試重複呼叫同一個生成**（會重複扣點）；要另一版就明確再生成一次。
4. `creative_get_flow_run_status` 取得 `content_url`（2 小時內有效），`curl` 下載到 `vo/raw/<幕>.mp3`。
5. 轉檔：`ffmpeg -i vo/raw/s0.mp3 -af atempo=0.95 -ar 44100 -ac 1 vo/s0.wav`（v3 偏快，放慢 5% 字幕比較讀得完；音高不變）。
6. **讀音檢核與校正**（下一節）→ 全部通過才往下。
7. 對時：連接器不回傳字級時間戳，用 `python scripts/align_audio.py storyboard.json --vo vo/ --asr`（離線辨識取得每個字實際被唸出的時間，誤差約 0.05 秒）。之後 `build_captions.py`、`AT()` 照舊。

### B. API key（給熟悉終端機的使用者）
1. 引導使用者到 ElevenLabs 後台自己建立 key（權限至少勾 Text to Speech；要瀏覽聲音庫再加 Voices Read），貼進專案 `.env`：`ELEVENLABS_API_KEY=...`，並確認 `.env` 在 `.gitignore`。
2. **絕不要求使用者把 key 貼在對話裡**；程式只從 `.env` 讀。缺權限時 API 回 `missing_permissions`，請使用者補勾即可，key 不變。
3. `python scripts/tts_elevenlabs.py storyboard.json --voice <id> --model eleven_v3`：逐幕生成並取回字級時間戳（會優先送 `tts` 欄位）。`--takes 0.5 1.0` 每幕兩種 stability 各一版。
4. 一樣跑下一節的讀音檢核。

## 讀音校正（中文必做）

TTS 會安靜地唸錯字，而且**多數錯在聲調**——語音辨識看不出來。

### 為什麼一般語音辨識抓不到
ElevenLabs scribe、Whisper 都有很強的語言模型：配音唸成「重新踩（cǎi）」，它會依上下文寫成「重新猜」。拿它們的文字稿比對，永遠顯示「正確」。

`scripts/pron_check.py` 改用**沒有語言模型的 CTC 辨識**（sherpa-onnx 的 zipformer-ctc-zh 與 SenseVoice，離線執行）：它逐格輸出聽到的音，唸成 cǎi 就寫「踩」、唸成 shòu 就寫「受」。再把聽到的字與旁白都轉成**帶聲調拼音**逐字比對：
- 兩個模型都聽成別的音 → **讀錯**（要處理）
- 只有一個模型聽錯 → **待確認**（請使用者試聽）
- 平翹舌不分（zh/z、ch/c、sh/s）是台灣口音常態，不算錯；多音字只要符合任一讀音就不算錯

```bash
pip install sherpa-onnx pypinyin          # 第一次執行會從 GitHub 下載模型（約 400 MB）
python scripts/pron_check.py storyboard.json --vo vo/          # 全片
python scripts/pron_check.py storyboard.json --vo vo/ --only s0,s7
python scripts/pron_check.py vo/s0.mp3 "請 AI 做一支手繪風的教學動畫"   # 單一音檔
```
有「讀錯」時結束碼為 1，可放進出片前檢查。

### 校正流程（由輕到重，每一步做完都重跑 pron_check）
1. **預防**（生成前）
   - 中文用 `eleven_v3`，送**繁體原文**。
   - 避開多音字：「長什麼樣子」→「是什麼樣子」、「兩行指令」→「兩條指令」。
   - 關鍵詞不要放在音檔第一個字：v3 開頭常含糊（「習慣用…」整段聽不清），加個引導詞「如果你習慣用…」。
2. **重錄同一句**：隨機性造成的錯（「卡」→「塔」、「真人」漏掉），用 `generations_count: 2` 再錄兩版，挑通過的。
3. **同音字繞過**：同一個詞每一版都錯，就是模型對這個詞的發音有偏差（實測「手繪」連續 5 版都唸成「手衛」、「食譜」唸成「食副」）。在 storyboard 加 `tts` 欄位，只改送去配音的文字，字幕仍用 `narration`：
   ```json
   { "id": "s0",
     "narration": "請 AI 做一支手繪風的教學動畫…",
     "tts":       "請 AI 做一支手慧風的教學動畫…" }
   ```
   選字原則：同音同調、單一讀音的常用字（繪→慧、譜→普）；字數不變，時間戳才能逐字對回。`pron_check.py` 一律拿 `narration` 比對，觀眾聽到的要和字幕一致。
4. **改寫句子**：以上都不行，就換一種說法，並同步改 `narration`、`script.md`、畫面上用到的關鍵字（`AT("關鍵字")`）。
5. **回報**：告訴使用者每幕結果、用過的同音字替換，以及剩下的「待確認」位置（附秒數），請他試聽。

### 實測案例（handdrawn-skill-demo，聲音 Tiffy）
| 原句 | v2＋簡體 聽到 | 處理後 |
|---|---|---|
| 重新**猜** | 重新**踩** | v3＋繁體 ✓ |
| 像**手**畫的 | **享受**畫的 | v3＋「像是用手畫的」✓ |
| **幾幕** | **繼母** | v3 ✓ |
| 簡**報** | 簡**寶** | v3 ✓ |
| 字**幕** | 字**母** | v3 ✓ |
| 來得**及讀** | 來的**基督** | v3 ✓ |
| 手**繪**風 | 手**回**風 | v3 仍是「手**衛**」→ `tts` 改「手慧風」✓ |
| 食**譜** | 食**是** | v3 仍是「食**副**」→ `tts` 改「食普」✓ |
全片從 17 個讀錯降到 0 個；總花費約 1,300 credits（含試錯）。

## 省額度流程
1. 腳本定稿前不呼叫 TTS。
2. 用同一段 20–30 秒旁白試聽 2–3 個聲音 → 使用者選定。
3. 逐幕生成，**只重錄有問題的那一幕**。
4. 估算：總字數 ×（1 + 重錄比例 0.5）。3 分鐘約 600 字，約 900 credits。

## 聲音類型與語速（eleven_v3 實測，中文）
| 聲音 | 類型 | 語速 | 適合 |
|---|---|---|---|
| Tiffy `1AKkSX7KMPHIWuz76m0n` | 台灣年輕女聲、中英夾雜自然 | 約 4.5 字／秒（建議 atempo 0.95） | 科技、教學示範 |
| Lily `pFZP5JQG7iQjIQuC4Bku` | 清亮女聲 | 約 3.3 字／秒 | 知識講解、科普 |
| Bill `pqHfZKP75CvOlQylNhV4` | 年長、沉穩說書男聲 | 約 2.7 字／秒 | 歷史、故事、典故 |
語速因聲音差很多，腳本長度要依選定聲音校正。內建聲音多為英文母語，唸中文可能帶口音；先試聽，或到 Voice Library 篩選中文母語聲音。

## 舊工具
`scripts/verify_vo.py`（兩個 Whisper 模型、無聲調拼音比對）能抓到整個字唸錯（澱→沼、鋁→雲），但**抓不到聲調錯誤**，也需要另外安裝 whisper.cpp。新專案改用 `pron_check.py`；`--t2s`（送簡體字形）只在使用 multilingual_v2 遇到罕用繁體字時才考慮。
