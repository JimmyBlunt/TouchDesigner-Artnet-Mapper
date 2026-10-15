"""Host/editor integration for real clip-local time and independent fades."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper import show_editor as editor
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer, TransportState
from pixelblaze_mapper.show_timeline_ui import Bridge, TDHost, preserve_transport
from tests.test_show_timeline import FakeHost


class OverlapHostTests(unittest.TestCase):
    def test_restart_installer_retries_until_ready_then_stops(self):
        from pixelblaze_mapper import show_timeline_ui as ui, show_midi, show_pads
        midi = SimpleNamespace(_manager=object(), tick=lambda: None)
        pads = SimpleNamespace(tick=lambda owner: None)
        with patch.dict('sys.modules', td=SimpleNamespace(op=lambda path: object())), \
                patch('pixelblaze_mapper.show_midi', midi), \
                patch('pixelblaze_mapper.show_pads', pads), \
                patch.object(ui, '_overlap_ready', False), \
                patch.object(ui, '_overlap_last_try', -1.), \
                patch.object(ui, '_last_tick', 0.), \
                patch.object(ui, '_bridge', None), \
                patch.object(ui.time, 'monotonic', return_value=10.), \
                patch('pixelblaze_mapper.show_overlap_runtime.install', side_effect=[{'installed': False}, {'installed': True}]) as install:
            ui.tick()
            ui.tick()
            self.assertEqual(install.call_count, 1)
            ui.time.monotonic.return_value = 12.
            ui.tick()
            ui.time.monotonic.return_value = 14.
            ui.tick()
            self.assertTrue(ui._overlap_ready)
            self.assertEqual(install.call_count, 2)

    def test_migration_backup_keeps_all_documents_and_never_overwrites(self):
        texts = dict(show_json='original show', automation_json='original recordings', imported_json='original native values')
        owner = SimpleNamespace(op=lambda name: SimpleNamespace(text=texts[name]))
        with TemporaryDirectory() as folder, patch.dict('sys.modules', td=SimpleNamespace(project=SimpleNamespace(folder=folder))):
            host = TDHost(owner)
            host.backup_timing_change()
            host.backup_timing_change()
            files = list((Path(folder)/'.controller-runtime'/'timing-backups').glob('*.json'))
            self.assertEqual(len(files), 2)
            for file in files:
                self.assertEqual(json.loads(file.read_text(encoding='utf-8')), texts)

    def test_new_show_and_append_defaults_are_independent(self):
        show = editor.empty_show()
        self.assertEqual(show['timing_mode'], 'overlap')
        self.assertNotIn('timing_mode', editor.EMPTY_SHOW)
        cue = editor.new_cue('Fill', editor.parameters_from_player({}), duration=10, transition_duration=3)
        show = editor.append_cue(show, cue)
        self.assertEqual(show['cues'][0]['fade_in'], 3)
        self.assertEqual(show['cues'][0]['fade_out'], 3)
        shorter = editor.update_cue(show, 0, 'duration', 1)
        self.assertEqual(shorter['cues'][0]['fade_in'], 1)
        self.assertEqual(show['cues'][0]['duration'], 10)

    def test_duplicate_and_save_roundtrip_keep_per_clip_fades(self):
        show = editor.append_cue(editor.empty_show(), editor.new_cue('Fill', editor.parameters_from_player({})))
        show['cues'][0].update(fade_in=2, fade_out=4, fade_in_curve='ease_in', fade_out_curve='smooth')
        duplicate = editor.duplicate_cue(show, 0)
        self.assertEqual(duplicate['cues'][1]['fade_out'], 4)
        self.assertEqual(Show.from_dict(duplicate).to_dict(), duplicate)

    def test_appended_fade_in_matches_preceding_overlap_even_for_cut(self):
        first = editor.new_cue('Fill', editor.parameters_from_player({}), duration=10, transition_duration=5)
        second = editor.new_cue('Fill', editor.parameters_from_player({}), duration=10, transition='cut')
        show = editor.append_cue(editor.append_cue(editor.empty_show(), first), second)
        self.assertEqual(show['cues'][1]['fade_in'], 5)
        self.assertEqual(show['cues'][1].get('fade_out', 0), 0)

    def test_finished_show_still_restarts_after_edit(self):
        host = FakeHost()
        old = ShowSequencer(Show.from_dict(dict(host.show, loop=False, timing_mode='overlap')))
        old.play()
        old.advance(100)
        new = ShowSequencer(old.show)
        preserve_transport(old, new)
        self.assertEqual(new.elapsed, new.cue.duration)
        new.play()
        self.assertEqual((new.cue_index, new.elapsed), (0, 0))

    def test_transport_preserves_visible_local_time_on_migration_and_edit(self):
        source = FakeHost().show
        old = ShowSequencer(Show.from_dict(source))
        old.cue_index, old.elapsed, old._current_time_offset = 1, 2, 3
        old.state, old.blackout, old._current_slot = TransportState.PAUSED, True, 'B'
        target = ShowSequencer(Show.from_dict(dict(source, timing_mode='overlap')))
        preserve_transport(old, target)
        self.assertEqual((target.cue_index, target.elapsed, target._current_time_offset), (1, 5, 0))
        self.assertIs(target.state, TransportState.PAUSED)
        self.assertTrue(target.blackout)
        self.assertEqual(target._current_slot, 'B')
        edited = ShowSequencer(target.show)
        preserve_transport(target, edited)
        self.assertEqual(edited.elapsed, 5)

    def test_new_actions_respect_recording_and_revision_guards(self):
        host = FakeHost()
        bridge = Bridge(host)
        before = deepcopy((host.show, host.data))
        host.recording = True
        for action in ('enable_overlap', 'clip_fades'):
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, 'Aufnahme'):
                bridge.execute(dict(action=action, revision=bridge.state['revision']))
        host.recording = False
        with self.assertRaisesRegex(ValueError, 'anderswo'):
            bridge.execute(dict(action='enable_overlap', revision='old'))
        self.assertEqual((host.show, host.data), before)


if __name__ == '__main__':
    unittest.main()
