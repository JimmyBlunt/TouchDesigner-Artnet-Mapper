"""Immutable, offline-only cumulative 3D layout drafts.

No TouchDesigner calls, hardware actions or file writes. Original scan points
are archived separately from object transforms. LED IDs, object-local indices
and global source indices survive transforms and explicit partial rescans.

Transforms use right-handed X, then Y, then Z Euler rotations (degrees), after
per-axis scaling about ``pivot``; translation is applied last. No normalization
or index allocation is implicit. Coordinate coincidence is allowed (separate
LEDs can occupy the same position); ownership/index overlaps are rejected.

Supported external formats reuse mapper_io: Pixelblaze arrays (2D gets z=0),
preserved generators with an explicitly supplied trusted materializer, and
MariMapper index/x/y/z CSV (including existing tx/ty/tz aliases), and the plain
3D coordinate-array JSON verified in MariMapper's Exported/AllExported.json.
Unknown JSON wrappers fail explicitly. Scene JSON is this module's versioned
format, NOT a MariMapper interchange.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from math import cos, isfinite, radians, sin
from typing import Callable
from uuid import uuid4

from .mapper_io import (
    GeneratorExecutionUnavailable, MappingData, MappingFormatError,
    PixelblazeGenerator, export_pixelblaze_json, import_marimapper_csv,
    import_pixelblaze,
)

SCENE_SCHEMA = "pixelblaze-layout-scene"
SCENE_VERSION = 1
Vec3 = tuple[float, float, float]


class SceneError(ValueError):
    """Invalid scene or edit; the current draft remains untouched."""


def new_id() -> str:
    return str(uuid4())


def _id(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise SceneError(f"{label} must be a non-empty, trimmed string")
    return value


def _index(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SceneError(f"{label} must be a non-negative integer")
    return value


def _vec(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise SceneError(f"{label} must contain three finite numbers")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
           for v in value):
        raise SceneError(f"{label} must contain three finite numbers")
    return tuple(float(v) for v in value)


@dataclass(frozen=True)
class Transform:
    translation: Vec3 = (0.0, 0.0, 0.0)
    rotation_degrees: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    pivot: Vec3 = (0.0, 0.0, 0.0)

    def __post_init__(self):
        for name in ("translation", "rotation_degrees", "scale", "pivot"):
            object.__setattr__(self, name, _vec(getattr(self, name), name))
        if any(v == 0 for v in self.scale):
            raise SceneError("scale must be non-zero on every axis (negative mirrors allowed)")

    def apply(self, point: Vec3) -> Vec3:
        xyz = _vec(point, "point")
        x, y, z = ((p - center) * size for p, center, size in zip(xyz, self.pivot, self.scale))
        rx, ry, rz = map(radians, self.rotation_degrees)
        y, z = y * cos(rx) - z * sin(rx), y * sin(rx) + z * cos(rx)
        x, z = x * cos(ry) + z * sin(ry), -x * sin(ry) + z * cos(ry)
        x, y = x * cos(rz) - y * sin(rz), x * sin(rz) + y * cos(rz)
        return _vec(tuple(v + p + t for v, p, t in zip((x, y, z), self.pivot, self.translation)),
                    "transformed point")


@dataclass(frozen=True)
class Scan:
    scan_id: str
    name: str
    points: tuple[Vec3, ...]
    source_format: str = "coordinates"
    missing_indices: tuple[int, ...] = ()
    # Deeply immutable CSV metadata, one tuple of (field, value) pairs per point.
    row_metadata: tuple[tuple[tuple[str, str], ...], ...] = ()
    warnings: tuple[str, ...] = ()
    generator_source: str | None = None
    # Explicit scan-frame -> object-original-frame alignment, never fitted here.
    registration: Transform = Transform()

    def __post_init__(self):
        _id(self.scan_id, "scan_id")
        _id(self.name, "scan name")
        _id(self.source_format, "source_format")
        object.__setattr__(self, "points", tuple(_vec(p, "scan point") for p in self.points))
        if not self.points:
            raise SceneError("scan must contain at least one point")
        missing = tuple(self.missing_indices)
        for i in missing:
            if _index(i, "missing index") >= len(self.points):
                raise SceneError("missing index outside scan")
        if len(set(missing)) != len(missing):
            raise SceneError("duplicate missing indices")
        object.__setattr__(self, "missing_indices", tuple(sorted(missing)))
        metadata = tuple(tuple(tuple(pair) for pair in row) for row in self.row_metadata)
        if metadata and len(metadata) != len(self.points):
            raise SceneError("row metadata must align with original scan points")
        for row in metadata:
            if any(len(pair) != 2 or any(not isinstance(v, str) for v in pair) for pair in row):
                raise SceneError("metadata entries must be string field/value pairs")
            if len({pair[0] for pair in row}) != len(row):
                raise SceneError("duplicate metadata fields")
        object.__setattr__(self, "row_metadata", metadata)
        if any(not isinstance(v, str) for v in self.warnings):
            raise SceneError("warnings must be strings")
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if self.generator_source is not None and not isinstance(self.generator_source, str):
            raise SceneError("generator_source must be text or null")
        if not isinstance(self.registration, Transform):
            raise SceneError("scan registration must be a Transform")
        for point in self.points:
            self.registration.apply(point)


def import_scan(source, *, format: str, name: str, scan_id: str | None = None,
                generator_count: int | None = None,
                generator_materializer: Callable[[PixelblazeGenerator, int], MappingData] | None = None) -> Scan:
    """Parse without guessing paths/schemas; use Path explicitly for a file.

    Generator evaluation is never automatic. A caller may explicitly pass the
    existing ``materialize_pixelblaze_generator`` adapter for trusted input.
    CSV source indices remain scan-local indices including marked missing slots.
    """
    generator_source = None
    if format == "marimapper-csv":
        mapping = import_marimapper_csv(source)
    elif format in ("pixelblaze", "pixelblaze-json", "pixelblaze-generator"):
        mapping = import_pixelblaze(source)
        if isinstance(mapping, PixelblazeGenerator):
            generator_source = mapping.source
            if generator_materializer is None:
                raise GeneratorExecutionUnavailable(
                    "Generator preserved, not executed: provide materialized coordinates or an explicit trusted materializer"
                )
            count = _index(generator_count, "generator_count")
            if count == 0:
                raise SceneError("generator_count must be positive")
            mapping = generator_materializer(mapping, count)
            if not isinstance(mapping, MappingData) or len(mapping.coordinates) != count:
                raise SceneError("generator result does not match requested count")
    elif format == "marimapper-json":
        try:
            mapping = import_pixelblaze(source)
        except MappingFormatError as exc:
            raise MappingFormatError(
                "Unrecognized MariMapper JSON schema: supported export is a plain [[x,y,z], ...] array; no wrapper schema is guessed"
            ) from exc
        if not isinstance(mapping, MappingData) or mapping.dimensions != 3:
            raise MappingFormatError("MariMapper JSON requires a materialized 3D coordinate array")
        mapping = replace(mapping, source_format="marimapper-json-array")
    else:
        raise MappingFormatError(f"Unsupported scan format: {format!r}")
    return Scan(
        scan_id if scan_id is not None else new_id(), name,
        tuple(tuple(p) if mapping.dimensions == 3 else (*p, 0.0) for p in mapping.coordinates),
        mapping.source_format, mapping.missing_indices,
        tuple(tuple(sorted(row.items())) for row in mapping.row_metadata),
        mapping.warnings, generator_source,
    )


@dataclass(frozen=True)
class LedBinding:
    led_id: str
    local_index: int
    source_index: int
    scan_id: str
    scan_index: int

    def __post_init__(self):
        _id(self.led_id, "led_id")
        _id(self.scan_id, "scan_id")
        for name in ("local_index", "source_index", "scan_index"):
            _index(getattr(self, name), name)


@dataclass(frozen=True)
class SceneObject:
    object_id: str
    name: str
    leds: tuple[LedBinding, ...]
    transform: Transform = Transform()

    def __post_init__(self):
        _id(self.object_id, "object_id")
        _id(self.name, "object name")
        object.__setattr__(self, "leds", tuple(self.leds))
        if not self.leds or any(not isinstance(v, LedBinding) for v in self.leds):
            raise SceneError("object requires LED bindings")
        if not isinstance(self.transform, Transform):
            raise SceneError("object transform must be a Transform")
        if len({v.local_index for v in self.leds}) != len(self.leds):
            raise SceneError("duplicate object-local LED index")


@dataclass(frozen=True)
class Scene:
    scene_id: str
    name: str
    scans: tuple[Scan, ...] = ()
    objects: tuple[SceneObject, ...] = ()
    # Optional final output count, not a restriction on intermediate drafts.
    expected_count: int | None = None

    def __post_init__(self):
        _id(self.scene_id, "scene_id")
        _id(self.name, "scene name")
        object.__setattr__(self, "scans", tuple(self.scans))
        object.__setattr__(self, "objects", tuple(self.objects))
        if self.expected_count is not None:
            _index(self.expected_count, "expected_count")
        if any(not isinstance(s, Scan) for s in self.scans) or any(not isinstance(o, SceneObject) for o in self.objects):
            raise SceneError("scene requires Scan and SceneObject records")
        if len({s.scan_id for s in self.scans}) != len(self.scans):
            raise SceneError("duplicate scan_id")
        if len({o.object_id for o in self.objects}) != len(self.objects):
            raise SceneError("duplicate object_id")
        scan_by_id = {s.scan_id: s for s in self.scans}
        ids, sources = set(), set()
        for obj in self.objects:
            for led in obj.leds:
                if led.led_id in ids or led.source_index in sources:
                    raise SceneError("overlapping LED identity or global source index")
                ids.add(led.led_id)
                sources.add(led.source_index)
                scan = scan_by_id.get(led.scan_id)
                if scan is None or led.scan_index >= len(scan.points):
                    raise SceneError("LED references unknown scan or point")
                obj.transform.apply(scan.registration.apply(scan.points[led.scan_index]))

    def object(self, object_id: str) -> SceneObject:
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj
        raise SceneError(f"unknown object_id: {object_id}")

    def world_points(self) -> tuple[tuple[LedBinding, Vec3], ...]:
        """Return bindings with transformed points, ordered by global index."""
        scans = {s.scan_id: s for s in self.scans}
        return tuple(sorted(
            ((led, obj.transform.apply(scans[led.scan_id].registration.apply(scans[led.scan_id].points[led.scan_index])))
             for obj in self.objects for led in obj.leds),
            key=lambda item: item[0].source_index,
        ))

    def validate_output(self) -> None:
        """Final Pixelblaze arrays need full contiguous 0..N-1 coverage."""
        bindings = [led for obj in self.objects for led in obj.leds]
        count = len(bindings)
        if count == 0:
            raise SceneError("cannot export an empty layout")
        if self.expected_count is not None and count != self.expected_count:
            raise SceneError(f"expected {self.expected_count} LEDs, got {count}")
        if {v.source_index for v in bindings} != set(range(count)):
            raise SceneError("global source indices have gaps; export will not silently renumber LEDs")
        scans = {s.scan_id: s for s in self.scans}
        if any(v.scan_index in scans[v.scan_id].missing_indices for v in bindings):
            raise SceneError("missing scan points must be rescanned before Pixelblaze export")


def _with_scan(scene: Scene, scan: Scan) -> tuple[Scan, ...]:
    previous = next((s for s in scene.scans if s.scan_id == scan.scan_id), None)
    if previous is not None and previous != scan:
        raise SceneError("scan_id already exists with different immutable original data")
    return scene.scans if previous else (*scene.scans, scan)


def append_scan(scene: Scene, scan: Scan, *, source_start: int | None = None,
                source_indices: tuple[int, ...] | None = None,
                scan_indices: tuple[int, ...] | None = None,
                object_id: str | None = None, name: str | None = None) -> Scene:
    """Append with explicit global ownership and optional scan-point selection.

    A CSV can use absolute source indices. Select its actual scan_indices
    explicitly to exclude leading missing placeholders, and supply the intended
    global source_indices; neither offset nor missing-point deletion is guessed.
    """
    if (source_start is None) == (source_indices is None):
        raise SceneError("provide exactly one of source_start or source_indices")
    selected = tuple(range(len(scan.points))) if scan_indices is None else tuple(scan_indices)
    if not selected or len(set(selected)) != len(selected):
        raise SceneError("scan_indices must be a non-empty unique selection")
    for i in selected:
        if _index(i, "scan index") >= len(scan.points):
            raise SceneError("scan index out of range")
    count = len(selected)
    if source_start is not None:
        _index(source_start, "source_start")
        source_indices = tuple(range(source_start, source_start + count))
    else:
        source_indices = tuple(source_indices)
    if len(source_indices) != count:
        raise SceneError("one explicit global source index is required per scan point")
    obj_id = object_id if object_id is not None else new_id()
    leds = tuple(LedBinding(new_id(), i, index, scan.scan_id, scan_index)
                 for i, (index, scan_index) in enumerate(zip(source_indices, selected)))
    obj = SceneObject(obj_id, name if name is not None else scan.name, leds)
    return replace(scene, scans=_with_scan(scene, scan), objects=(*scene.objects, obj))


def set_transform(scene: Scene, object_id: str, transform: Transform) -> Scene:
    obj = scene.object(object_id)
    updated = replace(obj, transform=transform)
    return replace(scene, objects=tuple(updated if o.object_id == object_id else o for o in scene.objects))


def replace_region(scene: Scene, object_id: str, local_indices: tuple[int, ...],
                   scan: Scan, *, scan_indices: tuple[int, ...] | None = None) -> Scene:
    """Replace selected measurements, preserving every LED and object identity.

    Selection order pairs with scan_indices (default original scan order).
    Scan.registration must explicitly map its original points to the object's
    ORIGINAL local frame (identity is the caller's assertion of shared frame).
    Existing object transform remains applied. No nearest-neighbor matching,
    registration fitting, resize or renumber guessing.
    The old scan stays archived in the scene, even when no LED references it.
    """
    obj = scene.object(object_id)
    selected = tuple(local_indices)
    incoming = tuple(range(len(scan.points))) if scan_indices is None else tuple(scan_indices)
    if not selected or len(selected) != len(incoming):
        raise SceneError("replacement count must match the non-empty selected region")
    for index in selected:
        _index(index, "selected local index")
    for index in incoming:
        if _index(index, "scan index") >= len(scan.points):
            raise SceneError("replacement scan index out of range")
    if len(set(selected)) != len(selected) or len(set(incoming)) != len(incoming):
        raise SceneError("replacement indices must be unique")
    if not set(selected).issubset({v.local_index for v in obj.leds}):
        raise SceneError("selected local index does not belong to this object")
    pairs = dict(zip(selected, incoming))
    updated = replace(obj, leds=tuple(
        replace(led, scan_id=scan.scan_id, scan_index=pairs[led.local_index])
        if led.local_index in pairs else led for led in obj.leds
    ))
    return replace(scene, scans=_with_scan(scene, scan),
                   objects=tuple(updated if o.object_id == object_id else o for o in scene.objects))


class SceneHistory:
    """In-memory draft undo/redo. Committing never applies to active LED output."""

    def __init__(self, scene: Scene):
        if not isinstance(scene, Scene):
            raise SceneError("history requires a Scene")
        self._current = scene
        self._undo: list[Scene] = []
        self._redo: list[Scene] = []

    @property
    def current(self) -> Scene:
        return self._current

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def commit(self, scene: Scene) -> Scene:
        if not isinstance(scene, Scene) or scene.scene_id != self.current.scene_id:
            raise SceneError("commit must preserve scene identity")
        archived = {s.scan_id: s for s in scene.scans}
        if any(archived.get(s.scan_id) != s for s in self.current.scans):
            raise SceneError("commit cannot alter or discard archived original scans")
        old_ids = {v.led_id: (o.object_id, v.local_index, v.source_index)
                   for o in self.current.objects for v in o.leds}
        for obj in scene.objects:
            for led in obj.leds:
                if led.led_id in old_ids and old_ids[led.led_id] != (obj.object_id, led.local_index, led.source_index):
                    raise SceneError("commit cannot reassign a stable LED identity")
        if scene != self.current:
            self._undo.append(self.current)
            self._current = scene
            self._redo.clear()
        return self.current

    def undo(self) -> Scene:
        if self._undo:
            self._redo.append(self.current)
            self._current = self._undo.pop()
        return self.current

    def redo(self) -> Scene:
        if self._redo:
            self._undo.append(self.current)
            self._current = self._redo.pop()
        return self.current


def export_scene_json(scene: Scene, *, indent: int = 2) -> str:
    """Lossless scene text, including archived original scans and stable IDs."""
    from dataclasses import asdict
    return json.dumps({"schema": SCENE_SCHEMA, "version": SCENE_VERSION, **asdict(scene)},
                      indent=indent, allow_nan=False, ensure_ascii=False)


def _fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names):
        raise SceneError(f"{label} fields must be exactly: {', '.join(names)}")
    return value


def import_scene_json(text: str) -> Scene:
    """Strict versioned scene input; unsupported schemas/fields fail visibly."""
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SceneError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(text, object_pairs_hook=unique_pairs)
        _fields(data, ("schema", "version", "scene_id", "name", "scans", "objects", "expected_count"), "scene")
        if data["schema"] != SCENE_SCHEMA or type(data["version"]) is not int or data["version"] != SCENE_VERSION:
            raise SceneError("unsupported scene schema/version (not MariMapper JSON)")
        if not isinstance(data["scans"], list) or not isinstance(data["objects"], list):
            raise SceneError("scans and objects must be arrays")
        scans = []
        for raw_scan in data["scans"]:
            _fields(raw_scan, Scan.__dataclass_fields__, "scan")
            registration = Transform(**_fields(raw_scan["registration"], Transform.__dataclass_fields__, "registration"))
            scans.append(Scan(**{**raw_scan, "registration": registration}))
        objects = []
        for raw in data["objects"]:
            _fields(raw, SceneObject.__dataclass_fields__, "object")
            if not isinstance(raw["leds"], list):
                raise SceneError("leds must be an array")
            leds = tuple(LedBinding(**_fields(v, LedBinding.__dataclass_fields__, "LED")) for v in raw["leds"])
            transform = Transform(**_fields(raw["transform"], Transform.__dataclass_fields__, "transform"))
            objects.append(SceneObject(raw["object_id"], raw["name"], leds, transform))
        return Scene(data["scene_id"], data["name"], tuple(scans), tuple(objects), data["expected_count"])
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise SceneError(f"invalid scene JSON: {exc}") from exc


def export_pixelblaze_3d(scene: Scene, *, indent: int = 2) -> str:
    """Export world coordinates at their exact global indices, never reindex.

    Pixelblaze arrays cannot carry scan/object/LED metadata. Save scene JSON
    alongside this interchange to retain IDs, raw scans and transforms.
    Undo/redo stacks themselves are session-local, not serialized.
    """
    scene.validate_output()
    return export_pixelblaze_json(MappingData(tuple(point for _, point in scene.world_points()),
                                             3, "layout-scene-world"), indent=indent)
