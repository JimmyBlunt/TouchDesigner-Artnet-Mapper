"""Save/reopen checkpoint with primitive-state hashes and output-off assertions."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td
from storage_roundtrip_20260907 import SNAPSHOT
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/implementation-2026-09-07/performance'
CHECK=SNAPSHOT+r'''
value=json.loads(result)
from pixelblaze_mapper.layout_session_storage import layout_snapshot,fixture_snapshot
stable={key:value[key] for key in ('file','folder','table_hashes','controls','workspace_hash','material_id',
 'library_parameter_store','p1_store','runtime_pickle_failures','errors','sender')}
stable['errors']=''.join(stable['errors'])
stable['layout_history_hash']=digest(json.dumps(layout_snapshot(editor(owner)),sort_keys=True))
stable['fixture_history_hash']=digest(json.dumps(fixture_snapshot(history(owner)),sort_keys=True))
stable['fixture_history_depth']=[len(history(owner)._undo),len(history(owner)._redo)]
stable['ui_status']=str(ui.status)
result=json.dumps(stable)
'''
SAVE=r'''
import json,pickle
from pixelblaze_mapper.layout_session_storage import prepare_save,prepare_apply_save,TRANSIENT_KEYS
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
manifest=prepare_save(op('/project1/layout_scene_editor'))
prepare_apply_save(op('/project1/layout_apply'))
op('/project1/show_control/callbacks').module.sync()
op('/project1/madmapper_library/runtime').module._persist_parameter_store()
op('/project1/material_state_runtime').module._persist()
excluded={'/project1':{'p1_material_runtime_cache','p1_material_state_runtime_schema'},
 '/project1/madmapper_library':{'material_hover_context_cache','material_parameter_context_cache'},
 '/project1/layout_scene_editor':set(TRANSIENT_KEYS),
 '/project1/layout_apply':{'prepared_plan','prepared_workspace_key','prepared_workspace_hash','applying'}}
for node in [op('/project1')]+op('/project1').findChildren():
    for key,value in node.storage.items():
        if key not in excluded.get(node.path,set()): pickle.dumps(value)
assert not op('/project1').errors(recurse=True)
saved=project.save(%r,saveExternalToxs=False)
result=json.dumps({'saved':saved,'file':project.name,'folder':project.folder,'manifest':manifest,
 'ui_status':str(ui.status),'sender_off':not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']})
'''
if __name__=='__main__':
    action=sys.argv[1]
    if action in ('before-save','after-reopen'):
        target=OUT/(action+'.json')
        if target.exists(): raise ValueError('Evidence exists')
        data=td(CHECK)
        target.write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in data.items() if k not in ('library_parameter_store','p1_store','controls','sender','table_hashes')},indent=2))
    elif action=='save':
        target=ROOT/'Backup/Implementation/PixelblazeMapper_20260907_PERFORMANCE_VERIFIED.toe'
        if target.exists() or (OUT/'save.json').exists(): raise ValueError('Candidate/evidence exists')
        data=td(SAVE%target.as_posix())
        (OUT/'save.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data,indent=2))
    elif action=='reload':
        saved=json.loads((OUT/'save.json').read_text())
        target=Path(saved['folder'])/saved['file']
        assert saved['saved'] and target.is_file()
        print(td("import json; assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']; run('project.load(args[0])',%r,delayFrames=10); result=json.dumps({'scheduled':%r})"%(target.as_posix(),target.as_posix())))
    elif action=='compare':
        before=json.loads((OUT/'before-save.json').read_text())
        after=json.loads((OUT/'after-reopen.json').read_text())
        checks={k:before[k]==after[k] for k in ('controls','workspace_hash','material_id','library_parameter_store',
          'layout_history_hash','fixture_history_hash','fixture_history_depth')}
        def settings_only(store):
            return {**store,'materials':{key:{k:v for k,v in value.items() if k not in ('phase','last_time')}
                    for key,value in store['materials'].items()}}
        checks['p1_settings']=settings_only(before['p1_store'])==settings_only(after['p1_store'])
        checks.update({path:before['table_hashes'][path]==after['table_hashes'][path]
          for path in before['table_hashes'] if path!='/project1/material_state_table'})
        checks.update(no_errors=not after['errors'],no_pickle_errors=not after['runtime_pickle_failures'],
          sender_off=not after['sender']['enabled'],no_packets_sent=after['sender']['telemetry']['packet_count']==0)
        data={'checks':checks,'passed':all(checks.values()),'file':after['folder']+'/'+after['file']}
        (OUT/'roundtrip.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data,indent=2))
        assert data['passed']
    else: raise ValueError(action)
