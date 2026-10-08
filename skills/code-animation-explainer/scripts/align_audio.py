#!/usr/bin/env python3
"""沒有字級時間戳的配音（ElevenLabs 連接器、錄音、其他 TTS）→ 產生和 tts_elevenlabs.py 相同格式的 <id>.align.json。

做法：
  1. ffmpeg silencedetect 找出句中停頓
  2. 旁白依標點（，。、：；！？）切成片段；取最長的 N-1 個停頓當片段邊界（N＝片段數），停頓不夠就依字數比例補
  3. 片段內依字數分配時間（中文 1、英文字母 0.35、空白 0），標點放在片段結尾
誤差通常在 0.1–0.2 秒，AT("關鍵字") 對時夠用；要逐字精準就改用語音辨識（ElevenLabs scribe）的字級時間。

用法：
  python align_audio.py storyboard.json --vo vo/            # 讀 vo/<id>.mp3（或 .wav），寫 vo/<id>.align.json
  python align_audio.py storyboard.json --vo vo/ --noise -30 --min-pause 0.1
"""
import argparse, json, os, re, subprocess

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


def main():
    ap = argparse.ArgumentParser(description='配音 → 估計字級時間（align.json）')
    ap.add_argument('storyboard'); ap.add_argument('--vo', default='vo')
    ap.add_argument('--noise', type=float, default=-30); ap.add_argument('--min-pause', type=float, default=0.1)
    a = ap.parse_args()
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    for s in sb['scenes']:
        if not s.get('narration'):
            continue
        src = next((os.path.join(a.vo, f"{s['id']}{e}") for e in ('.mp3', '.wav') if os.path.exists(os.path.join(a.vo, f"{s['id']}{e}"))), None)
        if not src:
            print(f"  {s['id']}：找不到 {a.vo}/{s['id']}.mp3"); continue
        head, tail, inner = pauses(src, a.noise, a.min_pause)
        al = align(s['narration'], head, tail, inner)
        json.dump({'alignment': al, 'source': 'align_audio.py（靜音偵測＋字數比例）'},
                  open(os.path.join(a.vo, f"{s['id']}.align.json"), 'w', encoding='utf-8'), ensure_ascii=False)
        n = len(phrases(s['narration']))
        print(f"  {s['id']}：{tail - head:.2f}s 語音、{len(inner)} 個停頓 / {n} 個片段" + ('' if len(inner) >= n - 1 else '（停頓不足，部分依字數比例切）'))


if __name__ == '__main__':
    main()
