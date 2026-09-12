"""Frozen calibration-only RGB marker model for the new LED2 recording."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import sys,json
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.gico_optical_erasure import decode_scores
from pixelblaze_mapper.gico_camera_benchmark import decode_levels
OUT=ROOT/'measurements/gico-td-camera-001-video-review/optical'
cv2.setNumThreads(2)
cap=cv2.VideoCapture('E:/LED2.mov',cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,2])
times=[26.4,27.2,28.4,29.2,30.2,31.2,32.2,33.2,34.2,35.2,36.2,37.2,40.4,47.2,55.2,63.2,71.2,79.2,87.2,95.2,103.2]
def at(t):
 cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read();assert ok
 return cv2.resize(im,(540,960))
dark=at(620)
clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8))
gray=clahe.apply(cv2.cvtColor(dark,cv2.COLOR_BGR2GRAY))
mask=np.zeros_like(gray);mask[60:245,25:510]=255;mask[570:640,25:500]=255
pts=cv2.goodFeaturesToTrack(gray,140,.01,8,mask=mask)
def align(im):
 current=clahe.apply(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY))
 q,st,_=cv2.calcOpticalFlowPyrLK(gray,current,pts,None,winSize=(25,25),maxLevel=3)
 good=st.ravel()==1;M,il=cv2.estimateAffinePartial2D(pts[good],q[good],method=cv2.RANSAC,ransacReprojThreshold=1.5)
 if M is None or il.sum()<70:
  correlation,M=cv2.findTransformECC(gray.astype(np.float32)/255,current.astype(np.float32)/255,np.eye(2,3,dtype=np.float32),cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-5),mask,5)
  assert correlation>.8,correlation
 return cv2.warpAffine(im,M,(540,960),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
images=[align(at(t)) for t in times]
coords=[]
for i,im in enumerate(images):
 excess=im[:,:,0].astype(float)-im[:,:,2]
 excess[:260]=0;excess[522:]=0;excess[:,:55]=0;excess[:,500:]=0
 smooth=cv2.GaussianBlur(excess,(5,5),1.)
 _,_,_,loc=cv2.minMaxLoc(smooth)
 coords.append(loc)
coords=np.array(coords,dtype=float)
def patches(im):
 im=cv2.GaussianBlur(im,(3,3),.65)
 return np.array([cv2.getRectSubPix(im,(15,15),tuple(xy)).reshape(-1) for xy in coords],float)
train=np.array([patches(dark)]+[patches(im) for im in images])
low=[];weight=[]
for i in range(21):
 off=np.delete(train[:,i],i+1,axis=0);mu=off.mean(0);delta=train[i+1,i]-mu
 # Local ridge fit uses only the black/one-hot calibration. The full local
 # covariance separates neighboring light spill from the requested marker.
 design=train[:,i]-mu
 target=np.zeros(len(train));target[i+1]=1
 w=design.T@np.linalg.solve(design@design.T+np.eye(len(train))*10000,target)
 low.append(mu);weight.append(w)
low=np.array(low);weight=np.array(weight)
def score(im):return np.sum((patches(align(im))-low)*weight,axis=-1)
holdout=[]
for i,t in enumerate(times):
 v=score(at(t+.2));holdout.append({'marker':i,'time':t+.2,'on':float(v[i]),'off_max':float(np.delete(v,i).max()),'off_min':float(np.delete(v,i).min())})
probes=[]
for t in [145,200,400,700,900,1100,1200,1300,1400,1450,1460]:
 v=score(at(t));probes.append({'time':t,'score':v.tolist(),'strict':decode_levels(v*100,np.zeros(21),np.ones(21)*100),'bounded':decode_scores(v)})
np.savez_compressed(OUT/'model.npz',dark=dark,pts=pts,coords=coords,low=low,weight=weight,train=train)
(OUT/'model-validation.json').write_text(json.dumps({'times':times,'coords':coords.tolist(),'patch_size':15,'holdout':holdout,'probes':probes},indent=2))
overlay=dark.copy()
for i,xy in enumerate(coords.astype(int)):
 cv2.circle(overlay,tuple(xy),5,(0,255,0),1);cv2.putText(overlay,str(i),tuple(xy+[3,-5]),cv2.FONT_HERSHEY_SIMPLEX,.38,(0,0,255),1)
cv2.imwrite(str(OUT/'marker-overlay.png'),overlay)
tiles=[]
for i,im in enumerate(images):
 tile=im[255:530,45:510].copy();cv2.putText(tile,f'{i} @ {times[i]}s',(4,20),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,0,255),1);tiles.append(tile)
tiles += [np.zeros_like(tiles[0])]*((-len(tiles))%4)
cv2.imwrite(str(OUT/'marker-proof.jpg'),np.vstack([np.hstack(tiles[j:j+4]) for j in range(0,len(tiles),4)]))
cap.release()
print(json.dumps({'coords':coords.tolist(),'holdout':holdout,'probes':[{'time':p['time'],'strict':p['strict'],'bounded':p['bounded']} for p in probes]}),flush=True)
