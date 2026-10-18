"""Live pre-save/reopen assertions. Execute within TouchDesigner; no output starts."""
import hashlib
import json
import shutil
from pathlib import Path

TABLES = (
 '/project1/multi_controller_output/controller_config',
 '/project1/multi_controller_output/segment_config',
 '/project1/pixelblaze_mapper/map_active',
 '/project1/pixelblaze_mapper/effect_panel_uv',
 '/project1/layout_apply/active_source_mask',
 '/project1/layout_apply/active_workspace',
 '/project1/show_control/show_json',
)


def capture(*, allow_running=False):
 from pixelblaze_mapper.guided_scan_live import assert_outputs_off
 if not allow_running:
  assert_outputs_off(op)
 sender=op('/project1/multi_controller_output/artnet_510_sender_callbacks').module
 output_off=not sender._enabled and not any(bool(n.par.active) for n in op('/project1/multi_controller_output').children if n.type=='dmxout')
 root=Path(project.folder)
 catalog=json.loads((root/'docs/release-v1.0.0/help_catalog.json').read_text(encoding='utf8'))
 fields={}
 for screen in catalog['screens']:
  panel=op(screen.get('target','')) if screen.get('target') else None
  if panel is None:continue
  for name in screen.get('fields',{}):
   field=panel.op(name)
   if field is None:continue
   text=field.op('string')
   if text is not None:fields[field.path]=text.text
 return dict(project=project.name,folder=project.folder,source_count=op('/project1/math1').numSamples,
  hashes={p:hashlib.sha256(op(p).text.encode()).hexdigest() for p in TABLES},
  fields=fields,errors=op('/project1').errors(recurse=True),warnings=op('/project1').warnings(recurse=True),
  theme=op('/project1').fetch('release_v1_theme',None,search=False),
  ui_error=op('/project1/release_ui_maintenance').fetch('release_help_error',None,search=False),
  output_off=output_off)


def save_release():
 from pixelblaze_mapper.routing_transaction import stop_outputs
 from pixelblaze_mapper.layout_session_storage import prepare_save,prepare_apply_save
 stop_outputs(op('/project1/multi_controller_output'))
 prepare_save(op('/project1/layout_scene_editor'));prepare_apply_save(op('/project1/layout_apply'))
 op('/project1').store('release_version','1.0.0')
 data=capture()
 assert not data['errors'] and not data['warnings'] and not data['ui_error'], {key:data[key] for key in ('errors','warnings','ui_error')}
 assert data['source_count']==10330 and data['theme']=='03'
 root=Path(project.folder)
 target=root/'PixelblazeMapper_v1.0.0.toe'
 assert not target.exists(), 'Existing release must not be overwritten silently'
 (root/'docs/release-v1.0.0/qa/before-reopen.json').write_text(json.dumps(data,indent=2),encoding='utf8')
 assert project.save(str(target)), 'Project save did not succeed'
 # TouchDesigner treats a trailing numeric filename component as its save
 # counter, so v1.0.0 may be written as v1.0.1. Publish an exact-byte alias.
 if not target.exists():
  actual=root/project.name
  assert actual.is_file() and actual.parent==root, 'Saved project not found'
  shutil.copy2(actual,target)
 return dict(file=str(target),size=target.stat().st_size,fields=len(data['fields']),errors=data['errors'])


def verify_reopen(*, allow_running=False):
 root=Path(project.folder)
 before=json.loads((root/'docs/release-v1.0.0/qa/before-reopen.json').read_text(encoding='utf8'))
 after=capture(allow_running=allow_running)
 changes={k:{'before':before[k],'after':after[k]} for k in ('source_count','hashes','fields','theme','errors','warnings','ui_error') if before[k]!=after[k]}
 result=dict(passed=not changes,changes=changes,project=project.name,output_off=after['output_off'],saved_output_off=before['output_off'])
 (root/'docs/release-v1.0.0/qa/reopen-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 return result
