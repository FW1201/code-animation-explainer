#!/usr/bin/env python3
"""逐幕生成 ElevenLabs 配音，取回字級時間戳，並可多版本生成＋讀音檢核自動擇優。

用法：
  python tts_elevenlabs.py storyboard.json --voice <VOICE_ID> --out vo/ [scene-01 ...]
  選項：
    --model eleven_v3        --lang zh
    --t2s                    送 TTS 時改用簡體字形（字數不變），時間戳再逐字對回繁體原文。
                             模型對罕用繁體字（澱、鋁、莖、澆、噸…）常唸錯，建議中文一律開啟。
    --takes 0.5 1.0          每幕用這些 stability 各生成一版，跑 verify_vo 檢核，保留疑似唸錯最少的一版。
    --sample "一段文字"       只生成試聽檔 vo/sample-<voice>.mp3；--voice 可給多個 id 一次比較多個聲音，
                             並印出每個聲音的實測語速（字／秒），用來估算片長。
- API key 從環境變數或 .env 的 ELEVENLABS_API_KEY 讀取；請勿寫進程式或貼到對話。
- 輸出 vo/<id>.mp3 與 vo/<id>.align.json；多版本時全部保留在 vo/takes/，報告在 vo/takes-report.json。
- 已存在的幕會跳過；列出幕 id 可強制重錄。
"""
import argparse, base64, json, os, shutil, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
PLAIN = lambda t: re.sub(r'\[\w+\]|[\s，。、：；！？「」『』（）〈〉《》]', '', t)  # 只算會唸出來的字


def load_key():
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key and os.path.exists('.env'):
        for line in open('.env', encoding='utf-8'):
            if line.startswith('ELEVENLABS_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"\'')
    if not key:
        sys.exit('找不到 ELEVENLABS_API_KEY：請在 .env 加上 ELEVENLABS_API_KEY=你的key')
    return key


def tts(key, voice, text, model, lang, stability=0.5):
    body = {'text': text, 'model_id': model, 'voice_settings': {'stability': stability, 'similarity_boost': 0.75}}
    if lang:
        body['language_code'] = lang
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',
        data=json.dumps(body).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(f'ElevenLabs 錯誤 {e.code}：{e.read().decode()[:400]}')
    return base64.b64decode(d['audio_base64']), d.get('normalized_alignment') or d.get('alignment')


def make_take(key, a, text, stability, path, voice=None):
    send = text
    if a.t2s:
        import opencc
        send = opencc.OpenCC('t2s').convert(text)
        if len(send) != len(text):
            send = text  # 長度不一致就無法逐字對回，退回原文
    audio, al = tts(key, voice or a.voice[0], send, a.model, a.lang, stability)
    if send != text and ''.join(al['characters']) == send:
        al['characters'] = list(text)
    open(path, 'wb').write(audio)
    json.dump({'text': text, 'tts_text': send, 'stability': stability, 'alignment': al},
              open(path[:-4] + '.align.json', 'w', encoding='utf-8'), ensure_ascii=False)
    end = al['character_end_times_seconds'][-1] if al and al.get('character_end_times_seconds') else 0
    return len(send), (len(PLAIN(text)) / end if end else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('storyboard', nargs='?'); ap.add_argument('only', nargs='*')
    ap.add_argument('--voice', required=True, nargs='+'); ap.add_argument('--out', default='vo')
    ap.add_argument('--model', default='eleven_v3'); ap.add_argument('--lang', default='zh')
    ap.add_argument('--t2s', action='store_true'); ap.add_argument('--takes', nargs='*', type=float)
    ap.add_argument('--sample')
    a = ap.parse_args()
    key = load_key()
    os.makedirs(a.out, exist_ok=True)
    if a.sample:
        for v in a.voice:
            p = os.path.join(a.out, f'sample-{v}.mp3')
            _, rate = make_take(key, a, a.sample, 0.5, p, v)
            print(f'試聽檔：{p}｜語速約 {rate:.1f} 字／秒')
        return
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    used, report = 0, {}
    for s in sb['scenes']:
        if (a.only and s['id'] not in a.only) or not s.get('narration'):
            continue
        mp3 = os.path.join(a.out, f"{s['id']}.mp3")
        if os.path.exists(mp3) and not a.only:
            print('略過', s['id']); continue
        text = (s.get('tts') or s['narration']).replace('\n', '')   # tts：送去配音的文字（同音字繞過唸錯），字幕仍用 narration
        if not a.takes:
            n, rate = make_take(key, a, text, 0.5, mp3); used += n; print(f"完成 {s['id']}｜語速 {rate:.1f} 字／秒"); continue
        from verify_vo import check
        tk = os.path.join(a.out, 'takes'); os.makedirs(tk, exist_ok=True)
        results = []
        for k, stab in enumerate(a.takes, 1):
            p = os.path.join(tk, f"{s['id']}.s{k}.mp3")
            used += make_take(key, a, text, stab, p)[0]
            flags = [f for f in check(p, text)[0] if f[3] == 'misread']
            results.append((p, flags)); print(f"{s['id']} s{k}（stability {stab}）：疑似唸錯 {len(flags)} 處", '；'.join(f'{f[0]}→{f[1]}' for f in flags))
        best = min(results, key=lambda x: len(x[1]))
        shutil.copy(best[0], mp3); shutil.copy(best[0][:-4] + '.align.json', mp3[:-4] + '.align.json')
        report[s['id']] = {'chosen': os.path.basename(best[0]), 'flags': best[1]}
        print(f"→ {s['id']} 採用 {os.path.basename(best[0])}")
    if report:
        json.dump(report, open(os.path.join(a.out, 'takes-report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('本次約用', used, 'credits')


if __name__ == '__main__':
    main()
