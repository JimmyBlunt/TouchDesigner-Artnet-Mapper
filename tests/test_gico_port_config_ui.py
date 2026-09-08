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
        self.assertIn("START-UNIVERSE (AB 0)", text)
        self.assertIn("destination_pixel_start", text)
        self.assertIn("GICO PORT CONFIG", text)
        self.assertIn("canvas.viewer = True", text)

    def test_main_router_rebuild_always_restores_the_gico_entry(self):
        text = (ROOT / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("build_gico_port_config_ui.py", text)
        self.assertIn('gico_scope["build"]()', text)

    def test_generated_singleton_cleans_numbered_duplicates_even_with_canonical(self):
        import re
        tree = ast.parse(BUILDER.read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_node')
        scope = {'re': re}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<node-helper>', 'exec'), scope)
        class Parent:
            def __init__(self):
                self.children = []
            def op(self, name):
                return next((node for node in self.children if node.name == name), None)
            def create(self, kind, name):
                node = Node(self, name + '1')
                self.children.append(node)
                return node
        class Node:
            def __init__(self, parent, name):
                self.parent, self.name = parent, name
            def destroy(self):
                self.parent.children.remove(self)
        parent = Parent()
        parent.children = [Node(parent, name) for name in ('apply', 'apply1', 'apply17', 'other')]
        for _ in range(3):
            self.assertEqual(scope['_node'](parent, 'button', 'apply').name, 'apply')
        self.assertEqual([node.name for node in parent.children], ['apply', 'other'])
        self.assertEqual(scope['_node'](parent, 'button', 'validate').name, 'validate')
        self.assertEqual(scope['_node'](parent, 'button', 'validate').name, 'validate')
        self.assertEqual(len(parent.children), 3)


if __name__ == "__main__":
    unittest.main()
