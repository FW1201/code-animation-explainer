#!/usr/bin/env python3
"""手寫筆順資料：掃描場景檔用到的中文字，從 hanzi-writer-data 抽出每個字的筆畫輪廓與中線，輸出 hanzi.js。
有了它，sketch.js 的 SK.write() 會照真正的筆順一筆一筆把字寫出來（不是整個字淡入）。

用法：
  python hanzi_prep.py --text script.md compositions/ --out style/hanzi.js
  python hanzi_prep.py --text compositions/ --data node_modules/hanzi-writer-data --out style/hanzi.js
沒有給 --data 時，會用 `npm pack hanzi-writer-data@2.0.1` 下載到暫存資料夾（只在準備時連網）。
資料來源：hanzi-writer-data（Make Me a Hanzi，字形取自文鼎 AR PL KaitiM），授權 Arphic Public License；
輸出檔開頭會附上授權說明，散布時請一併附上 ARPHICPL.TXT（本 skill 的 vendor/hanzi/ 已附）。
"""
import argparse, json, os, re, subprocess, sys, tarfile, tempfile

CJK = re.compile(r'[㐀-鿿豈-﫿]')
EXT = ('.html', '.js', '.md', '.json', '.txt')


def scan(paths):
    chars = set()
    for p in paths:
        files = [p] if os.path.isfile(p) else [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs if f.endswith(EXT)]
        for f in files:
            if f.endswith('hanzi.js') or 'node_modules' in f:
                continue
            chars |= set(CJK.findall(open(f, encoding='utf-8', errors='ignore').read()))
    return sorted(chars)


def fetch(tmp):
    subprocess.run(['npm', 'pack', 'hanzi-writer-data@2.0.1', '--silent'], cwd=tmp, check=True, capture_output=True)
    tgz = [f for f in os.listdir(tmp) if f.endswith('.tgz')][0]
    with tarfile.open(os.path.join(tmp, tgz)) as t:
        t.extractall(tmp, filter='data')
    return os.path.join(tmp, 'package')


def main():
    ap = argparse.ArgumentParser(description='抽出用到的中文字筆順資料 → hanzi.js')
    ap.add_argument('--text', nargs='+', required=True, help='要掃描用字的檔案或資料夾')
    ap.add_argument('--data', help='hanzi-writer-data 資料夾（含 <字>.json）；不給就自動下載')
    ap.add_argument('--out', default='style/hanzi.js')
    a = ap.parse_args()
    chars = scan(a.text)
    with tempfile.TemporaryDirectory() as tmp:
        data = a.data or fetch(tmp)
        out, missing = {}, []
        for c in chars:
            f = os.path.join(data, f'{c}.json')
            if os.path.exists(f):
                d = json.load(open(f, encoding='utf-8'))
                out[c] = {'s': d['strokes'], 'm': d['medians']}
            else:
                missing.append(c)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8') as fh:
        fh.write('// 由 hanzi_prep.py 產生。筆順資料：hanzi-writer-data（Make Me a Hanzi／文鼎 AR PL KaitiM），Arphic Public License。\n')
        fh.write('window.HANZI = Object.assign(window.HANZI || {}, ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ');\n')
    kb = os.path.getsize(a.out) // 1024
    print(f'{len(out)} 個字的筆順 → {a.out}（{kb} KB）' + (f'；沒有資料、改用字型淡入：{"".join(missing)}' if missing else ''))


if __name__ == '__main__':
    main()
