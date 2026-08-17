import csv
import io
import json
import unittest
from pathlib import Path

from pixelblaze_mapper import (
    GeneratorExecutionUnavailable,
    MappingData,
    MappingFormatError,
    PixelblazeGenerator,
    export_marimapper_csv,
    export_pixelblaze_js,
    export_pixelblaze_json,
    import_marimapper_csv,
    import_pixelblaze,
    materialize_pixelblaze_generator,
    normalize_coordinates,
    place_upright_sidewall_range,
    rotate_mapping_range_90,
)


FIXTURES = Path(__file__).with_name("fixtures")


class RotationTests(unittest.TestCase):
    def test_rotates_only_inclusive_range_without_reindexing(self):
        mapping = MappingData(
            ((0.1, 0.2, 0.3), (0.4, 0.25, 0.75), (0.9, 0.8, 0.7)),
            3,
            "fixture",
        )
        rotated = rotate_mapping_range_90(mapping, 1, 1, axis="x", turns=1)
        self.assertEqual(rotated.coordinates[0], mapping.coordinates[0])
        self.assertEqual(rotated.coordinates[1], (0.4, 0.25, 0.25))
        self.assertEqual(rotated.coordinates[2], mapping.coordinates[2])
        self.assertEqual(len(rotated.coordinates), len(mapping.coordinates))

    def test_four_quarter_turns_restore_coordinates(self):
        mapping = MappingData(((0.2, 0.3, 0.4),), 3, "fixture")
        rotated = rotate_mapping_range_90(mapping, 0, 0, axis="x", turns=4)
        self.assertEqual(rotated.coordinates, mapping.coordinates)

    def test_rejects_invalid_range_and_non_3d_mapping(self):
        mapping = MappingData(((0.2, 0.3, 0.4),), 3, "fixture")
        with self.assertRaises(MappingFormatError):
            rotate_mapping_range_90(mapping, 0, 1)
        mapping_2d = MappingData(((0.2, 0.3),), 2, "fixture")
        with self.assertRaises(MappingFormatError):
            rotate_mapping_range_90(mapping_2d, 0, 0)

    def test_places_sidewall_in_zy_without_reindexing_panels(self):
        mapping = MappingData(
            ((0.2, 0.25, 0.1), (0.8, 0.75, 0.9), (0.4, 0.5, 1.0)),
            3,
            "fixture",
        )
        placed = place_upright_sidewall_range(
            mapping, 0, 1, wall_x=0.94, normal_depth=0.04
        )
        for actual, expected in zip(placed.coordinates[0], (0.93, 0.9, 0.2)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(placed.coordinates[1], (0.95, 0.1, 0.8)):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(placed.coordinates[2], mapping.coordinates[2])

    def test_sidewall_placement_preserves_missing_origin_slot(self):
        mapping = MappingData(
            ((0.0, 0.0, 0.0), (0.2, 0.3, 0.4)),
            3,
            "fixture",
            missing_indices=(0,),
        )
        placed = place_upright_sidewall_range(mapping, 0, 1)
        self.assertEqual(placed.coordinates[0], (0.0, 0.0, 0.0))

    def test_real_3714_map_matches_reference_room_layout(self):
        source = (
            Path(__file__).parents[1]
            / "mappings"
            / "backups"
            / "mapping_before_sidewall_upright_x90.json"
        )
        original = import_pixelblaze(source)
        placed = place_upright_sidewall_range(
            original, 0, 1153, wall_x=0.94, normal_depth=0.04
        )
        self.assertEqual(len(placed.coordinates), 3714)
        self.assertEqual(placed.coordinates[1154:], original.coordinates[1154:])

        side = placed.coordinates[:1154]
        self.assertAlmostEqual(min(point[0] for point in side), 0.92)
        self.assertAlmostEqual(max(point[0] for point in side), 0.96)
        self.assertAlmostEqual(min(point[1] for point in side), 0.0)
        self.assertAlmostEqual(max(point[1] for point in side), 1.0)
        self.assertAlmostEqual(min(point[2] for point in side), 0.0)
        self.assertAlmostEqual(max(point[2] for point in side), 1.0)

        bottom = side[503:886]
        middle = side[0:503]
        top = side[886:1154]
        centroid = lambda points, axis: sum(p[axis] for p in points) / len(points)
        self.assertLess(centroid(bottom, 1), centroid(middle, 1))
        self.assertLess(centroid(middle, 1), centroid(top, 1))
        self.assertLess(centroid(bottom, 2), centroid(middle, 2))
        self.assertLess(centroid(middle, 2), centroid(top, 2))

        for panel in range(10):
            start = 1154 + panel * 256
            points = placed.coordinates[start : start + 256]
            pixel_zero = points[0]
            self.assertAlmostEqual(pixel_zero[0], max(p[0] for p in points))
            self.assertAlmostEqual(pixel_zero[1], min(p[1] for p in points))
            self.assertTrue(all(abs(p[2] - 1.0) < 1e-12 for p in points))


class PixelblazeImportTests(unittest.TestCase):
    def test_json5_style_comments_and_trailing_commas(self):
        mapping = import_pixelblaze(
            """[
              [0, 1, 2], // first LED
              [3.5, 4, 5,], /* trailing coordinate comma */
            ]"""
        )
        self.assertEqual(mapping.dimensions, 3)
        self.assertEqual(mapping.coordinates, ((0.0, 1.0, 2.0), (3.5, 4.0, 5.0)))

    def test_rejects_mixed_dimensions_and_non_finite_values(self):
        with self.assertRaisesRegex(MappingFormatError, "mix"):
            import_pixelblaze("[[0,1],[0,1,2]]")
        with self.assertRaises(MappingFormatError):
            import_pixelblaze("[[0, 1, 1e999]]")

    def test_generator_is_preserved_and_not_executed(self):
        source = (FIXTURES / "pixelblaze_generator.js").read_text(encoding="utf-8")
        generator = import_pixelblaze(source)
        self.assertIsInstance(generator, PixelblazeGenerator)
        self.assertFalse(generator.can_execute)
        self.assertEqual(export_pixelblaze_js(generator), source)
        with self.assertRaises(GeneratorExecutionUnavailable):
            generator.materialize()

    def test_arbitrary_expression_is_not_evaluated(self):
        with self.assertRaises(MappingFormatError):
            import_pixelblaze("__import__('os').system('bad')")

    def test_generator_can_be_materialized_by_opt_in_node_adapter(self):
        source = "function(pixelCount) { return Array.from({length: pixelCount}, (_, i) => [i, i/2, 0]); }"
        generator = import_pixelblaze(source)
        self.assertIsInstance(generator, PixelblazeGenerator)
        try:
            mapping = materialize_pixelblaze_generator(generator, 4)
        except GeneratorExecutionUnavailable:
            self.skipTest("Node.js is not installed")
        self.assertEqual(mapping.coordinates[-1], (3.0, 1.5, 0.0))
        self.assertEqual(mapping.source_format, "pixelblaze-js-materialized")

    def test_path_loading_is_explicit_and_text_is_never_guessed_as_a_path(self):
        fixture = FIXTURES / "pixelblaze_generator.js"
        generator = import_pixelblaze(fixture)
        self.assertIsInstance(generator, PixelblazeGenerator)
        with self.assertRaises(MappingFormatError):
            import_pixelblaze(str(fixture))


class MariMapperImportTests(unittest.TestCase):
    def test_orders_by_index_inserts_gaps_and_preserves_metadata(self):
        mapping = import_marimapper_csv(
            "index,x,y,z,xn,yn,zn,error\n"
            "2,2,20,200,.2,.2,.2,\n"
            "0,0,0,0,.0,.0,.0,good\n"
        )
        self.assertEqual(mapping.coordinates, ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (2.0, 20.0, 200.0)))
        self.assertEqual(mapping.missing_indices, (1,))
        self.assertIn("1 missing", mapping.warnings[0])
        self.assertEqual(mapping.row_metadata[2]["xn"], ".2")

    def test_rejects_duplicate_negative_and_non_finite_indices_or_values(self):
        invalid_cases = (
            "index,x,y,z\n0,0,0,0\n0,1,1,1\n",
            "index,x,y,z\n-1,0,0,0\n",
            "index,x,y,z\n0,nan,0,0\n",
            "index,x,y,z\n0,inf,0,0\n",
        )
        for text in invalid_cases:
            with self.subTest(text=text), self.assertRaises(MappingFormatError):
                import_marimapper_csv(text)

    def test_accepts_touchdesigner_t_axis_alias(self):
        mapping = import_marimapper_csv("index,tx,ty,tz\n0,1,2,3\n")
        self.assertEqual(mapping.coordinates, ((1.0, 2.0, 3.0),))

    def test_ballsmatrix3_index_characteristic(self):
        mapping = import_marimapper_csv(FIXTURES / "ballsmatrix3_normalized.csv")
        self.assertEqual(len(mapping.coordinates), 938)
        self.assertEqual(mapping.missing_indices, (894, 895, 896))
        self.assertEqual(len(mapping.coordinates) - len(mapping.missing_indices), 935)
        for index in mapping.missing_indices:
            self.assertEqual(mapping.coordinates[index], (0.0, 0.0, 0.0))
        self.assertIn("894-896", mapping.warnings[0])


class ExportAndNormalizationTests(unittest.TestCase):
    def test_pixelblaze_export_is_coordinate_array_only(self):
        mapping = import_marimapper_csv("index,x,y,z,error\n0,1,2,3,note\n")
        exported = export_pixelblaze_json(mapping)
        self.assertEqual(json.loads(exported), [[1.0, 2.0, 3.0]])
        self.assertNotIn("error", exported)
        self.assertNotIn("source", exported)

    def test_marimapper_round_trip_keeps_coordinates_and_metadata(self):
        original = import_marimapper_csv(
            "index,x,y,z,xn,error\n1,1.25,-2,3,.4,ok\n0,9,8,7,.8,fine\n"
        )
        exported = export_marimapper_csv(original)
        restored = import_marimapper_csv(exported)
        self.assertEqual(restored.coordinates, original.coordinates)
        self.assertEqual(restored.row_metadata, original.row_metadata)

    def test_fill_and_contain_are_derived_without_mutating_raw(self):
        raw = ((10.0, 20.0, 3.0), (20.0, 60.0, 3.0))
        fill = normalize_coordinates(raw, "fill")
        contain = normalize_coordinates(raw, "contain")
        self.assertEqual(raw, ((10.0, 20.0, 3.0), (20.0, 60.0, 3.0)))
        self.assertEqual(fill, ((0.0, 0.0, 0.5), (1.0, 1.0, 0.5)))
        self.assertEqual(contain, ((0.375, 0.0, 0.5), (0.625, 1.0, 0.5)))

    def test_two_dimensional_mapping_is_consistent_and_csv_gets_zero_z(self):
        mapping = import_pixelblaze("[[0,0],[1,1]]")
        csv_text = export_marimapper_csv(mapping)
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        self.assertEqual(rows[1]["z"], "0")


if __name__ == "__main__":
    unittest.main()
