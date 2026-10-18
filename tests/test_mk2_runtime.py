"""Acceptance of real MK2 Manager pipelines with a deterministic in-memory host."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.mk2_runtime import Manager
from tests.test_mk2_workflow import material


class FakeHost:
    def __init__(self, owner):
        self.owner = owner
        self.materials = {'m0': material(0, 16), 'm1': material(1)}
        self.state = dict(mode='material', active_material=deepcopy(self.materials['m0']),
                          recording=False, show=dict(id='cue1', duration=10, elapsed=0,
                                                    material=deepcopy(self.materials['m0']),
                                                    parameters=deepcopy(self.materials['m0']['parameters'])))
        self.commands = []

    def context(self, target=None, *, metadata_only=False):
        result = deepcopy(self.state)
        result['materials'] = {target: deepcopy(self.materials[target])} if target in self.materials else {}
        return result

    def execute(self, command):
        self.commands.append(deepcopy(command))
        action = command['action']
        if action == 'set_mode':
            self.state['mode'] = command['mode']
        elif action == 'set_parameter':
            for p in self.state['active_material']['parameters']:
                if p['id'] == command['parameter_id']:
                    p['value'] = command['value']
            self.state['show']['parameters'] = deepcopy(self.state['active_material']['parameters'])
        elif action == 'load_material':
            self.state['active_material'] = deepcopy(self.materials[command['material_id']])
        elif action == 'record_start':
            self.state['recording'] = command['kind']
        elif action == 'record_stop':
            self.state['recording'] = False


class FakeSurface:
    def __init__(self, *args, **kwargs):
        self.snapshot = {}
        self.status = 'fake connected'
        self.frame_version = 0

    def start(self):
        pass

    def stop(self):
        pass


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        td = SimpleNamespace(project=SimpleNamespace(folder=self.temp.name))
        self.addCleanup(patch.stopall)
        patch.dict('sys.modules', td=td).start()
        patch('pixelblaze_mapper.mk2_td.Host', FakeHost).start()
        patch('pixelblaze_mapper.maschine_mk2.Surface', FakeSurface).start()
        library = SimpleNamespace(_items=[dict(id='m0', label='Material 0'), dict(id='m1', label='Material 1')],
                                  _safe_preview_path=lambda _: None)
        self.editor = SimpleNamespace(show=lambda: dict(cues=[]), _library=lambda: library,
                                      _state=lambda key, default='': default)
        owner = SimpleNamespace(op=lambda name: SimpleNamespace(module=self.editor))
        self.manager = Manager(owner)

    def button(self, name, index=0):
        self.manager.dispatch(dict(type='button', name=name, index=index, down=True))
        self.manager.dispatch(dict(type='button', name=name, index=index, down=False))

    def press(self):
        self.manager.dispatch(dict(type='wheel_press'))

    def wheel(self, delta):
        self.manager.dispatch(dict(type='wheel', delta=delta))

    def save_current_web_bank(self, index, target):
        config = deepcopy(self.manager.config)
        config['pads'][index] = dict(kind='material', target=target)
        self.manager.command(dict(action='pads_config', pads_version=self.manager.version, config=config))

    def enable(self):
        config = self.manager.controller.export_config()
        config['hardware'] = True
        self.manager.controller.set_context(dict(config=config))
        self.manager.update_surface()

    def begin_assignment(self):
        self.button('scene')
        self.press()
        self.press()
        self.wheel(1)
        self.press()
        self.assertEqual(self.manager.controller.screen, 'confirm_assign')

    def test_browser_legacy_assignment_preserves_other_banks_and_same_target_preset(self):
        config = self.manager.controller.export_config()
        config['groups'][0]['pads'][0] = dict(kind='material', target='m0', values={'p0': .3})
        config['groups'][7]['pads'][15] = dict(kind='material', target='m1', values={'p0': .7})
        self.manager.controller.set_context(dict(config=config))
        self.manager.update_surface()
        self.save_current_web_bank(0, 'm0')
        stored = json.loads(self.manager.path.read_text(encoding='utf-8'))
        self.assertEqual(stored['groups'][0]['pads'][0]['values'], {'p0': .3})
        self.assertEqual(stored['groups'][7]['pads'][15]['values'], {'p0': .7})
        self.save_current_web_bank(0, 'm1')
        self.assertEqual(self.manager.controller.config['groups'][0]['pads'][0]['values'], {})

    def test_web_bank_change_and_stale_assignment_version(self):
        version = self.manager.version
        self.manager.command(dict(action='pads_bank', bank=6, pads_version=version))
        self.assertEqual(self.manager.snapshot()['bank'], 6)
        with self.assertRaises(ValueError):
            self.manager.command(dict(action='pads_config', pads_version=version, config=self.manager.config))
        self.save_current_web_bank(4, 'm1')
        stored = json.loads(self.manager.path.read_text(encoding='utf-8'))
        self.assertEqual(stored['groups'][6]['pads'][4]['target'], 'm1')
        self.assertEqual(stored['groups'][0]['pads'][4]['target'], '')

    def test_physical_bank_change_invalidates_old_browser_assignment(self):
        version = self.manager.version
        old = deepcopy(self.manager.config)
        self.button('group', 3)
        self.assertGreater(self.manager.version, version)
        with self.assertRaises(ValueError):
            self.manager.command(dict(action='pads_config', pads_version=version, config=old))

    def test_encoder_changes_accumulate_from_refreshed_host_values(self):
        for _ in range(3):
            self.manager.dispatch(dict(type='encoder', index=0, delta=1))
        values = [c['value'] for c in self.manager.host.commands if c['action'] == 'set_parameter']
        self.assertEqual(values, [.6, .7, .8])
        self.assertEqual(self.manager.snapshot()['controller']['parameter_pages'][0]['parameters'][0]['value'], .8)

    def test_physical_assignment_writes_schema_and_commits_ack(self):
        self.begin_assignment()
        self.press()
        self.assertEqual(self.manager.controller.screen, 'pad_grid')
        self.assertEqual(self.manager.version, 1)
        self.assertEqual(self.manager.controller.config['groups'][0]['pads'][0]['target'], 'm1')
        self.assertEqual(json.loads(self.manager.path.read_text())['schema_version'], 2)
        self.assertFalse(self.manager.host.commands)  # Assigning must never activate.

    def test_failed_config_write_preserves_previous_assignment_and_enables_retry(self):
        self.begin_assignment()
        with patch.object(self.manager, '_write_config', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.press()
        self.assertEqual(self.manager.controller.config['groups'][0]['pads'][0]['target'], '')
        self.assertFalse(self.manager.controller.snapshot()['saving'])
        self.assertEqual(self.manager.version, 0)
        self.assertIn('disk full', self.manager.controller.snapshot()['error'])
        self.press()
        self.assertEqual(self.manager.controller.config['groups'][0]['pads'][0]['target'], 'm1')

    def test_held_rec_chord_starts_once_and_release_does_not_stop_or_newcue(self):
        self.button('step')
        rec = dict(type='button', name='rec', down=True)
        self.manager.dispatch(rec)
        self.manager.dispatch(rec)
        self.manager.dispatch(dict(type='button', name='erase', down=True))
        self.manager.dispatch(rec)
        self.manager.dispatch(dict(type='button', name='erase', down=False))
        self.manager.dispatch(dict(type='button', name='rec', down=False))
        recording = [c for c in self.manager.host.commands if c['action'].startswith('record_')]
        self.assertEqual(recording, [dict(action='record_start', kind='automation')])
        self.button('rec')
        self.assertEqual(self.manager.host.commands[-1], dict(action='record_stop'))

    def test_stale_release_without_index_clears_latch_and_pending_rec_without_starting(self):
        self.enable()
        self.button('step')
        self.manager.dispatch(dict(type='button', name='rec', down=True))
        self.manager.post_event(dict(type='button', name='rec', down=False), self.manager.version-1)
        self.manager.tick()
        self.assertNotIn(('rec', 0), self.manager.controller.held)
        self.assertFalse(self.manager.controller.rec_pending)
        self.assertFalse(any(c['action'] == 'record_start' for c in self.manager.host.commands))
        self.button('rec')
        self.assertEqual(self.manager.host.commands[-1], dict(action='record_start', kind='new_cue'))

    def test_stale_device_pad_events_do_not_activate_current_bank(self):
        self.enable()
        self.save_current_web_bank(0, 'm1')
        self.manager.post(0, self.manager.version-1)
        self.manager.tick()
        self.assertFalse(any(c['action'] == 'load_material' for c in self.manager.host.commands))
        self.manager.post(0, self.manager.version)
        self.manager.tick()
        self.assertEqual(self.manager.host.commands[-1]['material_id'], 'm1')

    def test_disabled_hardware_drops_events_and_releases_held_buttons(self):
        self.enable()
        self.manager.tick()
        self.manager.dispatch(dict(type='button', name='erase', down=True))
        config = self.manager.controller.export_config()
        config['hardware'] = False
        self.manager.controller.set_context(dict(config=config))
        self.manager.tick()
        self.assertFalse(self.manager.controller.held)
        self.assertIsNone(self.manager.worker)

    def test_disconnect_clears_held_rec_and_discards_queued_actions_before_release(self):
        self.enable()
        self.button('step')
        self.manager.dispatch(dict(type='button', name='rec', down=True))
        self.manager.post_event(dict(type='button', name='rec', down=False), self.manager.version)
        self.manager.post_event(dict(type='connection_reset'), self.manager.version-1)
        self.assertEqual(self.manager.events.qsize(), 1)
        self.manager.tick()
        self.assertFalse(self.manager.controller.held)
        self.assertFalse(self.manager.controller.rec_pending)
        self.manager.dispatch(dict(type='button', name='rec', down=False))
        self.assertFalse(any(c['action']=='record_start' for c in self.manager.host.commands))
        self.button('rec')
        self.assertEqual(self.manager.host.commands[-1], dict(action='record_start',kind='new_cue'))

    def test_connection_reset_has_priority_over_full_queue_and_keeps_existing_take(self):
        self.enable()
        self.button('step')
        self.button('rec')
        for _ in range(128):
            self.manager.post_event(dict(type='wheel',delta=1), self.manager.version)
        self.manager.post_event(dict(type='connection_reset'), self.manager.version)
        self.assertEqual(self.manager.events.qsize(), 1)
        self.manager.tick()
        self.assertEqual(self.manager.host.state['recording'], 'new_cue')
        self.assertFalse(any(c['action']=='record_stop' for c in self.manager.host.commands))


if __name__ == '__main__':
    unittest.main()
