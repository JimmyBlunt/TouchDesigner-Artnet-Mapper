import unittest

from pixelblaze_mapper.router_calibration import (
    STRIPE_PALETTE,
    calibration_source,
    load_coordinates,
    load_measurement_coordinates,
)
from pixelblaze_mapper.spatial_map import build_side_spatial_map


class RouterCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These tests intentionally use the production Pixelblaze scan.  A
        # fabricated rectangular grid would not exercise the measured 3D
        # projection and could hide exactly the mapping errors we are testing.
        cls.coordinates = load_coordinates()
        cls.measurements = load_measurement_coordinates()
        cls.panels = {
            panel.name: panel
            for panel in build_side_spatial_map(
                cls.coordinates, measurement_coordinates=cls.measurements
            )
        }

    def calibration(self, **kwargs):
        return calibration_source(
            self.coordinates,
            measurement_coordinates=self.measurements,
            **kwargs,
        )

    def test_panel_identification_uses_expected_physical_ranges(self):
        source = self.calibration(pattern="panel_id")
        self.assertEqual(source[0], (1.0, 0.0, 0.0))
        self.assertEqual(source[517], (0.0, 1.0, 0.0))
        self.assertEqual(source[786], (0.0, 0.0, 1.0))
        self.assertEqual(source[1184], (0.0, 0.0, 0.0))

    def test_panel_filter_blacks_every_other_panel(self):
        source = self.calibration(panel="upper", pattern="panel_id")
        self.assertEqual(source[0], (0.0, 0.0, 0.0))
        self.assertEqual(source[517], (0.0, 1.0, 0.0))
        self.assertEqual(source[786], (0.0, 0.0, 0.0))

    def test_rows_and_columns_are_derived_per_measured_led(self):
        rows = self.calibration(panel="middle", pattern="rows")
        columns = self.calibration(panel="middle", pattern="columns")
        for led in self.panels["middle"].leds:
            self.assertEqual(rows[led.index], STRIPE_PALETTE[led.row % 3])
            self.assertEqual(columns[led.index], STRIPE_PALETTE[led.column % 3])

    def test_chase_is_bounded_and_index_exact(self):
        source = self.calibration(panel="middle", pattern="chase", chase_index=100)
        self.assertEqual(source[100], (0.0, 1.0, 0.0))
        self.assertEqual(source[99], (1.0, 1.0, 1.0))
        self.assertEqual(source[104], (0.0, 0.0, 0.0))

    def test_columns_follow_raw_scanner_x_for_every_panel(self):
        # The lower panel was previously transposed because cabinet-aligned UV
        # coordinates were used.  Physical columns must instead follow the X
        # axis measured by the complete Pixelblaze scan for all three panels.
        for panel in self.panels.values():
            xs = [self.measurements[led.index][0] for led in panel.leds]
            columns = [led.column for led in panel.leds]
            mean_x = sum(xs) / len(xs)
            mean_column = sum(columns) / len(columns)
            covariance = sum(
                (x - mean_x) * (column - mean_column)
                for x, column in zip(xs, columns)
            )
            self.assertGreater(abs(covariance), 1.0, panel.name)


if __name__ == "__main__":
    unittest.main()
