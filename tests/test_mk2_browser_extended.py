"""Independent category, accelerated browser and SELECT assignment acceptance."""
import unittest

from pixelblaze_mapper.mk2_workflow import Controller, material_categories
from tests.test_mk2_workflow import material
from tests.test_mk2_favorites import button, press, wheel
from tests import test_mk2_favorites as favorites_fixture


class ExtendedBrowserTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.
        self.c = Controller(clock=lambda: self.now)
        self.catalog = [dict(material(i), category='Group %02d' % (i % 20)) for i in range(100)]
        self.c.set_context(dict(catalog=self.catalog, active_material=self.catalog[0]))

    def browse(self, index=0):
        button(self.c, 'browse')
        self.c.browse_index = index

    def move(self, timestamp=None, delta=1):
        event = dict(type='wheel', delta=delta)
        if timestamp is not None:
            event['timestamp'] = timestamp
        return self.c.dispatch(event)

    def ack(self, command, success=True):
        self.c.dispatch(dict(type='command_result', request_id=command['request_id'],
                             success=success, error='disk full'))

    def config_pad(self, group=0, index=0, target='m2', values=None):
        config = self.c.export_config()
        config['groups'][group]['pads'][index] = dict(kind='material', target=target, values=values or {})
        self.c.set_context(dict(config=config))

    def direct(self, selected=1):
        self.browse(selected)
        self.assertEqual(button(self.c, 'select'), [])
        self.assertEqual(self.c.screen, 'browse_assign')

    def test_browser_first_two_steps_precise_then_medium_and_fast_thresholds(self):
        for interval, expected in ((.1, 3), (1/12, 5), (.04, 10), (.02, 10)):
            with self.subTest(interval=interval):
                self.c.reset_browse_motion()
                self.c.screen, self.c.browse_index = 'browse', 0
                self.move(0)
                self.assertEqual(self.c.browse_index, 1)
                self.move(interval)
                self.assertEqual(self.c.browse_index, 2)
                self.move(2*interval)
                self.assertEqual(self.c.browse_index, expected)

    def test_clock_fallback_and_clamped_list_boundaries(self):
        self.browse(90)
        for value in (0, .02, .04):
            self.now = value
            self.move()
        self.assertEqual(self.c.browse_index, 99)
        self.move(.06, -127)
        self.assertEqual(self.c.browse_index, 0)

    def test_pause_direction_change_button_and_wheel_press_reset_streak(self):
        self.browse(40)
        for action in ('pause', 'reverse', 'button', 'wheel_press'):
            with self.subTest(action=action):
                self.c.browse_index = 40
                self.c.reset_browse_motion()
                for t in (0, .02, .04):
                    self.move(t)
                self.assertEqual(self.c.browse_index, 50)
                if action == 'pause':
                    self.move(.20)
                    self.assertEqual(self.c.browse_index, 51)
                elif action == 'reverse':
                    self.move(.06, -1)
                    self.assertEqual(self.c.browse_index, 49)
                else:
                    button(self.c, 'top', 0) if action == 'button' else press(self.c)
                    self.move(.06)
                    self.assertEqual(self.c.browse_index, 51)

    def test_duplicate_or_backwards_timestamps_never_accelerate(self):
        self.browse()
        for t in (1, 1, .5, .5):
            self.move(t)
        self.assertEqual(self.c.browse_index, 4)

    def test_categories_merge_deduplicate_and_exclude_import_status(self):
        self.assertEqual(material_categories(dict(groups=['All', '  Lines  ', 'imported'],
                         categories=['lines', ' Geometry '], category='geometry / Color')),
                         ['Lines', 'Geometry', 'Color'])
        for item in ({}, dict(groups=['all', 'IMPORTED']), dict(category=None, categories=[3])):
            self.assertEqual(material_categories(item), ['Ohne Kategorie'])
        self.c.set_context(dict(catalog=[dict(material(0), groups=['All', 'Lines'], categories=['lines']),
                                        dict(material(1), category='LINES / Color'), material(2)]))
        counts = {x['label'].casefold():x['count'] for x in self.c.snapshot()['category_items']}
        self.assertEqual(counts, {'color':1, 'lines':2, 'test':2})

    def test_category_navigation_single_steps_press_filters_and_loads(self):
        self.browse()
        self.assertEqual(button(self.c, 'top', 2), [])
        self.assertEqual(self.c.screen, 'categories')
        for t in (0, .01, .02):
            self.move(t)
        self.assertEqual(self.c.category_index, 3)
        self.assertEqual(press(self.c), [])
        self.assertEqual(self.c.screen, 'browse')
        self.assertEqual(self.c.browse_filter, 'category')
        self.assertEqual(self.c.browse_category, 'Group 03')
        self.assertEqual([x['id'] for x in self.c.browse_catalog()], ['m3','m23','m43','m63','m83'])
        self.assertEqual(press(self.c)[0]['material_id'], 'm3')

    def test_category_cancel_and_switch_back_to_favorites(self):
        config = self.c.export_config()
        config['favorites'] = ['m8']
        self.c.set_context(dict(config=config))
        self.browse(8)
        button(self.c, 'top', 2)
        button(self.c, 'browse')
        self.assertEqual(self.c.browse_filter, 'all')
        self.assertEqual(self.c.browse_selected_id(), 'm8')
        button(self.c, 'top', 2)
        button(self.c, 'top', 1)
        self.assertEqual(self.c.screen, 'browse')
        self.assertEqual(self.c.browse_filter, 'favorites')
        self.assertEqual(self.c.browse_selected_id(), 'm8')

    def test_empty_category_catalog_and_removed_category_are_safe(self):
        self.browse()
        button(self.c, 'top', 2)
        self.c.set_context(dict(catalog=[]))
        self.move(0, 127)
        self.assertEqual(self.c.category_index, 0)
        self.assertEqual(press(self.c), [])
        self.assertEqual(self.c.snapshot()['category_items'], [])
        button(self.c, 'top', 0)
        self.assertEqual(self.c.browse_catalog(), [])

    def test_pad_targets_and_show_fields_never_use_browser_acceleration(self):
        self.direct()
        for t in (0, .01, .02):
            self.move(t)
        self.assertEqual(self.c.pad_index, 3)
        button(self.c, 'browse')
        button(self.c, 'scene')
        for t in (.03, .04, .05):
            self.move(t)
        self.assertEqual(self.c.pad_index, 6)
        self.c.set_context(dict(mode='show', show=dict(id='cue', duration=10)))
        press(self.c)
        for t in (.06, .07, .08):
            commands = self.move(t)
            self.assertEqual(commands[0]['value'], 10.1)

    def test_empty_pad_assigns_transactionally_preserves_banks_and_favorites(self):
        self.config_pad(7, 15, values={'p0': .125})
        config = self.c.export_config()
        config['favorites'] = ['m1']
        self.c.set_context(dict(config=config))
        self.direct()
        button(self.c, 'group', 6)
        command, = button(self.c, 'pad', 10)
        self.assertEqual(command['action'], 'persist_config')
        self.assertEqual(command['purpose'], 'direct_assign')
        self.assertEqual(self.c.export_config(), config)
        self.assertTrue(self.c.snapshot()['saving'])
        self.assertEqual(press(self.c), [])
        self.ack(command)
        saved = self.c.export_config()
        self.assertEqual(saved['groups'][6]['pads'][10]['target'], 'm1')
        self.assertEqual(saved['groups'][7], config['groups'][7])
        self.assertEqual(saved['favorites'], ['m1'])
        self.assertEqual(self.c.screen, 'browse')
        self.assertIsNone(self.c.snapshot()['direct_material'])

    def test_occupied_pad_only_select_confirms_and_presets_are_explicitly_replaced(self):
        self.config_pad(values={'p0': .9})
        old = self.c.export_config()
        self.direct()
        self.assertEqual(button(self.c, 'pad', 0), [])
        self.assertEqual(self.c.screen, 'confirm_overwrite')
        self.assertEqual(press(self.c), [])
        self.assertEqual(button(self.c, 'play'), [])
        self.assertEqual(self.c.export_config(), old)
        command, = button(self.c, 'select')
        self.assertEqual(self.c.export_config(), old)
        self.ack(command)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0],
                         dict(kind='material', target='m1', values={}))

    def test_browse_and_select_cancel_direct_assignment_without_loading(self):
        for cancel in ('browse', 'select'):
            with self.subTest(cancel=cancel):
                self.c.screen = 'home'
                self.direct()
                original = self.c.export_config()
                self.assertEqual(button(self.c, cancel), [])
                self.assertEqual(self.c.screen, 'browse')
                self.assertEqual(self.c.export_config(), original)
                self.assertIsNone(self.c.direct_target)
        self.config_pad()
        button(self.c, 'select')
        button(self.c, 'pad', 0)
        self.assertEqual(self.c.screen, 'confirm_overwrite')
        self.assertEqual(button(self.c, 'browse'), [])
        self.assertEqual(self.c.screen, 'browse')

    def test_frozen_material_survives_catalog_reorder_and_pad_reselection(self):
        self.config_pad()
        self.direct(4)
        button(self.c, 'pad', 0)
        self.c.set_context(dict(catalog=self.catalog[::-1]))
        self.assertEqual(self.c.snapshot()['direct_material']['id'], 'm4')
        button(self.c, 'group', 7)
        self.assertEqual(self.c.screen, 'browse_assign')
        command, = button(self.c, 'pad', 15)
        self.assertEqual(command['config']['groups'][7]['pads'][15]['target'], 'm4')
        self.assertEqual(command['config']['groups'][0]['pads'][0]['target'], 'm2')

    def test_save_failure_can_retry_empty_or_occupied_pad(self):
        for occupied in (False, True):
            with self.subTest(occupied=occupied):
                self.setUp()
                if occupied:
                    self.config_pad()
                original = self.c.export_config()
                self.direct()
                commands = button(self.c, 'pad', 0)
                if occupied:
                    commands = button(self.c, 'select')
                self.ack(commands[0], False)
                self.assertFalse(self.c.snapshot()['saving'])
                self.assertEqual(self.c.export_config(), original)
                self.assertIn('disk full', self.c.snapshot()['error'])
                retry = button(self.c, 'select') if occupied else button(self.c, 'pad', 0)
                self.ack(retry[0])
                self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm1')

    def test_concurrent_pad_change_blocks_old_confirm_until_reselected(self):
        self.config_pad()
        self.direct()
        button(self.c, 'pad', 0)
        self.config_pad(target='m3', values={'p0': .8})
        self.assertEqual(button(self.c, 'select'), [])
        self.assertIn('inzwischen', self.c.snapshot()['error'])
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm3')
        button(self.c, 'pad', 0)
        command, = button(self.c, 'select')
        self.ack(command)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm1')

    def test_pending_direct_save_blocks_cancel_new_target_and_duplicate_confirmation(self):
        self.direct()
        command, = button(self.c, 'pad', 3)
        for name, index in (('browse',0), ('select',0), ('group',7), ('pad',15)):
            self.assertEqual(button(self.c, name, index), [])
        self.move(0, 1)
        self.assertEqual((self.c.bank, self.c.pad_index), (0, 3))
        self.assertEqual(press(self.c), [])
        self.ack(command)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][3]['target'], 'm1')
        self.assertEqual(self.c.export_config()['groups'][7]['pads'][15]['target'], '')

    def test_unavailable_material_rechecked_before_pad_and_before_confirmation(self):
        for after_pad in (False, True):
            with self.subTest(after_pad=after_pad):
                self.setUp()
                self.config_pad()
                self.direct()
                if after_pad:
                    button(self.c, 'pad', 0)
                self.c.set_context(dict(catalog=[m for m in self.catalog if m['id'] != 'm1']))
                self.assertEqual(button(self.c, 'select') if after_pad else button(self.c, 'pad', 0), [])
                self.assertIn('nicht mehr verfügbar', self.c.snapshot()['error'])
                self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm2')

    def test_favorites_and_existing_assignment_browser_category_context(self):
        config = self.c.export_config()
        config['favorites'] = ['m23']
        self.c.set_context(dict(config=config))
        self.browse()
        button(self.c, 'top', 1)
        button(self.c, 'select')
        self.assertEqual(self.c.direct_target, 'm23')
        button(self.c, 'select')
        self.assertEqual(self.c.browse_filter, 'favorites')
        button(self.c, 'scene')
        press(self.c)
        press(self.c)
        self.assertEqual(self.c.browse_purpose, 'assign')
        button(self.c, 'top', 2)
        self.c.category_index = 3
        press(self.c)
        self.assertEqual(self.c.browse_purpose, 'assign')
        self.assertEqual(press(self.c), [])
        self.assertEqual(self.c.screen, 'confirm_assign')
        self.assertEqual(self.c.assign_target, 'm3')
        command, = press(self.c)
        self.ack(command)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm3')
        self.assertEqual(self.c.export_config()['favorites'], ['m23'])

    def test_direct_flow_clears_old_scene_assignment_context_on_cancel_or_success(self):
        for outcome in ('cancel', 'success'):
            with self.subTest(outcome=outcome):
                self.setUp()
                button(self.c, 'scene')
                press(self.c)
                press(self.c)
                self.assertEqual(self.c.browse_purpose, 'assign')
                self.assertIsNotNone(self.c._draft_base)
                self.c.browse_index = 4
                button(self.c, 'select')
                button(self.c, 'group', 1)
                if outcome == 'success':
                    command, = button(self.c, 'pad', 1)
                    self.ack(command)
                else:
                    button(self.c, 'select')
                self.assertEqual(self.c.screen, 'browse')
                self.assertEqual(self.c.browse_purpose, 'load')
                self.assertIsNone(self.c.assign_target)
                self.assertIsNone(self.c._draft_base)
                before = self.c.export_config()
                self.assertEqual(press(self.c), [dict(action='load_material', material_id='m4', values={})])
                self.assertEqual(self.c.export_config(), before)
                self.assertEqual(before['groups'][0]['pads'][0]['target'], '')
                self.assertEqual(before['groups'][1]['pads'][0]['target'], '')
                self.assertEqual(before['groups'][1]['pads'][1]['target'], 'm4' if outcome == 'success' else '')


class BrowserConnectionResetTests(unittest.TestCase):
    # Reuse only setup, not the inherited test suite, for the real Manager queue.
    setUp = favorites_fixture.FavoritesManagerTests.setUp

    def test_connection_reset_resets_browser_speed_before_next_queued_detent(self):
        manager = self.manager
        config = manager.controller.export_config()
        config['hardware'] = True
        manager.controller.set_context(dict(config=config))
        self.library._items = [dict(id='m%d'%i, label='%03d'%i) for i in range(100)]
        manager.refresh_catalog()
        button(manager, 'browse')
        for t in (0, .02, .04):
            manager.dispatch(dict(type='wheel', delta=1, timestamp=t))
        self.assertEqual(manager.controller.browse_index, 10)
        manager.post_event(dict(type='connection_reset'), manager.version)
        manager.tick()
        manager.dispatch(dict(type='wheel', delta=1, timestamp=.06))
        self.assertEqual(manager.controller.browse_index, 11)


if __name__ == '__main__':
    unittest.main()
