"""Isolated acquisition namespace: no existing layout, source CHOP or live route."""
from hashlib import sha256
import json
from math import ceil
from uuid import uuid4
from .multi_controller import ControllerConfig, SegmentConfig, RouterConfig
from .scan_routing import create_snapshot
from .scan_session import ScanSession, ScanTarget


def routing(settings):
    required = {'name', 'target', 'interface', 'universe', 'count', 'rate', 'order'}
    frame_keys = {'frame_start_universe', 'frame_universe_count'}
    if type(settings) is not dict or set(settings) not in (required, required | frame_keys):
        raise ValueError('Invalid independent scan settings')
    for key in ('universe', 'count', 'rate'):
        if type(settings[key]) is not int:
            raise ValueError(key + ' must be an integer')
    if not 1 <= settings['count'] <= 100000:
        raise ValueError('LED count must be 1..100000')
    if not isinstance(settings['name'], str) or not settings['name'].strip():
        raise ValueError('A capture name is required')
    first = settings.get('frame_start_universe', settings['universe'])
    frames = settings.get('frame_universe_count', ceil(settings['count']/170))
    if type(first) is not int or type(frames) is not int:
        raise ValueError('Controller frame start/count must be integers')
    panel_frames = ceil(settings['count']/170)
    if not (0 <= first <= settings['universe'] and frames > 0
            and first + frames <= 32768
            and settings['universe'] + panel_frames <= first + frames):
        raise ValueError('Controller frame range must contain every panel universe')
    controller = ControllerConfig(settings['name'], settings['target'], settings['interface'],
        enabled=True, start_universe=first, rate=settings['rate'],
        color_order=settings['order'], brightness=.05,
        reserved_universes=frames)
    config = RouterConfig((controller,), (SegmentConfig('capture', 0, settings['count'], controller.name,
                          destination_start=(settings['universe']-first)*170),),
                          source_pixel_count=settings['count'])
    create_snapshot(config, tuple(range(settings['count'])), brightness_cap=.05)
    return config


def revision(settings):
    return sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()


def session(settings):
    routing(settings)
    identifier = 'capture-' + str(uuid4())
    targets = tuple(ScanTarget(identifier + ':led:' + str(i), identifier, i, i)
                    for i in range(settings['count']))
    return ScanSession(identifier, identifier, revision(settings), targets,
                       tuple(t.led_id for t in targets))
