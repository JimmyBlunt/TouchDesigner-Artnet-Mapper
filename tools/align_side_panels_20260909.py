"""Guarded draft-only integration and roundtrip verification."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/implementation-2026-09-07/side-alignment'
PREPARE=r'''
import json, hashlib
from pathlib import Path
from pixelblaze_mapper.layout_scene_td import editor, active_hash, refresh, frame_view, status
from pixelblaze_mapper.layout_scene_adapter import document_json, load_document_json, LayoutEditor
from pixelblaze_mapper.layout_scene import SceneHistory
from pixelblaze_mapper.complete_side_rescan import complete_side_measurements
from pixelblaze_mapper.side_alignment_draft import prepare
root=Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
owner=op('/project1/layout_scene_editor'); session=editor(owner)
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
before=session.current; baseline=active_hash(owner)
rawfile=root/'mappings/sources/complete_new_0_1183_raw_2026-08-24.json'
repaired,estimated=complete_side_measurements(json.loads(rawfile.read_text()))
updated,report=prepare(before,repaired,estimated)
history=LayoutEditor(before); history.commit(updated)
assert history.undo()==before
assert history.redo()==updated
assert load_document_json(document_json(updated))==updated
report['undo_redo_passed']=True
report['document_roundtrip_passed']=True
report['raw_sha256']=hashlib.sha256(rawfile.read_bytes()).hexdigest()
report['active_hash_before']=baseline
report['active_hash_after']=active_hash(owner)
assert report['active_hash_before']==report['active_hash_after']
'''

def main():
    mode=sys.argv[1]
    if mode=='prepare':
        script=PREPARE+"\nresult=json.dumps({k:v for k,v in report.items() if k!='internal_binding_id_map'})"
    elif mode=='apply':
        script=PREPARE+r'''
backup=root/'Backup/Implementation/side-alignment-before.workspace.json'
target=root/'Backup/Implementation/side-alignment-draft.workspace.json'
assert not backup.exists() and not target.exists(), 'Evidence exists; inspect before repeating'
backup.write_text(document_json(before),encoding='utf-8')
fixtures_before=owner.op('fixture_document').text
try:
 session.commit(updated)
 session.select(report['panels'][0]['object_id'])
 owner.store('side_alignment_report',report)
 owner.store('view_angles',(-140.,8.))
 owner.store('view_zoom',1.7)
 refresh(owner)
 frame_view(owner)
 assert active_hash(owner)==baseline
 assert owner.op('fixture_document').text==fixtures_before
 assert not op('/project1').errors(recurse=True)
 assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
 target.write_text(document_json(session.current),encoding='utf-8')
 status(owner,'SIDE PANELS DRAFT | measured sizes / approved orientation | positions PHOTO ESTIMATE | ACTIVE OUTPUT UNCHANGED')
 report['draft_integrated']=True
 report['fixture_document_unchanged']=True
 report['objects']=len(session.current.scene.objects)
 report['points']=len(session.current.scene.world_points())
 report['errors']=''.join(op('/project1').errors(recurse=True))
 owner.store('side_alignment_report',report)
except:
 if session.current!=before: session.undo()
 session.select(before.scene.objects[0].object_id)
 refresh(owner)
 raise
result=json.dumps(report)
'''
    elif mode=='verify':
        script=r'''
import json
from pathlib import Path
from pixelblaze_mapper.layout_scene_td import editor,active_hash
from pixelblaze_mapper.layout_scene_adapter import document_json,load_document_json
from pixelblaze_mapper.layout_session_storage import layout_snapshot,restore_layout
owner=op('/project1/layout_scene_editor'); session=editor(owner)
report=owner.fetch('side_alignment_report')
snapshot=layout_snapshot(session)
restored=restore_layout(snapshot)
target=Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/Backup/Implementation/side-alignment-draft.workspace.json')
result=json.dumps({'workspace_matches_disk':session.current==load_document_json(target.read_text(encoding='utf-8')),
 'session_history_roundtrip':layout_snapshot(restored)==snapshot,
 'active_unchanged':active_hash(owner)==report['active_hash_before'],
 'sender_off':not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled'],
 'objects':len(session.current.scene.objects),'points':len(session.current.scene.world_points()),
 'errors':''.join(op('/project1').errors(recurse=True))})
'''
    else: raise ValueError(mode)
    value=td(script)
    if isinstance(value,str): value=json.loads(value)
    OUT.mkdir(exist_ok=True)
    (OUT/f'{mode}-evidence.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in value.items() if k!='internal_binding_id_map'},indent=2))

if __name__=='__main__': main()
