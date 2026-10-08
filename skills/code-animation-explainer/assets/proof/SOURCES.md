# 校樣素材來源（style_proof.py 用來測試「外部素材是否跟風格一致」）

這些是**真實的外部素材**，刻意不是程式畫的：照片有真實的光影與雜色、圖示是別人的線寬、插畫是別人的配色。校樣頁把它們丟進每一種風格，看處理後是否和程式畫的物件放在一起不突兀。

| 檔案 | 內容 | 來源 | 授權 |
|---|---|---|---|
| `astronaut.jpg` | 太空人 Eileen Collins 人像（顏色多、有膚色） | NASA，經 scikit-image `skimage.data.astronaut` | 公有領域 |
| `coffee.jpg` | 咖啡杯（暖色、木紋） | Rachel Michetti，經 `skimage.data.coffee` | CC0 |
| `rocket.jpg` | 夜間發射台上的火箭（低光、點光源） | SpaceX，經 `skimage.data.rocket` | 公有領域 |
| `cat.jpg` | 貓的特寫（毛髮細節） | Stefan van der Walt，經 `skimage.data.chelsea` | CC0 |
| `icon-*.svg` | rocket、leaf、lightbulb、book-open | [Lucide](https://lucide.dev) 0.460.0 | ISC |
| `illus-*.svg` | idea、globe、graduation-cap（多色扁平插畫） | [Flat Color Icons](https://github.com/icons8/flat-color-icons)，經 `@iconify-json/flat-color-icons` 1.2.1 | MIT |

照片已縮到 800px 寬。換成自己的素材測試：`python scripts/style_proof.py sketch-board --photos a.jpg b.jpg`。
