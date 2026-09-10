import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pixelblaze_mapper.layout_scene import Scene, SceneError, new_id
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor, document_json, load_document_json
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget
from pixelblaze_mapper.scan_result_review import inspect_saved_result, append_reviewed, review_defaults
from pixelblaze_mapper.scan_partial_acceptance import append_partial_reviewed, occupied_sources, PREFIX


class PartialAcceptanceTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        targets=tuple(ScanTarget('led-%d'%i,'object',i,i) for i in range(5))
        self.session=ScanSession('session','scene','revision',targets,tuple(t.led_id for t in targets))
        self.views=[]
        for index in range(2):
            folder=self.root/str(index);folder.mkdir()
            view=folder/'view.csv'
            view.write_text('index,u,v\n0,.1,.2\n1,.2,.2\n2,.3,.4\n')
            (folder/'capture.json').write_text(json.dumps({'scene_revision':'revision','identity':{str(i):'led-%d'%i for i in range(5)}}))
            (folder/'result.json').write_text(json.dumps({'state':'complete'}))
            self.views.append(view)
        self.path=self.root/'candidate_3d.csv'
        self.original='index,x,y,z,xn,yn,zn,error\n0,1,2,3,.1,.2,.3,.1\n2,4,5,6,.4,.5,.6,.2\n'
        self.path.write_text(self.original)
        (self.root/'quality_pending.json').write_text(json.dumps({'session_id':'session','reconstructed_ids':[0,2]}))
        self.review=inspect_saved_result(self.path)
        self.doc=LayoutDocument(Scene(new_id(),'existing'))
        self.addCleanup(patch.stopall)
        patch('socket.socket',side_effect=AssertionError('no hardware')).start()
        patch('subprocess.Popen',side_effect=AssertionError('no worker')).start()

    def append(self,**kwargs):
        return append_partial_reviewed(kwargs.pop('document',self.doc),self.review,self.session,
            kwargs.pop('views',self.views),source_offset=kwargs.pop('source_offset',100),name='Panel',**kwargs)

    def test_sparse_identity_trailing_missing_and_original_measurements(self):
        result=self.append();scan=result.scene.scans[0];obj=result.scene.objects[0]
        self.assertEqual(len(scan.points),5)
        self.assertEqual(scan.missing_indices,(1,3,4))
        self.assertEqual([(b.led_id,b.local_index,b.source_index,b.scan_index) for b in obj.leds],
                         [('led-0',0,100,0),('led-2',2,102,2)])
        self.assertEqual([p for b,p in result.scene.world_points()],[(1,2,3),(4,5,6)])
        rows=[dict(row) for row in scan.row_metadata]
        self.assertEqual(rows[1]['scan_status'],'missing_not_reconstructed')
        self.assertEqual(rows[4]['scan_status'],'missing_never_observed')
        self.assertTrue(all(row['occlusion']=='unknown' for row in rows))
        self.assertEqual(self.path.read_text(),self.original)
        evidence=json.loads(next(w[len(PREFIX):] for w in scan.warnings if w.startswith(PREFIX)))
        self.assertEqual(evidence['session'],json.loads(json.dumps(self.session.to_dict())))
        self.assertEqual(len(evidence['view_sha256']),6)
        with self.assertRaises(SceneError):result.scene.validate_output()

    def test_roundtrip_undo_redo_and_reserved_tail(self):
        result=self.append()
        self.assertEqual(load_document_json(document_json(result)),result)
        editor=LayoutEditor(self.doc);editor.commit(result);editor.undo()
        self.assertEqual(editor.current,self.doc)
        editor.redo();self.assertEqual(editor.current,result)
        self.assertEqual(occupied_sources(result),set(range(100,105)))
        defaults=review_defaults(result,{'ids':[100]})
        self.assertEqual(defaults['offset'],'5')
        self.assertEqual(result.routes,self.doc.routes)

    def test_missing_slots_cannot_be_reused_by_another_result(self):
        result=self.append()
        other=self.root/'other';other.mkdir()
        path=other/'candidate_3d.csv';path.write_text(self.original)
        (other/'quality_pending.json').write_text((self.root/'quality_pending.json').read_text())
        review=inspect_saved_result(path)
        with self.assertRaisesRegex(SceneError,'overlapping'):
            append_reviewed(result,review,source_offset=101,name='collision')
        with self.assertRaisesRegex(SceneError,'overlaps'):
            self.append(document=result,source_offset=104)

    def test_wrong_identity_insufficient_views_and_changed_candidate_rejected(self):
        with self.assertRaisesRegex(SceneError,'two supporting'):
            self.append(views=self.views[:1])
        self.path.write_text(self.original.replace('1,2,3','9,2,3'))
        with self.assertRaisesRegex(SceneError,'changed'):self.append()
        self.path.write_text(self.original)
        (self.views[0].parent/'capture.json').write_text('{}')
        with self.assertRaises(ValueError):self.append()

    def test_metadata_change_during_validation_rejected(self):
        from pixelblaze_mapper.scan_coverage_visual import build_data
        def changed(*args,**kwargs):
            result=build_data(*args,**kwargs)
            (self.views[0].parent/'result.json').write_text('{"state":"failed"}')
            return result
        with patch('pixelblaze_mapper.scan_coverage_visual.build_data',side_effect=changed):
            with self.assertRaisesRegex(SceneError,'changed'):self.append()


if __name__=='__main__':unittest.main()
