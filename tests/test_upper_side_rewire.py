import unittest

from pixelblaze_mapper.upper_side_rewire import (
    EXPECTED_NEW_POINTS,
    MISSING_HARDWARE_INDICES,
    TOTAL_POINTS,
    UPPER_HORIZONTAL_STEP,
    UPPER_HORIZONTAL_UNIT,
    UPPER_END,
    UPPER_RESERVED,
    UPPER_START,
    UPPER_VERTICAL_STEP,
    UPPER_VERTICAL_UNIT,
    replace_upper_panel,
    restore_scan_indices,
    scan_grid_coordinates,
)


def _grid_scan(count=EXPECTED_NEW_POINTS):
    result = []
    for index in range(count):
        row, column = divmod(index, 8)
        result.append(tuple(
            1.0
            + float(column) * UPPER_HORIZONTAL_STEP * UPPER_HORIZONTAL_UNIT[axis]
            + float(row) * UPPER_VERTICAL_STEP * UPPER_VERTICAL_UNIT[axis]
            for axis in range(3)
        ))
    return tuple(result)


def _sheared_grid_scan(count=EXPECTED_NEW_POINTS):
    result = []
    for index in range(count):
        row, column = divmod(index, 8)
        sheared_column = float(column) + 0.35 * row
        result.append(tuple(
            1.0
            + sheared_column * UPPER_HORIZONTAL_STEP * UPPER_HORIZONTAL_UNIT[axis]
            + float(row) * UPPER_VERTICAL_STEP * UPPER_VERTICAL_UNIT[axis]
            for axis in range(3)
        ))
    return tuple(result)


class UpperSideRewireTests(unittest.TestCase):
    def _mapping(self):
        points = [(index / TOTAL_POINTS, index / (TOTAL_POINTS * 2), 0.0) for index in range(TOTAL_POINTS)]
        points[UPPER_START + 10] = (0.0, 0.0, 0.0)
        return tuple(points)

    def test_only_upper_reserved_slice_changes(self):
        current = self._mapping()
        result, report = replace_upper_panel(current, _grid_scan())
        self.assertEqual(result[:UPPER_START], current[:UPPER_START])
        self.assertEqual(result[UPPER_END:], current[UPPER_END:])
        self.assertEqual(len(result), TOTAL_POINTS)
        self.assertEqual(report.padding_points, UPPER_RESERVED - EXPECTED_NEW_POINTS)
        self.assertEqual(report.hardware_trailing_black, 2)
        self.assertEqual(result[UPPER_END - 2:UPPER_END], ((0.0, 0.0, 0.0),) * 2)

    def test_exported_scan_restores_two_missing_first_tile_leds(self):
        result, report = replace_upper_panel(self._mapping(), _grid_scan(EXPECTED_NEW_POINTS - 2))
        self.assertEqual(report.source_points, 268)
        self.assertEqual(MISSING_HARDWARE_INDICES, (62, 63))
        self.assertEqual(report.inserted_points, 2)
        self.assertEqual(report.discarded_points, 0)
        self.assertEqual(report.appended_points, 0)
        self.assertEqual(report.estimated_points, 2)
        self.assertNotEqual(result[UPPER_START], (0.0, 0.0, 0.0))
        self.assertNotEqual(result[UPPER_START + 2], (0.0, 0.0, 0.0))

    def test_restored_export_inserts_hardware_62_and_63(self):
        exported = _grid_scan(EXPECTED_NEW_POINTS - 2)
        restored = restore_scan_indices(exported)
        self.assertEqual(restored[:62], exported[:62])
        self.assertEqual(restored[62:64], ((0.0, 0.0, 0.0),) * 2)
        self.assertEqual(restored[64], exported[62])
        self.assertEqual(restored[269], exported[267])

    def test_mounted_upper_panel_keeps_the_new_scan_axes(self):
        result, _ = replace_upper_panel(self._mapping(), _grid_scan())
        self.assertLess(result[UPPER_START][0], result[UPPER_START + 1][0])
        self.assertLess(result[UPPER_START][1], result[UPPER_START + 8][1])

    def test_calibrated_whole_panel_axes_keep_rows_horizontal(self):
        grid = scan_grid_coordinates(_grid_scan())
        self.assertAlmostEqual(grid[0][0], grid[8][0], places=9)
        result, _ = replace_upper_panel(self._mapping(), _grid_scan())
        self.assertAlmostEqual(result[UPPER_START][0], result[UPPER_START + 8][0], places=9)
        self.assertLess(result[UPPER_START][1], result[UPPER_START + 8][1])

    def test_oversize_scan_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected"):
            replace_upper_panel(self._mapping(), _grid_scan(EXPECTED_NEW_POINTS + 1))


if __name__ == "__main__":
    unittest.main()
