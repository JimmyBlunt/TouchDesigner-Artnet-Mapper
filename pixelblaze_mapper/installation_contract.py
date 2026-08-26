"""Canonical LED installation contract shared by mapper, preview and output.

This module is deliberately pure Python: importing it never talks to
TouchDesigner, the network or the hardware.  UI builders and adapters may
derive their labels, guards and slices from these values instead of keeping
independent 3,714/3,740/3,744 constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from numbers import Real
from typing import Iterable, Sequence


TOTAL_PIXELS = 3744
CHANNELS_PER_UNIVERSE = 510
CHANNELS_PER_PIXEL = 3
PIXELS_PER_UNIVERSE = CHANNELS_PER_UNIVERSE // CHANNELS_PER_PIXEL
UNIVERSES_PER_SIDE_PORT = 4
PIXELS_PER_SIDE_PORT = PIXELS_PER_UNIVERSE * UNIVERSES_PER_SIDE_PORT

# Missing coordinates may be preserved in an un-applied draft so index order
# is inspectable.  They are shown as black.  A live map must not contain any
# missing coordinate: silently collapsing an index would shift every later LED.
MISSING_DRAFT_RENDER = "black"
MISSING_ACTIVE_POLICY = "reject"


@dataclass(frozen=True)
class PanelContract:
    name: str
    start: int
    count: int
    port: int | None = None
    first_ui_universe: int | None = None
    reserved_universes: int = 0

    @property
    def stop(self) -> int:
        """Exclusive end index, suitable for Python slicing."""

        return self.start + self.count

    @property
    def last(self) -> int:
        return self.stop - 1

    @property
    def active_universes(self) -> int:
        return ceil(self.count / PIXELS_PER_UNIVERSE)

    @property
    def reserved_pixels(self) -> int:
        return self.reserved_universes * PIXELS_PER_UNIVERSE

    @property
    def trailing_black_pixels(self) -> int:
        return self.reserved_pixels - self.count

    @property
    def ui_universes(self) -> tuple[int, ...]:
        if self.first_ui_universe is None:
            return ()
        return tuple(range(self.first_ui_universe, self.first_ui_universe + self.reserved_universes))

    @property
    def active_ui_universes(self) -> tuple[int, ...]:
        return self.ui_universes[: self.active_universes]

    @property
    def black_ui_universes(self) -> tuple[int, ...]:
        return self.ui_universes[self.active_universes :]


MIDDLE = PanelContract("middle", 0, 517, port=1, first_ui_universe=1, reserved_universes=4)
UPPER = PanelContract("upper", 517, 269, port=2, first_ui_universe=5, reserved_universes=4)
LOWER = PanelContract("lower", 786, 398, port=3, first_ui_universe=9, reserved_universes=4)
REAR = PanelContract("rear", 1184, 2560)

PANELS = (MIDDLE, UPPER, LOWER, REAR)
SIDE_PANELS = (MIDDLE, UPPER, LOWER)
PANEL_BY_NAME = {panel.name: panel for panel in PANELS}
SIDE_PIXEL_COUNT = REAR.start
REAR_PANEL_COUNT = 10
REAR_PANEL_PIXELS = 16 * 16

BLACK_UI_UNIVERSES = tuple(
    universe for panel in SIDE_PANELS for universe in panel.black_ui_universes
)
BLACK_WIRE_UNIVERSES = tuple(universe - 1 for universe in BLACK_UI_UNIVERSES)


@dataclass(frozen=True)
class MappingQuality:
    pixel_count: int
    missing_indices: tuple[int, ...]
    active: bool

    @property
    def valid(self) -> bool:
        return self.pixel_count == TOTAL_PIXELS and (not self.active or not self.missing_indices)


def panel_for_index(index: int) -> PanelContract:
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < TOTAL_PIXELS:
        raise IndexError(f"LED index must be 0..{TOTAL_PIXELS - 1}")
    return next(panel for panel in PANELS if panel.start <= index < panel.stop)


def validate_mapping(
    coordinates: Sequence[Sequence[Real]],
    missing_indices: Iterable[int] = (),
    *,
    active: bool,
) -> MappingQuality:
    """Validate count, numeric XYZ values and the explicit missing policy.

    Draft maps may retain declared missing positions so the wire indices remain
    stable; preview code must render those positions black.  Active maps reject
    them.  A coordinate of ``(0, 0, 0)`` is not automatically missing because
    it can be a legitimate normalized position; only ``missing_indices`` is
    authoritative.
    """

    if len(coordinates) != TOTAL_PIXELS:
        raise ValueError(f"Expected {TOTAL_PIXELS} coordinates, got {len(coordinates)}")

    missing = tuple(sorted(set(missing_indices)))
    if any(isinstance(index, bool) or not isinstance(index, int) for index in missing):
        raise ValueError("Missing indices must be integers")
    if any(index < 0 or index >= TOTAL_PIXELS for index in missing):
        raise ValueError(f"Missing indices must be inside 0..{TOTAL_PIXELS - 1}")

    for index, coordinate in enumerate(coordinates):
        if len(coordinate) not in (2, 3):
            raise ValueError(f"Coordinate {index} must contain two or three values")
        if any(isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)) for value in coordinate):
            raise ValueError(f"Coordinate {index} contains a non-finite numeric value")

    if active and missing:
        preview = ", ".join(str(index) for index in missing[:8])
        suffix = "..." if len(missing) > 8 else ""
        raise ValueError(f"Active mapping contains missing LED indices: {preview}{suffix}")
    return MappingQuality(TOTAL_PIXELS, missing, active)


def validate_contract() -> None:
    """Fail fast if a future edit introduces a gap or overlap."""

    expected_start = 0
    for panel in PANELS:
        if panel.start != expected_start:
            raise RuntimeError(f"Panel contract has a gap or overlap before {panel.name}")
        expected_start = panel.stop
    if expected_start != TOTAL_PIXELS:
        raise RuntimeError("Panel contract does not cover the complete installation")
    if REAR.count != REAR_PANEL_COUNT * REAR_PANEL_PIXELS:
        raise RuntimeError("Rear contract is not ten complete 16x16 panels")
    if BLACK_UI_UNIVERSES != (7, 8, 12):
        raise RuntimeError("Reserved black universe contract changed unexpectedly")


validate_contract()
