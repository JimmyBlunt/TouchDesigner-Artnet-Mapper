"""TouchDesigner bridge for explicit camera probe / reviewed single-view scans.

Transient handles live in this module only. All stored TD values are JSON data.
Installing the bridge never opens cameras or activates output.
"""
from dataclasses import asdict, replace
import math
from hashlib import sha256
import json
import threading
import time

from . import camera_probe, scan_capture, scan_output_guard
from .routing_transaction import router_from_rows, table_rows
from .scan_routing import create_snapshot
from .scan_session import ScanSession

OWNER = '/project1/guided_scan'
ROUTER = '/project1/multi_controller_output'
MARKER = '# GUIDED_SCAN_OUTPUT_GUARD_V1'
_probe = None
_capture = None
_token = None
_signature = None
_last_poll = 0.0
_probe_stop_thread = None


def _field(op, name):
    node = op(OWNER + '/ui_panel/' + name + '/string')
    if node is None:
        raise ValueError('Required scan field is missing: ' + name)
    if node.numRows == 0:
        return ''
    value = node[0, 0]
    return '' if value is None else str(value).strip()


def _camera(op):
    return camera_probe.prepare_camera_probe(int(_field(op, 'camera')),
        int(_field(op, 'exposure')), int(_field(op, 'threshold')))


def scan_brightness(op):
    node = op(OWNER + '/ui_panel/brightness/string')
    percent = float(_field(op, 'brightness')) if node is not None else 5.0
    if not math.isfinite(percent) or not 1 <= percent <= 10:
        raise ValueError('Scan brightness must be 1–10 percent')
    return percent / 100.0


def set_scan_brightness(op, fraction):
    if _capture is not None and _capture.process.poll() is None:
        _status(op, 'Brightness locked during capture; change it between views')
        return
    percent = round(1 + 9 * max(0.0, min(1.0, float(fraction))), 1)
    op(OWNER + '/ui_panel/brightness/string').text = str(percent)
    _status(op, 'Scan brightness %.1f%% — CHECK SCAN PLAN before the next view; Live unchanged' % percent)


def brightness_position(op):
    """Read-only visual binding; incomplete keyboard input must not break drawing."""
    try:
        return (scan_brightness(op) * 100 - 1) / 9
    except (ValueError, TypeError):
        return 0.0


def _status(op, message):
    op(OWNER).store('message', message)
    op(OWNER + '/ui_panel/status').par.text = message


def _routing_signature(op):
    paths = [ROUTER + '/controller_config', ROUTER + '/segment_config',
             ROUTER + '/gico_port_config/ports',
             ROUTER + '/gico_port_config/settings']
    values = {p: op(p).text if op(p) is not None else None for p in paths}
    values['source_count'] = op('/project1/math1').numSamples
    values['session'] = op(OWNER).fetch('session', None)
    values['standalone'] = op(OWNER).fetch('standalone_capture', None)
    values['requested_scope'] = [_field(op, 'source_ids'), _field(op, 'anchors')]
    layout = op('/project1/layout_scene_editor')
    values['layout_workspace'] = layout.fetch('workspace', None) if layout is not None else None
    for name in ('draft_document', 'fixture_document'):
        node = layout.op(name) if layout is not None else None
        values[name] = node.text if node is not None else None
    return sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def native_outputs(op):
    return [n for n in op('/project1').findChildren() if n.type == 'dmxout']


def assert_outputs_off(op):
    if op(ROUTER + '/artnet_510_sender_callbacks').module.status().get('enabled'):
        raise RuntimeError('Stop Live/Calibration output in the router before scanning')
    active = [n.path for n in native_outputs(op) if bool(n.par.active.eval())]
    if active:
        raise RuntimeError('Native Art-Net output is active: ' + ', '.join(active))


def guard_sender_source(source):
    if MARKER in source:
        return source
    entry = '    if not value:\n        return True\n'
    if source.count(entry) != 1:
        raise ValueError('Unreviewed sender implementation; cannot install scan guard')
    # The existing sender stops first. Denied starts therefore stay OFF.
    return source.replace(entry, entry + '    ' + MARKER + '\n'
        '    from pixelblaze_mapper.scan_output_guard import assert_no_scan\n'
        '    assert_no_scan()\n', 1)


def install_sender_guard(op):
    node = op(ROUTER + '/artnet_510_sender_callbacks')
    if MARKER in node.text:
        return False
    assert_outputs_off(op)
    node.text = guard_sender_source(node.text)
    return True


def stage_standalone(op, settings):
    from .standalone_scan import session
    if _capture is not None and _capture.process.poll() is None:
        raise RuntimeError('Stop the current scan before creating another acquisition')
    state = session(settings)
    owner = op(OWNER)
    owner.store('standalone_capture', dict(settings))
    owner.store('session', state.to_dict())
    owner.store('capture_status', {})
    for key in ('capture_plan', 'capture_signature', 'manifest', 'candidate', 'merge_request'):
        owner.store(key, None)
    op(OWNER + '/ui_panel/source_ids/string').text = '0-%d' % (settings['count']-1)
    for key in ('anchors', 'views'):
        op(OWNER + '/ui_panel/' + key + '/string').text = ''
    _status(op, 'NEW ACQUISITION — local LED IDs only; no layout or live router changed. CHECK SCAN PLAN next.')
    return state


def prepare(op):
    from .build_scan_session_ui import select_scope
    if _capture is not None and _capture.process.poll() is None:
        raise RuntimeError('Stop current capture before changing the plan')
    state = select_scope(ScanSession.from_dict(op(OWNER).fetch('session')),
                         _field(op, 'source_ids'), _field(op, 'anchors'))
    layout = op('/project1/layout_scene_editor')
    draft = layout.op('draft_document') if layout is not None else None
    standalone = op(OWNER).fetch('standalone_capture', None)
    if standalone is not None:
        from .standalone_scan import routing, revision
        if state.scene_revision != revision(standalone):
            raise RuntimeError('Capture settings changed; create a new acquisition')
        config = routing(standalone)
    elif draft is not None:
        from .layout_scene_adapter import load_document_json, scene_revision
        if scene_revision(load_document_json(draft.text).scene) != state.scene_revision:
            raise RuntimeError('Layout changed: stage the object from Layout again before preparing a scan')
    op(OWNER).store('session', state.to_dict())
    lookup = {target.led_id: target.source_index for target in state.targets}
    source_ids = tuple(lookup[item] for item in state.capture_ids)
    if standalone is None:
        config = router_from_rows(table_rows(op(ROUTER + '/controller_config')),
            table_rows(op(ROUTER + '/segment_config')), op('/project1/math1').numSamples)
    brightness = scan_brightness(op)
    # Detached scan-only configuration: do not modify live controller brightness.
    config = replace(config, controllers=tuple(replace(c, brightness=brightness) for c in config.controllers))
    snapshot = create_snapshot(config, source_ids, brightness_cap=brightness)
    plan = scan_capture.prepare_capture(snapshot, asdict(_camera(op)), _field(op, 'workspace'))
    plan['identity'] = {str(index): target.led_id for target in state.targets
                        for index in [target.source_index] if index in source_ids}
    plan['scene_revision'] = state.scene_revision
    op(OWNER).store('capture_plan', plan)
    op(OWNER).store('capture_signature', _routing_signature(op))
    op(OWNER + '/worker_plan').text = json.dumps(plan, indent=2)
    op(OWNER + '/dry_run').text = json.dumps([asdict(s) for s in state.dry_run_schedule()], indent=2)
    lines = []
    for name in snapshot.controller_names:
        frames = [f for f in snapshot.packet_descriptors() if f.controller == name]
        lines.append('%s %s | Art-Net U%d-U%d (ab 0)' %
            (name, frames[0].target_address, frames[0].wire_universe,
             frames[-1].wire_universe))
    summary = '%s%d LEDs | 510 channels | scan %.1f%% | %s' % ('SEPARATE CAPTURE | ' if standalone else '', len(source_ids), brightness * 100, '; '.join(lines))
    if standalone is not None and 'frame_start_universe' in standalone:
        from math import ceil
        summary = ('SEPARATE CAPTURE | %d LEDs | scan %.1f%%\n'
                   '%s %s | PANEL U%d-U%d | SEND U%d-U%d; other slots BLACK') % (
            len(source_ids), brightness * 100, standalone['name'], standalone['target'],
            standalone['universe'], standalone['universe'] + ceil(standalone['count']/170) - 1,
            standalone['frame_start_universe'],
            standalone['frame_start_universe'] + standalone['frame_universe_count'] - 1)
    op(OWNER + '/ui_panel/routing_summary').par.text = summary
    _status(op, 'PLAN READY — no camera or output started. Scan blacks ALL reserved universes of listed controllers.')
    return summary


def camera_start(op):
    global _probe
    if _capture is not None and _capture.process.poll() is None:
        raise RuntimeError('Camera belongs to capture; stop scan first')
    _probe = camera_probe.start_camera_probe(_camera(op), confirmed=True)
    _status(op, 'CAMERA OPENING — native MariMapper preview; no LEDs sent, no images saved')


def camera_stop(op):
    global _probe_stop_thread
    if _probe is not None and (_probe_stop_thread is None or not _probe_stop_thread.is_alive()):
        _probe_stop_thread = threading.Thread(target=camera_probe.stop_camera_probe,
                                               args=(_probe,), daemon=True)
        _probe_stop_thread.start()
    _status(op, 'CAMERA STOP requested — waiting for device release')


def start(op, *, confirmed=False):
    global _capture, _token, _signature
    if confirmed is not True:
        raise ValueError('Review the controller blackout domain and confirm Scan Start')
    if _probe is not None and _probe.process.poll() is None:
        raise RuntimeError('Stop camera preview before starting a scan')
    if _capture is not None and _capture.process.poll() is None:
        raise RuntimeError('A scan is already running')
    plan = op(OWNER).fetch('capture_plan', None)
    if plan is None or op(OWNER).fetch('capture_signature', '') != _routing_signature(op):
        raise RuntimeError('Prepare the plan again: routing or scan scope changed')
    if plan['routing']['brightness_cap'] != scan_brightness(op):
        raise RuntimeError('Scan brightness changed; CHECK SCAN PLAN again')
    if plan['camera'] != asdict(_camera(op)) or plan['workspace'] != str(__import__('pathlib').Path(_field(op, 'workspace')).resolve()):
        raise RuntimeError('Camera/workspace changed; prepare the plan again')
    assert_outputs_off(op)
    install_sender_guard(op)
    token = scan_output_guard.acquire()
    try:
        _capture = scan_capture.start_capture(plan, confirmed=True)
    except Exception:
        scan_output_guard.release(token)
        raise
    _token = token
    _signature = _routing_signature(op)
    op(OWNER).store('capture_status', dict(_capture.status, state='starting',
        processed=0, detected=0, total=len(plan['routing']['source_indices']),
        current_index=None, current_source_index=None))
    from .scan_capture_progress import refresh
    refresh(op(OWNER))
    _status(op, 'SCAN STARTING — keep camera and object still; STOP aborts; Live stays off')


def stop(op):
    if _capture is not None:
        scan_capture.stop_capture(_capture)
    camera_stop(op)
    _status(op, 'STOP requested — scan output will send black; animation will not resume automatically')


def poll(op):
    global _last_poll, _token
    now = time.monotonic()
    if now - _last_poll < 0.5:
        return
    _last_poll = now
    if _capture is not None and _token is not None:
        try:
            assert_outputs_off(op)
            if _signature != _routing_signature(op):
                raise RuntimeError('Routing/scope changed during scan')
            if MARKER not in op(ROUTER + '/artnet_510_sender_callbacks').text:
                raise RuntimeError('Sender rebuilt while scanning')
        except Exception as error:
            scan_capture.stop_capture(_capture)
            _capture.status['application_abort_reason'] = str(error)
            _status(op, 'SCAN ABORT — ' + str(error))
        status = scan_capture.poll_capture(_capture)
        op(OWNER).store('capture_status', status)
        from .scan_capture_progress import refresh
        refresh(op(OWNER))
        _status(op, 'SCAN %s | %s/%s | %s' % (status.get('state'), status.get('processed', 0),
            status.get('total', '?'), status.get('application_abort_reason', status.get('error', 'camera fixed; Live remains OFF'))))
        if not status['running']:
            scan_output_guard.release(_token)
            _token = None
            if status.get('view_csv') and status.get('state') == 'complete':
                current = _field(op, 'views')
                paths = [p.strip() for p in current.split('|') if p.strip() and p.strip() != 'None']
                if status['view_csv'] not in paths:
                    paths.append(status['view_csv'])
                    op(OWNER + '/ui_panel/views/string').text = ' | '.join(paths)
                _status(op, 'VIEW SAVED — reposition camera, then START NEXT VIEW. 3D reconstruction/review remains a separate step.')
    elif _probe is not None:
        status = camera_probe.poll_camera_probe(_probe)
        op(OWNER).store('camera_status', status)
        text = 'CAMERA %s | %sx%s | frames %s | %s' % (status.get('state'),
            status.get('width', '?'), status.get('height', '?'), status.get('frames', 0), status.get('error', 'LED output untouched'))
        op(OWNER + '/ui_panel/camera_status').par.text = text
        if (status.get('state') == 'stopped'
                and str(op(OWNER).fetch('message', '')).startswith('CAMERA STOP requested')):
            _status(op, 'CAMERA CLOSED — device released; no LED output started'
                    if status.get('cleanup_confirmed') else
                    'CAMERA STOPPED — device cleanup was not confirmed')


def shutdown():
    if _capture is not None:
        scan_capture.stop_capture(_capture)
    if _probe is not None:
        threading.Thread(target=camera_probe.stop_camera_probe, args=(_probe,), daemon=True).start()
