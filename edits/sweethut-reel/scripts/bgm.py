# Original warm café jazz-hop loop, 90 BPM, F major. Royalty-free (generated here).
import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR=48000; BPM=90; beat=60/BPM; bar=4*beat
DUR=float(sys.argv[2]) if len(sys.argv)>2 else 40
N=int(SR*(DUR+2)); L=np.zeros(N); R=np.zeros(N); rng=np.random.default_rng(3)
def lp(x,f): return sosfilt(butter(2,f,'low',fs=SR,output='sos'),x)
def hp(x,f): return sosfilt(butter(2,f,'high',fs=SR,output='sos'),x)
def mf(m): return 440*2**((m-69)/12)
def add(x,t0,pan=0.5,g=1.0):
    i=int(t0*SR); e=min(N,i+len(x)); 
    if i>=N: return
    L[i:e]+=x[:e-i]*g*np.cos(pan*np.pi/2); R[i:e]+=x[:e-i]*g*np.sin(pan*np.pi/2)
def rhodes(m,d,v=0.5):
    t=np.arange(int(SR*(d+1.2)))/SR; f=mf(m)
    idx=2.2*np.exp(-t*4)+0.3
    s=np.sin(2*np.pi*f*t+idx*np.sin(2*np.pi*f*t))
    s+=0.15*np.sin(2*np.pi*f*2*t)*np.exp(-t*6)
    env=np.minimum(1,t/0.004)*np.exp(-t*0.9); rel=np.clip((d+1.2-t)/1.2,0,1)
    trem=1+0.12*np.sin(2*np.pi*4.5*t)
    return s*env*np.where(t>d,np.exp(-(t-d)*5),1)*trem*v
def bass(m,d,v=0.6):
    t=np.arange(int(SR*d))/SR; f=mf(m)
    s=np.tanh(1.6*(np.sin(2*np.pi*f*t)+0.25*np.sin(4*np.pi*f*t)))
    env=np.minimum(1,t/0.01)*np.exp(-t*1.5)*np.clip((d-t)/0.05,0,1)
    return s*env*v
def kick():
    t=np.arange(int(SR*0.4))/SR; f=50+90*np.exp(-t*35)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
def snare():
    t=np.arange(int(SR*0.3))/SR
    n=hp(lp(rng.standard_normal(len(t)),7000),900)*np.exp(-t*18)
    return n*0.5+0.25*np.sin(2*np.pi*190*t)*np.exp(-t*30)
def shaker(v):
    t=np.arange(int(SR*0.06))/SR
    return hp(rng.standard_normal(len(t)),6000)*np.exp(-t*70)*v
def bell(m,v=0.25):
    t=np.arange(int(SR*1.5))/SR; f=mf(m)
    return v*(np.sin(2*np.pi*f*t)+0.3*np.sin(2*np.pi*f*3.01*t)*np.exp(-t*6))*np.exp(-t*3)*np.minimum(1,t/0.002)
# chords (midi) : Fmaj9 Em7 Dm9 Cmaj7 | Bbmaj7 Am7 Gm9 C9sus
prog=[([53,57,60,64,67],41),([52,55,59,62],40),([50,53,57,60,64],38),([48,52,55,59],36),
      ([46,50,53,57],34),([45,48,52,55],33),([43,46,50,53,57],31),([48,53,55,58,62],36)]
nb=int(DUR/bar)+1
mel=[72,74,76,79,77,76,74,72]
for b in range(nb):
    t0=b*bar; ch,root=prog[b%8]
    # rhodes: hit on 1 and on "and of 2" (swing-ish)
    for k,m in enumerate(ch):
        add(rhodes(m,beat*1.4,0.18),t0+k*0.012,0.35+0.06*k)
        add(rhodes(m,beat*1.6,0.13),t0+beat*2.5+k*0.01,0.65-0.06*k)
    # bass
    add(bass(root,beat*1.4),t0,0.5); add(bass(root,beat*0.45,0.45),t0+beat*1.5,0.5); add(bass(root+7,beat*1.2,0.5),t0+beat*2.5,0.5)
    # drums: groove
    for kt in [0,beat*1.75,beat*2.5]: add(kick(),t0+kt,0.5,0.75)
    for st in [beat,beat*3]: add(snare(),t0+st+0.012,0.5,0.4)
    for s in range(16):
        sw=0.03 if s%2 else 0
        add(shaker(0.13 if s%4==2 else 0.07),t0+s*beat/4+sw,0.7)
    # sparse bell melody from bar 4
    if b>=4:
        for j in range(2): add(bell(mel[(b*2+j)%8]+12*(b%2==1 and j==1)),t0+beat*(0.5+2*j),0.3+0.4*j)
mix=np.stack([L,R],1)
# glue: soft lowpass of highs, saturation, master fade
mix=np.stack([lp(mix[:,0],12000),lp(mix[:,1],12000)],1)
mix=np.tanh(mix/np.max(np.abs(mix))*1.4)
n=int(SR*DUR); mix=mix[:n]
fi=int(SR*0.05); mix[:fi]*=np.linspace(0,1,fi)[:,None]
fo=int(SR*2.5); mix[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5
mix=mix/np.max(np.abs(mix))*0.89
wavfile.write(sys.argv[1],SR,(mix*32767).astype(np.int16))
print("bgm ok",DUR)
