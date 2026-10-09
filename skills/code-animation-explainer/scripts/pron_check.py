#!/usr/bin/env python3
"""中文配音讀音檢核：用「沒有語言模型」的 CTC 語音辨識，聽出每個字實際唸成什麼音，和旁白應有的拼音（含聲調）比對。

為什麼不用 ElevenLabs scribe／Whisper：它們有很強的語言模型，會把唸錯聲調的字「猜回」正確的字（唸成「重新踩」也會寫成「重新猜」），
抓不到錯。CTC 模型逐格輸出聽到的音，唸成 cǎi 就會寫出「踩」，唸成 shòu 就會寫出「受」。

做法：
  1. 兩個離線 CTC 模型（sherpa-onnx：zipformer-ctc-zh、SenseVoice）各辨識一次
  2. 辨識結果與旁白都轉成帶聲調拼音（pypinyin，辨識字取所有可能讀音），逐字對齊
  3. 兩個模型都聽成別的音（聲母、韻母或聲調不同）→ 列為讀錯；只有一個模型不同 → 列為「待確認」
     平翹舌不分（zh/z、ch/c、sh/s）是台灣口音的常態，不算錯
  4. storyboard 的 `tts`（送去配音的文字，可用同音字繞過唸錯，如「手繪」→「手慧」）與 `narration`（字幕）不同時，
     一律以 narration 的讀音為準來比對——觀眾聽到的要和字幕一致
已驗證：舊配音裡使用者聽出的「請／手／猜」錯誤，這支工具都抓得到（猜→踩、手→受），另外還抓到「繪→回」「幾幕→繼母」「報→寶」。

需要：pip install sherpa-onnx pypinyin、ffmpeg。模型第一次執行時從 GitHub（k2-fsa/sherpa-onnx releases）下載到 ~/.cache/pron_check（約 400 MB）。

用法：
  python pron_check.py storyboard.json --vo vo/          # 每一幕都查（vo/<id>.mp3 或 .wav）
  python pron_check.py vo/s0.mp3 "請 AI 做一支手繪風的教學動畫"
  python pron_check.py storyboard.json --vo vo/ --json pron.json
結束碼：有「讀錯」或有幕找不到音檔時回傳 1，方便放進出片前檢查。
"""
import argparse, difflib, json, os, re, subprocess, sys, tarfile, urllib.request

CACHE = os.path.expanduser(os.environ.get('PRON_CHECK_CACHE', '~/.cache/pron_check'))
REL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/'
MODELS = {
    'zipformer': 'sherpa-onnx-zipformer-ctc-zh-int8-2025-07-03',
    'sensevoice': 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17',
}
HAN = re.compile(r'[㐀-鿿豈-﫿]')


def fetch(name):
    d = os.path.join(CACHE, name)
    if os.path.exists(os.path.join(d, 'model.int8.onnx')):
        return d
    os.makedirs(CACHE, exist_ok=True)
    tb = os.path.join(CACHE, name + '.tar.bz2')
    print(f'  下載模型 {name} …', file=sys.stderr)
    urllib.request.urlretrieve(REL + name + '.tar.bz2', tb)
    with tarfile.open(tb) as t:
        t.extractall(CACHE, filter='data')
    os.remove(tb)
    return d


def recognizers():
    import sherpa_onnx
    z, s = fetch(MODELS['zipformer']), fetch(MODELS['sensevoice'])
    return {
        'zipformer': sherpa_onnx.OfflineRecognizer.from_zipformer_ctc(
            model=f'{z}/model.int8.onnx', tokens=f'{z}/tokens.txt', num_threads=4),
        'sensevoice': sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=f'{s}/model.int8.onnx', tokens=f'{s}/tokens.txt', language='zh', use_itn=False, num_threads=4),
    }


def load(path):
    import numpy as np
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.int16).astype(np.float32) / 32768


def py_all(ch):
    """一個字所有可能的帶調拼音（輕聲記為 5）"""
    from pypinyin import pinyin, Style
    return set(pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0])


def py_ctx(chars):
    """依上下文取旁白每個字的讀音（多音字照詞判斷）"""
    from pypinyin import pinyin, Style
    return [p[0] for p in pinyin(''.join(chars), style=Style.TONE3, neutral_tone_with_five=True)]


def flat(p):
    """台灣口音常見的平翹舌不分（zh/z、ch/c、sh/s）：比對時視為同一個聲母"""
    return re.sub(r'^(z|c|s)h', r'\1', p)


def compare(text, heard):
    exp = HAN.findall(text)
    got = HAN.findall(heard)
    ep = py_ctx(exp)
    gp = [sorted(py_all(c)) for c in got]
    # 對齊用「去掉聲調的音節」，聲調差異在對齊後再判斷，避免聲調錯一個字就整段錯位
    key = lambda p: flat(re.sub(r'\d', '', p))
    sm = difflib.SequenceMatcher(None, [key(p) for p in ep], [key(g[0]) for g in gp], autojunk=False)
    alt = [py_all(c) for c in exp]              # 旁白字的所有讀音：pypinyin 對繁體多音字（如「接著」的著）偶爾取錯，聽到的音屬於其中之一就不算錯
    res = [None] * len(exp)                     # 每個旁白字：None=聽起來正確，否則 (聽到的字, 聽到的拼音)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == 'equal':
            for k in range(a1 - a0):
                e, g = ep[a0 + k], gp[b0 + k]
                ok = e in g or bool(alt[a0 + k] & set(g)) or (e.endswith('5') and any(key(x) == key(e) for x in g)) or flat(e) in {flat(x) for x in g}
                res[a0 + k] = None if ok else (got[b0 + k], '/'.join(g))
        elif op == 'replace':
            for k in range(a1 - a0):
                j = b0 + min(k, b1 - b0 - 1)
                e = ep[a0 + k]
                g = gp[j]
                ok = e in g or bool(alt[a0 + k] & set(g)) or (e.endswith('5') and any(key(x) == key(e) for x in g)) or flat(e) in {flat(x) for x in g}
                res[a0 + k] = None if ok else (got[j], '/'.join(g))
        elif op == 'delete':
            for k in range(a0, a1):
                res[k] = ('（沒聽到）', '')
    return exp, ep, res


def check(audio, text, recs):
    x = load(audio)
    heard, per = {}, {}
    for name, r in recs.items():
        st = r.create_stream(); st.accept_waveform(16000, x); r.decode_stream(st)
        heard[name] = st.result.text
        per[name] = compare(text, st.result.text)
    exp, ep, _ = next(iter(per.values()))
    rows = []
    for i, (c, p) in enumerate(zip(exp, ep)):
        bad = {n: per[n][2][i] for n in per if per[n][2][i]}
        level = 'wrong' if len(bad) == len(per) else ('check' if bad else None)
        rows.append({'char': c, 'pinyin': p, 'level': level, 'heard': {n: v[0] for n, v in bad.items()},
                     'heard_pinyin': {n: v[1] for n, v in bad.items()}})
    return {'audio': audio, 'text': text, 'heard': heard, 'rows': rows}


def report(r, sid=''):
    wrong = [i for i, x in enumerate(r['rows']) if x['level'] == 'wrong']
    check_ = [i for i, x in enumerate(r['rows']) if x['level'] == 'check']
    name = f"{sid}：" if sid else ''
    mark = '✗' if wrong else ('△' if check_ else '✓')
    print(f"  {mark} {name}{os.path.basename(r['audio'])}　讀錯 {len(wrong)}、待確認 {len(check_)}")
    chars = [x['char'] for x in r['rows']]
    for i in wrong + check_:
        x = r['rows'][i]
        ctx = ''.join(chars[max(0, i - 3):i]) + f'【{x["char"]}】' + ''.join(chars[i + 1:i + 4])
        heard = '、'.join(f"{n}聽成「{h}」{x['heard_pinyin'][n]}" for n, h in x['heard'].items())
        print(f"     {'讀錯' if x['level'] == 'wrong' else '待確認'}　{ctx}　應為 {x['pinyin']}；{heard}")


def main():
    ap = argparse.ArgumentParser(description='中文配音讀音檢核（CTC 辨識 vs 應有拼音）')
    ap.add_argument('src', help='音檔，或 storyboard.json')
    ap.add_argument('text', nargs='?')
    ap.add_argument('--vo', default='vo')
    ap.add_argument('--only', help='只查這些幕，逗號分隔（如 s0,s3）')
    ap.add_argument('--json')
    a = ap.parse_args()
    recs = recognizers()
    out, missing = [], []
    if a.src.endswith('.json'):
        only = set(a.only.split(',')) if a.only else None
        for s in json.load(open(a.src, encoding='utf-8'))['scenes']:
            if not s.get('narration') or (only and s['id'] not in only):
                continue
            src = next((os.path.join(a.vo, s['id'] + e) for e in ('.mp3', '.wav') if os.path.exists(os.path.join(a.vo, s['id'] + e))), None)
            if not src:
                print(f"  ✗ {s['id']}：找不到音檔（{a.vo}/{s['id']}.mp3 或 .wav）"); missing.append(s['id']); continue
            r = check(src, s['narration'], recs); r['id'] = s['id']; out.append(r); report(r, s['id'])
    else:
        if not a.text:
            sys.exit('請給旁白文字')
        r = check(a.src, a.text, recs); out.append(r); report(r)
    nw = sum(x['level'] == 'wrong' for r in out for x in r['rows'])
    nc = sum(x['level'] == 'check' for r in out for x in r['rows'])
    print(f'\n讀錯 {nw} 個、待確認 {nc} 個（讀錯＝兩個模型都聽成別的音；待確認＝只有一個模型聽錯，請用耳朵確認）'
          + (f'；缺音檔 {len(missing)} 幕：{"、".join(missing)}' if missing else ''))
    if a.json:
        json.dump(out, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(1 if nw or missing else 0)


if __name__ == '__main__':
    main()
