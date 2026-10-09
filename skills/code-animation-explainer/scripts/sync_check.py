#!/usr/bin/env python3
"""改過旁白（narration）或配音文字（tts）之後的同步檢查。只用 Python 標準函式庫。

檢查三件事：
  1. 畫面裡每個 AT("關鍵字") ／ AT("幕", "關鍵字") 的關鍵字，都還存在於旁白中（改寫句子後最常壞的地方）
  2. 字幕（captions/cues.json）的文字都來自 narration，沒有混進 tts 用的同音字（例：手慧風）
  3. 每一幕都有配音檔（vo/<幕>.mp3 或 .wav）
用法：
  python sync_check.py storyboard.json --html compositions/ --cues captions/cues.json --vo vo/
有任何一項不通過時結束碼為 1。
"""
import argparse, json, os, re, sys

AT1 = re.compile(r'\bAT\(\s*["\']([^"\']+)["\']\s*\)')
AT2 = re.compile(r'\bAT\(\s*["\'](s[\w-]*)["\']\s*,\s*["\']([^"\']+)["\']\s*\)')
CLEAN = re.compile(r'[\s，。、：；！？「」『』（）〈〉《》,.;:!?()\[\]]')


def files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
        else:
            for r, _, fs in os.walk(p):
                for f in fs:
                    if f.endswith(('.html', '.js', '.mjs', '.jsx', '.tsx', '.ts')) and f != 'timing.js' and 'node_modules' not in r:
                        yield os.path.join(r, f)


def main():
    ap = argparse.ArgumentParser(description='旁白／字幕／錨點／音檔同步檢查')
    ap.add_argument('storyboard')
    ap.add_argument('--html', nargs='*', default=['compositions'])
    ap.add_argument('--cues', default='captions/cues.json')
    ap.add_argument('--vo', default='vo')
    a = ap.parse_args()
    scenes = [s for s in json.load(open(a.storyboard, encoding='utf-8'))['scenes'] if s.get('narration')]
    nar = {s['id']: s['narration'] for s in scenes}
    allnar = ''.join(nar.values())
    bad = 0

    print('1. AT() 關鍵字')
    seen = 0
    for f in files(a.html):
        src = open(f, encoding='utf-8', errors='ignore').read()
        for m in AT2.finditer(src):
            seen += 1
            sid, kw = m.groups()
            if sid in nar and kw not in nar[sid]:
                bad += 1; print(f'   ✗ {os.path.basename(f)}：AT("{sid}", "{kw}")　{sid} 的旁白裡沒有「{kw}」')
        for m in AT1.finditer(src):
            if AT2.match(src, m.start()):
                continue
            seen += 1
            kw = m.group(1)
            if kw not in allnar and not kw.startswith('s'):
                bad += 1; print(f'   ✗ {os.path.basename(f)}：AT("{kw}")　旁白裡沒有「{kw}」')
    print(f'   檢查 {seen} 個錨點')

    print('2. 字幕用字＝narration')
    if os.path.exists(a.cues):
        cues = json.load(open(a.cues, encoding='utf-8'))
        cues = cues.get('cues', cues) if isinstance(cues, dict) else cues
        flat = CLEAN.sub('', allnar)
        for c in cues:
            t = CLEAN.sub('', c.get('text', ''))
            if t and t not in flat:
                bad += 1; print(f'   ✗ 字幕「{c.get("text")}」不在旁白原文裡（混進 tts 同音字，或字幕沒重建）')
        for s in scenes:
            if s.get('tts'):
                diff = [(x, y) for x, y in zip(s['narration'], s['tts']) if x != y]
                print(f"   {s['id']} 用了 tts 替換：" + '、'.join(f'{x}→{y}' for x, y in diff[:6]))
    else:
        print(f'   － 找不到 {a.cues}，略過')

    print('3. 每幕都有配音')
    for s in scenes:
        if not any(os.path.exists(os.path.join(a.vo, s['id'] + e)) for e in ('.mp3', '.wav')):
            bad += 1; print(f"   ✗ {s['id']}：{a.vo}/ 裡沒有 {s['id']}.mp3 或 .wav")

    print(f'\n{"全部通過" if not bad else f"{bad} 個問題"}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
