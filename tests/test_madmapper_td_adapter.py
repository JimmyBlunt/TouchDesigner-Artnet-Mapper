from pathlib import Path
import tempfile
import unittest

from pixelblaze_mapper.madmapper_td_adapter import (
    ADAPTER_MARKER,
    adapt_material,
    prepared_shader_is_current,
    write_prepared_shader,
)


SIMPLE = r'''/*{
  "INPUTS": [
    {"NAME":"speed", "TYPE":"float", "DEFAULT":0.5},
    {"NAME":"color", "TYPE":"color", "DEFAULT":[1,0.25,0,1]},
    {"NAME":"mode", "TYPE":"long", "VALUES":["Soft Glow","Hard"], "DEFAULT":"Soft Glow", "FLAGS":"generate_as_define"}
  ],
  "GENERATORS": [{"NAME":"phase", "TYPE":"time_base", "PARAMS":{"speed":"speed"}}],
}*/
vec4 materialColorForPixel(vec2 uv) { return color * (0.5 + 0.5*sin(phase + uv.x)); }
'''


class AdapterTests(unittest.TestCase):
    def _material(self, root: Path, text: str = SIMPLE, name: str = "sample.fs") -> Path:
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_simple_material_is_wrapped_for_touchdesigner(self):
        with tempfile.TemporaryDirectory() as directory:
            result = adapt_material(self._material(Path(directory)))
        self.assertTrue(result.adaptable)
        self.assertIn(ADAPTER_MARKER, result.shader)
        self.assertIn("uniform vec4 uTDMaterial0", result.shader)
        self.assertIn("uniform vec4 uTDMaterial1", result.shader)
        self.assertIn("#define uTDTime uTDMaterial0.x", result.shader)
        self.assertIn("uniform vec4 uTDCoordinate", result.shader)
        self.assertIn("True global/panel-local/hybrid selection", result.shader)
        self.assertNotIn("vec2 localUV = fract(uv * panelCount)", result.shader)
        self.assertIn("mapMadMapperUV(vUV.st)", result.shader)
        self.assertIn("uniform vec4 uMMParam000; // native input: speed", result.shader)
        self.assertIn("#define speed (uMMParam000.x)", result.shader)
        self.assertIn("uniform vec4 uMMParam001; // native input: color", result.shader)
        self.assertIn("#define color (uMMParam001)", result.shader)
        self.assertIn("#define mode_IS_Soft_Glow", result.shader)
        self.assertEqual({"speed": "uMMParam000", "color": "uMMParam001"}, result.bindings)
        self.assertEqual(("speed", "color", "mode"), tuple(item.name for item in result.schema))
        self.assertIn("#define phase (uTDTime * (speed))", result.shader)
        self.assertIn("TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)))", result.shader)
        self.assertIn("float zoom = clamp(uTDMaterial0.w, 0.25, 8.0)", result.shader)
        self.assertIn("float scale = max(uTDMaterial0.y, 0.01) / 4.0", result.shader)
        self.assertIn("float width = clamp(uTDMaterial0.z, 0.01, 1.0)", result.shader)

    def test_prepared_shader_version_detects_stale_imports(self):
        self.assertFalse(prepared_shader_is_current("uniform float uTDTime;"))
        self.assertTrue(prepared_shader_is_current(ADAPTER_MARKER + "\nvoid main(){}"))

    def test_relaxed_madmapper_numbers_and_trailing_commas_keep_generators(self):
        source = r'''/*{
          "INPUTS": [{"NAME":"speed", "TYPE":"float", "DEFAULT":1.0, "MAX":360.,}],
          "GENERATORS": [{"NAME":"mat_time_source", "TYPE":"time_base", "PARAMS":{"speed":"speed",},}],
        }*/
        float phase = mat_time_source;
        vec4 materialColorForPixel(vec2 uv) { return vec4(fract(phase)); }
        '''
        with tempfile.TemporaryDirectory() as directory:
            result = adapt_material(self._material(Path(directory), source))
        self.assertTrue(result.adaptable, result.reasons)
        self.assertIn("uniform vec4 uMMParam000; // native input: speed", result.shader)
        self.assertIn("#define speed (uMMParam000.x)", result.shader)
        self.assertIn("#define mat_time_source (uTDTime * (speed))", result.shader)

    def test_native_inputs_get_independent_type_correct_uniforms(self):
        source = r'''/*{
          "INPUTS": [
            {"NAME":"speedA", "LABEL":"Layer A/Speed", "TYPE":"float", "DEFAULT":0.5},
            {"NAME":"speedB", "LABEL":"Layer B/Speed", "TYPE":"float", "DEFAULT":2.0},
            {"NAME":"steps", "TYPE":"int", "DEFAULT":7},
            {"NAME":"pulse", "TYPE":"event", "DEFAULT":0},
            {"NAME":"enabled", "TYPE":"bool", "DEFAULT":true},
            {"NAME":"mode", "TYPE":"long", "VALUES":["A","B"], "DEFAULT":"A"},
            {"NAME":"origin", "TYPE":"point2D", "DEFAULT":[0.25,0.75]},
            {"NAME":"size", "TYPE":"size2D", "DEFAULT":[1,2]},
            {"NAME":"range", "TYPE":"floatRange", "DEFAULT":[0.1,0.9]},
            {"NAME":"tint", "TYPE":"color", "DEFAULT":[1,0,0,1]}
          ]
        }*/
        vec4 materialColorForPixel(vec2 uv) { return tint; }
        '''
        with tempfile.TemporaryDirectory() as directory:
            result = adapt_material(self._material(Path(directory), source))
        self.assertTrue(result.adaptable, result.reasons)
        self.assertIn("#define speedA (uMMParam000.x)", result.shader)
        self.assertIn("#define speedB (uMMParam001.x)", result.shader)
        self.assertIn("#define steps (int(round(uMMParam002.x)))", result.shader)
        self.assertIn("#define pulse (int(round(uMMParam003.x)))", result.shader)
        self.assertIn("#define enabled (uMMParam004.x > 0.5)", result.shader)
        self.assertIn("#define mode (int(round(uMMParam005.x)))", result.shader)
        self.assertIn("#define origin (uMMParam006.xy)", result.shader)
        self.assertIn("#define size (uMMParam007.xy)", result.shader)
        self.assertIn("#define range (uMMParam008.xy)", result.shader)
        self.assertIn("#define tint (uMMParam009)", result.shader)
        self.assertEqual("Speed", result.schema[0].display_label)
        self.assertEqual("Speed", result.schema[1].display_label)
        self.assertEqual(("Layer A",), result.schema[0].groups)
        self.assertEqual(("Layer B",), result.schema[1].groups)

    def test_generate_as_define_uses_selected_compile_time_value(self):
        source = r'''/*{
          "INPUTS": [
            {"NAME":"mode", "TYPE":"long", "VALUES":["Soft Glow","Hard"],
             "DEFAULT":"Soft Glow", "FLAGS":"generate_as_define"},
            {"NAME":"quality", "TYPE":"int", "DEFAULT":2,
             "FLAGS":["generate_as_define"]},
            {"NAME":"enabled", "TYPE":"bool", "DEFAULT":false,
             "FLAGS":"generate_as_define"}
          ]
        }*/
        vec4 materialColorForPixel(vec2 uv) { return vec4(float(mode + quality)); }
        '''
        with tempfile.TemporaryDirectory() as directory:
            result = adapt_material(
                self._material(Path(directory), source),
                input_values={"mode": "Hard", "quality": 9, "enabled": True},
            )
        self.assertTrue(result.adaptable, result.reasons)
        self.assertIn("const int mode = 1;", result.shader)
        self.assertIn("#define mode_IS_Hard", result.shader)
        self.assertIn("const int quality = 9;", result.shader)
        self.assertIn("const bool enabled = true;", result.shader)
        self.assertIn("#define enabled_IS_true", result.shader)
        self.assertNotIn("uMMParam", result.shader)
        self.assertEqual({}, result.bindings)

    def test_known_include_is_inlined(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "MadCommon.glsl").write_text("float helper(float x) { return x; }", encoding="utf-8")
            shader = self._material(root, '/*{}*/\n#include "MadCommon.glsl"\nvec4 materialColorForPixel(vec2 uv){return vec4(helper(uv.x));}')
            result = adapt_material(shader)
        self.assertTrue(result.adaptable)
        self.assertIn("BEGIN MadCommon.glsl", result.shader)
        self.assertNotIn('#include "MadCommon.glsl"', result.shader)

    def test_missing_include_is_rejected_with_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            shader = self._material(Path(directory), '/*{}*/\n#include "missing.glsl"\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}')
            result = adapt_material(shader)
        self.assertFalse(result.adaptable)
        self.assertIn("missing include: missing.glsl", result.reasons)

    def test_vertex_material_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shader = self._material(root)
            (root / "sample.vs").write_text("void materialVsFunc(vec2 uv){}", encoding="utf-8")
            result = adapt_material(shader)
        self.assertIn("requires a MadMapper vertex shader", result.reasons)

    def test_texture_audio_feedback_and_varyings_are_rejected(self):
        cases = (
            ('/*{"INPUTS":[{"NAME":"fft","TYPE":"audioFFT"}]}*/\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}', "requires audiofft input"),
            ('/*{"IMPORTED":[{"NAME":"noise","PATH":"n.png"}]}*/\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}', "requires imported textures"),
            ('/*{"RASTERISATION_SETTINGS":{"REQUIRES_LAST_FRAME":true}}*/\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}', "requires previous-frame feedback"),
            ('/*{}*/\nin vec3 customData;\nvec4 materialColorForPixel(vec2 uv){return vec4(customData,1);}', "requires MadMapper-specific vertex/surface varyings"),
        )
        for source, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                result = adapt_material(self._material(Path(directory), source))
                self.assertTrue(any(reason in item for item in result.reasons))

    def test_unsupported_generator_is_rejected(self):
        source = '/*{"GENERATORS":[{"NAME":"x","TYPE":"animator"}]}*/\nvec4 materialColorForPixel(vec2 uv){return vec4(x);}'
        with tempfile.TemporaryDirectory() as directory:
            result = adapt_material(self._material(Path(directory), source))
        self.assertIn("unsupported generator: animator", result.reasons)

    def test_write_requires_successful_adaptation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = adapt_material(self._material(root))
            target = write_prepared_shader(result, root / "prepared" / "sample.frag")
            self.assertTrue(target.is_file())
            self.assertEqual(result.shader, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
