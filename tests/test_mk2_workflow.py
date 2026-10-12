"""Durable, device-independent acceptance tests for the MK2 0.2 workflows."""
from copy import deepcopy
import json
import unittest

from pixelblaze_mapper.mk2_workflow import Controller, validate_config


def parameter(index, **changes):
    result = dict(id='p%d' % index, label='Parameter %d' % index, value=.5,
                  min=0, max=1, step=.1, type='float', section='td' if index < 8 else 'native')
    result.update(changes)
    return result


def material(index, count=8):
    return dict(id='m%d' % index, label='Material %d' % index, category='Test', image='image%d' % index,
                parameters=[parameter(i) for i in range(count)])


class WorkflowCase(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.c = Controller(clock=lambda: self.now)
        self.catalog = [material(0, 25), material(1), material(2)]
        self.c.set_context(dict(active_material=self.catalog[0], catalog=self.catalog,
                                show=dict(id='cue1', material=self.catalog[1], duration=10, elapsed=2,
                                          transition='crossfade', transition_duration=1, playing=True,
                                          parameters=self.catalog[0]['parameters'],
                                          automated_ids=['p9'], modified_ids=['p3']),
                                transitions=['cut', 'crossfade', 'wipe']))

    def button(self, name, index=0):
        result = self.c.dispatch(dict(type='button', name=name, index=index, down=True))
        return result+self.c.dispatch(dict(type='button', name=name, index=index, down=False))

    def wheel(self, delta):
        return self.c.dispatch(dict(type='wheel', delta=delta))

    def press(self):
        return self.c.dispatch(dict(type='wheel_press'))

    def encoder(self, index=0, delta=1):
        return self.c.dispatch(dict(type='encoder', index=index, delta=delta))

    def assign(self, bank=0, pad=0, target='m0', values=None):
        config = self.c.export_config()
        config['groups'][bank]['pads'][pad] = dict(kind='material', target=target, values=values or {})
        self.c.set_context(dict(config=config))

    def edit(self):
        self.assign()
        self.button('scene')
        self.press()
        self.wheel(1)
        self.press()
        self.assertEqual(self.c.screen, 'pad_edit')

    def show(self, recording=False):
        self.c.set_context(dict(mode='show', recording=recording))

    def ack(self, command, success=True):
        return self.c.dispatch(dict(type='command_result', request_id=command['request_id'], success=success, error='disk full'))


class ConfigurationTests(WorkflowCase):
    def test_migrate_legacy_bank_without_losing_cue_or_hardware(self):
        old = dict(hardware=True, pads=[dict(kind='cue' if i == 3 else 'material', target=str(i)) for i in range(16)])
        result = validate_config(old)
        self.assertEqual(result['schema_version'], 2)
        self.assertTrue(result['hardware'])
        self.assertEqual(result['groups'][0]['pads'][3], dict(kind='cue', target='3', values={}))
        self.assertEqual([g['name'] for g in result['groups']], list('ABCDEFGH'))
        self.assertTrue(all(not p['target'] for g in result['groups'][1:] for p in g['pads']))

    def test_json_round_trip_preserves_eight_banks_and_presets(self):
        self.assign(7, 15, values={'p0': .125, 'enabled': True})
        saved = json.loads(json.dumps(self.c.export_config()))
        restored = Controller(saved)
        self.assertEqual(saved, restored.export_config())

    def test_config_and_snapshot_are_deep_copies(self):
        config = self.c.export_config()
        config['groups'][0]['pads'][0]['target'] = 'injected'
        snap = self.c.snapshot()
        snap['material']['parameters'][0]['value'] = 42
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')
        self.assertEqual(self.c.snapshot()['material']['parameters'][0]['value'], .5)

    def test_reject_future_schema_bad_sizes_and_nonfinite_values(self):
        for config in (dict(schema_version=99), dict(groups=[]), dict(pads=[])):
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_config(config)
        config = self.c.export_config()
        for value in (float('nan'), float('inf'), '3', [1, 2]):
            config['groups'][0]['pads'][0]['values'] = {'p': value}
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_config(config)


class MaterialAcceptanceTests(WorkflowCase):
    def test_master_speed_is_identifiable_on_compact_td_display(self):
        active = material(0)
        active['parameters'][0].update(id='global_master_speed', label='Master speed')
        self.c.set_context(dict(active_material=active))
        displayed = self.c.snapshot()['parameter_pages'][0]['parameters'][0]
        self.assertEqual(displayed['abbreviation'], 'Speed')
        self.assertEqual(displayed['label'], 'Master speed')

    def test_default_active_material_and_td_native_eight_parameter_pages(self):
        state = self.c.snapshot()
        self.assertEqual((state['mode'], state['screen'], state['material']['id']), ('material', 'home', 'm0'))
        self.assertEqual([p['label'] for p in state['parameter_pages']], ['TD', 'MM 1', 'MM 2', 'MM 3'])
        self.assertEqual([len(p['parameters']) for p in state['parameter_pages']], [8, 8, 8, 1])
        self.button('top', 2)
        self.assertEqual(self.encoder()[0]['parameter_id'], 'p16')

    def test_td_only_material_has_one_page_and_unused_top_buttons_do_nothing(self):
        self.c.set_context(dict(active_material=self.catalog[1]))
        self.button('top', 7)
        self.assertEqual(len(self.c.snapshot()['parameter_pages']), 1)
        self.assertEqual(self.c.page, 0)

    def test_more_than_sixtyfour_parameters_reports_inaccessible_overflow(self):
        self.c.set_context(dict(active_material=material(0, 73)))
        state = self.c.snapshot()
        self.assertEqual(len(state['parameter_pages']), 8)
        self.assertEqual(state['parameter_overflow'], 9)

    def test_runtime_parameter_waits_for_host_confirmation(self):
        command = self.encoder()[0]
        self.assertEqual(command, dict(action='set_parameter', parameter_id='p0', value=.6, material_id='m0'))
        self.assertEqual(self.c.snapshot()['parameter_pages'][0]['parameters'][0]['value'], .5)
        changed = deepcopy(self.catalog[0])
        changed['parameters'][0]['value'] = .6
        self.c.set_context(dict(active_material=changed))
        self.assertEqual(self.encoder()[0]['value'], .7)

    def test_encoder_bounds_type_steps_and_unsupported_type(self):
        self.assertEqual(self.encoder(delta=999)[0]['value'], 1)
        self.assertEqual(self.encoder(delta=-999)[0]['value'], 0)
        for kind, current, expected in [('int', 3, 4), ('bool', False, True), ('enum', 0, 1)]:
            m = material(0, 1)
            m['parameters'][0].update(type=kind, value=current, min=0, max=10, step=1, options=['a', 'b'])
            self.c.set_context(dict(active_material=m))
            self.assertEqual(self.encoder()[0]['value'], expected)
        m['parameters'][0].update(type='image')
        self.c.set_context(dict(active_material=m))
        self.assertEqual(self.encoder(), [])
        self.assertFalse(self.c.snapshot()['parameter_pages'][0]['parameters'][0]['editable'])

    def test_browse_wheel_does_not_load_until_press_and_displays_assignments(self):
        self.assign(3, 11, 'm1')
        self.button('browse')
        self.assertEqual(self.wheel(1), [])
        self.assertEqual(self.c.snapshot()['browse_items'][1]['assignments'], [dict(group=3, pad=11)])
        self.assertEqual(self.press(), [dict(action='load_material', material_id='m1', values={})])
        self.assertEqual(self.c.snapshot()['material']['id'], 'm0')

    def test_browse_clamps_empty_and_missing_or_unsupported_material(self):
        self.button('browse')
        self.wheel(-99)
        self.assertEqual(self.c.browse_index, 0)
        self.wheel(99)
        self.assertEqual(self.c.browse_index, 2)
        self.c.set_context(dict(catalog=[]))
        self.assertEqual(self.press(), [])
        unsupported = material(0)
        unsupported['compatibility'] = 'unsupported'
        self.c.set_context(dict(catalog=[unsupported]))
        self.assertEqual(self.press(), [])

    def test_eight_groups_and_physical_pads_load_presets_flash_red(self):
        self.assign(7, 15, 'm1', {'p0': .2})
        self.button('group', 7)
        commands = self.button('pad', 15)
        self.assertEqual(commands[0], dict(action='flash_pad', group=7, index=15, color='red'))
        self.assertEqual(commands[1], dict(action='load_material', material_id='m1', values={'p0': .2}))
        self.assertTrue(self.c.snapshot()['group_has_content'][7])
        self.assertTrue(self.c.snapshot()['pad_flash'][15])
        self.now += .25
        self.assertFalse(self.c.snapshot()['pad_flash'][15])

    def test_empty_pad_and_missing_material_never_load(self):
        self.assertEqual([c['action'] for c in self.button('pad')], ['flash_pad'])
        self.assign(target='deleted')
        self.assertEqual([c['action'] for c in self.button('pad')], ['flash_pad'])
        self.assertFalse(self.c.snapshot()['cards'][0]['available'])

    def test_legacy_cue_assignment_remains_callable(self):
        config = self.c.export_config()
        config['groups'][0]['pads'][0] = dict(kind='cue', target='legacycue', values={})
        self.c.set_context(dict(config=config))
        self.assertEqual(self.button('pad')[-1], dict(action='load_cue', cue_id='legacycue'))


class PadEditingAcceptanceTests(WorkflowCase):
    def start_assignment(self):
        self.button('scene')
        self.press()
        self.assertEqual(self.c.snapshot()['menu'], ['browse'])
        self.press()
        self.wheel(1)
        self.assertEqual(self.press(), [])
        self.assertEqual(self.c.screen, 'confirm_assign')
        self.assertEqual(self.c.snapshot()['confirm']['choice'], 0)

    def test_assignment_requires_confirm_then_successful_persistence(self):
        self.start_assignment()
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')
        command = self.press()[0]
        self.assertEqual(command['action'], 'persist_config')
        self.assertEqual(command['config']['groups'][0]['pads'][0]['target'], 'm1')
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')
        self.assertEqual(self.press(), [])
        self.ack(command)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm1')
        self.assertEqual(self.c.screen, 'pad_grid')

    def test_assignment_cancel_leaves_all_banks_untouched(self):
        before = self.c.export_config()
        self.start_assignment()
        self.wheel(1)
        self.assertEqual(self.press(), [])
        self.assertEqual(self.c.export_config(), before)
        self.assertEqual(self.c.screen, 'pad_grid')

    def test_failed_save_keeps_config_and_allows_retry(self):
        self.start_assignment()
        command = self.press()[0]
        self.ack(command, False)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')
        self.assertIn('disk full', self.c.snapshot()['error'])
        retried = self.press()[0]
        self.assertGreater(retried['request_id'], command['request_id'])
        self.ack(command)  # stale asynchronous acknowledgement must not commit.
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')
        self.ack(retried)
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], 'm1')

    def test_catalog_removal_during_confirmation_does_not_assign(self):
        self.start_assignment()
        self.c.set_context(dict(catalog=[]))
        self.assertEqual(self.press(), [])
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['target'], '')

    def test_edit_never_activates_material_and_requires_save(self):
        self.edit()
        self.assertEqual(self.encoder(), [])
        self.assertTrue(self.c.snapshot()['dirty'])
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['values'], {})
        self.press()
        command = self.press()[0]
        self.assertEqual(command['config']['groups'][0]['pads'][0]['values'], {'p0': .6})
        self.ack(command)
        self.assertEqual(self.c.context['active_material']['id'], 'm0')

    def test_clean_edit_idle_returns_exactly_after_twenty_seconds(self):
        self.edit()
        self.now += 19.99
        self.c.tick()
        self.assertEqual(self.c.screen, 'pad_edit')
        self.now += .01
        self.assertEqual(self.c.tick(), [])
        self.assertEqual(self.c.screen, 'pad_grid')

    def test_dirty_idle_requests_save_cancel_and_cancel_discards(self):
        self.edit()
        self.encoder()
        self.now += 20
        self.c.tick()
        self.assertEqual(self.c.screen, 'confirm_edit')
        self.assertEqual(self.c.snapshot()['confirm']['options'], ['Save', 'Cancel'])
        self.wheel(1)
        self.press()
        self.assertEqual(self.c.export_config()['groups'][0]['pads'][0]['values'], {})

    def test_edit_returned_to_original_value_counts_clean(self):
        self.edit()
        self.encoder(delta=1)
        self.encoder(delta=-1)
        self.assertFalse(self.c.snapshot()['dirty'])
        self.now += 20
        self.c.tick()
        self.assertEqual(self.c.screen, 'pad_grid')

    def test_dirty_edit_navigation_does_not_lose_values_or_switch_group(self):
        self.edit()
        self.encoder()
        self.assertEqual(self.button('group', 5), [])
        self.assertEqual(self.c.bank, 0)
        self.assertEqual(self.c.screen, 'confirm_edit')
        self.assertEqual(self.button('step'), [])
        self.assertEqual(self.c.mode, 'material')

    def test_external_mode_change_preserves_dirty_draft_for_save_or_cancel(self):
        self.edit()
        self.encoder()
        self.c.set_context(dict(mode='show'))
        self.assertEqual(self.c.screen, 'confirm_edit')
        self.assertTrue(self.c.snapshot()['dirty'])
        self.assertIn('extern', self.c.snapshot()['error'])
        command = self.press()[0]
        self.assertEqual(command['config']['groups'][0]['pads'][0]['values'], {'p0': .6})
        self.ack(command)
        self.assertEqual((self.c.mode, self.c.screen), ('show', 'home'))

    def test_recording_cannot_start_with_dirty_draft_confirmation_or_pending_save(self):
        self.edit()
        self.encoder()
        self.assertEqual(self.button('rec'), [])
        self.assertEqual(self.c.screen, 'confirm_edit')
        self.c.set_context(dict(mode='show'))
        for pending in (False, True):
            if pending:
                save = self.press()[0]
                self.assertTrue(self.c.snapshot()['saving'])
            self.assertEqual(self.button('rec'), [])
            self.c.dispatch(dict(type='button', name='erase', down=True))
            self.assertEqual(self.button('rec'), [])
            self.c.dispatch(dict(type='button', name='erase', down=False))
            self.assertTrue(self.c.snapshot()['dirty'])
            self.assertFalse(self.c.snapshot()['recording'])
        self.ack(save)
        self.assertEqual(self.button('rec'), [dict(action='record_start', kind='new_cue')])

    def test_concurrent_reassignment_cannot_receive_old_material_draft(self):
        self.edit()
        self.encoder()
        self.assign(target='m2')
        self.press()
        self.assertEqual(self.press(), [])
        self.assertEqual(self.c._pad()['target'], 'm2')
        self.assertIn('inzwischen', self.c.snapshot()['error'])

    def test_lazy_descriptor_hydrates_pad_editor(self):
        self.assign()
        self.c.set_context(dict(catalog=[dict(id='m0', label='Material 0')]))
        self.button('scene')
        self.press()
        self.wheel(1)
        self.press()
        self.assertEqual(self.c.snapshot()['parameter_pages'], [])
        self.c.set_context(dict(materials={'m0': material(0)}))
        self.encoder()
        self.assertEqual(self.c.snapshot()['parameter_pages'][0]['parameters'][0]['value'], .6)

    def test_delete_is_confirmed_and_can_be_cancelled(self):
        self.assign()
        self.button('scene')
        self.press()
        self.wheel(3)
        self.press()
        self.assertEqual(self.c.screen, 'confirm_delete')
        self.wheel(1)
        self.press()
        self.assertEqual(self.c._pad()['target'], 'm0')
        self.press()
        self.wheel(3)
        self.press()
        command = self.press()[0]
        self.ack(command)
        self.assertEqual(self.c._pad()['target'], '')


class ShowAcceptanceTests(WorkflowCase):
    def test_step_latches_only_after_host_mode_confirmation_and_debounces(self):
        down = dict(type='button', name='step', down=True)
        self.assertEqual(self.c.dispatch(down), [dict(action='set_mode', mode='show')])
        self.assertEqual(self.c.dispatch(down), [])
        self.assertEqual(self.c.mode, 'material')
        self.c.set_context(dict(mode='show'))
        self.c.dispatch(dict(type='button', name='step', down=False))
        self.assertEqual(self.button('step'), [dict(action='set_mode', mode='material')])

    def test_show_progress_remaining_and_parameter_activity(self):
        self.show()
        state = self.c.snapshot()
        self.assertIsNone(state['focused_parameter'])
        self.assertEqual(state['show']['progress'], .2)
        self.assertEqual(state['show']['remaining'], 8)
        self.assertEqual(state['group_activity'], [True, True, False, False, False, False, False, False])
        self.button('group', 1)
        self.button('pad', 1)
        self.assertEqual(self.c.snapshot()['focused_parameter']['id'], 'p9')
        self.assertTrue(self.c.snapshot()['focused_parameter']['automated'])
        self.button('top', 0)
        self.assertIsNone(self.c.snapshot()['focused_parameter'])

    def test_normal_show_encoders_are_inert(self):
        self.show()
        for i in range(8):
            self.assertEqual(self.encoder(i, 4), [])

    def test_show_wheel_focus_edit_changes_immediately_without_exit_commit(self):
        self.show()
        self.assertEqual(self.press(), [])
        command = self.wheel(2)[0]
        self.assertEqual(command, dict(action='set_show_field', cue_id='cue1', field='duration', value=10.2))
        self.assertEqual(self.c.snapshot()['show']['duration'], 10)
        self.assertEqual(self.press(), [])
        self.wheel(1)
        self.press()
        self.assertEqual(self.wheel(1)[0]['value'], 'wipe')

    def test_transition_duration_bounds_and_no_numeric_nan_commands(self):
        self.show()
        self.wheel(2)
        self.press()
        self.assertEqual(self.wheel(-127)[0]['value'], 0)
        self.assertEqual(self.wheel(127)[0]['value'], 10)
        self.assertEqual(self.wheel(float('nan')), [])
        self.assertEqual(self.encoder(delta=float('inf')), [])

    def test_play_previous_next_restart_forward_transport_intent(self):
        self.show()
        for name in ('play', 'previous', 'next', 'restart'):
            self.assertEqual(self.button(name), [dict(action='transport', command=name)])

    def test_rec_single_press_starts_new_cue_on_release(self):
        self.show()
        self.assertEqual(self.c.dispatch(dict(type='button', name='rec', down=True)), [])
        self.assertEqual(self.c.dispatch(dict(type='button', name='rec', down=False)), [dict(action='record_start', kind='new_cue')])
        self.assertFalse(self.c.snapshot()['recording'])
        self.c.set_context(dict(recording='new_cue'))
        self.assertEqual(self.encoder()[0]['action'], 'set_parameter')
        self.assertEqual(self.button('rec'), [dict(action='record_stop')])

    def test_rec_erase_chord_in_both_orders_never_starts_new_cue(self):
        for order in (('rec', 'erase'), ('erase', 'rec')):
            with self.subTest(order=order):
                self.setUp()
                self.show()
                result = []
                for name in order:
                    result += self.c.dispatch(dict(type='button', name=name, down=True))
                for name in order:
                    result += self.c.dispatch(dict(type='button', name=name, down=False))
                self.assertEqual(result, [dict(action='record_start', kind='automation')])

    def test_explicit_host_recording_disabled_keeps_existing_automation(self):
        self.show()
        self.c.set_context(dict(allow_automation_recording=False))
        self.c.dispatch(dict(type='button', name='erase', down=True))
        self.assertEqual(self.button('rec'), [])
        self.assertEqual(self.c.context['show']['automated_ids'], ['p9'])

    def test_recording_blocks_mode_clip_browser_and_clip_metadata_changes(self):
        self.show('automation')
        for name in ('step', 'play', 'previous', 'next', 'restart', 'browse', 'scene'):
            self.assertEqual(self.button(name), [])
        self.assertEqual(self.press(), [])
        self.assertFalse(self.c.show_editing)
        self.assertEqual(self.button('play'), [])
        self.button('top', 1)
        self.assertEqual(self.encoder()[0]['parameter_id'], 'p8')

    def test_unknown_and_invalid_events_are_ignored(self):
        for event in ({}, {'type': 'encoder', 'index': 8, 'delta': 1}, {'type': 'button', 'name': 'pad', 'index': -1},
                      {'type': 'button', 'name': 'group', 'index': 8}, None):
            self.assertEqual(self.c.dispatch(event), [])


if __name__ == '__main__':
    unittest.main()
