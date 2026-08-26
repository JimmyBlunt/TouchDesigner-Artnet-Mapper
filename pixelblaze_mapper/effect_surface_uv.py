"""Coordinate contracts for sampling one 2D effect on the installation.

The rear wall and side wall use different physical planes.  This module keeps
their projection explicit so a vertical animation remains vertical on both.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from pixelblaze_mapper.installation_contract import LOWER, PANELS, REAR, UPPER, panel_for_index


BACK_START = REAR.start
UPPER_SIDE_START = UPPER.start
UPPER_SIDE_END = UPPER.stop
LOWER_SIDE_START = LOWER.start
BACK_X_MIN = 0.015625
BACK_X_MAX = 0.984375
BACK_Z_MIN = 0.315625
BACK_Z_MAX = 0.684375
PANEL_IDS = {panel.name: index for index, panel in enumerate(PANELS)}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def side_wall_uv(source_x: float, source_y: float) -> tuple[float, float]:
    """Project the rotated side scan to horizontal/vertical texture UV.

    The side preview geometry is rotated -90 degrees around Z.  Consequently,
    original Y is the visible front/back axis and original X is visible height.
    Original Z is wall-normal relief and must never drive the 2D animation.
    """

    # TouchDesigner texture V increases downwards in the installation preview.
    # The physical side wall uses original X as height, but with the opposite
    # sign: high scanner X is physically at the top.  Rotate the scan into the
    # wall plane and invert that height once so every side panel follows the
    # preview from top to bottom.
    return clamp01(source_y), clamp01(1.0 - float(source_x))


def side_panel_uv(index: int, source_x: float, source_y: float) -> tuple[float, float]:
    """Project every side LED onto one consistent downward-running wall UV.

    All three side panels occupy the same physical wall plane.  Their wiring
    and Art-Net ranges differ, but their effect coordinates must not.  Using
    one projection here keeps animation direction continuous across middle,
    upper and lower without changing any physical LED index or universe.
    """

    return side_wall_uv(source_x, source_y)


def rear_wall_uv(room_x: float, room_z: float) -> tuple[float, float]:
    """Project the 2x5 rear wall to horizontal/vertical texture coordinates."""

    u = (float(room_z) - BACK_Z_MIN) / (BACK_Z_MAX - BACK_Z_MIN)
    v = (float(room_x) - BACK_X_MIN) / (BACK_X_MAX - BACK_X_MIN)
    return clamp01(u), clamp01(v)


@dataclass(frozen=True)
class EffectCoordinate:
    index: int
    panel_id: int
    panel: str
    global_uv: tuple[float, float]
    local_uv: tuple[float, float]


def _axis_local(value: float, minimum: float, maximum: float) -> float:
    span = maximum - minimum
    if span <= 1.0e-12:
        return 0.5
    return clamp01((float(value) - minimum) / span)


def build_effect_coordinates(
    global_uv_by_index: Mapping[int, tuple[float, float]] | Iterable[tuple[int, float, float]],
) -> tuple[EffectCoordinate, ...]:
    """Normalize measured global UVs independently inside four real panels.

    The caller supplies the already reviewed global installation projection.
    Local coordinates are derived from each panel's actual extrema; no fixed
    row length, 2x5 tile count, or equal-size panel assumption is involved.
    """

    if isinstance(global_uv_by_index, Mapping):
        source = {
            int(index): (clamp01(uv[0]), clamp01(uv[1]))
            for index, uv in global_uv_by_index.items()
        }
    else:
        source = {
            int(index): (clamp01(u), clamp01(v))
            for index, u, v in global_uv_by_index
        }
    expected = set(range(REAR.stop))
    if set(source) != expected:
        missing = sorted(expected - set(source))
        extra = sorted(set(source) - expected)
        raise ValueError(
            "Global UV input must cover exactly indices 0..3743 "
            f"(missing={missing[:5]}, extra={extra[:5]})"
        )

    bounds: dict[str, tuple[float, float, float, float]] = {}
    for panel in PANELS:
        values = [source[index] for index in range(panel.start, panel.stop)]
        us = [uv[0] for uv in values]
        vs = [uv[1] for uv in values]
        bounds[panel.name] = (min(us), max(us), min(vs), max(vs))

    result = []
    for index in range(REAR.stop):
        panel = panel_for_index(index)
        u, v = source[index]
        u_min, u_max, v_min, v_max = bounds[panel.name]
        result.append(
            EffectCoordinate(
                index=index,
                panel_id=PANEL_IDS[panel.name],
                panel=panel.name,
                global_uv=(u, v),
                local_uv=(
                    _axis_local(u, u_min, u_max),
                    _axis_local(v, v_min, v_max),
                ),
            )
        )
    return tuple(result)


@dataclass(frozen=True)
class SurfaceUVContract:
    # The spatial lookup is derived once from the Pixelblaze XYZ scan.  Every
    # physical wire index then samples the effect at its own stored UV point.
    side_source: str = "/project1/pixelblaze_mapper/side_spatial_lookup"
    coordinate_source: str = "/project1/null4"
    callback_dat: str = "/project1/effect_sample_uv_callbacks"
    output_chop: str = "/project1/effect_sample_uv"
    sampler_chop: str = "/project1/topto1"


CONTRACT = SurfaceUVContract()
