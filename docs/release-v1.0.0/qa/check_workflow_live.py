"""Run inside TD after workflow installers; isolated fixture with finally restore."""
import json, copy, traceback
from pathlib import Path
from pixelblaze_mapper import router_dynamic_ui, show_editor
s=op('/project1/show_control'); r=op('/project1/multi_controller_output'); ports=r.op('gico_port_config/controller_ports')
mod=s.op('editor_callbacks').module
show_nodes=[s.op(n) for n in ('show_json','automation_json','imported_json','editor_state','state_table','cue_table')]
show_nodes += [n for n in s.findChildren(type=tableDAT) if n.name in ('material_request','coordinate_request','mixer_request')]
saved_text={n.path:n.text for n in show_nodes}
saved_storage=copy.deepcopy(dict(s.storage)); router_storage=copy.deepcopy(dict(r.storage)); port_storage=copy.deepcopy(dict(ports.storage))
router_fields={n.path:n.op('string').text for n in r.op('ui_panel').children if n.type=='field'}
port_fields={n.path:n.op('string').text for n in ports.op('ui_panel').children if n.type=='field'}
router_tables={n:r.op(n).text for n in ('controller_config','segment_config')}
fixture=Path(project.folder)/'shows'/'__v1_workflow_qa_fixture_20261018.json'
assert not fixture.exists()
evidence={'checks':{},'errors':[]}
try:
 fixture.parent.mkdir(exist_ok=True)
 fixture.write_text(json.dumps(dict(show_editor.empty_show(),name='V1 QA fixture')),encoding='utf-8')
 mod._apply('load_show')
 assert s.op('control_panel/ed_show_picker_menu').par.display.eval()
 choices=s.fetch('saved_show_choices',[])
 idx=next(i for i,e in enumerate(choices) if Path(e['path'])==fixture)
 s.store('saved_show_page',idx//8)
 mod.picker_action('choose_'+str(idx%8))
 assert json.loads(s.op('show_json').text)['name']=='V1 QA fixture'
 assert json.loads(s.op('imported_json').text)=={}
 assert s.op('callbacks').module.runtime().plan().brightness==0
 evidence['checks']['picker_load_empty_missing_sidecars']=True
 mod._apply('save_show')
 assert fixture.with_suffix('.automation.json').exists() and fixture.with_suffix('.materials.json').exists()
 evidence['checks']['save_exact_selected_filename_and_sidecars']=True
 mod._apply('new_show')
 assert json.loads(s.op('show_json').text)['cues']==[] and json.loads(s.op('imported_json').text)=={}
 evidence['checks']['new_empty_show']=True
 s.op('callbacks').module.command('play')
 assert s.op('callbacks').module.runtime().state.value=='stopped'
 evidence['checks']['empty_play_stays_stopped_black']=True
 for item in router_dynamic_ui._entries(r):
  assert router_dynamic_ui.select_name(r,item['name'])
  assert r.fetch('router_card_name')==item['name']
 evidence['checks']['router_choose_all_controllers']=len(router_dynamic_ui._entries(r))
 pmod=ports.op('runtime').module
 for item in pmod._router().controllers:
  assert pmod.choose_controller(item.name),ports.fetch('message','')
  pmod=ports.op('runtime').module
  assert pmod._saved().controller.name==item.name
 evidence['checks']['port_choose_all_controllers']=len(pmod._router().controllers)
except Exception:
 evidence['errors'].append(traceback.format_exc())
finally:
 for path,value in saved_text.items(): op(path).text=value
 for owner,data in ((s,saved_storage),(r,router_storage),(ports,port_storage)):
  for key in list(owner.storage):
   if key not in data: owner.unstore(key)
  for key,value in data.items(): owner.store(key,value)
 for path,value in router_fields.items(): op(path+'/string').text=value
 for path,value in port_fields.items(): op(path+'/string').text=value
 s.op('callbacks').module._runtime_record=None
 s.op('editor_callbacks').module.repaint()
 # Rebuild the draft view from its restored snapshot; no routing mutation.
 ports.op('runtime').module._repaint()
 for path,value in port_fields.items(): op(path+'/string').text=value
 for path in ('/project1/show_control/control_panel/ed_show_picker_menu','/project1/multi_controller_output/ui_panel/router_controller_menu',ports.path+'/ui_panel/controller_menu'):
  n=op(path)
  if n is not None: n.par.display=False
 for file in (fixture,fixture.with_suffix('.automation.json'),fixture.with_suffix('.materials.json')):
  if file.exists(): file.unlink()
 evidence['checks']['router_tables_unchanged']=all(r.op(n).text==v for n,v in router_tables.items())
 evidence['checks']['show_json_restored']=s.op('show_json').text==saved_text[s.path+'/show_json']
 evidence['checks']['output_off']=not r.op('artnet_510_sender_callbacks').module.status()['enabled']
 path=Path(project.folder)/'docs/release-v1.0.0/qa/workflow-live.json'
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence))
