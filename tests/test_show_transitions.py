"""Contract tests for the extended Show Control transition set."""
import unittest

from pixelblaze_mapper.show_renderer import (
    TRANSITION_INFO,
    TRANSITIONS,
    render_frame,
    transition_b_weight,
    transition_gain_scale,
)
from pixelblaze_mapper.show_sequencer import TRANSITION_TYPES


COUNT = 240
U = tuple((index % 20) / 19.0 for index in range(COUNT))
V = tuple((index // 20) / 11.0 for index in range(COUNT))
SLOT_A = tuple([0.0] * COUNT for _ in range(3))
SLOT_B = tuple([1.0] * COUNT for _ in range(3))


def _frame(transition, mix):
    return render_frame(
        SLOT_A, SLOT_B, u=U, v=V, transition=transition, output_b_mix=mix,
        brightness=1.0, blackout=False, targets_a=('all',), targets_b=('all',),
        source_groups=(None,) * COUNT)


class TransitionSetTests(unittest.TestCase):
    def test_sequencer_and_renderer_agree(self):
        # The two modules never import each other; this is what keeps a show
        # that validates from hitting an unknown transition at render time.
        self.assertEqual(TRANSITION_TYPES, TRANSITIONS)

    def test_info_table_is_complete_and_unique(self):
        names = [name for name, _family, _label in TRANSITION_INFO]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), TRANSITIONS)
        for _name, family, label in TRANSITION_INFO:
            self.assertIn(family, {'blend', 'reveal'})
            self.assertTrue(label.strip())

    def test_endpoints_are_pure_a_and_pure_b(self):
        for name in sorted(TRANSITIONS):
            with self.subTest(name):
                self.assertEqual(max(_frame(name, 0.0)[0]), 0.0)
                self.assertEqual(min(_frame(name, 1.0)[0]), 1.0)

    def test_every_transition_actually_moves(self):
        # A reveal that never changes between the ends is a dead entry in the
        # menu; fade_black legitimately dips instead of revealing.
        for name in sorted(TRANSITIONS - {'cut'}):
            with self.subTest(name):
                middle = [sum(_frame(name, mix)[0]) / COUNT for mix in (0.25, 0.5, 0.75)]
                self.assertTrue(any(0.0 < value < 1.0 for value in middle), middle)

    def test_reveals_are_monotone_in_mix(self):
        for name in sorted(TRANSITIONS - {'glitch', 'fade_black'}):
            with self.subTest(name):
                totals = [sum(_frame(name, mix / 10.0)[0]) for mix in range(11)]
                for lower, upper in zip(totals, totals[1:]):
                    self.assertLessEqual(lower - 1e-9, upper)

    def test_fade_black_dips_and_recovers(self):
        self.assertEqual(transition_gain_scale('fade_black', 0.5), 0.0)
        self.assertEqual(transition_gain_scale('fade_black', 0.0), 1.0)
        self.assertEqual(transition_gain_scale('fade_black', 1.0), 1.0)
        self.assertEqual(transition_gain_scale('crossfade', 0.5), 1.0)
        self.assertEqual(max(_frame('fade_black', 0.5)[0]), 0.0)

    def test_burn_has_a_soft_edge(self):
        values = set(_frame('burn', 0.5)[0])
        self.assertTrue(values - {0.0, 1.0}, 'burn must produce partial weights')

    def test_per_led_helper_matches_frame_renderer(self):
        for name in sorted(TRANSITIONS):
            for mix in (0.0, 0.3, 0.5, 0.8, 1.0):
                frame = _frame(name, mix)[0]
                scale = transition_gain_scale(name, mix)
                for index in (0, 37, 119, COUNT - 1):
                    with self.subTest(name=name, mix=mix, index=index):
                        weight = transition_b_weight(name, mix, index, (U[index], V[index]))
                        self.assertAlmostEqual(frame[index], weight * scale, places=6)

    def test_unknown_transition_is_refused(self):
        with self.assertRaises(ValueError):
            _frame('swoosh', 0.5)

    def test_preview_shader_map_matches_renderer_order(self):
        # The GLSL preview addresses transitions by number. If the map and the
        # ordered info table drift, the wall and the preview run different
        # transitions and nothing raises.
        import re
        from pathlib import Path as _Path
        source = _Path(__file__).resolve().parents[1].joinpath(
            'pixelblaze_mapper/integrate_live_show.py').read_text(encoding='utf-8')
        body = re.search(r'TRANSITIONS = \{(.*?)\}', source, re.S).group(1)
        mapping = eval('{' + body + '}')
        expected = {name: index for index, (name, _f, _l) in enumerate(TRANSITION_INFO)}
        self.assertEqual(mapping, expected)
        marker = 'TRANSITION_SHADER = r' + "'''"
        shader = source.split(marker, 1)[1].split("'''", 1)[0]
        # The last mode is the trailing else, so it has no explicit test.
        for index in range(4, len(expected) - 1):
            self.assertIn('mode == %d' % index, shader)
        self.assertIn('else reveal =', shader)


if __name__ == '__main__':
    unittest.main()
