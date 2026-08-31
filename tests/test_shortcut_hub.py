import unittest
from pathlib import Path

from pixelblaze_mapper.shortcut_hub import SHORTCUTS, shortcut_rows, validate_shortcuts


class ShortcutHubTests(unittest.TestCase):
    def test_shortcuts_are_unique_and_scoped(self):
        self.assertEqual(validate_shortcuts(), ())
        self.assertEqual(len(SHORTCUTS), 10)

    def test_required_workflows_exist(self):
        by_key = {item.key: item for item in SHORTCUTS}
        self.assertEqual(by_key["1"].target, "/project1/LED_PREVIEW_OUT")
        self.assertEqual(by_key["6"].target, "/project1/multi_controller_output/ui_panel")
        self.assertEqual(by_key["2"].target, "/project1/material_browser")
        self.assertEqual(by_key["8"].target, "/project1/show_control/control_panel")
        self.assertEqual(by_key["0"].target, "/project1/multi_controller_output/gico_port_config/ui_panel")

    def test_table_contract(self):
        rows = shortcut_rows()
        self.assertEqual(rows[0], ("shortcut", "label", "target", "purpose"))
        self.assertEqual(rows[1][0], "Ctrl+Shift+1")

    def test_shortcuts_are_navigation_only(self):
        dangerous = ("dmxout", "active", "project.save", "destroy(")
        combined = " ".join(item.target + " " + item.purpose for item in SHORTCUTS).lower()
        self.assertTrue(all(token not in combined for token in dangerous))

    def test_builder_has_no_output_or_save_actions(self):
        source = (Path(__file__).parents[1] / "pixelblaze_mapper" / "build_shortcut_hub.py").read_text(encoding="utf-8").lower()
        self.assertIn("phase2_interaction_background_prototype/prototype_out", source)
        for token in ("dmxout", "netaddress", "project.save", "destroy("):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
