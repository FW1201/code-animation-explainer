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
  board.html   1920×1080 風格板：範例畫面＋色票（含對比度）＋字級＋動態參數。截圖後就是方向板
sample.json 欄位：kicker, title（[[ ]] 標螢光筆重點、| 手動分行）, body, stat, unit, stat_label, nodes[2], relation, caption, breath。
"""
import argparse, copy, html, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STYLES = os.path.join(HERE, '..', 'assets', 'styles')
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
    if fams:
        lines.append(f'@import url("https://fonts.googleapis.com/css2?{fams}&display=swap");')
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
    v['--tilt'] = L.get('tilt', '0deg'); v['--shadow'] = L.get('shadow', 'none'); v['--tex-opacity'] = L.get('tex_opacity', 0)
    lines.append(':root {')
    lines += [f'  {k}: {val};' for k, val in v.items()]
    lines.append('}')
    lines.append(f'/* 這個風格預設要掛的材質：<div class="stage {" ".join(s.get("texture", []))}"> */')
    return '\n'.join(lines) + '\n'


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
    visual = f'<div class="{card_cls}" style="display:inline-block">{diagram(s, smp)}</div>'
    if 'shot' in comps:  # 截圖卡：沒有真圖就放誠實的佔位
        visual = ('<div style="position:relative;display:flex;flex-direction:column;gap:72px;align-items:flex-start">'
                  '<div class="shot" style="width:620px"><div class="tape"></div>'
                  '<div style="height:250px;display:grid;place-items:center;background:color-mix(in oklab,var(--ink) 8%,var(--surface));" class="t-label">真實截圖放這裡</div>'
                  '<div class="src">來源：example.com</div></div>'
                  f'<div class="{card_cls}" style="margin-left:120px;padding:24px 32px">{diagram(s, smp, 620, 300)}</div></div>')
    lay = s.get('board', 'split')
    if lay == 'center':
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


def board_html(s, smp):
    c, t, m = s['color'], s['type'], s['motion']
    sw = ''.join(
        f'<div class="sw"><i style="background:{c[k]}"></i><b>{k}</b><span>{c[k]}</span><em>{html.escape(s.get("color_semantics", {}).get(k, ""))}</em></div>'
        for k in REQUIRED_COLORS)
    cr = ''.join(f'<li class="{"bad" if r < need else ""}">{fg} / {bg}　{r:.1f}:1 {"✓" if r >= need else "✗ 低於 " + str(need)}</li>' for fg, bg, r, need in contrast_report(s))
    ts = '<p style="margin:4px 0">' + '　'.join(f'<b>{k}</b> {t["scale"][k]}' for k in ('h1', 'h2', 'h3', 'body', 'label', 'caption')) + '　(px)</p>'
    mo = ''.join(f'<li><b>{k}</b> {m["ease"][k]} · {m["dur"][k]}s</li>' for k in ('enter', 'exit', 'pop', 'move', 'draw'))
    sig = ''.join(f'<li>{html.escape(x)}</li>' for x in m.get('signature', []))
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{html.escape(s["name"])} 風格板</title>
<link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="kit.css">
<style>
 html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#E9E7E2;font-family:"Noto Sans TC",sans-serif;color:#222}}
 .preview{{position:absolute;left:40px;top:40px;zoom:0.64;box-shadow:0 20px 60px -20px rgba(0,0,0,.45)}}
 .meta{{position:absolute;left:40px;top:770px;width:1220px}}
 .meta h1{{margin:0 0 6px;font-size:44px}} .meta p{{margin:4px 0;font-size:22px;color:#444}}
 .meta .tag{{display:inline-block;padding:2px 12px;border:1.5px solid #222;border-radius:99px;font-size:18px;margin-right:8px}}
 .panel{{position:absolute;left:1300px;top:36px;width:590px;font-size:16px;line-height:1.35}}
 .panel h2{{font-size:14px;letter-spacing:.12em;color:#777;margin:14px 0 6px;font-weight:700}}
 .sw{{display:grid;grid-template-columns:40px 84px 100px 1fr;gap:8px;align-items:center;margin:3px 0}}
 .sw i{{width:40px;height:26px;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}} .sw span{{font-family:monospace}} .sw em{{font-style:normal;color:#666;font-size:15px}}
 ul{{margin:0;padding-left:18px}} li.bad{{color:#B42318;font-weight:700}}
 .spec{{font-family:var(--font-display);font-weight:var(--w-display);font-size:36px;margin:2px 0}}
 .specb{{font-family:var(--font-body);font-size:22px;margin:2px 0}}
</style></head><body>
<div class="preview">{scene_html(s, smp)}</div>
<div class="meta"><h1>{html.escape(s["name"])}</h1>
 <span class="tag">{html.escape(s.get("temperature", ""))}</span>{''.join(f'<span class="tag">{html.escape(x)}</span>' for x in s.get("fits", [])[:4])}
 <p>{html.escape(s.get("positioning", ""))}</p><p>參照：{html.escape("、".join(s.get("benchmarks", [])))}</p>
 <p style="font-size:18px;color:#666">{html.escape(s.get("rationale", ""))}</p></div>
<div class="panel"><h2>色票（語意）</h2>{sw}<h2>對比度</h2><ul>{cr}</ul>
 <h2>字型</h2><div class="spec">標題 永字八法 Aa 123</div><div class="specb">內文：同樣是介詞，「對」把動作射向一個對象。</div>{ts}
 <h2>動態</h2><ul>{mo}<li><b>stagger</b> {m["stagger"]}s　<b>hold</b> {m["dur"].get("hold", 0.5)}s</li></ul>
 <h2>招牌動作</h2><ul>{sig}</ul><h2>轉場</h2><p style="margin:0">{html.escape(s.get("transition", {}).get("default", ""))}／{html.escape(s.get("transition", {}).get("chapter", ""))}</p></div>
</body></html>'''


def main():
    ap = argparse.ArgumentParser(description='風格卡 → tokens.css／tokens.js／tokens.json／kit.css／board.html')
    ap.add_argument('style', nargs='?'); ap.add_argument('--out', default='style')
    ap.add_argument('--sample'); ap.add_argument('--colors-from'); ap.add_argument('--type-from')
    ap.add_argument('--set', action='append', default=[], metavar='路徑=值')
    ap.add_argument('--list', action='store_true')
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
    smp = dict(DEFAULT_SAMPLE, **(json.load(open(a.sample, encoding='utf-8')) if a.sample else {}))
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, 'tokens.css'), 'w', encoding='utf-8').write(tokens_css(s))
    open(os.path.join(a.out, 'tokens.js'), 'w', encoding='utf-8').write(tokens_js(s))
    json.dump(s, open(os.path.join(a.out, 'tokens.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(STYLES, 'kit.css'), os.path.join(a.out, 'kit.css'))
    open(os.path.join(a.out, 'board.html'), 'w', encoding='utf-8').write(board_html(s, smp))
    print(f'已套用「{s["name"]}」→ {a.out}/（tokens.css、tokens.js、tokens.json、kit.css、board.html）')
    for fg, bg, r, need in contrast_report(s):
        if r < need:
            print(f'  ⚠ 對比度不足：{fg} 在 {bg} 上只有 {r:.1f}:1（需要 {need}:1）→ 這個顏色只能用在大字或圖形，或調整色值')
    print(f'  風格板截圖：npx playwright screenshot --viewport-size=1920,1080 --wait-for-timeout=2000 file://{os.path.abspath(a.out)}/board.html {a.out}/board.png')


if __name__ == '__main__':
    main()
