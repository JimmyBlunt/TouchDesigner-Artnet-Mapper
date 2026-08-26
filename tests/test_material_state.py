"""Offline contracts for P1 material state and phase continuity."""

import ast
import json
import unittest
from dataclasses import replace
from pathlib import Path

from pixelblaze_mapper.material_state import MaterialSettings, MaterialStateStore


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "pixelblaze_mapper" / "build_p1_material_state.py"


class MaterialStateTests(unittest.TestCase):
    def test_speed_change_preserves_accumulated_phase(self):
        store = MaterialStateStore()
        store.activate("core:plasma", 10.0, initial=MaterialSettings(speed=1.0))
        self.assertEqual(store.phase_at(12.0), 2.0)
        store.set_active_settings(replace(store.state("core:plasma").settings, speed=2.0), 12.0)
        self.assertEqual(store.phase_at(13.0), 4.0)
        # The former absTime*speed formula would jump to 24 at t=12.
        self.assertNotEqual(store.phase_at(13.0), 26.0)

    def test_global_master_speed_defaults_to_one_and_changes_continuously(self):
        store = MaterialStateStore()
        self.assertEqual(store.global_master_speed, 1.0)
        store.activate("core:fire", 0.0, initial=MaterialSettings(speed=2.0))
        self.assertEqual(store.phase_at(2.0), 4.0)
        store.set_global_master_speed(0.5, 2.0)
        self.assertEqual(store.phase_at(4.0), 6.0)

    def test_each_material_restores_all_approved_settings_and_its_phase(self):
        first = MaterialSettings(
            speed=0.5, scale=7.0, width=0.2, focus_x=0.1, focus_y=0.9,
            zoom=2.0, gradient="fire_ice", color_a=(1, 0.1, 0.02, 1),
            color_b=(0, 0.8, 1, 1), coordinate_mode="panel",
        )
        second = MaterialSettings(speed=2.0, scale=3.0, coordinate_mode="hybrid")
        store = MaterialStateStore()
        store.activate("core:fire", 0.0, initial=first)
        store.phase_at(2.0)
        store.activate("core:plasma", 2.0, initial=second)
        store.phase_at(3.0)
        restored = store.activate("core:fire", 3.0)
        self.assertEqual(restored.settings, first)
        self.assertEqual(restored.phase, 1.0)

    def test_json_roundtrip_preserves_materials_and_master(self):
        store = MaterialStateStore(global_master_speed=0.75)
        store.activate("madmapper:test", 4.0, initial=MaterialSettings(zoom=1.5))
        store.phase_at(6.0)
        copy = MaterialStateStore.from_dict(json.loads(json.dumps(store.to_dict())))
        self.assertEqual(copy.to_dict(), store.to_dict())

    def test_restart_rebases_clock_without_advancing_persisted_phase(self):
        store = MaterialStateStore()
        store.activate("core:matrix_rain", 10.0, initial=MaterialSettings(speed=1.5))
        self.assertEqual(store.phase_at(12.0), 3.0)
        restarted = MaterialStateStore.from_dict(
            json.loads(json.dumps(store.to_dict()))
        )

        rebased = restarted.rebase_active(10_000.0)

        self.assertIsNotNone(rebased)
        self.assertEqual(rebased.phase, 3.0)
        self.assertEqual(rebased.last_time, 10_000.0)
        self.assertEqual(restarted.phase_at(10_001.0), 4.5)

    def test_td_initialize_rebases_a_restored_current_material(self):
        text = BUILDER.read_text(encoding="utf-8")
        self.assertIn("state = STORE.rebase_active(_now())", text)
        self.assertLess(
            text.index("state = STORE.rebase_active(_now())"),
            text.index("_apply(state.settings)"),
        )

    def test_builder_is_valid_idempotent_and_output_isolated(self):
        text = BUILDER.read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn('"Globalmasterspeed", "Global Master Speed", 1.0', text)
        self.assertIn("material_state_runtime", text)
        self.assertIn("material_state_table", text)
        self.assertIn("parameterexecuteDAT", text)
        self.assertIn("executeDAT", text)
        self.assertIn("material_control_surface.op = op", text)
        self.assertIn("if parameter is not None else 1.0", text)
        self.assertIn("parameter = getattr(CONTROLS.par, 'Color' + suffix, None)", text)
        self.assertIn('player.par.vec0valuey.expr = "op(\'/project1/material_state_runtime\').module.phase()"', text)
        self.assertNotIn("project.save", text)
        self.assertNotIn("dmxout", text.lower())
        self.assertNotIn("artnet", text.lower())


if __name__ == "__main__":
    unittest.main()
