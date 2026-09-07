"""Execute actual embedded cache/status functions without TD or GPU."""
import ast
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

from pixelblaze_mapper.build_material_library_browser import _runtime_source as library_source
from pixelblaze_mapper.build_unified_material_browser import _runtime_source as browser_source, _material_player_runtime_source


def functions(source, names, **namespace):
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual embedded cache>', 'exec'), namespace)
    return namespace


class CatalogCacheTests(unittest.TestCase):
    def test_library_cache_reuses_items_and_filtered_without_refresh_or_render(self):
        items, filtered, storage = [{'id': 'active', 'label': 'Playing'}], [], {}
        owner = NS(store=lambda k, v: storage.update({k: v}), fetch=lambda k, d=None: storage.get(k, d))
        signature = Mock(return_value=('catalog-stamp', 'imports-stamp'))
        scope = functions(library_source(), {'_cache_catalog', '_restore_catalog_cache'},
            OWNER=owner, _CATALOG_CACHE_KEY='cache', _items=items, _filtered=filtered, _catalog_signature=signature)
        scope['_cache_catalog']()
        scope['_items'], scope['_filtered'] = [], []
        self.assertTrue(scope['_restore_catalog_cache']())
        self.assertIs(scope['_items'], items)
        self.assertIs(scope['_filtered'], filtered)
        self.assertEqual(storage['material_labels_by_id'], {'active': 'Playing'})
        signature.return_value = ('changed',)
        self.assertFalse(scope['_restore_catalog_cache']())

    def test_unified_cache_preserves_identity_and_page_filter_result(self):
        storage, items, filtered = {}, [{'key': 'a'}], [{'key': 'b'}]
        owner = NS(store=lambda k, v: storage.update({k: v}), fetch=lambda k, d=None: storage.get(k, d))
        scope = functions(browser_source(), {'_cache_catalog', '_restore_catalog_cache'},
            OWNER=owner, CATALOG_CACHE_KEY='cache', ITEMS=items, FILTERED=filtered, _catalog_signature=lambda: 'same')
        scope['_cache_catalog']()
        scope['ITEMS'], scope['FILTERED'] = [], []
        self.assertTrue(scope['_restore_catalog_cache']())
        self.assertIs(scope['ITEMS'], items)
        self.assertIs(scope['FILTERED'], filtered)

    def test_legacy_active_label_uses_published_id_not_selected_and_noop_is_readonly(self):
        state = {'selected_id': 'other', 'live_preview_id': 'playing'}
        writes = Mock(side_effect=lambda k, v: state.update({k: v}))
        owner = NS(fetch=lambda k, d=None: {'playing': 'Bubble Rings', 'other': 'Other'})
        scope = functions(library_source(), {'_restore_active_label'}, OWNER=owner,
            _state=lambda k: state.get(k, ''), _set_state=writes)
        scope['_restore_active_label']()
        self.assertEqual(state['active_label'], 'Bubble Rings')
        self.assertEqual(state['active_label_id'], 'playing')
        writes.reset_mock()
        scope['_restore_active_label']()
        writes.assert_not_called()

    def test_successful_activation_publishes_label_failed_activation_does_not(self):
        state = {}
        activate = Mock()
        scope = functions(library_source(), {'activate_selected'},
            _selected=lambda: {'id': 'a', 'label': 'A'}, _activate_parameter_shader=activate,
            _set_state=lambda k, v: state.update({k: v}), _set_text=Mock())
        self.assertTrue(scope['activate_selected']())
        self.assertEqual(state['active_label_id'], 'a')
        state.clear()
        activate.side_effect = ValueError('compile failed')
        self.assertFalse(scope['activate_selected']())
        self.assertEqual(state, {})

    def test_status_source_has_no_catalog_module_access(self):
        source = _material_player_runtime_source()
        compile(source, '<player status>', 'exec')
        self.assertNotIn('library.module', source)
        self.assertIn("material_labels_by_id", source)
        self.assertIn("active_values.get('active_id') or active_values.get('live_preview_id', '')", source)


if __name__ == '__main__':
    unittest.main()
