"""Prepare a fresh Panel 4 scan after the repaired ground wiring; preserve prior capture."""
import json
from pathlib import Path
import urllib.request
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/panel4-preparation-20260911/post-repair'
WORKSPACE = ROOT / 'Scans/back_panel4_810_249_20260911_repaired'


def main():
    OUT.mkdir(exist_ok=True)
    WORKSPACE.mkdir(exist_ok=True)
    assert not (OUT/'prepared.json').exists(), 'Inspect existing preparation before repeating'
    with urllib.request.urlopen('http://10.0.0.249/api/config', timeout=6) as response:
        config = json.load(response)
    port = next(p for p in config['outputs'] if p['id'] == 3)
    assert port['enabled'] and port['pixelCount'] == 810 and port['startUniverse'] == 133
    assert config['universeCount'] == 18
    assert [(p['pixelCount'],p['startUniverse']) for p in config['outputs'][:3]] == [(203,120),(738,122),(880,127)]
    (OUT/'controller-readback.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    settings = dict(name='BACK_PANEL4_810_249',target='10.0.0.249',interface='10.0.0.125',
                    universe=133,count=810,rate=30,order='RGB',frame_start_universe=120,frame_universe_count=18)
    script = r'''
import json
from pathlib import Path
from pixelblaze_mapper import guided_scan_live as live, scan_coverage, scan_workflow_ux
from pixelblaze_mapper.build_layout_apply import TouchDesignerLayoutAdapter
from pixelblaze_mapper.scan_routing import ScanRoutingSnapshot
p=op('/project1/guided_scan')
assert live._capture is None or live._capture.process.poll() is not None
assert live._probe is None or live._probe.process.poll() is not None
assert not (p.fetch('offline_status',{}) or {}).get('running')
live.assert_outputs_off(op)
adapter=TouchDesignerLayoutAdapter(op('/project1/layout_apply'))
before=adapter.active_hash()
folder=Path(%r)
old={'storage':{k:p.fetch(k,None) for k in ('session','standalone_capture','offline_status','result_review','manifest','capture_plan','capture_status')},
     'fields':{k:p.op('ui_panel/'+k+'/string').text for k in ('views','source_ids','workspace','camera','exposure','threshold','brightness','packet_gap')}}
(folder/'session-before-restart.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
settings=json.loads(%r)
live.stage_standalone(op,settings)
p.op('ui_panel/workspace/string').text=%r
p.op('ui_panel/packet_gap/string').text='1'
p.store('capture_packet_gap_ms',1.0)
for key,value in (('offline_status',{}),('result_review',None),('manifest_view_paths',[]),
                  ('registration_context',None),('registration_proposal',None),
                  ('coverage_visual_data',None),('workflow_page','capture')):
    p.store(key,value)
for key,value in settings.items():
    field=p.op('new_capture_panel/'+key+'/string')
    if field is not None:field.text=str(value)
live.prepare(op)
scan_coverage._last_key=None
scan_coverage.refresh(op)
scan_workflow_ux.refresh(p)
plan=p.fetch('capture_plan')
snapshot=ScanRoutingSnapshot.from_dict(plan['routing'])
assert snapshot.get_led_count()==810 and list(snapshot.source_indices)==list(range(810))
assert plan['packet_gap_ms']==1.0
assert len(snapshot.packet_descriptors())==18
for index,universe,slot in ((0,133,0),(809,137,129)):
    frames=snapshot.packet_descriptors(index,on=True)
    lit=[f for f in frames if any(f.payload)]
    assert len(lit)==1 and lit[0].wire_universe==universe
    assert set(i//3 for i,v in enumerate(lit[0].payload) if v)=={slot}
assert not p.op('ui_panel/views/string').text.strip()
assert p.fetch('coverage_summary')['total']==810 and p.fetch('coverage_summary')['views']==0
assert adapter.active_hash()==before
live.assert_outputs_off(op)
assert not op('/project1').errors(recurse=True)
intent={'panel':4,'position':'second row right, below Panel 2','width_cm':30,'height_cm':30,
        'led_count':810,'controller':'10.0.0.249','physical_output':4,'gpio':14,
        'start_universe':133,'end_universe':137,'controller_frame_start':120,'controller_frame_count':18,
        'state':'scan_plan_ready_camera_check_pending','scan_started':False}
op('/project1/layout_scene_editor').store('next_panel_intent',intent)
p.op('ui_panel').openViewer()
result=json.dumps({'intent':intent,'plan':plan,'routing_summary':p.op('ui_panel/routing_summary').par.text.eval(),
 'camera_settings':{k:p.op('ui_panel/'+k+'/string').text.strip() for k in ('camera','exposure','threshold','brightness','packet_gap')},
 'active_unchanged':True,'output_off':True,'errors':[]})
''' % (str(OUT),json.dumps(settings),str(WORKSPACE))
    data=td(script)
    (OUT/'prepared.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k!='plan'},indent=2))


if __name__ == '__main__':
    main()
