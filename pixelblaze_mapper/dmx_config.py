"""Pure-Python DMX/Art-Net allocation model for the Pixelblaze mapper.

This module does not import TouchDesigner and never sends network packets.  It
builds and validates the tables an adapter may later commit atomically.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import IPv4Address
from math import ceil
from typing import Any, Iterable, Mapping, Sequence, TypeVar


ARTNET_MAX_LINEAR_UNIVERSE = 127 * 256 + 15 * 16 + 15
DMX_WIRE_SLOTS = 512
DEFAULT_PAYLOAD_SLOTS = 510

T = TypeVar("T")


class DmxValidationError(ValueError):
    """Raised when a configuration or generated plan is unsafe."""


class DiffClass(str, Enum):
    """Primary risk classification for a proposed output change."""

    UNCHANGED = "unchanged"
    APPEND = "append"
    REINDEX = "reindex"
    NETWORK = "network"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ArtNetAddress:
    """Art-Net Port-Address decomposed into Net/Sub-Net/Universe fields."""

    net: int
    subnet: int
    universe: int

    def __post_init__(self) -> None:
        if not 0 <= self.net <= 127:
            raise DmxValidationError("Art-Net net must be 0..127")
        if not 0 <= self.subnet <= 15:
            raise DmxValidationError("Art-Net subnet must be 0..15")
        if not 0 <= self.universe <= 15:
            raise DmxValidationError("Art-Net universe field must be 0..15")

    @classmethod
    def from_linear(cls, value: int) -> "ArtNetAddress":
        if isinstance(value, bool) or not isinstance(value, int):
            raise DmxValidationError("Art-Net universe must be an integer")
        if not 0 <= value <= ARTNET_MAX_LINEAR_UNIVERSE:
            raise DmxValidationError(
                f"Art-Net universe must be 0..{ARTNET_MAX_LINEAR_UNIVERSE}"
            )
        return cls(value // 256, (value // 16) % 16, value % 16)

    @property
    def linear(self) -> int:
        return self.net * 256 + self.subnet * 16 + self.universe


@dataclass(frozen=True)
class DmxConfig:
    """Declarative DMX output settings.

    Values enter the model in ``source_order`` (logical RGB by default) and are
    emitted in ``output_order`` (the installation's GRB default).
    ``start_channel`` is one-based and applies only to the first universe.
    """

    pixel_count: int
    source_order: str = "RGB"
    output_order: str = "GRB"
    start_universe: int = 0
    start_channel: int = 1
    payload_slots: int = DEFAULT_PAYLOAD_SLOTS
    target_address: str = "10.0.0.244"
    local_address: str = "10.0.0.173"
    port: int = 6454

    @property
    def channels_per_pixel(self) -> int:
        return len(self.output_order)

    @property
    def pixels_per_full_universe(self) -> int:
        channels = self.channels_per_pixel
        return self.payload_slots // channels if channels else 0


@dataclass(frozen=True)
class UniverseAllocation:
    sequence: int
    channel: str
    address: ArtNetAddress
    start_pixel: int
    pixel_count: int
    start_channel: int
    leading_padding: int
    active_slots: int
    trailing_padding: int
    sample_count: int
    channels_per_pixel: int

    @property
    def stream_start(self) -> int:
        return self.start_pixel * self.channels_per_pixel

    @property
    def stream_end_exclusive(self) -> int:
        return self.stream_start + self.active_slots


@dataclass(frozen=True)
class DmxPlan:
    config: DmxConfig
    universes: tuple[UniverseAllocation, ...]

    @property
    def universe_count(self) -> int:
        return len(self.universes)

    @property
    def last_pixel_count(self) -> int:
        return self.universes[-1].pixel_count if self.universes else 0

    @property
    def flat_sample_count(self) -> int:
        return self.config.pixel_count * self.config.channels_per_pixel

    @property
    def lookup_index_end(self) -> int | None:
        return self.flat_sample_count - 1 if self.flat_sample_count else None

    @property
    def channel_names(self) -> tuple[str, ...]:
        return tuple(universe.channel for universe in self.universes)

    def dmx_universe_rows(self, *, include_header: bool = True) -> tuple[tuple[object, ...], ...]:
        """Rows compatible with the current ``DMX_Universes`` Table DAT."""

        rows: list[tuple[object, ...]] = []
        if include_header:
            rows.append(("Universe", "index", "pixel"))
        rows.extend(
            (universe.sequence, universe.start_pixel, universe.pixel_count)
            for universe in self.universes
        )
        return tuple(rows)

    def routing_rows(self, *, include_header: bool = True) -> tuple[tuple[object, ...], ...]:
        """Rows compatible with the current DMX Out routing Table DAT."""

        rows: list[tuple[object, ...]] = []
        if include_header:
            rows.append(("channel", "net", "subnet", "universe"))
        rows.extend(
            (
                universe.channel,
                universe.address.net,
                universe.address.subnet,
                universe.address.universe,
            )
            for universe in self.universes
        )
        return tuple(rows)

    def pack_pixels(self, pixels: Sequence[Sequence[T]], *, pad_value: T = 0) -> tuple[tuple[T, ...], ...]:
        """Reorder and pad logical pixels into fixed 510-sample universe frames."""

        if len(pixels) != self.config.pixel_count:
            raise DmxValidationError(
                f"Expected {self.config.pixel_count} pixels, got {len(pixels)}"
            )
        channel_count = self.config.channels_per_pixel
        for index, pixel in enumerate(pixels):
            if len(pixel) != channel_count:
                raise DmxValidationError(
                    f"Pixel {index} has {len(pixel)} channels; expected {channel_count}"
                )
        source_positions = {
            channel: index for index, channel in enumerate(self.config.source_order)
        }
        frames: list[tuple[T, ...]] = []
        for universe in self.universes:
            values: list[T] = [pad_value] * universe.leading_padding
            for pixel in pixels[
                universe.start_pixel : universe.start_pixel + universe.pixel_count
            ]:
                values.extend(pixel[source_positions[channel]] for channel in self.config.output_order)
            values.extend([pad_value] * universe.trailing_padding)
            if len(values) != self.config.payload_slots:
                raise DmxValidationError(
                    f"Internal packing error for {universe.channel}: {len(values)} samples"
                )
            frames.append(tuple(values))
        return tuple(frames)

    def pack_flat(self, values: Sequence[T], *, pad_value: T = 0) -> tuple[tuple[T, ...], ...]:
        """Pack a flat source-order stream into fixed-size universe frames."""

        channels = self.config.channels_per_pixel
        expected = self.config.pixel_count * channels
        if len(values) != expected:
            raise DmxValidationError(f"Expected {expected} values, got {len(values)}")
        pixels = tuple(
            tuple(values[offset : offset + channels])
            for offset in range(0, len(values), channels)
        )
        return self.pack_pixels(pixels, pad_value=pad_value)


def validate_config(config: DmxConfig) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    pixel_count_valid = (
        not isinstance(config.pixel_count, bool)
        and isinstance(config.pixel_count, int)
        and config.pixel_count >= 0
    )
    if not pixel_count_valid:
        issues.append(ValidationIssue("pixel_count", "pixel_count must be a non-negative integer"))

    source = config.source_order.upper() if isinstance(config.source_order, str) else ""
    output = config.output_order.upper() if isinstance(config.output_order, str) else ""
    if not source or len(source) != len(set(source)):
        issues.append(ValidationIssue("source_order", "source_order must contain unique channels"))
    if len(output) != len(source) or set(output) != set(source):
        issues.append(
            ValidationIssue(
                "output_order",
                "output_order must be a permutation of source_order",
            )
        )
    if source != config.source_order or output != config.output_order:
        issues.append(ValidationIssue("color_order_case", "color order must use uppercase channel names"))

    payload_valid = (
        not isinstance(config.payload_slots, bool)
        and isinstance(config.payload_slots, int)
        and 1 <= config.payload_slots <= DMX_WIRE_SLOTS
    )
    if not payload_valid:
        issues.append(
            ValidationIssue("payload_slots", f"payload_slots must be 1..{DMX_WIRE_SLOTS}")
        )
    channel_count = len(output)
    start_channel_valid = (
        not isinstance(config.start_channel, bool)
        and isinstance(config.start_channel, int)
        and payload_valid
        and 1 <= config.start_channel <= config.payload_slots
    )
    if channel_count and payload_valid and start_channel_valid and pixel_count_valid:
        leading = config.start_channel - 1
        if config.pixel_count and config.payload_slots - leading < channel_count:
            issues.append(
                ValidationIssue(
                    "start_channel_capacity",
                    "start_channel leaves no room for a complete pixel",
                )
            )

    if not start_channel_valid:
        issues.append(
            ValidationIssue(
                "start_channel",
                "start_channel must be one-based and inside payload_slots",
            )
        )
    if isinstance(config.start_universe, bool) or not isinstance(config.start_universe, int):
        issues.append(ValidationIssue("start_universe", "start_universe must be an integer"))
    elif not 0 <= config.start_universe <= ARTNET_MAX_LINEAR_UNIVERSE:
        issues.append(
            ValidationIssue(
                "start_universe",
                f"start_universe must be 0..{ARTNET_MAX_LINEAR_UNIVERSE}",
            )
        )

    for field_name, value in (
        ("target_address", config.target_address),
        ("local_address", config.local_address),
    ):
        try:
            if not isinstance(value, str):
                raise ValueError
            IPv4Address(value)
        except Exception:
            issues.append(ValidationIssue(field_name, f"{field_name} must be a valid IPv4 address"))
    if isinstance(config.port, bool) or not isinstance(config.port, int) or not 1 <= config.port <= 65535:
        issues.append(ValidationIssue("port", "port must be 1..65535"))

    if not issues and config.pixel_count:
        first_capacity = (config.payload_slots - config.start_channel + 1) // channel_count
        remaining = max(0, config.pixel_count - first_capacity)
        full_capacity = config.payload_slots // channel_count
        universe_count = 1 + ceil(remaining / full_capacity) if remaining else 1
        if config.start_universe + universe_count - 1 > ARTNET_MAX_LINEAR_UNIVERSE:
            issues.append(
                ValidationIssue(
                    "universe_overflow",
                    "allocated universes exceed the Art-Net address range",
                )
            )
    return tuple(issues)


def build_plan(config: DmxConfig) -> DmxPlan:
    issues = validate_config(config)
    if issues:
        raise DmxValidationError("; ".join(f"{issue.code}: {issue.message}" for issue in issues))
    if config.pixel_count == 0:
        return DmxPlan(config, ())

    channel_count = config.channels_per_pixel
    remaining = config.pixel_count
    start_pixel = 0
    sequence = 0
    allocations: list[UniverseAllocation] = []
    while remaining:
        start_channel = config.start_channel if sequence == 0 else 1
        leading = start_channel - 1
        capacity = (config.payload_slots - leading) // channel_count
        pixels = min(capacity, remaining)
        active = pixels * channel_count
        trailing = config.payload_slots - leading - active
        allocations.append(
            UniverseAllocation(
                sequence=sequence,
                channel=f"Universe{sequence}",
                address=ArtNetAddress.from_linear(config.start_universe + sequence),
                start_pixel=start_pixel,
                pixel_count=pixels,
                start_channel=start_channel,
                leading_padding=leading,
                active_slots=active,
                trailing_padding=trailing,
                sample_count=config.payload_slots,
                channels_per_pixel=channel_count,
            )
        )
        remaining -= pixels
        start_pixel += pixels
        sequence += 1
    plan = DmxPlan(config, tuple(allocations))
    plan_issues = validate_plan(plan)
    if plan_issues:
        raise DmxValidationError(
            "; ".join(f"{issue.code}: {issue.message}" for issue in plan_issues)
        )
    return plan


def allocate_dmx(config: Mapping[str, Any]) -> dict[str, Any]:
    """UI-contract adapter returning only JSON/Table-DAT-friendly values.

    Invalid drafts return structured blocking issues instead of raising.  This
    keeps the UI responsive while fields are being edited.  ``build_plan``
    remains the strict API for an eventual transactional TouchDesigner adapter.
    """

    field_aliases = {
        "pixel_count": "pixel_count",
        "channel_order": "output_order",
        "start_universe": "start_universe",
        "start_channel": "start_channel",
        "target_address": "target_address",
        "local_address": "local_address",
        "port": "port",
    }
    allowed = set(DmxConfig.__dataclass_fields__)
    kwargs: dict[str, Any] = {}
    for source_name, target_name in field_aliases.items():
        if source_name in config:
            kwargs[target_name] = config[source_name]
    for name in allowed:
        if name in config:
            kwargs[name] = config[name]

    pixel_format = config.get("pixel_format", "rgb")
    if "source_order" not in kwargs:
        kwargs["source_order"] = str(pixel_format).upper()
    issues: list[dict[str, str]] = []
    try:
        draft = DmxConfig(**kwargs)
    except TypeError as exc:
        return _allocation_error_result(config, "config", str(exc), "")

    config_issues = validate_config(draft)
    if config_issues:
        issues = [_ui_issue(issue) for issue in config_issues]
        return {
            "pixel_count": draft.pixel_count if isinstance(draft.pixel_count, int) else 0,
            "channels_required": 0,
            "universe_count": 0,
            "last_universe_pixels": 0,
            "capacity_pixels": 0,
            "rows": [],
            "issues": issues,
        }

    plan = build_plan(draft)
    rows = [
        {
            "channel": universe.channel,
            "logical": universe.sequence,
            "net": universe.address.net,
            "subnet": universe.address.subnet,
            "universe": universe.address.universe,
            "pixel_start": universe.start_pixel,
            "pixel_count": universe.pixel_count,
            "dmx_start": universe.start_channel,
            "dmx_end": universe.start_channel + universe.active_slots - 1,
            "state": "OK",
        }
        for universe in plan.universes
    ]
    return {
        "pixel_count": draft.pixel_count,
        "channels_required": plan.flat_sample_count,
        "universe_count": plan.universe_count,
        "last_universe_pixels": plan.last_pixel_count,
        "capacity_pixels": sum(
            (draft.payload_slots - universe.leading_padding)
            // draft.channels_per_pixel
            for universe in plan.universes
        ),
        "rows": rows,
        "issues": issues,
    }


def _allocation_error_result(
    config: Mapping[str, Any], code: str, message: str, field: str
) -> dict[str, Any]:
    pixel_count = config.get("pixel_count", 0)
    return {
        "pixel_count": pixel_count if isinstance(pixel_count, int) else 0,
        "channels_required": 0,
        "universe_count": 0,
        "last_universe_pixels": 0,
        "capacity_pixels": 0,
        "rows": [],
        "issues": [
            {"severity": "blocked", "code": code, "message": message, "field": field}
        ],
    }


def _ui_issue(issue: ValidationIssue) -> dict[str, str]:
    ui_fields = {
        "output_order": "channel_order",
        "source_order": "pixel_format",
    }
    field = ui_fields.get(
        issue.code,
        issue.code if issue.code in DmxConfig.__dataclass_fields__ else "",
    )
    return {
        "severity": "blocked",
        "code": issue.code,
        "message": issue.message,
        "field": field,
    }


def validate_plan(plan: DmxPlan) -> tuple[ValidationIssue, ...]:
    issues = list(validate_config(plan.config))
    if issues:
        return tuple(issues)
    expected_start = 0
    seen_addresses: set[int] = set()
    for sequence, universe in enumerate(plan.universes):
        if universe.sequence != sequence or universe.channel != f"Universe{sequence}":
            issues.append(ValidationIssue("sequence", f"Invalid channel sequence at {sequence}"))
        if universe.start_pixel != expected_start:
            issues.append(ValidationIssue("pixel_gap", f"Unexpected start pixel in {universe.channel}"))
        expected_start += universe.pixel_count
        expected_address = plan.config.start_universe + sequence
        if universe.address.linear != expected_address or expected_address in seen_addresses:
            issues.append(ValidationIssue("routing", f"Invalid/duplicate route for {universe.channel}"))
        seen_addresses.add(expected_address)
        expected_start_channel = plan.config.start_channel if sequence == 0 else 1
        if universe.start_channel != expected_start_channel:
            issues.append(ValidationIssue("start_channel", f"Wrong start channel in {universe.channel}"))
        if universe.leading_padding != universe.start_channel - 1:
            issues.append(ValidationIssue("leading_padding", f"Wrong leading padding in {universe.channel}"))
        capacity = (plan.config.payload_slots - universe.leading_padding) // plan.config.channels_per_pixel
        expected_pixels = min(capacity, plan.config.pixel_count - universe.start_pixel)
        if universe.pixel_count != expected_pixels or universe.pixel_count <= 0:
            issues.append(ValidationIssue("pixel_allocation", f"Wrong pixel allocation in {universe.channel}"))
        if universe.leading_padding + universe.active_slots + universe.trailing_padding != plan.config.payload_slots:
            issues.append(ValidationIssue("sample_count", f"Invalid padding in {universe.channel}"))
        if universe.leading_padding < 0 or universe.trailing_padding < 0:
            issues.append(ValidationIssue("padding", f"Negative padding in {universe.channel}"))
        if universe.sample_count != plan.config.payload_slots:
            issues.append(ValidationIssue("sample_count", f"Wrong sample count in {universe.channel}"))
        if universe.channels_per_pixel != plan.config.channels_per_pixel:
            issues.append(ValidationIssue("channels_per_pixel", f"Wrong channel count in {universe.channel}"))
        if universe.active_slots != universe.pixel_count * plan.config.channels_per_pixel:
            issues.append(ValidationIssue("active_slots", f"Invalid active slot count in {universe.channel}"))
    if expected_start != plan.config.pixel_count:
        issues.append(ValidationIssue("pixel_total", "Universe pixel total differs from pixel_count"))
    if bool(plan.universes) != bool(plan.config.pixel_count):
        issues.append(ValidationIssue("universe_count", "Empty/non-empty plan does not match pixel_count"))
    return tuple(issues)


_NETWORK_FIELDS = (
    "source_order",
    "output_order",
    "start_universe",
    "start_channel",
    "payload_slots",
    "target_address",
    "local_address",
    "port",
)


def classify_diff(
    current: DmxConfig,
    proposed: DmxConfig,
    *,
    current_indices: Iterable[int] | None = None,
    proposed_indices: Iterable[int] | None = None,
) -> DiffClass:
    """Classify the highest-risk difference between two output topologies.

    Network/output settings take precedence.  Without explicit index sequences,
    contiguous ranges derived from ``pixel_count`` are used.
    """

    if any(getattr(current, field) != getattr(proposed, field) for field in _NETWORK_FIELDS):
        return DiffClass.NETWORK
    old = tuple(range(current.pixel_count)) if current_indices is None else tuple(current_indices)
    new = tuple(range(proposed.pixel_count)) if proposed_indices is None else tuple(proposed_indices)
    if len(old) != current.pixel_count or len(new) != proposed.pixel_count:
        return DiffClass.REINDEX
    contiguous_old = old == tuple(range(len(old)))
    contiguous_new = new == tuple(range(len(new)))
    if old == new and contiguous_old:
        return DiffClass.UNCHANGED
    if len(new) > len(old) and contiguous_old and contiguous_new and new[: len(old)] == old:
        return DiffClass.APPEND
    return DiffClass.REINDEX
