"""Temporarily time live frame handlers; restore source verbatim in finally."""
import json
import time
from pathlib import Path
from audit_20260907_capture import td

OUT=Path(__file__).resolve().parents[1]/'docs/implementation-2026-09-07/performance'
START=r"""
import json
paths=[('/project1/execute2','onFrameStart'),
 ('/project1/material_phase_execute','onFrameStart'),
 ('/project1/show_control/transport_execute','onFrameEnd'),
 ('/project1/multi_controller_output/artnet_510_execute','onFrameStart'),
 ('/project1/multi_controller_output/router_status_execute','onFrameStart'),
 ('/project1/pixelblaze_mapper/preview3d/animation_driver','onFrameStart')]
paths=[(p,f) for p,f in paths if not op(p).bypass]
originals={p:op(p).text for p,_ in paths}
for path,func in paths:
    suffix='''
import time as _perf_clock
_perf_samples=[]
_perf_original=%s
def %s(frame):
    start=_perf_clock.perf_counter()
    try:
        return _perf_original(frame)
    finally:
        if len(_perf_samples)<2000:
            _perf_samples.append((_perf_clock.perf_counter()-start)*1000)
''' %% (func,func)
    op(path).text=originals[path]+suffix
result=json.dumps(originals)
""".replace('%%','%')
END=r'''
import json
paths=%r
result=json.dumps({p:list(op(p).module._perf_samples) for p in paths})
'''

if __name__=='__main__':
    target=OUT/'frame-callback-times.json'
    if target.exists(): raise ValueError('Evidence exists')
    original=td(START)
    (OUT/'frame-callback-originals.json').write_text(json.dumps(original,indent=2),encoding='utf-8')
    try:
        time.sleep(15)
        values=td(END%list(original))
        target.write_text(json.dumps(values,indent=2),encoding='utf-8')
        print(json.dumps({p:{'count':len(v),'mean_ms':sum(v)/len(v) if v else None,
           'max_ms':max(v) if v else None} for p,v in values.items()},indent=2))
    finally:
        restore='import json\noriginals=%r\nfor path,text in originals.items(): op(path).text=text\nresult=json.dumps({"restored":list(originals)})'%original
        print(td(restore))
