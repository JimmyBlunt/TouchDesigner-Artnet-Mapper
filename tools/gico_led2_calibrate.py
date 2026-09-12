"""Find the ordered one-hot calibration in LED2; no sender-ID inference."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
from pathlib import Path
import json
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'measurements/gico-td-camera-001-video-review/optical'
OUT.mkdir(exist_ok=True)
cv2.setNumThreads(2)
cap=cv2.VideoCapture('E:/LED2.mov')
mask=np.zeros((960,540),np.uint8)
poly=np.array([[55,485],[55,380],[112,364],[250,364],[255,397],[373,397],[376,260],[399,260],[407,340],[493,340],[498,449],[390,451],[390,493],[335,496],[334,521],[203,521],[200,490]],np.int32)
cv2.fillPoly(mask,[poly],1)
samples=[]; frames={};i=0
while True:
    ok,im=cap.read()
    if not ok:break
    t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
    if t>115:break
    if i%6==0:
        small=cv2.resize(im,(540,960))
        excess=small[:,:,0].astype(float)-small[:,:,2]
        binary=np.uint8((excess>45)&(mask==1))*255
        count,labels,stats,centroids=cv2.connectedComponentsWithStats(binary)
        components=[]
        for k in range(1,count):
            if stats[k,cv2.CC_STAT_AREA]>=8:
                components.append({'xy':centroids[k].tolist(),'area':int(stats[k,cv2.CC_STAT_AREA])})
        components.sort(key=lambda c:-c['area'])
        samples.append({'time':t,'components':components})
        frames[len(samples)-1]=small
    i+=1
cap.release()
(OUT/'calibration-recon.json').write_text(json.dumps(samples,indent=2))
# Stable single-light runs. The phase sequence, not expected frame IDs, labels them.
runs=[];current=[]
for index,s in enumerate(samples):
    cs=s['components']
    valid=len(cs)==1 or (len(cs)>1 and cs[1]['area']<cs[0]['area']*.18)
    xy=np.array(cs[0]['xy']) if valid else None
    if xy is None or (current and np.linalg.norm(xy-np.array(samples[current[-1]]['components'][0]['xy']))>12):
        if len(current)>=2:runs.append(current)
        current=[]
    if xy is not None:current.append(index)
if len(current)>=2:runs.append(current)
records=[];tiles=[]
for j,run in enumerate(runs):
    a,z=run[0],run[-1];mid=run[len(run)//2]
    xy=np.median([samples[k]['components'][0]['xy'] for k in run],axis=0)
    record={'index':j,'start':samples[a]['time'],'end':samples[z]['time'],'mid':samples[mid]['time'],'xy':xy.tolist(),'samples':len(run)}
    records.append(record)
    tile=frames[mid][250:530,45:510].copy()
    cv2.putText(tile,f"{j}: {record['start']:.1f}-{record['end']:.1f}s",(5,20),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,0,255),1)
    tiles.append(tile)
    cv2.imwrite(str(OUT/f'cal-run-{j:02d}.png'),frames[mid])
(OUT/'calibration-runs.json').write_text(json.dumps(records,indent=2))
if tiles:
    tiles += [np.zeros_like(tiles[0])]*((-len(tiles))%4)
    cv2.imwrite(str(OUT/'calibration-contact.jpg'),np.vstack([np.hstack(tiles[j:j+4]) for j in range(0,len(tiles),4)]))
print(json.dumps(records),flush=True)
