"""Actual reversible TD 2D apply, isolated from the user's draft workspace.

No hardware output. Captures current actual XYZ and bindings, applies an explicit
test UV placement, verifies and restores the complete baseline in finally.
"""
import json
from pathlib import Path
from audit_20260907_capture import td

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=r'''import json
from dataclasses import replace
from pixelblaze_mapper.layout_active_snapshot import read_active_snapshot
from pixelblaze_mapper.fixture_scene import FixtureScene, project_fixture, Transform2D, scene_revision
from pixelblaze_mapper.build_layout_apply import TouchDesignerLayoutAdapter, prepare_layout, apply_plan, revert_last, digest, MAP, UV
owner=op('/project1/layout_apply')
adapter=TouchDesignerLayoutAdapter(owner)
adapter.assert_outputs_off()
baseline=adapter.capture()
assert owner.fetch('last_snapshot',None) is None, 'Existing user revert state must not be overwritten'
document,warnings=read_active_snapshot(owner)
fixtures=[]
for obj in document.scene.objects:
    f=project_fixture(document.scene,obj.object_id,projection='YX')
    coords=[p for _,p in f.sample_uv()]
    lo=[min(p[a] for p in coords) for a in range(2)]
    hi=[max(p[a] for p in coords) for a in range(2)]
    scale=tuple(.6/max(hi[a]-lo[a],1e-9) for a in range(2))
    f=replace(f, uv_transform=Transform2D(translation=tuple(.2-lo[a]*scale[a] for a in range(2)),scale=scale))
    fixtures.append(f)
model=FixtureScene(document.scene.scene_id,scene_revision(document.scene),tuple(fixtures),document.scene.expected_count)
from pixelblaze_mapper.routing_transaction import table_rows
plan=prepare_layout(document,model,mode='2d',projection='YX',source_count=document.scene.expected_count,
    base_active_hash=adapter.active_hash(),preserve_routing=True,active_map_rows=table_rows(op(MAP)))
report={'source_count':plan.source_count,'snapshot_warnings':warnings,'before_hash':digest(baseline),'hardware_output':False,'ui_draft_modified':False}
applied=False
try:
    apply_plan(plan,document,model,adapter)
    applied=True
    changed=adapter.capture()
    report.update({'apply':'passed','physical_map_unchanged':changed['texts'][MAP]==baseline['texts'][MAP],
        'bindings_unchanged':changed['bindings']==baseline['bindings'],
        'uv_changed':changed['texts'][UV]!=baseline['texts'][UV],
        'position_verification':adapter.verify(plan,baseline)})
except Exception as error:
    report.update({'apply':'failed','error':str(error)})
finally:
    if applied:
        try:
            revert_last(owner)
            report['revert']='passed'
        except Exception as error:
            report.update({'revert':'FAILED','revert_error':str(error)})
    report['after_hash']=adapter.active_hash()
    report['exact_baseline_restored']=adapter.capture()==baseline
    report['errors']=list(op('/project1').errors(recurse=True))
result=json.dumps(report)
'''

if __name__ == '__main__':
    result=td(SCRIPT)
    (ROOT/'docs/implementation-2026-09-07/live-layout-apply-probe.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
