"""Coordinate-driven calibration patterns for the Art-Net router.

Every color is assigned to a physical LED index through the measured
Pixelblaze XYZ map.  No rectangular panel size or row length is guessed.
"""

from __future__ import annotations

import json
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
    coordinates: Sequence[Sequence[float]],
    *,
    measurement_coordinates: Sequence[Sequence[float]] | None = None,
    panel: str = "all",
    pattern: str = "panel_id",
    chase_index: int = 0,
) -> tuple[tuple[float, float, float], ...]:
    """Return a complete source buffer using only measured spatial lookup data."""

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
