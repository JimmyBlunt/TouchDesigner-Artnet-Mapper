"""Offline publication acceptance using temporary packages, never the real catalog."""
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import publish_material_audit as publish
from pixelblaze_mapper.material_library import MaterialCatalog, MaterialRecord, Compatibility, write_catalog


class PublishAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'original.fs'
        self.source.write_text('/*{}*/\nvec4 materialColorForPixel(vec2 p){return vec4(p,0.,1.);}', encoding='utf-8')
        self.material_id = 'mat_'+'a'*20
        self.item = MaterialRecord(self.material_id, 'Test Material', 'original.fs', str(self.source),
                                   'isf', (), (), Compatibility.UNSUPPORTED, (), {})
        self.catalog = MaterialCatalog('test', 'Test', str(self.root), (self.item,))
        self.catalog_path, self.results_path = self.root/'catalog.json', self.root/'results.json'
        self.import_root = self.root/'imported'
        self.package = self.import_root/self.material_id
        self.package.mkdir(parents=True)
        (self.package/'original.fs').write_bytes(self.source.read_bytes())
        self.source_hash = publish.audit.sha256_file(self.source)
        self.manifest = {'material_id':self.material_id, 'source_sha256':self.source_hash,
                         'imported_file':'original.fs', 'imported_files':{'original.fs':self.source_hash}}
        (self.package/'material-import.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        self.adaptation = SimpleNamespace(status='adaptable', adaptable=True, reasons=(), warnings=(),
                                          shader='// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 6\nvoid main(){}',
                                          textures=(), schema=(), metadata={})
        self.runtime = {'probe_script_sha256':'runtime-test'}
        for patcher in (patch.object(publish, 'EXPECTED_COUNT', 1),
                        patch.object(publish.adapter, 'adapt_material', side_effect=lambda *a, **k:self.adaptation),
                        patch.object(publish.audit, 'runtime_fingerprints', return_value=self.runtime)):
            patcher.start()
            self.addCleanup(patcher.stop)
        write_catalog(self.catalog, self.catalog_path)
        self.record = {'id':self.material_id, 'name':self.item.name, 'source_path':str(self.source),
                       'source_sha256':self.source_hash, 'status':'passed', 'completed_at':'2026-10-13T00:00:00Z',
                       'import':{'status':'existing'}, 'reasons':[],
                       'probe':{'errors':[], 'samples':[{'time':t, 'shape':[64,96,4], 'finite':True,
                                 'nonfinite_count':0, 'rgb_min':0.1, 'rgb_max':1.0, 'spatial_variance':0.2,
                                 'alpha_max':1.0} for t in (0.,1.,2.)]}}
        self.refresh_fingerprint()

    def refresh_fingerprint(self):
        _, fresh = publish._fresh_adaptation(self.catalog, self.item, {})
        self.record['adaptation'] = fresh
        raw = dict(source=self.record['source_sha256'], adaptation=fresh,
                   adapter_hash=publish.audit.sha256_file(publish.adapter.__file__),
                   runtime_hashes=self.runtime, quarantine=publish.audit.quarantine_reason(self.item), import_status='ok')
        self.record['fingerprint'] = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
        self.data = {'schema_version':1, 'transport_failed':False,
                     'provenance':{'import_root':str(self.import_root)}, 'results':[self.record]}
        self.save_results()

    def save_results(self):
        self.results_path.write_text(json.dumps(self.data), encoding='utf-8')

    def plan(self):
        self.save_results()
        return publish.build_plan(self.results_path, self.catalog_path, self.import_root)

    def snapshot(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_default_plan_is_read_only_and_carries_actual_gpu_evidence(self):
        before = self.snapshot()
        plan = publish.build_plan(self.results_path, self.catalog_path, self.import_root)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(plan.summary['prepared_shaders'], 1)
        result = json.loads(plan.writes[-1][1])['materials'][0]
        self.assertEqual(result['compatibility'], 'adaptable')
        self.assertEqual(result['metadata']['_TD_VALIDATION']['gpu_evidence'], self.record['probe'])

    def test_full_638_coverage_is_required_in_production(self):
        with patch.object(publish, 'EXPECTED_COUNT', 638):
            with self.assertRaisesRegex(publish.PublicationError, 'exactly 638'):
                self.plan()

    def test_missing_duplicate_or_foreign_result_ids_fail(self):
        for rows in ([], [self.record,self.record], [dict(self.record,id='mat_'+'b'*20)]):
            self.data['results'] = rows
            with self.assertRaises(publish.PublicationError):self.plan()

    def test_interruption_pending_and_transport_failure_fail(self):
        for status in ('in_progress','probe_error','offline_adapted','import_conflict'):
            self.record['status']=status
            with self.assertRaises(publish.PublicationError):self.plan()
        self.record['status']='passed'
        self.data['transport_failed']=True
        with self.assertRaises(publish.PublicationError):self.plan()

    def test_stale_source_adapter_runtime_or_texture_evidence_fails(self):
        self.source.write_text('changed',encoding='utf-8')
        with self.assertRaisesRegex(publish.PublicationError,'Source changed'):self.plan()
        self.source.write_bytes((self.package/'original.fs').read_bytes())
        with patch.object(publish.audit,'runtime_fingerprints',return_value={'probe_script_sha256':'new'}):
            with self.assertRaisesRegex(publish.PublicationError,'fingerprint'):self.plan()
        self.adaptation.shader += '\n// changed'
        with self.assertRaisesRegex(publish.PublicationError,'Adaptation'):self.plan()

    def test_finite_review_remains_adaptable_with_warning(self):
        self.record['status']='review'
        self.record['probe']['samples'][0]['spatial_variance']=0
        plan=self.plan(); material=json.loads(plan.writes[-1][1])['materials'][0]
        self.assertEqual(material['compatibility'],'adaptable')
        self.assertIn('visual review',material['compatibility_reasons'][0])

    def test_nonfinite_and_compile_errors_remain_unsupported_without_shader_write(self):
        self.record['status']='review'
        self.record['probe']['samples'][0].update(finite=False,nonfinite_count=1)
        plan=self.plan(); self.assertEqual(plan.summary['prepared_shaders'],0)
        self.assertEqual(json.loads(plan.writes[-1][1])['materials'][0]['metadata']['_TD_VALIDATION']['status'],'nonfinite')
        self.record['status']='compile_error';self.record['probe']['errors']=['compiler error']
        plan=self.plan(); self.assertEqual(plan.summary['outcomes'],{'compile_error':1})

    def test_malformed_sample_evidence_is_rejected(self):
        for edit in ({'time':5}, {'shape':[1,1,4]}, {'finite':True,'nonfinite_count':7}):
            original=copy.deepcopy(self.record['probe']['samples'][0])
            self.record['probe']['samples'][0].update(edit)
            with self.assertRaises(publish.PublicationError):self.plan()
            self.record['probe']['samples'][0]=original

    def test_quarantine_cannot_be_overridden_by_success(self):
        self.item=replace(self.item,name='Twisted Tunnel')
        self.catalog=replace(self.catalog,materials=(self.item,))
        write_catalog(self.catalog,self.catalog_path);self.refresh_fingerprint()
        with self.assertRaisesRegex(publish.PublicationError,'Quarantine'):self.plan()
        self.record['status']='quarantined'
        plan=self.plan();self.assertEqual(plan.summary['outcomes'],{'quarantined':1})
        self.assertEqual(plan.summary['prepared_shaders'],0)

    def test_missing_manifest_skips_preparation_without_creating_a_package(self):
        (self.package/'material-import.json').unlink()
        plan=self.plan()
        self.assertEqual(plan.summary['prepared_shaders'],0)
        self.assertEqual(plan.summary['missing_managed_packages'],[self.material_id])

    def test_modified_package_and_foreign_prepared_shader_are_protected(self):
        (self.package/'original.fs').write_text('user edit',encoding='utf-8')
        with self.assertRaisesRegex(publish.PublicationError,'Imported file changed'):self.plan()
        (self.package/'original.fs').write_bytes(self.source.read_bytes())
        (self.package/'prepared.frag').write_text('my own shader',encoding='utf-8')
        with self.assertRaisesRegex(publish.PublicationError,'Foreign prepared'):self.plan()

    def test_apply_rechecks_plan_and_backs_up_catalog(self):
        target=self.package/'prepared.frag'
        target.write_text('// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 2\nold',encoding='utf-8')
        plan=self.plan();before=self.catalog_path.read_bytes()
        result=publish.apply_plan(plan)
        self.assertEqual(Path(result['catalog_backup']).read_bytes(),before)
        self.assertEqual(target.read_text(),self.adaptation.shader)
        self.assertFalse(result['live_deployment'])

    def test_change_after_plan_refuses_before_any_backup_or_write(self):
        plan=self.plan();self.source.write_text('changed after plan',encoding='utf-8')
        before=self.snapshot()
        with self.assertRaisesRegex(publish.PublicationError,'changed after planning'):publish.apply_plan(plan)
        self.assertEqual(before,self.snapshot())

    def test_failed_catalog_write_rolls_back_prepared_shader(self):
        target=self.package/'prepared.frag'
        target.write_text('// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 2\nold',encoding='utf-8')
        plan=self.plan();before_shader=target.read_bytes();before_catalog=self.catalog_path.read_bytes()
        real=publish._atomic_write
        def fail_catalog(path,data):
            if path==self.catalog_path:raise OSError('simulated disk failure')
            real(path,data)
        with patch.object(publish,'_atomic_write',side_effect=fail_catalog):
            with self.assertRaises(OSError):publish.apply_plan(plan)
        self.assertEqual(target.read_bytes(),before_shader)
        self.assertEqual(self.catalog_path.read_bytes(),before_catalog)


if __name__=='__main__':unittest.main()
