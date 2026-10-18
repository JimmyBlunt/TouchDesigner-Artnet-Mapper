import unittest

from tools.artnet_port_length_test import (
    build_frames,
    build_identity_frames,
    build_panel_identity_frames,
    build_one_universe_frames,
    wire_grb,
)


class PortLengthDiagnosticTests(unittest.TestCase):
    def test_builds_nine_exact_universes_with_declared_boundaries(self):
        frames = build_frames()
        self.assertEqual(tuple(universe for universe, _ in frames), tuple(range(0, 9)))
        self.assertTrue(all(len(payload) == 510 for _, payload in frames))

        pixels = []
        for _, payload in frames:
            pixels.extend(payload[index:index + 3] for index in range(0, 510, 3))
        red_grb = bytes((0, 20, 0))
        green_grb = bytes((20, 0, 0))

        for first, count, capacity in ((0, 517, 680), (680, 269, 340), (1020, 398, 510)):
            self.assertTrue(all(pixel == red_grb for pixel in pixels[first:first + count]))
            self.assertTrue(all(pixel == green_grb for pixel in pixels[first + count:first + capacity]))

    def test_identity_mode_uses_one_color_per_physical_port(self):
        frames = build_identity_frames()
        self.assertEqual(tuple(universe for universe, _ in frames), tuple(range(0, 9)))
        expected = (
            (range(0, 4), bytes((0, 20, 0))),
            (range(4, 6), bytes((20, 0, 0))),
            (range(6, 9), bytes((0, 0, 20))),
        )
        for indices, wire_color in expected:
            for index in indices:
                self.assertEqual(frames[index][1], wire_color * 170)

    def test_panel_identity_preserves_physical_port_boundaries(self):
        frames = build_panel_identity_frames()
        flat = b"".join(payload for _, payload in frames)
        pixels = [flat[index:index + 3] for index in range(0, len(flat), 3)]
        self.assertEqual(pixels[0], wire_grb((20, 0, 0)))
        self.assertEqual(pixels[509], wire_grb((20, 0, 0)))
        self.assertEqual(pixels[510], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[516], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[517], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[679], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[680], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[778], wire_grb((0, 20, 0)))
        self.assertEqual(pixels[779], wire_grb((0, 0, 0)))
        self.assertEqual(pixels[786], wire_grb((0, 0, 0)))
        self.assertEqual(pixels[1019], wire_grb((0, 0, 0)))
        self.assertEqual(pixels[1020], wire_grb((0, 0, 20)))
        self.assertEqual(pixels[1417], wire_grb((0, 0, 20)))
        self.assertEqual(pixels[1418], wire_grb((0, 0, 0)))

    def test_one_universe_blanks_every_other_frame(self):
        frames = build_one_universe_frames(5)
        self.assertEqual(tuple(universe for universe, _ in frames), tuple(range(0, 9)))
        for universe, payload in frames:
            expected = wire_grb((20, 20, 20)) if universe == 4 else wire_grb((0, 0, 0))
            self.assertEqual(payload, expected * 170)

        with self.assertRaises(ValueError):
            build_one_universe_frames(0)


if __name__ == "__main__":
    unittest.main()
