// 黑板粉筆 — 由 style_apply.py 產生。動態參數一律從這裡拿，不要在場景裡寫死秒數與 easing。
window.STYLE = {
 "id": "chalkboard",
 "name": "黑板粉筆",
 "temperature": "中性·暖",
 "positioning": "深綠黑板上一筆一筆寫出來，像老師在台前邊講邊畫",
 "fits": [
  "數學解題步驟",
  "國語文字詞拆解",
  "公式推導",
  "課堂開場"
 ],
 "avoid_for": [
  "大量真實截圖",
  "資料圖表"
 ],
 "benchmarks": [
  "可汗學院手寫板書",
  "日本 NHK for School 板書動畫"
 ],
 "rationale": "板面綠取自教室黑板（偏藍綠、低彩度），粉筆三色是教室最常見的白黃粉藍；字型選手寫感的芫荽與霞鶩文楷，模擬板書。",
 "color": {
  "bg": "#24372C",
  "surface": "#2D4537",
  "ink": "#F1EFE6",
  "ink-2": "#B9C2B4",
  "primary": "#F6D365",
  "accent": "#F2998C",
  "accent-2": "#94D2E6",
  "hl": "#F6D36566"
 },
 "color_semantics": {
  "primary": "黃粉筆：重點、答案",
  "accent": "粉紅粉筆：易錯處",
  "accent-2": "藍粉筆：補充、第二步",
  "hl": "黃粉筆塗底"
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
   "h1": 104,
   "h2": 80,
   "h3": 58,
   "body": 44,
   "label": 30,
   "small": 26,
   "stat": 180,
   "breath": 140,
   "caption": 46
  },
  "lh_display": 1.25,
  "lh_body": 1.5,
  "ls_display": "0.04em",
  "ls_body": "0.04em"
 },
 "layout": {
  "safe": 110,
  "caption_zone": 180,
  "radius": 6,
  "stroke": 4,
  "offset": 0,
  "tilt": "0deg",
  "shadow": "none",
  "tex_opacity": 0.35,
  "ink_width": 7,
  "cap_radius": 4,
  "composition": [
   "板書由左上往右下寫，保留右側 30% 給圖",
   "一次只擦一塊、寫一塊",
   "木框下緣放字幕"
  ]
 },
 "texture": [
  "tex-chalk",
  "tex-vignette"
 ],
 "components": [
  "ink",
  "hl",
  "chalk",
  "breath"
 ],
 "motion": {
  "ease": {
   "enter": "power2.out",
   "exit": "power1.in",
   "pop": "power2.out",
   "move": "power2.inOut",
   "draw": "power1.inOut"
  },
  "dur": {
   "enter": 0.5,
   "exit": 0.6,
   "pop": 0.4,
   "move": 1.0,
   "draw": 1.0,
   "hold": 0.6
  },
  "stagger": 0.12,
  "idle": "粉筆灰微粒極慢飄落（固定種子）",
  "signature": [
   "字與線一筆一筆描出（--draw），速度穩定像真的在寫",
   "答案用黃粉筆圈起",
   "換題用板擦遮罩由左擦到右"
  ]
 },
 "camera": {
  "establish": 1.0,
  "max_zoom": 1.4,
  "budget": "15 秒內 ≤2 次",
  "moves": [
   "推近正在寫的那一行",
   "跟著板書往下平移"
  ]
 },
 "transition": {
  "default": "板擦擦去（mask wipe 由左到右）",
  "chapter": "整塊黑板往上捲動換新板面"
 },
 "caption": {
  "bg": "color-mix(in oklab, var(--bg) 70%, black)",
  "ink": "var(--ink)",
  "kw": "var(--primary)",
  "world": "木框下緣的深色字幕條，像黑板下方的粉筆槽"
 },
 "sound": {
  "bgm": "無或極輕的木吉他",
  "sfx_density": "1–2 個／10 秒",
  "sfx": [
   "粉筆敲黑板（寫完一步）",
   "板擦"
  ],
  "foley": [
   "粉筆寫字沙沙聲",
   "粉筆敲黑板",
   "板擦"
  ],
  "palette": "木吉他、輕鋼琴或無配樂"
 },
 "do": [
  "字要大，最後一排看得到",
  "同一種意義固定用同一色粉筆"
 ],
 "dont": [
  "印刷感的粗黑體標題",
  "照片",
  "陰影與漸層"
 ],
 "board": "center",
 "essence": [
  "深綠黑板上粉筆一筆一筆寫出來",
  "三色粉筆各有意義：黃＝重點、粉紅＝易錯、藍＝補充",
  "字是板書手寫字，不是印刷字",
  "擦掉、重寫是常態"
 ],
 "not": [
  "不是白板（深色板面、有粉筆灰、沒有馬克筆光澤）",
  "不是深底數學（粉筆質感、手寫，不是乾淨向量）"
 ],
 "native_moves": [
  {
   "name": "板書寫出",
   "how": "照筆順寫出算式與字",
   "fits": [
    "直式除法",
    "生字筆順",
    "公式推導"
   ]
  },
  {
   "name": "黃粉筆圈答案",
   "how": "最後的答案圈起來",
   "fits": [
    "應用題答案",
    "主旨句",
    "關鍵公式"
   ]
  },
  {
   "name": "板擦擦掉",
   "how": "由左到右擦掉一塊，寫下一題",
   "fits": [
    "換題",
    "改錯",
    "比較前後"
   ]
  }
 ],
 "camera_vocab": [
  {
   "move": "推近正在寫的那行",
   "expresses": "跟著老師的筆",
   "serves": "步驟"
  },
  {
   "move": "跟著板書往下",
   "expresses": "下一步",
   "serves": "計算過程"
  },
  {
   "move": "拉遠看整面黑板",
   "expresses": "整題做完",
   "serves": "統整"
  }
 ],
 "pitfalls": [
  {
   "issue": "用印刷粗黑體當標題",
   "fix": "標題也用手寫字型"
  },
  {
   "issue": "粉筆字太小",
   "fix": "字比其他風格大一級"
  },
  {
   "issue": "一次寫滿整面",
   "fix": "寫一塊擦一塊"
  }
 ],
 "variation": {
  "structures": [
   "例題→練習→答案",
   "錯誤示範→找錯→正確做法",
   "一個公式從左到右推導"
  ],
  "openings": [
   "黑板上已經有一道題",
   "空黑板，粉筆寫下日期與題目",
   "上一堂課的殘影被擦掉"
  ],
  "endings": [
   "答案圈起來，粉筆放下",
   "整面擦乾淨只留一行重點",
   "寫下明天的問題"
  ]
 },
 "sketch": {
  "roughness": 1.4,
  "bowing": 1.2,
  "fill_style": "zigzag",
  "hachure_gap": 12,
  "hachure_angle": -30,
  "fill_weight": 2,
  "stroke_width": 5,
  "multi_stroke": true,
  "board": true
 },
 "assets": {
  "icon": {
   "mode": "rough",
   "stroke": 3,
   "cap": "round",
   "color": "ink",
   "accent": "primary",
   "source": "Lucide／Tabler（線條圖示）"
  },
  "photo": {
   "treatment": "chalk",
   "frame": "none",
   "allowed": true
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
  "note": "照片轉成粉筆線稿；圖示用手寫線重畫"
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
