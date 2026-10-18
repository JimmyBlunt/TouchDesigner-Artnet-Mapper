"""Coverage actions must never retain another panel after refresh or failure."""
import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import scan_coverage_visual_ui as ui
from pixelblaze_mapper.standalone_scan import session


class CoverageUITests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.session = session({'name': 'Current panel', 'target': '192.0.2.1',
                                'interface': '192.0.2.2', 'universe': 1,
                                'count': 3, 'rate': 30, 'order': 'RGB'})
        self.view = self.root / 'view.csv'
        self.view.write_text('index,u,v\n0,.1,.2\n1,.2,.2\n')
        (self.root / 'capture.json').write_text(json.dumps({
            'scene_revision': self.session.scene_revision,
            'identity': {str(t.source_index): t.led_id for t in self.session.targets}}))
        (self.root / 'result.json').write_text(json.dumps({'state': 'complete'}))
        self.values = {'session': self.session.to_dict(), 'coverage_visual_revision': 4,
                       'coverage_visual_data': {'views': [{'path': 'old-panel'}]}}
        self.nodes = {}
        def node(path):
            if path not in self.nodes:
                self.nodes[path] = SimpleNamespace(par=SimpleNamespace(text='old-panel'),
                                                  text='', cook=Mock(), openViewer=Mock(),
                                                  op=lambda child: node(path+'/'+child))
            return self.nodes[path]
        self.owner = SimpleNamespace(path=ui.OWNER, op=node,
                                     fetch=lambda key, default=None: self.values.get(key, default),
                                     store=lambda key, value: self.values.__setitem__(key, value))
        node('ui_panel/views/string').text = str(self.view)
        self.addCleanup(patch.stopall)
        patch.object(ui, 'style_button').start()

    def act(self, command='refresh'):
        return ui.act(lambda path: self.owner, command)

    def candidate(self, session_id):
        path = self.root / 'candidate_3d.csv'
        path.write_text('index,x,y,z\n0,0,0,0\n')
        (self.root / 'quality_pending.json').write_text(json.dumps({
            'session_id': session_id, 'reconstructed_ids': [0]}))
        return str(path)

    def test_previous_panel_candidate_does_not_block_current_saved_views(self):
        self.values['offline_status'] = {'state': 'review_required', 'session_id': 'old-panel',
                                         'candidate': self.candidate('old-panel')}
        self.assertTrue(self.act('open'))
        data = self.values['coverage_visual_data']
        self.assertFalse(data['has_candidate'])
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['views'][0]['path'], str(self.view.resolve()))
        self.assertIn('2/3 erkannt', self.owner.op('coverage_visual_panel/summary').par.text)
        self.assertIn('NIE ERKANNT (Scanindizes ab 0):\n2',
                      self.owner.op('coverage_visual_panel/detail').par.text)
        self.owner.op('coverage_visual_image').cook.assert_called_once_with(force=True)
        self.owner.op('coverage_visual_panel').openViewer.assert_called_once()

    def test_matching_candidate_still_shows_reconstruction(self):
        self.values['offline_status'] = {'state': 'review_required',
            'session_id': self.session.session_id, 'candidate': self.candidate(self.session.session_id)}
        self.assertTrue(self.act())
        self.assertTrue(self.values['coverage_visual_data']['has_candidate'])
        self.assertIn('1/3 in 3D', self.owner.op('coverage_visual_panel/summary').par.text)

    def test_partial_next_scan_keeps_completed_full_acquisition_visible(self):
        partial = replace(self.session, selected_ids=(self.session.targets[2].led_id,))
        self.values['session'] = partial.to_dict()
        self.values['standalone_capture'] = {'count': 3}
        self.assertTrue(self.act())
        self.assertEqual(self.values['coverage_visual_data']['total'], 3)
        self.assertEqual(len(self.values['coverage_visual_data']['views'][0]['points']), 2)
        self.assertEqual(self.values['session'], partial.to_dict())

    def test_failed_validation_clears_old_image_and_labels(self):
        self.values['offline_status'] = {'state': 'review_required',
            'session_id': self.session.session_id, 'candidate': self.candidate('wrong-report')}
        self.assertFalse(self.act())
        self.assertEqual(ui._view(self.owner), ({}, 0, None))
        self.assertGreater(self.values['coverage_visual_revision'], 4)
        self.assertEqual(self.owner.op('coverage_visual_panel/detail').par.text, '')
        self.assertEqual(self.owner.op('coverage_visual_panel/view_name').par.text, '')
        self.assertIn('identity', self.owner.op('coverage_visual_panel/footer').par.text)
        self.owner.op('coverage_visual_image').cook.assert_called_once_with(force=True)

    def test_empty_selection_clears_previous_panel(self):
        self.owner.op('ui_panel/views/string').text = ''
        self.assertTrue(self.act())
        self.assertIsNone(ui._view(self.owner)[2])
        self.assertEqual(self.owner.op('coverage_visual_panel/detail').par.text, '')
        self.assertEqual(self.owner.op('coverage_visual_panel/view_name').par.text, '')
        self.owner.op('coverage_visual_image').cook.assert_called_once_with(force=True)

    def test_navigation_recooks_image_without_reading_scan_files(self):
        self.assertTrue(self.act())
        with patch('pixelblaze_mapper.scan_coverage_visual.build_data', side_effect=AssertionError):
            self.assertTrue(self.act('next'))
        self.assertEqual(self.owner.op('coverage_visual_image').cook.call_count, 2)


if __name__ == '__main__':
    unittest.main()
