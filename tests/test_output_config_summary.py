"""Offline P0 contracts for the read-only Output Config summary."""

import ast
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "pixelblaze_mapper" / "output_config_summary.py"
BUILDER = ROOT / "pixelblaze_mapper" / "build_phase2_output_ui.py"


def load_model():
    spec = importlib.util.spec_from_file_location("output_config_summary_test", MODEL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OutputConfigSummaryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_model()
        self.controllers = ({
            "enabled": "1", "name": "WS2812_NODE", "target_ip": "10.0.0.244",
            "local_interface": "10.0.0.125", "port": "6454",
            "start_universe": "1", "color_order": "GRB", "brightness": "0.03",
            "rate": "60", "art_sync": "0",
            "reserved_universes": "12",
        },)
        self.segments = (
            {"controller": "WS2812_NODE", "destination_start": "0", "count": "517"},
            {"controller": "WS2812_NODE", "destination_start": "680", "count": "269"},
            {"controller": "WS2812_NODE", "destination_start": "1360", "count": "398"},
        )

    def test_summary_derives_live_values_without_a_draft(self):
        summary = self.module.build_output_summary(
            self.controllers, self.segments,
            {"enabled": True, "mode": "live", "error": "", "controllers": ["WS2812_NODE"]},
            source_pixels=3744,
        )
        self.assertEqual(summary.state, "LIVE")
        self.assertEqual(summary.source_pixels, 3744)
        controller = summary.controllers[0]
        self.assertEqual(controller.state, "LIVE")
        self.assertEqual(controller.pixel_capacity, 2040)
        self.assertEqual(controller.universe_count, 12)
        self.assertEqual(controller.universe_label, "U1-U12")
        self.assertEqual(controller.rate, 60)

    def test_sender_and_validation_errors_block_visible_state(self):
        summary = self.module.build_output_summary(
            self.controllers, self.segments,
            {"enabled": False, "mode": "error", "error": "socket failed", "controllers": []},
            source_pixels=None,
            validation_rows=({"severity": "error", "message": "invalid route"},),
        )
        self.assertEqual(summary.state, "BLOCKED")
        rows = dict(self.module.display_rows(summary))
        self.assertEqual(rows["SOURCE"], "unavailable")
        self.assertEqual(rows["VALIDATION"], "1 error(s)")
        self.assertEqual(rows["SENDER ERROR"], "socket failed")

    def test_configured_enabled_is_not_misreported_as_live(self):
        summary = self.module.build_output_summary(
            self.controllers, self.segments,
            {"enabled": False, "mode": "live", "error": "", "controllers": []},
            source_pixels=3744,
        )
        self.assertEqual(summary.state, "OUTPUT OFF")
        self.assertEqual(summary.controllers[0].state, "READY / SENDER OFF")

    def test_builder_is_read_only_single_authority_and_compiles(self):
        source = BUILDER.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('ROUTER = "/project1/multi_controller_output"', source)
        self.assertIn("controller_config", source)
        self.assertIn("segment_config", source)
        self.assertIn("sender.module.status()", source)
        self.assertIn("target.openViewer()", source)
        self.assertIn("canvas.viewer = True", source)
        self.assertIn("if int(frame) % 15:", source)
        for forbidden in (
            "config_draft", "universe_draft", "Reviewapply", "Revertdraft",
            "REVIEW & APPLY", "REVERT DRAFT", "project.save(", "set_enabled(True)",
        ):
            self.assertNotIn(forbidden, source)

    def test_derived_display_nodes_are_text_not_fields_or_parameters(self):
        source = BUILDER.read_text(encoding="utf-8")
        for name in ("state_value", "source_value", "sender_value", "controllers_value", "validation_value"):
            self.assertIn('_text(canvas, "%s"' % name, source)
        self.assertNotIn("fieldCOMP", source)
        self.assertNotIn("appendCustomPage", source)


if __name__ == "__main__":
    unittest.main()
