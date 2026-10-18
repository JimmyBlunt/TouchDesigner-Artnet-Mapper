"""Selection preview isolation and failure regressions without live TD changes."""
import ast
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from pixelblaze_mapper.mk2_material_preview import MaterialPreview, PARENT, PANEL, LIBRARY, EDITOR


class Parameters:
    def __init__(self):
        self.values = {}

    def __getattr__(self, name):
        return self.values.setdefault(name, SimpleNamespace(val=None))


class Node:
    def __init__(self, registry, path, kind='baseCOMP'):
        self.registry, self.path, self.kind = registry, path, kind
        self.par, self.lock = Parameters(), False
        self.frame, self.cooks, self.problem = None, 0, ''
        registry[path] = self

    def op(self, name):
        return self.registry.get(self.path + '/' + name)

    def create(self, kind, name):
        return Node(self.registry, self.path + '/' + name, kind)

    def cook(self, force=False):
        self.cooks += 1
        if not self.lock:
            if self.kind == 'selectTOP':
                self.frame = copy.deepcopy(self.registry[self.par.top.val].frame)
            elif self.kind == 'moviefileinTOP':
                self.frame = Path(self.par.file.val).read_bytes()

    def errors(self):
        return self.problem


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.registry = {}
        Node(self.registry, PARENT)
        self.hover = Node(self.registry, '/project1/madmapper_library/hover_preview', 'glslTOP')
        self.core = Node(self.registry, '/project1/material_browser/preview_2', 'glslTOP')
        self.core.frame = ['core initial']
        self.live = Node(self.registry, '/project1/material_gradient_player', 'glslTOP')
        self.protected = dict(Source='show', selected_id='other', active_id='on-air',
                              native={'gain': .73, 'offset': [1, 2]}, playing=True)
        self.before = copy.deepcopy(self.protected)
        self.items = [{'id': 'a', 'label': 'Material A', 'compatibility': 'supported'},
                      {'id': 'b', 'label': 'Material B', 'compatibility': 'supported'},
                      {'id': 'blocked', 'label': 'Blocked', 'compatibility': 'unsupported'}]
        self.compiled, self.failure, self.allowed = [], None, set()
        self.library = SimpleNamespace(_items=self.items, _compile_hover_item=self.compile,
                                       _validated_file=self.validate, _safe_preview_path=lambda item: None)
        Node(self.registry, LIBRARY).module = self.library
        self.catalog = {'ripple': {'index': 2, 'label': 'Ripple'},
                        'Ripple': {'index': 2, 'label': 'Ripple'}}
        Node(self.registry, EDITOR).module = SimpleNamespace(_catalog=lambda: self.catalog)
        td = SimpleNamespace(**{k: k for k in ('containerCOMP', 'textCOMP', 'opviewerCOMP',
                                              'selectTOP', 'moviefileinTOP')})
        self.preview = MaterialPreview(self.registry.get, td)

    def compile(self, item):
        self.compiled.append(item['id'])
        if self.failure:
            raise ValueError(self.failure)
        self.hover.frame = ['pixels', item['id'], copy.deepcopy(self.protected['native'])]
        return self.hover

    def validate(self, value, extensions):
        path = Path(value)
        if str(path) not in self.allowed or path.suffix.lower() not in extensions:
            raise ValueError('Outside approved roots')
        return path

    def assert_isolated(self):
        self.assertEqual(self.protected, self.before)
        self.assertEqual(self.live.cooks, 0)

    def test_native_selection_is_owned_still_and_preserves_show_and_parameters(self):
        self.assertEqual(self.preview.select('a'), PANEL)
        capture = self.registry[PANEL + '/captured_frame']
        expected = copy.deepcopy(capture.frame)
        self.assertTrue(capture.lock)
        self.assertEqual(capture.par.top.val, '')
        self.assertEqual(self.registry[PANEL + '/image'].par.opviewer.val, capture.path)
        self.compile(self.items[1])  # Another UI owns and changes the shared hover.
        self.assertEqual(capture.frame, expected)
        self.assertEqual(self.registry[PANEL + '/status'].par.text.val, 'Vorschau (Standbild)')
        self.assertEqual(self.registry[PANEL + '/hint'].par.text.val, 'Rad drücken: laden')
        self.assert_isolated()

    def test_prefix_alias_and_repeated_selection_do_not_compile_or_rebuild(self):
        self.preview.select('madmapper:a')
        nodes = dict(self.registry)
        self.preview.select('a')
        self.assertEqual(self.compiled, ['a'])
        self.assertEqual(self.registry, nodes)
        self.preview.select('b')
        self.assertEqual(self.compiled, ['a', 'b'])
        self.assertEqual(self.registry, nodes)
        self.assertEqual(self.registry[PANEL + '/title'].par.text.val, 'Material B')
        self.assertEqual(self.registry[PANEL + '/captured_frame'].frame[1], 'b')
        self.assert_isolated()

    def test_core_alias_uses_catalog_index_and_captures_without_activation(self):
        self.preview.select('core:RIPPLE')
        self.assertEqual(self.preview.state['status'], 'ready')
        self.assertEqual(self.preview.state['label'], 'Ripple')
        self.assertEqual(self.compiled, [])
        self.assertEqual(self.core.cooks, 0)
        self.core.frame = ['later time']
        self.assertEqual(self.registry[PANEL + '/captured_frame'].frame, ['core initial'])
        self.assert_isolated()

    def test_invalid_core_index_is_visible_and_does_not_touch_other_nodes(self):
        self.catalog['bad'] = {'index': 25}
        self.preview.select('core:bad')
        self.assertEqual(self.preview.state['status'], 'error')
        self.assertIn('Vorschauindex', self.preview.state['error'])
        self.assertFalse(self.registry[PANEL + '/image'].par.display.val)
        self.assert_isolated()

    def test_compile_failure_uses_only_approved_descriptor_image(self):
        self.failure = 'Shader compiler error'
        with TemporaryDirectory() as folder:
            image = Path(folder) / 'thumb.png'
            image.write_bytes(b'approved thumbnail')
            self.allowed.add(str(image))
            self.preview.select('a', {'id': 'a', 'image': str(image)})
            self.assertEqual(self.preview.state['status'], 'thumbnail')
            self.assertEqual(self.registry[PANEL + '/captured_frame'].frame, b'approved thumbnail')
            self.assertIn('Shader compiler error', self.registry[PANEL + '/status'].par.text.val)
        self.assert_isolated()

    def test_unsupported_does_not_compile_and_can_show_saved_preview_path(self):
        with TemporaryDirectory() as folder:
            image = Path(folder) / 'thumb.png'
            image.write_bytes(b'blocked thumbnail')
            self.allowed.add(str(image))
            self.preview.select('blocked', {'preview_path': str(image)})
            self.assertEqual(self.compiled, [])
            self.assertEqual(self.preview.state['status'], 'thumbnail')
            self.assertIn('gesperrt', self.preview.state['error'])
        self.assert_isolated()

    def test_unknown_selection_clears_old_picture_and_reports_error(self):
        self.preview.select('a')
        self.preview.select('missing')
        viewer = self.registry[PANEL + '/image']
        self.assertEqual(viewer.par.opviewer.val, '')
        self.assertFalse(viewer.par.display.val)
        self.assertEqual(self.preview.state['status'], 'error')
        self.assertIn('missing', self.preview.state['error'])
        self.assert_isolated()

    def test_unapproved_or_wrong_material_thumbnail_never_loaded(self):
        self.failure = 'Failed'
        with TemporaryDirectory() as folder:
            image = Path(folder) / 'thumb.png'
            image.write_bytes(b'private')
            self.preview.select('a', {'image': str(image)})
            self.assertNotIn(PANEL + '/thumbnail', self.registry)
            self.allowed.add(str(image))
            self.preview.select('b', {'id': 'a', 'image': str(image)})
            self.assertNotIn(PANEL + '/thumbnail', self.registry)
        self.assert_isolated()

    def test_unexpected_live_top_return_is_rejected_without_cook(self):
        self.library._compile_hover_item = lambda item: self.live
        self.preview.select('a')
        self.assertEqual(self.preview.state['status'], 'error')
        self.assertIn('isolierte', self.preview.state['error'])
        self.assert_isolated()

    def test_missing_parent_is_explicit_and_never_creates_project_nodes(self):
        del self.registry[PARENT]
        before = dict(self.registry)
        with self.assertRaisesRegex(RuntimeError, 'Fensterverwaltung'):
            self.preview.select('a')
        self.assertEqual(self.registry, before)
        self.assertEqual(self.compiled, [])

    def test_failed_fallback_validation_does_not_hide_compile_diagnostic(self):
        self.failure = 'Useful shader diagnostic'
        def invalid(item):
            raise ValueError('Deleted thumbnail')
        self.library._safe_preview_path = invalid
        self.preview.select('a')
        self.assertEqual(self.preview.state['status'], 'error')
        self.assertEqual(self.preview.state['error'], 'Useful shader diagnostic')
        self.assert_isolated()

    def test_real_library_hover_callback_connects_to_capture_without_live_writes(self):
        # Execute the shipped callback itself, with only TD/GPU dependencies
        # replaced. This catches drift in the actual preview integration API.
        from pixelblaze_mapper.build_material_library_browser import _runtime_source
        tree = ast.parse(_runtime_source())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == '_compile_hover_item')
        owner = Node(self.registry, '/project1/madmapper_library')
        shader = Node(self.registry, owner.path + '/hover_shader')
        shader.text = ''
        state = copy.deepcopy(self.protected)
        owner.fetch = lambda key, default=None: state.get(key, default)
        owner.store = lambda key, value: state.__setitem__(key, value)
        configured = []
        def configure(target, adaptation, values, publish_schema):
            configured.append((target.path, values, publish_schema))
            target.frame = ['actual callback pixels', copy.deepcopy(values)]
        with TemporaryDirectory() as folder:
            source = Path(folder) / 'material.fs'
            source.write_text('void main() {}', encoding='utf-8')
            self.items[0]['source_path'] = str(source)
            adaptation = SimpleNamespace(shader='void main() {}')
            namespace = dict(OWNER=owner, _hover_context_cache={},
                             _validated_file=lambda path, extensions: Path(path),
                             PARAMETER_STORE=SimpleNamespace(material_ids=[]),
                             _parameter_context=lambda item: (adaptation, copy.deepcopy(self.protected['native'])),
                             _configure_parameter_uniforms=configure,
                             _diagnostic_messages=lambda messages: messages)
            exec(compile(ast.Module(body=[function], type_ignores=[]), '<real-hover-callback>', 'exec'), namespace)
            self.library._compile_hover_item = namespace['_compile_hover_item']
            self.preview.select('a')
        self.assertEqual(self.preview.state['status'], 'ready')
        self.assertEqual(configured, [(self.hover.path, self.before['native'], False)])
        self.assertEqual(self.hover.cooks, 1)
        self.assertEqual(shader.text, 'void main() {}')
        self.assertEqual(state.pop('hover_compiled_id'), 'a')
        self.assertEqual(state, self.before)
        self.assertEqual(self.registry[PANEL + '/captured_frame'].frame,
                         ['actual callback pixels', self.before['native']])
        self.assert_isolated()


if __name__ == '__main__':
    unittest.main()
