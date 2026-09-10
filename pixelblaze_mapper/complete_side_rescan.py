"""Rebuild all three side panels from the complete 2026-08-24 Pixelblaze scan."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from statistics import median
from typing import Sequence

from pixelblaze_mapper.installation_contract import LOWER, MIDDLE, REAR, TOTAL_PIXELS, UPPER

from pixelblaze_mapper.lower_side_rewire import (
    Coordinate,
    _coordinate,
    _missing,
    estimate_missing_points,
)


OLD_TOTAL_POINTS = 3740
OLD_REAR_START = 1180
REAR_COUNT = 2560

MIDDLE_START = MIDDLE.start
MIDDLE_COUNT = MIDDLE.count
UPPER_START = UPPER.start
UPPER_COUNT = UPPER.count
LOWER_START = LOWER.start
LOWER_COUNT = LOWER.count
NEW_REAR_START = REAR.start
NEW_TOTAL_POINTS = TOTAL_PIXELS
RAW_EXPORTED_POINTS = 1183


@dataclass(frozen=True)
class PanelSpec:
    name: str
    source_start: int
    count: int
    old_start: int
    old_end: int


PANEL_SPECS = (
    PanelSpec("middle", MIDDLE_START, MIDDLE_COUNT, 0, 509),
    PanelSpec("upper", UPPER_START, UPPER_COUNT, 509, 781),
    PanelSpec("lower", LOWER_START, LOWER_COUNT, 781, OLD_REAR_START),
)


@dataclass(frozen=True)
class CompleteRescanReport:
    raw_source_points: int
    appended_points: int
    source_missing_points: int
    rejected_outlier_indices: tuple[int, ...]
    estimated_points: int
    middle_range: str
    upper_range: str
    lower_range: str
    rear_range: str
    output_points: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _bounds(values: Sequence[float]) -> tuple[float, float]:
    low, high = min(values), max(values)
    if math.isclose(low, high, abs_tol=1e-12):
        raise ValueError("Cannot align a zero-size coordinate range")
    return low, high


def _scale(value: float, source: tuple[float, float], target: tuple[float, float]) -> float:
    return target[0] + (value - source[0]) * (target[1] - target[0]) / (source[1] - source[0])


def _distance(left: Coordinate, right: Coordinate) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def reject_gross_spatial_outliers(points: Sequence[Coordinate]) -> tuple[tuple[Coordinate, ...], tuple[int, ...]]:
    """Replace only isolated scan failures, never ordinary surface variation."""

    values = tuple(_coordinate(point) for point in points)
    valid = tuple((index, point) for index, point in enumerate(values) if not _missing(point))
    if len(valid) < 3:
        raise ValueError("At least three measured panel points are required")
    neighbourhood = []
    for position, (_, point) in enumerate(valid):
        distances = sorted(
            _distance(point, other)
            for other_position, (_, other) in enumerate(valid)
            if other_position != position
        )
        neighbourhood.append(sum(distances[:4]) / min(4, len(distances)))
    threshold = median(neighbourhood) * 5.0
    rejected = tuple(
        valid[index][0]
        for index, distance in enumerate(neighbourhood)
        if distance > threshold
    )
    result = list(values)
    for index in rejected:
        result[index] = (0.0, 0.0, 0.0)
    return tuple(result), rejected


def complete_side_measurements(
    raw_scan: Sequence[Sequence[float]],
) -> tuple[tuple[Coordinate, ...], frozenset[int]]:
    """Return the repaired scanner-space coordinates for all three side panels.

    Measured XYZ values are preserved byte-for-byte after float conversion.  Only
    missing scan entries and isolated gross failures are estimated from their
    measured neighbours.  These scanner-space coordinates are the authoritative
    source for physical row/column calibration; the cabinet-aligned coordinates
    are deliberately not used for that purpose.
    """

    source = tuple(_coordinate(point) for point in raw_scan)
    if len(source) not in (RAW_EXPORTED_POINTS, NEW_REAR_START):
        raise ValueError(
            f"Expected {RAW_EXPORTED_POINTS} exported or {NEW_REAR_START} indexed side points"
        )
    indexed = source + ((0.0, 0.0, 0.0),) * (NEW_REAR_START - len(source))
    completed_side: list[Coordinate] = []
    estimated_indices: set[int] = set()
    for spec in PANEL_SPECS:
        panel = indexed[spec.source_start:spec.source_start + spec.count]
        cleaned, rejected = reject_gross_spatial_outliers(panel)
        estimated_indices.update(
            spec.source_start + offset
            for offset, point in enumerate(cleaned)
            if _missing(point)
        )
        estimated_indices.update(spec.source_start + offset for offset in rejected)
        completed_side.extend(estimate_missing_points(cleaned))
    if len(completed_side) != NEW_REAR_START:
        raise RuntimeError("Repaired side scan has an unexpected point count")
    return tuple(completed_side), frozenset(estimated_indices)


def align_panel_3d(scan: Sequence[Coordinate], target: Sequence[Coordinate]) -> tuple[Coordinate, ...]:
    """Fit scanner X/Y into the existing panel box and retain measured depth."""

    source = tuple(point for point in scan if not _missing(point))
    destination = tuple(point for point in target if not _missing(point))
    if len(source) != len(scan):
        raise ValueError("Panel gaps must be estimated before alignment")
    if not destination:
        raise ValueError("Existing panel has no usable alignment coordinates")

    sx = _bounds(tuple(point[0] for point in source))
    sy = _bounds(tuple(point[1] for point in source))
    tx = _bounds(tuple(point[0] for point in destination))
    ty = _bounds(tuple(point[1] for point in destination))
    source_z = tuple(point[2] for point in source)
    target_z = sum(point[2] for point in destination) / len(destination)
    depth_scale = min((tx[1] - tx[0]) / (sx[1] - sx[0]), (ty[1] - ty[0]) / (sy[1] - sy[0]))
    depth_center = median(source_z)

    return tuple(
        (
            _scale(point[0], sx, tx),
            _scale(point[1], sy, ty),
            target_z + (point[2] - depth_center) * depth_scale,
        )
        for point in source
    )


def rebuild_complete_side_mapping(
    current: Sequence[Sequence[float]],
    raw_scan: Sequence[Sequence[float]],
) -> tuple[tuple[Coordinate, ...], CompleteRescanReport]:
    current_points = tuple(_coordinate(point) for point in current)
    source = tuple(_coordinate(point) for point in raw_scan)
    if len(current_points) != OLD_TOTAL_POINTS:
        raise ValueError(f"Expected the previous {OLD_TOTAL_POINTS}-point mapping")
    if len(source) not in (RAW_EXPORTED_POINTS, NEW_REAR_START):
        raise ValueError(f"Expected {RAW_EXPORTED_POINTS} exported or {NEW_REAR_START} indexed side points")

    appended = NEW_REAR_START - len(source)
    indexed = source + ((0.0, 0.0, 0.0),) * appended
    source_missing = sum(_missing(point) for point in indexed)
    aligned_panels = []
    outlier_globals: list[int] = []
    estimated = 0
    for spec in PANEL_SPECS:
        panel = indexed[spec.source_start:spec.source_start + spec.count]
        cleaned, rejected = reject_gross_spatial_outliers(panel)
        outlier_globals.extend(spec.source_start + index for index in rejected)
        estimated += sum(_missing(point) for point in cleaned)
        completed = estimate_missing_points(cleaned)
        aligned_panels.extend(align_panel_3d(completed, current_points[spec.old_start:spec.old_end]))

    rear = current_points[OLD_REAR_START:]
    if len(rear) != REAR_COUNT:
        raise RuntimeError("Existing rear wall is not the expected 2,560 points")
    combined = tuple(aligned_panels) + rear
    if len(combined) != NEW_TOTAL_POINTS:
        raise RuntimeError("Complete rescan produced an unexpected mapping length")
    if combined[NEW_REAR_START:] != rear:
        raise RuntimeError("Rear-wall coordinates changed unexpectedly")

    report = CompleteRescanReport(
        raw_source_points=len(source),
        appended_points=appended,
        source_missing_points=source_missing,
        rejected_outlier_indices=tuple(outlier_globals),
        estimated_points=estimated,
        middle_range="0..516",
        upper_range="517..785",
        lower_range="786..1183",
        rear_range="1184..3743",
        output_points=len(combined),
    )
    return combined, report
