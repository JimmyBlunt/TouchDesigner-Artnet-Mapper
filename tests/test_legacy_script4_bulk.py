"""Parity against actual saved TD callback, including RNG and Float32 bytes."""
import ast
import builtins
import copy
import hashlib
import json
from pathlib import Path
import random
import struct
import unittest

from pixelblaze_mapper.legacy_script4_bulk import REFERENCE_SHA256, make_bulk_callback, source_for_bulk

CAPTURE = Path(__file__).parents[1] / 'docs/implementation-2026-09-07/performance/hot-sources.json'


def reference_source():
    text = json.loads(CAPTURE.read_text(encoding='utf-8'))['/project1/script4_callbacks']['text']
    if hashlib.sha256(text.encode()).hexdigest() != REFERENCE_SHA256:
        raise AssertionError('The real callback reference fixture changed')
    return text


def loaded_reference(seed, source=None):
    rng = random.Random(seed)
    imports = dict(vars(builtins))
    def isolated_import(name, *args, **kwargs):
        if name != 'random':
            raise AssertionError('Unexpected import in reviewed callback: ' + name)
        return rng
    imports['__import__'] = isolated_import
    namespace = {'__builtins__': imports}
    exec(compile(reference_source() if source is None else source, '<captured original script4_callbacks>', 'exec'), namespace)
    return namespace, rng


def float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


class Channel:
    def __init__(self, name, owner):
        self.name, self.owner = name, owner
        self.values = [0.0] * owner.numSamples
    def __setitem__(self, index, value):
        self.owner.scalar_writes += 1
        self.values[index] = float32(value)
    @property
    def vals(self):
        return list(self.values)
    @vals.setter
    def vals(self, values):
        self.owner.bulk_writes += 1
        if len(values) != self.owner.numSamples:
            raise ValueError('Channel size mismatch')
        self.values[:] = [float32(value) for value in values]


class Script:
    def __init__(self, count=0, names=()):
        self.channels = {}
        self._count = count
        self.scalar_writes = self.bulk_writes = 0
        for name in names:
            self.appendChan(name)
    @property
    def numSamples(self):
        return self._count
    @numSamples.setter
    def numSamples(self, value):
        self._count = value
        for channel in self.channels.values():
            channel.values[:] = [0.0] * value
    def clear(self): self.channels.clear()
    def appendChan(self, name):
        channel = Channel(name, self)
        self.channels[name] = channel
        return channel
    def chans(self): return list(self.channels.values())
    def __getitem__(self, name): return self.channels[name]
    def image(self):
        return [(name, struct.pack('<%df' % len(channel.values), *channel.values))
                for name, channel in self.channels.items()]


class LegacyBulkTests(unittest.TestCase):
    def parity(self, *, seed, calls, dense=False, count=0, names=(), whole_source=False):
        original, rng_before = loaded_reference(seed)
        optimized, rng_after = loaded_reference(seed, source_for_bulk(reference_source()) if whole_source else None)
        if dense:
            for index, state in enumerate(original['led_states']):
                state['active'] = True
                state['brightness'] = (0.010001, .5, 1.0)[index % 3]
            optimized['led_states'][:] = copy.deepcopy(original['led_states'])
        states = optimized['led_states']
        before = Script(count, names)
        after = Script(count, names)
        original_func = optimized['onCook']
        callback = original_func if whole_source else make_bulk_callback(original_func, reference_source())
        self.assertIs(callback.__globals__, original_func.__globals__)
        self.assertIs(optimized['led_states'], states)
        self.assertEqual(rng_before.getstate(), rng_after.getstate())
        for index in range(calls):
            original['onCook'](before)
            callback(after)
            self.assertEqual(before.image(), after.image(), 'Float32 byte mismatch at cook %d' % index)
            self.assertEqual(original['led_states'], optimized['led_states'])
            self.assertEqual(original['frame_count'], optimized['frame_count'])
            self.assertEqual(rng_before.getstate(), rng_after.getstate())
        self.assertEqual(before.scalar_writes, calls * 3 * 1152)
        self.assertEqual(after.scalar_writes, 0)
        self.assertEqual(after.bulk_writes, calls * 3)
        self.assertIs(optimized['led_states'], states)

    def test_sparse_random_simulation_exact_for_three_seeds_and_180_cooks(self):
        for seed in (0, 1234, 987654321):
            with self.subTest(seed=seed):
                self.parity(seed=seed, calls=60)

    def test_dense_fade_deactivation_and_clamping_state_parity(self):
        self.parity(seed=13, calls=80, dense=True, count=1152, names=('r', 'g', 'b'))

    def test_existing_channels_reordered_and_extra_channel_preserved(self):
        self.parity(seed=6, calls=3, count=1152, names=('b', 'r', 'extra', 'g'))

    def test_original_channel_initialization_and_resize_are_retained(self):
        for count, names in ((5, ('r', 'g', 'b')), (1152, ('r',)), (0, ())):
            with self.subTest(count=count, names=names):
                self.parity(seed=7, calls=2, count=count, names=names)

    def test_live_style_function_swap_preserves_existing_state_and_rng(self):
        namespace, rng = loaded_reference(5)
        script = Script()
        for _ in range(4):
            namespace['onCook'](script)
        states = namespace['led_states']
        document, count, rng_state = copy.deepcopy(states), namespace['frame_count'], rng.getstate()
        original = namespace['onCook']
        replacement = make_bulk_callback(original, reference_source())
        namespace['onCook'] = replacement
        self.assertIs(namespace['led_states'], states)
        self.assertEqual(states, document)
        self.assertEqual(namespace['frame_count'], count)
        self.assertEqual(rng.getstate(), rng_state)
        namespace['onCook'] = original  # Reversible without source reload.
        self.assertIs(namespace['led_states'], states)

    def test_source_or_running_function_change_blocks_without_mutating_state(self):
        namespace, rng = loaded_reference(4)
        before = copy.deepcopy(namespace['led_states']), rng.getstate()
        with self.assertRaisesRegex(ValueError, 'source differs'):
            make_bulk_callback(namespace['onCook'], reference_source() + '\n')
        with self.assertRaisesRegex(ValueError, 'Running onCook differs'):
            make_bulk_callback(lambda script: None, reference_source())
        self.assertEqual((namespace['led_states'], rng.getstate()), before)

    def test_full_source_changes_only_ast_transfer_loop_line_span(self):
        original = reference_source()
        result = source_for_bulk(original)
        callback = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == 'onCook')
        loop = next(node for node in callback.body if isinstance(node, ast.For))
        lines = original.splitlines(keepends=True)
        prefix, suffix = ''.join(lines[:loop.lineno - 1]), ''.join(lines[loop.end_lineno:])
        expected = ('    r_channel.vals = [value[0] for value in led_data]\n'
                    '    g_channel.vals = [value[1] for value in led_data]\n'
                    '    b_channel.vals = [value[2] for value in led_data]\n')
        self.assertEqual(result.encode(), (prefix + expected + suffix).encode())
        for name in ('generate_combined_effect', 'onSetupParameters'):
            before = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == name)
            after = next(node for node in ast.parse(result).body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.get_source_segment(original, before), ast.get_source_segment(result, after))

    def test_full_source_parity_including_initial_rng_consumption(self):
        self.parity(seed=2026, calls=40, whole_source=True)
        self.parity(seed=71, calls=40, dense=True, whole_source=True)

    def test_full_source_rejects_unknown_or_already_patched_source(self):
        for source in (reference_source() + '\n', reference_source().replace('0.98', '0.97'),
                       source_for_bulk(reference_source())):
            with self.subTest(source_length=len(source)):
                with self.assertRaisesRegex(ValueError, 'source differs'):
                    source_for_bulk(source)

    def test_synchronous_source_migration_and_rollback_restore_state_without_extra_steps(self):
        baseline, baseline_rng = loaded_reference(314)
        current, rng = loaded_reference(314)
        before, after = Script(), Script()
        for _ in range(8):
            baseline['onCook'](before)
            current['onCook'](after)
        for source in (source_for_bulk(reference_source()), reference_source()):
            states, count, rng_state = current['led_states'], current['frame_count'], rng.getstate()
            # Simulates a fresh DAT namespace on the same synchronous thread.
            new = {'__builtins__': current['__builtins__']}
            exec(compile(source, '<new DAT namespace simulation>', 'exec'), new)
            self.assertNotEqual(rng.getstate(), rng_state)  # Initialization really consumes RNG.
            new['led_states'], new['frame_count'] = states, count
            rng.setstate(rng_state)
            current = new
            self.assertIs(current['led_states'], states)
            self.assertEqual(current['frame_count'], baseline['frame_count'])
            self.assertEqual(rng.getstate(), baseline_rng.getstate())
            for _ in range(3):
                baseline['onCook'](before)
                current['onCook'](after)
                self.assertEqual(before.image(), after.image())
                self.assertEqual(baseline['led_states'], current['led_states'])
                self.assertEqual(baseline['frame_count'], current['frame_count'])
                self.assertEqual(baseline_rng.getstate(), rng.getstate())


if __name__ == '__main__':
    unittest.main()
