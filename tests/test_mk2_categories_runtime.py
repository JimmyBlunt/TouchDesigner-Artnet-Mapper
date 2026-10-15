"""Runtime category coverage and receive-time handling without live TD mutation."""
from copy import deepcopy
from queue import Queue
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper.mk2_runtime import Manager
from pixelblaze_mapper.mk2_workflow import Controller, material_categories


def catalog_manager(items, core=None):
    library=SimpleNamespace(_items=items,_safe_preview_path=lambda item:None)
    editor=SimpleNamespace(_library=lambda:library,_catalog=lambda:core or {})
    manager=Manager.__new__(Manager)
    manager.owner=SimpleNamespace(op=lambda name:SimpleNamespace(module=editor))
    manager.catalog_version=0
    return manager


class RuntimeCategoryTests(unittest.TestCase):
    def test_refresh_combines_sources_without_losing_memberships_or_mutating_source(self):
        items=[dict(id='multi',label='Multi',groups=[' imported ',' Geometry  '],
                    categories=['geometry','  Color   effects ','All'],category='Legacy')]
        before=deepcopy(items)
        manager=catalog_manager(items)
        manager.refresh_catalog()
        entry=manager.catalog[0]
        self.assertEqual(entry['categories'],['Geometry','Color effects','Legacy'])
        self.assertEqual(entry['category'],'Geometry / Color effects / Legacy')
        self.assertEqual(items,before)
        self.assertIs(manager.catalog_source,items)
        self.assertEqual(manager.catalog_version,1)

    def test_uncategorized_browsable_items_get_real_fallback_and_core_has_own_category(self):
        items=[dict(id='empty',label='Empty'),dict(id='pseudo',label='Pseudo',groups=['imported','ALL']),
               dict(id='blocked',label='Blocked',compatibility='unsupported')]
        manager=catalog_manager(items,{'fill':{'label':'Fill'}})
        manager.refresh_catalog()
        by_id={item['id']:item for item in manager.catalog}
        self.assertEqual(set(by_id),{'empty','pseudo','core:fill'})
        for key in ('empty','pseudo'):
            self.assertEqual(by_id[key]['categories'],['Ohne Kategorie'])
            self.assertEqual(by_id[key]['category'],'Ohne Kategorie')
        self.assertEqual(by_id['core:fill']['categories'],['TouchDesigner'])
        self.assertEqual(by_id['core:fill']['category'],'TouchDesigner')

    def test_category_refresh_changes_memberships_without_removing_materials(self):
        items=[dict(id='a',label='A',categories=['First']),dict(id='b',label='B')]
        manager=catalog_manager(items)
        manager.refresh_catalog()
        items[0]['categories']=['Second']
        manager.refresh_catalog()
        self.assertEqual(manager.catalog_version,2)
        self.assertEqual([i['id'] for i in manager.catalog],['a','b'])
        self.assertEqual(manager.catalog[0]['categories'],['Second'])
        self.assertEqual(manager.catalog[1]['categories'],['Ohne Kategorie'])

    def test_every_runtime_entry_is_reachable_through_at_least_one_category(self):
        manager=catalog_manager([
            dict(id='one',label='One',groups=['Shapes'],categories=['Motion']),
            dict(id='two',label='Two',groups=['All','imported']),
            dict(id='three',label='Three',category='Motion'),
        ],{'fill':{'label':'Fill'}})
        manager.refresh_catalog()
        controller=Controller()
        controller.set_context(dict(catalog=manager.catalog))
        reached=set()
        for entry in manager.catalog:
            for category in entry['categories']:
                controller.browse_filter='category'
                controller.browse_category=category
                visible={item['id'] for item in controller.browse_catalog()}
                self.assertIn(entry['id'],visible)
                reached.update(visible)
        self.assertEqual(reached,{entry['id'] for entry in manager.catalog})

    def test_shared_normalization_handles_empty_and_casefold_equivalent_metadata(self):
        self.assertEqual(material_categories(dict(groups=['  LIGHT\tpatterns','light patterns','imported'],
                                                   categories=['ALL','Color'],category=' Color ')),
                         ['LIGHT patterns','Color'])
        self.assertEqual(material_categories({}),['Ohne Kategorie'])


class RuntimeWheelReceiveTimeTests(unittest.TestCase):
    def manager(self):
        manager=catalog_manager([])
        manager.refresh_catalog()
        manager._refresh_context=Mock()
        manager._execute=Mock()
        manager.update_surface=Mock()
        manager.worker=object()
        manager.version=3
        manager.error=''
        manager.events=Queue()
        manager.controller=SimpleNamespace(config={'hardware':True},tick=lambda:[],bank=0,
            held={('rec',0)},rec_pending=True,rec_chord=True,flash_until={1:2.},
            reset_browse_motion=Mock(),error='',dispatch=Mock(return_value=[]))
        return manager

    def test_batched_wheel_events_keep_distinct_receive_times_and_leave_input_unchanged(self):
        manager=self.manager()
        received=[]
        manager.dispatch=lambda event:received.append(event)
        first=dict(type='wheel',delta=1,timestamp=1.)
        second=dict(type='wheel',delta=1)
        manager.events.put((first,3,99.2))
        manager.events.put((second,3,99.7))
        with patch('pixelblaze_mapper.mk2_runtime.time.monotonic',return_value=100.):
            manager.tick()
        self.assertEqual([event['timestamp'] for event in received],[99.2,99.7])
        self.assertEqual(first['timestamp'],1.)
        self.assertNotIn('timestamp',second)

    def test_stale_wheel_is_dropped_and_disconnect_resets_motion_even_at_old_version(self):
        manager=self.manager()
        manager.dispatch=Mock()
        manager.events.put((dict(type='wheel',delta=1),3,98.))
        manager.events.put((dict(type='connection_reset'),2,98.))
        with patch('pixelblaze_mapper.mk2_runtime.time.monotonic',return_value=100.):
            manager.tick()
        manager.dispatch.assert_not_called()
        manager.controller.reset_browse_motion.assert_called_once_with()
        self.assertFalse(manager.controller.held)
        self.assertFalse(manager.controller.rec_pending)
        self.assertFalse(manager.controller.rec_chord)
        self.assertFalse(manager.controller.flash_until)

    def test_direct_dispatch_leaves_timestamp_for_controller_clock_fallback(self):
        manager=self.manager()
        event=dict(type='wheel',delta=1)
        manager.dispatch(event)
        manager.controller.dispatch.assert_called_once_with(event)
        self.assertNotIn('timestamp',event)


if __name__=='__main__':
    unittest.main()
