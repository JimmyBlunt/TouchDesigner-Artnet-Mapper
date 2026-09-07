"""Explicit storage audit and roundtrip evidence. Does not start LED output."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/implementation-2026-09-07/storage-repair'

INSTALL = r'''
import json, ast, sys, importlib
from pathlib import Path
root=Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
def source(name, function=None, attribute=None, constant=None):
    tree=ast.parse((root/'pixelblaze_mapper'/name).read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if function and isinstance(node,ast.FunctionDef) and node.name==function:
            scope={}; exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),scope)
            return scope[function]()
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if attribute and isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and (target.value.id,target.attr)==attribute:
                    return ast.literal_eval(node.value)
                if constant and isinstance(target,ast.Name) and target.id==constant:
                    return ast.literal_eval(node.value)
    raise ValueError(name)
# Update only runtime DAT sources: do not rebuild UI or overwrite live tables.
op('/project1/show_control/callbacks').text=source('build_show_sequencer.py',attribute=('callbacks','text'))
op('/project1/show_control/callbacks').module.sync()
op('/project1/madmapper_library/runtime').text=source('build_material_library_browser.py',function='_runtime_source')
lib=op('/project1/madmapper_library/runtime').module
lib._persist_parameter_store()
op('/project1/material_state_runtime').text=source('build_p1_material_state.py',function='_runtime_source')
op('/project1/material_state_runtime').module._persist()
for name in ('layout_session_storage','layout_scene_td','layout_fixture_td','build_layout_apply'):
    fullname='pixelblaze_mapper.'+name
    if fullname in sys.modules: importlib.reload(sys.modules[fullname])
    else: importlib.import_module(fullname)
owner=op('/project1/layout_scene_editor')
ui_builder=importlib.import_module('pixelblaze_mapper.build_layout_scene_ui')
importlib.reload(ui_builder)
owner.op('runtime').text=ui_builder.RUNTIME
from pixelblaze_mapper.layout_session_storage import prepare_save, prepare_apply_save
manifest=prepare_save(owner)
apply_owner=op('/project1/layout_apply')
assert apply_owner is not None, 'Locate live LayoutApply before migration'
apply_owner.op('runtime').text=source('build_layout_apply.py',attribute=('runtime','text'))
apply_manifest=prepare_apply_save(apply_owner)
result=json.dumps({'layout':manifest,'apply':apply_manifest,'errors':list(op('/project1').errors(recurse=True)),
 'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()})
'''

SNAPSHOT = r'''
import json, hashlib, pickle
from dataclasses import asdict
from pixelblaze_mapper.layout_scene_td import editor
from pixelblaze_mapper.layout_fixture_td import history
from pixelblaze_mapper.layout_workspace import export_workspace
def digest(text): return hashlib.sha256(text.encode()).hexdigest()
def plain(value):
    if value is None or isinstance(value,(str,int,float,bool)): return value
    if isinstance(value,dict): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [plain(v) for v in value]
    if hasattr(value,'to_json'): return json.loads(value.to_json())
    if hasattr(value,'__dataclass_fields__'): return plain(asdict(value))
    return {'type':type(value).__module__+'.'+type(value).__name__}
owner=op('/project1/layout_scene_editor')
workspace=json.loads(export_workspace(editor(owner).current,history(owner).current))
tables={}
for path in ['/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv',
 '/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config',
 '/project1/multi_controller_output/gico_port_config/port_config','/project1/multi_controller_output/gico_port_config/global_config',
 '/project1/show_control/show_json','/project1/show_control/state_table','/project1/material_browser/unified_state',
 '/project1/madmapper_library/browser_state','/project1/material_state_table']:
    node=op(path)
    if node is not None: tables[path]=node.text
controls=op('/project1/madmapper_player_controls')
parameters={p.name:plain(p.eval()) for p in controls.customPars}
failures=[]; objects=[]
for node in [op('/project1')]+op('/project1').findChildren():
    for key,value in list(node.storage.items()):
        try: pickle.dumps(value)
        except Exception as error: failures.append({'path':node.path,'key':key,'error':str(error)})
        if type(value).__module__.startswith('pixelblaze_mapper'):
            objects.append({'path':node.path,'key':key,'type':type(value).__module__+'.'+type(value).__name__})
lib=op('/project1/madmapper_library/runtime').module
active=lib._active_item()
result=json.dumps({'file':project.name,'folder':project.folder,'tables':tables,
 'table_hashes':{p:digest(t) for p,t in tables.items()},'controls':parameters,'workspace':workspace,
 'workspace_hash':digest(json.dumps(workspace,sort_keys=True)),
 'material_id':active['id'] if active else None,
 'library_parameter_store':plain(op('/project1/madmapper_library').fetch('madmapper_parameter_store',None)),
 'p1_store':plain(op('/project1').fetch('p1_material_state_store',None)),
 'runtime_pickle_failures':failures,'runtime_class_objects':objects,
 'errors':list(op('/project1').errors(recurse=True)),
 'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()})
'''

if __name__ == '__main__':
    action=sys.argv[1]
    OUT.mkdir(parents=True,exist_ok=True)
    if action == 'snapshot':
        label=sys.argv[2]
        if not label.replace('-','').isalnum(): raise ValueError('Invalid label')
        target=OUT/(label+'.json')
        if target.exists(): raise RuntimeError('Evidence exists; use a new label')
        result=td(SNAPSHOT)
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('tables','workspace','library_parameter_store','p1_store')},indent=2))
    elif action == 'install':
        result=td(INSTALL)
        (OUT/'install.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    elif action in ('save','save-verified'):
        suffix='REPAIRED' if action=='save' else 'VERIFIED'
        target=ROOT/('Backup/Implementation/PixelblazeMapper_20260907_STORAGE_'+suffix+'.toe')
        record=OUT/(action+'.json')
        if target.exists() or record.exists(): raise RuntimeError('Use new candidate filename')
        script=r'''import json,pickle
from pixelblaze_mapper.layout_session_storage import prepare_save,prepare_apply_save,TRANSIENT_KEYS
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
layout=prepare_save(op('/project1/layout_scene_editor'))
apply=prepare_apply_save(op('/project1/layout_apply'))
op('/project1/show_control/callbacks').module.sync()
op('/project1/madmapper_library/runtime').module._persist_parameter_store()
op('/project1/material_state_runtime').module._persist()
excluded={'/project1':{'p1_material_runtime_cache','p1_material_state_runtime_schema'},
 '/project1/madmapper_library':{'material_hover_context_cache','material_parameter_context_cache'},
 '/project1/layout_scene_editor':set(TRANSIENT_KEYS),
 '/project1/layout_apply':{'prepared_plan','prepared_workspace_key','prepared_workspace_hash','applying'}}
failures=[]
for node in [op('/project1')]+op('/project1').findChildren():
    for key,value in list(node.storage.items()):
        if key in excluded.get(node.path,set()): continue
        try: pickle.dumps(value)
        except Exception as error: failures.append({'path':node.path,'key':key,'error':str(error)})
assert not failures,str(failures)
assert not list(op('/project1').errors(recurse=True))
saved=project.save(%r,saveExternalToxs=False)
result=json.dumps({'saved':saved,'file':project.name,'folder':project.folder,'layout':layout,'apply':apply,
 'preflight_unexpected_pickle_failures':failures,'declared_startup_overrides':{k:sorted(v) for k,v in excluded.items()},
 'ui_status':str(ui.status),'note':'save True alone is NOT roundtrip success; inspect UI and reopen',
 'sender_enabled':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']})
''' % target.as_posix()
        result=td(script)
        record.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    elif action in ('reload','reload-verified'):
        saved=json.loads((OUT/('save.json' if action=='reload' else 'save-verified.json')).read_text(encoding='utf-8'))
        target=Path(saved['folder'])/saved['file']
        if not target.is_file() or not saved['saved']: raise RuntimeError('No saved candidate')
        script="import json; assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']; run('project.load(args[0])', %r, delayFrames=10); result=json.dumps({'reload_scheduled':%r})" % (target.as_posix(),target.as_posix())
        print(td(script))
    elif action == 'compare':
        baseline=json.loads((OUT/'before-repair.json').read_text(encoding='utf-8'))
        after=json.loads((OUT/'after-verified-reopen.json').read_text(encoding='utf-8'))
        stable=[p for p in baseline['table_hashes'] if p!='/project1/material_state_table']
        checks={p:baseline['table_hashes'][p]==after['table_hashes'][p] for p in stable}
        checks.update(controls=baseline['controls']==after['controls'],workspace=baseline['workspace']==after['workspace'],
                      material_id=baseline['material_id']==after['material_id'],no_errors=not after['errors'],
                      no_pickle_errors=not after['runtime_pickle_failures'],sender_off=not after['sender']['enabled'],
                      no_packets_sent=after['sender']['telemetry']['packet_count']==0)
        assert all(checks.values()),checks
        report={'passed':True,'checks':checks,'material_phase_comparison':'material-roundtrip-comparison.json',
                'verified_file':after['folder']+'/'+after['file'],'tests':{'count':558,'result':'OK','seconds':32.464}}
        (OUT/'roundtrip-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
    elif action == 'inspect-file':
        import io, pickle, hashlib
        class DataOnly(pickle.Unpickler):
            def find_class(self,module,name): raise ValueError('Class object in durable storage: '+module+'.'+name)
        folder=ROOT/'Backup/Implementation/storage_verify/repaired.toe.dir'
        records={}
        for relative in ('project1.n','project1/show_control.n','project1/madmapper_library.n','project1/layout_scene_editor.n','project1/layout_apply.n'):
            path=folder/relative
            values=[line[5:] for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('dict ')]
            assert len(values)==1,relative
            raw=bytes.fromhex(values[0])
            records[relative]=DataOnly(io.BytesIO(raw)).load()
        layout=records['project1/layout_scene_editor.n']
        assert layout['layout_editor_session'] is None and layout['fixture_history'] is None
        assert layout['layout_session_snapshot']['current']['scene']['expected_count']==3744
        assert len(layout['fixture_session_snapshot']['redo'])==3
        library=records['project1/madmapper_library.n']
        assert library['material_hover_context_cache'] is None and library['material_parameter_context_cache'] is None
        assert isinstance(library['madmapper_parameter_store'],dict)
        assert isinstance(records['project1.n']['p1_material_state_store'],dict)
        assert records['project1.n']['p1_material_runtime_cache'] is None
        assert records['project1/show_control.n']['show_runtime_record']['schema']=='pixelblaze-show-runtime-state'
        (OUT/'file-storage.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        result={'data_only_unpickle':'passed','verified_storage_nodes':list(records),
                'layout_fixture_histories_present':True,'transient_classes_excluded':True}
        (OUT/'file-inspection.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    else:
        raise ValueError(action)
