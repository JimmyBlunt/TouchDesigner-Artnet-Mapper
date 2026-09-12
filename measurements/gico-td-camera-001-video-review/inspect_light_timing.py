"""Sparse optical timing reconnaissance; this is not frame-ID decoding."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

out=Path(__file__).resolve().parent
cap=cv2.VideoCapture('E:/LED2.mov')
rows=[]
boundary='--boundaries' in sys.argv
times=(list(range(608,635,2))+list(range(1128,1155,2))+list(range(1450,1484,2))
       if boundary else sorted(set(list(np.arange(0,1484,8))+list(np.arange(0,120,2)))))
tiles=[]
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000)
    ok,frame=cap.read()
    if not ok:
        rows.append({'failed':float(t)})
        continue
    roi=frame[400:1140]
    rows.append({'pts':cap.get(cv2.CAP_PROP_POS_MSEC)/1000,
                 'blue_pixels':int(np.sum((roi[:,:,0].astype(float)-roi[:,:,2])>50))})
    if boundary:
        small=cv2.resize(frame,(180,320))
        cv2.putText(small,str(t)+'s',(4,18),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
        tiles.append(small)
cap.release()
name='boundary-light-timing.json' if boundary else 'sparse-light-timing.json'
(out/name).write_text(json.dumps(rows,indent=2),encoding='utf8')
if boundary:
    tiles.extend([np.zeros((320,180,3),np.uint8)]*((6-len(tiles)%6)%6))
    cv2.imwrite(str(out/'boundary-contact-sheet.jpg'),np.vstack([np.hstack(tiles[i:i+6]) for i in range(0,len(tiles),6)]))
