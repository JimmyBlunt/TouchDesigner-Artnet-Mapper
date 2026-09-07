"""Fixed-node cook-rate measurements. No input, force cook or sender activation."""
import json
import sys
import time
from pathlib import Path
from audit_20260907_capture import td
OUT=Path(__file__).resolve().parents[1]/'docs/implementation-2026-09-07/performance-next'
SCRIPT=r'''
import json,time,hashlib
paths=['/project1/script4','/project1/esp_artnet_live_pack','/project1/esp_artnet_out',
 '/project1/multi_controller_output/pack_ws2812_node','/project1/multi_controller_output/pack_apa102_esp',
 '/project1/multi_controller_output/dmxout_ws2812_node','/project1/multi_controller_output/dmxout_apa102_esp',
 '/project1/madmapper_library/live_preview','/project1/res1','/project1/math1',
 '/project1/pixelblaze_mapper/preview3d/instance_data','/project1/LED_PREVIEW_OUT']
nodes={p:{'cooks':int(passive(op(p)).totalCooks),'cpu_ms':float(passive(op(p)).cpuCookTime)} for p in paths}
sources=['/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv',
 '/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config']
result=json.dumps({'wall':time.perf_counter(),'frame':int(absTime.frame),'file':project.name,
 'nodes':nodes,'native_active':{p:bool(op(p).par.active.eval()) for p in paths if op(p).type=='dmxout'},
 'hashes':{p:hashlib.sha256(op(p).text.encode()).hexdigest() for p in sources},
 'controls':{p.name:str(p.eval()) for p in op('/project1/madmapper_player_controls').customPars},
 'errors':op('/project1').errors(recurse=True),
 'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()})
'''
if __name__=='__main__':
    label=sys.argv[1]
    if not label.replace('-','').isalnum(): raise ValueError(label)
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(label+'.json')
    if target.exists(): raise ValueError('Evidence exists')
    samples=[td(SCRIPT)]
    for _ in range(3):
        time.sleep(10)
        samples.append(td(SCRIPT))
    intervals=[]
    for a,b in zip(samples,samples[1:]):
        seconds=b['wall']-a['wall']
        intervals.append({'seconds':seconds,'rates':{p:(b['nodes'][p]['cooks']-v['cooks'])/seconds for p,v in a['nodes'].items()}})
    data={'samples':samples,'intervals':intervals}
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'rates':[i['rates'] for i in intervals],'errors':samples[-1]['errors'],
      'sender':samples[-1]['sender']['enabled'],'native_active':samples[-1]['native_active']},indent=2))
