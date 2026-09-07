"""Scoped performance deployment and evidence; hardware output must remain off."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/implementation-2026-09-07/performance'
INSPECT = r'''
import json, hashlib
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
paths=['/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv',
 '/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config',
 '/project1/multi_controller_output/gico_port_config/port_config','/project1/multi_controller_output/gico_port_config/global_config']
frame=op('/project1/material_phase_execute')
live=op('/project1/madmapper_library/live_preview')
controls=op('/project1/madmapper_player_controls')
result=json.dumps({'file':project.name,'folder':project.folder,
 'hashes':{p:digest(op(p).text) for p in paths if op(p) is not None},
 'controls':{p.name:p.eval() for p in controls.customPars},
 'phase_execute':{p.name:str(p.eval()) for p in frame.pars()},
 'phase_callback':frame.text,'live_cooks':int(live.totalCooks),'live_cpu':float(live.cpuCookTime),
 'live_gpu':float(live.gpuCookTime),'live_lock':live.lock,
 'live_parameters':{p.name:str(p.eval()) for p in live.pars() if p.name.startswith(('res','vec0','output'))},
 'errors':op('/project1').errors(recurse=True),
 'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()})
'''

INSTALL_MATERIALS = r'''
import json, importlib
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
from pixelblaze_mapper import build_p1_material_state, build_unified_material_browser
importlib.reload(build_p1_material_state)
importlib.reload(build_unified_material_browser)
op('/project1/material_phase_execute').text=build_p1_material_state._frame_callback_source()
op('/project1/material_browser/unified_runtime').text=build_unified_material_browser._runtime_source()
result=json.dumps({'installed':['material_phase_execute','material_browser/unified_runtime'],
 'errors':op('/project1').errors(recurse=True)})
'''

EXECUTES = r'''
import json
rows=[]
for n in op('/project1').findChildren():
    if n.family=='DAT' and n.type=='execute':
        rows.append({'path':n.path,'parameters':{p.name:str(p.eval()) for p in n.pars()},'text':n.text})
result=json.dumps(rows)
'''

HOT_SOURCES = r'''
import json
paths=['/project1/chopexec1','/project1/script4_callbacks','/project1/esp_artnet_live_pack_callbacks',
 '/project1/multi_controller_output/pack_ws2812_node_callbacks','/project1/multi_controller_output/pack_apa102_esp_callbacks']
result=json.dumps({p:{'text':op(p).text,'parameters':{v.name:str(v.eval()) for v in op(p).pars()}} for p in paths})
'''

INSTALL_LAYOUT_SHOW = r'''
import json, importlib, time
from pixelblaze_mapper import layout_session_storage, layout_scene_td, layout_fixture_td, build_show_sequencer
for module in (layout_session_storage,layout_scene_td,layout_fixture_td,build_show_sequencer):
    importlib.reload(module)
sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()
assert not sender['enabled']
owner=op('/project1/layout_scene_editor')
manifest=layout_session_storage.prepare_save(owner)
timings=[]
for i in range(3):
    start=time.perf_counter()
    layout_session_storage.persist_layout(owner,layout_scene_td.editor(owner))
    layout_session_storage.persist_fixtures(owner,layout_fixture_td.history(owner),owner.fetch('fixture_preview',None))
    timings.append((time.perf_counter()-start)*1000)
repair=build_show_sequencer.repair_placeholder_inputs(op('/project1/show_control'),constant_type=constantTOP)
for path in repair['repaired']: op(path).cook(force=True)
result=json.dumps({'layout':manifest,'warm_snapshot_ms':timings,'placeholder_repair':repair,
 'errors':op('/project1').errors(recurse=True),'sender_enabled':sender['enabled']})
'''

INSTALL_PACKER = r'''
import json,importlib,hashlib
from pixelblaze_mapper import realtime_packer,layout_session_storage
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
source=op('/project1/math1')
channels=tuple(tuple(float(channel[i]) for i in range(source.numSamples)) for channel in source.chans()[:3])
modules=[op('/project1/multi_controller_output/'+name).module for name in
 ('pack_ws2812_node_callbacks','pack_apa102_esp_callbacks')]
before=[module._controller_packer().pack_channels(*channels) for module in modules]
importlib.reload(realtime_packer)
importlib.reload(layout_session_storage)
after=[module._controller_packer().pack_channels(*channels) for module in modules]
assert before==after,'Packed frames changed'
result=json.dumps({'byte_identical':True,'payloads':[{'frames':len(frames),
 'bytes':sum(len(f) for f in frames),'sha256':hashlib.sha256(b''.join(frames)).hexdigest()} for frames in after],
 'errors':op('/project1').errors(recurse=True)})
'''

if __name__ == '__main__':
    action=sys.argv[1]
    script=INSPECT if action.startswith('inspect-') else INSTALL_MATERIALS if action=='install-materials' else EXECUTES if action=='executes' else INSTALL_LAYOUT_SHOW if action=='install-layout-show' else HOT_SOURCES if action=='hot-sources' else INSTALL_PACKER if action=='install-packer' else None
    if script is None: raise ValueError(action)
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(action+'.json')
    if target.exists(): raise ValueError('Evidence already exists')
    data=td(script)
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('controls','phase_execute','phase_callback','live_parameters','sender')},indent=2) if isinstance(data,dict) else 'Recorded '+str(len(data))+' callbacks')
