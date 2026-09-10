import unittest

from pixelblaze_mapper.lower_side_rewire import (
    EXPECTED_NEW_POINTS,
    LOWER_RESERVED,
    LOWER_START,
    REAR_START,
    TOTAL_POINTS,
    estimate_missing_points,
    replace_lower_panel,
)


class LowerSideRewireTests(unittest.TestCase):
    def test_only_reserved_lower_slice_changes(self):
        current = tuple((index / TOTAL_POINTS, index / (TOTAL_POINTS * 2), 0.0) for index in range(TOTAL_POINTS))
        scan = tuple((float(index + 1), 2.0, float(EXPECTED_NEW_POINTS - index)) for index in range(EXPECTED_NEW_POINTS))
        result, report = replace_lower_panel(current, scan)
        self.assertEqual(result[:LOWER_START], current[:LOWER_START])
        self.assertEqual(result[REAR_START:], current[REAR_START:])
        self.assertEqual(len(result), TOTAL_POINTS)
        self.assertEqual(LOWER_START + EXPECTED_NEW_POINTS, REAR_START)
        self.assertEqual(report.padding_points, LOWER_RESERVED - EXPECTED_NEW_POINTS)
        self.assertEqual(report.hardware_trailing_black, 3)

    def test_missing_scan_points_are_interpolated(self):
        current = tuple((index / TOTAL_POINTS, index / TOTAL_POINTS, 0.0) for index in range(TOTAL_POINTS))
        scan = [(float(index + 1), 1.0, float(index + 2)) for index in range(EXPECTED_NEW_POINTS)]
        scan[17] = (0.0, 0.0, 0.0)
        result, report = replace_lower_panel(current, scan)
        self.assertNotEqual(result[LOWER_START + 17], (0.0, 0.0, 0.0))
        self.assertEqual(report.source_missing, 1)
        self.assertEqual(report.estimated_points, 1)

    def test_internal_gap_and_trailing_points_follow_index_path(self):
        points = (
            (0.0, 1.0, 1.0),
            (1.0, 2.0, 2.0),
            (0.0, 0.0, 0.0),
            (3.0, 4.0, 4.0),
            (0.0, 0.0, 0.0),
        )
        estimated = estimate_missing_points(points)
        self.assertEqual(estimated[2], (2.0, 3.0, 3.0))
        self.assertEqual(estimated[4], (4.0, 5.0, 5.0))

    def test_short_scan_is_extended_to_index_398(self):
        current = tuple((index / TOTAL_POINTS, index / TOTAL_POINTS, 0.0) for index in range(TOTAL_POINTS))
        scan = tuple((float(index + 1), 1.0, float(index + 2)) for index in range(EXPECTED_NEW_POINTS - 2))
        result, report = replace_lower_panel(current, scan)
        self.assertEqual(len(result), TOTAL_POINTS)
        self.assertEqual(report.appended_points, 2)
        self.assertEqual(report.estimated_points, 2)
        self.assertNotEqual(result[REAR_START - 1], (0.0, 0.0, 0.0))

    def test_new_index_order_controls_coordinate_order(self):
        current = tuple((index / TOTAL_POINTS, index / TOTAL_POINTS, 0.0) for index in range(TOTAL_POINTS))
        scan = tuple((float(index + 1), 0.0, float(index + 2)) for index in range(EXPECTED_NEW_POINTS))
        reversed_scan = tuple(reversed(scan))
        forward, _ = replace_lower_panel(current, scan)
        backward, _ = replace_lower_panel(current, reversed_scan)
        self.assertEqual(forward[LOWER_START], backward[LOWER_START + EXPECTED_NEW_POINTS - 1])

    def test_oversize_scan_is_rejected(self):
        current = ((0.1, 0.1, 0.0),) * TOTAL_POINTS
        with self.assertRaisesRegex(ValueError, str(EXPECTED_NEW_POINTS)):
            replace_lower_panel(current, ((1.0, 2.0, 3.0),) * (EXPECTED_NEW_POINTS + 1))


if __name__ == "__main__":
    unittest.main()
