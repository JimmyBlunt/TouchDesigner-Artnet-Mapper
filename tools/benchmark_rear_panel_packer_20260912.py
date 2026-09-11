"""Offline, byte-checked benchmark of the five mapped rear panels. No output."""
from pathlib import Path
import json
import platform
import random
import statistics
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixelblaze_mapper import realtime_packer
from pixelblaze_mapper.multi_controller import (
    ControllerConfig, RouterConfig, SegmentConfig, build_router_plan,
    MultiControllerValidationError,
)
from numbers import Real


def original(value, scale):
    value_type = type(value)
    if value_type is not float and value_type is not int and not isinstance(value, Real):
        raise MultiControllerValidationError('Source channel contains a non-numeric value')
    return max(0, min(255, int(round(float(value) * scale))))


def topology(brightness):
    segments = ((1440, 203, 0), (3744, 738, 340), (4482, 880, 1190),
                (5362, 810, 2210), (6172, 352, 3230))
    return RouterConfig(
        (ControllerConfig('rear', '10.0.0.248', '10.0.0.125', start_universe=120,
                          brightness=brightness, reserved_universes=29),),
        tuple(SegmentConfig(str(i), start, count, 'rear', destination)
              for i, (start, count, destination) in enumerate(segments)),
        source_pixel_count=6524, warn_unassigned=False,
    )


def benchmark():
    rng = random.Random(20260912)
    channels = tuple(tuple(rng.uniform(-.1, 1.1) for _ in range(6524)) for _ in range(3))
    result = {'python': platform.python_version(), 'source_pixels': 6524,
              'mapped_pixels': 2983, 'universes': 29,
              'scope': 'Offline tuple input; excludes TD indexing/cook, UDP and receiver.',
              'frames_per_repeat': 80, 'repeats': 7, 'measurements': []}
    optimized = realtime_packer._normalized_byte
    for brightness in (.2, .7):
        config = topology(brightness)
        plan = build_router_plan(config)
        packer = realtime_packer.compile_router_packer(plan)
        expected = {name: tuple(bytes(frame) for frame in frames)
                    for name, frames in plan.pack_pixels(tuple(zip(*channels))).items()}
        samples = {'original': [], 'optimized': []}
        for repeat in range(7):
            order = ('original', 'optimized') if repeat % 2 == 0 else ('optimized', 'original')
            for name in order:
                with patch.object(realtime_packer, '_normalized_byte',
                                  original if name == 'original' else optimized):
                    assert packer.pack_channels(*channels) == expected
                    started = time.perf_counter()
                    for _ in range(80):
                        packer.pack_channels(*channels)
                    samples[name].append((time.perf_counter() - started) * 1000 / 80)
        medians = {name: statistics.median(values) for name, values in samples.items()}
        result['measurements'].append({
            'brightness': brightness, 'byte_identical_to_reference': True,
            'milliseconds_per_frame': samples, 'median_ms': medians,
            'reduction_percent': 100 * (1 - medians['optimized'] / medians['original']),
        })
    return result


if __name__ == '__main__':
    print(json.dumps(benchmark(), indent=2))
