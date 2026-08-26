import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pixelblaze_mapper" / "restore_photo_calibration.py"


class PhotoCalibrationRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_keeps_current_clean_panel_split(self):
        self.assertIn("REAR_START = REAR.start", self.text)
        self.assertIn("source.numSamples != TOTAL_PIXELS", self.text)
        self.assertIn("PANEL_COUNT * PANEL_SIZE", self.text)

    def test_contains_ten_panels_and_eighty_corner_values(self):
        assignment = next(
            node for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "PANEL_CORNERS" for target in node.targets)
        )
        corners = ast.literal_eval(assignment.value)
        self.assertEqual(len(corners), 10)
        self.assertTrue(all(len(panel) == 4 for panel in corners))
        self.assertTrue(all(len(point) == 2 for panel in corners for point in panel))

    def test_restores_editable_parameters_and_pin_expressions(self):
        self.assertIn('page.appendFloat(name, label=name)', self.text)
        self.assertIn('getattr(pin.par, target).expr', self.text)
        self.assertIn('"Einzelfaecher"', self.text)

    def test_canonical_preview_is_bound_to_photo_composite(self):
        self.assertIn('CANONICAL_PREVIEW = "/project1/LED_PREVIEW_OUT"', self.text)
        self.assertIn("preview_alias.par.top = output.path", self.text)
        self.assertIn('"previewAlias": preview_alias.path', self.text)

    def test_reference_photo_is_pinned_to_frame_zero(self):
        self.assertIn('movie.par.index.expr = ""', self.text)
        self.assertIn("movie.par.index = 0", self.text)
        self.assertIn("movie.par.play = False", self.text)
        self.assertIn("reload_pulse.pulse()", self.text)
        self.assertIn("movie.cook(force=True)", self.text)

    def test_is_preview_only_and_never_saves_or_touches_network(self):
        self.assertNotIn("project.save", self.text)
        self.assertNotIn("dmxout", self.text.lower())
        self.assertNotIn("network_output_enabled", self.text)
        self.assertIn('"networkChanged": False', self.text)


if __name__ == "__main__":
    unittest.main()
