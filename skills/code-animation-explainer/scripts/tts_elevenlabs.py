#!/usr/bin/env python3
"""逐幕生成 ElevenLabs 配音，並取回字級時間戳（只用 Python 標準庫）。

用法：
  python tts_elevenlabs.py storyboard.json --voice <VOICE_ID> --out vo/ [--model eleven_v3] [--lang zh] [scene-01 scene-03 ...]

- API key 從環境變數或 .env 的 ELEVENLABS_API_KEY 讀取；請勿寫進程式或貼到對話。
- 每幕輸出 vo/<id>.mp3 與 vo/<id>.align.json（characters / start / end 秒）。
- 已存在的幕會跳過；在最後列出幕 id 可強制重錄指定幕。
- 試聽：--sample "一段文字" 會用同一段文字生成 vo/sample-<voice>.mp3。
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error


def load_key():
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key and os.path.exists('.env'):
        for line in open('.env', encoding='utf-8'):
            if line.startswith('ELEVENLABS_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"\'')
    if not key:
        sys.exit('找不到 ELEVENLABS_API_KEY：請在 .env 加上 ELEVENLABS_API_KEY=你的key')
    return key


def tts(key, voice, text, model, lang):
    body = {'text': text, 'model_id': model, 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}}
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('storyboard', nargs='?')
    ap.add_argument('only', nargs='*')
    ap.add_argument('--voice', required=True)
    ap.add_argument('--out', default='vo')
    ap.add_argument('--model', default='eleven_v3')
    ap.add_argument('--lang', default='zh')
    ap.add_argument('--sample')
    a = ap.parse_args()
    key = load_key()
    os.makedirs(a.out, exist_ok=True)
    if a.sample:
        audio, _ = tts(key, a.voice, a.sample, a.model, a.lang)
        p = os.path.join(a.out, f'sample-{a.voice}.mp3')
        open(p, 'wb').write(audio)
        print('試聽檔：', p)
        return
    sb = json.load(open(a.storyboard, encoding='utf-8'))
    total = 0
    for s in sb['scenes']:
        if a.only and s['id'] not in a.only:
            continue
        mp3 = os.path.join(a.out, f"{s['id']}.mp3")
        if os.path.exists(mp3) and not a.only:
            print('略過', s['id'])
            continue
        text = s['narration'].replace('\n', '')
        audio, align = tts(key, a.voice, text, a.model, a.lang)
        open(mp3, 'wb').write(audio)
        json.dump({'text': text, 'alignment': align}, open(os.path.join(a.out, f"{s['id']}.align.json"), 'w', encoding='utf-8'), ensure_ascii=False)
        total += len(text)
        print('完成', s['id'], len(text), '字')
    print('本次約用', total, 'credits')


if __name__ == '__main__':
    main()
