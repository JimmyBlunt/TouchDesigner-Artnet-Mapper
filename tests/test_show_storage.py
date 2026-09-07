"""Portable Show storage/reopen checks; no TD API, save or output calls."""
import ast
import json
import pickle
from pathlib import Path
from types import SimpleNamespace
import unittest

from pixelblaze_mapper.show_sequencer import Show
from tests.test_show_sequencer import cue
from tests.test_routing_apply_regression import Table


SOURCE = (Path(__file__).parents[1] / 'pixelblaze_mapper/build_show_sequencer.py').read_text(encoding='utf-8')
CALLBACK = next(node.value for node in ast.walk(ast.parse(SOURCE))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and node.value.startswith('# Isolated transport UI callbacks'))


class ShowStorageTests(unittest.TestCase):
    def setUp(self):
        self.tables = {'state_table': Table([['key', 'value'], ['cue_index', 1], ['elapsed', 3],
            ['slot_time_offset', 2], ['outgoing_slot', 'B'], ['loop', 1], ['blackout', 1], ['transport', 'playing']]),
            'show_json': SimpleNamespace(text=json.dumps(Show('preserve', (cue('one'), cue('two'))).to_dict()))}
        for path in ('slot_a_adapter/material_request', 'slot_b_adapter/material_request',
                     'slot_a_adapter/coordinate_request', 'slot_b_adapter/coordinate_request',
                     'transition_adapter/mixer_request'):
            self.tables[path] = Table([['key', 'value']])
        self.stored = {}
        owner = SimpleNamespace(fetch=lambda name, default: self.stored.get(name, default), store=self.stored.__setitem__)
        self.tables['callbacks'] = SimpleNamespace(parent=lambda: owner)
        self.scope = self.reload_callback()

    def reload_callback(self):
        scope = {'op': self.tables.get}
        exec(CALLBACK, scope)
        return scope

    def assert_plain_storage(self):
        encoded = json.dumps(self.stored)
        self.assertEqual(json.loads(encoded), self.stored)
        pickle.dumps(self.stored)
        self.assertIsInstance(self.stored['show_runtime_record'], dict)

    def test_stale_unpicklable_legacy_object_is_replaced_by_plain_data(self):
        class OldRuntime:
            def __reduce__(self):
                raise pickle.PicklingError('stale ShowSequencer class')
        self.stored['show_runtime_record'] = (self.tables['show_json'].text, OldRuntime())
        with self.assertRaises(pickle.PicklingError):
            pickle.dumps(self.stored)
        sequence = self.scope['runtime']()
        self.assert_plain_storage()
        self.assertEqual((sequence.cue_index, sequence.elapsed, sequence.plan().slot_b_time), (1, 3, 5))
        self.assertTrue(sequence.show.loop)
        self.assertTrue(sequence.blackout)
        self.assertEqual(sequence.state.value, 'paused')

    def test_explicit_play_runs_but_reopen_requires_play_again(self):
        self.scope['command']('play')
        self.scope['advance'](.5)
        self.assertEqual(self.scope['runtime']().state.value, 'playing')
        self.assert_plain_storage()
        reloaded = self.reload_callback()
        sequence = reloaded['runtime']()
        self.assertEqual(sequence.state.value, 'paused')
        self.assertEqual(sequence.elapsed, 3.5)
        reloaded['advance'](10)
        self.assertEqual(sequence.elapsed, 3.5)
        reloaded['command']('play')
        reloaded['advance'](.5)
        self.assertEqual(sequence.elapsed, 4)
        self.assert_plain_storage()

    def test_runtime_class_replacement_discards_transient_old_instance(self):
        original = self.scope['runtime']()
        class ReloadedSequencer(self.scope['ShowSequencer']):
            pass
        self.scope['ShowSequencer'] = ReloadedSequencer
        rebuilt = self.scope['runtime']()
        self.assertIsInstance(rebuilt, ReloadedSequencer)
        self.assertIsNot(rebuilt, original)
        self.assertEqual(rebuilt.plan().slot_b_time, original.plan().slot_b_time)
        self.assert_plain_storage()

    def test_legacy_object_is_removed_even_if_show_json_is_invalid(self):
        self.stored['show_runtime_record'] = ('old', object())
        self.tables['show_json'].text = '{invalid'
        with self.assertRaises(ValueError):
            self.scope['runtime']()
        self.assert_plain_storage()


if __name__ == '__main__':
    unittest.main()
