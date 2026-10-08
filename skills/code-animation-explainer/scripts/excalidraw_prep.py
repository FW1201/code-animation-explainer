#!/usr/bin/env python3
"""把 Excalidraw 畫好的圖變成可以逐步畫出的動畫資料。

老師在 Excalidraw（excalidraw.com）畫好圖 → 選單「儲存到…」存成 .excalidraw 檔 → 執行：
  python excalidraw_prep.py diagram.excalidraw --out compositions/        # 依圖層順序（先畫的先出現）
  python excalidraw_prep.py diagram.excalidraw --order y --out compositions/  # 由上到下的閱讀順序
輸出：
  diagram.excalidraw.js   window.EXCALIDRAW["diagram"] = {...}（file:// 也能載入，不用 fetch）
  diagram.steps.json      每一步的 id、類型、文字，"at" 欄填 AT("關鍵字") 就能讓那一步對上旁白
場景裡：
  <script src="diagram.excalidraw.js"></script>
  const steps = SK.excalidraw(svgEl, EXCALIDRAW["diagram"], { prefix: "s3-" });
  SK.play(tl, steps, AT("首先"), { anchors: { "葉綠體": AT("葉綠體") } });
顏色：Excalidraw 預設色會換成風格色（藍→primary、紅→accent、綠→accent-2、淡藍底→primary-wash…），
所以同一張圖套不同風格卡會自動換色；其他顏色維持原樣並在這裡列出，可以用 SK.excalidraw 的 palette 參數對應。
"""
import argparse, json, os, re, sys, zlib

SUPPORTED = {'rectangle', 'ellipse', 'diamond', 'line', 'arrow', 'freedraw', 'text'}
MAPPED = {'#1e1e1e', '#000000', '#343a40', '#868e96', '#1971c2', '#e03131', '#2f9e44', '#f08c00', '#6741d9', '#0c8599',
          '#a5d8ff', '#ffc9c9', '#b2f2bb', '#ffec99', '#d0bfff', '#99e9f2', '#ffffff', 'transparent'}
KEEP = ('id', 'type', 'x', 'y', 'width', 'height', 'angle', 'strokeColor', 'backgroundColor', 'fillStyle', 'strokeWidth',
        'strokeStyle', 'roughness', 'seed', 'points', 'text', 'fontSize', 'textAlign', 'lineHeight', 'containerId', 'isDeleted')


def main():
    ap = argparse.ArgumentParser(description='.excalidraw → 動畫資料')
    ap.add_argument('file'); ap.add_argument('--out', default='.'); ap.add_argument('--name')
    ap.add_argument('--order', choices=['z', 'y', 'x'], default='z', help='z＝圖層順序（預設）、y＝由上到下、x＝由左到右')
    a = ap.parse_args()
    data = json.load(open(a.file, encoding='utf-8'))
    name = a.name or re.sub(r'\.excalidraw$', '', os.path.basename(a.file))
    els = [e for e in data.get('elements', []) if not e.get('isDeleted')]
    skipped = sorted({e['type'] for e in els if e['type'] not in SUPPORTED})
    els = [{k: e[k] for k in KEEP if k in e} for e in els if e['type'] in SUPPORTED]
    if a.order != 'z':
        key = 'y' if a.order == 'y' else 'x'
        hosts = {e['id']: e for e in els}
        # 綁在容器上的文字跟著容器排
        els.sort(key=lambda e: (hosts.get(e.get('containerId'), e)[key], 0 if not e.get('containerId') else 1))
    for e in els:
        if not e.get('seed'):
            e['seed'] = zlib.crc32(e['id'].encode()) % 2147483646 + 1   # 沒有 seed 就補一個固定值（每次執行都一樣）
    os.makedirs(a.out, exist_ok=True)
    js = os.path.join(a.out, f'{name}.excalidraw.js')
    open(js, 'w', encoding='utf-8').write(
        f'// excalidraw_prep.py 由 {os.path.basename(a.file)} 產生\nwindow.EXCALIDRAW = window.EXCALIDRAW || {{}};\n'
        f'window.EXCALIDRAW[{json.dumps(name)}] = {json.dumps({"elements": els}, ensure_ascii=False)};\n')
    steps = []
    for e in els:
        if e['type'] == 'text' and e.get('containerId'):
            for s in steps:
                if s['id'] == e['containerId']:
                    s['label'] = s['label'] or e['text']
            continue
        steps.append({'id': e['id'], 'type': e['type'], 'label': e.get('text', ''), 'at': ''})
    sp = os.path.join(a.out, f'{name}.steps.json')
    json.dump(steps, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(els)} 個元素、{len(steps)} 步 → {js}、{sp}')
    for i, s in enumerate(steps, 1):
        print(f'  {i:>2}. {s["type"]:<9} {s["label"][:24]}')
    colors = sorted({c.lower() for e in els for c in (e.get('strokeColor'), e.get('backgroundColor')) if c} - MAPPED)
    if colors:
        print('  △ 這些顏色不在預設對應表，會照原色畫：' + '、'.join(colors) + '（用 SK.excalidraw 的 palette 對應到風格色）')
    if skipped:
        print('  △ 略過不支援的元素：' + '、'.join(skipped) + '（圖片請另外放成 .shot 截圖卡或 <img>）')


if __name__ == '__main__':
    main()
