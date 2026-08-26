"""Non-destructive regression checks for shortcut dialog 5: Pixel Mapper.

The tests deliberately avoid TouchDesigner UI automation and never write a map.
They validate the canonical production artefacts and the safety contract used by
the dialog.  Supervised click/import/export/apply tests are documented separately.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pixelblaze_mapper import td_controller
from pixelblaze_mapper.mapper_io import (
    export_marimapper_csv,
    export_pixelblaze_json,
    import_marimapper_csv,
    import_pixelblaze,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MAP = ROOT / "mappings" / "mapping_complete_new_0_1183_full_2026-08-24.json"
SPATIAL_MAP = ROOT / "mappings" / "side_spatial_lookup_complete_new_2026-08-24.json"
RESCAN_REPORT = ROOT / "mappings" / "complete_new_0_1183_report.json"


class PixelMapperDialogRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coordinates = json.loads(CANONICAL_MAP.read_text(encoding="utf-8"))
        cls.spatial = json.loads(SPATIAL_MAP.read_text(encoding="utf-8"))
        cls.report = json.loads(RESCAN_REPORT.read_text(encoding="utf-8"))

    def test_dialog_and_output_share_the_3744_pixel_contract(self):
        self.assertEqual(td_controller.EXPECTED_PIXELS, 3744)
        self.assertEqual(len(self.coordinates), 3744)
        self.assertEqual(self.report["output_points"], 3744)

    def test_hardware_panel_boundaries_are_contiguous_and_complete(self):
        self.assertEqual(self.report["middle_range"], "0..516")
        self.assertEqual(self.report["upper_range"], "517..785")
        self.assertEqual(self.report["lower_range"], "786..1183")
        self.assertEqual(self.report["rear_range"], "1184..3743")
        self.assertEqual(517 + 269 + 398 + 2560, 3744)

    def test_spatial_lookup_preserves_every_side_wire_index(self):
        self.assertFalse(self.spatial["wire_order_changed"])
        panels = self.spatial["panels"]
        self.assertEqual(
            [(p["name"], p["source_start"], p["count"]) for p in panels],
            [("middle", 0, 517), ("upper", 517, 269), ("lower", 786, 398)],
        )
        indices = [led["index"] for panel in panels for led in panel["leds"]]
        self.assertEqual(indices, list(range(1184)))

    def test_canonical_map_is_finite_three_dimensional_data(self):
        for point in self.coordinates:
            self.assertEqual(len(point), 3)
            self.assertTrue(all(isinstance(value, (int, float)) for value in point))
            self.assertTrue(all(value == value and abs(value) != float("inf") for value in point))

    def test_pixelblaze_round_trip_preserves_count_and_coordinates(self):
        mapping = import_pixelblaze(CANONICAL_MAP)
        exported = export_pixelblaze_json(mapping)
        restored = import_pixelblaze(exported)
        self.assertEqual(len(restored.coordinates), 3744)
        self.assertEqual(restored.coordinates, mapping.coordinates)

    def test_marimapper_round_trip_preserves_count_and_coordinates(self):
        mapping = import_pixelblaze(CANONICAL_MAP)
        exported = export_marimapper_csv(mapping)
        restored = import_marimapper_csv(exported)
        self.assertEqual(len(restored.coordinates), 3744)
        self.assertEqual(restored.coordinates, mapping.coordinates)


if __name__ == "__main__":
    unittest.main()
