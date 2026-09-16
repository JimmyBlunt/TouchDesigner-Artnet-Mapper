"""Relocate validated active references; preserve historical evidence files."""
import json
from pathlib import Path
from tools.audit_20260907_capture import td
from tools.install_scan_workflow_ux import SNAPSHOT
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=SNAPSHOT+r'''
import importlib
from pixelblaze_mapper import workspace_relocation as relocation
importlib.reload(relocation)
root=__ROOT__
old='C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
owner=op('/project1/guided_scan')
before=snapshot()
original_storage={}
for key,value in owner.storage.items():
    try: json.dumps(value); original_storage[key]=value
    except (TypeError,ValueError): pass
fields={n.path:n.text for n in owner.findChildren() if n.family=='DAT' and n.name=='string'}
# Historical manifests stay in acquisition files. Prepared caches cannot survive
# a root change; source observations/session identities do survive.
invalidated=('capture_plan','capture_signature','manifest','merge_request','result_review','coverage_summary','scan_library_index','scan_library_preview','scan_library_visible','scan_library_selected')
active={k:v for k,v in original_storage.items() if k not in invalidated}
plan=relocation.prepare_relocation({'storage':active,'fields':fields},old,root)
for key,value in plan['value']['storage'].items(): owner.store(key,value)
for path,value in plan['value']['fields'].items(): op(path).text=value
for key in invalidated: owner.store(key, '' if key=='capture_signature' else None)
owner.store('scan_library_selected',[])
owner.unstore('scan_library_index')
owner.store('scan_library_preview',None)
for path in ('/project1/guided_scan/worker_plan','/project1/guided_scan/live_plan'):
    node=op(path)
    if node is not None: node.text='Workspace relocated. Prepare a new plan before starting.'
owner.op('ui_panel/status').par.text='Workspace moved and copied files verified. Prepare scan/3D again before starting.'
from pixelblaze_mapper import scan_coverage
scan_coverage._last_key=None
scan_coverage.refresh(op)
after=snapshot()
result=json.dumps({'checks':{'maps_routes_draft_unchanged':before['hashes']==after['hashes'],
 'outputs_off':not after['sender']['enabled'] and not any(after['native'].values()),'errors_empty':not after['errors']},
 'relocation':plan,'invalidated':invalidated,'before':before,'after':after})
'''
if __name__=='__main__':
    result=td(SCRIPT.replace('__ROOT__',repr(str(ROOT))))
    (ROOT/'docs/completion-20260910/path-relocation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result['checks']))
    assert all(result['checks'].values())
