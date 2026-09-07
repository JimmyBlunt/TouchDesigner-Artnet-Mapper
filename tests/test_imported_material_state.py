import unittest
import json

from pixelblaze_mapper.imported_material_state import ImportedMaterialStateStore
from pixelblaze_mapper.madmapper_parameters import parameter_schema


def schema(*inputs):
    return parameter_schema({"INPUTS": list(inputs)})


class ImportedMaterialStateTests(unittest.TestCase):
    def test_each_material_keeps_its_own_native_values(self):
        parameters = schema({"NAME": "speed", "TYPE": "float", "DEFAULT": 1, "MIN": 0, "MAX": 4})
        store = ImportedMaterialStateStore()
        store.merge("a", parameters)
        store.set_value("a", parameters[0], 3)
        store.merge("b", parameters)
        store.set_value("b", parameters[0], 0.5)
        self.assertEqual(store.values("a")["speed"], 3.0)
        self.assertEqual(store.values("b")["speed"], 0.5)

    def test_schema_edits_keep_matching_values_and_default_new_or_changed_types(self):
        old = schema(
            {"NAME": "speed", "TYPE": "float", "DEFAULT": 1},
            {"NAME": "mode", "TYPE": "int", "DEFAULT": 2},
        )
        changed = schema(
            {"NAME": "speed", "TYPE": "float", "DEFAULT": 9},
            {"NAME": "mode", "TYPE": "bool", "DEFAULT": True},
            {"NAME": "new_value", "TYPE": "float", "DEFAULT": 0.25},
        )
        store = ImportedMaterialStateStore()
        store.merge("material", old)
        store.set_value("material", old[0], 4)
        store.set_value("material", old[1], 7)
        values = store.merge("material", changed)
        self.assertEqual(values, {"speed": 4.0, "mode": True, "new_value": 0.25})

    def test_components_clamp_and_uniforms_skip_compile_time_inputs(self):
        parameters = schema(
            {"NAME": "position", "TYPE": "point2D", "DEFAULT": [0, 0], "MIN": [-1, -1], "MAX": [1, 1]},
            {"NAME": "mode", "TYPE": "long", "VALUES": ["A", "B"], "DEFAULT": "A", "FLAGS": "generate_as_define"},
        )
        store = ImportedMaterialStateStore()
        store.merge("material", parameters)
        self.assertEqual(store.set_value("material", parameters[0], 4, component=1), (0.0, 1.0))
        self.assertEqual(store.uniform_vectors("material", parameters), {"uMMParam000": (0.0, 1.0, 0.0, 0.0)})

    def test_page_and_json_round_trip(self):
        parameters = schema({"NAME": "speed", "TYPE": "float", "DEFAULT": 1})
        store = ImportedMaterialStateStore()
        store.merge("material", parameters)
        self.assertEqual(store.set_page("material", 4, 5), 4)
        restored = ImportedMaterialStateStore.from_dict(store.to_dict())
        restored.merge("material", parameters)
        self.assertEqual(restored.page("material", 5), 4)

    def test_rollback_snapshot_is_independent_of_later_edits(self):
        parameters = schema({"NAME": "speed", "TYPE": "float", "DEFAULT": 1})
        store = ImportedMaterialStateStore()
        store.merge("a", parameters)
        before = store.to_dict()
        store.set_value("a", parameters[0], 3)
        restored = ImportedMaterialStateStore.from_dict(before)
        self.assertEqual(restored.values("a")["speed"], 1)
        before["materials"]["a"]["values"]["speed"] = 8
        self.assertEqual(restored.values("a")["speed"], 1)

    def test_json_vector_values_are_not_shared_with_caller(self):
        parameters = schema({"NAME": "position", "TYPE": "point2D", "DEFAULT": [0, 0]})
        store = ImportedMaterialStateStore()
        store.merge("a", parameters)
        document = json.loads(json.dumps(store.to_dict()))
        restored = ImportedMaterialStateStore.from_dict(document)
        document["materials"]["a"]["values"]["position"][0] = 123
        values = restored.values("a")
        values["position"][1] = 234
        self.assertEqual(restored.values("a")["position"], [0, 0])


if __name__ == "__main__":
    unittest.main()
