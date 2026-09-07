"""Read-only assertions/evidence after real mouse/keyboard input."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=r'''import json
from dataclasses import asdict
from pixelblaze_mapper.layout_scene_td import editor, active_hash
from pixelblaze_mapper.layout_fixture_td import history
from pixelblaze_mapper.layout_scene_adapter import scene_revision
owner=op('/project1/layout_scene_editor')
scene=editor(owner).current.scene
fixtures=history(owner).current
result=json.dumps({'scene_hash':scene_revision(scene),'active_hash':active_hash(owner),'count':scene.expected_count,
    'view':owner.fetch('layout_view',None),'status':owner.op('ui_panel/status').par.text.eval(),
    'fixtures':[{'id':f.fixture_id,'output':asdict(f.output_transform),'uv':asdict(f.uv_transform)} for f in fixtures.fixtures],
    'errors':list(owner.errors(recurse=True))})
'''
if __name__=='__main__':
    label=sys.argv[1]
    if not label.replace('-','').isalnum(): raise ValueError('Simple label required')
    result=td(SCRIPT)
    (ROOT/'docs/implementation-2026-09-07'/('ui-layout-'+label+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
