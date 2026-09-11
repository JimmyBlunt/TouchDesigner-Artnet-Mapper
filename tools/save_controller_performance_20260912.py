"""Finalize tested transport settings and save an output-off native checkpoint."""
import hashlib
import json
from pathlib import Path
import urllib.request
from audit_20260907_capture import td
from performance_checkpoint_20260907 import SAVE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/controller-performance-20260912'
SCRIPT=r'''
import json,importlib
from pixelblaze_mapper import sender_external_source,router_dynamic_ui
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
r=op('/project1/multi_controller_output');d=r.op('artnet_510_sender_callbacks')
importlib.reload(sender_external_source);d.text=sender_external_source.install_source(d.text)
r.op('controller_config')[3,'rate']='8';r.store('live_packet_gap_ms',{'BACK_PANEL_249':1.5})
r.store('external_sender_settings',{'enabled':True,'python':'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe'})
u=r.op('ui_callbacks');old="fps = state.get('telemetry', {}).get('actual_send_fps', 0.0)"
if old in u.text:
    text=u.text.replace(old,'from pixelblaze_mapper.sender_external_source import rate_label')
    text=text.replace('%.1f actual fps','%s').replace(', fps, _source_pixels()',', rate_label(state), _source_pixels()')
    compile(text,'<ui_callbacks>','exec');u.text=text
r.store('router_card_drafts',{});r.store('router_card_baselines',{});r.store('router_card_name','BACK_PANEL_249');router_dynamic_ui.select(r,reload=True)
u.module._set_status('OUTPUT OFF | external sender prepared | 8 FPS / 1.5 ms | 30 FPS target not reached')
u.module.refresh_status(force=True)
assert_outputs_off(op);assert not op('/project1').errors(recurse=True)
result=json.dumps({'sender':d.module.status(),'controllers':r.op('controller_config').text,'gap':r.fetch('live_packet_gap_ms'),'external':r.fetch('external_sender_settings'),'source_count':op('/project1/math1').numSamples,'errors':op('/project1').errors(recurse=True)})
'''

if __name__=='__main__':
    assert not (OUT/'save.json').exists()
    state=td(SCRIPT)
    (OUT/'final-native-state.json').write_text(json.dumps(state,indent=2))
    print(state,flush=True)
    config=json.load(urllib.request.urlopen('http://10.0.0.248/api/config',timeout=8))
    assert config==json.loads((OUT/'config-before.json').read_text())
    (OUT/'controller-config-restored-final.json').write_text(json.dumps(config,indent=2))
    path=ROOT/'PixelblazeMapper_CONTROLLER_PERFORMANCE_20260912.toe'
    request=urllib.request.Request('http://127.0.0.1:9981/api/td/server/exec',
        data=json.dumps({'script':SAVE%path.as_posix()}).encode(),headers={'Content-Type':'application/json'})
    response=json.load(urllib.request.urlopen(request,timeout=120));assert response['success'],response
    saved=json.loads(response['data']['result']);actual=Path(saved['folder'])/saved['file']
    saved['sha256']=hashlib.sha256(actual.read_bytes()).hexdigest()
    (OUT/'save.json').write_text(json.dumps(saved,indent=2))
    print({k:saved[k] for k in ['saved','file','sender_off']},flush=True)
