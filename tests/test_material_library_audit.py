"""Permanent offline acceptance of sequential material audit safety/evidence."""
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from tools import audit_material_library as audit
from pixelblaze_mapper.material_library import build_catalog, write_catalog, import_material


def good_probe():
    return dict(errors=[], info='Compiled successfully', temporal_mean_abs_delta=[0., 0.],
                samples=[dict(time=t, shape=[64, 96, 4], finite=True, nonfinite_count=0,
                              rgb_min=0., rgb_max=1., rgb_mean=.5, rgb_variance=.1,
                              spatial_variance=.1, alpha_min=1., alpha_max=1., alpha_mean=1.)
                         for t in audit.TIMES])


class ClassificationTests(unittest.TestCase):
    def test_static_nonuniform_image_passes_and_is_not_a_compile_failure(self):
        self.assertEqual(audit.classify_probe(good_probe()), ('passed', []))

    def test_nonfinite_blank_uniform_and_transparent_are_review_not_failures(self):
        changes = (dict(finite=False, nonfinite_count=1), dict(rgb_min=0., rgb_max=0.),
                   dict(spatial_variance=0.), dict(alpha_max=0.))
        for change in changes:
            with self.subTest(change=change):
                probe = good_probe()
                probe['samples'][0].update(change)
                status, reasons = audit.classify_probe(probe)
                self.assertEqual(status, 'review')
                self.assertTrue(reasons)

    def test_compile_and_missing_readback_are_distinct_failures(self):
        self.assertEqual(audit.classify_probe(dict(errors=['GPU compile failed']))[0], 'compile_error')
        self.assertEqual(audit.classify_probe(dict(info='ERROR: line 7'))[0], 'compile_error')
        self.assertEqual(audit.classify_probe(dict(exception='No image'))[0], 'probe_error')
        self.assertEqual(audit.classify_probe(dict(errors=[], samples=[]))[0], 'probe_error')

    def test_resume_fingerprint_status_retry_and_interrupted_gpu(self):
        self.assertFalse(audit.should_run(dict(status='passed', fingerprint='same'), 'same', True))
        self.assertTrue(audit.should_run(dict(status='passed', fingerprint='old'), 'new', True))
        self.assertTrue(audit.should_run(dict(status='review', fingerprint='same'), 'same', True, ['review']))
        self.assertFalse(audit.should_run(dict(status='in_progress', fingerprint='old'), 'new', True))
        self.assertTrue(audit.should_run(dict(status='in_progress'), 'new', True, ['in_progress']))
        interrupted = dict(status='probe_error', fingerprint='old', interrupted_gpu=True)
        self.assertFalse(audit.should_run(interrupted, 'changed-runtime', True))
        self.assertFalse(audit.should_run(interrupted, 'changed-runtime', True, ['compile_error']))
        self.assertTrue(audit.should_run(interrupted, 'changed-runtime', True, ['probe_error']))


class AuditTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base/'source'
        self.source.mkdir()
        for name in ('First', 'Second'):
            folder = self.source/name
            folder.mkdir()
            (folder/(name+'.fs')).write_text('''/*{"INPUTS":[{"NAME":"gain","TYPE":"float","DEFAULT":0.5}]}*/
vec4 materialColorForPixel(vec2 uv) { return vec4(uv * gain, 0.5, 1.); }
''', encoding='utf-8')
        self.catalog = build_catalog(self.source, source_id='audit-fixture', source_label='Audit fixture')
        self.catalog_path = self.base/'catalog.json'
        write_catalog(self.catalog, self.catalog_path)
        self.output = self.base/'results'
        self.imports = self.base/'imports'

    def run_audit(self, **kwargs):
        with redirect_stdout(StringIO()):
            return audit.run_audit(self.catalog_path, self.output, self.imports, **kwargs)

    def test_offline_import_and_adaptation_without_any_td_call(self):
        execute = Mock(side_effect=AssertionError('Offline audit must never contact TD'))
        result = self.run_audit(offline_only=True, execute=execute)
        self.assertEqual(result['counts'], {'offline_adapted': 2})
        execute.assert_not_called()
        for item in result['results']:
            self.assertEqual(item['import']['status'], 'imported')
            self.assertTrue(Path(item['import']['path']).is_file())
            self.assertEqual(len(item['source_sha256']), 64)
            self.assertEqual(len(item['adaptation']['shader_sha256']), 64)
        self.assertFalse((self.output/'results.json.tmp').exists())

    def test_managed_modified_import_is_preserved_and_not_gpu_probed(self):
        item = self.catalog.materials[0]
        imported = import_material(self.catalog, item.id, self.imports)
        modified = 'intentional user modifications: preserve exactly'
        imported.source_path.write_text(modified, encoding='utf-8')
        execute = Mock(side_effect=AssertionError('Conflict must not be GPU-probed'))
        result = self.run_audit(ids=[item.id], execute=execute)
        self.assertEqual(result['counts'], {'import_conflict': 1})
        self.assertEqual(imported.source_path.read_text(encoding='utf-8'), modified)
        self.assertEqual(result['results'][0]['import']['status'], 'conflict')
        execute.assert_not_called()

    def test_catalog_quarantine_and_twisted_tunnel_never_gpu_even_with_retry(self):
        first, second = self.catalog.materials
        first = replace(first, metadata=dict(first.metadata, _TD_VALIDATION={'status':'quarantined','reason':'GPU hazard'}))
        second = replace(second, name='Twisted Tunnel')
        catalog = replace(self.catalog, materials=(first, second))
        write_catalog(catalog, self.catalog_path)
        execute = Mock(side_effect=AssertionError('Quarantine must never contact TD'))
        result = self.run_audit(execute=execute)
        self.assertEqual(result['counts'], {'quarantined': 2})
        self.assertTrue(all('adaptation' in item for item in result['results']))
        self.assertTrue(all(Path(item['import']['path']).exists() for item in result['results']))
        retried = self.run_audit(resume=True, retry=['quarantined'], execute=execute)
        self.assertEqual(retried['counts'], {'quarantined': 2})
        execute.assert_not_called()

    def test_gpu_marker_is_on_disk_before_call_and_cleanup_is_owned(self):
        observed = []
        def execute(script):
            if "owner.destroy()" in script:
                self.assertIn("owner.fetch('material_audit_owner',None)==", script)
                self.assertNotIn('/project1/madmapper', script)
                observed.append('cleanup')
                return {}
            journal = json.loads((self.output/'results.json').read_text(encoding='utf-8'))
            in_progress = [r for r in journal['results'] if r['status'] == 'in_progress']
            self.assertEqual(len(in_progress), 1)
            observed.append(in_progress[0]['id'])
            self.assertIn("preview.par.format='rgba32float'", script)
            self.assertIn('preview.numpyArray(delayed=False)', script)
            self.assertIn('bind_textures(preview', script)
            self.assertIn('preview.par.vec0valuex=phase', script)
            self.assertNotIn('activate_selected', script)
            return good_probe()
        result = self.run_audit(execute=execute)
        self.assertEqual(result['counts'], {'passed': 2})
        self.assertEqual(observed, [item.id for item in self.catalog.materials]+['cleanup'])
        self.assertTrue(all(r['no_temporal_change'] for r in result['results']))

    def test_resume_retains_success_and_retries_only_requested_review(self):
        count = 0
        def execute(script):
            nonlocal count
            if 'owner.destroy()' in script:
                return {}
            count += 1
            result = good_probe()
            if count == 1:
                result['samples'][0]['spatial_variance'] = 0
            return result
        result = self.run_audit(execute=execute)
        self.assertEqual(result['counts'], {'review': 1, 'passed': 1})
        never = Mock(side_effect=AssertionError('Completed results must resume without GPU calls'))
        self.run_audit(resume=True, execute=never)
        never.assert_not_called()
        result = self.run_audit(resume=True, retry=['review'], execute=execute)
        self.assertEqual(result['counts'], {'passed': 2})
        self.assertEqual(count, 3)

    def test_offline_results_advance_to_gpu_and_transport_failure_stops_sequence(self):
        self.run_audit(offline_only=True)
        calls = []
        def execute(script):
            calls.append(script)
            if 'owner.destroy()' not in script:
                raise TimeoutError('simulated GPU/REST interruption')
            return {}
        result = self.run_audit(resume=True, execute=execute)
        self.assertTrue(result['transport_failed'])
        self.assertEqual(result['counts'], {'probe_error': 1, 'offline_adapted': 1})
        self.assertEqual(len(calls), 2)  # One GPU submission, one owned cleanup.
        failed = next(r for r in result['results'] if r['status'] == 'probe_error')
        self.assertTrue(failed['interrupted_gpu'])
        self.assertEqual(failed['phase'], 'gpu')

    def test_gpu_script_and_cleanup_parse_without_touchdesigner(self):
        captured = []
        probe = audit.GPUProbe(self.output, execute=lambda script: captured.append(script) or good_probe())
        item = self.catalog.materials[0]
        record, adaptation = audit.prepare(self.catalog, item, self.imports, 'adapter-hash')
        probe.run(item, adaptation)
        probe.close()
        for script in captured:
            compile(script, '<td-audit>', 'exec')
        bindings = json.loads((self.output/'probe-work/bindings.json').read_text())
        self.assertEqual(len(bindings['values']), 1)
        self.assertTrue(all(len(v) == 4 for v in bindings['values'].values()))

    def test_all_cube_faces_and_runtime_changes_invalidate_previous_success(self):
        item = self.catalog.materials[0]
        paths = []
        for index in range(6):
            path = self.base/('cube-face-%d.png' % index)
            path.write_bytes(('face-%d' % index).encode())
            paths.append(str(path))
        adaptation = audit.adapter.adapt_material(item.source_path)
        adaptation = replace(adaptation, textures=({'TYPE':'cube', 'resolved_path':paths[0], 'resolved_paths':paths},))
        with patch.object(audit.adapter, 'adapt_material', return_value=adaptation):
            first, _ = audit.prepare(self.catalog, item, self.imports, 'adapter', {'probe':'old', 'binder':'old'})
            texture = first['adaptation']['textures'][0]
            self.assertEqual([entry['path'] for entry in texture['files']], paths)
            self.assertEqual(len({entry['sha256'] for entry in texture['files']}), 6)
            Path(paths[-1]).write_bytes(b'changed-negative-Z')
            changed_face, _ = audit.prepare(self.catalog, item, self.imports, 'adapter', {'probe':'old', 'binder':'old'})
            self.assertNotEqual(first['fingerprint'], changed_face['fingerprint'])
            self.assertEqual(texture['sha256'], changed_face['adaptation']['textures'][0]['sha256'])
            changed_probe, _ = audit.prepare(self.catalog, item, self.imports, 'adapter', {'probe':'new', 'binder':'old'})
            changed_binder, _ = audit.prepare(self.catalog, item, self.imports, 'adapter', {'probe':'old', 'binder':'new'})
            self.assertNotEqual(changed_face['fingerprint'], changed_probe['fingerprint'])
            self.assertNotEqual(changed_face['fingerprint'], changed_binder['fingerprint'])

    def test_provenance_records_probe_harness_texture_and_parameter_code_hashes(self):
        result = self.run_audit(offline_only=True)
        for key in ('probe_script_sha256', 'audit_harness_sha256', 'texture_runtime_sha256', 'parameter_runtime_sha256'):
            self.assertEqual(len(result['provenance'][key]), 64)


if __name__ == '__main__':
    unittest.main()
