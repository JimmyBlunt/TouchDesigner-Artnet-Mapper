"""Connected offline acceptance: raw HID -> real decoder/queue/workflow/render.

The USB surface and TouchDesigner host are doubles. No live hardware or project is
touched. This suite asserts command routing, persistence and rendered states;
real automation curve semantics are covered by the separate TD adapter suites.
"""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper import maschine_mk2 as hardware
from pixelblaze_mapper.mk2_runtime import Manager
from tests.test_mk2_runtime import FakeHost, FakeSurface


class ScenarioHost(FakeHost):
    """Host acknowledgement double, deliberately not an automation renderer."""
    def __init__(self, owner):
        super().__init__(owner)
        self.state['transitions'] = ['cut', 'crossfade', 'wipe']
        self.state['show'].update(transition='crossfade', transition_duration=1., transition_progress=0.,
                                  playing=False, automated_ids=['p9'], modified_ids=['p0'])
        self.cue_ids = ['cue1', 'cue2']
        self.cue_index = 0
        self.fail_load = None

    def execute(self, command):
        if command['action'] == 'load_material' and command['material_id'] == self.fail_load:
            raise ValueError('Simulierter Ladefehler: bisheriges Material bleibt aktiv.')
        super().execute(command)
        if command['action'] == 'load_material':
            for p in self.state['active_material']['parameters']:
                if p['id'] in command.get('values', {}):
                    p['value'] = command['values'][p['id']]
        elif command['action'] == 'set_show_field':
            self.state['show'][command['field']] = command['value']
        elif command['action'] == 'record_start':
            if command['kind'] == 'new_cue':
                self.cue_ids.append('cue_new_%d' % len(self.cue_ids))
                self.state['show']['id'] = self.cue_ids[-1]
            self.state['show']['playing'] = True
        elif command['action'] == 'transport':
            operation = command['command']
            if operation == 'next':
                self.cue_index = min(len(self.cue_ids)-1, self.cue_index+1)
            elif operation == 'previous':
                self.cue_index = max(0, self.cue_index-1)
            elif operation == 'restart':
                self.cue_index = 0
                self.state['show']['elapsed'] = 0
            self.state['show'].update(id=self.cue_ids[self.cue_index], playing=True)


class Rig:
    """Only bytes enter production input paths; no direct Controller dispatch."""
    def __init__(self):
        self.stack = ExitStack()
        self.folder = Path(self.stack.enter_context(TemporaryDirectory()))
        self.stack.enter_context(patch.dict('sys.modules', td=SimpleNamespace(project=SimpleNamespace(folder=str(self.folder)))))
        self.stack.enter_context(patch('pixelblaze_mapper.mk2_td.Host', ScenarioHost))
        self.stack.enter_context(patch('pixelblaze_mapper.maschine_mk2.Surface', FakeSurface))
        library = SimpleNamespace(_items=[dict(id='m0', label='Material 0', category='Geometry'),
                                          dict(id='m1', label='Material 1', category='Colour')],
                                  _safe_preview_path=lambda _: None)
        editor = SimpleNamespace(show=lambda: dict(cues=[]), _library=lambda: library,
                                 _state=lambda key, default='': default)
        self.owner = SimpleNamespace(op=lambda _: SimpleNamespace(module=editor))
        self.now = 10.0
        self.screens = set()
        self.restart()
        config = deepcopy(self.manager.config)
        config['hardware'] = True
        self.manager.command(dict(action='pads_config', config=config, pads_version=self.manager.version))
        self.manager.tick()

    def close(self):
        self.stack.close()

    def restart(self):
        self.manager = Manager(self.owner)
        self.manager.controller.clock = lambda: self.now
        self.manager.controller.last_activity = self.now
        self.edges, self.pads = hardware.ControlEdges(), hardware.PadEdges()
        self.report = bytearray(25)
        self.report[0] = 1
        for i in range(8):
            self.report[9+2*i:11+2*i] = (500).to_bytes(2, 'little')
        self.edges.read(self.report)
        baseline = bytes([0x20])+bytes(32)
        for _ in range(3):
            self.pads.read(baseline)
        self.manager.tick()

    @property
    def host(self):
        return self.manager.host

    @property
    def controller(self):
        return self.manager.controller

    def send(self):
        for event in self.edges.read(bytes(self.report)):
            self.manager.post_event(event, self.manager.version)
        self.manager.tick()

    def down(self, name, index=None):
        offset, bit = next(key for key, value in hardware.BUTTONS.items() if value == (name, index))
        self.report[offset] |= 1 << bit
        self.send()

    def up(self, name, index=None):
        offset, bit = next(key for key, value in hardware.BUTTONS.items() if value == (name, index))
        self.report[offset] &= ~(1 << bit)
        self.send()

    def button(self, name, index=None):
        self.down(name, index)
        self.up(name, index)

    def press(self):
        self.button('wheel')

    def wheel(self, steps):
        for _ in range(abs(steps)):
            self.report[8] = (self.report[8]+(1 if steps > 0 else -1)) % 16
            self.send()

    def encoder(self, index=0, counts=15):
        offset = 9+2*index
        current = int.from_bytes(self.report[offset:offset+2], 'little')
        self.report[offset:offset+2] = ((current+counts) % 1000).to_bytes(2, 'little')
        self.send()

    def pad(self, physical_index, pressure=80, release=True):
        report = bytearray([0x20])+bytearray(32)
        usb_index = next(i for i in range(16) if hardware.physical_pad(i) == physical_index)
        report[1+usb_index*2] = pressure & 255
        report[2+usb_index*2] = (usb_index << 4) | ((pressure >> 8) & 15)
        for _ in range(3):
            for index in self.pads.read(report):
                self.manager.post(index, self.manager.version)
            self.manager.tick()
        if release:
            for _ in range(3):
                self.pads.read(bytes([0x20])+bytes(32))

    def idle(self, seconds):
        self.now += seconds
        self.manager.tick()

    def state(self, screen=None):
        self.manager.update_surface()
        view = self.controller.snapshot()
        if screen is not None and view['screen'] != screen:
            raise AssertionError('Expected screen %s, got %s: %s' % (screen, view['screen'], view.get('error')))
        self.screens.add(view['screen'])
        snapshot = dict(controller=view, images={}, cards=view['cards'], selected=view['pad_index'])
        images = hardware.render(snapshot)
        for display, image in enumerate(images):
            assert image.size == (256, 64) and image.mode == '1'
            assert image.getbbox() is not None, 'Visible display must not be blank'
            packets = list(hardware.display_packets(display, image.tobytes()))
            assert len(packets) == 8 and all(len(p) == 265 for p in packets)
        return view, tuple(image.tobytes() for image in images)

    def assign_empty(self, material_index=1, confirm=True):
        self.press()
        self.state('pad_menu')
        assert self.controller.snapshot()['menu'] == ['browse']
        self.press()
        self.state('browse')
        self.wheel(material_index)
        self.press()
        self.state('confirm_assign')
        if not confirm:
            self.wheel(1)
        self.press()
        self.state('pad_grid')

    def edit_selected(self):
        self.press()
        self.wheel(1)
        self.press()
        self.state('pad_edit')


class ConnectedScenarios(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.addCleanup(self.r.close)

    def test_material_browse_load_native_pages_and_encoder_images(self):
        """G01–G03/G05–G06, M01–M04: bytes to active material and display."""
        r = self.r
        home, before = r.state('home')
        self.assertEqual(home['material']['id'], 'm0')
        self.assertEqual([p['label'] for p in home['parameter_pages']], ['TD', 'MM 1'])
        r.button('top', 1)
        _, native = r.state('home')
        self.assertNotEqual(before, native)
        r.encoder(2)
        self.assertEqual(r.host.commands[-1], dict(action='set_parameter', parameter_id='p10', value=.6, material_id='m0'))
        self.assertNotEqual(native[1], r.state()[1][1])
        r.button('browse')
        r.state('browse')
        r.wheel(1)
        self.assertEqual(r.host.state['active_material']['id'], 'm0')
        r.press()
        self.assertEqual(r.host.state['active_material']['id'], 'm1')
        r.button('browse')
        after, display = r.state('home')
        self.assertEqual(after['material']['id'], 'm1')
        self.assertEqual(len(after['parameter_pages']), 1)
        self.assertNotEqual(before[0], display[0])

    def test_bank_assignment_confirmation_preset_select_delete_and_restart(self):
        """G07, M05–M08/M10, D1: complete bank D pad 6 lifecycle."""
        r = self.r
        r.button('scene')
        r.button('group', 3)
        r.wheel(5)
        self.assertEqual((r.controller.bank, r.controller.pad_index), (3, 5))
        initial = r.controller.export_config()
        r.assign_empty(confirm=False)
        self.assertEqual(r.controller.export_config(), initial)
        self.assertFalse(any(c['action'] == 'load_material' for c in r.host.commands))
        r.assign_empty()
        self.assertEqual(r.controller.config['groups'][3]['pads'][5]['target'], 'm1')
        r.edit_selected()
        r.encoder()
        self.assertEqual(r.host.state['active_material']['id'], 'm0')
        self.assertFalse(any(c['action'] == 'set_parameter' for c in r.host.commands))
        r.press()
        r.state('confirm_edit')
        r.press()
        r.state('pad_grid')
        self.assertEqual(r.controller.config['groups'][3]['pads'][5]['values'], {'p0': .6})
        saved = json.loads(r.manager.path.read_text(encoding='utf-8'))
        r.restart()
        self.assertEqual(r.controller.export_config(), saved)
        r.button('group', 3)
        r.pad(5)
        self.assertEqual(r.host.state['active_material']['id'], 'm1')
        self.assertEqual(r.host.state['active_material']['parameters'][0]['value'], .6)
        self.assertTrue(r.state()[0]['pad_flash'][5])
        r.button('scene')
        r.press()  # Select from the saved pad's menu.
        r.press()
        self.assertEqual(r.host.commands[-1]['values'], {'p0': .6})
        r.wheel(3)
        r.press()
        r.state('confirm_delete')
        r.wheel(1)
        r.press()
        self.assertEqual(r.controller.config['groups'][3]['pads'][5]['target'], 'm1')
        r.press()
        r.wheel(3)
        r.press()
        r.press()
        self.assertEqual(r.controller.config['groups'][3]['pads'][5]['target'], '')
        r.restart()
        self.assertEqual(r.controller.config['groups'][3]['pads'][5]['target'], '')
        self.assertEqual(r.controller.config['groups'][0]['pads'], initial['groups'][0]['pads'])

    def test_edit_idle_clean_dirty_cancel_save_and_external_mode(self):
        """M08–M09: timers, cancellation, external mode and persisted draft."""
        r = self.r
        r.button('scene')
        r.assign_empty(material_index=0)
        r.edit_selected()
        r.idle(19.99)
        r.state('pad_edit')
        r.idle(.01)
        r.state('pad_grid')
        r.edit_selected()
        r.encoder()
        r.idle(19)
        r.encoder(counts=10)  # Resets idle; values .5 -> .6 -> .7.
        r.idle(19.99)
        r.state('pad_edit')
        r.idle(.01)
        r.state('confirm_edit')
        r.wheel(1)
        r.press()
        self.assertEqual(r.controller.config['groups'][0]['pads'][0]['values'], {})
        r.edit_selected()
        r.encoder(counts=10)
        r.host.state['mode'] = 'show'  # Simulated host's external mode switch.
        r.manager.tick()
        self.assertEqual(r.state('confirm_edit')[0]['mode'], 'show')
        self.assertTrue(r.controller.snapshot()['dirty'])
        commands = len(r.host.commands)
        r.button('rec')
        r.down('erase')
        r.button('rec')
        r.up('erase')
        self.assertEqual(len(r.host.commands), commands)
        self.assertFalse(r.host.state['recording'])
        r.state('confirm_edit')
        r.press()
        self.assertEqual(r.state('home')[0]['mode'], 'show')
        self.assertEqual(r.controller.config['groups'][0]['pads'][0]['values'], {'p0': .6})
        self.assertFalse(any(c['action'] == 'set_parameter' for c in r.host.commands))

    def test_show_metadata_transport_focus_activity_and_inert_encoders(self):
        """G01, S01–S06/S10: real focus workflow and render changes."""
        r = self.r
        r.button('step')
        start, before = r.state('home')
        self.assertEqual(start['mode'], 'show')
        self.assertIsNone(start['focused_parameter'])
        r.press()
        r.wheel(2)
        self.assertEqual(r.host.state['show']['duration'], 10.2)
        r.press()
        r.wheel(1)
        r.press()
        r.wheel(1)
        self.assertEqual(r.host.state['show']['transition'], 'wipe')
        r.press()
        r.wheel(1)
        r.press()
        r.wheel(2)
        self.assertEqual(r.host.state['show']['transition_duration'], 1.2)
        r.press()
        r.button('group', 1)
        r.pad(1)
        view, focused = r.state('home')
        self.assertEqual(view['focused_parameter']['id'], 'p9')
        self.assertTrue(view['focused_parameter']['automated'])
        self.assertNotEqual(before[1], focused[1])
        count = len(r.host.commands)
        r.encoder(1, 25)
        self.assertEqual(len(r.host.commands), count)
        r.button('top', 0)
        self.assertIsNone(r.state()[0]['focused_parameter'])
        r.button('play')
        r.button('next')
        self.assertEqual(r.host.state['show']['id'], 'cue2')
        r.button('previous')
        self.assertEqual(r.host.state['show']['id'], 'cue1')
        r.host.state['show'].update(elapsed=5.1, transition_progress=.5)
        r.manager.tick()
        middle, middle_frames = r.state()
        self.assertEqual(middle['show']['progress'], .5)
        self.assertNotEqual(before[0], middle_frames[0])
        r.button('restart')
        self.assertEqual(r.host.state['show']['elapsed'], 0)

    def test_both_recording_workflows_lock_transport_and_restore_encoder_policy(self):
        """S06–S10: physical REC release/chord, lock matrix, page encoder route."""
        r = self.r
        r.button('step')
        old_count = len(r.host.cue_ids)
        r.down('rec')
        r.send()  # Held duplicate report must never create a second command.
        self.assertFalse(r.host.state['recording'])
        r.up('rec')
        self.assertEqual(r.host.state['recording'], 'new_cue')
        self.assertEqual(len(r.host.cue_ids), old_count+1)
        r.button('top', 1)
        r.encoder(3)
        self.assertEqual(r.host.commands[-1]['parameter_id'], 'p11')
        self.assertEqual(r.host.commands[-1]['action'], 'set_parameter')
        before = len(r.host.commands)
        for name in ('step', 'browse', 'scene', 'play', 'previous', 'next', 'restart'):
            r.button(name)
        self.assertEqual(len(r.host.commands), before)
        r.button('rec')
        self.assertFalse(r.host.state['recording'])
        before = len(r.host.commands)
        r.encoder(3, 20)
        self.assertEqual(len(r.host.commands), before)
        for order in (('rec', 'erase'), ('erase', 'rec')):
            count = len(r.host.cue_ids)
            starts = sum(c['action'] == 'record_start' for c in r.host.commands)
            r.down(order[0])
            r.down(order[1])
            r.send()
            self.assertEqual(r.host.state['recording'], 'automation')
            self.assertEqual(len(r.host.cue_ids), count)
            self.assertEqual(sum(c['action'] == 'record_start' for c in r.host.commands), starts+1)
            r.up(order[1])
            r.up(order[0])
            self.assertEqual(r.host.state['recording'], 'automation')
            r.encoder(4)
            self.assertEqual(r.host.commands[-1]['action'], 'set_parameter')
            r.button('rec')
            self.assertFalse(r.host.state['recording'])
        self.assertEqual(sum(c['action'] == 'record_start' and c['kind'] == 'new_cue' for c in r.host.commands), 1)

    def test_failed_assignment_retry_load_failure_and_pressure_hold(self):
        """G07–G08, M04/M07/M10: no false success or repeated held-pad load."""
        r = self.r
        r.button('scene')
        r.press()
        r.press()
        r.wheel(1)
        r.press()
        old = r.controller.export_config()
        with patch.object(r.manager, '_write_config', side_effect=OSError('Simulierter voller Datenträger')):
            r.press()
        self.assertEqual(r.controller.export_config(), old)
        self.assertIn('Datenträger', r.controller.snapshot()['error'])
        self.assertFalse(r.controller.snapshot()['saving'])
        r.press()
        self.assertEqual(r.controller.config['groups'][0]['pads'][0]['target'], 'm1')
        r.host.fail_load = 'm1'
        r.pad(0)
        self.assertEqual(r.host.state['active_material']['id'], 'm0')
        self.assertIn('Ladefehler', r.manager.snapshot()['error'])
        self.assertIn('Ladefehler', r.manager.error)
        self.assertIn('Ladefehler', r.manager.snapshot()['controller']['error'])
        self.assertFalse(any(c['action'] == 'load_material' for c in r.host.commands))
        r.host.fail_load = None
        r.pad(0, release=False)
        r.pad(0, release=False)
        self.assertEqual(sum(c['action'] == 'load_material' for c in r.host.commands), 1)
        self.assertEqual(r.host.state['active_material']['id'], 'm1')
        self.assertEqual(r.manager.error, '')
        self.assertEqual(r.manager.snapshot()['controller']['error'], '')

    def test_all_eight_banks_and_sixteen_physical_pad_positions_route_correctly(self):
        """G07, M10, B1/B2: every physical bank/pad pair, not just first pad."""
        r = self.r
        config = r.controller.export_config()
        for bank, group in enumerate(config['groups']):
            for pad in range(16):
                group['pads'][pad] = dict(kind='material', target='m%d' % ((bank+pad) % 2),
                                          values={'p0': (bank*16+pad)/127})
        r.controller.set_context(dict(config=config))
        r.manager.save()
        r.manager.update_surface()
        for bank in range(8):
            r.button('group', bank)
            self.assertEqual(r.controller.bank, bank)
            for pad in range(16):
                r.pad(pad)
                command = r.host.commands[-1]
                self.assertEqual(command['material_id'], 'm%d' % ((bank+pad) % 2), (bank, pad))
                self.assertEqual(command['values'], {'p0': (bank*16+pad)/127}, (bank, pad))
                self.assertEqual(r.controller.pad_index, pad)
            r.state('home')
        self.assertEqual(sum(c['action'] == 'load_material' for c in r.host.commands), 128)
        r.restart()
        self.assertEqual(r.controller.export_config(), config)

    def test_all_eight_encoders_native_page_and_idle_noise_route_only_intended_parameter(self):
        """G03/G05, M02/M03, B1: every encoder on TD and native pages."""
        r = self.r
        for count in (5, -5, 5, -5, 5, -5):
            r.encoder(0, count)
        self.assertEqual(r.host.commands, [])
        for page in (0, 1):
            r.button('top', page)
            for index in range(8):
                before = len(r.host.commands)
                r.encoder(index, 15 if page == 0 else 10)
                self.assertEqual(len(r.host.commands), before+1)
                self.assertEqual(r.host.commands[-1]['parameter_id'], 'p%d' % (page*8+index))
                self.assertEqual(r.host.commands[-1]['value'], .6)
            r.state('home')


if __name__ == '__main__':
    unittest.main()
