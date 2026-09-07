"""Pure-Python configuration model for fixed GICO Art-Net port blocks.

The GICO controller applies one global universe count to every physical port.
This module models that constraint without importing TouchDesigner and without
sending Art-Net data.  Universe numbers are the one-based values shown by the
controller's configuration utility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS


CHANNELS_PER_UNIVERSE = 510
CHANNELS_PER_PIXEL = 3
PIXELS_PER_UNIVERSE = CHANNELS_PER_UNIVERSE // CHANNELS_PER_PIXEL
COLOR_ORDERS = frozenset(("RGB", "RBG", "GRB", "GBR", "BRG", "BGR"))


class GicoConfigError(ValueError):
    """Raised when a GICO port draft cannot be used safely."""


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    field: str = ""
    port: int | None = None

    @property
    def blocking(self) -> bool:
        return self.severity == "error"


@dataclass(frozen=True)
class GicoPortConfig:
    """User-editable settings for one physical controller port.

    ``source_start=None`` intentionally means that no logical LED range has
    been assigned yet.  This is a valid draft state even for an enabled port;
    adapters must not emit a routing segment until a source is assigned.
    """

    port: int
    label: str = ""
    enabled: bool = False
    source_start: int | None = None
    pixel_count: int = 0
    reverse: bool = False
    color_order: str = "RGB"


@dataclass(frozen=True)
class GicoConfig:
    universes_per_port: int
    ports: tuple[GicoPortConfig, ...]
    first_universe: int = 1
    source_pixel_count: int = TOTAL_PIXELS


@dataclass(frozen=True)
class GicoPortPlan:
    config: GicoPortConfig
    start_universe: int
    end_universe: int
    destination_pixel_start: int
    capacity_pixels: int

    @property
    def source_end_exclusive(self) -> int | None:
        if self.config.source_start is None:
            return None
        return self.config.source_start + self.config.pixel_count

    @property
    def has_source_assignment(self) -> bool:
        return self.config.source_start is not None

    @property
    def routable(self) -> bool:
        return (
            self.config.enabled
            and self.has_source_assignment
            and self.config.pixel_count > 0
        )


@dataclass(frozen=True)
class GicoPlan:
    config: GicoConfig
    ports: tuple[GicoPortPlan, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def blocking(self) -> bool:
        return any(issue.blocking for issue in self.issues)

    @property
    def reserved_universes(self) -> int:
        if not self.ports:
            return 0
        return max(port.config.port for port in self.ports) * self.config.universes_per_port

    def port(self, number: int) -> GicoPortPlan:
        for item in self.ports:
            if item.config.port == number:
                return item
        raise KeyError(number)


def _is_integer(value: object, *, minimum: int = 0) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= minimum


def _overlaps(left_start: int, left_count: int, right_start: int, right_count: int) -> bool:
    return max(left_start, right_start) < min(
        left_start + left_count,
        right_start + right_count,
    )


def validate_gico_config(config: GicoConfig) -> tuple[ValidationIssue, ...]:
    """Validate a draft without requiring every physical port to be routed."""

    issues: list[ValidationIssue] = []
    global_valid = _is_integer(config.universes_per_port, minimum=1)
    if not global_valid:
        issues.append(
            ValidationIssue(
                "error",
                "universes_per_port",
                "universes_per_port must be a positive integer",
                "universes_per_port",
            )
        )
    if not _is_integer(config.first_universe, minimum=1) or config.first_universe > 32768:
        issues.append(
            ValidationIssue(
                "error",
                "first_universe",
                "first_universe must be a one-based universe number in 1..32768",
                "first_universe",
            )
        )
    if not _is_integer(config.source_pixel_count, minimum=1):
        issues.append(ValidationIssue('error', 'source_pixel_count',
                                      'source_pixel_count must be positive', 'source_pixel_count'))

    seen_ports: set[int] = set()
    assigned: list[GicoPortConfig] = []
    for port in config.ports:
        port_number_valid = _is_integer(port.port, minimum=1)
        if not port_number_valid:
            issues.append(
                ValidationIssue(
                    "error", "port", "port must be a positive integer", "port", port.port
                )
            )
        elif port.port in seen_ports:
            issues.append(
                ValidationIssue(
                    "error",
                    "duplicate_port",
                    f"physical port {port.port} is configured more than once",
                    "port",
                    port.port,
                )
            )
        else:
            seen_ports.add(port.port)
        if (port_number_valid and global_valid
                and _is_integer(config.first_universe, minimum=1)
                and config.first_universe + port.port * config.universes_per_port - 1 > 32768):
            issues.append(ValidationIssue('error', 'universe_overflow',
                'port block exceeds UI universe 32768 / wire universe 32767',
                'first_universe', port.port))

        if not isinstance(port.label, str):
            issues.append(
                ValidationIssue("error", "label", "label must be text", "label", port.port)
            )
        if not isinstance(port.enabled, bool):
            issues.append(
                ValidationIssue(
                    "error", "enabled", "enabled must be boolean", "enabled", port.port
                )
            )
        if not isinstance(port.reverse, bool):
            issues.append(
                ValidationIssue(
                    "error", "reverse", "reverse must be boolean", "reverse", port.port
                )
            )
        if port.color_order not in COLOR_ORDERS:
            issues.append(
                ValidationIssue(
                    "error",
                    "color_order",
                    "color_order must be an RGB channel permutation",
                    "color_order",
                    port.port,
                )
            )

        count_valid = _is_integer(port.pixel_count)
        if not count_valid:
            issues.append(
                ValidationIssue(
                    "error",
                    "pixel_count",
                    "pixel_count must be a non-negative integer",
                    "pixel_count",
                    port.port,
                )
            )
        elif global_valid and port.pixel_count > config.universes_per_port * PIXELS_PER_UNIVERSE:
            capacity = config.universes_per_port * PIXELS_PER_UNIVERSE
            issues.append(
                ValidationIssue(
                    "error",
                    "port_capacity",
                    f"port {port.port} needs {port.pixel_count} pixels but its block holds {capacity}",
                    "pixel_count",
                    port.port,
                )
            )

        source_valid = port.source_start is None or _is_integer(port.source_start)
        if not source_valid:
            issues.append(
                ValidationIssue(
                    "error",
                    "source_start",
                    "source_start must be a non-negative integer or None",
                    "source_start",
                    port.port,
                )
            )
        elif (
            port.enabled is True
            and count_valid
            and port.pixel_count > 0
            and port.source_start is None
        ):
            issues.append(
                ValidationIssue(
                    "warning",
                    "source_unassigned",
                    f"port {port.port} has no logical source range and is not routable yet",
                    "source_start",
                    port.port,
                )
            )

        if (
            port.enabled is True
            and count_valid
            and port.pixel_count > 0
            and isinstance(port.source_start, int)
            and not isinstance(port.source_start, bool)
            and port.source_start >= 0
        ):
            assigned.append(port)
            if (_is_integer(config.source_pixel_count, minimum=1)
                    and port.source_start + port.pixel_count > config.source_pixel_count):
                issues.append(ValidationIssue('error', 'source_range',
                    f'port {port.port} exceeds the {config.source_pixel_count}-pixel source',
                    'source_start', port.port))

    for index, left in enumerate(assigned):
        for right in assigned[index + 1 :]:
            assert left.source_start is not None and right.source_start is not None
            if _overlaps(left.source_start, left.pixel_count, right.source_start, right.pixel_count):
                issues.append(
                    ValidationIssue(
                        "error",
                        "source_overlap",
                        f"source ranges for ports {left.port} and {right.port} overlap",
                        "source_start",
                    )
                )

    return tuple(issues)


def build_gico_plan(config: GicoConfig) -> GicoPlan:
    """Compute fixed port blocks and reject only unsafe draft values."""

    issues = validate_gico_config(config)
    blocking = tuple(issue for issue in issues if issue.blocking)
    if blocking:
        summary = "; ".join(f"{issue.code}: {issue.message}" for issue in blocking)
        raise GicoConfigError(summary)

    capacity = config.universes_per_port * PIXELS_PER_UNIVERSE
    plans = tuple(
        GicoPortPlan(
            config=port,
            start_universe=config.first_universe + (port.port - 1) * config.universes_per_port,
            end_universe=config.first_universe + port.port * config.universes_per_port - 1,
            destination_pixel_start=(port.port - 1) * capacity,
            capacity_pixels=capacity,
        )
        for port in sorted(config.ports, key=lambda item: item.port)
    )
    return GicoPlan(config=config, ports=plans, issues=issues)
