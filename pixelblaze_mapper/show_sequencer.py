"""Deterministic, TouchDesigner-independent show sequencer.

The core deliberately has no wall-clock or rendering dependency.  A host calls
``advance(seconds)`` with its own clock delta and consumes :class:`ABSlotPlan`
to drive two material slots and a transition mixer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 2
COORDINATE_MODES = frozenset({"global", "panel_local", "hybrid"})
TARGET_GROUPS = frozenset({"all", "middle", "upper", "lower", "rear"})
TIMING_MODES = frozenset({"legacy", "overlap"})
FADE_CURVES = frozenset({"linear", "smooth", "ease_in", "ease_out"})
# Kept in step with pixelblaze_mapper.show_renderer.TRANSITIONS by
# tests/test_show_transitions.py; this module stays import-free on purpose.
TRANSITION_TYPES = frozenset({
    "cut", "crossfade", "fade_black", "burn",
    "dissolve", "glitch",
    "wipe", "wipe_left", "wipe_up", "wipe_down",
    "radial", "iris", "bars", "checker", "spiral",
})


class ShowValidationError(ValueError):
    """Raised when a show is incomplete, ambiguous, or unsafe to run."""


class TransportState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


def _color(value: object, field: str) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ShowValidationError(f"{field} must contain four RGBA numbers")
    return tuple(_number(item, field, minimum=0.0, maximum=1.0) for item in value)  # type: ignore[return-value]


@dataclass(frozen=True)
class MaterialParameters:
    """Complete renderer state saved by a Show material preset."""

    speed: float
    scale: float
    width: float
    focus_x: float
    focus_y: float
    zoom: float
    gradient: str
    color_a: tuple[float, float, float, float]
    color_b: tuple[float, float, float, float]
    intensity: float = 1.0
    contrast: float = 1.25
    trail: float = 0.0
    direction: float = 0.125
    rotation_degrees: float = 0.0
    seed: float = 0.0
    effect_transition: float = 0.5
    panel_columns: float = 2.0
    panel_rows: float = 5.0
    hybrid_mix: float = 0.5
    density: float = 1.0

    def __post_init__(self) -> None:
        _number(self.speed, "cue.parameters.speed", minimum=0.0, maximum=8.0)
        _number(self.scale, "cue.parameters.scale", minimum=0.01, maximum=100.0)
        _number(self.width, "cue.parameters.width", minimum=0.0, maximum=1.0)
        _number(self.focus_x, "cue.parameters.focus_x", minimum=0.0, maximum=1.0)
        _number(self.focus_y, "cue.parameters.focus_y", minimum=0.0, maximum=1.0)
        _number(self.zoom, "cue.parameters.zoom", minimum=0.25, maximum=8.0)
        _text(self.gradient, "cue.parameters.gradient")
        object.__setattr__(self, "color_a", _color(self.color_a, "cue.parameters.color_a"))
        object.__setattr__(self, "color_b", _color(self.color_b, "cue.parameters.color_b"))
        _number(self.intensity, "cue.parameters.intensity", minimum=0.0, maximum=2.0)
        _number(self.contrast, "cue.parameters.contrast", minimum=0.0, maximum=4.0)
        _number(self.trail, "cue.parameters.trail", minimum=0.0, maximum=1.0)
        _number(self.direction, "cue.parameters.direction", minimum=-8.0, maximum=8.0)
        _number(self.rotation_degrees, "cue.parameters.rotation_degrees", minimum=-3600.0, maximum=3600.0)
        _number(self.seed, "cue.parameters.seed", minimum=-1000000.0, maximum=1000000.0)
        _number(self.effect_transition, "cue.parameters.effect_transition", minimum=0.0, maximum=1.0)
        _number(self.panel_columns, "cue.parameters.panel_columns", minimum=1.0, maximum=64.0)
        _number(self.panel_rows, "cue.parameters.panel_rows", minimum=1.0, maximum=64.0)
        _number(self.hybrid_mix, "cue.parameters.hybrid_mix", minimum=0.0, maximum=1.0)
        _number(self.density, "cue.parameters.density", minimum=0.01, maximum=8.0)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MaterialParameters":
        if not isinstance(data, Mapping):
            raise ShowValidationError("cue.parameters must be an object")
        expected = set(cls.__dataclass_fields__)
        missing, extra = expected - set(data), set(data) - expected
        if missing or extra:
            raise ShowValidationError(
                f"cue.parameters fields invalid; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        values = dict(data)
        values["color_a"] = _color(values["color_a"], "cue.parameters.color_a")
        values["color_b"] = _color(values["color_b"], "cue.parameters.color_b")
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return {
            field: list(value) if field in {"color_a", "color_b"} else value
            for field, value in ((name, getattr(self, name)) for name in self.__dataclass_fields__)
        }


def _number(value: object, field: str, *, minimum: float, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ShowValidationError(f"{field} must be a number")
    result = float(value)
    if not isfinite(result) or result < minimum or (maximum is not None and result > maximum):
        limit = f"{minimum}..{maximum}" if maximum is not None else f">= {minimum}"
        raise ShowValidationError(f"{field} must be finite and {limit}")
    return result


def _text(value: object, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ShowValidationError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise ShowValidationError(f"{field} must not have surrounding whitespace")
    return value


@dataclass(frozen=True)
class Cue:
    id: str
    name: str
    effect: str
    preset: str
    parameters: MaterialParameters
    coordinate_mode: str
    duration: float
    transition: str
    transition_duration: float
    brightness: float
    target_groups: tuple[str, ...]
    fade_in: float = 0.0
    fade_out: float = 0.0
    fade_in_curve: str = "linear"
    fade_out_curve: str = "linear"

    def __post_init__(self) -> None:
        _text(self.id, "cue.id")
        _text(self.name, "cue.name")
        _text(self.effect, "cue.effect")
        _text(self.preset, "cue.preset", allow_empty=True)
        if not isinstance(self.parameters, MaterialParameters):
            raise ShowValidationError("cue.parameters must be validated MaterialParameters")
        if self.coordinate_mode not in COORDINATE_MODES:
            raise ShowValidationError(
                "cue.coordinate_mode must be global, panel_local, or hybrid"
            )
        duration = _number(self.duration, "cue.duration", minimum=0.001)
        _number(self.fade_in, "cue.fade_in", minimum=0.0)
        _number(self.fade_out, "cue.fade_out", minimum=0.0)
        for field in ("fade_in_curve", "fade_out_curve"):
            if not isinstance(getattr(self, field), str) or getattr(self, field) not in FADE_CURVES:
                raise ShowValidationError(f"cue.{field} must be linear, smooth, ease_in, or ease_out")
        if self.transition not in TRANSITION_TYPES:
            raise ShowValidationError(
                "cue.transition must be one of: " + ", ".join(sorted(TRANSITION_TYPES))
            )
        transition_duration = _number(
            self.transition_duration, "cue.transition_duration", minimum=0.0
        )
        if transition_duration > duration:
            raise ShowValidationError("cue.transition_duration must not exceed cue.duration")
        if self.transition == "cut" and transition_duration != 0.0:
            raise ShowValidationError("cut transition_duration must be 0")
        if self.transition != "cut" and transition_duration <= 0.0:
            raise ShowValidationError("non-cut transition_duration must be greater than 0")
        _number(self.brightness, "cue.brightness", minimum=0.0, maximum=1.0)
        if not isinstance(self.target_groups, tuple) or not self.target_groups:
            raise ShowValidationError("cue.target_groups must be a non-empty tuple")
        for group in self.target_groups:
            _text(group, "cue.target_groups item")
            if group not in TARGET_GROUPS:
                raise ShowValidationError(
                    "cue.target_groups must use all, middle, upper, lower, or rear"
                )
        if len(set(self.target_groups)) != len(self.target_groups):
            raise ShowValidationError("cue.target_groups must not contain duplicates")
        if "all" in self.target_groups and len(self.target_groups) != 1:
            raise ShowValidationError("cue.target_groups all cannot be combined")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Cue":
        if not isinstance(data, Mapping):
            raise ShowValidationError("cue must be an object")
        expected = {
            "id", "name", "effect", "preset", "parameters", "coordinate_mode", "duration",
            "transition", "transition_duration", "brightness", "target_groups",
        }
        optional = {"fade_in", "fade_out", "fade_in_curve", "fade_out_curve"}
        missing, extra = expected - set(data), set(data) - expected - optional
        if missing or extra:
            raise ShowValidationError(
                f"cue fields invalid; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        groups = data["target_groups"]
        if not isinstance(groups, list):
            raise ShowValidationError("cue.target_groups must be a JSON array")
        return cls(
            id=data["id"], name=data["name"], effect=data["effect"],
            preset=data["preset"], parameters=MaterialParameters.from_dict(data["parameters"]),
            coordinate_mode=data["coordinate_mode"],
            duration=data["duration"], transition=data["transition"],
            transition_duration=data["transition_duration"],
            brightness=data["brightness"], target_groups=tuple(groups),
            fade_in=data.get("fade_in", 0.0), fade_out=data.get("fade_out", 0.0),
            fade_in_curve=data.get("fade_in_curve", "linear"),
            fade_out_curve=data.get("fade_out_curve", "linear"),
        )
    def to_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "effect": self.effect,
            "preset": self.preset,
            "parameters": self.parameters.to_dict(),
            "coordinate_mode": self.coordinate_mode,
            "duration": self.duration,
            "transition": self.transition,
            "transition_duration": self.transition_duration,
            "brightness": self.brightness,
            "target_groups": list(self.target_groups),
        }
        # Existing schema-2 documents round-trip byte-for-byte structurally.
        for field, default in (("fade_in", 0.0), ("fade_out", 0.0),
                               ("fade_in_curve", "linear"), ("fade_out_curve", "linear")):
            if getattr(self, field) != default:
                result[field] = getattr(self, field)
        return result


@dataclass(frozen=True)
class Show:
    name: str
    cues: tuple[Cue, ...]
    loop: bool = False
    schema_version: int = SCHEMA_VERSION
    timing_mode: str = "legacy"

    def __post_init__(self) -> None:
        _text(self.name, "show.name")
        if not isinstance(self.timing_mode, str) or self.timing_mode not in TIMING_MODES:
            raise ShowValidationError("show.timing_mode must be legacy or overlap")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ShowValidationError(f"schema_version must be {SCHEMA_VERSION}")
        if not isinstance(self.loop, bool):
            raise ShowValidationError("show.loop must be boolean")
        if not isinstance(self.cues, tuple) or not self.cues:
            raise ShowValidationError("show.cues must be a non-empty tuple")
        if not all(isinstance(cue, Cue) for cue in self.cues):
            raise ShowValidationError("show.cues must contain Cue values")
        ids = [cue.id for cue in self.cues]
        if len(ids) != len(set(ids)):
            raise ShowValidationError("cue ids must be unique")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Show":
        if not isinstance(data, Mapping):
            raise ShowValidationError("show must be an object")
        expected = {"schema_version", "name", "loop", "cues"}
        missing, extra = expected - set(data), set(data) - expected - {"timing_mode"}
        if missing or extra:
            raise ShowValidationError(
                f"show fields invalid; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        raw_cues = data["cues"]
        if not isinstance(raw_cues, list):
            raise ShowValidationError("show.cues must be a JSON array")
        return cls(
            name=data["name"],
            cues=tuple(Cue.from_dict(item) for item in raw_cues),
            loop=data["loop"],
            schema_version=data["schema_version"],
            timing_mode=data.get("timing_mode", "legacy"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "name": self.name,
            "loop": self.loop,
            "cues": [cue.to_dict() for cue in self.cues],
        }
        if self.timing_mode != "legacy":
            result["timing_mode"] = self.timing_mode
        return result


def _effective_overlaps(show: Show) -> tuple[float, ...]:
    if not isinstance(show, Show):
        raise ShowValidationError("timeline requires a validated Show")
    if show.timing_mode == "legacy":
        return tuple(cue.transition_duration for cue in show.cues)
    result = []
    incoming = 0.0
    for index, cue in enumerate(show.cues):
        outgoing = 0.0
        if index+1 < len(show.cues) and cue.transition != "cut":
            # A positive solo margin prevents three simultaneous clips and
            # ensures an incoming clip cannot finish before its predecessor.
            outgoing = max(0.0, min(cue.transition_duration,
                                   cue.duration-incoming-.001,
                                   show.cues[index+1].duration-.001))
        result.append(outgoing)
        incoming = outgoing
    return tuple(result)


def overlap_duration(show: Show, index: int) -> float:
    """Effective outgoing overlap; legacy retains its historic preroll length."""
    values = _effective_overlaps(show)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(values):
        raise ShowValidationError("overlap index is out of range")
    return values[index]


def timeline_rows(show: Show) -> list[dict[str, Any]]:
    """Canonical clip intervals. The overlap loop seam is always a hard restart."""
    overlaps = _effective_overlaps(show)
    start = 0.0
    rows = []
    for index, cue in enumerate(show.cues):
        end = start+cue.duration
        rows.append(dict(id=cue.id, start=start, end=end,
                         fade_start=end-overlaps[index],
                         overlap_in=overlaps[index-1] if index and show.timing_mode == "overlap" else 0.0,
                         overlap_out=overlaps[index]))
        start = end-overlaps[index] if show.timing_mode == "overlap" else end
    return rows


def _fade_curve(value: float, kind: str) -> float:
    if kind == "smooth":
        return value*value*(3-2*value)
    if kind == "ease_in":
        return value*value
    if kind == "ease_out":
        return 1-(1-value)*(1-value)
    return value


def cue_envelope(cue: Cue, localtime: float) -> float:
    """Independent clip fade gain; fade-out is 1-curve(normalized fade progress).

    Long requested fades are bounded to the clip duration. If fades intersect,
    their gains multiply, without renormalizing or changing the transition mix.
    """
    if not isinstance(cue, Cue):
        raise ShowValidationError("cue_envelope requires a validated Cue")
    if isinstance(localtime, bool) or not isinstance(localtime, (int, float)) or not isfinite(localtime):
        raise ShowValidationError("envelope time must be finite")
    if localtime < 0 or localtime > cue.duration:
        return 0.0
    gain = 1.0
    fade_in, fade_out = min(cue.fade_in, cue.duration), min(cue.fade_out, cue.duration)
    if fade_in:
        gain *= _fade_curve(min(1.0, localtime/fade_in), cue.fade_in_curve)
    if fade_out:
        progress = max(0.0, (localtime-(cue.duration-fade_out))/fade_out)
        gain *= 1-_fade_curve(min(1.0, progress), cue.fade_out_curve)
    return max(0.0, min(1.0, gain))


@dataclass(frozen=True)
class ABSlotPlan:
    """A complete render-host instruction for the current instant."""

    slot_a: Cue | None
    slot_b: Cue | None
    outgoing_slot: str
    incoming_slot: str | None
    transition: str
    progress: float
    output_b_mix: float
    brightness: float
    target_groups: tuple[str, ...]
    blackout: bool
    slot_a_time: float = 0.0
    slot_b_time: float = 0.0
    timing_mode: str = "legacy"
    slot_a_gain: float = 1.0
    slot_b_gain: float = 1.0
    slot_a_brightness: float = 1.0
    slot_b_brightness: float = 1.0


def load_show(path: str | Path) -> Show:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ShowValidationError(f"cannot load show {source}: {exc}") from exc
    return Show.from_dict(raw)


def save_show(show: Show, path: str | Path) -> Path:
    if not isinstance(show, Show):
        raise ShowValidationError("save_show requires a validated Show")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(show.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(target)
    return target


class ShowSequencer:
    """Explicit transport whose result depends only on calls and deltas."""

    def __init__(self, show: Show):
        if not isinstance(show, Show):
            raise ShowValidationError("ShowSequencer requires a validated Show")
        self.show = show
        self.state = TransportState.STOPPED
        self.cue_index = 0
        self.elapsed = 0.0
        self.blackout = False
        self._current_slot = "A"
        self._current_time_offset = 0.0
        # Transient only: distinguish explicit seeks from ordinary elapsed
        # advancement when integrating live per-slot speed overrides.
        self.position_revision = 0

    @property
    def cue(self) -> Cue:
        return self.show.cues[self.cue_index]

    def play(self) -> None:
        if self.state is TransportState.STOPPED and self.elapsed >= self.cue.duration:
            self.cue_index, self.elapsed, self._current_slot = 0, 0.0, "A"
            self._current_time_offset = 0.0
            self.position_revision += 1
        self.state = TransportState.PLAYING

    def pause(self) -> None:
        if self.state is TransportState.PLAYING:
            self.state = TransportState.PAUSED

    def stop(self) -> None:
        self.state = TransportState.STOPPED
        self.cue_index, self.elapsed, self._current_slot = 0, 0.0, "A"
        self._current_time_offset = 0.0
        self.position_revision += 1

    def set_loop(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ShowValidationError("loop must be boolean")
        self.show = Show(
            name=self.show.name, cues=self.show.cues, loop=enabled,
            schema_version=self.show.schema_version,
            timing_mode=self.show.timing_mode,
        )

    def set_blackout(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ShowValidationError("blackout must be boolean")
        self.blackout = enabled

    def toggle_blackout(self) -> bool:
        self.blackout = not self.blackout
        return self.blackout

    def _next_index(self) -> int | None:
        if self.cue_index + 1 < len(self.show.cues):
            return self.cue_index + 1
        return 0 if self.show.loop else None

    def next(self) -> bool:
        target = self._next_index()
        if target is None:
            return False
        self.cue_index, self.elapsed = target, 0.0
        self._current_slot = "B" if self._current_slot == "A" else "A"
        self._current_time_offset = 0.0  # Explicit manual jumps restart the cue.
        self.position_revision += 1
        return True

    def go(self) -> bool:
        return self.next()

    def previous(self) -> bool:
        if self.cue_index > 0:
            target = self.cue_index - 1
        elif self.show.loop:
            target = len(self.show.cues) - 1
        else:
            return False
        self.cue_index, self.elapsed = target, 0.0
        self._current_slot = "B" if self._current_slot == "A" else "A"
        self._current_time_offset = 0.0
        self.position_revision += 1
        return True

    def seek(self, cue: int | str, elapsed: float = 0.0) -> None:
        if isinstance(cue, bool):
            raise ShowValidationError("cue seek target must be an index or id")
        if isinstance(cue, str):
            matches = [i for i, item in enumerate(self.show.cues) if item.id == cue]
            if not matches:
                raise ShowValidationError(f"unknown cue id: {cue}")
            index = matches[0]
        elif isinstance(cue, int) and 0 <= cue < len(self.show.cues):
            index = cue
        else:
            raise ShowValidationError("cue seek index is out of range")
        position = _number(elapsed, "seek elapsed", minimum=0.0)
        if position >= self.show.cues[index].duration:
            raise ShowValidationError("seek elapsed must be less than cue.duration")
        self.cue_index, self.elapsed = index, position
        self._current_slot = "A" if index % 2 == 0 else "B"
        self._current_time_offset = 0.0
        self.position_revision += 1

    def advance(self, seconds: float) -> None:
        delta = _number(seconds, "advance seconds", minimum=0.0)
        if self.state is not TransportState.PLAYING or delta == 0.0:
            return
        epsilon = 1e-12
        while delta > epsilon and self.state is TransportState.PLAYING:
            remaining = max(0.0, self.cue.duration - self.elapsed)
            if delta + epsilon < remaining:
                self.elapsed += delta
                return
            delta = max(0.0, delta - remaining)
            target = self._next_index()
            if target is None:
                self.elapsed = self.cue.duration
                self.state = TransportState.STOPPED
                return
            # Incoming material started at the beginning of this transition.
            # Retain that preroll when it becomes the outgoing/current slot.
            if self.show.timing_mode == "overlap":
                preroll = overlap_duration(self.show, self.cue_index)
                self.cue_index, self.elapsed = target, preroll
                self._current_time_offset = 0.0
            else:
                preroll = self.cue.transition_duration if self.cue.transition != 'cut' else 0.0
                self.cue_index, self.elapsed = target, 0.0
                self._current_time_offset = preroll
            self._current_slot = "B" if self._current_slot == "A" else "A"

    def plan(self) -> ABSlotPlan:
        current = self.cue
        next_index = self._next_index()
        if self.show.timing_mode == "overlap" and self.cue_index == len(self.show.cues)-1:
            next_index = None  # No last-to-first transition, even for a loop.
        incoming = self.show.cues[next_index] if next_index is not None else None
        incoming_slot = "B" if self._current_slot == "A" else "A"
        progress = 0.0
        transition = current.transition
        overlap = overlap_duration(self.show, self.cue_index)
        if incoming is not None and overlap > 0:
            start = current.duration - overlap
            progress = min(1.0, max(0.0, (self.elapsed - start) / overlap))
        slot_a = current if self._current_slot == "A" else incoming
        slot_b = current if self._current_slot == "B" else incoming
        current_time = getattr(self, '_current_time_offset', 0.0) + self.elapsed
        incoming_time = max(0.0, self.elapsed - (current.duration - overlap)) if incoming is not None and transition != 'cut' else 0.0
        output_b_mix = progress if self._current_slot == "A" else 1.0 - progress
        if incoming is None or current.transition == "cut":
            progress = 0.0
            output_b_mix = 0.0 if self._current_slot == "A" else 1.0
            incoming_slot_value: str | None = None if incoming is None else incoming_slot
        else:
            incoming_slot_value = incoming_slot
        current_gain = incoming_gain = 1.0
        if self.show.timing_mode == "overlap":
            current_gain = cue_envelope(current, current_time)
            incoming_active = incoming is not None and overlap > 0 and self.elapsed >= current.duration-overlap
            incoming_gain = cue_envelope(incoming, incoming_time) if incoming_active else 0.0
        return ABSlotPlan(
            slot_a=slot_a,
            slot_b=slot_b,
            outgoing_slot=self._current_slot,
            incoming_slot=incoming_slot_value,
            transition=transition,
            progress=progress,
            output_b_mix=output_b_mix,
            brightness=0.0 if self.blackout else current.brightness,
            target_groups=current.target_groups,
            blackout=self.blackout,
            slot_a_time=current_time if self._current_slot == 'A' else incoming_time,
            slot_b_time=current_time if self._current_slot == 'B' else incoming_time,
            timing_mode=self.show.timing_mode,
            slot_a_gain=current_gain if self._current_slot == 'A' else incoming_gain,
            slot_b_gain=current_gain if self._current_slot == 'B' else incoming_gain,
            slot_a_brightness=slot_a.brightness if slot_a else 0.0,
            slot_b_brightness=slot_b.brightness if slot_b else 0.0,
        )
