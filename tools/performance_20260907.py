"""Bounded read-only TD cook inventory. No force cook or hardware activation."""
import json
import sys
import time
from pathlib import Path
from audit_20260907_capture import td

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/implementation-2026-09-07/performance'
SCRIPT=r'''
import json
import time
rows=[]
paths = [
 '/project1/madmapper_library/live_preview',
 '/project1/madmapper_material_player', '/project1/material_gradient_player',
 '/project1/res1', '/project1/noise_Simplex4D', '/project1/LED_PREVIEW_OUT',
 '/project1/layout_scene_editor/scene_render', '/project1/show_control/runtime',
 '/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype/interactive_camera/renderView/render1',
 '/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype/mesh_rear_left_data',
 '/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype/mesh_rear_right_data',
 '/project1/multi_controller_output/pack_ws2812_node',
 '/project1/material_browser/unified_image_24', '/project1/material_browser/unified_image_9',
 '/project1/material_browser/ui_preview', '/project1/madmapper_library/ui_preview',
 '/project1/topto1', '/project1/math1']
for path in paths:
    n = op(path)
    if n is None: continue
    try:
        rows.append({'path':n.path,'type':n.type,'cooks':int(n.totalCooks),
          'cpu_ms':float(n.cpuCookTime),'gpu_ms':float(getattr(n,'gpuCookTime',0)),
          'lock':bool(getattr(n,'lock',False))})
    except Exception: pass
result=json.dumps({'wall_seconds':time.perf_counter(),'seconds':float(absTime.seconds),'frame':int(absTime.frame),'nodes':rows,
 'file':project.name,'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status(),
 'controls':{p.name:p.eval() for p in op('/project1/madmapper_player_controls').customPars},
 'browser_state':op('/project1/material_browser/unified_state').text,
 'library_state':op('/project1/madmapper_library/browser_state').text,
 'errors':op('/project1').errors(recurse=True)})
'''
if __name__=='__main__':
    label=sys.argv[1]
    if not label.replace('-','').isalnum(): raise ValueError(label)
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(label+'.json')
    if target.exists(): raise ValueError('Evidence exists')
    first=td(SCRIPT)
    time.sleep(10)
    last=td(SCRIPT)
    elapsed=last['wall_seconds']-first['wall_seconds']
    before={v['path']:v for v in first['nodes']}
    active=[]
    for row in last['nodes']:
        old=before.get(row['path'])
        if old is None: continue
        delta=row['cooks']-old['cooks']
        if delta>0: active.append(dict(row,delta=delta,cooks_per_second=delta/elapsed))
    active.sort(key=lambda v:v['cpu_ms'],reverse=True)
    record={'elapsed':elapsed,'first':first,'last':last,'active':active}
    target.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'elapsed':elapsed,'active_count':len(active),'top_cpu':active[:25],
      'top_gpu':sorted(active,key=lambda v:v['gpu_ms'],reverse=True)[:15],
      'errors':last['errors'],'sender_enabled':last['sender']['enabled']},indent=2))
