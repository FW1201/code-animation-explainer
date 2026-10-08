// 白板講解 — 由 style_apply.py 產生。動態參數一律從這裡拿，不要在場景裡寫死秒數與 easing。
window.STYLE = {
 "id": "whiteboard",
 "name": "白板講解",
 "temperature": "中性",
 "positioning": "一面亮面白板上，馬克筆一筆一筆寫出整堂課，鏡頭在白板上移動而不剪接",
 "fits": [
  "自然科學",
  "「X 怎麼運作」",
  "數學應用題",
  "教師研習概念說明",
  "線上課程"
 ],
 "avoid_for": [
  "大量真實截圖",
  "故事型內容"
 ],
 "benchmarks": [
  "RSA Animate／Cognitive Media 白板動畫",
  "minutephysics（一句話一張圖）"
 ],
 "rationale": "板面帶暖的白，不是螢幕純白；三支馬克筆各有固定意義：深色畫結構、藍色畫訊號與過程、橘色只給最重要的那一點。",
 "color": {
  "bg": "#F1F0EC",
  "surface": "#FBFAF7",
  "ink": "#23262C",
  "ink-2": "#5C636C",
  "primary": "#2A5CB3",
  "accent": "#C8502A",
  "accent-2": "#2E7D50",
  "hl": "#FFE58A99"
 },
 "color_semantics": {
  "primary": "藍筆：訊號、測量、過程",
  "accent": "橘筆：每一區只有一個的重點",
  "accent-2": "綠筆：正確、結果",
  "hl": "螢光筆塗底"
 },
 "type": {
  "display": {
   "family": "\"Iansui\", \"LXGW WenKai TC\", cursive",
   "weight": 400
  },
  "body": {
   "family": "\"LXGW WenKai TC\", serif",
   "weight": 400
  },
  "mono": "\"JetBrains Mono\", monospace",
  "hand": "\"Iansui\", cursive",
  "google": [
   "Iansui",
   "LXGW WenKai TC:wght@400;700",
   "JetBrains Mono:wght@500"
  ],
  "scale": {
   "h1": 112,
   "h2": 84,
   "h3": 60,
   "body": 44,
   "label": 32,
   "small": 26,
   "stat": 180,
   "breath": 140,
   "caption": 44
  },
  "lh_display": 1.2,
  "lh_body": 1.5,
  "ls_display": "0.04em",
  "ls_body": "0.04em"
 },
 "layout": {
  "safe": 110,
  "caption_zone": 170,
  "radius": 10,
  "stroke": 4,
  "offset": 0,
  "tilt": "0deg",
  "shadow": "0 6px 0 -2px color-mix(in oklab, var(--ink) 12%, transparent)",
  "tex_opacity": 0.3,
  "ink_width": 6,
  "cap_radius": 14,
  "composition": [
   "白板是一張地圖：每個概念住在自己的區域，鏡頭在區域之間移動",
   "畫面下方 12% 永遠留給字幕",
   "標籤要嘛整個在鏡頭內、要嘛整個在外，不被推近切掉一半"
  ]
 },
 "texture": [
  "tex-whiteboard"
 ],
 "components": [
  "sk",
  "hl",
  "breath"
 ],
 "sketch": {
  "roughness": 0.8,
  "bowing": 0.6,
  "fill_style": "hachure",
  "hachure_gap": 14,
  "hachure_angle": -41,
  "fill_weight": 2.5,
  "stroke_width": 5,
  "multi_stroke": false,
  "board": true
 },
 "motion": {
  "ease": {
   "enter": "power2.out",
   "exit": "power1.in",
   "pop": "back.out(1.4)",
   "move": "power2.inOut",
   "draw": "power1.inOut"
  },
  "dur": {
   "enter": 0.5,
   "exit": 0.4,
   "pop": 0.45,
   "move": 1.0,
   "draw": 0.7,
   "hold": 0.6
  },
  "stagger": 0.1,
  "idle": "鏡頭極慢漂移；白板反光以鏡頭 0.35 倍速移動",
  "signature": [
   "文字照筆順寫出，說到哪個詞，那個詞剛好寫完",
   "磁鐵掉下、滑動（白板上唯一可以移動的東西）",
   "板擦倒著擦，等於時間倒轉"
  ]
 },
 "camera": {
  "establish": 1.06,
  "max_zoom": 1.8,
  "budget": "15 秒內 ≤3 次",
  "moves": [
   "跟著筆走到下一區",
   "推近到一個符號"
  ]
 },
 "camera_vocab": [
  {
   "move": "跟著正在畫的線走",
   "expresses": "一個想法帶出下一個",
   "serves": "過程、流程、轉場"
  },
  {
   "move": "靜止不動",
   "expresses": "現在請讀",
   "serves": "公式、定義、清單"
  },
  {
   "move": "回到先前畫過的區域",
   "expresses": "免費的回呼",
   "serves": "比較、用前面的結果"
  },
  {
   "move": "從很小的圖拉遠",
   "expresses": "尺度",
   "serves": "驚人的大小、補上脈絡"
  },
  {
   "move": "拉遠到看見整面白板",
   "expresses": "整堂課變成一張圖",
   "serves": "統整、概念地圖"
  }
 ],
 "transition": {
  "default": "跟著筆畫的線移到下一區（不剪接）",
  "chapter": "快速橫甩（whip）到新的區域"
 },
 "caption": {
  "bg": "color-mix(in oklab, var(--surface) 92%, transparent)",
  "ink": "var(--ink)",
  "kw": "var(--accent)",
  "world": "米白圓角標籤條，前面一小段強調色馬克筆短劃；每行 ≤22 字"
 },
 "sound": {
  "bgm": "單一鋼琴動機或撥弦，概念一步加一件樂器",
  "sfx_density": "依筆畫：寫字時有筆聲，其他 0–2 個／10 秒",
  "sfx": [
   "馬克筆摩擦",
   "磁鐵吸上白板",
   "板擦"
  ],
  "foley": [
   "馬克筆在亮面上的嘶聲（隨筆速起落）",
   "偶爾的吱聲",
   "磁鐵喀一聲",
   "毛氈板擦摩擦",
   "筆蓋開合"
  ],
  "palette": "鋼琴、撥弦、木琴、輕刷鼓"
 },
 "essence": [
  "一面實體白板：學生學到的一切都在眼前用馬克筆寫出來",
  "白板是地圖：一個概念一區，鏡頭在區域間移動",
  "真的馬克筆：落筆處墨較濃、線條會超出、圓圈收不攏、有舊課殘影",
  "沒有手：筆自己浮著寫，磁鐵與板擦自己動"
 ],
 "not": [
  "不是黑板粉筆（不是深綠板面、沒有粉筆灰）",
  "不是藍圖（沒有藍底與製圖規範）",
  "不是動態文字（字是照筆順寫的，不是整塊飛進來）"
 ],
 "native_moves": [
  {
   "name": "照筆順寫出",
   "how": "說到哪寫到哪，公式一項一項長出",
   "fits": [
    "一元一次方程式的移項",
    "光合作用反應式",
    "漢字的部件組合"
   ]
  },
  {
   "name": "筆帶著鏡頭",
   "how": "轉場就是一條畫出來的線，鏡頭沿著它走",
   "fits": [
    "神經訊號傳遞",
    "水循環",
    "一封信的旅程"
   ]
  },
  {
   "name": "磁鐵",
   "how": "主角交給一塊磁鐵：掉下、滑動、拿起",
   "fits": [
    "行星在軌道上",
    "細胞在血管裡",
    "棋子在地圖上"
   ]
  },
  {
   "name": "板擦倒帶",
   "how": "倒著擦掉軌跡＝時間倒轉",
   "fits": [
    "可逆反應",
    "「如果當初沒有…」",
    "改錯"
   ]
  },
  {
   "name": "兩支筆同時寫",
   "how": "兩個量即時比較",
   "fits": [
    "兩種儲蓄方案",
    "族群與食物量",
    "兩種解法"
   ]
  }
 ],
 "pitfalls": [
  {
   "issue": "一支筆排太多工作，越寫越落後",
   "fix": "每個圖給一個截止時間窗，重疊的交給第二支筆"
  },
  {
   "issue": "標點不見了（字型的句點只有 1px）",
   "fix": "細於線寬的筆畫畫成點"
  },
  {
   "issue": "推近時標籤被切一半",
   "fix": "標籤整個在內或整個在外"
  },
  {
   "issue": "虛線每一段都有最短時長，結果一條虛線寫好幾秒",
   "fix": "虛線另設最短時長"
  }
 ],
 "variation": {
  "structures": [
   "證明：最上面一句主張，往下一步一步，每步證完框起來",
   "辯論：兩支筆各占半邊，畫到中間相遇",
   "時間軸：一條長橫線從左騎到右，事件掛在上面"
  ],
  "openings": [
   "中間畫一個巨大問號，縮成第一張圖裡的一個點",
   "擦過的白板，錯誤答案的殘影還看得到",
   "一塊磁鐵「喀」一聲掉在空白板上"
  ],
  "endings": [
   "答案圈兩圈，筆蓋蓋上",
   "整面擦掉，只留一行",
   "推近到最小的那個符號，它變成標題"
  ]
 },
 "do": [
  "一支筆一種意義，全片不換",
  "字比你以為的大一級"
 ],
 "dont": [
  "畫出手或游標",
  "整塊文字淡入",
  "剪接（要換區就甩鏡）"
 ],
 "board": "center",
 "assets": {
  "icon": {
   "mode": "rough",
   "stroke": 2.5,
   "cap": "round",
   "color": "ink",
   "accent": "primary",
   "source": "Lucide／Tabler（線條圖示）"
  },
  "photo": {
   "treatment": "duotone",
   "frame": "magnet",
   "allowed": true,
   "tones": [
    "ink",
    "surface"
   ]
  },
  "illustration": {
   "recolor": true,
   "max_colors": 3
  },
  "chart": {
   "axis": "ink-2",
   "grid": "none",
   "mark": "bar",
   "label": "label"
  },
  "text": {
   "label": "plain",
   "emphasis": "circle",
   "number": "hand",
   "quote": "kai"
  },
  "avoid": [
   "emoji",
   "3D 圖示",
   "彩色漸層插畫"
  ],
  "note": "照片像印出來用磁鐵貼在白板上；圖示用馬克筆線重畫"
 }
};
(function (S) {
  const m = S.motion, mk = k => (o = {}) => Object.assign({ duration: m.dur[k], ease: m.ease[k] }, o);
  window.M = {
    in: mk("enter"), out: mk("exit"), pop: mk("pop"), move: mk("move"), draw: mk("draw"),
    hold: m.dur.hold, stagger: m.stagger,
    // 鏡頭推拉時長依倍率變化量：1→2x 約 0.55s，夾在 0.30–0.94s
    zoomDur: (a, b) => Math.min(0.94, Math.max(0.30, 0.55 * Math.abs(Math.log(b / a)) / Math.LN2)),
    color: k => getComputedStyle(document.documentElement).getPropertyValue("--" + k).trim(),
  };
})(window.STYLE);
