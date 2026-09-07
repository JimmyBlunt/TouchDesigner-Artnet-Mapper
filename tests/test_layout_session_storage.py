"""Durable histories, stale-module migration and effective TOE pickle contract."""
from dataclasses import replace
import pickle
from pathlib import Path
import subprocess
import sys
import unittest

from pixelblaze_mapper.layout_scene import Scene, Scan, Transform, append_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutEditor, LayoutDocument
from pixelblaze_mapper.fixture_scene import FixtureScene, FixtureHistory, Transform2D, project_fixture, replace_transform, scene_revision
from pixelblaze_mapper.layout_session_storage import (
    layout_snapshot, restore_layout, fixture_snapshot, restore_fixtures,
    prepare_save, prepare_apply_save, LAYOUT_KEY, FIXTURE_KEY, _verify_plain,
)


def session():
    scene = append_scan(Scene("scene", "Room"), Scan("scan", "Original", ((0, 0, 0), (1, 2, 3))), source_start=0, object_id="object")
    editor = LayoutEditor(LayoutDocument(scene))
    editor.bind_route("controller", 3)
    editor.transform(Transform(translation=(1, 0, 0)))
    editor.transform(Transform(rotation_degrees=(0, 30, 0)))
    editor.undo()
    fixtures = FixtureScene(scene.scene_id, scene_revision(scene), (project_fixture(scene, "object"),), 2)
    history = FixtureHistory(fixtures)
    id = fixtures.fixtures[0].fixture_id
    history.commit(replace_transform(history.current, id, "output", Transform2D(translation=(2, 3))))
    history.commit(replace_transform(history.current, id, "uv", Transform2D(scale=(.1, .2))))
    history.undo()
    return editor, history


class StorageOwner:
    def __init__(self, values):
        self.values, self.startup = values, {}

    def fetch(self, key, default=None):
        return self.values.get(key, default)

    def store(self, key, value):
        self.values[key] = value

    def storeStartupValue(self, key, value):
        self.startup[key] = value

    def op(self, path):
        return None


class DurableSessionTests(unittest.TestCase):
    def test_histories_selection_routes_originals_roundtrip_as_primitives(self):
        editor, fixtures = session()
        for snapshot in (layout_snapshot(editor), fixture_snapshot(fixtures)):
            _verify_plain(snapshot)
            self.assertEqual(pickle.loads(pickle.dumps(snapshot)), snapshot)
        recovered = restore_layout(layout_snapshot(editor))
        self.assertEqual(recovered.current, editor.current)
        self.assertEqual(recovered._undo, editor._undo)
        self.assertEqual(recovered._redo, editor._redo)
        self.assertEqual(recovered.selected_object_id, editor.selected_object_id)
        self.assertEqual(recovered.redo(), editor.redo())
        restored = restore_fixtures(fixture_snapshot(fixtures))
        self.assertEqual(restored._undo, fixtures._undo)
        self.assertEqual(restored.redo(), fixtures.redo())

    def test_visible_preview_recovers_as_single_undoable_draft_not_mouse_state(self):
        editor, fixtures = session()
        original = editor.current
        editor.transform(Transform(translation=(9, 8, 7)), preview=True)
        restored = restore_layout(layout_snapshot(editor))
        self.assertEqual(restored.current.scene, editor.preview)
        self.assertIsNone(restored.preview)
        self.assertIsNone(restored.prepared)
        self.assertEqual(restored.undo(), original)
        initial = fixtures.current
        preview = replace_transform(initial, initial.fixtures[0].fixture_id, "uv", Transform2D(translation=(.2, .3)))
        restored_fixtures = restore_fixtures(fixture_snapshot(fixtures, preview))
        self.assertEqual(restored_fixtures.current, preview)
        self.assertEqual(restored_fixtures.undo(), initial)

    def test_prepare_save_records_plain_snapshot_before_effective_pickle(self):
        editor, fixtures = session()
        owner = StorageOwner({"layout_editor_session": editor, "fixture_history": fixtures,
                              "selected_fixture_id": fixtures.current.fixtures[0].fixture_id,
                              "layout_view": "2d", "fixture_domain": "uv", "layout_drag": ((0, 0), Transform())})
        manifest = prepare_save(owner)
        self.assertEqual(manifest["layout_undo"], len(editor._undo))
        self.assertIn(LAYOUT_KEY, owner.values)
        self.assertIn(FIXTURE_KEY, owner.values)
        effective = {**owner.values, **owner.startup}
        _verify_plain(effective)
        restored_storage = pickle.loads(pickle.dumps(effective))
        self.assertIsNone(restored_storage["layout_editor_session"])
        self.assertEqual(restore_layout(restored_storage[LAYOUT_KEY]).current, editor.current)
        self.assertEqual(restore_fixtures(restored_storage[FIXTURE_KEY]).current, fixtures.current)
        self.assertEqual(restored_storage["selected_fixture_id"], owner.values["selected_fixture_id"])
        self.assertEqual(restored_storage["layout_view"], "2d")

    def test_restore_rejects_unknown_version_and_invalid_identity_history(self):
        editor, _ = session()
        data = layout_snapshot(editor)
        with self.assertRaises(ValueError):
            restore_layout({**data, "version": 99})
        with self.assertRaises(ValueError):
            restore_layout({**data, "selected_object_id": "unknown"})

    def test_apply_plan_expires_but_exact_primitive_revert_snapshot_survives(self):
        snapshot = {"texts": {"map": "old"}, "bindings": {"callback": ("old", "", "ParMode.CONSTANT")},
                    "actual_xyz": {"null4": [(0.0, -2.0, 3.0)]}}
        owner = StorageOwner({"last_snapshot": snapshot, "last_applied_hash": "hash", "prepared_plan": object(), "applying": False})
        manifest = prepare_apply_save(owner)
        effective = {**owner.values, **owner.startup}
        _verify_plain(effective)
        restored = pickle.loads(pickle.dumps(effective))
        self.assertTrue(manifest["revert_snapshot_preserved"])
        self.assertIsNone(restored["prepared_plan"])
        self.assertEqual(restored["last_snapshot"], snapshot)
        self.assertIsInstance(restored["last_snapshot"]["bindings"]["callback"], tuple)

    def test_apply_snapshot_with_unserializable_data_blocks_instead_of_dropping_revert(self):
        owner = StorageOwner({"last_snapshot": {"bad": object()}, "last_applied_hash": "hash"})
        with self.assertRaisesRegex(ValueError, "Non-primitive"):
            prepare_apply_save(owner)
        self.assertEqual(owner.startup, {})

    def test_real_import_reload_stale_pickle_failure_migrates_without_class_identity(self):
        # Isolated interpreter avoids replacing class definitions in other tests.
        script = '''import importlib,pickle
import pixelblaze_mapper.layout_scene as scene
import pixelblaze_mapper.layout_scene_adapter as adapter
import pixelblaze_mapper.fixture_scene as fixture
from pixelblaze_mapper.layout_session_storage import layout_snapshot,restore_layout,fixture_snapshot,restore_fixtures
s=scene.append_scan(scene.Scene('s','Room'),scene.Scan('scan','Original',((1,2,3),)),source_start=0,object_id='object')
editor=adapter.LayoutEditor(adapter.LayoutDocument(s))
editor.transform(scene.Transform(translation=(1,0,0)))
history=fixture.FixtureHistory(fixture.FixtureScene('s',fixture.scene_revision(s),(fixture.project_fixture(s,'object'),),1))
importlib.reload(scene);importlib.reload(adapter);importlib.reload(fixture)
try:
    pickle.dumps(editor)
except pickle.PicklingError:
    pass
else:
    raise AssertionError('test did not reproduce stale class pickling failure')
plain=layout_snapshot(editor); fixture_plain=fixture_snapshot(history)
new=restore_layout(pickle.loads(pickle.dumps(plain)))
new_fixture=restore_fixtures(pickle.loads(pickle.dumps(fixture_plain)))
assert type(new) is adapter.LayoutEditor
assert type(new_fixture) is fixture.FixtureHistory
assert new.current.scene.world_points()[0][1] == (2,2,3)
assert new.undo().scene.world_points()[0][1] == (1,2,3)
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
