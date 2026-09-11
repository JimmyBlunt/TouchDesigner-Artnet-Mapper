"""Explicit, supervised single-view MariMapper capture launcher.

No launch on import/prepare. The caller must acquire application output ownership
and keep polling (heartbeats). Captures create a NEW directory, never overwrite
maps. A result is 2D observations, not an automatically merged 3D layout.
"""
from dataclasses import dataclass, field
import json
from math import isfinite
from pathlib import Path
import queue
import subprocess
import threading
import time
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe')


def prepare_capture(snapshot, camera, workspace, *, identity=None, scene_revision=None, packet_gap_ms=None):
    from .scan_routing import ScanRoutingSnapshot
    # Round trip validates serialized routing, not just a caller supplied hash.
    checked = ScanRoutingSnapshot.from_dict(snapshot.to_dict())
    from .camera_probe import prepare_camera_probe
    if type(camera) is not dict or set(camera) != {'device', 'exposure', 'threshold'}:
        raise ValueError('Camera needs exactly device, exposure and threshold')
    probe = prepare_camera_probe(device=camera['device'], exposure=camera['exposure'],
                                 threshold=camera['threshold'])
    del probe
    folder = Path(workspace).resolve(strict=True)
    if not folder.is_dir():
        raise ValueError('Choose an existing scan workspace folder')
    plan = {'schema': 'pixelblaze-single-view-capture', 'version': 1,
            'routing': checked.to_dict(), 'camera': dict(camera),
            'workspace': str(folder), 'directory_name': 'capture-' + str(uuid4()),
            'heartbeat_seconds': 5.0, 'max_led_seconds': 30.0}
    if packet_gap_ms is not None:
        if type(packet_gap_ms) not in (int, float) or not isfinite(packet_gap_ms) or not 0 <= packet_gap_ms <= 2:
            raise ValueError('packet_gap_ms must be finite in 0..2 ms')
        plan['packet_gap_ms'] = float(packet_gap_ms)
    if identity is not None or scene_revision is not None:
        if (type(identity) is not dict or set(identity) != {str(i) for i in checked.source_indices}
                or any(type(value) is not str or not value.strip() for value in identity.values())
                or len(set(identity.values())) != len(identity)
                or type(scene_revision) is not str or not scene_revision.strip()):
            raise ValueError('Identity metadata requires exact source-ID coverage, unique LED IDs and scene revision')
        plan.update(identity=dict(identity), scene_revision=scene_revision)
    return plan


def validate_capture_manifest(plan):
    """Validate full plain-data boundary without starting or creating anything."""
    from .scan_routing import ScanRoutingSnapshot
    fields = {'schema', 'version', 'routing', 'camera', 'workspace', 'directory_name',
              'heartbeat_seconds', 'max_led_seconds'}
    if type(plan) is not dict or set(plan) - {'packet_gap_ms'} not in (fields, fields | {'identity', 'scene_revision'}):
        raise ValueError('Invalid capture manifest fields')
    if 'packet_gap_ms' in plan and plan['packet_gap_ms'] is None:
        raise ValueError('Explicit null packet_gap_ms is invalid')
    if (plan['schema'] != 'pixelblaze-single-view-capture' or type(plan['version']) is not int
            or plan['version'] != 1 or type(plan['heartbeat_seconds']) not in (int, float)
            or plan['heartbeat_seconds'] != 5.0 or type(plan['max_led_seconds']) not in (int, float)
            or plan['max_led_seconds'] != 30.0):
        raise ValueError('Unsupported capture manifest/timing')
    name = plan['directory_name']
    if type(name) is not str or not name.startswith('capture-'):
        raise ValueError('Invalid capture directory name')
    if name != 'capture-' + str(UUID(name[8:])):
        raise ValueError('Capture directory must have a canonical generated ID')
    checked = prepare_capture(ScanRoutingSnapshot.from_dict(plan['routing']), plan['camera'], plan['workspace'],
                              identity=plan.get('identity'), scene_revision=plan.get('scene_revision'),
                              packet_gap_ms=plan.get('packet_gap_ms'))
    if 'identity' in plan and 'identity' not in checked:
        raise ValueError('Explicit null identity metadata is invalid')
    checked['directory_name'] = name
    return checked


@dataclass
class CaptureHandle:
    process: object
    directory: Path
    messages: object = field(default_factory=queue.Queue)
    status: dict = field(default_factory=lambda: {'state': 'starting', 'blackout_sent': False})
    last_heartbeat: float = 0.0
    stop_requested: bool = False


def _read(handle, stream, kind):
    try:
        for line in stream:
            if kind == 'status':
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        handle.messages.put(value)
                except ValueError:
                    pass
            # Native libraries can write stderr: drain without retaining images,
            # unbounded logs, or mistaking native text for protocol success.
    finally:
        stream.close()


def start_capture(plan, *, confirmed=False):
    if confirmed is not True:
        raise ValueError('Explicit scan confirmation is required')
    plan = validate_capture_manifest(plan)
    from .scan_routing import ScanRoutingSnapshot
    checked = prepare_capture(ScanRoutingSnapshot.from_dict(plan['routing']),
                              plan['camera'], plan['workspace'], identity=plan.get('identity'),
                              scene_revision=plan.get('scene_revision'), packet_gap_ms=plan.get('packet_gap_ms'))
    if plan.get('schema') != checked['schema'] or plan.get('version') != 1:
        raise ValueError('Invalid capture plan')
    # Use a fresh directory even for repeated starts of the same prepared plan.
    directory = Path(checked['workspace']) / checked['directory_name']
    directory.mkdir(exist_ok=False)
    manifest = directory / 'capture.json'
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(checked, stream, indent=2)
    process = subprocess.Popen([str(PYTHON), '-u', '-m',
        'pixelblaze_mapper.scan_capture_worker', str(manifest), '--confirm-capture'],
        cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, bufsize=1, shell=False,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    handle = CaptureHandle(process, directory, status={
        'state': 'starting', 'processed': 0, 'detected': 0,
        'total': len(checked['routing']['source_indices']),
        'current_index': None, 'current_source_index': None, 'blackout_sent': False})
    for stream, kind in ((process.stdout, 'status'), (process.stderr, 'stderr')):
        threading.Thread(target=_read, args=(handle, stream, kind), daemon=True).start()
    return handle


def poll_capture(handle):
    while True:
        try:
            handle.status.update(handle.messages.get_nowait())
        except queue.Empty:
            break
    code = handle.process.poll()
    if code is None and not handle.stop_requested and time.monotonic() - handle.last_heartbeat >= 0.5:
        try:
            handle.process.stdin.write('{"action":"heartbeat"}\n')
            handle.process.stdin.flush()
            handle.last_heartbeat = time.monotonic()
        except (OSError, ValueError):
            handle.status.update(state='connection_lost', blackout_confirmed=False)
    if code is not None:
        handle.status['exit_code'] = code
        if code != 0 and handle.status.get('state') == 'complete':
            handle.status.update(state='failed', error='Worker exited abnormally after completion message',
                                 blackout_confirmed=False)
        elif handle.status.get('state') not in ('complete', 'cancelled', 'failed'):
            handle.status.update(state='failed', error='Worker exited without final status',
                                 blackout_confirmed=False)
    return dict(handle.status, directory=str(handle.directory), running=code is None)


def stop_capture(handle):
    """Nonblocking stop: parent stays responsive while worker blacks out."""
    handle.stop_requested = True
    if handle.process.poll() is None:
        try:
            handle.process.stdin.write('{"action":"stop"}\n')
            handle.process.stdin.flush()
        except (OSError, ValueError):
            pass  # Missing heartbeat independently expires at the worker.
    return poll_capture(handle)
