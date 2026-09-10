"""Real pure-editor behavior plus explicitly labelled static TD contracts."""
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import Mock
from types import SimpleNamespace

from pixelblaze_mapper.layout_scene import Scene, Scan, SceneError, Transform, append_scan
from pixelblaze_mapper.layout_scene_adapter import (
    LayoutDocument, LayoutEditor, RouteBinding, prepare_transaction, apply_prepared,
    scene_revision, document_json, load_document_json, parse_indices, user_to_td,
    object_color, nudge,
)
from pixelblaze_mapper.scan_session import MergeRequest, Replacement
from pixelblaze_mapper.build_layout_scene_ui import RUNTIME, _only_led_shape


def document():
    scene = append_scan(Scene("scene", "Room"), Scan("scan", "Original", ((1, 2, 3), (4, 5, 6))),
                        source_start=0, object_id="object")
    return LayoutDocument(scene, (RouteBinding("object", "controller-a", 1),))


class EditorBehaviorTests(unittest.TestCase):
    def test_route_and_transform_undo_redo_together(self):
        editor = LayoutEditor(document())
        original = editor.current
        editor.transform(Transform(translation=(1, 2, 3)))
        transformed = editor.current
        editor.bind_route("controller-b", 3)
        self.assertEqual(editor.current.routes[0].port, 3)
        self.assertEqual(editor.undo(), transformed)
        self.assertEqual(editor.undo(), original)
        editor.redo()
        editor.redo()
        self.assertEqual(editor.current.routes[0].controller, "controller-b")

    def test_drag_preview_one_undo_step_and_cancellation(self):
        editor = LayoutEditor(document())
        original = editor.current
        for x in (1, 2, 3):
            editor.transform(Transform(translation=(x, 0, 0)), preview=True)
        self.assertIs(editor.current, original)
        self.assertNotEqual(editor.display_scene, original.scene)
        editor.finish_gesture()
        self.assertEqual(editor.current.scene.objects[0].transform.translation, (3, 0, 0))
        self.assertEqual(editor.undo(), original)
        editor.transform(Transform(translation=(9, 0, 0)), preview=True)
        editor.cancel_gesture()
        self.assertEqual(editor.display_scene, original.scene)

    def test_append_and_selection(self):
        editor = LayoutEditor(document())
        editor.append(Scan("new", "New", ((8, 8, 8),)), source_start=2, object_id="other")
        self.assertEqual(editor.selected_object_id, "other")
        editor.undo()
        self.assertEqual(editor.selected_object_id, "object")
        with self.assertRaises(SceneError):
            editor.select("missing")

    def test_explicit_range_parsing(self):
        self.assertEqual(parse_indices("0-2, 5, 9-10"), (0, 1, 2, 5, 9, 10))
        self.assertEqual(parse_indices(""), ())
        for text in ("0-2,2", "-1", "5-2", "a", "0-2000000"):
            with self.subTest(text=text), self.assertRaises(SceneError):
                parse_indices(text)

    def test_roundtrip_route_intent_and_scene(self):
        doc = document()
        self.assertEqual(load_document_json(document_json(doc)), doc)
        with self.assertRaises(SceneError):
            LayoutDocument(doc.scene, (RouteBinding("unknown", "controller", 1),))

    def test_axes_mapping_is_only_display_and_nudge_preserves_other_axes(self):
        self.assertEqual(user_to_td((1, 2, 3)), (2, 1, -3))
        transform = nudge(Transform(), "up", step=.2)
        transform = nudge(transform, "right", step=.3)
        transform = nudge(transform, "pageup", step=.4)
        self.assertEqual(transform.translation, (.2, .3, .4))
        self.assertEqual(nudge(Transform(), "right", mode="rotate", axis="x", step=90).rotation_degrees, (90, 0, 0))
        with self.assertRaises(SceneError):
            nudge(Transform(), "right", step=float("nan"))

    def test_object_colors_are_stable_and_bright(self):
        self.assertEqual(object_color("a"), object_color("a"))
        self.assertNotEqual(object_color("a"), object_color("b"))
        self.assertTrue(all(.25 <= v <= .95 for v in object_color("a")))

    def test_scan_handoff_requires_revision_identity_and_evidence(self):
        editor = LayoutEditor(document())
        led = editor.current.scene.objects[0].leds[1]
        request = MergeRequest("session", "scene", scene_revision(editor.current.scene), "newscan",
                               (Replacement(led.led_id, "object", 1, 1, 0),), "registration.json", "quality.json")
        scan = Scan("newscan", "Rescan", ((8, 9, 10),), registration=Transform(translation=(1, 0, 0)))
        original = editor.current
        editor.accept_scan_request(request, scan)
        self.assertEqual(editor.current.scene.world_points()[1][1], (9, 9, 10))
        self.assertEqual(editor.undo(), original)
        for invalid in (replace(request, expected_scene_revision="stale"), replace(request, registration_reference=""),
                        replace(request, replacements=(replace(request.replacements[0], source_index=99),)),
                        replace(request, replacements=())):
            with self.subTest(invalid=invalid), self.assertRaises(SceneError):
                editor.accept_scan_request(invalid, scan)
        self.assertEqual(editor.current, original)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.doc = document()
        self.plan = prepare_transaction(self.doc, base_active_hash="baseline")
        self.calls = []
        self.kwargs = dict(
            document=self.doc, read_active_hash=lambda: "baseline",
            capture_snapshot=lambda: {"active": "old"},
            write_coordinates=lambda value: self.calls.append("coordinates"),
            write_routes=lambda routes: self.calls.append("routes"),
            verify_applied=lambda plan: True,
            restore_snapshot=lambda snapshot: self.calls.append(("rollback", snapshot)),
        )

    def test_preparation_does_not_apply_and_requires_routes_and_baseline(self):
        self.assertFalse(self.plan.changes_active_output)
        with self.assertRaises(SceneError):
            prepare_transaction(LayoutDocument(self.doc.scene), base_active_hash="baseline")
        with self.assertRaises(SceneError):
            prepare_transaction(self.doc, base_active_hash="")
        self.assertEqual(self.calls, [])

    def test_injected_success_transaction(self):
        apply_prepared(self.plan, **self.kwargs)
        self.assertEqual(self.calls, ["coordinates", "routes"])

    def test_failure_restores_full_caller_snapshot(self):
        self.kwargs["write_routes"] = Mock(side_effect=RuntimeError("route failure"))
        with self.assertRaisesRegex(SceneError, "rolled back"):
            apply_prepared(self.plan, **self.kwargs)
        self.assertEqual(self.calls, ["coordinates", ("rollback", {"active": "old"})])

    def test_verification_failure_rolls_back(self):
        self.kwargs["verify_applied"] = lambda plan: False
        with self.assertRaises(SceneError):
            apply_prepared(self.plan, **self.kwargs)
        self.assertEqual(self.calls[-1], ("rollback", {"active": "old"}))

    def test_stale_active_draft_and_tampered_payload_rejected_before_writers(self):
        for plan, kwargs in (
            (self.plan, {**self.kwargs, "read_active_hash": lambda: "changed"}),
            (replace(self.plan, draft_revision="stale"), self.kwargs),
            (replace(self.plan, coordinates_json="[[99,99,99]]"), self.kwargs),
        ):
            with self.assertRaises(SceneError):
                apply_prepared(plan, **kwargs)
        self.assertEqual(self.calls, [])

    def test_changed_during_snapshot_does_not_clobber_concurrent_change(self):
        self.kwargs["read_active_hash"] = Mock(side_effect=["baseline", "changed"])
        with self.assertRaisesRegex(SceneError, "no writers"):
            apply_prepared(self.plan, **self.kwargs)
        self.assertEqual(self.calls, [])

    def test_rollback_failure_is_not_hidden(self):
        self.kwargs["write_coordinates"] = Mock(side_effect=RuntimeError("write"))
        self.kwargs["restore_snapshot"] = Mock(side_effect=RuntimeError("restore"))
        with self.assertRaisesRegex(SceneError, "ROLLBACK FAILED"):
            apply_prepared(self.plan, **self.kwargs)


class StaticTouchDesignerContracts(unittest.TestCase):
    """These tests are NOT live UI, GPU or keyboard end-to-end checks."""
    def test_runtime_compiles_and_no_builder_autorun(self):
        compile(RUNTIME, "layout-runtime", "exec")
        root = Path(__file__).parents[1] / "pixelblaze_mapper"
        source = (root / "build_layout_scene_ui.py").read_text(encoding="utf-8")
        self.assertNotIn("\nprint(build(", source)
        self.assertNotIn("project.save", source)
        self.assertIn('"VALIDATE / PREPARE"', source)
        self.assertIn('keys.par.panels = viewport.path', source)
        self.assertIn('("buttontype", "momentary")', source)
        self.assertIn('callback.par.panelvalue = "lselect"', source)
        self.assertIn('_set(callback, "whileon", False)', source)
        self.assertNotIn('callback.par.panelvalue = "state"', source)

    def test_runtime_delegates_only_to_explicit_apply_boundary(self):
        source = (Path(__file__).parents[1] / "pixelblaze_mapper" / "layout_scene_td.py").read_text(encoding="utf-8")
        self.assertNotIn("apply_prepared(", source)
        self.assertNotIn("outputConnectors", source)
        self.assertNotIn("send_bytes", source)
        self.assertIn('owner.op("/project1/layout_apply/runtime")', source)
        self.assertIn('runtime.module.prepare(mode=mode, projection=projection, preserve_routing=True, uv_source=uv_source)', source)
        self.assertIn('field(owner, "preserverouting").upper() != "YES"', source)


class GeometryDrawingBoundaryTests(unittest.TestCase):
    """Real flag-helper behavior using boundary fakes, not GPU render tests."""
    def test_default_torus_disabled_and_owned_shape_enabled_without_deletion(self):
        for name in ("led_geometry", "fixture_output_geometry", "fixture_uv_geometry"):
            with self.subTest(geometry=name):
                torus = SimpleNamespace(name="torus1", display=True, render=True, data="default torus preserved")
                custom = SimpleNamespace(name="custom", display=True, render=True, data="user geometry preserved")
                dat = SimpleNamespace(name="notes", text="untouched")
                shape = SimpleNamespace(name="led_shape", display=False, render=False)
                children = [torus, custom, dat, shape]
                geometry = SimpleNamespace(name=name, children=children)
                _only_led_shape(geometry, shape)
                _only_led_shape(geometry, shape)  # Rebuild is idempotent.
                self.assertFalse(torus.display or torus.render)
                self.assertFalse(custom.display or custom.render)
                self.assertTrue(shape.display and shape.render)
                self.assertIs(geometry.children, children)
                self.assertEqual(torus.data, "default torus preserved")
                self.assertEqual(custom.data, "user geometry preserved")
                self.assertEqual(dat.text, "untouched")

    def test_foreign_shape_rejected_before_flags_change(self):
        torus = SimpleNamespace(name="torus1", display=True, render=True)
        shape = SimpleNamespace(name="led_shape", display=False, render=False)
        with self.assertRaises(RuntimeError):
            _only_led_shape(SimpleNamespace(children=[torus]), shape)
        self.assertTrue(torus.display and torus.render)

    def test_builder_uses_exclusive_shape_for_3d_and_shared_2d_factory(self):
        source = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_layout_scene_ui.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("    _only_led_shape(geometry, shape)"), 2)
        self.assertIn('_fixture_canvas(owner, panel, "output", 20)', source)
        self.assertIn('_fixture_canvas(owner, panel, "uv", 410)', source)


if __name__ == "__main__":
    unittest.main()
