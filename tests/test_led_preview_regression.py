"""Static regression contracts for shortcut dialog 1, LED Preview.

The tests never open TouchDesigner, modify a mapping, save a project or send
Art-Net.  Known Core-68 defects are marked as expected failures until the user
approves their correction after the analysis phase.
"""

from pathlib import Path
import unittest

from pixelblaze_mapper.shortcut_hub import SHORTCUTS


ROOT = Path(__file__).resolve().parents[1]
SHORTCUT_BUILDER = ROOT / "pixelblaze_mapper" / "build_shortcut_hub.py"
RESTORE = ROOT / "pixelblaze_mapper" / "restore_photo_calibration.py"


class LedPreviewRegressionTests(unittest.TestCase):
    def test_dialog_one_targets_the_canonical_preview(self):
        preview = next(item for item in SHORTCUTS if item.key == "1")
        self.assertEqual(preview.label, "LED PREVIEW")
        self.assertEqual(preview.target, "/project1/LED_PREVIEW_OUT")

    def test_preview_restore_is_non_destructive(self):
        source = RESTORE.read_text(encoding="utf-8").lower()
        for forbidden in ("project.save", "dmxout", "netaddress"):
            self.assertNotIn(forbidden, source)
        self.assertIn('"networkchanged": false', source)

    def test_ten_independent_rear_panels_are_declared(self):
        source = RESTORE.read_text(encoding="utf-8")
        self.assertIn("PANEL_COUNT = REAR_PANEL_COUNT", source)
        self.assertIn("PANEL_SIZE = REAR_PANEL_PIXELS", source)
        self.assertIn("PANEL_COUNT * 8", source)

    def test_keyboard_in_declares_the_runtime_proven_keyevent_contract(self):
        source = SHORTCUT_BUILDER.read_text(encoding="utf-8")
        self.assertIn("def keyEvent(", source)
        self.assertIn("target.openViewer()", source)
        self.assertIn("ui.status = label + ' | ' + path", source)

    def test_preview_contract_covers_all_3744_current_leds(self):
        source = RESTORE.read_text(encoding="utf-8")
        self.assertIn("source.numSamples != TOTAL_PIXELS", source)

    def test_rear_start_follows_the_current_1184_side_leds(self):
        source = RESTORE.read_text(encoding="utf-8")
        self.assertIn("REAR_START = REAR.start", source)


if __name__ == "__main__":
    unittest.main()
