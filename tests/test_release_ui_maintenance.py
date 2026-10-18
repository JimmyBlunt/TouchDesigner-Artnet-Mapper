"""Regression: TextDATs and TextCOMPs share TD's `type == 'text'`."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import build_release_ui as release


def node(name, *, component, styled):
    return SimpleNamespace(name=name, type='text', isCOMP=component,
                           fetch=Mock(return_value={} if styled else None))


class MaintenanceTests(unittest.TestCase):
    def audit(self, children, *, missing_help=False):
        panel=SimpleNamespace(children=children,
                              op=lambda name: None if missing_help else object())
        root=SimpleNamespace(fetch=lambda *args, **kwargs: '03')
        screen={'key':'router', 'target':'/project1/router'}
        with patch.object(release,'_resolve',side_effect=lambda path: root if path=='/project1' else panel), \
             patch.object(release,'load_catalog',return_value=[screen]), \
             patch.object(release,'select_theme'), \
             patch.object(release,'install_screen') as install, \
             patch.object(release,'_last_maintenance',0), \
             patch('time.monotonic',side_effect=[10,12.1,14.2]):
            for _ in range(3): release.maintenance_tick()
            return install.call_count

    def test_callback_and_shader_text_dats_do_not_trigger_reinstallation(self):
        callback=node('title_callbacks',component=False,styled=False)
        shader=node('preview_pixel',component=False,styled=False)
        title=node('title',component=True,styled=True)
        self.assertEqual(self.audit([callback,shader,title]),0)
        callback.fetch.assert_not_called()
        shader.fetch.assert_not_called()

    def test_new_unstyled_text_component_still_triggers_repair(self):
        self.assertEqual(self.audit([node('new_title',component=True,styled=False)]),3)

    def test_missing_help_still_triggers_repair(self):
        self.assertEqual(self.audit([node('title',component=True,styled=True)],missing_help=True),3)


if __name__=='__main__': unittest.main()
