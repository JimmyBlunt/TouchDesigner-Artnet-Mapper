"""Pure-Python multi-controller Art-Net routing for the 3,740 pixel map.

The module deliberately has no TouchDesigner or networking dependency.  It
validates a draft topology and packs RGB source pixels into fixed 510-slot
ArtDMX frames.  A TouchDesigner adapter may consume the returned table rows,
but enabling a DMX Out CHOP is always an explicit, separate action.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address
from math import ceil
from numbers import Real
from typing import Iterable, Sequence


SOURCE_PIXEL_COUNT = 3744
SLOTS_PER_UNIVERSE = 510
PIXELS_PER_UNIVERSE = 170
ARTNET_MAX_LINEAR_UNIVERSE = 32767
COLOR_ORDERS = frozenset(("RGB", "RBG", "GRB", "GBR", "BRG", "BGR"))


class MultiControllerValidationError(ValueError):
    """Raised when a topology cannot be packed safely."""


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    field: str = ""

    @property
    def blocking(self) -> bool:
        return self.severity == "error"


@dataclass(frozen=True)
class ControllerConfig:
    name: str
    target_address: str
    local_interface: str
    enabled: bool = False
    port: int = 6454
    start_universe: int = 0
    color_order: str = "RGB"
    brightness: float = 0.02
    rate: int = 30
    art_sync: bool = False


@dataclass(frozen=True)
class SegmentConfig:
    name: str
    source_start: int
    count: int
    controller: str
    destination_start: int = 0
    reverse: bool = False
    color_override: str | None = None


@dataclass(frozen=True)
class RouterConfig:
    controllers: tuple[ControllerConfig, ...]
    segments: tuple[SegmentConfig, ...]
    source_pixel_count: int = SOURCE_PIXEL_COUNT
    warn_unassigned: bool = True


@dataclass(frozen=True)
class UniverseRoute:
    channel: str
    sequence: int
    linear_universe: int
    net: int
    subnet: int
    universe: int
    destination_pixel_start: int
    active_pixel_count: int


@dataclass(frozen=True)
class ControllerPlan:
    config: ControllerConfig
    destination_pixel_count: int
    routes: tuple[UniverseRoute, ...]

    @property
    def universe_count(self) -> int:
        return len(self.routes)

    def routing_rows(self, include_header: bool = True) -> tuple[tuple[object, ...], ...]:
        rows: list[tuple[object, ...]] = []
        if include_header:
            rows.append(("channel", "net", "subnet", "universe"))
        rows.extend((route.channel, route.net, route.subnet, route.universe) for route in self.routes)
        return tuple(rows)


@dataclass(frozen=True)
class RouterPlan:
    config: RouterConfig
    controllers: tuple[ControllerPlan, ...]
    issues: tuple[ValidationIssue, ...]

    def controller(self, name: str) -> ControllerPlan:
        for item in self.controllers:
            if item.config.name == name:
                return item
        raise KeyError(name)

    def pack_pixels(
        self,
        pixels: Sequence[Sequence[Real]],
        *,
        normalized: bool = True,
    ) -> dict[str, tuple[tuple[int, ...], ...]]:
        """Pack a complete RGB source into fixed 510-slot frames.

        With ``normalized=True`` (the TouchDesigner default), component values
        are interpreted as 0..1.  ``normalized=False`` accepts byte-like 0..255
        values.  Values are brightness-scaled, rounded, and clamped to bytes.
        """

        if len(pixels) != self.config.source_pixel_count:
            raise MultiControllerValidationError(
                f"Expected {self.config.source_pixel_count} source pixels, got {len(pixels)}"
            )
        for index, pixel in enumerate(pixels):
            if len(pixel) != 3:
                raise MultiControllerValidationError(
                    f"Source pixel {index} has {len(pixel)} components; expected RGB"
                )
            if any(not isinstance(value, Real) for value in pixel):
                raise MultiControllerValidationError(f"Source pixel {index} is not numeric")

        segments_by_controller: dict[str, list[SegmentConfig]] = {
            item.config.name: [] for item in self.controllers
        }
        for segment in self.config.segments:
            segments_by_controller[segment.controller].append(segment)

        packed: dict[str, tuple[tuple[int, ...], ...]] = {}
        for controller_plan in self.controllers:
            controller = controller_plan.config
            destination = [[0, 0, 0] for _ in range(controller_plan.destination_pixel_count)]
            for segment in segments_by_controller[controller.name]:
                order = segment.color_override or controller.color_order
                source_indices: Iterable[int]
                if segment.reverse:
                    source_indices = range(
                        segment.source_start + segment.count - 1,
                        segment.source_start - 1,
                        -1,
                    )
                else:
                    source_indices = range(segment.source_start, segment.source_start + segment.count)
                for offset, source_index in enumerate(source_indices):
                    logical = pixels[source_index]
                    by_name = {"R": logical[0], "G": logical[1], "B": logical[2]}
                    destination[segment.destination_start + offset] = [
                        _component_to_byte(by_name[channel], controller.brightness, normalized)
                        for channel in order
                    ]

            frames: list[tuple[int, ...]] = []
            for route in controller_plan.routes:
                frame = [0] * SLOTS_PER_UNIVERSE
                start = route.destination_pixel_start
                active = destination[start : start + route.active_pixel_count]
                flat = [component for pixel in active for component in pixel]
                frame[: len(flat)] = flat
                frames.append(tuple(frame))
            packed[controller.name] = tuple(frames)
        return packed


def _component_to_byte(value: Real, brightness: float, normalized: bool) -> int:
    scale = 255.0 if normalized else 1.0
    return max(0, min(255, int(round(float(value) * scale * brightness))))


def _valid_integer(value: object, minimum: int, maximum: int | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        return False
    return maximum is None or value <= maximum


def _valid_order(value: object) -> bool:
    return isinstance(value, str) and value in COLOR_ORDERS


def _valid_unicast_ipv4(value: object, *, local: bool = False) -> bool:
    try:
        if not isinstance(value, str):
            return False
        address = IPv4Address(value)
    except Exception:
        return False
    if address.is_multicast or address.is_unspecified and not local:
        return False
    return not address.is_reserved


def _interval_overlaps(left_start: int, left_count: int, right_start: int, right_count: int) -> bool:
    return max(left_start, right_start) < min(left_start + left_count, right_start + right_count)


def _range_text(indices: Sequence[int]) -> str:
    if not indices:
        return ""
    ranges: list[str] = []
    start = previous = indices[0]
    for item in indices[1:]:
        if item != previous + 1:
            ranges.append(str(start) if start == previous else f"{start}-{previous}")
            start = item
        previous = item
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def validate_router(config: RouterConfig) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if not _valid_integer(config.source_pixel_count, 1):
        issues.append(ValidationIssue("error", "source_pixel_count", "source_pixel_count must be a positive integer", "source_pixel_count"))
        source_count = 0
    else:
        source_count = config.source_pixel_count

    names: set[str] = set()
    valid_controllers: dict[str, ControllerConfig] = {}
    for index, controller in enumerate(config.controllers):
        field = f"controllers[{index}]"
        if not isinstance(controller.name, str) or not controller.name.strip():
            issues.append(ValidationIssue("error", "controller_name", "Controller name must not be empty", field + ".name"))
        elif controller.name in names:
            issues.append(ValidationIssue("error", "duplicate_controller", f"Duplicate controller name: {controller.name}", field + ".name"))
        else:
            names.add(controller.name)
            valid_controllers[controller.name] = controller
        if not isinstance(controller.enabled, bool):
            issues.append(ValidationIssue("error", "enabled", "enabled must be boolean", field + ".enabled"))
        if not _valid_unicast_ipv4(controller.target_address):
            issues.append(ValidationIssue("error", "target_address", "Target must be a valid unicast IPv4 address", field + ".target_address"))
        if not _valid_unicast_ipv4(controller.local_interface, local=True):
            issues.append(ValidationIssue("error", "local_interface", "Local interface must be a valid IPv4 address", field + ".local_interface"))
        if not _valid_integer(controller.port, 1, 65535):
            issues.append(ValidationIssue("error", "port", "Port must be 1..65535", field + ".port"))
        if not _valid_integer(controller.start_universe, 0, ARTNET_MAX_LINEAR_UNIVERSE):
            issues.append(ValidationIssue("error", "start_universe", f"Start universe must be 0..{ARTNET_MAX_LINEAR_UNIVERSE}", field + ".start_universe"))
        if not _valid_order(controller.color_order):
            issues.append(ValidationIssue("error", "color_order", "Color order must be an RGB permutation", field + ".color_order"))
        if isinstance(controller.brightness, bool) or not isinstance(controller.brightness, Real) or not 0 <= controller.brightness <= 1:
            issues.append(ValidationIssue("error", "brightness", "Brightness must be between 0 and 1", field + ".brightness"))
        if not _valid_integer(controller.rate, 1, 120):
            issues.append(ValidationIssue("error", "rate", "Rate must be 1..120 fps", field + ".rate"))
        if not isinstance(controller.art_sync, bool):
            issues.append(ValidationIssue("error", "art_sync", "art_sync must be boolean", field + ".art_sync"))

    valid_segments: list[SegmentConfig] = []
    segment_names: set[str] = set()
    for index, segment in enumerate(config.segments):
        field = f"segments[{index}]"
        if not isinstance(segment.name, str) or not segment.name.strip():
            issues.append(ValidationIssue("error", "segment_name", "Segment name must not be empty", field + ".name"))
        elif segment.name in segment_names:
            issues.append(ValidationIssue("error", "duplicate_segment", f"Duplicate segment name: {segment.name}", field + ".name"))
        else:
            segment_names.add(segment.name)
        valid_source_start = _valid_integer(segment.source_start, 0)
        valid_count = _valid_integer(segment.count, 1)
        valid_destination = _valid_integer(segment.destination_start, 0)
        if not valid_source_start:
            issues.append(ValidationIssue("error", "source_start", "source_start must be a non-negative integer", field + ".source_start"))
        if not valid_count:
            issues.append(ValidationIssue("error", "segment_count", "count must be a positive integer", field + ".count"))
        if not valid_destination:
            issues.append(ValidationIssue("error", "destination_start", "destination_start must be a non-negative integer", field + ".destination_start"))
        if valid_source_start and valid_count and source_count and segment.source_start + segment.count > source_count:
            issues.append(ValidationIssue("error", "source_range", f"Segment {segment.name} exceeds the {source_count}-pixel source", field + ".source_start"))
        if segment.controller not in valid_controllers:
            issues.append(ValidationIssue("error", "unknown_controller", f"Unknown controller: {segment.controller}", field + ".controller"))
        if not isinstance(segment.reverse, bool):
            issues.append(ValidationIssue("error", "reverse", "reverse must be boolean", field + ".reverse"))
        if segment.color_override not in (None, "") and not _valid_order(segment.color_override):
            issues.append(ValidationIssue("error", "color_override", "Color override must be empty or an RGB permutation", field + ".color_override"))
        if valid_source_start and valid_count and valid_destination and segment.controller in valid_controllers:
            valid_segments.append(segment)

    for left_index, left in enumerate(valid_segments):
        for right in valid_segments[left_index + 1 :]:
            if left.controller == right.controller and _interval_overlaps(left.destination_start, left.count, right.destination_start, right.count):
                issues.append(ValidationIssue("error", "destination_overlap", f"Segments {left.name} and {right.name} overlap on {left.controller}", "segments"))
            if _interval_overlaps(left.source_start, left.count, right.source_start, right.count):
                issues.append(ValidationIssue("warning", "source_overlap", f"Source ranges for {left.name} and {right.name} overlap (fan-out is allowed)", "segments"))

    by_controller: dict[str, int] = {name: 0 for name in valid_controllers}
    for segment in valid_segments:
        by_controller[segment.controller] = max(by_controller[segment.controller], segment.destination_start + segment.count)
    for index, controller in enumerate(config.controllers):
        universe_count = ceil(by_controller.get(controller.name, 0) / PIXELS_PER_UNIVERSE)
        if (
            _valid_integer(controller.start_universe, 0, ARTNET_MAX_LINEAR_UNIVERSE)
            and universe_count
            and controller.start_universe + universe_count - 1 > ARTNET_MAX_LINEAR_UNIVERSE
        ):
            issues.append(ValidationIssue("error", "universe_overflow", f"Controller {controller.name} exceeds the Art-Net universe range", f"controllers[{index}].start_universe"))

    # The same linear universe is intentionally reusable on different unicast
    # destinations.  On the same target endpoint it would be ambiguous and is
    # therefore rejected even when the controller rows have different names.
    for left_index, left in enumerate(config.controllers):
        left_count = ceil(by_controller.get(left.name, 0) / PIXELS_PER_UNIVERSE)
        if not left_count or not _valid_integer(left.start_universe, 0, ARTNET_MAX_LINEAR_UNIVERSE):
            continue
        for right_index in range(left_index + 1, len(config.controllers)):
            right = config.controllers[right_index]
            right_count = ceil(by_controller.get(right.name, 0) / PIXELS_PER_UNIVERSE)
            if not right_count or not _valid_integer(right.start_universe, 0, ARTNET_MAX_LINEAR_UNIVERSE):
                continue
            same_endpoint = left.target_address == right.target_address and left.port == right.port
            if same_endpoint and _interval_overlaps(left.start_universe, left_count, right.start_universe, right_count):
                issues.append(ValidationIssue(
                    "error",
                    "artnet_route_overlap",
                    f"Controllers {left.name} and {right.name} overlap at {left.target_address}:{left.port}",
                    f"controllers[{right_index}].start_universe",
                ))

    if config.warn_unassigned and source_count:
        assigned = [False] * source_count
        for segment in valid_segments:
            for pixel in range(segment.source_start, min(source_count, segment.source_start + segment.count)):
                assigned[pixel] = True
        missing = [index for index, state in enumerate(assigned) if not state]
        if missing:
            issues.append(ValidationIssue("warning", "unassigned_source", f"Unassigned source pixels: {_range_text(missing)}", "segments"))
    return tuple(issues)


def build_router_plan(config: RouterConfig) -> RouterPlan:
    issues = validate_router(config)
    blocking = [issue for issue in issues if issue.blocking]
    if blocking:
        raise MultiControllerValidationError("; ".join(f"{issue.code}: {issue.message}" for issue in blocking))
    plans: list[ControllerPlan] = []
    for controller in config.controllers:
        segments = [item for item in config.segments if item.controller == controller.name]
        destination_count = max((item.destination_start + item.count for item in segments), default=0)
        routes: list[UniverseRoute] = []
        for sequence in range(ceil(destination_count / PIXELS_PER_UNIVERSE)):
            linear = controller.start_universe + sequence
            start = sequence * PIXELS_PER_UNIVERSE
            routes.append(
                UniverseRoute(
                    channel=f"Universe{sequence}",
                    sequence=sequence,
                    linear_universe=linear,
                    net=linear // 256,
                    subnet=(linear // 16) % 16,
                    universe=linear % 16,
                    destination_pixel_start=start,
                    active_pixel_count=min(PIXELS_PER_UNIVERSE, destination_count - start),
                )
            )
        plans.append(ControllerPlan(controller, destination_count, tuple(routes)))
    return RouterPlan(config, tuple(plans), issues)


def default_router_config(local_interface: str = "10.0.0.125") -> RouterConfig:
    """Safe two-controller draft matching the currently discussed hardware."""

    return RouterConfig(
        controllers=(
            ControllerConfig(
                name="WS2812_NODE",
                target_address="10.0.0.244",
                local_interface=local_interface,
                enabled=False,
                # GICO UI labels its first universe as 1, while Art-Net carries
                # that universe as the zero-based wire address 0.
                start_universe=0,
                color_order="GRB",
            ),
            ControllerConfig(
                name="APA102_ESP",
                target_address="10.0.0.251",
                local_interface=local_interface,
                enabled=False,
                color_order="RGB",
            ),
        ),
        segments=(
            # Controller hardware is configured for four universes per port.
            # Each Art-Net universe carries 170 RGB pixels (510 channels):
            # port 1 / middle = U1..U4, port 2 / upper = U5..U8,
            # port 3 / lower = U9..U12.  U7..U8 are intentionally black,
            # because the upper side has only 269 pixels.
            SegmentConfig("WS_SIDE_MIDDLE", 0, 517, "WS2812_NODE", 0),
            SegmentConfig("WS_SIDE_UPPER", 517, 269, "WS2812_NODE", 680),
            SegmentConfig("WS_SIDE_LOWER", 786, 398, "WS2812_NODE", 1360),
            # ESP firmware reserves target pixels 0..511 for its WS output.
            SegmentConfig("APA102", 1187, 1167, "APA102_ESP", 512),
        ),
        source_pixel_count=SOURCE_PIXEL_COUNT,
        warn_unassigned=True,
    )


def controller_rows(config: RouterConfig) -> tuple[tuple[object, ...], ...]:
    rows: list[tuple[object, ...]] = [
        ("enabled", "name", "target_ip", "local_interface", "port", "start_universe", "color_order", "brightness", "rate", "art_sync")
    ]
    rows.extend(
        (int(item.enabled), item.name, item.target_address, item.local_interface, item.port, item.start_universe, item.color_order, item.brightness, item.rate, int(item.art_sync))
        for item in config.controllers
    )
    return tuple(rows)


def segment_rows(config: RouterConfig) -> tuple[tuple[object, ...], ...]:
    rows: list[tuple[object, ...]] = [
        ("name", "source_start", "count", "controller", "destination_start", "reverse", "color_override")
    ]
    rows.extend(
        (item.name, item.source_start, item.count, item.controller, item.destination_start, int(item.reverse), item.color_override or "")
        for item in config.segments
    )
    return tuple(rows)
