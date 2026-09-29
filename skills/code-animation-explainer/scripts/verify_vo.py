#!/usr/bin/env python3
"""配音讀音檢核：用兩個 Whisper 模型聽寫配音，轉成無聲調拼音後與腳本比對。

- 同音字（例：碘液／點葉）不算錯，因為比的是拼音不是字形。
- 兩個模型在同一位置都聽成別的音，才判定「疑似唸錯」（降低誤報）。
- 一長段都對不上（→ ∅）通常是 Whisper 漏聽，不是唸錯，列為「需人工試聽」。

需求：ffmpeg、whisper.cpp 的 `whisper-cli`（或設定 WHISPER_CLI）、兩個 ggml 模型、`pip install pypinyin opencc-python-reimplemented`
用法：
  python verify_vo.py storyboard.json --vo vo/ [scene-01 ...] [--models large-v3.bin medium.bin] [--prompt "以下是繁體中文的…旁白。"]
  python verify_vo.py --file x.mp3 --text "旁白"
專業術語（例：促發、共現、構式）Whisper 常聽成常見詞（觸發）。把術語放進 --prompt
（例：--prompt "以下是語言學旁白，術語：促發、共現構式分析、行為輪廓。"）可減少誤報；
仍被標記的術語要請使用者試聽，不能直接判定配音正確或錯誤。
程式介面：from verify_vo import check；check(mp3, text) → (flags, per_model)
"""
import argparse, difflib, glob, json, os, re, subprocess, sys, tempfile
from pypinyin import lazy_pinyin
import opencc

S2T = opencc.OpenCC('s2t')
PUNCT = re.compile(r'[\s，。、：；！？「」『』（）〈〉《》,.!?:;\-—…\[\]a-zA-Z]')
D = '零一二三四五六七八九'


def num2zh(m):
    """Whisper 常把中文數字寫成阿拉伯數字；年份（4 位、非整百）逐字唸，其餘依位數唸。"""
    n = m.group(0)
    if len(n) == 4 and not n.endswith('00'):
        return ''.join(D[int(c)] for c in n)
    v, out = int(n), ''
    for unit, base in (('千', 1000), ('百', 100), ('十', 10)):
        if v >= base:
            out += ('' if unit == '十' and not out and v // base == 1 and len(n) == 2 else D[v // base]) + unit
            v %= base
        elif out and v and not out.endswith('零'):
            out += '零'
    return (out + (D[v] if v else '')) or '零'
CLI = os.environ.get('WHISPER_CLI', 'whisper-cli')
LONG_GAP = 8  # 超過這麼多字的整段不符，視為漏聽


def default_models():
    found = []
    for name in ('ggml-large-v3.bin', 'ggml-medium.bin'):
        hits = glob.glob(os.path.expanduser(f'~/.cache/**/{name}'), recursive=True)
        if hits:
            found.append(hits[0])
    return found


def clean(t):
    t = re.sub(r'\d+', num2zh, re.sub(r'\[\w+\]', '', t))
    # 兩／二、着／著 讀音相同或只是字形差異，統一後再比
    return PUNCT.sub('', S2T.convert(t)).replace('兩', '二').replace('着', '著')


def transcribe(mp3, model, prompt):
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, 'a.wav')
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ar', '16000', '-ac', '1', wav])
        subprocess.run([CLI, '-m', model, '-l', 'zh', '-mc', '0', '-nt', '-otxt', '-of', os.path.join(d, 'o'),
                        '--prompt', prompt, '-f', wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return open(os.path.join(d, 'o.txt'), encoding='utf-8').read()


def diff(ref, hyp):
    rp, hp = lazy_pinyin(ref), lazy_pinyin(hyp)
    return [(ref[a1:a2] or '∅', hyp[b1:b2] or '∅', a1)
            for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, rp, hp, autojunk=False).get_opcodes() if op != 'equal']


def check(mp3, text, models=None, prompt='以下是繁體中文的教學旁白。'):
    models = models or default_models()
    if len(models) < 2:
        sys.exit('需要兩個 Whisper 模型（例如 large-v3 與 medium），用 --models 指定')
    ref = clean(text)
    per_model = [diff(ref, clean(transcribe(mp3, m, prompt))) for m in models[:2]]
    span = lambda p, r: set(range(p, p + max(1, len(r))))
    other = set().union(*[span(p, r) for r, h, p in per_model[1]]) if per_model[1] else set()
    flags = []
    for r, h, p in per_model[0]:
        if span(p, r) & other:
            h2 = next((hh for rr, hh, pp in per_model[1] if span(pp, rr) & span(p, r)), '?')
            kind = 'listen' if len(r) >= LONG_GAP and (h == '∅' or h2 == '∅') else 'misread'
            flags.append((r, h, h2, kind))
    return flags, per_model


def recheck_listen(mp3, text, flags, align_path, models, prompt):
    """Whisper 常整句漏聽（尤其結尾）。把「需人工試聽」的段落依字級時間切出來單獨再聽一次；
    切段重聽沒問題就移除該旗標，仍有問題則保留並附上切段的結果。"""
    if not os.path.exists(align_path):
        return flags
    al = json.load(open(align_path, encoding='utf-8'))['alignment']
    raw = ''.join(al['characters'])
    out = []
    for f in flags:
        if f[3] != 'listen':
            out.append(f); continue
        i = raw.find(f[0][:4])
        if i < 0:
            out.append(f); continue
        j = min(len(al['characters']) - 1, i + len(f[0]) - 1)
        a, b = max(0, al['character_start_times_seconds'][i] - 0.8), al['character_end_times_seconds'][j] + 0.8
        with tempfile.TemporaryDirectory() as d:
            seg = os.path.join(d, 'seg.mp3')
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.2f}', '-to', f'{b:.2f}', '-i', mp3, seg])
            sub = [x for x in check(seg, f[0], models, prompt)[0] if x[3] == 'misread']
        ref = clean(f[0])
        # 切段邊緣只少一個字（兩個模型都聽成 ∅）多半是切點截到，不算唸錯
        edge = lambda r: len(r) == 1 and (ref.startswith(r) or ref.endswith(r))
        out += [(r, h1, h2, 'misread') for r, h1, h2, _ in sub if not (h1 == '∅' and h2 == '∅' and edge(r))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('storyboard', nargs='?'); ap.add_argument('only', nargs='*')
    ap.add_argument('--vo', default='vo'); ap.add_argument('--models', nargs='*')
    ap.add_argument('--prompt', default='以下是繁體中文的教學旁白。')
    ap.add_argument('--file'); ap.add_argument('--text')
    a = ap.parse_args()
    if a.file:
        print(json.dumps(check(a.file, a.text, a.models, a.prompt)[0], ensure_ascii=False)); return
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    report, total = {}, 0
    for s in sb['scenes']:
        if (a.only and s['id'] not in a.only) or not s.get('narration'):
            continue
        mp3 = os.path.join(a.vo, f"{s['id']}.mp3")
        flags, pm = check(mp3, s['narration'], a.models, a.prompt)
        flags = recheck_listen(mp3, s['narration'], flags, mp3[:-4] + '.align.json', a.models, a.prompt)
        mis = [f for f in flags if f[3] == 'misread']; lis = [f for f in flags if f[3] == 'listen']
        total += len(mis)
        print(f"== {s['id']}  疑似唸錯 {len(mis)} 處、需人工試聽 {len(lis)} 處")
        for r, h1, h2, k in flags:
            print(f"   {'✗' if k == 'misread' else '?'} 腳本「{r}」→ 模型A「{h1}」／模型B「{h2}」")
        report[s['id']] = [list(f) for f in flags]
    json.dump(report, open(os.path.join(a.vo, 'verify-report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'合計疑似唸錯 {total} 處；報告：{os.path.join(a.vo, "verify-report.json")}')


if __name__ == '__main__':
    main()
