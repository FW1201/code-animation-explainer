#!/usr/bin/env python3
"""風格校樣：把「外部收集的素材」和「程式畫的物件」放進同一個畫面，檢查是否像同一個風格。

畫面左上是原始素材（真實照片、別人的線條圖示、別人的多色插畫），下方與右邊是經過風格卡處理後的樣子，
旁邊再擺程式畫的卡片、流程方塊、長條圖、標籤與字幕條。看截圖時問一句：「哪一個東西看起來是從別的影片剪過來的？」

用法：
  python style_proof.py sketch-board                 # 產生 proof/sketch-board/proof.html 並截圖 → assets/styles/previews/proof/sketch-board.jpg
  python style_proof.py all                          # 16 種全部
  python style_proof.py vox-paper --photos a.jpg b.jpg c.jpg d.jpg --out my-proof/   # 換成自己的素材
需求：Python 3、node＋playwright（或設 PLAYWRIGHT_PATH）、ffmpeg。素材來源與授權見 assets/proof/SOURCES.md。
"""
import argparse, glob, html, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
STYLES = os.path.join(ROOT, 'assets', 'styles')
PROOF = os.path.join(ROOT, 'assets', 'proof')
PHOTOS = ['astronaut.jpg', 'coffee.jpg', 'rocket.jpg', 'cat.jpg']
ICONS = ['rocket', 'leaf', 'lightbulb', 'book-open']
ILLUS = ['idea', 'globe', 'graduation-cap']


def svg_inline(path, attrs):
    s = open(path, encoding='utf-8').read()
    s = s[s.index('<svg'):]
    head, rest = s.split('>', 1)
    head = head.replace('<svg', '<svg ' + attrs, 1)
    for a in ('class="lucide', 'width="24"', 'height="24"'):
        head = head.replace(a, 'data-x="' if a.startswith('class') else '')
    return head + '>' + rest


def page(s, photos):
    name, ess = html.escape(s['name']), html.escape(s['essence'][0])
    d = s['detail']
    tex = ' '.join(s.get('texture', []))
    raw = ''.join(f'<img class="raw" src="{p}" alt="">' for p in photos)
    raw += ''.join(svg_inline(os.path.join(PROOF, f'icon-{n}.svg'), 'class="raw-ic"') for n in ICONS[:2])
    raw += ''.join(svg_inline(os.path.join(PROOF, f'illus-{n}.svg'), 'class="raw-ic"') for n in ILLUS[:2])
    labels = ['人像', '物品', '夜景', '動物']
    ph = ''.join(f'<div class="cell"><img data-as="photo" src="{p}" alt="{labels[i]}" data-src="公有領域／CC0"><span class="el-label">{labels[i]}</span></div>'
                 for i, p in enumerate(photos))
    ic = ''.join(svg_inline(os.path.join(PROOF, f'icon-{n}.svg'), f'data-as="icon" id="pf-ic-{n}"') for n in ICONS)
    il = ''.join(svg_inline(os.path.join(PROOF, f'illus-{n}.svg'), f'data-as="illus" id="pf-il-{n}" class="ill"') for n in ILLUS)
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{name} 校樣</title>
<link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="kit.css">
<script src="tokens.js"></script><script src="rough.js"></script><script src="sketch.js"></script><script src="assets.js"></script>
<style>
body {{ margin: 0; }}
.at {{ position: absolute; z-index: 2; }}
.raws {{ display: flex; gap: 14px; align-items: center; }}
.raw {{ height: 92px; border-radius: 3px; }}
.raw-ic {{ width: 76px; height: 76px; }}
.raw-ic:not([fill]) {{ color: #000; }}
.photos {{ display: grid; grid-template-columns: 450px 450px; gap: 86px 44px; }}
.cell {{ position: relative; height: 210px; display: grid; place-items: center; }}
.cell .as-photo {{ max-width: 100%; max-height: 100%; }}
.cell .as-photo img {{ max-height: 185px; max-width: 400px; }}
.cell .as-edge--circle img {{ width: 200px; height: 200px; }}
.cell .el-label {{ position: absolute; left: -6px; top: -10px; z-index: 3; }}
.icons {{ display: flex; gap: 34px; align-items: center; --icon-size: 84px; }}
.ill {{ width: 120px; height: 120px; overflow: visible; }}
.flow {{ display: flex; align-items: center; gap: 0; margin-top: 10px; }}
.rcol {{ display: flex; flex-direction: column; gap: 10px; }}
.rcol .card {{ padding: 26px 36px; }}
.plate {{ position: absolute; left: 50px; top: 24px; width: 1010px; height: 330px; z-index: 1; background: var(--surface); border-radius: var(--radius); }}
.rcol .cap {{ font-size: var(--fs-small); color: var(--ink-2); margin-top: 6px; }}
.ess {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.flow .obj {{ padding: 18px 28px; font: var(--w-body) var(--fs-label)/1.2 var(--font-body); }}
.flow > svg {{ width: 70px; height: 30px; overflow: visible; }}
</style></head>
<body><div class="stage {tex}" id="stage">
  {'<div class="plate"></div>' if s['layout'].get('text_on') == 'surface' else ''}
  <div class="at kicker" style="left:80px;top:40px">風格校樣 · {html.escape(s["id"])}</div>
  <div class="at t-h3" style="left:80px;top:78px">{name}</div>
  <div class="at t-label ess" style="left:80px;top:160px;color:var(--ink-2);width:980px">{ess}</div>
  <div class="at" style="font-size:var(--fs-small);left:80px;top:212px;color:var(--ink-2)">原始素材（外部收集，未處理）</div>
  <div class="at raws" style="left:80px;top:250px">{raw}</div>
  <div class="at photos" style="left:80px;top:380px">{ph}</div>
  <div class="at rcol" style="left:1130px;top:50px;width:710px">
  <div class="card" id="pf-card">
    <div class="kicker">程式畫的物件</div>
    <div class="t-h3" style="margin:6px 0 10px">光合作用的<span class="el-emph">原料</span></div>
    <div class="t-body" style="font-size:var(--fs-label)">二氧化碳＋水，在光的幫助下變成養分。</div>
    <div style="display:flex;gap:16px;margin-top:16px;align-items:center"><span class="el-label">葉綠體</span><span class="el-num" style="font-size:var(--fs-h2)">6<small>CO₂</small></span></div>
  </div>
  <div class="cap">外部圖示（Lucide）→ 處理後</div>
  <div class="icons">{ic}</div>
  <div class="cap">外部插畫（多色）→ 處理後｜程式畫的長條圖</div>
  <div class="icons">{il}<svg id="pf-chart" width="220" height="150" viewBox="0 0 240 170"></svg></div>
  <div class="flow">
    <div class="obj" id="pf-n0">陽光</div><svg viewBox="0 0 70 30" id="pf-a0"></svg>
    <div class="obj" id="pf-n1">葉子</div><svg viewBox="0 0 70 30" id="pf-a1"></svg>
    <div class="obj" id="pf-n2">養分</div>
  </div>
  </div>
  <div class="caption-bar">字幕條：同一個畫面裡，每樣東西都像同一支筆畫的</div>
</div>
<script>
addEventListener("DOMContentLoaded", async () => {{
  await document.fonts.ready;
  AS.apply();
  const sk = !!(STYLE.sketch && window.SK), ch = document.getElementById("pf-chart");
  [0, 1].forEach(i => {{
    const a = document.getElementById("pf-a" + i);
    if (sk) SK.arrow(a, 10, 15, 60, 15, {{ id: "pf-ar" + i, stroke: "ink", width: 2.5, head: 12 }});
    else a.innerHTML = '<path d="M8 15H58M48 6l10 9-10 9" fill="none" stroke="var(--ink)" stroke-width="var(--stroke)" stroke-linecap="round" stroke-linejoin="round"/>';
  }});
  const bars = [[60, "primary"], [110, "primary"], [150, "accent-2"]];
  bars.forEach(([h, c], i) => {{
    const x = 30 + i * 70;
    if (sk) SK.rect(ch, x, 160 - h, 46, h, {{ id: "pf-b" + i, fill: c, stroke: "ink", width: 2 }});
    else ch.insertAdjacentHTML("beforeend", `<rect x="${{x}}" y="${{160 - h}}" width="46" height="${{h}}" rx="${{Math.min(4, parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--radius")))}}" fill="var(--${{c}})"/>`);
  }});
  if (sk) SK.line(ch, 10, 160, 235, 160, {{ id: "pf-ax", stroke: "ink-2", width: 2 }});
  else ch.insertAdjacentHTML("beforeend", '<path d="M10 160H235" stroke="var(--ink-2)" stroke-width="2"/>');
  window.__duration = 0; window.__seek = () => {{}}; window.__ready = true;
}});
</script></body></html>
'''


def build(sid, out, photos):
    subprocess.run([sys.executable, os.path.join(HERE, 'style_apply.py'), sid, '--out', out], check=True, capture_output=True)
    names = []
    for p in photos:
        n = os.path.basename(p); shutil.copy(p, os.path.join(out, n)); names.append(n)
    s = json.load(open(os.path.join(out, 'tokens.json'), encoding='utf-8'))
    open(os.path.join(out, 'proof.html'), 'w', encoding='utf-8').write(page(s, names))
    return os.path.join(out, 'proof.html')


def shoot(html_path, jpg):
    env = dict(os.environ)
    if 'PLAYWRIGHT_PATH' not in env and os.path.isdir('/opt/node-tools/node_modules/playwright'):
        env['PLAYWRIGHT_PATH'] = '/opt/node-tools/node_modules/playwright'
    tmp = os.path.join(os.path.dirname(html_path), '_shot')
    subprocess.run(['node', os.path.join(HERE, 'render_seek.mjs'), html_path, tmp, '--at', '0'], check=True, env=env, capture_output=True)
    png = glob.glob(os.path.join(tmp, '*.png'))[0]
    os.makedirs(os.path.dirname(jpg), exist_ok=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', png, '-q:v', '3', jpg], check=True)
    shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser(description='風格校樣：外部素材＋程式物件的一致性截圖')
    ap.add_argument('style', help='風格 id，或 all'); ap.add_argument('--photos', nargs='+')
    ap.add_argument('--out', help='輸出資料夾（預設 proof/<id>/，截圖存到 assets/styles/previews/proof/）')
    ap.add_argument('--no-shot', action='store_true')
    a = ap.parse_args()
    ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(STYLES, '*.json'))) if a.style == 'all' else [a.style]
    photos = a.photos or [os.path.join(PROOF, p) for p in PHOTOS]
    for sid in ids:
        out = a.out if a.out and len(ids) == 1 else os.path.join(a.out or 'proof', sid)
        h = build(sid, out, photos)
        if not a.no_shot:
            jpg = os.path.join(out, 'proof.jpg') if a.out else os.path.join(STYLES, 'previews', 'proof', f'{sid}.jpg')
            shoot(h, jpg)
            print(f'  {sid} → {jpg}')
        else:
            print(f'  {sid} → {h}')


if __name__ == '__main__':
    main()
