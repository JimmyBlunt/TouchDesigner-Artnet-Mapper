"""Measured LED-index lookup for the three irregular side panels.

FastLED-style XY maps normally translate a logical grid cell to a physical
wire index.  TouchDesigner renders in the opposite direction: for every fixed
Art-Net/wire index it needs the measured position at which to sample a texture.
This module stores both representations without changing the wire order.

The continuous XYZ/UV values are copied from the Pixelblaze scan.  Logical
rows and columns are derived from the measured nearest-neighbour lattice; no
panel row/column counts are hard-coded.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from statistics import median
from typing import Sequence

from pixelblaze_mapper.complete_side_rescan import NEW_TOTAL_POINTS, PANEL_SPECS
from pixelblaze_mapper.effect_surface_uv import side_panel_uv


@dataclass(frozen=True)
class LatticeBasis:
    horizontal: tuple[float, float]
    vertical: tuple[float, float]
    column_phase: float
    row_phase: float


@dataclass(frozen=True)
class SpatialLED:
    index: int
    panel: str
    x: float
    y: float
    z: float
    u: float
    v: float
    column: int
    row: int
    coordinate_quality: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PanelSpatialMap:
    name: str
    source_start: int
    count: int
    width: int
    height: int
    basis: LatticeBasis
    leds: tuple[SpatialLED, ...]

    def to_dict(self) -> dict[str, object]:
        cells: dict[str, list[int]] = {}
        for led in self.leds:
            cells.setdefault(f"{led.column},{led.row}", []).append(led.index)
        return {
            "name": self.name,
            "source_start": self.source_start,
            "count": self.count,
            "width": self.width,
            "height": self.height,
            "basis": asdict(self.basis),
            # A list is intentional: it preserves every measured LED even if
            # two noisy scan points quantize to the same diagnostic cell.
            "xy_to_indices": cells,
            "leds": [led.to_dict() for led in self.leds],
        }


def _nearest_axis_vectors(
    points: Sequence[tuple[float, float]],
    *,
    horizontal: bool,
) -> tuple[tuple[float, float], ...]:
    vectors: list[tuple[float, float]] = []
    for index, (u, v) in enumerate(points):
        candidates: list[tuple[float, float, float]] = []
        for other_index, (other_u, other_v) in enumerate(points):
            if other_index == index:
                continue
            du, dv = other_u - u, other_v - v
            main = du if horizontal else dv
            cross = dv if horizontal else du
            if abs(main) > 2.0 * abs(cross):
                candidates.append((math.hypot(du, dv), du, dv))
        if not candidates:
            continue
        _, du, dv = min(candidates)
        if (horizontal and du < 0.0) or (not horizontal and dv < 0.0):
            du, dv = -du, -dv
        vectors.append((du, dv))
    if not vectors:
        raise ValueError("The measured coordinates do not contain a usable LED lattice")
    return tuple(vectors)


def _basis(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    horizontal = _nearest_axis_vectors(points, horizontal=True)
    vertical = _nearest_axis_vectors(points, horizontal=False)
    return (
        (median(vector[0] for vector in horizontal), median(vector[1] for vector in horizontal)),
        (median(vector[0] for vector in vertical), median(vector[1] for vector in vertical)),
    )


def _logical_coordinates(
    points: Sequence[tuple[float, float]],
    horizontal: tuple[float, float],
    vertical: tuple[float, float],
) -> tuple[list[float], list[float]]:
    determinant = horizontal[0] * vertical[1] - vertical[0] * horizontal[1]
    if math.isclose(determinant, 0.0, abs_tol=1e-12):
        raise ValueError("Measured horizontal and vertical LED axes are parallel")
    columns, rows = [], []
    for u, v in points:
        columns.append((vertical[1] * u - vertical[0] * v) / determinant)
        rows.append((-horizontal[1] * u + horizontal[0] * v) / determinant)
    return columns, rows


def _quantize(values: Sequence[float]) -> tuple[tuple[int, ...], float]:
    """Snap measured lattice coordinates to integer cells with a fitted phase."""

    best_error, best_phase = math.inf, 0.0
    for step in range(400):
        phase = step / 400.0
        error = sum((value - phase - round(value - phase)) ** 2 for value in values)
        if error < best_error:
            best_error, best_phase = error, phase
    cells = [round(value - best_phase) for value in values]
    offset = min(cells)
    return tuple(cell - offset for cell in cells), best_phase


def build_side_spatial_map(
    coordinates: Sequence[Sequence[float]],
    *,
    measurement_coordinates: Sequence[Sequence[float]] | None = None,
    estimated_indices: set[int] | frozenset[int] = frozenset(),
) -> tuple[PanelSpatialMap, ...]:
    if len(coordinates) != NEW_TOTAL_POINTS:
        raise ValueError(f"Expected the complete {NEW_TOTAL_POINTS}-point mapping")
    if measurement_coordinates is not None and len(measurement_coordinates) != PANEL_SPECS[-1].source_start + PANEL_SPECS[-1].count:
        raise ValueError("Expected 1,184 repaired scanner-space side coordinates")

    result: list[PanelSpatialMap] = []
    for spec in PANEL_SPECS:
        xyz = coordinates[spec.source_start:spec.source_start + spec.count]
        projected = tuple(
            side_panel_uv(spec.source_start + offset, float(point[0]), float(point[1]))
            for offset, point in enumerate(xyz)
        )
        # The globally aligned cabinet map is ideal for preview/effect sampling,
        # but its per-panel scaling and orientation must never define physical
        # calibration cells.  Pixelblaze scanner X/Y is the measured panel plane
        # for every panel (including the lower panel, whose wire begins vertically).
        lattice_points = (
            tuple(
                (float(point[0]), float(point[1]))
                for point in measurement_coordinates[
                    spec.source_start:spec.source_start + spec.count
                ]
            )
            if measurement_coordinates is not None
            else projected
        )
        horizontal, vertical = _basis(lattice_points)
        continuous_columns, continuous_rows = _logical_coordinates(
            lattice_points, horizontal, vertical
        )
        columns, column_phase = _quantize(continuous_columns)
        rows, row_phase = _quantize(continuous_rows)
        leds = tuple(
            SpatialLED(
                index=spec.source_start + offset,
                panel=spec.name,
                x=float(point[0]),
                y=float(point[1]),
                z=float(point[2]),
                u=projected[offset][0],
                v=projected[offset][1],
                column=columns[offset],
                row=rows[offset],
                coordinate_quality=(
                    "estimated" if spec.source_start + offset in estimated_indices else "measured"
                ),
            )
            for offset, point in enumerate(xyz)
        )
        result.append(
            PanelSpatialMap(
                name=spec.name,
                source_start=spec.source_start,
                count=spec.count,
                width=max(columns) + 1,
                height=max(rows) + 1,
                basis=LatticeBasis(horizontal, vertical, column_phase, row_phase),
                leds=leds,
            )
        )
    return tuple(result)


def spatial_map_document(
    coordinates: Sequence[Sequence[float]],
    source: str,
    *,
    measurement_coordinates: Sequence[Sequence[float]] | None = None,
    estimated_indices: set[int] | frozenset[int] = frozenset(),
) -> dict[str, object]:
    panels = build_side_spatial_map(
        coordinates,
        measurement_coordinates=measurement_coordinates,
        estimated_indices=estimated_indices,
    )
    measured_count = sum(
        led.coordinate_quality == "measured" for panel in panels for led in panel.leds
    )
    estimated_count = sum(panel.count for panel in panels) - measured_count
    return {
        "schema": "touchdesigner-artnet-spatial-map/v1",
        "source": source,
        "coordinate_space": "cabinet-side-global-uv+scanner-space-physical-lattice",
        "wire_order_changed": False,
        "coordinate_quality": {
            "measured": measured_count,
            "estimated": estimated_count,
            "estimated_indices": sorted(estimated_indices),
        },
        "panels": [panel.to_dict() for panel in panels],
    }
