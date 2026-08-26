"""Offline benchmark for the canonical 3,744-LED Show renderer."""

from __future__ import annotations

from pathlib import Path
from statistics import median
import sys
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pixelblaze_mapper.installation_contract import TOTAL_PIXELS
from pixelblaze_mapper.show_renderer import render_frame, render_led


def benchmark(iterations: int = 25) -> dict[str, float]:
    count = TOTAL_PIXELS
    slot_a = ([40.0] * count, [80.0] * count, [120.0] * count)
    slot_b = ([160.0] * count, [200.0] * count, [240.0] * count)
    u = [index / (count - 1) for index in range(count)]
    v = [0.5] * count
    kwargs = dict(
        transition="crossfade", output_b_mix=0.5, brightness=0.8,
        blackout=False, targets_a=("middle", "rear"),
        targets_b=("upper", "lower"),
    )

    def legacy():
        return [
            render_led(
                tuple(channel[index] for channel in slot_a),
                tuple(channel[index] for channel in slot_b),
                led_index=index, uv=(u[index], v[index]), **kwargs,
            )
            for index in range(count)
        ]

    def bulk():
        return render_frame(slot_a, slot_b, u=u, v=v, **kwargs)

    bulk()  # warm cached target masks before measuring steady-state frames
    legacy_times, bulk_times = [], []
    for _ in range(iterations):
        started = perf_counter()
        legacy()
        legacy_times.append((perf_counter() - started) * 1000.0)
        started = perf_counter()
        bulk()
        bulk_times.append((perf_counter() - started) * 1000.0)
    before = median(legacy_times)
    after = median(bulk_times)
    return {
        "legacy_ms": before,
        "bulk_ms": after,
        "speedup": before / after,
        "pixels": float(count),
    }


if __name__ == "__main__":
    result = benchmark()
    print(
        "Show renderer: {pixels:.0f} LEDs | legacy {legacy_ms:.3f} ms | "
        "bulk {bulk_ms:.3f} ms | {speedup:.2f}x".format(**result)
    )
