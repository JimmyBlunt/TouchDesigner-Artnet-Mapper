from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import ast
import unittest

from pixelblaze_mapper import show_timeline as timeline, show_automation as auto, show_midi as midi
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer, TransportState
from tests.test_show_timeline import sample, FakeHost
from pixelblaze_mapper.show_timeline_ui import Bridge


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.show, self.data = sample()
        self.sequence = ShowSequencer(Show.from_dict(self.show))
        self.sequence.play()

    def region(self, start=5, end=17):
        _, self.data = timeline.edit(self.show, self.data, dict(action='loop', start=start, end=end, enabled=True))

    def test_boundary_wrap_multi_cue_and_large_delta(self):
        self.region()
        self.sequence.seek(1, 4)
        timeline.advance_with_loop(self.sequence, 2, self.data)
        self.assertEqual((self.sequence.cue_index, self.sequence.elapsed), (0, 6))
        timeline.advance_with_loop(self.sequence, 37, self.data)
        self.assertEqual((self.sequence.cue_index, self.sequence.elapsed), (0, 7))
        self.assertIs(self.sequence.state, TransportState.PLAYING)

    def test_paused_and_disabled_keep_normal_transport(self):
        self.region()
        self.sequence.seek(0, 1)
        self.sequence.pause()
        timeline.advance_with_loop(self.sequence, 3, self.data)
        self.assertEqual(self.sequence.elapsed, 1)
        self.sequence.play()
        self.data['loop_region']['enabled'] = False
        timeline.advance_with_loop(self.sequence, 3, self.data)
        self.assertEqual(self.sequence.elapsed, 4)

    def test_seek_outside_region_and_shortened_show(self):
        self.region()
        timeline.advance_with_loop(self.sequence, .5, self.data)
        self.assertEqual(self.sequence.elapsed, 5.5)
        self.data['loop_region'].update(start=50, end=80)
        timeline.advance_with_loop(self.sequence, 1, self.data)
        self.assertEqual(self.sequence.elapsed, 6.5)

    def test_end_of_nonlooping_show_still_wraps_region(self):
        self.show['loop'] = False
        self.sequence = ShowSequencer(Show.from_dict(self.show))
        self.sequence.play()
        self.sequence.seek(2, 11)
        self.region(0, 36)
        timeline.advance_with_loop(self.sequence, 1, self.data)
        self.assertEqual((self.sequence.cue_index, self.sequence.elapsed), (0, 0))
        self.assertIs(self.sequence.state, TransportState.PLAYING)

    def test_validation_undo_and_persistence(self):
        host = FakeHost()
        bridge = Bridge(host)
        original = deepcopy(host.data)
        bridge.execute(dict(action='loop', start=3, end=15, enabled=True, revision=bridge.state['revision']))
        self.assertEqual(auto.validate(host.data)['loop_region']['start'], 3)
        bridge.execute(dict(action='undo', revision=bridge.state['revision']))
        self.assertEqual(host.data, original)
        for start, end in [(5,5), (-1,3), (0,100), (0,float('nan'))]:
            with self.assertRaises(ValueError):
                timeline.edit(self.show, self.data, dict(action='loop', start=start, end=end, enabled=True))


class MidiTests(unittest.TestCase):
    def test_raw_addresses_and_release_messages(self):
        self.assertEqual(midi.decode([0xB2, 0, 127]), (dict(kind='cc',channel=3,number=0),127))
        self.assertEqual(midi.decode([0x99, 36, 100])[0], dict(kind='note',channel=10,number=36))
        for raw in ([0x89,36,127], [0x99,36,0], [0xf8], [0xe0,0,127]):
            self.assertIsNone(midi.decode(raw))

    def test_absolute_relative_and_bounds(self):
        binding = midi.default_config()['bindings'][1]
        self.assertEqual(midi.mapped_value(binding, 127, 0), 4)
        self.assertEqual(midi.mapped_value(binding, 0, 4), 0)
        binding['mode'] = 'relative_twos'
        self.assertAlmostEqual(midi.mapped_value(binding, 127, 2), 2-4/127)
        self.assertEqual(midi.mapped_value(binding, 1, 4), 4)
        binding['mode'] = 'relative_offset'
        self.assertAlmostEqual(midi.mapped_value(binding, 63, 2), 2-4/127)

    def test_validation_and_no_preset_addresses(self):
        config = midi.validate(midi.default_config())
        self.assertEqual(len(config['bindings']), 16)
        self.assertTrue(all(b['source'] is None for b in config['bindings']))
        config['bindings'][0]['maximum'] = float('inf')
        with self.assertRaises(ValueError): midi.validate(config)

    def test_learning_consumes_event_and_unbinds_conflict(self):
        manager = object.__new__(midi.Manager)
        manager.config = midi.default_config()
        manager.config['enabled'] = True
        source = dict(kind='cc', channel=1, number=7)
        manager.config['bindings'][0]['source'] = source
        manager.learning = 2
        saved = []
        manager.save = lambda: saved.append(True)
        manager.receive([0xb0,7,100])
        self.assertIsNone(manager.learning)
        self.assertIsNone(manager.config['bindings'][0]['source'])
        self.assertEqual(manager.config['bindings'][2]['source'], source)
        self.assertEqual(saved, [True])

    def test_live_values_do_not_leak_to_other_cues_or_blackout(self):
        show, _ = sample()
        sequence = ShowSequencer(Show.from_dict(show))
        manager = SimpleNamespace(config={'enabled':True}, cue_id=sequence.cue.id, values={'brightness':.7,'speed':3})
        with patch.object(midi, '_manager', manager):
            self.assertEqual(midi.live_values('other'), {})
            self.assertEqual(midi.apply_plan(sequence.plan(),sequence.cue.id).brightness,.7)
            sequence.blackout = True
            self.assertEqual(midi.apply_plan(sequence.plan(),sequence.cue.id).brightness,0)
            manager.config['enabled'] = False
            self.assertEqual(midi.live_values(sequence.cue.id),{})

    def test_generated_recording_samples_live_midi_values(self):
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        from pixelblaze_mapper import show_editor
        show, _ = sample()
        cue_id = show['cues'][0]['id']
        samples = []
        recorder = SimpleNamespace(last_time=None, sample=lambda t, values:samples.append((t,dict(values))))
        source = timeline.install_editor_source(EDITOR_RUNTIME)
        function = next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='record_tick')
        scope = dict(drive_imported_slots=lambda:None, _state=lambda name,*args:{'recording':'1','record_cue':cue_id}.get(name,''),
                     _take=lambda:recorder, show=lambda:show, player_values=lambda:{}, editor=show_editor, automation=auto,
                     OWNER=SimpleNamespace(op=lambda _:SimpleNamespace(module=SimpleNamespace(_get=lambda *args:0))))
        manager = SimpleNamespace(config={'enabled':True}, cue_id=cue_id, values={'brightness':.4,'speed':3})
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<record midi test>','exec'),scope)
        with patch.object(midi,'_manager',manager):
            scope['record_tick'](.5)
        self.assertEqual(samples,[(.5,{'brightness':.4,'speed':3})])

    def test_generated_live_overlay_only_applies_to_on_air_slot(self):
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        # Isolate the MIDI layer; the outer MK2 layer has its own integration suite.
        source = timeline.install_editor_source(EDITOR_RUNTIME).split('# MK2_EDITOR_V020')[0]
        functions = [n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_effective_parameters']
        scope = dict(_midi_base_effective=lambda cue,on_air:{'speed':1,'zoom':2})
        exec(compile(ast.Module(body=[functions[-1]],type_ignores=[]),'<overlay midi test>','exec'),scope)
        manager = SimpleNamespace(config={'enabled':True},cue_id='a',values={'speed':3,'brightness':.5})
        with patch.object(midi,'_manager',manager):
            self.assertEqual(scope['_effective_parameters']({'id':'a'},True),{'speed':3,'zoom':2})
            self.assertEqual(scope['_effective_parameters']({'id':'a'},False),{'speed':1,'zoom':2})


if __name__ == '__main__':
    unittest.main()
