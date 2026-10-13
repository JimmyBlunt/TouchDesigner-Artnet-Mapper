"""Cube inputs preserve face order, cache identity and clean up owned nodes."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pixelblaze_mapper.material_texture_runtime import bind_textures


class CubeBindingTests(unittest.TestCase):
    def setUp(self):
        self.children = []
        def create(kind,name):
            node=SimpleNamespace(name=name,kind=kind,par=SimpleNamespace(),inputs=[],
                                 cook=lambda **kw:None,errors=lambda:[])
            node.setInputs=lambda nodes:setattr(node,'inputs',list(nodes))
            node.destroy=lambda:self.children.remove(node)
            self.children.append(node)
            return node
        parent=SimpleNamespace(children=self.children,create=create,
            op=lambda name:next((n for n in self.children if n.name==name),None))
        self.stored={}
        self.preview=SimpleNamespace(name='probe',parent=lambda:parent,par=SimpleNamespace(),
            inputs=[],fetch=lambda k,d:self.stored.get(k,d),store=lambda k,v:self.stored.update({k:v}))
        self.preview.setInputs=lambda nodes:setattr(self.preview,'inputs',list(nodes))
        self.td=patch.dict(sys.modules,{'td':SimpleNamespace(moviefileinTOP='image',cubemapTOP='cube')})
        self.td.start()
        self.addCleanup(self.td.stop)
        self.cube=dict(TYPE='cube',resolved_path='px.png',
                       resolved_paths=['px.png','nx.png','py.png','ny.png','pz.png','nz.png'])

    def bind(self,textures):
        bind_textures(self.preview,SimpleNamespace(textures=textures))

    def test_six_faces_keep_gl_order_and_mix_with_2d(self):
        self.bind([self.cube,dict(resolved_path='flat.png')])
        cube,flat=self.preview.inputs
        self.assertEqual(cube.kind,'cube')
        self.assertEqual(cube.par.mode,'onepersidetocubemap')
        self.assertEqual([n.par.file for n in cube.inputs],self.cube['resolved_paths'])
        self.assertEqual(flat.par.file,'flat.png')
        self.assertEqual(len(self.children),8)

    def test_changed_nonfirst_face_invalidates_cached_binding(self):
        self.bind([self.cube])
        changed=dict(self.cube,resolved_paths=[*self.cube['resolved_paths'][:5],'new-nz.png'])
        self.bind([changed])
        self.assertEqual(self.preview.inputs[0].inputs[5].par.file,'new-nz.png')
        self.assertEqual(len(self.children),7)

    def test_cube_to_flat_to_empty_cleans_faces_and_keeps_unrelated_nodes(self):
        unrelated=self.preview.parent().create('other','production_image')
        self.bind([self.cube])
        self.bind([dict(resolved_path='flat.png')])
        self.assertEqual(len(self.children),2)
        self.bind([])
        self.assertEqual(self.children,[unrelated])
        self.assertEqual(self.preview.inputs,[])

    def test_invalid_face_count_keeps_existing_connection(self):
        self.bind([dict(resolved_path='flat.png')])
        before=list(self.preview.inputs)
        with self.assertRaisesRegex(ValueError,'six'):
            self.bind([dict(self.cube,resolved_paths=['only.png'])])
        self.assertEqual(before,self.preview.inputs)


if __name__=='__main__':
    unittest.main()
