import numpy as np, wave
w=wave.open('audio.wav'); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
N=4096; hop=480; win=np.hanning(N); f=np.fft.rfftfreq(N,1/sr)
T=[];F=[];L=[];TON=[];SUB=[]
for i in range(int(7.4*sr),int(14.9*sr),hop):
    seg=x[i:i+N]; S=np.abs(np.fft.rfft(seg*win)); band=(f>250)&(f<700)
    k=np.argmax(S*band); a,b,c=np.log(S[k-1:k+2]+1e-12); p=0.5*(a-c)/(a-2*b+c); fk=(k+p)*sr/N
    lvl=20*np.log10(np.sqrt(np.mean(seg**2))+1e-9)
    ton=20*np.log10(S[k]/(np.median(S[(f>150)&(f<3000)])+1e-12))
    sub=20*np.log10(S[int(round(fk/2*N/sr))]/S[k]+1e-12); h2=20*np.log10(S[int(round(2*fk*N/sr))]/S[k]+1e-12)
    T.append(i/sr+N/2/sr);F.append(fk);L.append(lvl);TON.append(ton);SUB.append((sub,h2))
T,F,L,TON=map(np.array,(T,F,L,TON)); SUB=np.array(SUB)
play=L>-30
# stable segments: freq within 1.5 % for >=0.15 s while playing
segs=[];s=None
for j in range(len(F)):
    ok=play[j] and TON[j]>40
    if ok and s is not None and abs(F[j]-np.median(F[s:j]))/np.median(F[s:j])<0.015: continue
    if s is not None and j-s>=15: segs.append((T[s],T[j-1],np.median(F[s:j]),np.max(L[s:j]),np.median(SUB[s:j,0]),np.median(SUB[s:j,1])))
    s=j if ok else None
for a,b,fm,lv,sb,h2 in segs: print(f"{a:6.2f}-{b:6.2f}s  {fm:6.1f} Hz  peak {lv:6.1f} dBFS  f/2 {sb:6.1f} dB  2f {h2:6.1f} dB")
# tone breaks during playing
br=[(round(T[j],2),round(F[j])) for j in range(len(F)) if play[j] and TON[j]<35]
print('frames while playing with weak tone (<35 dB over floor):',len(br),'of',play.sum(), br[:12])
import numpy as np, wave, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
w=wave.open('audio.wav'); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
N=4096; hop=480; win=np.hanning(N); f=np.fft.rfftfreq(N,1/sr); rows=[]
for i in range(0,len(x)-N,hop):
    seg=x[i:i+N]; S=np.abs(np.fft.rfft(seg*win)); band=(f>250)&(f<700); k=np.argmax(S*band)
    a,b,c=np.log(S[k-1:k+2]+1e-12) if k>0 else (0.0,0.0,0.0); p=0.5*(a-c)/(a-2*b+c) if (a-2*b+c)!=0 else 0.0
    rows.append((i/sr+N/2/sr,(k+p)*sr/N,20*np.log10(np.sqrt(np.mean(seg**2))+1e-9)))
R=np.array(rows); np.savetxt('pitch-track.csv',R,delimiter=',',header='t_s,loudest_peak_250_700_hz,level_dbfs',fmt='%.3f',comments='')
fig,ax=plt.subplots(figsize=(10,4.2),dpi=110)
ax.axhspan(313,367,color='#4c78a8',alpha=.15,label='C21 band, hole closed (313-367 Hz)')
ax.axhspan(432,508,color='#f58518',alpha=.15,label='C22 band, hole open (432-508 Hz)')
ax.axhline(340.1,color='#4c78a8',ls='--',lw=1,label='model, closed 340.1 Hz'); ax.axhline(469.8,color='#f58518',ls='--',lw=1,label='model, open 469.8 Hz')
m=R[:,2]>-30; sc=ax.scatter(R[m,0],R[m,1],c=R[m,2],s=6,cmap='viridis',vmin=-30,vmax=-8)
fig.colorbar(sc,ax=ax,label='level, dBFS (phone, uncalibrated)')
ax.set_xlim(7.4,14.9); ax.set_ylim(300,540); ax.set_xlabel('time in the video, s'); ax.set_ylabel('pitch, Hz')
ax.set_title('First printed pigeon whistle (v0.1 file): played pitch, frames louder than -30 dBFS'); ax.legend(fontsize=7,loc='lower left',ncol=2)
fig.tight_layout(); fig.savefig('pitch-track.png')
