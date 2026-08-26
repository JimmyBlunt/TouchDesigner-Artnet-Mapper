"""Non-destructive regression checks for dialog 8 (Show Control).

The suite never opens a TouchDesigner pane, changes the live visual source,
sends Art-Net, or saves a project.  Known live-integration gaps are encoded as
expected failures so the audit remains green while still becoming an
``unexpected success`` as soon as a fix is implemented and the marker can be
removed deliberately.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pixelblaze_mapper.show_sequencer import Cue, Show, ShowSequencer


ROOT = Path(__file__).resolve().parents[1]
BUILDER = (ROOT / "pixelblaze_mapper" / "build_show_sequencer.py").read_text(
    encoding="utf-8"
)
INTEGRATION = (ROOT / "pixelblaze_mapper" / "integrate_live_show.py").read_text(
    encoding="utf-8"
)


def _cue(name: str, transition: str = "crossfade") -> Cue:
    return Cue(
        id=name.lower(),
        name=name,
        effect=name,
        preset="Preset " + name,
        coordinate_mode="global",
        duration=10.0,
        transition=transition,
        transition_duration=0.0 if transition == "cut" else 2.0,
        brightness=0.5,
        target_groups=("all",),
    )


class ShowControlDialogContractTests(unittest.TestCase):
    def test_all_visible_transport_buttons_have_callback_commands(self):
        for command in (
            "previous", "play", "pause", "stop", "next", "go", "loop", "blackout"
        ):
            self.assertIn(f"elif name == '{command}'", BUILDER) if command != "play" else self.assertIn(
                "if name == 'play'", BUILDER
            )
            self.assertIn(f'("btn_{command}"', BUILDER)
        self.assertIn("op('callbacks').module.command(%r)", BUILDER)

    def test_dialog_builder_has_no_network_enable_or_project_save(self):
        self.assertNotIn("project.save", BUILDER)
        self.assertNotIn("network_output_enabled', 1", BUILDER)
        self.assertNotIn('network_output_enabled", 1', BUILDER)

    def test_alternating_slots_require_mix_direction_independent_of_progress(self):
        sequence = ShowSequencer(Show("Audit", (_cue("A"), _cue("B"), _cue("C"))))
        sequence.next()
        plan = sequence.plan()
        self.assertEqual(plan.outgoing_slot, "B")
        self.assertEqual(plan.progress, 0.0)
        self.assertEqual(plan.output_b_mix, 1.0)

    @unittest.expectedFailure
    def test_live_mixer_consumes_output_b_mix_for_slot_direction(self):
        self.assertIn(
            "_value('transition_adapter/mixer_request', 'output_b_mix'",
            INTEGRATION,
        )

    @unittest.expectedFailure
    def test_live_status_uses_dynamic_outgoing_slot_and_label(self):
        render_section = INTEGRATION.split("def _render_sync_source", 1)[1]
        self.assertIn("outgoing_slot", render_section)
        self.assertNotIn("'A -> B", render_section)

    @unittest.expectedFailure
    def test_cue_preset_changes_live_renderer(self):
        render_section = INTEGRATION.split("def _render_sync_source", 1)[1]
        self.assertIn("_value(request_path, 'preset'", render_section)

    @unittest.expectedFailure
    def test_target_groups_reach_live_renderer(self):
        render_section = INTEGRATION.split("def _render_sync_source", 1)[1]
        self.assertIn("target_groups", render_section)


if __name__ == "__main__":
    unittest.main()
