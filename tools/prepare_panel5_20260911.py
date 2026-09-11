"""Prepare the confirmed Panel 5 scan without starting camera or LED output."""
import json
from pathlib import Path
import urllib.request
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/panel5-preparation-20260911/scan-ready'
WORKSPACE = ROOT / 'Scans/back_panel5_352_249_20260911_fullscan'


def main():
    OUT.mkdir(exist_ok=True)
    WORKSPACE.mkdir(exist_ok=True)
    assert not (OUT/'prepared.json').exists(), 'Inspect existing preparation before repeating'
    with urllib.request.urlopen('http://10.0.0.249/api/config', timeout=6) as response:
        config = json.load(response)
    port = next(p for p in config['outputs'] if p['id'] == 4)
    assert port['enabled'] and port['pixelCount'] == 352 and port['startUniverse'] == 139
    assert config['universeCount'] == 21
    assert [(p['pixelCount'],p['startUniverse']) for p in config['outputs'][:4]] == [(203,120),(738,122),(880,127),(810,133)]
    (OUT/'controller-readback.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    settings = dict(name='BACK_PANEL5_352_249',target='10.0.0.249',interface='10.0.0.125',
                    universe=139,count=352,rate=30,order='RGB',frame_start_universe=120,frame_universe_count=22)
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
(folder/'panel4-session-before.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
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
assert snapshot.get_led_count()==352 and list(snapshot.source_indices)==list(range(352))
assert plan['packet_gap_ms']==1.0
assert len(snapshot.packet_descriptors())==22
for index,universe,slot in ((0,139,0),(351,141,11)):
    frames=snapshot.packet_descriptors(index,on=True)
    lit=[f for f in frames if any(f.payload)]
    assert len(lit)==1 and lit[0].wire_universe==universe
    assert set(i//3 for i,v in enumerate(lit[0].payload) if v)=={slot}
assert not p.op('ui_panel/views/string').text.strip()
assert p.fetch('coverage_summary')['total']==352 and p.fetch('coverage_summary')['views']==0
assert adapter.active_hash()==before
live.assert_outputs_off(op)
assert not op('/project1').errors(recurse=True)
intent={'panel':5,'position':'third row left, below Panel 3','width_cm':30,'height_cm':30,
        'led_count':352,'controller':'10.0.0.249','physical_output':5,'gpio':19,
        'start_universe':139,'end_universe':141,'controller_frame_start':120,'controller_frame_count':22,
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
