"""Contract tests for Material Browser speed, colour, and framing controls."""

import ast
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_FILE = ROOT / "pixelblaze_mapper" / "material_control_surface.py"


def module():
    spec = importlib.util.spec_from_file_location("material_control_surface", MODULE_FILE)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


class MaterialControlSurfaceTests(unittest.TestCase):
    def test_module_is_valid_python(self):
        ast.parse(MODULE_FILE.read_text(encoding="utf-8"))

    def test_presets_are_named_and_colour_values_are_in_range(self):
        value = module()
        self.assertGreaterEqual(len(value.GRADIENT_PRESETS), 5)
        for key, preset in value.GRADIENT_PRESETS.items():
            self.assertEqual(key, preset.key)
            for component in preset.color_a + preset.color_b:
                self.assertGreaterEqual(component, 0.0)
                self.assertLessEqual(component, 1.0)

    def test_frame_shader_patch_is_idempotent_and_uses_centered_focus(self):
        value = module()
        base = "out vec4 fragColor;\nconst float PI = 3.14;\nvoid main() {\nvec2 sourceUV = vUV.st;\n        vec2 uv = coordinateSpace(sourceUV);\n}\n"
        first = value.patch_shader_source(base)
        second = value.patch_shader_source(first)
        self.assertEqual(first, second)
        self.assertIn("uniform vec4 uParams4", first)
        self.assertIn("focus + (sourceUV - vec2(0.5)) / zoom", first)
        self.assertIn("materialBrowserFrame(vUV.st)", first)

    def test_patch_rejects_unrecognised_shader_layout(self):
        with self.assertRaises(ValueError):
            module().patch_shader_source("void main() {}")

    def test_install_contract_is_non_network_and_non_saving(self):
        text = MODULE_FILE.read_text(encoding="utf-8").lower()
        self.assertNotIn("dmxout", text)
        self.assertNotIn("artnet", text)
        self.assertNotIn("project.save", text)
        self.assertIn("networkoutputenabled\": false", text)
        self.assertIn("projectsaved\": false", text)

    def test_existing_speed_and_colour_controls_remain_the_single_source(self):
        text = MODULE_FILE.read_text(encoding="utf-8")
        self.assertIn("controls.par.Colorr", text)
        self.assertIn("controls.par.Color2r", text)
        self.assertNotIn("Speed =", text)

    def test_gradient_click_forces_the_shared_material_postprocess_to_refresh(self):
        text = MODULE_FILE.read_text(encoding="utf-8")
        self.assertIn('op(ROOT + "/material_gradient_player")', text)
        self.assertIn("postprocess.cook(force=True)", text)


if __name__ == "__main__":
    unittest.main()
