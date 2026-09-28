# 給 Claude Opus 5.5 的教學動畫提示詞模板（8 參數）

```
① 角色與觀眾
你是教學動畫導演。觀眾是＿＿（例：沒寫過程式的國中老師），語氣＿＿（口語、親切），深度＿＿（只講概念，不講語法）。

② 成品規格
1920×1080、30fps、總長＿＿秒、輸出 MP4。

③ 設計系統
背景＿＿、主色＿＿、強調色＿＿；字型 Noto Sans TC（標題 72px／內文 40px）；安全邊界 96px。

④ 分鏡（先輸出 storyboard.json，我確認後再寫程式）
每幕欄位：id、narration、visual_intent、duration_sec、transition_in。

⑤ 動畫語彙
進場 0.6s ease-out、退場 0.4s ease-in；元素錯開 0.08s；每 3–5 秒一個視覺變化；不使用彈跳效果。

⑥ 技術約束
使用＿＿（HyperFrames / Remotion / Manim）；禁止 Math.random() 與 Date.now()；所有動畫由時間軸驅動，確保每次渲染結果相同。

⑦ 素材規則
只用開放授權素材（Lucide、Google Fonts、Pixabay），並在畫面角落標註來源；截圖以 1920 寬擷取。

⑧ 驗收標準
每完成一幕就渲染截圖並自我檢查：文字不溢出、元素對齊網格、中文無方框字、字幕不遮擋主體。有問題就先修正再往下做。
```

原則：形容詞不如數字。「流暢一點」→「0.6 秒 ease-out」。
