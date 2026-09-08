"""Execute the actual TD runtime against empty Text DATs, without hardware."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper import build_scan_session_ui as builder
from pixelblaze_mapper import guided_scan_live as live
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget
from tests.test_guided_scan_live import Owner


class EmptyTextDAT:
    def __init__(self, text=''):
        self.text = text

    def __getitem__(self, key):
        raise RuntimeError('Cell does not exist')

    def __setitem__(self, key, value):
        raise RuntimeError('Cell does not exist')


class ScanUIStagingTests(unittest.TestCase):
    def setUp(self):
        self.owner = Owner()
        for name in ('source_ids', 'anchors'):
            self.owner.children['ui_panel/' + name + '/string'] = EmptyTextDAT()
        for name in ('worker_plan', 'dry_run'):
            self.owner.children[name] = EmptyTextDAT('old job')
        for name in ('status', 'routing_summary'):
            self.owner.children['ui_panel/' + name] = SimpleNamespace(par=SimpleNamespace(text='old'))
        for key in ('session', 'standalone_capture', 'capture_plan', 'capture_signature',
                    'manifest', 'candidate', 'merge_request'):
            self.owner.store(key, {'old': True})
        self.state = ScanSession('session', 'scene', 'revision',
            (ScanTarget('led0', 'obj', 0, 517),), ('led0',))
        self.ns = {'op': lambda path: self.owner}
        exec(builder._runtime_source(), self.ns)
        self.ns['plan_scene'] = lambda *args: self.state
        self.capture_patch = patch.object(live, '_capture', None)
        self.capture_patch.start()
        self.addCleanup(self.capture_patch.stop)

    def test_empty_text_dat_stages_and_invalidates_previous_plan(self):
        self.ns['stage_scene'](None, 'obj')
        self.assertEqual(self.owner.children['ui_panel/source_ids/string'].text, '517')
        self.assertEqual(self.ns['_field']('anchors'), '')
        self.assertEqual(self.owner.fetch('session'), self.state.to_dict())
        for key in ('standalone_capture', 'capture_plan', 'capture_signature',
                    'manifest', 'candidate', 'merge_request'):
            self.assertIsNone(self.owner.fetch(key))
        self.assertEqual(self.owner.children['worker_plan'].text, '')
        self.assertEqual(self.owner.children['dry_run'].text, '')

    def test_missing_widget_preserves_previous_session_and_scope(self):
        del self.owner.children['ui_panel/anchors/string']
        before = copy.deepcopy(self.owner.storage)
        with self.assertRaisesRegex(ValueError, 'anchors'):
            self.ns['stage_scene'](None, 'obj')
        self.assertEqual(self.owner.storage, before)
        self.assertEqual(self.owner.children['ui_panel/source_ids/string'].text, '')

    def test_running_capture_cannot_be_retargeted(self):
        before = copy.deepcopy(self.owner.storage)
        live._capture = SimpleNamespace(process=SimpleNamespace(poll=lambda: None))
        with self.assertRaisesRegex(ValueError, 'Stop'):
            self.ns['stage_scene'](None, 'obj')
        self.assertEqual(self.owner.storage, before)

    def test_scope_write_failure_rolls_back_fields_before_session_change(self):
        class FailOnce:
            def __init__(self):
                self.value = 'old anchors'
                self.fail = True
            @property
            def text(self):
                return self.value
            @text.setter
            def text(self, value):
                if self.fail:
                    self.fail = False
                    raise RuntimeError('write failure')
                self.value = value
        self.owner.children['ui_panel/anchors/string'] = FailOnce()
        before = copy.deepcopy(self.owner.storage)
        with self.assertRaisesRegex(RuntimeError, 'write failure'):
            self.ns['stage_scene'](None, 'obj')
        self.assertEqual(self.owner.storage, before)
        self.assertEqual(self.owner.children['ui_panel/source_ids/string'].text, '')
        self.assertEqual(self.ns['_field']('anchors'), 'old anchors')

    def test_empty_builder_field_read_has_no_cell_dependency(self):
        self.assertEqual(builder.field_text(EmptyTextDAT()), '')
        self.assertEqual(builder.field_text(EmptyTextDAT(' 120 ')), '120')
        with self.assertRaises(ValueError):
            builder.field_text(None)


if __name__ == '__main__':
    unittest.main()
