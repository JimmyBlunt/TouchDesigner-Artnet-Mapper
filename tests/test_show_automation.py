"""Contract tests for recorded Show Control parameter moves."""
import unittest

from pixelblaze_mapper import show_automation as automation
from pixelblaze_mapper.show_automation import AutomationError, Recorder


def _ramp(cue_id='c1', parameter='speed', steps=20, step=0.1):
    recorder = Recorder(cue_id)
    for index in range(steps):
        recorder.sample(index * step, {parameter: float(index)})
    return recorder.result()


class RecordingTests(unittest.TestCase):
    def test_untouched_parameters_are_not_recorded(self):
        recorder = Recorder('c1')
        for index in range(50):
            recorder.sample(index * 0.05, {'speed': 1.0 + index * 0.1, 'scale': 4.0})
        tracks = recorder.result()
        self.assertIn('speed', tracks)
        self.assertNotIn('scale', tracks, 'a constant control must not fill the track')

    def test_repeated_values_collapse(self):
        recorder = Recorder('c1')
        for index in range(100):
            recorder.sample(index * 0.05, {'speed': 2.0})
        self.assertTrue(recorder.is_empty())

    def test_samples_inside_one_frame_replace_instead_of_stacking(self):
        recorder = Recorder('c1')
        recorder.sample(0.0, {'speed': 1.0})
        for index in range(20):
            recorder.sample(0.001 * index, {'speed': 1.0 + index})
        self.assertLessEqual(len(recorder.result().get('speed', [])), 2)

    def test_non_recordable_parameters_are_ignored(self):
        recorder = Recorder('c1')
        for index in range(10):
            recorder.sample(index * 0.1, {'gradient': index, 'seed': index})
        self.assertTrue(recorder.is_empty())

    def test_sample_cap_is_enforced(self):
        recorder = Recorder('c1', max_samples=5)
        for index in range(50):
            recorder.sample(index * 0.1, {'speed': float(index)})
        self.assertLessEqual(len(recorder.result()['speed']), 5)
        self.assertGreater(recorder.dropped, 0)

    def test_recorder_needs_a_cue_id(self):
        with self.assertRaises(AutomationError):
            Recorder('  ')

    def test_negative_time_is_refused(self):
        with self.assertRaises(AutomationError):
            Recorder('c1').sample(-1.0, {'speed': 1.0})


class PlaybackTests(unittest.TestCase):
    def test_linear_interpolation_between_samples(self):
        track = [[0.0, 0.0], [2.0, 10.0]]
        self.assertAlmostEqual(automation.value_at(track, 0.0), 0.0)
        self.assertAlmostEqual(automation.value_at(track, 1.0), 5.0)
        self.assertAlmostEqual(automation.value_at(track, 2.0), 10.0)

    def test_ends_are_held_not_extrapolated(self):
        track = [[1.0, 4.0], [2.0, 8.0]]
        self.assertAlmostEqual(automation.value_at(track, 0.0), 4.0)
        self.assertAlmostEqual(automation.value_at(track, 99.0), 8.0)

    def test_lookup_matches_a_linear_recording(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        for elapsed, expected in ((0.0, 0.0), (0.5, 5.0), (1.0, 10.0), (1.9, 19.0)):
            with self.subTest(elapsed=elapsed):
                self.assertAlmostEqual(
                    automation.values_at(data, 'c1', elapsed)['speed'], expected, places=6)

    def test_unknown_cue_returns_nothing(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        self.assertEqual(automation.values_at(data, 'other', 1.0), {})

    def test_empty_track_is_refused(self):
        with self.assertRaises(AutomationError):
            automation.value_at([], 0.0)


class StorageTests(unittest.TestCase):
    def test_round_trip_through_validate(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        self.assertEqual(automation.validate(data), data)
        self.assertEqual(automation.cue_ids(data), ('c1',))

    def test_merge_leaves_other_cues_alone(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        data = automation.merge(data, 'c2', _ramp(parameter='density'))
        self.assertEqual(automation.cue_ids(data), ('c1', 'c2'))
        self.assertIn('speed', data['tracks']['c1'])
        self.assertIn('density', data['tracks']['c2'])

    def test_merging_nothing_clears_the_cue(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        self.assertEqual(automation.cue_ids(automation.merge(data, 'c1', {})), ())

    def test_clear_and_rename(self):
        data = automation.merge(automation.empty(), 'c1', _ramp())
        self.assertEqual(automation.cue_ids(automation.clear_cue(data, 'c1')), ())
        moved = automation.rename_cue(data, 'c1', 'c9')
        self.assertEqual(automation.cue_ids(moved), ('c9',))

    def test_track_length_reports_the_last_sample(self):
        data = automation.merge(automation.empty(), 'c1', _ramp(steps=11, step=0.5))
        self.assertAlmostEqual(automation.track_length(data, 'c1'), 5.0)

    def test_malformed_input_is_refused(self):
        cases = (
            {'schema': 'other', 'version': 1, 'tracks': {}},
            {'schema': automation.SCHEMA, 'version': 99, 'tracks': {}},
            {'schema': automation.SCHEMA, 'version': 1, 'tracks': []},
        )
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(AutomationError):
                    automation.validate(case)

    def test_unordered_or_negative_samples_are_refused(self):
        for samples in ([[1.0, 0.0], [0.5, 1.0]], [[-1.0, 0.0], [1.0, 1.0]]):
            with self.subTest(samples=samples):
                with self.assertRaises(AutomationError):
                    automation.merge(automation.empty(), 'c1', {'speed': samples})

    def test_unrecordable_parameter_is_refused_on_merge(self):
        with self.assertRaises(AutomationError):
            automation.merge(automation.empty(), 'c1', {'gradient': [[0.0, 1.0], [1.0, 2.0]]})


if __name__ == '__main__':
    unittest.main()


class DiagnosisTests(unittest.TestCase):
    """A take can come back empty for three different reasons."""

    def test_untouched_controls_report_no_movement(self):
        recorder = Recorder('c1')
        for index in range(20):
            recorder.sample(index * 0.1, {'speed': 2.0})
        self.assertTrue(recorder.is_empty())
        self.assertEqual(recorder.diagnosis(), 'no-movement')

    def test_a_standing_clock_is_reported_separately(self):
        # The transport was not playing: cue time never advanced, so every
        # sample lands on the same instant and collapses into one.
        recorder = Recorder('c1')
        for index in range(20):
            recorder.sample(0.0, {'speed': 1.0 + index})
        self.assertTrue(recorder.is_empty())
        self.assertGreater(recorder.changes, 0)
        self.assertEqual(recorder.span, 0.0)
        self.assertEqual(recorder.diagnosis(), 'no-time')

    def test_a_good_take_has_no_diagnosis(self):
        recorder = Recorder('c1')
        for index in range(20):
            recorder.sample(index * 0.1, {'speed': 1.0 + index})
        self.assertFalse(recorder.is_empty())
        self.assertEqual(recorder.diagnosis(), '')
        self.assertAlmostEqual(recorder.span, 1.9)


class SurvivalTests(unittest.TestCase):
    """A take must outlive the host module that started it."""

    def test_take_resumes_from_its_stored_state(self):
        recorder = Recorder('c1')
        for index in range(6):
            recorder.sample(index * 0.2, {'speed': float(index)})
        carried = recorder.state          # all the host has to keep
        resumed = Recorder.from_state(carried)
        for index in range(6, 12):
            resumed.sample(index * 0.2, {'speed': float(index)})
        self.assertEqual(len(resumed.result()['speed']), 12)
        self.assertAlmostEqual(resumed.span, 2.2)
        self.assertEqual(resumed.cue_id, 'c1')

    def test_state_is_plain_data(self):
        recorder = Recorder('c1')
        recorder.sample(0.0, {'speed': 1.0})
        recorder.sample(1.0, {'speed': 2.0})
        import json as _json
        self.assertEqual(_json.loads(_json.dumps(recorder.state))['cue_id'], 'c1')

    def test_mutating_through_one_view_is_seen_by_the_other(self):
        # The host keeps one dict; both views must write into it, or a reload
        # would quietly fork the take.
        first = Recorder('c1')
        second = Recorder.from_state(first.state)
        first.sample(0.0, {'speed': 1.0})
        second.sample(1.0, {'speed': 5.0})
        self.assertEqual(len(first.result()['speed']), 2)

    def test_incomplete_state_is_refused(self):
        with self.assertRaises(AutomationError):
            Recorder.from_state({'cue_id': 'c1'})
        with self.assertRaises(AutomationError):
            Recorder.from_state('not a dict')

    def test_blank_take_helper(self):
        take = automation.new_take('c9')
        self.assertEqual(Recorder.from_state(take).cue_id, 'c9')
        self.assertTrue(Recorder.from_state(take).is_empty())
