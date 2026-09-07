"""Behavioral adapter tests using a tiny TD boundary fake, NOT live UI tests."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import layout_fixture_td as fixture_ui, layout_scene_td as ui
from pixelblaze_mapper.fixture_scene import FixtureHistory, FixtureScene, Transform2D, project_fixture, replace_transform
from pixelblaze_mapper.layout_scene import Scene, Scan, Transform, append_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor, RouteBinding, scene_revision
from pixelblaze_mapper.layout_workspace import export_workspace, import_workspace


class Node:
    def __init__(self, text=""):
        self.text = text
        self.par = SimpleNamespace(text="", display=True, enable=True)
        self.panel = SimpleNamespace(u=.5, v=.5)
        self.cook = Mock()
        self.numRows = 1

    def __getitem__(self, key):
        return self.text


class Owner:
    def __init__(self, document):
        self.values = {"layout_editor_session": LayoutEditor(document)}
        paths = ["fixture_document", "draft_document", "instances", "fixture_output_instances", "fixture_uv_instances",
                 "ui_panel/status", "ui_panel/objects", "ui_panel/draft_badge", "ui_panel/provenance", "ui_panel/axes",
                 "ui_panel/viewport", "ui_panel/btn_transform"]
        for domain in ("output", "uv"):
            paths.extend("ui_panel/fixtures_" + domain + suffix for suffix in ("", "/info", "/viewport"))
        for name in [prefix + axis for prefix in "trs" for axis in "xyz"]:
            paths.extend(("ui_panel/" + name, "ui_panel/" + name + "/string"))
        self.nodes = {path: Node() for path in paths}
        for name, value in {"mode": "move", "step": ".1", "projection": "YX", "objectno": "1", "expectedcount": "", "controller": "", "port": "1"}.items():
            self.nodes["ui_panel/" + name + "/string"] = Node(value)

    def op(self, path):
        return self.nodes.get(path)

    def store(self, key, value):
        self.values[key] = value

    def fetch(self, key, default=None):
        return self.values.get(key, default)


def document():
    scene = append_scan(Scene("scene", "Room"), Scan("scan", "Original", ((0, 0, 0), (1, 2, 3))), source_start=0, object_id="one")
    return LayoutDocument(scene, (RouteBinding("one", "controller", 1),))


class FixtureAdapterTests(unittest.TestCase):
    def setUp(self):
        self.doc = document()
        self.owner = Owner(self.doc)
        self.choose = Mock(return_value=None)
        self.confirm = Mock(return_value=True)

    def project(self):
        ui.action(self.owner, "project2d", self.choose, self.confirm)
        self.assertNotIn("BLOCKED", self.owner.op("ui_panel/status").par.text)
        return fixture_ui.current(self.owner)

    def test_projection_mode_and_fit_never_edit_3d(self):
        model = self.project()
        original_output = model.fixtures[0].output_points()
        self.assertEqual(model.expected_count, 2)
        self.assertEqual(self.owner.fetch("layout_view"), "2d")
        self.assertFalse(self.owner.op("ui_panel/btn_transform").par.enable)
        ui.action(self.owner, "fituv", self.choose, self.confirm)
        changed = fixture_ui.current(self.owner)
        self.assertEqual(changed.fixtures[0].output_points(), original_output)
        self.assertNotEqual(changed.fixtures[0].uv_transform, model.fixtures[0].uv_transform)
        self.assertEqual(ui.editor(self.owner).current, self.doc)

    def test_keys_and_undo_are_domain_scoped(self):
        initial = self.project()
        ui.key(self.owner, "right")
        output = fixture_ui.current(self.owner)
        self.assertEqual(output.fixtures[0].output_transform.translation, (.1, 0))
        self.assertEqual(output.fixtures[0].uv_transform, initial.fixtures[0].uv_transform)
        self.owner.store("fixture_domain", "uv")
        ui.key(self.owner, "up")
        self.assertEqual(fixture_ui.current(self.owner).fixtures[0].uv_transform.translation, (0, .1))
        ui.action(self.owner, "undo", self.choose, self.confirm)
        self.assertEqual(fixture_ui.current(self.owner), output)
        self.assertEqual(ui.editor(self.owner).current, self.doc)

    def test_drag_preview_one_undo_and_escape(self):
        initial = self.project()
        viewport = self.owner.op("ui_panel/fixtures_output/viewport")
        fixture_ui.drag(self.owner, "output", "start")
        viewport.panel.u = .6
        fixture_ui.drag(self.owner, "output", "update")
        self.assertEqual(fixture_ui.history(self.owner).current, initial)
        self.assertNotEqual(fixture_ui.current(self.owner), initial)
        fixture_ui.drag(self.owner, "output", "end")
        self.assertNotEqual(fixture_ui.history(self.owner).current, initial)
        ui.key(self.owner, "z", ctrl=True)
        self.assertEqual(fixture_ui.current(self.owner), initial)
        fixture_ui.drag(self.owner, "output", "start")
        viewport.panel.u = .7
        fixture_ui.drag(self.owner, "output", "update")
        ui.key(self.owner, "escape")
        fixture_ui.drag(self.owner, "output", "update")
        fixture_ui.drag(self.owner, "output", "end")
        self.assertEqual(fixture_ui.current(self.owner), initial)

    def test_stale_geometry_export_rejected_before_file_dialog(self):
        self.project()
        ui.action(self.owner, "fituv", self.choose, self.confirm)
        ui.editor(self.owner).transform(Transform(translation=(1, 0, 0)))
        ui.action(self.owner, "exportuv", self.choose, self.confirm)
        self.assertIn("3D scene changed", self.owner.op("ui_panel/status").par.text)
        self.choose.assert_not_called()

    def test_partial_fixture_coverage_export_rejected(self):
        ui.editor(self.owner).append(Scan("other", "Other", ((.5, .5, .5),)), source_start=2, object_id="two")
        ui.editor(self.owner).select("one")
        self.project()
        ui.action(self.owner, "fituv", self.choose, self.confirm)
        ui.action(self.owner, "exportuv", self.choose, self.confirm)
        self.assertIn("coverage", self.owner.op("ui_panel/status").par.text)
        self.choose.assert_not_called()

    def test_stale_reset_requires_confirmation(self):
        original = self.project()
        ui.editor(self.owner).transform(Transform(translation=(1, 0, 0)))
        self.confirm.return_value = False
        ui.action(self.owner, "project2d", self.choose, self.confirm)
        self.assertEqual(fixture_ui.current(self.owner), original)
        self.confirm.assert_called_once()

    def test_configured_final_count_not_overridden_by_current_scene_length(self):
        session = ui.editor(self.owner)
        session.commit(replace(session.current, scene=replace(session.current.scene, expected_count=3744)))
        self.project()
        ui.action(self.owner, "fituv", self.choose, self.confirm)
        ui.action(self.owner, "exportuv", self.choose, self.confirm)
        self.assertIn("coverage", self.owner.op("ui_panel/status").par.text)
        self.choose.assert_not_called()

    def test_3d_numeric_transform_blocked_in_2d(self):
        self.project()
        ui.action(self.owner, "transform", self.choose, self.confirm)
        self.assertIn("only enabled in the 3D tab", self.owner.op("ui_panel/status").par.text)
        self.assertEqual(ui.editor(self.owner).current, self.doc)

    def test_load_active_snapshot_is_separate_from_file_dialog_and_invalidates_plan(self):
        from pixelblaze_mapper.layout_active_snapshot import snapshot_document
        snapshot, warnings = snapshot_document([("index", "tx", "ty", "tz"), ("0", "8", "9", "10")])
        self.owner.store("ui_prepared_context", ("3d", "YX", "old"))
        with patch("pixelblaze_mapper.layout_active_snapshot.read_active_snapshot", return_value=(snapshot, warnings)), patch.object(ui, "frame_view"):
            ui.action(self.owner, "loadactive", self.choose, self.confirm)
        self.choose.assert_not_called()
        self.assertEqual(ui.editor(self.owner).current, snapshot)
        self.assertEqual(fixture_ui.current(self.owner).expected_count, 1)
        self.assertIsNone(self.owner.fetch("ui_prepared_context"))
        self.assertIn("ACTIVE SNAPSHOT", self.owner.op("ui_panel/status").par.text)

    def test_failed_or_declined_snapshot_preserves_entire_draft(self):
        initial = self.project()
        self.confirm.return_value = False
        with patch("pixelblaze_mapper.layout_active_snapshot.read_active_snapshot") as reader:
            ui.action(self.owner, "loadactive", self.choose, self.confirm)
            reader.assert_not_called()
        self.confirm.return_value = True
        with patch("pixelblaze_mapper.layout_active_snapshot.read_active_snapshot", side_effect=ValueError("changed during snapshot")):
            ui.action(self.owner, "loadactive", self.choose, self.confirm)
        self.assertEqual(ui.editor(self.owner).current, self.doc)
        self.assertEqual(fixture_ui.current(self.owner), initial)

    def range(self, text):
        self.owner.nodes["ui_panel/fixturerange/string"] = Node(text)

    def test_multiple_disjoint_fixture_ranges_preserve_original_bindings(self):
        self.range("0")
        self.project()
        first = fixture_ui.selected(self.owner)
        ui.key(self.owner, "right")
        moved_first = fixture_ui.selected(self.owner)
        self.range("1")
        self.project()
        model = fixture_ui.current(self.owner)
        self.assertEqual(len(model.fixtures), 2)
        self.assertEqual(model.fixture(first.fixture_id), moved_first)
        self.assertEqual([led for f in model.fixtures for led in f.leds], list(self.doc.scene.objects[0].leds))
        self.assertEqual(ui.editor(self.owner).current, self.doc)
        self.assertNotEqual(model.fixtures[0].fixture_id, model.fixtures[1].fixture_id)

    def test_overlapping_whole_object_request_does_not_regroup_existing_ranges(self):
        self.range("0")
        initial = self.project()
        self.range("")
        ui.action(self.owner, "project2d", self.choose, self.confirm)
        self.assertIn("Overlapping", self.owner.op("ui_panel/status").par.text)
        self.assertEqual(fixture_ui.current(self.owner), initial)

    def test_exact_range_reprojection_keeps_fixture_id_and_other_fixture(self):
        self.range("0")
        self.project()
        first_id = fixture_ui.selected(self.owner).fixture_id
        self.range("1")
        self.project()
        other = fixture_ui.selected(self.owner)
        self.range("0")
        self.project()
        self.assertEqual(fixture_ui.selected(self.owner).fixture_id, first_id)
        self.assertEqual(fixture_ui.current(self.owner).fixture(other.fixture_id), other)
        self.confirm.assert_called_once()

    def test_hit_picking_keeps_individual_fixture_selection_with_same_object(self):
        self.range("0")
        self.project()
        first = fixture_ui.selected(self.owner)
        self.range("1")
        self.project()
        cx, cy, span = self.owner.fetch("fixture_output_frame")
        point = first.output_points()[0][1]
        fixture_ui._pick(self.owner, "output", ((point[0] - cx) / span + .5, (point[1] - cy) / span + .5))
        self.assertEqual(fixture_ui.selected(self.owner).fixture_id, first.fixture_id)
        ui.key(self.owner, "right")
        self.assertEqual(fixture_ui.current(self.owner).fixtures[1].output_transform.translation, (0, 0))

    def test_invalid_range_on_stale_source_preserves_existing_fixture_history(self):
        initial = self.project()
        ui.editor(self.owner).transform(Transform(translation=(1, 0, 0)))
        self.range("99")
        ui.action(self.owner, "project2d", self.choose, self.confirm)
        self.assertEqual(fixture_ui.current(self.owner), initial)
        self.confirm.assert_not_called()

    def test_pure_projection_subset_preserves_canonical_order_and_missing_mask(self):
        scene = append_scan(Scene("subset", "Subset"), Scan("scan-subset", "Original", ((0, 0, 0), (1, 2, 3), (4, 5, 6)), missing_indices=(1,)), source_start=0, object_id="subset-object")
        fixture = fixture_ui.project_selection(scene, "subset-object", local_indices=(2, 0))
        self.assertEqual([led.local_index for led in fixture.leds], [0, 2])
        self.assertEqual(fixture.missing_ids, ())
        self.assertEqual(fixture.leds, (scene.objects[0].leds[0], scene.objects[0].leds[2]))
        for indices in ((), (0, 0), (-1,), (3,)):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                fixture_ui.project_selection(scene, "subset-object", local_indices=indices)


class WorkspaceTests(unittest.TestCase):
    def test_full_workspace_roundtrip_both_transforms_routes_and_stale_state(self):
        doc = document()
        fixtures = FixtureScene(doc.scene.scene_id, scene_revision(doc.scene), (project_fixture(doc.scene, "one"),), 2)
        fixtures = replace_transform(fixtures, fixtures.fixtures[0].fixture_id, "output", Transform2D(translation=(5, 6), rotation=30))
        fixtures = replace_transform(fixtures, fixtures.fixtures[0].fixture_id, "uv", Transform2D(scale=(.1, .2)))
        self.assertEqual(import_workspace(export_workspace(doc, fixtures)), (doc, fixtures))
        stale = replace(fixtures, scene_revision="stale")
        self.assertEqual(import_workspace(export_workspace(doc, stale)), (doc, stale))

    def test_duplicate_keys_unknown_version_rejected(self):
        with self.assertRaises(ValueError):
            import_workspace('{"schema":"x","schema":"y"}')
        with self.assertRaises(ValueError):
            import_workspace('{"schema":"pixelblaze-layout-workspace","version":99}')

    def test_static_canvases_have_separate_render_and_keyboard_hooks(self):
        source = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_layout_scene_ui.py").read_text(encoding="utf-8")
        self.assertIn('_fixture_canvas(owner, panel, "output", 20)', source)
        self.assertIn('_fixture_canvas(owner, panel, "uv", 410)', source)
        self.assertIn('" ".join(v.path for v in fixture_views)', source)
        self.assertIn('"EXPORT WORKSPACE"', source)
        compile(source, "builder", "exec")

    def test_runtime_recovery_preserves_complete_workspace(self):
        doc = document()
        owner = Owner(doc)
        ui.action(owner, "project2d", Mock(), lambda _: True)
        ui.key(owner, "right")
        owner.store("fixture_domain", "uv")
        ui.key(owner, "up")
        before = export_workspace(ui.editor(owner).current, fixture_ui.history(owner).current)
        ui.refresh(owner)
        # Simulates Python module/session recovery from persistent DATs.
        owner.values = {}
        after = export_workspace(ui.editor(owner).current, fixture_ui.history(owner).current)
        self.assertEqual(after, before)


class ActiveBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.owner = Owner(document())
        self.owner.nodes["ui_panel/preserverouting/string"] = Node("NO")
        self.backend = SimpleNamespace(prepare=Mock(return_value=SimpleNamespace(workspace_revision="revision")), apply=Mock(), revert=Mock())
        self.owner.nodes["/project1/layout_apply/runtime"] = SimpleNamespace(module=self.backend)
        self.confirm = Mock(return_value=True)

    def action(self, name):
        ui.action(self.owner, name, Mock(), self.confirm)

    def test_missing_runtime_never_builds_or_applies(self):
        del self.owner.nodes["/project1/layout_apply/runtime"]
        self.action("prepare")
        self.assertIn("not installed", self.owner.op("ui_panel/status").par.text)
        self.backend.prepare.assert_not_called()

    def test_routing_opt_in_and_confirmation_both_required(self):
        self.action("prepare")
        self.backend.prepare.assert_not_called()
        self.owner.nodes["ui_panel/preserverouting/string"].text = "YES"
        self.confirm.return_value = False
        self.action("prepare")
        self.backend.prepare.assert_not_called()
        self.confirm.return_value = True
        self.action("prepare")
        self.backend.prepare.assert_called_once_with(mode="3d", projection="YX", preserve_routing=True)
        self.backend.apply.assert_not_called()

    def test_apply_requires_matching_tab_and_separate_confirmation(self):
        self.owner.nodes["ui_panel/preserverouting/string"].text = "YES"
        self.action("apply")
        self.backend.apply.assert_not_called()
        self.action("prepare")
        self.owner.store("layout_view", "2d")
        self.action("apply")
        self.backend.apply.assert_not_called()
        self.owner.store("layout_view", "3d")
        self.confirm.return_value = False
        self.action("apply")
        self.backend.apply.assert_not_called()
        self.confirm.return_value = True
        self.action("apply")
        self.backend.apply.assert_called_once()
        self.assertIsNone(self.owner.fetch("ui_prepared_context"))

    def test_output_off_error_is_visible_without_ui_sender_mutation(self):
        self.owner.nodes["ui_panel/preserverouting/string"].text = "YES"
        self.backend.prepare.side_effect = ValueError("Output must be OFF")
        self.action("prepare")
        self.assertIn("Output must be OFF", self.owner.op("ui_panel/status").par.text)
        self.backend.apply.assert_not_called()

    def test_revert_is_separate_and_keeps_draft(self):
        original = ui.editor(self.owner).current
        self.confirm.return_value = False
        self.action("revert")
        self.backend.revert.assert_not_called()
        self.confirm.return_value = True
        self.action("revert")
        self.backend.revert.assert_called_once()
        self.assertEqual(ui.editor(self.owner).current, original)

    def test_builder_revokes_consent_not_workspace(self):
        source = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_layout_scene_ui.py").read_text(encoding="utf-8")
        self.assertIn('opt_in.op("string").text = "NO"', source)
        self.assertIn('owner.store("ui_prepared_context", None)', source)
        self.assertNotIn('draft.text =', source)
        self.assertNotIn('store("fixture_history",', source)


if __name__ == "__main__":
    unittest.main()
