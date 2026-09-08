import json
from pathlib import Path
import tempfile
import unittest

from pixelblaze_mapper.scan_result_review import inspect_result, append_reviewed
from pixelblaze_mapper.layout_scene import Scene, Transform, SceneError, new_id, import_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor


class ResultReviewTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/'candidate_3d.csv'
        self.path.write_text('index,x,y,z,xn,yn,zn,error\n0,1,2,3,0,0,0,0.1\n2,4,5,6,0,0,0,0.2\n')
        (self.path.parent/'quality_pending.json').write_text(json.dumps({'session_id':'s','reconstructed_ids':[0,2]}))
        self.status={'state':'review_required','running':False,'candidate':str(self.path),'session_id':'s','reconstructed':2,'missing_ids':[1]}
        self.review=inspect_result(self.status)
        self.doc=LayoutDocument(Scene(new_id(),'existing'))

    def test_sparse_sources_and_transform_preserve_original_scan(self):
        updated=append_reviewed(self.doc,self.review,source_offset=100,name='back',transform=Transform(translation=(1,0,0)))
        self.assertEqual([b.source_index for b in updated.scene.objects[0].leds],[100,102])
        self.assertEqual([p for b,p in updated.scene.world_points()],[(2,2,3),(5,5,6)])
        self.assertEqual(updated.scene.scans[0].points[0],(1,2,3))
        self.assertFalse(self.doc.scene.objects)

    def test_existing_object_is_unchanged_and_addition_is_undoable(self):
        editor=LayoutEditor(self.doc)
        editor.append(import_scan('[[0,0,0]]',format='pixelblaze',name='existing'),source_start=0)
        before=editor.current
        editor.commit(append_reviewed(before,self.review,source_offset=10,name='new'))
        self.assertEqual(editor.current.scene.objects[0],before.scene.objects[0])
        editor.undo(); self.assertEqual(editor.current,before)

    def test_collision_and_duplicate_rejected(self):
        one=append_reviewed(self.doc,self.review,source_offset=0,name='one')
        with self.assertRaisesRegex(SceneError,'already'):
            append_reviewed(one,self.review,source_offset=10,name='again')
        editor=LayoutEditor(self.doc)
        editor.append(import_scan('[[0,0,0]]',format='pixelblaze',name='occupied'),source_start=0)
        with self.assertRaisesRegex(SceneError,'overlapping'):
            append_reviewed(editor.current,self.review,source_offset=0,name='collision')

    def test_changed_file_is_not_transferred(self):
        self.path.write_text(self.path.read_text().replace('1,2,3','9,2,3'))
        with self.assertRaisesRegex(SceneError,'changed'):
            append_reviewed(self.doc,self.review,source_offset=0,name='bad')

    def test_incomplete_job_and_wrong_report_rejected(self):
        with self.assertRaises(SceneError): inspect_result({**self.status,'running':True})
        with self.assertRaises(SceneError): inspect_result({**self.status,'session_id':'other'})

    def test_missing_pixels_not_silently_exportable(self):
        updated=append_reviewed(self.doc,self.review,source_offset=0,name='gaps')
        with self.assertRaises(SceneError): updated.scene.validate_output()
