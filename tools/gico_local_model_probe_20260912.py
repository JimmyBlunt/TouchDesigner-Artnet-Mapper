import cv2,numpy as np,json,sys
from pathlib import Path
sys.path.insert(0,'tools');import gico_camera_analyze as a
from pixelblaze_mapper import gico_camera_benchmark as b
r=Path('measurements/gico-camera-001-original-review');rep=json.loads(Path('measurements/gico-camera-001/run.json').read_text());ph={x['name']:x for x in rep['phases']};mod=np.load(r/'template-model.npz');dark=mod['dark'];pts=mod['pts'];gray=cv2.cvtColor(dark,cv2.COLOR_BGR2GRAY);coords=np.array(json.loads((r/'calibration-initial/calibration.json').read_text())['panels'][0]['xy'])/2;c=cv2.VideoCapture('E:/LED Full.mov')
def at(t):return cv2.resize(a.frame_at(c,t),None,fx=.5,fy=.5)
def patches(im):
 g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);q,st,err=cv2.calcOpticalFlowPyrLK(gray,g,pts,None,winSize=(31,31),maxLevel=3);st=st.ravel()==1;M,il=cv2.estimateAffinePartial2D(pts[st],q[st],method=cv2.RANSAC,ransacReprojThreshold=1.5)
 if il.sum()<100:raise ValueError('Insufficient static registration features')
 aligned=cv2.warpAffine(im,M,(540,960),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP);aligned=cv2.GaussianBlur(aligned,(3,3),.65)
 return np.array([cv2.getRectSubPix(aligned,(19,19),tuple(xy.astype(float))).reshape(-1) for xy in coords],float)
train=[patches(dark)]
for i in range(21):
 p=ph['marker_%02d'%i];train.append(patches(at(58.62+(p['start']+p['end'])/2)))
train=np.array(train);low=[];weight=[]
for i in range(21):
 off=np.delete(train[:,i],i+1,axis=0);mu=off.mean(0);delta=train[i+1,i]-mu;var=off.var(0);w=delta/(var+100);w/=np.dot(w,delta);low.append(mu);weight.append(w)
low=np.array(low);weight=np.array(weight)
def scores(ps):return np.sum((ps-low)*weight,axis=-1)
checks=[]
for i in range(21):
 p=ph['marker_%02d'%i];v=scores(patches(at(58.62+p['start']+.25)));expected=np.eye(21)[i];checks.append({'marker':i,'on':float(v[i]),'off_max':float(np.delete(v,i).max()),'max_abs_error':float(np.abs(v-expected).max())})
print('holdout',checks)
rows=[]
for t in [100,170,225]:
 v=scores(patches(at(t)));row={'time':t,'scores':np.round(v,3).tolist(),'decode':b.decode_levels(v*100,np.zeros(21),np.ones(21)*100)};rows.append(row);print(row)
np.savez_compressed(r/'local-model.npz',dark=dark,pts=pts,coords=coords,low=low,weight=weight,train=train)
(r/'local-model-validation.json').write_text(json.dumps({'method':'Independent local RGB diagonal discriminant; known one-hot calibration only; blur and static-board affine registration; separate quarter-phase holdout images','holdout':checks,'probe':rows},indent=2));c.release()
