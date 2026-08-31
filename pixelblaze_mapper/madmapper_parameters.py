"""Pure MadMapper INPUT schema and value coercion.

MadMapper materials describe their own controls in the JSON header.  This
module preserves declaration order and slash-separated label groups so a
TouchDesigner UI can be generated per imported material instead of pretending
that every shader has the same handful of parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import re
from typing import Any, Mapping


SUPPORTED_TYPES = frozenset(
    {"float", "int", "bool", "event", "long", "point2d", "size2d", "floatrange", "color"}
)
VECTOR_TYPES = frozenset({"point2d", "size2d", "floatrange", "color"})
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _field(item: Mapping[str, Any], name: str, default: Any = None) -> Any:
    target = name.casefold()
    for key, value in item.items():
        if str(key).casefold() == target:
            return value
    return default


def _flags(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        raw = re.split(r"[,;]", value)
    elif isinstance(value, (list, tuple)):
        raw = value
    else:
        raw = ()
    return tuple(dict.fromkeys(str(item).strip().casefold() for item in raw if str(item).strip()))


@dataclass(frozen=True)
class MaterialParameter:
    index: int
    name: str
    label: str
    groups: tuple[str, ...]
    kind: str
    default: Any
    minimum: Any
    maximum: Any
    values: tuple[str, ...]
    flags: tuple[str, ...]

    @property
    def uniform(self) -> str:
        return "uMMParam%03d" % self.index

    @property
    def compile_time(self) -> bool:
        return "generate_as_define" in self.flags

    @property
    def components(self) -> int:
        if self.kind == "color":
            return 4
        if self.kind in {"point2d", "size2d", "floatrange"}:
            return 2
        return 1

    @property
    def display_label(self) -> str:
        return self.label.split("/")[-1].strip() or self.name

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "label": self.label,
            "display_label": self.display_label,
            "groups": list(self.groups),
            "type": self.kind,
            "default": self.default,
            "min": self.minimum,
            "max": self.maximum,
            "values": list(self.values),
            "flags": list(self.flags),
            "uniform": self.uniform,
            "compile_time": self.compile_time,
            "components": self.components,
        }


def parameter_schema(metadata: Mapping[str, Any]) -> tuple[MaterialParameter, ...]:
    raw = metadata.get("INPUTS", []) if isinstance(metadata, Mapping) else []
    if not isinstance(raw, list):
        return ()
    result: list[MaterialParameter] = []
    names: set[str] = set()
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        name = str(_field(item, "NAME", "")).strip()
        kind = str(_field(item, "TYPE", "float")).strip().casefold()
        if not _IDENTIFIER.fullmatch(name) or name in names or kind not in SUPPORTED_TYPES:
            continue
        names.add(name)
        label = str(_field(item, "LABEL", name)).strip() or name
        parts = tuple(part.strip() for part in label.split("/") if part.strip())
        values = _field(item, "VALUES", ())
        values = tuple(str(value) for value in values) if isinstance(values, (list, tuple)) else ()
        default = _field(item, "DEFAULT", None)
        if default is None:
            default = False if kind == "bool" else (0 if kind in {"int", "event", "long"} else 0.0)
        if kind == "long" and isinstance(default, str):
            default = values.index(default) if default in values else 0
        result.append(
            MaterialParameter(
                index=len(result),
                name=name,
                label=label,
                groups=parts[:-1],
                kind=kind,
                default=default,
                minimum=_field(item, "MIN", None),
                maximum=_field(item, "MAX", None),
                values=values,
                flags=_flags(_field(item, "FLAGS", "")),
            )
        )
    return tuple(result)


def _finite(value: Any, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    return number if isfinite(number) else float(fallback)


def _bounds(parameter: MaterialParameter, component: int) -> tuple[float | None, float | None]:
    def component_value(value: Any) -> float | None:
        if isinstance(value, (list, tuple)):
            value = value[component] if component < len(value) else None
        if value is None:
            return None
        number = _finite(value, 0.0)
        return number

    return component_value(parameter.minimum), component_value(parameter.maximum)


def coerce_value(parameter: MaterialParameter, value: Any) -> Any:
    if parameter.components > 1:
        raw = list(value) if isinstance(value, (list, tuple)) else []
        default = list(parameter.default) if isinstance(parameter.default, (list, tuple)) else []
        size = parameter.components
        values: list[float] = []
        for index in range(size):
            fallback = default[index] if index < len(default) else (1.0 if parameter.kind == "color" and index == 3 else 0.0)
            number = _finite(raw[index] if index < len(raw) else fallback, fallback)
            low, high = _bounds(parameter, index)
            if parameter.kind == "color":
                low, high = 0.0, 1.0
            if low is not None:
                number = max(low, number)
            if high is not None:
                number = min(high, number)
            values.append(number)
        return tuple(values)
    if parameter.kind == "bool":
        return bool(value) and str(value).casefold() not in {"0", "false", "none", "off"}
    if parameter.kind in {"int", "event", "long"}:
        number = int(round(_finite(value, parameter.default or 0)))
        if parameter.kind == "long" and parameter.values:
            number = max(0, min(len(parameter.values) - 1, number))
        low, high = _bounds(parameter, 0)
        if low is not None:
            number = max(int(low), number)
        if high is not None:
            number = min(int(high), number)
        return number
    number = _finite(value, parameter.default or 0.0)
    low, high = _bounds(parameter, 0)
    if low is not None:
        number = max(low, number)
    if high is not None:
        number = min(high, number)
    return number


def default_values(schema: tuple[MaterialParameter, ...]) -> dict[str, Any]:
    return {parameter.name: coerce_value(parameter, parameter.default) for parameter in schema}


def uniform_vector(parameter: MaterialParameter, value: Any) -> tuple[float, float, float, float]:
    value = coerce_value(parameter, value)
    if isinstance(value, tuple):
        result = list(value)
    else:
        result = [1.0 if value is True else 0.0 if value is False else float(value)]
    result.extend([0.0] * (4 - len(result)))
    return tuple(float(item) for item in result[:4])


__all__ = [
    "MaterialParameter", "SUPPORTED_TYPES", "VECTOR_TYPES", "coerce_value",
    "default_values", "parameter_schema", "uniform_vector",
]
