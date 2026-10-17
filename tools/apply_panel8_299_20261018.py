"""Apply the reviewed Panel 8 replacement in TouchDesigner, preserving routes."""
import json
from pathlib import Path
from pixelblaze_mapper import layout_scene_td as layout, guided_scan_live as live
from pixelblaze_mapper.layout_scene_adapter import load_document_json, document_json
from pixelblaze_mapper.layout_workspace import import_workspace
from pixelblaze_mapper.build_layout_apply import TouchDesignerLayoutAdapter, prepare_layout, apply_plan
from pixelblaze_mapper.routing_transaction import table_rows, write_rows, stop_outputs, router_from_rows
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.layout_session_storage import prepare_save, prepare_apply_save


def run():
    root=Path(project.folder)
    folder=root/'docs/panel8-replacement-299-20261018'
    report=json.loads((folder/'fit-report.json').read_text(encoding='utf-8'))
    pid=report['object_id']
    owner=op('/project1/layout_scene_editor'); editor=layout.editor(owner)
    applied=op('/project1/layout_apply'); adapter=TouchDesignerLayoutAdapter(applied)
    router=op('/project1/multi_controller_output'); guided=op('/project1/guided_scan')
    assert editor.preview is None
    assert live._capture is None or live._capture.process.poll() is not None
    assert not (guided.fetch('offline_status',{}) or {}).get('running')
    before_draft=(folder/'before-draft.json').read_text(encoding='utf-8')
    before_workspace=(folder/'before-active-workspace.json').read_text(encoding='utf-8')
    assert document_json(editor.current)==before_draft
    assert applied.op('active_workspace').text==before_workspace
    before=json.loads((folder/'before-tables.json').read_text(encoding='utf-8'))
    assert all(op(p).text==text for p,text in before.items())
    document=load_document_json((folder/'prepared-active.json').read_text(encoding='utf-8'))
    draft=load_document_json((folder/'prepared-draft.json').read_text(encoding='utf-8'))
    _,fixtures=import_workspace(before_workspace)
    uvs=json.loads((folder/'prepared-uv.json').read_text(encoding='utf-8'))
    count=op('/project1/math1').numSamples
    assert count==10330
    controllers=table_rows(router.op('controller_config')); segments=table_rows(router.op('segment_config'))
    segment=next(r for r in segments if r[0]=='PORT_PANEL8_251_1')
    assert segment[1:5]==['2720','299','PANEL8_251','0']
    expected={b.source_index:p for b,p in document.scene.world_points()}
    previous_map=table_rows(op('/project1/pixelblaze_mapper/map_active'))
    previous_uv=table_rows(op('/project1/pixelblaze_mapper/effect_panel_uv'))
    previous_mask=table_rows(applied.op('active_source_mask'))
    for i,p in expected.items():
        if not 2720<=i<3019:
            assert all(abs(float(previous_map[i+1][a+1])-p[a])<1e-10 for a in range(3)),i
    stop_outputs(router); live.assert_outputs_off(op)
    prepare_save(owner);prepare_apply_save(applied)
    backup=root/'PixelblazeMapper_BEFORE_PANEL8_REPLACEMENT_20261018.toe'
    assert not backup.exists()
    project.save(str(backup))
    snapshot=adapter.capture()
    (folder/'transaction-snapshot.json').write_text(json.dumps(snapshot),encoding='utf-8')
    material=op('/project1/topto1'); previous_material=str(material.par.top.eval())
    previous_selection=editor.selected_object_id
    committed=False
    try:
        material.par.top='/project1/res1'
        write_rows(op('/project1/pixelblaze_mapper/effect_panel_uv'),uvs)
        adapter._cook()
        plan=prepare_layout(document,fixtures,mode='3d',source_count=count,
            base_active_hash=adapter.active_hash(),preserve_routing=True,
            uv_source='current',active_uv_rows=uvs)
        apply_plan(plan,document,fixtures,adapter)
        editor.commit(draft);committed=True
        editor.select(pid);layout.refresh(owner)
        assert table_rows(router.op('controller_config'))==controllers
        assert table_rows(router.op('segment_config'))==segments
        actual=table_rows(op('/project1/pixelblaze_mapper/map_active'))
        mask=table_rows(applied.op('active_source_mask'))
        actual_uv=table_rows(op('/project1/pixelblaze_mapper/effect_panel_uv'))
        assert actual_uv==uvs
        for i in range(count):
            if 2720<=i<3019:
                enabled=i-2720 not in report['missing']
                assert mask[i+1]==[str(i),str(int(enabled))]
                p=expected[i] if enabled else (0.,0.,0.)
                assert all(abs(float(actual[i+1][a+1])-p[a])<1e-10 for a in range(3))
            else:
                assert mask[i+1]==previous_mask[i+1]
                assert actual_uv[i+1]==previous_uv[i+1]
                assert all(abs(float(actual[i+1][a+1])-float(previous_map[i+1][a+1]))<1e-10 for a in range(3)),i
        # Verify routed gaps and final index without sending to hardware.
        router_plan=build_router_plan(router_from_rows(controllers,segments,count))
        probe=[(0.,0.,0.)]*count
        for i in range(2720,3019):
            if mask[i+1][1]=='1':probe[i]=(1.,1.,1.)
        frames=router_plan.pack_pixels(probe)['PANEL8_251']
        flat=[value for frame in frames for value in frame]
        lit={i for i in range(len(flat)//3) if any(flat[3*i:3*i+3])}
        assert lit==set(range(299))-{1,61,93}
        assert not op('/project1').errors(recurse=True),op('/project1').errors(recurse=True)
    except Exception:
        stop_outputs(router)
        adapter.restore(snapshot)
        if committed:
            editor.undo();editor.select(previous_selection);layout.refresh(owner)
        raise
    finally:
        material.par.top=previous_material
        adapter._cook()
        stop_outputs(router)
    report.update(applied=True,output_enabled=False,backup=str(backup),source_count=count,
        source_address_check=True,other_geometry_uv_and_routes_preserved=True,
        missing_slots_black=True,old_object_replaced=True)
    guided.store('panel8_integration_report',report)
    guided.store('pending_panel8_rescan',None)
    owner.store('panel8_integration_report',report)
    owner.store('next_panel_intent',dict(panel=8,object_id=pid,led_count=299,measured=296,
        missing=[1,61,93],state='integrated_partial',controller='10.0.0.251',physical_output=1))
    layout.status(owner,'PANEL 8 ERSETZT | 296/299 | Dreieck unten, kurze Kante links/innen | offen: 1, 61, 93')
    owner.op('ui_panel').openViewer()
    prepare_save(owner);prepare_apply_save(applied)
    saved=root/'PixelblazeMapper_PANEL8_299_REPLACED_20261018.toe'
    project.save(str(saved))
    report['project']=project.name
    report['saved_project']=str(root/project.name)
    (folder/'applied.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    op('/project1/layout_scene_editor/scene_render').save(str(folder/'touchdesigner-after.png'))
    return report


result=json.dumps(run())
