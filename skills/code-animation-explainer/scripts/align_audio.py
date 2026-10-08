#!/usr/bin/env python3
"""沒有字級時間戳的配音（ElevenLabs 連接器、錄音、其他 TTS）→ 產生和 tts_elevenlabs.py 相同格式的 <id>.align.json。

做法：
  1. ffmpeg silencedetect 找出句中停頓
  2. 旁白依標點（，。、：；！？）切成片段；取最長的 N-1 個停頓當片段邊界（N＝片段數），停頓不夠就依字數比例補
  3. 片段內依字數分配時間（中文 1、英文字母 0.35、空白 0），標點放在片段結尾
誤差通常在 0.1–0.2 秒；語速快、停頓少時（如 eleven_v3）片段會對歪。

--asr（建議）：改用離線語音辨識（sherpa-onnx SenseVoice，和 pron_check.py 同一個模型）取得「每個字實際被唸出的時間」，
逐字對齊旁白；辨識不到的字（英文、輕聲）用前後已對到的字內插。誤差約 0.05 秒。需要 pip install sherpa-onnx pypinyin。

用法：
  python align_audio.py storyboard.json --vo vo/ --asr      # 逐字時間（建議）
  python align_audio.py storyboard.json --vo vo/            # 靜音偵測＋字數比例（不需額外套件）
  python align_audio.py storyboard.json --vo vo/ --noise -30 --min-pause 0.1
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PUNCT = '，。、：；！？,.;:!?'


def pauses(path, noise, dmin):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', f'silencedetect=noise={noise}dB:d={dmin}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r.stderr)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                               capture_output=True, text=True).stdout)
    sil = list(zip(st, en + [dur] * (len(st) - len(en))))
    head = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0                     # 開頭靜音
    tail = sil[-1][0] if sil and sil[-1][1] > dur - 0.05 else dur            # 結尾靜音
    inner = [(a, b) for a, b in sil if a > head + 0.05 and b < tail - 0.05]
    return head, tail, inner


def weight(c):
    if c.isspace() or c in '「」『』（）()':
        return 0.0
    if c in PUNCT:
        return 0.0
    return 0.35 if re.match(r'[A-Za-z0-9]', c) else 1.0


def phrases(text):
    out, cur = [], ''
    for c in text:
        cur += c
        if c in PUNCT:
            out.append(cur); cur = ''
    if cur.strip():
        out.append(cur)
    return out


def align(text, head, tail, inner):
    ph = phrases(text)
    W = [sum(weight(c) for c in p) for p in ph]
    # 片段邊界：最長的 N-1 個停頓（照時間排序）；不夠就在最長的語音段裡依字數比例切
    cuts = sorted(sorted(inner, key=lambda s: s[1] - s[0], reverse=True)[:len(ph) - 1])
    spans, t = [], head
    for a, b in cuts:
        spans.append([t, a]); t = b
    spans.append([t, tail])
    while len(spans) < len(ph):                       # 停頓不夠：把含最多字的語音段依字數切開
        i = max(range(len(spans)), key=lambda k: spans[k][1] - spans[k][0])
        a, b = spans[i]; spans[i:i + 1] = [[a, (a + b) / 2], [(a + b) / 2, b]]
    # 片段數和語音段數對齊後，依字數重新分配（相鄰片段若被分到同一段，用字數比例分）
    chars, st, et = [], [], []
    for p, w, (a, b) in zip(ph, W, spans):
        unit = (b - a) / w if w else 0
        x = a
        for c in p:
            d = weight(c) * unit
            chars.append(c); st.append(round(x, 3)); x += d; et.append(round(x, 3))
    return {'characters': chars, 'character_start_times_seconds': st, 'character_end_times_seconds': et}


def align_asr(text, path, rec):
    """用 CTC 辨識的逐字時間戳對齊旁白（拼音去聲調比對，容忍聲調差異與簡繁差異）"""
    import difflib
    import pron_check as pc
    x = pc.load(path)
    st = rec.create_stream(); st.accept_waveform(16000, x); rec.decode_stream(st)
    toks = [(t, ts) for t, ts in zip(st.result.tokens, st.result.timestamps) if pc.HAN.match(t)]
    chars = list(text)
    idx = [i for i, c in enumerate(chars) if pc.HAN.match(c)]
    ep = pc.py_ctx([chars[i] for i in idx])
    key = lambda p: pc.flat(re.sub(r'\d', '', p))
    gp = [key(sorted(pc.py_all(t))[0]) for t, _ in toks]
    t0 = [None] * len(chars)
    sm = difflib.SequenceMatcher(None, [key(p) for p in ep], gp, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op in ('equal', 'replace'):
            for k in range(min(a1 - a0, b1 - b0)):
                t0[idx[a0 + k]] = float(toks[b0 + k][1])
    dur = len(x) / 16000
    # 沒對到的字（英文、標點、漏聽）：在前後錨點間依字重內插
    anchors = [(-1, 0.0)] + [(i, t) for i, t in enumerate(t0) if t is not None] + [(len(chars), dur)]
    for (ia, ta), (ib, tb) in zip(anchors, anchors[1:]):
        gap = list(range(ia + 1, ib))
        if not gap:
            continue
        w = [weight(chars[i]) for i in gap]
        start = ta + (0.18 if ia >= 0 and weight(chars[ia]) else 0)
        span = max(0.0, tb - start); tot = sum(w) or 1; acc = start
        for i, wi in zip(gap, w):
            t0[i] = round(acc, 3); acc += span * wi / tot
    t1 = []
    for i in range(len(chars)):
        nxt = next((t0[j] for j in range(i + 1, len(chars)) if weight(chars[j])), dur)
        t1.append(round(min(nxt, t0[i] + 0.45) if weight(chars[i]) else t0[i], 3))
    return {'characters': chars, 'character_start_times_seconds': [round(t, 3) for t in t0], 'character_end_times_seconds': t1}


def main():
    ap = argparse.ArgumentParser(description='配音 → 估計字級時間（align.json）')
    ap.add_argument('storyboard'); ap.add_argument('--vo', default='vo')
    ap.add_argument('--noise', type=float, default=-30); ap.add_argument('--min-pause', type=float, default=0.1)
    ap.add_argument('--asr', action='store_true', help='用離線語音辨識的逐字時間（需要 sherpa-onnx、pypinyin）')
    a = ap.parse_args()
    rec = None
    if a.asr:
        import pron_check as pc
        rec = pc.recognizers()['sensevoice']
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    for s in sb['scenes']:
        if not s.get('narration'):
            continue
        src = next((os.path.join(a.vo, f"{s['id']}{e}") for e in ('.mp3', '.wav') if os.path.exists(os.path.join(a.vo, f"{s['id']}{e}"))), None)
        if not src:
            print(f"  {s['id']}：找不到 {a.vo}/{s['id']}.mp3"); continue
        if rec:
            al = align_asr(s['narration'], src, rec)
            json.dump({'alignment': al, 'source': 'align_audio.py --asr（SenseVoice 逐字時間）'},
                      open(os.path.join(a.vo, f"{s['id']}.align.json"), 'w', encoding='utf-8'), ensure_ascii=False)
            print(f"  {s['id']}：逐字對齊 {len(al['characters'])} 字，最後一字 {al['character_end_times_seconds'][-1]:.2f}s")
            continue
        head, tail, inner = pauses(src, a.noise, a.min_pause)
        al = align(s['narration'], head, tail, inner)
        json.dump({'alignment': al, 'source': 'align_audio.py（靜音偵測＋字數比例）'},
                  open(os.path.join(a.vo, f"{s['id']}.align.json"), 'w', encoding='utf-8'), ensure_ascii=False)
        n = len(phrases(s['narration']))
        print(f"  {s['id']}：{tail - head:.2f}s 語音、{len(inner)} 個停頓 / {n} 個片段" + ('' if len(inner) >= n - 1 else '（停頓不足，部分依字數比例切）'))


if __name__ == '__main__':
    main()
