# Synthesize a small premium SFX kit + original BGM (royalty-free, made here).
import numpy as np, sys, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR=48000; out=sys.argv[1]; os.makedirs(out,exist_ok=True)
rng=np.random.default_rng(7)
def t(d): return np.arange(int(SR*d))/SR
def bp(x,lo,hi,o=4): return sosfilt(butter(o,[lo,hi],'band',fs=SR,output='sos'),x)
def lp(x,f,o=4): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x)
def hp(x,f,o=4): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x)
def norm(x,pk=0.89):
    m=np.max(np.abs(x)); return x/m*pk if m>0 else x
def st(l,r=None): return np.stack([l,l if r is None else r],1)
def save(n,x):
    if x.ndim==1: x=st(x)
    wavfile.write(f"{out}/{n}.wav",SR,(norm(x)*32767).astype(np.int16))
def verb(x,dec=1.2,mix=0.25):
    n=int(SR*dec); ir=rng.standard_normal(n)*np.exp(-np.linspace(0,7,n)); ir=lp(ir,6000)
    ir2=rng.standard_normal(n)*np.exp(-np.linspace(0,7,n)); ir2=lp(ir2,6000)
    L=np.pad(np.convolve(x,ir),(0,1))[:len(x)+n]; R=np.pad(np.convolve(x,ir2),(0,1))[:len(x)+n]
    d=np.pad(x,(0,n)); L=d+mix*L/np.max(np.abs(L)+1e-9)*np.max(np.abs(x)); R=d+mix*R/np.max(np.abs(R)+1e-9)*np.max(np.abs(x))
    return st(L,R)
# whoosh: swept band noise, pan L->R
def whoosh(d=0.55,f0=300,f1=5000,rev=False):
    n=int(SR*d); x=rng.standard_normal(n); y=np.zeros(n); seg=256
    fs=np.geomspace(f0,f1,n//seg+1)
    if rev: fs=fs[::-1]
    for i in range(0,n,seg):
        f=fs[i//seg]; lo=max(80,f*0.5); hi=min(20000,f*1.6)
        y[i:i+seg]=bp(x[max(0,i-2048):i+seg],lo,hi,2)[-len(x[i:i+seg]):]
    env=np.sin(np.linspace(0,np.pi,n))**2; env=env*np.exp(-np.linspace(0,1.2,n)) if not rev else env
    y=y*env; p=np.linspace(0,1,n)
    Lw=verb(y*np.cos(p*np.pi/2),0.5,0.2)[:,0]; Rw=verb(y*np.sin(p*np.pi/2),0.5,0.2)[:,1]; return st(Lw,Rw)
save("whoosh",whoosh())
save("whoosh_soft",whoosh(0.8,200,2500)*0.7)
# pop: sine pitch drop + click
tt=t(0.18); f=900*np.exp(-tt*28)+260; ph=2*np.pi*np.cumsum(f)/SR
pop=np.sin(ph)*np.exp(-tt*30)+0.3*hp(rng.standard_normal(len(tt)),3000)*np.exp(-tt*300)
save("pop",verb(pop,0.4,0.12))
# sparkle / shimmer: random high bell partials
def bell(f,d=1.6,a=1):
    tt=t(d); s=sum(w*np.sin(2*np.pi*f*r*tt)*np.exp(-tt*k) for r,w,k in [(1,1,3),(2.76,.5,5),(5.4,.25,8),(8.93,.12,12)])
    return a*s*(1-np.exp(-tt*400))
n=int(SR*1.8); L=np.zeros(n); R=np.zeros(n)
for i in range(14):
    s0=int(SR*(0.02+i*0.045+rng.uniform(0,0.02))); f=rng.choice([2093,2349,2637,3136,3520,4186])*rng.uniform(.995,1.005)
    b=bell(f,1.2,0.6*np.exp(-i*0.12)); e=min(n,s0+len(b)); pan=rng.uniform(0.15,.85)
    L[s0:e]+=b[:e-s0]*np.cos(pan*np.pi/2); R[s0:e]+=b[:e-s0]*np.sin(pan*np.pi/2)
air=hp(rng.standard_normal(n),7000)*np.exp(-t(1.8)*3)*0.05
save("sparkle",st(L+air,R+air))
# ding: warm bell
save("ding",verb(bell(1318.5,2.2)+0.5*bell(1975.5,2.2),1.5,0.3))
# impact: sub boom + soft noise
tt=t(1.2); f=110*np.exp(-tt*6)+38; boom=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*3.5)
boom+=0.25*lp(rng.standard_normal(len(tt)),1800)*np.exp(-tt*12)
save("impact",verb(boom,1.0,0.15))
# riser: noise + rising tone, ends sharply
tt=t(1.0); r=hp(rng.standard_normal(len(tt)),1500)*(tt/tt[-1])**3
tone=np.sin(2*np.pi*np.cumsum(300+900*(tt/tt[-1])**2)/SR)*(tt/tt[-1])**2*0.4
save("riser",verb(r*0.6+tone,0.8,0.2))
# swipe/tick for word-ish accents: soft paper tick
tt=t(0.08); tick=bp(rng.standard_normal(len(tt)),2000,9000)*np.exp(-tt*80)
save("tick",tick)
# cash/kaching-ish chime for CTA: two bells
c=np.zeros(int(SR*2.2)); b1=bell(2637,2); b2=bell(3520,2); c[:len(b1)]+=b1; c[int(SR*.09):int(SR*.09)+len(b2)]+=b2
save("chime",verb(c,1.4,0.3))
print("sfx ok")
