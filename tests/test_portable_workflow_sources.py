"""Generated workflow helpers resolve paths from their checkout, including moves."""
import ast
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).parents[1]
class PortableWorkflowSourcesTests(unittest.TestCase):
    def test_builder_constants_follow_source_file_in_a_different_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            checkout=Path(folder)/'relocated project'
            for filename,key,suffix in [('build_shortcut_hub.py','LOCAL_ROOT',''),('build_show_sequencer.py','DEMO_SHOW','shows/demo_show.json')]:
                path=ROOT/'pixelblaze_mapper'/filename
                tree=ast.parse(path.read_text(encoding='utf-8'))
                assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets))
                scope={'Path':Path,'__file__':str(checkout/'pixelblaze_mapper'/filename)}
                exec(compile(ast.Module(body=[assignment],type_ignores=[]),'<relocated>','exec'),scope)
                self.assertEqual(Path(scope[key]),checkout/suffix)

    def test_material_control_callback_points_at_installed_package_and_sets_file_context(self):
        path=ROOT/'pixelblaze_mapper/build_unified_material_browser.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_material_control_runtime_source')
        scope={}
        exec(compile(ast.Module(body=[factory],type_ignores=[]),'<factory>','exec'),scope)
        generated=scope['_material_control_runtime_source']()
        runtime={}
        exec(generated,runtime)
        self.assertEqual(Path(runtime['SOURCE']),ROOT/'pixelblaze_mapper/material_control_surface.py')
        self.assertIn("'__file__': SOURCE",generated)
        self.assertNotIn('TouchDesignerLocal',generated)
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            moved={'project':SimpleNamespace(folder=folder)}
            exec(generated,moved)
            self.assertEqual(Path(moved['SOURCE']),Path(folder)/'pixelblaze_mapper/material_control_surface.py')

if __name__=='__main__': unittest.main()
