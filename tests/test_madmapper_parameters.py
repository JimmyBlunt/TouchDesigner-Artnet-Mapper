import unittest

from pixelblaze_mapper.madmapper_parameters import (
    coerce_value,
    default_values,
    parameter_schema,
    uniform_vector,
)


class MadMapperParameterTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "INPUTS": [
                {"LABEL": "Layer A/Speed", "NAME": "speed_a", "TYPE": "float", "MIN": 0, "MAX": 4, "DEFAULT": 1},
                {"LABEL": "Layer B/Speed", "NAME": "speed_b", "TYPE": "float", "MIN": 0, "MAX": 8, "DEFAULT": 2},
                {"Label": "Color/Tint", "NAME": "tint", "TYPE": "color", "DEFAULT": [1, 0.5, 0, 1]},
                {"LABEL": "Mode", "NAME": "mode", "TYPE": "long", "VALUES": ["A", "B"], "DEFAULT": "B", "FLAGS": "generate_as_define"},
                {"LABEL": "Move", "NAME": "move", "TYPE": "point2D", "MIN": [-1, -1], "MAX": [1, 1], "DEFAULT": [0, 0]},
            ]
        }

    def test_schema_preserves_duplicate_labels_by_unique_shader_name(self):
        schema = parameter_schema(self.metadata)
        self.assertEqual([item.name for item in schema[:2]], ["speed_a", "speed_b"])
        self.assertEqual([item.groups for item in schema[:2]], [("Layer A",), ("Layer B",)])
        self.assertEqual([item.display_label for item in schema[:2]], ["Speed", "Speed"])
        self.assertEqual([item.uniform for item in schema[:2]], ["uMMParam000", "uMMParam001"])

    def test_types_defaults_and_compile_time_flags(self):
        schema = parameter_schema(self.metadata)
        values = default_values(schema)
        self.assertEqual(values["mode"], 1)
        self.assertTrue(schema[3].compile_time)
        self.assertEqual(uniform_vector(schema[2], values["tint"]), (1.0, 0.5, 0.0, 1.0))

    def test_values_are_clamped_per_component(self):
        schema = parameter_schema(self.metadata)
        self.assertEqual(coerce_value(schema[0], 9), 4.0)
        self.assertEqual(coerce_value(schema[4], [2, -2]), (1.0, -1.0))


if __name__ == "__main__":
    unittest.main()
