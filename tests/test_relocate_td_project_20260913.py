import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from tools.relocate_td_project_20260913 import OLD, ROOT, portable_code


class PortableDatTests(unittest.TestCase):
    def test_root_literal_uses_current_project(self):
        source = 'ROOT = ' + repr(OLD) + '\n'
        namespace = {'project': SimpleNamespace(folder='Z:/moved')}
        exec(portable_code(source), namespace)
        self.assertEqual(namespace['ROOT'], 'Z:/moved')

    def test_builder_suffix_is_portable_without_path_import(self):
        source = 'BUILDER = ' + repr(OLD + '/pixelblaze_mapper/build_multi_controller_output.py')
        namespace = {'project': SimpleNamespace(folder='Z:/moved/')}
        exec(portable_code(source), namespace)
        self.assertEqual(namespace['BUILDER'], 'Z:/moved/pixelblaze_mapper/build_multi_controller_output.py')

    def test_missing_code_target_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing active code reference'):
            portable_code('SOURCE = ' + repr(OLD + '/missing_20260913_not_a_file.py'))

    def test_future_import_and_docstring_survive(self):
        source = '"""Module docs."""\nfrom __future__ import annotations\nimport pixelblaze_mapper\n'
        updated = portable_code(source)
        self.assertEqual(ast.get_docstring(ast.parse(updated)), 'Module docs.')
        compile(updated, '<test>', 'exec')
        self.assertEqual(portable_code(updated), updated)

    def test_history_prose_and_other_roots_unchanged(self):
        source = 'history = ' + repr('Loaded previously from ' + OLD) + '\nother = "C:/other/file.csv"\n'
        self.assertEqual(portable_code(source), source)


if __name__ == '__main__':
    unittest.main()
