"""Behavioral tests of actual embedded TD functions, without GPU or output."""
import ast
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

from pixelblaze_mapper.build_material_library_browser import _runtime_source as library_source
from pixelblaze_mapper.build_unified_material_browser import _runtime_source as browser_source
from pixelblaze_mapper.material_state import MaterialSettings, MaterialStateStore


def function(source, name, **namespace):
    tree = ast.parse(source())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual TD runtime>', 'exec'), namespace)
    return namespace[name]


class MaterialP1RuntimeTests(unittest.TestCase):
    def test_selected_detail_preview_never_touches_production_shader(self):
        item = dict(id='new', compatibility='ready', prepared_shader_path='x')
        live = NS(text='old live shader')
        detail = NS(text='')
        candidate = Mock()
        candidate.errors.return_value = []
        candidate.warnings.return_value = []
        viewer = NS(par=NS(opviewer=''))
        nodes = {'preview_shader': live, 'detail_shader': detail,
                 'detail_preview': candidate, 'detail_preview_info': NS(text=''),
                 'ui_panel/detail_viewer': viewer}
        state = {}
        fn = function(library_source, 'open_live_preview',
            _selected=lambda: item, _state=lambda name: '', READY_COMPATIBILITY={'ready'},
            _parameter_context=lambda _: (NS(shader='void main(){TDOutputSwizzle(vUV);}'), {}),
            OWNER=NS(op=nodes.get), _configure_parameter_uniforms=Mock(),
            _sync_preview_activity=Mock(),
            _diagnostic_messages=lambda x: x, _set_state=lambda key, val: state.update({key: val}),
            _set_text=Mock())
        self.assertTrue(fn())
        self.assertEqual(live.text, 'old live shader')
        self.assertEqual(state, {'detail_preview_id': 'new'})
        self.assertEqual(viewer.par.opviewer, candidate.path)

    def test_rejected_candidate_does_not_publish_shader(self):
        live = NS(text='old shader')
        nodes = {'preview_shader': live, 'detail_shader': NS(text=''), 'detail_preview': Mock()}
        fn = function(library_source, '_activate_parameter_shader',
            _parameter_context=lambda _: (NS(shader='bad shader'), {}), OWNER=NS(op=nodes.get),
            _configure_parameter_uniforms=Mock(), _compile_errors=lambda *a: ['compile failed'])
        with self.assertRaisesRegex(ValueError, 'compile failed'):
            fn({'id': 'new'})
        self.assertEqual(live.text, 'old shader')

    def test_native_inspector_targets_active_not_catalog_selection(self):
        values = {'selected_id': 'other', 'active_id': 'playing'}
        fn = function(library_source, '_active_item',
            _state=lambda key: values.get(key, ''), _items=[{'id': 'other'}, {'id': 'playing'}])
        self.assertEqual(fn()['id'], 'playing')

    def test_opening_native_editor_same_value_has_no_setter_or_status_side_effect(self):
        title = NS(fetch=lambda key, default=None: 'speed' if key == 'parameter_name' else default)
        setter = Mock()
        status = Mock()
        library = NS(parameter_snapshot=lambda: {'parameters': [dict(name='speed', components=1, value=.25)]},
                     set_material_parameter=setter)
        fn = function(browser_source, 'native_editor_value_changed',
            _native_control=lambda name: title, _native_library=lambda: library, _status=status)
        self.assertFalse(fn(0, .25))
        setter.assert_not_called()
        status.assert_not_called()

    def test_hydration_does_not_read_or_write_native_state(self):
        title = NS(fetch=lambda key, default=None: True if key == 'hydrating' else default)
        library = Mock()
        fn = function(browser_source, 'native_editor_value_changed',
            _native_control=lambda name: title, _native_library=library)
        self.assertFalse(fn(0, 5))
        library.assert_not_called()

    def test_selecting_visible_page2_card_does_not_activate_or_reset_page(self):
        state = {'layout': '4x2', 'page': 1}
        items = [dict(key=str(i), label=str(i)) for i in range(20)]
        card = NS(fetch=lambda key, default: '9')
        fn = function(browser_source, 'select_slot', FILTERED=items,
            _state=lambda key, default=None: state.get(key, default),
            OWNER=NS(op=lambda _: card), _set_state=lambda key, val: state.update({key: val}),
            _status=Mock())
        self.assertTrue(fn(1))
        self.assertEqual(state, {'layout': '4x2', 'page': 1, 'selected_key': '9'})

    def test_new_settings_original_and_legacy_migration_preserves_old_look(self):
        self.assertEqual(MaterialSettings().color_mode, 'original')
        self.assertEqual(MaterialSettings.from_dict({'speed': .5}).color_mode, 'legacy')
        settings = MaterialSettings(intensity=.25, contrast=2, color_mode='gradient', gradient_strength=.3)
        self.assertEqual(MaterialSettings.from_dict(json.loads(json.dumps(settings.to_dict()))), settings)

    def test_intensity_contrast_and_color_mode_are_per_material(self):
        store = MaterialStateStore()
        first = MaterialSettings(intensity=.2, contrast=3, color_mode='gradient')
        store.activate('a', 0, initial=first)
        store.activate('b', 1)
        self.assertEqual(store.state('b').settings, MaterialSettings())
        self.assertEqual(store.activate('a', 2).settings, first)


if __name__ == '__main__':
    unittest.main()
