"""Read-only optical transition localization; does not infer encoded IDs."""
import json
from pathlib import Path
import cv2
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
cap = cv2.VideoCapture('E:/LED2.mov', cv2.CAP_FFMPEG, [cv2.CAP_PROP_N_THREADS, 2])
cache = {}

def sample(index):
    if index in cache:
        return cache[index]
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(index)
    roi = frame[400:1140:3, ::3]
    blue = int(np.sum(roi[:,:,0].astype(np.int16) - roi[:,:,2] > 50))
    row = {'index': index, 'pts': cap.get(cv2.CAP_PROP_POS_MSEC)/1000, 'blue_pixels_decimated':blue}
    cache[index] = row
    return row

def boundary(name, seconds, lit_before):
    lo, hi = [round(t*30) for t in seconds]
    assert (sample(lo)['blue_pixels_decimated'] > 100) == lit_before
    assert (sample(hi)['blue_pixels_decimated'] > 100) != lit_before
    while hi-lo > 1:
        mid = (hi+lo)//2
        if (sample(mid)['blue_pixels_decimated'] > 100) == lit_before:
            lo=mid
        else:
            hi=mid
    rows = [sample(i) for i in range(lo-3,hi+4)]
    return {'name':name, 'last_before':sample(lo),'first_after':sample(hi),'neighbors':rows}

results=[]
if (OUT/'black-transitions.json').exists():
    results=json.loads((OUT/'black-transitions.json').read_text())
else:
    for name,window,lit in [('pause15_start',(610,612),True),('pause15_end',(626,628),False),('pause25_start',(1130,1132),True),('pause25_end',(1146,1148),False),('pause30_start',(1472,1474),True),('after_test_cyan',(1476,1478),False)]:
        result=boundary(name,window,lit)
        results.append(result)
        print(json.dumps(result),flush=True)
cap.release()
(OUT/'black-transitions.json').write_text(json.dumps(results,indent=2),encoding='utf8')
rows = [json.loads(line) for line in (ROOT/'gico-td-camera-001'/'submitted-frames.jsonl').read_text().splitlines()]
transitions=[]
for i,row in enumerate(rows):
    if i==0 or row['phase'] != rows[i-1]['phase']:
        transitions.append({'before':rows[i-1] if i else None,'after':row})
(OUT/'submitted-transitions.json').write_text(json.dumps(transitions,indent=2),encoding='utf8')
