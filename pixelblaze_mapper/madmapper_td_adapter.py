"""Prepare a conservative subset of MadMapper materials for TouchDesigner.

The catalog intentionally contains every discovered material.  This adapter is
the second safety gate: it only emits a GLSL TOP fragment shader when the
MadMapper source can be represented without hidden surface state, feedback,
audio, or texture wiring.  Unsupported materials still keep their thumbnail
and metadata in the browser.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


_HEADER_RE = re.compile(r"/\*\s*(\{.*?\})\s*\*/", re.DOTALL)
_INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]\s*$', re.MULTILINE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
_VARYING_RE = re.compile(r"^\s*(?:flat\s+)?in\s+[^;]+;", re.MULTILINE)
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_TEXTURE_INPUTS = {"image", "audio", "audiofft", "2d", "3d", "cube"}
_SUPPORTED_GENERATORS = {"time_base"}


@dataclass(frozen=True)
class AdaptationResult:
    status: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    shader: str | None
    metadata: Mapping[str, Any]

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


def _input_definitions(metadata: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    definitions: list[str] = []
    reasons: list[str] = []
    for item in _items(metadata, "INPUTS"):
        name = str(item.get("NAME", "")).strip()
        kind = str(item.get("TYPE", "float")).lower()
        if not _SAFE_IDENTIFIER_RE.match(name):
            reasons.append("invalid input identifier: %s" % (name or "<empty>"))
            continue
        if kind in _TEXTURE_INPUTS:
            reasons.append("requires %s input: %s" % (kind, name))
            continue
        default = item.get("DEFAULT", 0.0)
        flags = str(item.get("FLAGS", "")).lower()
        if kind == "float":
            definitions.append("const float %s = %s;" % (name, _glsl_number(default)))
        elif kind in {"int", "event"}:
            definitions.append("const int %s = %s;" % (name, _glsl_number(default, integer=True)))
        elif kind == "bool":
            truth = bool(default) and str(default).lower() not in {"0", "false", "none"}
            definitions.append("const bool %s = %s;" % (name, "true" if truth else "false"))
            if "generate_as_define" in flags:
                definitions.append("#define %s_IS_%s" % (name, "true" if truth else "false"))
        elif kind == "long":
            values = item.get("VALUES", [])
            if isinstance(default, str) and isinstance(values, list) and default in values:
                index = values.index(default)
                selected = default
            else:
                index = int(default) if isinstance(default, (int, float)) else 0
                selected = values[index] if isinstance(values, list) and 0 <= index < len(values) else index
            definitions.append("const int %s = %d;" % (name, index))
            if "generate_as_define" in flags:
                definitions.append("#define %s_IS_%s" % (name, _symbol(selected)))
        elif kind in {"point2d", "size2d", "floatrange"}:
            definitions.append("const vec2 %s = %s;" % (name, _glsl_vector(default, 2)))
        elif kind == "color":
            definitions.append("const vec4 %s = %s;" % (name, _glsl_vector(default, 4)))
        else:
            reasons.append("unsupported input type %s: %s" % (kind, name))
    return definitions, reasons


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


def adapt_material(shader_path: str | Path, library_roots: Iterable[str | Path] = ()) -> AdaptationResult:
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

    input_defs, input_reasons = _input_definitions(metadata)
    generator_defs, generator_reasons, generator_warnings = _generator_definitions(metadata)
    reasons.extend(input_reasons)
    reasons.extend(generator_reasons)
    warnings.extend(generator_warnings)

    body = _HEADER_RE.sub("", source, count=1)
    body = re.sub(r"^\s*#version[^\n]*$", "", body, flags=re.MULTILINE)
    body, include_reasons = _inline_includes(body, path.parent, [Path(item) for item in library_roots], {path})
    reasons.extend(include_reasons)

    if reasons:
        return AdaptationResult("unsupported", tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(warnings)), None, metadata)

    prelude = """// Prepared from a MadMapper material for TouchDesigner GLSL TOP.
out vec4 fragColor;
uniform float uTDTime;
uniform vec4 uTDCoordinate; // mode, panel columns, panel rows, hybrid mix
#define TIME uTDTime
#define TIMEDELTA (1.0 / 60.0)
#define FRAMEINDEX int(uTDTime * 60.0)
#define RENDERSIZE vec2(512.0, 512.0)
#define DATE vec4(0.0)

vec2 mapMadMapperUV(vec2 uv)
{
    // True global/panel-local/hybrid selection happens in the downstream
    // per-LED sampler, where the physical panel ID is available.
    return uv;
}
"""
    prepared = "\n".join([prelude, *input_defs, *generator_defs, body, """
void main()
{
    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
"""])
    return AdaptationResult("adaptable", (), tuple(dict.fromkeys(warnings)), prepared, metadata)


def write_prepared_shader(result: AdaptationResult, destination: str | Path) -> Path:
    if not result.adaptable or result.shader is None:
        raise ValueError("material is not adaptable: %s" % "; ".join(result.reasons))
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result.shader, encoding="utf-8", newline="\n")
    return target
