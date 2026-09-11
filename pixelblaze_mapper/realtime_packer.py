"""Compiled real-time RGB packer for TouchDesigner's Art-Net path.

The validated :mod:`multi_controller` packer remains the reference
implementation.  This module compiles its immutable routing plan once and then
reads the three source channels directly.  It deliberately returns exact
510-byte payloads and preserves the reference implementation's rounding,
brightness and colour-order semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Sequence

from .multi_controller import (
    MultiControllerValidationError,
    RouterPlan,
    SLOTS_PER_UNIVERSE,
)


@dataclass(frozen=True)
class PixelWrite:
    """One pre-resolved source pixel write into a controller payload."""

    source_index: int
    frame_index: int
    slot: int
    component_indices: tuple[int, int, int]


@dataclass(frozen=True)
class CompiledControllerPacker:
    """Controller-specific writes with no routing work in the frame loop."""

    name: str
    frame_count: int
    source_pixel_count: int
    brightness: float
    writes: tuple[PixelWrite, ...]

    def pack_channels(
        self,
        red: Sequence[Real],
        green: Sequence[Real],
        blue: Sequence[Real],
    ) -> tuple[bytes, ...]:
        """Pack normalized RGB channels into immutable 510-byte frames."""

        if min(len(red), len(green), len(blue)) < self.source_pixel_count:
            raise MultiControllerValidationError(
                f"Expected at least {self.source_pixel_count} samples per RGB channel"
            )
        channels = (red, green, blue)
        frames = [bytearray(SLOTS_PER_UNIVERSE) for _ in range(self.frame_count)]
        scale = 255.0 * self.brightness
        for write in self.writes:
            frame = frames[write.frame_index]
            source = write.source_index
            slot = write.slot
            first, second, third = write.component_indices
            frame[slot] = _normalized_byte(channels[first][source], scale)
            frame[slot + 1] = _normalized_byte(channels[second][source], scale)
            frame[slot + 2] = _normalized_byte(channels[third][source], scale)
        return tuple(bytes(frame) for frame in frames)


@dataclass(frozen=True)
class CompiledRouterPacker:
    """All controller packers derived from one validated router plan."""

    controllers: tuple[CompiledControllerPacker, ...]

    def controller(self, name: str) -> CompiledControllerPacker:
        for controller in self.controllers:
            if controller.name == name:
                return controller
        raise KeyError(name)

    def pack_channels(
        self,
        red: Sequence[Real],
        green: Sequence[Real],
        blue: Sequence[Real],
    ) -> dict[str, tuple[bytes, ...]]:
        return {
            controller.name: controller.pack_channels(red, green, blue)
            for controller in self.controllers
        }


def compile_router_packer(plan: RouterPlan) -> CompiledRouterPacker:
    """Resolve segments, reversing and colour order outside the frame loop."""

    compiled: list[CompiledControllerPacker] = []
    component_index = {"R": 0, "G": 1, "B": 2}
    for controller_plan in plan.controllers:
        controller = controller_plan.config
        writes: list[PixelWrite] = []
        for segment in plan.config.segments:
            if segment.controller != controller.name:
                continue
            order = segment.color_override or controller.color_order
            indices = tuple(component_index[channel] for channel in order)
            if segment.reverse:
                sources = range(
                    segment.source_start + segment.count - 1,
                    segment.source_start - 1,
                    -1,
                )
            else:
                sources = range(segment.source_start, segment.source_start + segment.count)
            for offset, source_index in enumerate(sources):
                destination = segment.destination_start + offset
                linear_slot = destination * 3
                writes.append(
                    PixelWrite(
                        source_index=source_index,
                        frame_index=linear_slot // SLOTS_PER_UNIVERSE,
                        slot=linear_slot % SLOTS_PER_UNIVERSE,
                        component_indices=indices,
                    )
                )
        compiled.append(
            CompiledControllerPacker(
                name=controller.name,
                frame_count=controller_plan.universe_count,
                source_pixel_count=plan.config.source_pixel_count,
                brightness=float(controller.brightness),
                writes=tuple(writes),
            )
        )
    return CompiledRouterPacker(tuple(compiled))


def _normalized_byte(value: Real, scale: float) -> int:
    # TD channel snapshots normally contain builtin floats. Avoid Real's ABC
    # lookup for those and exact ints, but retain the original fallback for
    # NumPy scalars, numeric subclasses, Fraction, and bool (historically Real).
    value_type = type(value)
    if value_type is not float and value_type is not int and not isinstance(value, Real):
        raise MultiControllerValidationError("Source channel contains a non-numeric value")
    # round(float) already returns a builtin int, including ties-to-even.
    # Avoid three builtin calls per channel while preserving conversion and
    # nonfinite exceptions before clipping (do not clamp the float first).
    rounded = round(float(value) * scale)
    return 0 if rounded < 0 else 255 if rounded > 255 else rounded
