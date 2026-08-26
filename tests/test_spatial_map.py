import unittest

from pixelblaze_mapper.complete_side_rescan import NEW_TOTAL_POINTS
from pixelblaze_mapper.spatial_map import build_side_spatial_map, spatial_map_document


def synthetic_mapping():
    points = [(0.0, 0.0, 0.0) for _ in range(NEW_TOTAL_POINTS)]
    # Give all three panel ranges non-degenerate measured grids.  Wiring order
    # is deliberately serpentine to prove that geometry, not index order,
    # determines logical X/Y.
    ranges = ((0, 517), (517, 269), (786, 398))
    for start, count in ranges:
        width = 20
        for offset in range(count):
            row, column = divmod(offset, width)
            if row % 2:
                column = width - 1 - column
            points[start + offset] = (column * 0.02, row * 0.03, offset * 0.0001)
    return points


class SpatialMapTests(unittest.TestCase):
    def test_keeps_every_wire_index_and_exact_xyz(self):
        coordinates = synthetic_mapping()
        panels = build_side_spatial_map(coordinates)
        self.assertEqual(sum(panel.count for panel in panels), 1184)
        self.assertEqual([led.index for panel in panels for led in panel.leds], list(range(1184)))
        led = panels[0].leds[123]
        self.assertEqual((led.x, led.y, led.z), tuple(coordinates[123]))

    def test_document_contains_both_index_to_position_and_xy_to_indices(self):
        coordinates = synthetic_mapping()
        document = spatial_map_document(
            coordinates,
            "scan.json",
            measurement_coordinates=coordinates[:1184],
            estimated_indices={423, 1183},
        )
        self.assertFalse(document["wire_order_changed"])
        self.assertEqual(document["source"], "scan.json")
        first = document["panels"][0]
        self.assertEqual(len(first["leds"]), 517)
        self.assertTrue(first["xy_to_indices"])
        self.assertEqual(document["coordinate_quality"]["measured"], 1182)
        self.assertEqual(document["coordinate_quality"]["estimated"], 2)
        by_index = {
            led["index"]: led
            for panel in document["panels"]
            for led in panel["leds"]
        }
        self.assertEqual(by_index[423]["coordinate_quality"], "estimated")
        self.assertEqual(by_index[424]["coordinate_quality"], "measured")


if __name__ == "__main__":
    unittest.main()
