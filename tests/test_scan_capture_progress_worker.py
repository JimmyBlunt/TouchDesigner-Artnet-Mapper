"""Progress regressions using fake detector, processes and sockets only."""
import json
from pathlib import Path
import queue
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import scan_capture as capture
from pixelblaze_mapper import scan_capture_worker as worker

try:
    from tests.test_scan_capture import Harness, snapshot
except ModuleNotFoundError:
    from test_scan_capture import Harness, snapshot


def observation(index):
    return SimpleNamespace(led_id=index, point=SimpleNamespace(u=lambda: .2, v=lambda: .3))


class CameraProgressTests(unittest.TestCase):
    def run_child(self, answers):
        results = queue.Queue()
        calls = []
        camera = Mock()
        backend = Mock()
        detector = ModuleType('marimapper.detector')
        detector.Camera = lambda device: camera
        detector.set_cam_dark = lambda cam, exposure: True
        detector.find_led = lambda *args: None
        detector.TimeoutController = lambda: None

        def detect(cam, output, index, *args):
            # Record the queue at detector entry: position must already be visible.
            calls.append((index, [dict(item) for item in results.queue]))
            answer = answers[len(calls) - 1]
            if isinstance(answer, BaseException):
                raise answer
            return answer

        led = ModuleType('marimapper.led')
        led.get_distance = lambda *args: 0
        cv2 = ModuleType('cv2')
        cv2.destroyAllWindows = Mock()
        with patch.dict('sys.modules', {'marimapper': ModuleType('marimapper'),
                        'marimapper.detector': detector, 'marimapper.led': led, 'cv2': cv2}), \
             patch('pixelblaze_mapper.camera_probe_worker._native_api'), \
             patch('pixelblaze_mapper.scan_detector.enable_and_find_led', side_effect=detect), \
             patch('pixelblaze_mapper.marimapper_router_backend.pipe_backend', return_value=backend):
            worker._camera_view(None, results, threading.Event(), 2,
                                {'device': 0, 'exposure': -10, 'threshold': 160})
        camera.reset.assert_called_once()
        camera.device.release.assert_called_once()
        return list(results.queue), calls

    def test_position_precedes_detection_and_misses_advance_processed(self):
        items, calls = self.run_child([observation(0), None, observation(0)])
        first, second = calls[0][1][-1], calls[1][1][-1]
        self.assertEqual((first['current_index'], first['processed'], first['detected']), (0, 0, 0))
        self.assertEqual((second['current_index'], second['processed'], second['detected']), (1, 1, 1))
        completed = [item for item in items if 'processed' in item and 'current_index' not in item]
        self.assertEqual([(item['processed'], item['detected'], item['total']) for item in completed],
                         [(1, 1, 2), (2, 1, 2)])

    def test_movement_recheck_does_not_count_as_another_led(self):
        items, calls = self.run_child([observation(0), None, observation(0)])
        self.assertEqual([index for index, _ in calls], [0, 1, 0])
        self.assertEqual(calls[-1][1][-1], {'state': 'movement_check', 'current_index': None})
        progress = [item for item in items if 'processed' in item]
        self.assertEqual((progress[-1]['processed'], progress[-1]['detected']), (2, 1))
        ready = next(item for item in items if item['state'] == 'view_ready')
        self.assertEqual(ready['observations'], [[0, .2, .3]])

    def test_exception_or_cancel_mid_led_does_not_mark_it_processed(self):
        for error in (RuntimeError('detector failed'), InterruptedError('Capture cancelled')):
            with self.subTest(error=type(error).__name__):
                items, calls = self.run_child([observation(0), error])
                self.assertEqual(calls[-1][1][-1]['current_index'], 1)
                progress = [item for item in items if 'processed' in item]
                self.assertEqual((progress[-1]['processed'], progress[-1]['detected']), (1, 1))
                self.assertFalse(any(item['state'] in ('movement_check', 'view_ready') for item in items))
                self.assertIn(str(error), next(item['error'] for item in items if item['state'] == 'camera_failed'))

    def test_all_missed_is_fully_checked_but_rejected(self):
        items, calls = self.run_child([None, None])
        self.assertEqual(len(calls), 2)
        progress = [item for item in items if 'processed' in item]
        self.assertEqual((progress[-1]['processed'], progress[-1]['detected']), (2, 0))
        self.assertFalse(any(item['state'] == 'view_ready' for item in items))


class ProgressHarness(Harness):
    def __init__(self, *, cancelled=False, failed=False):
        super().__init__('progress', hung=cancelled or failed)
        self.cancelled, self.failed = cancelled, failed

    def poll(self, timeout):
        self.polls += 1
        self.now += .5
        if self.polls == 1:
            for item in (
                {'state': 'capturing', 'current_index': 0, 'processed': 0, 'detected': 0, 'total': 2},
                {'state': 'capturing', 'processed': 1, 'detected': 1, 'total': 2},
                {'state': 'capturing', 'current_index': 1, 'processed': 1, 'detected': 1, 'total': 2},
            ):
                self.results.put(item)
            if self.failed:
                self.results.put({'state': 'camera_failed', 'error': 'mid LED failure'})
            elif not self.cancelled:
                for item in (
                    {'state': 'capturing', 'processed': 2, 'detected': 1, 'total': 2},
                    {'state': 'movement_check', 'current_index': None},
                    {'state': 'view_ready', 'observations': [[0, .2, .3]]},
                    {'state': 'camera_closed', 'camera_cleanup_attempted': True, 'camera_cleanup_errors': []},
                ):
                    self.results.put(item)
                self.exitcode = 0
        elif self.cancelled:
            self.messages.put({'action': 'stop'})
        return False


class SupervisorProgressTests(unittest.TestCase):
    def test_sparse_original_ids_and_final_completed_counters(self):
        harness = ProgressHarness()
        outcome, rows = harness.run()
        current = [item for item in harness.statuses if item.get('current_index') is not None]
        self.assertEqual([(item['current_index'], item['current_source_index']) for item in current],
                         [(0, 503), (1, 500)])
        movement = next(item for item in harness.statuses if item['state'] == 'movement_check')
        self.assertIsNone(movement['current_source_index'])
        self.assertEqual((outcome['state'], outcome['processed'], outcome['detected'], outcome['total']),
                         ('complete', 2, 1, 2))
        self.assertIsNone(outcome['current_source_index'])
        self.assertEqual(rows, [[0, .2, .3]])

    def test_cancel_and_failure_preserve_completed_counts_and_last_attempted_id(self):
        for arguments, state in (({'cancelled': True}, 'cancelled'), ({'failed': True}, 'failed')):
            with self.subTest(state=state):
                harness = ProgressHarness(**arguments)
                outcome, rows = harness.run()
                self.assertEqual((outcome['state'], outcome['processed'], outcome['detected'], outcome['total']),
                                 (state, 1, 1, 2))
                self.assertEqual(outcome['last_source_index'], 500)
                self.assertIsNone(outcome['current_source_index'])
                self.assertIsNone(outcome['current_index'])
                self.assertIsNone(rows)
                self.assertTrue(outcome['blackout_sent'])
                self.assertTrue(all(not any(packet[18:]) for packet, _ in harness.socket.packets[-6:]))

    def test_cancelled_result_file_retains_counters_without_view(self):
        outcome, rows = ProgressHarness(cancelled=True).run()
        with tempfile.TemporaryDirectory() as folder:
            plan = capture.prepare_capture(snapshot(), {'device': 0, 'exposure': -10, 'threshold': 160}, folder)
            directory = Path(folder) / plan['directory_name']
            directory.mkdir()
            manifest = directory / 'capture.json'
            manifest.write_text(json.dumps(plan), encoding='utf-8')
            with patch.object(worker, 'run_capture', return_value=(outcome, rows)), patch.object(worker, '_emit'):
                self.assertEqual(worker.main([str(manifest), '--confirm-capture']), 1)
            stored = json.loads((directory / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual((stored['processed'], stored['detected'], stored['total'], stored['last_source_index']),
                             (1, 1, 2, 500))
            self.assertFalse((directory / 'view.csv').exists())


if __name__ == '__main__':
    unittest.main()
