"""Save boundaries exercise actual runtime code, not only string contracts."""
import ast
import importlib
import json
import pickle
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

from pixelblaze_mapper.build_material_library_browser import _runtime_source as library_source
from pixelblaze_mapper.build_p1_material_state import _runtime_source as state_source
from pixelblaze_mapper.imported_material_state import ImportedMaterialStateStore
from pixelblaze_mapper.material_state import MaterialSettings, MaterialStateStore
from pixelblaze_mapper.material_storage import runtime_cache, state_document


class Owner:
    def __init__(self, storage=None):
        self.storage = storage or {}
        self.startup = {}

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def store(self, key, value):
        self.storage[key] = value

    def storeStartupValue(self, key, value):
        self.startup[key] = value

    def save_image(self):
        # Documented TD startup substitution, simulated; native save is root's test.
        return pickle.loads(pickle.dumps({**self.storage, **self.startup}))


def preamble(source, owner):
    tree = ast.parse(source())
    body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            break
        body.append(node)
    scope = {'op': lambda _: owner}
    exec(compile(ast.Module(body=body, type_ignores=[]), '<actual runtime startup>', 'exec'), scope)
    return scope


class MaterialStorageTests(unittest.TestCase):
    def test_p1_saved_phase_is_current_and_reopen_rebases_without_downtime(self):
        store = MaterialStateStore()
        store.activate('madmapper:playing', 10, initial=MaterialSettings(speed=2))
        owner = Owner({'p1_material_state_store': store, 'p1_material_state_runtime_schema': 3})
        scope = preamble(state_source, owner)
        functions = [n for n in ast.parse(state_source()).body if isinstance(n, ast.FunctionDef)]
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<actual phase runtime>', 'exec'), scope)
        scope['_now'] = lambda: 13
        owner.store = Mock(side_effect=owner.store)
        self.assertEqual(scope['tick'](), 6)
        owner.store.assert_not_called()
        image = owner.save_image()
        self.assertEqual(image['p1_material_state_store']['materials']['madmapper:playing']['phase'], 6)
        reopened_owner = Owner(image)
        reopened = preamble(state_source, reopened_owner)
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<actual restored phase>', 'exec'), reopened)
        applied = []
        reopened.update(_now=lambda: 10000, _current_key=lambda: 'madmapper:playing',
                        _apply=applied.append, _persist=lambda: None, CONTROLS=NS(par=NS()))
        reopened['initialize']()
        self.assertEqual(reopened['STORE'].state('madmapper:playing').phase, 6)
        self.assertEqual(reopened['STORE'].phase_at(10001), 8)
        self.assertEqual(applied[0].speed, 2)

    def test_cache_without_td_startup_support_never_persists_python_objects(self):
        legacy = {'unsafe': object()}
        owner = NS(storage={'cache': legacy})
        self.assertEqual(runtime_cache(owner, 'cache'), {})
        self.assertNotIn('cache', owner.storage)

    def test_document_is_detached_primitives_and_rejects_nonfinite_values(self):
        source = {'materials': {'a': {'values': {'color': (1, .5, 0)}}}}
        converted = state_document(source)
        self.assertEqual(converted['materials']['a']['values']['color'], [1, .5, 0])
        converted['materials'].clear()
        self.assertIn('a', source['materials'])
        with self.assertRaises(ValueError):
            state_document({'materials': {'a': {'values': {'v': float('nan')}}}})

    def test_stale_adaptation_cache_is_not_pickled_and_runtime_reuses_it(self):
        import pixelblaze_mapper.madmapper_td_adapter as adapter
        old = adapter.AdaptationResult('adaptable', (), (), 'shader', {})
        importlib.reload(adapter)
        with self.assertRaises(pickle.PicklingError):
            pickle.dumps(old)
        cache = {'material': {'initial': old}}
        owner = Owner({'material_parameter_context_cache': cache,
                       'material_hover_context_cache': {'material': (old, {}, ())}})
        first = preamble(library_source, owner)
        image = owner.save_image()
        self.assertIs(first['_parameter_context_cache'], cache)
        self.assertIs(preamble(library_source, owner)['_parameter_context_cache'], cache)
        self.assertIsNone(image['material_parameter_context_cache'])
        self.assertIsNone(image['material_hover_context_cache'])
        restored = preamble(library_source, Owner(image))
        self.assertEqual(restored['_parameter_context_cache'], {})

    def test_legacy_native_store_migrates_without_class_identity_and_preserves_all_values(self):
        document = {'schema': 1, 'materials': {
            'playing': {'types': {'scale': 'float'}, 'values': {'scale': .258123456789}, 'page': 2},
            'other': {'types': {'tint': 'color'}, 'values': {'tint': [1, .5, 0, 1]}, 'page': 0}}}
        # Represents a still usable object created before its class was reloaded.
        class OldStore:
            def to_dict(self):
                return document
        owner = Owner({'madmapper_parameter_store': OldStore(), 'active_label': 'Bubble Rings'})
        scope = preamble(library_source, owner)
        self.assertEqual(scope['PARAMETER_STORE'].to_dict(), document)
        image = owner.save_image()
        self.assertIsInstance(image['madmapper_parameter_store'], dict)
        self.assertEqual(image['active_label'], 'Bubble Rings')
        self.assertEqual(preamble(library_source, Owner(image))['PARAMETER_STORE'].to_dict(), document)

    def test_native_persist_writes_only_primitives_and_same_dat_document(self):
        store = ImportedMaterialStateStore.from_dict({'materials': {'a': {
            'types': {'v': 'float'}, 'values': {'v': .123456789}, 'page': 1}}})
        owner = Owner()
        rows = []
        class Table:
            def clear(self): rows.clear()
            def appendRow(self, row): rows.append(row)
        owner.op = lambda _: Table()
        scope = {'OWNER': owner, 'PARAMETER_STORE': store, 'json': json}
        tree = ast.parse(library_source())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_persist_parameter_store')
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual persist>', 'exec'), scope)
        scope['_persist_parameter_store']()
        self.assertEqual(owner.save_image()['madmapper_parameter_store'], json.loads(rows[1][1]))

    def test_p1_runtime_reload_keeps_phase_but_save_contains_no_class_instances(self):
        store = MaterialStateStore()
        store.activate('madmapper:playing', 10, initial=MaterialSettings(scale=7, intensity=.2))
        store.tick(12)
        owner = Owner({'p1_material_state_store': store, 'p1_material_state_runtime_schema': 3})
        first = preamble(state_source, owner)
        first['STORE'].tick(14)
        second = preamble(state_source, owner)
        self.assertIs(second['STORE'], first['STORE'])
        self.assertEqual(second['STORE'].state('madmapper:playing').phase, 4)
        image = owner.save_image()
        self.assertIsInstance(image['p1_material_state_store'], dict)
        self.assertIsNone(image['p1_material_runtime_cache'])
        self.assertIsNone(image['p1_material_state_runtime_schema'])
        restored = preamble(state_source, Owner(image))['STORE']
        self.assertEqual(restored.active_key, 'madmapper:playing')
        self.assertEqual(restored.state(restored.active_key).settings.scale, 7)
        self.assertEqual(restored.state(restored.active_key).settings.intensity, .2)


if __name__ == '__main__':
    unittest.main()
