"""Controlled local TD build/evidence runner. Never starts an output.

Run checkpoint once before install. Explicit stage only; no automatic hardware
tests. Existing TOE/source files are never overwritten by checkpoint.
"""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td, SNAPSHOT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'implementation-2026-09-07'


def checkpoint():
    OUT.mkdir(parents=True, exist_ok=True)
    target = ROOT / 'Backup' / 'Implementation' / 'before_20260907_p0_p1.toe'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or (OUT / 'before.json').exists():
        raise RuntimeError('Checkpoint already exists; refusing overwrite')
    before = td(SNAPSHOT)
    if before['sender']['enabled']:
        raise RuntimeError('Output is running; refusing install checkpoint')
    (OUT / 'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
    print(td('import json\nresult=json.dumps({"saved":project.save(%r, saveExternalToxs=False)})' % target.as_posix()))


def install(stage):
    if not (OUT / 'before.json').exists():
        raise RuntimeError('Create checkpoint first')
    names = {
        'p0': ['build_multi_controller_output.py', 'build_gico_port_config_ui.py'],
        'materials': ['build_p1_material_state.py', 'build_material_library_browser.py', 'build_unified_material_browser.py'],
        'show': ['build_show_sequencer.py', 'integrate_live_show.py'],
        'layout': ['build_layout_scene_ui.py', 'build_layout_apply.py', 'build_scan_session_ui.py'],
        'shortcuts': ['build_shortcut_hub.py'],
    }[stage]
    script = '''import json, sys, importlib
from pathlib import Path
sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks')
assert not sender.module.status()['enabled'], 'Output must be OFF'
root=Path(%r)
sys.path.insert(0,str(root)) if str(root) not in sys.path else None
for module in ['routing_transaction','gico_port_config','port_topology','material_state','material_control_surface','imported_material_state','show_sequencer','show_renderer','layout_scene_td','layout_fixture_td','build_layout_apply']:
    qualified='pixelblaze_mapper.'+module
    if qualified in sys.modules: importlib.reload(sys.modules[qualified])
before_controls=op('/project1/madmapper_player_controls')
preserved_tone={k:before_controls.par[k].eval() for k in ('Intensity','Contrast')}
for name in %r:
    path=root/'pixelblaze_mapper'/name
    scope=dict(globals());scope['__name__']='__main__';scope['__file__']=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    if name == 'build_layout_scene_ui.py': scope['build']()
if %r == 'materials':
    for key,value in preserved_tone.items(): before_controls.par[key].val=value
    lib=op('/project1/madmapper_library/runtime').module
    active=lib._active_item()
    if active is not None: lib._activate_parameter_shader(active)
    op('/project1/material_state_runtime').module.controls_changed()
sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks')
assert not sender.module.status()['enabled'], 'Unexpected output activation'
result=json.dumps({'stage':%r,'errors':list(op('/project1').errors(recurse=True)), 'sender':sender.module.status()})
''' % (ROOT.as_posix(), names, stage, stage)
    result = td(script)
    (OUT / ('install-' + stage + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'checkpoint':
        checkpoint()
    elif action in ('p0', 'materials', 'show', 'layout', 'shortcuts'):
        install(action)
    elif action == 'probe-nav':
        print(td('''import json
b=op('/project1/material_browser'); n=b.op('unified_next_click')
n.store('impl_original_text',n.text)
n.store('impl_original_panelvalue',n.par.panelvalue.eval())
n.text="def onOffToOn(panelValue):\\n    parent().store('impl_nav_hits',parent().fetch('impl_nav_hits',0)+1)\\n    op('/project1/material_browser/unified_runtime').module.change_page(1)\\n"
n.par.panelvalue='lselect'
result=json.dumps({'value':n.par.panelvalue.eval(),'hits':b.fetch('impl_nav_hits',0)})
'''))
    elif action == 'read-nav':
        print(td("import json; b=op('/project1/material_browser'); result=json.dumps({'hits':b.fetch('impl_nav_hits',0),'state':b.op('unified_state').text,'errors':list(b.errors(recurse=True))})"))
    elif action == 'restore-material-test':
        result=td('''import json
lib=op('/project1/madmapper_library/runtime').module
browser=op('/project1/material_browser/unified_runtime').module
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
active=lib._active_item()
assert active and active['id']=='mat_67a99c60e4c0797447fb', 'Active material changed since test; do not overwrite user selection'
evidence={'page2_selection':op('/project1/material_browser/unified_state').text,'active_after_apply':active['id'],'label_after_apply':lib._state('active_label')}
browser._set_state('selected_key','madmapper:mat_ab0287bb394c824f13df')
assert browser.apply_selected(), 'Could not restore baseline material'
browser.toggle_native_parameters(False)
evidence['restored_active']=lib._active_item()['id']
evidence['errors']=list(op('/project1').errors(recurse=True))
result=json.dumps(evidence)
''')
        (OUT/'material-page2-click-test.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    elif action == 'save-candidate':
        target=ROOT/'Backup/Implementation/PixelblazeMapper_20260907_P0P1_2D_CANDIDATE.toe'
        if target.exists() or (OUT/'saved-candidate.json').exists():
            raise RuntimeError('Candidate checkpoint already recorded; use a new reviewed filename')
        result=td('''import json
from pathlib import Path
sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks')
assert not sender.module.status()['enabled'], 'Output must stay OFF'
errors=list(op('/project1').errors(recurse=True))
assert not errors, str(errors)
saved=project.save(%r,saveExternalToxs=False)
result=json.dumps({'saved':saved,'file':project.name,'folder':project.folder,'sender_enabled':sender.module.status()['enabled'],'errors':errors})
''' % target.as_posix())
        (OUT/'saved-candidate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    else:
        raise ValueError(action)
