"""Replace only the lower side-panel index order in the 3740-point map.

The replacement scan is a standalone MariMapper/Pixelblaze coordinate array.
It is projected from scanner X/Z into the already calibrated lower-panel box.
All coordinates outside the reserved lower-panel slice remain unchanged.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


TOTAL_POINTS = 3740
LOWER_START = 781
LOWER_RESERVED = 399
REAR_START = 1180
EXPECTED_NEW_POINTS = 399
HARDWARE_LOWER_CAPACITY = 402


Coordinate = tuple[float, float, float]


@dataclass(frozen=True)
class RewireReport:
    source_points: int
    source_missing: int
    appended_points: int
    estimated_points: int
    reserved_points: int
    padding_points: int
    lower_start: int
    rear_start: int
    hardware_trailing_black: int


def _coordinate(value: Sequence[float]) -> Coordinate:
    if len(value) != 3:
        raise ValueError("Every mapping point must contain exactly x, y, z")
    point = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in point):
        raise ValueError("Mapping coordinates must be finite")
    return point  # type: ignore[return-value]


def load_coordinate_array(path: str | Path) -> tuple[Coordinate, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Pixelblaze mapping must be a JSON coordinate array")
    return tuple(_coordinate(point) for point in data)


def _missing(point: Coordinate) -> bool:
    return all(abs(value) <= 1e-12 for value in point)


def _bounds(values: Iterable[float]) -> tuple[float, float]:
    items = tuple(values)
    if not items:
        raise ValueError("Cannot align an empty point set")
    low, high = min(items), max(items)
    if math.isclose(low, high, abs_tol=1e-12):
        raise ValueError("Cannot align a zero-size point set")
    return low, high


def align_scan_to_lower_panel(
    scan: Sequence[Coordinate],
    current_lower: Sequence[Coordinate],
) -> tuple[Coordinate, ...]:
    """Keep the existing panel box while adopting the new LED index order.

    Scanner X becomes the existing first panel coordinate. Scanner Z is
    inverted for the second coordinate, matching the established side-panel
    orientation and the already verified downward animation direction.
    """

    scan_valid = tuple(point for point in scan if not _missing(point))
    target_valid = tuple(point for point in current_lower if not _missing(point))
    sx0, sx1 = _bounds(point[0] for point in scan_valid)
    sz0, sz1 = _bounds(-point[2] for point in scan_valid)
    tx0, tx1 = _bounds(point[0] for point in target_valid)
    ty0, ty1 = _bounds(point[1] for point in target_valid)
    target_z = sum(point[2] for point in target_valid) / len(target_valid)

    def scale(value: float, source: tuple[float, float], target: tuple[float, float]) -> float:
        return target[0] + (value - source[0]) * (target[1] - target[0]) / (source[1] - source[0])

    result = []
    for point in scan:
        if _missing(point):
            result.append((0.0, 0.0, 0.0))
        else:
            result.append((
                scale(point[0], (sx0, sx1), (tx0, tx1)),
                scale(-point[2], (sz0, sz1), (ty0, ty1)),
                target_z,
            ))
    return tuple(result)


def estimate_missing_points(points: Sequence[Coordinate]) -> tuple[Coordinate, ...]:
    """Estimate missing coordinates along the physical LED index path.

    Internal gaps are linearly interpolated between the nearest registered
    neighbours. Missing points at either end continue the nearest contiguous
    run using a least-squares line. This is intentionally deterministic so the
    estimated locations can be reviewed and regenerated exactly.
    """

    values = tuple(_coordinate(point) for point in points)
    valid = tuple(index for index, point in enumerate(values) if not _missing(point))
    if len(valid) < 2:
        raise ValueError("At least two registered LED positions are required")

    result = list(values)
    valid_set = set(valid)

    def interpolate(index: int, left: int, right: int) -> Coordinate:
        amount = (index - left) / (right - left)
        return tuple(
            values[left][axis] + amount * (values[right][axis] - values[left][axis])
            for axis in range(3)
        )  # type: ignore[return-value]

    def contiguous_tail(before: bool) -> tuple[int, ...]:
        ordered = valid if before else tuple(reversed(valid))
        run = [ordered[0]]
        step = 1 if before else -1
        for index in ordered[1:]:
            if index == run[-1] + step:
                run.append(index)
                if len(run) == 4:
                    break
            else:
                break
        if len(run) < 2:
            run = list(ordered[:min(4, len(ordered))])
        return tuple(sorted(run))

    def extrapolate(index: int, anchors: Sequence[int]) -> Coordinate:
        mean_index = sum(anchors) / len(anchors)
        variance = sum((item - mean_index) ** 2 for item in anchors)
        if variance <= 1e-12:
            raise ValueError("Cannot extrapolate from coincident LED indices")
        result_axes = []
        for axis in range(3):
            mean_value = sum(values[item][axis] for item in anchors) / len(anchors)
            slope = sum(
                (item - mean_index) * (values[item][axis] - mean_value)
                for item in anchors
            ) / variance
            result_axes.append(mean_value + slope * (index - mean_index))
        return tuple(result_axes)  # type: ignore[return-value]

    first, last = valid[0], valid[-1]
    start_anchors = contiguous_tail(True)
    end_anchors = contiguous_tail(False)
    for index in range(len(values)):
        if index in valid_set:
            continue
        left = next((item for item in reversed(valid) if item < index), None)
        right = next((item for item in valid if item > index), None)
        if left is not None and right is not None:
            result[index] = interpolate(index, left, right)
        elif index < first:
            result[index] = extrapolate(index, start_anchors)
        elif index > last:
            result[index] = extrapolate(index, end_anchors)
        else:
            raise RuntimeError("Unable to estimate missing LED position")
    return tuple(result)


def replace_lower_panel(
    current: Sequence[Sequence[float]],
    scan: Sequence[Sequence[float]],
) -> tuple[tuple[Coordinate, ...], RewireReport]:
    mapping = tuple(_coordinate(point) for point in current)
    replacement = tuple(_coordinate(point) for point in scan)
    if len(mapping) != TOTAL_POINTS:
        raise ValueError(f"Expected {TOTAL_POINTS} current mapping points")
    if len(replacement) > EXPECTED_NEW_POINTS:
        raise ValueError(f"Expected at most {EXPECTED_NEW_POINTS} new lower-panel points")
    if LOWER_START + LOWER_RESERVED != REAR_START:
        raise RuntimeError("Lower-panel slice no longer ends at the rear-panel boundary")

    old_lower = mapping[LOWER_START:REAR_START]
    appended = EXPECTED_NEW_POINTS - len(replacement)
    padded_scan = replacement + ((0.0, 0.0, 0.0),) * appended
    aligned_with_gaps = align_scan_to_lower_panel(padded_scan, old_lower)
    aligned = estimate_missing_points(aligned_with_gaps)
    padding = ((0.0, 0.0, 0.0),) * (LOWER_RESERVED - len(aligned))
    combined = mapping[:LOWER_START] + aligned + padding + mapping[REAR_START:]
    if len(combined) != TOTAL_POINTS:
        raise RuntimeError("Replacement changed the total mapping length")
    if combined[:LOWER_START] != mapping[:LOWER_START]:
        raise RuntimeError("A preceding panel was modified")
    if combined[REAR_START:] != mapping[REAR_START:]:
        raise RuntimeError("Rear-panel coordinates were modified")

    report = RewireReport(
        source_points=len(replacement),
        source_missing=sum(_missing(point) for point in replacement),
        appended_points=appended,
        estimated_points=sum(_missing(point) for point in padded_scan),
        reserved_points=LOWER_RESERVED,
        padding_points=len(padding),
        lower_start=LOWER_START,
        rear_start=REAR_START,
        hardware_trailing_black=HARDWARE_LOWER_CAPACITY - len(aligned),
    )
    return combined, report
