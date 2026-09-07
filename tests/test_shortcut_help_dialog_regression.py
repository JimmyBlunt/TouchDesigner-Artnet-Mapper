"""Static regression coverage for dialog 9 (Shortcut Help).

The suite is deliberately non-destructive.  It does not open a viewer, inject
keyboard input, save TouchDesigner or touch output/network configuration.
Real focus and window behaviour is covered by the supervised live matrix in
``docs/SHORTCUT_HELP_REGRESSION_AUDIT_DE.md``.
"""

from pathlib import Path
import unittest

from pixelblaze_mapper.dialog_contracts import DIALOGS
from pixelblaze_mapper.shortcut_hub import SHORTCUTS, shortcut_rows, validate_shortcuts


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_shortcut_hub.py"
USER_DOC = ROOT / "docs" / "TOUCHDESIGNER_SHORTCUTS_DE.md"


class ShortcutHelpDialogRegressionTests(unittest.TestCase):
    def test_legacy_digits_preserved_and_three_unique_shortcuts_added(self):
        self.assertEqual(validate_shortcuts(), ())
        self.assertEqual([item.key for item in SHORTCUTS], list("1234567890lgc"))
        self.assertEqual(len({item.target for item in SHORTCUTS}), 13)

    def test_help_rows_match_all_dialog_contracts_exactly(self):
        # The original audit contract remains the ten numbered dialogs.
        help_rows = shortcut_rows()[1:11]
        expected = tuple(
            (f"Ctrl+Shift+{item.key}", item.label, item.target)
            for item in DIALOGS
        )
        actual = tuple(row[:3] for row in help_rows)
        self.assertEqual(actual, expected)

    def test_all_targets_are_navigation_scoped(self):
        for item in SHORTCUTS:
            with self.subTest(shortcut=item.combo):
                self.assertTrue(item.target.startswith("/project1/"))
                self.assertTrue(item.label.strip())
                self.assertTrue(item.purpose.strip())

    def test_builder_renders_every_visible_row(self):
        source = BUILDER.read_text(encoding="utf-8")
        for item in SHORTCUTS:
            with self.subTest(shortcut=item.combo):
                self.assertIn('"combo_" + item.key', source)
                self.assertIn('"name_" + item.key', source)
                self.assertIn('"purpose_" + item.key', source)
        self.assertIn("TOUCHDESIGNER SHORTCUTS", source)
        self.assertIn("Text-entry fields can consume keyboard input", source)

    def test_callback_has_missing_target_feedback_and_success_status(self):
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("Shortcut target missing:", source)
        self.assertIn("target.openViewer()", source)
        self.assertIn("ui.status = label + ' | ' + path", source)

    def test_shortcuts_do_not_contain_output_save_or_persistent_actions(self):
        source = BUILDER.read_text(encoding="utf-8").lower()
        forbidden = (
            "project.save(",
            "dmxout",
            "netaddress",
            "send_bytes",
            "destroy(",
            "import selected",
            "blackout",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_german_user_document_lists_every_shortcut_and_target_purpose(self):
        text = USER_DOC.read_text(encoding="utf-8")
        for item in SHORTCUTS:
            with self.subTest(shortcut=item.combo):
                self.assertIn(f"Strg+Umschalt+{item.key.upper()}", text)
                self.assertIn(item.label, text)


if __name__ == "__main__":
    unittest.main()
