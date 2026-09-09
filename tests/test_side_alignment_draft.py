import numpy as np
import unittest
from pixelblaze_mapper.layout_scene import Scene, Scan, SceneObject, LedBinding
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor, document_json, load_document_json
from pixelblaze_mapper.side_alignment_draft import prepare, SPECS, UNITS_PER_CM

def fixture():
    points=tuple((i%16/100,i//16/100,0.) for i in range(3744))
    scan=Scan('original','Original',points)
    back=Scan('back','Back',tuple((.9,1.,.6) for _ in range(203)))
    old=SceneObject('old','Old',tuple(LedBinding(f'l{i}',i,i,'original',i) for i in range(3744) if i not in range(1440,1696)))
    new=SceneObject('new','New',tuple(LedBinding(f'n{i}',i,1440+i,'back',i) for i in range(203)))
    doc=LayoutDocument(Scene('scene','Scene',(scan,back),(old,new),3744))
    repaired=tuple((float(i%20),float(i//20),0.1*(i%20)) for i in range(1184))
    return doc,repaired

def test_sizes_identity_and_untouched_rear():
    doc,points=fixture(); text=document_json(doc)
    updated,report=prepare(doc,points,(634,))
    assert document_json(doc)==text
    before={l.source_index:(l,p) for l,p in doc.scene.world_points()}
    after={l.source_index:(l,p) for l,p in updated.scene.world_points()}
    assert before.keys()==after.keys()
    assert all(before[i]==after[i] for i in before if i>=1184)
    assert updated.scene.scans[:len(doc.scene.scans)]==doc.scene.scans
    for key,name,start,count,width,height,center in SPECS:
        p=np.array([after[i][1] for i in range(start,start+count)])
        assert np.allclose(np.ptp(p,axis=0)[:2],[height*UNITS_PER_CM,width*UNITS_PER_CM])
        assert np.allclose((p.max(0)+p.min(0))/2,center)
        assert [after[i][0].local_index for i in range(start,start+count)]==list(range(count))
    assert not report['active_applied']

def test_undo_redo_serialization_and_repeated_guard():
    doc,points=fixture(); updated,_=prepare(doc,points)
    history=LayoutEditor(doc); history.commit(updated)
    assert history.undo()==doc
    assert history.redo()==updated
    assert load_document_json(document_json(updated))==updated
    with unittest.TestCase().assertRaises(ValueError): prepare(updated,points)

def test_approved_top_bottom_orientation():
    doc,points=fixture(); updated,_=prepare(doc,points)
    after={l.source_index:p for l,p in updated.scene.world_points()}
    # Synthetic plane has h aligned with increasing raw X and v with raw Y.
    # Confirmed face: vertical=-h; horizontal=-v=-worldY.
    assert after[1][0]<after[0][0]
    assert after[20][1]>after[0][1]
    assert np.isclose(after[1][2],after[0][2])

def test_invalid_input_rejected():
    doc,points=fixture()
    with unittest.TestCase().assertRaises(ValueError): prepare(doc,points[:-1])
    bad=list(points); bad[517]=(float('nan'),0.,0.)
    with unittest.TestCase().assertRaises(ValueError): prepare(doc,bad)

def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(value) for name,value in globals().items() if name.startswith('test_') and callable(value))
