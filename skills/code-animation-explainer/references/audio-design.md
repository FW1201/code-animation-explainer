# 聲音設計：配音、配樂、音效三軌

聲音也是風格的一部分：風格卡的 `sound` 欄定了配樂類型、音效密度與種類。

## 三軌各司其職

| 軌 | 角色 | 時間尺度 | 和畫面的關係 | 音量（相對） |
|---|---|---|---|---|
| 配音 | 主角，學生要聽懂的內容 | 句 | 動畫卡在字級時間（AT 錨點） | 基準，整片響度 −16 LUFS |
| 配樂（BGM） | 情緒鋪底 | 整段 20–60 秒 | 段落級，換章節可換 | 有人聲時比人聲低 18–22 dB（ducking） |
| 音效（SFX） | 標記關鍵時刻 | 0.2–2 秒 | 對到幀 | 比配樂峰值高 6–8 dB，但不蓋過人聲 |

## 聲音導演規則（聲音是一半的影片）

| 規則 | 做法 |
|---|---|
| 每個看得見的動作都有聲音 | 落定、翻頁、筆畫、點擊、磁鐵、印章；**材質要對**：紙、木、金屬、墨、粉筆聲音都不同。從風格卡 `sound.foley` 挑 |
| 三層 | 環境底（教室、風、城市）＋ 動作音（foley）＋ 配樂；配樂在旁白與關鍵動作音下壓低 |
| 至少兩次真正的靜默 | 放在轉折或答案揭曉前；靜默後的第一個聲音，要是全片最重要的聲音之一 |
| 聲音當轉場（至少兩次） | J-cut：下一幕的聲音提早 0.5 秒進來；L-cut：上一幕的聲音延續過剪接點 |
| 用風格自己的樂器 | 照風格卡 `sound.palette`（水墨＝古琴簫、白板＝鋼琴撥弦、實機錄影＝鋼琴＋8-bit）；**不要每支片都是通用鋼琴弦樂** |
| 節奏要有變化 | 一快一慢交替，有一次明顯加速或減速，有一次長停留讓學生呼吸 |

## 教學片的音效原則

- **密度要低**：0–3 個／10 秒（依風格卡）。教學片是給人聽講的，不是產品發表會。標了一輪 cue 之後，**刪掉 30–50%**，剩下的才有份量。
- **一定要配**：答案揭曉、關鍵結果出現、焦點轉移到新主角、章節轉換。
- **可以配**：元素彈出、圖示堆疊（用輕 tick）、板擦、翻頁。
- **不要配**：每個字出現、每個淡入、背景漂移。
- 音色要配風格：黑板＝粉筆敲板；皮影＝鑼、木魚；藍圖＝機構卡合；繪本＝木琴；Neon Circuit＝節點接通 tick。
- 在 `storyboard.json` 每幕寫 `sfx: [{"at": "AT(\"方向\")", "kind": "chime"}]`，和動畫用同一個錨點。

## 混音參數（ffmpeg）

```bash
# 配樂限在中低頻、音效推到中高頻，彼此不打架；配樂在人聲出現時自動壓低
ffmpeg -i vo.wav -i bgm.wav -i sfx.wav -filter_complex "
 [0]asplit[vo][key];
 [1]lowpass=f=4000,volume=0.45[bgm];
 [2]highpass=f=800[sfx];
 [bgm][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];
 [vo][duck][sfx]amix=inputs=3:duration=first:normalize=0,
 loudnorm=I=-16:TP=-1.5:LRA=11[a]" -map "[a]" mix.wav
```

- `amix` 一定要 `normalize=0`，否則動態被壓平、人聲變小。
- 交付前：`ffmpeg -i out.mp4 -af volumedetect -f null -` 確認 max ≤ −1 dB；`ffprobe` 確認有 AAC 音軌。
- 配樂在章節之間淡入淡出 1–2 秒，片尾和最後一幀一起停，不要拖尾。

## 什麼時候不要配樂

- 數學推導需要專心聽的段落（math-dark、chalkboard 可以整段無配樂）。
- 旁白本身情緒很強的段落（故事高潮），讓聲音留白。

---
聲音導演規則改寫自 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)（MIT © LemoLab）的 DIRECTOR.md §6–7。雙軌制、頻段隔離與 `normalize=0` 參數改寫自 [huashu-design](https://github.com/alchaincyf/huashu-design)（MIT © alchaincyf）的 `audio-design-rules.md`，密度調整為教學片。
