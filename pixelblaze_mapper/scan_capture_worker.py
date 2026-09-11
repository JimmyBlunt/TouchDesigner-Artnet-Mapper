"""Opt-in MariMapper one-view supervisor. Only supervisor owns Art-Net sockets.

Native detector functions run in a disposable camera child; hangs cannot prevent
the supervisor from sending black. UDP send completion is NOT optical proof.
"""
import argparse
import csv
import json
import multiprocessing as mp
from math import isfinite
from pathlib import Path
import queue
import socket
import sys
import threading
import time


def artdmx_packet(universe, payload):
    if type(universe) is not int or not 0 <= universe <= 32767:
        raise ValueError('Invalid Art-Net wire universe')
    payload = bytes(payload)
    if len(payload) != 510:
        raise ValueError('Scan requires exactly 510 channels per universe')
    return (b'Art-Net\x00\x00\x50\x00\x0e\x00\x00' +
            universe.to_bytes(2, 'little') + b'\x01\xfe' + payload)


class CaptureWatchdog:
    def __init__(self, clock=time.monotonic, heartbeat_seconds=5.0):
        self.clock = clock
        self.deadline = clock() + heartbeat_seconds
        self.interval = heartbeat_seconds
        self.stopped = False

    def command(self, message):
        if message == {'action': 'heartbeat'} and not self.stopped:
            self.deadline = self.clock() + self.interval
        elif message == {'action': 'stop'}:
            self.stopped = True
        else:
            self.stopped = True

    def check(self):
        if self.stopped:
            raise InterruptedError('Scan stopped')
        if self.clock() >= self.deadline:
            raise InterruptedError('TouchDesigner heartbeat expired')


def _camera_view(connection, result_queue, cancel, count, settings):
    """Reuse native images, exposure and adaptive timing with checked transitions.

Our adapter starts search after send ACK and requires darkness after every LED.
Dense worker IDs are translated to original source IDs by the supervisor.
"""
    camera = None
    cleanup = []
    metrics = None
    try:
        from .camera_probe_worker import _native_api
        _native_api()  # Verify exact installed revision in child too; opens no camera.
        from marimapper.detector import Camera, set_cam_dark, find_led, TimeoutController
        from .scan_detector import enable_and_find_led, search_timeout
        from marimapper.led import get_distance
        from .marimapper_router_backend import pipe_backend
        from .scan_capture_timing import CaptureTimings, TimedBackend
        metrics = CaptureTimings()
        backend = TimedBackend(pipe_backend(connection, count, timeout=2.0), metrics)
        camera = Camera(settings['device'])

        class CancellableCamera:
            def __init__(self, source):
                self.source = source
                self.deadline = time.monotonic() + 30.0

            def __getattr__(self, name):
                return getattr(self.source, name)

            def read(self):
                if cancel.is_set():
                    raise InterruptedError('Capture cancelled')
                if time.monotonic() > self.deadline:
                    raise TimeoutError('Native detector exceeded per-LED deadline')
                return metrics.read(self.source.read)

            def eat(self, count=30):
                # Delegating source.eat would bypass our cancellable read.
                for _ in range(count):
                    self.read()

        wrapped = CancellableCamera(camera)
        backend.set_leds([[0, 0, 0] for _ in range(count)])
        exposure_applied = set_cam_dark(wrapped, settings['exposure'])
        if find_led(wrapped, settings['threshold'], True) is not None:
            raise RuntimeError('Light detected during initial blackout; adjust exposure/threshold')
        result_queue.put({'state': 'capturing', 'exposure_applied': bool(exposure_applied)})
        timing = TimeoutController()
        detections = []
        for index in range(count):
            wrapped.deadline = time.monotonic() + 30.0
            result_queue.put({'state': 'capturing', 'current_index': index,
                              'processed': index, 'detected': len(detections), 'total': count})
            timeout_used = search_timeout(timing) if getattr(timing, 'timeout', None) is not None else None
            metrics.begin()
            led = enable_and_find_led(wrapped, backend, index, 0, timing,
                                      settings['threshold'], True)
            measured = metrics.finish(timeout_seconds=getattr(timing, 'timeout', None))
            measured['search_timeout_used_ms'] = round(timeout_used * 1000, 3) if timeout_used is not None else None
            if led is not None:
                detections.append(led)
            result_queue.put({'state': 'capturing', 'processed': index + 1,
                              'detected': len(detections), 'total': count, 'timing': measured})
        if not detections:
            raise RuntimeError('No LEDs detected; no view accepted')
        result_queue.put({'state': 'movement_check', 'current_index': None})
        wrapped.deadline = time.monotonic() + 30.0
        again = enable_and_find_led(wrapped, backend, detections[0].led_id, 0,
                                   timing, settings['threshold'], True)
        if again is None or get_distance(again, detections[0]) > 0.01:
            raise RuntimeError('Movement check failed or unverified; view rejected')
        result_queue.put({'state': 'view_ready', 'observations': [
            [led.led_id, float(led.point.u()), float(led.point.v())] for led in detections]})
    except BaseException as error:
        failure = {'state': 'camera_failed', 'error': str(error) or type(error).__name__}
        if metrics is not None and metrics.active:
            failure['timing'] = metrics.finish(completed=False)
        result_queue.put(failure)
    finally:
        if camera is not None:
            for name, action in (('reset', camera.reset), ('release', camera.device.release)):
                try:
                    action()
                except BaseException as error:
                    cleanup.append(name + ': ' + str(error))
        try:
            import cv2
            cv2.destroyAllWindows()
        except BaseException as error:
            cleanup.append('windows: ' + str(error))
        result_queue.put({'state': 'camera_closed', 'camera_cleanup_attempted': True,
                          'camera_cleanup_errors': cleanup})


def _stdin_reader(messages):
    try:
        while True:
            line = sys.stdin.readline(4097)
            if not line or len(line) > 4096:
                break
            try:
                messages.put(json.loads(line))
            except ValueError:
                messages.put({'action': 'stop'})
    finally:
        messages.put({'action': 'stop'})


def _emit(status):
    print(json.dumps(status, allow_nan=False), flush=True)


def _validated_observations(rows, count):
    if type(rows) is not list or not rows or len(rows) > count:
        raise ValueError('Invalid/empty observations')
    seen = set()
    output = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ValueError('Invalid observation row')
        index, u, v = row
        if type(index) is not int or not 0 <= index < count or index in seen:
            raise ValueError('Invalid/duplicate worker observation ID')
        if any(type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1 for value in (u, v)):
            raise ValueError('Observations must be finite normalized UV')
        seen.add(index)
        output.append([index, float(u), float(v)])
    return output


def run_capture(manifest):
    from .scan_capture import validate_capture_manifest
    manifest = validate_capture_manifest(manifest)
    from .scan_routing import ScanRoutingSnapshot
    snapshot = ScanRoutingSnapshot.from_dict(manifest['routing'])
    frames = snapshot.packet_descriptors()
    if any(frame.art_sync for frame in frames):
        raise ValueError('ArtSync controllers are not yet supported by scan capture')
    interval = 1.0 / min(20, *(frame.rate for frame in frames))
    from .camera_probe_worker import _native_api
    _native_api()  # Exact version/commit check BEFORE any socket or camera creation.
    messages = queue.Queue()
    threading.Thread(target=_stdin_reader, args=(messages,), daemon=True).start()
    watchdog = CaptureWatchdog()
    sockets = {}
    child = None
    child_started = False
    cancellation = mp.Event()
    parent, remote = mp.Pipe()
    results = mp.Queue()
    outcome = {'state': 'failed', 'processed': 0, 'detected': 0,
               'total': len(snapshot.source_indices), 'current_index': None,
               'current_source_index': None, 'blackout_sent': False,
               'blackout_confirmed': False, 'optical_blackout_confirmed': False}
    observations = None
    finished = False
    last_request_id = 0
    last_transmit = None

    def send(frame_map, *, emergency=False):
        nonlocal last_transmit
        if not emergency and last_transmit is not None:
            delay = interval - (time.monotonic() - last_transmit)
            if delay > 0:
                time.sleep(delay)
        if any(any(frame.payload) for frame in frame_map):
            while True:
                try:
                    watchdog.command(messages.get_nowait())
                except queue.Empty:
                    break
            watchdog.check()  # No new light after stop/expiry during rate wait.
        errors = []
        for frame in frame_map:
            try:
                sock = sockets[frame.local_interface]
                sock.sendto(artdmx_packet(frame.wire_universe, frame.payload),
                            (frame.target_address, frame.port))
            except Exception as error:
                errors.append(str(error))
        last_transmit = time.monotonic()
        if errors:
            raise OSError('; '.join(errors))

    try:
        for controller in snapshot.packet_descriptors():
            if controller.local_interface not in sockets:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sockets[controller.local_interface] = sock
                if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                sock.settimeout(0.2)
                sock.bind((controller.local_interface, 6454))
        # Hold black before camera detection, including unused port reservations.
        send(frames)
        child = mp.Process(target=_camera_view, args=(remote, results, cancellation,
                           len(snapshot.source_indices), manifest['camera']), daemon=True)
        child.start()
        child_started = True
        remote.close()
        _emit(dict(outcome, state='camera_starting'))
        last_progress = time.monotonic()
        while not finished:
            while not messages.empty():
                watchdog.command(messages.get_nowait())
            watchdog.check()
            now = time.monotonic()
            if now - last_progress > 40:
                raise TimeoutError('Camera/detector stopped progressing')
            if parent.poll(0.01):
                request = parent.recv()
                if type(request) is not dict:
                    raise ValueError('Invalid native backend request')
                req_id = request.get('request_id')
                try:
                    if type(req_id) is not int or req_id <= last_request_id:
                        raise ValueError('Invalid/replayed native backend request ID')
                    last_request_id = req_id
                    if request.get('action') == 'blackout':
                        frames = snapshot.packet_descriptors()
                    elif request.get('action') == 'set_led' and type(request.get('on')) is bool:
                        frames = snapshot.packet_descriptors(request['index'], on=request['on'])
                    else:
                        raise ValueError('Unsupported native backend request')
                    send(frames)
                    parent.send({'ok': True, 'request_id': req_id})
                except Exception as error:
                    parent.send({'ok': False, 'request_id': req_id, 'error': str(error)})
                    raise
            # Polling and command sends can block. Schedule repeats from actual
            # transmission completion, never the stale loop-entry timestamp:
            # an early repeat would wait here and delay the next LED command.
            now = time.monotonic()
            if now - last_transmit >= interval:
                send(frames)
            now = time.monotonic()
            while True:
                try:
                    result = results.get_nowait()
                except queue.Empty:
                    break
                last_progress = now
                state = result.get('state')
                # Dense worker positions are not necessarily original LED IDs.
                if 'current_index' in result:
                    index = result['current_index']
                    result['current_source_index'] = None if index is None else snapshot.source_index(index)
                for key in ('processed', 'detected', 'total', 'current_index', 'current_source_index', 'timing'):
                    if key in result:
                        outcome[key] = result[key]
                if state == 'camera_failed':
                    raise RuntimeError(result.get('error', 'Native camera failed'))
                if state == 'view_ready':
                    observations = _validated_observations(result.pop('observations'), snapshot.get_led_count())
                if state == 'camera_closed':
                    outcome.update(result)
                    if observations is None:
                        raise RuntimeError('Camera closed without accepted view')
                    if result.get('camera_cleanup_attempted') is not True or result.get('camera_cleanup_errors') != []:
                        raise RuntimeError('Camera cleanup incomplete or failed')
                    outcome['camera_cleanup_confirmed'] = True
                    outcome['state'] = 'complete'
                    finished = True
                    break
                _emit(result)
            if not finished and child.exitcode is not None:
                # Queue feeder can lag the process briefly; never accept a view
                # without its explicit completion and cleanup messages.
                if now - last_progress > 1:
                    raise RuntimeError('Camera child exited without completed view')
    except InterruptedError as error:
        outcome.update(state='cancelled', error=str(error))
    except Exception as error:
        outcome.update(state='failed', error=str(error))
    finally:
        cancellation.set()
        errors = []
        for attempt in range(3):
            try:
                send(snapshot.packet_descriptors(), emergency=attempt == 0)
            except Exception as error:
                errors.append(str(error))
        outcome['blackout_sent'] = not errors
        outcome['blackout_errors'] = errors
        # No optical observation after teardown: do not claim physical black.
        cleanup_errors = []
        if child is not None and child_started:
            try:
                child.join(1.0)
                if child.is_alive():
                    outcome['camera_forced_stop'] = True
                    outcome['camera_cleanup_confirmed'] = False
                    child.terminate()
                    child.join(1.0)
                if outcome['state'] == 'complete' and child.exitcode != 0:
                    outcome.update(state='failed', error='Camera child did not exit cleanly')
            except Exception as error:
                cleanup_errors.append('child: ' + str(error))
        if errors and outcome['state'] == 'complete':
            outcome.update(state='failed', error='Final blackout transmission failed')
        for sock in sockets.values():
            try:
                sock.close()
            except Exception as error:
                cleanup_errors.append('socket: ' + str(error))
        for connection in (parent, remote):
            try:
                connection.close()
            except Exception as error:
                cleanup_errors.append('pipe: ' + str(error))
        outcome['supervisor_cleanup_errors'] = cleanup_errors
        if cleanup_errors and outcome['state'] == 'complete':
            outcome.update(state='failed', error='Supervisor cleanup incomplete')
    outcome['last_source_index'] = outcome['current_source_index']
    outcome['current_index'] = outcome['current_source_index'] = None
    return outcome, observations if outcome['state'] == 'complete' else None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('--confirm-capture', action='store_true')
    args = parser.parse_args(argv)
    if not args.confirm_capture:
        parser.error('Explicit --confirm-capture required; no hardware started')
    path = Path(args.manifest).resolve(strict=True)
    manifest = json.loads(path.read_text(encoding='utf-8'))
    from .scan_capture import validate_capture_manifest
    manifest = validate_capture_manifest(manifest)
    workspace = Path(manifest['workspace']).resolve(strict=True)
    directory = (workspace / manifest['directory_name']).resolve(strict=True)
    if directory != path.parent or directory.parent != workspace or path.name != 'capture.json':
        raise ValueError('Capture directory does not match manifest')
    if (directory / 'view.csv').exists() or (directory / 'result.json').exists():
        raise ValueError('Capture directory already contains results')
    outcome, observations = run_capture(manifest)
    if observations is not None and outcome['state'] == 'complete':
        from .scan_routing import ScanRoutingSnapshot
        snapshot = ScanRoutingSnapshot.from_dict(manifest['routing'])
        observations = _validated_observations(observations, snapshot.get_led_count())
        with (directory / 'view.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['index', 'u', 'v'])
            writer.writerows((snapshot.source_index(index), u, v) for index, u, v in observations)
        outcome['view_csv'] = str(directory / 'view.csv')
    with (directory / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(outcome, stream, indent=2)
    _emit(outcome)
    return 0 if outcome['state'] == 'complete' else 1


if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
