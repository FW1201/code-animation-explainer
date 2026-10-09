#!/usr/bin/env python3
"""同一份教材 × 多種風格卡：產生示範影片 s3「換一張卡」要用的畫面。

每種風格各產生一頁 lesson.html（內容完全相同：標題、真實照片、外部圖示、手繪或程式畫的箭頭、說明卡、數字、字幕條），
再截成 1920×1080 的定格圖 variants/<id>.jpg，影片裡用這些圖做快切與八宮格。

  python variants/build_variants.py              # 預設 8 種風格
  python variants/build_variants.py chalkboard ink-wash
需要：Python 3、node＋playwright、ffmpeg；字型由 font_subset.py 下載子集（只在產生時連網）。
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, '..', '..', '..', 'skills', 'code-animation-explainer')
SCRIPTS = os.path.join(SKILL, 'scripts')
PROOF = os.path.join(SKILL, 'assets', 'proof')
STYLES = ['sketch-board', 'chalkboard', 'ink-wash', 'magazine', 'data-journal', 'blueprint', 'picture-book', 'neon-circuit']

LESSON = '''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>火箭為什麼飛得上去</title>
<link rel="stylesheet" href="fonts/fonts.css"><link rel="stylesheet" href="style/tokens.css"><link rel="stylesheet" href="style/kit.css">
<script src="style/tokens.js"></script><script src="style/rough.js"></script><script src="style/sketch.js"></script><script src="style/assets.js"></script>
<style>
body { margin: 0; }
.at { position: absolute; z-index: 2; }
#photo .as-photo img { width: 620px; }
#photo .as-edge--circle img { width: 470px; height: 470px; }
#dia { overflow: visible; }
.rcol { display: flex; flex-direction: column; gap: 26px; }
</style></head>
<body><div class="stage __TEX__">
  __PLATE__
  <div class="at kicker" style="left:130px;top:90px">自然科學 · 國中</div>
  <h1 class="at t-h1" style="left:130px;top:140px;margin:0">火箭為什麼<span class="el-emph">飛得上去</span>？</h1>
  <div class="at" id="photo" style="left:130px;top:340px"><img data-as="photo" src="rocket.jpg" alt="發射台上的火箭" data-src="SpaceX（公有領域）"></div>
  <svg class="at" id="dia" style="left:860px;top:330px" width="330" height="520" viewBox="0 0 330 520"></svg>
  <svg data-as="icon" id="v-rocket" class="at is-accent" style="left:930px;top:520px;--icon-size:150px" viewBox="0 0 24 24">__ICON__</svg>
  <span class="at el-label" style="left:1040px;top:345px">推力</span>
  <span class="at el-label" style="left:1040px;top:780px">重力</span>
  <div class="at rcol" style="left:1200px;top:340px;width:620px">
    <div class="card">
      <div class="t-h3" style="margin:0 0 12px">作用力與反作用力</div>
      <div class="t-body" style="font-size:var(--fs-label)">燃料燒成氣體往下噴，氣體也把火箭往上推。<span class="el-emph">推力大過重力</span>，就往上加速。</div>
    </div>
    <div><span class="el-num" style="font-size:min(var(--fs-stat), 140px)">11.2<small>km/s</small></span><div class="t-label" style="color:var(--ink-2);margin-top:18px">脫離地球需要的速度</div></div>
  </div>
  <!-- 不放字幕條：影片本身有字幕，截圖裡再一條會和影片字幕疊在一起 -->
</div>
<script>
addEventListener("DOMContentLoaded", async () => {
  await document.fonts.ready;
  AS.apply();
  const d = document.getElementById("dia"), sk = !!(STYLE.sketch);
  const arrow = (x1, y1, x2, y2, c, id) => sk ? SK.arrow(d, x1, y1, x2, y2, { id, stroke: c, width: 6, head: 30 })
    : d.insertAdjacentHTML("beforeend", `<path d="M${x1} ${y1}L${x2} ${y2}M${x2 - 22} ${y2 + (y2 < y1 ? 26 : -26)}L${x2} ${y2}L${x2 + 22} ${y2 + (y2 < y1 ? 26 : -26)}" style="fill:none;stroke:var(--${c});stroke-width:calc(var(--stroke) * 2.2);stroke-linecap:round;stroke-linejoin:round"/>`);
  arrow(145, 170, 145, 20, "primary", "v-up");
  arrow(145, 360, 145, 505, "accent", "v-down");
  window.__duration = 0; window.__seek = () => {}; window.__ready = true;
});
</script></body></html>
'''


def prep_photo(src, dst):
    """夜景太暗：先把曝光拉正（自動色階＋提亮暗部），風格濾鏡才有層次可以映射。"""
    from PIL import Image, ImageOps
    im = ImageOps.autocontrast(Image.open(src).convert('RGB'), cutoff=1)
    im = im.point(lambda v: round(255 * (v / 255) ** 0.72))
    im.save(dst, quality=90)


def icon():
    s = open(os.path.join(PROOF, 'icon-rocket.svg'), encoding='utf-8').read()
    return s[s.index('>', s.index('<svg')) + 1:s.rindex('</svg>')]


def main():
    ids = sys.argv[1:] or STYLES
    env = dict(os.environ)
    if 'PLAYWRIGHT_PATH' not in env:                  # 找全域安裝的 playwright（npm i -g playwright）；找不到就讓 render_seek.mjs 自己找並提示
        g = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()
        if g and os.path.isdir(os.path.join(g, 'playwright')):
            env['PLAYWRIGHT_PATH'] = os.path.join(g, 'playwright')
    import json
    for sid in ids:
        out = os.path.join(HERE, sid)
        os.makedirs(out, exist_ok=True)
        subprocess.run([sys.executable, os.path.join(SCRIPTS, 'style_apply.py'), sid, '--local-fonts', '--out', os.path.join(out, 'style')], check=True, capture_output=True)
        s = json.load(open(os.path.join(out, 'style', 'tokens.json'), encoding='utf-8'))
        prep_photo(os.path.join(PROOF, 'rocket.jpg'), os.path.join(out, 'rocket.jpg'))
        plate = '<div style="position:absolute;left:90px;top:60px;width:1740px;height:880px;background:var(--surface);border-radius:var(--radius)"></div>' if s['layout'].get('text_on') == 'surface' else ''
        html = LESSON.replace('__TEX__', ' '.join(s.get('texture', []))).replace('__ICON__', icon()).replace('__PLATE__', plate)
        open(os.path.join(out, 'lesson.html'), 'w', encoding='utf-8').write(html)
        for k in range(3):                    # 字型下載偶爾逾時，重試
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'font_subset.py'), '--style', os.path.join(out, 'style', 'tokens.json'),
                                '--text', os.path.join(out, 'lesson.html'), '--out', os.path.join(out, 'fonts')], capture_output=True, text=True)
            if r.returncode == 0: break
        else:
            sys.exit(f'{sid} 字型下載失敗：{r.stdout[-300:]}{r.stderr[-300:]}')
        tmp = os.path.join(out, '_shot')
        subprocess.run(['node', os.path.join(SCRIPTS, 'render_seek.mjs'), os.path.join(out, 'lesson.html'), tmp, '--at', '0'], check=True, env=env, capture_output=True)
        png = [f for f in os.listdir(tmp) if f.endswith('.png')][0]
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', os.path.join(tmp, png), '-q:v', '3', os.path.join(HERE, f'{sid}.jpg')], check=True)
        shutil.rmtree(tmp)
        print('  ', sid)


if __name__ == '__main__':
    main()
