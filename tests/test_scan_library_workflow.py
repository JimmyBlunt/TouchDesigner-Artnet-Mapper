"""Library selection, provenance, resume and cached preview without hardware."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import scan_library as library
from pixelblaze_mapper import scan_library_ui as ui_module
from pixelblaze_mapper.scan_capture import prepare_capture
from pixelblaze_mapper.scan_routing import create_snapshot
from pixelblaze_mapper.scan_session import ScanSession, ScanSessionError
from pixelblaze_mapper.standalone_scan import routing, session


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.settings = {'name': 'Panel', 'target': '192.0.2.20', 'interface': '192.0.2.10',
                         'universe': 120, 'count': 4, 'rate': 30, 'order': 'RGB'}
        self.session = session(self.settings)

    def capture(self, name, observed=(0, 2), state=None):
        state = state or self.session
        snapshot = create_snapshot(routing(self.settings), (0, 1, 2, 3), brightness_cap=.05)
        plan = prepare_capture(snapshot, {'device': 0, 'exposure': -10, 'threshold': 160}, self.root,
                               identity={str(t.source_index): t.led_id for t in state.targets},
                               scene_revision=state.scene_revision)
        directory = self.root / name
        directory.mkdir()
        (directory/'capture.json').write_text(json.dumps(plan), encoding='utf-8')
        (directory/'result.json').write_text(json.dumps({'state': 'complete'}), encoding='utf-8')
        path = directory/'view.csv'
        path.write_text('index,u,v\n' + ''.join('%d,0.2,0.8\n' % i for i in observed), encoding='utf-8')
        return path

    def test_index_search_kinds_depth_and_entry_bounds(self):
        self.capture('capture-one')
        deep = self.root/'project'/'job'
        deep.mkdir(parents=True)
        (deep/'candidate_3d.csv').write_text('index,x,y,z\n0,1,2,3\n')
        (deep/'too-deep').mkdir()
        (deep/'too-deep'/'hidden.csv').write_text('index,u,v\n0,0.1,0.2\n')
        index = library.library_index(self.root)
        self.assertEqual(len(index['items']), 2)
        self.assertEqual(len(library.filter_items(index, 'project 3D')), 1)
        self.assertEqual(len(library.filter_items(index, kind='2D view')), 1)
        bounded = library.library_index(self.root, max_entries=1)
        self.assertTrue(bounded['truncated'])
        self.assertEqual(bounded['examined'], 1)

    def test_index_reads_headers_without_parsing_csv_bodies(self):
        path = self.root/'broken.csv'
        path.write_text('index,u,v\nnot-a-point\n')
        self.assertEqual(len(library.library_index(self.root)['items']), 1)
        with self.assertRaises((ValueError, ScanSessionError)):
            library.inspect_preview(path)

    def test_preview_retains_sparse_zero_coordinates_and_bounds_without_filling(self):
        path = self.root/'map.csv'
        path.write_text('index,x,y,z\n0,0,0,0\n17,-2,3,4\n')
        data = library.inspect_preview(path, max_points=1)
        self.assertEqual(data['ids'], [0, 17])
        self.assertEqual(data['count'], 2)
        self.assertTrue(data['sampled'])
        self.assertEqual(data['bounds_min'], [-2, 0, 0])
        self.assertEqual(data['bounds_max'], [0, 3, 4])
        self.assertEqual(data['points'][0], (0, 0, 0, 0))

    def test_preview_rejects_duplicate_ids_and_nonfinite_or_outside_uv(self):
        path = self.root/'bad.csv'
        for rows in ('0,0.1,0.2\n0,0.2,0.3\n', '0,nan,0.2\n', '0,1.1,0.2\n'):
            path.write_text('index,u,v\n' + rows)
            with self.subTest(rows=rows), self.assertRaises(ScanSessionError):
                library.inspect_preview(path)

    def test_attachment_rejects_same_numeric_ids_from_different_acquisition(self):
        first = self.capture('capture-first')
        other = self.capture('capture-other', state=session(self.settings))
        self.assertEqual(library.verified_view_paths([first, first], self.session), [str(first)])
        with self.assertRaisesRegex(ScanSessionError, 'another acquisition'):
            library.verified_view_paths([first, other], self.session)

    def test_legacy_and_incomplete_capture_cannot_be_silently_attached(self):
        path = self.capture('capture-first')
        (path.parent/'result.json').write_text('{"state":"failed"}')
        with self.assertRaises(ScanSessionError):
            library.verified_view_paths([path], self.session)
        (path.parent/'capture.json').unlink()
        with self.assertRaises(OSError):
            library.verified_view_paths([path], self.session)

    def test_resume_uses_original_namespace_not_new_uuid(self):
        path = self.capture('capture-first')
        resumed = library.resume_acquisition(path)
        state = ScanSession.from_dict(resumed['session'])
        self.assertEqual(state, self.session)
        self.assertEqual(resumed['settings'], self.settings)
        self.assertEqual(resumed['workspace'], str(self.root))
        self.assertEqual(library.verified_view_paths([path], state), [str(path)])

    def test_resume_rejects_changed_settings_revision_or_mixed_identity(self):
        path = self.capture('capture-first')
        file = path.parent/'capture.json'
        original = json.loads(file.read_text())
        bad = dict(original, scene_revision='bad')
        file.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ScanSessionError, 'settings'):
            library.resume_acquisition(path)
        original['identity']['1'] = 'foreign:led:1'
        file.write_text(json.dumps(original))
        with self.assertRaisesRegex(ScanSessionError, 'mixes'):
            library.resume_acquisition(path)

    def test_resume_relocated_copy_preserves_original_manifest_bytes(self):
        path = self.capture('capture-first')
        manifest = path.parent/'capture.json'
        data = json.loads(manifest.read_text())
        data['workspace'] = 'X:/historical/missing/location'
        manifest.write_text(json.dumps(data))
        before = manifest.read_bytes()
        resumed = library.resume_acquisition(path)
        self.assertEqual(resumed['workspace'], str(self.root))
        self.assertEqual(resumed['session']['session_id'], self.session.session_id)
        self.assertEqual(manifest.read_bytes(), before)

    def test_weak_missing_new_scope_preserves_id_namespace_and_original_files(self):
        path = self.capture('capture-first')
        original = path.read_bytes()
        state, counts = library.coverage_selection(self.session, [path], 'missing')
        self.assertEqual(state.selected_ids, (self.session.targets[1].led_id, self.session.targets[3].led_id))
        self.assertEqual(state.session_id, self.session.session_id)
        self.assertEqual(state.views, ())
        self.assertEqual(counts['missing'], [1, 3])
        weak, _ = library.coverage_selection(self.session, [path], 'weak')
        self.assertEqual(weak.selected_ids, self.session.selected_ids)
        self.assertEqual(path.read_bytes(), original)

    def test_full_coverage_missing_filter_leaves_selection_unchanged(self):
        path = self.capture('capture-first', observed=(0, 1, 2, 3))
        with self.assertRaisesRegex(ScanSessionError, 'No LEDs'):
            library.coverage_selection(self.session, [path], 'missing')

    def test_cached_preview_reads_once_and_changes_when_file_changes(self):
        path = self.capture('capture-first')
        ui_module._previews.clear()
        with patch.object(library, 'inspect_preview', wraps=library.inspect_preview) as inspect:
            first = ui_module.cached_preview(path)
            self.assertIs(ui_module.cached_preview(path), first)
            self.assertEqual(inspect.call_count, 1)
            path.write_text(path.read_text()+'3,0.3,0.4\n')
            self.assertEqual(ui_module.cached_preview(path)['count'], 3)
            self.assertEqual(inspect.call_count, 2)

    def test_preview_pixels_are_finite_and_orbit_changes_3d_view(self):
        import numpy as np
        path = self.root/'map.csv'
        path.write_text('index,x,y,z\n0,0,0,0\n1,1,2,3\n2,2,0,-1\n')
        preview = library.inspect_preview(path)
        first = ui_module.preview_image(preview, 0)
        second = ui_module.preview_image(preview, 90)
        self.assertEqual(first.shape, (265, 610, 4))
        self.assertTrue(np.isfinite(first).all())
        self.assertFalse(np.array_equal(first, second))


class Owner:
    path = '/project1/guided_scan'

    def __init__(self):
        self.storage = {}
        self.nodes = {}
        for name in ('source_ids', 'anchors', 'views', 'workspace', 'camera', 'exposure', 'threshold', 'brightness'):
            self.nodes['ui_panel/'+name+'/string'] = SimpleNamespace(text='')
        for name in ('name', 'target', 'interface', 'universe', 'count', 'rate', 'order'):
            self.nodes['new_capture_panel/'+name+'/string'] = SimpleNamespace(text='')
        for name in ('query', 'folder'):
            self.nodes['library_panel/'+name+'/string'] = SimpleNamespace(text='')
        for name in ('status', 'list_status'):
            self.nodes['library_panel/'+name] = SimpleNamespace(par=SimpleNamespace(text=''))
        self.nodes['library_panel'] = SimpleNamespace(openViewer=Mock())
        self.runtime = SimpleNamespace(_require_idle=Mock(), _set_views=Mock(), _status=Mock())
        self.nodes['runtime'] = SimpleNamespace(module=self.runtime)

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def store(self, key, value):
        self.storage[key] = value

    def op(self, path):
        return self.nodes.get(path)


class LibraryUIBehaviorTests(unittest.TestCase):
    setUp = LibraryTests.setUp
    capture = LibraryTests.capture

    def test_readable_button_roles_and_selection_affordances_use_native_parameters(self):
        owner = Owner()
        names = ['row_0'] + ['btn_' + name for name in
            ('attach', 'resume', 'review', 'clear', 'previous', 'next', 'all', 'views', 'results')]
        for name in names:
            owner.nodes['library_panel/' + name] = SimpleNamespace(par=SimpleNamespace(
                colorr=.5, colorg=.5, colorb=.5, bgcolorr=.5, bgcolorg=.5, bgcolorb=.5,
                enable=True, display=True, label='', opacity=.5, dodisablecolor=True))
        owner.store('scan_library_index', {'items': [{'path': 'view.csv', 'kind': '2D view', 'name': 'view.csv'}]})
        ui_module.render(owner)
        self.assertFalse(owner.op('library_panel/btn_attach').par.enable)
        self.assertFalse(owner.op('library_panel/btn_previous').par.enable)
        owner.store('scan_library_selected', ['view.csv'])
        owner.store('session', {'stage': 'planned'})
        ui_module.render(owner)
        row = owner.op('library_panel/row_0').par
        self.assertEqual((row.bgcolorr, row.bgcolorg, row.bgcolorb), ui_module.BUTTON_COLORS['selected'])
        self.assertEqual((row.colorr, row.colorg, row.colorb), ui_module.BUTTON_COLORS['selected'])
        self.assertTrue(owner.op('library_panel/btn_attach').par.enable)
        self.assertTrue(owner.op('library_panel/btn_resume').par.enable)
        self.assertFalse(owner.op('library_panel/btn_review').par.enable)

    def test_friendly_name_keeps_context_and_short_identity_without_modifying_source(self):
        item = {'name': 'Rear_Panel/capture-01234567-89ab-cdef-0123-456789abcdef/view.csv',
                'kind': '2D view'}
        before = dict(item)
        self.assertEqual(ui_module.friendly_name(item), 'Rear Panel / View 01234567')
        self.assertEqual(item, before)

    def test_caption_overlay_passes_clicks_and_tracks_changed_row_labels(self):
        caption = SimpleNamespace(par=SimpleNamespace(text='', x=0, y=0, hmode='fixed', vmode='fixed',
            alignx='left', aligny='center', type='multiline', wordwrap=False, font='Verdana', fontsize=12,
            fontalpha=1, bgalpha=1, opacity=1, layer=0, display=True, clickthrough=False,
            fontcolorr=.5, fontcolorg=.5, fontcolorb=.5))
        storage = {}
        button = SimpleNamespace(par=SimpleNamespace(label='First row', colorr=.5, colorg=.5, colorb=.5),
            create=Mock(), op=lambda path: caption, fetch=lambda key, default=None: storage.get(key, default),
            store=lambda key, value: storage.update({key: value}))
        ui_module.style_button(button, 'selected')
        self.assertEqual(caption.par.text, 'First row')
        self.assertTrue(caption.par.clickthrough)
        self.assertEqual((caption.par.hmode, caption.par.vmode), ('fill', 'fill'))
        self.assertEqual(caption.par.bgalpha, 0)
        self.assertEqual(caption.par.fontcolorr, .96)
        self.assertEqual(button.par.label, '')
        ui_module.style_button(button)
        self.assertEqual(caption.par.text, 'First row')
        button.par.label = '[x] Different row'
        ui_module.style_button(button, 'selected')
        self.assertEqual(caption.par.text, '[x] Different row')
    def test_attach_action_uses_only_explicit_selected_paths(self):
        one, two = self.capture('capture-one'), self.capture('capture-two')
        owner = Owner()
        owner.store('session', self.session.to_dict())
        owner.store('scan_library_index', library.library_index(self.root))
        owner.store('scan_library_selected', [str(two)])
        owner.nodes['ui_panel/source_ids/string'].text = '0-3'
        with patch('pixelblaze_mapper.scan_workflow_ux.refresh'):
            self.assertTrue(ui_module.act(lambda path: owner, Mock(), 'attach'))
        owner.runtime._set_views.assert_called_once_with([str(two)])

    def test_no_selection_does_not_attach_all_matches(self):
        self.capture('capture-one')
        owner = Owner()
        owner.store('session', self.session.to_dict())
        owner.store('scan_library_index', library.library_index(self.root))
        owner.nodes['ui_panel/source_ids/string'].text = '0-3'
        self.assertFalse(ui_module.act(lambda path: owner, Mock(), 'attach'))
        owner.runtime._set_views.assert_not_called()

    def test_render_never_discovers_or_reads_files(self):
        owner = Owner()
        owner.store('scan_library_index', {'items': [{'path': 'gone.csv', 'kind': '2D view', 'name': 'Gone'}]})
        with (patch.object(library, 'library_index', side_effect=AssertionError('disk')),
              patch.object(library, 'inspect_preview', side_effect=AssertionError('disk'))):
            ui_module.render(owner)
        self.assertEqual(len(owner.fetch('scan_library_visible')), 1)

    def test_restored_state_invalidates_plans_but_not_files(self):
        path = self.capture('capture-first')
        payload = library.resume_acquisition(path)
        owner = Owner()
        owner.store('manifest', 'previous.json')
        owner.store('capture_plan', {'old': True})
        owner.nodes['ui_panel/views/string'].text = 'old.csv'
        ui_module.stage_restored(owner, payload)
        self.assertEqual(owner.fetch('session')['session_id'], self.session.session_id)
        self.assertIsNone(owner.fetch('manifest'))
        self.assertIsNone(owner.fetch('capture_plan'))
        self.assertEqual(owner.nodes['ui_panel/views/string'].text, '')
        self.assertTrue(path.exists())

    def test_missing_resume_widget_leaves_existing_fields_and_state_intact(self):
        path = self.capture('capture-first')
        owner = Owner()
        del owner.nodes['new_capture_panel/rate/string']
        owner.nodes['ui_panel/source_ids/string'].text = 'old scope'
        owner.store('session', {'old': True})
        with self.assertRaises(ScanSessionError):
            ui_module.stage_restored(owner, library.resume_acquisition(path))
        self.assertEqual(owner.fetch('session'), {'old': True})
        self.assertEqual(owner.nodes['ui_panel/source_ids/string'].text, 'old scope')


if __name__ == '__main__':
    unittest.main()
