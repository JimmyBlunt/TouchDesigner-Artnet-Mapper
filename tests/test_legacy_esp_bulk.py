"""Byte parity against the captured native ESP callback; no TouchDesigner/output."""
import hashlib
import itertools
import json
from pathlib import Path
import random
from types import SimpleNamespace as NS
import unittest

try:
    from pixelblaze_mapper.legacy_esp_bulk import frames, source_for_bulk
except ImportError:
    frames = source_for_bulk = None

ROOT = Path(__file__).resolve().parents[1]


class Channel:
    def __init__(self, name, values): self.name, self.vals = name, list(values)
    def __getitem__(self, index): return self.vals[index]
    def __setitem__(self, index, value): self.vals[index] = value


class Source:
    def __init__(self, rgb):
        self.numSamples = len(rgb[0])
        self.data = {key: Channel(key, values) for key, values in zip('rgb', rgb)}
    def __getitem__(self, name): return self.data[name]


class Script:
    def __init__(self, source): self.inputs, self.outputs, self.numSamples = [source], [], 0
    def clear(self): self.outputs = []
    def appendChan(self, name):
        channel = Channel(name, [0] * self.numSamples)
        self.outputs.append(channel)
        return channel


@unittest.skipIf(frames is None, 'NumPy required for native bulk parity tests')
class LegacyBulkTests(unittest.TestCase):
    def test_all_color_orders_offsets_clamping_and_ties_match_captured_callback(self):
        baseline = json.loads((ROOT / 'docs/completion-20260910/legacy-output-before.json').read_text())['pack']
        changed = source_for_bulk(baseline, hashlib.sha256(baseline.encode()).hexdigest())
        rng = random.Random(51)
        rgb = [[rng.uniform(-.1, 1.1) for _ in range(1720)] for _ in range(3)]
        rgb[0][:8] = [0, .5, 1, 2.5/255, 3.5/255, 5.5/255, -1, 2]
        for order, offset, count, master in itertools.product((''.join(p) for p in itertools.permutations('RGB')), (0, 1700), (20, 1679), (.02, .5, 1.)):
            with self.subTest(order=order, offset=offset, count=count, master=master):
                config = dict(enabled='1', master_brightness=str(master), source_offset=str(offset), pixel_count=str(count), color_order=order)
                results = []
                for code in (baseline, changed):
                    ns = {'op': lambda path: None}
                    exec(compile(code, '<legacy parity>', 'exec'), ns)
                    ns['_config'] = lambda key, default: config.get(key, default)
                    script = Script(Source(rgb))
                    ns['onCook'](script)
                    results.append([channel.vals for channel in script.outputs])
                self.assertEqual(results[0], results[1])

    def test_inactive_slots_black_before_offset_and_keep_reserved_tail(self):
        result = frames([[1.] * 1800] * 3, offset=100, count=1679, order='RGB', master=1., inactive=((100, 101), (170, 170)))
        flat = result.reshape(-1).tolist()
        self.assertEqual(flat[:6], [0.] * 6)
        self.assertEqual(flat[6:9], [255.] * 3)
        self.assertEqual(flat[70*3:71*3], [0.] * 3)
        self.assertEqual(flat[1679*3:], [0.] * 63)
        self.assertEqual(result.shape, (10, 510))

    def test_invalid_parameters_and_nonfinite_channels_fail_closed(self):
        good = dict(offset=0, count=2, order='RGB', master=.5)
        for key, value in (('offset', True), ('offset', 1.2), ('count', -1), ('count', 1680),
                           ('master', float('nan')), ('master', True), ('order', 'RRB')):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                frames([[1., .2]] * 3, **dict(good, **{key: value}))
        with self.assertRaises(ValueError): frames([[1., float('nan')]] * 3, **good)
