"""Sparse unlabelled light-pattern changes; descriptive, not a FPS acceptance test."""
import json
from pathlib import Path
import cv2
import numpy as np

out=Path(__file__).resolve().parent
cap=cv2.VideoCapture('E:/LED2.mov', cv2.CAP_FFMPEG, [cv2.CAP_PROP_N_THREADS, 2])
results=[]
for start in [30,60,90,130,300,600,1000,1200,1300,1350,1380,1400,1420,1440,1450,1460,1470]:
    cap.set(cv2.CAP_PROP_POS_MSEC,start*1000)
    previous=None
    xor=[]
    identical=0
    for i in range(91):
        ok,frame=cap.read()
        if not ok: raise RuntimeError(start)
        roi=frame[400:1140:3,::3]
        mask=roi[:,:,0].astype(np.int16)-roi[:,:,2]>50
        if previous is not None:
            xor.append(int(np.count_nonzero(mask != previous)))
        previous=mask
    result={'start':start,'seconds':3,'xor_counts':xor,'changes_above_100':sum(x>100 for x in xor),'changes_above_300':sum(x>300 for x in xor),'median_xor':float(np.median(xor))}
    results.append(result)
    print(json.dumps({k:v for k,v in result.items() if k!='xor_counts'}),flush=True)
cap.release()
(out/'unlabelled-pattern-change-probes.json').write_text(json.dumps(results,indent=2),encoding='utf8')
