"""Timeline contracts: playback, editing, persistence, history and local API."""
from copy import deepcopy
import json
import threading
import time
import unittest
import ast
from types import SimpleNamespace
import urllib.request
import urllib.error

from pixelblaze_mapper import show_automation as auto, show_editor as editor, show_timeline as timeline
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer
from pixelblaze_mapper.show_timeline_ui import Bridge


def sample():
    show = dict(editor.EMPTY_SHOW, name='Timeline-Testshow (isoliert)')
    for name in ('Aurora', 'Rainbow', 'Plasma'):
        show = editor.append_cue(show, editor.new_cue('Fill', editor.parameters_from_player({}),
                                                     name=name, duration=12, transition_duration=3))
    data = auto.merge(auto.empty(), show['cues'][0]['id'], {'speed': [[0, 1], [4, 2], [10, .5]],
                                                          'brightness': [[0, .2], [6, .6], [12, .3]]})
    return show, data


class FakeHost:
    def __init__(self):
        self.show, self.data = sample()
        self.sequence = ShowSequencer(Show.from_dict(self.show))
        self.recording = False
        self.saved = None

    def raw(self):
        return json.dumps([self.show, self.data])

    def documents(self):
        return deepcopy(self.show), deepcopy(self.data), {c['id']:{k:v for k,v in dict(c['parameters'],brightness=c['brightness']).items() if auto.recordable(k)} for c in self.show['cues']}

    def transport(self):
        return dict(index=self.sequence.cue_index, elapsed=self.sequence.elapsed,
                    state=self.sequence.state.value, recording=self.recording)

    def write(self, show, data):
        self.show, self.data = deepcopy(show), deepcopy(data)

    def control(self, command):
        action = command['action']
        if action == 'seek':
            self.sequence.seek(*timeline.locate(self.show, command['time']))
        else:
            getattr(self.sequence, action)()

    def save(self):
        self.saved = deepcopy((self.show, self.data))


class EditingTests(unittest.TestCase):
    def setUp(self):
        self.show, self.data = sample()
        self.cue = self.show['cues'][0]['id']

    def edit(self, **command):
        return timeline.edit(self.show, self.data, dict(cue=self.cue, **command))

    def test_edit_does_not_change_original_recording_or_input(self):
        before = deepcopy((self.show, self.data))
        show, data = self.edit(action='lane', parameter='speed', curve=dict(points=[[0, 2], [10, 4]], mode='smooth'))
        self.assertEqual((self.show, self.data), before)
        self.assertEqual(data['tracks'], self.data['tracks'])
        self.assertEqual(auto.values_at(data, self.cue, 5)['speed'], 3)
        data['edits'][self.cue]['speed']['enabled'] = False
        self.assertEqual(auto.values_at(data, self.cue, 5), auto.values_at(self.data, self.cue, 5))

    def test_new_parameter_without_recording_plays_and_roundtrips(self):
        show, data = self.edit(action='lane', parameter='zoom', curve=dict(points=[[0, 1], [8, 5]], mode='ease_in'))
        loaded = auto.validate(json.loads(json.dumps(data)))
        self.assertEqual(auto.values_at(loaded, self.cue, 4)['zoom'], 2)
        _, reset = timeline.edit(show, loaded, dict(action='reset_lane', cue=self.cue, parameter='zoom'))
        self.assertNotIn('zoom', auto.values_at(reset, self.cue, 4))

    def test_shortening_holds_original_samples_for_restoration(self):
        show, data = self.edit(action='resize', duration=2)
        self.assertEqual(data, self.data)
        self.assertEqual(show['cues'][0]['transition_duration'], 2)
        self.assertEqual(timeline.layout(show)[1]['start'], 2)
        restored, _ = timeline.edit(show, data, dict(action='resize', cue=self.cue, duration=12))
        self.assertEqual(restored['cues'][0]['duration'], 12)
        self.assertEqual(auto.values_at(data, self.cue, 10), auto.values_at(self.data, self.cue, 10))

    def test_move_uses_cue_identity_and_sequential_time(self):
        show, data = self.edit(action='move', time=35)
        self.assertEqual(show['cues'][-1]['id'], self.cue)
        self.assertEqual(data, self.data)
        self.assertEqual([r['start'] for r in timeline.layout(show)], [0, 12, 24])

    def test_seek_boundaries_and_end(self):
        self.assertEqual(timeline.locate(self.show, 12), (1, 0))
        self.assertEqual(timeline.locate(self.show, -10), (0, 0))
        index, elapsed = timeline.locate(self.show, 100)
        self.assertEqual(index, 2)
        self.assertLess(elapsed, 12)

    def test_invalid_edit_is_atomic(self):
        for points in ([[0, 1], [0, 2]], [[0, float('nan')]], [[-1, 2]]):
            with self.assertRaises(ValueError):
                self.edit(action='lane', parameter='speed', curve=dict(points=points))
        with self.assertRaises(ValueError):
            self.edit(action='resize', duration=float('inf'))
        self.assertEqual((self.show, self.data), sample())

    def test_transition_curves_match_both_ab_slots_and_blackout(self):
        show, data = self.edit(action='transition', duration=4,
                              curve=dict(points=[[0, 0], [1, 1]], mode='ease_in'))
        sequence = ShowSequencer(Show.from_dict(show))
        sequence.seek(0, 10)
        for slot in ('A', 'B'):
            sequence._current_slot = slot
            plan = auto.playback_plan(sequence.plan(), data, self.cue, sequence.elapsed)
            self.assertAlmostEqual(plan.progress, .25)
            self.assertAlmostEqual(plan.output_b_mix, .25 if slot == 'A' else .75)
        sequence.set_blackout(True)
        self.assertEqual(auto.playback_plan(sequence.plan(), data, self.cue, 10).brightness, 0)

    def test_transition_rejects_backwards_and_missing_endpoints(self):
        for points in ([[0,.2],[1,1]], [[0,0],[.3,.8],[.6,.2],[1,1]]):
            with self.assertRaises(ValueError):
                self.edit(action='transition', curve=dict(points=points))

    def test_modes_have_expected_value(self):
        for mode, expected in [('linear',.25),('step',0),('smooth',.15625),('ease_in',.0625),('ease_out',.4375)]:
            self.assertAlmostEqual(auto.value_at([[0,0],[1,1]], .25, mode), expected)

    def test_duplicate_delete_keep_layers_consistent(self):
        _, data = self.edit(action='lane', parameter='speed', curve=dict(points=[[0,3]]))
        data = auto.copy_cue(data, self.cue, 'copy')
        self.assertEqual(data['edits']['copy'], data['edits'][self.cue])
        data = auto.clear_cue(data, self.cue)
        self.assertNotIn(self.cue, data['edits'])
        self.assertIn('copy', data['edits'])

    def test_runtime_patches_idempotent_and_keep_performance_patches(self):
        import ast
        from pathlib import Path
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        from pixelblaze_mapper.show_sync_fastpath import install_callback_source
        file = Path(__file__).parents[1]/'pixelblaze_mapper/build_show_sequencer.py'
        source = next(n.value for n in ast.walk(ast.parse(file.read_text())) if isinstance(n, ast.Constant)
                      and isinstance(n.value, str) and n.value.startswith('# Isolated transport UI callbacks'))
        patched = timeline.install_sync_source(install_callback_source(source))
        self.assertEqual(timeline.install_sync_source(patched), patched)
        self.assertIn('SHOW_IDLE_SYNC_FASTPATH', patched)
        patched = timeline.install_editor_source(EDITOR_RUNTIME)
        self.assertEqual(timeline.install_editor_source(patched), patched)
        self.assertIn("and cue_id not in (data.get('edits')", patched)

    def test_generated_player_uses_new_lane_without_original_recording(self):
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        source = timeline.install_editor_source(EDITOR_RUNTIME)
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == '_effective_parameters')
        _, data = self.edit(action='lane', parameter='zoom', curve=dict(points=[[0, 1], [8, 5]]))
        data['tracks'] = {}
        scope = dict(automation=auto, _cached_automation=lambda: data, _state=lambda *args: '0',
                     OWNER=SimpleNamespace(op=lambda _:SimpleNamespace(module=SimpleNamespace(_get=lambda *args:4))))
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<editor test>', 'exec'), scope)
        self.assertEqual(scope['_effective_parameters'](self.show['cues'][0], True)['zoom'], 3)
        self.assertEqual(scope['_effective_parameters'](self.show['cues'][0], False)['zoom'], 1)

    def test_imported_uniforms_reset_to_capture_when_override_is_removed(self):
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        source = timeline.install_editor_source(EDITOR_RUNTIME)
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == '_imported_overrides')
        _, data = self.edit(action='lane', parameter='mat__uSpeed', curve=dict(points=[[0, 7]]))
        scope = dict(automation=auto, automation_data=lambda:data, _state=lambda *args:'0',
                     imported_data=lambda:{self.cue:{'values':{'uSpeed':2,'mat_scale':3}}},
                     OWNER=SimpleNamespace(op=lambda _:SimpleNamespace(module=SimpleNamespace(_get=lambda key,*args:'A' if key=='outgoing_slot' else 0))))
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<import test>', 'exec'), scope)
        self.assertEqual(scope['_imported_overrides']('a',self.cue)['mat__uSpeed'],7)
        data['edits']={}
        self.assertEqual(scope['_imported_overrides']('a',self.cue)['mat__uSpeed'],2)
        self.assertEqual(scope['_imported_overrides']('a',self.cue)['mat_scale'],3)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeHost()
        self.bridge = Bridge(self.host)

    def execute(self, action, **args):
        return self.bridge.execute(dict(action=action, revision=self.bridge.state['revision'], **args))

    def test_undo_redo_save_and_external_edit_conflict(self):
        before = self.host.raw()
        self.execute('resize', cue='aurora', duration=20)
        self.execute('undo')
        self.assertEqual(self.host.raw(), before)
        self.execute('redo')
        self.assertEqual(self.host.show['cues'][0]['duration'], 20)
        self.execute('save')
        self.assertEqual(self.host.saved, (self.host.show, self.host.data))
        self.assertFalse(self.bridge.state['dirty'])
        stale = self.bridge.state['revision']
        self.host.show['name'] = 'external'
        self.bridge.refresh()
        self.assertFalse(self.bridge.state['undo'])
        with self.assertRaises(ValueError):
            self.bridge.execute(dict(action='resize', cue='aurora', duration=4, revision=stale))
        self.assertEqual(self.host.show['cues'][0]['duration'], 20)

    def test_recording_rejects_edit_and_transport(self):
        self.host.recording = True
        for action in ('resize', 'play', 'seek', 'save'):
            with self.assertRaises(ValueError):
                self.execute(action, cue='aurora', duration=4, time=2)

    def test_expired_command_cannot_run_later(self):
        job=dict(command=dict(action='stop'),deadline=0,done=threading.Event())
        self.bridge.commands.put(job)
        self.bridge.tick()
        self.assertIn('error',job)
        self.assertTrue(job['done'].is_set())

    def test_http_serves_ui_and_refuses_cross_origin_or_missing_token(self):
        self.bridge.port = 0
        self.bridge.start()
        self.bridge.port = self.bridge.server.server_port
        url = f'http://127.0.0.1:{self.bridge.port}'
        try:
            with urllib.request.urlopen(url) as response:
                self.assertIn(b'Show Timeline',response.read())
            with urllib.request.urlopen(url+'/api/state') as response:
                state=json.load(response)
            self.assertEqual(state['revision'],self.bridge.state['revision'])
            # The HTTP thread queues; only the host thread applies the edit.
            outcome = []
            def post():
                payload=json.dumps(dict(action='resize',cue='aurora',duration=18,revision=state['revision'])).encode()
                request=urllib.request.Request(url+'/api/command',payload,{'X-Timeline-Token':self.bridge.token})
                with urllib.request.urlopen(request) as response:
                    outcome.append(json.load(response))
            worker=threading.Thread(target=post)
            worker.start()
            deadline=time.monotonic()+3
            while worker.is_alive() and time.monotonic()<deadline:
                self.bridge.tick()
                time.sleep(.01)
            worker.join(timeout=1)
            self.assertEqual(outcome[0]['show']['cues'][0]['duration'],18)
            for headers in ({}, {'X-Timeline-Token':self.bridge.token,'Origin':'https://example.com'}):
                request=urllib.request.Request(url+'/api/command',b'{}',headers)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request)
                self.assertEqual(error.exception.code,403)
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(url+'/../show_timeline_ui.py')
        finally:
            self.bridge.server.shutdown()
            self.bridge.server.server_close()


if __name__ == '__main__':
    unittest.main()
