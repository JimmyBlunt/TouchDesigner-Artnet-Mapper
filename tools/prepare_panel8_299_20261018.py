"""Run in TouchDesigner: prepare the changed Panel 8 without starting capture."""
import json
from pathlib import Path
from urllib.request import urlopen
from pixelblaze_mapper import guided_scan_live as live, scan_coverage, scan_workflow_ux, led_search_ui
from pixelblaze_mapper.routing_transaction import table_rows, router_from_rows, apply_router_transaction, stop_outputs
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.scan_routing import ScanRoutingSnapshot
from pixelblaze_mapper.scan_capture import validate_capture_manifest
from pixelblaze_mapper.layout_session_storage import prepare_save, prepare_apply_save
from pixelblaze_mapper.layout_workspace import import_workspace


def run():
    root = Path(project.folder)
    evidence = root / 'docs/panel8-rescan-299-20261018'
    workspace = root / 'Scans/Panel8_OUT1_299_20261018'
    evidence.mkdir(exist_ok=True)
    workspace.mkdir(exist_ok=True)
    router = op('/project1/multi_controller_output')
    owner = op('/project1/guided_scan')
    editor = op('/project1/layout_scene_editor')
    apply = op('/project1/layout_apply')
    assert live._capture is None or live._capture.process.poll() is not None
    assert live._probe is None or live._probe.process.poll() is not None
    assert not (owner.fetch('offline_status', {}) or {}).get('running')
    with urlopen('http://10.0.0.251/api/config', timeout=6) as response:
        hardware = json.load(response)
    port = next(p for p in hardware['outputs'] if p['id'] == 0)
    assert port['enabled'] and port['pixelCount'] == 299 and port['startUniverse'] == 156
    (evidence/'controller-readback.json').write_text(json.dumps(hardware, indent=2), encoding='utf-8')

    controllers = table_rows(router.op('controller_config'))
    before_segments = table_rows(router.op('segment_config'))
    segments = [list(r) for r in before_segments]
    row = next(r for r in segments if r[0] == 'PORT_PANEL8_251_1')
    assert row[1:] == ['2720', '256', 'PANEL8_251', '0', '0', 'BGR']
    row[2] = '299'
    count = op('/project1/math1').numSamples
    plan = build_router_plan(router_from_rows(controllers, segments, count))
    assert plan.controller('PANEL8_251').universe_count == 7
    active, _ = import_workspace(apply.op('active_workspace').text)
    assert not any(2976 <= b.source_index < 3019 for o in active.scene.objects for b in o.leds)
    assert all(str(apply.op('active_source_mask')[i+1, 1]) == '0' for i in range(2976, 3019))
    protected = {p: op(p).text for p in (
        '/project1/pixelblaze_mapper/map_active', '/project1/pixelblaze_mapper/effect_panel_uv',
        '/project1/layout_apply/active_source_mask', '/project1/layout_apply/active_workspace',
        '/project1/layout_scene_editor/draft_document')}
    (evidence/'protected-tables-before.json').write_text(json.dumps(protected), encoding='utf-8')
    (evidence/'port-editor-before.json').write_text(json.dumps(router.op('gico_port_config/controller_ports').storage, default=str, indent=2), encoding='utf-8')
    stop_outputs(router)
    live.assert_outputs_off(op)
    prepare_save(editor)
    prepare_apply_save(apply)
    # Keep the project folder unchanged: embedded builders resolve imports here.
    backup = root / 'PixelblazeMapper_BEFORE_PANEL8_299_20261018.toe'
    assert not backup.exists(), 'Do not overwrite the pre-change backup'
    project.save(str(backup))
    apply_router_transaction(router, controllers, segments,
        lambda: router.op('ui_callbacks').module._rebuild_router(), source_pixels=count)
    ports = router.op('gico_port_config/controller_ports')
    runtime = ports.op('runtime').module
    runtime._save(runtime._import_controller('PANEL8_251'))
    ports.store('baseline', runtime._signature())
    ports.store('page', 0)
    runtime._status('PANEL 8: 299 LEDs | OUT 1 | neue 3D-Positionen nach Scan uebernehmen')
    runtime._repaint()

    settings = dict(name='PANEL8_OUT1_299_20261018', target='10.0.0.251',
        interface='10.0.0.125', universe=156, count=299, rate=30, order='BGR',
        frame_start_universe=156, frame_universe_count=7)
    live.stage_standalone(op, settings)
    owner.op('ui_panel/workspace/string').text = str(workspace)
    for key, value in settings.items():
        field = owner.op('new_capture_panel/' + key + '/string')
        if field is not None:
            field.text = str(value)
    for key, value in dict(offline_status={}, result_review=None, manifest_view_paths=[],
            registration_context=None, registration_proposal=None, coverage_visual_data=None,
            workflow_page='capture', camera_status={}).items():
        owner.store(key, value)
    owner.op('ui_panel/offline_status').par.text = 'Noch kein 3D-Ergebnis fuer Panel 8 / 299 LEDs.'
    owner.op('ui_panel/camera_status').par.text = 'Kamera vor der ersten Ansicht pruefen.'
    owner.op('led_search_panel/controller/string').text = settings['target']
    owner.op('led_search_panel/controller').panel.field.val = settings['target']
    owner.op('led_search_panel/index/string').text = '0'
    owner.op('led_search_panel/index').panel.field.val = '0'
    owner.store('led_search_device', {'target': settings['target'], 'outputs': hardware['outputs']})
    owner.store('led_search_output', 0)
    led_search_ui.render(op)
    summary = live.prepare(op)
    scan_coverage._last_key = None
    scan_coverage.refresh(op)
    scan_workflow_ux.refresh(owner)
    # Field COMPs keep an editor buffer in addition to the string DAT.
    for panel_name in ('ui_panel', 'new_capture_panel'):
        for field in owner.op(panel_name).children:
            if field.isCOMP and field.op('string') and hasattr(field.panel, 'field'):
                field.panel.field.val = field.op('string').text.strip()
    capture_plan = owner.fetch('capture_plan')
    validate_capture_manifest(capture_plan)
    snapshot = ScanRoutingSnapshot.from_dict(capture_plan['routing'])
    assert list(snapshot.source_indices) == list(range(299))
    # Exhaustively validate every LED address without sending a network packet.
    for index in range(299):
        frames = snapshot.packet_descriptors(index, on=True)
        assert len(frames) == 7
        lit = [f for f in frames if any(f.payload)]
        assert len(lit) == 1
        assert lit[0].wire_universe == 156 + index // 170
        assert {i // 3 for i, value in enumerate(lit[0].payload) if value} == {index % 170}
        assert all(not any(f.payload) for f in frames if f.wire_universe >= 158)
    assert owner.fetch('coverage_summary')['total'] == 299
    assert owner.fetch('coverage_summary')['views'] == 0
    assert not owner.op('ui_panel/views/string').text.strip()
    assert led_search_ui.selected_settings(op)['count'] == 299
    assert ports.fetch('draft')['ports'][0]['pixel_count'] == 299
    assert table_rows(router.op('controller_config')) == controllers
    assert table_rows(router.op('segment_config')) == segments
    assert all(op(p).text == text for p, text in protected.items())
    live.assert_outputs_off(op)
    assert not op('/project1').errors(recurse=True), op('/project1').errors(recurse=True)

    intent = dict(panel=8, object_id='99fa5b92-0a88-41a3-abe9-2903e536a17a',
        led_count=299, controller='10.0.0.251', physical_output=1,
        start_universe=156, end_universe=157, source_start=2720, source_end=3018,
        scan_local_ids=[0, 298], old_geometry_led_count=256,
        geometry_status='old_reference_only_pending_rescan', workspace=str(workspace),
        state='scan_plan_ready_camera_check_pending', scan_started=False)
    editor.store('next_panel_intent', intent)
    owner.store('pending_panel8_rescan', intent)
    message = 'PANEL 8 | 299 LEDs (0-298) | OUT 1 / 10.0.0.251 | Kamera pruefen, dann neue Ansichten aufnehmen.'
    live._status(op, message)
    owner.op('ui_panel').openViewer()
    prepare_save(editor)
    prepare_apply_save(apply)
    saved = root / 'PixelblazeMapper_PANEL8_299_SCAN_READY_20261018.toe'
    project.save(str(saved))
    report = dict(intent=intent, settings=settings, routing_summary=summary,
        backup=str(backup), saved_project=str(saved), output_enabled=False,
        verified_led_addresses=299, other_panels_unchanged=True,
        coordinates_preserved=True, extra_43_live_sources_masked_black=True,
        camera_settings={k:owner.op('ui_panel/'+k+'/string').text.strip()
                         for k in ('camera','exposure','threshold','brightness','packet_gap')},
        hardware_changed=False, project_errors=op('/project1').errors(recurse=True))
    (evidence/'scan-plan.json').write_text(json.dumps(capture_plan, indent=2), encoding='utf-8')
    (evidence/'prepared.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (workspace/'rescan-intent.json').write_text(json.dumps(intent, indent=2), encoding='utf-8')
    return report


result = json.dumps(run())
