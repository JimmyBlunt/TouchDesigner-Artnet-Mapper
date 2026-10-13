"""Carry-forward evidence tests, using temporary managed packages only."""
import copy
import json
from unittest.mock import patch
import unittest

from tests import test_publish_material_audit as fixture_module
from tools import revalidate_material_audit as revalidate


class RevalidationTests(unittest.TestCase):
    def setUp(self):
        # Reuse the isolated catalog/package builder, not its test cases.
        self.f = fixture_module.PublishAuditTests('test_default_plan_is_read_only_and_carries_actual_gpu_evidence')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.old_runtime = {key:'old-'+key for key in (
            'probe_script_sha256','audit_harness_sha256','texture_runtime_sha256',
            'audio_runtime_sha256','shader_repairs_sha256','generator_sha256','parameter_runtime_sha256')}
        self.f.runtime.clear(); self.f.runtime.update(self.old_runtime)
        self.f.refresh_fingerprint()
        self.set_provenance()
        self.current = dict(self.old_runtime,shader_repairs_sha256='new-repairs-only')
        p = patch.object(revalidate.audit,'runtime_fingerprints',return_value=self.current)
        p.start();self.addCleanup(p.stop)

    def set_provenance(self):
        self.f.data['provenance'].update(self.old_runtime)
        self.f.data['provenance'].update(adapter_sha256=revalidate.audit.sha256_file(revalidate.adapter.__file__),
                                         times=[0.,1.,2.],resolution=[96,64])
        self.f.save_results()

    def plan(self):
        self.f.save_results()
        return revalidate.build_plan(self.f.results_path,self.f.catalog_path,self.f.import_root)

    def test_exact_evidence_carries_forward_without_any_gpu_import_or_write(self):
        before=self.f.snapshot(); original=copy.deepcopy(self.f.record)
        with (patch.object(revalidate.audit,'prepare',side_effect=AssertionError('prepare imports files')),
              patch.object(revalidate.audit,'td',side_effect=AssertionError('GPU forbidden'))):
            plan=revalidate.build_plan(self.f.results_path,self.f.catalog_path,self.f.import_root)
        self.assertEqual(before,self.f.snapshot())
        self.assertEqual(plan.summary['carried'],1)
        carried=plan.data['results'][0]
        for key in ('probe','completed_at','status','reasons','source_sha256','adaptation'):
            self.assertEqual(carried[key],original[key])
        self.assertNotEqual(carried['fingerprint'],original['fingerprint'])
        proof=carried['carry_forward'][0]
        self.assertEqual(proof['old_fingerprint'],original['fingerprint'])
        self.assertEqual(proof['new_fingerprint'],carried['fingerprint'])
        self.assertEqual(proof['old_shader_repairs_sha256'],self.old_runtime['shader_repairs_sha256'])
        self.assertEqual(proof['new_shader_repairs_sha256'],self.current['shader_repairs_sha256'])
        self.assertFalse(proof['gpu_rerun'])
        self.assertEqual(plan.data['provenance']['shader_repairs_sha256'],self.current['shader_repairs_sha256'])

    def test_source_or_shader_change_keeps_old_fingerprint_for_resume(self):
        original=copy.deepcopy(self.f.record)
        self.f.source.write_text('changed source',encoding='utf-8')
        plan=self.plan()
        self.assertEqual(plan.summary['carried'],0)
        self.assertEqual(plan.data['results'][0],original)
        self.f.source.write_bytes((self.f.package/'original.fs').read_bytes())
        self.f.adaptation.shader+='\n// new compiled shader'
        plan=self.plan()
        self.assertEqual(plan.data['results'][0],original)
        self.assertFalse(plan.summary['all_fingerprints_current'])
        self.assertEqual(plan.data['provenance']['shader_repairs_sha256'],self.old_runtime['shader_repairs_sha256'])

    def test_nonfirst_cube_face_change_invalidates_carryforward(self):
        faces=[]
        for i in range(6):
            p=self.f.root/('face%d.png'%i);p.write_bytes(bytes([i]));faces.append(str(p))
        self.f.adaptation.textures=({'name':'cube','resolved_path':faces[0],'resolved_paths':faces},)
        self.f.refresh_fingerprint();self.set_provenance()
        original=copy.deepcopy(self.f.record)
        (self.f.root/'face5.png').write_bytes(b'changed last face')
        plan=self.plan()
        self.assertEqual(plan.summary['carried'],0)
        self.assertEqual(plan.data['results'][0],original)

    def test_every_runtime_except_repairs_and_probe_settings_must_match(self):
        for key in self.current:
            if key=='shader_repairs_sha256':continue
            with patch.dict(self.current,{key:'changed'}):
                with self.assertRaises(revalidate.publish.PublicationError):self.plan()
        for key,value in (('adapter_sha256','changed'),('times',[0.,2.,4.]),('resolution',[192,128])):
            old=self.f.data['provenance'][key];self.f.data['provenance'][key]=value
            with self.assertRaises(revalidate.publish.PublicationError):self.plan()
            self.f.data['provenance'][key]=old

    def test_bad_or_interrupted_gpu_evidence_does_not_carry(self):
        original=copy.deepcopy(self.f.record)
        edits=[{'status':'in_progress'}, {'interrupted_gpu':True}, {'probe':{'samples':[]}},
               {'probe':{'errors':['compile error'], 'samples':original['probe']['samples']}},
               {'fingerprint':'unverifiable'}]
        for edit in edits:
            self.f.record.clear();self.f.record.update(copy.deepcopy(original));self.f.record.update(edit)
            plan=self.plan()
            self.assertEqual(plan.summary['carried'],0)
            self.assertEqual(plan.data['results'][0],self.f.record)

    def test_contradictory_finite_counts_block_carryforward(self):
        self.f.record['probe']['samples'][0]['nonfinite_count']=1
        plan=self.plan()
        self.assertEqual(plan.summary['carried'],0)

    def test_transport_failure_refuses_entire_operation(self):
        self.f.data['transport_failed']=True
        with self.assertRaises(revalidate.publish.PublicationError):self.plan()

    def test_modified_import_package_is_not_accepted_as_import_ok(self):
        (self.f.package/'original.fs').write_text('user edit',encoding='utf-8')
        plan=self.plan()
        self.assertEqual(plan.summary['carried'],0)
        self.assertIn('Imported file changed',plan.summary['requires_reaudit'][0]['reason'])

    def test_nonfinite_review_keeps_its_failure_evidence(self):
        self.f.record['status']='review'
        self.f.record['probe']['samples'][0].update(finite=False,nonfinite_count=1)
        plan=self.plan()
        self.assertEqual(plan.summary['carried'],1)
        self.assertEqual(plan.data['results'][0]['status'],'review')
        self.assertEqual(plan.data['results'][0]['probe']['samples'][0]['nonfinite_count'],1)

    def test_apply_backs_up_original_then_second_plan_is_already_current(self):
        plan=self.plan();before=self.f.results_path.read_bytes()
        result=revalidate.apply_plan(plan)
        from pathlib import Path
        self.assertEqual(Path(result['original_results_backup']).read_bytes(),before)
        second=revalidate.build_plan(self.f.results_path,self.f.catalog_path,self.f.import_root)
        self.assertEqual(second.summary['carried'],0)
        self.assertEqual(second.summary['already_current'],1)

    def test_stale_plan_refuses_before_backup(self):
        plan=self.plan();self.f.source.write_text('new change',encoding='utf-8');before=self.f.snapshot()
        with self.assertRaises(revalidate.publish.PublicationError):revalidate.apply_plan(plan)
        self.assertEqual(self.f.snapshot(),before)


if __name__=='__main__':unittest.main()
