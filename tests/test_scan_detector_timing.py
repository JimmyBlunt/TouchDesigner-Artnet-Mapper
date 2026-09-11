"""Adapter timing and dark-transition tests with a virtual clock only."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.scan_detector import enable_and_find_led


class Clock:
    def __init__(self, tick=0.0):
        self.now, self.tick = 0.0, tick

    def __call__(self):
        value = self.now
        self.now += self.tick
        return value


class Trial:
    def __init__(self, readings, *, timeout=.1, on_delay=0.0, off_delay=0.0,
                 clock=None, off_error=None):
        self.clock = clock or Clock()
        self.readings = iter(readings)
        self.calls, self.samples, self.find_calls = [], [], []
        self.on_delay, self.off_delay, self.off_error = on_delay, off_delay, off_error
        self.timing = SimpleNamespace(timeout=timeout, add_response_time=self.samples.append)
        self.camera = object()

    def find(self, camera, threshold, display):
        self.find_calls.append((camera, threshold, display, self.clock.now))
        delay, result = next(self.readings)
        self.clock.now += delay
        if isinstance(result, BaseException):
            raise result
        return result

    def set_led(self, index, on):
        self.calls.append((index, on, self.clock.now))
        self.clock.now += self.on_delay if on else self.off_delay
        if not on and self.off_error is not None:
            raise self.off_error

    def run(self):
        return enable_and_find_led(self.camera, self, 17, 2, self.timing, 160, True,
                                   find=self.find, make_led=lambda *args: args, clock=self.clock)


class DetectorTimingTests(unittest.TestCase):
    def test_search_budget_starts_after_on_ack_and_sample_excludes_both_sends(self):
        point = object()
        trial = Trial([(.01, None), (.05, point), (.01, None)], on_delay=.2, off_delay=.2)
        self.assertEqual(trial.run(), (17, 2, point))
        self.assertEqual([on for _, on, _ in trial.calls], [True, False])
        self.assertAlmostEqual(trial.samples[0], .05)
        self.assertEqual([(cam is trial.camera, threshold, display)
                          for cam, threshold, display, _ in trial.find_calls],
                         [(True, 160, True)] * 3)

    def test_positive_tiny_budget_still_reads_one_search_frame(self):
        point = object()
        trial = Trial([(0, None), (0, point), (0, None)], timeout=.000001, clock=Clock(tick=.001))
        self.assertEqual(trial.run(), (17, 2, point))
        self.assertEqual(len(trial.find_calls), 3)

    def test_tiny_adaptive_timeout_allows_detection_at_50ms_without_fixed_hold(self):
        point = object()
        trial = Trial([(.01, None), (.025, None), (.025, point), (.01, None)], timeout=.001)
        self.assertEqual(trial.run(), (17, 2, point))
        self.assertAlmostEqual(trial.samples[0], .05)
        # The 100-ms floor is an allowance, not a mandatory illumination time.
        self.assertAlmostEqual(trial.calls[-1][2] - trial.calls[0][2], .05)

    def test_tiny_adaptive_timeout_gives_miss_full_100ms_allowance(self):
        trial = Trial([(0, None)] + [(.025, None)] * 4 + [(0, None)], timeout=.001)
        self.assertIsNone(trial.run())
        self.assertAlmostEqual(trial.calls[-1][2] - trial.calls[0][2], .1)
        self.assertEqual(len(trial.find_calls), 6)

    def test_persistent_pre_dark_light_fails_before_any_on_command(self):
        trial = Trial([(1.01, object()) for _ in range(10)])
        with self.assertRaises((RuntimeError, TimeoutError)):
            trial.run()
        self.assertFalse(any(on for _, on, _ in trial.calls))
        self.assertLessEqual(len(trial.find_calls), 4)
        self.assertEqual(trial.samples, [])

    def test_miss_waits_for_dark_after_off_before_returning_none(self):
        trial = Trial([(.01, None), (.06, None), (.06, None), (.1, object()), (.1, None)])
        self.assertIsNone(trial.run())
        self.assertEqual([on for _, on, _ in trial.calls], [True, False])
        self.assertEqual(len(trial.find_calls), 5)
        self.assertGreater(trial.clock.now, trial.calls[-1][2] + .19)
        self.assertEqual(trial.samples, [])

    def test_success_with_persistent_post_dark_light_fails_with_bounded_off(self):
        trial = Trial([(.01, None), (.05, object())] + [(1.01, object()) for _ in range(10)])
        with self.assertRaises((RuntimeError, TimeoutError)):
            trial.run()
        self.assertEqual([on for _, on, _ in trial.calls], [True, False])
        self.assertLessEqual(len(trial.find_calls), 6)

    def test_miss_with_persistent_post_dark_light_is_error_not_normal_miss(self):
        trial = Trial([(.01, None), (.11, None)] + [(1.01, object()) for _ in range(10)])
        with self.assertRaises((RuntimeError, TimeoutError)):
            trial.run()
        self.assertEqual([on for _, on, _ in trial.calls], [True, False])
        self.assertLessEqual(len(trial.find_calls), 6)

    def test_search_exception_and_interrupt_attempt_off_and_preserve_cause(self):
        for error in (RuntimeError('camera failed'), KeyboardInterrupt('cancelled')):
            with self.subTest(error=type(error).__name__):
                trial = Trial([(.01, None), (.01, error)], off_error=ValueError('OFF failed'))
                with self.assertRaises(type(error)) as caught:
                    trial.run()
                self.assertIs(caught.exception, error)
                self.assertEqual([on for _, on, _ in trial.calls], [True, False])
                self.assertEqual(trial.samples, [])

    def test_invalid_timeout_is_rejected_before_on(self):
        for timeout in (0, -.1, float('nan'), float('inf')):
            with self.subTest(timeout=timeout):
                trial = Trial([], timeout=timeout)
                with self.assertRaises(ValueError):
                    trial.run()
                self.assertEqual(trial.calls, [])

    def test_search_does_not_depend_on_wall_clock(self):
        point = object()
        trial = Trial([(.01, None), (.05, point), (.01, None)])
        with patch('time.time', side_effect=AssertionError('wall clock must not drive deadlines')):
            self.assertEqual(trial.run(), (17, 2, point))


if __name__ == '__main__':
    unittest.main()
