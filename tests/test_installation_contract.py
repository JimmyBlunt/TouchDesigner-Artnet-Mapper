import math
import unittest

from pixelblaze_mapper.installation_contract import (
    BLACK_UI_UNIVERSES,
    BLACK_WIRE_UNIVERSES,
    LOWER,
    MIDDLE,
    MISSING_ACTIVE_POLICY,
    MISSING_DRAFT_RENDER,
    PANELS,
    REAR,
    SIDE_PANELS,
    TOTAL_PIXELS,
    UPPER,
    panel_for_index,
    validate_mapping,
)
from pixelblaze_mapper.build_led_preview_contract import (
    COUNT_MARKER,
    MISSING_MARKER,
    patch_callback_source,
)


def coordinates(count=TOTAL_PIXELS):
    return tuple((float(index), 0.0, 0.0) for index in range(count))


class InstallationContractTests(unittest.TestCase):
    def test_panel_ranges_are_contiguous_and_cover_every_led(self):
        self.assertEqual(
            [(panel.name, panel.start, panel.last, panel.count) for panel in PANELS],
            [
                ("middle", 0, 516, 517),
                ("upper", 517, 785, 269),
                ("lower", 786, 1183, 398),
                ("rear", 1184, 3743, 2560),
            ],
        )
        self.assertEqual(sum(panel.count for panel in PANELS), TOTAL_PIXELS)

    def test_side_ports_reserve_four_universes_each(self):
        self.assertEqual(
            [(panel.port, panel.ui_universes) for panel in SIDE_PANELS],
            [(1, (1, 2, 3, 4)), (2, (5, 6, 7, 8)), (3, (9, 10, 11, 12))],
        )
        self.assertEqual(MIDDLE.active_ui_universes, (1, 2, 3, 4))
        self.assertEqual(UPPER.active_ui_universes, (5, 6))
        self.assertEqual(LOWER.active_ui_universes, (9, 10, 11))
        self.assertEqual(BLACK_UI_UNIVERSES, (7, 8, 12))
        self.assertEqual(BLACK_WIRE_UNIVERSES, (6, 7, 11))

    def test_reserved_tail_is_explicitly_black_not_reassigned(self):
        self.assertEqual(
            [panel.trailing_black_pixels for panel in SIDE_PANELS],
            [163, 411, 282],
        )

    def test_boundary_lookup_never_crosses_panels(self):
        for index, expected in ((0, MIDDLE), (516, MIDDLE), (517, UPPER), (785, UPPER),
                                (786, LOWER), (1183, LOWER), (1184, REAR), (3743, REAR)):
            self.assertIs(panel_for_index(index), expected)
        for invalid in (-1, TOTAL_PIXELS, True):
            with self.assertRaises(IndexError):
                panel_for_index(invalid)

    def test_draft_missing_indices_keep_count_and_render_black(self):
        quality = validate_mapping(coordinates(), (7, 517, 3743), active=False)
        self.assertTrue(quality.valid)
        self.assertEqual(quality.missing_indices, (7, 517, 3743))
        self.assertEqual(MISSING_DRAFT_RENDER, "black")

    def test_active_missing_indices_are_rejected(self):
        self.assertEqual(MISSING_ACTIVE_POLICY, "reject")
        with self.assertRaisesRegex(ValueError, "missing LED indices"):
            validate_mapping(coordinates(), (500,), active=True)

    def test_wrong_count_and_invalid_coordinates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected 3744"):
            validate_mapping(coordinates(TOTAL_PIXELS - 1), active=False)
        invalid = list(coordinates())
        invalid[12] = (math.nan, 0.0, 0.0)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_mapping(invalid, active=False)

    def test_preview_callback_patch_guards_count_and_blacks_missing_leds(self):
        original = (
            "def onCook(scriptOp):\n"
            "    n=len(values)\n"
            "    if error or n == 0:\n"
            "        return\n"
            "    for name,vals in zip(('r','g','b'),colors):\n"
            "        pass\n"
        )
        patched = patch_callback_source(original)
        self.assertIn(COUNT_MARKER, patched)
        self.assertIn("n != 3744", patched)
        self.assertIn(MISSING_MARKER, patched)
        self.assertIn("colors[2][missing_index] = 0.0", patched)
        self.assertEqual(patch_callback_source(patched), patched)

    def test_preview_callback_patch_rejects_unknown_callback_shape(self):
        with self.assertRaisesRegex(ValueError, "count anchor"):
            patch_callback_source("def onCook(scriptOp):\n    return\n")


if __name__ == "__main__":
    unittest.main()
