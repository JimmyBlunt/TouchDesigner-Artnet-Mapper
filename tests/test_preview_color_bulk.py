"""Compare preview RGB behavior to the captured scalar callback, without TD."""
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
from pixelblaze_mapper import preview_color_bulk as bulk


ROOT = Path(__file__).resolve().parents[1]


def captured():
    return json.loads((ROOT/'docs/completion-20260910/performance-callbacks-before.json').read_text())['preview']


def scalar(rows, n):
    maxv = max(max(row[:n]) for row in rows)
    scale = (1.0/65025.0 if maxv > 255.0001 else 1.0/255.0) if maxv > 1.0001 else 1.0
    return [[max(0.0, min(1.0, float(v)*scale)) for v in row[:n]] for row in rows]


class NormalizeTests(unittest.TestCase):
    def test_scalar_equivalence_across_ranges_and_threshold_boundaries(self):
        rng = np.random.default_rng(20260910)
        maxima = [1, 1.0001, np.nextafter(1.0001, np.inf),
                  255, 255.0001, np.nextafter(255.0001, np.inf), 65025, 130050]
        for maximum in maxima:
            data = rng.uniform(-maximum*.2, maximum*.99, (3, 3744))
            data[2, 0] = maximum
            before = data.copy()
            with self.subTest(maximum=maximum):
                output = bulk.normalize_rgb(data, 3744)
                np.testing.assert_array_equal(output, scalar(data.tolist(), 3744))
                np.testing.assert_array_equal(data, before)
                self.assertFalse(np.shares_memory(output, data))

    def test_maximum_is_global_rgb_and_excludes_unused_tail(self):
        data = [[.5, 1, 65025], [0, -1, 999999], [255, 127.5, 999999]]
        output = bulk.normalize_rgb(data, 2)
        np.testing.assert_array_equal(output, scalar(data, 2))
        self.assertEqual(output[0, 1], 1/255)
        self.assertEqual(output[2, 0], 1)
        self.assertEqual(data[0], [.5, 1, 65025])

    def test_negative_and_zero_input_clamp_to_black(self):
        data = np.array([[-1, -0.0, 0], [-5, -100, 0], [-.5, -1e-300, 0]])
        np.testing.assert_array_equal(bulk.normalize_rgb(data, 3), np.zeros((3, 3)))

    def test_rare_nonfinite_input_preserves_ordered_scalar_semantics(self):
        for data in (
                [[float('nan'), .5], [255, .25], [0, 1]],
                [[.5, float('nan')], [0, 1], [255, .25]],
                [[float('inf'), .5], [float('-inf'), 1], [0, .25]]):
            with self.subTest(data=data):
                np.testing.assert_array_equal(bulk.normalize_rgb(data, 2), scalar(data, 2))

    def test_shape_validation_and_empty_sample_count(self):
        self.assertEqual(bulk.normalize_rgb([[], [], []], 0).shape, (3, 0))
        for data, n in (([[1], [2]], 1), ([[1], [2], [3]], 2), ([[1], [2], [3]], -1),
                        ([[1], [2], [3]], True)):
            with self.subTest(data=data, n=n), self.assertRaises(ValueError):
                bulk.normalize_rgb(data, n)

    def test_channel_names_determine_order_and_each_channel_is_read_once(self):
        class Channel:
            def __init__(self, values):
                self.values, self.reads = values, 0
            @property
            def vals(self):
                self.reads += 1
                return self.values
        channels = {'b': Channel([.7, .8]), 'a': Channel([999, 999]),
                    'r': Channel([.1, .2]), 'g': Channel([.3, .4])}
        self.assertEqual(bulk.normalized_chop_colors(channels, 2), [[.1, .2], [.3, .4], [.7, .8]])
        self.assertEqual([channels[name].reads for name in ('r', 'g', 'b', 'a')], [1, 1, 1, 0])


class SourceTests(unittest.TestCase):
    def test_source_replacement_verifies_capture_and_only_changes_exact_block(self):
        source = captured()
        self.assertEqual(sha256(source.encode()).hexdigest(), bulk.CAPTURED_SHA256)
        changed = bulk.source_for_bulk(source)
        self.assertEqual(changed.replace(bulk.BULK_BLOCK, bulk.SCALAR_BLOCK), source)
        self.assertEqual(bulk.ensure_bulk_source(changed), changed)
        self.assertIn('# P0_CANONICAL_MISSING_BLACK', changed)
        self.assertIn('colorsys.hsv_to_rgb', changed)

    def test_unknown_or_edited_source_is_rejected(self):
        source = captured()
        with self.assertRaisesRegex(ValueError, 'baseline'):
            bulk.source_for_bulk(source + '\n# changed')
        wrong = source.replace('255.0001', '255.1')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            bulk.source_for_bulk(wrong, sha256(wrong.encode()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'reviewed callback'):
            bulk.ensure_bulk_source(bulk.source_for_bulk(source) + '\n# unexpected')

    def test_actual_callback_keeps_channel_order_coordinates_and_missing_mask(self):
        class Param:
            def __init__(self, value): self.value = value
            def eval(self): return self.value
        class Table:
            def __init__(self): self.rows = []
            @property
            def numRows(self): return len(self.rows)
            @property
            def numCols(self): return len(self.rows[0]) if self.rows else 0
            def __getitem__(self, key): return self.rows[key[0]][key[1]]
            def clear(self): self.rows.clear()
            def appendRow(self, row): self.rows.append(row)
        class ColorInput:
            path = '/colors'
            numSamples = 3744
            def __init__(self):
                self.channels = {name: SimpleNamespace(vals=(np.arange(3744) % 256 * factor).tolist())
                                 for name, factor in (('b', 1), ('r', .5), ('g', .25))}
            def __getitem__(self, name): return self.channels.get(name)
        class Script:
            def __init__(self, owner): self.owner, self.channels, self.numSamples = owner, {}, 0
            def parent(self): return self.owner
            def clear(self): self.channels.clear()
            def appendChan(self, name):
                self.channels[name] = SimpleNamespace(vals=[])
                return self.channels[name]
            def fetch(self, key, default=None): return default
        def run(source):
            color, table = ColorInput(), Table()
            owner = SimpleNamespace(par=SimpleNamespace(Colorchop=Param('colors'), Fitmode=Param('contain')),
                op=lambda path: {'colors': color, 'preview_status': table,
                                 'preview_out': SimpleNamespace(path='/preview/out')}.get(path))
            script = Script(owner)
            scope = {}
            exec(source, scope)
            points = [(i/3744, 0, 0) for i in range(3744)]
            scope['_coordinates'] = lambda *_: (SimpleNamespace(path='/coordinates'), points,
                                                 [-1, 0, 17, 3743, 3744], '')
            scope['onCook'](script)
            return script, table
        original, original_status = run(captured())
        updated, updated_status = run(bulk.source_for_bulk(captured()))
        self.assertEqual(list(updated.channels), ['tx', 'ty', 'tz', 'r', 'g', 'b'])
        for name in original.channels:
            np.testing.assert_array_equal(updated.channels[name].vals, original.channels[name].vals)
        self.assertEqual(updated_status.rows, original_status.rows)
        for name in ('r', 'g', 'b'):
            self.assertEqual([updated.channels[name].vals[i] for i in (0, 17, 3743)], [0, 0, 0])


if __name__ == '__main__':
    unittest.main()
