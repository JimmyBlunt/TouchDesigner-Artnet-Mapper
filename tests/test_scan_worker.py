"""Behavioral offline safety tests; no native dependency imports or hardware."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pixelblaze_mapper.scan_session import ScanSession, ScanTarget, ScanSessionError
from pixelblaze_mapper.scan_worker import (create_manifest, load_observations, reconstruct,
                                          main, validate_manifest, CAMERA_MODELS)
from pixelblaze_mapper.build_scan_session_ui import attach_existing_views, parse_indices, select_scope, _runtime_source, worker_command


class ScanWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root / ('view-%d.csv' % i) for i in range(2)]
        for path in self.paths:
            path.write_text('index,u,v\n10,0.2,0.3\n42,0.4,0.5\n99,0.6,0.7\n', encoding='utf-8')
        self.state = ScanSession('s', 'scene', 'revision',
            (ScanTarget('a', 'obj', 0, 10), ScanTarget('b', 'obj', 1, 42), ScanTarget('anchor', 'obj', 2, 99)),
            ('a', 'b'), ('anchor',))
        self.ready, self.views = attach_existing_views(self.state, self.paths)

    def manifest(self):
        return create_manifest(self.ready, views=self.views, source_roots=[self.root],
            workspace_root=self.root, output_directory=self.root / 'new-result')

    def test_sparse_ids_preserved_and_no_output(self):
        doc, rows = load_observations(self.manifest())
        self.assertEqual([row[0] for row in rows], [10, 42, 99, 10, 42, 99])
        self.assertFalse((self.root / 'new-result').exists())
        self.assertFalse(doc['capabilities']['camera_capture'])

    def test_changed_input_rejected(self):
        doc = self.manifest()
        self.paths[0].write_text('index,u,v\n10,0,0\n', encoding='utf-8')
        with self.assertRaisesRegex(ScanSessionError, 'changed'):
            load_observations(doc)

    def test_existing_or_outside_output_rejected(self):
        for path in (self.root, self.root.parent / 'outside', self.paths[0], self.root / 'absent-parent' / 'child'):
            with self.subTest(path=path), self.assertRaises(ScanSessionError):
                create_manifest(self.ready, views=self.views, source_roots=[self.root],
                    workspace_root=self.root, output_directory=path)

    def test_scope_and_coordinates_rejected(self):
        for line in ('111,0.2,0.3', '10,nan,0.3', '10,0,0,extra', '10,0', '10,0,0\n10,1,1'):
            with self.subTest(line=line):
                self.paths[0].write_text('index,u,v\n' + line + '\n', encoding='utf-8')
                with self.assertRaises(ScanSessionError):
                    load_observations(self.manifest())

    def test_view_evidence_must_match_actual_detections(self):
        self.paths[0].write_text('index,u,v\n10,0,0\n', encoding='utf-8')
        with self.assertRaisesRegex(ScanSessionError, 'evidence'):
            load_observations(self.manifest())

    def test_duplicate_view_and_unreviewed_revision_rejected(self):
        for mutate in (lambda doc: doc['inputs'].append(doc['inputs'][0]),
                       lambda doc: doc.update(upstream_revision='different')):
            doc = deepcopy(self.manifest())
            mutate(doc)
            with self.assertRaises(ScanSessionError):
                load_observations(doc)

    def test_unconfirmed_reconstruction_never_imports_native_modules(self):
        with patch('builtins.__import__') as imports:
            with self.assertRaises(ScanSessionError):
                reconstruct({}, confirmed=False)
            imports.assert_not_called()

    def test_default_cli_dry_run_no_native_reconstruction(self):
        path = self.root / 'manifest.json'
        path.write_text(json.dumps(self.manifest()), encoding='utf-8')
        with patch('pixelblaze_mapper.scan_worker.reconstruct') as native, patch('builtins.print') as output:
            main([str(path)])
            native.assert_not_called()
            self.assertTrue(json.loads(output.call_args.args[0])['dry_run'])

    def test_native_integer_ids_are_serializable_in_success_report(self):
        # Model NumPy's int64 without importing NumPy/native dependencies here.
        class NativeIndex:
            def __int__(self):
                return 10
            def __hash__(self):
                return hash(10)
            def __eq__(self, other):
                return int(self) == other
        point = SimpleNamespace(led_id=NativeIndex(), point=SimpleNamespace(position=(1., 2., 3.)))
        native = {
            'marimapper.led': SimpleNamespace(LED2D=lambda *args: args, Point2D=lambda *args: args),
            'marimapper.sfm': SimpleNamespace(sfm=lambda rows, **kwargs: [point]),
            'marimapper.database_populator': SimpleNamespace(camera_models=[
                SimpleNamespace(__name__='camera_model_radial')]),
            'marimapper.file_tools': SimpleNamespace(write_3d_leds_to_file=lambda points, path:
                path.write_text('index,x,y,z,xn,yn,zn,error\n10,1,2,3,0,0,0,0\n')),
        }
        doc = self.manifest()
        origin = json.dumps({'vcs_info': {'commit_id': doc['upstream_revision']}})
        with patch.dict('sys.modules', native), \
             patch('importlib.metadata.version', side_effect=lambda name: '3.4.2' if name == 'marimapper' else '3.11.1'), \
             patch('importlib.metadata.distribution', return_value=SimpleNamespace(read_text=lambda name: origin)):
            report = reconstruct(doc, confirmed=True)
        self.assertEqual(report['reconstructed_ids'], [10])
        self.assertIs(type(report['reconstructed_ids'][0]), int)
        saved = json.loads((self.root / 'new-result/quality_pending.json').read_text())
        self.assertEqual(saved['reconstructed_ids'], [10])
        self.assertFalse(saved['hardware_output_used'])

    def test_camera_model_manifest_and_legacy_default(self):
        doc = self.manifest()
        self.assertEqual(doc['reconstruction'], dict(camera_model='camera_model_radial', interpolation=False))
        del doc['reconstruction']
        self.assertEqual(validate_manifest(doc)['reconstruction']['camera_model'], 'camera_model_radial')
        for name in CAMERA_MODELS:
            selected = create_manifest(self.ready, views=self.views, source_roots=[self.root],
                workspace_root=self.root, output_directory=self.root / 'result', camera_model=name)
            self.assertEqual(validate_manifest(selected)['reconstruction']['camera_model'], name)
            self.assertFalse((self.root / 'result').exists())

    def test_unknown_model_and_interpolation_fail_closed(self):
        for options in ({'camera_model': 'opencv'}, {'camera_model': None},
                        {'interpolation': True}, {'interpolation': 0},
                        {'interpolation_max_fill': 3, 'interpolation_max_error': .15}, []):
            with self.subTest(options=options), self.assertRaises(ScanSessionError):
                doc = self.manifest()
                doc['reconstruction'] = options
                validate_manifest(doc)

    def test_selected_native_camera_model_is_forwarded_and_reported(self):
        from unittest.mock import Mock
        point = SimpleNamespace(led_id=10, point=SimpleNamespace(position=(-1., 2., -3.)))
        # Distinct sentinels prove the selected function object reaches native sfm.
        models = [SimpleNamespace(__name__=name) for name in CAMERA_MODELS]
        native_sfm = Mock(return_value=[point])
        native = {
            'marimapper.led': SimpleNamespace(LED2D=lambda *args: args, Point2D=lambda *args: args),
            'marimapper.sfm': SimpleNamespace(sfm=native_sfm),
            'marimapper.database_populator': SimpleNamespace(camera_models=models),
            'marimapper.file_tools': SimpleNamespace(write_3d_leds_to_file=Mock()),
        }
        for name in CAMERA_MODELS:
            with self.subTest(name=name):
                doc = create_manifest(self.ready, views=self.views, source_roots=[self.root],
                    workspace_root=self.root, output_directory=self.root / name, camera_model=name)
                origin = json.dumps({'vcs_info': {'commit_id': doc['upstream_revision']}})
                with patch.dict('sys.modules', native), \
                     patch('importlib.metadata.version', side_effect=lambda package: '3.4.2' if package == 'marimapper' else '3.11.1'), \
                     patch('importlib.metadata.distribution', return_value=SimpleNamespace(read_text=lambda _: origin)):
                    report = reconstruct(doc, confirmed=True)
                self.assertIs(native_sfm.call_args.kwargs['camera_model'],
                              next(model for model in models if model.__name__ == name))
                self.assertEqual(report['camera_model'], name)
                self.assertEqual(report['interpolated_ids'], [])
                self.assertFalse(report['interpolation'])
                self.assertEqual(point.point.position, (-1., 2., -3.))
                self.assertEqual(json.loads((self.root / name / 'quality_pending.json').read_text())['camera_model'], name)

    def test_distinct_actual_views_required(self):
        with self.assertRaises(ScanSessionError):
            attach_existing_views(self.state, [self.paths[0], self.paths[0]])

    def test_explicit_scope_and_anchor_selection(self):
        selected = select_scope(self.state, '42', '10,99')
        self.assertEqual(selected.selected_ids, ('b',))
        self.assertEqual(selected.anchor_ids, ('a', 'anchor'))
        self.assertEqual(parse_indices('10-12, 42'), (10, 11, 12, 42))
        for value in ('', '-1', '12-10', '10,10', 'nan', '0-100001'):
            with self.subTest(value=value), self.assertRaises(ScanSessionError):
                parse_indices(value)
        with self.assertRaises(ScanSessionError):
            select_scope(self.state, '999')

    def test_generated_runtime_compiles_but_is_not_real_mouse_proof(self):
        compile(_runtime_source(), '<guided runtime>', 'exec')
        self.assertNotIn('subprocess', _runtime_source())
        self.assertNotIn('VideoCapture', _runtime_source())

    def test_worker_command_is_data_only_and_requires_boolean_confirmation(self):
        python = self.root / 'python.exe'
        python.write_bytes(b'test fixture, never executed')
        manifest = self.root / 'manifest.json'
        manifest.write_text('{}', encoding='utf-8')
        self.assertNotIn('--confirm-offline-reconstruction', worker_command(python, manifest))
        self.assertIn('--confirm-offline-reconstruction', worker_command(python, manifest, confirm=True))
        with self.assertRaises(ScanSessionError):
            worker_command(python, manifest, confirm='yes')


if __name__ == '__main__':
    unittest.main()
