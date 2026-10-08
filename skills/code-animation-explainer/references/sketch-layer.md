# 手寫感圖層：Rough.js 與 Excalidraw

手寫感不是「找一個手寫字型」就好。真正讓圖看起來像手畫的是**線**：稍微歪、會超出端點、雙線描邊、用斜線塗滿面積。Excalidraw 的手繪感就來自開源的 **Rough.js**（MIT）。這個 skill 把它包成 `assets/styles/sketch.js`，參數寫進風格卡的 `sketch` 欄，所以手寫感也是一組可調、可檢查的風格參數。

## 1. 什麼時候開

| 風格卡 | sketch | 感覺 |
|---|---|---|
| `sketch-board` | roughness 1.0、hachure、雙線 | Excalidraw 式數位草圖 |
| `whiteboard` | roughness 0.8、單線、粗 | 馬克筆：線穩、少抖 |
| `chalkboard` | roughness 1.4、zigzag 填色 | 粉筆：抖、填色像來回塗 |
| `picture-book` | roughness 1.6、bowing 1.4、密斜線 | 蠟筆：彎、粗、塗得滿 |

其他風格（資料新聞、藍圖、等距、Neon Circuit）要求精確，不開。要在其他風格局部用手寫感（例如 Vox 拼貼上的一個手繪箭頭），直接呼叫 `SK.*` 並把 `roughness` 調低到 0.5–0.8。

## 2. 風格卡的 `sketch` 參數

| 欄位 | Rough.js 參數 | 範圍與效果 |
|---|---|---|
| `roughness` | roughness | 0＝直線；0.6–1.0 穩定手繪；1.4–2 抖、像粉筆蠟筆；>2 太髒 |
| `bowing` | bowing | 直線的彎曲程度；0.5 微彎、1.5 很彎 |
| `fill_style` | fillStyle | `hachure` 斜線、`cross-hatch` 交叉線、`zigzag` 鋸齒、`dots` 點、`dashed`、`zigzag-line`、`solid` 實心 |
| `hachure_gap` | hachureGap | 斜線間距（px）；≥ 線寬 ×4，否則蓋住裡面的字 |
| `hachure_angle` | hachureAngle | 斜線角度，預設 −41° |
| `fill_weight` | fillWeight | 斜線粗細 |
| `stroke_width` | strokeWidth | 輪廓線寬 |
| `multi_stroke` | !disableMultiStroke | true＝畫兩次（數位草圖感）；false＝一筆（馬克筆感） |
| `board` | — | true 時風格板用手寫感畫示意圖 |

用 `--set` 試調：`python scripts/style_apply.py sketch-board --set sketch.roughness=1.6 --set sketch.fill_style=cross-hatch --out design-demos/B`。

## 3. 決定性：seed 一定要固定

Rough.js 的 `seed` 是 0 時會改用 `Math.random()`，**每一幀的線條都會抖動**，逐格渲染的影片會像在閃。`sketch.js` 依每個圖形的 `id` 算出固定 seed，所以：
- 一律用 `SK.rect()`、`SK.arrow()`…，每個圖形給一個 `id`（加幕號前綴：`s3-box`）。
- 不要直接呼叫 `rough.svg()`；`style_lint.py` 抓到沒給 seed 的呼叫會報錯。
- 想讓同一個圖形換一種抖法，就換 id 或明確給 `seed`。

## 4. API（`sketch.js`）

載入順序：`tokens.js` → `rough.js` → `sketch.js`（`style_apply.py` 會把三個檔都放進 `style/`）。

```html
<script src="../style/tokens.js"></script>
<script src="../style/rough.js"></script>
<script src="../style/sketch.js"></script>
<svg id="s3-svg" width="1600" height="700"></svg>
<script>
const v = document.getElementById("s3-svg");
SK.rect(v, 80, 200, 300, 200, { id: "s3-subj", fill: "primary-wash" });
SK.text(v, 230, 300, "主語", { id: "s3-t1", size: "h2" });
SK.ellipse(v, 1300, 300, 320, 220, { id: "s3-obj", fill: "accent-2-wash" });
SK.text(v, 1300, 300, "對象", { id: "s3-t2", size: "h2" });
SK.arrow(v, 400, 280, 1120, 290, { id: "s3-arr", stroke: "accent", bend: 120 });

SK.hide("#s3-subj, #s3-t1, #s3-obj, #s3-t2, #s3-arr");     // 先設成「還沒畫」
const tl = gsap.timeline({ paused: true });
SK.draw(tl, "#s3-subj", AT("主語"));                         // 輪廓先畫、斜線後補
SK.draw(tl, "#s3-t1", ">");                                  // 字一個一個出現
SK.draw(tl, "#s3-arr", AT("射向"));
SK.draw(tl, "#s3-obj", ">");
SK.draw(tl, "#s3-t2", ">");
</script>
```

| 函式 | 說明 |
|---|---|
| `SK.rect／ellipse／circle／diamond／line／polyline／polygon／curve／path` | 圖形；`o.fill`、`o.stroke` 寫 token 名稱（`primary-wash`、`accent`…），`o.dashed` 虛線，其他 Rough.js 參數可逐一覆寫 |
| `SK.arrow(svg, x1, y1, x2, y2, o)` | 箭頭；`o.bend` 弧度、`o.head` 箭頭長 |
| `SK.text(svg, x, y, str, o)` | 手寫字（`var(--font-hand)`），每字一個 tspan |
| `SK.hide(target)` | 初始狀態（畫建時間軸前呼叫） |
| `SK.draw(tl, target, at, o)` | 畫出：線約占 70% 時間，斜線填色在後半補上，文字逐字出現；時長預設 `M.draw()` |
| `SK.excalidraw(svg, data, o)` | 把 Excalidraw 圖重畫成風格色，回傳步驟清單（§5） |
| `SK.play(tl, steps, at, o)` | 依序畫出每一步；`o.anchors` 指定某一步對上旁白 |

`SK.draw` 回傳的是時間軸，不能串接 `.draw()`，一步一行。

## 5. Excalidraw 工作流：老師自己畫圖，程式負責動起來

不會寫程式的老師也能自己畫圖：

1. 在 [excalidraw.com](https://excalidraw.com) 畫好圖。**畫的先後順序就是動畫出現的順序**（圖層順序）；也可以畫完再用 `--order y` 改成由上到下。
2. 選單「儲存到…」存成 `diagram.excalidraw`。
3. 轉成動畫資料：
   ```bash
   python scripts/excalidraw_prep.py diagram.excalidraw --out compositions/
   ```
   產出 `diagram.excalidraw.js`（用 `<script>` 載入，`file://` 也能用，不必 fetch）與 `diagram.steps.json`（每一步的 id 與文字，方便對旁白）。
4. 場景裡：
   ```js
   const steps = SK.excalidraw(svgEl, EXCALIDRAW["diagram"], { prefix: "s3-" });
   const tl = gsap.timeline({ paused: true });
   SK.play(tl, steps, AT("首先"), { anchors: { "葉綠體": AT("葉綠體"), "二氧化碳＋水": AT("二氧化碳") } });
   ```

**重畫而不是貼 SVG**：每個元素用它在 Excalidraw 裡自己的 seed 與 roughness 重畫，所以線條長相和老師畫的一樣，但可以逐筆動畫、換成風格色、在時間軸上任意 seek。

**顏色會換成風格色**：Excalidraw 的預設色代表「角色」，不代表固定顏色。

| Excalidraw 預設色 | 換成 |
|---|---|
| 黑 `#1e1e1e` | `ink` |
| 藍 `#1971c2`、青 `#0c8599` | `primary` |
| 紅 `#e03131`、橘 `#f08c00` | `accent` |
| 綠 `#2f9e44`、紫 `#6741d9` | `accent-2` |
| 淡藍、淡紅、淡綠、淡紫底 | `primary-wash`、`accent-wash`、`accent-2-wash` |
| 淡黃底 `#ffec99` | `hl` |

同一張圖套不同風格卡就會自動換色。要改對應：`SK.excalidraw(svg, data, { palette: { "#f08c00": "hl" } })`。不在表上的顏色會照原色畫，`excalidraw_prep.py` 會列出來。

支援的元素：矩形、橢圓、菱形、線、箭頭、手繪線、文字（綁在形狀上的文字和形狀算同一步）。圖片、框架、嵌入物件會略過：圖片改用 `.shot` 截圖卡另外放。

## 6. 字型

- **中文手寫**：芫荽 Iansui（OFL，Google Fonts）。Excalidraw 內建的中文字型「小賴」偏簡體；芫荽同樣是手寫感，而且繁體字齊全。
- **英文手寫**：Excalifont（Excalidraw 2024 年的新手寫字型，[OFL-1.1](https://plus.excalidraw.com/excalifont)）。不在 Google Fonts，要從官方頁面下載放進專案 `fonts/`，用 `@font-face` 載入；`sketch-board` 的 `type.hand` 已把它排在 Iansui 前面。
- 正式渲染前用 `scripts/font_subset.py` 做中文子集。

## 7. 常見問題

| 症狀 | 原因 | 修法 |
|---|---|---|
| 每一幀線條都在抖 | seed 是 0 | 用 `SK.*` 並給 id |
| 斜線填色蓋住裡面的字 | hachure_gap 太小 | gap ≥ 線寬 ×4，或字下面墊一塊淡色實心 |
| 圖看起來很髒 | roughness 太高、雙線太粗 | roughness ≤1.5；小圖降到 0.6 |
| 虛線沒有「畫出來」的效果 | 虛線本身就用了 dasharray | 虛線改成淡入（`SK.draw` 已自動處理） |
| Excalidraw 的圖太小或太大 | 原圖座標範圍不同 | `SK.excalidraw` 會自動設 viewBox；調整 svg 的寬高即可，`o.widthScale` 調線寬、`o.textScale` 調字 |
| 中文字變成別的字型 | Excalifont 沒有中文字 | 字型堆疊後面一定接 Iansui |

## 細緻 vs 粗糙：手寫感的調參經驗

手繪感不是越抖越好。抖動大、線粗、斜線稀而粗，會變成「粗糙」而不是「手繪」。sketch-board 的建議值（已寫進風格卡）：

| 參數 | 粗糙 | 細緻（建議） |
|---|---|---|
| `roughness` | 1.0 以上 | 0.7 |
| `bowing` | 1.0 | 0.8 |
| `stroke_width` | 3 | 2.4 |
| `hachure_gap`／`fill_weight` | 12／1.5 | 8／0.9（斜線密而淡） |

要「動態」不要靠抖：讓筆尖跟著線走（`pen`）、便利貼待機輕擺、元素彈入時帶一點旋轉落定、畫到哪一步就亮出順序號碼。真的要刻意的「亂」（例如示範 AI 亂猜），只在那幾個物件上把 roughness 拉高，對比才出得來。

## 手寫：照筆順一筆一筆寫字（`SK.write`）

字整個淡入不叫手寫。中文字用真正的筆順寫出來，觀眾才會覺得「有人在寫」。

```bash
python scripts/hanzi_prep.py --text compositions/ --out style/hanzi.js   # 抽出用到的字的筆順（自動下載 hanzi-writer-data）
```
```html
<script src="../style/hanzi.js"></script>
<script>
const w = SK.write(svg, 120, 168, "AI 每一幕都在重新猜", { id: "s1-title", size: 78 });   // 回傳 { el, width, x(i) }
SK.marker(svg, w.x(7) + 14, w.right - 8, 190, { id: "s1-mk", before: w.el });           // 螢光筆劃在重點詞底下
SK.hide("#s1-title, #s1-mk");
const track = [];
SK.draw(tl, "#s1-title", AT("重新猜") - 2, { duration: 2, track });   // 每一筆的時間依筆畫長度分配；track 回報每一筆給筆尖
SK.draw(tl, "#s1-mk", AT("重新猜"));
</script>
```

- 中文照筆順逐筆寫（字形是楷書，文鼎 AR PL KaitiM，Arphic Public License，授權檔在 `vendor/hanzi/ARPHICPL.TXT`）；英數與標點用手寫字型逐字出現。
- 用在**標題、重點詞、板書**；內文、標籤、字幕仍用字型（全部手寫反而讀得慢）。
- 速度：一個字 0.2–0.3 秒，標題總長 2–2.5 秒；寫太慢觀眾會等，太快就看不出筆順。
- 筆尖：`track` 陣列給 `penTrack()`（範例見 `examples/handdrawn-skill-demo/compositions/demo.html`），筆尖會跟著每一筆移動。

## 線條：一筆接一筆，不要四邊同時長出來

Rough.js 一個形狀的輸出常是「一個 path 裡好幾段」，直接做虛線動畫會讓每一段同時長出來（方框四個邊一起冒出），不像手在畫。`sketch.js` 會把每一段拆成獨立的 path，`SK.draw` 依序畫：方框是上→右→下→左一筆一筆，斜線填色是一條一條塗上去。還沒畫到的線完全不顯示（圓頭線段長度 0 時會留一個點，`kit.css` 已處理）。

## 資訊密度

一幕只講一件事：**標題＋一個主圖＋最多一張便利貼**。和旁白、字幕重複的字卡刪掉（字幕已經在唸了）；次要的標籤（「蒸發」「降雨」這種）只留讀懂圖必要的兩三個。截圖遮住字幕，三秒內看得出這一幕在說什麼，就夠了。
