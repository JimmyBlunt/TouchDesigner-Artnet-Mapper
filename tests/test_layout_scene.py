"""Offline data-model tests: no TD/UI, active-map writes, or network access."""

from dataclasses import FrozenInstanceError, replace
import json
import unittest
from unittest.mock import Mock

from pixelblaze_mapper.layout_scene import (
    LedBinding, Scan, Scene, SceneError, SceneHistory, SceneObject, Transform,
    append_scan, export_pixelblaze_3d, export_scene_json, import_scan,
    import_scene_json, replace_region, set_transform,
)
from pixelblaze_mapper.mapper_io import GeneratorExecutionUnavailable, MappingData, MappingFormatError


def scan(id="scan-a", points=((1, 0, 0), (0, 1, 0)), **kwargs):
    return Scan(id, id, points, **kwargs)


def scene():
    return append_scan(Scene("scene", "Room"), scan(), source_start=0, object_id="object-a")


class TransformTests(unittest.TestCase):
    def assertPoint(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=10)

    def test_right_handed_axes(self):
        self.assertPoint(Transform(rotation_degrees=(90, 0, 0)).apply((0, 1, 0)), (0, 0, 1))
        self.assertPoint(Transform(rotation_degrees=(0, 90, 0)).apply((1, 0, 0)), (0, 0, -1))
        self.assertPoint(Transform(rotation_degrees=(0, 0, 90)).apply((1, 0, 0)), (0, 1, 0))

    def test_order_is_scale_then_xyz_rotation_then_translation_about_pivot(self):
        t = Transform(translation=(5, 6, 7), rotation_degrees=(90, 90, 90),
                      scale=(2, 3, 4), pivot=(1, 1, 1))
        self.assertPoint(t.apply((2, 2, 2)), (10, 10, 6))

    def test_pivot_is_fixed_without_translation(self):
        t = Transform(rotation_degrees=(90, 12, 44), scale=(4, -1, 2), pivot=(1, 2, 3))
        self.assertPoint(t.apply((1, 2, 3)), (1, 2, 3))

    def test_original_and_identities_immutable(self):
        original = scene()
        transformed = set_transform(original, "object-a", Transform(translation=(5, 0, 0)))
        self.assertEqual(original.scans[0].points, ((1, 0, 0), (0, 1, 0)))
        self.assertIs(original.scans[0], transformed.scans[0])
        self.assertEqual(original.objects[0].leds, transformed.objects[0].leds)
        self.assertEqual(transformed.world_points()[0][1], (6, 0, 0))
        with self.assertRaises(FrozenInstanceError):
            original.scans[0].name = "changed"

    def test_mutable_arguments_are_snapshotted(self):
        points, translation = [[1, 2, 3]], [2, 3, 4]
        s = scan(points=points)
        t = Transform(translation=translation)
        points[0][0], translation[0] = 100, 100
        self.assertEqual(s.points, ((1, 2, 3),))
        self.assertEqual(t.translation, (2, 3, 4))

    def test_finite_nonzero_transform_validation(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(SceneError):
                Transform(translation=(value, 0, 0))
        with self.assertRaises(SceneError):
            Transform(scale=(1, 0, 1))
        with self.assertRaises(SceneError):
            set_transform(scene(), "object-a", Transform(scale=(1e308, 1e308, 1e308), translation=(1e308, 0, 0)))


class ImportTests(unittest.TestCase):
    def test_pixelblaze_2d_and_3d(self):
        a = import_scan("[[1,2],[3,4]]", format="pixelblaze", name="A", scan_id="a")
        self.assertEqual(a.points, ((1, 2, 0), (3, 4, 0)))
        b = import_scan("[[1,2,3], // comment\n]", format="pixelblaze-json", name="B")
        self.assertEqual(b.points, ((1, 2, 3),))

    def test_csv_local_indices_metadata_missing(self):
        a = import_scan("index,x,y,z,error\n2,1,2,3,0.02\n0,4,5,6,0.01\n",
                        format="marimapper-csv", name="CSV")
        self.assertEqual(a.points, ((4, 5, 6), (0, 0, 0), (1, 2, 3)))
        self.assertEqual(a.missing_indices, (1,))
        self.assertEqual(dict(a.row_metadata[2]), {"error": "0.02"})
        draft = append_scan(Scene("s", "S"), a, source_start=0)
        with self.assertRaisesRegex(SceneError, "missing"):
            export_pixelblaze_3d(draft)
        self.assertEqual(import_scene_json(export_scene_json(draft)), draft)

    def test_unknown_mari_json_is_not_guessed(self):
        for format in ("marimapper-json", "other"):
            with self.subTest(format=format), self.assertRaises(MappingFormatError):
                import_scan('{"points":[[1,2,3]]}', format=format, name="Unknown")

    def test_verified_mari_plain_json_array_supported_without_brand_guessing(self):
        value = import_scan("[[1,2,3],[4,5,6]]", format="marimapper-json", name="AllExported")
        self.assertEqual(value.points, ((1, 2, 3), (4, 5, 6)))
        self.assertEqual(value.source_format, "marimapper-json-array")
        for unsupported in ("[[1,2]]", "function(pixelCount) { return [[1,2,3]]; }"):
            with self.assertRaises(MappingFormatError):
                import_scan(unsupported, format="marimapper-json", name="bad")

    def test_duplicate_csv_rows_rejected(self):
        with self.assertRaises(MappingFormatError):
            import_scan("index,x,y,z\n0,1,2,3\n0,4,5,6\n", format="marimapper-csv", name="bad")

    def test_generators_never_execute_by_default(self):
        js = "function(pixelCount) { return [[1,2,3]]; }"
        with self.assertRaises(GeneratorExecutionUnavailable):
            import_scan(js, format="pixelblaze-generator", name="JS")

    def test_explicit_generator_materializer_and_count(self):
        js = "function(pixelCount) { return [[1,2,3]]; }"
        materializer = Mock(return_value=MappingData(((1, 2, 3),), 3, "trusted-result"))
        a = import_scan(js, format="pixelblaze", name="JS", generator_count=1,
                        generator_materializer=materializer)
        self.assertEqual(a.generator_source, js)
        self.assertEqual(materializer.call_args.args[1], 1)
        self.assertEqual(a.points, ((1, 2, 3),))
        with self.assertRaisesRegex(SceneError, "count"):
            import_scan(js, format="pixelblaze", name="JS", generator_count=2,
                        generator_materializer=materializer)
        materializer.reset_mock()
        with self.assertRaises(SceneError):
            import_scan(js, format="pixelblaze", name="JS", generator_materializer=materializer)
        materializer.assert_not_called()

    def test_empty_nonfinite_boolean_points_rejected(self):
        for data in ("[]", "[[true,0,0]]", "[[1e999,0,0]]"):
            with self.subTest(data=data), self.assertRaises((SceneError, MappingFormatError)):
                import_scan(data, format="pixelblaze", name="bad")


class SceneIdentityTests(unittest.TestCase):
    def test_append_requires_explicit_global_ownership(self):
        base = Scene("s", "S")
        with self.assertRaises(SceneError):
            append_scan(base, scan())
        with self.assertRaises(SceneError):
            append_scan(base, scan(), source_start=0, source_indices=(0, 1))
        with self.assertRaises(SceneError):
            append_scan(base, scan(), source_indices=(0,))

    def test_cumulative_append_does_not_modify_previous_object(self):
        old = scene()
        new = append_scan(old, scan("scan-b"), source_start=2, object_id="object-b")
        self.assertIs(new.objects[0], old.objects[0])
        self.assertEqual([v.source_index for o in new.objects for v in o.leds], [0, 1, 2, 3])
        self.assertEqual(len(json.loads(export_pixelblaze_3d(new))), 4)

    def test_overlap_duplicate_object_and_modified_scan_rejected(self):
        old = scene()
        for kwargs in ({"source_start": 1}, {"source_start": 2, "object_id": "object-a"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SceneError):
                append_scan(old, scan("scan-b"), **kwargs)
        with self.assertRaisesRegex(SceneError, "immutable"):
            append_scan(old, scan("scan-a", ((9, 9, 9),)), source_start=2)

    def test_coincident_coordinates_are_allowed_not_index_overlap(self):
        a = scan(points=((1, 1, 1), (1, 1, 1)))
        draft = append_scan(Scene("s", "S"), a, source_start=0)
        self.assertEqual(json.loads(export_pixelblaze_3d(draft)), [[1, 1, 1], [1, 1, 1]])

    def test_sparse_indices_cannot_be_silently_renumbered(self):
        draft = append_scan(Scene("s", "S"), scan(), source_indices=(10, 20))
        with self.assertRaisesRegex(SceneError, "renumber"):
            export_pixelblaze_3d(draft)
        restored = import_scene_json(export_scene_json(draft))
        self.assertEqual([v.source_index for v in restored.objects[0].leds], [10, 20])

    def test_output_is_global_index_order_not_object_or_local_order(self):
        draft = append_scan(Scene("s", "S"), scan(), source_indices=(1, 0))
        self.assertEqual(json.loads(export_pixelblaze_3d(draft)), [[0, 1, 0], [1, 0, 0]])

    def test_absolute_csv_indices_explicit_selection_does_not_create_phantom_leds(self):
        source = import_scan("index,x,y,z\n517,1,2,3\n518,4,5,6\n", format="marimapper-csv", name="Upper")
        draft = append_scan(Scene("s", "S"), source, scan_indices=(517, 518), source_indices=(517, 518))
        self.assertEqual(len(draft.objects[0].leds), 2)
        self.assertEqual([(v.local_index, v.source_index, v.scan_index) for v in draft.objects[0].leds],
                         [(0, 517, 517), (1, 518, 518)])
        self.assertEqual(source.points[517], (1, 2, 3))

    def test_bad_append_selection_fails(self):
        for selection in ((0, 0), (9,), (), (True,)):
            with self.subTest(selection=selection), self.assertRaises(SceneError):
                append_scan(Scene("s", "S"), scan(), scan_indices=selection, source_start=0)

    def test_final_expected_count_does_not_block_partial_drafts(self):
        draft = append_scan(Scene("s", "S", expected_count=4), scan(), source_start=0)
        with self.assertRaisesRegex(SceneError, "expected 4"):
            export_pixelblaze_3d(draft)
        complete = append_scan(draft, scan("b"), source_start=2)
        complete.validate_output()

    def test_full_installation_partial_rescan_preserves_all_unselected_global_ids(self):
        points = tuple((i / 3743, 0.5, 0.25) for i in range(3744))
        original = append_scan(Scene("s", "Installation", expected_count=3744),
                               scan(points=points), source_start=0, object_id="installation")
        updated = replace_region(original, "installation", (517, 785, 1183),
                                 scan("partial", ((0.1, 0.2, 0.3),) * 3))
        original_leds, updated_leds = original.objects[0].leds, updated.objects[0].leds
        for index in range(3744):
            self.assertEqual(original_leds[index].led_id, updated_leds[index].led_id)
            self.assertEqual(updated_leds[index].source_index, index)
            if index not in {517, 785, 1183}:
                self.assertIs(original_leds[index], updated_leds[index])
        exported = json.loads(export_pixelblaze_3d(updated))
        self.assertEqual(len(exported), 3744)
        self.assertEqual(exported[1184], list(points[1184]))

    def test_explicit_empty_ids_are_not_silently_replaced(self):
        with self.assertRaises(SceneError):
            import_scan("[[1,2,3]]", format="pixelblaze", name="S", scan_id="")
        with self.assertRaises(SceneError):
            append_scan(Scene("s", "S"), scan(), source_start=0, object_id="")

    def test_unknown_scan_reference_and_duplicate_identity_rejected(self):
        old = scene()
        led = old.objects[0].leds[0]
        with self.assertRaises(SceneError):
            replace(old, objects=(SceneObject("o", "O", (replace(led, scan_id="absent"),)),))
        with self.assertRaises(SceneError):
            replace(old, objects=(old.objects[0], SceneObject("other", "Other", (replace(led, source_index=3),))))


class RescanHistoryTests(unittest.TestCase):
    def test_partial_rescan_preserves_ids_other_leds_and_transform(self):
        old = append_scan(scene(), scan("b"), source_start=2, object_id="object-b")
        old = set_transform(old, "object-a", Transform(translation=(10, 0, 0)))
        candidate = scan("rescan", ((9, 8, 7),))
        updated = replace_region(old, "object-a", (1,), candidate)
        a, b = old.objects[0], updated.objects[0]
        self.assertEqual([(v.led_id, v.local_index, v.source_index) for v in a.leds],
                         [(v.led_id, v.local_index, v.source_index) for v in b.leds])
        self.assertIs(a.leds[0], b.leds[0])
        self.assertIs(updated.objects[1], old.objects[1])
        self.assertEqual(a.transform, b.transform)
        self.assertEqual(updated.world_points()[1][1], (19, 8, 7))
        self.assertEqual(updated.scans[:2], old.scans)

    def test_explicit_pairing_not_nearest_neighbor_or_source_offset(self):
        updated = replace_region(scene(), "object-a", (1, 0), scan("b", ((10, 0, 0), (20, 0, 0))))
        self.assertEqual([p for _, p in updated.world_points()], [(20, 0, 0), (10, 0, 0)])

    def test_subset_of_candidate_scan_with_anchors_excluded(self):
        candidate = scan("b", ((100, 0, 0), (4, 5, 6), (200, 0, 0)))
        updated = replace_region(scene(), "object-a", (0,), candidate, scan_indices=(1,))
        self.assertEqual(updated.world_points()[0][1], (4, 5, 6))
        self.assertEqual(len(updated.objects[0].leds), 2)

    def test_registered_rescan_preserves_raw_scan_and_composes_with_object_transform(self):
        original = set_transform(scene(), "object-a", Transform(translation=(10, 0, 0)))
        raw = scan("rescan", ((1, 2, 3),), registration=Transform(translation=(-1, 0, 0), scale=(2, 2, 2)))
        updated = replace_region(original, "object-a", (0,), raw)
        self.assertEqual(updated.world_points()[0][1], (11, 4, 6))
        self.assertEqual(raw.points, ((1, 2, 3),))
        self.assertEqual(import_scene_json(export_scene_json(updated)), updated)

    def test_bad_selection_is_rejected_without_mutating_original(self):
        old = scene()
        snapshot = export_scene_json(old)
        for local, incoming in (((0, 1), None), ((4,), None), ((0, 0), (0, 0)), ((True,), None), ((0,), (5,))):
            with self.subTest(local=local), self.assertRaises(SceneError):
                replace_region(old, "object-a", local, scan("b", ((2, 3, 4),)), scan_indices=incoming)
        self.assertEqual(export_scene_json(old), snapshot)

    def test_rescan_can_resolve_missing_without_index_change(self):
        old = append_scan(Scene("s", "S"), scan(missing_indices=(1,)), source_start=0, object_id="a")
        updated = replace_region(old, "a", (1,), scan("b", ((9, 0, 0),)))
        updated.validate_output()
        self.assertEqual(updated.scans[0].missing_indices, (1,))

    def test_undo_redo_of_append_transform_and_partial_rescan(self):
        history = SceneHistory(Scene("s", "S"))
        states = [history.current]
        history.commit(append_scan(history.current, scan(), source_start=0, object_id="a"))
        states.append(history.current)
        history.commit(set_transform(history.current, "a", Transform(translation=(1, 2, 3))))
        states.append(history.current)
        history.commit(replace_region(history.current, "a", (0,), scan("b", ((9, 9, 9),))))
        states.append(history.current)
        for expected in reversed(states[:-1]):
            self.assertIs(history.undo(), expected)
        self.assertFalse(history.can_undo)
        for expected in states[1:]:
            self.assertIs(history.redo(), expected)
        self.assertFalse(history.can_redo)

    def test_new_edit_clears_redo_noop_does_not(self):
        h = SceneHistory(scene())
        h.commit(set_transform(h.current, "object-a", Transform(translation=(1, 0, 0))))
        h.undo()
        h.commit(h.current)
        self.assertTrue(h.can_redo)
        h.commit(set_transform(h.current, "object-a", Transform(translation=(2, 0, 0))))
        self.assertFalse(h.can_redo)

    def test_history_rejects_rewriting_originals_or_renumbering_identity(self):
        h = SceneHistory(scene())
        original = h.current
        changed_scan = replace(original.scans[0], points=((9, 9, 9), (8, 8, 8)))
        with self.assertRaisesRegex(SceneError, "original"):
            h.commit(replace(original, scans=(changed_scan,)))
        obj = original.objects[0]
        changed_obj = replace(obj, leds=(replace(obj.leds[0], source_index=4), obj.leds[1]))
        with self.assertRaisesRegex(SceneError, "identity"):
            h.commit(replace(original, objects=(changed_obj,)))
        self.assertIs(h.current, original)
        self.assertFalse(h.can_undo)


class SerializationTests(unittest.TestCase):
    def test_roundtrip_retains_archived_scans_ids_metadata_and_transform(self):
        old = scene()
        changed = replace_region(old, "object-a", (0,), scan("b", ((3, 4, 5),)))
        changed = set_transform(changed, "object-a", Transform(rotation_degrees=(12, 23, 34)))
        restored = import_scene_json(export_scene_json(changed))
        self.assertEqual(restored, changed)
        self.assertEqual(export_pixelblaze_3d(restored), export_pixelblaze_3d(changed))

    def test_unknown_schema_extra_fields_and_duplicate_json_keys_fail(self):
        data = json.loads(export_scene_json(scene()))
        for edit in ({"version": 2}, {"version": True}, {"schema": "marimapper"}, {"extra": 1}):
            with self.subTest(edit=edit), self.assertRaises(SceneError):
                import_scene_json(json.dumps({**data, **edit}))
        with self.assertRaisesRegex(SceneError, "duplicate JSON"):
            import_scene_json('{"version":1,"version":1}')
        with self.assertRaises(SceneError):
            import_scene_json("not json")

    def test_invalid_nested_transform_and_reference_fail(self):
        data = json.loads(export_scene_json(scene()))
        data["objects"][0]["transform"]["scale"][0] = 0
        with self.assertRaises(SceneError):
            import_scene_json(json.dumps(data))
        data = json.loads(export_scene_json(scene()))
        data["objects"][0]["leds"][0]["scan_index"] = 99
        with self.assertRaises(SceneError):
            import_scene_json(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
