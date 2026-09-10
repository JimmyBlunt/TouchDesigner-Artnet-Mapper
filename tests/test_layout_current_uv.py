"""Physical-world geometry can apply independently of established material UV."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from pixelblaze_mapper.build_layout_apply import prepare_layout, apply_plan, TouchDesignerLayoutAdapter, MAP, UV
from pixelblaze_mapper.layout_scene import SceneError, Transform
from tests.test_layout_apply import MemoryAdapter
from tests.test_sparse_layout_apply import sparse_inputs


def current_inputs():
    document, fixtures, active_map = sparse_inputs()
    obj = document.scene.objects[0]
    document = replace(document, scene=replace(document.scene, objects=(replace(obj,
        transform=Transform(translation=(20., -40., 60.))),)))
    uvs = (('index', 'panel_id', 'panel', 'global_u', 'global_v', 'local_u', 'local_v'),) + tuple(
        (str(index), '8', 'Existing material panel', '.1', '.2', '.8', '.9') for index in range(7))
    return document, fixtures, active_map, uvs


def current_plan():
    document, fixtures, _, uvs = current_inputs()
    return document, fixtures, prepare_layout(document, fixtures, mode='3d', source_count=7,
        base_active_hash='before', preserve_routing=True, uv_source='current', active_uv_rows=uvs)


class CurrentMaterialUVTests(unittest.TestCase):
    def test_arbitrary_world_xyz_preserves_entire_material_uv_snapshot(self):
        document, fixtures, _, uvs = current_inputs()
        with self.assertRaisesRegex(SceneError, 'Projected 3D UV outside'):
            prepare_layout(document, fixtures, mode='3d', source_count=7, base_active_hash='before', preserve_routing=True)
        document, fixtures, plan = current_plan()
        self.assertEqual(plan.uv_rows, uvs)
        self.assertEqual(plan.map_rows[3], (2, 20.1, -39.8, 59.7))
        self.assertEqual(plan.inactive_source_indices, (0, 1, 3, 4, 6))
        self.assertEqual(plan.uv_source, 'current')
        apply_plan(plan, document, fixtures, MemoryAdapter())

    def test_invalid_current_uv_never_becomes_an_apply_plan(self):
        document, fixtures, _, uvs = current_inputs()
        variants = [None, uvs[:-1], (('bad',),) + uvs[1:], uvs[:1] + tuple(reversed(uvs[1:]))]
        for value in ('nan', '1.001', '-.01', 'not numeric', True):
            variants.append(uvs[:1] + (uvs[1][:3] + (value,) + uvs[1][4:],) + uvs[2:])
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(SceneError):
                prepare_layout(document, fixtures, mode='3d', source_count=7,
                    base_active_hash='before', preserve_routing=True, uv_source='current', active_uv_rows=rows)

    def test_keep_current_is_an_explicit_3d_only_choice(self):
        document, fixtures, active_map, uvs = current_inputs()
        for mode, choice in (('2d', 'current'), ('3d', 'automatic')):
            with self.assertRaises(SceneError):
                prepare_layout(document, fixtures, mode=mode, source_count=7,
                    base_active_hash='before', preserve_routing=True, uv_source=choice,
                    active_map_rows=active_map, active_uv_rows=uvs)

    def test_stale_current_uv_hash_stops_before_write(self):
        document, fixtures, plan = current_plan()
        adapter = MemoryAdapter()
        adapter.hash = 'material UV changed'
        with self.assertRaisesRegex(SceneError, 'Active mapping/routing changed'):
            apply_plan(plan, document, fixtures, adapter)
        self.assertNotIn('write', adapter.calls)

    def test_preflight_checks_live_uv_against_prepared_snapshot(self):
        _, _, plan = current_plan()
        changed = [list(row) for row in plan.uv_rows]
        changed[3][3] = '.3'
        class Table:
            def __init__(self, rows): self.rows, self.numRows, self.numCols = rows, len(rows), len(rows[0])
            def __getitem__(self, key): return self.rows[key[0]][key[1]]
        class Adapter(TouchDesignerLayoutAdapter):
            def node(self, path): return {MAP: NS(numRows=8), UV: Table(changed)}[path]
        with patch('pixelblaze_mapper.output_slot_mask.assert_sparse_contract', return_value=True):
            with self.assertRaisesRegex(SceneError, 'Current material UV changed'):
                Adapter(NS(op=lambda path: None)).preflight(plan)

    def test_actual_writer_does_not_touch_preserved_uv_table(self):
        _, _, plan = current_plan()
        nodes = {}
        class Table:
            def __init__(self): self.rows, self.text, self.par = [], '', NS(callbacks='old')
            def clear(self): self.rows = []
            def appendRow(self, row): self.rows.append(row)
        class Adapter(TouchDesignerLayoutAdapter):
            def node(self, path):
                if path == UV:
                    raise AssertionError('Preserved UV must not be written')
                return nodes.setdefault(path, Table())
            def _cook(self): pass
        Adapter(NS(path='/project1/layout_apply')).write(plan)
        self.assertEqual(nodes[MAP].rows, list(plan.map_rows))

    def test_failure_restores_prior_geometry_and_uv(self):
        document, fixtures, plan = current_plan()
        adapter = MemoryAdapter()
        adapter.state['uv'] = plan.uv_rows
        before = deepcopy(adapter.state)
        adapter.fail_verify = True
        with self.assertRaisesRegex(SceneError, 'rolled back'):
            apply_plan(plan, document, fixtures, adapter)
        self.assertEqual(adapter.state, before)


if __name__ == '__main__':
    unittest.main()
