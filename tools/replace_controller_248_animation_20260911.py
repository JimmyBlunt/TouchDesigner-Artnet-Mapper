"""Retarget the rear controller and prepare an output-off, five-panel animation."""
import json
from pathlib import Path
from math import ceil


def apply_native(op, folder):
    from pixelblaze_mapper import guided_scan_live as live, scan_output_guard, router_dynamic_ui
    from pixelblaze_mapper.routing_transaction import table_rows,apply_router_transaction,router_from_rows
    from pixelblaze_mapper.multi_controller import build_router_plan
    from pixelblaze_mapper.layout_scene_td import editor
    from pixelblaze_mapper.layout_scene_adapter import document_json
    from hashlib import sha256
    folder=Path(folder)
    assert not (folder/'prepared.json').exists()
    config=json.loads((folder/'controller-config-before.json').read_text(encoding='utf-8'))
    assert [(p['pixelCount'],p['startUniverse']) for p in config['outputs'][:5]]==[(203,120),(738,122),(880,127),(810,133),(352,139)]
    assert not json.loads((folder/'controller-test-pattern-before.json').read_text())['active']
    end=max(p['startUniverse']+ceil(p['pixelCount']/170) for p in config['outputs'] if p['enabled'])
    assert end==149
    live.assert_outputs_off(op);assert not scan_output_guard.active()
    assert live._capture is None or live._capture.process.poll() is not None
    assert live._probe is None or live._probe.process.poll() is not None
    router=op('/project1/multi_controller_output');scan=op('/project1/guided_scan')
    controls=op('/project1/madmapper_player_controls')
    tables=table_rows(router.op('controller_config'));segments=table_rows(router.op('segment_config'))
    count=op('/project1/math1').numSamples;assert count==6524
    stable_paths=('/project1/pixelblaze_mapper/map_active','/project1/pixelblaze_mapper/effect_panel_uv',
                  '/project1/layout_apply/active_source_mask','/project1/layout_scene_editor/draft_document')
    stable={p:sha256(op(p).text.encode()).hexdigest() for p in stable_paths}
    before={'controllers':tables,'segments':segments,'controls':{p.name:p.eval() for p in controls.customPars},
        'scan_storage':{k:scan.fetch(k,None) for k in ('session','standalone_capture','capture_plan','capture_signature','manifest','offline_status')},
        'stable_hashes':stable}
    (folder/'transaction-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    rows=[list(row) for row in tables];header=rows[0]
    for row in rows[1:]:
        if row[header.index('name')]=='BACK_PANEL_249':
            assert row[header.index('target_ip')]=='10.0.0.249'
            for key,value in {'target_ip':'10.0.0.248','reserved_universes':'29','brightness':'0.2','rate':'15','enabled':'1'}.items():
                row[header.index(key)]=value
        else:row[header.index('enabled')]='0'
    plan=build_router_plan(router_from_rows(rows,segments,count))
    document=editor(op('/project1/layout_scene_editor')).current
    valid={b.source_index for b,p in document.scene.world_points()}
    pixels=[(1.,.5,.25) if i in valid else (0.,0.,0.) for i in range(count)]
    frames=plan.pack_pixels(pixels)['BACK_PANEL_249'];assert len(frames)==29
    assert not any(v for frame in frames[22:] for v in frame), 'Unmapped port 6 must remain black'
    assert not any(frames[18]), 'Unused U138 must remain black'
    apply_router_transaction(router,rows,segments,lambda:router.op('ui_callbacks').module._rebuild_router(),source_pixels=count)
    # Keep the stable controller key referenced by five layout objects. Only
    # the network address changes; historical capture manifests stay immutable.
    router.store('router_card_drafts',{});router.store('router_card_baselines',{})
    router.store('router_card_name','BACK_PANEL_249');router_dynamic_ui.select(router,reload=True)
    field=router.op('gico_port_config/controller_ports/ui_panel/target/string')
    if field is not None:field.text='10.0.0.248'
    settings=dict(scan.fetch('standalone_capture'))
    settings.update(target='10.0.0.248',frame_universe_count=29)
    scan.store('standalone_capture',settings)
    scan.store('capture_plan',None);scan.store('capture_signature',None)
    for key,value in {'target':'10.0.0.248','frame_universe_count':'29'}.items():
        scan.op('new_capture_panel/'+key+'/string').text=value
    scan.op('worker_plan').text=''
    scan.op('ui_panel/routing_summary').par.text='Controller replaced: 10.0.0.248 | old scan completed | create a new acquisition before capture'
    scan.store('message','Controller 248 bereit. Abgeschlossene Scans bleiben archiviert; neue Aufnahme fuer weitere Scans anlegen.')
    intent=op('/project1/layout_scene_editor').fetch('next_panel_intent',None)
    if isinstance(intent,dict):
        op('/project1/layout_scene_editor').store('next_panel_intent',dict(intent,controller='10.0.0.248',controller_frame_count=29,state='panel_completed_new_capture_required'))
    runtime=op('/project1/material_state_runtime').module
    runtime.activate('core:ocean_waves')
    for key,value in {'Speed':.35,'Scale':2.,'Intensity':1.,'Coordinatemode':'global','Colormode':'gradient',
        'Gradientpreset':'neon_cyan_magenta','Gradientstrength':1.,'Globalmasterspeed':1.}.items():
        setattr(controls.par,key,value)
    runtime.controls_changed()
    op('/project1/math1').cook(force=True)
    assert {p:sha256(op(p).text.encode()).hexdigest() for p in stable_paths}==stable
    live.assert_outputs_off(op)
    assert not op('/project1').errors(recurse=True)
    report={'target':'10.0.0.248','stable_controller_key':'BACK_PANEL_249','panels':[1,2,3,4,5],
        'sent_universes':[120,148],'black_universes':[138,142,143,144,145,146,147,148],
        'brightness_percent':20,'requested_fps':15,'material':'ocean_waves','speed':.35,
        'other_controllers_disabled_for_animation':True,'geometry_and_masks_unchanged':True,
        'old_capture_plan_invalidated':True,'output_started':False,'errors':[]}
    (folder/'prepared.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
