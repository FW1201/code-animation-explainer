#!/usr/bin/env python3
"""環境檢查：列出這台電腦缺哪些工具，並給出對應作業系統的安裝指令。只用 Python 標準函式庫。

用法：
  python doctor.py              # 檢查全部路線
  python doctor.py --json       # 機器可讀
在 Claude 裡也可以直接說「幫我檢查環境」，Agent 會跑這支程式再照提示協助安裝。

路線（不是每條都要裝）：
  基本出片     python3、ffmpeg／ffprobe、Node.js 22+、playwright＋chromium（render_seek.mjs、style_catalog.py --render）
  配音與讀音   numpy、pypinyin、sherpa-onnx（pron_check.py、align_audio.py --asr、bgm.py）
  素材與截圖   puppeteer-core（shoot.mjs）、npm（hanzi_prep.py 下載筆順資料）
  舊工具       opencc、whisper-cli（verify_vo.py、tts_elevenlabs.py --t2s），新專案不需要
"""
import argparse, importlib.util, json, os, platform, re, shutil, subprocess, sys

OS = {'Darwin': 'mac', 'Windows': 'win'}.get(platform.system(), 'linux')
HERE = os.path.dirname(os.path.abspath(__file__))

# 每個工具在三種作業系統的安裝指令
INSTALL = {
    'ffmpeg': {'mac': 'brew install ffmpeg', 'win': 'winget install Gyan.FFmpeg', 'linux': 'sudo apt install ffmpeg'},
    'node': {'mac': 'brew install node@22', 'win': 'winget install OpenJS.NodeJS.LTS', 'linux': '用 nvm 安裝：curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && nvm install 22'},
    'playwright': {'all': f'cd "{HERE}" && npm i playwright && npx playwright install chromium'},
    'puppeteer-core': {'all': f'cd "{HERE}" && npm i puppeteer-core（另需本機 Chrome，或設定 CHROME_PATH）'},
    'pip': {'all': 'python3 -m pip install {pkg}'},
    'python': {'mac': 'brew install python', 'win': 'winget install Python.Python.3.12', 'linux': 'sudo apt install python3 python3-pip'},
    'brew': {'mac': '沒有 Homebrew：/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'},
}


def how(tool, pkg=None):
    d = INSTALL[tool]
    cmd = d.get('all') or d.get(OS) or d.get('linux')
    return cmd.replace('{pkg}', pkg or tool)


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ''


def has_py(mod):
    return importlib.util.find_spec(mod) is not None


def node_module(name):
    """在 scripts／目前資料夾／PLAYWRIGHT_PATH 找得到 node 套件嗎"""
    if name == 'playwright' and os.environ.get('PLAYWRIGHT_PATH') and os.path.isdir(os.environ['PLAYWRIGHT_PATH']):
        return True
    for base in (HERE, os.getcwd()):
        d = base
        while True:
            if os.path.isdir(os.path.join(d, 'node_modules', name)):
                return True
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
    out = run(['npm', 'root', '-g']) if shutil.which('npm') else ''
    return bool(out) and os.path.isdir(os.path.join(out.splitlines()[-1], name))


def chromium():
    if os.environ.get('PLAYWRIGHT_BROWSERS_PATH') and os.path.isdir(os.environ['PLAYWRIGHT_BROWSERS_PATH']):
        return True
    cache = {'mac': '~/Library/Caches/ms-playwright', 'win': '~/AppData/Local/ms-playwright', 'linux': '~/.cache/ms-playwright'}[OS]
    p = os.path.expanduser(cache)
    return os.path.isdir(p) and any(n.startswith('chromium') for n in os.listdir(p))


def checks():
    out = []

    def add(group, name, ok, need, fix='', note=''):
        out.append({'group': group, 'name': name, 'ok': bool(ok), 'required': need, 'fix': '' if ok else fix, 'note': note})

    v = sys.version_info
    add('基本出片', f'Python {v.major}.{v.minor}', v >= (3, 9), True, how('python'), '需要 3.9 以上')
    add('基本出片', 'ffmpeg／ffprobe', shutil.which('ffmpeg') and shutil.which('ffprobe'), True, how('ffmpeg'), '合成影片、混音、檢查音量')
    nv = run(['node', '--version']) if shutil.which('node') else ''
    m = re.match(r'v(\d+)', nv)
    add('基本出片', f'Node.js {nv or "（未安裝）"}', m and int(m.group(1)) >= 22, True, how('node'), '需要 22 以上')
    add('基本出片', 'playwright（npm 套件）', node_module('playwright'), True, how('playwright'), '逐格渲染 render_seek.mjs')
    add('基本出片', 'Chromium（playwright 瀏覽器）', chromium(), True, 'npx playwright install chromium')
    add('配音與讀音', 'numpy', has_py('numpy'), False, how('pip', 'numpy'), 'bgm.py、pron_check.py')
    add('配音與讀音', 'pypinyin', has_py('pypinyin'), False, how('pip', 'pypinyin'), '讀音檢核')
    add('配音與讀音', 'sherpa-onnx', has_py('sherpa_onnx'), False, how('pip', 'sherpa-onnx'), '讀音檢核、逐字對時（第一次執行自動下載約 400 MB 模型）')
    add('素材與截圖', 'npm', shutil.which('npm'), False, how('node'), 'hanzi_prep.py 下載筆順資料')
    add('素材與截圖', 'puppeteer-core', node_module('puppeteer-core'), False, how('puppeteer-core'), '批次截網頁 shoot.mjs')
    add('舊工具（可略）', 'opencc', has_py('opencc'), False, how('pip', 'opencc-python-reimplemented'), 'verify_vo.py、--t2s')
    add('舊工具（可略）', 'whisper-cli', shutil.which(os.environ.get('WHISPER_CLI', 'whisper-cli')), False, 'https://github.com/ggml-org/whisper.cpp', 'verify_vo.py')
    if os.path.exists('.env'):
        gi = open('.gitignore', encoding='utf-8').read() if os.path.exists('.gitignore') else ''
        add('安全', '.env 已列入 .gitignore', re.search(r'^\.env\b', gi, re.M), True, "echo .env >> .gitignore", 'API key 不能進版控')
    if OS == 'mac' and not shutil.which('brew'):
        add('基本出片', 'Homebrew（Mac 套件管理）', False, False, how('brew'), '上面的 brew 指令需要它')
    return out


def main():
    ap = argparse.ArgumentParser(description='環境檢查')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    res = checks()
    if a.json:
        print(json.dumps({'os': OS, 'checks': res}, ensure_ascii=False, indent=1)); return
    print(f'作業系統：{platform.system()}（{OS}）\n')
    group = None
    for r in res:
        if r['group'] != group:
            group = r['group']; print(f'【{group}】')
        mark = '✓' if r['ok'] else ('✗' if r['required'] else '－')
        print(f"  {mark} {r['name']}" + (f"　{r['note']}" if r['note'] else ''))
        if not r['ok']:
            print(f"      安裝：{r['fix']}")
    miss = [r for r in res if r['required'] and not r['ok']]
    opt = [r for r in res if not r['required'] and not r['ok'] and not r['group'].startswith('舊工具')]
    print(f"\n必要項目缺 {len(miss)} 個" + (f"；選用項目缺 {len(opt)} 個（要用到那條路線再裝）" if opt else ''))
    sys.exit(1 if miss else 0)


if __name__ == '__main__':
    main()
