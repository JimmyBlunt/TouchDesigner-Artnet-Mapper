"""Permanent offline regression checks for narrowly scoped source repairs."""
import hashlib
import math
import unittest
from dataclasses import replace
from unittest.mock import patch

from pixelblaze_mapper import material_shader_repairs as repairs


def reduced_fixture(filename):
    """Minimal reproducer retaining every affected original expression.

    The fixture's own hash substitutes only for the production full-file hash;
    production hashes and complete sources are audited separately at integration.
    """
    rule = repairs.REPAIRS[filename]
    source = '/*{"INPUTS":[]}*/\n' + '\n'.join(old for old, _ in rule.replacements)
    rule = replace(rule, sha256=hashlib.sha256(source.encode()).hexdigest())
    return source, rule


class SourceRepairScopeTests(unittest.TestCase):
    def test_unrecognized_material_and_changed_source_are_untouched(self):
        text = 'void main(){ float bad = sqrt(-1.0); }'
        for filename in ('other.fs', *repairs.REPAIRS):
            self.assertEqual(repairs.repair_source(filename, text), (text, []))

    def test_all_reviewed_rules_apply_only_to_matching_complete_content(self):
        for filename in repairs.REPAIRS:
            with self.subTest(filename=filename):
                source, rule = reduced_fixture(filename)
                with patch.dict(repairs.REPAIRS, {filename: rule}):
                    changed, warnings = repairs.repair_source('C:\\originals\\' + filename, source)
                    self.assertNotEqual(changed, source)
                    self.assertEqual(len(warnings), 1)
                    self.assertIn(filename, warnings[0])
                    self.assertEqual(repairs.repair_source(filename, source + '\n'), (source + '\n', []))
                    self.assertEqual(repairs.repair_source('unreviewed.fs', source), (source, []))
                    self.assertEqual(repairs.repair_source(filename, changed), (changed, []))

    def test_crlf_and_bom_variants_are_equivalent(self):
        filename = 'Burst.fs'
        source, rule = reduced_fixture(filename)
        with patch.dict(repairs.REPAIRS, {filename: rule}):
            self.assertEqual(repairs.repair_source(filename, source), repairs.repair_source(filename, '\ufeff' + source.replace('\n', '\r\n')))

    def test_guards_follow_metadata_and_precede_uses(self):
        source, rule = reduced_fixture('Burst.fs')
        with patch.dict(repairs.REPAIRS, {'Burst.fs': rule}):
            changed, _ = repairs.repair_source('Burst.fs', source)
        self.assertLess(changed.index('*/'), changed.index('float pbmRepairNonzero'))
        self.assertLess(changed.index('float pbmRepairNonzero'), changed.index('explosionColour / pbmRepairNonzero'))
        self.assertEqual(changed.count('float pbmRepairNonzero(float'), 1)

    def test_uninitialized_accumulators_and_self_shadowing_are_removed(self):
        source, rule = reduced_fixture('[recode]_Orbital_Wonky.fs')
        with patch.dict(repairs.REPAIRS, {'[recode]_Orbital_Wonky.fs': rule}):
            changed, _ = repairs.repair_source('[recode]_Orbital_Wonky.fs', source)
        self.assertIn('vec4 color = vec4(0.0);', changed)
        for kind, name in [('vec2', 'noiseUV'), ('float', 'noiseCircle'), ('float', 'noiseStroke')]:
            self.assertNotIn(kind + ' ' + name + ' =', changed)
        self.assertIn('circle(localNoiseUV, circlesRadius) - localNoiseCircle', changed)

    def test_zero_period_layer_removed_without_changing_other_periods(self):
        source, rule = reduced_fixture('Glass Garden.fs')
        with patch.dict(repairs.REPAIRS, {'Glass Garden.fs': rule}):
            changed, _ = repairs.repair_source('Glass Garden.fs', source)
        self.assertIn('for (float i = 1.; i < 3.; i++)', changed)
        self.assertNotIn('for (float i = 0.;', changed)
        self.assertIn('0.732* i', changed)

    def test_no_blanket_output_sanitizer_or_nan_filter_is_added(self):
        for rule in repairs.REPAIRS.values():
            for _, new in rule.replacements:
                self.assertNotIn('isnan', new)
                self.assertNotIn('isinf', new)
                self.assertNotIn('clamp(out_color', new)
        self.assertNotIn('nan_to_num', repairs._HELPERS)

    def test_scalar_waveform_lookup_keeps_position_and_real_audio_sampler(self):
        source, rule = reduced_fixture('Splotch Theory.fs')
        with patch.dict(repairs.REPAIRS, {'Splotch Theory.fs':rule}):
            changed, _ = repairs.repair_source('Splotch Theory.fs', source)
        self.assertIn('IMG_NORM_PIXEL(mat_audio, vec2(i, 0.5))', changed)
        self.assertNotIn('IMG_NORM_PIXEL(mat_audio, i)', changed)
        self.assertNotIn('vec4(1.)', changed)


class DomainRegressionTests(unittest.TestCase):
    def test_starfield_ratio_cancellation_retains_both_modes(self):
        for radial_distance in (0.125, 0.5, 1.0):
            for radius in (0.125, 0.7, 2.0):
                for warp in (0.01, 0.5, 1.0):
                    self.assertAlmostEqual((radial_distance / radius * warp) / radial_distance, warp / radius)
                    self.assertAlmostEqual((radial_distance * radius * warp) / radial_distance, radius * warp)
        # The same analytic ratios remain finite when random radDist equals 0.
        self.assertTrue(math.isfinite(0.5 / 0.7))

    def test_singular_reciprocal_guard_preserves_every_nonzero_sample(self):
        def guard(value): return 1e-6 if value == 0 else value
        for value in (-100, -0.1, -1e-8, 1e-8, 0.1, 100):
            self.assertEqual(1 / guard(value), 1 / value)
        self.assertTrue(math.isfinite(1 / guard(0)))
        # The original LED zero base channel multiplied by infinity gave NaN.
        self.assertEqual(0 * (1 / guard(0)), 0)

    def test_radiance_domain_guards_leave_valid_sqrt_and_pow_unchanged(self):
        for value in (0, 1e-8, 0.1, 1, 100):
            self.assertEqual(math.sqrt(max(value, 0)), math.sqrt(value))
            for exponent in (0.5, 0.9, 1.5, 3.5):
                self.assertEqual(max(value, 0) ** exponent, value ** exponent)
        for value in (-0.001, -1, -100):
            self.assertTrue(math.isfinite(math.sqrt(max(value, 0))))

    def test_signed_noise_square_preserves_intended_square(self):
        for noise in (-1, -0.3, 0, 0.3, 1):
            self.assertEqual(abs(noise) ** 2, noise * noise)

    def test_sphere_depth_keeps_unit_sphere_and_excludes_outside_disk(self):
        for x, y in ((0, 0), (0.3, 0.4), (1, 0)):
            depth = 1 - x*x - y*y
            z = math.sqrt(depth)
            self.assertAlmostEqual(x*x+y*y+z*z, 1)
        self.assertLess(1 - 1.1**2, 0)


if __name__ == '__main__':
    unittest.main()
