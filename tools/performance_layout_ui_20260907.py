"""Readback/restore for genuine native mouse tests; never activates output."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td
OUT=Path(__file__).resolve().parents[1]/'docs/implementation-2026-09-07/performance'
SCRIPT=r'''
import json,hashlib,builtins
from dataclasses import asdict
from pixelblaze_mapper.layout_fixture_td import history,current,refresh
from pixelblaze_mapper.layout_scene_td import editor
from pixelblaze_mapper.layout_session_storage import fixture_snapshot,restore_fixtures
from pixelblaze_mapper.layout_scene_adapter import document_json
owner=op('/project1/layout_scene_editor')
action=%r
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
if action=='begin':
    assert not hasattr(builtins,'_codex_fixture_test_before')
    builtins._codex_fixture_test_before=fixture_snapshot(history(owner))
elif action=='restore':
    owner.store('fixture_history',restore_fixtures(builtins._codex_fixture_test_before))
    owner.store('fixture_preview',None)
    refresh(owner)
    assert fixture_snapshot(history(owner))==builtins._codex_fixture_test_before
    del builtins._codex_fixture_test_before
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
result=json.dumps({'action':action,'fixture':asdict(current(owner)),
 'history_depth':[len(history(owner)._undo),len(history(owner)._redo)],
 'scene_hash':digest(document_json(editor(owner).current)),
 'active_hashes':{p:digest(op(p).text) for p in ['/project1/pixelblaze_mapper/map_active',
 '/project1/pixelblaze_mapper/effect_panel_uv','/project1/multi_controller_output/controller_config',
 '/project1/multi_controller_output/segment_config']},'errors':op('/project1').errors(recurse=True)})
'''
if __name__=='__main__':
    action=sys.argv[1]
    if not action.replace('-','').isalnum(): raise ValueError(action)
    target=OUT/('ui-'+action+'.json')
    if target.exists(): raise ValueError('Evidence exists')
    data=td(SCRIPT%action)
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'action':action,'history_depth':data['history_depth'],
      'transforms':[{k:v for k,v in f.items() if 'transform' in k} for f in data['fixture']['fixtures']],
      'hashes':data['active_hashes'],'errors':data['errors']},indent=2))
