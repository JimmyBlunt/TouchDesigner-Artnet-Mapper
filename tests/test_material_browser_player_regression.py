"""Regression contracts for shortcut dialogs 2 and 4.

These tests are deliberately offline and non-destructive.  They do not open a
TouchDesigner project, send Art-Net, or save a .toe file.  The corresponding
live acceptance measurements are documented in
``docs/MATERIAL_BROWSER_PLAYER_REGRESSION_AUDIT_DE.md``.
"""

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BROWSER = ROOT / "pixelblaze_mapper" / "build_unified_material_browser.py"
CONTROLS = ROOT / "pixelblaze_mapper" / "material_control_surface.py"
CORE = ROOT / "effects" / "build_core_effects.py"
ROUTER = ROOT / "pixelblaze_mapper" / "build_multi_controller_output.py"


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_controls_module():
    spec = importlib.util.spec_from_file_location("material_control_surface_regression", CONTROLS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def controls_placeholder(name: str) -> str:
    return "{controls}." + name


class MaterialBrowserPlayerRegressionTests(unittest.TestCase):
    def test_material_browser_exposes_all_current_live_controls(self):
        text = source(BROWSER)
        for label in (
        "MASTER SPEED",
        "FOCUS X",
        "FOCUS Y",
        "FRAME ZOOM",
        "STOP",
        "0.5x",
        "1x",
        "2x",
        "RESET VIEW",
        "NEON",
        "AMBER",
        "ACID",
        "FIRE/ICE",
        "MONO",
        ):
            self.assertIn(repr(label), text)


    def test_visible_material_control_callbacks_target_the_central_player(self):
        text = source(BROWSER)
        self.assertIn("op('/project1/madmapper_player_controls').par.%s = float(par.eval())", text)
        self.assertIn('node.par.pars = "value0"', text)
        self.assertIn("controls.par.Source = 'materials'", text)
        self.assertIn("controls.par.Material = item['id']", text)


    def test_core_player_uses_one_global_speed_source(self):
        """The installed P1 runtime owns phase; absolute time is fallback only."""
        text = source(CORE)
        self.assertIn("material_state_runtime').module.phase()", text)
        self.assertIn('absTime.seconds * {controls}.Speed', text)


    def test_all_shader_parameters_are_bound_to_the_central_control_component(self):
        text = source(CORE)
        for name in (
        "Material.menuIndex",
        "Speed",
        "Scale",
        "Width",
        "Coordinatemode.menuIndex",
        "Intensity",
        "Contrast",
        "Trail",
        "Direction",
        "Rotation",
        "Seed",
        "Transition",
        "Panelcolumns",
        "Panelrows",
        "Hybridmix",
        "Density",
        ):
            self.assertIn(controls_placeholder(name), text)
    def test_framing_patch_is_before_coordinate_conversion_and_network_isolated(self):
        value = load_controls_module()
        base = "const float PI = 3.14;\nvoid main(){\nvec2 sourceUV = vUV.st;\nvec2 uv = coordinateSpace(sourceUV);\n}"
        patched = value.patch_shader_source(base)
        self.assertLess(patched.index("materialBrowserFrame(vUV.st)"), patched.index("coordinateSpace(sourceUV)"))
        lowered = source(CONTROLS).lower()
        self.assertNotIn("dmxout", lowered)
        self.assertNotIn("artnet", lowered)
        self.assertNotIn("project.save", lowered)


    def test_gradient_presets_have_bounded_rgb_values(self):
        presets = load_controls_module().GRADIENT_PRESETS
        self.assertGreaterEqual(len(presets), 5)
        for preset in presets.values():
            self.assertTrue(all(0.0 <= value <= 1.0 for value in preset.color_a + preset.color_b))


    def test_router_sender_builds_all_universes_from_one_packer_snapshot(self):
        text = source(ROUTER)
        self.assertIn("source.cook(force=False)", text)
        self.assertIn("live_frames = _live_frames(configs) if _mode == 'live' else None", text)
        self.assertIn("frames = (_calibration_frames or {}).get(config['name']) if _mode == 'calibration' else live_frames.get(config['name'])", text)
        self.assertIn("for offset, payload in enumerate(frames):", text)


    def test_material_controls_do_not_write_project_or_controller_configuration(self):
        combined = (source(BROWSER) + source(CONTROLS)).lower()
        self.assertNotIn("project.save", combined)
        self.assertNotIn("controller_config[", combined)
        self.assertNotIn("segment_config[", combined)


if __name__ == "__main__":
    unittest.main()
