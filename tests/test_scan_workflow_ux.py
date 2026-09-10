"""Exercise native runtime navigation and scope preservation without hardware."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import build_scan_session_ui as builder
from pixelblaze_mapper import scan_workflow_ux as ux
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget
from tests.test_guided_scan_live import Owner


class ScanWorkflowUXTests(unittest.TestCase):
    def session(self):
        return ScanSession('session', 'scene', 'revision', tuple(
            ScanTarget(name, 'obj', index, index) for index, name in enumerate('abc')), ('a', 'b'))

    def owner(self):
        owner = Owner()
        for name in set(ux.COMMON) | set(ux.CAPTURE) | set(ux.OFFLINE) | set(ux.SETTINGS):
            owner.children['ui_panel/' + name] = SimpleNamespace(par=SimpleNamespace())
        for name in ('views', 'source_ids', 'anchors', 'workspace'):
            owner.children['ui_panel/' + name + '/string'] = SimpleNamespace(text='')
        for prefix in 'trs':
            for axis in 'xyz':
                for suffix in ('', '_label'):
                    owner.children['review_panel/' + prefix + axis + suffix] = SimpleNamespace(par=SimpleNamespace())
                owner.children['review_panel/' + prefix + axis + '/string'] = SimpleNamespace(text='1' if prefix == 's' else '0')
        owner.children['review_panel/alignment_hint'] = SimpleNamespace(par=SimpleNamespace())
        return owner

    def test_compact_scope_roundtrips_sparse_identity(self):
        ids = (0, 1, 2, 7, 9, 10, 517, 785)
        self.assertEqual(builder.parse_indices(ux.compact_indices(ids)), ids)
        self.assertEqual(ux.compact_indices(()), '')

    def test_duplicate_view_paths_do_not_fake_minimum_view_count(self):
        self.assertEqual(ux.view_paths('None | C:/Scan/view.csv | c:\\scan\\view.csv | '), ['C:/Scan/view.csv'])
        self.assertIn('1 saved', ux.guidance(session={'stage': 'planned'}, page='offline', views='a.csv | a.csv'))

    def test_tabs_retain_values_and_always_offer_stop(self):
        owner = self.owner()
        owner.op('ui_panel/source_ids/string').text = '517, 785'
        owner.op('ui_panel/views/string').text = 'first.csv | second.csv'
        for page in ('settings', 'offline', 'capture'):
            owner.store('workflow_page', page)
            ux.refresh(owner)
            self.assertTrue(owner.op('ui_panel/btn_stop').par.display)
            self.assertTrue(owner.op('ui_panel/workspace').par.display)
            self.assertEqual(owner.op('ui_panel/source_ids').par.display, page == 'capture')
            self.assertEqual(owner.op('ui_panel/python').par.display, page == 'settings')
            self.assertEqual(owner.op('ui_panel/views').par.display, page == 'offline')
        self.assertEqual(owner.op('ui_panel/source_ids/string').text, '517, 785')
        self.assertEqual(owner.op('ui_panel/views/string').text, 'first.csv | second.csv')

    def test_navigation_and_help_cannot_launch_capture_or_worker(self):
        owner = self.owner()
        ui = SimpleNamespace(messageBox=Mock())
        scope = {'op': lambda path: owner, 'ui': ui}
        exec(builder._runtime_source(), scope)
        with patch.object(scope['live'], 'start', side_effect=AssertionError('capture started')), \
                patch.object(scope['live'], 'camera_start', side_effect=AssertionError('camera started')), \
                patch.object(scope['offline_job'], 'start', side_effect=AssertionError('worker started')):
            for action in ('page_offline', 'page_settings', 'help', 'review_advanced', 'page_capture'):
                self.assertTrue(scope['act'](action))
        ui.messageBox.assert_called_once()
        self.assertTrue(owner.fetch('review_advanced'))

    def test_open_saved_result_cancel_preserves_state(self):
        owner = self.owner()
        owner.store('session', {'existing': True})
        scope = {'op': lambda path: owner, 'ui': SimpleNamespace(chooseFile=lambda **kwargs: None)}
        exec(builder._runtime_source(), scope)
        with patch('pixelblaze_mapper.scan_result_review.open_review') as review:
            self.assertTrue(scope['act']('open_saved_result'))
            review.assert_not_called()
        self.assertEqual(owner.fetch('session'), {'existing': True})

    def test_hidden_alignment_keeps_current_values_visible(self):
        owner = self.owner()
        owner.op('review_panel/tx/string').text = '125'
        ux.refresh(owner)
        self.assertFalse(owner.op('review_panel/tx').par.display)
        self.assertIn('Translation: 125, 0, 0', owner.op('review_panel/alignment_hint').par.text)
        owner.store('review_advanced', True)
        ux.refresh(owner)
        self.assertTrue(owner.op('review_panel/tx').par.display)
        self.assertFalse(owner.op('review_panel/alignment_hint').par.display)

    def test_workspace_and_view_pickers_support_cancel_and_deduplication(self):
        owner = self.owner()
        owner.op('ui_panel/workspace/string').text = 'C:/old'
        owner.op('ui_panel/views/string').text = 'C:/scan/a.csv'
        ui = SimpleNamespace(chooseFolder=Mock(side_effect=[None, 'C:/new']),
                             chooseFile=Mock(side_effect=[None, 'C:/scan/a.csv', 'C:/scan/b.csv']))
        scope = {'op': lambda path: owner, 'ui': ui}
        exec(builder._runtime_source(), scope)
        self.assertTrue(scope['act']('browse_workspace'))
        self.assertEqual(owner.op('ui_panel/workspace/string').text, 'C:/old')
        self.assertTrue(scope['act']('browse_workspace'))
        self.assertEqual(owner.op('ui_panel/workspace/string').text, 'C:/new')
        for _ in range(3):
            self.assertTrue(scope['act']('add_view'))
        self.assertEqual(owner.op('ui_panel/views/string').text, 'C:/scan/a.csv | C:/scan/b.csv')

    def test_running_3d_stop_is_available_from_every_tab(self):
        owner = self.owner()
        owner.store('offline_status', {'running': True})
        for page in ('capture', 'settings', 'offline'):
            owner.store('workflow_page', page)
            ux.refresh(owner)
            self.assertTrue(owner.op('ui_panel/btn_offline_stop').par.display)

    def test_status_labels_recover_from_stored_facts_after_rebuild(self):
        owner = self.owner()
        owner.store('offline_status', {'state': 'review_required', 'reconstructed': 203})
        owner.store('camera_status', {'state': 'stopped', 'frames': 44, 'width': 640, 'height': 480})
        ux.refresh(owner)
        self.assertIn('203 LEDs', owner.op('ui_panel/offline_status').par.text)
        self.assertIn('stopped', owner.op('ui_panel/camera_status').par.text)
        self.assertIn('640x480', owner.op('ui_panel/camera_status').par.text)

    def test_running_work_takes_priority_over_next_step(self):
        self.assertIn('Keep camera', ux.guidance(capture={'running': True}, page='offline'))
        self.assertIn('STOP 3D', ux.guidance(offline={'running': True}))
        self.assertIn('Review result', ux.guidance(offline={'state': 'review_required'}))
        self.assertIn('SESSION ENDED', ux.guidance(session={'stage': 'cancelled'}))
        self.assertIn('Close camera', ux.guidance(session={'stage': 'planned'}, camera={'state': 'running', 'returncode': None}))

    def test_offline_scope_uses_edited_ids_without_live_routing(self):
        original = self.session()
        selected = builder.offline_scope(original, '1-2', '0')
        self.assertEqual(selected.selected_ids, ('b', 'c'))
        self.assertEqual(selected.anchor_ids, ('a',))
        self.assertEqual(original.selected_ids, ('a', 'b'))
        self.assertEqual(selected.scene_revision, original.scene_revision)

    def test_reprepare_attached_views_gets_new_job_identity(self):
        original = self.session()
        for name in ('first', 'second'):
            original = original.start_view(name).finish_view(('a', 'b'), name + '.csv')
        original = original.request_reconstruction()
        selected = builder.offline_scope(original, '0-1')
        self.assertNotEqual(selected.session_id, original.session_id)
        self.assertEqual(selected.targets, original.targets)
        self.assertEqual(selected.views, ())
        self.assertEqual(len(original.views), 2)

    def test_discovery_and_offline_runtime_pass_edited_scope(self):
        owner = self.owner()
        owner.store('session', self.session().to_dict())
        owner.op('ui_panel/source_ids/string').text = '1-2'
        owner.op('ui_panel/views/string').text = 'a.csv | b.csv'
        scope = {'op': lambda path: owner}
        exec(builder._runtime_source(), scope)
        with patch('pixelblaze_mapper.scan_library.discover_saved_views', return_value={'paths': [], 'message': 'No new views'}) as discover:
            self.assertTrue(scope['act']('discover_views'))
            self.assertEqual(discover.call_args.kwargs['session'].selected_ids, ('b', 'c'))
        scope['attach_existing_views'] = Mock(side_effect=ValueError('Stop after scope validation'))
        with patch.object(scope['live'], '_capture', None), patch.object(scope['offline_job'], '_job', None), \
                patch.object(scope['live'], 'prepare', side_effect=AssertionError('Hardware routing invoked')):
            self.assertFalse(scope['act']('offline'))
        self.assertEqual(scope['attach_existing_views'].call_args.args[0].selected_ids, ('b', 'c'))
        self.assertEqual(tuple(owner.fetch('session')['selected_ids']), ('a', 'b'))

    def test_manual_view_edit_requires_manifest_reprepare(self):
        owner = self.owner()
        owner.store('manifest', 'old-job.json')
        owner.store('manifest_view_paths', ['first.csv', 'second.csv'])
        owner.op('ui_panel/views/string').text = 'first.csv | second.csv | third.csv'
        scope = {'op': lambda path: owner}
        exec(builder._runtime_source(), scope)
        with patch.object(scope['offline_job'], 'start') as start:
            self.assertFalse(scope['act']('offline_start'))
            start.assert_not_called()
        self.assertIn('View list changed', owner.fetch('message'))

    def test_visible_form_rectangles_do_not_overlap(self):
        # Brightness fill and marker intentionally overlay the slider.
        for page in (ux.CAPTURE, ux.OFFLINE, ux.SETTINGS):
            items = {**ux.COMMON, **page}
            items = {name: rect for name, rect in items.items() if name not in ('brightness_fill', 'brightness_marker')}
            for name, (x, y, w, h) in items.items():
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, 1160)
                self.assertLessEqual(y + h, 900)
                for other, (ox, oy, ow, oh) in items.items():
                    if name >= other:
                        continue
                    self.assertFalse(x < ox + ow and ox < x + w and y < oy + oh and oy < y + h,
                                     '%s overlaps %s' % (name, other))


if __name__ == '__main__':
    unittest.main()
