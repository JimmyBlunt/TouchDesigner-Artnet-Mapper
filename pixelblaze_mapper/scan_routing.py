"""Pure scan payloads from an explicit canonical router, never from defaults.

No socket, camera, TouchDesigner, lease acquisition, file access, or output
activation. A snapshot identifies data to review; its hash is NOT authorization.
Only controllers carrying selected LEDs are included in the scan frame domain.
Every included controller's full reserved/derived universe span is black except
for the single selected target. In particular, unselected LEDs on those
controllers are intentionally black: a future lease must authorize that domain.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
from hashlib import sha256
import json
from math import isfinite

from .multi_controller import ControllerConfig, RouterConfig, SegmentConfig, build_router_plan
from .realtime_packer import compile_router_packer


SCHEMA = 'pixelblaze-scan-routing'
VERSION = 1
MAX_SCAN_BRIGHTNESS = 0.1


class ScanRoutingError(ValueError):
    """Invalid, ambiguous or unscannable source selection/snapshot."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _index(value, count, label):
    if type(value) is not int or not 0 <= value < count:
        raise ScanRoutingError('%s must be an integer in 0..%d' % (label, count - 1))
    return value


@dataclass(frozen=True)
class ScanTargetRoute:
    worker_index: int
    source_index: int
    controller: str
    frame_index: int
    wire_universe: int
    slot: int
    component_indices: tuple[int, int, int]


@dataclass(frozen=True)
class ScanFrame:
    """Addressed payload descriptor, NOT a sent packet or delivery receipt."""
    controller: str
    target_address: str
    local_interface: str
    port: int
    wire_universe: int
    rate: int
    art_sync: bool
    payload: bytes


@dataclass(frozen=True)
class ScanRoutingSnapshot:
    """Immutable, validated dense-index mapping and original routing model.

    Physical port labels are not inferred from segments: the canonical router
    supplies exact destination slots/universes, including six-universe blocks,
    arbitrary base universes and non-aligned prefixes. Hardware port metadata
    and scene/lease identity can be bound by the caller's larger manifest.
    """
    config: RouterConfig
    source_indices: tuple[int, ...]
    brightness_cap: float = MAX_SCAN_BRIGHTNESS
    targets: tuple[ScanTargetRoute, ...] = field(init=False)
    controller_names: tuple[str, ...] = field(init=False)
    _packers: tuple = field(init=False, repr=False, compare=False)
    _plans: tuple = field(init=False, repr=False, compare=False)
    _black: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self.config, RouterConfig):
            raise ScanRoutingError('An explicit RouterConfig is required; no routing defaults')
        cap = self.brightness_cap
        if type(cap) not in (int, float) or not isfinite(cap) or not 0 < cap <= MAX_SCAN_BRIGHTNESS:
            raise ScanRoutingError('brightness_cap must be finite in (0, 0.1]')
        object.__setattr__(self, 'brightness_cap', float(cap))
        # Tuples detach caller-provided lists; nested canonical models are frozen.
        config = replace(self.config, controllers=tuple(self.config.controllers), segments=tuple(self.config.segments))
        if (type(config.warn_unassigned) is not bool or
                any(not isinstance(c, ControllerConfig) or type(c.enabled) is not bool for c in config.controllers) or
                any(not isinstance(s, SegmentConfig) for s in config.segments)):
            raise ScanRoutingError('Expected canonical controllers/segments and boolean flags')
        object.__setattr__(self, 'config', config)
        try:
            plan = build_router_plan(config)
        except (ValueError, TypeError, AttributeError) as error:
            raise ScanRoutingError('Invalid router: ' + str(error)) from error
        selected = tuple(self.source_indices)
        if not selected:
            raise ScanRoutingError('Scan source selection must not be empty')
        for source in selected:
            _index(source, config.source_pixel_count, 'source_index')
        if len(set(selected)) != len(selected):
            raise ScanRoutingError('Duplicate source_index')
        object.__setattr__(self, 'source_indices', selected)
        compiled = compile_router_packer(plan)
        by_source = {source: [] for source in selected}
        disabled = set()
        for controller in plan.controllers:
            for write in compiled.controller(controller.config.name).writes:
                if write.source_index not in by_source:
                    continue
                if not controller.config.enabled:
                    disabled.add(write.source_index)
                    continue
                by_source[write.source_index].append((controller, write))
        targets = []
        for dense, source in enumerate(selected):
            matches = by_source[source]
            if not matches:
                reason = 'disabled controller' if source in disabled else 'unrouted source'
                raise ScanRoutingError('%s: %d' % (reason, source))
            if len(matches) != 1:
                raise ScanRoutingError('Ambiguous active routing for source_index %d' % source)
            controller, write = matches[0]
            targets.append(ScanTargetRoute(dense, source, controller.config.name,
                write.frame_index, controller.routes[write.frame_index].linear_universe,
                write.slot, write.component_indices))
        object.__setattr__(self, 'targets', tuple(targets))
        selected_controllers = {target.controller for target in targets}
        packers = tuple(replace(p, brightness=min(p.brightness, float(cap)))
                        for p in compiled.controllers if p.name in selected_controllers)
        if any(round(255.0 * p.brightness) < 1 for p in packers):
            raise ScanRoutingError('Configured/capped brightness rounds to black; target is unscannable')
        object.__setattr__(self, 'controller_names', tuple(p.name for p in packers))
        object.__setattr__(self, '_packers', packers)
        object.__setattr__(self, '_plans', tuple(p for p in plan.controllers if p.config.name in selected_controllers))
        object.__setattr__(self, '_black', tuple((p.name, tuple(bytes(510) for _ in range(p.frame_count))) for p in packers))
        # Also reject non-JSON canonical data before any snapshot is usable.
        try:
            _json(self._document())
        except (ValueError, TypeError) as error:
            raise ScanRoutingError('Routing is not finite plain JSON data') from error

    def get_led_count(self):
        return len(self.source_indices)

    def source_index(self, worker_index):
        return self.source_indices[_index(worker_index, self.get_led_count(), 'worker_index')]

    def worker_index(self, source_index):
        _index(source_index, self.config.source_pixel_count, 'source_index')
        try:
            return self.source_indices.index(source_index)
        except ValueError as error:
            raise ScanRoutingError('Source is outside the frozen scan selection') from error

    def black_frames(self):
        return black_frames(self)

    def single_led_frames(self, worker_index, on=True):
        return single_led_frames(self, worker_index, on=on)

    def packet_descriptors(self, worker_index=None, *, on=False):
        """Full-domain addressed frames; omit index for explicit all-black.

        ``on=True`` requires a valid dense index. Each descriptor's wire
        universe comes directly from the canonical plan, with no UI conversion.
        ``art_sync`` merely reports configuration; this function does not
        construct an ArtSync packet, start a sender, or acknowledge delivery.
        """
        if type(on) is not bool:
            raise ScanRoutingError('on must be boolean')
        if worker_index is None:
            if on:
                raise ScanRoutingError('An ON frame requires a worker_index')
            frames = black_frames(self)
        else:
            frames = single_led_frames(self, worker_index, on=on)
        return tuple(ScanFrame(plan.config.name, plan.config.target_address,
                               plan.config.local_interface, plan.config.port,
                               route.linear_universe, plan.config.rate,
                               plan.config.art_sync, payload)
                     for plan in self._plans
                     for route, payload in zip(plan.routes, frames[plan.config.name]))

    def _document(self):
        return {'schema': SCHEMA, 'version': VERSION,
                'routing': asdict(self.config), 'source_indices': list(self.source_indices),
                'brightness_cap': self.brightness_cap,
                'controller_names': list(self.controller_names),
                'targets': [asdict(target) for target in self.targets]}

    @property
    def fingerprint(self):
        return sha256(_json(self._document()).encode('utf-8')).hexdigest()

    def to_dict(self):
        """Return detached JSON data; original and capped brightness are distinct.

        The original brightness is in routing.controllers; effective brightness
        is min(original, brightness_cap). Fingerprint binds all source routes,
        including currently unselected/disabled ones, and the scan selection.
        """
        document = json.loads(_json(self._document()))
        document['fingerprint'] = self.fingerprint
        return document

    @classmethod
    def from_dict(cls, document):
        """Rebuild and compare all derived addresses; never trust supplied slots."""
        try:
            required = {'schema', 'version', 'routing', 'source_indices', 'brightness_cap',
                        'controller_names', 'targets', 'fingerprint'}
            if not isinstance(document, dict) or set(document) != required:
                raise ScanRoutingError('Unexpected scan snapshot fields')
            if document['schema'] != SCHEMA or type(document['version']) is not int or document['version'] != VERSION:
                raise ScanRoutingError('Unsupported scan snapshot schema/version')
            routing = document['routing']
            if set(routing) != {f.name for f in fields(RouterConfig)}:
                raise ScanRoutingError('Unexpected router fields')
            def items(model, rows):
                expected = {f.name for f in fields(model)}
                if not isinstance(rows, list) or any(not isinstance(row, dict) or set(row) != expected for row in rows):
                    raise ScanRoutingError('Incomplete or unexpected routing record fields')
                return tuple(model(**row) for row in rows)
            if not isinstance(document['source_indices'], list):
                raise ScanRoutingError('source_indices must be an explicit list')
            config = RouterConfig(items(ControllerConfig, routing['controllers']),
                                  items(SegmentConfig, routing['segments']),
                                  routing['source_pixel_count'], routing['warn_unassigned'])
            snapshot = cls(config, tuple(document['source_indices']), document['brightness_cap'])
            if _json(document) != _json(snapshot.to_dict()):
                raise ScanRoutingError('Snapshot fingerprint/derived routing mismatch')
            return snapshot
        except (KeyError, TypeError, AttributeError) as error:
            raise ScanRoutingError('Malformed scan routing snapshot') from error


def create_snapshot(config, source_indices, *, brightness_cap=MAX_SCAN_BRIGHTNESS):
    return ScanRoutingSnapshot(config, tuple(source_indices), brightness_cap)


def black_frames(snapshot):
    """Fresh controller dictionary of immutable, full-reserve 510-byte frames."""
    if not isinstance(snapshot, ScanRoutingSnapshot):
        raise ScanRoutingError('Validated ScanRoutingSnapshot required')
    return dict(snapshot._black)


def single_led_frames(snapshot, worker_index, *, on=True):
    """Stateless MariMapper-index operation; returns payloads, never sends them.

    Even an OFF request validates its index so a stale/different scan cannot
    silently operate this domain. Every call blacks any previously lit target.
    """
    if not isinstance(snapshot, ScanRoutingSnapshot):
        raise ScanRoutingError('Validated ScanRoutingSnapshot required')
    source = snapshot.source_index(worker_index)
    if type(on) is not bool:
        raise ScanRoutingError('on must be boolean')
    if not on:
        return black_frames(snapshot)
    channel = [0.0] * snapshot.config.source_pixel_count
    channel[source] = 1.0
    return {p.name: p.pack_channels(channel, channel, channel) for p in snapshot._packers}
