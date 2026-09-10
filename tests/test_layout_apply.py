"""Offline behavior tests for actual prepared-layout transaction and callbacks."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace as NS
import unittest

from pixelblaze_mapper.layout_scene import Scene, Scan, append_scan, SceneError, export_pixelblaze_3d
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument
from pixelblaze_mapper.fixture_scene import FixtureScene, project_fixture, scene_revision, replace_transform, Transform2D
from pixelblaze_mapper.build_layout_apply import prepare_layout, apply_plan, POSITION_CALLBACK, TouchDesignerLayoutAdapter, MAP, UV, SOURCE_MASK


def inputs():
    scene = append_scan(Scene('s', 'Scene', expected_count=2), Scan('raw', 'Raw', ((.1, .2, -.5), (.3, .4, .8))),
                        source_start=0, object_id='object')
    fixture = project_fixture(scene, 'object', fixture_id='fixture')
    fixtures = FixtureScene(scene.scene_id, scene_revision(scene), (fixture,), expected_count=2)
    document = LayoutDocument(scene)
    active = (('index', 'tx', 'ty', 'tz'), ('0', '10', '20', '-30'), ('1', '40', '50', '-60'))
    return document, fixtures, active


def prepared(mode='2d'):
    document, fixtures, active = inputs()
    plan = prepare_layout(document, fixtures, mode=mode, projection='YX', source_count=2,
        base_active_hash='before', preserve_routing=True, active_map_rows=active)
    return document, fixtures, plan


class MemoryAdapter:
    def __init__(self):
        self.state = {'map': 'original', 'uv': 'original', 'routing': 'fixed'}
        self.calls = []
        self.enabled = False
        self.hash = 'before'
        self.fail_write = self.fail_verify = self.fail_restore = False

    def assert_outputs_off(self):
        if self.enabled:
            raise SceneError('Output ON')

    @contextmanager
    def lock(self):
        self.calls.append('lock')
        yield

    def active_hash(self):
        return self.hash

    def preflight(self, plan):
        self.calls.append('preflight')

    def capture(self):
        self.calls.append('capture')
        return deepcopy(self.state)

    def write(self, plan):
        self.calls.append('write')
        if plan.mode == '3d':
            self.state['map'] = plan.map_rows
        self.state['uv'] = plan.uv_rows
        if self.fail_write:
            raise ValueError('partial write failed')

    def verify(self, plan, snapshot):
        self.calls.append('verify')
        return not self.fail_verify

    def restore(self, snapshot):
        self.calls.append('restore')
        if self.fail_restore:
            raise ValueError('recovery failed')
        self.state = snapshot

    def remember(self, snapshot, plan):
        self.calls.append('remember')
        self.snapshot = snapshot


class LayoutApplyTests(unittest.TestCase):
    def test_2d_preserves_physical_map_and_records_output_separately(self):
        document, fixtures, plan = prepared()
        self.assertEqual(plan.map_rows, inputs()[2])
        self.assertEqual(plan.map_3d_rows, plan.map_rows)
        self.assertEqual(plan.fixture_output_rows[1][-2:], (.2, .1))
        self.assertEqual(plan.uv_rows[1][3:], (.2, .1, .2, .1))
        self.assertEqual(json.loads(plan.workspace_json)['layout']['scene']['scene_id'], 's')

    def test_3d_world_coordinates_preserve_negative_depth(self):
        document, fixtures, plan = prepared('3d')
        self.assertEqual(plan.map_rows[1], (0, .1, .2, -.5))
        self.assertEqual(plan.uv_rows[1][3:5], (.2, .1))
        self.assertEqual(json.loads(export_pixelblaze_3d(document.scene))[0][2], -.5)

    def test_count_and_routing_confirmation_fail_without_writes(self):
        document, fixtures, active = inputs()
        for changes in ({'source_count': 3}, {'preserve_routing': False}, {'mode': 'auto'}, {'projection': 'automatic'}):
            args = dict(mode='2d', projection='YX', source_count=2, base_active_hash='before', preserve_routing=True, active_map_rows=active)
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(SceneError):
                prepare_layout(document, fixtures, **args)

    def test_2d_requires_current_map_and_no_silent_uv_clamp(self):
        document, fixtures, active = inputs()
        for data in (None, (('bad',),), active[::-1]):
            with self.subTest(data=data), self.assertRaises(SceneError):
                prepare_layout(document, fixtures, mode='2d', source_count=2, base_active_hash='before',
                    preserve_routing=True, active_map_rows=data)
        fixtures = replace_transform(fixtures, 'fixture', 'uv', Transform2D(translation=(2, 3)))
        with self.assertRaises(ValueError):
            prepare_layout(document, fixtures, mode='2d', source_count=2, base_active_hash='before',
                preserve_routing=True, active_map_rows=active)

    def test_out_of_bounds_3d_projection_rejected(self):
        document, fixtures, _ = inputs()
        with self.assertRaises(SceneError):
            prepare_layout(document, fixtures, mode='3d', projection='XZ', source_count=2,
                base_active_hash='before', preserve_routing=True)

    def test_success_changes_sampling_not_routing_and_remembers_snapshot(self):
        document, fixtures, plan = prepared()
        adapter = MemoryAdapter()
        apply_plan(plan, document, fixtures, adapter)
        self.assertEqual(adapter.state['map'], 'original')
        self.assertEqual(adapter.state['routing'], 'fixed')
        self.assertEqual(adapter.state['uv'], plan.uv_rows)
        self.assertEqual(adapter.snapshot['uv'], 'original')

    def test_partial_write_and_failed_verification_restore(self):
        document, fixtures, plan = prepared()
        for field in ('fail_write', 'fail_verify'):
            adapter = MemoryAdapter()
            setattr(adapter, field, True)
            original = deepcopy(adapter.state)
            with self.subTest(field=field), self.assertRaisesRegex(SceneError, 'rolled back'):
                apply_plan(plan, document, fixtures, adapter)
            self.assertEqual(adapter.state, original)
            self.assertIn('restore', adapter.calls)

    def test_failed_recovery_is_not_success(self):
        document, fixtures, plan = prepared()
        adapter = MemoryAdapter()
        adapter.fail_write = adapter.fail_restore = True
        with self.assertRaisesRegex(SceneError, 'ROLLBACK FAILED'):
            apply_plan(plan, document, fixtures, adapter)

    def test_stale_active_and_output_on_do_not_write(self):
        document, fixtures, plan = prepared()
        for field, value in (('hash', 'changed'), ('enabled', True)):
            adapter = MemoryAdapter()
            setattr(adapter, field, value)
            with self.subTest(field=field), self.assertRaises(SceneError):
                apply_plan(plan, document, fixtures, adapter)
            self.assertNotIn('write', adapter.calls)

    def test_workspace_changed_in_other_domain_invalidates_preparation(self):
        document, fixtures, plan = prepared()
        changed = replace_transform(fixtures, 'fixture', 'output', Transform2D(translation=(1, 2)))
        adapter = MemoryAdapter()
        with self.assertRaisesRegex(SceneError, 'changed'):
            apply_plan(plan, document, changed, adapter)
        self.assertEqual(adapter.calls, [])

    def test_forged_uv_payload_is_revalidated(self):
        document, fixtures, plan = prepared()
        adapter = MemoryAdapter()
        with self.assertRaises(SceneError):
            apply_plan(replace(plan, uv_rows=()), document, fixtures, adapter)
        self.assertEqual(adapter.calls, [])

    def test_snapshot_race_stops_before_first_write(self):
        document, fixtures, plan = prepared()
        adapter = MemoryAdapter()
        capture = adapter.capture
        def changed_capture():
            snapshot = capture()
            adapter.hash = 'changed'
            return snapshot
        adapter.capture = changed_capture
        with self.assertRaisesRegex(SceneError, 'snapshot'):
            apply_plan(plan, document, fixtures, adapter)
        self.assertNotIn('write', adapter.calls)

    def test_exact_position_callback_never_recenters_negative_values(self):
        rows = inputs()[2]
        class Table:
            numRows = len(rows)
            def __getitem__(self, key):
                row, name = key
                return rows[row][rows[0].index(name)]
        class Chop:
            def __init__(self): self.channels = {}
            def clear(self): self.channels = {}
            def appendChan(self, name):
                value = NS(vals=[])
                self.channels[name] = value
                return value
        scope = {'op': lambda _: Table()}
        exec(compile(POSITION_CALLBACK, '<actual position callback>', 'exec'), scope)
        chop = Chop()
        scope['onCook'](chop)
        self.assertEqual(chop.channels['tz'].vals, [-30.0, -60.0])
        self.assertEqual(chop.numSamples, 2)

    def test_actual_td_writer_in_2d_does_not_write_map_or_material_source(self):
        document, fixtures, plan = prepared()
        nodes = {}
        class Table:
            def __init__(self): self.rows = []; self.text = ''; self.par = NS(callbacks='old')
            def clear(self): self.rows = []
            def appendRow(self, row): self.rows.append(row)
        class Fake(TouchDesignerLayoutAdapter):
            def node(self, path): return nodes.setdefault(path, Table())
            def _cook(self): pass
        adapter = Fake(NS(path='/project1/layout_apply'))
        adapter.write(plan)
        self.assertNotIn(MAP, nodes)
        self.assertNotIn('/project1/res1', nodes)
        self.assertEqual(nodes[UV].rows, list(plan.uv_rows))

    def test_2d_writer_preserves_legacy_position_callback_binding(self):
        _, _, plan = prepared()
        nodes = {}
        class Table:
            def __init__(self): self.rows = []; self.text = ''; self.par = NS(callbacks='/project1/read_LED_map')
            def clear(self): self.rows = []
            def appendRow(self, row): self.rows.append(row)
        class Fake(TouchDesignerLayoutAdapter):
            def node(self, path): return nodes.setdefault(path, Table())
            def _cook(self): pass
        adapter = Fake(NS(path='/project1/layout_apply'))
        led = adapter.node('/project1/LedMap')
        adapter.write(plan)
        self.assertEqual(led.par.callbacks, '/project1/read_LED_map')

    def test_2d_verification_accepts_unchanged_legacy_display_offset_not_raw_xyz(self):
        _, _, plan = prepared()
        from pixelblaze_mapper.build_layout_apply import ROUTER
        class Table:
            def __init__(self, rows): self.rows = [[str(v) for v in row] for row in rows]; self.numRows = len(rows); self.numCols = len(rows[0])
            def __getitem__(self, key): return self.rows[key[0]][key[1]]
        class Chop:
            numSamples = 2
            def __init__(self, channels): self.channels = channels
            def __getitem__(self, key): return self.channels[key]
        # Physical table negative Z is still viewed through the legacy +60 shift.
        displayed = {'tx': [10., 40.], 'ty': [20., 50.], 'tz': [30., 0.]}
        sample_uv = {'tx': [.2, .4], 'ty': [.1, .3], 'tz': [0., 0.]}
        nodes = {MAP: Table(plan.map_rows), UV: Table(plan.uv_rows), SOURCE_MASK: Table(plan.source_mask_rows),
                 '/project1/LedMap': Chop(displayed), '/project1/null4': Chop(displayed),
                 '/project1/effect_sample_uv': Chop(sample_uv), '/project1/topto1': NS(numSamples=2),
                 '/project1/math1': NS(numSamples=2)}
        state = {'texts': {p: 'original' for p in (ROUTER + '/controller_config', ROUTER + '/segment_config',
                 '/project1/effect_sample_uv_callbacks', '/project1/read_LED_map')}, 'links': {},
                 'bindings': {'/project1/LedMap|callbacks': ('/project1/read_LED_map', None, 'ParMode.CONSTANT')},
                 'downstream_xyz': {path: deepcopy(displayed) for path in ('/project1/LedMap', '/project1/null4')}}
        class Fake(TouchDesignerLayoutAdapter):
            def node(self, path): return nodes[path]
            def capture(self): return deepcopy(state)
        adapter = Fake(NS(path='/project1/layout_apply'))
        self.assertTrue(adapter.verify(plan, deepcopy(state)))
        snapshot = deepcopy(state)
        state['bindings']['/project1/LedMap|callbacks'] = ('/project1/layout_apply/position_callbacks', None, 'ParMode.CONSTANT')
        self.assertFalse(adapter.verify(plan, snapshot))
        state['bindings'] = deepcopy(snapshot['bindings'])
        state['downstream_xyz']['/project1/null4']['tz'][0] += .001
        self.assertFalse(adapter.verify(plan, snapshot))


if __name__ == '__main__':
    unittest.main()
