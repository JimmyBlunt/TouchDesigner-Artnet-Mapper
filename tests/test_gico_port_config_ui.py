import ast
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_gico_port_config_ui.py"


class GicoPortConfigUIContracts(unittest.TestCase):
    def test_builder_and_runtime_compile(self):
        text = BUILDER.read_text(encoding="utf-8")
        ast.parse(text)
        spec = importlib.util.spec_from_file_location("gico_ui", BUILDER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        compile(module._runtime_source(), "<gico-runtime>", "exec")

    def test_apply_is_safe_and_does_not_invent_port_four_source(self):
        text = BUILDER.read_text(encoding="utf-8")
        self.assertIn('(4, "Port 4", 1, "", 896, 0, "GRB")', text)
        self.assertIn("if not item.routable", text)
        self.assertIn("_stop_output()", text)
        self.assertIn("reserved_universes", text)
        self.assertNotIn("set_enabled(True)", text)
        self.assertNotIn("project.save", text)
        # Static source check is sufficient here; executing the embedded
        # runtime requires TouchDesigner's injected globals.
        self.assertIn("scope = dict(globals())", text)

    def test_ui_exposes_global_constraint_and_derived_port_blocks(self):
        text = BUILDER.read_text(encoding="utf-8")
        self.assertIn("UNIVERSES PER PORT", text)
        self.assertIn("FIRST UI UNIVERSE", text)
        self.assertIn("destination_pixel_start", text)
        self.assertIn("GICO PORT CONFIG", text)

    def test_main_router_rebuild_always_restores_the_gico_entry(self):
        text = (ROOT / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("build_gico_port_config_ui.py", text)
        self.assertIn('gico_scope["build"]()', text)


if __name__ == "__main__":
    unittest.main()
