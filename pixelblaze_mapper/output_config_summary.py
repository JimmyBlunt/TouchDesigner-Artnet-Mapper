"""Pure read-only projection of the live Art-Net router state.

The Output Config dialog is deliberately not a second configuration editor.
This module turns the Router's live tables and sender status into immutable,
display-ready values. It has no TouchDesigner dependency and cannot write a
controller table, start network output, or save a project.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Mapping


PIXELS_PER_UNIVERSE = 170


def _integer(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _floating(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _boolean(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ControllerSummary:
    name: str
    configured_enabled: bool
    sender_active: bool
    target: str
    local_interface: str
    port: int
    first_universe: int
    last_universe: int
    universe_count: int
    pixel_capacity: int
    color_order: str
    brightness: float
    rate: int
    art_sync: bool

    @property
    def state(self) -> str:
        if self.sender_active:
            return "LIVE"
        if self.configured_enabled:
            return "READY / SENDER OFF"
        return "DISABLED"

    @property
    def universe_label(self) -> str:
        if not self.universe_count:
            return "none"
        if self.universe_count == 1:
            return "U%d" % self.first_universe
        return "U%d-U%d" % (self.first_universe, self.last_universe)


@dataclass(frozen=True)
class OutputSummary:
    source_pixels: int | None
    controllers: tuple[ControllerSummary, ...]
    sender_enabled: bool
    sender_mode: str
    sender_error: str
    validation_errors: tuple[str, ...]
    validation_warnings: tuple[str, ...]

    @property
    def state(self) -> str:
        if self.sender_error or self.validation_errors:
            return "BLOCKED"
        if self.sender_enabled:
            return "LIVE"
        return "OUTPUT OFF"


def build_output_summary(
    controller_rows: Iterable[Mapping[str, object]],
    segment_rows: Iterable[Mapping[str, object]],
    sender_status: Mapping[str, object] | None,
    *,
    source_pixels: int | None,
    validation_rows: Iterable[Mapping[str, object]] = (),
) -> OutputSummary:
    """Build one immutable summary solely from live Router-owned sources."""

    controllers = tuple(dict(row) for row in controller_rows)
    segments = tuple(dict(row) for row in segment_rows)
    status = dict(sender_status or {})
    active = {str(value) for value in status.get("controllers", ())}

    destination_counts: dict[str, int] = {}
    for row in segments:
        name = str(row.get("controller", ""))
        end = _integer(row.get("destination_start")) + _integer(row.get("count"))
        destination_counts[name] = max(destination_counts.get(name, 0), end)

    results: list[ControllerSummary] = []
    for row in controllers:
        name = str(row.get("name", ""))
        pixels = destination_counts.get(name, 0)
        derived_count = ceil(pixels / PIXELS_PER_UNIVERSE) if pixels else 0
        count = max(derived_count, _integer(row.get("reserved_universes")))
        capacity = count * PIXELS_PER_UNIVERSE if count else pixels
        first = _integer(row.get("start_universe"))
        results.append(ControllerSummary(
            name=name,
            configured_enabled=_boolean(row.get("enabled")),
            sender_active=name in active and _boolean(status.get("enabled")),
            target=str(row.get("target_ip", "")),
            local_interface=str(row.get("local_interface", "")),
            port=_integer(row.get("port")),
            first_universe=first,
            last_universe=first + count - 1 if count else first,
            universe_count=count,
            pixel_capacity=capacity,
            color_order=str(row.get("color_order", "")),
            brightness=_floating(row.get("brightness")),
            rate=_integer(row.get("rate")),
            art_sync=_boolean(row.get("art_sync")),
        ))

    errors: list[str] = []
    warnings: list[str] = []
    for row in validation_rows:
        severity = str(row.get("severity", "")).strip().casefold()
        message = str(row.get("message", "")).strip()
        if not message:
            continue
        if severity == "error":
            errors.append(message)
        elif severity == "warning":
            warnings.append(message)

    raw_pixels = None if source_pixels is None else _integer(source_pixels, -1)
    normalized_pixels = raw_pixels if raw_pixels is not None and raw_pixels >= 0 else None
    return OutputSummary(
        source_pixels=normalized_pixels,
        controllers=tuple(results),
        sender_enabled=_boolean(status.get("enabled")),
        sender_mode=str(status.get("mode", "unknown")),
        sender_error=str(status.get("error", "")).strip(),
        validation_errors=tuple(errors),
        validation_warnings=tuple(warnings),
    )


def display_rows(summary: OutputSummary) -> tuple[tuple[str, str], ...]:
    """Return stable labels for the read-only TouchDesigner adapter."""

    source = "unavailable" if summary.source_pixels is None else f"{summary.source_pixels:,} RGB pixels"
    rows: list[tuple[str, str]] = [
        ("STATE", summary.state),
        ("SOURCE", source),
        ("SENDER", "%s | %s" % ("ON" if summary.sender_enabled else "OFF", summary.sender_mode.upper())),
    ]
    for controller in summary.controllers:
        rows.append((controller.name, "%s | %s:%d via %s | %s | %d px | %s | %d fps | %.1f%% | ArtSync %s" % (
            controller.state, controller.target, controller.port, controller.local_interface,
            controller.universe_label, controller.pixel_capacity,
            controller.color_order, controller.rate, controller.brightness * 100.0,
            "ON" if controller.art_sync else "OFF",
        )))
    if summary.sender_error:
        rows.append(("SENDER ERROR", summary.sender_error))
    if summary.validation_errors:
        rows.append(("VALIDATION", "%d error(s)" % len(summary.validation_errors)))
    elif summary.validation_warnings:
        rows.append(("VALIDATION", "%d warning(s)" % len(summary.validation_warnings)))
    else:
        rows.append(("VALIDATION", "OK"))
    return tuple(rows)
