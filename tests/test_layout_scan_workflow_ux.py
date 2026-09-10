"""Exercise Layout's real scan action with TD widgets mocked, without hardware."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import layout_scene_td as td
from pixelblaze_mapper.layout_scene import Scene, Scan, SceneError, Transform, append_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor


def document():
    # Local positions, original scan indices and global addresses deliberately differ.
    first = Scan('first-scan', 'First', tuple((i, i + 1, i + 2) for i in range(8)))
    scene = append_scan(Scene('room', 'Room'), first, object_id='first-object',
                        scan_indices=(1, 3, 5, 7), source_indices=(517, 519, 800, 1200))
    second = Scan('second-scan', 'Second', ((8, 9, 10), (10, 11, 12)))
    scene = append_scan(scene, second, object_id='second-object', source_indices=(22, 35))
    return LayoutDocument(scene)


class TextDAT:
    def __init__(self, text=''):
        self.text = text

    @property
    def numRows(self):
        return int(bool(self.text))

    def __getitem__(self, key):
        if key != (0, 0) or not self.numRows:
            raise IndexError(key)
        return self.text


class Owner:
    def __init__(self, session):
        self.storage = {'layout_editor_session': session}
        self.stage_scene = Mock()
        self.viewer = Mock()
        self.nodes = {
            'ui_panel/localrange/string': TextDAT(),
            'ui_panel/objectno/string': TextDAT('1'),
            'ui_panel/status': SimpleNamespace(par=SimpleNamespace(text='')),
            '/project1/guided_scan/ui_panel': SimpleNamespace(openViewer=self.viewer),
            '/project1/guided_scan/runtime': SimpleNamespace(
                module=SimpleNamespace(stage_scene=self.stage_scene)),
        }

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def store(self, key, value):
        self.storage[key] = value

    def op(self, path):
        return self.nodes.get(path)


class SelectedScanIdentityTests(unittest.TestCase):
    def setUp(self):
        self.scene = document().scene
        self.leds = self.scene.object('first-object').leds

    def test_local_selection_uses_stable_ids_and_preserves_requested_order(self):
        selected = td.selected_scan_ids(self.scene, 'first-object', '3, 0-1')
        self.assertEqual(selected, (self.leds[3].led_id, self.leds[0].led_id, self.leds[1].led_id))
        self.assertEqual(tuple(led.source_index for led in self.leds), (517, 519, 800, 1200))

    def test_blank_is_all_selected_object_leds_only(self):
        expected = tuple(led.led_id for led in self.leds)
        for value in ('', '  '):
            with self.subTest(value=value):
                self.assertEqual(td.selected_scan_ids(self.scene, 'first-object', value), expected)

    def test_invalid_ranges_and_missing_object_fail(self):
        for value in ('4', '-1', '2-1', '0-1,1', '517', 'a', '0,', '0-1000002'):
            with self.subTest(value=value), self.assertRaises(SceneError):
                td.selected_scan_ids(self.scene, 'first-object', value)
        for object_id in (None, 'unknown'):
            with self.subTest(object_id=object_id), self.assertRaises(SceneError):
                td.selected_scan_ids(self.scene, object_id, '')


class ScanImportFormatTests(unittest.TestCase):
    def test_auto_formats_ignore_case_and_allow_blank_preference(self):
        for path, expected in (
                ('scan.csv', 'marimapper-csv'), ('SCAN.CSV', 'marimapper-csv'),
                ('room.json', 'pixelblaze'), ('room.JS', 'pixelblaze'),
                ('room.map', 'pixelblaze')):
            for requested in ('auto', ' AUTO ', ''):
                with self.subTest(path=path, requested=requested):
                    self.assertEqual(td.scan_import_format(path, requested), expected)

    def test_explicit_format_is_preserved_and_unknown_auto_extension_rejected(self):
        self.assertEqual(td.scan_import_format('scan.data', ' MARIMAPPER-CSV '), 'marimapper-csv')
        self.assertEqual(td.scan_import_format('scan.csv', 'pixelblaze'), 'pixelblaze')
        for path in ('readme.txt', 'scan', 'scan.csv.exe'):
            with self.subTest(path=path), self.assertRaises(SceneError):
                td.scan_import_format(path)


class LayoutScanActionTests(unittest.TestCase):
    def setUp(self):
        self.session = LayoutEditor(document())
        self.owner = Owner(self.session)
        self.refresh = patch.object(td, 'refresh').start()
        self.addCleanup(patch.stopall)
        self.chooser = Mock(side_effect=AssertionError('Scan staging must not open a file chooser'))
        self.confirm = Mock(side_effect=AssertionError('Staging must not request hardware permission'))

    def scan(self, text=''):
        self.owner.nodes['ui_panel/localrange/string'].text = text
        td.action(self.owner, 'scan', self.chooser, self.confirm)

    def test_actual_action_stages_stable_selected_ids_without_mutating_draft(self):
        before = self.session.current
        leds = before.scene.object('first-object').leds
        self.scan('1,3')
        self.owner.stage_scene.assert_called_once_with(
            before.scene, 'first-object', selected_ids=(leds[1].led_id, leds[3].led_id))
        self.owner.viewer.assert_called_once_with()
        self.assertIs(self.session.current, before)
        self.assertEqual(self.session._undo, [])
        self.assertIn('2 selected LEDs', self.owner.nodes['ui_panel/status'].par.text)

    def test_blank_stages_all_of_current_selection(self):
        self.session.select('second-object')
        leds = self.session.current.scene.object('second-object').leds
        self.scan('   ')
        self.owner.stage_scene.assert_called_once_with(
            self.session.current.scene, 'second-object', selected_ids=tuple(led.led_id for led in leds))

    def test_invalid_ranges_do_not_stage_or_open_previous_session(self):
        for value in ('4', '517', '1-0', '0,0', 'not a range'):
            with self.subTest(value=value):
                self.scan(value)
                self.owner.stage_scene.assert_not_called()
                self.owner.viewer.assert_not_called()
                self.assertIn('BLOCKED', self.owner.nodes['ui_panel/status'].par.text)

    def test_drag_preview_blocks_scan_without_discarding_preview(self):
        self.session.transform(Transform(translation=(1, 0, 0)), preview=True)
        preview = self.session.preview
        self.scan()
        self.owner.stage_scene.assert_not_called()
        self.owner.viewer.assert_not_called()
        self.assertIs(self.session.preview, preview)
        self.assertIn('drag', self.owner.nodes['ui_panel/status'].par.text)

    def test_missing_selection_and_panel_do_not_stage(self):
        self.session.selected_object_id = None
        self.scan()
        self.owner.stage_scene.assert_not_called()
        self.assertIn('Select an object', self.owner.nodes['ui_panel/status'].par.text)
        self.session.select('first-object')
        del self.owner.nodes['/project1/guided_scan/ui_panel']
        self.scan()
        self.owner.stage_scene.assert_not_called()
        self.owner.viewer.assert_not_called()

    def test_staging_failure_does_not_open_previous_session(self):
        self.owner.stage_scene.side_effect = ValueError('Stop the previous capture first')
        self.scan('1')
        self.owner.viewer.assert_not_called()
        self.assertIn('Stop the previous capture first', self.owner.nodes['ui_panel/status'].par.text)

    def test_selection_changed_without_refresh_cannot_reuse_previous_local_range(self):
        self.owner.store('scan_range_object', 'first-object')
        self.session.select('second-object')
        self.scan('1')
        self.owner.stage_scene.assert_not_called()
        self.owner.viewer.assert_not_called()
        self.assertIn('Selected object changed', self.owner.nodes['ui_panel/status'].par.text)

    def test_missing_runtime_must_not_report_success_or_show_stale_session(self):
        for runtime in (None, SimpleNamespace(module=SimpleNamespace())):
            with self.subTest(runtime=runtime):
                self.owner.nodes['/project1/guided_scan/runtime'] = runtime
                self.scan()
                self.owner.viewer.assert_not_called()
                self.assertIn('BLOCKED', self.owner.nodes['ui_panel/status'].par.text)


class RefreshScanRangeBindingTests(unittest.TestCase):
    def setUp(self):
        self.session = LayoutEditor(document())
        self.owner = Owner(self.session)
        for name in ('objects', 'draft_badge', 'provenance'):
            self.owner.nodes['ui_panel/' + name] = SimpleNamespace(par=SimpleNamespace(text=''))
        self.owner.nodes['instances'] = SimpleNamespace(cook=Mock())
        self.persistence = patch('pixelblaze_mapper.layout_session_storage.persist_layout').start()
        self.addCleanup(patch.stopall)

    def test_real_refresh_clears_range_when_selected_object_changes(self):
        td.refresh(self.owner, fields=False, save=False)
        self.owner.nodes['ui_panel/localrange/string'].text = '0-1'
        self.session.select('second-object')
        td.refresh(self.owner, fields=False, save=False)
        self.assertEqual(self.owner.nodes['ui_panel/localrange/string'].text, '')
        self.assertEqual(self.owner.fetch('scan_range_object'), 'second-object')

    def test_real_refresh_keeps_range_during_same_object_updates(self):
        td.refresh(self.owner, fields=False, save=False)
        self.owner.nodes['ui_panel/localrange/string'].text = '1,3'
        self.session.transform(Transform(translation=(1, 0, 0)), preview=True)
        td.refresh(self.owner, fields=False, save=False)
        self.assertEqual(self.owner.nodes['ui_panel/localrange/string'].text, '1,3')
        self.assertEqual(self.owner.fetch('scan_range_object'), 'first-object')


if __name__ == '__main__':
    unittest.main()
