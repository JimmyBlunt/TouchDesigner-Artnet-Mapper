"""Offline frame-by-frame LED2 extraction in independently timed intervals."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,json,hashlib,sys,time
from collections import Counter
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.gico_optical_erasure import decode_scores
from pixelblaze_mapper.gico_camera_benchmark import decode_levels,summarize

WINDOWS=[('measure_15',133.,609.,15,8.,-93.),('measure_25',653.,1129.,25,8.,-93.),
         ('measure_30_slow',1173.,1444.,30,8.,-93.),
         ('measure_30_end',1450.,1471.,30,1.,1254.)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--window');args=ap.parse_args()
 args.output.mkdir(parents=True,exist_ok=True)
 cv2.setNumThreads(2)
 model=np.load(args.model);dark,pts,coords,low,weight=(model[k] for k in ('dark','pts','coords','low','weight'))
 clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8));gray=clahe.apply(cv2.cvtColor(dark,cv2.COLOR_BGR2GRAY))
 cap=cv2.VideoCapture('E:/LED2.mov',cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,2]);assert cap.isOpened()
 total=0;started=time.perf_counter()
 try:
  for name,start,end,fps,scale,offset in WINDOWS:
   if args.window and args.window!=name:continue
   outfile=args.output/(name+'.npz')
   if outfile.exists():raise ValueError('Existing evidence: '+str(outfile))
   cap.set(cv2.CAP_PROP_POS_MSEC,start*1000)
   scores=[];stats=[];direct=[];bounded=[];reasons=Counter();prev=None
   while True:
    ok,im=cap.read()
    if not ok:raise ValueError('Premature end of video')
    t=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
    if t>=end:break
    if t<start:continue
    if prev is not None and t<=prev:raise ValueError('Nonmonotonic PTS')
    prev=t;im=cv2.resize(im,(540,960));current=clahe.apply(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY))
    q,st,_=cv2.calcOpticalFlowPyrLK(gray,current,pts,None,winSize=(25,25),maxLevel=3)
    good=st.ravel()==1
    M,inliers=cv2.estimateAffinePartial2D(pts[good],q[good],method=cv2.RANSAC,ransacReprojThreshold=1.5)
    count=int(inliers.sum()) if inliers is not None else 0
    residual=float('nan');value=strict=None;why='registration_failed';erased=0;score=np.full(21,np.nan)
    if M is not None and count>=70:
     predicted=pts[good].reshape(-1,2)@M[:,:2].T+M[:,2]
     residual=float(np.median(np.linalg.norm(predicted-q[good].reshape(-1,2),axis=1)[inliers.ravel()==1]))
     if residual<=1.:
      aligned=cv2.warpAffine(im,M,(540,960),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
      aligned=cv2.GaussianBlur(aligned,(3,3),.65)
      patches=np.array([cv2.getRectSubPix(aligned,(15,15),tuple(xy)).reshape(-1) for xy in coords],float)
      score=np.sum((patches-low)*weight,axis=-1)
      strict=decode_levels(score*100,np.zeros(21),np.ones(21)*100)[0]
      value,why,erased=decode_scores(score)
    real=(t-offset)/scale
    direct.append({'time':real,'id':strict});bounded.append({'time':real,'id':value});reasons[why]+=1
    scores.append(score)
    stats.append([t,real,count,residual,-1 if strict is None else strict,-1 if value is None else value,erased]+(M.ravel().tolist() if M is not None else [float('nan')]*6))
    total+=1
    if total%1000==0:print(json.dumps({'window':name,'samples':total,'video_s':round(t,2),'elapsed_s':round(time.perf_counter()-started,1)}),flush=True)
   np.savez_compressed(outfile,scores=np.array(scores,dtype=np.float32),stats=np.array(stats))
   report={'window':name,'video_start':start,'video_end':end,'scale':scale,'offset':offset,'real_duration':(end-start)/scale,
      'time_basis':'confirmed 8x middle' if scale==8 else '1x end hypothesis; validate independently decoded ID progression',
      'requested_fps':fps,'samples':len(stats),'reasons':dict(reasons),'model_sha256':hashlib.sha256(args.model.read_bytes()).hexdigest(),
      'direct_only':summarize(direct,fps),'bounded_erasures':summarize(bounded,fps)}
   (args.output/(name+'.json')).write_text(json.dumps(report,indent=2))
   print(json.dumps({'finished':name,'samples':len(stats),'reasons':dict(reasons),'bounded_rate':report['bounded_erasures'].get('observed_unique_fps')}),flush=True)
 finally:cap.release()

if __name__=='__main__':main()
