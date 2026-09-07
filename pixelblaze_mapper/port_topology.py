"""Hardware-aware controller/port drafts, independent of TouchDesigner/network.

GICO exposes equal fixed hardware blocks. Generic independent-port profiles
are explicitly user-selected capabilities, not a claim about arbitrary devices.
"""

from dataclasses import dataclass, replace
from math import ceil

from pixelblaze_mapper.multi_controller import (
    ControllerConfig, RouterConfig, SegmentConfig, build_router_plan,
)


PROFILES = ('gico_equal', 'independent')
PIXELS_PER_UNIVERSE = 170


@dataclass(frozen=True)
class PortDraft:
    number: int
    label: str = ''
    enabled: bool = True
    source_start: int | None = None
    pixel_count: int = 0
    reserved_universes: int = 6
    reverse: bool = False
    color_order: str = 'GRB'
    # None allocates after the preceding reserved block. An explicit target
    # preserves existing non-aligned routes such as the APA102 prefix at 512.
    destination_start: int | None = None


@dataclass(frozen=True)
class ControllerDraft:
    controller: ControllerConfig
    profile: str
    ports: tuple[PortDraft, ...]


@dataclass(frozen=True)
class PortPlan:
    port: PortDraft
    destination_start: int
    capacity_pixels: int
    used_universes: int
    first_wire_universe: int
    last_wire_universe: int

    @property
    def routable(self):
        return self.port.enabled and self.port.source_start is not None and self.port.pixel_count > 0


@dataclass(frozen=True)
class TopologyPlan:
    draft: ControllerDraft
    controller: ControllerConfig
    ports: tuple[PortPlan, ...]
    segments: tuple[SegmentConfig, ...]


def ui_to_wire(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 32768:
        raise ValueError('First UI universe must be 1..32768')
    return value - 1


def wire_to_ui(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 32767:
        raise ValueError('Wire universe must be 0..32767')
    return value + 1


def _integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def build_topology(draft, *, source_pixels=3744):
    if draft.profile not in PROFILES:
        raise ValueError('Profile must be gico_equal or independent')
    numbers = [port.number for port in draft.ports]
    if any(not _integer(number, 1) for number in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError('Port numbers must be unique positive integers')
    if draft.profile == 'gico_equal' and len({port.reserved_universes for port in draft.ports}) > 1:
        raise ValueError('GICO hardware requires the same reserved universe count for every port')
    if draft.profile == 'gico_equal' and set(numbers) != {1, 2, 3, 4}:
        raise ValueError('This GICO hardware profile has four fixed physical slots; use disabled ports instead of removing slots')
    if draft.controller.name == 'WS2812_NODE' and draft.profile != 'gico_equal':
        raise ValueError('Known WS2812_NODE is GICO hardware; independent port capacities are not supported')
    plans, segments, blocks, sources = [], [], [], []
    next_pixel = 0
    for port in sorted(draft.ports, key=lambda item: item.number):
        if not _integer(port.reserved_universes, 1):
            raise ValueError('Port %d: reserve must be a positive universe count' % port.number)
        if not _integer(port.pixel_count):
            raise ValueError('Port %d: pixel count must be nonnegative' % port.number)
        if not isinstance(port.enabled, bool) or not isinstance(port.reverse, bool):
            raise ValueError('Port flags must be boolean')
        if not isinstance(port.label, str):
            raise ValueError('Port label must be text')
        if port.color_order not in ('RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR'):
            raise ValueError('Port color order must be an RGB permutation')
        if port.source_start is not None and not _integer(port.source_start):
            raise ValueError('Port source start must be nonnegative or blank')
        fixed_start = (port.number - 1) * port.reserved_universes * PIXELS_PER_UNIVERSE
        destination = (fixed_start if draft.profile == 'gico_equal' else next_pixel)
        if port.destination_start is not None:
            if not _integer(port.destination_start):
                raise ValueError('Target start must be nonnegative or automatic')
            if draft.profile == 'gico_equal' and port.destination_start != fixed_start:
                raise ValueError('GICO target starts are fixed by physical port number')
            destination = port.destination_start
        first_block = destination // PIXELS_PER_UNIVERSE
        end = (first_block + port.reserved_universes) * PIXELS_PER_UNIVERSE
        capacity = end - destination
        if port.pixel_count > capacity:
            raise ValueError('Port %d: %d pixels exceed capacity %d' % (port.number, port.pixel_count, capacity))
        block_start = first_block * PIXELS_PER_UNIVERSE
        if any(max(block_start, start) < min(end, stop) for start, stop in blocks):
            raise ValueError('Reserved port universe blocks overlap')
        blocks.append((block_start, end))
        next_pixel = max(next_pixel, end)
        used = ceil((destination % PIXELS_PER_UNIVERSE + port.pixel_count) / PIXELS_PER_UNIVERSE) if port.pixel_count else 0
        item = PortPlan(port, destination, capacity, used,
                        draft.controller.start_universe + first_block,
                        draft.controller.start_universe + first_block + port.reserved_universes - 1)
        plans.append(item)
        if item.routable:
            end_source = port.source_start + port.pixel_count
            if end_source > source_pixels:
                raise ValueError('Port %d exceeds the %d-pixel source' % (port.number, source_pixels))
            if any(max(port.source_start, start) < min(end_source, stop) for start, stop in sources):
                raise ValueError('Source ranges within this controller overlap')
            sources.append((port.source_start, end_source))
            segments.append(SegmentConfig('PORT_%s_%d' % (draft.controller.name, port.number),
                port.source_start, port.pixel_count, draft.controller.name, destination,
                port.reverse, port.color_order))
    controller = replace(draft.controller, reserved_universes=ceil(next_pixel / PIXELS_PER_UNIVERSE))
    build_router_plan(RouterConfig((controller,), tuple(segments), source_pixel_count=source_pixels))
    return TopologyPlan(draft, controller, tuple(plans), tuple(segments))


def merge_controller(config, draft, *, source_pixels=None):
    """Create or replace only the selected identity; preserve every other route."""
    count = config.source_pixel_count if source_pixels is None else source_pixels
    plan = build_topology(draft, source_pixels=count)
    controllers = tuple(item for item in config.controllers if item.name != draft.controller.name) + (plan.controller,)
    segments = tuple(item for item in config.segments if item.controller != draft.controller.name) + plan.segments
    result = RouterConfig(controllers, segments, source_pixel_count=count)
    build_router_plan(result)
    return result


def remove_controller(config, name):
    if name not in {controller.name for controller in config.controllers}:
        raise ValueError('Unknown controller: ' + name)
    result = replace(config, controllers=tuple(item for item in config.controllers if item.name != name),
                     segments=tuple(item for item in config.segments if item.controller != name))
    build_router_plan(result)
    return result


def add_port(draft, port=None):
    number = max((item.number for item in draft.ports), default=0) + 1
    reserve = draft.ports[0].reserved_universes if draft.ports and draft.profile == 'gico_equal' else 1
    item = port or PortDraft(number, 'Port %d' % number, False, reserved_universes=reserve)
    if item.number in {existing.number for existing in draft.ports}:
        raise ValueError('Port number already exists')
    return replace(draft, ports=draft.ports + (item,))


def remove_port(draft, number):
    if number not in {item.number for item in draft.ports}:
        raise ValueError('Unknown port')
    return replace(draft, ports=tuple(item for item in draft.ports if item.number != number))
