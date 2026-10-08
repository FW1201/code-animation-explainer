#!/usr/bin/env python3
"""建置：字級時間 → 字幕 → compositions/timing.js（畫面用 AT() 讀它對時）。

  python build.py            # 有 vo/*.align.json 就用真的配音時間；沒有就用估算語速（無聲樣片）
  python build.py --rate 3.3 # 估算語速（字／秒），配音前先抓片長
真的配音錄好後重跑一次，所有 AT("關鍵字") 會自動跟上新的時間，畫面不用改。
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '..', '..', 'skills', 'code-animation-explainer', 'scripts')
LEAD, TAIL, END_HOLD = 0.5, 0.9, 2.0          # 每幕前留白、後留白、片尾停留
PAUSE = {'，': 0.18, '、': 0.12, '：': 0.2, '。': 0.35, '！': 0.35, '？': 0.35}


def estimate(text, rate):
    """沒有配音時，依語速估一份和 ElevenLabs 相同格式的字級時間。英文詞照 3 個字母≈1 個中文字。"""
    chars, st, et, t = [], [], [], 0.0
    for c in text:
        d = 0.0 if c in '「」 ' else (1 / rate / 3 if re.match(r'[A-Za-z]', c) else 1 / rate)
        chars.append(c); st.append(round(t, 3)); t += d; et.append(round(t, 3)); t += PAUSE.get(c, 0)
    return {'alignment': {'characters': chars, 'character_start_times_seconds': st, 'character_end_times_seconds': et}}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--rate', type=float, default=3.3)
    a = ap.parse_args()
    sb = json.load(open(os.path.join(HERE, 'storyboard.json'), encoding='utf-8'))
    real = all(os.path.exists(os.path.join(HERE, 'vo', f"{s['id']}.align.json")) for s in sb['scenes'])
    vo = os.path.join(HERE, 'vo' if real else 'vo_est')
    if not real:
        os.makedirs(vo, exist_ok=True)
        for s in sb['scenes']:
            json.dump(estimate(s['narration'], a.rate), open(os.path.join(vo, f"{s['id']}.align.json"), 'w', encoding='utf-8'), ensure_ascii=False)
    cap = os.path.join(HERE, 'captions')
    subprocess.run([sys.executable, os.path.join(SCRIPTS, 'build_captions.py'), os.path.join(HERE, 'storyboard.json'),
                    '--vo', vo, '--out', cap, '--lead', str(LEAD), '--tail', str(TAIL)], check=True)
    tl = json.load(open(os.path.join(cap, 'timeline.json'), encoding='utf-8'))
    cues = json.load(open(os.path.join(cap, 'cues.json'), encoding='utf-8'))
    scenes = []
    for s, x in zip(sb['scenes'], tl):
        al = json.load(open(os.path.join(vo, f"{s['id']}.align.json"), encoding='utf-8'))['alignment']
        scenes.append({'id': s['id'], 'start': x['start'], 'dur': x['dur'], 'lead': LEAD,
                       'chars': al['characters'], 'starts': al['character_start_times_seconds']})
    total = round(tl[-1]['start'] + tl[-1]['dur'] + END_HOLD, 3)
    data = {'source': 'vo' if real else 'estimate', 'total': total, 'scenes': scenes,
            'cues': [{'t0': round(q['start'], 3), 't1': round(q['end'], 3), 'text': q['text']} for q in cues]}
    open(os.path.join(HERE, 'compositions', 'timing.js'), 'w', encoding='utf-8').write(
        f'// build.py 產生（{"真實配音" if real else "估算語速"}），不要手改\nwindow.TIMING = {json.dumps(data, ensure_ascii=False)};\n')
    print(f'時間來源：{"vo/（真實配音）" if real else f"估算 {a.rate} 字／秒"}；全片 {total} 秒、{len(cues)} 則字幕 → compositions/timing.js')


if __name__ == '__main__':
    main()
