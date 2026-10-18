"""Execute generated navigation callbacks with offline viewers only."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

from pixelblaze_mapper.shortcut_hub import SHORTCUTS, ShortcutSpec, validate_shortcuts


SOURCE = (Path(__file__).parents[1] / 'pixelblaze_mapper/build_shortcut_hub.py').read_text(encoding='utf-8')


class ShortcutNavigationRuntimeTests(unittest.TestCase):
    def setUp(self):
        factory = next(node for node in ast.parse(SOURCE).body
                       if isinstance(node, ast.FunctionDef) and node.name == '_callback_source')
        scope = {'SHORTCUTS': SHORTCUTS}
        exec(compile(ast.Module(body=[factory], type_ignores=[]), '<factory>', 'exec'), scope)
        self.opened = []
        self.nodes = {item.target: SimpleNamespace(openViewer=lambda path=item.target: self.opened.append(path))
                      for item in SHORTCUTS}
        self.ui = SimpleNamespace(status='')
        self.runtime = {'op': self.nodes.get, 'ui': self.ui}
        exec(scope['_callback_source'](), self.runtime)

    def test_each_new_shortcut_resolves_target_at_open_time(self):
        for key in 'lgc':
            target = next(item.target for item in SHORTCUTS if item.key == key)
            self.assertTrue(self.runtime['open_target'](key))
            self.assertEqual(self.opened[-1], target)
            del self.nodes[target]
            self.assertFalse(self.runtime['open_target'](key))
            self.assertIn('target missing', self.ui.status)

    def test_keyboard_filters_modifiers_and_release(self):
        def event(key='l', ctrl=True, shift=True, alt=False, state=True):
            return self.runtime['keyEvent'](None, key, '', alt, False, False,
                ctrl, False, False, shift, False, False, state, 0)
        for kwargs in (dict(ctrl=False), dict(shift=False), dict(alt=True), dict(state=False), dict(key='x')):
            event(**kwargs)
        self.assertEqual(self.opened, [])
        event(key='L')
        self.assertEqual(self.opened, ['/project1/layout_scene_editor/ui_panel'])

    def test_led_search_import_bootstraps_current_project_folder(self):
        self.runtime['project'] = SimpleNamespace(folder='D:/Moved Project')
        with patch('pixelblaze_mapper.led_search.act', return_value=True) as action:
            with patch.object(sys, 'path', list(sys.path)):
                self.assertTrue(self.runtime['open_target']('s'))
                self.assertEqual(sys.path[0], 'D:/Moved Project')
            action.assert_called_once_with(self.nodes.get, 'open')

    def test_viewer_failure_is_feedback_not_unhandled_exception(self):
        def fail():
            raise RuntimeError('viewer unavailable')
        self.nodes['/project1/layout_scene_editor/ui_panel'] = SimpleNamespace(openViewer=fail)
        self.assertFalse(self.runtime['open_target']('l'))
        self.assertIn('viewer unavailable', self.ui.status)
        self.assertFalse(self.runtime['open_target']('invalid'))

    def test_alpha_keys_are_ascii_and_case_insensitively_unique(self):
        one = ShortcutSpec('l', 'layout', '/project1/layout', 'test')
        self.assertEqual(validate_shortcuts((one,)), ())
        self.assertTrue(validate_shortcuts((one, ShortcutSpec('L', 'other', '/project1/other', 'test'))))
        for key in ('é', '!', '00', ''):
            self.assertTrue(validate_shortcuts((ShortcutSpec(key, 'bad', '/project1/bad', 'test'),)))

    def test_clicks_are_direct_navigation_and_all_rows_fit(self):
        self.assertIn('node.par.panelvalue = "lselect"', SOURCE)
        self.assertIn(".module.open_target(%r)", SOURCE)
        self.assertIn('len(SHORTCUTS) * 48', SOURCE)
        self.assertIn('"open_" + item.key', SOURCE)

    def test_generated_open_button_is_one_press_one_navigation(self):
        function = next(node for node in ast.parse(SOURCE).body
                        if isinstance(node, ast.FunctionDef) and node.name == '_open_button')
        button = SimpleNamespace(path='/hub/help_panel/open_l', par=SimpleNamespace())
        callback = SimpleNamespace(par=SimpleNamespace())
        scope = {'_get_or_create': lambda parent, kind, name: callback if name.startswith('open_click_') else button,
                 '_set': lambda node, name, value: setattr(node.par, name, value),
                 'buttonCOMP': object(), 'panelexecuteDAT': object()}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<button>', 'exec'), scope)
        item = next(item for item in SHORTCUTS if item.key == 'l')
        scope['_open_button'](None, None, item, 100)
        self.assertEqual(callback.par.panelvalue, 'lselect')
        self.assertTrue(callback.par.offtoon)
        for name in ('ontooff', 'whileon', 'whileoff', 'valuechange'):
            self.assertFalse(getattr(callback.par, name))
        actions = []
        runtime = {'op': lambda path: SimpleNamespace(module=SimpleNamespace(open_target=actions.append))}
        exec(callback.text, runtime)
        runtime['onOffToOn'](SimpleNamespace(val=1))
        self.assertEqual(actions, ['l'])
        height = 200 + len(SHORTCUTS) * 48
        self.assertGreater(height - 154 - (len(SHORTCUTS) - 1) * 48, 56)


if __name__ == '__main__':
    unittest.main()
