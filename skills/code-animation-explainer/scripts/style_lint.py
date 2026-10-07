#!/usr/bin/env python3
"""檢查場景檔有沒有偏離選定的風格（風格敏感度的守門員）。

用法：
  python style_lint.py style/tokens.json compositions/ [更多檔案或資料夾…]
  python style_lint.py style/tokens.json scene-03.html --strict      # 警告也算失敗
掃描 .html／.css／.js；回傳碼：有錯誤＝1，否則 0（--strict 時有警告也是 1）。
某一行確定是刻意的，在行尾加註解 lint-ok 即可略過該行。

錯誤（一定要修）：
  色碼不在風格卡色票裡；寫死 font-family；字級小於風格卡的 small；linear easing；
  Math.random()／Date.now()（無法逐格重現）
警告（多半該修）：
  GSAP ease 不是風格卡定義的那幾種；寫死 duration（請用 M.in()／M.out() 等）；
  寫死 px 字級但不在字級表裡；CSS transition（seek 不安全）；<br> 斷行；emoji 當圖示；
  rgb()/hsl() 字面色（請用 var(--…) 或 color-mix）
"""
import argparse, json, os, re, sys

HEX = re.compile(r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
FONT_FAMILY = re.compile(r'font-family\s*:\s*([^;}"\n]+)')
FONT_SIZE = re.compile(r'font-size\s*:\s*(\d+(?:\.\d+)?)px')
FONT_SHORT = re.compile(r'font\s*:\s*[^;]*?(\d+(?:\.\d+)?)px')
EASE = re.compile(r'''ease\s*:\s*["']([^"']+)["']''')
DURATION = re.compile(r'\bduration\s*:\s*(\d+(?:\.\d+)?)')
TRANSITION = re.compile(r'(?<![-\w])transition\s*:\s*(?!none)')
RGB = re.compile(r'\b(?:rgba?|hsla?)\(\s*\d')
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿]')
NONDET = re.compile(r'Math\.random\(|Date\.now\(|performance\.now\(')
SKIP_DIRS = {'node_modules', '.git', 'renders', 'out'}


def norm_hex(h):
    h = h.lower().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return '#' + h


def collect(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in sorted(files):
                    if f.endswith(('.html', '.css', '.js')) and not f.startswith(('tokens.', 'kit.')):
                        yield os.path.join(root, f)
        elif os.path.isfile(p):
            yield p


def strip_comments_keep_lines(text):
    # 把 /* … */ 與 <!-- … --> 換成同樣行數的空白，行號才對得上；保留 lint-ok 標記
    def blank(m):
        s = m.group(0)
        return ('lint-ok' if 'lint-ok' in s else '') + '\n' * s.count('\n')
    text = re.sub(r'/\*.*?\*/', blank, text, flags=re.S)
    return re.sub(r'<!--.*?-->', blank, text, flags=re.S)


def lint_file(path, style):
    palette = {norm_hex(v) for v in style['color'].values() if isinstance(v, str) and v.startswith('#')}
    palette |= {norm_hex(x) for x in style.get('lint', {}).get('extra_colors', [])}
    eases = set(style['motion']['ease'].values()) | {'none'} - {'linear'}
    durs = {float(v) for v in style['motion']['dur'].values()} | {0.0}
    scale = {float(v) for v in style['type']['scale'].values()}
    floor = float(style['type']['scale']['small'])
    errs, warns = [], []
    raw = open(path, encoding='utf-8', errors='replace').read()
    lines = strip_comments_keep_lines(raw).split('\n')
    is_js = path.endswith('.js')
    for n, line in enumerate(lines, 1):
        if 'lint-ok' in line:
            continue
        loc = f'{path}:{n}'
        if not line.lstrip().startswith('//'):
            for h in HEX.findall(line):
                if norm_hex(h) not in palette:
                    errs.append(f'{loc}  色碼 {h} 不在風格卡色票裡 → 改用 var(--…)；確定要新增就先加進風格卡')
        for fam in FONT_FAMILY.findall(line):
            if 'var(--font' not in fam and 'inherit' not in fam:
                errs.append(f'{loc}  寫死字型 {fam.strip()[:40]} → 改用 var(--font-display／body／mono／hand)')
        for px in FONT_SIZE.findall(line) + FONT_SHORT.findall(line):
            v = float(px)
            if v < floor:
                errs.append(f'{loc}  字級 {px}px 小於風格卡下限 {floor:g}px（教室最後一排看不到）')
            elif v not in scale:
                warns.append(f'{loc}  字級 {px}px 不在字級表 → 改用 .t-h1／.t-body… 或 var(--fs-…)')
        for e in EASE.findall(line):
            if e in ('linear', 'none') and e not in style['motion']['ease'].values():
                errs.append(f'{loc}  ease "{e}" 是線性運動，教學動畫一律用風格卡的 easing（M.in()／M.move()…）')
            elif e not in eases:
                warns.append(f'{loc}  ease "{e}" 不是這個風格的 easing（{"、".join(sorted(eases - {"none"}))}）')
        if is_js or '<script' in raw:
            for d in DURATION.findall(line):
                if float(d) not in durs:
                    warns.append(f'{loc}  寫死 duration {d} → 用 M.in()／M.out()／M.pop()／M.move()／M.draw() 帶入風格卡時長')
        if NONDET.search(line):
            errs.append(f'{loc}  Math.random／Date.now 會讓每次渲染不同 → 用固定種子 PRNG、由時間軸 t 計算')
        if TRANSITION.search(line) and not is_js:
            warns.append(f'{loc}  CSS transition 在逐格 seek 渲染下不可靠 → 改由 GSAP 補間')
        if RGB.search(line):
            warns.append(f'{loc}  rgb()/hsl() 字面色 → 改用 var(--…) 或 color-mix(in oklab, var(--ink) 30%, transparent)')
        if '<br' in line:
            warns.append(f'{loc}  <br> 斷行 → 改用 <span class="line">')
        if EMOJI.search(line):
            warns.append(f'{loc}  emoji 當圖示會讓畫面變成 AI 模板感 → 改用 Lucide／Tabler 等開放授權圖示')
    return errs, warns


def main():
    ap = argparse.ArgumentParser(description='檢查場景檔是否遵守風格卡')
    ap.add_argument('tokens'); ap.add_argument('paths', nargs='+'); ap.add_argument('--strict', action='store_true')
    a = ap.parse_args()
    style = json.load(open(a.tokens, encoding='utf-8'))
    files = list(collect(a.paths))
    if not files:
        sys.exit('沒有找到 .html／.css／.js 檔')
    E, W = [], []
    for f in files:
        e, w = lint_file(f, style)
        E += e; W += w
    for x in E:
        print('✗', x)
    for x in W:
        print('△', x)
    print(f'\n風格「{style["name"]}」：檢查 {len(files)} 個檔案，錯誤 {len(E)}、警告 {len(W)}')
    sys.exit(1 if E or (a.strict and W) else 0)


if __name__ == '__main__':
    main()
