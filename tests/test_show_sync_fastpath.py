"""Idle Show callback optimization preserves transport, live edits and feedback."""
import json
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper.integrate_live_show import _render_sync_source
from pixelblaze_mapper.show_sequencer import Show
from pixelblaze_mapper.show_sync_fastpath import (
    install_callback_source, restore_callback_source, install_render_source,
    restore_render_source, REQUEST_PATHS,
)
from tests.test_show_storage import CALLBACK
from tests.test_show_sequencer import cue
from tests.test_routing_apply_regression import Table as BaseTable


class Table(BaseTable):
    @property
    def text(self):
        return '\n'.join('\t'.join(row) for row in self.rows)


class IdleSyncTests(unittest.TestCase):
    def setUp(self):
        self.nodes = {path: Table([['key','value']]) for path in REQUEST_PATHS}
        self.nodes['state_table'] = Table([['key','value'],['transport','paused'],['elapsed',1]])
        self.nodes['show_json'] = NS(text=json.dumps(Show('test',(cue('one'),cue('two'))).to_dict()))
        self.storage = {}
        owner = NS(fetch=lambda key, default=None: self.storage.get(key,default), store=self.storage.__setitem__)
        self.nodes['callbacks'] = NS(parent=lambda: owner)
        self.render = NS(sync_render=Mock(),sync_feedback=Mock(),preflight=Mock())
        self.nodes['render_sync'] = NS(module=self.render)
        self.scope = {'op': self.nodes.get}
        exec(install_callback_source(CALLBACK),self.scope)
        self.scope['sync']()

    def test_paused_unchanged_skips_serialization_and_full_renderer(self):
        before = {p:self.nodes[p].text for p in REQUEST_PATHS}
        with patch.object(self.scope['json'],'dumps',wraps=json.dumps) as dump:
            for _ in range(20):
                self.scope['advance'](.01)
            dump.assert_not_called()
        self.assertEqual(self.render.sync_render.call_count,1)
        self.assertEqual(self.render.sync_feedback.call_count,20)
        self.assertEqual(self.scope['runtime']().elapsed,1)
        self.assertEqual(before,{p:self.nodes[p].text for p in REQUEST_PATHS})

    def test_stop_and_ui_commands_apply_immediately(self):
        self.scope['command']('stop')
        self.assertEqual(self.scope['runtime']().elapsed,0)
        count = self.render.sync_render.call_count
        self.scope['advance'](.1)
        self.assertEqual(self.render.sync_render.call_count,count)
        self.scope['command']('blackout')
        self.assertTrue(self.scope['runtime']().blackout)
        self.assertEqual(self.scope['_get']('blackout'),'1')
        self.assertEqual(self.render.sync_render.call_count,count+1)
        self.scope['command']('next')
        self.assertEqual(self.scope['runtime']().cue_index,1)
        self.assertEqual(self.render.sync_render.call_count,count+2)

    def test_playing_progresses_in_background_and_keeps_full_sync(self):
        self.nodes['/project1/madmapper_player_controls'] = NS(par=NS(Source=NS(eval=lambda:'movie')))
        self.scope['command']('play')
        count = self.render.sync_render.call_count
        self.scope['advance'](.5)
        self.scope['advance'](.5)
        self.assertEqual(self.scope['runtime']().elapsed,2)
        self.assertEqual(self.render.sync_render.call_count,count+2)
        self.assertEqual(self.scope['_get']('transport'),'playing')

    def test_same_frame_request_and_state_edits_invalidate_skip(self):
        for path in REQUEST_PATHS:
            table = self.nodes[path]
            original = table[1,1]
            table[1,1] = 'externally changed'
            count = self.render.sync_render.call_count
            self.scope['advance'](.01)
            self.assertEqual(self.render.sync_render.call_count,count+1,path)
            self.assertEqual(table[1,1],original,path)

    def test_show_json_change_is_applied_during_pause(self):
        original_runtime = self.scope['runtime']()
        data = json.loads(self.nodes['show_json'].text)
        data['cues'][0]['parameters']['speed'] = 2.0
        self.nodes['show_json'].text = json.dumps(data)
        self.scope['advance'](.01)
        self.assertIsNot(self.scope['runtime'](),original_runtime)
        self.assertEqual(self.scope['runtime']().cue.parameters.speed,2)
        self.assertEqual(self.scope['runtime']().state.value,'paused')
        self.assertEqual(self.render.sync_render.call_count,2)

    def test_invalid_show_cannot_hide_behind_idle_cache(self):
        self.nodes['show_json'].text = '{invalid'
        with self.assertRaises(ValueError):
            self.scope['advance'](.01)

    def test_render_module_reload_on_same_dat_requires_full_sync(self):
        dat = self.nodes['render_sync']
        replacement = NS(_feedback_context=None,sync_feedback=Mock())
        replacement.sync_render = Mock(side_effect=lambda:setattr(replacement,'_feedback_context',('ready',)))
        dat.module = replacement
        self.scope['advance'](.01)
        replacement.sync_render.assert_called_once()
        replacement.sync_feedback.assert_not_called()
        self.assertIs(self.nodes['render_sync'],dat)
        self.scope['advance'](.01)
        replacement.sync_render.assert_called_once()
        replacement.sync_feedback.assert_called_once()

    def test_same_module_context_reset_also_requires_full_sync(self):
        self.render._feedback_context = None
        self.render.sync_render.side_effect = lambda:setattr(self.render,'_feedback_context',('ready',))
        self.scope['advance'](.01)
        self.assertEqual(self.render.sync_render.call_count,2)
        self.scope['advance'](.01)
        self.assertEqual(self.render.sync_render.call_count,2)
        self.render.sync_feedback.assert_called_once()

    def test_failed_sync_cannot_reuse_previous_success_record(self):
        self.render.sync_render.side_effect = RuntimeError('renderer failure')
        with self.assertRaises(RuntimeError):
            self.scope['sync']()
        with self.assertRaises(RuntimeError):
            self.scope['advance'](.01)

    def test_reloaded_playing_show_still_requires_explicit_play(self):
        self.scope['command']('play')
        self.scope['advance'](.5)
        restored = {'op':self.nodes.get}
        exec(install_callback_source(CALLBACK),restored)
        restored['advance'](10)
        self.assertEqual(restored['runtime']().state.value,'paused')
        self.assertEqual(restored['runtime']().elapsed,1.5)
        self.assertIsInstance(self.storage['show_runtime_record'],dict)
        json.dumps(self.storage)


class SourceAndFeedbackTests(unittest.TestCase):
    def test_callback_and_render_patches_are_reversible_and_fail_closed(self):
        patched = install_callback_source(CALLBACK)
        self.assertEqual(install_callback_source(patched),patched)
        self.assertEqual(restore_callback_source(patched),CALLBACK)
        with self.assertRaises(ValueError):
            install_callback_source(patched.replace('sequence.advance(seconds)','sequence.advance(0)'))
        render = _render_sync_source([])
        self.assertEqual(install_render_source(render),render)
        original = restore_render_source(render)
        self.assertNotIn('def sync_feedback()',original)
        self.assertEqual(install_render_source(original),render)
        with self.assertRaises(ValueError):
            install_render_source(render.replace('_feedback_context = None','_feedback_context = 0'))

    def test_idle_feedback_keeps_quarter_second_rate_without_reapplying_slots(self):
        state = Table([['key','value'],['transport','paused']])
        nodes = {'state_table':state, 'cue_table':Table([['id','name'],['first','Cue One']]),
                 'show_transition_mixer':NS(),
                 'transition_adapter/mixer_request':Table([['key','value']]),
                 'control_panel/btn_loop':NS(), 'control_panel/btn_blackout':NS()}
        scope = {'op':nodes.get}
        exec(_render_sync_source([]),scope)
        apply = Mock(return_value=('Effect','Preset','all'))
        badge = Mock()
        scope['_apply_slot'] = apply
        scope['_sender_badge'] = badge
        scope['_text_if_changed'] = Mock()
        scope['_set_parameter'] = Mock()
        scope['time'] = NS(monotonic=lambda:1.)
        scope['sync_render']()
        self.assertEqual(apply.call_count,2)
        self.assertEqual(badge.call_count,1)
        scope['time'] = NS(monotonic=lambda:1.1)
        scope['sync_feedback']()
        self.assertEqual(badge.call_count,1)
        scope['time'] = NS(monotonic=lambda:1.25)
        scope['sync_feedback']()
        self.assertEqual(badge.call_count,2)
        self.assertEqual(apply.call_count,2)


if __name__ == '__main__':
    unittest.main()
