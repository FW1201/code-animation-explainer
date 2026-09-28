# 程式合成背景音樂（無授權疑慮）。用法：python bgm.py <秒數> <輸出.wav>，需要 numpy；再用 ffmpeg 轉 mp3。
import numpy as np, wave
import sys
SR=44100; DUR=int(sys.argv[1]) if len(sys.argv)>1 else 480; BPM=84; beat=60/BPM
t=np.arange(int(SR*DUR))/SR
def note(m): return 440*2**((m-69)/12)
prog=[[48,55,59,64],[45,52,55,60],[41,48,52,57],[43,50,55,59]]  # Cmaj7 Am7 Fmaj7 G
bar=beat*4*2  # 每和弦兩小節
out=np.zeros_like(t)
rng=np.random.default_rng(7)
for i in range(int(DUR/bar)+1):
    ch=prog[i%4]; s=int(i*bar*SR); e=min(len(t),int((i+1)*bar*SR+SR*1.5))
    if s>=len(t): break
    tt=np.arange(e-s)/SR
    env=np.minimum(1,tt/1.2)*np.minimum(1,np.maximum(0,(bar+1.5-tt)/1.5))
    for m in ch:
        f=note(m)
        out[s:e]+=0.05*env*(np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*1.003*tt)+0.2*np.sin(2*np.pi*2*f*tt))
    # 琶音：八分音符
    arp=[ch[1]+12,ch[2]+12,ch[3]+12,ch[2]+12]
    for k in range(16):
        if rng.random()<0.25: continue
        ps=s+int(k*beat/2*SR); pe=min(len(t),ps+int(SR*1.6))
        if ps>=len(t): break
        pt=np.arange(pe-ps)/SR; f=note(arp[k%4])
        out[ps:pe]+=0.035*np.exp(-pt*3.2)*(np.sin(2*np.pi*f*pt)+0.3*np.sin(2*np.pi*2*f*pt))*np.minimum(1,pt/0.005)
# 簡單低通
a=0.18; y=np.zeros_like(out); acc=0.0
for i in range(0,len(out)):
    acc+=a*(out[i]-acc); y[i]=acc
fade=np.minimum(1,np.minimum(t/3,(DUR-t)/4)); y*=fade
y=y/np.max(np.abs(y))*0.6
st=np.stack([y,np.roll(y,300)],1)
w=wave.open((sys.argv[2] if len(sys.argv)>2 else 'bgm.wav'),'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
