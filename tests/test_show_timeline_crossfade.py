"""Crossfade boundary edits, persistence and atomic undo contracts."""
from copy import deepcopy
import json
import unittest

from tests.test_show_timeline import FakeHost
from pixelblaze_mapper import show_timeline as timeline
from pixelblaze_mapper.show_timeline_ui import Bridge


class CrossfadeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeHost()
        self.cue = self.host.show['cues'][0]['id']
        self.host.data['transitions'] = {self.cue: dict(points=[[0, 0], [.4, .2], [1, 1]], mode='smooth', enabled=True)}
        self.bridge = Bridge(self.host)

    def edge(self, edge, time):
        return self.bridge.execute(dict(action='transition', cue=self.cue, edge=edge, time=time,
                                        revision=self.bridge.state['revision']))

    def test_start_expands_fade_without_moving_clip_or_recordings(self):
        original = deepcopy(self.host.data)
        self.edge('start', 5)
        self.assertEqual(self.host.show['cues'][0]['duration'], 12)
        self.assertEqual(self.host.show['cues'][0]['transition_duration'], 7)
        self.assertEqual(timeline.layout(self.host.show)[1]['start'], 12)
        self.assertEqual(self.host.data, original)

    def test_end_extends_clip_and_fade_atomically_with_fixed_start(self):
        original = deepcopy((self.host.show, self.host.data))
        self.edge('end', 16)
        self.assertEqual(timeline.layout(self.host.show)[0]['fade_start'], 9)
        self.assertEqual(self.host.show['cues'][0]['transition_duration'], 7)
        self.assertEqual(timeline.layout(self.host.show)[1]['start'], 16)
        self.assertEqual(len(self.bridge.history.undo_stack), 1)
        self.bridge.execute(dict(action='undo', revision=self.bridge.state['revision']))
        self.assertEqual((self.host.show, self.host.data), original)
        self.bridge.execute(dict(action='redo', revision=self.bridge.state['revision']))
        self.bridge.execute(dict(action='save', revision=self.bridge.state['revision']))
        self.assertEqual(json.loads(json.dumps(self.host.saved))[0]['cues'][0]['duration'], 16)

    def test_clamps_crossed_endpoints_and_negative_times(self):
        for edge, time, duration, fade in [('start', -9, 12, 12), ('start', 50, 12, .1), ('end', -5, 9.1, .1)]:
            with self.subTest(edge=edge, time=time):
                host = FakeHost()
                show, _ = timeline.edit(host.show, host.data, dict(action='transition', cue=host.show['cues'][0]['id'], edge=edge, time=time))
                self.assertAlmostEqual(show['cues'][0]['duration'], duration)
                self.assertAlmostEqual(show['cues'][0]['transition_duration'], fade)

    def test_invalid_recording_and_stale_edits_do_not_write(self):
        original = deepcopy((self.host.show, self.host.data))
        for edge, time in [('start', float('nan')), ('end', float('inf')), ('other', 5)]:
            with self.assertRaises(ValueError):
                self.edge(edge, time)
        self.host.recording = True
        with self.assertRaises(ValueError):
            self.edge('start', 5)
        self.host.recording = False
        with self.assertRaises(ValueError):
            self.bridge.execute(dict(action='transition', cue=self.cue, edge='start', time=5, revision='old'))
        self.assertEqual((self.host.show, self.host.data), original)
        self.assertFalse(self.bridge.history.undo_stack)


if __name__ == '__main__':
    unittest.main()
