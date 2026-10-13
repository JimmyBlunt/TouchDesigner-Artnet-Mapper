"""Prepare a conservative subset of MadMapper materials for TouchDesigner.

The catalog intentionally contains every discovered material.  This adapter is
the second safety gate: it only emits a GLSL TOP fragment shader when the
MadMapper source can be represented without hidden surface state, feedback,
audio, or unsupported texture types. Resolved image assets are exposed for
runtime wiring. Unsupported materials still keep their thumbnail
and metadata in the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from pixelblaze_mapper.madmapper_parameters import (
    MaterialParameter,
    SUPPORTED_TYPES,
    coerce_value,
    parameter_schema,
)
from pixelblaze_mapper.material_generator_glsl import (
    SUPPORTED_STATELESS_GENERATORS, generator_expression,
)
from pixelblaze_mapper.material_shader_repairs import repair_source


_HEADER_RE = re.compile(r"/\*\s*(\{.*?\})\s*\*/", re.DOTALL)
_INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]\s*$', re.MULTILINE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
# Match interface declarations, not `in vec3 color, in float distance` in
# function parameter lists. The old semicolon scan crossed whole functions.
_INTERFACE_RE = re.compile(
    r'^[ \t]*(?:(?:flat|smooth|noperspective|centroid|sample)\s+)*'
    r'(?P<direction>in|out)\s+(?:(?:lowp|mediump|highp)\s+)?'
    r'(?P<type>[A-Za-z_]\w*)\s+(?P<name>[A-Za-z_]\w*)'
    r'(?P<array>\s*\[[^\]\r\n]*\])?\s*;', re.MULTILINE)
_VARYING_RE = re.compile(
    r'^[ \t]*(?:layout\s*\([^\r\n)]*\)\s*)?'
    r'(?:(?:flat|smooth|noperspective|centroid|sample)\s+)*in\s+'
    r'(?:(?:lowp|mediump|highp)\s+)?[A-Za-z_]\w*\s+'
    r'(?:\{|[A-Za-z_]\w*(?:\s*\[[^\]\r\n]*\])?'
    r'(?:\s*,\s*[A-Za-z_]\w*(?:\s*\[[^\]\r\n]*\])?)*\s*;)', re.MULTILINE)
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_TEXTURE_INPUTS = {"image", "audio", "audiofft", "2d", "3d", "cube"}
_SUPPORTED_GENERATORS = {"time_base"} | SUPPORTED_STATELESS_GENERATORS
ADAPTER_VERSION = 6
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
    textures: tuple[Mapping[str, Any], ...] = ()

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
    glsl_type = {'float':'float', 'int':'int', 'event':'int', 'long':'int',
                 'bool':'bool', 'point2d':'vec2', 'size2d':'vec2',
                 'floatrange':'vec2', 'color':'vec4'}[kind]
    # Variables permit normal lexical shadowing in library function arguments
    # and material locals. Macros corrupted declarations such as float speed.
    definitions.append("%s %s = %s;" % (glsl_type, name, expression))
    return definitions


def _input_definitions(
    metadata: Mapping[str, Any], input_values: Mapping[str, Any] | None = None,
    resolved_texture_inputs: frozenset[str] = frozenset(),
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
            if name not in resolved_texture_inputs:
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
    generators = _items(metadata, "GENERATORS")
    names = {str(g.get('NAME','')) for g in generators}
    scalar_inputs = {p.name for p in parameter_schema(metadata)
                     if p.kind in {'float','int','long','event','bool'}}
    nodes: dict[str, tuple[list[str], list[str]]] = {}
    for generator in generators:
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
        if name in nodes:
            reasons.append('duplicate generator identifier: ' + name)
            continue
        if kind in SUPPORTED_STATELESS_GENERATORS:
            generated, errors, notes = generator_expression(generator)
            reasons.extend(errors)
            warnings.extend(notes)
            references = [v for v in params.values() if isinstance(v,str) and _SAFE_IDENTIFIER_RE.fullmatch(v)]
            for reference in references:
                if reference not in scalar_inputs and reference not in names:
                    reasons.append('generator requires scalar input or generator: '+reference)
            nodes[name] = (generated, [v for v in references if v in names])
            continue
        speed = params.get("speed", 1.0)
        speed_expr = speed if isinstance(speed, str) and _SAFE_IDENTIFIER_RE.match(speed) else _glsl_number(speed)
        nodes[name] = (["float %s = uTDTime * (%s);" % (name, speed_expr)],
                       [speed] if isinstance(speed,str) and speed in names else [])
        if any(key in params for key in ("bpm_sync", "strob", "speed_curve", "link_speed_to_global_bpm")):
            warnings.append("%s uses simplified TouchDesigner time-base semantics" % name)
    complete, visiting = set(), set()
    def emit(name: str) -> None:
        if name in complete or name not in nodes:
            return
        if name in visiting:
            reasons.append('cyclic generator dependency: ' + name)
            return
        visiting.add(name)
        generated, dependencies = nodes[name]
        for dependency in dependencies:
            emit(dependency)
        visiting.remove(name)
        complete.add(name)
        definitions.extend(generated)
    for name in nodes:
        emit(name)
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


def _without_comments(source: str) -> str:
    return re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:'\n'*m.group().count('\n'),source,flags=re.DOTALL)


def _audio_texture_path() -> str | None:
    """Resolve only an explicitly configured, existing audio source."""
    from pixelblaze_mapper.material_audio_runtime import configured_audio_path
    return configured_audio_path()


def _uniform_vertex_source(path: Path, fragment: str, metadata: Mapping[str,Any],
                           roots: Iterable[Path]) -> tuple[str, dict[str,Any], str, str | None]:
    """Inline only a provably vertex-independent companion stage.

    An output calculated entirely from uniforms is identical at every vertex,
    hence also after interpolation. Running that unchanged calculation once
    per fragment preserves it. Coordinate-dependent vertex calculations,
    unknown interfaces and actual vertex builtins remain unsupported.
    """
    companions = list(path.parent.glob('*.vs'))
    if not companions:
        return fragment,dict(metadata),'',None
    if len(companions)!=1:
        return fragment,dict(metadata),'','requires a MadMapper vertex shader'
    vertex_path=companions[0]
    raw=vertex_path.read_text(encoding='utf-8-sig')
    vertex_meta=_metadata_from_source(raw)
    merged=dict(metadata)
    if vertex_meta:
        for key in ('INPUTS','GENERATORS','IMPORTED','RASTERISATION_SETTINGS'):
            if key in merged and key in vertex_meta and merged[key]!=vertex_meta[key]:
                return fragment,merged,'','conflicting fragment/vertex metadata: '+key
        merged=dict(vertex_meta,**merged)
    vertex=_without_comments(raw)
    expanded,errors=_inline_includes(vertex,vertex_path.parent,roots,{vertex_path.resolve()})
    signature=re.search(r'\bvoid\s+materialVsFunc\s*\(([^)]*)\)',vertex)
    if errors or not signature or len(re.findall(r'\bvoid\s+materialVsFunc\s*\(',vertex))!=1:
        return fragment,merged,'','requires a MadMapper vertex shader'
    arguments=[arg.strip() for arg in signature[1].split(',') if arg.strip()]
    names=[]
    for argument in arguments:
        match=re.fullmatch(r'(?:in\s+)?vec2\s+([A-Za-z_]\w*)',argument)
        if not match:
            return fragment,merged,'','requires a MadMapper vertex shader'
        names.append(match[1])
    checked = _without_comments(expanded)
    # Included library functions may have their own unrelated `uv` arguments.
    # Inspect the actual entry body and all macro definitions, where a vertex
    # argument can be substituted, without conflating those lexical scopes.
    entry = re.search(r'\bvoid\s+materialVsFunc\s*\([^)]*\)\s*\{', checked)
    if entry is None:
        return fragment,merged,'','requires a MadMapper vertex shader'
    depth,end = 1,entry.end()
    while end<len(checked) and depth:
        depth += (checked[end]=='{')-(checked[end]=='}')
        end += 1
    if depth:
        return fragment,merged,'','requires a MadMapper vertex shader'
    entry_body = checked[entry.end():end]
    directives = '\n'.join(re.findall(r'^\s*#[^\n]*',checked.replace('\\\n',''),re.MULTILINE))
    if any(len(re.findall(r'\b'+re.escape(name)+r'\b',vertex))!=1 or
           re.search(r'\b'+re.escape(name)+r'\b',entry_body+'\n'+directives) for name in names):
        return fragment,merged,'','requires a MadMapper vertex shader'
    if re.search(r'\b(?:gl_\w+|SURFACE_IS_\w+)\b',_without_comments(expanded)):
        return fragment,merged,'','requires a MadMapper vertex shader'
    if _VARYING_RE.search(vertex):
        return fragment,merged,'','requires a MadMapper vertex shader'
    outputs={match['name']:match for match in _INTERFACE_RE.finditer(vertex) if match['direction']=='out'}
    inputs=[match for match in _INTERFACE_RE.finditer(fragment) if match['direction']=='in']
    for item in inputs:
        counterpart=outputs.get(item['name'])
        if counterpart is None or counterpart['type']!=item['type'] or re.sub(r'\s+','',counterpart['array'] or '')!=re.sub(r'\s+','',item['array'] or ''):
            return fragment,merged,'','requires MadMapper-specific vertex/surface varyings'
    # Remove only matched interface declarations; unrelated `in` qualifiers in
    # function arguments and unmatched/complex interfaces are never stripped.
    fragment=_INTERFACE_RE.sub(lambda m:'' if m['direction']=='in' and m['name'] in outputs else m.group(),fragment)
    vertex=_INTERFACE_RE.sub(lambda m:('%s %s%s;'%(m['type'],m['name'],m['array'] or '')) if m['direction']=='out' else m.group(),vertex)
    call='    materialVsFunc(%s);\n'%(', '.join('vec2(0.0)' for _ in names))
    return vertex+'\n'+fragment,merged,call,None


def adapt_material(
    shader_path: str | Path,
    library_roots: Iterable[str | Path] = (),
    input_values: Mapping[str, Any] | None = None,
) -> AdaptationResult:
    path = Path(shader_path).resolve()
    library_roots = tuple(Path(root) for root in library_roots)
    source = path.read_text(encoding="utf-8-sig")
    source, source_repair_warnings = repair_source(path, source)
    metadata = _metadata_from_source(source)
    source,metadata,vertex_call,vertex_reason = _uniform_vertex_source(
        path,_without_comments(source),metadata,library_roots)
    if path.parent.name == '[recode]_Albers':
        for generator in _items(metadata, 'GENERATORS'):
            if generator.get('NAME') == 'mat_noise_color_time':
                generator['PARAMS']['speed'] = 'colorAnimation'
    if path.parent.name == '[recode]_The_Chemical_Brothers':
        for generator in _items(metadata, 'GENERATORS'):
            if generator.get('NAME') == 'mat_time':
                generator['PARAMS']['speed'] = 'mat_tunnelSpeed'
    # Dependency checks must inspect executable GLSL, never tutorial comments.
    source = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: '\n' * m.group().count('\n'), source, flags=re.DOTALL)
    if path.stem == 'Weather':
        source = source.replace('float t = mat_time;', '')
    # Unused generator declarations in upstream templates may refer to deleted
    # controls. Retain the transitive dependencies of generators actually used.
    generators = _items(metadata, 'GENERATORS')
    used = {g.get('NAME') for g in generators if re.search(r'\b'+re.escape(str(g.get('NAME', '')))+r'\b', source)}
    for _ in generators:
        for g in generators:
            if g.get('NAME') in used:
                params = g.get('PARAMS', {})
                used.update(v for v in (params.values() if isinstance(params,dict) else ()) if isinstance(v, str))
    metadata['GENERATORS'] = [g for g in generators if g.get('NAME') in used]
    if path.stem == 'Bar Code Enhanced':
        source = re.sub(r'^\s*a\s*(?=vec2\s+rotate2D)', '', source)
    # These names collide with defines supplied by TouchDesigner's GLSL header.
    renamed_inputs = set()
    input_names = {item.get('NAME') for item in _items(metadata, 'INPUTS')}
    for name in ('F2', 'F3', 'F4', 'G2', 'G3', 'G4', 'long'):
        if name in input_names or re.search(r'\b(?:float|vec[234])\s+[^;\n]*\b' + name + r'\s*(?:[=,;])', source):
            source = re.sub(r'\b' + name + r'\b', 'mm_material_' + name, source)
            renamed_inputs.add(name)
    source = re.sub(r'\blong\s+(?=[A-Za-z_]\w*)', 'int ', source)
    for name in ('tanh', 'round'):
        if re.search(r'\b(?:float|vec[234])\s+'+name+r'\s*\(', source):
            source = re.sub(r'\b'+name+r'\b', 'mm_material_'+name, source)
    if path.stem == 'GridZoomSandwich':
        source = source.replace('gl_FragColor = vec4(0.25);', 'return vec4(0.25);')
    if path.stem == 'strobeFlip':
        for generator in _items(metadata, 'GENERATORS'):
            if generator.get('PARAMS', {}).get('speed') == 'speed':
                generator['PARAMS']['speed'] = 'mat_speed'
    if path.stem in ('Cartoon Fire', 'Perlinsphere'):
        source = 'vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}\n' + source
    reasons: list[str] = []
    warnings: list[str] = list(source_repair_warnings)

    if path.suffix.lower() != ".fs":
        reasons.append("source is not a MadMapper .fs fragment shader")
    if not re.search(r"\bvec4\s+materialColorForPixel\s*\(", source):
        reasons.append("materialColorForPixel function is missing")
    if vertex_reason:
        reasons.append(vertex_reason)
    if vertex_call:
        warnings.append('uniform-only vertex calculations evaluated per fragment')
    if _VARYING_RE.search(_HEADER_RE.sub("", source)):
        reasons.append("requires MadMapper-specific vertex/surface varyings")
    if "SURFACE_IS_" in source:
        reasons.append("uses MadMapper surface-specific branches")
    if "gl_FragColor" in source:
        reasons.append("writes gl_FragColor outside the material return contract")

    raster = metadata.get("RASTERISATION_SETTINGS", {})
    if isinstance(raster, dict) and raster.get("REQUIRES_LAST_FRAME"):
        reasons.append("requires previous-frame feedback")
    textures = []
    texture_defs = []
    texture_indices = {'2d': 0, 'cube': 0}
    for item in _items(metadata, "IMPORTED"):
        name = str(item.get('NAME', ''))
        if not re.search(r'\b' + re.escape(name) + r'\b', source) and name != 'noiseLUT':
            continue
        value = item.get('PATH')
        kind = str(item.get('TYPE','2d')).lower()
        if kind not in ('2d','image','cube'):
            reasons.append('requires cube/3D texture: ' + name)
            continue
        if kind == 'cube':
            # ISF/MadMapper PATH lists retain the six declared OpenGL faces:
            # +X, -X, +Y, -Y, +Z, -Z. Unknown representations stay blocked.
            # MadMapper-Materials/MaterialsDoc.md (pinned d7ff211), line 200.
            if not isinstance(value,list) or len(value)!=6 or not all(isinstance(face,str) and face for face in value):
                reasons.append('cube texture requires six ordered face paths: ' + name)
                continue
            paths = value
        elif isinstance(value,str) and value:
            paths = [value]
            kind = '2d'
        else:
            reasons.append('invalid texture path: ' + name)
            continue
        if not _SAFE_IDENTIFIER_RE.match(name):
            reasons.append('invalid texture identifier: ' + name)
            continue
        resolved_paths = []
        for asset_path in paths:
            resolved = _resolve_include(asset_path, path.parent, library_roots)
            if resolved is None:
                # MadMapper shares assets between sibling material folders.
                matches = {p.resolve() for root in library_roots for p in root.rglob(Path(asset_path).name) if p.is_file()}
                if len(matches) == 1:
                    resolved = matches.pop()
                elif matches:
                    import hashlib
                    hashes = {hashlib.sha256(p.read_bytes()).digest() for p in matches}
                    if len(hashes) == 1:
                        resolved = sorted(matches)[0]
            if resolved is None:
                reasons.append('missing texture: ' + asset_path)
            else:
                resolved_paths.append(str(resolved))
        if len(resolved_paths)!=len(paths):
            continue
        texture = dict(item, resolved_path=resolved_paths[0])
        if kind == 'cube':
            texture.update(TYPE='cube', resolved_paths=resolved_paths)
        textures.append(texture)
        sampler = 'sTDCubeInputs' if kind == 'cube' else 'sTD2DInputs'
        texture_defs.append('#define %s %s[%d]' % (name, sampler, texture_indices[kind]))
        texture_indices[kind] += 1

    audio_inputs = [item for item in _items(metadata,'INPUTS')
                    if str(item.get('TYPE','')).lower() in {'audio','audiofft'}]
    resolved_audio = set()
    if audio_inputs:
        audio_path = _audio_texture_path()
        audio_schema = parameter_schema(metadata)
        values = input_values if isinstance(input_values,Mapping) else {}
        scalar_parameters = [p for p in audio_schema if p.kind in {'float','int','long','event','bool'}]
        audio_values = {p.name:_selected_input_value(p,values) for p in scalar_parameters}
        audio_uniforms = {p.name:p.uniform for p in scalar_parameters if not p.compile_time}
        for item in audio_inputs:
            name = str(item.get('NAME',''))
            if not audio_path or not _SAFE_IDENTIFIER_RE.fullmatch(name):
                continue
            invalid = []
            for field in ('SIZE','ATTACK','DECAY','RELEASE'):
                if field not in item:
                    continue
                value = item[field]
                if isinstance(value,str):
                    if value not in audio_values:
                        invalid.append('audio '+field+' requires scalar parameter: '+value)
                elif not isinstance(value,(int,float)) or not math.isfinite(value) or value < (1 if field=='SIZE' else 0):
                    invalid.append('invalid audio '+field+': '+name)
            reasons.extend(invalid)
            if invalid:
                continue
            textures.append(dict(item,source='audio_file',resolved_path=audio_path,
                                 _parameter_values=audio_values,_parameter_uniforms=audio_uniforms,loop=True))
            texture_defs.append('#define %s sTD2DInputs[%d]' % (name,texture_indices['2d']))
            texture_indices['2d'] += 1
            resolved_audio.add(name)

    input_defs, input_reasons, schema, bindings = _input_definitions(metadata, input_values, frozenset(resolved_audio))
    generator_defs, generator_reasons, generator_warnings = _generator_definitions(metadata)
    for name in renamed_inputs:
        input_defs = [re.sub(r'\b'+name+r'\b', 'mm_material_'+name, line) for line in input_defs]
        generator_defs = [re.sub(r'\b'+name+r'\b', 'mm_material_'+name, line) for line in generator_defs]
    reasons.extend(input_reasons)
    reasons.extend(generator_reasons)
    warnings.extend(generator_warnings)

    body = source
    body = re.sub(r"^\s*#version[^\n]*$", "", body, flags=re.MULTILINE)
    # Undefine library macros which would rewrite material-local declarations.
    declarations = set(re.findall(r'\b(?:float|int|vec[234])\s+([A-Za-z_]\w*)', body))
    body, include_reasons = _inline_includes(body, path.parent, [Path(item) for item in library_roots], {path})
    macros = set(re.findall(r'^\s*#define\s+(\w+)\b', body, re.MULTILINE))
    collisions = declarations & macros
    for name in collisions:
        # Rename the library macro and references only inside expanded includes.
        body = re.sub(r'// BEGIN .*?// END [^\n]*', lambda m: re.sub(r'\b'+re.escape(name)+r'\b', 'MM_LIBRARY_'+name, m.group()), body, flags=re.DOTALL)
    body = re.sub(r'\bprecision\s+(?:lowp|mediump|highp)\s+\w+\s*;', '', body)
    body = re.sub(r'\b(?:lowp|mediump|highp)\s+', '', body)
    body = re.sub(r'^(\s*)#define\s+(F4|G4)\b', r'\1#undef \2\n\1#define \2', body, flags=re.MULTILINE)
    # GLSL 4.x removed the dimension-suffixed builtins. These overloads have
    # exactly the same coordinates, bias/LOD and derivative argument semantics.
    # Do not guess mappings for projected, shadow or vendor-specific variants.
    legacy_texture_calls = {
        'texture2D':'texture', 'textureCube':'texture',
        'texture2DLod':'textureLod', 'textureCubeLod':'textureLod',
        'texture2DGradEXT':'textureGrad', 'textureCubeGradEXT':'textureGrad',
    }
    body = re.sub(r'\b('+'|'.join(legacy_texture_calls)+r')(?=\s*\()',
                  lambda m:legacy_texture_calls[m.group()],body)
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
#define RENDERSIZE uTDOutputInfo.res.zw
#define DATE vec4(0.0)
#define IMG_NORM_PIXEL(image, coord) texture(image, coord)
#define isf_FragNormCoord vUV.st
#define IMG_PIXEL(image, coord) texture(image, (coord) / vec2(textureSize(image, 0)))
#define IMG_SIZE(image) vec2(textureSize(image, 0))
#define texture2D texture

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
    prepared = "\n".join([prelude, *input_defs, *generator_defs, *texture_defs, body, """
void main()
{
%s
    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
""" % vertex_call])
    return AdaptationResult(
        "adaptable", (), tuple(dict.fromkeys(warnings)), prepared, metadata,
        schema, bindings, tuple(textures),
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
