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


SCHEMA_VERSION = 1
COORDINATE_MODES = frozenset({"global", "panel_local", "hybrid"})
TRANSITION_TYPES = frozenset(
    {"cut", "crossfade", "dissolve", "wipe", "radial", "glitch"}
)


class ShowValidationError(ValueError):
    """Raised when a show is incomplete, ambiguous, or unsafe to run."""


class TransportState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


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
    coordinate_mode: str
    duration: float
    transition: str
    transition_duration: float
    brightness: float
    target_groups: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.id, "cue.id")
        _text(self.name, "cue.name")
        _text(self.effect, "cue.effect")
        _text(self.preset, "cue.preset", allow_empty=True)
        if self.coordinate_mode not in COORDINATE_MODES:
            raise ShowValidationError(
                "cue.coordinate_mode must be global, panel_local, or hybrid"
            )
        duration = _number(self.duration, "cue.duration", minimum=0.001)
        if self.transition not in TRANSITION_TYPES:
            raise ShowValidationError(
                "cue.transition must be cut, crossfade, dissolve, wipe, radial, or glitch"
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
        if len(set(self.target_groups)) != len(self.target_groups):
            raise ShowValidationError("cue.target_groups must not contain duplicates")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Cue":
        if not isinstance(data, Mapping):
            raise ShowValidationError("cue must be an object")
        expected = {
            "id", "name", "effect", "preset", "coordinate_mode", "duration",
            "transition", "transition_duration", "brightness", "target_groups",
        }
        missing, extra = expected - set(data), set(data) - expected
        if missing or extra:
            raise ShowValidationError(
                f"cue fields invalid; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        groups = data["target_groups"]
        if not isinstance(groups, list):
            raise ShowValidationError("cue.target_groups must be a JSON array")
        return cls(
            id=data["id"], name=data["name"], effect=data["effect"],
            preset=data["preset"], coordinate_mode=data["coordinate_mode"],
            duration=data["duration"], transition=data["transition"],
            transition_duration=data["transition_duration"],
            brightness=data["brightness"], target_groups=tuple(groups),
        )
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "effect": self.effect,
            "preset": self.preset,
            "coordinate_mode": self.coordinate_mode,
            "duration": self.duration,
            "transition": self.transition,
            "transition_duration": self.transition_duration,
            "brightness": self.brightness,
            "target_groups": list(self.target_groups),
        }


@dataclass(frozen=True)
class Show:
    name: str
    cues: tuple[Cue, ...]
    loop: bool = False
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _text(self.name, "show.name")
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
        missing, extra = expected - set(data), set(data) - expected
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
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "loop": self.loop,
            "cues": [cue.to_dict() for cue in self.cues],
        }


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

    @property
    def cue(self) -> Cue:
        return self.show.cues[self.cue_index]

    def play(self) -> None:
        if self.state is TransportState.STOPPED and self.elapsed >= self.cue.duration:
            self.cue_index, self.elapsed, self._current_slot = 0, 0.0, "A"
        self.state = TransportState.PLAYING

    def pause(self) -> None:
        if self.state is TransportState.PLAYING:
            self.state = TransportState.PAUSED

    def stop(self) -> None:
        self.state = TransportState.STOPPED
        self.cue_index, self.elapsed, self._current_slot = 0, 0.0, "A"

    def set_loop(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ShowValidationError("loop must be boolean")
        self.show = Show(
            name=self.show.name, cues=self.show.cues, loop=enabled,
            schema_version=self.show.schema_version,
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
            self.cue_index, self.elapsed = target, 0.0
            self._current_slot = "B" if self._current_slot == "A" else "A"

    def plan(self) -> ABSlotPlan:
        current = self.cue
        next_index = self._next_index()
        incoming = self.show.cues[next_index] if next_index is not None else None
        incoming_slot = "B" if self._current_slot == "A" else "A"
        progress = 0.0
        transition = current.transition
        if incoming is not None and current.transition_duration > 0:
            start = current.duration - current.transition_duration
            progress = min(1.0, max(0.0, (self.elapsed - start) / current.transition_duration))
        slot_a = current if self._current_slot == "A" else incoming
        slot_b = current if self._current_slot == "B" else incoming
        output_b_mix = progress if self._current_slot == "A" else 1.0 - progress
        if incoming is None or current.transition == "cut":
            progress = 0.0
            output_b_mix = 0.0 if self._current_slot == "A" else 1.0
            incoming_slot_value: str | None = None if incoming is None else incoming_slot
        else:
            incoming_slot_value = incoming_slot
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
        )
