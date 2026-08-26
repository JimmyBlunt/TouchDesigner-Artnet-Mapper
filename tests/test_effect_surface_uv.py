import ast
import unittest
from pathlib import Path

from pixelblaze_mapper.effect_surface_uv import (
    BACK_START,
    CONTRACT,
    LOWER_SIDE_START,
    UPPER_SIDE_END,
    UPPER_SIDE_START,
    PANEL_IDS,
    build_effect_coordinates,
    rear_wall_uv,
    side_panel_uv,
    side_wall_uv,
)


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_effect_surface_uv.py"


class EffectSurfaceUVTests(unittest.TestCase):
    def test_side_uv_matches_the_minus_90_degree_preview_rotation(self):
        # Real first side-wall sample from the preserved 3D source table.
        u, v = side_wall_uv(0.5557997437, 0.9803440487)
        self.assertAlmostEqual(u, 0.9803440487)
        self.assertAlmostEqual(v, 0.4442002563)

    def test_side_vertical_endpoints(self):
        self.assertEqual(side_wall_uv(0.0, 0.25), (0.25, 1.0))
        self.assertEqual(side_wall_uv(1.0, 0.25), (0.25, 0.0))

    def test_all_side_panels_use_the_same_downward_wall_axis(self):
        self.assertEqual((UPPER_SIDE_START, UPPER_SIDE_END), (517, 786))
        self.assertEqual(LOWER_SIDE_START, 786)
        expected = (0.8, 0.8)
        for index in (0, 516, 517, 785, 786, 1183):
            self.assertEqual(side_panel_uv(index, 0.2, 0.8), expected)

    def test_rear_projection_contract_is_unchanged(self):
        self.assertEqual(BACK_START, 1184)
        self.assertEqual(rear_wall_uv(0.015625, 0.315625), (0.0, 0.0))
        self.assertEqual(rear_wall_uv(0.984375, 0.684375), (1.0, 1.0))

    def test_td_contract_uses_existing_chain(self):
        self.assertEqual(CONTRACT.output_chop, "/project1/effect_sample_uv")
        self.assertEqual(CONTRACT.sampler_chop, "/project1/topto1")
        self.assertEqual(
            CONTRACT.side_source,
            "/project1/pixelblaze_mapper/side_spatial_lookup",
        )

    def test_builder_is_valid_and_does_not_touch_routing(self):
        text = BUILDER.read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn('float(reference[row, "u"])', text)
        self.assertIn('float(reference[row, "v"])', text)
        self.assertNotIn("UPPER_SIDE_START <= index < UPPER_SIDE_END", text)
        self.assertIn("reference = op(CONTRACT.side_source)", text)
        self.assertIn('"effect_panel_uv"', text)
        self.assertIn("mode in ('panel', 'panel_local')", text)
        self.assertIn('"universeRoutingChanged": False', text)
        self.assertNotIn("project.save", text)
        self.assertNotIn("dmxout", text.lower())

    def test_true_local_uvs_are_normalized_inside_each_real_panel(self):
        ranges = ((0, 517), (517, 786), (786, 1184), (1184, 3744))
        source = {}
        for panel_number, (start, stop) in enumerate(ranges):
            span = stop - start - 1
            for index in range(start, stop):
                phase = (index - start) / span
                source[index] = (0.1 * panel_number + 0.05 * phase, 0.9 - 0.1 * phase)
        values = build_effect_coordinates(source)
        self.assertEqual(len(values), 3744)
        for panel_number, (start, stop) in enumerate(ranges):
            panel = values[start:stop]
            self.assertEqual({item.panel_id for item in panel}, {panel_number})
            self.assertAlmostEqual(min(item.local_uv[0] for item in panel), 0.0)
            self.assertAlmostEqual(max(item.local_uv[0] for item in panel), 1.0)
            self.assertAlmostEqual(min(item.local_uv[1] for item in panel), 0.0)
            self.assertAlmostEqual(max(item.local_uv[1] for item in panel), 1.0)
        self.assertEqual(PANEL_IDS, {"middle": 0, "upper": 1, "lower": 2, "rear": 3})

    def test_local_uv_builder_requires_exact_full_index_coverage(self):
        with self.assertRaisesRegex(ValueError, "exactly indices 0..3743"):
            build_effect_coordinates({index: (0.0, 0.0) for index in range(3743)})


if __name__ == "__main__":
    unittest.main()
