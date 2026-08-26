"""Deterministic MadMapper/ISF material catalogue and safe local importer.

This module deliberately has no TouchDesigner or network dependency.  It scans
an already local source tree and emits a UI-friendly JSON document::

    {
      "schema_version": 1,
      "source": {"id": "madmapper-materials", "label": "...", "root": "..."},
      "materials": [{
        "id": "mat_...", "name": "Fluid Noise", "relative_path": "...",
        "source_path": "...", "kind": "isf", "groups": ["noise_texture"],
        "tags": ["fluid", "noise"], "compatibility": "adaptable",
        "compatibility_reasons": ["..."], "metadata": {...},
        "preview_path": "... or null"
      }],
      "facets": {"groups": {...}, "tags": {...}, "kinds": {...},
                 "compatibility": {...}}
    }

Stable IDs depend on the caller-controlled source ID and normalized relative
path, never on the absolute checkout location.  Imports are copied into one
managed directory per stable ID; a marker file prevents this library from ever
overwriting an unrelated directory or a changed file.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = 1
IMPORT_MANIFEST = "material-import.json"
MAX_INSPECT_BYTES = 4 * 1024 * 1024

FRAGMENT_SUFFIXES = frozenset({".fs", ".frag", ".glsl", ".isf", ".shader", ".material"})
VERTEX_SUFFIXES = frozenset({".vs", ".vert"})
KNOWN_UNSUPPORTED_SUFFIXES = frozenset(
    {".comp", ".geom", ".tesc", ".tese", ".hlsl", ".fx", ".metal"}
)
KNOWN_SUFFIXES = FRAGMENT_SUFFIXES | VERTEX_SUFFIXES | KNOWN_UNSUPPORTED_SUFFIXES
IGNORED_DIRS = frozenset({".git", "__pycache__", ".idea", ".vscode"})

_WORD_RE = re.compile(r"[a-z0-9]+")
_INCLUDE_RE = re.compile(r"^\s*#\s*include\b", re.MULTILINE)
_STOP_WORDS = frozenset(
    {
        "a", "an", "and", "by", "for", "from", "in", "is", "material", "materials",
        "of", "on", "or", "shader", "the", "to", "with", "fragment", "factory",
    }
)

# Canonical tag -> words or phrases which imply it.  Keeping this explicit makes
# classification inspectable and deterministic instead of model-dependent.
TAG_ALIASES: Mapping[str, tuple[str, ...]] = {
    "noise": ("noise", "noisy", "fbm", "perlin", "simplex", "turbulence"),
    "cellular": ("cellular", "cell", "voronoi"),
    "fluid": ("fluid", "flow", "liquid", "smoke", "ink"),
    "organic": ("blob", "blobby", "metaball", "organic"),
    "particles": ("particle", "particles", "spark", "stars", "dust"),
    "lines": ("line", "lines", "stripe", "stripes", "barcode"),
    "geometry": ("arc", "circle", "shape", "sdf", "polygon", "geometry", "grid"),
    "pulse": ("pulse", "wave", "ripple", "radial"),
    "comet": ("comet", "tail", "trail"),
    "glitch": ("glitch", "bad tv", "badtv", "scanline", "distortion"),
    "transition": ("transition", "wipe", "dissolve", "crossfade", "fade"),
    "audio_reactive": ("audio", "sound", "music", "fft", "spectrum", "beat"),
    "image_filter": ("filter", "blur", "sharpen", "pixelate", "input image", "image"),
    "color": ("color", "colour", "gradient", "palette", "hue", "rainbow"),
    "utility": ("test", "calibration", "utility", "solid", "fill", "checker"),
}

GROUP_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("transitions", ("transition",)),
    ("audio_reactive", ("audio_reactive",)),
    ("particles", ("particles", "comet")),
    ("noise_texture", ("noise", "cellular")),
    ("fluid_organic", ("fluid", "organic")),
    ("lines_geometry", ("lines", "geometry", "pulse")),
    ("glitch_distortion", ("glitch",)),
    ("image_filters", ("image_filter",)),
    ("color_generators", ("color",)),
    ("utility_testing", ("utility",)),
)


class MaterialLibraryError(ValueError):
    """Base error for invalid catalogues, unsafe paths, and import conflicts."""


class MaterialImportError(MaterialLibraryError):
    """Raised when an import would escape a root or overwrite existing data."""


class Compatibility(str, Enum):
    NATIVE = "native"
    ADAPTABLE = "adaptable"
    UNSUPPORTED = "unsupported"


def _json_value(value: Any) -> Any:
    """Return a recursively JSON-safe metadata value with deterministic keys."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(value[key]) for key in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return str(value)


@dataclass(frozen=True)
class MaterialRecord:
    id: str
    name: str
    relative_path: str
    source_path: str
    kind: str
    groups: tuple[str, ...]
    tags: tuple[str, ...]
    compatibility: Compatibility
    compatibility_reasons: tuple[str, ...]
    metadata: Mapping[str, Any]
    preview_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "relative_path": self.relative_path,
            "source_path": self.source_path,
            "kind": self.kind,
            "groups": list(self.groups),
            "tags": list(self.tags),
            "compatibility": self.compatibility.value,
            "compatibility_reasons": list(self.compatibility_reasons),
            "metadata": _json_value(self.metadata),
            "preview_path": self.preview_path,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MaterialRecord":
        required = {
            "id", "name", "relative_path", "source_path", "kind", "groups", "tags",
            "compatibility", "compatibility_reasons", "metadata", "preview_path",
        }
        if not isinstance(data, Mapping) or set(data) != required:
            raise MaterialLibraryError("material record fields do not match schema version 1")
        try:
            compatibility = Compatibility(data["compatibility"])
        except (TypeError, ValueError) as exc:
            raise MaterialLibraryError("invalid material compatibility") from exc
        scalar_fields = ("id", "name", "relative_path", "source_path", "kind")
        if any(not isinstance(data[field], str) or not data[field] for field in scalar_fields):
            raise MaterialLibraryError("material string fields must be non-empty")
        for field in ("groups", "tags", "compatibility_reasons"):
            if not isinstance(data[field], list) or not all(isinstance(x, str) for x in data[field]):
                raise MaterialLibraryError(f"material {field} must be a string array")
        if not isinstance(data["metadata"], Mapping):
            raise MaterialLibraryError("material metadata must be an object")
        preview = data["preview_path"]
        if preview is not None and not isinstance(preview, str):
            raise MaterialLibraryError("material preview_path must be string or null")
        return cls(
            id=data["id"], name=data["name"], relative_path=data["relative_path"],
            source_path=data["source_path"], kind=data["kind"],
            groups=tuple(data["groups"]), tags=tuple(data["tags"]),
            compatibility=compatibility,
            compatibility_reasons=tuple(data["compatibility_reasons"]),
            metadata=dict(data["metadata"]), preview_path=preview,
        )


@dataclass(frozen=True)
class MaterialCatalog:
    source_id: str
    source_label: str
    source_root: str
    materials: tuple[MaterialRecord, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise MaterialLibraryError(f"schema_version must be {SCHEMA_VERSION}")
        if any(
            not isinstance(value, str) or not value
            for value in (self.source_id, self.source_label, self.source_root)
        ):
            raise MaterialLibraryError("catalog source fields must be non-empty")
        ids = [item.id for item in self.materials]
        if len(ids) != len(set(ids)):
            raise MaterialLibraryError("material ids must be unique")

    def by_id(self, material_id: str) -> MaterialRecord:
        for material in self.materials:
            if material.id == material_id:
                return material
        raise MaterialLibraryError(f"unknown material id: {material_id}")

    def facets(self) -> dict[str, dict[str, int]]:
        return {
            "groups": dict(sorted(Counter(x for m in self.materials for x in m.groups).items())),
            "tags": dict(sorted(Counter(x for m in self.materials for x in m.tags).items())),
            "kinds": dict(sorted(Counter(m.kind for m in self.materials).items())),
            "compatibility": dict(
                sorted(Counter(m.compatibility.value for m in self.materials).items())
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source": {
                "id": self.source_id,
                "label": self.source_label,
                "root": self.source_root,
            },
            "materials": [material.to_dict() for material in self.materials],
            "facets": self.facets(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MaterialCatalog":
        if not isinstance(data, Mapping) or set(data) != {
            "schema_version", "source", "materials", "facets"
        }:
            raise MaterialLibraryError("catalog fields do not match schema version 1")
        if data["schema_version"] != SCHEMA_VERSION:
            raise MaterialLibraryError(f"schema_version must be {SCHEMA_VERSION}")
        source = data["source"]
        if not isinstance(source, Mapping) or set(source) != {"id", "label", "root"}:
            raise MaterialLibraryError("catalog source fields are invalid")
        raw_materials = data["materials"]
        if not isinstance(raw_materials, list):
            raise MaterialLibraryError("catalog materials must be an array")
        catalog = cls(
            source_id=source["id"], source_label=source["label"], source_root=source["root"],
            materials=tuple(MaterialRecord.from_dict(item) for item in raw_materials),
            schema_version=data["schema_version"],
        )
        if data["facets"] != catalog.facets():
            raise MaterialLibraryError("catalog facets do not match material records")
        return catalog


@dataclass(frozen=True)
class ImportedMaterial:
    id: str
    directory: Path
    source_path: Path
    manifest_path: Path
    created: bool


def _slug(text: str) -> str:
    value = "-".join(_WORD_RE.findall(text.casefold()))
    return value or "materials"


def _tokens(text: str) -> set[str]:
    return {token for token in _WORD_RE.findall(text.casefold()) if token not in _STOP_WORDS}


def extract_isf_metadata(source: str) -> dict[str, Any]:
    """Extract the first valid ISF-style JSON object from a block comment.

    Malformed comments are ignored.  A JSON object is considered ISF metadata
    when it contains at least one standard ISF/MadMapper metadata key.
    """
    decoder = json.JSONDecoder()
    marker_keys = {
        "ISFVSN", "INPUTS", "CATEGORIES", "DESCRIPTION", "CREDIT", "PASSES",
        "IMPORTED", "VSN", "NAME", "LABEL", "TAGS",
    }
    for match in re.finditer(r"/\*(.*?)\*/", source, flags=re.DOTALL):
        comment = match.group(1).lstrip("\ufeff \t\r\n*")
        start = comment.find("{")
        if start < 0:
            continue
        candidate = comment[start:]
        try:
            value, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            try:
                relaxed = _normalise_relaxed_numbers(_remove_trailing_commas(candidate))
                value, _ = decoder.raw_decode(relaxed)
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict) and marker_keys.intersection(value):
            return _json_value(value)
    return {}


def _remove_trailing_commas(text: str) -> str:
    """Remove commas immediately before ``]``/``}`` without touching strings."""
    result: list[str] = []
    in_string = False
    escaped = False
    length = len(text)
    for index, character in enumerate(text):
        if in_string:
            result.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
            result.append(character)
            continue
        if character == ",":
            lookahead = index + 1
            while lookahead < length and text[lookahead].isspace():
                lookahead += 1
            if lookahead < length and text[lookahead] in "]}":
                continue
        result.append(character)
    return "".join(result)


def _normalise_relaxed_numbers(text: str) -> str:
    """Convert MadMapper's JSON-like ``360.`` numbers without editing strings."""
    result: list[str] = []
    outside: list[str] = []
    in_string = False
    escaped = False

    def flush_outside() -> None:
        if not outside:
            return
        segment = "".join(outside)
        segment = re.sub(r"(?<![A-Za-z0-9_.])(-?\d+)\.(?=\s*[,}\]])", r"\1.0", segment)
        segment = re.sub(r"(?<![A-Za-z0-9_.])(-?)\.(\d+)", r"\g<1>0.\2", segment)
        result.append(segment)
        outside.clear()

    for character in text:
        if in_string:
            result.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            flush_outside()
            result.append(character)
            in_string = True
        else:
            outside.append(character)
    flush_outside()
    return "".join(result)


def _read_source(path: Path) -> tuple[str, bool]:
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            raw = stream.read(MAX_INSPECT_BYTES + 1)
    except OSError:
        return "", False
    too_large = size > MAX_INSPECT_BYTES or len(raw) > MAX_INSPECT_BYTES
    return raw[:MAX_INSPECT_BYTES].decode("utf-8-sig", errors="replace"), too_large


def _kind_and_compatibility(path: Path, source: str, metadata: Mapping[str, Any], too_large: bool) -> tuple[str, Compatibility, tuple[str, ...]]:
    suffix = path.suffix.casefold()
    if suffix in VERTEX_SUFFIXES:
        return "vertex_glsl", Compatibility.UNSUPPORTED, ("standalone vertex shader has no fragment output",)
    if suffix in KNOWN_UNSUPPORTED_SUFFIXES:
        return suffix.lstrip(".") + "_shader", Compatibility.UNSUPPORTED, ("shader language or stage is not supported by the TouchDesigner fragment importer",)
    if too_large:
        return "glsl_fragment", Compatibility.UNSUPPORTED, ("file exceeds the safe inspection limit",)
    if metadata:
        reasons = ["ISF/MadMapper metadata and uniforms require a TouchDesigner adapter"]
        if metadata.get("PASSES"):
            reasons.append("multi-pass material requires explicit pass graph conversion")
        if metadata.get("IMPORTED"):
            reasons.append("imported image resources must be connected in TouchDesigner")
        return "isf", Compatibility.ADAPTABLE, tuple(reasons)
    if "TDOutputSwizzle" in source or "sTD2DInputs" in source:
        return "touchdesigner_glsl", Compatibility.NATIVE, ("contains TouchDesigner GLSL markers",)
    if "materialColorForPixel" in source:
        return "madmapper_glsl", Compatibility.ADAPTABLE, ("MadMapper material entry point requires a TouchDesigner wrapper",)
    if "mainImage" in source:
        return "shadertoy_glsl", Compatibility.ADAPTABLE, ("ShaderToy entry point and uniforms require a TouchDesigner wrapper",)
    if re.search(r"\bvoid\s+main\s*\(", source):
        reasons = ["generic fragment shader may require uniform and output-name mapping"]
        if _INCLUDE_RE.search(source):
            reasons.append("include files must remain available beside the imported shader")
        return "glsl_fragment", Compatibility.ADAPTABLE, tuple(reasons)
    return "glsl_helper", Compatibility.UNSUPPORTED, ("no supported fragment entry point was found",)


def _metadata_text(metadata: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in ("NAME", "LABEL", "DESCRIPTION", "CREDIT", "CATEGORIES", "TAGS"):
        value = metadata.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    inputs = metadata.get("INPUTS", [])
    if isinstance(inputs, list):
        for item in inputs:
            if isinstance(item, Mapping):
                parts.extend(str(item.get(key, "")) for key in ("NAME", "LABEL", "TYPE"))
    return " ".join(parts)


def _classify(name: str, relative_path: str, metadata: Mapping[str, Any], source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    haystack = " ".join((name, relative_path, _metadata_text(metadata))).casefold()
    haystack_tokens = _tokens(haystack)
    category_values = metadata.get("CATEGORIES", [])
    if not isinstance(category_values, list):
        category_values = [category_values]
    explicit_tags = metadata.get("TAGS", [])
    if isinstance(explicit_tags, str):
        explicit_tags = [part.strip() for part in explicit_tags.split(",") if part.strip()]
    elif not isinstance(explicit_tags, list):
        explicit_tags = [explicit_tags]
    input_names: list[str] = []
    inputs = metadata.get("INPUTS", [])
    if isinstance(inputs, list):
        for item in inputs:
            if isinstance(item, Mapping):
                input_names.extend(str(item.get(key, "")) for key in ("NAME", "LABEL"))
    tag_seed = " ".join(
        (
            name,
            str(Path(relative_path).with_suffix("")),
            *(str(value) for value in category_values),
            *(str(value) for value in explicit_tags),
            *input_names,
        )
    )
    raw_tokens = {token for token in _tokens(tag_seed) if len(token) > 1}
    tags = set(raw_tokens)
    for canonical, aliases in TAG_ALIASES.items():
        if any(_tokens(alias).issubset(haystack_tokens) for alias in aliases):
            tags.add(canonical)
    # Shader markers improve categorisation even when filenames are generic.
    if any(word in source for word in ("audioFFT", "iChannelTime", "soundInput")):
        tags.add("audio_reactive")
    path_parts = {part.casefold() for part in Path(relative_path).parts}
    groups: list[str] = []
    for path_name, source_group in (
        ("factory", "factory"), ("demos", "demos"), ("online library", "online_library")
    ):
        if path_name in path_parts:
            groups.append(source_group)
    groups.extend(group for group, tag_names in GROUP_RULES if tags.intersection(tag_names))
    if not groups:
        groups.append("uncategorized")
    return tuple(groups), tuple(sorted(tags))


def _display_name(path: Path, metadata: Mapping[str, Any]) -> str:
    for key in ("NAME", "LABEL"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    candidate = path.parent.name if path.stem.casefold() in {"material", "fragment", "shader"} else path.stem
    return re.sub(r"[_-]+", " ", candidate).strip().title() or path.name


def _preview_for(shader: Path, source_root: Path) -> str | None:
    candidates = (
        shader.with_suffix(".png"), shader.with_suffix(".jpg"), shader.with_suffix(".jpeg"),
        shader.parent / "preview.png", shader.parent / "thumbnail.png",
        shader.parent / "preview.jpg", shader.parent / "thumbnail.jpg",
        shader.parent / "preview.jpeg", shader.parent / "thumbnail.jpeg",
    )
    root_resolved = source_root.resolve(strict=True)
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root_resolved)
        except (OSError, ValueError):
            continue
        return str(resolved)
    return None


def _iter_known_files(root: Path) -> Iterable[Path]:
    for directory, dir_names, file_names in os.walk(root, followlinks=False):
        dir_names[:] = sorted(
            (name for name in dir_names if name not in IGNORED_DIRS), key=str.casefold
        )
        for file_name in sorted(file_names, key=str.casefold):
            path = Path(directory) / file_name
            if path.suffix.casefold() in KNOWN_SUFFIXES:
                yield path


def _has_fragment_entrypoint(path: Path) -> bool:
    if path.suffix.casefold() not in FRAGMENT_SUFFIXES:
        return False
    source, too_large = _read_source(path)
    return not too_large and bool(
        re.search(r"\bvoid\s+main\s*\(", source)
        or "mainImage" in source
        or "materialColorForPixel" in source
    )


def _package_files(shader: Path, source_root: Path) -> tuple[str, ...]:
    """Return safe files belonging to an unambiguous one-shader material folder."""
    if shader.parent == source_root or shader.parent.name.casefold() in {
        "factory", "materials", "generators", "filters", "examples", "templates",
        "library", "libraries",
    }:
        return ()
    entrypoints = [
        sibling for sibling in shader.parent.iterdir()
        if sibling.is_file() and _has_fragment_entrypoint(sibling)
    ]
    if len(entrypoints) != 1 or entrypoints[0].resolve() != shader.resolve():
        return ()
    root_resolved = source_root.resolve(strict=True)
    package_paths: list[str] = []
    for candidate in sorted(shader.parent.iterdir(), key=lambda item: item.name.casefold()):
        if not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
            relative = resolved.relative_to(root_resolved).as_posix()
        except (OSError, ValueError):
            continue
        package_paths.append(relative)
    return tuple(sorted(set(package_paths), key=str.casefold))


def build_catalog(source_root: str | Path, *, source_id: str | None = None, source_label: str | None = None) -> MaterialCatalog:
    """Scan ``source_root`` without following directory symlinks."""
    root = Path(source_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise MaterialLibraryError(f"source root is not a directory: {root}")
    stable_source_id = _slug(source_id or root.name)
    label = (source_label or root.name).strip()
    if not label:
        raise MaterialLibraryError("source_label must not be empty")
    records: list[MaterialRecord] = []
    official_layout = (root / "Materials").is_dir() and (root / "Libraries").is_dir()
    for path in _iter_known_files(root):
        try:
            resolved = path.resolve(strict=True)
            relative = resolved.relative_to(root).as_posix()
        except (OSError, ValueError):
            # Broken and escaping symlinks cannot become importable records.
            continue
        if official_layout and (
            resolved.suffix.casefold() != ".fs"
            or not relative.casefold().startswith("materials/")
        ):
            # The official repository defines one browser material per .fs file.
            # .vs/.glsl files and Libraries are dependencies of those records.
            continue
        if resolved.suffix.casefold() in VERTEX_SUFFIXES and any(
            _has_fragment_entrypoint(sibling)
            for sibling in resolved.parent.iterdir()
            if sibling.is_file() and sibling != resolved
        ):
            # A vertex shader beside a material fragment is a package companion,
            # not a separately selectable browser item.
            continue
        source, too_large = _read_source(resolved)
        metadata = extract_isf_metadata(source)
        name = _display_name(resolved, metadata)
        kind, compatibility, reasons = _kind_and_compatibility(
            resolved, source, metadata, too_large
        )
        if kind == "glsl_helper":
            in_library = any(
                part.casefold() in {"library", "libraries", "includes"}
                for part in resolved.relative_to(root).parts[:-1]
            )
            package_companion = any(
                _has_fragment_entrypoint(sibling)
                for sibling in resolved.parent.iterdir()
                if sibling.is_file() and sibling != resolved
            )
            if in_library or package_companion:
                continue
        package_files = _package_files(resolved, root)
        if package_files:
            metadata = dict(metadata)
            metadata["_PACKAGE_FILES"] = list(package_files)
            companion_suffixes = sorted(
                {
                    Path(item).suffix.casefold()
                    for item in package_files
                    if item.casefold() != relative.casefold()
                }
            )
            metadata["_COMPANION_TYPES"] = companion_suffixes
            extra_reasons = list(reasons)
            if ".vs" in companion_suffixes:
                extra_reasons.append("material includes a companion vertex shader that must be adapted with the fragment")
            if _INCLUDE_RE.search(source):
                extra_reasons.append("included MadMapper libraries must be resolved by the TouchDesigner adapter")
            reasons = tuple(dict.fromkeys(extra_reasons))
        groups, tags = _classify(name, relative, metadata, source)
        identity = f"{stable_source_id}:{relative.casefold()}".encode("utf-8")
        material_id = "mat_" + hashlib.sha256(identity).hexdigest()[:20]
        records.append(
            MaterialRecord(
                id=material_id, name=name, relative_path=relative,
                source_path=str(resolved), kind=kind, groups=groups, tags=tags,
                compatibility=compatibility, compatibility_reasons=reasons,
                metadata=metadata, preview_path=_preview_for(resolved, root),
            )
        )
    records.sort(key=lambda item: (item.name.casefold(), item.relative_path.casefold()))
    return MaterialCatalog(
        source_id=stable_source_id, source_label=label, source_root=str(root),
        materials=tuple(records),
    )


def write_catalog(catalog: MaterialCatalog, path: str | Path) -> Path:
    if not isinstance(catalog, MaterialCatalog):
        raise MaterialLibraryError("write_catalog requires a MaterialCatalog")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(catalog.to_dict(), indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    temporary.replace(target)
    return target


def load_catalog(path: str | Path) -> MaterialCatalog:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterialLibraryError(f"cannot load catalog {source}: {exc}") from exc
    return MaterialCatalog.from_dict(data)


def _as_catalog(catalog_or_path: MaterialCatalog | str | Path) -> MaterialCatalog:
    return catalog_or_path if isinstance(catalog_or_path, MaterialCatalog) else load_catalog(catalog_or_path)


def _normalise_filter(values: str | Iterable[str] | None) -> frozenset[str]:
    if values is None:
        return frozenset()
    if isinstance(values, str):
        values = (values,)
    return frozenset(value.casefold() for value in values)


def _query_score(material: MaterialRecord, query: str) -> float | None:
    terms = tuple(_tokens(query))
    if not terms:
        return 0.0
    searchable = " ".join(
        (material.name, material.relative_path, material.kind, *material.groups, *material.tags,
         _metadata_text(material.metadata))
    ).casefold()
    words = _tokens(searchable)
    total = 0.0
    for term in terms:
        if term in searchable:
            total += 3.0 if term in _tokens(material.name) else 2.0
            continue
        ratio = max((SequenceMatcher(None, term, word).ratio() for word in words), default=0.0)
        if ratio < 0.72:
            return None
        total += ratio
    return total


def search_catalog(
    catalog_or_path: MaterialCatalog | str | Path,
    query: str = "",
    *,
    groups: str | Iterable[str] | None = None,
    tags: str | Iterable[str] | None = None,
    kinds: str | Iterable[str] | None = None,
    compatibility: str | Compatibility | Iterable[str | Compatibility] | None = None,
    limit: int | None = None,
) -> tuple[MaterialRecord, ...]:
    """Search with AND semantics between facets and tolerant text terms."""
    catalog = _as_catalog(catalog_or_path)
    group_filter, tag_filter, kind_filter = map(
        _normalise_filter, (groups, tags, kinds)
    )
    if isinstance(compatibility, (str, Compatibility)):
        compatibility = (compatibility,)
    compatibility_filter = frozenset(
        (item.value if isinstance(item, Compatibility) else str(item)).casefold()
        for item in (compatibility or ())
    )
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
        raise MaterialLibraryError("limit must be a non-negative integer or null")
    matches: list[tuple[float, MaterialRecord]] = []
    for material in catalog.materials:
        if group_filter and not group_filter.issubset({x.casefold() for x in material.groups}):
            continue
        if tag_filter and not tag_filter.issubset({x.casefold() for x in material.tags}):
            continue
        if kind_filter and material.kind.casefold() not in kind_filter:
            continue
        if compatibility_filter and material.compatibility.value.casefold() not in compatibility_filter:
            continue
        score = _query_score(material, query)
        if score is not None:
            matches.append((score, material))
    matches.sort(key=lambda item: (-item[0], item[1].name.casefold(), item[1].relative_path.casefold()))
    records = tuple(item[1] for item in matches)
    return records if limit is None else records[:limit]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_material(
    catalog_or_path: MaterialCatalog | str | Path,
    material_id: str,
    import_root: str | Path,
) -> ImportedMaterial:
    """Copy one selected material without overwriting any existing content.

    The source is revalidated against the catalogue root at import time, so a
    changed symlink or forged catalogue cannot copy arbitrary host files.
    Existing managed imports are idempotent only when their marker, source hash,
    and imported file all still match.
    """
    catalog = _as_catalog(catalog_or_path)
    material = catalog.by_id(material_id)
    try:
        source_root = Path(catalog.source_root).resolve(strict=True)
        source = Path(material.source_path).resolve(strict=True)
        source.relative_to(source_root)
    except (OSError, ValueError) as exc:
        raise MaterialImportError("material source escapes or no longer exists within source root") from exc
    if not source.is_file():
        raise MaterialImportError("material source is not a regular file")
    expected_relative = source.relative_to(source_root).as_posix()
    if expected_relative.casefold() != material.relative_path.casefold():
        raise MaterialImportError("material source no longer matches its catalog relative path")

    raw_package_files = material.metadata.get("_PACKAGE_FILES", [material.relative_path])
    if not isinstance(raw_package_files, list) or not all(
        isinstance(value, str) for value in raw_package_files
    ):
        raise MaterialImportError("material package file list is invalid")
    package_relative_root = Path(material.relative_path).parent
    package_sources: list[tuple[Path, Path]] = []
    requested_paths = list(dict.fromkeys((*raw_package_files, material.relative_path)))
    for relative_name in requested_paths:
        relative_path = Path(relative_name)
        if relative_path.is_absolute():
            raise MaterialImportError("material package contains an absolute path")
        try:
            destination_relative = relative_path.relative_to(package_relative_root)
            package_source = (source_root / relative_path).resolve(strict=True)
            package_source.relative_to(source_root)
        except (OSError, ValueError) as exc:
            raise MaterialImportError("material package file escapes its source folder") from exc
        if not package_source.is_file():
            raise MaterialImportError("material package contains a non-file entry")
        package_sources.append((package_source, destination_relative))

    destination_root = Path(import_root).expanduser()
    destination_root.mkdir(parents=True, exist_ok=True)
    destination_root = destination_root.resolve(strict=True)
    target_dir = destination_root / material.id
    main_destination_relative = Path(material.relative_path).relative_to(package_relative_root)
    target = target_dir / main_destination_relative
    marker = target_dir / IMPORT_MANIFEST
    package_hashes = {
        destination_relative.as_posix(): _sha256(package_source)
        for package_source, destination_relative in package_sources
    }
    source_hash = package_hashes[main_destination_relative.as_posix()]

    if target_dir.exists():
        try:
            target_dir.resolve(strict=True).relative_to(destination_root)
        except (OSError, ValueError) as exc:
            raise MaterialImportError("existing import destination escapes managed root") from exc
        if not target_dir.is_dir() or not marker.is_file():
            raise MaterialImportError("import destination exists but is not managed by this library")
        try:
            old_manifest = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MaterialImportError("existing import marker is unreadable") from exc
        if (
            old_manifest.get("material_id") != material.id
            or old_manifest.get("source_sha256") != source_hash
            or old_manifest.get("imported_files") != package_hashes
        ):
            raise MaterialImportError("existing import differs; refusing to overwrite it")
        for relative_name, expected_hash in package_hashes.items():
            imported_file = target_dir / relative_name
            if not imported_file.is_file() or _sha256(imported_file) != expected_hash:
                raise MaterialImportError("existing imported material differs; refusing to overwrite it")
        return ImportedMaterial(material.id, target_dir, target, marker, False)

    # Stable IDs are hex-only by construction, but validate the target again to
    # keep this safe even if a forged MaterialRecord enters a constructed catalog.
    if not re.fullmatch(r"mat_[0-9a-f]{20}", material.id):
        raise MaterialImportError("material id is not a safe managed-directory name")
    try:
        target_dir.relative_to(destination_root)
    except ValueError as exc:
        raise MaterialImportError("import destination escapes managed root") from exc

    target_dir.mkdir()
    for package_source, destination_relative in package_sources:
        destination = target_dir / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_source, destination)
    manifest_data = {
        "schema_version": SCHEMA_VERSION,
        "material_id": material.id,
        "source_id": catalog.source_id,
        "source_relative_path": material.relative_path,
        "source_sha256": source_hash,
        "imported_file": source.name,
        "imported_files": package_hashes,
        "kind": material.kind,
        "compatibility": material.compatibility.value,
    }
    marker.write_text(
        json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    return ImportedMaterial(material.id, target_dir, target, marker, True)


def import_materials(
    catalog_or_path: MaterialCatalog | str | Path,
    material_ids: Sequence[str],
    import_root: str | Path,
) -> tuple[ImportedMaterial, ...]:
    """Import a deterministic de-duplicated selection in the given order."""
    catalog = _as_catalog(catalog_or_path)
    seen: set[str] = set()
    results: list[ImportedMaterial] = []
    for material_id in material_ids:
        if material_id not in seen:
            results.append(import_material(catalog, material_id, import_root))
            seen.add(material_id)
    return tuple(results)


__all__ = [
    "Compatibility", "ImportedMaterial", "MaterialCatalog", "MaterialImportError",
    "MaterialLibraryError", "MaterialRecord", "build_catalog", "extract_isf_metadata",
    "import_material", "import_materials", "load_catalog", "search_catalog", "write_catalog",
]
