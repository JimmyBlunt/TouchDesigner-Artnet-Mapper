import json
from pathlib import Path
import tempfile
import unittest

from pixelblaze_mapper.show_sequencer import (
    ABSlotPlan,
    Cue,
    MaterialParameters,
    Show,
    ShowSequencer,
    ShowValidationError,
    TransportState,
    load_show,
    save_show,
)


def parameters(**changes):
    values = dict(
        speed=1.0, scale=4.0, width=0.3, focus_x=0.5, focus_y=0.5,
        zoom=1.0, gradient="neon_cyan_magenta",
        color_a=(0.91, 0.0, 1.0, 1.0), color_b=(0.0, 0.72, 0.86, 1.0),
        intensity=1.0, contrast=1.25, trail=0.55, direction=0.125,
        rotation_degrees=0.0, seed=0.0, effect_transition=0.5,
        panel_columns=2.0, panel_rows=5.0, hybrid_mix=0.5, density=1.25,
    )
    values.update(changes)
    return MaterialParameters(**values)


def cue(cue_id, duration=10.0, transition="crossfade", transition_duration=2.0):
    return Cue(
        id=cue_id,
        name="Cue " + cue_id,
        effect="Particles",
        preset="Cyan",
        parameters=parameters(),
        coordinate_mode="hybrid",
        duration=duration,
        transition=transition,
        transition_duration=transition_duration,
        brightness=0.2,
        target_groups=("middle", "rear"),
    )


def two_cue_show(loop=False):
    return Show(name="Test", cues=(cue("one"), cue("two", transition="cut", transition_duration=0)), loop=loop)


class ValidationTests(unittest.TestCase):
    def test_all_transition_and_coordinate_modes_are_accepted(self):
        transitions = ("cut", "crossfade", "dissolve", "wipe", "radial", "glitch")
        modes = ("global", "panel_local", "hybrid")
        for index, transition in enumerate(transitions):
            for mode in modes:
                item = Cue(
                    id=f"c{index}-{mode}", name="Valid", effect="Fluid Noise", preset="Default",
                    parameters=parameters(),
                    coordinate_mode=mode, duration=1.0, transition=transition,
                    transition_duration=0.0 if transition == "cut" else 0.5,
                    brightness=1.0, target_groups=("all",),
                )
                self.assertEqual(item.transition, transition)

    def test_rejects_invalid_cue_values(self):
        valid = cue("valid").to_dict()
        mutations = (
            {"id": ""}, {"coordinate_mode": "roomish"}, {"duration": 0},
            {"duration": float("inf")}, {"transition": "morph"},
            {"transition_duration": 11}, {"brightness": -0.1}, {"brightness": 1.1},
            {"target_groups": []}, {"target_groups": ["all", "all"]},
            {"target_groups": ["backwall"]}, {"target_groups": ["all", "rear"]},
        )
        for mutation in mutations:
            raw = dict(valid)
            raw.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ShowValidationError):
                Cue.from_dict(raw)

    def test_cut_and_animated_transition_duration_rules(self):
        with self.assertRaisesRegex(ShowValidationError, "cut"):
            cue("bad-cut", transition="cut", transition_duration=1)
        with self.assertRaisesRegex(ShowValidationError, "greater than 0"):
            cue("bad-fade", transition="wipe", transition_duration=0)

    def test_complete_material_parameters_round_trip_and_validate(self):
        item = parameters(speed=1.5, focus_x=0.25, zoom=2.0)
        self.assertEqual(MaterialParameters.from_dict(item.to_dict()), item)
        incomplete = item.to_dict()
        del incomplete["gradient"]
        with self.assertRaisesRegex(ShowValidationError, "missing"):
            MaterialParameters.from_dict(incomplete)
        invalid = item.to_dict()
        invalid["color_a"] = [1.0, 0.0, 0.0]
        with self.assertRaisesRegex(ShowValidationError, "RGBA"):
            MaterialParameters.from_dict(invalid)

    def test_strict_json_fields_and_unique_ids(self):
        raw = cue("one").to_dict()
        raw["surprise"] = True
        with self.assertRaisesRegex(ShowValidationError, "extra"):
            Cue.from_dict(raw)
        with self.assertRaisesRegex(ShowValidationError, "unique"):
            Show(name="Bad", cues=(cue("same"), cue("same")))
        show_raw = two_cue_show().to_dict()
        del show_raw["loop"]
        with self.assertRaisesRegex(ShowValidationError, "missing"):
            Show.from_dict(show_raw)


class TransportTests(unittest.TestCase):
    def test_exact_transition_and_cue_boundaries(self):
        sequencer = ShowSequencer(two_cue_show())
        sequencer.play()
        sequencer.advance(7.999)
        self.assertEqual(sequencer.plan().progress, 0.0)
        sequencer.advance(0.001)
        self.assertEqual(sequencer.elapsed, 8.0)
        self.assertEqual(sequencer.plan().progress, 0.0)
        sequencer.advance(1.0)
        self.assertAlmostEqual(sequencer.plan().progress, 0.5)
        sequencer.advance(1.0)
        self.assertEqual((sequencer.cue.id, sequencer.elapsed), ("two", 0.0))
        self.assertEqual(sequencer.plan().outgoing_slot, "B")

    def test_pause_resume_preserves_exact_position(self):
        sequencer = ShowSequencer(two_cue_show())
        sequencer.play()
        sequencer.advance(3.25)
        sequencer.pause()
        sequencer.advance(100)
        self.assertEqual((sequencer.state, sequencer.elapsed), (TransportState.PAUSED, 3.25))
        sequencer.play()
        sequencer.advance(0.75)
        self.assertEqual((sequencer.state, sequencer.elapsed), (TransportState.PLAYING, 4.0))

    def test_stop_resets_and_natural_end_stops_on_final_frame(self):
        sequencer = ShowSequencer(two_cue_show())
        sequencer.play()
        sequencer.advance(20.0)
        self.assertEqual(sequencer.state, TransportState.STOPPED)
        self.assertEqual((sequencer.cue.id, sequencer.elapsed), ("two", 10.0))
        sequencer.play()  # completed transport restarts from cue zero
        self.assertEqual((sequencer.cue.id, sequencer.elapsed), ("one", 0.0))
        sequencer.advance(1)
        sequencer.stop()
        self.assertEqual((sequencer.state, sequencer.cue_index, sequencer.elapsed),
                         (TransportState.STOPPED, 0, 0.0))

    def test_multi_boundary_advance_and_loop(self):
        sequencer = ShowSequencer(two_cue_show(loop=True))
        sequencer.play()
        sequencer.advance(25.5)
        self.assertEqual((sequencer.cue.id, sequencer.elapsed), ("one", 5.5))
        self.assertEqual(sequencer.state, TransportState.PLAYING)

    def test_next_previous_go_seek_and_loop_toggle(self):
        sequencer = ShowSequencer(two_cue_show())
        self.assertFalse(sequencer.previous())
        self.assertTrue(sequencer.go())
        self.assertEqual(sequencer.cue.id, "two")
        self.assertFalse(sequencer.next())
        self.assertTrue(sequencer.previous())
        sequencer.seek("two", 4.5)
        self.assertEqual((sequencer.cue_index, sequencer.elapsed), (1, 4.5))
        sequencer.seek(0, 1.25)
        self.assertEqual((sequencer.cue.id, sequencer.elapsed), ("one", 1.25))
        sequencer.set_loop(True)
        self.assertTrue(sequencer.previous())
        self.assertEqual(sequencer.cue.id, "two")
        with self.assertRaises(ShowValidationError):
            sequencer.seek("missing")
        with self.assertRaises(ShowValidationError):
            sequencer.seek(0, 10.0)

    def test_blackout_does_not_interrupt_transport(self):
        sequencer = ShowSequencer(two_cue_show())
        sequencer.play()
        sequencer.set_blackout(True)
        sequencer.advance(1.5)
        plan = sequencer.plan()
        self.assertTrue(plan.blackout)
        self.assertEqual(plan.brightness, 0.0)
        self.assertEqual((sequencer.state, sequencer.elapsed), (TransportState.PLAYING, 1.5))
        sequencer.toggle_blackout()
        self.assertAlmostEqual(sequencer.plan().brightness, 0.2)

    def test_ab_plan_has_slots_mix_and_targets(self):
        sequencer = ShowSequencer(two_cue_show())
        self.assertIsInstance(sequencer.plan(), ABSlotPlan)
        plan = sequencer.plan()
        self.assertEqual((plan.slot_a.id, plan.slot_b.id), ("one", "two"))
        self.assertEqual((plan.outgoing_slot, plan.incoming_slot), ("A", "B"))
        self.assertEqual((plan.transition, plan.output_b_mix), ("crossfade", 0.0))
        self.assertEqual(plan.target_groups, ("middle", "rear"))
        sequencer.seek(0, 9.0)
        self.assertEqual(sequencer.plan().output_b_mix, 0.5)

    def test_bad_advance_values_are_rejected(self):
        sequencer = ShowSequencer(two_cue_show())
        for value in (-1, float("nan"), True, "1"):
            with self.subTest(value=value), self.assertRaises(ShowValidationError):
                sequencer.advance(value)


class PersistenceAndBuilderTests(unittest.TestCase):
    def test_demo_show_loads_and_round_trips_exactly(self):
        project = Path(__file__).resolve().parents[1]
        demo = load_show(project / "shows" / "demo_show.json")
        self.assertEqual((demo.name, len(demo.cues), demo.loop), ("Core Effects Demo", 3, True))
        with tempfile.TemporaryDirectory() as temp:
            target = save_show(demo, Path(temp) / "nested" / "show.json")
            self.assertEqual(load_show(target), demo)
            self.assertFalse(target.with_suffix(".json.tmp").exists())

    def test_invalid_json_and_wrong_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text("{oops", encoding="utf-8")
            with self.assertRaises(ShowValidationError):
                load_show(path)
            wrong = two_cue_show().to_dict()
            wrong["schema_version"] = 3
            path.write_text(json.dumps(wrong), encoding="utf-8")
            with self.assertRaisesRegex(ShowValidationError, "schema_version"):
                load_show(path)

    def test_builder_is_import_safe_and_declares_isolation(self):
        import pixelblaze_mapper.build_show_sequencer as builder
        self.assertEqual(builder.OWNER, "/project1/show_control")
        source = Path(builder.__file__).read_text(encoding="utf-8")
        self.assertNotIn("project.save", source)
        self.assertNotIn("dmxout", source.lower())
        self.assertIn("productionTouched", source)
        self.assertIn("slot_a_adapter", source)
        self.assertIn("slot_b_adapter", source)
        self.assertIn("transition_adapter", source)
        self.assertIn("ShowSequencer", source)
        self.assertIn("sequence.next()", source)
        self.assertIn("show_runtime_record", source)


if __name__ == "__main__":
    unittest.main()
