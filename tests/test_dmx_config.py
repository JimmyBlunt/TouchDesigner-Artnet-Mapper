import unittest
from dataclasses import replace

from pixelblaze_mapper.dmx_config import (
    ARTNET_MAX_LINEAR_UNIVERSE,
    ArtNetAddress,
    DiffClass,
    DmxConfig,
    DmxPlan,
    DmxValidationError,
    UniverseAllocation,
    allocate_dmx,
    build_plan,
    classify_diff,
    validate_config,
    validate_plan,
)


class AllocationTests(unittest.TestCase):
    def test_rgb_input_grb_output_defaults(self):
        config = DmxConfig(pixel_count=1)
        self.assertEqual(config.source_order, "RGB")
        self.assertEqual(config.output_order, "GRB")
        self.assertEqual(config.channels_per_pixel, 3)
        frame = build_plan(config).pack_pixels(((10, 20, 30),))[0]
        self.assertEqual(frame[:3], (20, 10, 30))
        self.assertEqual(frame[3:], (0,) * 507)

    def test_current_3714_pixel_baseline(self):
        plan = build_plan(DmxConfig(pixel_count=3714))
        self.assertEqual(plan.universe_count, 22)
        self.assertEqual(plan.last_pixel_count, 144)
        self.assertEqual(plan.flat_sample_count, 11142)
        self.assertEqual(plan.lookup_index_end, 11141)
        self.assertEqual(plan.universes[20].start_pixel, 3400)
        self.assertEqual(plan.universes[21].start_pixel, 3570)
        self.assertEqual(plan.universes[21].active_slots, 432)
        self.assertEqual(plan.universes[21].trailing_padding, 78)

    def test_ballsmatrix_938_slots(self):
        plan = build_plan(DmxConfig(pixel_count=938))
        self.assertEqual(plan.universe_count, 6)
        self.assertEqual([item.pixel_count for item in plan.universes], [170] * 5 + [88])
        self.assertEqual(plan.universes[-1].active_slots, 264)
        self.assertEqual(plan.universes[-1].trailing_padding, 246)

    def test_optional_start_channel_reduces_only_first_universe(self):
        plan = build_plan(DmxConfig(pixel_count=170, start_channel=4))
        self.assertEqual(plan.universe_count, 2)
        first, second = plan.universes
        self.assertEqual((first.start_channel, first.leading_padding), (4, 3))
        self.assertEqual((first.pixel_count, first.active_slots, first.trailing_padding), (169, 507, 0))
        self.assertEqual((second.start_channel, second.pixel_count), (1, 1))

    def test_every_packed_frame_is_510_and_padding_is_zero(self):
        config = DmxConfig(pixel_count=171, source_order="GRB", output_order="GRB")
        plan = build_plan(config)
        pixels = tuple((index, index + 1, index + 2) for index in range(171))
        frames = plan.pack_pixels(pixels)
        self.assertEqual([len(frame) for frame in frames], [510, 510])
        self.assertEqual(frames[0][-3:], pixels[169])
        self.assertEqual(frames[1][:3], pixels[170])
        self.assertEqual(frames[1][3:], (0,) * 507)

    def test_empty_map_has_no_universe_and_no_lookup_end(self):
        plan = build_plan(DmxConfig(pixel_count=0))
        self.assertEqual(plan.universes, ())
        self.assertIsNone(plan.lookup_index_end)


class AddressAndTableTests(unittest.TestCase):
    def test_artnet_address_decomposition(self):
        self.assertEqual(ArtNetAddress.from_linear(0), ArtNetAddress(0, 0, 0))
        self.assertEqual(ArtNetAddress.from_linear(15), ArtNetAddress(0, 0, 15))
        self.assertEqual(ArtNetAddress.from_linear(16), ArtNetAddress(0, 1, 0))
        self.assertEqual(ArtNetAddress.from_linear(256), ArtNetAddress(1, 0, 0))
        self.assertEqual(ArtNetAddress.from_linear(ARTNET_MAX_LINEAR_UNIVERSE).linear, ARTNET_MAX_LINEAR_UNIVERSE)
        with self.assertRaises(DmxValidationError):
            ArtNetAddress(0, 0, 16)

    def test_start_universe_offsets_routes_not_channel_names(self):
        plan = build_plan(DmxConfig(pixel_count=171, start_universe=15))
        self.assertEqual(plan.channel_names, ("Universe0", "Universe1"))
        self.assertEqual(plan.universes[0].address, ArtNetAddress(0, 0, 15))
        self.assertEqual(plan.universes[1].address, ArtNetAddress(0, 1, 0))

    def test_table_rows_match_touchdesigner_contract(self):
        plan = build_plan(DmxConfig(pixel_count=3714))
        dmx_rows = plan.dmx_universe_rows()
        routing = plan.routing_rows()
        self.assertEqual(len(dmx_rows), 23)
        self.assertEqual(dmx_rows[0], ("Universe", "index", "pixel"))
        self.assertEqual(dmx_rows[-1], (21, 3570, 144))
        self.assertEqual(len(routing), 23)
        self.assertEqual(routing[0], ("channel", "net", "subnet", "universe"))
        self.assertEqual(routing[16], ("Universe15", 0, 0, 15))
        self.assertEqual(routing[17], ("Universe16", 0, 1, 0))
        self.assertEqual(routing[-1], ("Universe21", 0, 1, 5))


class ValidationTests(unittest.TestCase):
    def test_rejects_bad_counts_orders_addresses_and_port(self):
        invalid = (
            DmxConfig(pixel_count=-1),
            DmxConfig(pixel_count=1, output_order="RGBW"),
            DmxConfig(pixel_count=1, output_order="RRG"),
            DmxConfig(pixel_count=1, start_channel=509),
            DmxConfig(pixel_count=1, payload_slots=513),
            DmxConfig(pixel_count=1, start_universe=-1),
            DmxConfig(pixel_count=1, target_address="not-an-ip"),
            DmxConfig(pixel_count=1, local_address="10.0.0.999"),
            DmxConfig(pixel_count=1, port=0),
            DmxConfig(pixel_count=1, payload_slots="510"),  # type: ignore[arg-type]
            DmxConfig(pixel_count=1, source_order=123),  # type: ignore[arg-type]
        )
        for config in invalid:
            with self.subTest(config=config):
                self.assertTrue(validate_config(config))
                with self.assertRaises(DmxValidationError):
                    build_plan(config)

    def test_rejects_artnet_range_overflow(self):
        config = DmxConfig(pixel_count=171, start_universe=ARTNET_MAX_LINEAR_UNIVERSE)
        self.assertIn("universe_overflow", {issue.code for issue in validate_config(config)})

    def test_plan_validator_detects_broken_total_and_padding(self):
        valid = build_plan(DmxConfig(pixel_count=1))
        broken_universe = replace(valid.universes[0], pixel_count=0, trailing_padding=506)
        broken = DmxPlan(valid.config, (broken_universe,))
        codes = {issue.code for issue in validate_plan(broken)}
        self.assertIn("pixel_total", codes)
        self.assertIn("active_slots", codes)
        self.assertIn("sample_count", codes)

    def test_pack_validates_pixel_and_channel_counts(self):
        plan = build_plan(DmxConfig(pixel_count=1))
        with self.assertRaises(DmxValidationError):
            plan.pack_pixels(())
        with self.assertRaises(DmxValidationError):
            plan.pack_pixels(((1, 2),))


class DiffTests(unittest.TestCase):
    def setUp(self):
        self.current = DmxConfig(pixel_count=3714)

    def test_unchanged_topology(self):
        self.assertEqual(classify_diff(self.current, replace(self.current)), DiffClass.UNCHANGED)
        noncontiguous = tuple(range(3713)) + (9999,)
        self.assertEqual(
            classify_diff(
                self.current,
                self.current,
                current_indices=noncontiguous,
                proposed_indices=noncontiguous,
            ),
            DiffClass.REINDEX,
        )

    def test_append(self):
        proposed = replace(self.current, pixel_count=3970)
        self.assertEqual(classify_diff(self.current, proposed), DiffClass.APPEND)

    def test_reindex_for_remove_insert_or_reorder(self):
        removed = replace(self.current, pixel_count=3713)
        self.assertEqual(classify_diff(self.current, removed), DiffClass.REINDEX)
        self.assertEqual(
            classify_diff(
                self.current,
                self.current,
                current_indices=(0, 1, 2) + tuple(range(3, 3714)),
                proposed_indices=(1, 0, 2) + tuple(range(3, 3714)),
            ),
            DiffClass.REINDEX,
        )

    def test_network_change_has_highest_priority(self):
        changed = replace(self.current, pixel_count=4000, target_address="10.0.0.245")
        self.assertEqual(classify_diff(self.current, changed), DiffClass.NETWORK)
        self.assertEqual(
            classify_diff(self.current, replace(self.current, output_order="RGB")),
            DiffClass.NETWORK,
        )


class UiAdapterTests(unittest.TestCase):
    def test_allocate_dmx_matches_ui_contract_and_is_discoverable(self):
        result = allocate_dmx(
            {
                "contract": "td.pixelblaze.output-config/v1",
                "pixel_count": 3714,
                "pixel_format": "rgb",
                "channel_order": "GRB",
                "start_universe": 0,
                "start_channel": 1,
                "target_address": "10.0.0.244",
                "local_address": "10.0.0.173",
                "port": 6454,
            }
        )
        self.assertEqual(result["pixel_count"], 3714)
        self.assertEqual(result["channels_required"], 11142)
        self.assertEqual(result["universe_count"], 22)
        self.assertEqual(result["last_universe_pixels"], 144)
        self.assertEqual(result["capacity_pixels"], 3740)
        self.assertEqual(result["issues"], [])
        self.assertEqual(
            result["rows"][-1],
            {
                "channel": "Universe21",
                "logical": 21,
                "net": 0,
                "subnet": 1,
                "universe": 5,
                "pixel_start": 3570,
                "pixel_count": 144,
                "dmx_start": 1,
                "dmx_end": 432,
                "state": "OK",
            },
        )
        from pixelblaze_mapper import allocate_dmx as public_allocator
        from pixelblaze_mapper.phase2_output_ui_contract import (
            build_with_shared_allocator,
            find_shared_allocator,
            OutputDraft,
        )

        self.assertIs(public_allocator, allocate_dmx)
        allocator, path = find_shared_allocator()
        self.assertIsNotNone(allocator)
        self.assertEqual(path, "pixelblaze_mapper.dmx_config.build_plan")
        normalized, _ = build_with_shared_allocator(OutputDraft())
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized.universe_count, 22)
        self.assertEqual(normalized.capacity_pixels, 3740)
        self.assertFalse(normalized.blocked)

    def test_allocate_dmx_returns_structured_blocking_issues(self):
        result = allocate_dmx(
            {
                "pixel_count": 1,
                "pixel_format": "rgb",
                "channel_order": "RGBW",
                "target_address": "bad-ip",
            }
        )
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["universe_count"], 0)
        self.assertTrue(result["issues"])
        self.assertTrue(all(issue["severity"] == "blocked" for issue in result["issues"]))
        self.assertTrue(all(set(issue) == {"severity", "code", "message", "field"} for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
