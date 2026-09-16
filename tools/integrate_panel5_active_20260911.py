"""Prepare explicit Panel 5 capacity, UV and route changes without hardware."""
from dataclasses import replace
from pixelblaze_mapper.layout_scene_adapter import RouteBinding
from pixelblaze_mapper.routing_transaction import router_from_rows
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.effect_surface_uv import rear_wall_uv

COUNT=6524
MISSING_LOCAL={123,197,231,234,235,243,244,252,253,261,270}
MISSING_SOURCES={6172+i for i in MISSING_LOCAL}
PANEL='9d1130c2-e47f-4f98-acaa-1f31b2332e57'


def apply_native(op, folder):
    """Capacity -> validated route -> sparse layout apply, with outer rollback."""
    import json
    from pathlib import Path
    from pixelblaze_mapper import layout_scene_td as layout
    from pixelblaze_mapper.layout_scene_adapter import load_document_json, document_json
    from pixelblaze_mapper.build_layout_apply import TouchDesignerLayoutAdapter, prepare_current, apply_current
    from pixelblaze_mapper.routing_transaction import table_rows, write_rows, apply_router_transaction
    folder=Path(folder)
    expected=json.loads((folder/'active-before.json').read_text(encoding='utf-8'))
    owner=op('/project1/layout_scene_editor');editor=layout.editor(owner)
    router=op('/project1/multi_controller_output');apply_owner=op('/project1/layout_apply')
    adapter=TouchDesignerLayoutAdapter(apply_owner);adapter.assert_outputs_off()
    assert editor.preview is None and document_json(editor.current)==expected['document']
    original=editor.current
    snapshot=adapter.capture()
    for path in ('/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv',
                 router.path+'/controller_config',router.path+'/segment_config'):
        assert snapshot['texts'][path]==expected['active']['texts'][path], 'Active data changed during preparation'
    (folder/'transaction-snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
    mapping=op('/project1/pixelblaze_mapper/map_active');uv=op('/project1/pixelblaze_mapper/effect_panel_uv')
    old_controllers=table_rows(router.op('controller_config'));old_segments=table_rows(router.op('segment_config'))
    updated,plan=prepare(original,table_rows(mapping),table_rows(uv),old_controllers,old_segments)
    previous_apply={key:apply_owner.fetch(key,None) for key in ('last_snapshot','last_applied_hash')}
    def rebuild():router.op('ui_callbacks').module._rebuild_router()
    committed=False
    try:
        # Grow the sparse mask with the tables before cooking any dependent
        # packer/preview. New slots remain black until the reviewed apply.
        mask=op('/project1/layout_apply/active_source_mask')
        old_mask=table_rows(mask)
        assert len(old_mask)==6173
        write_rows(mapping,plan['maps']);write_rows(uv,plan['uv'])
        write_rows(mask,old_mask+[[str(i),'0'] for i in range(6172,COUNT)])
        adapter._cook()
        assert all(op(path).numSamples==COUNT for path in ('/project1/null4','/project1/effect_sample_uv','/project1/topto1','/project1/math1'))
        apply_router_transaction(router,plan['controllers'],plan['segments'],rebuild,source_pixels=COUNT)
        editor.commit(updated);committed=True;layout.refresh(owner)
        prepared=prepare_current(apply_owner,mode='3d',preserve_routing=True,uv_source='current')
        assert prepared.source_count==COUNT and len(prepared.inactive_source_indices)==1147
        assert set(plan['panel5_missing_sources'])<=set(prepared.inactive_source_indices)
        apply_current(apply_owner)
        adapter.assert_outputs_off()
        assert table_rows(router.op('controller_config'))==plan['controllers']
        assert table_rows(router.op('segment_config'))==plan['segments']
        current_uv=table_rows(uv)
        assert current_uv==plan['uv']
        op('/project1/show_control/show_led_renderer').cook(force=True)
        assert op('/project1/show_control/show_led_renderer').numSamples==COUNT
        preview=op('/project1/pixelblaze_mapper/preview3d/instance_data');preview.cook(force=True)
        assert preview.numSamples==COUNT
        assert all(float(preview['a'][i])==0 for i in prepared.inactive_source_indices)
        assert not op('/project1').errors(recurse=True)
    except Exception:
        mask=op('/project1/layout_apply/active_source_mask')
        if snapshot['texts']['/project1/layout_apply/active_source_mask'] is None and mask is not None:mask.destroy()
        elif mask is not None:mask.text=snapshot['texts'][mask.path]
        mapping.text=snapshot['texts'][mapping.path];uv.text=snapshot['texts'][uv.path];adapter._cook()
        apply_router_transaction(router,old_controllers,old_segments,rebuild,source_pixels=6172)
        adapter.restore(snapshot)
        if committed:editor.undo();layout.refresh(owner)
        apply_owner.store('prepared_plan',None)
        for key,value in previous_apply.items():apply_owner.store(key,value)
        adapter.assert_outputs_off()
        raise
    report={key:value for key,value in plan.items() if key not in ('maps','uv','controllers','segments')}
    report.update(active_mapping_integrated=True,network_output_started=False,
                  old_template_removed_from_active=True,preview_count=preview.numSamples,
                  errors=list(op('/project1').errors(recurse=True)))
    constraints=dict(owner.fetch('panel_dimension_constraints',{}) or {})
    constraints[PANEL]=dict(constraints[PANEL],active_output_integrated=True)
    owner.store('panel_dimension_constraints',constraints)
    router.store('panel5_active_integration',report)
    # This operation also grows capacity and changes routing. A map-only Revert
    # cannot undo that combined transaction; use the complete saved checkpoint.
    apply_owner.store('last_snapshot',None)
    apply_owner.store('last_applied_hash',None)
    layout.status(owner,'PANEL 5 FERTIG | 341/352 gueltig | .249 Ausgang 5 U139-141 | LED-Ausgabe AUS')
    (folder/'active-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (folder/'active-integrated-document.json').write_text(document_json(editor.current),encoding='utf-8')
    return report


def prepare(document, old_maps, old_uv, controllers, segments):
    obj = document.scene.object(PANEL)
    assert len(obj.leds) == 341
    assert len(old_maps) == len(old_uv) == 6173
    assert {b.source_index for b in obj.leds} == set(range(6172, COUNT)) - MISSING_SOURCES
    assert all(b.source_index == 6172 + b.scan_index for b in obj.leds)
    points = {b.source_index: p for b, p in document.scene.world_points()}
    assert not set(range(2464, 2720)) & points.keys()
    assert all(abs(float(old_maps[i+1][a+1])-p[a]) < 1e-7
               for i, p in points.items() if i < 6172 for a in range(3))
    maps = [list(r) for r in old_maps] + [[str(i),'0','0','0'] for i in range(6172, COUNT)]
    uvs = [list(r) for r in old_uv]
    for index in range(6172, COUNT):
        uv = rear_wall_uv(points[index][0], points[index][2]) if index in points else (0.,0.)
        uvs.append([str(index),'3','rear',*[repr(v) for v in (*uv,*uv)]])
    new_controllers = [list(r) for r in controllers]
    header = controllers[0]
    named = [r for r in new_controllers[1:] if r[header.index('name')] == 'BACK_PANEL_249']
    assert len(named) == 1
    controller = named[0]
    assert controller[header.index('target_ip')] == '10.0.0.249'
    assert controller[header.index('start_universe')] == '120'
    assert controller[header.index('reserved_universes')] == '18'
    controller[header.index('reserved_universes')] = '22'
    assert not any(r[0] == 'BACK_THIRD_LEFT_PANEL5' for r in segments[1:])
    new_segments = [list(r) for r in segments] + [
        ['BACK_THIRD_LEFT_PANEL5','6172','352','BACK_PANEL_249','3230','0','RGB']]
    plan = build_router_plan(router_from_rows(new_controllers,new_segments,COUNT))
    assert plan.controller('BACK_PANEL_249').universe_count == 22
    assert not any(r.object_id == PANEL for r in document.routes)
    updated = replace(document,scene=replace(document.scene,expected_count=COUNT),
                      routes=document.routes+(RouteBinding(PANEL,'BACK_PANEL_249',5),))
    pixels = [(1.,.5,.25) if i in points else (0.,0.,0.) for i in range(COUNT)]
    packed_all = plan.pack_pixels(pixels)
    packed = packed_all['BACK_PANEL_249']
    flat = [channel for frame in packed for channel in frame]
    assert all(bool(any(flat[3*(3230+i):3*(3230+i)+3])) == (i not in MISSING_LOCAL) for i in range(352))
    for start, end in ((203,340),(1078,1190),(2070,2210),(3020,3230),(3582,3740)):
        assert not any(flat[3*start:3*end])
    old_plan = build_router_plan(router_from_rows(controllers,segments,6172))
    old_frames = old_plan.pack_pixels(pixels[:6172])
    assert packed[:18] == old_frames['BACK_PANEL_249']
    assert packed_all['WS2812_NODE'] == old_frames['WS2812_NODE']
    inactive = sorted(set(range(COUNT))-points.keys())
    assert len(inactive) == 1147 and len(points) == 5377
    assert set(range(2464,2720)) <= set(inactive)
    return updated,{'maps':maps,'uv':uvs,'controllers':new_controllers,'segments':new_segments,
        'source_count':COUNT,'valid_count':len(points),'inactive_count':len(inactive),
        'panel5_missing_sources':sorted(MISSING_SOURCES),'panel5_source_start':6172,'panel5_count':352,
        'retired_template_sources':[2464,2719],'controller':'BACK_PANEL_249','physical_port':5,
        'destination_start':3230,'universes':list(range(139,142)),
        'controller_frame_universes':list(range(120,142)),
        'offline_pack_checks_passed':True,'panel1_to_panel4_and_side_frames_unchanged':True}

