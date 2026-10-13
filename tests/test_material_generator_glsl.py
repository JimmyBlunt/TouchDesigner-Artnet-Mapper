"""Acceptance checks for documented stateless generator behavior; no GPU calls."""

import math
import unittest

from pixelblaze_mapper.material_generator_glsl import generator_expression


def evaluate(kind, params, values=None, **kwargs):
    definitions, reasons, warnings = generator_expression(
        {"NAME": "result", "TYPE": kind, "PARAMS": params}, **kwargs
    )
    assert not reasons, reasons
    assert not warnings, warnings
    expression = definitions[0].split(" = ", 1)[1].removesuffix(";")
    # The restricted helper emits only scalar literals, products and float casts.
    return eval(expression, {"__builtins__": {}, "float": float}, values or {})


class StatelessGeneratorTests(unittest.TestCase):
    def test_documented_multiplier_defaults_are_identity(self):
        self.assertEqual(evaluate("multiplier", {}), 1.0)
        for index in range(1, 5):
            self.assertEqual(evaluate("multiplier", {"value%d" % index: -2.5}), -2.5)

    def test_all_four_channels_contribute_without_clamping(self):
        self.assertEqual(evaluate("multiplier", dict(value1=-3, value2=2, value3=4, value4=0.5)), -12)
        self.assertEqual(evaluate("multiplier", dict(value1=0, value2=100)), 0)

    def test_official_demo_multiplier_tracks_its_live_input(self):
        params = dict(value1="mat_animator", value2=0.5, value3=1, value4=1)
        for sample in (-2, 0, 0.125, 0.5, 1, 2):
            self.assertEqual(evaluate("multiplier", params, {"mat_animator": sample}), sample * 0.5)

    def test_pass_thru_preserves_signed_values_and_does_not_scale(self):
        for sample in (-10.25, -0.0, 0, 0.5, 1, 400):
            self.assertEqual(evaluate("pass_thru", {"input_value": "source"}, {"source": sample}), sample)

    def test_scalar_boolean_and_integer_values_convert_to_float(self):
        for sample in (False, True, 17):
            self.assertEqual(evaluate("pass_thru", {"input_value": sample}), float(sample))
            self.assertEqual(evaluate("pass_thru", {"input_value": "input"}, {"input": sample}), float(sample))

    def test_external_bpm_and_audio_are_not_replaced_with_constants(self):
        for url in ("/custom/BPM/bpm", "/custom/BPM/bpmPos", "/audioin/MadMapper/amplitude"):
            definitions, reasons, warnings = generator_expression({"NAME": "result", "TYPE": "pass_thru", "PARAMS": {"input_value": url}})
            self.assertEqual(definitions, [])
            self.assertEqual(reasons, ["requires external channel: " + url])
            self.assertEqual(warnings, [])

    def test_explicit_external_binding_reads_real_uniform(self):
        for bpm in (60, 120, 137.5):
            self.assertEqual(evaluate("pass_thru", {"input_value": "/custom/BPM/bpm"}, {"actual_bpm": bpm}, channel_bindings={"/custom/BPM/bpm": "actual_bpm"}), bpm)

    def test_stateful_and_underdocumented_generators_stay_blocked(self):
        for kind in ("time_base", "animator", "incrementer", "damper", "adsr", "linear_filter", "ease_filter", "shaper"):
            definitions, reasons, _ = generator_expression({"NAME": "result", "TYPE": kind})
            self.assertFalse(definitions)
            self.assertTrue(reasons)

    def test_unknown_parameters_or_filters_are_not_silently_ignored(self):
        for g in ({"PARAMS": {"value1": 2, "value5": 8}}, {"FILTERS": {}}, {"PARAMS": []}):
            definitions, reasons, _ = generator_expression(dict(NAME="result", TYPE="multiplier", **g))
            self.assertFalse(definitions)
            self.assertTrue(reasons)

    def test_missing_pass_thru_input_does_not_invent_a_default(self):
        self.assertTrue(generator_expression({"NAME": "result", "TYPE": "pass_thru"})[1])

    def test_invalid_and_nonfinite_input_emit_no_glsl(self):
        for value in (None, [], {}, math.nan, math.inf, -math.inf, 10**1000, "x + 1", "x); discard;", "result"):
            definitions, reasons, _ = generator_expression({"NAME": "result", "TYPE": "pass_thru", "PARAMS": {"input_value": value}})
            self.assertFalse(definitions)
            self.assertTrue(reasons)

    def test_invalid_identifiers_and_channel_bindings_emit_no_glsl(self):
        for name in (None, "", "gl_value", "bad name", "float", "a;discard"):
            self.assertTrue(generator_expression({"NAME": name, "TYPE": "multiplier"})[1])
        self.assertTrue(generator_expression({"NAME": "result", "TYPE": "pass_thru", "PARAMS": {"input_value": "/x"}}, channel_bindings={"/x": "0.0"})[1])


if __name__ == "__main__":
    unittest.main()
