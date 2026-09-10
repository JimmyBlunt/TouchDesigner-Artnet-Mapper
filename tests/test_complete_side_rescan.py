import unittest

from pixelblaze_mapper.complete_side_rescan import (
    LOWER_COUNT,
    MIDDLE_COUNT,
    NEW_REAR_START,
    NEW_TOTAL_POINTS,
    OLD_REAR_START,
    OLD_TOTAL_POINTS,
    UPPER_COUNT,
    rebuild_complete_side_mapping,
)


class CompleteSideRescanTests(unittest.TestCase):
    def _current(self):
        side = [(0.1 + i / 5000, 0.2 + i / 4000, 0.0) for i in range(OLD_REAR_START)]
        rear = [(0.5, 1.0, 0.5 + i / 10000) for i in range(OLD_TOTAL_POINTS - OLD_REAR_START)]
        return tuple(side + rear)

    def _scan(self):
        points = []
        for count in (MIDDLE_COUNT, UPPER_COUNT, LOWER_COUNT - 1):
            for index in range(count):
                row, column = divmod(index, 16)
                points.append((float(column), float(row), 2.0 + 0.01 * column))
        return tuple(points)

    def test_rebuild_uses_new_boundaries_and_preserves_rear(self):
        current = self._current()
        result, report = rebuild_complete_side_mapping(current, self._scan())
        self.assertEqual(len(result), NEW_TOTAL_POINTS)
        self.assertEqual(result[NEW_REAR_START:], current[OLD_REAR_START:])
        self.assertEqual(report.appended_points, 1)
        self.assertEqual(report.rear_range, "1184..3743")

    def test_missing_and_gross_outlier_points_are_estimated(self):
        scan = list(self._scan())
        scan[10] = (0.0, 0.0, 0.0)
        scan[30] = (1000.0, 1000.0, 1000.0)
        result, report = rebuild_complete_side_mapping(self._current(), scan)
        self.assertEqual(len(result), NEW_TOTAL_POINTS)
        self.assertIn(30, report.rejected_outlier_indices)
        self.assertGreaterEqual(report.estimated_points, 3)


if __name__ == "__main__":
    unittest.main()
