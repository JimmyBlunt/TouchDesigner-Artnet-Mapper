"""Offline behavioral tests for independent layout/UV fixture domains."""
from dataclasses import FrozenInstanceError, replace
import json
import unittest

from pixelblaze_mapper.layout_scene import Scene, Scan, Transform, append_scan, export_scene_json, set_transform
from pixelblaze_mapper.fixture_scene import (
    Fixture, FixtureError, FixtureHistory, FixtureScene, Transform2D, add_fixture,
    export_fixture_json, export_sampling_uv, import_fixture_json, project_fixture,
    replace_transform, scene_revision,
)


def source():
    return append_scan(Scene('scene', 'Original', expected_count=3),
        Scan('scan', 'Raw', ((0.1, 0.2, 5), (0.3, 0.4, 6), (0.5, 0.6, 7))),
        source_start=0, object_id='object')


def draft():
    scene = source()
    return FixtureScene(scene.scene_id, scene_revision(scene), (project_fixture(scene, 'object', fixture_id='fixture'),), expected_count=3)


class FixtureSceneTests(unittest.TestCase):
    def test_default_projection_y_horizontal_x_vertical_no_3d_mutation(self):
        scene = source()
        before = export_scene_json(scene)
        fixture = project_fixture(scene, 'object')
        self.assertEqual(fixture.local_points, ((0.2, 0.1), (0.4, 0.3), (0.6, 0.5)))
        self.assertEqual(fixture.leds, scene.object('object').leds)
        self.assertEqual(before, export_scene_json(scene))

    def test_registered_local_projection_ignores_world_object_transform(self):
        original = source()
        changed = set_transform(original, 'object', Transform(translation=(100, 200, 300)))
        self.assertEqual(project_fixture(original, 'object').local_points, project_fixture(changed, 'object').local_points)
        registered = replace(original, scans=(replace(original.scans[0], registration=Transform(translation=(2, 3, 0))),))
        self.assertEqual(project_fixture(registered, 'object').local_points[0], (3.2, 2.1))

    def test_all_explicit_projections(self):
        for projection, expected in (('XY', (0.1, 0.2)), ('YX', (0.2, 0.1)), ('XZ', (0.1, 5)),
                                     ('ZX', (5, 0.1)), ('YZ', (0.2, 5)), ('ZY', (5, 0.2))):
            with self.subTest(projection=projection):
                self.assertEqual(project_fixture(source(), 'object', projection).local_points[0], expected)
        with self.assertRaises(FixtureError):
            project_fixture(source(), 'object', 'AUTO')

    def test_output_move_never_moves_uv(self):
        old = draft()
        changed = replace_transform(old, 'fixture', 'output', Transform2D(translation=(42, -2), rotation=33, scale=(2, 3)))
        self.assertEqual(old.sampling_rows(), changed.sampling_rows())
        self.assertNotEqual(old.fixture('fixture').output_points(), changed.fixture('fixture').output_points())
        self.assertEqual(old.fixture('fixture').local_points, changed.fixture('fixture').local_points)

    def test_uv_move_never_moves_output(self):
        old = draft()
        changed = replace_transform(old, 'fixture', 'uv', Transform2D(translation=(0.1, 0.2), rotation=45, scale=(-1, 2)))
        self.assertEqual(old.fixture('fixture').output_points(), changed.fixture('fixture').output_points())
        self.assertNotEqual(old.sampling_rows(), changed.sampling_rows())
        self.assertEqual(old.fixture('fixture').leds, changed.fixture('fixture').leds)

    def test_transform_order_and_pivot(self):
        result = Transform2D(translation=(10, 20), rotation=90, scale=(2, 3), pivot=(1, 1)).apply((2, 3))
        self.assertAlmostEqual(result[0], 5)
        self.assertAlmostEqual(result[1], 23)

    def test_invalid_numeric_transform_values(self):
        for args in ({'rotation': True}, {'rotation': float('nan')}, {'scale': (0, 1)},
                     {'translation': (1, float('inf'))}, {'pivot': (1,)}, {'scale': ('1', 1)}):
            with self.subTest(args=args), self.assertRaises(FixtureError):
                Transform2D(**args)
        with self.assertRaises(FixtureError):
            replace_transform(draft(), 'fixture', 'both', Transform2D())

    def test_bounds_are_visible_not_silently_clamped(self):
        changed = replace_transform(draft(), 'fixture', 'uv', Transform2D(translation=(-2, 3)))
        self.assertEqual(len(changed.fixture('fixture').out_of_bounds_ids()), 3)
        with self.assertRaises(FixtureError):
            export_sampling_uv(changed)
        rows = json.loads(export_sampling_uv(changed, bounds='preserve'))
        self.assertEqual(rows[0], [-1.8, 3.1])
        with self.assertRaises(FixtureError):
            export_sampling_uv(changed, bounds='clamp')

    def test_sample_export_stable_source_order(self):
        base = draft()
        fixture = base.fixture('fixture')
        reversed_fixture = replace(fixture, leds=tuple(reversed(fixture.leds)), local_points=tuple(reversed(fixture.local_points)))
        reordered = replace(base, fixtures=(reversed_fixture,))
        self.assertEqual(export_sampling_uv(base), export_sampling_uv(reordered))
        self.assertEqual(json.loads(export_sampling_uv(base)), [[0.2, 0.1], [0.4, 0.3], [0.6, 0.5]])

    def test_holes_missing_and_expected_count_block_export(self):
        base = draft()
        fixture = base.fixture('fixture')
        for bad in (replace(base, expected_count=4),
                    replace(base, fixtures=(replace(fixture, missing_ids=(fixture.leds[0].led_id,)),)),
                    replace(base, fixtures=(replace(fixture, leds=fixture.leds[1:], local_points=fixture.local_points[1:]),), expected_count=None)):
            with self.subTest(bad=bad), self.assertRaises(FixtureError):
                export_sampling_uv(bad)

    def test_duplicate_ownership_rejected(self):
        base = draft()
        with self.assertRaises(FixtureError):
            add_fixture(base, replace(base.fixture('fixture'), fixture_id='other'))

    def test_json_roundtrip_both_domains_and_missing(self):
        base = replace_transform(draft(), 'fixture', 'uv', Transform2D(translation=(0.2, 0.3), rotation=25, pivot=(0.5, 0.5)))
        rebuilt = import_fixture_json(export_fixture_json(base))
        self.assertEqual(base, rebuilt)
        self.assertEqual(base.sampling_rows(), rebuilt.sampling_rows())
        with self.assertRaises(FrozenInstanceError):
            rebuilt.fixtures = ()

    def test_json_unknown_and_duplicate_fields_fail(self):
        for text in ('{}', '[]', '{"schema":"x","schema":"y"}', '{"schema":"pixelblaze-fixture-scene","version":9}'):
            with self.subTest(text=text), self.assertRaises(FixtureError):
                import_fixture_json(text)
        doc = json.loads(export_fixture_json(draft()))
        doc['surprise'] = True
        with self.assertRaises(FixtureError):
            import_fixture_json(json.dumps(doc))

    def test_stale_scene_requires_explicit_rebase(self):
        original = source()
        base = FixtureScene(original.scene_id, scene_revision(original), (project_fixture(original, 'object'),))
        base.validate_source_scene(original)
        with self.assertRaises(FixtureError):
            base.validate_source_scene(set_transform(original, 'object', Transform(translation=(1, 2, 3))))

    def test_undo_redo_domains_and_branch(self):
        base = draft()
        history = FixtureHistory(base)
        moved = replace_transform(base, 'fixture', 'output', Transform2D(translation=(2, 3)))
        history.commit(moved)
        uv = replace_transform(moved, 'fixture', 'uv', Transform2D(scale=(0.5, 0.5)))
        history.commit(uv)
        self.assertEqual(history.undo(), moved)
        self.assertEqual(history.undo(), base)
        self.assertEqual(history.redo(), moved)
        history.commit(replace_transform(moved, 'fixture', 'uv', Transform2D(rotation=45)))
        self.assertFalse(history.can_redo)

    def test_history_cannot_mutate_local_geometry_or_identity(self):
        base = draft()
        fixture = base.fixture('fixture')
        changed = replace(base, fixtures=(replace(fixture, local_points=((0, 0),) + fixture.local_points[1:]),))
        with self.assertRaises(FixtureError):
            FixtureHistory(base).commit(changed)


if __name__ == '__main__':
    unittest.main()
