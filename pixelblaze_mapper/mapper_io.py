"""Portable mapping I/O for Pixelblaze, MariMapper, and TouchDesigner.

The module intentionally has no TouchDesigner dependency.  It keeps imported raw
coordinates immutable and makes display normalization (``fill``/``contain``) an
explicit derived operation.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence, TextIO


class MappingFormatError(ValueError):
    """Raised when mapping input is malformed or internally inconsistent."""


class GeneratorExecutionUnavailable(RuntimeError):
    """Raised when JavaScript materialization is requested without a JS runtime."""


Coordinate = tuple[float, ...]


@dataclass(frozen=True)
class MappingData:
    """A materialized, index-ordered LED mapping.

    ``coordinates`` always contains one item per LED index.  MariMapper gaps are
    represented by zero coordinates and recorded in ``missing_indices``.
    ``row_metadata`` is aligned to coordinates and preserves optional CSV fields.
    """

    coordinates: tuple[Coordinate, ...]
    dimensions: int
    source_format: str
    warnings: tuple[str, ...] = ()
    missing_indices: tuple[int, ...] = ()
    row_metadata: tuple[Mapping[str, str], ...] = ()
    metadata_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dimensions not in (2, 3):
            raise MappingFormatError("Mappings must consistently be 2D or 3D")
        for index, coordinate in enumerate(self.coordinates):
            if len(coordinate) != self.dimensions:
                raise MappingFormatError(
                    f"Coordinate {index} has {len(coordinate)} dimensions; "
                    f"expected {self.dimensions}"
                )
            _validate_coordinate(coordinate, index)
        if self.row_metadata and len(self.row_metadata) != len(self.coordinates):
            raise MappingFormatError("row_metadata must be aligned to coordinates")

    def normalized(self, mode: str) -> "MappingData":
        """Return a normalized copy using Pixelblaze-style Fill or Contain.

        Fill scales every axis independently to 0..1.  Contain uses a shared
        scale (the largest axis extent) and centers shorter/flat axes at 0.5.
        Raw coordinates in this object are never changed.
        """

        normalized_coordinates = normalize_coordinates(self.coordinates, mode)
        return MappingData(
            coordinates=normalized_coordinates,
            dimensions=self.dimensions,
            source_format=f"{self.source_format}:{mode.lower()}",
            warnings=self.warnings,
            missing_indices=self.missing_indices,
            row_metadata=self.row_metadata,
            metadata_fields=self.metadata_fields,
        )


def rotate_mapping_range_90(
    mapping: MappingData,
    start_index: int,
    end_index: int,
    *,
    axis: str = "x",
    turns: int = 1,
    center: Coordinate = (0.5, 0.5, 0.5),
) -> MappingData:
    """Rotate an inclusive 3D LED-index range in exact 90-degree steps.

    Pixel indices and metadata remain in place. Positive turns use the
    right-hand rule. Around normalized X, one turn maps (x,y,z) to (x,1-z,y).
    """

    if mapping.dimensions != 3:
        raise MappingFormatError("Range rotation requires a 3D mapping")
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        raise MappingFormatError("Rotation indices must be integers")
    if start_index < 0 or end_index < start_index or end_index >= len(mapping.coordinates):
        raise MappingFormatError("Rotation index range is outside the mapping")
    normalized_axis = axis.lower()
    if normalized_axis not in ("x", "y", "z"):
        raise MappingFormatError("Rotation axis must be x, y, or z")
    if len(center) != 3 or not all(math.isfinite(float(value)) for value in center):
        raise MappingFormatError("Rotation center must contain three finite values")
    if not isinstance(turns, int):
        raise MappingFormatError("Rotation turns must be an integer")

    quarter_turns = turns % 4
    cx, cy, cz = (float(value) for value in center)

    def rotate_once(point: Coordinate) -> Coordinate:
        x, y, z = point
        dx, dy, dz = x - cx, y - cy, z - cz
        if normalized_axis == "x":
            return (cx + dx, cy - dz, cz + dy)
        if normalized_axis == "y":
            return (cx + dz, cy + dy, cz - dx)
        return (cx - dy, cy + dx, cz + dz)

    coordinates = list(mapping.coordinates)
    for index in range(start_index, end_index + 1):
        point = coordinates[index]
        for _ in range(quarter_turns):
            point = rotate_once(point)
        coordinates[index] = tuple(0.0 if abs(value) < 1e-15 else value for value in point)

    note = (
        f"rotated indices {start_index}-{end_index} "
        f"{quarter_turns * 90} degrees around {normalized_axis.upper()}"
    )
    return MappingData(
        coordinates=tuple(coordinates),
        dimensions=mapping.dimensions,
        source_format=f"{mapping.source_format}:rotate-{normalized_axis}{quarter_turns * 90}",
        warnings=(*mapping.warnings, note),
        missing_indices=mapping.missing_indices,
        row_metadata=mapping.row_metadata,
        metadata_fields=mapping.metadata_fields,
    )


def place_upright_sidewall_range(
    mapping: MappingData,
    start_index: int,
    end_index: int,
    *,
    wall_x: float = 0.94,
    normal_depth: float = 0.04,
) -> MappingData:
    """Orient a previously horizontal side-wall scan into the room layout.

    The source scan's X/Z plane contains the recognizable contour motifs.
    The installed right wall is the project's Z/Y plane, so the mapping is:

    ``new_x = wall_x + (old_y - 0.5) * normal_depth``
    ``new_y = 1 - old_z``
    ``new_z = old_x``

    This keeps the three motifs upright in the Z/Y elevation, places them on
    the right wall, and preserves a small amount of measured normal relief.
    Indices, metadata, missing slots, and coordinates outside the inclusive
    range are unchanged.
    """

    if mapping.dimensions != 3:
        raise MappingFormatError("Side-wall placement requires a 3D mapping")
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        raise MappingFormatError("Side-wall indices must be integers")
    if start_index < 0 or end_index < start_index or end_index >= len(mapping.coordinates):
        raise MappingFormatError("Side-wall index range is outside the mapping")
    if not math.isfinite(wall_x) or not math.isfinite(normal_depth) or normal_depth < 0:
        raise MappingFormatError("wall_x and normal_depth must be finite; depth cannot be negative")

    missing = set(mapping.missing_indices)
    coordinates = list(mapping.coordinates)
    for index in range(start_index, end_index + 1):
        if index in missing:
            continue
        old_x, old_y, old_z = coordinates[index]
        coordinates[index] = (
            wall_x + (old_y - 0.5) * normal_depth,
            1.0 - old_z,
            old_x,
        )

    note = (
        f"upright right-wall placement indices {start_index}-{end_index}; "
        f"ZY=(source X,1-source Z), wall X={wall_x}, normal depth={normal_depth}"
    )
    return MappingData(
        coordinates=tuple(coordinates),
        dimensions=mapping.dimensions,
        source_format=f"{mapping.source_format}:upright-right-wall",
        warnings=(*mapping.warnings, note),
        missing_indices=mapping.missing_indices,
        row_metadata=mapping.row_metadata,
        metadata_fields=mapping.metadata_fields,
    )


@dataclass(frozen=True)
class PixelblazeGenerator:
    """A safely preserved Pixelblaze JavaScript mapper generator.

    The source can be round-tripped, displayed, or sent to a trusted JavaScript
    execution adapter.  This Python module never evaluates it.
    """

    source: str
    source_format: str = "pixelblaze-js-generator"
    warnings: tuple[str, ...] = field(
        default=(
            "JavaScript generator preserved but not executed; materialize it in "
            "Pixelblaze or an explicitly trusted JavaScript runtime.",
        )
    )

    @property
    def can_execute(self) -> bool:
        return False

    def materialize(self) -> MappingData:
        raise GeneratorExecutionUnavailable(
            "JavaScript generator execution is unavailable in the safe Python "
            "I/O module; provide materialized coordinates or a trusted adapter."
        )


def materialize_pixelblaze_generator(
    generator: PixelblazeGenerator,
    pixel_count: int,
    *,
    node_executable: str | None = None,
    timeout: float = 2.0,
) -> MappingData:
    """Materialize a Pixelblaze mapper function in an isolated Node process.

    This adapter is deliberately opt-in.  The generator receives only
    ``pixelCount`` and JavaScript's standard ``Math`` object; Node APIs such as
    ``require`` and ``process`` are not exposed.  Execution is time-limited and
    dynamic string/wasm code generation is disabled.  Node's VM is a useful
    containment layer for mapper files, but callers should still only execute
    files they intended to open.
    """

    if isinstance(pixel_count, bool) or not isinstance(pixel_count, int) or pixel_count < 0:
        raise ValueError("pixel_count must be a non-negative integer")
    executable = node_executable or shutil.which("node")
    if not executable:
        raise GeneratorExecutionUnavailable(
            "Node.js was not found; install Node or open a materialized JSON map"
        )
    worker = Path(__file__).with_name("js_materialize.mjs")
    payload = json.dumps(
        {"source": generator.source, "pixelCount": pixel_count}, allow_nan=False
    )
    try:
        completed = subprocess.run(
            [executable, str(worker)],
            input=payload,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as exc:
        raise MappingFormatError("Pixelblaze generator exceeded the execution limit") from exc
    except OSError as exc:
        raise GeneratorExecutionUnavailable(f"Could not start Node.js: {exc}") from exc
    if completed.returncode:
        message = (completed.stderr or completed.stdout or "generator failed").strip()
        raise MappingFormatError(f"Pixelblaze generator error: {message[:500]}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MappingFormatError("Pixelblaze generator did not return valid JSON") from exc
    if not isinstance(value, list):
        raise MappingFormatError("Pixelblaze generator must return a coordinate array")
    coordinates = _coerce_coordinate_array(value)
    dimensions = len(coordinates[0]) if coordinates else 3
    warnings = ()
    if len(coordinates) != pixel_count:
        warnings = (
            f"Generator returned {len(coordinates)} coordinates for pixelCount={pixel_count}",
        )
    return MappingData(
        coordinates,
        dimensions,
        "pixelblaze-js-materialized",
        warnings=warnings,
    )


def import_pixelblaze(source: str | bytes | Path | TextIO) -> MappingData | PixelblazeGenerator:
    """Import a Pixelblaze coordinate array or preserve a JS generator.

    Materialized input accepts strict JSON plus JavaScript-style comments and
    trailing commas.  Arbitrary expressions are not evaluated.
    """

    text = _read_text(source)
    try:
        value = json.loads(_remove_trailing_commas(_strip_js_comments(text)))
    except json.JSONDecodeError as exc:
        if _looks_like_javascript_generator(text):
            _validate_balanced_javascript(text)
            return PixelblazeGenerator(source=text)
        raise MappingFormatError(
            f"Pixelblaze input is neither a coordinate array nor a recognized "
            f"JavaScript generator (line {exc.lineno}, column {exc.colno})"
        ) from exc

    if not isinstance(value, list):
        raise MappingFormatError("Pixelblaze mapping root must be an array")
    coordinates = _coerce_coordinate_array(value)
    dimensions = len(coordinates[0]) if coordinates else 3
    return MappingData(coordinates, dimensions, "pixelblaze-json")


def import_pixelblaze_js(source: str | bytes | Path | TextIO) -> PixelblazeGenerator:
    """Explicitly import and preserve a JavaScript mapper generator."""

    text = _read_text(source)
    if not _looks_like_javascript_generator(text):
        raise MappingFormatError("Input is not a recognized JavaScript generator")
    _validate_balanced_javascript(text)
    return PixelblazeGenerator(source=text)


def import_marimapper_csv(source: str | bytes | Path | TextIO) -> MappingData:
    """Import MariMapper CSV, ordering rows strictly by ``index``.

    Required coordinate headers are ``x,y,z``.  ``tx,ty,tz`` are accepted as a
    compatibility alias for existing TouchDesigner tables.  All additional
    fields (including ``xn,yn,zn,error``) are preserved as string metadata.
    """

    text = _read_text(source)
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        headers = reader.fieldnames
        if not headers:
            raise MappingFormatError("MariMapper CSV has no header")
        headers = [header.strip() for header in headers]
        reader.fieldnames = headers
        lowered = {header.lower(): header for header in headers}
        if "index" not in lowered:
            raise MappingFormatError("MariMapper CSV requires an index column")
        if all(name in lowered for name in ("x", "y", "z")):
            axes = tuple(lowered[name] for name in ("x", "y", "z"))
        elif all(name in lowered for name in ("tx", "ty", "tz")):
            axes = tuple(lowered[name] for name in ("tx", "ty", "tz"))
        else:
            raise MappingFormatError("MariMapper CSV requires x,y,z columns")

        index_header = lowered["index"]
        extra_fields = tuple(h for h in headers if h not in (index_header, *axes))
        by_index: dict[int, tuple[Coordinate, dict[str, str]]] = {}
        for line_number, row in enumerate(reader, start=2):
            raw_index = (row.get(index_header) or "").strip()
            try:
                index = int(raw_index)
            except ValueError as exc:
                raise MappingFormatError(
                    f"Line {line_number}: invalid integer index {raw_index!r}"
                ) from exc
            if index < 0:
                raise MappingFormatError(f"Line {line_number}: negative index {index}")
            if index in by_index:
                raise MappingFormatError(f"Line {line_number}: duplicate index {index}")
            coordinate = tuple(
                _parse_finite_float(row.get(axis), f"line {line_number} column {axis}")
                for axis in axes
            )
            metadata = {field: row.get(field, "") or "" for field in extra_fields}
            by_index[index] = (coordinate, metadata)
    except csv.Error as exc:
        raise MappingFormatError(f"Invalid MariMapper CSV: {exc}") from exc

    if not by_index:
        return MappingData((), 3, "marimapper-csv", metadata_fields=extra_fields)

    maximum = max(by_index)
    missing = tuple(index for index in range(maximum + 1) if index not in by_index)
    coordinates: list[Coordinate] = []
    metadata_rows: list[Mapping[str, str]] = []
    for index in range(maximum + 1):
        coordinate, metadata = by_index.get(index, ((0.0, 0.0, 0.0), {}))
        coordinates.append(coordinate)
        metadata_rows.append(metadata)
    warnings: tuple[str, ...] = ()
    if missing:
        warnings = (
            f"Inserted [0,0,0] for {len(missing)} missing indices: "
            f"{_format_index_ranges(missing)}",
        )
    return MappingData(
        tuple(coordinates),
        3,
        "marimapper-csv",
        warnings,
        missing,
        tuple(metadata_rows),
        extra_fields,
    )


def export_pixelblaze_json(mapping: MappingData, *, indent: int | None = None) -> str:
    """Export only the raw coordinate array, with no application metadata."""

    return json.dumps(
        [list(coordinate) for coordinate in mapping.coordinates],
        indent=indent,
        allow_nan=False,
        separators=(",", ":") if indent is None else None,
    )


def export_pixelblaze_js(generator: PixelblazeGenerator) -> str:
    """Return a preserved generator byte-for-byte as text."""

    return generator.source


def export_marimapper_csv(mapping: MappingData, *, include_metadata: bool = True) -> str:
    """Export index-ordered ``index,x,y,z`` MariMapper CSV.

    2D mappings receive a zero ``z`` coordinate.  Preserved optional columns are
    appended when ``include_metadata`` is true.
    """

    output = io.StringIO(newline="")
    extra_fields = mapping.metadata_fields if include_metadata else ()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("index", "x", "y", "z", *extra_fields))
    for index, coordinate in enumerate(mapping.coordinates):
        xyz = (*coordinate, 0.0) if mapping.dimensions == 2 else coordinate
        metadata = mapping.row_metadata[index] if mapping.row_metadata else {}
        writer.writerow(
            (index, *(_format_number(value) for value in xyz), *(metadata.get(f, "") for f in extra_fields))
        )
    return output.getvalue()


def normalize_coordinates(
    coordinates: Sequence[Sequence[float]], mode: str
) -> tuple[Coordinate, ...]:
    """Derive Fill/Contain coordinates without mutating the source."""

    normalized_mode = mode.strip().lower()
    if normalized_mode not in ("fill", "contain"):
        raise ValueError("Normalization mode must be 'fill' or 'contain'")
    if not coordinates:
        return ()
    dimensions = len(coordinates[0])
    if dimensions not in (2, 3):
        raise MappingFormatError("Mappings must consistently be 2D or 3D")
    coerced = tuple(tuple(float(value) for value in coordinate) for coordinate in coordinates)
    for index, coordinate in enumerate(coerced):
        if len(coordinate) != dimensions:
            raise MappingFormatError("Mappings must consistently be 2D or 3D")
        _validate_coordinate(coordinate, index)

    minima = tuple(min(point[axis] for point in coerced) for axis in range(dimensions))
    maxima = tuple(max(point[axis] for point in coerced) for axis in range(dimensions))
    spans = tuple(maxima[axis] - minima[axis] for axis in range(dimensions))
    if normalized_mode == "fill":
        return tuple(
            tuple(
                (point[axis] - minima[axis]) / spans[axis] if spans[axis] else 0.5
                for axis in range(dimensions)
            )
            for point in coerced
        )

    common_span = max(spans)
    if not common_span:
        return tuple(tuple(0.5 for _ in range(dimensions)) for _ in coerced)
    centers = tuple((minima[axis] + maxima[axis]) / 2.0 for axis in range(dimensions))
    return tuple(
        tuple((point[axis] - centers[axis]) / common_span + 0.5 for axis in range(dimensions))
        for point in coerced
    )


def _read_text(source: str | bytes | Path | TextIO) -> str:
    if isinstance(source, bytes):
        return source.decode("utf-8-sig")
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8-sig")
    if hasattr(source, "read"):
        text = source.read()
        return text.decode("utf-8-sig") if isinstance(text, bytes) else text
    if isinstance(source, str):
        # A plain string is intentionally treated as mapping content.  File
        # loading must be explicit via Path so long JSON/JS sources are never
        # accidentally interpreted as filesystem paths.
        return source
    raise TypeError("source must be mapping text, bytes, pathlib.Path, or a text stream")


def _coerce_coordinate_array(value: list[object]) -> tuple[Coordinate, ...]:
    if not value:
        return ()
    coordinates: list[Coordinate] = []
    dimensions: int | None = None
    for index, item in enumerate(value):
        if not isinstance(item, list):
            raise MappingFormatError(f"Coordinate {index} must be an array")
        if dimensions is None:
            dimensions = len(item)
            if dimensions not in (2, 3):
                raise MappingFormatError("Coordinates must have exactly 2 or 3 values")
        if len(item) != dimensions:
            raise MappingFormatError("Pixelblaze coordinates mix 2D and 3D values")
        coordinate = tuple(_coerce_finite_number(v, f"coordinate {index}") for v in item)
        coordinates.append(coordinate)
    return tuple(coordinates)


def _coerce_finite_number(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MappingFormatError(f"{context} contains a non-numeric value")
    number = float(value)
    if not math.isfinite(number):
        raise MappingFormatError(f"{context} contains a non-finite value")
    return number


def _parse_finite_float(value: str | None, context: str) -> float:
    try:
        number = float((value or "").strip())
    except ValueError as exc:
        raise MappingFormatError(f"{context}: expected a number, got {value!r}") from exc
    if not math.isfinite(number):
        raise MappingFormatError(f"{context}: number must be finite")
    return number


def _validate_coordinate(coordinate: Sequence[float], index: int) -> None:
    for value in coordinate:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise MappingFormatError(f"Coordinate {index} contains a non-finite number")


def _strip_js_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            result.append(char)
            if char == "\\" and index + 1 < len(text):
                index += 1
                result.append(text[index])
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
            result.append(char)
        elif char == "/" and nxt == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            if index < len(text):
                result.append(text[index])
        elif char == "/" and nxt == "*":
            index += 2
            while index + 1 < len(text) and text[index : index + 2] != "*/":
                if text[index] in "\r\n":
                    result.append(text[index])
                index += 1
            index += 1
        else:
            result.append(char)
        index += 1
    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    # After comments are removed, this is safe for numeric coordinate arrays.
    return re.sub(r",\s*([}\]])", r"\1", text)


_JS_GENERATOR_PATTERNS = (
    re.compile(r"\bfunction\b"),
    re.compile(r"=>"),
    re.compile(r"\b(?:mapPixels|pixelCount|return)\b"),
    re.compile(r"\bfor\s*\("),
)


def _looks_like_javascript_generator(text: str) -> bool:
    stripped = _strip_js_comments(text).strip()
    return bool(stripped) and any(pattern.search(stripped) for pattern in _JS_GENERATOR_PATTERNS)


def _validate_balanced_javascript(text: str) -> None:
    clean = _strip_js_comments(text)
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    quote: str | None = None
    escaped = False
    for position, char in enumerate(clean):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'", "`"):
            quote = char
        elif char in "([{":
            stack.append((char, position))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                raise MappingFormatError(f"Unbalanced JavaScript near character {position}")
            stack.pop()
    if quote:
        raise MappingFormatError("Unterminated JavaScript string")
    if stack:
        raise MappingFormatError("Unbalanced JavaScript delimiters")


def _format_index_ranges(indices: Iterable[int]) -> str:
    values = list(indices)
    if not values:
        return ""
    ranges: list[str] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = value
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def _format_number(value: float) -> str:
    return format(value, ".17g")
