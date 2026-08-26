import random
import unittest

from pixelblaze_mapper.multi_controller import (
    ControllerConfig,
    RouterConfig,
    SegmentConfig,
    build_router_plan,
    default_router_config,
)
from pixelblaze_mapper.realtime_packer import compile_router_packer


def channels(count=3744):
    rng = random.Random(7301)
    return tuple(tuple(rng.uniform(-0.1, 1.1) for _ in range(count)) for _ in range(3))


class RealtimePackerTests(unittest.TestCase):
    def assert_matches_reference(self, config, rgb):
        plan = build_router_plan(config)
        pixels = tuple(zip(*rgb))
        reference = plan.pack_pixels(pixels)
        actual = compile_router_packer(plan).pack_channels(*rgb)
        self.assertEqual(set(actual), set(reference))
        for name, frames in reference.items():
            self.assertEqual(actual[name], tuple(bytes(frame) for frame in frames))

    def test_default_topology_is_byte_identical(self):
        self.assert_matches_reference(default_router_config(), channels())

    def test_reverse_override_brightness_rounding_and_clamping_are_identical(self):
        config = RouterConfig(
            controllers=(
                ControllerConfig(
                    "A", "10.0.0.2", "10.0.0.1", color_order="GRB", brightness=0.37
                ),
            ),
            segments=(
                SegmentConfig("normal", 0, 173, "A", 0),
                SegmentConfig("reverse", 173, 9, "A", 180, reverse=True, color_override="BGR"),
            ),
            source_pixel_count=182,
            warn_unassigned=False,
        )
        self.assert_matches_reference(config, channels(182))

    def test_frames_are_exactly_510_bytes_and_reserved_ranges_stay_black(self):
        plan = build_router_plan(default_router_config())
        packed = compile_router_packer(plan).pack_channels(*channels())
        self.assertTrue(all(len(frame) == 510 for frames in packed.values() for frame in frames))
        ws = b"".join(packed["WS2812_NODE"])
        self.assertEqual(len(packed["WS2812_NODE"]), 12)
        self.assertEqual(ws[517 * 3 : 680 * 3], bytes((680 - 517) * 3))
        self.assertEqual(ws[(680 + 269) * 3 : 1360 * 3], bytes((1360 - 949) * 3))
        self.assertEqual(ws[(1360 + 398) * 3 : 2040 * 3], bytes((2040 - 1758) * 3))


if __name__ == "__main__":
    unittest.main()
