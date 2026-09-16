"""Coordinate-driven calibration patterns for the Art-Net router.

Every color is assigned to a physical LED index through the measured
Pixelblaze XYZ map.  No rectangular panel size or row length is guessed.
"""

from __future__ import annotations

import json
from math import floor, isfinite
from pathlib import Path
from typing import Sequence

from pixelblaze_mapper.complete_side_rescan import (
    NEW_TOTAL_POINTS,
    complete_side_measurements,
)
from pixelblaze_mapper.spatial_map import build_side_spatial_map


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPING = ROOT / "mappings" / "mapping_complete_new_0_1183_full_2026-08-24.json"
DEFAULT_RAW_MAPPING = ROOT / "mappings" / "sources" / "complete_new_0_1183_raw_2026-08-24.json"
PANELS = ("all", "middle", "upper", "lower")
PATTERNS = ("panel_id", "rows", "columns", "chase")
STRIPE_PALETTE = (
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 1.0),
    (0.0, 0.0, 1.0),
)
PANEL_PALETTE = {
    "middle": (1.0, 0.0, 0.0),
    "upper": (0.0, 1.0, 0.0),
    "lower": (0.0, 0.0, 1.0),
}


def load_coordinates(path: str | Path = DEFAULT_MAPPING) -> tuple[tuple[float, float, float], ...]:
    coordinates = json.loads(Path(path).read_text(encoding="utf-8"))
    if len(coordinates) != NEW_TOTAL_POINTS:
        raise ValueError(f"Expected {NEW_TOTAL_POINTS} mapped coordinates")
    return tuple(tuple(float(value) for value in point[:3]) for point in coordinates)


def load_measurement_coordinates(
    path: str | Path = DEFAULT_RAW_MAPPING,
) -> tuple[tuple[float, float, float], ...]:
    """Load and minimally repair the authoritative Pixelblaze scanner map."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    coordinates, _ = complete_side_measurements(raw)
    return coordinates


def calibration_source(
    coordinates: Sequence[Sequence[float]] | None,
    *,
    active_uv=None,
    source_count: int | None = None,
    measurement_coordinates: Sequence[Sequence[float]] | None = None,
    panel: str = "all",
    pattern: str = "panel_id",
    chase_index: int = 0,
) -> tuple[tuple[float, float, float], ...]:
    """Return a complete source buffer using only measured spatial lookup data."""

    if source_count is not None:
        if active_uv is None:
            raise ValueError("Active calibration requires the current material UV table")
        from .routing_transaction import table_rows
        return active_calibration_source(table_rows(active_uv), source_count=source_count,
                                         panel=panel, pattern=pattern, chase_index=chase_index)
    panel = panel.strip().lower()
    pattern = pattern.strip().lower()
    if panel not in PANELS:
        raise ValueError("Panel must be all, middle, upper or lower")
    if pattern not in PATTERNS:
        raise ValueError("Pattern must be panel_id, rows, columns or chase")
    if not 0 <= int(chase_index) < NEW_TOTAL_POINTS:
        raise ValueError(f"Chase index must be 0..{NEW_TOTAL_POINTS - 1}")

    source = [(0.0, 0.0, 0.0)] * NEW_TOTAL_POINTS
    selected = tuple(
        item for item in build_side_spatial_map(
            coordinates,
            measurement_coordinates=measurement_coordinates,
        )
        if panel == "all" or item.name == panel
    )
    for mapped_panel in selected:
        for led in mapped_panel.leds:
            if pattern == "panel_id":
                color = PANEL_PALETTE[mapped_panel.name]
            elif pattern == "rows":
                color = STRIPE_PALETTE[led.row % len(STRIPE_PALETTE)]
            elif pattern == "columns":
                color = STRIPE_PALETTE[led.column % len(STRIPE_PALETTE)]
            else:
                distance = abs(led.index - int(chase_index))
                color = (
                    (0.0, 1.0, 0.0) if distance == 0 else
                    (1.0, 1.0, 1.0) if distance <= 3 else
                    (0.0, 0.0, 0.0)
                )
            source[led.index] = color
    return tuple(source)


def active_calibration_source(rows, *, source_count, panel="all", pattern="panel_id", chase_index=0):
    """Create an address-preserving diagnostic buffer from the current layout.

    Rows/columns are 24 horizontal/vertical UV stripes, not a claimed physical
    LED lattice. Output availability is applied by the sender's authoritative
    source mask after this pure pattern generation. No mapping files are read.
    """
    from .show_renderer import source_groups_from_panels
    if type(source_count) is not int or source_count <= 0:
        raise ValueError("Active calibration needs a positive source count")
    panel, pattern = panel.strip().lower(), pattern.strip().lower()
    if panel not in (*PANELS, "rear") or pattern not in PATTERNS:
        raise ValueError("Unknown calibration panel or pattern")
    if type(chase_index) is not int or not 0 <= chase_index < source_count:
        raise ValueError(f"Chase index must be 0..{source_count - 1}")
    if not rows or len(rows) != source_count + 1:
        raise ValueError("Active calibration UV rows must match source count")
    header = rows[0]
    if len(set(header)) != len(header) or not {"index", "panel", "local_u", "local_v"} <= set(header):
        raise ValueError("Active calibration UV schema is incomplete or ambiguous")
    index_col, panel_col, u_col, v_col = (header.index(k) for k in ("index", "panel", "local_u", "local_v"))
    labels, uv = [], []
    for index, row in enumerate(rows[1:]):
        if len(row) != len(header) or str(row[index_col]) != str(index):
            raise ValueError("Active calibration source indices must remain ordered")
        pair = tuple(float(row[column]) for column in (u_col, v_col))
        if any(not isfinite(value) or not 0 <= value <= 1 for value in pair):
            raise ValueError("Active calibration UV values must be finite and inside 0..1")
        labels.append(str(row[panel_col])); uv.append(pair)
    groups = source_groups_from_panels(tuple(labels))
    palette = dict(PANEL_PALETTE, rear=(1.0, .45, 0.0))
    result = []
    for index, (group, pair) in enumerate(zip(groups, uv)):
        if labels[index] == "__inactive__" or (panel != "all" and group != panel):
            color = (0., 0., 0.)
        elif pattern == "panel_id":
            color = palette.get(group, (1., 1., 1.))
        elif pattern in ("rows", "columns"):
            position = pair[1 if pattern == "rows" else 0]
            color = STRIPE_PALETTE[min(23, floor(position * 24)) % len(STRIPE_PALETTE)]
        else:
            distance = abs(index - chase_index)
            color = (0., 1., 0.) if distance == 0 else (1., 1., 1.) if distance <= 3 else (0., 0., 0.)
        result.append(color)
    return tuple(result)
