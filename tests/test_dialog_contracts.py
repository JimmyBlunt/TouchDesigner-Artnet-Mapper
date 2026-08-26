"""Regression contracts for all nine shortcut-reachable dialogs.

The suite is deliberately non-destructive. It validates routing, builders and
test coverage without opening a viewer, changing the selected material,
rewriting a mapping, or sending Art-Net.
"""

from pathlib import Path
import unittest

from pixelblaze_mapper.dialog_contracts import DIALOGS, validate_dialog_contracts
from pixelblaze_mapper.shortcut_hub import SHORTCUTS


ROOT = Path(__file__).resolve().parents[1]


class DialogContractTests(unittest.TestCase):
    def test_all_nine_dialogs_have_a_stable_contract(self):
        self.assertEqual(validate_dialog_contracts(), ())
        self.assertEqual(len(DIALOGS), 9)

    def test_shortcut_hub_and_dialog_contracts_match_exactly(self):
        expected = [(item.key, item.label, item.target) for item in DIALOGS]
        actual = [(item.key, item.label, item.target) for item in SHORTCUTS]
        self.assertEqual(actual, expected)

    def test_every_implemented_dialog_has_its_builder_in_version_control(self):
        missing = [item.implementation for item in DIALOGS
                   if item.implementation and not (ROOT / item.implementation).is_file()]
        self.assertFalse(missing, "missing dialog implementations: " + repr(missing))

    def test_all_hardware_or_persistent_actions_are_explicitly_guarded(self):
        guarded = {action for item in DIALOGS for action in item.guarded_actions}
        for action in ("Output off", "Safe apply", "Start", "Kalibrierung",
                       "GO", "PLAY", "STOP", "BLACKOUT", "Import selected"):
            self.assertIn(action, guarded)

    def test_output_config_is_read_only_and_routes_edits_to_artnet_router(self):
        output = next(item for item in DIALOGS if item.key == "7")
        self.assertEqual(output.guarded_actions, ())
        self.assertIn("Live-Status lesen", output.safe_actions)
        self.assertIn("Art-Net Router öffnen", output.safe_actions)

    def test_shortcut_builder_is_navigation_only(self):
        source = (ROOT / "pixelblaze_mapper" / "build_shortcut_hub.py").read_text(encoding="utf-8").lower()
        for forbidden in ("project.save(", "dmxout", "netaddress", "destroy("):
            self.assertNotIn(forbidden, source)
