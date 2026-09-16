
import json,importlib,hashlib
from pixelblaze_mapper import guided_scan_live as live
live.assert_outputs_off(op)
assert all(h is None or h.process.poll() is not None for h in (live._capture,live._probe))
p=op(live.OWNER)
paths=['/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv','/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config','/project1/layout_scene_editor/draft_document','/project1/layout_scene_editor/fixture_document']
before={v:hashlib.sha256(op(v).text.encode()).hexdigest() for v in paths}
selection={name:p.op('ui_panel/'+name+'/string').text for name in ['source_ids','anchors','views','workspace']}
from pixelblaze_mapper import scan_coverage_visual_ui as visual,scan_workflow_ux as ux
importlib.reload(visual);importlib.reload(ux)
visual.install(globals())
ux.refresh(p)
assert visual.act(op,'open')
image_node=p.op('coverage_visual_image');image_node.cook(force=True)
result=json.dumps({'data':p.fetch('coverage_visual_data'),'index':p.fetch('coverage_visual_index'),'summary':str(p.op('coverage_visual_panel/summary').par.text.eval()),'detail':str(p.op('coverage_visual_panel/detail').par.text.eval()),'footer':str(p.op('coverage_visual_panel/footer').par.text.eval()),'errors':list(p.errors(recurse=True)),'layout_routing_unchanged':before=={v:hashlib.sha256(op(v).text.encode()).hexdigest() for v in paths},'selection_unchanged':selection=={name:p.op('ui_panel/'+name+'/string').text for name in selection},'image_resolution':[image_node.width,image_node.height],'capture_running':live._capture is not None and live._capture.process.poll() is None,'camera_running':live._probe is not None and live._probe.process.poll() is None})
