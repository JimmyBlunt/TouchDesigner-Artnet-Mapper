"""Offline contracts for direct, unsampled mouse press callbacks.

The event harness verifies generated callback dispatch, not TouchDesigner's
native event delivery; a real short-click check is still required in TD.
"""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper import build_gico_port_config_ui as gico


ROOT = Path(__file__).resolve().parents[1] / 'pixelblaze_mapper'


class DialogPressBindingTests(unittest.TestCase):
    def test_every_owned_button_binding_watches_direct_left_press(self):
        for filename, expected in (('build_multi_controller_output.py', 2),
                                   ('build_show_sequencer.py', 1),
                                   ('build_gico_port_config_ui.py', 1)):
            tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
            values = [node.value.value for node in ast.walk(tree)
                      if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                      and any(isinstance(target, ast.Attribute) and target.attr == 'panelvalue'
                              for target in node.targets)]
            self.assertEqual(values, ['lselect'] * expected, filename)

    def test_topology_uses_same_direct_press_helper(self):
        source = (ROOT / 'build_port_topology_ui.py').read_text(encoding='utf-8')
        self.assertIn("'_click'", source)
        self.assertNotIn('chopexecuteDAT', source)

    def test_generated_gico_and_topology_callback_dispatches_each_press_only_once(self):
        parameter = SimpleNamespace(active=True, panelvalue='state', offtoon=False,
                                    ontooff=True, whileon=True, whileoff=True, valuechange=True)
        node = SimpleNamespace(par=parameter)
        with patch.object(gico, '_node', return_value=node), patch.object(gico, 'panelexecuteDAT', object(), create=True):
            result = gico._click(SimpleNamespace(op=lambda name: None), 'click_apply',
                                 SimpleNamespace(path='/button'), 'calls.append("apply")')
        self.assertIs(result, node)
        self.assertEqual(parameter.panelvalue, 'lselect')
        self.assertTrue(parameter.active)
        self.assertTrue(parameter.offtoon)
        self.assertFalse(parameter.ontooff)
        self.assertFalse(parameter.whileon)
        self.assertFalse(parameter.whileoff)
        self.assertFalse(parameter.valuechange)
        calls = []
        scope = {'calls': calls}
        exec(node.text, scope)
        # Two short press/release pairs, without any render-frame/CHOP sample.
        previous = False
        for selected in (True, False, True, False):
            if selected and not previous and parameter.offtoon:
                scope['onOffToOn'](SimpleNamespace(val=1))
            previous = selected
        self.assertEqual(calls, ['apply', 'apply'])


if __name__ == '__main__':
    unittest.main()
