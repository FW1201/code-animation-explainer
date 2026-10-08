#!/usr/bin/env python3
"""從風格卡自動產生風格庫文件，文件和卡片永遠同步。

用法：
  python style_catalog.py              # 重寫 references/style-library.md 的總表與輪盤表、產生 assets/styles/previews/index.html
  python style_catalog.py --render     # 另外重新渲染所有風格板預覽圖（需要 npx playwright 與 ffmpeg）
  python style_catalog.py --check      # 只檢查文件是否和卡片一致（不寫檔；不一致回傳 1）
style-library.md 裡只有 <!-- catalog:start -->…<!-- catalog:end --> 與 <!-- roulette:start -->…<!-- roulette:end --> 兩段是產生的，
其他段落（依科目挑選、實作提醒）手寫。新增或修改風格卡後跑一次。
"""
import argparse, glob, html, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
STYLES = os.path.join(ROOT, 'assets', 'styles')
LIB = os.path.join(ROOT, 'references', 'style-library.md')


def cards():
    out = [json.load(open(p, encoding='utf-8')) for p in sorted(glob.glob(os.path.join(STYLES, '*.json')))]
    return sorted(out, key=lambda s: s['id'])


def catalog_md(cs):
    rows = ['| id | 風格 | 溫度 | 最適合 | 原生招式 | 手寫感 | 預覽 |', '|---|---|---|---|---|---|---|']
    for s in cs:
        moves = '、'.join(m['name'] for m in s['native_moves'][:3])
        sk = f'roughness {s["sketch"]["roughness"]}' if s.get('sketch') else '—'
        rows.append(f'| `{s["id"]}` | {s["name"]} | {s["temperature"]} | {"、".join(s["fits"][:3])} | {moves} | {sk} | `previews/{s["id"]}.jpg` |')
    return '\n'.join(rows)


def roulette_md(cs):
    n = len(cs)
    head = '| ' + ' | '.join(str(i) for i in range(n)) + ' |'
    sep = '|' + '---|' * n
    body = '| ' + ' | '.join(s['id'] for s in cs) + ' |'
    return f'`date +%S`，`秒數 % {n}` 對照下表（0 起算）：\n\n{head}\n{sep}\n{body}'


def replace_block(text, tag, content):
    a, b = f'<!-- {tag}:start -->', f'<!-- {tag}:end -->'
    if a not in text:
        sys.exit(f'style-library.md 缺少 {a} 標記')
    i, j = text.index(a) + len(a), text.index(b)
    return text[:i] + '\n<!-- 由 scripts/style_catalog.py 產生，請改風格卡再重跑，不要手改 -->\n' + content + '\n' + text[j:]


def gallery_html(cs):
    items = []
    for s in cs:
        ess = ''.join(f'<li>{html.escape(x)}</li>' for x in s['essence'][:3])
        items.append(f'<article><img src="{s["id"]}.jpg" alt="{html.escape(s["name"])} 風格板" loading="lazy">'
                     f'<h2>{html.escape(s["name"])} <code>{s["id"]}</code></h2><p class="t">{html.escape(s["temperature"])}｜{html.escape("、".join(s["fits"][:4]))}</p>'
                     f'<p>{html.escape(s["positioning"])}</p><ul>{ess}</ul></article>')
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>教學動畫風格庫</title><style>
:root{{--bg:#F4F2ED;--ink:#222;--muted:#666;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1B1B1D;--ink:#EEE;--muted:#AAA;--card:#26262A}}}}
body{{margin:0;padding:32px 16px;background:var(--bg);color:var(--ink);font:16px/1.6 "Noto Sans TC",system-ui,sans-serif}}
h1{{max-width:1400px;margin:0 auto 24px;font-size:28px}}
main{{max-width:1400px;margin:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr));gap:20px}}
article{{background:var(--card);border-radius:12px;overflow:hidden;box-shadow:0 8px 24px -16px #0006}}
img{{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}} article>*:not(img){{margin:10px 16px}}
h2{{font-size:20px}} code{{font-size:14px;color:var(--muted)}} .t{{color:var(--muted);font-size:14px}} ul{{padding-left:20px;font-size:14px}}
</style></head><body><h1>教學動畫風格庫（{len(cs)} 種）</h1><main>{"".join(items)}</main></body></html>
'''


def render(cs):
    with tempfile.TemporaryDirectory() as tmp:
        for s in cs:
            out = os.path.join(tmp, s['id'])
            subprocess.run([sys.executable, os.path.join(HERE, 'style_apply.py'), s['id'], '--out', out], check=True, capture_output=True)
            png = os.path.join(tmp, s['id'] + '.png')
            subprocess.run(['npx', '--no-install', 'playwright', 'screenshot', '--viewport-size=1920,1080', '--wait-for-timeout=3000',
                            f'file://{out}/board.html', png], check=True, capture_output=True)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', png, '-vf', 'scale=1280:-1', '-q:v', '4',
                            os.path.join(STYLES, 'previews', s['id'] + '.jpg')], check=True)
            print('  預覽', s['id'])


def main():
    ap = argparse.ArgumentParser(description='風格卡 → 風格庫文件與預覽索引')
    ap.add_argument('--render', action='store_true'); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    cs = cards()
    text = open(LIB, encoding='utf-8').read()
    new = replace_block(replace_block(text, 'catalog', catalog_md(cs)), 'roulette', roulette_md(cs))
    gal_path = os.path.join(STYLES, 'previews', 'index.html')
    gal = gallery_html(cs)
    if a.check:
        stale = [p for p, want in ((LIB, new), (gal_path, gal)) if not os.path.exists(p) or open(p, encoding='utf-8').read() != want]
        missing = [s['id'] for s in cs if not os.path.exists(os.path.join(STYLES, 'previews', s['id'] + '.jpg'))]
        for p in stale:
            print('✗ 需要重新產生：', os.path.relpath(p, ROOT))
        for m in missing:
            print('✗ 缺預覽圖：', m)
        sys.exit(1 if stale or missing else 0)
    open(LIB, 'w', encoding='utf-8').write(new)
    open(gal_path, 'w', encoding='utf-8').write(gal)
    if a.render:
        render(cs)
    print(f'{len(cs)} 張風格卡 → references/style-library.md（總表、輪盤）、assets/styles/previews/index.html')


if __name__ == '__main__':
    main()
