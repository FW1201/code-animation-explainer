# 8 參數提示詞框架

給模型寫動畫程式時（包括你自己要寫下一幕時），把這 8 個參數寫清楚。每一個參數都對應一種常見失敗。

| # | 參數 | 寫什麼 | 沒寫會怎樣 |
|---|---|---|---|
| 1 | 角色與觀眾 | 誰看、語氣、深度 | 用語太難或太幼稚 |
| 2 | 成品規格 | 解析度、fps、總秒數、輸出格式 | 尺寸怪、長度失控 |
| 3 | 設計系統 | **風格卡 id＋`style/` tokens 路徑**；顏色語意；視覺密度標準＋參照標杆＋氛圍層；禁止寫死色碼、字型、字級 | 每幕風格不一致、越後面越偏回模型預設 |
| 4 | 分鏡 JSON | 先輸出 storyboard.json（含分鏡卡八欄、hero_state、check_times），確認後才寫程式 | 結構每次不同、畫面沒構圖 |
| 5 | 動畫語彙 | **流派＋風格卡＋渲染技術＋動作行為＋互動方式**；hero element；只用 `M.in()／M.out()／M.pop()／M.move()／M.draw()`；每幕一個招牌動作；運鏡預算 | 像帶配音的簡報、動作生硬、風格不明 |
| 6 | 技術約束 | 指定引擎；禁用隨機數／即時時間；時間軸驅動 | 每次渲染不同、無法迭代 |
| 7 | 素材規則 | 來源、授權、截圖尺寸、出處標註 | 版權風險、素材模糊 |
| 8 | 驗收標準 | `style_lint.py` 零錯誤；封面測試（每幀 ≤3 活躍元素）；逐階段截圖檢查：元素在容器內、無重疊、不碰標題線、中文字型、字幕遮擋；動畫順序符合概念邏輯；圖上數字都有出處 | 風格漂移、錯誤留到最後、資料被質疑 |

## 可直接複製的模板

```
① 角色與觀眾
你是教學動畫導演。觀眾是＿＿，語氣＿＿，深度＿＿。

② 成品規格
1920×1080、30fps、總長＿＿秒、輸出 MP4。

③ 設計系統
風格卡：＿＿（例：chalkboard，見 style-library.md）。每一幕先載入 style/tokens.css、style/kit.css、style/tokens.js。
顏色只用 var(--…)，並依語意：primary＝＿＿、accent＝＿＿、accent-2＝＿＿。字級只用 .t-h1／.t-h2／.t-h3／.t-body／.t-label；字型只用 var(--font-…)。
視覺密度：每幀要有＿＿（例：紙紋、地面線、截圖卡陰影、hero 的閒置呼吸），任意暫停一幀和參照標杆＿＿放在一起不丟人。
禁止寫死色碼、字型、px 字級；禁止 emoji 圖示、紫藍漸層、霓虹光暈。
素材：照片、圖示、插畫用 AS.apply() 依風格卡 assets 處理；標籤、數字、引文、強調只用 .el-label／.el-num／.el-quote／.el-emph。

④ 分鏡（先輸出 storyboard.json，我確認後再寫程式）
每幕欄位：id、role、task（教學任務）、narration、visual_intent、duration_sec、hero_state、shot、camera、composition（百分比）、key_motion、signature、native_move、transition_out、check_times、on_screen、assets。

⑤ 動畫語彙
流派：＿＿（例：Animated Diagram）；技術：＿＿（例：SVG＋GSAP）；互動：＿＿（影片版可寫「無」）。
hero element：＿＿，從頭到尾都在畫面上，每幕是它的狀態改變；換幕用共享元素或風格卡的轉場，不整頁淡出淡入。
時長與 easing 一律用 M.in()／M.out()／M.pop()／M.move()／M.draw()、M.stagger、M.hold；每幕至少一個風格卡招牌動作；任一幀都有閒置運動（有限次數）。
先讀風格卡的 essence、not、native_moves、camera_vocab、pitfalls：情緒高點用一個原生招式，運鏡只從 camera_vocab 選；手寫線條用 SK.*。
運鏡：15 秒內 ≤4 次，推近 ≥1.25x 且終點是具體錨點，結尾回全景停 0.8 秒。

⑥ 技術約束
使用＿＿（HyperFrames / Remotion / Manim / HTML+GSAP）；禁止 Math.random() 與 Date.now()；所有動畫由暫停的時間軸驅動，渲染結果可重現。

⑦ 素材規則
只用開放授權素材並標註來源；網頁截圖以 1600–1920 寬擷取；記錄擷取日期。

⑧ 驗收標準
每完成一幕：跑 style_lint.py 到零錯誤；在 check_times 截圖並自我檢查：每幀 ≤3 個活躍元素、文字不溢出容器、元素對齊、中文無方框字、字幕不遮擋主體、遮掉文字仍認得出風格。有問題先修正再往下。
```

**原則：形容詞不如數字，數字不如 token。**「動畫要流暢一點」→「0.6 秒 expo.out」→「`M.in()`」；「字大一點」→「標題 84px」→「`.t-h1`」。寫成 token，改風格卡就能全片一起變，每幕也不會各自發明數值。
