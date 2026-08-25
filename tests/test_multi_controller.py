import unittest
from dataclasses import replace
from pathlib import Path

from pixelblaze_mapper.multi_controller import (
    ARTNET_MAX_LINEAR_UNIVERSE,
    ControllerConfig,
    MultiControllerValidationError,
    RouterConfig,
    SegmentConfig,
    build_router_plan,
    controller_rows,
    default_router_config,
    segment_rows,
    validate_router,
)


def source(count=3744):
    return tuple(((index % 256) / 255, ((index + 1) % 256) / 255, ((index + 2) % 256) / 255) for index in range(count))


class DefaultTopologyTests(unittest.TestCase):
    def setUp(self):
        self.config = default_router_config("10.0.0.178")
        self.plan = build_router_plan(self.config)

    def test_safe_default_controller_values(self):
        ws, esp = self.config.controllers
        self.assertEqual((ws.target_address, esp.target_address), ("10.0.0.244", "10.0.0.251"))
        self.assertEqual((ws.local_interface, esp.local_interface), ("10.0.0.178", "10.0.0.178"))
        self.assertFalse(ws.enabled)
        self.assertFalse(esp.enabled)
        self.assertEqual((ws.start_universe, esp.start_universe), (0, 0))
        self.assertEqual((ws.brightness, esp.brightness), (0.02, 0.02))

    def test_default_spans_and_universe_counts(self):
        ws = self.plan.controller("WS2812_NODE")
        esp = self.plan.controller("APA102_ESP")
        # The physical controller reserves four complete 510-channel universe
        # blocks per side-panel port.  The upper and lower panels therefore
        # start at destination pixels 680 and 1360 rather than being packed
        # directly after the preceding panel.
        self.assertEqual((ws.destination_pixel_count, ws.universe_count), (1758, 11))
        self.assertEqual((esp.destination_pixel_count, esp.universe_count), (1679, 10))
        self.assertEqual(ws.routes[-1].active_pixel_count, 58)
        self.assertEqual(esp.routes[-1].active_pixel_count, 149)

    def test_same_universe_numbers_are_valid_on_different_ips(self):
        self.assertFalse(any(issue.blocking for issue in self.plan.issues))
        self.assertEqual(self.plan.controller("WS2812_NODE").routes[0].linear_universe, 0)
        self.assertEqual(self.plan.controller("APA102_ESP").routes[0].linear_universe, 0)

    def test_default_warns_only_about_unassigned_tail(self):
        warnings = [issue for issue in self.plan.issues if issue.severity == "warning"]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].code, "unassigned_source")
        self.assertIn("1184-1186", warnings[0].message)
        self.assertIn("2354-3743", warnings[0].message)

    def test_config_table_contracts(self):
        controllers = controller_rows(self.config)
        segments = segment_rows(self.config)
        self.assertEqual(controllers[0][0:4], ("enabled", "name", "target_ip", "local_interface"))
        self.assertEqual(controllers[1][0:3], (0, "WS2812_NODE", "10.0.0.244"))
        self.assertEqual(segments[1][0:5], ("WS_SIDE_MIDDLE", 0, 517, "WS2812_NODE", 0))
        self.assertEqual(segments[2][0:5], ("WS_SIDE_UPPER", 517, 269, "WS2812_NODE", 680))
        self.assertEqual(segments[3][0:5], ("WS_SIDE_LOWER", 786, 398, "WS2812_NODE", 1360))
        self.assertEqual(segments[4][0:5], ("APA102", 1187, 1167, "APA102_ESP", 512))


class PackingTests(unittest.TestCase):
    def test_fixed_510_slot_frames_and_zero_padding(self):
        plan = build_router_plan(default_router_config("10.0.0.178"))
        packed = plan.pack_pixels(source())
        self.assertTrue(all(len(frame) == 510 for frames in packed.values() for frame in frames))
        self.assertNotEqual(packed["WS2812_NODE"][-1][:-3], (0,) * 507)
        self.assertEqual(packed["WS2812_NODE"][-1][-3:], (0,) * 3)
        self.assertEqual(packed["APA102_ESP"][-1][447:], (0,) * 63)

    def test_esp_firmware_prefix_is_black(self):
        plan = build_router_plan(default_router_config("10.0.0.178"))
        frames = plan.pack_pixels(source())["APA102_ESP"]
        flattened = tuple(value for frame in frames for value in frame)
        self.assertEqual(flattened[: 512 * 3], (0,) * (512 * 3))
        expected = tuple(
            round(value * 255 * 0.02)
            for pixel in source()[1187:1190]
            for value in pixel
        )
        self.assertEqual(flattened[512 * 3 : 515 * 3], expected)

    def test_color_order_brightness_reverse_and_override(self):
        controller = ControllerConfig("A", "10.0.0.2", "10.0.0.1", color_order="GRB", brightness=0.5)
        config = RouterConfig(
            (controller,),
            (
                SegmentConfig("normal", 0, 1, "A", 0),
                SegmentConfig("reversed_override", 1, 2, "A", 1, reverse=True, color_override="BGR"),
            ),
            source_pixel_count=3,
            warn_unassigned=False,
        )
        frame = build_router_plan(config).pack_pixels(((1, 0.5, 0), (0, 0, 1), (1, 0, 0)))["A"][0]
        self.assertEqual(frame[:9], (64, 128, 0, 0, 0, 128, 128, 0, 0))

    def test_byte_input_mode_and_clamping(self):
        config = RouterConfig(
            (ControllerConfig("A", "10.0.0.2", "10.0.0.1", brightness=1),),
            (SegmentConfig("all", 0, 1, "A"),),
            source_pixel_count=1,
            warn_unassigned=False,
        )
        frame = build_router_plan(config).pack_pixels(((-1, 128, 999),), normalized=False)["A"][0]
        self.assertEqual(frame[:3], (0, 128, 255))

    def test_rejects_wrong_source_shape(self):
        plan = build_router_plan(default_router_config())
        with self.assertRaises(MultiControllerValidationError):
            plan.pack_pixels(((0, 0, 0),))
        malformed = [(0, 0, 0)] * 3744
        malformed[7] = (0, 0)
        with self.assertRaises(MultiControllerValidationError):
            plan.pack_pixels(malformed)


class ValidationTests(unittest.TestCase):
    def codes(self, config):
        return {issue.code for issue in validate_router(config)}

    def test_rejects_invalid_controller_fields(self):
        bad = ControllerConfig(
            "A", "not-ip", "10.0.0.999", enabled=1, port=0,
            start_universe=-1, color_order="RGG", brightness=1.1, rate=0,
            art_sync=1,
        )
        codes = self.codes(RouterConfig((bad,), (), warn_unassigned=False))
        self.assertTrue({"target_address", "local_interface", "enabled", "port", "start_universe", "color_order", "brightness", "rate", "art_sync"}.issubset(codes))

    def test_rejects_duplicates_unknowns_and_bad_segment_fields(self):
        controller = ControllerConfig("A", "10.0.0.2", "10.0.0.1")
        config = RouterConfig(
            (controller, controller),
            (
                SegmentConfig("bad", -1, 0, "missing", -2, reverse=1, color_override="RGBW"),
                SegmentConfig("bad", 3743, 2, "A"),
            ),
        )
        codes = self.codes(config)
        self.assertTrue({"duplicate_controller", "duplicate_segment", "source_start", "segment_count", "destination_start", "unknown_controller", "reverse", "color_override", "source_range"}.issubset(codes))

    def test_destination_overlap_blocks_but_source_fanout_warns(self):
        controller = ControllerConfig("A", "10.0.0.2", "10.0.0.1")
        segments = (
            SegmentConfig("one", 0, 10, "A", 0),
            SegmentConfig("two", 5, 10, "A", 5),
        )
        config = RouterConfig((controller,), segments, source_pixel_count=20, warn_unassigned=False)
        issues = validate_router(config)
        self.assertIn("destination_overlap", {issue.code for issue in issues if issue.blocking})
        self.assertIn("source_overlap", {issue.code for issue in issues if not issue.blocking})
        with self.assertRaises(MultiControllerValidationError):
            build_router_plan(config)

    def test_source_fanout_to_two_controllers_is_allowed(self):
        controllers = (
            ControllerConfig("A", "10.0.0.2", "10.0.0.1"),
            ControllerConfig("B", "10.0.0.3", "10.0.0.1"),
        )
        segments = (SegmentConfig("a", 0, 1, "A"), SegmentConfig("b", 0, 1, "B"))
        plan = build_router_plan(RouterConfig(controllers, segments, source_pixel_count=1))
        self.assertFalse(any(issue.blocking for issue in plan.issues))
        self.assertIn("source_overlap", {issue.code for issue in plan.issues})

    def test_same_universe_on_same_ip_is_rejected(self):
        controllers = (
            ControllerConfig("A", "10.0.0.2", "10.0.0.1"),
            ControllerConfig("B", "10.0.0.2", "10.0.0.1"),
        )
        segments = (SegmentConfig("a", 0, 1, "A"), SegmentConfig("b", 1, 1, "B"))
        config = RouterConfig(controllers, segments, source_pixel_count=2)
        self.assertIn("artnet_route_overlap", self.codes(config))

    def test_non_overlapping_universes_on_same_ip_are_allowed(self):
        controllers = (
            ControllerConfig("A", "10.0.0.2", "10.0.0.1", start_universe=0),
            ControllerConfig("B", "10.0.0.2", "10.0.0.1", start_universe=1),
        )
        segments = (SegmentConfig("a", 0, 1, "A"), SegmentConfig("b", 1, 1, "B"))
        config = RouterConfig(controllers, segments, source_pixel_count=2)
        self.assertNotIn("artnet_route_overlap", self.codes(config))

    def test_rejects_universe_overflow(self):
        controller = ControllerConfig("A", "10.0.0.2", "10.0.0.1", start_universe=ARTNET_MAX_LINEAR_UNIVERSE)
        config = RouterConfig((controller,), (SegmentConfig("all", 0, 171, "A"),), source_pixel_count=171)
        self.assertIn("universe_overflow", self.codes(config))

    def test_warning_can_be_disabled(self):
        config = replace(default_router_config(), warn_unassigned=False)
        self.assertNotIn("unassigned_source", self.codes(config))


class BuilderContractTests(unittest.TestCase):
    def test_embedded_packer_restores_project_import_path_after_reopen(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn('LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"', text)
        self.assertIn("if LOCAL_ROOT not in sys.path:", text)
        self.assertIn("sys.path.insert(0, LOCAL_ROOT)", text)

    def test_gico_sender_preserves_exact_510_byte_payloads(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("artnet_510_sender_callbacks", text)
        self.assertIn("payload = bytes(payload)", text)
        self.assertIn("pack.numSamples != 510", text)
        self.assertIn("for index in range(510)", text)
        self.assertIn("_socket.bind((locals_used[0], 6454))", text)
        self.assertIn("configs = _controllers(True)", text)
        self.assertIn("for config in configs:", text)
        self.assertIn("importlib.reload(effect_surface_uv)", text)
        self.assertIn("importlib.reload(spatial_map)", text)
        self.assertIn("importlib.reload(router_calibration)", text)

    def test_gico_sender_disables_sequence_filtering(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("b'\\x00\\x00'", text)
        self.assertIn("_packet(config['universe'] + offset, payload)", text)
        self.assertNotIn("_sequence = 1", text)
        self.assertNotIn("_packet(config['universe'] + offset, _sequence, payload)", text)

    def test_builder_is_isolated_and_never_activates_or_saves(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn('OWNER = "/project1/multi_controller_output"', text)
        self.assertIn('_set_if_present(output, "active", False)', text)
        self.assertIn('_set_if_present(output, "netport", controller.port)', text)
        self.assertIn('_set_if_present(output, "routingtable", routing.path)', text)
        self.assertIn("node.inputConnectors[0].disconnect()", text)
        self.assertIn("source.outputConnectors[0].connect(node)", text)
        self.assertIn('selectCHOP, "source_select"', text)
        self.assertIn('_set_if_present(source, "chop", SOURCE)', text)
        self.assertIn("scriptOp.numSamples = 510", text)
        self.assertNotIn("project.save(", text)
        self.assertNotIn("/project1/dmxout1", text)

    def test_builder_preserves_editable_tables_on_rerun(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("_read_existing_config(owner)", text)
        self.assertIn("if config is None:", text)
        self.assertIn("BLOCKED / DISABLED", text)

    def test_friendly_editor_exposes_both_receivers_and_safe_actions(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn('(("ws", config.controllers[0]', text)
        self.assertIn('("apa", config.controllers[1]', text)
        for suffix in ('"ip"', '"universe"', '"brightness"', '"enabled"'):
            self.assertIn(suffix, text)
        self.assertIn("APPLY SAFE DRAFT", text)
        self.assertIn("START ENABLED", text)
        self.assertIn("ALL OUTPUTS OFF", text)
        self.assertIn("START CALIBRATION", text)
        self.assertIn("NEXT PANEL", text)
        self.assertIn("NEXT PATTERN", text)
        self.assertIn("RETURN TO LIVE", text)

    def test_editor_validates_before_activation_and_defaults_to_off(self):
        text = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_multi_controller_output.py").read_text(encoding="utf-8")
        self.assertIn("ipaddress.ip_address(address)", text)
        self.assertIn("if not apply_safe():", text)
        self.assertIn("node.par.active = False", text)
        start = text[text.index("def start_enabled"):text.index("def start_calibration")]
        self.assertIn("all_off()", start)
        self.assertIn("sender.module.set_live()", start)
        self.assertIn("sender.module.set_enabled(True)", start)
        self.assertNotIn("node.par.active = True", start)


if __name__ == "__main__":
    unittest.main()
