"""Immutable 2D fixture layout and independent material UV placement.

Output layout and UV placement each transform the SAME frozen local geometry;
neither transform is composed with the other. No sampler/output/file mutation.
Projection defaults to Y horizontal / X vertical and never edits the 3D Scene.
"""

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from math import cos, isfinite, radians, sin
from uuid import uuid4

from .layout_scene import LedBinding, export_scene_json

SCHEMA = 'pixelblaze-fixture-scene'
VERSION = 1


class FixtureError(ValueError):
    pass


def _id(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise FixtureError(label + ' must be a nonempty trimmed string')
    return value


def _vec(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(
        isinstance(v, bool) or not isinstance(v, (float, int)) or not isfinite(v) for v in value
    ):
        raise FixtureError(label + ' requires two finite numbers')
    return tuple(float(v) for v in value)


@dataclass(frozen=True)
class Transform2D:
    """Scale about pivot, rotate counterclockwise (degrees), then translate."""
    translation: tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    scale: tuple[float, float] = (1.0, 1.0)
    pivot: tuple[float, float] = (0.0, 0.0)

    def __post_init__(self):
        for field in ('translation', 'scale', 'pivot'):
            object.__setattr__(self, field, _vec(getattr(self, field), field))
        if any(v == 0 for v in self.scale):
            raise FixtureError('Zero scale collapses fixture geometry')
        if isinstance(self.rotation, bool) or not isinstance(self.rotation, (int, float)) or not isfinite(self.rotation):
            raise FixtureError('rotation must be finite degrees')

    def apply(self, point):
        px, py = _vec(point, 'point')
        x, y = (px - self.pivot[0]) * self.scale[0], (py - self.pivot[1]) * self.scale[1]
        a = radians(self.rotation)
        result = (x * cos(a) - y * sin(a) + self.pivot[0] + self.translation[0],
                  x * sin(a) + y * cos(a) + self.pivot[1] + self.translation[1])
        return _vec(result, 'transformed point')


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    object_id: str
    leds: tuple[LedBinding, ...]
    local_points: tuple[tuple[float, float], ...]
    output_transform: Transform2D = Transform2D()
    uv_transform: Transform2D = Transform2D()
    projection: str = 'YX'
    missing_ids: tuple[str, ...] = ()

    def __post_init__(self):
        _id(self.fixture_id, 'fixture_id')
        _id(self.object_id, 'object_id')
        object.__setattr__(self, 'leds', tuple(self.leds))
        object.__setattr__(self, 'local_points', tuple(_vec(p, 'local point') for p in self.local_points))
        object.__setattr__(self, 'missing_ids', tuple(self.missing_ids))
        if not self.leds or len(self.leds) != len(self.local_points) or any(not isinstance(v, LedBinding) for v in self.leds):
            raise FixtureError('Fixture needs one local point for each stable LED binding')
        for field in ('led_id', 'source_index', 'local_index'):
            if len({getattr(v, field) for v in self.leds}) != len(self.leds):
                raise FixtureError('Duplicate fixture ' + field)
        if self.projection not in ('XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY', '2D'):
            raise FixtureError('Unknown explicit projection')
        if not isinstance(self.output_transform, Transform2D) or not isinstance(self.uv_transform, Transform2D):
            raise FixtureError('Both domains need Transform2D values')
        if len(set(self.missing_ids)) != len(self.missing_ids) or not set(self.missing_ids) <= {led.led_id for led in self.leds}:
            raise FixtureError('Missing IDs must be unique fixture LEDs')
        # Reject overflow at construction, not later during export.
        self.output_points()
        self.sample_uv()

    def output_points(self):
        return tuple((led, self.output_transform.apply(point)) for led, point in zip(self.leds, self.local_points))

    def sample_uv(self):
        return tuple((led, self.uv_transform.apply(point)) for led, point in zip(self.leds, self.local_points))

    def out_of_bounds_ids(self):
        return tuple(led.led_id for led, point in self.sample_uv() if any(v < 0 or v > 1 for v in point))


def scene_revision(scene):
    return sha256(export_scene_json(scene, indent=None).encode('utf-8')).hexdigest()


def project_fixture(scene, object_id, projection='YX', fixture_id=None):
    """Project registered object-local geometry; object world transform ignored.

    This explicit choice lets users arrange 2D fixtures independently of 3D.
    No auto-centering, unit conversion, UV fitting or discarded-axis mutation.
    """
    if projection not in ('XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'):
        raise FixtureError('Choose XY, YX, XZ, ZX, YZ or ZY explicitly')
    obj = scene.object(object_id)
    scans = {scan.scan_id: scan for scan in scene.scans}
    axes = tuple('XYZ'.index(axis) for axis in projection)
    points, missing = [], []
    for led in obj.leds:
        scan = scans[led.scan_id]
        point = scan.registration.apply(scan.points[led.scan_index])
        points.append(tuple(point[axis] for axis in axes))
        if led.scan_index in scan.missing_indices:
            missing.append(led.led_id)
    return Fixture(fixture_id or str(uuid4()), object_id, obj.leds, tuple(points),
                   projection=projection, missing_ids=tuple(missing))


@dataclass(frozen=True)
class FixtureScene:
    scene_id: str
    scene_revision: str
    fixtures: tuple[Fixture, ...] = ()
    expected_count: int | None = None

    def __post_init__(self):
        _id(self.scene_id, 'scene_id')
        _id(self.scene_revision, 'scene_revision')
        if self.expected_count is not None and (isinstance(self.expected_count, bool) or not isinstance(self.expected_count, int) or self.expected_count < 0):
            raise FixtureError('expected_count must be a nonnegative integer')
        object.__setattr__(self, 'fixtures', tuple(self.fixtures))
        if any(not isinstance(item, Fixture) for item in self.fixtures):
            raise FixtureError('fixtures must contain Fixture values')
        if len({item.fixture_id for item in self.fixtures}) != len(self.fixtures):
            raise FixtureError('Duplicate fixture ID')
        leds = [led for fixture in self.fixtures for led in fixture.leds]
        for field in ('led_id', 'source_index'):
            if len({getattr(v, field) for v in leds}) != len(leds):
                raise FixtureError('Overlapping fixtures claim the same ' + field)
        local = [(fixture.object_id, led.local_index) for fixture in self.fixtures for led in fixture.leds]
        if len(set(local)) != len(local):
            raise FixtureError('Overlapping object-local indices')

    def fixture(self, fixture_id):
        for fixture in self.fixtures:
            if fixture.fixture_id == fixture_id:
                return fixture
        raise FixtureError('Unknown fixture ID: ' + fixture_id)

    def sampling_rows(self):
        return tuple(sorted((row for fixture in self.fixtures for row in fixture.sample_uv()), key=lambda row: row[0].source_index))

    def validate_source_scene(self, scene):
        if scene.scene_id != self.scene_id or scene_revision(scene) != self.scene_revision:
            raise FixtureError('3D scene changed: explicitly rebase/reproject fixture draft before apply')
        bindings = {(obj.object_id, led.led_id): led for obj in scene.objects for led in obj.leds}
        if any(bindings.get((fixture.object_id, led.led_id)) != led for fixture in self.fixtures for led in fixture.leds):
            raise FixtureError('Fixture no longer matches source LED bindings')


def add_fixture(scene, fixture):
    return replace(scene, fixtures=scene.fixtures + (fixture,))


def replace_transform(scene, fixture_id, domain, transform):
    if domain not in ('output', 'uv'):
        raise FixtureError('Choose output or uv domain explicitly')
    old = scene.fixture(fixture_id)
    updated = replace(old, **{domain + '_transform': transform})
    return replace(scene, fixtures=tuple(updated if item.fixture_id == fixture_id else item for item in scene.fixtures))


def export_sampling_uv(scene, *, bounds='reject', indent=2):
    """Dense source-index ordered UV array, never renumbers or silently clamps."""
    if bounds not in ('reject', 'preserve'):
        raise FixtureError('Choose reject or explicitly preserve out-of-bounds UV')
    rows = scene.sampling_rows()
    if scene.expected_count is not None and len(rows) != scene.expected_count:
        raise FixtureError('Fixture coverage does not match expected output count')
    if not rows or [led.source_index for led, _ in rows] != list(range(len(rows))):
        raise FixtureError('Global source coverage has gaps; refusing to renumber')
    if any(fixture.missing_ids for fixture in scene.fixtures):
        raise FixtureError('Missing points require verified rescan before export')
    if bounds == 'reject' and any(fixture.out_of_bounds_ids() for fixture in scene.fixtures):
        raise FixtureError('UV outside 0..1: adjust placement or explicitly preserve; no silent clamp')
    return json.dumps([point for _, point in rows], indent=indent, allow_nan=False)


def export_fixture_json(scene, *, indent=2):
    return json.dumps({'schema': SCHEMA, 'version': VERSION, **asdict(scene)}, indent=indent, allow_nan=False)


def import_fixture_json(text):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise FixtureError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    try:
        data = json.loads(text, object_pairs_hook=unique_pairs)
        if data.pop('schema', None) != SCHEMA or data.pop('version', None) != VERSION:
            raise FixtureError('Unsupported fixture schema/version')
        fixtures = []
        for entry in data.pop('fixtures'):
            entry['leds'] = tuple(LedBinding(**led) for led in entry['leds'])
            for field in ('output_transform', 'uv_transform'):
                entry[field] = Transform2D(**entry[field])
            fixtures.append(Fixture(**entry))
        return FixtureScene(fixtures=tuple(fixtures), **data)
    except (TypeError, KeyError, AttributeError, json.JSONDecodeError) as error:
        raise FixtureError('Malformed fixture document') from error


class FixtureHistory:
    """Draft-only undo/redo, including both independent transform domains."""
    def __init__(self, scene):
        if not isinstance(scene, FixtureScene):
            raise FixtureError('History needs a FixtureScene')
        self._current, self._undo, self._redo = scene, [], []

    @property
    def current(self):
        return self._current

    @property
    def can_undo(self):
        return bool(self._undo)

    @property
    def can_redo(self):
        return bool(self._redo)

    def commit(self, scene):
        if not isinstance(scene, FixtureScene) or (scene.scene_id, scene.scene_revision) != (self.current.scene_id, self.current.scene_revision):
            raise FixtureError('History cannot change source scene identity/revision')
        originals = {led.led_id: (fixture.object_id, led, point) for fixture in self.current.fixtures
                     for led, point in zip(fixture.leds, fixture.local_points)}
        if any(led.led_id in originals and originals[led.led_id] != (fixture.object_id, led, point)
               for fixture in scene.fixtures for led, point in zip(fixture.leds, fixture.local_points)):
            raise FixtureError('Cannot reassign stable IDs or mutate frozen local geometry')
        if scene != self.current:
            self._undo.append(self.current)
            self._current = scene
            self._redo.clear()
        return self.current

    def undo(self):
        if self._undo:
            self._redo.append(self.current)
            self._current = self._undo.pop()
        return self.current

    def redo(self):
        if self._redo:
            self._undo.append(self.current)
            self._current = self._redo.pop()
        return self.current
