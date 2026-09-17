"""Contract tests for the Show Control editing operations."""
import unittest

from pixelblaze_mapper import show_editor as editor
from pixelblaze_mapper.show_sequencer import Show, ShowValidationError


def _show(count=3):
    show = dict(editor.EMPTY_SHOW)
    parameters = editor.parameters_from_player({})
    for index in range(count):
        show = editor.append_cue(show, editor.new_cue(
            'Aurora', parameters, name='Cue %d' % (index + 1)))
    return show


class EditingTests(unittest.TestCase):
    def test_every_mutation_returns_a_runnable_show(self):
        show = _show()
        for mutate in (lambda s: editor.duplicate_cue(s, 0),
                       lambda s: editor.move_cue(s, 0, 1),
                       lambda s: editor.update_cue(s, 0, 'transition', 'iris'),
                       lambda s: editor.delete_cue(s, 0)):
            show = mutate(show)
            Show.from_dict(show)

    def test_ids_stay_unique_through_duplication(self):
        show = _show(1)
        for _ in range(4):
            show = editor.duplicate_cue(show, 0)
        ids = [cue['id'] for cue in show['cues']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_mutations_do_not_touch_the_input(self):
        show = _show()
        before = str(show)
        editor.delete_cue(show, 1)
        editor.update_cue(show, 0, 'duration', 99)
        self.assertEqual(str(show), before)

    def test_cut_forces_zero_transition_duration(self):
        show = editor.update_cue(_show(), 0, 'transition', 'cut')
        self.assertEqual(show['cues'][0]['transition_duration'], 0.0)

    def test_leaving_cut_restores_a_usable_transition_duration(self):
        show = editor.update_cue(_show(), 0, 'transition', 'cut')
        show = editor.update_cue(show, 0, 'transition', 'wipe_up')
        self.assertGreater(show['cues'][0]['transition_duration'], 0.0)

    def test_shortening_a_cue_clamps_its_transition(self):
        show = editor.update_cue(_show(), 0, 'transition_duration', 8.0)
        show = editor.update_cue(show, 0, 'duration', 2.0)
        cue = show['cues'][0]
        self.assertLessEqual(cue['transition_duration'], cue['duration'])
        Show.from_dict(show)

    def test_gradient_change_moves_both_colours(self):
        show = editor.update_cue(_show(), 0, 'gradient', 'fire_ice')
        parameters = show['cues'][0]['parameters']
        self.assertEqual(parameters['gradient'], 'fire_ice')
        self.assertAlmostEqual(parameters['color_a'][0], 1.0)
        self.assertAlmostEqual(parameters['color_b'][2], 1.0)

    def test_move_at_the_edges_is_a_no_op(self):
        show = _show()
        self.assertEqual(editor.move_cue(show, 0, -1)['cues'][0]['id'], show['cues'][0]['id'])
        last = len(show['cues']) - 1
        self.assertEqual(editor.move_cue(show, last, 1)['cues'][last]['id'], show['cues'][last]['id'])

    def test_unknown_values_are_refused(self):
        show = _show()
        for field, value in (('transition', 'swoosh'), ('coordinate_mode', 'sideways'),
                             ('gradient', 'chrome'), ('nonsense', 1)):
            with self.subTest(field=field):
                with self.assertRaises(ShowValidationError):
                    editor.update_cue(show, 0, field, value)

    def test_index_outside_the_show_is_refused(self):
        show = _show()
        for index in (-1, 3, 'first'):
            with self.subTest(index=index):
                with self.assertRaises(ShowValidationError):
                    editor.delete_cue(show, index)

    def test_empty_show_stays_editable(self):
        show = dict(editor.EMPTY_SHOW)
        self.assertEqual(editor.summary_rows(show), [])
        self.assertEqual(editor.total_duration(show), 0.0)
        show = editor.set_show_field(show, 'name', 'Abend')
        self.assertEqual(show['name'], 'Abend')


class PlayerCaptureTests(unittest.TestCase):
    def test_player_values_land_in_the_matching_fields(self):
        parameters = editor.parameters_from_player({
            'Speed': 0.8, 'Scale': 7.0, 'Density': 1.4, 'Seed': 12.0,
            'Gradientpreset': 'amber_violet', 'Rotation': 45.0})
        self.assertAlmostEqual(parameters['speed'], 0.8)
        self.assertAlmostEqual(parameters['scale'], 7.0)
        self.assertAlmostEqual(parameters['density'], 1.4)
        self.assertAlmostEqual(parameters['rotation_degrees'], 45.0)
        self.assertEqual(parameters['gradient'], 'amber_violet')

    def test_missing_player_controls_fall_back_to_defaults(self):
        parameters = editor.parameters_from_player({})
        cue = editor.new_cue('Fill', parameters)
        Show.from_dict(dict(editor.EMPTY_SHOW, cues=[cue]))

    def test_gradient_supplies_the_colours_when_the_player_omits_them(self):
        parameters = editor.parameters_from_player({'Gradientpreset': 'fire_ice'})
        self.assertAlmostEqual(parameters['color_a'][0], 1.0)
        self.assertAlmostEqual(parameters['color_a'][3], 1.0)

    def test_explicit_player_colours_win(self):
        parameters = editor.parameters_from_player({
            'Gradientpreset': 'fire_ice', 'Colorr': 0.25, 'Colorg': 0.5, 'Colorb': 0.75})
        self.assertAlmostEqual(parameters['color_a'][0], 0.25)
        self.assertAlmostEqual(parameters['color_a'][1], 0.5)

    def test_out_of_range_colours_are_clamped(self):
        parameters = editor.parameters_from_player({'Colorr': 4.0, 'Colorg': -2.0, 'Colorb': 0.5})
        self.assertEqual(parameters['color_a'][0], 1.0)
        self.assertEqual(parameters['color_a'][1], 0.0)

    def test_player_coordinate_names_map_to_schema_names(self):
        self.assertEqual(editor.PLAYER_COORDINATE_MODES['panel'], 'panel_local')
        for value in editor.PLAYER_COORDINATE_MODES.values():
            self.assertIn(value, editor.COORDINATE_ORDER)


class MenuTests(unittest.TestCase):
    def test_menu_orders_cover_the_validated_sets(self):
        from pixelblaze_mapper.show_sequencer import COORDINATE_MODES, TRANSITION_TYPES
        self.assertEqual(set(editor.TRANSITION_ORDER), TRANSITION_TYPES)
        self.assertEqual(set(editor.COORDINATE_ORDER), set(COORDINATE_MODES))
        self.assertTrue(all(editor.TRANSITION_LABELS[name] for name in editor.TRANSITION_ORDER))


if __name__ == '__main__':
    unittest.main()
