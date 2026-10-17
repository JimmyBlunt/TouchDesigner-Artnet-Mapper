from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/panel8-replacement-299-20261018'
WORK=ROOT/'Scans/Panel8_OUT1_299_20261018'
MANIFEST=next(WORK.glob('scan-*.json'))
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
candidate=Path(manifest['output_directory'])/'candidate_3d.csv'
rows=np.genfromtxt(candidate,delimiter=',',names=True)
ids=rows['index'].astype(int)
pts=np.column_stack([rows[a] for a in 'xyz'])
center=pts.mean(0)
_,singular,basis=np.linalg.svd(pts-center,full_matrices=False)
flat=(pts-center)@basis[:2].T
fig,axes=plt.subplots(2,3,figsize=(15,10))
for ax,item in zip(axes.flat,manifest['inputs']):
    data=np.genfromtxt(item['path'],delimiter=',',names=True)
    ax.scatter(data['u'],data['v'],c=data['index'],cmap='turbo',s=7)
    for i,u,v in zip(data['index'],data['u'],data['v']):
        if int(i)%10==0 or int(i) in (0,2,60,62,92,94,298):ax.annotate(str(int(i)),(u,v),fontsize=5)
    ax.invert_yaxis(); ax.set_aspect('equal'); ax.set_title(Path(item['path']).parent.name[:18])
ax=axes.flat[-1]
ax.scatter(flat[:,0],flat[:,1],c=ids,cmap='turbo',s=8)
for i,p in zip(ids,flat):
    if i%5==0 or i in (0,2,60,62,92,94,298): ax.annotate(str(i),p,fontsize=6)
ax.set_aspect('equal'); ax.set_title('3D reconstruction projected onto fitted plane')
fig.tight_layout(); fig.savefig(OUT/'scan-analysis.png',dpi=150)
hull=ConvexHull(flat)
report={'candidate':str(candidate),'ids':ids.tolist(),'missing':sorted(set(range(299))-set(ids)),
    'error_percentiles':np.percentile(rows['error'],[0,50,90,95,99,100]).tolist(),
    'singular_values':singular.tolist(),'center':center.tolist(),'basis':basis.tolist(),
    'hull':[{'id':int(ids[i]),'point':flat[i].tolist()} for i in hull.vertices]}
(OUT/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('ids','basis','center')}))

# Align the long, straight final row; inspect which end contains the short leg.
lookup=dict(zip(ids,pts))
right=lookup[298]-lookup[283]; right/=np.linalg.norm(right)
down=np.mean([lookup[i] for i in ids if i<94],0)-np.mean([lookup[i] for i in ids if i>=267],0)
down-=right*np.dot(down,right); down/=np.linalg.norm(down)
xy=np.column_stack(((pts-center)@right,-(pts-center)@down))
fig,axs=plt.subplots(1,2,figsize=(13,7))
for ax,sign in zip(axs,(1,-1)):
    ax.scatter(sign*xy[:,0],xy[:,1],c=ids,cmap='turbo',s=17)
    for i,p in zip(ids,xy):
        if i%5==0 or i in (0,2,60,62,92,94,298,283):ax.annotate(str(i),(sign*p[0],p[1]),fontsize=7)
    ax.set_aspect('equal');ax.set_title('Triangle down | horizontal sign '+str(sign));ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(OUT/'orientation-options.png',dpi=140)
(OUT/'fit-basis.json').write_text(json.dumps({'right':right.tolist(),'down':down.tolist(),'center':center.tolist()}),encoding='utf-8')
