#!/usr/bin/env python3
"""閱讀時間檢查：字幕、畫面字卡、標題卡有沒有停留夠久，讓學生讀得完。

用法：
  python read_check.py captions/cues.json                          # 只查字幕
  python read_check.py captions/cues.json --storyboard storyboard.json --timeline captions/timeline.json
  python read_check.py captions/cues.json --rate 2.7               # 說書類聲音語速較慢時調整
規則（中文）：
  字幕   停留 ≥ 1.8 秒，且每秒不超過 6 字（讀得完）；說完之後若下一句還沒來，要多留 ≥0.6 秒
         （cues.json 有 speech 欄時用實際說話長度；沒有時用字數 ÷ 語速估算，語速預設 3.3 字／秒）
  字卡   停留 ≥ 字數 ÷ 4.5 ＋ 1.5 秒（storyboard 每幕 on_screen 欄：[{"text": "…", "in": 秒, "out": 秒, "kind": "card|title|label"}]，秒數為幕內時間）
  標題卡 停留 ≥ 4 秒（kind: "title"）；標籤（kind: "label"）不檢查，因為它不是要學生讀完的句子
  另外檢查：字幕每行超過 22 字、相鄰字幕間隔 0.05–0.25 秒（會閃）
回傳碼：有不足＝1，否則 0。
"""
import argparse, json, re, sys

CJK = re.compile(r'[㐀-鿿豈-﫿]')


def count(text):
    """中文一字算一個；英文、數字每 3 個字元約等於一個中文字的閱讀時間。"""
    t = re.sub(r'\[[^\]]*\]', '', text)
    cjk = len(CJK.findall(t))
    other = len(re.sub(r'[\s　-〿＀-￯，。、！？；：「」『』（）]', '', CJK.sub('', t)))
    return cjk + other / 3


def main():
    ap = argparse.ArgumentParser(description='檢查字幕與字卡的閱讀時間')
    ap.add_argument('cues'); ap.add_argument('--storyboard'); ap.add_argument('--timeline')
    ap.add_argument('--rate', type=float, default=3.3, help='配音語速（字／秒），cues 沒有 speech 欄時用來估算')
    ap.add_argument('--cps', type=float, default=6.0, help='字幕最高密度（字／秒）；國小可調到 4.5')
    ap.add_argument('--line', type=int, default=22, help='字幕每行最多字數')
    a = ap.parse_args()
    bad, warn = [], []
    cues = json.load(open(a.cues, encoding='utf-8'))
    for i, q in enumerate(cues):
        n, dur = count(q['text']), q['end'] - q['start']
        speech = q.get('speech', n / a.rate)
        nxt = cues[i + 1]['start'] if i + 1 < len(cues) else None
        if dur + 1e-6 < 1.8:
            bad.append(f'字幕 {i + 1}（{q["start"]:.1f}s）「{q["text"]}」只停 {dur:.1f}s（至少 1.8s）→ 和前後句合併，或在這句後加停頓')
        elif n / dur > a.cps:
            bad.append(f'字幕 {i + 1}（{q["start"]:.1f}s）「{q["text"]}」{n:.0f} 字停 {dur:.1f}s，每秒 {n / dur:.1f} 字讀不完（上限 {a.cps:g}）→ 拆短句或放慢語速')
        elif dur + 1e-6 < speech + 0.6 and (nxt is None or nxt - q['end'] > 0.05):
            warn.append(f'字幕 {i + 1}「{q["text"][:12]}」說完就消失 → 後面還有空檔，延長到說完後 0.6s（常見原因：這句是一幕的最後一句，把 build_captions.py --tail 調到 ≥0.9）')
        if len(q['text']) > a.line * 2:
            warn.append(f'字幕 {i + 1}「{q["text"][:12]}…」{len(q["text"])} 字，超過兩行（每行 {a.line} 字）→ 在句讀處拆開')
        if i + 1 < len(cues):
            gap = cues[i + 1]['start'] - q['end']
            if 0.05 < gap < 0.25:
                warn.append(f'字幕 {i + 1}→{i + 2} 間隔 {gap:.2f}s，會閃一下 → 接起來或拉開到 ≥0.25s')
    if a.storyboard:
        sb = json.load(open(a.storyboard, encoding='utf-8'))
        start = {}
        if a.timeline:
            start = {x['id']: x['start'] for x in json.load(open(a.timeline, encoding='utf-8'))}
        t = 0.0
        for s in sb['scenes']:
            base = start.get(s['id'], t)
            for c in s.get('on_screen', []):
                kind, dur = c.get('kind', 'card'), c['out'] - c['in']
                if kind == 'label':
                    continue
                need = 4.0 if kind == 'title' else count(c['text']) / 4.5 + 1.5
                if dur + 1e-6 < need:
                    bad.append(f'{s["id"]} {"標題卡" if kind == "title" else "字卡"}（{base + c["in"]:.1f}s）「{c["text"]}」停 {dur:.1f}s，需要 ≥ {need:.1f}s')
            t = base + s.get('duration_sec', 0)
    for x in bad:
        print('✗', x)
    for x in warn:
        print('△', x)
    print(f'\n閱讀時間：{len(cues)} 則字幕；不足 {len(bad)}、提醒 {len(warn)}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
