"""Offline capture supervisor tests. All sockets/processes/cameras are fakes."""
from contextlib import ExitStack
from dataclasses import replace
import csv
import io
import json
from pathlib import Path
import queue
import tempfile
import threading
from types import ModuleType
import unittest
from unittest.mock import patch

from pixelblaze_mapper import scan_capture as capture
from pixelblaze_mapper import scan_capture_worker as worker
from pixelblaze_mapper import scan_output_guard as guard
from pixelblaze_mapper.multi_controller import ControllerConfig, RouterConfig, SegmentConfig
from pixelblaze_mapper.scan_routing import create_snapshot


def snapshot():
    return create_snapshot(RouterConfig((ControllerConfig('test', '192.0.2.10', '192.0.2.1',
        enabled=True, start_universe=300, brightness=.02, reserved_universes=2),),
        (SegmentConfig('selected', 500, 4, 'test', 168),), source_pixel_count=800), [503, 500])


class FakeSocket:
    def __init__(self, fail_after=None):
        self.packets = []
        self.fail_after = fail_after
        self.closed = False
        self.times = []
        self.clock = lambda: 0

    def setsockopt(self, *args): pass
    def settimeout(self, *args): pass
    def bind(self, address): self.bound = address
    def close(self): self.closed = True

    def sendto(self, packet, address):
        if self.fail_after is not None and len(self.packets) >= self.fail_after:
            raise OSError('simulated sender failure')
        self.packets.append((packet, address))
        self.times.append(self.clock())
        return len(packet)


class Harness:
    """Deterministic event loop; never executes a native child target."""
    def __init__(self, mode='complete', *, request=None, fail_after=None, hung=False):
        self.mode, self.request, self.hung = mode, request, hung
        self.now = 0.0
        self.polls = 0
        self.socket = FakeSocket(fail_after)
        self.socket.clock = self.clock
        self.results = queue.Queue()
        self.messages = None
        self.acks = []
        self.statuses = []
        self.terminated = False
        self.closed = False
        self.exitcode = 1 if mode == 'abnormal' else None
        self.starts = 0
        self.event = threading.Event()
        self.manifest = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, Path.cwd())

    def clock(self): return self.now
    def sleep(self, seconds): self.now += seconds
    def thread(self, target, args, **kwargs):
        self.messages = args[0]
        return self
    def start(self):
        self.starts += 1
        if self.mode == 'start_failed' and self.starts == 2:
            raise OSError('child could not start')
    def join(self, *args): pass
    def is_alive(self): return self.hung or self.exitcode is None
    def terminate(self): self.terminated = True; self.hung = False; self.exitcode = -1
    def close(self): self.closed = True
    def send(self, value): self.acks.append(value)
    def recv(self): return self.request

    def poll(self, timeout):
        self.polls += 1
        self.now += .5
        if self.mode == 'progress_timeout':
            self.messages.put({'action': 'heartbeat'})
        if self.polls == 1:
            if self.mode == 'cancel': self.messages.put({'action': 'stop'})
            if self.mode == 'camera_failed':
                self.results.put({'state': 'camera_failed', 'error': 'simulated camera exception'})
            if self.mode in ('complete', 'cleanup_failed'):
                self.results.put({'state': 'view_ready', 'observations': [[0, .1, .2], [1, .3, .4]]})
                self.results.put({'state': 'camera_closed', 'camera_cleanup_attempted': True,
                                  'camera_cleanup_errors': ['release failed'] if self.mode == 'cleanup_failed' else []})
                if not self.hung: self.exitcode = 0
        return self.polls == 1 and self.request is not None

    def run(self):
        real_watchdog = worker.CaptureWatchdog
        with ExitStack() as stack:
            stack.enter_context(patch('pixelblaze_mapper.camera_probe_worker._native_api'))
            for target, replacement in (
                ('threading.Thread', self.thread), ('socket.socket', lambda *a: self.socket),
                ('mp.Event', lambda: self.event), ('mp.Pipe', lambda: (self, self)),
                ('mp.Queue', lambda: self.results), ('mp.Process', lambda **kw: self),
                ('time.monotonic', self.clock), ('time.sleep', self.sleep),
                ('CaptureWatchdog', lambda: real_watchdog(clock=self.clock)), ('_emit', self.statuses.append)):
                stack.enter_context(patch('pixelblaze_mapper.scan_capture_worker.' + target, replacement))
            return worker.run_capture(self.manifest)


class SupervisorTests(unittest.TestCase):
    def test_child_start_failure_still_blacks_and_closes_socket(self):
        h = Harness('start_failed')
        outcome, rows = h.run()
        self.assertEqual(outcome['state'], 'failed')
        self.assertIn('could not start', outcome['error'])
        self.assertIsNone(rows)
        self.assert_final_black(h)

    def test_controller_rate_caps_periodic_and_command_sends(self):
        h = Harness('progress_timeout')
        source = snapshot()
        config = replace(source.config, controllers=(replace(source.config.controllers[0], rate=1),))
        h.manifest['routing'] = create_snapshot(config, source.source_indices).to_dict()
        h.run()
        # Two universes per batch; final emergency black may bypass cap, all
        # earlier complete batches must obey the configured one-frame/s cap.
        batches = h.socket.times[::2][:-3]
        self.assertGreater(len(batches), 2)
        self.assertTrue(all(b-a >= 1.0 for a, b in zip(batches, batches[1:])))

    def test_preflight_revision_failure_precedes_socket_creation(self):
        plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, Path.cwd())
        with patch('pixelblaze_mapper.camera_probe_worker._native_api', side_effect=RuntimeError('wrong commit')), \
             patch.object(worker.socket, 'socket') as socket_factory:
            with self.assertRaisesRegex(RuntimeError, 'commit'):
                worker.run_capture(plan)
            socket_factory.assert_not_called()

    def test_unsupported_artsync_rejected_before_socket_or_native(self):
        source = snapshot()
        config = replace(source.config, controllers=(replace(source.config.controllers[0], art_sync=True),))
        plan = capture.prepare_capture(create_snapshot(config, source.source_indices),
                                       {'device': 0, 'exposure': -10, 'threshold': 160}, Path.cwd())
        with patch('pixelblaze_mapper.camera_probe_worker._native_api') as native, \
             patch.object(worker.socket, 'socket') as socket_factory:
            with self.assertRaisesRegex(ValueError, 'ArtSync'):
                worker.run_capture(plan)
            socket_factory.assert_not_called()
            native.assert_not_called()

    def test_full_manifest_camera_validation_before_socket(self):
        plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, Path.cwd())
        bad = [dict(plan, version=True), dict(plan, directory_name='../outside'),
               dict(plan, max_led_seconds=300), dict(plan, camera=dict(plan['camera'], threshold=255)),
               dict(plan, camera=dict(plan['camera'], extra='not allowed'))]
        with patch.object(worker.socket, 'socket') as socket_factory:
            for manifest in bad:
                with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                    worker.run_capture(manifest)
            socket_factory.assert_not_called()

    def test_observation_validation_rejects_nonfinite_duplicate_or_unselected_ids(self):
        for rows in ([], [[2, .1, .2]], [[True, .1, .2]], [[0, float('nan'), .2]],
                     [[0, 1.1, .2]], [[0, .1, .2], [0, .3, .4]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                worker._validated_observations(rows, 2)

    def test_artdmx_exact_header_and_payload_validation(self):
        packet = worker.artdmx_packet(300, bytes(510))
        self.assertEqual(packet[:14], b'Art-Net\x00\x00\x50\x00\x0e\x00\x00')
        self.assertEqual(packet[14:18], b'\x2c\x01\x01\xfe')
        self.assertEqual(len(packet), 528)
        for universe, payload in ((True, bytes(510)), (-1, bytes(510)), (32768, bytes(510)), (0, bytes(512))):
            with self.assertRaises(ValueError): worker.artdmx_packet(universe, payload)

    def assert_final_black(self, harness):
        self.assertGreaterEqual(len(harness.socket.packets), 6)
        self.assertTrue(all(not any(packet[18:]) for packet, _ in harness.socket.packets[-6:]))
        self.assertEqual({int.from_bytes(packet[14:16], 'little') for packet, _ in harness.socket.packets[-6:]}, {300, 301})
        self.assertTrue(harness.socket.closed)
        self.assertTrue(harness.event.is_set())

    def test_single_dense_index_uses_frozen_original_destination(self):
        h = Harness(request={'action': 'set_led', 'index': 0, 'on': True, 'request_id': 7})
        outcome, observations = h.run()
        self.assertEqual(outcome['state'], 'complete')
        self.assertTrue(outcome['blackout_sent'])
        self.assertFalse(outcome['optical_blackout_confirmed'])
        self.assertEqual(observations[0][0], 0)
        self.assertEqual(h.acks, [{'ok': True, 'request_id': 7}])
        lit = [(packet, address) for packet, address in h.socket.packets if any(packet[18:])]
        self.assertEqual(len(lit), 1)
        packet, address = lit[0]
        self.assertEqual(address, ('192.0.2.10', 6454))
        self.assertEqual(int.from_bytes(packet[14:16], 'little'), 301)
        # Original source503 maps destination171: slot1 in second universe.
        self.assertEqual(packet[18:21], bytes(3))
        self.assertEqual(packet[21:24], bytes([5] * 3))
        self.assertEqual(sum(v != 0 for v in packet[18:]), 3)
        self.assert_final_black(h)

    def test_cancel_blacks_every_reserved_universe_and_stops_hung_child(self):
        h = Harness('cancel', request={'action': 'set_led', 'index': 0, 'on': True, 'request_id': 1}, hung=True)
        outcome, observations = h.run()
        self.assertEqual(outcome['state'], 'cancelled')
        self.assertIsNone(observations)
        self.assertTrue(h.terminated)
        self.assertFalse(outcome['camera_cleanup_confirmed'])
        self.assert_final_black(h)

    def test_heartbeat_expiry_blacks_and_cancels(self):
        h = Harness('heartbeat_expired', hung=True)
        outcome, _ = h.run()
        self.assertEqual(outcome['state'], 'cancelled')
        self.assertIn('heartbeat', outcome['error'])
        self.assert_final_black(h)

    def test_detector_timeout_despite_heartbeats_blacks(self):
        h = Harness('progress_timeout', hung=True)
        outcome, _ = h.run()
        self.assertEqual(outcome['state'], 'failed')
        self.assertIn('progress', outcome['error'])
        self.assert_final_black(h)

    def test_abnormal_child_exit_is_not_accepted(self):
        h = Harness('abnormal')
        outcome, observations = h.run()
        self.assertEqual(outcome['state'], 'failed')
        self.assertIsNone(observations)
        self.assert_final_black(h)

    def test_camera_exception_blacks(self):
        h = Harness('camera_failed')
        outcome, observations = h.run()
        self.assertEqual(outcome['state'], 'failed')
        self.assertIn('camera exception', outcome['error'])
        self.assertIsNone(observations)
        self.assert_final_black(h)

    def test_invalid_selection_rejected_with_negative_ack_and_black(self):
        h = Harness(request={'action': 'set_led', 'index': 503, 'on': True, 'request_id': 1})
        outcome, observations = h.run()
        self.assertEqual(outcome['state'], 'failed')
        self.assertFalse(h.acks[0]['ok'])
        self.assertIsNone(observations)
        self.assert_final_black(h)

    def test_blackout_send_failure_cannot_report_complete(self):
        h = Harness(fail_after=2)
        outcome, _ = h.run()
        self.assertFalse(outcome['blackout_sent'])
        self.assertNotEqual(outcome['state'], 'complete')

    def test_forced_child_stop_cannot_report_clean_complete(self):
        h = Harness(hung=True)
        outcome, _ = h.run()
        self.assertTrue(h.terminated)
        self.assertNotEqual(outcome['state'], 'complete')

    def test_camera_cleanup_error_cannot_report_clean_complete(self):
        outcome, _ = Harness('cleanup_failed').run()
        self.assertNotEqual(outcome['state'], 'complete')


class WatchdogTests(unittest.TestCase):
    def test_expiry_stop_and_malformed_commands_fail_closed(self):
        now = [0.0]
        for message in ({'action': 'stop'}, {'action': 'unknown'}, None):
            w = worker.CaptureWatchdog(clock=lambda: now[0])
            w.command(message)
            with self.assertRaises(InterruptedError): w.check()
        w = worker.CaptureWatchdog(clock=lambda: now[0])
        now[0] = 4
        w.command({'action': 'heartbeat'})
        now[0] = 8
        w.check()
        now[0] = 9
        with self.assertRaises(InterruptedError): w.check()


class HandleTests(unittest.TestCase):
    def test_identity_attribution_is_validated_and_preserved_in_started_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            identity = {'503': 'stable-led-a', '500': 'stable-led-b'}
            plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160},
                                           folder, identity=identity, scene_revision='scene-revision-verified')
            identity['503'] = 'caller-mutated'
            process = unittest.mock.Mock()
            with patch.object(capture.subprocess, 'Popen', return_value=process), \
                 patch.object(capture.threading, 'Thread'):
                handle = capture.start_capture(plan, confirmed=True)
            document = json.loads((handle.directory / 'capture.json').read_text())
            self.assertEqual(document['identity'], {'503': 'stable-led-a', '500': 'stable-led-b'})
            self.assertEqual(document['scene_revision'], 'scene-revision-verified')
            self.assertNotEqual(document['directory_name'], plan['directory_name'])
            for invalid in (dict(plan, identity={'503': 'a'}), dict(plan, scene_revision=''),
                            dict(plan, identity={'503': 'same', '500': 'same'})):
                with self.assertRaises(ValueError): capture.validate_capture_manifest(invalid)
            invalid = dict(plan)
            del invalid['scene_revision']
            with self.assertRaises(ValueError): capture.validate_capture_manifest(invalid)

    def test_manifest_cannot_escape_workspace_or_change_timing(self):
        plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, Path.cwd())
        for name in ('..', '../capture-abc', 'C:/other', 'capture-not-a-uuid'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                capture.validate_capture_manifest(dict(plan, directory_name=name))
        with self.assertRaises(ValueError):
            capture.validate_capture_manifest(dict(plan, heartbeat_seconds=True))

    def test_nonzero_process_exit_overrides_queued_complete(self):
        process = unittest.mock.Mock()
        process.poll.return_value = 7
        handle = capture.CaptureHandle(process, Path('unused'))
        handle.messages.put({'state': 'complete', 'blackout_sent': True})
        state = capture.poll_capture(handle)
        self.assertEqual(state['state'], 'failed')
        self.assertEqual(state['exit_code'], 7)

    def test_stop_sends_no_followup_heartbeat(self):
        process = unittest.mock.Mock()
        process.poll.return_value = None
        process.stdin = io.StringIO()
        handle = capture.CaptureHandle(process, Path('unused'))
        capture.stop_capture(handle)
        capture.poll_capture(handle)
        self.assertEqual(process.stdin.getvalue(), '{"action":"stop"}\n')

    def test_prepare_and_unconfirmed_start_do_not_launch(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(capture.subprocess, 'Popen') as launch:
            plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, folder)
            self.assertFalse(list(Path(folder).iterdir()))
            with self.assertRaises(ValueError): capture.start_capture(plan)
            launch.assert_not_called()

    def test_csv_restores_original_source_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, folder)
            directory = Path(folder) / manifest['directory_name']
            directory.mkdir()
            # Use real exclusive file creation and CSV path, but no scan/camera/socket.
            path = directory / 'capture.json'
            with patch.object(Path, 'read_text', return_value=json.dumps(manifest)), \
                 patch.object(Path, 'resolve', autospec=True, side_effect=lambda p, **kw: p.absolute()), \
                 patch.object(worker, 'run_capture', return_value=({'state': 'complete'}, [[0, .1, .2], [1, .3, .4]])), \
                 patch.object(worker, '_emit'):
                self.assertEqual(worker.main([str(path), '--confirm-capture']), 0)
            with (directory / 'view.csv').open(newline='') as stream:
                self.assertEqual([row['index'] for row in csv.DictReader(stream)], ['503', '500'])


class GuardTests(unittest.TestCase):
    def test_ownership_no_steal_wrong_release_or_automatic_resume(self):
        with patch.object(guard, '_token', None):
            token = guard.acquire()
            self.assertTrue(guard.active())
            with self.assertRaises(RuntimeError): guard.acquire()
            with self.assertRaises(RuntimeError): guard.assert_no_scan()
            with self.assertRaises(RuntimeError): guard.release('wrong')
            self.assertTrue(guard.active())
            guard.release(token)
            self.assertFalse(guard.active())
            guard.assert_no_scan()


class CameraChildTests(unittest.TestCase):
    def test_cancellation_reaches_eat_and_independent_cleanup_runs(self):
        event = threading.Event()
        event.set()
        results = queue.Queue()
        camera = unittest.mock.Mock()
        camera.device = unittest.mock.Mock()
        camera.reset.side_effect = RuntimeError('reset rejected')
        detector = ModuleType('marimapper.detector')
        detector.Camera = lambda device: camera
        detector.set_cam_dark = lambda cam, exposure: cam.eat(2)
        detector.find_led = lambda *args: None
        detector.enable_and_find_led = lambda *args: None
        detector.TimeoutController = lambda: None
        led = ModuleType('marimapper.led')
        led.get_distance = lambda *args: 0
        cv2 = ModuleType('cv2')
        cv2.destroyAllWindows = unittest.mock.Mock()
        with patch.dict('sys.modules', {'marimapper': ModuleType('marimapper'),
                        'marimapper.detector': detector, 'marimapper.led': led, 'cv2': cv2}), \
             patch('pixelblaze_mapper.camera_probe_worker._native_api'), \
             patch('pixelblaze_mapper.marimapper_router_backend.pipe_backend', return_value=unittest.mock.Mock()):
            worker._camera_view(None, results, event, 2, {'device': 0, 'exposure': -10, 'threshold': 160})
        items = list(results.queue)
        self.assertEqual(items[0]['state'], 'camera_failed')
        self.assertIn('cancelled', items[0]['error'])
        self.assertEqual(items[-1]['state'], 'camera_closed')
        self.assertTrue(items[-1]['camera_cleanup_errors'])
        camera.read.assert_not_called()
        camera.device.release.assert_called_once()
        cv2.destroyAllWindows.assert_called_once()


if __name__ == '__main__': unittest.main()
