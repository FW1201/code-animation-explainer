# 配音：選擇與設定

## 為什麼 AI 配音像機器
語音合成＝文字 → 韻律（prosody：音高、節奏、停頓）→ 聲學。機械感多半來自韻律太平：沒有起伏、該停不停、沒有呼吸。對策：
1. 選能理解語氣的模型
2. 用標點與停頓標籤控制斷句（`[pause]`、逗號、句號）
3. 加情緒提示（疑問、強調、輕聲）
4. 句子寫短、寫口語；數字、英文縮寫寫成唸法（「0.6 秒」可寫「零點六秒」）

## 方案比較（依使用者條件推薦）

| 方案 | 特色 | 何時選 |
|---|---|---|
| ElevenLabs `eleven_v3` | 表現力強、支援情緒標籤、回傳字級時間戳 | 預設首選；免費 10k credits／月（不可商用、需標註「Voice generated with ElevenLabs」） |
| ElevenLabs `eleven_multilingual_v2` | 穩定 | v3 不可用時 |
| MiniMax Speech／Fish Audio | 中文韻律自然、價格低 | 大量中文、預算有限 |
| CosyVoice 2／F5-TTS（開源） | 本機、可零樣本克隆 | 不想上傳資料、有 GPU |
| 使用者自己錄音 | 最自然 | 有時間、有安靜環境；之後用 Whisper 做字級對齊 |

聲音克隆（Instant／Professional Voice Clone）通常需要付費方案與 1–3 分鐘乾淨錄音。

## 用 ElevenLabs 連接器配音（不需要 API key）

使用者在 Claude 設定了 ElevenLabs 連接器（Settings → Connectors）時，直接用連接器，不必建 key、也不必開網路白名單：

1. `creative_list_voices`（`languages: ["zh"]`、`use_cases: ["informative_educational"]`）挑聲音；台灣華語可選 Tiffy（女、年輕、中英夾雜自然）或 IAN（男）。
2. `creative_create_flow` 建一個 flow，每幕一次 `creative_generate_speech`（`generations_count: 1` 省額度；先 `estimate_only: true` 估價，中文約每字 0.1 credit）。送簡體字形（`opencc t2s`）。
3. `creative_get_flow_run_status` 取得每段的 `content_url`（2 小時內有效），`curl` 下載到 `vo/<幕>.mp3`。
4. 連接器不回傳字級時間戳：`python scripts/align_audio.py storyboard.json --vo vo/`（靜音偵測＋字數比例）產生 `vo/<幕>.align.json`，之後的 `build_captions.py`、`AT()` 對時都照舊。
   要逐字精準時，把音檔上傳到同一個 flow 再用 `creative_transcribe_audio`（scribe，每字時間戳）。
5. 真人配音常比估算快：全片太趕或字幕讀不完時，用 `ffmpeg -af atempo=0.92` 放慢 5–10%（音高不變）再對時。

## API key 安全
- 引導使用者到供應商後台自己建立 key，貼進專案 `.env`（例如 `ELEVENLABS_API_KEY=...`），並把 `.env` 加入 `.gitignore`。
- 絕不要求使用者把 key 貼在對話裡；程式只從 `.env` 讀。
- ElevenLabs key 權限：至少 Text to Speech；要瀏覽聲音庫再加 Voices Read。缺權限時 API 會回 `missing_permissions`，照訊息請使用者補勾即可，key 字串不變。

## 讀音檢核（中文）
- 常見錯誤來源：罕用繁體字（澱、鋁、莖、澆、噸…）、破音字、專有名詞、英文縮寫。
- 預防：送 TTS 用簡體字形（`tts_elevenlabs.py --t2s`），字數不變所以時間戳可逐字對回繁體原文。
- 檢核：`verify_vo.py`（兩個 Whisper 模型＋無聲調拼音比對，同音字不算錯）。
- 擇優：`--takes 0.5 1.0` 兩種 stability 各一版，自動保留疑點最少者。stability 高（1.0 Robust）通常唸得比較穩但較平，低（0.5 Natural）較有表情。
- 數字：Whisper 常把中文數字寫成阿拉伯數字，`verify_vo.py` 會先轉回中文（年份逐字、其餘依位數）再比；「兩／二」「着／著」視為相同。
- 整句漏聽：Whisper 偶爾整句沒聽寫出來（常在結尾）。`verify_vo.py` 會依字級時間把該段切出來單獨再聽，重聽沒問題就不算錯。
- 仍有疑點就改寫腳本用詞，或請使用者試聽後決定。

## 省額度流程
1. 腳本定稿前不呼叫 TTS。
2. 用同一段 20–30 秒旁白生成 2–3 個聲音試聽 → 使用者選定。
3. 逐幕生成（`scripts/tts_elevenlabs.py`），只重錄有問題的那一幕。
4. 1 個中文字 ≈ 1 credit；估算：總字數 × 版本數 ×（1 + 重錄比例）。3 分鐘約 600 字，單版約 600 credits，雙版擇優約 1,200。

## 聲音類型與語速（eleven_v3 實測，中文）
| 聲音 | 類型 | 語速 | 適合 |
|---|---|---|---|
| Lily `pFZP5JQG7iQjIQuC4Bku` | 清亮女聲 | 約 3.3 字／秒 | 知識講解、科普 |
| Bill `pqHfZKP75CvOlQylNhV4` | 年長、沉穩說書男聲 | 約 2.7 字／秒 | 歷史、故事、典故 |
| George `JBFqnCBsd6RMkjVDRZzb` | 溫暖說故事 | 試聽再測 | 故事 |
語速因聲音差很多，腳本長度要依選定聲音校正；`--sample` 會印出實測語速。說書類旁白可把每幕前後留白拉長（例：前 0.6 秒、後 0.9 秒），節奏比較從容。

## 預設中文聲音
ElevenLabs 內建聲音多為英文母語，唸中文可能帶口音；先試聽再決定，或到 Voice Library 篩選 Chinese 母語聲音（需 Voices Read 權限）。
