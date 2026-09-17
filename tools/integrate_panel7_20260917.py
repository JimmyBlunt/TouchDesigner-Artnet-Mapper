"""Activate measured Panel 7 on the second output of 10.0.0.251.

Runs inside TouchDesigner.  The editor draft already carries Panel 7
(tools/prepare_panel7_20260917.py); this step moves the same object into the
ACTIVE workspace, grows the source tables from 7646 to 8195, retires the 256
template LEDs that occupied the slot and repoints segment PORT_PANEL8_251_2
from the placeholder sources to the measured ones.  Every table write is
rolled back on any failure.
"""
import json
from dataclasses import replace
from pathlib import Path

from pixelblaze_mapper import layout_scene_td as layout
from pixelblaze_mapper.build_layout_apply import TouchDesignerLayoutAdapter, prepare_layout, apply_plan
from pixelblaze_mapper.effect_surface_uv import rear_wall_uv
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
from pixelblaze_mapper.layout_remove_leds import prepare as remove_leds
from pixelblaze_mapper.layout_scene_adapter import document_json
from pixelblaze_mapper.layout_workspace import import_workspace
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.routing_transaction import (table_rows, write_rows,
    apply_router_transaction, router_from_rows, stop_outputs)

OLD_COUNT = 7646
COUNT = 8195
OFFSET = 7646
LEDS = 549
RETIRED = set(range(2976, 3232))
TEMPLATE_ID = '33ef5c9a-877d-5d46-a359-13632f057db5'
SEGMENT = 'PORT_PANEL8_251_2'


def run(op, project, folder):
    folder = Path(folder)
    report = json.loads((folder / 'draft-plan.json').read_text(encoding='utf-8'))
    panel_id = report['panel_id']

    editor_owner = op('/project1/layout_scene_editor')
    editor = layout.editor(editor_owner)
    apply_owner = op('/project1/layout_apply')
    adapter = TouchDesignerLayoutAdapter(apply_owner)
    router = op('/project1/multi_controller_output')
    sender = router.op('artnet_510_sender_callbacks')
    was_running = bool(sender.module.status().get('enabled'))

    # The draft was committed in a separate, reviewed step; require it intact.
    assert editor.preview is None, 'Finish the current layout drag first'
    assert document_json(editor.current) == (folder / 'before-editor.json').read_text(encoding='utf-8')
    before_workspace = (folder / 'before-active-workspace.json').read_bytes().decode('utf-8')
    assert apply_owner.op('active_workspace').text == before_workspace

    mapping = op('/project1/pixelblaze_mapper/map_active')
    uv = op('/project1/pixelblaze_mapper/effect_panel_uv')
    mask = apply_owner.op('active_source_mask')
    for filename, node in (('before-map.tsv', mapping), ('before-uv.tsv', uv),
                           ('before-mask.tsv', mask),
                           ('before-controllers.tsv', router.op('controller_config')),
                           ('before-segments.tsv', router.op('segment_config'))):
        assert node.text == (folder / filename).read_bytes().decode('utf-8'), filename

    old_maps, old_uv, old_mask = map(table_rows, (mapping, uv, mask))
    old_controllers = table_rows(router.op('controller_config'))
    old_segments = table_rows(router.op('segment_config'))
    assert len(old_maps) == len(old_uv) == len(old_mask) == OLD_COUNT + 1

    panel = editor.current.scene.object(panel_id)
    scan = next(s for s in editor.current.scene.scans if s.scan_id == panel.leds[0].scan_id)
    routes = tuple(r for r in editor.current.routes if r.object_id == panel_id)
    assert len(panel.leds) == LEDS and len(routes) == 1

    active_before, fixtures = import_workspace(before_workspace)
    template = active_before.scene.object(TEMPLATE_ID)
    active, removed = remove_leds(active_before, template.object_id,
        [b.local_index for b in template.leds if b.source_index in RETIRED])
    assert {b.source_index for b in removed} == RETIRED
    active = replace(active, scene=replace(active.scene, expected_count=COUNT,
        scans=active.scene.scans + (scan,), objects=active.scene.objects + (panel,)),
        routes=active.routes + routes)
    points = {b.source_index: p for b, p in active.scene.world_points()}
    inactive = set(range(COUNT)) - points.keys()
    assert RETIRED <= inactive
    assert {OFFSET + i for i in range(LEDS)} <= points.keys()
    # Untouched sources keep their existing measured coordinates bit for bit.
    assert all(abs(float(old_maps[i + 1][a + 1]) - p[a]) < 1e-7
               for i, p in points.items() if i < OLD_COUNT for a in range(3))

    maps = [list(r) for r in old_maps] + [[str(i), '0', '0', '0'] for i in range(OLD_COUNT, COUNT)]
    uvs = [list(r) for r in old_uv]
    for i in range(OLD_COUNT, COUNT):
        value = rear_wall_uv(points[i][0], points[i][2]) if i in points else (0., 0.)
        uvs.append([str(i), '3', 'rear', *[repr(v) for v in (*value, *value)]])
    masks = [list(r) for r in old_mask] + [[str(i), '0'] for i in range(OLD_COUNT, COUNT)]

    segments = [list(r) for r in old_segments]
    hit = [r for r in segments if r[0] == SEGMENT]
    assert len(hit) == 1 and hit[0][1] == '2976' and hit[0][2] == str(LEDS)
    hit[0][1] = str(OFFSET)
    assert [r[1] for r in segments if r[0] == 'PORT_PANEL8_251_1'] == ['2720']

    plan = build_router_plan(router_from_rows(old_controllers, segments, COUNT))
    assert plan.controller('PANEL8_251').universe_count == 6
    # Offline proof that the measured sources reach the right wire slots.
    probe = [(1., .5, .25) if i in (OFFSET, OFFSET + LEDS - 1, 2720, 2975) else (0., 0., 0.)
             for i in range(COUNT)]
    packed = plan.pack_pixels(probe)
    previous = build_router_plan(router_from_rows(old_controllers, old_segments, OLD_COUNT)
                                 ).pack_pixels(probe[:OLD_COUNT])
    for name in ('WS2812_NODE', 'APA102_ESP', 'BACK_PANEL_249'):
        assert packed[name] == previous[name], name
    flat = [v for frame in packed['PANEL8_251'] for v in frame]
    lit = {i for i in range(len(flat) // 3) if any(flat[3 * i:3 * i + 3])}
    assert lit == {0, 255, 340, 340 + LEDS - 1}, sorted(lit)

    # apply_plan insists on the canonical global material source. The browser
    # may have another material loaded; borrow res1 and hand it straight back.
    topto = op('/project1/topto1')
    material_before = str(topto.par.top.eval())
    if material_before != '/project1/res1':
        topto.par.top = '/project1/res1'

    snapshot = adapter.capture()
    previous_apply = {k: apply_owner.fetch(k, None) for k in ('last_snapshot', 'last_applied_hash')}

    def rebuild():
        router.op('ui_callbacks').module._rebuild_router()

    stop_outputs(router)
    assert_outputs_off(op)
    try:
        write_rows(mapping, maps)
        write_rows(uv, uvs)
        write_rows(mask, masks)
        adapter._cook()
        assert all(op(p).numSamples == COUNT for p in
                   ('/project1/null4', '/project1/effect_sample_uv', '/project1/topto1', '/project1/math1'))
        apply_router_transaction(router, old_controllers, segments, rebuild, source_pixels=COUNT)
        prepared = prepare_layout(active, fixtures, mode='3d', source_count=COUNT,
                                  base_active_hash=adapter.active_hash(), preserve_routing=True,
                                  uv_source='current', active_uv_rows=table_rows(uv))
        assert prepared.source_count == COUNT
        assert set(prepared.inactive_source_indices) == inactive
        apply_plan(prepared, active, fixtures, adapter)
        assert_outputs_off(op)
        assert table_rows(router.op('controller_config')) == old_controllers
        assert table_rows(router.op('segment_config')) == segments
        preview = op('/project1/pixelblaze_mapper/preview3d/instance_data')
        preview.cook(force=True)
        renderer = op('/project1/show_control/show_led_renderer')
        renderer.cook(force=True)
        op('/project1/LED_PREVIEW_OUT').cook(force=True)
        assert preview.numSamples == renderer.numSamples == COUNT
        assert all(float(preview['a'][i]) == 0 for i in inactive)
        assert not op('/project1').errors(recurse=True)
    except Exception:
        if material_before != '/project1/res1':
            topto.par.top = material_before
        stop_outputs(router)
        mapping.text = (folder / 'before-map.tsv').read_bytes().decode('utf-8')
        uv.text = (folder / 'before-uv.tsv').read_bytes().decode('utf-8')
        mask.text = (folder / 'before-mask.tsv').read_bytes().decode('utf-8')
        adapter._cook()
        try:
            apply_router_transaction(router, old_controllers, old_segments, rebuild, source_pixels=OLD_COUNT)
        except Exception:
            pass
        adapter.restore(snapshot)
        apply_owner.store('prepared_plan', None)
        for key, value in previous_apply.items():
            apply_owner.store(key, value)
        raise

    if material_before != '/project1/res1':
        topto.par.top = material_before
        adapter._cook()
        assert not op('/project1').errors(recurse=True)

    result = dict(report)
    result.update(active_applied=True, source_count=COUNT,
                  valid_scene_points=len(points), inactive_source_count=len(inactive),
                  retired_template_sources=[min(RETIRED), max(RETIRED)],
                  offline_route_checks_passed=True, outputs_started=False,
                  was_running_before=was_running, global_material=material_before,
                  segment=[r for r in table_rows(router.op('segment_config')) if r[0] == SEGMENT][0])
    constraints = dict(editor_owner.fetch('panel_dimension_constraints', {}) or {})
    constraints[panel_id] = dict(width_cm=30, height_cm=30, active_output_integrated=True,
                                 physical_outputs=report['outputs'], reference=report['size_reference'])
    editor_owner.store('panel_dimension_constraints', constraints)
    router.store('panel7_active_integration', result)
    apply_owner.store('last_snapshot', None)
    apply_owner.store('last_applied_hash', None)
    layout.status(editor_owner,
                  'PANEL 7 FERTIG | 549/549 gemessen | unter Panel 5, links neben Panel 8 | U158-U161 | Ausgabe AUS')
    (folder / 'active-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (folder / 'active-applied-document.json').write_text(document_json(active), encoding='utf-8')
    return result
