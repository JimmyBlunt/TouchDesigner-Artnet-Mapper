"""Actual embedded preview-lifecycle functions; no TD or GPU writes."""
import ast
from types import SimpleNamespace as NS
import unittest
from pixelblaze_mapper.build_material_library_browser import _runtime_source as library_source
from pixelblaze_mapper.build_unified_material_browser import _runtime_source as browser_source


def function(source, name, **scope):
    nodes = [node for node in ast.parse(source()).body if isinstance(node, ast.FunctionDef) and node.name == name]
    if not nodes:
        raise AssertionError('Missing actual runtime function: ' + name)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual preview activity>', 'exec'), scope)
    return scope[name]


class PreviewActivityTests(unittest.TestCase):
    def test_only_visible_core_previews_animate_and_page_return_unfreezes(self):
        nodes = {prefix + str(i): NS(lock=False) for prefix in ('preview_', 'card_top_') for i in range(3)}
        storage = {}
        owner = NS(op=nodes.get, fetch=lambda k, d=None: storage.get(k, d), store=lambda k, v: storage.update({k: v}))
        items = [dict(source='core', effect_index=i) for i in range(3)]
        sync = function(browser_source, '_sync_core_preview_activity', OWNER=owner, ITEMS=items)
        sync([items[1]])
        for i in range(3):
            self.assertEqual(nodes['preview_' + str(i)].lock, i != 1)
            self.assertEqual(nodes['card_top_' + str(i)].lock, i != 1)
        sync([items[0], dict(source='imported')])
        self.assertFalse(nodes['preview_0'].lock)
        self.assertTrue(nodes['preview_1'].lock)
        sync([])
        self.assertTrue(all(node.lock for node in nodes.values()))

    def library_fixture(self):
        states = {'selected_id': 'selected', 'detail_preview_id': 'selected', 'hover_slot': '', 'hover_material_id': ''}
        nodes = {'hover_preview': NS(path='/hover', lock=False), 'detail_preview': NS(path='/detail', lock=False)}
        target = {'detail': '/image', 'card': '/image'}
        nodes['ui_panel/detail_viewer'] = NS(par=NS(opviewer=NS(eval=lambda: target['detail'])))
        nodes['ui_panel/card_viewer_0'] = NS(par=NS(opviewer=NS(eval=lambda: target['card']), display=NS(eval=lambda: True)))
        seen = []
        def node(name):
            seen.append(name)
            return nodes.get(name)
        sync = function(library_source, '_sync_preview_activity', OWNER=NS(op=node),
            _state=lambda key: states.get(key, ''), _item_for_slot=lambda slot: {'id': 'hovered'})
        return sync, states, nodes, target, seen

    def test_inactive_library_previews_freeze_without_touching_production(self):
        sync, states, nodes, target, seen = self.library_fixture()
        sync()
        self.assertTrue(nodes['hover_preview'].lock)
        self.assertTrue(nodes['detail_preview'].lock)
        self.assertNotIn('live_preview', seen)
        self.assertNotIn('preview_shader', seen)

    def test_hover_and_selected_live_detail_resume_only_while_referenced(self):
        sync, states, nodes, target, seen = self.library_fixture()
        target['detail'] = '/detail'
        sync()
        self.assertFalse(nodes['detail_preview'].lock)
        states.update(hover_slot='0', hover_material_id='hovered')
        target.update(detail='/hover', card='/hover')
        sync()
        self.assertFalse(nodes['hover_preview'].lock)
        self.assertTrue(nodes['detail_preview'].lock)
        states.update(hover_slot='', hover_material_id='')
        target['detail'] = '/detail'
        sync()
        self.assertTrue(nodes['hover_preview'].lock)
        self.assertFalse(nodes['detail_preview'].lock)
        states['selected_id'] = 'different'
        sync()
        self.assertTrue(nodes['detail_preview'].lock)

    def test_locked_diagnostic_candidates_are_unlocked_for_real_compile(self):
        source = library_source()
        body = source.split('def _activate_parameter_shader(item):', 1)[1].split('def reset_material_parameters', 1)[0]
        self.assertIn('candidate.lock = False', body)
        self.assertIn('candidate.lock = previous_lock', body)
        self.assertNotIn('preview.lock', body)

    def test_failed_candidate_compile_restores_lock_without_touching_live(self):
        from unittest.mock import Mock
        candidate = NS(lock=True)
        def cook(**kwargs):
            self.assertFalse(candidate.lock)
        candidate.cook = cook
        seen = []
        nodes = {'detail_preview': candidate, 'detail_shader': NS(text='old')}
        def node(name):
            seen.append(name)
            return nodes[name]
        activate = function(library_source, '_activate_parameter_shader', OWNER=NS(op=node),
            _parameter_context=lambda _: (NS(shader='invalid'), {}), _configure_parameter_uniforms=Mock(),
            _compile_errors=lambda *args: ['compile failed'])
        with self.assertRaisesRegex(ValueError, 'compile failed'):
            activate({'id': 'bad'})
        self.assertTrue(candidate.lock)
        self.assertNotIn('live_preview', seen)


if __name__ == '__main__':
    unittest.main()
