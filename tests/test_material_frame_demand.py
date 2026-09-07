"""Run real frame/render callbacks with isolated operators; no TD or GPU."""
import ast
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

from pixelblaze_mapper.build_p1_material_state import _frame_callback_source
from pixelblaze_mapper.build_unified_material_browser import _runtime_source


class MaterialFrameDemandTests(unittest.TestCase):
    def run_frame(self, source, missing=None):
        runtime = NS(phase=Mock(return_value=12.25), tick=Mock())
        player = NS(par=NS(vec0valuey=NS(val=-1)))
        imported = NS(par=NS(vec0valuex=NS(val=-2)), cook=Mock())
        nodes = {
            '/project1/material_state_runtime': NS(module=runtime),
            '/project1/madmapper_material_player': player,
            '/project1/madmapper_library/live_preview': imported,
            '/project1/madmapper_player_controls': NS(par=NS(Source=NS(eval=lambda: source))),
        }
        if missing:
            nodes[missing] = None
        scope = {'op': nodes.get}
        exec(compile(_frame_callback_source(), '<actual material frame>', 'exec'), scope)
        scope['onFrameStart'](100)
        runtime.phase.assert_called_once_with()
        runtime.tick.assert_not_called()  # phase() already performs the durable tick.
        return player, imported

    def test_imported_updates_only_imported_and_retains_force_cook(self):
        player, imported = self.run_frame('imported')
        self.assertEqual(player.par.vec0valuey.val, -1)
        self.assertEqual(imported.par.vec0valuex.val, 12.25)
        imported.cook.assert_called_once_with(force=True)

    def test_core_updates_only_core_without_forcing_import(self):
        player, imported = self.run_frame('materials')
        self.assertEqual(player.par.vec0valuey.val, 12.25)
        self.assertEqual(imported.par.vec0valuex.val, -2)
        imported.cook.assert_not_called()

    def test_other_sources_tick_once_without_invalidating_material_tops(self):
        for source in ('movie', 'show', 'unknown'):
            with self.subTest(source=source):
                player, imported = self.run_frame(source)
                self.assertEqual(player.par.vec0valuey.val, -1)
                self.assertEqual(imported.par.vec0valuex.val, -2)
                imported.cook.assert_not_called()

    def test_missing_controls_or_selected_top_does_not_write_other_source(self):
        for missing in ('/project1/madmapper_player_controls',
                        '/project1/madmapper_library/live_preview'):
            with self.subTest(missing=missing):
                player, imported = self.run_frame('imported', missing)
                self.assertEqual(player.par.vec0valuey.val, -1)
                self.assertEqual(imported.par.vec0valuex.val, -2)
                imported.cook.assert_not_called()

    def test_actual_render_reopens_image_only_when_path_changes(self):
        class ImageParameters:
            def __init__(self):
                self.value = 'same.png'
                self.writes = []
            @property
            def file(self):
                return NS(eval=lambda: self.value)
            @file.setter
            def file(self, value):
                self.writes.append(value)
                self.value = value
        image = NS(path='/browser/image', par=ImageParameters())
        nodes = {'unified_image_0': image, 'unified_page': NS(par=NS()),
                 'unified_fallback': NS(path='/browser/fallback')}
        for slot in range(32):
            nodes['unified_viewer_%d' % slot] = NS(par=NS())
            nodes['unified_card_%d' % slot] = NS(par=NS(), store=Mock(), unstore=Mock())
        item = dict(source='imported', key='a', label='A', category='test', preview_path='same.png')
        scope = dict(OWNER=NS(op=nodes.get), FILTERED=[item], _set_state=Mock(),
                     _state=lambda key, default='': {'layout': '8x4', 'page': 0, 'source': 'All', 'group': 'All'}.get(key, default),
                     _button=Mock(), _sync_core_preview_activity=Mock())
        node = next(n for n in ast.parse(_runtime_source()).body if isinstance(n, ast.FunctionDef) and n.name == 'render')
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual unified render>', 'exec'), scope)
        scope['render']()
        self.assertEqual(image.par.writes, [])
        item['preview_path'] = 'new.png'
        scope['render']()
        scope['render']()
        self.assertEqual(image.par.writes, ['new.png'])
        item['preview_path'] = ''
        scope['render']()
        self.assertEqual(image.par.writes, ['new.png', ''])
        self.assertEqual(nodes['unified_viewer_0'].par.opviewer, '/browser/fallback')


if __name__ == '__main__':
    unittest.main()
