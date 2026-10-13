"""Exact, stateless MadMapper generator translations.

Source: MadMapper-Materials/MaterialsDoc.md at d7ff211281f1878feeccd8ead05ce855c0eac5ee,
sections Pass Thru and Multiplier (lines 299-315 and 386-401).
https://github.com/madmappersoftware/MadMapper-Materials/blob/d7ff211281f1878feeccd8ead05ce855c0eac5ee/MaterialsDoc.md

This deliberately does not approximate generators with temporal state. Input
identifiers refer to scalar inputs or other generator outputs; the caller must
resolve their dependencies and place definitions in dependency order. Channel
URLs require an explicit mapping to a real scalar uniform, never a placeholder.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any


SUPPORTED_STATELESS_GENERATORS = frozenset({"pass_thru", "multiplier"})
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_RESERVED = frozenset({"true", "false", "float", "int", "uint", "bool", "void", "if", "else", "for", "while", "return", "uniform", "in", "out", "inout", "const", "struct", "break", "continue", "discard"})


def _identifier(value: Any) -> bool:
    return (isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))
            and not value.startswith("gl_") and "__" not in value
            and value not in _RESERVED)


def _scalar(value: Any, name: str, channels: Mapping[str, str]) -> str:
    if isinstance(value, str):
        if value.startswith("/"):
            if value not in channels:
                raise ValueError("requires external channel: %s" % value)
            value = channels[value]
            if not _identifier(value):
                raise ValueError("invalid channel binding: %s" % value)
        if not _identifier(value):
            raise ValueError("invalid scalar reference: %s" % value)
        if value == name:
            raise ValueError("self-referencing generator: %s" % name)
        # Generator outputs are floats; explicit conversion also supports scalar
        # integer/event and boolean inputs without implicit GLSL conversions.
        return "float(%s)" % value
    if isinstance(value, (int, float)):
        try:
            number = float(value)
        except (ValueError, OverflowError):
            raise ValueError("non-finite generator value") from None
        if not math.isfinite(number):
            raise ValueError("non-finite generator value")
        text = format(number, ".17g")
        if "." not in text and "e" not in text.lower():
            text += ".0"
        return text
    raise ValueError("generator value must be a scalar number or reference")


def generator_expression(
    generator: Mapping[str, Any], *, channel_bindings: Mapping[str, str] | None = None
) -> tuple[list[str], list[str], list[str]]:
    """Return (GLSL definitions, blocking reasons, warnings).

    Only exact stateless semantics are accepted. Bindings map full external
    channel URLs to *existing* scalar GLSL uniforms; providing the uniform and
    updating it from the actual channel remains the caller's responsibility.
    Unknown parameters are rejected rather than silently discarded.
    """
    if not isinstance(generator, Mapping):
        return [], ["invalid generator declaration"], []
    name = generator.get("NAME")
    if not _identifier(name):
        return [], ["invalid generator identifier: %s" % (name or "<empty>")], []
    kind = str(generator.get("TYPE", "")).lower()
    if kind not in SUPPORTED_STATELESS_GENERATORS:
        return [], ["unsupported stateless generator: %s" % kind], []
    if "FILTERS" in generator:
        return [], ["unsupported generator FILTERS: %s" % name], []
    params = generator.get("PARAMS", {})
    if not isinstance(params, Mapping):
        return [], ["invalid generator parameters: %s" % name], []
    allowed = {"input_value"} if kind == "pass_thru" else {"value1", "value2", "value3", "value4"}
    unknown = set(params) - allowed
    if unknown:
        return [], ["unsupported generator parameters: %s" % ", ".join(sorted(map(str, unknown)))], []
    if kind == "pass_thru" and "input_value" not in params:
        # The documentation does not establish an omitted-input default.
        return [], ["missing pass_thru input_value: %s" % name], []
    try:
        channels = channel_bindings or {}
        if kind == "pass_thru":
            expression = _scalar(params["input_value"], name, channels)
        else:
            expression = " * ".join("(%s)" % _scalar(params.get("value%d" % i, 1), name, channels) for i in range(1, 5))
    except ValueError as exc:
        return [], [str(exc)], []
    return ["float %s = %s;" % (name, expression)], [], []
