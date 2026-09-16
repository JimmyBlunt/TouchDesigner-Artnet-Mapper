
import importlib,json,hashlib,sys
from pathlib import Path
from pixelblaze_mapper import guided_scan_live as live
live.assert_outputs_off(op)
assert all(h is None or h.process.poll() is not None for h in (live._capture,live._probe))
p=op(live.OWNER)
assert not p.fetch('offline_status',{}).get('running')
root=Path('C:\\Users\\jbhtz\\OneDrive\\Desktop\\Pictures\\Documents\\ChatGPT\\LED-Touchdesigner-Controller\\PixelblazeMapper')
for name in ('standalone_scan','guided_scan_live','scan_library','scan_library_ui'):
    importlib.reload(importlib.import_module('pixelblaze_mapper.'+name))
from pixelblaze_mapper import guided_scan_live as live
path=root/'pixelblaze_mapper/build_scan_session_ui.py'
scope=dict(globals(),__name__='panel2_scan_install',__file__=str(path))
exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
scope['build']()
settings={'name':'BACK_PANEL2_738_249','target':'10.0.0.249','interface':'10.0.0.125','universe':122,'count':738,'rate':30,'order':'RGB','frame_start_universe':120,'frame_universe_count':7}
for name,value in settings.items():
    p.op('new_capture_panel/'+name+'/string').text=str(value)
p.op('ui_panel/workspace/string').text='C:\\Users\\jbhtz\\OneDrive\\Desktop\\Pictures\\Documents\\ChatGPT\\LED-Touchdesigner-Controller\\PixelblazeMapper\\Scans\\back_panel2_738_249_20260910_fullscan'
p.op('runtime').module.act('stage_capture')
for key in ('result_review','registration_context','registration_proposal','coverage_summary'):
    p.store(key,{})
p.store('manifest_view_paths',[])
p.op('runtime').module.act('prepare')
plan=p.fetch('capture_plan')
assert plan and len(plan['identity'])==738
assert plan['routing']['routing']['controllers'][0]['reserved_universes']==7
assert plan['routing']['routing']['controllers'][0]['start_universe']==120
assert plan['routing']['targets'][0]['wire_universe']==122
assert plan['routing']['targets'][-1]['wire_universe']==126
assert plan['routing']['targets'][-1]['slot']==171
assert p.fetch('standalone_capture')==settings
assert p.op('ui_panel/views/string').text.strip()==''
live.assert_outputs_off(op)
paths=['/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv','/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config','/project1/layout_scene_editor/draft_document','/project1/layout_scene_editor/fixture_document']
result=json.dumps({'plan':plan,'session':p.fetch('session'),'settings':settings,'summary':str(p.op('ui_panel/routing_summary').par.text.eval()),'fields':{name:p.op('ui_panel/'+name+'/string').text for name in ['camera','exposure','threshold','brightness','source_ids','workspace','views']},'hashes':{path:hashlib.sha256(op(path).text.encode()).hexdigest() for path in paths},'errors':list(p.errors(recurse=True)),'camera_started':live._probe is not None,'scan_started':live._capture is not None,'native_outputs_off':all(not bool(n.par.active.eval()) for n in live.native_outputs(op))})
