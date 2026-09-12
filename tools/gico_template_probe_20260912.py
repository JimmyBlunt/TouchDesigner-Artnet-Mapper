import cv2,numpy as np,json,sys
from pathlib import Path
sys.path.insert(0,'tools');import gico_camera_analyze as a
r=Path('measurements/gico-camera-001-original-review');report=json.loads(Path('measurements/gico-camera-001/run.json').read_text());ph={x['name']:x for x in report['phases']};c=cv2.VideoCapture('E:/LED Full.mov')
def at(t):return cv2.resize(a.frame_at(c,t),None,fx=.5,fy=.5)
dark=at(58.62+(ph['black_reference']['start']+ph['black_reference']['end'])/2);gray=cv2.cvtColor(dark,cv2.COLOR_BGR2GRAY);mask=np.zeros_like(gray);mask[110:300,20:520]=255;pts=cv2.goodFeaturesToTrack(gray,200,.01,8,mask=mask)
def align(im):
 g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);q,st,err=cv2.calcOpticalFlowPyrLK(gray,g,pts,None,winSize=(31,31),maxLevel=3);st=st.ravel()==1;M,inl=cv2.estimateAffinePartial2D(pts[st],q[st],method=cv2.RANSAC,ransacReprojThreshold=1.5)
 if inl.sum()<100:raise ValueError('Registration failed')
 return cv2.warpAffine(im,M,(540,960),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
def chrom(im):
 f=im.astype(np.float32);return f[:,:,0]-(f[:,:,1]+f[:,:,2])/2
base=chrom(dark)
def signal(im):
 q=chrom(align(im))-base;return q[300:595,:515]-np.median(q[110:300,20:520])
ims=[]
for i in range(21):
 p=ph['marker_%02d'%i];ims.append(signal(at(58.62+(p['start']+p['end'])/2)))
templates=np.stack(ims,axis=-1);sel=np.max(templates,axis=-1)>35;A=templates[sel].astype(float);P=np.linalg.pinv(A);print('features',A.shape,'condition',np.linalg.cond(A),'rank',np.linalg.matrix_rank(A))
rows=[]
for t in [100,170,225]:
 y=signal(at(t))[sel];coef=P@y;rel=float(np.linalg.norm(y-A@coef)/np.linalg.norm(y));rows.append({'t':t,'coef':np.round(coef,3).tolist(),'residual_relative':rel});print(rows[-1])
np.savez_compressed(r/'template-model.npz',dark=dark,pts=pts,mask=sel,templates=A,pinv=P)
(r/'template-probe.json').write_text(json.dumps({'features':A.shape,'condition':np.linalg.cond(A),'rows':rows},indent=2));c.release()
