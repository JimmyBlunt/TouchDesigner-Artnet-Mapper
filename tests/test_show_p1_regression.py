"""Portable regression evidence for Show handoff, UV and transition endpoints."""

import unittest
import ast
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from pixelblaze_mapper.show_renderer import render_frame, transition_b_weight, slot_uv_frame
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer
from pixelblaze_mapper.integrate_live_show import _slot_uv_source, _render_sync_source, LED_RENDER_CALLBACK
from tests.test_routing_apply_regression import Table
from tests.test_show_sequencer import cue


class ShowP1RegressionTests(unittest.TestCase):
    def test_slot_coordinate_modes_do_not_share_external_player_state(self):
        columns = ([.1, .2], [.3, .4], [.8, .9], [.6, .7])
        self.assertEqual(slot_uv_frame(*columns, mode='global'), ((.1, .2), (.3, .4)))
        self.assertEqual(slot_uv_frame(*columns, mode='panel'), ((.8, .9), (.6, .7)))
        hybrid = slot_uv_frame(*columns, mode='hybrid', hybrid_mix=.25)
        self.assertAlmostEqual(hybrid[0][0], .275)
        self.assertAlmostEqual(hybrid[1][1], .475)
        for invalid in ('missing', ''):
            with self.assertRaises(ValueError):
                slot_uv_frame(*columns, mode=invalid)

    def test_generated_uv_callback_samples_each_slot_and_rejects_reordered_indices(self):
        lookup = Table([['index', 'global_u', 'global_v', 'local_u', 'local_v'],
                        [0, .1, .2, .8, .9], [1, .3, .4, .5, .6]])
        channels = {}
        script = SimpleNamespace(clear=channels.clear,
            appendChan=lambda name: channels.setdefault(name, SimpleNamespace(vals=[])))
        for mode, expected in [('global', (.1, .3)), ('panel', (.8, .5))]:
            request = Table([['key', 'value'], ['mode', mode], ['hybrid_mix', .5]])
            scope = {'op': lambda path: lookup if path.endswith('effect_panel_uv') else request}
            exec(_slot_uv_source('slot/coordinate_request'), scope)
            scope['onCook'](script)
            self.assertEqual(channels['tx'].vals, expected)
        lookup[1, 'index'] = 1
        with self.assertRaisesRegex(RuntimeError, 'ordered'):
            scope['onCook'](script)

    def test_automatic_handoff_keeps_incoming_slot_time_continuous(self):
        show = Show('phase', (cue('one'), cue('two'), cue('three')), loop=True)
        for fps in (30, 60):
            sequence = ShowSequencer(show)
            sequence.play()
            sequence.advance(10 - 1 / fps)
            before = sequence.plan()
            incoming = before.slot_b_time
            sequence.advance(1 / fps)
            after = sequence.plan()
            self.assertEqual(after.outgoing_slot, 'B')
            self.assertAlmostEqual(after.slot_b_time - incoming, 1 / fps)
            sequence.pause()
            sequence.advance(100)
            self.assertEqual(sequence.plan().slot_b_time, after.slot_b_time)

    def test_manual_go_resets_new_current_slot_clock(self):
        sequence = ShowSequencer(Show('manual', (cue('one'), cue('two'))))
        sequence.play()
        sequence.advance(9)
        sequence.go()
        self.assertEqual(sequence.plan().slot_b_time, 0.0)

    def test_automatic_reverse_slot_and_loop_keep_preroll(self):
        sequence = ShowSequencer(Show('loop', (cue('one'), cue('two')), loop=True))
        sequence.play()
        sequence.advance(19.9)
        before = sequence.plan().slot_a_time
        sequence.advance(.1)
        self.assertEqual(sequence.plan().outgoing_slot, 'A')
        self.assertAlmostEqual(sequence.plan().slot_a_time - before, .1)
        sequence.stop()
        self.assertEqual(sequence.plan().slot_a_time, 0)

    def test_cut_handoff_does_not_apply_preroll(self):
        sequence = ShowSequencer(Show('cut', (cue('one', transition='cut', transition_duration=0), cue('two'))))
        sequence.play()
        sequence.advance(10)
        self.assertEqual(sequence.plan().slot_b_time, 0)

    def test_generated_runtime_restores_state_and_every_toggle_click(self):
        source = (Path(__file__).parents[1] / 'pixelblaze_mapper/build_show_sequencer.py').read_text(encoding='utf-8')
        callback = next(node.value for node in ast.walk(ast.parse(source))
                        if isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and node.value.startswith('# Isolated transport UI callbacks'))
        tables = {'state_table': Table([['key', 'value'], ['cue_index', 1], ['elapsed', 3],
            ['slot_time_offset', 2], ['outgoing_slot', 'B'], ['loop', 1], ['blackout', 1], ['transport', 'paused']]),
            'show_json': SimpleNamespace(text=json.dumps(Show('restore', (cue('one'), cue('two'))).to_dict()))}
        for path in ('slot_a_adapter/material_request', 'slot_b_adapter/material_request',
                     'slot_a_adapter/coordinate_request', 'slot_b_adapter/coordinate_request',
                     'transition_adapter/mixer_request'):
            tables[path] = Table([['key', 'value']])
        stored = {}
        owner = SimpleNamespace(fetch=lambda name, default: stored.get(name, default), store=stored.__setitem__)
        tables['callbacks'] = SimpleNamespace(parent=lambda: owner)
        scope = {'op': tables.get}
        exec(callback, scope)
        sequence = scope['runtime']()
        self.assertEqual((sequence.cue_index, sequence.elapsed, sequence.plan().slot_b_time), (1, 3, 5))
        self.assertEqual(sequence.state.value, 'paused')
        for name, attribute in [('loop', lambda: sequence.show.loop), ('blackout', lambda: sequence.blackout)]:
            self.assertTrue(attribute())
            scope['command'](name)
            self.assertFalse(attribute())
            scope['command'](name)
            self.assertTrue(attribute())
        self.assertIn('node.par.buttontype = "momentary"', source)

    def test_generated_renderer_rejects_missing_effect_and_uses_slot_phase(self):
        source = _render_sync_source([dict(id='particles', label='Particles', index=1, preset='Cyan')])
        compile(LED_RENDER_CALLBACK, '<led>', 'exec')
        scope = {'op': lambda path: SimpleNamespace(text=json.dumps({'cues': [dict(id='bad', effect='missing')]}))}
        exec(source, scope)
        with self.assertRaisesRegex(RuntimeError, 'Unresolved Show cue/effect'):
            scope['preflight']()
        self.assertIn("_value(request_path, 'animation_time', '0')", source)
        self.assertNotIn("'elapsed', '0')) *", source)

    def test_sender_badge_reports_observed_state_without_enabling_output(self):
        class Parameter:
            def __init__(self, value):
                self.val = value
            def eval(self):
                return self.val
        title = SimpleNamespace(par={'text': Parameter('')})
        source = Parameter('show')
        status = dict(enabled=False, error='')
        state = Table([['key', 'value']])
        nodes = {'control_panel/title': title, 'state_table': state,
            '/project1/madmapper_player_controls': SimpleNamespace(par=SimpleNamespace(Source=source)),
            '/project1/multi_controller_output/artnet_510_sender_callbacks':
                SimpleNamespace(module=SimpleNamespace(status=lambda: status))}
        scope = {'op': nodes.get}
        exec(_render_sync_source([]), scope)
        for enabled, selected, expected in ((False, 'show', 'OUTPUT OFF'),
                (True, 'show', 'LIVE SENDING'), (True, 'materials', 'OTHER SOURCE SENDING')):
            status['enabled'], source.val = enabled, selected
            scope['_sender_badge']()
            self.assertIn(expected, title.par['text'].val)
            self.assertEqual(state[1, 1], str(int(enabled)))
        del nodes['/project1/multi_controller_output/artnet_510_sender_callbacks']
        scope['_sender_badge']()
        self.assertIn('STATUS UNKNOWN', title.par['text'].val)
        self.assertEqual(state[1, 1], 'unknown')

    def test_every_transition_has_exact_endpoint_masks(self):
        for transition in ('cut', 'crossfade', 'wipe', 'radial', 'dissolve', 'glitch'):
            for uv in ((0, 0), (0.5, 0.5), (1, 1)):
                with self.subTest(transition=transition, uv=uv):
                    self.assertEqual(transition_b_weight(transition, 0, 0, uv), 0)
                    self.assertEqual(transition_b_weight(transition, 1, 0, uv), 1)

    def test_bulk_endpoint_never_leaks_incoming_panel(self):
        frame = render_frame(([1.] * 3744,), ([9.] * 3744,), u=[0.] * 3744, v=[0.5] * 3744,
            transition='wipe', output_b_mix=0, brightness=1, blackout=False,
            targets_a=('middle',), targets_b=('rear',))
        self.assertEqual(frame[0][0], 1)
        self.assertEqual(frame[0][1184], 0)


if __name__ == '__main__':
    unittest.main()
