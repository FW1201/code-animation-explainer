#!/usr/bin/env python3
"""程式合成背景音樂：五聲音階（宮商角徵羽）撥弦琴音＋低音持續音。無授權疑慮、固定亂數種子（可重現）。
用法：bgm_qin.py <秒數> <輸出.wav>"""
import sys, wave, numpy as np
SR = 44100; DUR = float(sys.argv[1]); OUT = sys.argv[2]
rng = np.random.default_rng(928)
n = int(SR * DUR); out = np.zeros(n)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
PENTA = [0, 2, 4, 7, 9]                        # 宮 商 角 徵 羽（D 調）
scale = [50 + o * 12 + p for o in (0, 1, 2) for p in PENTA]   # D3 起三個八度
def pluck(t0, midi, amp, dur=3.2, slide=0.0):
    s = int(t0 * SR); e = min(n, s + int(dur * SR))
    if s >= n: return
    t = np.arange(e - s) / SR
    f = hz(midi) * (1 + slide * np.exp(-t * 9))  # 起音的小滑音（吟猱感）
    ph = 2 * np.pi * np.cumsum(f) / SR
    sig = np.zeros_like(t)
    for k, a in enumerate([1, 0.55, 0.32, 0.18, 0.1, 0.06], 1):
        sig += a * np.sin(k * ph) * np.exp(-t * (1.6 + 1.1 * k))
    sig *= np.minimum(1, t / 0.004)
    out[s:e] += amp * sig
# 低音持續音（D2＋A2），緩慢起伏
t = np.arange(n) / SR
drone = 0.035 * (np.sin(2 * np.pi * hz(38) * t) + 0.5 * np.sin(2 * np.pi * hz(45) * t)) * (0.7 + 0.3 * np.sin(2 * np.pi * t / 11))
out += drone * np.minimum(1, t / 4) * np.minimum(1, (DUR - t) / 4)
# 旋律：以慢速、級進為主的五聲音階漫步
beat = 0.82; idx = 6; tt = 1.5
while tt < DUR - 3:
    idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2, 0]), 2, len(scale) - 3))
    pluck(tt, scale[idx], 0.16, slide=rng.choice([0, 0, 0.012, -0.01]))
    if rng.random() < 0.22: pluck(tt, scale[idx] - 12, 0.08)          # 八度散音
    if rng.random() < 0.18: pluck(tt + beat / 2, scale[idx + 1], 0.09)
    tt += beat * rng.choice([1, 1, 1, 2, 1.5])
    if rng.random() < 0.08: tt += beat * 2                            # 留白
# 簡易殘響
rev = np.zeros_like(out)
for d, g in [(0.083, 0.32), (0.127, 0.24), (0.191, 0.17), (0.263, 0.11)]:
    k = int(d * SR); rev[k:] += g * out[:-k]
out = out + rev
out /= np.max(np.abs(out)) + 1e-9; out *= 0.8
w = wave.open(OUT, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
