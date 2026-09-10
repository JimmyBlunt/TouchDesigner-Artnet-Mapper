import unittest
from types import SimpleNamespace
from pixelblaze_mapper.scan_capture_timing import CaptureTimings, TimedBackend, PHASES


class CaptureTimingTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.metrics = CaptureTimings(clock=lambda: self.now)

    def advance(self, seconds, value=None):
        self.now += seconds
        return value

    def test_phases_preserve_result_and_partition_cycle(self):
        calls = []
        def send(index, on):
            calls.append((index, on))
            return self.advance(.05, 'ack')
        backend = TimedBackend(SimpleNamespace(set_led=send), self.metrics)
        self.metrics.begin()
        image = object()
        self.assertIs(self.metrics.read(lambda: self.advance(.03, image)), image)
        self.assertEqual(backend.set_led(5, True), 'ack')
        self.metrics.read(lambda: self.advance(.1, image))
        self.advance(.02)
        backend.set_led(5, False)
        self.metrics.read(lambda: self.advance(.04, image))
        self.advance(.01)
        result = self.metrics.finish(timeout_seconds=1)
        last = result['last']
        self.assertEqual(calls, [(5, True), (5, False)])
        self.assertEqual([last[key] for key in PHASES], [30, 50, 120, 50, 50])
        self.assertEqual(last['cycle_ms'], 300)
        self.assertEqual(last['camera_read_ms'], 170)
        self.assertEqual(last['camera_frames'], 3)
        self.assertEqual(sum(last[key] for key in PHASES), last['cycle_ms'])

    def test_partial_failure_is_excluded_from_completed_average(self):
        self.metrics.begin()
        self.advance(.3)
        self.metrics.finish()
        self.metrics.begin()
        self.advance(.9)
        result = self.metrics.finish(completed=False)
        self.assertFalse(result['last_completed'])
        self.assertEqual(result['last']['cycle_ms'], 900)
        self.assertEqual(result['mean']['cycle_ms'], 300)
        self.assertEqual(result['completed_samples'], 1)

    def test_warmup_and_movement_reads_do_not_add_samples(self):
        self.metrics.read(lambda: self.advance(2))
        self.assertEqual(self.metrics.samples, 0)
        self.metrics.begin()
        self.advance(.2)
        self.metrics.finish()
        self.metrics.read(lambda: self.advance(2))
        self.assertEqual(self.metrics.samples, 1)

    def test_backend_and_camera_exceptions_are_unchanged(self):
        error = RuntimeError('device error')
        def fail(*args):
            self.advance(.02)
            raise error
        backend = TimedBackend(SimpleNamespace(set_led=fail), self.metrics)
        self.metrics.begin()
        with self.assertRaises(RuntimeError) as caught:
            backend.set_led(2, True)
        self.assertIs(caught.exception, error)
        with self.assertRaises(RuntimeError):
            self.metrics.read(fail)
        last = self.metrics.finish(completed=False)['last']
        self.assertEqual(last['send_on_ms'], 20)
        self.assertEqual(last['camera_read_ms'], 20)

    def test_recent_window_is_bounded_and_whole_view_mean_retained(self):
        for index in range(25):
            self.metrics.begin()
            self.advance(.1 if index < 5 else .2)
            result = self.metrics.finish()
        self.assertEqual(len(self.metrics.recent), 20)
        self.assertEqual(result['completed_samples'], 25)
        self.assertEqual(result['mean']['cycle_ms'], 180)
        self.assertEqual(result['recent_mean']['cycle_ms'], 200)


class TimingPipelineTests(unittest.TestCase):
    def test_camera_events_include_complete_and_partial_measurements(self):
        from tests.test_scan_capture_progress_worker import CameraProgressTests, observation
        helper = CameraProgressTests()
        rows, _ = helper.run_child([observation(0), None, observation(0)])
        measured = [row['timing'] for row in rows if 'timing' in row]
        self.assertEqual([row['completed_samples'] for row in measured], [1, 2])
        self.assertTrue(all(row['last_completed'] for row in measured))
        rows, _ = helper.run_child([observation(0), RuntimeError('partial LED')])
        failed = next(row for row in rows if row['state'] == 'camera_failed')
        self.assertFalse(failed['timing']['last_completed'])
        self.assertEqual(failed['timing']['completed_samples'], 1)

    def test_supervisor_retains_timing_in_final_outcome(self):
        from tests.test_scan_capture_progress_worker import ProgressHarness
        class MeasuredHarness(ProgressHarness):
            def poll(self, timeout):
                result = super().poll(timeout)
                for row in self.results.queue:
                    if row.get('processed') == 2:
                        row['timing'] = {'completed_samples': 2, 'mean': {'cycle_ms': 300}}
                return result
        outcome, _ = MeasuredHarness().run()
        self.assertEqual(outcome['timing'], {'completed_samples': 2, 'mean': {'cycle_ms': 300}})


if __name__ == '__main__':
    unittest.main()
