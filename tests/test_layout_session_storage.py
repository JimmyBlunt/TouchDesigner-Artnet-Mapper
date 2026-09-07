"""Durable histories, stale-module migration and effective TOE pickle contract."""
from dataclasses import replace
import gc
import json
import pickle
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from pixelblaze_mapper.layout_scene import Scene, Scan, Transform, append_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutEditor, LayoutDocument
from pixelblaze_mapper.fixture_scene import FixtureScene, FixtureHistory, Transform2D, project_fixture, replace_transform, scene_revision
from pixelblaze_mapper.layout_session_storage import (
    layout_snapshot, restore_layout, fixture_snapshot, restore_fixtures,
    prepare_save, prepare_apply_save, LAYOUT_KEY, FIXTURE_KEY, _verify_plain,
    clear_serialization_cache, serialized, _SERIALIZED,
)
from pixelblaze_mapper import layout_session_storage as storage


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
    def setUp(self):
        clear_serialization_cache()

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

    def test_schema1_history_and_preview_remain_restore_compatible(self):
        editor, fixtures = session()
        editor.transform(Transform(translation=(4, 5, 6)), preview=True)
        data = layout_snapshot(editor)
        old = {**data, "version": 1, "current": json.loads(data["current"]),
               "undo": [json.loads(v) for v in data["undo"]], "redo": [json.loads(v) for v in data["redo"]],
               "preview": json.loads(data["preview"])}
        self.assertEqual(restore_layout(old).current, restore_layout(data).current)
        data = fixture_snapshot(fixtures)
        old = {**data, "version": 1, "current": json.loads(data["current"]),
               "undo": [json.loads(v) for v in data["undo"]], "redo": [json.loads(v) for v in data["redo"]]}
        self.assertEqual(restore_fixtures(old).redo(), restore_fixtures(data).redo())

    def test_prepopulated_cache_bypasses_old_and_nested_only_reloaded_classes(self):
        script = '''import importlib
from unittest.mock import patch
import pixelblaze_mapper.layout_scene as scene
import pixelblaze_mapper.layout_scene_adapter as adapter
import pixelblaze_mapper.fixture_scene as fixture
import pixelblaze_mapper.layout_session_storage as storage
s=scene.append_scan(scene.Scene('s','Room'),scene.Scan('scan','Original',((1,2,3),)),source_start=0,object_id='object')
doc=adapter.LayoutDocument(s)
f=fixture.FixtureScene('s',fixture.scene_revision(s),(fixture.project_fixture(s,'object'),),1)
values=(('document',doc),('scene',s),('fixture',f))
for kind,value in values: storage.serialized(kind,value)
with patch.object(storage,'_encode_uncached',wraps=storage._encode_uncached) as encode:
    for kind,value in values: storage.serialized(kind,value)
    assert encode.call_count == 0
importlib.reload(scene)
assert type(doc) is adapter.LayoutDocument
with patch.object(storage,'_encode_uncached',wraps=storage._encode_uncached) as encode:
    storage.serialized('document',doc)
    assert encode.call_count == 1, 'nested model reload must invalidate current outer-class cache'
importlib.reload(adapter);importlib.reload(fixture)
with patch.object(storage,'_encode_uncached',wraps=storage._encode_uncached) as encode:
    for kind,value in values: storage.serialized(kind,value)
    assert encode.call_count == 3, 'cached-before-reload stale values must bypass'
for kind,value in values: assert (kind,id(value)) not in storage._SERIALIZED
new=adapter.load_document_json(storage.serialized('document',doc))
storage.serialized('document',new)
with patch.object(storage,'_encode_uncached',wraps=storage._encode_uncached) as encode:
    for _ in range(5): storage.serialized('document',new)
    assert encode.call_count == 0, 'current-generation warm path must remain cached'
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unchanged_snapshot_serializes_zero_entries_and_writes_no_storage(self):
        editor, fixtures = session()
        owner = StorageOwner({})
        storage.persist_layout(owner, editor)
        storage.persist_fixtures(owner, fixtures)
        previous = (owner.values[LAYOUT_KEY], owner.values[FIXTURE_KEY])
        with patch.object(storage, "_encode_uncached", wraps=storage._encode_uncached) as encode:
            for _ in range(5):
                storage.persist_layout(owner, editor)
                storage.persist_fixtures(owner, fixtures)
            encode.assert_not_called()
        self.assertIs(owner.values[LAYOUT_KEY], previous[0])
        self.assertIs(owner.values[FIXTURE_KEY], previous[1])

    def test_drag_serializes_only_new_preview_not_unchanged_current_or_history(self):
        editor, fixtures = session()
        layout_snapshot(editor)
        fixture_snapshot(fixtures)
        initial_layout = editor.current
        initial_fixture = fixtures.current
        with patch.object(storage, "_encode_uncached", wraps=storage._encode_uncached) as encode:
            for i in range(3):
                editor.transform(Transform(translation=(i + 10, 0, 0)), preview=True)
                layout_data = layout_snapshot(editor)
                preview = replace_transform(fixtures.current, fixtures.current.fixtures[0].fixture_id, "uv", Transform2D(translation=(i + .1, 0)))
                fixture_data = fixture_snapshot(fixtures, preview)
            self.assertEqual([call.args[0] for call in encode.call_args_list], ["scene", "fixture"] * 3)
        self.assertIs(editor.current, initial_layout)
        self.assertIs(fixtures.current, initial_fixture)
        self.assertEqual(restore_layout(layout_data).current.scene, editor.preview)
        self.assertEqual(restore_fixtures(fixture_data).current, preview)

    def test_cache_holds_strings_not_mutable_snapshot_aliases(self):
        editor, _ = session()
        first = layout_snapshot(editor)
        good = first["current"]
        first["current"] = "corrupted external copy"
        first["undo"].clear()
        again = layout_snapshot(editor)
        self.assertEqual(again["current"], good)
        self.assertEqual(len(again["undo"]), len(editor._undo))
        self.assertTrue(all(isinstance(entry[1], str) for entry in _SERIALIZED.values()))

    def test_nested_mutable_model_bypasses_identity_cache(self):
        editor, _ = session()
        # Models normally normalize this to tuples. Simulate a legacy/corrupt
        # nested container before the first cache read: never trust its identity.
        metadata = [[("note", "before")], [("note", "before")]]
        scan = editor.current.scene.scans[0]
        object.__setattr__(scan, "row_metadata", metadata)
        with patch.object(storage, "_encode_uncached", wraps=storage._encode_uncached) as encode:
            before = serialized("document", editor.current)
            metadata[0][0] = ("note", "after")
            after = serialized("document", editor.current)
            self.assertEqual(encode.call_count, 2)
        self.assertNotEqual(before, after)
        self.assertNotIn(("document", id(editor.current)), _SERIALIZED)

    def test_weak_cache_releases_discarded_models(self):
        editor, _ = session()
        value = editor.current
        key = ("document", id(value))
        serialized("document", value)
        self.assertIn(key, _SERIALIZED)
        del editor, value
        gc.collect()
        self.assertNotIn(key, _SERIALIZED)

    def test_preflight_forces_full_reencoding_and_publishes_both_only_after_success(self):
        editor, fixtures = session()
        owner = StorageOwner({"layout_editor_session": editor, "fixture_history": fixtures})
        prepare_save(owner)
        old_layout, old_fixture = owner.values[LAYOUT_KEY], owner.values[FIXTURE_KEY]
        with patch.object(storage, "_encode_uncached", wraps=storage._encode_uncached) as encode:
            prepare_save(owner)
            self.assertEqual(encode.call_count, 2 + len(editor._undo) + len(editor._redo) + len(fixtures._undo) + len(fixtures._redo))
        stable = (owner.values[LAYOUT_KEY], owner.values[FIXTURE_KEY])
        with patch.object(storage, "fixture_snapshot", side_effect=ValueError("invalid fixture")):
            with self.assertRaisesRegex(ValueError, "invalid fixture"):
                prepare_save(owner)
        self.assertIs(owner.values[LAYOUT_KEY], stable[0])
        self.assertIs(owner.values[FIXTURE_KEY], stable[1])
        bad = {**old_layout, "current": 42}
        with self.assertRaises(ValueError):
            restore_layout(bad)


if __name__ == "__main__":
    unittest.main()
