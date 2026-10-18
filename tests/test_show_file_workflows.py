import ast
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from pixelblaze_mapper import show_editor as editor, show_automation as automation
from pixelblaze_mapper.build_show_picker import PICKER_RUNTIME, replace_picker_runtime
from pixelblaze_mapper.show_catalog import load_show_bundle

SOURCE = Path(__file__).parents[1] / 'pixelblaze_mapper/build_show_editor.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))
RUNTIME = next(ast.literal_eval(n.value) for n in TREE.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EDITOR_RUNTIME' for t in n.targets))
APPLY = next(n for n in ast.parse(RUNTIME).body if isinstance(n, ast.FunctionDef) and n.name == '_apply')

class ShowFileWorkflowsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.stored = {}
        self.state = {'recording':'0'}
        self.document = editor.empty_show()
        self.recorded = automation.empty()
        self.materials = {'old_material': {'source':'old'}}
        self.fields = {'ed_show_name':'Test'}
        self.scope = dict(json=json, editor=editor, automation=automation,
            OWNER=SimpleNamespace(store=self.stored.__setitem__, fetch=lambda k,d=None:self.stored.get(k,d)),
            show=lambda:self.document, selected=lambda:0, _state=lambda k,d='':self.state.get(k,d),
            _set_state=self.state.__setitem__, automation_data=lambda:self.recorded, imported_data=lambda:self.materials,
            _write_automation=lambda v:setattr(self,'recorded',v), _write_imported=lambda v:setattr(self,'materials',v),
            _message=lambda v:self.state.__setitem__('message',v), write=lambda v:setattr(self,'document',v),
            _field=self.fields.__getitem__, _show_path=lambda n:str(self.folder/(n+'.json')))
        exec(PICKER_RUNTIME, self.scope)
        exec(compile(ast.Module(body=[APPLY], type_ignores=[]),'<apply>','exec'),self.scope)

    def save_fixture(self, name='unusual-file.json', document=None):
        path=self.folder/name
        path.write_text(json.dumps(document or dict(editor.empty_show(),name='Different Label')),encoding='utf-8')
        return path

    def test_switch_without_sidecars_clears_previous_bundle(self):
        path=self.save_fixture()
        self.scope['_load_show_file'](str(path))
        self.assertEqual(self.materials,{})
        self.assertEqual(self.recorded,automation.empty())
        self.assertIn('old_material',self.stored['previous_show_bundle']['materials'])
        self.assertEqual(self.document['name'],'Different Label')
        self.assertEqual(self.state['page'],0)

    def test_invalid_sidecar_never_mutates_live_state(self):
        path=self.save_fixture()
        path.with_suffix('.materials.json').write_text('[]',encoding='utf-8')
        before=(self.document,self.materials,self.recorded,dict(self.stored))
        with self.assertRaises(ValueError): self.scope['_load_show_file'](str(path))
        self.assertEqual((self.document,self.materials,self.recorded,self.stored),before)

    def test_recording_blocks_new_and_load(self):
        self.state['recording']='1'
        with self.assertRaises(ValueError): self.scope['_load_show_file'](str(self.save_fixture()))
        with self.assertRaises(ValueError): self.scope['_apply']('new_show')
        self.assertIn('old_material',self.materials)

    def test_new_show_resets_sidecars_and_retains_recovery_bundle(self):
        self.scope['_apply']('new_show')
        self.assertEqual(self.materials,{})
        self.assertEqual(self.recorded,automation.empty())
        self.assertEqual(self.document['cues'],[])
        self.assertIn('old_material',self.stored['previous_show_bundle']['materials'])

    def test_save_updates_selected_filename_then_rename_saves_copy(self):
        path=self.save_fixture()
        self.scope['_load_show_file'](str(path))
        self.fields['ed_show_name']='Different Label'
        self.scope['_apply']('save_show')
        self.assertFalse((self.folder/'different-label.json').exists())
        self.assertTrue(path.with_suffix('.automation.json').exists())
        self.fields['ed_show_name']='New Copy'
        self.scope['_apply']('save_show')
        self.assertTrue((self.folder/'new-copy.json').exists())
        self.assertTrue(path.exists())
        self.assertEqual(load_show_bundle(self.folder/'new-copy.json')[0]['name'],'New Copy')

    def test_load_button_opens_same_picker(self):
        calls=[]
        self.scope['picker_action']=calls.append
        self.scope['_apply']('load_show')
        self.assertEqual(calls,['open'])

    def test_picker_upgrade_is_idempotent_and_preserves_other_functions(self):
        source='def custom_patch():\n    return 123\n'+PICKER_RUNTIME
        updated=replace_picker_runtime(replace_picker_runtime(source))
        self.assertEqual(updated.count('def picker_action('),1)
        self.assertEqual(updated.count('def _load_show_file('),1)
        self.assertIn('return 123',updated)

if __name__=='__main__': unittest.main()
