"""Offline benchmark for the reference and compiled Art-Net packers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelblaze_mapper.multi_controller import build_router_plan, default_router_config
from pixelblaze_mapper.realtime_packer import compile_router_packer


def _measure(callback, iterations: int) -> tuple[float, float, float]:
    samples = []
    for _ in range(iterations):
        started = time.perf_counter()
        callback()
        samples.append((time.perf_counter() - started) * 1000.0)
    return min(samples), statistics.median(samples), statistics.mean(samples)


def benchmark(iterations: int = 200) -> dict[str, object]:
    pixels = tuple(
        ((index % 256) / 255.0, ((index + 1) % 256) / 255.0, ((index + 2) % 256) / 255.0)
        for index in range(3744)
    )
    red, green, blue = (tuple(pixel[channel] for pixel in pixels) for channel in range(3))
    plan = build_router_plan(default_router_config())
    compiled = compile_router_packer(plan)
    expected = plan.pack_pixels(pixels)
    actual = compiled.pack_channels(red, green, blue)
    byte_identical = all(
        actual[name] == tuple(bytes(frame) for frame in frames)
        for name, frames in expected.items()
    )
    reference = _measure(lambda: plan.pack_pixels(pixels), iterations)
    optimized = _measure(lambda: compiled.pack_channels(red, green, blue), iterations)
    ws = compiled.controller("WS2812_NODE")
    active_only = _measure(lambda: ws.pack_channels(red, green, blue), iterations)
    return {
        "iterations": iterations,
        "byte_identical": byte_identical,
        "reference_ms": {"min": reference[0], "median": reference[1], "mean": reference[2]},
        "compiled_all_ms": {"min": optimized[0], "median": optimized[1], "mean": optimized[2]},
        "compiled_ws_only_ms": {"min": active_only[0], "median": active_only[1], "mean": active_only[2]},
        "median_reduction_percent": 100.0 * (1.0 - optimized[1] / reference[1]),
        "active_only_median_reduction_percent": 100.0 * (1.0 - active_only[1] / reference[1]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=200)
    args = parser.parse_args()
    result = benchmark(max(1, args.iterations))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["byte_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
