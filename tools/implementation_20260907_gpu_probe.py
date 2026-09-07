"""Reversible current-renderer check; requires output OFF, restores controls."""
import json
from pathlib import Path
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r'''import json
import numpy as np
c=op('/project1/madmapper_player_controls')
sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks')
assert not sender.module.status()['enabled']
names=('Intensity','Contrast','Colormode','Gradientstrength')
before={name:c.par[name].eval() for name in names}
def pixels():
    for path in ('/project1/madmapper_library/live_preview','/project1/visual_source_switch','/project1/material_gradient_player','/project1/res1'):
        op(path).cook(force=True)
    a=op('/project1/res1').numpyArray(delayed=False)
    return {'max_rgb':float(np.max(a[:,:,:3])), 'mean_rgb':float(np.mean(a[:,:,:3])), 'shape':list(a.shape)}
measurements={}
try:
    measurements['baseline']=pixels()
    c.par.Intensity=0
    measurements['intensity_zero']=pixels()
    assert measurements['intensity_zero']['max_rgb'] < 0.00001, 'Blackout has nonzero RGB'
    c.par.Intensity=before['Intensity']
    c.par.Colormode='original'
    measurements['original']=pixels()
finally:
    for name,value in before.items(): c.par[name]=value
    op('/project1/material_state_runtime').module.controls_changed()
    restored=pixels()
assert not sender.module.status()['enabled']
result=json.dumps({'measurements':measurements,'restored_controls':{name:c.par[name].eval() for name in names},'expected_controls':before,'restored_frame':restored,'errors':list(op('/project1').errors(recurse=True))})
'''

if __name__ == '__main__':
    result=td(SCRIPT)
    (ROOT/'docs/implementation-2026-09-07/gpu-material-probe.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
