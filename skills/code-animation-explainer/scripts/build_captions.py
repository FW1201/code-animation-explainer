#!/usr/bin/env python3
"""把各幕的字級時間戳轉成字幕 cue（JSON）與 SRT，並提供 AT 錨點查詢。

用法：
  python build_captions.py storyboard.json --vo vo/ --lead 0.5 --tail 0.7 --out captions/
輸出：
  captions/cues.json   每則字幕 {scene, start, end, text}（全片時間，秒）
  captions/captions.srt
  captions/timeline.json 每幕 {id, start, dur}（場景長度＝lead＋配音長度＋tail）
  captions/snapshot-times.txt 逐階段截圖時間：每則字幕結束前 0.3 秒＋每幕結束前 0.6 秒。
    畫面階段通常跟著句子切換，只抽幕中間點會漏掉「某階段才出現」的溢字與重疊；
    用法：npx hyperframes snapshot --at "$(cat captions/snapshot-times.txt)" --no-end
假設每幕配音在場景內從 lead 秒開始播放。align.json 格式同 tts_elevenlabs.py 的輸出。
在自己的建置腳本裡可 import at(text, chars, starts, lead) 把 AT("字串") 換成秒數。
"""
import argparse, json, os

HARD, SOFT = set('。！？'), set('，：；、')


def at(needle, chars, starts, lead=0.5, nth=0):
    text, i = ''.join(chars), -1
    for _ in range(nth + 1):
        i = text.find(needle, i + 1)
        if i < 0:
            raise KeyError(f'旁白中找不到「{needle}」')
    return starts[i] + lead


def strip_tags(chars, st, et):
    out, i = [], 0
    while i < len(chars):
        if chars[i] == '[':
            while i < len(chars) and chars[i] != ']':
                i += 1
            i += 1
            continue
        out.append((chars[i], st[i], et[i]))
        i += 1
    return out


def split(disp):
    """在句讀處斷句；引號「」內盡量不斷，除非已經太長（≥20 字）。"""
    groups, cur, quote = [], [], False
    for k, (c, a, b) in enumerate(disp):
        if c.strip() == '' and not cur:
            continue
        cur.append((c, a, b))
        quote = True if c == '「' else False if c == '」' else quote
        n = sum(1 for x in cur if x[0].strip())
        if (c in HARD and not quote) or (c == '」' and n >= 8) or (c in SOFT and n >= 11 and not quote) or (c in SOFT and n >= 20):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    return groups


def srt_t(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('storyboard'); ap.add_argument('--vo', default='vo'); ap.add_argument('--out', default='captions')
    ap.add_argument('--lead', type=float, default=0.5); ap.add_argument('--tail', type=float, default=0.7)
    a = ap.parse_args()
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    os.makedirs(a.out, exist_ok=True)
    t, cues, tl = 0.0, [], []
    for s in sb['scenes']:
        if not s.get('narration'):  # 片尾等無旁白的幕不產生字幕
            continue
        al = json.load(open(os.path.join(a.vo, f"{s['id']}.align.json"), encoding='utf-8'))['alignment']
        c, st, et = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
        dur = a.lead + et[-1] + a.tail
        base = t + a.lead
        scene_cues = []
        for g in split(strip_tags(c, st, et)):
            txt = ''.join(x[0] for x in g).strip().rstrip('，。、：；').lstrip('，。、：；').strip()
            if txt.count('「') > txt.count('」'):  # 引號跨行時補齊，每則字幕自成完整引號
                txt += '」'
            if txt.count('」') > txt.count('「'):
                txt = '「' + txt
            if txt == '「」':
                continue
            if txt:
                scene_cues.append({'scene': s['id'], 'start': base + g[0][1], 'end': base + g[-1][2] + 0.6, 'text': txt,
                                   'speech': round(g[-1][2] - g[0][1], 3)})  # 說完後多留 0.6 秒（有空間時），read_check.py 會檢查
        for i, q in enumerate(scene_cues):
            nxt = scene_cues[i + 1]['start'] if i + 1 < len(scene_cues) else t + dur - 0.3
            q['end'] = max(min(max(q['end'], q['start'] + 0.8), nxt), q['start'] + 0.4)
            if i + 1 < len(scene_cues) and nxt - q['end'] < 0.6:
                q['end'] = nxt
        cues += scene_cues
        tl.append({'id': s['id'], 'start': round(t, 3), 'dur': round(dur, 3)})
        t += dur
    json.dump(cues, open(os.path.join(a.out, 'cues.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(tl, open(os.path.join(a.out, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    snaps = sorted({round(q['end'] - 0.3, 1) for q in cues} | {round(x['start'] + x['dur'] - 0.6, 1) for x in tl})
    open(os.path.join(a.out, 'snapshot-times.txt'), 'w').write(','.join(f'{x:g}' for x in snaps))
    with open(os.path.join(a.out, 'captions.srt'), 'w', encoding='utf-8') as f:
        for i, q in enumerate(cues, 1):
            f.write(f"{i}\n{srt_t(q['start'])} --> {srt_t(q['end'])}\n{q['text']}\n\n")
    print(f'{len(cues)} 則字幕，全片 {t:.1f} 秒；逐階段截圖 {len(snaps)} 個時間點 → snapshot-times.txt')


if __name__ == '__main__':
    main()
