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
    if type(settings) is not dict or set(settings) != required:
        raise ValueError('Invalid independent scan settings')
    for key in ('universe', 'count', 'rate'):
        if type(settings[key]) is not int:
            raise ValueError(key + ' must be an integer')
    if not 1 <= settings['count'] <= 100000:
        raise ValueError('LED count must be 1..100000')
    if not isinstance(settings['name'], str) or not settings['name'].strip():
        raise ValueError('A capture name is required')
    controller = ControllerConfig(settings['name'], settings['target'], settings['interface'],
        enabled=True, start_universe=settings['universe'], rate=settings['rate'],
        color_order=settings['order'], brightness=.05,
        reserved_universes=ceil(settings['count']/170))
    config = RouterConfig((controller,), (SegmentConfig('capture', 0, settings['count'], controller.name),),
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
