"""Sparse workspace apply preserves source addresses and stages explicit black slots."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS
import unittest

from pixelblaze_mapper.build_layout_apply import (
    prepare_layout, apply_plan, SOURCE_MASK, TouchDesignerLayoutAdapter,
)
from pixelblaze_mapper.layout_scene import Scene, Scan, SceneError, append_scan, export_pixelblaze_3d
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument
from pixelblaze_mapper.fixture_scene import FixtureScene, project_fixture, scene_revision
from tests.test_layout_apply import MemoryAdapter


def sparse_inputs(*, missing=False):
    scene = append_scan(Scene('sparse', 'Sparse layout'), Scan('scan', 'Scan', ((.1, .2, -.3), (.4, .5, -.6)),
                         missing_indices=(1,) if missing else ()), source_start=2, object_id='object')
    # Source 2 and 5 are physical LEDs. 0, 1, 3, 4 and 6 are untouched addresses,
    # not permission to rebase those two LEDs into source slots 0 and 1.
    obj = scene.objects[0]
    scene = replace(scene, objects=(replace(obj, leds=(obj.leds[0], replace(obj.leds[1], source_index=5))),))
    fixtures = FixtureScene(scene.scene_id, scene_revision(scene), (project_fixture(scene, 'object'),))
    current = (('index', 'tx', 'ty', 'tz'),) + tuple((str(i), '10', '20', '-30') for i in range(7))
    return LayoutDocument(scene), fixtures, current


def sparse_plan(mode='3d', **kwargs):
    document, fixtures, current = sparse_inputs(**kwargs)
    plan = prepare_layout(document, fixtures, mode=mode, source_count=7, base_active_hash='before',
                          preserve_routing=True, active_map_rows=current)
    return document, fixtures, plan


class SparseLayoutApplyTests(unittest.TestCase):
    def test_gaps_and_tail_slots_keep_canonical_addresses(self):
        _, _, plan = sparse_plan()
        self.assertEqual(plan.source_count, 7)
        self.assertEqual(plan.map_rows[3], (2, .1, .2, -.3))
        self.assertEqual(plan.map_rows[6], (5, .4, .5, -.6))
        self.assertEqual(plan.inactive_source_indices, (0, 1, 3, 4, 6))
        self.assertEqual(plan.source_mask_rows, (('index', 'enabled'), (0, 0), (1, 0), (2, 1), (3, 0), (4, 0), (5, 1), (6, 0)))
        for index in plan.inactive_source_indices:
            self.assertEqual(plan.map_rows[index + 1], (index, 0., 0., 0.))
            self.assertEqual(plan.uv_rows[index + 1][1:], (-1, '__inactive__', 0., 0., 0., 0.))

    def test_sparse_active_apply_does_not_weaken_dense_export(self):
        document, _, _ = sparse_plan()
        with self.assertRaisesRegex(SceneError, 'gaps'):
            export_pixelblaze_3d(document.scene)

    def test_missing_scan_binding_is_black_without_losing_identity(self):
        document, fixtures, plan = sparse_plan(missing=True)
        self.assertIn(5, plan.inactive_source_indices)
        self.assertEqual(plan.map_rows[6], (5, 0., 0., 0.))
        self.assertEqual(document.scene.objects[0].leds[1].source_index, 5)
        self.assertEqual(document.scene.scans[0].missing_indices, (1,))
        _, _, two_d = sparse_plan('2d', missing=True)
        self.assertEqual(two_d.inactive_source_indices, plan.inactive_source_indices)

    def test_2d_keeps_physical_map_and_sparse_fixture_addresses(self):
        _, _, plan = sparse_plan('2d')
        self.assertEqual(plan.map_rows, sparse_inputs()[2])
        self.assertEqual([row[0] for row in plan.fixture_output_rows[1:]], [2, 5])
        self.assertEqual(plan.uv_rows[3][3:], (.2, .1, .2, .1))
        self.assertEqual(plan.uv_rows[6][3:], (.5, .4, .5, .4))

    def test_incomplete_fixture_cannot_be_silently_blackened(self):
        document, fixtures, current = sparse_inputs()
        fixture = fixtures.fixtures[0]
        fixtures = replace(fixtures, fixtures=(replace(fixture, leds=fixture.leds[:1], local_points=fixture.local_points[:1]),))
        with self.assertRaisesRegex(SceneError, 'Fixture coverage is incomplete'):
            prepare_layout(document, fixtures, mode='2d', source_count=7, base_active_hash='before',
                           preserve_routing=True, active_map_rows=current)

    def test_outside_capacity_fails_before_any_apply(self):
        document, fixtures, _ = sparse_inputs()
        with self.assertRaisesRegex(SceneError, 'capacity'):
            prepare_layout(document, fixtures, mode='3d', source_count=5, base_active_hash='before', preserve_routing=True)

    def test_mask_payload_tampering_and_stale_workspace_fail_before_lock(self):
        document, fixtures, plan = sparse_plan()
        adapter = MemoryAdapter()
        forged = replace(plan, source_mask_rows=(('index', 'enabled'),) + tuple((i, 1) for i in range(7)))
        with self.assertRaisesRegex(SceneError, 'payload changed'):
            apply_plan(forged, document, fixtures, adapter)
        self.assertEqual(adapter.calls, [])
        changed = replace(document, scene=replace(document.scene, name='Changed'))
        with self.assertRaisesRegex(SceneError, 'changed'):
            apply_plan(plan, changed, fixtures, adapter)
        self.assertEqual(adapter.calls, [])

    def test_boolean_mask_flags_do_not_pass_integer_payload_validation(self):
        document, fixtures, plan = sparse_plan()
        forged = replace(plan, source_mask_rows=(('index', 'enabled'),) + tuple((i, bool(enabled)) for i, enabled in plan.source_mask_rows[1:]))
        adapter = MemoryAdapter()
        with self.assertRaisesRegex(SceneError, 'strict integer'):
            apply_plan(forged, document, fixtures, adapter)
        self.assertEqual(adapter.calls, [])

    def test_output_mask_contract_blacks_gaps_without_shifting_pixels(self):
        from pixelblaze_mapper.output_slot_mask import ranges_for, channels
        _, _, plan = sparse_plan()
        table = NS(text='\n'.join('\t'.join(map(str, row)) for row in plan.source_mask_rows))
        ranges = ranges_for(lambda path: table if path == SOURCE_MASK else None, plan.source_count)
        rgb = channels(([i + .1 for i in range(7)], [.7] * 7, [.8] * 7), ranges)
        self.assertEqual(len(rgb[0]), 7)
        self.assertEqual((rgb[0][2], rgb[0][5]), (2.1, 5.1))
        self.assertEqual([rgb[0][i] for i in plan.inactive_source_indices], [0.] * 5)
    def test_partial_sparse_write_restores_mask_and_prior_routing(self):
        document, fixtures, plan = sparse_plan()
        class MaskAdapter(MemoryAdapter):
            def write(self, plan):
                self.state['mask'] = plan.source_mask_rows
                super().write(plan)
        for failure in ('fail_write', 'fail_verify'):
            adapter = MaskAdapter()
            adapter.state['mask'] = 'old mask'
            setattr(adapter, failure, True)
            before = deepcopy(adapter.state)
            with self.assertRaisesRegex(SceneError, 'rolled back'):
                apply_plan(plan, document, fixtures, adapter)
            self.assertEqual(adapter.state, before)

    def test_stale_active_mask_hash_blocks_write(self):
        document, fixtures, plan = sparse_plan()
        adapter = MemoryAdapter()
        adapter.hash = 'mask changed'
        with self.assertRaisesRegex(SceneError, 'Active mapping/routing changed'):
            apply_plan(plan, document, fixtures, adapter)
        self.assertNotIn('write', adapter.calls)

    def test_output_enabled_during_snapshot_blocks_first_write(self):
        document, fixtures, plan = sparse_plan()
        adapter = MemoryAdapter()
        capture = adapter.capture
        def raced_capture():
            previous = capture()
            adapter.enabled = True
            return previous
        adapter.capture = raced_capture
        with self.assertRaisesRegex(SceneError, 'Output ON'):
            apply_plan(plan, document, fixtures, adapter)
        self.assertNotIn('write', adapter.calls)

    def test_actual_writer_publishes_mask_in_same_transaction(self):
        _, _, plan = sparse_plan()
        nodes = {}
        class Table:
            def __init__(self):
                self.rows, self.text, self.par = [], '', NS(callbacks='old')
            def clear(self): self.rows = []
            def appendRow(self, row): self.rows.append(row)
        class Adapter(TouchDesignerLayoutAdapter):
            def node(self, path): return nodes.setdefault(path, Table())
            def _cook(self): pass
        Adapter(NS(path='/project1/layout_apply')).write(plan)
        self.assertEqual(nodes[SOURCE_MASK].rows, list(plan.source_mask_rows))
        self.assertIn('"inactive_output": "black"', nodes['/project1/layout_apply/active_settings'].text)

    def test_native_restore_removes_mask_when_it_was_absent(self):
        nodes = {}
        class Mask:
            text = 'index\tenabled\n0\t0'
            def destroy(self): del nodes[SOURCE_MASK]
        nodes[SOURCE_MASK] = Mask()
        nodes['/project1/LedMap'] = NS(par=NS(callbacks='new callback'))
        snapshot = {'texts': {SOURCE_MASK: None},
                    'bindings': {'/project1/LedMap|callbacks': ('old callback', None, 'ParMode.CONSTANT')},
                    'output_contract': {}}
        class Adapter(TouchDesignerLayoutAdapter):
            def node(self, path): return nodes[path]
            def output_contract(self): return {}
            def _cook(self): pass
            def capture(self):
                return {'texts': {SOURCE_MASK: nodes[SOURCE_MASK].text if SOURCE_MASK in nodes else None},
                        'bindings': {'/project1/LedMap|callbacks': (nodes['/project1/LedMap'].par.callbacks, None, 'ParMode.CONSTANT')},
                        'output_contract': {}}
        Adapter(NS(op=nodes.get)).restore(snapshot)
        self.assertNotIn(SOURCE_MASK, nodes)
        self.assertEqual(nodes['/project1/LedMap'].par.callbacks, 'old callback')

    def test_native_restore_rejects_concurrently_changed_output_contract(self):
        class Adapter(TouchDesignerLayoutAdapter):
            def output_contract(self): return {'sender': 'changed source'}
            def node(self, path): self.fail('No restoration writes allowed')
        with self.assertRaisesRegex(SceneError, 'Output callbacks or sink wiring changed concurrently'):
            Adapter(NS()).restore({'output_contract': {'sender': 'reviewed source'}})

    def test_legacy_parameter_and_referenced_dat_changes_invalidate_output_contract(self):
        from pixelblaze_mapper.build_layout_apply import digest
        from tests.test_native_dmx_gate import Parameter
        par = Parameter(255.)
        par.name, par.style, par.bindExpr = 'gain', 'Float', ''
        pulse = Parameter(0)
        pulse.name, pulse.style = 'resetpulse', 'Pulse'
        dat = NS(path='/project1/universe_rows', type='table', family='DAT', text='source\tuniverse\n0\t1', inputs=[], par=NS())
        reference = Parameter(dat)
        reference.name, reference.style = 'dat', 'DAT'
        node = NS(path='/project1/math2', type='math', family='CHOP', inputs=[], par=NS(),
                  pars=lambda: [par, pulse, reference], sample_value=.2)
        nodes = {node.path: node, dat.path: dat}
        adapter = TouchDesignerLayoutAdapter(NS(op=nodes.get))
        before = digest(adapter.output_contract())
        node.sample_value = .9  # Live animation samples are not structural settings.
        pulse.val = 1
        self.assertEqual(digest(adapter.output_contract()), before)
        par.val = 254.
        self.assertNotEqual(digest(adapter.output_contract()), before)
        par.val = 255.
        dat.text = 'source\tuniverse\n0\t2'
        self.assertNotEqual(digest(adapter.output_contract()), before)
        dat.text = 'source\tuniverse\n0\t1'
        par.expr = '255 * .5'
        self.assertNotEqual(digest(adapter.output_contract()), before)

    def test_legacy_direct_dat_sources_participate_in_output_contract(self):
        from pixelblaze_mapper.build_layout_apply import digest
        dat = NS(path='/project1/Universe_Config', type='table', family='DAT', text='0\t1', inputs=[], par=NS())
        adapter = TouchDesignerLayoutAdapter(NS(op=lambda path: dat if path == dat.path else None))
        before = digest(adapter.output_contract())
        dat.text = '0\t2'
        self.assertNotEqual(digest(adapter.output_contract()), before)


if __name__ == '__main__':
    unittest.main()
