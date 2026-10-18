from enum import Enum
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pixelblaze_mapper.release_ui_theme import compact_size, style_node, restore_node, STORAGE_KEY, THEME, ink_role
from pixelblaze_mapper import build_release_ui as release


class Mode(Enum):
    CONSTANT = 0
    EXPRESSION = 1


class Par:
    def __init__(self, value, expr='', mode=Mode.CONSTANT):
        self.val, self.expr, self.mode = value, expr, mode
    def eval(self): return self.val


class Node:
    def __init__(self, name='caption', kind='text', **pars):
        self.name, self.type = name, kind
        self.par = SimpleNamespace(**{key: value if isinstance(value, Par) else Par(value) for key,value in pars.items()})
        self.storage = {}
    def fetch(self, key, default=None, search=True): return self.storage.get(key, default)
    def store(self, key, value): self.storage[key] = value


def check_readable_compact_sizes():
    assert compact_size(8) == 10
    assert compact_size(12) == 12
    assert compact_size(14) == 13
    assert compact_size(27, 'title') == 20


def check_theme_does_not_change_semantic_state_and_restores_style():
    node = Node(font='Verdana', fontsize=14, text='299', value0=5,
                bgcolorr=.03, bgcolorg=.04, bgcolorb=.05)
    style_node(node)
    assert node.par.font.eval() == 'Bahnschrift'
    assert node.par.fontsize.eval() == 13
    assert node.par.text.eval() == '299' and node.par.value0.eval() == 5
    style_node(node)
    assert node.par.fontsize.eval() == 13
    restore_node(node)
    assert node.par.font.eval() == 'Verdana'
    assert node.par.fontsize.eval() == 14
    assert node.par.bgcolorr.eval() == .03


def check_dynamic_and_safety_colors_are_preserved():
    node = Node(font='Verdana', fontsize=12, bgcolorr=Par(.1, 'parent().par.Red', Mode.EXPRESSION),
                bgcolorg=.1, bgcolorb=.1)
    style_node(node)
    assert node.par.bgcolorr.expr == 'parent().par.Red'
    assert 'bgcolorr' not in node.fetch(STORAGE_KEY)
    red = Node(bgcolorr=.9, bgcolorg=.1, bgcolorb=.1)
    style_node(red)
    assert red.par.bgcolorr.eval() == .9


def check_pinned_info_can_be_closed_after_reenter():
    panel = Node()
    tip = Node(text='', display=False)
    panel.op = lambda name: tip
    with patch.object(release, '_resolve', lambda path: panel):
        release.show_tip('/test', 'Summary', pinned=True)
        release.show_tip('/test', visible=False)
        release.show_tip('/test', 'Summary')
        assert tip.par.display.eval() is True
        release.show_tip('/test', 'Summary', pinned=True)
        assert tip.par.display.eval() is False


class ReleaseThemeTests(unittest.TestCase):
    def test_rounded_surface_noncommercial_resolution(self):
        from pixelblaze_mapper.release_ui_layout import surface_geometry
        for width,height in ((1420,300),(1420,450),(1420,730),(800,1500)):
            geometry=surface_geometry(width,height,8)
            self.assertLessEqual(max(geometry['resolutionw'],geometry['resolutionh']),1280)
            self.assertAlmostEqual(geometry['resolutionw']/geometry['resolutionh'],width/height,delta=.015)
            self.assertAlmostEqual(geometry['cornerradius']*max(width,height)/1280,8)
    def test_font_roles(self):
        self.assertEqual(ink_role(Node('screen_title')),'heading')
        self.assertEqual(ink_role(Node('route_count')),'value')
        self.assertEqual(ink_role(Node('input',kind='field')),'value')
        self.assertEqual(ink_role(Node('apply',kind='button')),'button')
        self.assertNotEqual(THEME['heading'],THEME['value'])
        self.assertNotEqual(THEME['button'],THEME['value'])
    def test_readable_compact_sizes(self): check_readable_compact_sizes()
    def test_semantic_preservation_and_rollback(self): check_theme_does_not_change_semantic_state_and_restores_style()
    def test_dynamic_colors_preserved(self): check_dynamic_and_safety_colors_are_preserved()
    def test_info_close_after_reenter(self): check_pinned_info_can_be_closed_after_reenter()
    def test_howto_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(release, 'CATALOG', Path(folder)/'help_catalog.json'):
                with patch.object(release, 'load_catalog', lambda: [{'key':'bad','howto':'../../secret.html'}]):
                    with self.assertRaises(ValueError): release.open_howto('bad')


if __name__ == '__main__': unittest.main()
