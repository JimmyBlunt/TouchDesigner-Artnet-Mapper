"""Catalog reuse never freezes live values or leaks mutable worker snapshots."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from pixelblaze_mapper.mk2_workflow import Controller
from tests import test_mk2_runtime as runtime_fixture
from tests.test_mk2_workflow import material


class CatalogCacheTests(unittest.TestCase):
    def controller(self):
        controller=Controller()
        items=[dict(material(i),categories=['Category '+str(i%3)]) for i in range(635)]
        controller.set_context(dict(catalog=items,active_material=items[0]))
        return controller,items

    def test_published_rows_are_reused_and_nested_metadata_is_readonly(self):
        controller,items=self.controller()
        first=controller.snapshot(readonly_catalog=True)
        with self.assertRaises(TypeError): first['browse_items'][0]['label']='changed'
        with self.assertRaises(TypeError): first['browse_items'][0]['parameters'][0]['value']=9
        items[0]['label']='outside mutation'
        public=controller.snapshot()
        public['browse_items'][0]['label']='public mutation'
        public['browse_items'][0]['parameters'][0]['value']=9
        with patch('pixelblaze_mapper.mk2_workflow.material_categories',side_effect=AssertionError('catalog rescanned')):
            for value in (.1,.2,.3):
                active=deepcopy(items[0]);active['parameters'][0]['value']=value
                controller.set_context(dict(active_material=active))
                current=controller.snapshot(readonly_catalog=True)
                self.assertIs(current['browse_items'],first['browse_items'])
                self.assertEqual(current['parameter_pages'][0]['parameters'][0]['value'],value)
        self.assertEqual(first['browse_items'][0]['label'],'Material 0')
        self.assertNotEqual(first['browse_items'][0]['parameters'][0]['value'],9)

    def test_filter_favorites_assignment_and_catalog_refresh_invalidate_metadata(self):
        controller,items=self.controller()
        initial=controller.snapshot(readonly_catalog=True)['browse_items']
        config=controller.export_config();config['favorites']=['m2']
        config['groups'][3]['pads'][7]=dict(kind='material',target='m2',values={})
        controller.set_context(dict(config=config))
        controller.browse_filter='favorites'
        favorite=controller.snapshot(readonly_catalog=True)['browse_items']
        self.assertIsNot(favorite,initial)
        self.assertEqual([item['id'] for item in favorite],['m2'])
        self.assertTrue(favorite[0]['favorite'])
        self.assertEqual(dict(favorite[0]['assignments'][0]),dict(group=3,pad=7))
        updated=deepcopy(items);updated[2]['label']='Renamed';updated[2]['categories']=['New']
        controller.set_context(dict(catalog=updated[::-1]))
        self.assertEqual(controller.browse_selected_id(),'m2')
        renamed=controller.snapshot(readonly_catalog=True)['browse_items']
        self.assertEqual(renamed[0]['label'],'Renamed')
        controller.browse_filter='category';controller.browse_category='New'
        self.assertEqual([item['id'] for item in controller.browse_catalog()],['m2'])
        self.assertIn(dict(label='New',count=1),controller.category_items())
        controller.set_context(dict(catalog=[]))
        self.assertEqual(controller.snapshot(readonly_catalog=True)['browse_items'],())

    def test_show_progress_recording_and_edit_values_stay_fresh_with_shared_catalog(self):
        controller,items=self.controller()
        initial=controller.snapshot(readonly_catalog=True)['browse_items']
        for elapsed,value in ((1,.2),(2,.7)):
            parameters=deepcopy(items[0]['parameters']);parameters[0]['value']=value
            controller.set_context(dict(mode='show',recording='automation',
                show=dict(material=items[0],parameters=parameters,duration=10,elapsed=elapsed)))
            view=controller.snapshot(readonly_catalog=True)
            self.assertIs(view['browse_items'],initial)
            self.assertEqual(view['show']['progress'],elapsed/10)
            self.assertEqual(view['parameter_pages'][0]['parameters'][0]['value'],value)
            self.assertEqual(view['recording'],'automation')
        controller.set_context(dict(mode='material',recording=False))
        controller.screen='pad_edit';controller.edit_material=deepcopy(items[0])
        controller.edit_original={};controller.edit_values={'p0':.8}
        view=controller.snapshot(readonly_catalog=True)
        self.assertEqual(view['parameter_pages'][0]['parameters'][0]['value'],.8)
        self.assertIs(view['browse_items'],initial)


class ManagerCatalogCacheTests(unittest.TestCase):
    setUp=runtime_fixture.RuntimeTests.setUp

    def test_context_merges_once_and_only_sends_catalog_when_refreshed(self):
        manager=self.manager
        with patch.object(manager.controller,'set_context',wraps=manager.controller.set_context) as merge:
            manager._refresh_context()
            self.assertEqual(merge.call_count,1)
            self.assertNotIn('catalog',merge.call_args.args[0])
            manager.refresh_catalog()
            manager._refresh_context()
            self.assertEqual(merge.call_count,2)
            self.assertIn('catalog',merge.call_args.args[0])

    def test_worker_render_accepts_readonly_catalog_and_tracks_browse_selection(self):
        from pixelblaze_mapper.maschine_mk2 import render,button_lights
        manager=self.manager;manager.worker=runtime_fixture.FakeSurface()
        manager.controller.screen='browse'
        manager.update_surface()
        rows=manager.worker.snapshot['controller']['browse_items']
        manager.controller.dispatch(dict(type='wheel',delta=1))
        manager.update_surface()
        snapshot=manager.worker.snapshot
        self.assertIs(snapshot['controller']['browse_items'],rows)
        self.assertEqual(snapshot['controller']['browse_index'],1)
        self.assertEqual(len(render(snapshot)),2)
        self.assertTrue(button_lights(snapshot))


if __name__=='__main__': unittest.main()
