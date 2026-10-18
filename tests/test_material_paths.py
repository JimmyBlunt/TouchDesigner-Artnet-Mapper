import json, tempfile, unittest
from copy import deepcopy
from pathlib import Path
from pixelblaze_mapper.material_paths import resolve_asset_path, resolve_catalog_document, load_catalog_document

class PortableMaterialPathsTests(unittest.TestCase):
    def test_old_existing_copy_cannot_shadow_checkout_and_metadata_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shader=root/'material_library/sources/Materials/Molnár/Molnár.fs'
            shader.parent.mkdir(parents=True); shader.write_text('reviewed',encoding='utf-8')
            old='C:\\Old Checkout\\material_library\\sources\\Materials\\Molnár\\Molnár.fs'
            document={'source':{'root':'C:/Old Checkout/material_library/sources/Materials'},'materials':[{'id':'stable','source_path':old,'preview_path':None,'relative_path':'corrupt name not used','metadata':{'_TD_VALIDATION':{'source_sha256':'same','status':'quarantined'}}}]}
            before=deepcopy(document)
            result=resolve_catalog_document(document,root/'material_library/catalogs/a.json')
            self.assertEqual(Path(result['materials'][0]['source_path']),shader)
            self.assertEqual(result['materials'][0]['metadata'],before['materials'][0]['metadata'])
            self.assertEqual(result['materials'][0]['id'],'stable')
            self.assertEqual(document,before)

    def test_relative_catalog_and_package_paths_are_portable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(Path(resolve_asset_path('material_library/imported/id/prepared.frag',project_root=root)),root/'material_library/imported/id/prepared.frag')
            self.assertEqual(Path(resolve_asset_path('../sources/texture.png',base_dir=root/'material_library/catalogs')),root/'material_library/sources/texture.png')
            self.assertEqual(resolve_asset_path('D:/unrelated/file.png',project_root=root),'D:/unrelated/file.png')

    def test_rejects_traversal_and_preserves_empty_values(self):
        for path in ('C:/old/material_library/../outside','material_library/sources/../../outside','material_library/x:stream'):
            with self.subTest(path=path),self.assertRaises(ValueError): resolve_asset_path(path)
        self.assertIsNone(resolve_asset_path(None))
        self.assertEqual(resolve_asset_path(''),'')

    def test_catalog_file_not_rewritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); path=root/'material_library/catalogs/test.json'
            path.parent.mkdir(parents=True)
            text=json.dumps({'source':{'root':'C:/old/material_library/sources'},'materials':[]})
            path.write_text(text,encoding='utf-8')
            data=load_catalog_document(path)
            self.assertEqual(Path(data['source']['root']),root/'material_library/sources')
            self.assertEqual(path.read_text(encoding='utf-8'),text)

if __name__=='__main__': unittest.main()
