"""Sample only changed operator cook counters during a loopback run."""
import json
from install_td_performance_program_20260912 import td,OUT
from td_program_benchmark_20260912 import run

PATH='/project1/show_control/transport_execute'
if __name__=='__main__':
    target=OUT/'cook-profile.json'
    if target.exists():raise ValueError('Evidence exists')
    original=td('import json\nresult=json.dumps(op(%r).text)'%PATH)
    suffix=r'''
_cook_original=onFrameEnd
_cook_paths=['/project1/topto1','/project1/res1','/project1/material_gradient_player','/project1/math1','/project1/pixelblaze_mapper/preview3d/instance_data','/project1/pixelblaze_mapper/preview3d/preview_render','/project1/madmapper_library/live_preview','/project1/show_control/slot_a_player','/project1/show_control/slot_b_player','/project1/show_control/show_led_render','/project1/legacy_source_mask']
_cook_nodes=[op(p) for p in _cook_paths if op(p) is not None]
_cook_last={};_cook_samples={n.path:[] for n in _cook_nodes}
def onFrameEnd(frame):
    _cook_original(frame)
    for n in _cook_nodes:
        count=n.totalCooks
        if count != _cook_last.get(n.path):
            if n.path in _cook_last:_cook_samples[n.path].append(n.cpuCookTime)
            _cook_last[n.path]=count
'''
    td('import json\nop(%r).text=%r\nresult=json.dumps(True)'%(PATH,original+suffix))
    try:
        run('cook-profile-loopback',25,'BACK_PANEL_249',30)
        data=td('import json\nresult=json.dumps(op(%r).module._cook_samples)'%PATH)
        result={p:{'count':len(v),'mean_ms':sum(v)/len(v) if v else 0,'max_ms':max(v) if v else 0} for p,v in data.items()}
        target.write_text(json.dumps({'summary':result,'samples':data},indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:
        td('import json\nop(%r).text=%r\nresult=json.dumps(True)'%(PATH,original))
