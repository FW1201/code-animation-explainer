#!/usr/bin/env python3
"""中文字型子集：只下載影片裡真的用到的字，存進專案，渲染時不用連網。

用法：
  python font_subset.py --style style/tokens.json --text script.md storyboard.json compositions/ --out fonts/
  python font_subset.py --family "Noto Sans TC:wght@400;700" --family "Iansui" --text script.md --out fonts/
做法：掃描文字檔收集用到的字（另外固定加上英數與常用標點）→ 用 Google Fonts CSS API 的 &text= 參數
只要這些字 → 下載 woff2 → 產生 fonts/fonts.css（@font-face 指向本機檔案）。
場景改成 <link rel="stylesheet" href="fonts/fonts.css">，並移除 tokens.css 開頭的 Google Fonts @import。
一支 3 分鐘的影片通常用 400–700 個不同的字，每個字型檔約 100–300 KB（完整中文字型 5–15 MB）。
腳本或字卡改字後要重跑，不然新字會變成方框或退回系統字型。
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
BASE = ''.join(chr(c) for c in range(0x20, 0x7f)) + '，。、！？；：「」『』（）—…・／＋－×÷％０１２３４５６７８９'


def gather(paths):
    chars = set(BASE)
    for p in paths:
        files = [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs] if os.path.isdir(p) else [p]
        for f in files:
            if f.endswith(('.md', '.json', '.html', '.js', '.txt', '.srt', '.css')):
                chars |= set(open(f, encoding='utf-8', errors='ignore').read())
    return ''.join(sorted(c for c in chars if c.isprintable() and not c.isspace() or c == ' '))


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()


def main():
    ap = argparse.ArgumentParser(description='Google Fonts 中文子集下載')
    ap.add_argument('--style', help='style/tokens.json：用風格卡 type.google 列出的字型')
    ap.add_argument('--family', action='append', default=[], help='Google Fonts 族名（可帶 :wght@400;700），可重複')
    ap.add_argument('--text', nargs='+', required=True, help='要掃描用字的檔案或資料夾')
    ap.add_argument('--out', default='fonts')
    a = ap.parse_args()
    fams = list(a.family)
    if a.style:
        fams += json.load(open(a.style, encoding='utf-8'))['type'].get('google', [])
    if not fams:
        sys.exit('沒有指定字型：用 --style 或 --family')
    text = gather(a.text)
    os.makedirs(a.out, exist_ok=True)
    css_out, total, seen = [], 0, {}
    for fam in dict.fromkeys(fams):
        q = urllib.parse.urlencode({'family': fam, 'text': text, 'display': 'swap'}, safe=':;@,')
        try:
            css = fetch(f'https://fonts.googleapis.com/css2?{q}').decode()
        except Exception as e:  # 字型名稱打錯、或這個字型沒有這些字重
            print(f'✗ {fam}：{e}'); continue
        for block in re.findall(r'@font-face\s*{[^}]+}', css):
            name = re.search(r"font-family:\s*'([^']+)'", block).group(1)
            weight = re.search(r'font-weight:\s*(\d+)', block).group(1)
            url = re.search(r'src:\s*url\(([^)]+)\)', block).group(1)
            if url not in seen:  # 可變字型的多個字重常指向同一個檔案
                fn = f'{re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")}-{weight}.woff2'
                data = fetch(url)
                open(os.path.join(a.out, fn), 'wb').write(data)
                seen[url] = fn; total += len(data)
                print(f'✓ {name} {weight}：{len(data) / 1024:.0f} KB → {a.out}/{fn}')
            css_out.append(block.replace(f'url({url})', f'url("{seen[url]}")'))
    open(os.path.join(a.out, 'fonts.css'), 'w', encoding='utf-8').write(
        f'/* font_subset.py 產生：{len(text)} 個字元的子集。腳本改字後請重跑。 */\n' + '\n'.join(css_out) + '\n')
    print(f'\n共 {len(text)} 個字元、{len(seen)} 個字型檔、{total / 1024:.0f} KB → {a.out}/fonts.css')


if __name__ == '__main__':
    main()
