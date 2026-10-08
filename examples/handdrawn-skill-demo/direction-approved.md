# 方向確認

- 日期：2026-10-08
- 展示版本：
  - A 輪盤＋主題 → sketch-board（手繪草圖，Excalidraw 式）— design-demos/A.png
  - B 標杆 RSA Animate → whiteboard（白板講解）— design-demos/B.png
  - C 課堂感 → chalkboard（黑板粉筆）— design-demos/C.png
- 使用者原話：「A 手繪草圖」
- 定案：sketch-board；hero element＝手繪「風格卡」
- 套用指令：`python ../../skills/code-animation-explainer/scripts/style_apply.py sketch-board --local-fonts --out style/`

## TREATMENT

三個候選結構（從 sketch-board 的 `variation.structures` 改寫）：
1. **問題→嘗試→答案**：先給失敗例子（第五幕變簡報），再拆原因，最後給 skill 的解法。← 採用：看的人先認出自己的痛點，價值最清楚
2. 心智圖：中心「手寫風教學動畫」，四周長出風格卡、種子、Excalidraw、素材對齊四個分支
3. 前後對照：同一支片子先用一句提示詞做一次、再用風格卡做一次

開場：第 1 幕 vs 第 5 幕的縮圖對照（不用「空白畫布上一個問號」這個陳腔濫調）
結尾：拉遠成整張畫布（所有區域變成一張概念圖）＋一句可以直接照抄的提示詞

## 不重複檢查（與風格板範例比較）

| 項目 | 這一支 | 風格板範例 | 一樣？ |
|---|---|---|---|
| 結構 | 問題→嘗試→答案 | 單一概念圖 | 否 |
| 開場 | 兩張縮圖對照＋紅圈 | 標題＋示意圖 | 否 |
| 招牌鏡頭 | 拉遠成整張畫布 | 無 | 否 |
| 運鏡路線 | 六塊區域平移，最後拉遠 | 靜止 | 否 |
| 配樂形狀 | 待配音後定 | — | — |
| 結尾 | 一句提示詞卡 | 無 | 否 |
