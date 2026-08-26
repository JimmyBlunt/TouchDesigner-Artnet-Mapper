import unittest
from time import perf_counter

from pixelblaze_mapper.show_renderer import (
    normalize_target_groups,
    render_frame,
    render_led,
    target_mask,
    transition_b_weight,
)


class ShowRendererContractTests(unittest.TestCase):
    def test_exact_canonical_panel_boundaries(self):
        expectations = (
            ("middle", 0, 516), ("upper", 517, 785),
            ("lower", 786, 1183), ("rear", 1184, 3743),
        )
        for group, first, last in expectations:
            self.assertEqual(target_mask((group,), first), 1.0)
            self.assertEqual(target_mask((group,), last), 1.0)
            for other in {0, 517, 786, 1184, 3743} - {first, last}:
                if not first <= other <= last:
                    self.assertEqual(target_mask((group,), other), 0.0)

    def test_all_and_combined_groups_validate(self):
        self.assertEqual(target_mask(("all",), 2345), 1.0)
        self.assertEqual(normalize_target_groups(("middle", "rear")), ("middle", "rear"))
        with self.assertRaises(ValueError):
            normalize_target_groups(("all", "rear"))
        with self.assertRaises(ValueError):
            normalize_target_groups(("backwall",))

    def test_alternating_b_direction_is_independent_of_progress(self):
        self.assertEqual(transition_b_weight("crossfade", 1.0, 0, (0.5, 0.5)), 1.0)
        color = render_led(
            (10.0, 20.0, 30.0), (100.0, 120.0, 140.0), led_index=0,
            uv=(0.5, 0.5), transition="crossfade", output_b_mix=1.0,
            brightness=1.0, blackout=False,
            targets_a=("all",), targets_b=("all",),
        )
        self.assertEqual(color, (100.0, 120.0, 140.0))

    def test_each_slot_is_masked_before_transition(self):
        middle = render_led(
            (100.0, 0.0, 0.0), (0.0, 100.0, 0.0), led_index=0,
            uv=(0.5, 0.5), transition="crossfade", output_b_mix=0.5,
            brightness=1.0, blackout=False,
            targets_a=("middle",), targets_b=("rear",),
        )
        rear = render_led(
            (100.0, 0.0, 0.0), (0.0, 100.0, 0.0), led_index=1184,
            uv=(0.5, 0.5), transition="crossfade", output_b_mix=0.5,
            brightness=1.0, blackout=False,
            targets_a=("middle",), targets_b=("rear",),
        )
        self.assertEqual(middle, (50.0, 0.0, 0.0))
        self.assertEqual(rear, (0.0, 50.0, 0.0))

    def test_blackout_is_final_gain_and_does_not_change_mix(self):
        result = render_led(
            (100.0, 100.0, 100.0), (20.0, 20.0, 20.0), led_index=517,
            uv=(0.5, 0.5), transition="crossfade", output_b_mix=0.25,
            brightness=0.7, blackout=True,
            targets_a=("all",), targets_b=("all",),
        )
        self.assertEqual(result, (0.0, 0.0, 0.0))

    def test_bulk_frame_matches_reference_for_every_transition(self):
        count = 3744
        slot_a = ([10.0 + i % 7 for i in range(count)], [20.0] * count, [30.0] * count)
        slot_b = ([100.0] * count, [110.0 + i % 5 for i in range(count)], [120.0] * count)
        u = [i / (count - 1) for i in range(count)]
        v = [(i % 64) / 63 for i in range(count)]
        for transition in ("cut", "crossfade", "dissolve", "wipe", "radial", "glitch"):
            bulk = render_frame(
                slot_a, slot_b, u=u, v=v, transition=transition,
                output_b_mix=0.37, brightness=0.6, blackout=False,
                targets_a=("middle", "rear"), targets_b=("upper", "lower"),
            )
            for index in (0, 516, 517, 785, 786, 1183, 1184, 2345, 3743):
                reference = render_led(
                    tuple(channel[index] for channel in slot_a),
                    tuple(channel[index] for channel in slot_b),
                    led_index=index, uv=(u[index], v[index]), transition=transition,
                    output_b_mix=0.37, brightness=0.6, blackout=False,
                    targets_a=("middle", "rear"), targets_b=("upper", "lower"),
                )
                for actual, expected in zip(
                    (channel[index] for channel in bulk), reference
                ):
                    self.assertAlmostEqual(actual, expected, places=12)

    def test_bulk_crossfade_hot_path_has_large_performance_margin(self):
        count = 3744
        slot_a = ([10.0] * count, [20.0] * count, [30.0] * count)
        slot_b = ([100.0] * count, [110.0] * count, [120.0] * count)
        u, v = [0.5] * count, [0.5] * count
        kwargs = dict(
            u=u, v=v, transition="crossfade", output_b_mix=0.5,
            brightness=0.8, blackout=False,
            targets_a=("all",), targets_b=("rear",),
        )
        render_frame(slot_a, slot_b, **kwargs)
        started = perf_counter()
        for _ in range(10):
            render_frame(slot_a, slot_b, **kwargs)
        average_ms = (perf_counter() - started) * 100.0
        # Loose CI guard; the local benchmark is ~1.8 ms. A regression to the
        # former ~15 ms per-pixel call path fails with ample machine variance.
        self.assertLess(average_ms, 8.0)


if __name__ == "__main__":
    unittest.main()
