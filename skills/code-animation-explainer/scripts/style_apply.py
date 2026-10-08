#!/usr/bin/env python3
"""把風格卡（assets/styles/<id>.json）套成專案的設計 tokens，並產生一張風格板（方向板）。

用法：
  python style_apply.py vox-paper --out style/                       # 用內建風格卡
  python style_apply.py my-style.json --out style/ --sample sample.json
  python style_apply.py data-journal --colors-from vox-paper --out style/   # 混搭：B 的版面＋A 的配色
  python style_apply.py chalkboard --set color.primary=#FFE08A --set type.scale.body=46 --out style/
  python style_apply.py --list                                        # 列出所有風格卡

輸出（--out 資料夾）：
  tokens.css   CSS 變數（色彩、字型、字級、版面、材質），每一幕都要先載入它
  tokens.js    window.STYLE（完整風格卡）＋ window.M 動態 helper：M.in() / M.out() / M.pop() / M.move() / M.draw()
  tokens.json  解析後的風格卡（style_lint.py 用它檢查場景有沒有偏離風格）
  kit.css      視覺元件庫（材質、卡片、截圖卡、螢光筆、手繪線、字幕條…）
  assets.js    素材對齊：AS.photo（照片濾鏡＋外框）、AS.icon（圖示線寬顏色、手寫重畫）、AS.recolor（插畫換風格色）
  sketch.js＋rough.js  手寫感圖層：SK.rect／SK.arrow／SK.text…（參數讀風格卡 sketch 欄，seed 固定），SK.excalidraw 匯入 Excalidraw 圖
  board.html   1920×1080 風格板：範例畫面＋色票（含對比度）＋字級＋動態參數。截圖後就是方向板
sample.json 欄位：kicker, title（[[ ]] 標螢光筆重點、| 手動分行）, body, stat, unit, stat_label, nodes[2], relation, caption, breath。
"""
import argparse, copy, html, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STYLES = os.path.join(HERE, '..', 'assets', 'styles')
ICON_MODES = ['line', 'solid', 'rough', 'none']
PHOTO_TREAT = ['none', 'duotone', 'halftone', 'ink', 'silhouette', 'chalk', 'blueprint', 'soft']
PHOTO_FRAME = ['none', 'shot', 'polaroid', 'magnet', 'rounded', 'ui']
# 細節層（detail）：物件質感與外部素材處理。選項與效果見 references/style-system.md §1.4
OBJ_OPTS = {'surface': ['flat', 'paper', 'grain', 'hatch', 'halftone', 'chalk', 'wash', 'glass', 'blueprint', 'scan'],
            'edge': ['clean', 'rough', 'brush', 'torn'], 'border': ['none', 'hair', 'ink', 'chalk', 'double', 'dashed'],
            'shadow': ['none', 'soft', 'lift', 'hard', 'long', 'glow']}
PHOTO_MODES = ['color', 'map', 'halftone', 'posterize', 'lines', 'chalk', 'ink', 'silhouette']
PHOTO_EDGES = ['none', 'rounded', 'circle', 'soft', 'brush', 'torn']
ILLUS_MODES = ['palette', 'duotone', 'mono', 'outline', 'rough']
TEXT_OPTS = {'label': ['plate', 'pill', 'plain', 'tag', 'inscription', 'mono'], 'emphasis': ['hl', 'underline', 'circle', 'seal', 'color'],
             'number': ['stat', 'mono', 'hand'], 'quote': ['card', 'kai', 'rule']}
# 文字元素：每個選項對應一組 CSS 變數，kit.css 的 .el-label／.el-emph／.el-num／.el-quote 讀它們
LABEL = {
    'plate': dict(bg='var(--surface)', ink='var(--ink)', border='var(--stroke) solid var(--ink)', radius='var(--radius)', pad='8px 20px', font='var(--font-body)', weight=700, ls='0.02em', marker='0px'),
    'pill': dict(bg='color-mix(in oklab, var(--primary) 14%, transparent)', ink='var(--ink)', border='0', radius='999px', pad='8px 22px', font='var(--font-body)', weight=600, ls='0.02em', marker='0px'),
    'plain': dict(bg='transparent', ink='var(--ink-2)', border='0', radius='0', pad='0', font='var(--font-body)', weight=600, ls='0.08em', marker='0px'),
    'tag': dict(bg='var(--accent)', ink='var(--surface)', border='0', radius='4px', pad='6px 16px', font='var(--font-display)', weight=900, ls='0.04em', marker='0px'),
    'inscription': dict(bg='transparent', ink='var(--ink)', border='0', radius='0', pad='0', font='var(--font-hand)', weight=400, ls='0.1em', marker='14px'),
    'mono': dict(bg='transparent', ink='var(--ink-2)', border='0', radius='0', pad='0', font='var(--font-mono)', weight=500, ls='0.04em', marker='0px'),
}
EMPH = {
    'hl': dict(bg='linear-gradient(var(--hl), var(--hl))', size='calc(var(--p) * 100%) 42%', color='inherit', ring='none', radius='0', pad='0 .08em', weight='inherit'),
    'underline': dict(bg='linear-gradient(var(--accent), var(--accent))', size='calc(var(--p) * 100%) 6px', color='inherit', ring='none', radius='0', pad='0', weight='inherit'),
    'circle': dict(bg='none', size='auto', color='inherit', ring='0 0 0 4px var(--accent)', radius='999px', pad='0 .35em', weight='inherit'),
    'seal': dict(bg='linear-gradient(var(--accent), var(--accent))', size='calc(var(--p) * 100%) 100%', color='var(--surface)', ring='none', radius='4px', pad='0 .2em', weight=700),
    'color': dict(bg='none', size='auto', color='var(--accent)', ring='none', radius='0', pad='0', weight=800),
}
NUM = {'stat': dict(font='var(--font-display)', color='var(--primary)', weight='var(--w-display)'),
       'mono': dict(font='var(--font-mono)', color='var(--ink)', weight=600),
       'hand': dict(font='var(--font-hand)', color='var(--accent)', weight=400)}
QUOTE = {'card': dict(font='var(--font-body)', bg='var(--surface)', rule='0', pad='28px 36px', radius='var(--radius)', shadow='var(--shadow)'),
         'kai': dict(font='var(--font-hand)', bg='transparent', rule='0', pad='0', radius='0', shadow='none'),
         'rule': dict(font='var(--font-display)', bg='transparent', rule='6px solid var(--primary)', pad='4px 0 4px 28px', radius='0', shadow='none')}
REQUIRED_COLORS = ['bg', 'surface', 'ink', 'ink-2', 'primary', 'accent', 'accent-2', 'hl']
SCALE_KEYS = ['h1', 'h2', 'h3', 'body', 'label', 'small', 'stat', 'breath', 'caption']
DEFAULT_SAMPLE = {
    'kicker': '02 近義介詞', 'title': '「對」有方向，|[[「跟」]]沒有',
    'body': '同樣是介詞，「對」把動作射向一個對象；「跟」只是兩個人一起做。',
    'stat': '3.2', 'unit': '倍', 'stat_label': '「對」後接心理動詞的比例（示意）',
    'nodes': ['我', '你'], 'relation': '對', 'caption': '「對」帶出的是動作的方向', 'breath': '差在方向',
}


def load_style(ref):
    path = ref if ref.endswith('.json') else os.path.join(STYLES, f'{ref}.json')
    if not os.path.exists(path):
        sys.exit(f'找不到風格卡：{ref}（用 --list 看有哪些）')
    return json.load(open(path, encoding='utf-8'))


def set_path(d, dotted, value):
    keys = dotted.split('.')
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    try:
        value = json.loads(value)
    except (ValueError, TypeError):
        pass
    d[keys[-1]] = value


def rgb(hexstr):
    h = hexstr.lstrip('#')
    if len(h) not in (6, 8):
        return None
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(c):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    ca, cb = rgb(a), rgb(b)
    if not ca or not cb or len(a.lstrip('#')) == 8 or len(b.lstrip('#')) == 8:
        return None
    la, lb = sorted((luminance(ca), luminance(cb)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validate(s):
    errs = [f'color.{k}' for k in REQUIRED_COLORS if k not in s.get('color', {})]
    errs += [f'type.scale.{k}' for k in SCALE_KEYS if k not in s.get('type', {}).get('scale', {})]
    for k in ('display', 'body', 'mono'):
        if k not in s.get('type', {}):
            errs.append(f'type.{k}')
    for k in ('enter', 'exit', 'pop', 'move', 'draw'):
        if k not in s.get('motion', {}).get('ease', {}) or k not in s.get('motion', {}).get('dur', {}):
            errs.append(f'motion.ease/dur.{k}')
    # 風格語法層：讓模型知道這個媒材「長什麼樣、不是什麼、能做什麼招式、會踩什麼坑」
    g = s
    if len(g.get('essence', [])) < 3: errs.append('essence（辨識特徵 ≥3 條）')
    if not g.get('not'): errs.append('not（易混淆風格界線）')
    nm = g.get('native_moves', [])
    if len(nm) < 3 or any(len(m.get('fits', [])) < 3 for m in nm): errs.append('native_moves（≥3 招，每招 fits ≥3 例）')
    if len(g.get('camera_vocab', [])) < 3: errs.append('camera_vocab（≥3 種運鏡）')
    if len(g.get('pitfalls', [])) < 2: errs.append('pitfalls（≥2 條媒材陷阱）')
    v = g.get('variation', {})
    if any(len(v.get(k, [])) < 3 for k in ('structures', 'openings', 'endings')): errs.append('variation（結構／開場／結尾各 3）')
    if not g.get('caption', {}).get('world'): errs.append('caption.world（字幕在這個風格裡是什麼）')
    if not g.get('sound', {}).get('foley'): errs.append('sound.foley（材質音）')
    a = g.get('assets', {})
    if not a: errs.append('assets（素材處理規則）')
    else:
        if a.get('icon', {}).get('mode') not in ICON_MODES: errs.append(f'assets.icon.mode（{"／".join(ICON_MODES)}）')
        ph = a.get('photo', {})
        if ph.get('treatment') not in PHOTO_TREAT: errs.append(f'assets.photo.treatment（{"／".join(PHOTO_TREAT)}）')
        if ph.get('frame', 'none') not in PHOTO_FRAME: errs.append(f'assets.photo.frame（{"／".join(PHOTO_FRAME)}）')
        tx = a.get('text', {})
        for k, opts in TEXT_OPTS.items():
            if tx.get(k) not in opts: errs.append(f'assets.text.{k}（{"／".join(opts)}）')
    d = g.get('detail')
    if not d:
        errs.append('detail（物件質感＋外部素材處理）')
    else:
        for k, opts in OBJ_OPTS.items():
            if d.get('object', {}).get(k) not in opts: errs.append(f'detail.object.{k}（{"／".join(opts)}）')
        ph = d.get('photo', {})
        if ph.get('mode') not in PHOTO_MODES: errs.append(f'detail.photo.mode（{"／".join(PHOTO_MODES)}）')
        if ph.get('edge', 'none') not in PHOTO_EDGES: errs.append(f'detail.photo.edge（{"／".join(PHOTO_EDGES)}）')
        if ph.get('mode') in ('map', 'posterize', 'halftone') and len(ph.get('map', [])) < 2: errs.append('detail.photo.map（至少兩個色）')
        if d.get('illustration', {}).get('mode') not in ILLUS_MODES: errs.append(f'detail.illustration.mode（{"／".join(ILLUS_MODES)}）')
    sk = g.get('sketch')
    if sk is not None and not all(k in sk for k in ('roughness', 'bowing', 'fill_style')):
        errs.append('sketch（至少 roughness、bowing、fill_style）')
    if errs:
        sys.exit('風格卡缺欄位：' + '、'.join(errs))


def contrast_report(s):
    """文字的底色預設是 bg；文字其實放在 surface 上（如皮影幕布）時，風格卡寫 layout.text_on。
    graphic_only 列出只當色塊／圖形、不當文字色的顏色，不檢查。"""
    c, base, skip = s['color'], s['layout'].get('text_on', 'bg'), set(s.get('graphic_only', []))
    pairs = [('ink', base, 4.5), ('ink-2', base, 4.5), ('ink', 'surface', 4.5), ('primary', base, 3.0), ('accent', base, 3.0), ('accent-2', base, 3.0)]
    out = []
    for fg, bg, need in dict.fromkeys(pairs):
        if fg in skip:
            continue
        r = contrast(c[fg], c[bg])
        if r is not None:
            out.append((fg, bg, r, need))
    return out


def tokens_css(s):
    c, t, L = s['color'], s['type'], s['layout']
    fams = '&'.join('family=' + f.replace(' ', '+') for f in t.get('google', []))
    lines = [f'/* {s["name"]}（{s["id"]}）— 由 style_apply.py 產生，請改風格卡再重產，不要手改 */']
    if fams and not s.get('_local_fonts'):
        lines.append(f'@import url("https://fonts.googleapis.com/css2?{fams}&display=swap");')
    elif fams:
        lines.append('/* 字型改由本機 fonts/fonts.css 載入（font_subset.py 產生），渲染時不連網 */')
    v = {f'--{k}': c[k] for k in REQUIRED_COLORS}
    derived = {
        'kicker-ink': 'var(--primary)', 'card-border': 'var(--ink)', 'shot-frame': 'var(--surface)', 'ink-stroke': 'var(--ink)',
        'tape': 'color-mix(in oklab, var(--hl) 70%, transparent)',
        'shadow-color': 'color-mix(in oklab, var(--ink) 35%, transparent)',
        'vignette': 'color-mix(in oklab, var(--ink) 22%, transparent)',
        'grid-major': 'color-mix(in oklab, var(--ink) 22%, transparent)',
        'grid-minor': 'color-mix(in oklab, var(--ink) 10%, transparent)',
        'primary-wash': 'color-mix(in oklab, var(--primary) 40%, transparent)',
        'accent-wash': 'color-mix(in oklab, var(--accent) 40%, transparent)',
        'accent-2-wash': 'color-mix(in oklab, var(--accent-2) 40%, transparent)',
    }
    for k, val in derived.items():
        v[f'--{k}'] = c.get(k, val)
    cap = s.get('caption', {})
    v['--cap-bg'] = cap.get('bg', 'color-mix(in oklab, var(--ink) 86%, transparent)')
    v['--cap-ink'] = cap.get('ink', 'var(--bg)')
    v['--cap-kw'] = cap.get('kw', 'var(--hl)')
    v['--font-display'] = t['display']['family']; v['--w-display'] = t['display']['weight']
    v['--font-body'] = t['body']['family']; v['--w-body'] = t['body']['weight']
    v['--font-mono'] = t['mono']; v['--font-hand'] = t.get('hand', t['body']['family'])
    for k in SCALE_KEYS:
        v[f'--fs-{k}'] = f'{t["scale"][k]}px'
    v['--lh-display'] = t.get('lh_display', 1.15); v['--lh-body'] = t.get('lh_body', 1.5)
    v['--ls-display'] = t.get('ls_display', '0'); v['--ls-body'] = t.get('ls_body', '0.02em')
    for k, unit in (('safe', 'px'), ('caption_zone', 'px'), ('radius', 'px'), ('stroke', 'px'), ('offset', 'px'), ('ink_width', 'px'), ('cap_radius', 'px')):
        v['--' + k.replace('_', '-')] = f'{L.get(k, 0)}{unit}'
    v['--backlight'] = L.get('backlight', '70% 75%')
    a = s.get('assets', {})
    ic = a.get('icon', {})
    v['--icon-stroke'] = ic.get('stroke', 2); v['--icon-cap'] = ic.get('cap', 'round')
    v['--icon-join'] = 'round' if ic.get('cap', 'round') == 'round' else 'miter'
    v['--icon-color'] = f'var(--{ic.get("color", "ink")})'; v['--icon-accent'] = f'var(--{ic.get("accent", "primary")})'
    txt = a.get('text', {})
    for pre, table, key in (('label', LABEL, 'label'), ('emph', EMPH, 'emphasis'), ('num', NUM, 'number'), ('quote', QUOTE, 'quote')):
        for k, val in table.get(txt.get(key), next(iter(table.values()))).items():
            v[f'--{pre}-{k}'] = val
    v.update(object_vars(s))
    v['--tilt'] = L.get('tilt', '0deg'); v['--shadow'] = L.get('shadow', 'none'); v['--tex-opacity'] = L.get('tex_opacity', 0)
    lines.append(':root {')
    lines += [f'  {k}: {val};' for k, val in v.items()]
    lines.append('}')
    lines.append(object_rules(s))
    lines.append(f'/* 這個風格預設要掛的材質：<div class="stage {" ".join(s.get("texture", []))}"> */')
    return '\n'.join(lines) + '\n'


def _svg(body, w=400, h=300):
    """SVG → CSS url()（mask 與材質用）。preserveAspectRatio=none：跟著物件大小伸縮。"""
    x = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' preserveAspectRatio='none'>{body}</svg>"
    return 'url("data:image/svg+xml;utf8,' + x.replace('#', '%23').replace('"', "'") + '")'


def _noise(freq, rgb, alpha, seed=7, size=300):
    r, g, b = rgb
    return ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='{s}' height='{s}'><filter id='n'>"
            "<feTurbulence type='fractalNoise' baseFrequency='{f}' numOctaves='2' seed='{sd}' stitchTiles='stitch'/>"
            "<feColorMatrix values='0 0 0 0 {r}  0 0 0 0 {g}  0 0 0 0 {b}  0 0 0 {a} 0'/></filter>"
            "<rect width='{s}' height='{s}' filter='url(%23n)'/></svg>\")").format(s=size, f=freq, sd=seed, r=r, g=g, b=b, a=alpha)


def _torn(seed=5, w=400, h=300, amp=6, step=9):
    """撕紙邊：四邊鋸齒，固定種子（每次一樣）。"""
    st = [seed]
    def rnd():
        st[0] = (st[0] * 1103515245 + 12345) & 0x7fffffff
        return st[0] / 0x7fffffff
    pts = []
    for x in range(0, w + 1, step): pts.append((x, rnd() * amp))
    for y in range(0, h + 1, step): pts.append((w - rnd() * amp, y))
    for x in range(w, -1, -step): pts.append((x, h - rnd() * amp))
    for y in range(h, -1, -step): pts.append((rnd() * amp, y))
    return _svg("<polygon points='" + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + "'/>", w, h)


def edge_mask(edge, radius=0):
    if edge == 'rough':
        return _svg("<filter id='f' x='-5%' y='-5%' width='110%' height='110%'><feTurbulence type='fractalNoise' baseFrequency='0.035' numOctaves='2' seed='3'/>"
                    f"<feDisplacementMap in='SourceGraphic' scale='7'/></filter><rect x='5' y='5' width='390' height='290' rx='{min(radius, 40)}' filter='url(#f)'/>")
    if edge == 'brush':
        return _svg("<filter id='f' x='-5%' y='-5%' width='110%' height='110%'><feTurbulence type='fractalNoise' baseFrequency='0.02 0.12' numOctaves='3' seed='8'/>"
                    "<feDisplacementMap in='SourceGraphic' scale='26'/><feGaussianBlur stdDeviation='1.2'/></filter><rect x='16' y='14' width='368' height='272' filter='url(#f)'/>")
    if edge == 'torn':
        return _torn()
    return 'none'


def object_vars(s):
    """detail.object → --obj-* 變數。kit.css 的 .card／.obj 用它們畫底、邊、影子、材質。"""
    o = (s.get('detail') or {}).get('object', {})
    L = s['layout']
    dark = luminance(rgb(s['color']['surface'])) < 0.25
    ink = rgb(s['color']['ink'])
    inkf = tuple(round(x / 255, 3) for x in ink)
    tex = {
        'flat': [],
        'paper': [_noise('0.012 0.06', inkf, 0.05, 11), _noise('0.8', inkf, 0.05, 5, 200)],
        'grain': [_noise('0.9', inkf, 0.10, 5, 200)],
        'hatch': ['repeating-linear-gradient(-45deg, color-mix(in oklab, var(--primary) 16%, transparent) 0 2px, transparent 2px 15px)'],
        'halftone': ['radial-gradient(color-mix(in oklab, var(--ink) 13%, transparent) 1.3px, transparent 1.8px) 0 0 / 10px 10px'],
        'chalk': [_noise('0.65', inkf, 0.18, 9, 240), _noise('0.03 0.2', inkf, 0.10, 4)],
        'wash': ['radial-gradient(60% 50% at 25% 30%, color-mix(in oklab, var(--hl) 30%, transparent), transparent 70%)',
                 'radial-gradient(55% 60% at 80% 75%, color-mix(in oklab, var(--primary) 16%, transparent), transparent 70%)',
                 _noise('0.02 0.05', inkf, 0.08, 13)],
        'glass': ['linear-gradient(160deg, color-mix(in oklab, var(--ink) 9%, transparent), transparent 45%)'],
        'blueprint': ['repeating-linear-gradient(0deg, color-mix(in oklab, var(--ink) 9%, transparent) 0 1px, transparent 1px 24px)',
                      'repeating-linear-gradient(90deg, color-mix(in oklab, var(--ink) 9%, transparent) 0 1px, transparent 1px 24px)'],
        'scan': ['repeating-linear-gradient(0deg, color-mix(in oklab, var(--ink) 5%, transparent) 0 1px, transparent 1px 4px)'],
    }[o.get('surface', 'flat')]
    g = float(o.get('grain', 0) or 0)
    if g and o.get('surface') not in ('grain', 'chalk'):
        tex = tex + [_noise('0.9', inkf, round(g * 0.6, 3), 21, 200)]
    surface = 'color-mix(in oklab, var(--surface) 72%, transparent)' if o.get('surface') == 'glass' else 'var(--surface)'
    border = {'none': 'none', 'hair': '1.5px solid color-mix(in oklab, var(--ink) 30%, transparent)',
              'ink': 'var(--stroke) solid var(--ink)', 'chalk': 'var(--stroke) solid color-mix(in oklab, var(--ink) 75%, transparent)',
              'double': '5px double var(--ink)', 'dashed': '2px dashed var(--ink-2)'}[o.get('border', 'none')]
    sh = {'none': ('0px', '0px', '0px', 'transparent', '0px'),
          'soft': ('0px', '18px', '22px', 'color-mix(in oklab, var(--shadow-color) 70%, transparent)', '12px'),
          'lift': ('0px', '9px', '0px', 'color-mix(in oklab, var(--ink) 22%, transparent)', '0px'),
          'hard': ('var(--offset)', 'var(--offset)', '0px', 'var(--card-border)', '0px'),
          'long': ('14px', '14px', '0px', 'color-mix(in oklab, var(--ink) 18%, transparent)', '0px'),
          'glow': ('0px', '0px', '26px', 'color-mix(in oklab, var(--primary) 45%, transparent)', '0px')}[o.get('shadow', 'none')]
    if dark and o.get('shadow') == 'soft':
        sh = ('0px', '18px', '26px', 'color-mix(in oklab, black 60%, transparent)', '12px')
    radius = o.get('corner', L.get('radius', 0))
    return {
        '--obj-bg': ', '.join(tex + [surface]) if tex else surface,
        '--obj-border': border, '--obj-radius': f'{radius}px',
        '--obj-mask': edge_mask(o.get('edge', 'clean'), radius),
        '--obj-sh-x': sh[0], '--obj-sh-y': sh[1], '--obj-sh-blur': sh[2], '--obj-sh-color': sh[3], '--obj-sh-inset': sh[4],
        '--mask-torn': _torn(9, amp=10, step=12), '--mask-brush': edge_mask('brush'),
        '--obj-highlight': 'inset 0 1px 0 color-mix(in oklab, white 18%, transparent)' if o.get('surface') == 'glass' else 'none',
    }


def object_rules(s):
    """邊緣不是直線（rough／brush／torn）時，卡片的底、影子改畫在兩個遮罩過的偽元素上，邊緣才會跟著不規則。"""
    edge = (s.get('detail') or {}).get('object', {}).get('edge', 'clean')
    if edge == 'clean':
        return ''
    ring = 'box-shadow: inset 0 0 0 calc(var(--stroke) + 2px) var(--ink);' if s['detail']['object'].get('border') in ('ink', 'chalk') else ''
    return f"""/* 物件邊緣：{edge}（detail.object.edge） */
:root .card, :root .obj {{ background: none; border: none; box-shadow: none; }}
:root .card::before, :root .obj::before, :root .card::after, :root .obj::after {{ content: ""; position: absolute; inset: 0; z-index: -1;
  -webkit-mask: var(--obj-mask) 0 0 / 100% 100% no-repeat; mask: var(--obj-mask) 0 0 / 100% 100% no-repeat; }}
:root .card::before, :root .obj::before {{ background: var(--obj-sh-color); translate: var(--obj-sh-x) var(--obj-sh-y); }}
:root .card::after, :root .obj::after {{ background: var(--obj-bg); {ring} }}
:root .card--ghost::before, :root .card--ghost::after {{ display: none; }}
"""


def tokens_js(s):
    return (f'// {s["name"]} — 由 style_apply.py 產生。動態參數一律從這裡拿，不要在場景裡寫死秒數與 easing。\n'
            f'window.STYLE = {json.dumps(s, ensure_ascii=False, indent=1)};\n'
            '(function (S) {\n'
            '  const m = S.motion, mk = k => (o = {}) => Object.assign({ duration: m.dur[k], ease: m.ease[k] }, o);\n'
            '  window.M = {\n'
            '    in: mk("enter"), out: mk("exit"), pop: mk("pop"), move: mk("move"), draw: mk("draw"),\n'
            '    hold: m.dur.hold, stagger: m.stagger,\n'
            '    // 鏡頭推拉時長依倍率變化量：1→2x 約 0.55s，夾在 0.30–0.94s\n'
            '    zoomDur: (a, b) => Math.min(0.94, Math.max(0.30, 0.55 * Math.abs(Math.log(b / a)) / Math.LN2)),\n'
            '    color: k => getComputedStyle(document.documentElement).getPropertyValue("--" + k).trim(),\n'
            '  };\n'
            '})(window.STYLE);\n')


def diagram(s, smp, w=760, h=420):
    a, b = smp['nodes']
    n = int(min(200, w * 0.24))                      # 節點寬依畫布縮放，箭頭才有空間
    nh, cy, fs = int(n * 0.8), h // 2, 'var(--fs-h2)' if n >= 180 else 'var(--fs-h3)'
    rnd = 'rx="999"' if s['layout'].get('radius', 0) >= 20 else f'rx="{s["layout"].get("radius", 0)}"'
    x1, x2 = 40 + n + 16, w - 40 - n - 16
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="overflow:visible">
  <line x1="40" y1="{h - 50}" x2="{w - 40}" y2="{h - 50}" style="stroke:var(--ink);stroke-opacity:.25;stroke-width:var(--stroke)"/>
  <rect x="40" y="{cy - nh // 2}" width="{n}" height="{nh}" {rnd} style="fill:var(--primary);stroke:var(--ink);stroke-width:var(--stroke)"/>
  <text x="{40 + n // 2}" y="{cy}" dominant-baseline="central" text-anchor="middle" style="fill:var(--bg);font:var(--w-display) {fs}/1 var(--font-display)">{html.escape(a)}</text>
  <rect x="{w - 40 - n}" y="{cy - nh // 2}" width="{n}" height="{nh}" {rnd} style="fill:var(--surface);stroke:var(--ink);stroke-width:var(--stroke)"/>
  <text x="{w - 40 - n // 2}" y="{cy}" dominant-baseline="central" text-anchor="middle" style="fill:var(--ink);font:var(--w-display) {fs}/1 var(--font-display)">{html.escape(b)}</text>
  <g class="ink is-accent"><path pathLength="1" d="M{x1} {cy} C {x1 + (x2 - x1) * 0.3} {cy - nh * 0.7}, {x1 + (x2 - x1) * 0.7} {cy - nh * 0.7}, {x2} {cy}"/>
  <path pathLength="1" d="M{x2 - 34} {cy - 30} L{x2} {cy} L{x2 - 42} {cy + 8}"/></g>
  <text x="{w // 2}" y="{cy - nh * 0.7 - 24}" text-anchor="middle" style="fill:var(--accent);font:var(--w-display) var(--fs-h3)/1 var(--font-display)">{html.escape(smp['relation'])}</text>
</svg>'''


def sketch_diagram(s, smp, w=760, h=420):
    """手寫感版本的示意圖：用 sketch.js（Rough.js）畫，seed 固定，所以每次渲染長得一樣。"""
    a, b = (json.dumps(x, ensure_ascii=False) for x in smp['nodes'])
    rel = json.dumps(smp['relation'], ensure_ascii=False)
    n = int(min(220, w * 0.26)); nh = int(n * 0.75); cy = h // 2
    return (f'<svg id="skd" width="{w}" height="{h}" style="overflow:visible"></svg>'
            f'<script>addEventListener("DOMContentLoaded",()=>{{const v=document.getElementById("skd");'
            f'SK.line(v,30,{h - 40},{w - 30},{h - 40},{{id:"g0",stroke:"ink-2",width:2}});'
            f'SK.rect(v,40,{cy - nh // 2},{n},{nh},{{id:"n1",fill:"primary-wash"}});SK.text(v,{40 + n // 2},{cy},{a},{{id:"t1",size:"h2"}});'
            f'SK.ellipse(v,{w - 40 - n // 2},{cy},{n},{nh},{{id:"n2",fill:"accent-2-wash"}});SK.text(v,{w - 40 - n // 2},{cy},{b},{{id:"t2",size:"h2"}});'
            f'SK.arrow(v,{40 + n + 14},{cy - 10},{w - 40 - n - 10},{cy - 6},{{id:"ar",stroke:"accent",bend:{int(nh * 0.6)}}});'
            f'SK.text(v,{w // 2},{cy - int(nh * 0.6) - 40},{rel},{{id:"t3",size:"h3",color:"accent"}});}});</script>')


def iso_diagram(smp, w=860, h=560):
    """等距示意：浮在空中的展台＋三個積木，每個面三種明度（上亮、左中、右暗），引線標籤。"""
    import math
    k, c30, ox, oy = 46, math.cos(math.pi / 6), w / 2, 150
    P = lambda x, y, z: (ox + (x - y) * c30 * k, oy + ((x + y) / 2 - z) * k)
    pts = lambda *q: ' '.join(f'{a:.1f},{b:.1f}' for a, b in (P(*p) for p in q))
    def block(x, y, z, dx, dy, dz, hue):
        top = f'color-mix(in oklab, var(--{hue}) 78%, white)'
        left = f'var(--{hue})'
        right = f'color-mix(in oklab, var(--{hue}) 74%, var(--ink))'
        return (f'<polygon points="{pts((x, y + dy, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x, y + dy, z + dz))}" style="fill:{left}"/>'
                f'<polygon points="{pts((x + dx, y, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x + dx, y, z + dz))}" style="fill:{right}"/>'
                f'<polygon points="{pts((x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz))}" style="fill:{top}"/>')
    def pin(x, y, z, text, dx, dy):
        sx, sy = P(x, y, z)
        return (f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" style="fill:var(--surface);stroke:var(--ink);stroke-width:2.5"/>'
                f'<polyline points="{sx:.1f},{sy:.1f} {sx:.1f},{sy + dy:.1f} {sx + dx:.1f},{sy + dy:.1f}" style="fill:none;stroke:var(--ink);stroke-width:2"/>'
                f'<text x="{sx + dx + (10 if dx > 0 else -10):.1f}" y="{sy + dy:.1f}" text-anchor="{"start" if dx > 0 else "end"}" dominant-baseline="central" '
                f'style="font:var(--w-display) var(--fs-label)/1 var(--font-display);fill:var(--ink);paint-order:stroke;stroke:var(--bg);stroke-width:7px">{html.escape(text)}</text>')
    a, b = smp['nodes']
    s = [block(0, 0, -1.2, 7, 5, 1.2, 'ink-2'), block(0, 0, -0.35, 7, 5, 0.35, 'accent-2')]  # 展台＋地層
    s += [block(1, 1, 0, 2, 2, 2.2, 'primary'), block(4.2, 1.2, 0, 1.6, 1.6, 1.2, 'accent'), block(4.4, 3.4, 0, 1.2, 1.2, 0.6, 'accent')]
    r1, r2 = P(3, 2, 0.05), P(4.2, 2, 0.05)
    s.append(f'<line x1="{r1[0]:.1f}" y1="{r1[1]:.1f}" x2="{r2[0]:.1f}" y2="{r2[1]:.1f}" style="stroke:var(--ink);stroke-width:3;stroke-dasharray:10 8"/>')
    s += [pin(2, 2, 2.2, a, -150, -70), pin(5, 2, 1.2, b, 150, -90), pin(5, 4, 0.6, smp["relation"] + " ×3", 140, 80)]
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="overflow:visible">{"".join(s)}</svg>'


def screencast_html(smp):
    """實機錄屏：重畫的應用程式視窗＋游標＋像素小助手＋按鍵提示，畫面上沒有真截圖。"""
    mascot = ''.join(f'<i style="grid-column:{c + 1};grid-row:{r + 1}"></i>' for r, row in enumerate(['.XXXX.', 'XXXXXX', 'X.XX.X', 'XXXXXX', '.X..X.']) for c, ch in enumerate(row) if ch == 'X')
    return (f'<div class="win" style="position:absolute;left:120px;top:96px;width:1680px;height:760px">'
            f'<div class="win-bar"><span></span><span></span><span></span><b>{html.escape(smp["kicker"])}．文件</b></div>'
            f'<div style="display:grid;grid-template-columns:300px 1fr;height:calc(100% - 56px)">'
            f'<div class="win-side"><p class="on">大綱</p><p>例句庫</p><p>語料統計</p><p>匯出</p></div>'
            f'<div style="padding:56px 72px;display:flex;flex-direction:column;gap:32px">'
            f'<h1 class="t-h2">{title_html(smp["title"].replace("|", ""))}</h1>'
            f'<div class="win-input" style="margin-bottom:40px">{html.escape(smp["body"][:22])}<span class="caret"></span></div>'
            f'<div style="display:flex;gap:20px;align-items:flex-end"><span class="win-btn" style="position:relative">插入例句'
            f'<span class="pix" style="position:absolute;left:30px;bottom:100%">{mascot}</span></span><span class="win-btn ghost">比較用法</span></div>'
            f'</div></div></div>'
            f'<svg class="cursor" style="left:560px;top:600px" width="44" height="56" viewBox="0 0 22 28"><path d="M2 2 L2 22 L7 17 L11 26 L14 25 L10 16 L17 16 Z"/></svg>'
            f'<div class="hud-key">⌘ K</div><div class="chapter-pill">02 插入例句</div>')


def scroll_html(smp):
    """水墨：大片留白、遠山淡墨、近山濃墨、直排題字、朱紅印章、題跋字幕。"""
    return ('<svg class="layer" viewBox="0 0 1920 1080" preserveAspectRatio="none">'
            '<defs><filter id="bleed"><feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="3"/><feDisplacementMap in="SourceGraphic" scale="38"/><feGaussianBlur stdDeviation="2.5"/></filter>'
            '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--ink)" stop-opacity="1"/><stop offset="1" stop-color="var(--ink)" stop-opacity="0"/></linearGradient></defs>'
            '<g filter="url(#bleed)">'
            '<path d="M-40 760 C 220 520, 360 470, 520 600 C 640 420, 820 380, 980 640 L 980 900 L -40 900 Z" fill="url(#fade)" opacity=".16"/>'
            '<path d="M260 820 C 420 560, 560 470, 700 640 C 760 560, 860 520, 940 700 L 940 960 L 260 960 Z" fill="url(#fade)" opacity=".34"/>'
            '<path d="M1180 900 C 1280 640, 1400 560, 1500 720 C 1560 640, 1640 660, 1720 780 L 1720 1000 L 1180 1000 Z" fill="url(#fade)" opacity=".6"/>'
            '</g>'
            '<path d="M380 905 q 120 -6 260 2 M 520 930 q 160 -4 300 3" stroke="var(--ink)" stroke-opacity=".35" stroke-width="3" fill="none" stroke-linecap="round"/>'
            '<g transform="translate(700 860)"><ellipse cx="0" cy="0" rx="9" ry="22" fill="var(--ink)" opacity=".8"/><circle cx="0" cy="-30" r="8" fill="var(--ink)" opacity=".9"/><circle cx="12" cy="-8" r="5" fill="var(--accent)"/></g>'
            '</svg>'
            f'<div style="position:absolute;right:220px;top:120px;writing-mode:vertical-rl;font:var(--w-display) var(--fs-h1)/1.3 var(--font-display);letter-spacing:.2em;color:var(--ink)">{html.escape(smp["breath"])}</div>'
            f'<div style="position:absolute;right:150px;top:120px;writing-mode:vertical-rl;font:var(--w-body) var(--fs-label)/1.6 var(--font-body);color:var(--ink-2)">{html.escape(smp["kicker"])}</div>'
            '<div class="seal" style="position:absolute;right:150px;top:730px">知方</div>')


def title_html(t):
    """[[字]] → 螢光筆；| → 手動分行（標題不要讓瀏覽器在詞中間斷行）。"""
    t = re.sub(r'\[\[(.+?)\]\]', r'<span class="hl">\1</span>', html.escape(t).replace('&quot;', '"'))
    return ''.join(f'<span class="line">{x}</span>' for x in t.split('|')) if '|' in t else t


def scene_html(s, smp):
    comps, tex = set(s.get('components', [])), ' '.join(s.get('texture', []))
    kicker = f'<div class="kicker">{html.escape(smp["kicker"])}</div>'
    title = f'<h1 class="t-h1">{title_html(smp["title"])}</h1>'
    body = f'<p class="t-body c-muted" style="max-width:760px">{html.escape(smp["body"])}</p>'
    stat = f'<div><div class="stat t-num">{html.escape(smp["stat"])}<small>{html.escape(smp["unit"])}</small></div><div class="t-label">{html.escape(smp["stat_label"])}</div></div>'
    cap = f'<div class="caption-bar">{html.escape(smp["caption"]).replace("方向", "<span class=kw>方向</span>")}</div>'
    card_cls = 'card card--cutout' if 'card--cutout' in comps else ('card card--ghost' if 'card--ghost' in comps else 'card')
    sk = (s.get('sketch') or {}).get('board')
    dia = sketch_diagram(s, smp) if sk else diagram(s, smp)
    visual = f'<div class="{card_cls}" style="display:inline-block">{dia}</div>' if not sk else f'<div style="display:inline-block">{dia}</div>'
    if 'shot' in comps:  # 截圖卡：沒有真圖就放誠實的佔位
        visual = ('<div style="position:relative;display:flex;flex-direction:column;gap:72px;align-items:flex-start">'
                  '<div class="shot" style="width:620px"><div class="tape"></div>'
                  '<div style="height:250px;display:grid;place-items:center;background:color-mix(in oklab,var(--ink) 8%,var(--surface));" class="t-label">真實截圖放這裡</div>'
                  '<div class="src">來源：example.com</div></div>'
                  f'<div class="{card_cls}" style="margin-left:120px;padding:24px 32px">{diagram(s, smp, 620, 300)}</div></div>')
    lay = s.get('board', 'split')
    if lay == 'iso':
        inner = (f'<div class="safe" style="display:grid;grid-template-columns:5fr 6fr;gap:24px;align-items:center">'
                 f'<div style="display:flex;flex-direction:column;gap:32px">{kicker}{title}{body}</div>'
                 f'<div>{iso_diagram(smp)}</div></div>')
    elif lay == 'screencast':
        inner = screencast_html(smp)
    elif lay == 'scroll':
        inner = scroll_html(smp)
    elif lay == 'center':
        inner = (f'<div class="safe" style="display:flex;flex-direction:column;align-items:center;text-align:center;gap:36px">'
                 f'{kicker}{title}{visual}</div>')
    elif lay == 'editorial':
        inner = ('<div style="position:absolute;right:0;top:0;width:36%;height:100%;background:var(--accent)"></div>'
                 f'<div class="safe" style="display:grid;grid-template-columns:7fr 5fr;gap:64px">'
                 f'<div style="display:flex;flex-direction:column;gap:40px;margin-left:-24px">{kicker}{title}{body}</div>'
                 f'<div style="display:flex;flex-direction:column;justify-content:center;gap:24px;z-index:1">{stat}</div></div>')
    elif lay == 'stage':
        inner = ('<div class="layer"><div style="position:absolute;left:68%;top:6%;width:420px;height:420px;border-radius:50%;background:var(--accent-2);opacity:.85"></div>'
                 '<div style="position:absolute;left:-6%;top:58%;width:640px;height:640px;border-radius:50%;background:var(--surface)"></div>'
                 '<div style="position:absolute;left:78%;top:62%;width:120px;height:120px;border-radius:50%;background:var(--accent)"></div></div>'
                 f'<div class="safe" style="display:flex;flex-direction:column;gap:48px">{kicker}{title}'
                 f'<div style="align-self:center;z-index:1">{diagram(s, smp)}</div></div>')
    else:  # split
        inner = (f'<div class="safe" style="display:grid;grid-template-columns:5fr 6fr;gap:72px;align-items:center">'
                 f'<div style="display:flex;flex-direction:column;gap:36px">{kicker}{title}{body}{stat}</div>'
                 f'<div style="justify-self:center">{visual}</div></div>')
    return f'<div class="stage {tex}">{inner}{cap}</div>'


ICONS = {  # 示範用的簡單線條圖示（24 格，自行繪製）
    'leaf': '<path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14z"/><path d="M5 19l8-8"/>',
    'bulb': '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z"/>',
    'book': '<path d="M4 5h6a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4z"/><path d="M20 5h-6a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6z"/>',
}


def demo_html(s):
    """素材示範：同一張照片、同一組圖示、同一組文字元素，套這個風格後的樣子。"""
    a = s['assets']; ph = a['photo']; ic = a['icon']
    if ph.get('allowed', True):
        photo = '<img data-as="photo" data-src="範例" alt="範例照片" src="sample-photo.jpg" style="width:440px">'
    else:
        photo = (f'<div style="width:440px;height:275px;display:grid;place-items:center;text-align:center;border:3px dashed var(--ink-2);color:var(--ink-2);'
                 f'font:600 var(--fs-label)/1.4 var(--font-body);padding:20px">不用照片<br>{html.escape(ph.get("instead", ""))}</div>')
    if ic['mode'] == 'none':
        icons = '<p class="el-label" style="margin:0">不用圖示</p>'
    else:
        icons = ''.join(f'<svg data-as="icon" id="demo-ic-{k}" class="{"is-accent" if k == "bulb" else ""}" viewBox="0 0 24 24" width="110" height="110">{d}</svg>' for k, d in ICONS.items())
    return (f'<div class="demo"><div class="demo-in stage {" ".join(s.get("texture", []))}" style="width:1160px;height:600px">'
            f'<div style="position:absolute;left:40px;top:40px;z-index:1">{photo}</div>'
            f'<div style="position:absolute;left:560px;top:40px;right:40px;display:flex;flex-direction:column;gap:26px;z-index:1">'
            f'<div style="display:flex;gap:34px;align-items:center">{icons}</div>'
            f'<div style="display:flex;gap:28px;align-items:baseline"><span class="el-label">葉綠體</span><span class="el-num">3.2<small>倍</small></span></div>'
            f'<p class="el-quote">光合作用把<span class="el-emph">光能</span>變成化學能</p></div></div></div>')


def grammar_html(s):
    ess = ''.join(f'<li>{html.escape(x)}</li>' for x in s.get('essence', [])[:4])
    nots = '；'.join(s.get('not', [])[:2])
    moves = '、'.join(m['name'] for m in s.get('native_moves', [])[:5])
    return (f'<h2>辨識特徵</h2><ul>{ess}</ul><p class="not">不是：{html.escape(nots)}</p>'
            f'<h2>原生招式</h2><p style="margin:0">{html.escape(moves)}</p>')


def board_html(s, smp):
    c, t, m = s['color'], s['type'], s['motion']
    sw = ''.join(
        f'<div class="sw"><i style="background:{c[k]}"></i><b>{k}</b><span>{c[k]}</span><em>{html.escape(s.get("color_semantics", {}).get(k, ""))}</em></div>'
        for k in REQUIRED_COLORS)
    rep = contrast_report(s)
    bad = [x for x in rep if x[2] < x[3]]
    cr = (''.join(f'<li class="bad">{fg} / {bg}　{r:.1f}:1 ✗ 低於 {need}</li>' for fg, bg, r, need in bad) if bad
          else f'<li>{len(rep)} 組全部通過（最低 {min(x[2] for x in rep):.1f}:1）</li>')
    ts = '<p style="margin:4px 0">' + '　'.join(f'<b>{k}</b> {t["scale"][k]}' for k in ('h1', 'h2', 'h3', 'body', 'label', 'caption')) + '　(px)</p>'
    mo = '<p style="margin:0">' + '　'.join(f'<b>{k}</b> {m["ease"][k]} {m["dur"][k]}s' for k in ('enter', 'exit', 'pop', 'move', 'draw')) + '</p>'
    skp = s.get('sketch')
    skl = (f'<p style="margin:2px 0 0">手寫感：roughness {skp["roughness"]}　bowing {skp["bowing"]}　填色 {skp["fill_style"]}</p>' if skp else '')
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{html.escape(s["name"])} 風格板</title>
<link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="kit.css">
<script src="tokens.js"></script><script src="rough.js"></script><script src="sketch.js"></script><script src="assets.js"></script>
<style>
 html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#E9E7E2;font-family:"Noto Sans TC",sans-serif;color:#222}}
 .preview{{position:absolute;left:40px;top:40px;zoom:0.64;box-shadow:0 20px 60px -20px rgba(0,0,0,.45)}}
 .meta{{position:absolute;left:40px;top:770px;width:630px}}
 .demo{{position:absolute;left:690px;top:762px;width:580px;height:300px;overflow:hidden;border-radius:6px;box-shadow:0 10px 30px -16px rgba(0,0,0,.45)}}
 .demo-in{{zoom:.5}} .demo .el-num{{font-size:calc(var(--fs-stat) * .62)}} .demo-tag{{position:absolute;left:690px;top:740px;font-size:14px;letter-spacing:.12em;color:#777;font-weight:700}}
 .meta h1{{margin:0 0 6px;font-size:40px}} .meta p{{margin:4px 0;font-size:19px;color:#444}}
 .meta .tag{{display:inline-block;padding:2px 12px;border:1.5px solid #222;border-radius:99px;font-size:18px;margin-right:8px}}
 .panel{{position:absolute;left:1300px;top:36px;width:590px;font-size:16px;line-height:1.35}}
 .panel h2{{font-size:14px;letter-spacing:.12em;color:#777;margin:14px 0 6px;font-weight:700}}
 .sw{{display:grid;grid-template-columns:40px 84px 100px 1fr;gap:8px;align-items:center;margin:3px 0}}
 .sw i{{width:40px;height:26px;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}} .sw span{{font-family:monospace}} .sw em{{font-style:normal;color:#666;font-size:15px}}
 ul{{margin:0;padding-left:18px}} li.bad{{color:#B42318;font-weight:700}} .not{{margin:4px 0 0;color:#8a3b12;font-size:15px}}
 .spec{{font-family:var(--font-display);font-weight:var(--w-display);font-size:36px;margin:2px 0}}
 .specb{{font-family:var(--font-body);font-size:22px;margin:2px 0}}
</style></head><body>
<div class="preview">{scene_html(s, smp)}</div>
<div class="demo-tag">素材對齊示範（照片／圖示／標籤／數字／引文／強調）</div>{demo_html(s)}
<script>addEventListener("DOMContentLoaded",()=>AS.apply(document.querySelector(".demo")));</script>
<div class="meta"><h1>{html.escape(s["name"])}</h1>
 <span class="tag">{html.escape(s.get("temperature", ""))}</span>{''.join(f'<span class="tag">{html.escape(x)}</span>' for x in s.get("fits", [])[:4])}
 <p>{html.escape(s.get("positioning", ""))}</p><p>參照：{html.escape("、".join(s.get("benchmarks", [])))}</p>
 <p style="font-size:18px;color:#666">{html.escape(s.get("rationale", ""))}</p></div>
<div class="panel"><h2>色票（語意）</h2>{sw}<h2>對比度</h2><ul>{cr}</ul>
 <h2>字型</h2><div class="spec">標題 永字八法 Aa 123</div>{ts}
 <h2>動態</h2>{mo}<p style="margin:2px 0 0"><b>stagger</b> {m["stagger"]}s　<b>hold</b> {m["dur"].get("hold", 0.5)}s</p>{skl}
 {grammar_html(s)}<h2>字幕</h2><p style="margin:0">{html.escape(s.get("caption", {}).get("world", ""))}</p></div>
</body></html>'''


def main():
    ap = argparse.ArgumentParser(description='風格卡 → tokens.css／tokens.js／tokens.json／kit.css／board.html')
    ap.add_argument('style', nargs='?'); ap.add_argument('--out', default='style')
    ap.add_argument('--sample'); ap.add_argument('--colors-from'); ap.add_argument('--type-from')
    ap.add_argument('--set', action='append', default=[], metavar='路徑=值')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--local-fonts', action='store_true', help='不寫 Google Fonts @import；改用 font_subset.py 產生的本機字型（正式渲染用）')
    a = ap.parse_args()
    if a.list or not a.style:
        for f in sorted(os.listdir(STYLES)):
            if f.endswith('.json'):
                s = json.load(open(os.path.join(STYLES, f), encoding='utf-8'))
                print(f'{s["id"]:<14} {s["temperature"]:<6} {s["name"]}｜適合：{"、".join(s["fits"][:3])}')
        return
    s = copy.deepcopy(load_style(a.style))
    if a.colors_from:
        o = load_style(a.colors_from)
        s['color'], s['color_semantics'] = o['color'], o.get('color_semantics', {})
        s['caption'] = o.get('caption', s.get('caption'))
        s['mixed_from'] = s.get('mixed_from', []) + [f'color←{o["id"]}']
    if a.type_from:
        o = load_style(a.type_from)
        s['type'] = o['type']; s['mixed_from'] = s.get('mixed_from', []) + [f'type←{o["id"]}']
    for kv in a.set:
        k, _, val = kv.partition('=')
        set_path(s, k, val)
    validate(s)
    if a.local_fonts:
        s['_local_fonts'] = True
    smp = dict(DEFAULT_SAMPLE, **(json.load(open(a.sample, encoding='utf-8')) if a.sample else {}))
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, 'tokens.css'), 'w', encoding='utf-8').write(tokens_css(s))
    open(os.path.join(a.out, 'tokens.js'), 'w', encoding='utf-8').write(tokens_js(s))
    json.dump(s, open(os.path.join(a.out, 'tokens.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(STYLES, 'kit.css'), os.path.join(a.out, 'kit.css'))
    shutil.copy(os.path.join(STYLES, 'sketch.js'), os.path.join(a.out, 'sketch.js'))
    shutil.copy(os.path.join(STYLES, '..', 'vendor', 'rough.js'), os.path.join(a.out, 'rough.js'))
    shutil.copy(os.path.join(STYLES, 'assets.js'), os.path.join(a.out, 'assets.js'))
    shutil.copy(os.path.join(STYLES, 'sample-photo.jpg'), os.path.join(a.out, 'sample-photo.jpg'))
    open(os.path.join(a.out, 'board.html'), 'w', encoding='utf-8').write(board_html(s, smp))
    print(f'已套用「{s["name"]}」→ {a.out}/（tokens.css、tokens.js、tokens.json、kit.css、sketch.js、rough.js、assets.js、board.html）')
    for fg, bg, r, need in contrast_report(s):
        if r < need:
            print(f'  ⚠ 對比度不足：{fg} 在 {bg} 上只有 {r:.1f}:1（需要 {need}:1）→ 這個顏色只能用在大字或圖形，或調整色值')
    print(f'  風格板截圖：npx playwright screenshot --viewport-size=1920,1080 --wait-for-timeout=2000 file://{os.path.abspath(a.out)}/board.html {a.out}/board.png')


if __name__ == '__main__':
    main()
