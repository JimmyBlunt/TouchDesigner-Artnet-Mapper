"""Standalone scientific summary figure from archived optical decisions."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'measurements/gico-td-camera-001-video-review/optical'
report=json.loads((BASE/'comparison.json').read_text())
cases=[c for c in report['cases'] if c['window']!='measure_30_end']
assert len(cases)==3
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
ax=axes[0,0];x=np.arange(3);planned=[c['fps_requested'] for c in cases]
actual=[c['variants']['including_bounded_erasures']['two_consecutive_frames']['observed_unique_fps_estimate'] for c in cases]
ax.bar(x-.18,planned,.36,color='#d5dae1',label='Testinhalt: Soll')
ax.bar(x+.18,actual,.36,color='#007d8a',label='Optisch: beobachtet')
for xi,v in zip(x,actual):ax.text(xi+.18,v+.7,f'{v:.2f}',ha='center',fontweight='bold')
ax.set_xticks(x,[f"{c['fps_requested']} FPS\n{c['real_duration_seconds']:.3g} s ausgewertet" for c in cases])
ax.set_ylim(0,35);ax.set_ylabel('Unterschiedliche sichtbare Bilder / s');ax.set_title('TD → GICO: sichtbare Bildwechsel');ax.legend(loc='upper left',fontsize=9)
paths={'measure_15':'extraction','measure_25':'extraction-25','measure_30_slow':'extraction-30'}
for ax,c in zip([axes[0,1],axes[1,0],axes[1,1]],cases):
 stats=np.load(BASE/paths[c['window']]/(c['window']+'.npz'))['stats']
 groups=[]
 for s in stats:
  ident=int(s[5]);t=float(s[1])
  if groups and ident>=0 and groups[-1][0]==ident:groups[-1][2]+=1
  else:groups.append([ident,t,1])
 stable=[]
 for ident,t,n in groups:
  if ident>=0 and n>=2 and (not stable or ident!=stable[-1][0]):stable.append((ident,t))
 ts=np.array([v[1] for v in stable]);delta=np.diff(ts)*1000
 ax.scatter(ts[1:]-stats[0,1],delta,s=7,color='#007d8a',alpha=.55,rasterized=True)
 ax.axhline(1000/c['fps_requested'],color='#ad6534',linestyle='--',label='Idealer Abstand')
 ax.set_title(f"{c['fps_requested']} FPS: Abstände erkannter neuer Bilder")
 ax.set_xlabel('Reale Sekunden im Messfenster');ax.set_ylabel('Abstand / ms');ax.set_ylim(bottom=0)
 ax.legend(fontsize=9)
fig.suptitle('Originalaufnahme LED2.mov · unabhängige Zeitlupenkalibrierung',fontsize=15,fontweight='bold')
fig.supxlabel('Mindestens zwei aufeinanderfolgende gültige Kamerabilder pro ID; begrenzte CRC-Rekonstruktion eingeschlossen.\nLücken umfassen auch nicht lesbare Bilder; keine Messung elektrischer Refreshes oder nachgewiesener Netzwerkverluste.',fontsize=9)
fig.savefig(BASE/'fps-results.png',dpi=150)
fig.savefig(BASE/'fps-results.pdf')
