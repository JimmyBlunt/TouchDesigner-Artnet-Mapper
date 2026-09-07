import unittest
from pathlib import Path


SOURCE = (Path(__file__).parents[1] / "pixelblaze_mapper" / "integrate_live_show.py").read_text(encoding="utf-8")


class LiveShowIntegrationContractTests(unittest.TestCase):
    def test_visual_only_and_network_safe(self):
        self.assertIn("status = sender.module.status()", SOURCE)
        self.assertIn("controls.par.Source = selected_source", SOURCE)
        self.assertNotIn("set_enabled(", SOURCE)
        self.assertNotIn("dmxout", SOURCE.lower())
        self.assertNotIn("project.save(", SOURCE)

    def test_has_two_players_mixer_and_six_transitions(self):
        self.assertIn('"slot_a_player"', SOURCE)
        self.assertIn('"slot_b_player"', SOURCE)
        self.assertIn('"show_transition_mixer"', SOURCE)
        for name in ("cut", "crossfade", "dissolve", "wipe", "radial", "glitch"):
            self.assertIn("'%s'" % name, SOURCE)

    def test_exposes_show_as_third_visual_source(self):
        self.assertIn('["movie", "materials", "show"]', SOURCE)
        self.assertIn('root.create(selectTOP, "show_control_out")', SOURCE)


if __name__ == "__main__":
    unittest.main()
