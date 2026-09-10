"""Prepare explicit Panel 2 capacity, UV and route changes without hardware."""
from dataclasses import replace
from pixelblaze_mapper.layout_scene_adapter import RouteBinding
from pixelblaze_mapper.routing_transaction import router_from_rows
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.effect_surface_uv import rear_wall_uv

COUNT=4482
PANEL='eeb92daf-cb0b-4ddf-952b-d3c49897b0f9'


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
        write_rows(mapping,plan['maps']);write_rows(uv,plan['uv']);adapter._cook()
        assert all(op(path).numSamples==COUNT for path in ('/project1/null4','/project1/effect_sample_uv','/project1/topto1','/project1/math1'))
        apply_router_transaction(router,plan['controllers'],plan['segments'],rebuild,source_pixels=COUNT)
        editor.commit(updated);committed=True;layout.refresh(owner)
        prepared=prepare_current(apply_owner,mode='3d',preserve_routing=True,uv_source='current')
        assert prepared.source_count==COUNT and len(prepared.inactive_source_indices)==367
        assert set(plan['panel2_missing_sources'])<=set(prepared.inactive_source_indices)
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
        apply_router_transaction(router,old_controllers,old_segments,rebuild,source_pixels=3744)
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
    router.store('panel2_active_integration',report)
    layout.status(owner,'PANEL 2 FERTIG | 680 gueltig / 58 schwarz | .249 Ausgang 2 U122-126 | LED-Ausgabe AUS')
    (folder/'active-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (folder/'active-integrated-document.json').write_text(document_json(editor.current),encoding='utf-8')
    return report


def prepare(document, old_maps, old_uv, controllers, segments):
    obj=document.scene.object(PANEL)
    assert len(obj.leds)==680
    assert len(old_maps)==len(old_uv)==3745
    assert all(b.source_index==3744+b.scan_index for b in obj.leds)
    points={b.source_index:p for b,p in document.scene.world_points()}
    assert not set(range(1184,1440))&points.keys()
    assert all(abs(float(old_maps[i+1][a+1])-p[a])<1e-7
               for i,p in points.items() if i<3744 for a in range(3))
    maps=[list(r) for r in old_maps]+[[str(i),'0','0','0'] for i in range(3744,COUNT)]
    uvs=[list(r) for r in old_uv]
    for index in range(3744,COUNT):
        uv=rear_wall_uv(points[index][0],points[index][2]) if index in points else (0.,0.)
        uvs.append([str(index),'3','rear',*[repr(v) for v in (*uv,*uv)]])
    new_controllers=[list(r) for r in controllers]
    header=controllers[0];named=[r for r in new_controllers[1:] if r[header.index('name')]=='BACK_PANEL_249']
    assert len(named)==1
    controller=named[0]
    assert controller[header.index('target_ip')]=='10.0.0.249'
    assert controller[header.index('start_universe')]=='120'
    assert controller[header.index('reserved_universes')]=='2'
    controller[header.index('reserved_universes')]='7'
    assert not any(r[0]=='BACK_TOP_RIGHT_PANEL2' for r in segments[1:])
    new_segments=[list(r) for r in segments]+[['BACK_TOP_RIGHT_PANEL2','3744','738','BACK_PANEL_249','340','0','RGB']]
    plan=build_router_plan(router_from_rows(new_controllers,new_segments,COUNT))
    assert plan.controller('BACK_PANEL_249').universe_count==7
    assert not any(r.object_id==PANEL for r in document.routes)
    updated=replace(document,scene=replace(document.scene,expected_count=COUNT),
                    routes=document.routes+(RouteBinding(PANEL,'BACK_PANEL_249',2),))
    # Offline packet construction: no sockets. Every missing source is black.
    pixels=[(1.,.5,.25) if i in points else (0.,0.,0.) for i in range(COUNT)]
    packed=plan.pack_pixels(pixels)['BACK_PANEL_249']
    flat=[channel for frame in packed for channel in frame]
    expected=sorted(set(range(3744,COUNT))-points.keys())
    assert len(expected)==58
    for source in range(3744,COUNT):
        address=3*(340+source-3744)
        assert bool(any(flat[address:address+3]))==(source in points)
    assert not any(flat[203*3:340*3]) and not any(flat[(340+738)*3:])
    old_plan=build_router_plan(router_from_rows(controllers,segments,3744))
    old_frame=old_plan.pack_pixels(pixels[:3744])
    assert packed[:2]==old_frame['BACK_PANEL_249']
    assert plan.pack_pixels(pixels)['WS2812_NODE']==old_frame['WS2812_NODE']
    return updated,{'maps':maps,'uv':uvs,'controllers':new_controllers,'segments':new_segments,
        'source_count':COUNT,'valid_count':len(points),'inactive_count':COUNT-len(points),
        'panel2_missing_sources':expected,'panel2_source_start':3744,'panel2_count':738,
        'controller':'BACK_PANEL_249','physical_port':2,'destination_start':340,
        'universes':[122,123,124,125,126],'controller_frame_universes':[120,121,122,123,124,125,126],
        'offline_pack_checks_passed':True,'panel1_and_side_frames_unchanged':True}
