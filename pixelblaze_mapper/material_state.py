"""Pure per-material parameter and continuous-phase state.

The phase clock integrates elapsed time.  It intentionally never derives the
phase from ``absolute_time * speed`` because changing speed in that formula
changes the already elapsed part of the animation and therefore jumps.

This module has no TouchDesigner or output dependencies.  The companion
``build_p1_material_state.py`` adapts it to the live control component.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import isfinite
from typing import Any, Mapping


COORDINATE_MODES = ("global", "panel", "hybrid")
DEFAULT_COLOR_A = (0.91, 0.0, 1.0, 1.0)
DEFAULT_COLOR_B = (0.0, 0.72, 0.86, 1.0)


def _finite(name: str, value: Any, minimum: float, maximum: float) -> float:
    number = float(value)
    if not isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{name} must be finite and inside {minimum}..{maximum}")
    return number


def _color(name: str, value: Any) -> tuple[float, float, float, float]:
    components = tuple(float(item) for item in value)
    if len(components) not in (3, 4):
        raise ValueError(f"{name} must contain RGB or RGBA")
    if len(components) == 3:
        components += (1.0,)
    if any(not isfinite(item) or not 0.0 <= item <= 1.0 for item in components):
        raise ValueError(f"{name} components must be finite and inside 0..1")
    return components


@dataclass(frozen=True)
class MaterialSettings:
    speed: float = 1.0
    scale: float = 4.0
    width: float = 0.5
    focus_x: float = 0.5
    focus_y: float = 0.5
    zoom: float = 1.0
    gradient: str = "neon_cyan_magenta"
    color_a: tuple[float, float, float, float] = DEFAULT_COLOR_A
    color_b: tuple[float, float, float, float] = DEFAULT_COLOR_B
    coordinate_mode: str = "global"
    intensity: float = 1.0
    contrast: float = 1.25
    color_mode: str = "original"
    gradient_strength: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "speed", _finite("speed", self.speed, 0.0, 16.0))
        object.__setattr__(self, "scale", _finite("scale", self.scale, 0.01, 128.0))
        object.__setattr__(self, "width", _finite("width", self.width, 0.0, 1.0))
        object.__setattr__(self, "focus_x", _finite("focus_x", self.focus_x, 0.0, 1.0))
        object.__setattr__(self, "focus_y", _finite("focus_y", self.focus_y, 0.0, 1.0))
        object.__setattr__(self, "zoom", _finite("zoom", self.zoom, 0.25, 8.0))
        object.__setattr__(self, "intensity", _finite("intensity", self.intensity, 0.0, 2.0))
        object.__setattr__(self, "contrast", _finite("contrast", self.contrast, 0.1, 4.0))
        object.__setattr__(self, "gradient_strength", _finite("gradient_strength", self.gradient_strength, 0.0, 1.0))
        if self.color_mode not in ('original', 'gradient', 'legacy'):
            raise ValueError('color_mode must be original, gradient, or legacy')
        if not str(self.gradient).strip():
            raise ValueError("gradient must not be empty")
        object.__setattr__(self, "gradient", str(self.gradient))
        object.__setattr__(self, "color_a", _color("color_a", self.color_a))
        object.__setattr__(self, "color_b", _color("color_b", self.color_b))
        mode = "panel" if self.coordinate_mode == "panel_local" else str(self.coordinate_mode)
        if mode not in COORDINATE_MODES:
            raise ValueError("coordinate_mode must be global, panel, or hybrid")
        object.__setattr__(self, "coordinate_mode", mode)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> "MaterialSettings":
        values = dict(values)
        # Old projects always had duotone applied. Preserve that look rather
        # than silently switching existing shows to the new default.
        values.setdefault('color_mode', 'legacy')
        return cls(**values)


@dataclass(frozen=True)
class MaterialState:
    settings: MaterialSettings = MaterialSettings()
    phase: float = 0.0
    last_time: float | None = None

    def __post_init__(self) -> None:
        if not isfinite(float(self.phase)):
            raise ValueError("phase must be finite")
        if self.last_time is not None and not isfinite(float(self.last_time)):
            raise ValueError("last_time must be finite or None")

    def advanced(self, now: float, master_speed: float) -> "MaterialState":
        timestamp = _finite("now", now, -1.0e15, 1.0e15)
        master = _finite("global_master_speed", master_speed, 0.0, 16.0)
        if self.last_time is None:
            return replace(self, last_time=timestamp)
        elapsed = max(0.0, timestamp - self.last_time)
        return replace(
            self,
            phase=self.phase + elapsed * self.settings.speed * master,
            last_time=timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings": self.settings.to_dict(),
            "phase": float(self.phase),
            "last_time": self.last_time,
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> "MaterialState":
        return cls(
            settings=MaterialSettings.from_dict(values.get("settings", {})),
            phase=float(values.get("phase", 0.0)),
            last_time=values.get("last_time"),
        )


class MaterialStateStore:
    """Keep settings and a paused/resumable phase for every material key."""

    def __init__(self, *, global_master_speed: float = 1.0) -> None:
        self.global_master_speed = _finite(
            "global_master_speed", global_master_speed, 0.0, 16.0
        )
        self.active_key: str | None = None
        self._states: dict[str, MaterialState] = {}

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self._states)

    def state(self, key: str) -> MaterialState:
        return self._states[str(key)]

    def activate(
        self,
        key: str,
        now: float,
        *,
        initial: MaterialSettings | None = None,
    ) -> MaterialState:
        material_key = str(key).strip()
        if not material_key:
            raise ValueError("material key must not be empty")
        self.tick(now)
        self.active_key = material_key
        state = self._states.get(material_key)
        if state is None:
            state = MaterialState(initial or MaterialSettings(), last_time=float(now))
        else:
            state = replace(state, last_time=float(now))
        self._states[material_key] = state
        return state

    def tick(self, now: float) -> float:
        if self.active_key is None:
            return 0.0
        current = self._states[self.active_key].advanced(now, self.global_master_speed)
        self._states[self.active_key] = current
        return current.phase

    def set_active_settings(self, settings: MaterialSettings, now: float) -> MaterialState:
        if self.active_key is None:
            raise RuntimeError("No active material")
        self.tick(now)
        current = self._states[self.active_key]
        current = replace(current, settings=settings, last_time=float(now))
        self._states[self.active_key] = current
        return current

    def set_global_master_speed(self, value: float, now: float) -> float:
        # Advance with the previous multiplier first.  This is the same
        # continuity rule used for a material speed change.
        self.tick(now)
        self.global_master_speed = _finite("global_master_speed", value, 0.0, 16.0)
        return self.global_master_speed

    def phase_at(self, now: float) -> float:
        return self.tick(now)

    def rebase_active(self, now: float) -> MaterialState | None:
        """Move only the active clock anchor without advancing its phase.

        Persisted ``last_time`` values belong to the previous process/runtime.
        Reusing them after a reopen would count downtime as animation time.
        """

        timestamp = _finite("now", now, -1.0e15, 1.0e15)
        if self.active_key is None:
            return None
        current = replace(self._states[self.active_key], last_time=timestamp)
        self._states[self.active_key] = current
        return current

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": 1,
            "global_master_speed": self.global_master_speed,
            "active_key": self.active_key,
            "materials": {key: state.to_dict() for key, state in self._states.items()},
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> "MaterialStateStore":
        store = cls(global_master_speed=values.get("global_master_speed", 1.0))
        store._states = {
            str(key): MaterialState.from_dict(state)
            for key, state in dict(values.get("materials", {})).items()
        }
        active = values.get("active_key")
        store.active_key = str(active) if active in store._states else None
        return store
