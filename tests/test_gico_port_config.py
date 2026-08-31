import unittest

from pixelblaze_mapper.gico_port_config import (
    CHANNELS_PER_UNIVERSE,
    PIXELS_PER_UNIVERSE,
    GicoConfig,
    GicoConfigError,
    GicoPortConfig,
    build_gico_plan,
    validate_gico_config,
)


class GicoPortBlockTests(unittest.TestCase):
    def test_six_universes_create_fixed_1020_pixel_blocks(self):
        config = GicoConfig(
            universes_per_port=6,
            ports=tuple(GicoPortConfig(number) for number in range(1, 5)),
        )
        plan = build_gico_plan(config)

        self.assertEqual(CHANNELS_PER_UNIVERSE, 510)
        self.assertEqual(PIXELS_PER_UNIVERSE, 170)
        self.assertEqual(plan.reserved_universes, 24)
        self.assertEqual(
            [
                (
                    item.config.port,
                    item.start_universe,
                    item.end_universe,
                    item.destination_pixel_start,
                    item.capacity_pixels,
                )
                for item in plan.ports
            ],
            [
                (1, 1, 6, 0, 1020),
                (2, 7, 12, 1020, 1020),
                (3, 13, 18, 2040, 1020),
                (4, 19, 24, 3060, 1020),
            ],
        )

    def test_port_four_can_describe_896_pixels_without_inventing_a_source(self):
        config = GicoConfig(
            universes_per_port=6,
            ports=(
                GicoPortConfig(
                    4,
                    label="Port 4",
                    enabled=True,
                    source_start=None,
                    pixel_count=896,
                    reverse=True,
                    color_order="GRB",
                ),
            ),
        )
        plan = build_gico_plan(config)
        port = plan.port(4)

        self.assertEqual((port.start_universe, port.end_universe), (19, 24))
        self.assertEqual((port.destination_pixel_start, port.capacity_pixels), (3060, 1020))
        self.assertEqual(port.config.pixel_count, 896)
        self.assertIsNone(port.config.source_start)
        self.assertIsNone(port.source_end_exclusive)
        self.assertFalse(port.has_source_assignment)
        self.assertFalse(port.routable)
        self.assertEqual(
            [issue.code for issue in plan.issues],
            ["source_unassigned"],
        )
        self.assertFalse(plan.blocking)

    def test_assigned_enabled_port_is_routable(self):
        port = GicoPortConfig(2, enabled=True, source_start=517, pixel_count=269)
        item = build_gico_plan(GicoConfig(6, (port,))).port(2)
        self.assertTrue(item.routable)
        self.assertEqual(item.source_end_exclusive, 786)


class GicoValidationTests(unittest.TestCase):
    def codes(self, config):
        return {issue.code for issue in validate_gico_config(config)}

    def test_rejects_nonpositive_global_values(self):
        for config in (
            GicoConfig(0, ()),
            GicoConfig(-1, ()),
            GicoConfig(6, (), first_universe=0),
        ):
            with self.subTest(config=config):
                self.assertTrue(any(issue.blocking for issue in validate_gico_config(config)))
                with self.assertRaises(GicoConfigError):
                    build_gico_plan(config)

    def test_rejects_capacity_overflow_and_negative_ranges(self):
        config = GicoConfig(
            6,
            (
                GicoPortConfig(1, source_start=-1, pixel_count=1021),
                GicoPortConfig(0, source_start=0, pixel_count=-1),
            ),
        )
        codes = self.codes(config)
        self.assertTrue({"port_capacity", "source_start", "port", "pixel_count"}.issubset(codes))
        with self.assertRaises(GicoConfigError):
            build_gico_plan(config)

    def test_rejects_duplicate_ports_flags_and_color_order(self):
        config = GicoConfig(
            6,
            (
                GicoPortConfig(1),
                GicoPortConfig(1, enabled=1, reverse=1, color_order="RGBW"),  # type: ignore[arg-type]
            ),
        )
        self.assertTrue(
            {"duplicate_port", "enabled", "reverse", "color_order"}.issubset(self.codes(config))
        )

    def test_rejects_overlapping_enabled_source_ranges(self):
        config = GicoConfig(
            6,
            (
                GicoPortConfig(1, enabled=True, source_start=0, pixel_count=517),
                GicoPortConfig(2, enabled=True, source_start=500, pixel_count=269),
            ),
        )
        self.assertIn("source_overlap", self.codes(config))
        with self.assertRaises(GicoConfigError):
            build_gico_plan(config)

    def test_disabled_drafts_do_not_create_live_source_overlap(self):
        config = GicoConfig(
            6,
            (
                GicoPortConfig(1, enabled=True, source_start=0, pixel_count=517),
                GicoPortConfig(2, enabled=False, source_start=500, pixel_count=269),
            ),
        )
        self.assertNotIn("source_overlap", self.codes(config))
        self.assertFalse(build_gico_plan(config).blocking)


if __name__ == "__main__":
    unittest.main()
