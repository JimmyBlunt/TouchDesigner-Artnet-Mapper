"""Prepare a conservative subset of MadMapper materials for TouchDesigner.

The catalog intentionally contains every discovered material.  This adapter is
the second safety gate: it only emits a GLSL TOP fragment shader when the
MadMapper source can be represented without hidden surface state, feedback,
audio, or texture wiring.  Unsupported materials still keep their thumbnail
and metadata in the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from pixelblaze_mapper.madmapper_parameters import (
    MaterialParameter,
    SUPPORTED_TYPES,
    coerce_value,
    parameter_schema,
)


_HEADER_RE = re.compile(r"/\*\s*(\{.*?\})\s*\*/", re.DOTALL)
_INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]\s*$', re.MULTILINE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
_VARYING_RE = re.compile(r"^\s*(?:flat\s+)?in\s+[^;]+;", re.MULTILINE)
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_TEXTURE_INPUTS = {"image", "audio", "audiofft", "2d", "3d", "cube"}
_SUPPORTED_GENERATORS = {"time_base"}
ADAPTER_VERSION = 3
ADAPTER_MARKER = "// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION %d" % ADAPTER_VERSION


@dataclass(frozen=True)
class AdaptationResult:
    status: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    shader: str | None
    metadata: Mapping[str, Any]
    schema: tuple[MaterialParameter, ...] = ()
    bindings: Mapping[str, str] = field(default_factory=dict)

    @property
    def adaptable(self) -> bool:
        return self.status == "adaptable" and self.shader is not None


def _metadata_from_source(source: str) -> dict[str, Any]:
    # Use the catalogue's relaxed MadMapper parser first so catalogue and
    # adapter make the same decision for headers containing values such as
    # ``360.`` and trailing commas.  Keep the small strict fallback for using
    # this module independently.
    try:
        from pixelblaze_mapper.material_library import extract_isf_metadata

        relaxed = extract_isf_metadata(source)
        if relaxed:
            return relaxed
    except (ImportError, ValueError):
        pass
    match = _HEADER_RE.search(source)
    if not match:
        return {}
    candidate = _TRAILING_COMMA_RE.sub(r"\1", match.group(1))
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _items(metadata: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = metadata.get(key, [])
    if isinstance(value, dict):
        value = [dict({"NAME": name}, **entry) for name, entry in value.items() if isinstance(entry, dict)]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _glsl_number(value: Any, *, integer: bool = False) -> str:
    try:
        number = int(value) if integer else float(value)
    except (TypeError, ValueError):
        number = 0 if integer else 0.0
    if integer:
        return str(number)
    rendered = format(number, ".12g")
    return rendered if any(character in rendered for character in ".eE") else rendered + ".0"


def _glsl_vector(value: Any, size: int) -> str:
    values = list(value) if isinstance(value, (list, tuple)) else []
    values = (values + [0.0] * size)[:size]
    return "vec%d(%s)" % (size, ", ".join(_glsl_number(item) for item in values))


def _symbol(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value).strip())
    text = text.strip("_") or "Value"
    return text if not text[0].isdigit() else "_" + text


def _selected_input_value(parameter: MaterialParameter, input_values: Mapping[str, Any]) -> Any:
    value = input_values.get(parameter.name, parameter.default)
    if parameter.kind == "long" and isinstance(value, str):
        value = parameter.values.index(value) if value in parameter.values else parameter.default
    return coerce_value(parameter, value)


def _compile_time_input_definitions(parameter: MaterialParameter, value: Any) -> list[str]:
    name = parameter.name
    kind = parameter.kind
    if kind == "float":
        return ["const float %s = %s;" % (name, _glsl_number(value))]
    if kind in {"int", "event"}:
        return ["const int %s = %s;" % (name, _glsl_number(value, integer=True))]
    if kind == "bool":
        truth = bool(value)
        return [
            "const bool %s = %s;" % (name, "true" if truth else "false"),
            "#define %s_IS_%s" % (name, "true" if truth else "false"),
        ]
    if kind == "long":
        index = int(value)
        selected = parameter.values[index] if 0 <= index < len(parameter.values) else index
        return [
            "const int %s = %d;" % (name, index),
            "#define %s_IS_%s" % (name, _symbol(selected)),
        ]
    if kind in {"point2d", "size2d", "floatrange"}:
        return ["const vec2 %s = %s;" % (name, _glsl_vector(value, 2))]
    if kind == "color":
        return ["const vec4 %s = %s;" % (name, _glsl_vector(value, 4))]
    return []


def _runtime_input_definitions(parameter: MaterialParameter) -> list[str]:
    name = parameter.name
    uniform = parameter.uniform
    kind = parameter.kind
    definitions = ["uniform vec4 %s; // native input: %s" % (uniform, name)]
    if kind == "float":
        expression = "%s.x" % uniform
    elif kind in {"int", "event", "long"}:
        expression = "int(round(%s.x))" % uniform
    elif kind == "bool":
        expression = "%s.x > 0.5" % uniform
    elif kind in {"point2d", "size2d", "floatrange"}:
        expression = "%s.xy" % uniform
    elif kind == "color":
        expression = uniform
    else:  # pragma: no cover - guarded by parameter_schema
        return []
    definitions.append("#define %s (%s)" % (name, expression))
    return definitions


def _input_definitions(
    metadata: Mapping[str, Any], input_values: Mapping[str, Any] | None = None
) -> tuple[list[str], list[str], tuple[MaterialParameter, ...], dict[str, str]]:
    definitions: list[str] = []
    reasons: list[str] = []
    values = input_values if isinstance(input_values, Mapping) else {}
    schema = parameter_schema(metadata)

    # Retain the adapter safety gate for inputs which the pure schema parser
    # deliberately omits.  This keeps texture/audio requirements visible as
    # explicit unsupported reasons instead of silently dropping them.
    for item in _items(metadata, "INPUTS"):
        name = str(item.get("NAME", "")).strip()
        kind = str(item.get("TYPE", "float")).lower()
        if not _SAFE_IDENTIFIER_RE.match(name):
            reasons.append("invalid input identifier: %s" % (name or "<empty>"))
            continue
        if kind in _TEXTURE_INPUTS:
            reasons.append("requires %s input: %s" % (kind, name))
            continue
        if kind not in SUPPORTED_TYPES:
            reasons.append("unsupported input type %s: %s" % (kind, name))

    bindings: dict[str, str] = {}
    for parameter in schema:
        if parameter.compile_time:
            definitions.extend(
                _compile_time_input_definitions(
                    parameter, _selected_input_value(parameter, values)
                )
            )
        else:
            definitions.extend(_runtime_input_definitions(parameter))
            bindings[parameter.name] = parameter.uniform
    return definitions, reasons, schema, bindings


def _generator_definitions(metadata: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    definitions: list[str] = []
    reasons: list[str] = []
    warnings: list[str] = []
    for generator in _items(metadata, "GENERATORS"):
        name = str(generator.get("NAME", "")).strip()
        kind = str(generator.get("TYPE", "")).lower()
        if not _SAFE_IDENTIFIER_RE.match(name):
            reasons.append("invalid generator identifier: %s" % (name or "<empty>"))
            continue
        if kind not in _SUPPORTED_GENERATORS:
            reasons.append("unsupported generator: %s" % kind)
            continue
        params = generator.get("PARAMS", {})
        params = params if isinstance(params, dict) else {}
        speed = params.get("speed", 1.0)
        speed_expr = speed if isinstance(speed, str) and _SAFE_IDENTIFIER_RE.match(speed) else _glsl_number(speed)
        definitions.append("#define %s (uTDTime * (%s))" % (name, speed_expr))
        if any(key in params for key in ("bpm_sync", "strob", "speed_curve", "link_speed_to_global_bpm")):
            warnings.append("%s uses simplified TouchDesigner time-base semantics" % name)
    return definitions, reasons, warnings


def _resolve_include(name: str, parent: Path, library_roots: Iterable[Path]) -> Path | None:
    candidates = [parent / name]
    for root in library_roots:
        root = Path(root)
        candidates.extend((root / name, root / "Libraries" / name))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _inline_includes(source: str, parent: Path, library_roots: Iterable[Path], seen: set[Path]) -> tuple[str, list[str]]:
    reasons: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        resolved = _resolve_include(name, parent, library_roots)
        if resolved is None:
            reasons.append("missing include: %s" % name)
            return ""
        if resolved in seen:
            return "// include already expanded: %s" % name
        seen.add(resolved)
        nested, nested_reasons = _inline_includes(resolved.read_text(encoding="utf-8-sig"), resolved.parent, library_roots, seen)
        reasons.extend(nested_reasons)
        return "\n// BEGIN %s\n%s\n// END %s\n" % (name, nested, name)

    return _INCLUDE_RE.sub(replace, source), reasons


def adapt_material(
    shader_path: str | Path,
    library_roots: Iterable[str | Path] = (),
    input_values: Mapping[str, Any] | None = None,
) -> AdaptationResult:
    path = Path(shader_path).resolve()
    source = path.read_text(encoding="utf-8-sig")
    metadata = _metadata_from_source(source)
    reasons: list[str] = []
    warnings: list[str] = []

    if path.suffix.lower() != ".fs":
        reasons.append("source is not a MadMapper .fs fragment shader")
    if not re.search(r"\bvec4\s+materialColorForPixel\s*\(", source):
        reasons.append("materialColorForPixel function is missing")
    if any(path.parent.glob("*.vs")):
        reasons.append("requires a MadMapper vertex shader")
    if _VARYING_RE.search(_HEADER_RE.sub("", source)):
        reasons.append("requires MadMapper-specific vertex/surface varyings")
    if "SURFACE_IS_" in source:
        reasons.append("uses MadMapper surface-specific branches")
    if "gl_FragColor" in source:
        reasons.append("writes gl_FragColor outside the material return contract")

    raster = metadata.get("RASTERISATION_SETTINGS", {})
    if isinstance(raster, dict) and raster.get("REQUIRES_LAST_FRAME"):
        reasons.append("requires previous-frame feedback")
    if _items(metadata, "IMPORTED"):
        reasons.append("requires imported textures")

    input_defs, input_reasons, schema, bindings = _input_definitions(metadata, input_values)
    generator_defs, generator_reasons, generator_warnings = _generator_definitions(metadata)
    reasons.extend(input_reasons)
    reasons.extend(generator_reasons)
    warnings.extend(generator_warnings)

    body = _HEADER_RE.sub("", source, count=1)
    body = re.sub(r"^\s*#version[^\n]*$", "", body, flags=re.MULTILINE)
    body, include_reasons = _inline_includes(body, path.parent, [Path(item) for item in library_roots], {path})
    reasons.extend(include_reasons)

    if reasons:
        return AdaptationResult(
            "unsupported", tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(warnings)),
            None, metadata, schema, bindings,
        )

    prelude = """%s
// Prepared from a MadMapper material for TouchDesigner GLSL TOP.
out vec4 fragColor;
uniform vec4 uTDMaterial0; // phase, scale, width, frame zoom
uniform vec4 uTDMaterial1; // focus x, focus y, reserved, reserved
uniform vec4 uTDCoordinate; // mode, panel columns, panel rows, hybrid mix
#define uTDTime uTDMaterial0.x
#define TIME uTDTime
#define TIMEDELTA (1.0 / 60.0)
#define FRAMEINDEX int(uTDTime * 60.0)
#define RENDERSIZE vec2(512.0, 512.0)
#define DATE vec4(0.0)

vec2 mapMadMapperUV(vec2 uv)
{
    vec2 focus = clamp(uTDMaterial1.xy, vec2(0.0), vec2(1.0));
    float zoom = clamp(uTDMaterial0.w, 0.25, 8.0);
    float scale = max(uTDMaterial0.y, 0.01) / 4.0;
    float width = clamp(uTDMaterial0.z, 0.01, 1.0);
    vec2 framed = focus + (uv - vec2(0.5)) / zoom;
    framed = focus + (framed - focus) * vec2(scale * (0.5 / width), scale);
    // True global/panel-local/hybrid selection happens in the downstream
    // per-LED sampler, where the physical panel ID is available.
    return framed;
}
""" % ADAPTER_MARKER
    prepared = "\n".join([prelude, *input_defs, *generator_defs, body, """
void main()
{
    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
"""])
    return AdaptationResult(
        "adaptable", (), tuple(dict.fromkeys(warnings)), prepared, metadata,
        schema, bindings,
    )


def prepared_shader_is_current(source: str) -> bool:
    """Return whether a prepared shader uses the current live-control contract."""

    return ADAPTER_MARKER in str(source)


def write_prepared_shader(result: AdaptationResult, destination: str | Path) -> Path:
    if not result.adaptable or result.shader is None:
        raise ValueError("material is not adaptable: %s" % "; ".join(result.reasons))
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result.shader, encoding="utf-8", newline="\n")
    return target
