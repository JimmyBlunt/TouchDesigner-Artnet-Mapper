"""Exact legacy byte/exception parity plus an opt-in offline benchmark."""

import builtins
from decimal import Decimal
from fractions import Fraction
import importlib.util
import math
from numbers import Real
import random
import unittest
from unittest.mock import patch

from pixelblaze_mapper import realtime_packer as packer
from pixelblaze_mapper.multi_controller import MultiControllerValidationError, build_router_plan, default_router_config


def legacy_normalized_byte(value, scale):
    """Frozen pre-optimization implementation, including its bool acceptance."""
    if not isinstance(value, Real):
        raise MultiControllerValidationError('Source channel contains a non-numeric value')
    return max(0, min(255, int(round(float(value) * scale))))


def outcome(function, value, scale):
    try:
        return ('byte', function(value, scale))
    except Exception as error:
        return (type(error), str(error))


class RealtimePackerFastpathTests(unittest.TestCase):
    def test_builtin_numbers_bypass_real_abc_but_other_types_keep_fallback(self):
        checks = []
        def checked(value, cls):
            checks.append(type(value))
            return builtins.isinstance(value, cls)
        with patch.object(packer, 'isinstance', checked, create=True):
            for value in (0., .5, 1., -1., 0, 1, 999):
                packer._normalized_byte(value, 255.)
            self.assertEqual(checks, [])
            for value in (True, False, Fraction(1, 3)):
                self.assertEqual(packer._normalized_byte(value, 255.), legacy_normalized_byte(value, 255.))
        self.assertEqual(checks, [bool, bool, Fraction])

    def test_halfway_neighbors_clamps_signed_zero_and_random_bytes_match_legacy(self):
        rng = random.Random(9107)
        for scale in (0., 255. * .37, 127.5, 255.):
            values = [-0., 0., -1., 1., 2., -999, 999, True, False]
            if scale:
                for byte in range(-2, 258):
                    half = (byte + .5) / scale
                    values.extend((math.nextafter(half, -math.inf), half, math.nextafter(half, math.inf)))
            values.extend(rng.uniform(-2, 3) for _ in range(1000))
            expected = bytes(legacy_normalized_byte(value, scale) for value in values)
            actual = bytes(packer._normalized_byte(value, scale) for value in values)
            self.assertEqual(actual, expected)

    def test_nonfinite_overflow_and_rejected_types_have_identical_exception_type_and_message(self):
        values = (math.nan, math.inf, -math.inf, 1e308, -1e308, 10**500,
                  None, '0.5', 1j, Decimal('.5'), object())
        for value in values:
            for scale in (0., 255. * .37, 255.):
                with self.subTest(value=repr(value), scale=scale):
                    self.assertEqual(outcome(packer._normalized_byte, value, scale),
                                     outcome(legacy_normalized_byte, value, scale))
        self.assertIs(outcome(packer._normalized_byte, math.nan, 255.)[0], ValueError)
        self.assertIs(outcome(packer._normalized_byte, math.inf, 255.)[0], OverflowError)

    def test_real_subclasses_keep_float_conversion(self):
        class CustomFloat(float):
            def __float__(self):
                return .25
        class CustomInt(int):
            def __float__(self):
                return .75
        for value in (CustomFloat(999), CustomInt(999), Fraction(1, 2), Fraction(-1, 2)):
            self.assertEqual(packer._normalized_byte(value, 255.), legacy_normalized_byte(value, 255.))

    @unittest.skipUnless(importlib.util.find_spec('numpy') is not None, 'NumPy unavailable; use existing native interpreter for this check')
    def test_numpy_real_fallback_is_unchanged(self):
        import numpy as np
        for value in (np.float32(.5), np.float64(.5), np.int32(1), np.int64(1),
                      np.float32(np.nan), np.float64(np.inf), np.bool_(True)):
            for scale in (0., 127.5, 255.):
                self.assertEqual(outcome(packer._normalized_byte, value, scale),
                                 outcome(legacy_normalized_byte, value, scale))

    def test_entire_payloads_match_frozen_legacy_converter(self):
        plan = build_router_plan(default_router_config())
        compiled = packer.compile_router_packer(plan)
        values = (-.1, 0, -0., True, False, .5 / 255, 1.5 / 255, .5, 1, 1.1, Fraction(1, 3))
        channels = tuple(tuple(values[(index + channel) % len(values)] for index in range(plan.config.source_pixel_count))
                         for channel in range(3))
        actual = compiled.pack_channels(*channels)
        with patch.object(packer, '_normalized_byte', legacy_normalized_byte):
            legacy = compiled.pack_channels(*channels)
        self.assertEqual(actual, legacy)


def benchmark():
    """No network/TD imports: fixed inputs, byte equality, paired median timing."""
    import json
    import platform
    import statistics
    import time
    rng = random.Random(9107)
    compiled = packer.compile_router_packer(build_router_plan(default_router_config()))
    count = compiled.controllers[0].source_pixel_count
    channels = tuple(tuple(rng.uniform(-.1, 1.1) for _ in range(count)) for _ in range(3))
    fast = packer._normalized_byte
    expected = compiled.pack_channels(*channels)
    timings = {'legacy': [], 'fast': []}
    frames = 150
    for iteration in range(7):
        # Alternate order to reduce consistent warm-up/thermal bias.
        order = ('legacy', 'fast') if iteration % 2 == 0 else ('fast', 'legacy')
        for name in order:
            with patch.object(packer, '_normalized_byte', fast if name == 'fast' else legacy_normalized_byte):
                assert compiled.pack_channels(*channels) == expected
                started = time.perf_counter()
                for _ in range(frames):
                    compiled.pack_channels(*channels)
                timings[name].append(time.perf_counter() - started)
    medians = {name: statistics.median(values) for name, values in timings.items()}
    print(json.dumps({'python': platform.python_version(), 'platform': platform.platform(),
        'frames_per_repeat': frames, 'repeats': 7, 'source_pixels': count,
        'writes_per_frame': sum(len(item.writes) for item in compiled.controllers),
        'bitwise_equal': True, 'seconds': timings, 'median_seconds': medians,
        'speedup': medians['legacy'] / medians['fast'],
        'time_reduction_percent': 100 * (1 - medians['fast'] / medians['legacy']),
        'benchmark_scope': 'offline default compiled router, builtin-float channels; not live TD FPS'}, indent=2))


if __name__ == '__main__':
    import sys
    if '--benchmark' in sys.argv:
        benchmark()
    else:
        unittest.main()
