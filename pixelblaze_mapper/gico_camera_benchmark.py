"""Pure optical benchmark encoding/analysis. Importing this module sends nothing."""
from __future__ import annotations

import math
import statistics

BITS = 12
MODULUS = 1 << BITS
MARKERS = 21  # 12 Gray bits, 8 CRC bits, constant white reference
PANELS = (("side_1", 517, 0), ("side_2", 269, 1020), ("side_3", 398, 2040))
UNIVERSES = 24
LEVEL = 16


def crc8(data):
    """CRC-8/ATM, polynomial 0x07, init 0, no reflection/xorout."""
    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ (7 if crc & 128 else 0)) & 255
    return crc


def encode(frame_id):
    if type(frame_id) is not int or not 0 <= frame_id < MODULUS:
        raise ValueError("Frame ID must be an integer in 0..4095")
    gray = frame_id ^ (frame_id >> 1)
    check = crc8(frame_id.to_bytes(2, "little"))
    return [(gray >> i) & 1 for i in range(BITS)] + [(check >> i) & 1 for i in range(8)] + [1]


def decode(bits):
    if len(bits) != MARKERS or any(v not in (0, 1) for v in bits) or bits[-1] != 1:
        return None
    gray = sum(bits[i] << i for i in range(BITS))
    value = gray
    while gray:
        gray >>= 1
        value ^= gray
    check = sum(bits[BITS+i] << i for i in range(8))
    return value if crc8(value.to_bytes(2, "little")) == check else None


def marker_indices(count):
    """Spread markers through the physical chain, including both ends."""
    if count < MARKERS:
        raise ValueError("Panel is too small")
    return [round(i * (count - 1) / (MARKERS - 1)) for i in range(MARKERS)]


def payloads(bits, level=LEVEL):
    if len(bits) != MARKERS or any(v not in (0, 1) for v in bits):
        raise ValueError("Expected 21 binary marker states")
    if type(level) is not int or not 1 <= level <= 25:
        raise ValueError("Benchmark level must be 1..25 (at most 9.8 percent)")
    result = [bytearray(510) for _ in range(UNIVERSES)]
    for _, count, base in PANELS:
        for index, enabled in zip(marker_indices(count), bits):
            pixel = base + index
            universe, offset = divmod(pixel, 170)
            result[universe][offset * 3:offset * 3 + 3] = bytes([level * enabled] * 3)
    return [bytes(p) for p in result]


def packet(universe, data, sequence=0):
    if not 0 <= universe < UNIVERSES or len(data) != 510 or not 0 <= sequence <= 255:
        raise ValueError("Invalid benchmark ArtDmx packet")
    return b"Art-Net\0\x00\x50\x00\x0e" + bytes([sequence, 0, universe, 0, 1, 254]) + data


def plan():
    return {
        "schema": 1, "target": "10.0.0.244", "interface": "10.0.0.125",
        "universes": list(range(UNIVERSES)), "level": LEVEL,
        "artdmx_sequence": 0,
        "artdmx_sequence_reason": "GICO compatibility; optical identity uses Gray+CRC payload",
        "id_bits": BITS, "crc": "CRC-8/ATM", "marker_count": MARKERS,
        "panels": [{"name": n, "count": c, "destination_start": b,
                    "local_marker_indices": marker_indices(c)} for n, c, b in PANELS],
        "preamble": {"all_on_seconds": 3, "black_seconds": 1,
                     "marker_seconds": 1, "marker_order": list(range(MARKERS))},
        "cases": [{"fps": fps, "warmup_seconds": 3, "seconds": 60} for fps in (15, 25, 30)],
        "minimum_camera_fps": 120, "preferred_camera_fps": 240,
        "receiver_fps": None,
    }


def decode_levels(values, low, high):
    """Reject transition/exposure ambiguity instead of silently guessing bits."""
    if any(len(v) != MARKERS for v in (values, low, high)):
        raise ValueError("Expected 21 marker samples")
    ratios = []
    for value, dark, lit in zip(values, low, high):
        if not all(math.isfinite(v) for v in (value, dark, lit)) or lit-dark < 15:
            return None, "calibration_contrast"
        ratios.append((value-dark)/(lit-dark))
    # Per-frame global brightness correction from permanent reference marker.
    reference = ratios[-1]
    if not .45 <= reference <= 1.8:
        return None, "reference_exposure"
    ratios = [v/reference for v in ratios]
    if any(.25 < v < .75 for v in ratios):
        return None, "transition_or_pwm"
    bits = [int(v >= .75) for v in ratios]
    decoded = decode(bits)
    return (decoded, "valid") if decoded is not None else (None, "crc_or_reference")


def summarize(samples, expected_fps, min_stable=2):
    """Conservative observational summary; gaps are never labelled proven loss."""
    if expected_fps <= 0 or min_stable < 1:
        raise ValueError("Invalid expected rate or stability threshold")
    if any(not math.isfinite(s["time"]) for s in samples):
        raise ValueError("Invalid timestamp")
    if any(b["time"] <= a["time"] for a, b in zip(samples, samples[1:])):
        raise ValueError("Camera timestamps must be strictly increasing")
    # Only consecutive valid camera frames establish a stable observed ID.
    runs = []
    for sample in samples:
        value = sample.get("id")
        if value is not None and (type(value) is not int or not 0 <= value < MODULUS):
            raise ValueError("Invalid decoded frame ID")
        if runs and value is not None and runs[-1]["id"] == value:
            runs[-1]["count"] += 1
            runs[-1]["last"] = sample["time"]
        else:
            runs.append({"id": value, "first": sample["time"], "last": sample["time"], "count": 1})
    stable = [r for r in runs if r["id"] is not None and r["count"] >= min_stable]
    distinct = []
    for run in stable:
        if distinct and distinct[-1]["id"] == run["id"]:
            distinct[-1]["last"] = run["last"]
        else:
            distinct.append(dict(run))
    gaps = []; intervals = []; backwards = 0
    for a, b in zip(distinct, distinct[1:]):
        delta = (b["id"]-a["id"]) % MODULUS
        elapsed = b["first"]-a["first"]
        # Large/backwards discontinuities are excluded, not counted as 4000 drops.
        if delta > min(MODULUS // 2, math.ceil(elapsed*expected_fps*2)+2):
            backwards += 1
            continue
        intervals.append(elapsed)
        if delta > 1:
            gaps.append({"after_id": a["id"], "before_id": b["id"],
                         "unobserved_ids": delta-1, "start": a["first"], "end": b["first"]})
    # The first visible ID can already be mid-hold at the recording/window edge.
    # Exclude it from rate estimation so a clipped first hold cannot inflate FPS.
    rate_images = distinct[1:]
    span = rate_images[-1]["first"]-rate_images[0]["first"] if len(rate_images) > 1 else 0
    camera_intervals = [b["time"]-a["time"] for a, b in zip(samples, samples[1:])]
    camera_fps = 1/statistics.median(camera_intervals) if camera_intervals else None
    rejected = sum(s.get("id") is None for s in samples)
    warnings = ["Unobserved IDs can be camera/decode misses; they are not proven controller drops.",
                "A camera cannot distinguish repeated electrical refreshes of the same LED image.",
                "CRC8 reduces but does not eliminate plausible mixed-frame/rolling-shutter errors."]
    if camera_fps is None or camera_fps < expected_fps*4*.95:
        warnings.append("Camera sampling is below 4x requested sender FPS.")
    if backwards:
        warnings.append("Unexpected ID discontinuities detected; do not infer controller loss.")
    return {"camera_samples": len(samples), "valid_samples": len(samples)-rejected,
            "rejected_fraction": rejected/len(samples) if samples else None,
            "stable_distinct_images": len(distinct), "observation_span_seconds": span,
            "observed_unique_fps_estimate": (len(rate_images)-1)/span if span and not backwards else None,
            "camera_fps_median": camera_fps,
            "camera_interval_max_ms": max(camera_intervals)*1000 if camera_intervals else None,
            "observed_interval_max_ms": max(intervals)*1000 if intervals else None,
            "unobserved_ids": sum(g["unobserved_ids"] for g in gaps),
            "unobserved_ranges": gaps, "unexpected_discontinuities": backwards,
            "proven_controller_drops": None, "warnings": warnings}
