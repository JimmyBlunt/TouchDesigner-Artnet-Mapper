"""Export-speed transition fingerprint around the end of slow motion; no IDs."""
import json
from pathlib import Path
import cv2
import numpy as np

out=Path(__file__).resolve().parent
cap=cv2.VideoCapture('E:/LED2.mov',cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,2])
cap.set(cv2.CAP_PROP_POS_MSEC,1438*1000)
rows=[]
prev=None
for i in range(16*30+1):
    ok,frame=cap.read()
    if not ok:raise RuntimeError(i)
    roi=frame[400:1140:3,::3]
    mask=roi[:,:,0].astype(np.int16)-roi[:,:,2]>50
    if prev is not None:
        rows.append({'pts':cap.get(cv2.CAP_PROP_POS_MSEC)/1000,'mask_xor':int(np.count_nonzero(mask!=prev))})
    prev=mask
cap.release()
(out/'tail-change-fingerprints.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
for second in range(1438,1454):
    vals=[r['mask_xor'] for r in rows if second<=r['pts']<second+1]
    print(second,len(vals),sum(v>1000 for v in vals),np.median(vals),flush=True)
