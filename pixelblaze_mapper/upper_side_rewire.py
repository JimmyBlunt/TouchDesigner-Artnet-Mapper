"""Replace only the upper side-panel index order in the 3,740-point map."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from pixelblaze_mapper.lower_side_rewire import (
    Coordinate,
    _coordinate,
    _missing,
    estimate_missing_points,
)


TOTAL_POINTS = 3740
UPPER_START = 509
UPPER_RESERVED = 272
UPPER_END = UPPER_START + UPPER_RESERVED
EXPECTED_NEW_POINTS = 270
HARDWARE_UPPER_CAPACITY = 272
MISSING_HARDWARE_INDICES = (62, 63)

# Calibrated from all 268 measured 3D positions.  These two orthogonal plane
# directions follow the cabinet's physical horizontal and vertical LED grid;
# unlike a single tile's wiring order they remain valid for every rotated tile.
UPPER_HORIZONTAL_UNIT = (0.6070654226367344, -0.7653479219402478, 0.21380863177296558)
UPPER_VERTICAL_UNIT = (-0.7766660247957918, -0.514525117381007, 0.36339206033148785)
UPPER_HORIZONTAL_STEP = 0.82912303
UPPER_VERTICAL_STEP = 0.95022662


@dataclass(frozen=True)
class UpperRewireReport:
    source_points: int
    source_missing: int
    inserted_points: int
    discarded_points: int
    appended_points: int
    estimated_points: int
    reserved_points: int
    padding_points: int
    upper_start: int
    upper_end: int
    hardware_trailing_black: int


def _subtract(left: Coordinate, right: Coordinate) -> Coordinate:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _dot(left: Coordinate, right: Coordinate) -> float:
    return sum(a * b for a, b in zip(left, right))


def _normalize(vector: Coordinate) -> Coordinate:
    length = math.sqrt(_dot(vector, vector))
    if length <= 1e-12:
        raise ValueError("Cannot derive an axis from coincident scan points")
    return tuple(value / length for value in vector)  # type: ignore[return-value]


def _average(vectors: Sequence[Coordinate]) -> Coordinate:
    if not vectors:
        raise ValueError("Cannot average an empty vector set")
    return tuple(sum(item[axis] for item in vectors) / len(vectors) for axis in range(3))  # type: ignore[return-value]


def _grid_axes(scan: Sequence[Coordinate]) -> tuple[Coordinate, Coordinate]:
    """Return whole-panel grid steps independent of per-tile wiring rotation."""

    if len(scan) < EXPECTED_NEW_POINTS:
        raise ValueError("The complete indexed upper-panel scan is required")
    return (
        tuple(value * UPPER_HORIZONTAL_STEP for value in UPPER_HORIZONTAL_UNIT),
        tuple(value * UPPER_VERTICAL_STEP for value in UPPER_VERTICAL_UNIT),
    )


def _basis_coordinates(
    vector: Coordinate,
    first_axis: Coordinate,
    second_axis: Coordinate,
) -> tuple[float, float]:
    """Resolve a 3D vector in the measured, potentially sheared grid basis."""

    first_first = _dot(first_axis, first_axis)
    first_second = _dot(first_axis, second_axis)
    second_second = _dot(second_axis, second_axis)
    determinant = first_first * second_second - first_second * first_second
    if abs(determinant) <= 1e-12:
        raise ValueError("The scanned grid axes are linearly dependent")
    vector_first = _dot(vector, first_axis)
    vector_second = _dot(vector, second_axis)
    first_amount = (
        vector_first * second_second - vector_second * first_second
    ) / determinant
    second_amount = (
        vector_second * first_first - vector_first * first_second
    ) / determinant
    return first_amount, second_amount


def scan_grid_coordinates(scan: Sequence[Coordinate]) -> tuple[tuple[float, float], ...]:
    """Return cabinet-oriented X/Y coordinates in physical LED-grid units."""

    first_axis, second_axis = _grid_axes(scan)
    origin = scan[0]
    result = []
    for point in scan:
        first, second = _basis_coordinates(
            _subtract(point, origin), first_axis, second_axis
        )
        # The new upper-panel scan already uses the cabinet orientation.
        # Keeping the scan axes prevents a requested row from becoming a
        # physical column on the mounted panel.
        result.append((first, second))
    return tuple(result)


def restore_scan_indices(scan: Sequence[Coordinate]) -> tuple[Coordinate, ...]:
    """Restore the two unscanned LEDs at the end of the first 8x8 tile."""

    values = tuple(_coordinate(point) for point in scan)
    if len(values) == EXPECTED_NEW_POINTS:
        return values
    if len(values) != 268:
        raise ValueError(
            f"Expected 268 exported or {EXPECTED_NEW_POINTS} indexed upper points"
        )
    missing = set(MISSING_HARDWARE_INDICES)
    restored = []
    source_index = 0
    for hardware_index in range(EXPECTED_NEW_POINTS):
        if hardware_index in missing:
            restored.append((0.0, 0.0, 0.0))
        else:
            restored.append(values[source_index])
            source_index += 1
    if source_index != len(values):
        raise RuntimeError("Not all exported upper-panel scan points were consumed")
    return tuple(restored)


def _bounds(values: Sequence[float]) -> tuple[float, float]:
    low, high = min(values), max(values)
    if math.isclose(low, high, abs_tol=1e-12):
        raise ValueError("Cannot align a zero-size coordinate range")
    return low, high


def _scale(value: float, source: tuple[float, float], target: tuple[float, float]) -> float:
    return target[0] + (value - source[0]) * (target[1] - target[0]) / (source[1] - source[0])


def align_scan_to_upper_panel(
    scan: Sequence[Coordinate],
    current_upper: Sequence[Coordinate],
) -> tuple[Coordinate, ...]:
    """Flatten the new 3D scan and fit it into the existing upper panel box."""

    target_valid = tuple(point for point in current_upper if not _missing(point))
    if not target_valid:
        raise ValueError("The current upper panel has no usable target coordinates")

    grid_coordinates = scan_grid_coordinates(scan)
    projected_x = [point[0] for point in grid_coordinates]
    projected_y = [point[1] for point in grid_coordinates]
    source_x = _bounds(projected_x)
    source_y = _bounds(projected_y)
    target_x = _bounds([point[0] for point in target_valid])
    target_y = _bounds([point[1] for point in target_valid])
    target_z = sum(point[2] for point in target_valid) / len(target_valid)

    return tuple(
        (
            _scale(x, source_x, target_x),
            _scale(y, source_y, target_y),
            target_z,
        )
        for x, y in zip(projected_x, projected_y)
    )


def replace_upper_panel(
    current: Sequence[Sequence[float]],
    scan: Sequence[Sequence[float]],
) -> tuple[tuple[Coordinate, ...], UpperRewireReport]:
    mapping = tuple(_coordinate(point) for point in current)
    replacement = tuple(_coordinate(point) for point in scan)
    if len(mapping) != TOTAL_POINTS:
        raise ValueError(f"Expected {TOTAL_POINTS} current mapping points")
    indexed_scan = restore_scan_indices(replacement)
    inserted = len(MISSING_HARDWARE_INDICES) if len(replacement) == 268 else 0
    discarded = 0
    completed_scan = estimate_missing_points(indexed_scan)
    aligned = align_scan_to_upper_panel(completed_scan, mapping[UPPER_START:UPPER_END])
    padding = ((0.0, 0.0, 0.0),) * (UPPER_RESERVED - len(aligned))
    combined = mapping[:UPPER_START] + aligned + padding + mapping[UPPER_END:]

    if len(combined) != TOTAL_POINTS:
        raise RuntimeError("Upper replacement changed the total mapping length")
    if combined[:UPPER_START] != mapping[:UPPER_START]:
        raise RuntimeError("Middle panel changed unexpectedly")
    if combined[UPPER_END:] != mapping[UPPER_END:]:
        raise RuntimeError("Lower or rear panels changed unexpectedly")

    report = UpperRewireReport(
        source_points=len(replacement),
        source_missing=sum(_missing(point) for point in replacement),
        inserted_points=inserted,
        discarded_points=discarded,
        appended_points=0,
        estimated_points=sum(_missing(point) for point in indexed_scan),
        reserved_points=UPPER_RESERVED,
        padding_points=len(padding),
        upper_start=UPPER_START,
        upper_end=UPPER_END,
        hardware_trailing_black=HARDWARE_UPPER_CAPACITY - len(aligned),
    )
    return combined, report
