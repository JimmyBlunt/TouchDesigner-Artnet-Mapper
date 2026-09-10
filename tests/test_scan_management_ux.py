"""Persistence, source ownership and review regressions; no hardware calls."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.layout_scene import Scene, SceneError, import_scan, new_id
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor
from pixelblaze_mapper.scan_library import discover_saved_views
from pixelblaze_mapper.scan_result_review import (
    append_reviewed, compact_ids, format_review_summary, inspect_saved_result, open_review, review_defaults,
)
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget


class ScanManagementTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        targets = tuple(ScanTarget('led-%d' % i, 'object', i, i) for i in range(3))
        self.session = ScanSession('session', 'scene', 'revision', targets, tuple(t.led_id for t in targets))
        self.no_socket = patch('socket.socket', side_effect=AssertionError('no hardware')).start()
        self.no_process = patch('subprocess.Popen', side_effect=AssertionError('no process')).start()
        self.addCleanup(patch.stopall)

    def saved_view(self, name, *, revision='revision', identity=None, state='complete'):
        folder = self.root / ('capture-' + name)
        folder.mkdir()
        path = folder / 'view.csv'
        path.write_text('index,u,v\n0,.1,.2\n2,.3,.4\n')
        (folder / 'capture.json').write_text(json.dumps({
            'scene_revision': revision,
            'identity': identity if identity is not None else {'0': 'led-0', '1': 'led-1', '2': 'led-2'},
        }))
        (folder / 'result.json').write_text(json.dumps({'state': state}))
        return path

    def saved_result(self):
        folder = self.root / 'result-original'
        folder.mkdir()
        path = folder / 'candidate_3d.csv'
        path.write_text('index,x,y,z,xn,yn,zn,error\n0,1,2,3,0,0,0,.1\n2,4,5,6,0,0,0,.2\n')
        (folder / 'quality_pending.json').write_text(json.dumps({'session_id': 's', 'reconstructed_ids': [0, 2]}))
        return path

    def test_discovery_never_mixes_same_numeric_ids_from_other_objects(self):
        matching = self.saved_view('matching')
        self.saved_view('other-object', identity={'0': 'other-0', '1': 'other-1', '2': 'other-2'})
        self.saved_view('stale', revision='old')
        self.saved_view('incomplete', state='failed')
        result = discover_saved_views(self.root, self.session)
        self.assertEqual(result['paths'], [str(matching.resolve())])
        self.assertEqual(len(result['available']), 3)
        self.assertEqual(len(result['skipped']), 1)
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()

    def test_unstaged_and_legacy_views_require_explicit_selection(self):
        self.saved_view('matching')
        (self.root / 'old.csv').write_text('index,u,v\n0,.2,.3\n')
        result = discover_saved_views(self.root)
        self.assertEqual(result['paths'], [])
        self.assertEqual(len(result['available']), 2)
        self.assertIn('first', result['message'])

    def test_partial_scope_rejects_extra_observed_ids(self):
        self.saved_view('full')
        partial = ScanSession('session', 'scene', 'revision', self.session.targets, ('led-0',))
        self.assertEqual(discover_saved_views(self.root, partial)['paths'], [])

    def test_saved_result_reopens_without_worker_and_does_not_invent_missing_observations(self):
        review = inspect_saved_result(self.saved_result())
        self.assertIsNone(review['missing_observed_ids'])
        self.assertIn('unknown', format_review_summary(review))
        self.assertEqual(review['ids'], [0, 2])
        self.assertFalse(review['registration'])
        self.no_process.assert_not_called()

    def test_saved_result_requires_matching_report_and_rechecks_before_append(self):
        path = self.saved_result()
        review = inspect_saved_result(path)
        report = path.parent / 'quality_pending.json'
        report.write_text(json.dumps({'session_id': 's', 'reconstructed_ids': [0, 1]}))
        with self.assertRaisesRegex(SceneError, 'differ'):
            inspect_saved_result(path)
        with self.assertRaisesRegex(SceneError, 'changed'):
            append_reviewed(LayoutDocument(Scene(new_id(), 'draft')), review, source_offset=0, name='new')

    def test_saved_result_rejects_nonfinite_quality_metadata(self):
        path = self.saved_result()
        path.write_text(path.read_text().replace('0,0,0,.1', '0,0,nan,.1'))
        with self.assertRaisesRegex(SceneError, 'nonfinite'):
            inspect_saved_result(path)

    def test_review_defaults_are_fresh_per_result_and_preserve_user_edits_on_reopen(self):
        path = self.saved_result()
        from tests.test_guided_scan_live import Owner
        owner, panel = Owner(), Owner()
        panel.openViewer = lambda: None
        owner.children['review_panel'] = panel
        panel.children['summary'] = SimpleNamespace(par=SimpleNamespace(text=''))
        panel.children['notice'] = SimpleNamespace(par=SimpleNamespace(text=''))
        for name in ('name', 'offset', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
            panel.children[name + '/string'] = SimpleNamespace(text='stale')
        document = LayoutDocument(Scene(new_id(), 'draft'))
        with patch('pixelblaze_mapper.layout_scene_td.editor', return_value=SimpleNamespace(current=document)):
            open_review(lambda name: owner, path=path)
            self.assertEqual(panel.op('offset/string').text, '0')
            self.assertEqual(panel.op('tx/string').text, '0')
            self.assertEqual(panel.op('sx/string').text, '1')
            panel.op('name/string').text = 'My scan'
            panel.op('tx/string').text = '2'
            open_review(lambda name: owner, path=path)
            self.assertEqual(panel.op('name/string').text, 'My scan')
            self.assertEqual(panel.op('tx/string').text, '2')

    def test_offset_defaults_avoid_collision_without_packing_sparse_ids(self):
        review = inspect_saved_result(self.saved_result())
        editor = LayoutEditor(LayoutDocument(Scene(new_id(), 'draft')))
        editor.append(import_scan('[[0,0,0],[1,1,1]]', format='pixelblaze', name='Raw scan'), source_start=0)
        defaults = review_defaults(editor.current, review)
        self.assertEqual(defaults, {'name': 'Raw scan 2', 'offset': '2'})
        updated = append_reviewed(editor.current, review, source_offset=int(defaults['offset']), name=defaults['name'])
        self.assertEqual([led.source_index for led in updated.scene.objects[-1].leds], [2, 4])
        self.assertEqual(updated.scene.objects[0], editor.current.scene.objects[0])
        with self.assertRaisesRegex(SceneError, 'use offset 2'):
            append_reviewed(editor.current, review, source_offset=0, name='collision')

    def test_large_missing_lists_have_bounded_readable_summary(self):
        self.assertEqual(compact_ids([0, 1, 2, 5, 6, 9]), '0-2, 5-6, 9')
        self.assertLess(len(compact_ids(range(0, 100000, 2))), 100)
