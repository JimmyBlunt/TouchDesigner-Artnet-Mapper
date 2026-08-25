import unittest

from pixelblaze_mapper.complete_side_rescan import NEW_TOTAL_POINTS
from pixelblaze_mapper.multi_controller import build_router_plan, default_router_config
from pixelblaze_mapper.spatial_map import build_side_spatial_map
from tools.artnet_complete_side_test import ROW_PALETTE, artdmx_packet, row_test_source


def spatial_coordinates():
    coordinates = [(0.0, 0.0, 0.0) for _ in range(NEW_TOTAL_POINTS)]
    for start, count in ((0, 517), (517, 269), (786, 398)):
        for offset in range(count):
            row, column = divmod(offset, 20)
            if row % 2:
                column = 19 - column
            # Middle and upper use direct X/Y; lower keeps the verified rotated
            # side-wall projection where source X is visible height.
            if start < 786:
                coordinates[start + offset] = (column * 0.02, row * 0.03, 0.0)
            else:
                coordinates[start + offset] = (row * 0.03, column * 0.02, 0.0)
    return tuple(coordinates)


class CompleteSideArtNetTestTests(unittest.TestCase):
    def test_only_the_new_side_prefix_is_colored(self):
        source = row_test_source(spatial_coordinates())
        self.assertTrue(any(pixel != (0.0, 0.0, 0.0) for pixel in source[:1184]))
        self.assertTrue(all(pixel == (0.0, 0.0, 0.0) for pixel in source[1184:]))

    def test_every_routed_side_pixel_is_non_black(self):
        source = row_test_source(spatial_coordinates())
        frames = build_router_plan(default_router_config("127.0.0.1")).pack_pixels(source)["WS2812_NODE"]
        # Controller ports reserve four whole 510-channel universe blocks.
        # Middle occupies wire U0..U3 (the last one has seven LEDs), upper is
        # U4..U5, U6..U7 are deliberately black, and lower is U8..U10.
        active_counts = (170, 170, 170, 7, 170, 99, 0, 0, 170, 170, 58)
        self.assertEqual(len(frames), len(active_counts))
        for frame, active_count in zip(frames, active_counts):
            pixels = tuple(tuple(frame[index:index + 3]) for index in range(0, 510, 3))
            self.assertTrue(all(pixel != (0, 0, 0) for pixel in pixels[:active_count]))
            self.assertTrue(all(pixel == (0, 0, 0) for pixel in pixels[active_count:]))

    def test_artdmx_packet_uses_compatibility_sequence_zero_and_exact_length(self):
        payload = bytes(range(255)) * 2
        packet = artdmx_packet(9, payload)
        self.assertEqual(packet[:8], b"Art-Net\x00")
        self.assertEqual(packet[8:12], b"\x00\x50\x00\x0e")
        self.assertEqual(packet[12:18], bytes((0, 0, 9, 0, 1, 254)))
        self.assertEqual(packet[18:], payload)

    def test_row_pattern_is_driven_by_spatial_lookup_not_wire_order(self):
        coordinates = spatial_coordinates()
        source = row_test_source(coordinates)
        panels = build_side_spatial_map(coordinates)
        for panel in panels:
            for led in panel.leds:
                self.assertEqual(source[led.index], ROW_PALETTE[led.row % 3])
        # The physical wire sequence is not treated as a fixed row width.
        self.assertTrue(any(
            panel.leds[offset + 1].row == panel.leds[offset].row
            for panel in panels
            for offset in range(len(panel.leds) - 1)
        ))
        self.assertTrue(any(
            panel.leds[offset + 1].row != panel.leds[offset].row
            for panel in panels
            for offset in range(len(panel.leds) - 1)
        ))


if __name__ == "__main__":
    unittest.main()
