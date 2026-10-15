"""Real transport -> editor hooks -> A/B uniforms -> mixer, without live TD."""
import ast
from copy import deepcopy
from dataclasses import replace
from enum import Enum
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from pixelblaze_mapper import show_overlap_runtime as overlap, show_automation as auto
from pixelblaze_mapper import show_midi, mk2_td
from pixelblaze_mapper.show_renderer import render_frame
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer
from pixelblaze_mapper.show_timeline import install_editor_source, install_sync_source
from pixelblaze_mapper.show_sync_fastpath import install_callback_source
from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
from pixelblaze_mapper.integrate_live_show import _render_sync_source, LED_RENDER_CALLBACK
from pixelblaze_mapper.madmapper_parameters import parameter_schema, default_values, uniform_vector
from tests.test_show_sequencer import cue


def transport_source():
    path = Path(__file__).resolve().parents[1] / 'pixelblaze_mapper/build_show_sequencer.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    return next(n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
                and n.value.value.startswith('# Isolated transport UI callbacks;'))


class Mode(Enum):
    CONSTANT = 'constant'


class Par:
    def __init__(self, value=0.):
        self.val, self.mode = value, Mode.CONSTANT
        self.sequence = NS(numBlocks=3)

    def eval(self):
        return self.val


class Pars:
    def __init__(self):
        object.__setattr__(self, 'values', {})

    def __getattr__(self, key):
        par = self.values.setdefault(key, Par())
        par.name = key
        return par

    def __setattr__(self, key, value):
        self.__getattr__(key).val = value

    def __getitem__(self, key):
        return self.__getattr__(key)


class Node:
    def __init__(self, nodes, path, text=''):
        self.nodes, self.path, self.name = nodes, path, path.rsplit('/', 1)[-1]
        self.text, self.par, self.storage = text, Pars(), {}
        self.rows = [['key', 'value']]
        nodes[path] = self

    def op(self, name):
        return self.nodes.get(self.path+'/'+name)

    @property
    def customPars(self):
        return list(self.par.values.values())

    def parent(self):
        return self.nodes[self.path.rsplit('/', 1)[0]]

    def store(self, key, value):
        self.storage[key] = value

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def unstore(self, key):
        self.storage.pop(key, None)

    @property
    def numRows(self):
        return len(self.rows)

    def __getitem__(self, cell):
        row, column = cell
        return self.rows[row][column]

    def __setitem__(self, cell, value):
        row, column = cell
        self.rows[row][column] = str(value)

    def appendRow(self, row):
        self.rows.append(list(map(str, row)))

    def clear(self):
        self.text = ''

    def write(self, text):
        self.text += text


class Rig:
    """Executes full generated sources; replaces only native objects/GPU compile."""
    def __init__(self, imported=False, legacy=False):
        self.nodes = {}
        self.owner = Node(self.nodes, '/project1/show_control')
        for name in ('control_panel', 'editor_state', 'state_table', 'show_json', 'automation_json',
                     'imported_json', 'callbacks', 'editor_callbacks', 'render_sync',
                     'show_transition_mixer', 'show_led_renderer_callbacks', 'show_transition_fs'):
            Node(self.nodes, self.owner.path+'/'+name)
        first = replace(cue('one'), fade_out=2., brightness=.8, target_groups=('all',))
        second = replace(cue('two', transition='cut', transition_duration=0),
                         fade_in=2., brightness=.4, target_groups=('all',))
        if imported:
            first, second = replace(first, effect='madmapper:m'), replace(second, effect='madmapper:m')
        self.show = Show(name='Overlap integration', cues=(first, second), timing_mode='legacy' if legacy else 'overlap')
        self.sequence = ShowSequencer(self.show)
        self.owner.op('show_json').text = json.dumps(self.show.to_dict())
        self.owner.op('automation_json').text = json.dumps(auto.empty())
        self.owner.op('imported_json').text = '{}'
        self.schema = parameter_schema({'INPUTS': [
            {'NAME': 'gain', 'TYPE': 'float', 'MIN': 0, 'MAX': 4, 'DEFAULT': 1},
            {'NAME': 'enabled', 'TYPE': 'bool', 'DEFAULT': True},
            {'NAME': 'colour', 'TYPE': 'color', 'DEFAULT': [.1, .2, .3, 1]},
        ]})
        self.defaults = default_values(self.schema)
        self.adaptation = NS(schema=self.schema, shader='void main() {}')
        self.native_live = 1.
        self.library = NS(_items=[{'id': 'm', 'label': 'Native material'}],
            _parameter_context=lambda item: (self.adaptation, deepcopy(self.defaults)),
            _configure_parameter_uniforms=self.configure,
            parameter_snapshot=lambda: {'parameters': [{'name': 'gain', 'value': self.native_live}]})
        Node(self.nodes, '/project1/madmapper_library/runtime').module = self.library
        Node(self.nodes, '/project1/material_state_runtime').module = NS(phase=lambda: 12345.)
        controls = Node(self.nodes, '/project1/madmapper_player_controls')
        controls.par.Source.val = 'show'
        controls.par.Speed.val = 1.
        controls.par.Scale.val = 99.
        self.protected_controls = {'Source': 'show', 'Speed': 1., 'Scale': 99.}
        for slot in ('a', 'b'):
            for suffix in ('player', 'import', 'import_fs', 'mux'):
                Node(self.nodes, self.owner.path+'/slot_'+slot+'_'+suffix)
            for name in ('material_request', 'coordinate_request'):
                Node(self.nodes, self.owner.path+'/slot_'+slot+'_adapter/'+name)
        Node(self.nodes, self.owner.path+'/transition_adapter/mixer_request')
        self.editor_scope = self.exec_source(install_editor_source(EDITOR_RUNTIME), 'editor_callbacks', project=NS(folder=str(Path.cwd())))
        self.transport_scope = self.exec_source(install_sync_source(install_callback_source(transport_source())), 'callbacks')
        self.transport_scope['_runtime_record'] = (self.owner.op('show_json').text, self.sequence)
        self.render_scope = self.exec_source(_render_sync_source([{'id': 'particles', 'index': 0, 'label': 'Particles', 'preset': 'Cyan'}]), 'render_sync')
        self.render_scope['sync_feedback'] = lambda: None  # UI feedback is outside this render contract.
        self.owner.op('show_led_renderer_callbacks').text = LED_RENDER_CALLBACK

    def resolve(self, path):
        return self.nodes.get(path if path.startswith('/') else self.owner.path+'/'+path)

    def exec_source(self, source, name, **extra):
        scope = dict(op=self.resolve, **extra)
        exec(compile(source, '<generated '+name+'>', 'exec'), scope)
        self.owner.op(name).text = source
        self.owner.op(name).module = NS(**scope)
        return scope

    def configure(self, renderer, adaptation, values, publish_schema=False):
        assert not publish_schema
        for parameter in adaptation.schema:
            for suffix, value in zip('xyzw', uniform_vector(parameter, values[parameter.name])):
                getattr(renderer.par, 'vec%dvalue%s' % (3+parameter.index, suffix)).val = value

    def automation(self, tracks):
        data = auto.empty()
        for cue_id, values in tracks.items():
            data = auto.merge(data, cue_id, values)
        self.owner.op('automation_json').text = json.dumps(data)
        return data

    def sync(self, elapsed):
        self.sequence.elapsed = elapsed
        plan = self.transport_scope['sync']()
        self.editor_scope['drive_imported_slots']()
        return plan


class OverlapRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.host = patch.object(mk2_td, '_host', None)
        self.midi = patch.object(show_midi, '_manager', None)
        self.host.start(); self.midi.start()
        self.addCleanup(self.host.stop); self.addCleanup(self.midi.stop)

    def test_full_generated_core_callbacks_animate_incoming_before_handover(self):
        rig = Rig()
        rig.automation({'one': {'scale': [[0, 1], [10, 3]], 'brightness': [[0, .2], [10, .6]]},
                        'two': {'scale': [[0, 4], [2, 8]], 'global_master_speed': [[0, 2], [10, 2]],
                                'brightness': [[0, .8], [2, .4]]}})
        plan = rig.sync(9.)
        self.assertAlmostEqual(plan.slot_a_brightness, .56)
        self.assertAlmostEqual(plan.slot_b_brightness, .6)
        self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuez.eval(), 2.8)
        self.assertAlmostEqual(rig.owner.op('slot_b_player').par.vec0valuez.eval(), 6.)
        self.assertAlmostEqual(rig.owner.op('slot_b_player').par.vec0valuey.eval(), 2.)
        self.assertEqual(overlap.render_options(rig.resolve)['slot_b_gain'], .5)
        rig.sequence.play(); rig.sequence.advance(1.)
        rig.transport_scope['sync']()
        self.assertEqual(rig.sequence.cue.id, 'two')
        self.assertAlmostEqual(rig.owner.op('slot_b_player').par.vec0valuey.eval(), 4.)
        controls = rig.resolve('/project1/madmapper_player_controls')
        self.assertEqual({name: getattr(controls.par, name).eval() for name in rig.protected_controls}, rig.protected_controls)

    def test_full_generated_native_callbacks_restore_both_slot_defaults_and_typed_automation(self):
        rig = Rig(imported=True)
        rig.automation({'one': {'mat__gain': [[0, 1], [10, 3]]},
                        'two': {'mat__gain': [[0, 2], [2, 4]], 'mat__enabled': [[0, 0], [2, 0]],
                                'mat__colour__component_0': [[0, .4], [2, .8]],
                                'intensity': [[0, .5], [2, 1.5]], 'contrast': [[0, 2], [2, 2]]}})
        rig.sync(9.)
        a, b = (rig.owner.op('slot_'+slot+'_import') for slot in ('a', 'b'))
        self.assertAlmostEqual(a.par.vec3valuex.eval(), 2.8)
        self.assertAlmostEqual(b.par.vec3valuex.eval(), 3.)
        self.assertAlmostEqual(b.par.vec4valuex.eval(), 0.)
        self.assertAlmostEqual(b.par.vec5valuex.eval(), .6)
        self.assertAlmostEqual(b.par.vec5valuey.eval(), .2)
        self.assertAlmostEqual(a.par.vec0valuex.eval(), 9.)
        self.assertAlmostEqual(b.par.vec0valuex.eval(), 1.)
        self.assertEqual(overlap.render_options(rig.resolve)['slot_b_tone'], (1., 2.))
        rig.automation({})
        rig.sync(9.)
        self.assertAlmostEqual(b.par.vec3valuex.eval(), 1.)
        self.assertAlmostEqual(b.par.vec4valuex.eval(), 1.)
        self.assertAlmostEqual(b.par.vec5valuex.eval(), .1)

    def test_normal_native_recording_monitors_outgoing_hands_without_touching_incoming(self):
        rig = Rig(imported=True)
        rig.automation({'two': {'mat__gain': [[0, 2], [2, 4]]}})
        rig.editor_scope['_set_state']('recording', '1')
        rig.editor_scope['_set_state']('record_cue', 'one')
        rig.native_live = 3.75
        rig.sync(9.)
        self.assertEqual(rig.owner.op('slot_a_import').par.vec3valuex.eval(), 3.75)
        self.assertEqual(rig.owner.op('slot_b_import').par.vec3valuex.eval(), 3.)

    def test_recorded_phase_is_integral_not_elapsed_times_instantaneous_speed(self):
        cue_dict = cue('one').to_dict()
        data = auto.merge(auto.empty(), 'one', {'speed': [[0, 1], [2, 3]],
                                               'global_master_speed': [[0, 1], [2, 1]]})
        self.assertAlmostEqual(overlap.clip_phase(cue_dict, data, 2), 4.)
        self.assertAlmostEqual(overlap.clip_phase(cue_dict, data, 1), 1.5)
        self.assertAlmostEqual(overlap.clip_phase(cue_dict, data, 0), 0.)
        self.assertAlmostEqual(overlap.clip_phase(cue_dict, data, 4), 10.)

    def test_live_midi_speed_outside_take_integrates_only_clip_time_and_pauses(self):
        rig = Rig()
        with patch.object(show_midi, 'live_values', side_effect=lambda cue_id: {'global_master_speed': 2.} if cue_id == 'one' else {}):
            rig.sync(3.)
            rig.sync(4.)
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 5.)
            rig.sync(4.)
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 5.)
            rig.sync(1.)  # Backwards seek restores deterministic phase.
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 1.)

    def test_explicit_forward_seek_resets_live_speed_phase_but_advancement_does_not(self):
        rig = Rig()
        with patch.object(show_midi, 'live_values', return_value={'global_master_speed': 2.}):
            rig.sync(3.)
            rig.sync(4.)
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 5.)
            rig.sequence.seek(0, 7.)
            rig.sync(7.)
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 7.)
            rig.sync(8.)
            self.assertAlmostEqual(rig.owner.op('slot_a_player').par.vec0valuey.eval(), 9.)
            revision = rig.sequence.position_revision
            rig.sequence.play(); rig.sequence.advance(.1)
            self.assertEqual(rig.sequence.position_revision, revision)
            rig.sequence.stop()
            self.assertGreater(rig.sequence.position_revision, revision)

    def test_legacy_callback_path_keeps_incoming_static_and_old_global_brightness(self):
        rig = Rig(legacy=True)
        rig.automation({'two': {'scale': [[0, 8], [2, 10]], 'brightness': [[0, 1], [2, 1]]}})
        plan = rig.sync(9.)
        self.assertEqual(rig.owner.op('slot_b_player').par.vec0valuez.eval(), 4.)
        self.assertEqual(plan.brightness, .8)
        self.assertEqual(overlap.render_options(rig.resolve), {})

    def test_prepared_install_idempotent_and_does_not_write_any_node(self):
        rig = Rig()
        before = {path: node.text for path, node in rig.nodes.items()}
        prepared = overlap.prepare_install(rig.owner)
        self.assertEqual(before, {path: node.text for path, node in rig.nodes.items()})
        for name, installer in [('callbacks', overlap.install_transport_source),
                                ('editor_callbacks', overlap.install_editor_source),
                                ('render_sync', overlap.install_render_source),
                                ('show_led_renderer_callbacks', overlap.install_led_source)]:
            self.assertEqual(installer(prepared[name]), prepared[name])

    def test_installer_preserves_running_sequence_and_documents_and_is_idempotent(self):
        rig = Rig()
        rig.sequence.play()
        rig.sequence.elapsed = 4.
        record = (rig.owner.op('show_json').text, rig.sequence)
        rig.owner.op('callbacks').module._runtime_record = record
        original = {name: rig.owner.op(name).text for name in ('show_json', 'automation_json', 'imported_json')}
        result = overlap.install(rig.owner)
        self.assertTrue(result['installed'])
        self.assertIn('show_transition_fs', result['changed'])
        self.assertIs(rig.owner.op('callbacks').module._runtime_record, record)
        self.assertEqual(rig.sequence.elapsed, 4.)
        self.assertEqual(rig.sequence.state.value, 'playing')
        self.assertEqual(original, {name: rig.owner.op(name).text for name in original})
        self.assertEqual(overlap.install(rig.owner)['changed'], [])

    def test_installer_defers_incomplete_build_or_recording_without_changing_source(self):
        self.assertEqual(overlap.install(None)['status'], 'not_ready')
        rig = Rig()
        rig.editor_scope['_set_state']('recording', '1')
        before = {path: node.text for path, node in rig.nodes.items()}
        result = overlap.install(rig.owner)
        self.assertFalse(result['installed'])
        self.assertEqual(result['status'], 'recording')
        self.assertEqual(before, {path: node.text for path, node in rig.nodes.items()})

    def test_installer_rolls_back_partial_dat_assignment_failure(self):
        rig = Rig()
        names = ('callbacks', 'show_transition_fs')
        before = {name: rig.owner.op(name).text for name in names}
        record = (rig.owner.op('show_json').text, rig.sequence)
        rig.owner.op('callbacks').module._runtime_record = record
        failed = []
        def rejecting(node, name, value):
            if name == 'text' and node.name == 'show_transition_fs' and value == 'new shader' and not failed:
                failed.append(True)
                raise RuntimeError('Native DAT assignment failed')
            object.__setattr__(node, name, value)
        prepared = {'callbacks': before['callbacks']+'\n# changed', 'show_transition_fs': 'new shader'}
        with patch.object(overlap, 'prepare_install', return_value=prepared), patch.object(Node, '__setattr__', rejecting):
            with self.assertRaisesRegex(RuntimeError, 'Native DAT assignment'):
                overlap.install(rig.owner)
        self.assertEqual(before, {name: rig.owner.op(name).text for name in names})
        self.assertIs(rig.owner.op('callbacks').module._runtime_record, record)


def render_options(**changes):
    result = dict(u=[.25, .75], v=[.5, .5], transition='crossfade', output_b_mix=.5,
                  brightness=.13, blackout=False, targets_a=('all',), targets_b=('all',),
                  source_groups=['middle', 'rear'], timing_mode='overlap',
                  slot_a_gain=.5, slot_b_gain=.5, slot_a_brightness=1., slot_b_brightness=1.)
    result.update(changes)
    return result


class OverlapMixerTests(unittest.TestCase):
    def test_matched_fades_are_not_squared_and_brightness_is_per_clip(self):
        a, b = [[200., 200.]], [[100., 100.]]
        result = render_frame(a, b, **render_options(slot_a_brightness=.5, slot_b_brightness=.8))
        self.assertEqual(result, ([90., 90.],))

    def test_excess_envelopes_normalize_before_brightness_and_dips_remain(self):
        a, b = [[200., 200.]], [[100., 100.]]
        self.assertEqual(render_frame(a, b, **render_options(slot_a_gain=1., slot_b_gain=1.)), ([150., 150.],))
        self.assertEqual(render_frame(a, b, **render_options(slot_a_gain=.2, slot_b_gain=.2)), ([60., 60.],))

    def test_spatial_wipe_keeps_masks_and_independent_envelopes(self):
        result = render_frame([[200., 200.]], [[100., 100.]],
                              **render_options(transition='wipe', slot_a_gain=.4, slot_b_gain=.8))
        self.assertEqual(result, ([80., 80.],))
        masked = render_frame([[200., 200.]], [[100., 100.]],
                              **render_options(transition='wipe', targets_b=('rear',)))
        self.assertEqual(masked, ([0., 100.],))

    def test_native_tone_uses_normalized_rgb_in_u256_led_units(self):
        result = render_frame([[.25*255, .75*255]], [[0., 0.]],
                              **render_options(slot_a_gain=1., slot_b_gain=0., slot_a_tone=(.5, 2.)))
        self.assertEqual(result, ([0., 127.5],))
        self.assertEqual(render_frame([[255., 255.]], [[255., 255.]], **render_options(blackout=True)), ([0., 0.],))

    def test_actual_numpy_arrays_work_for_optional_installed_fastpath(self):
        import numpy as np
        a, b = np.ones((3, 2))*200., np.ones((3, 2))*100.
        result = overlap.render_numpy(a, b, **render_options(slot_a_tone=(.6, 1.3)))
        reference = render_frame(a.tolist(), b.tolist(), **render_options(slot_a_tone=(.6, 1.3)))
        np.testing.assert_allclose(result, reference, rtol=1e-6)

    def test_optional_numpy_callback_is_redirected_without_importing_untracked_module(self):
        source = '# SHOW_NUMPY_MIX_V1\n' + LED_RENDER_CALLBACK.replace('    frame = render_frame(', '    frame = render_numpy(')
        patched = overlap.install_led_source(source)
        self.assertIn("fromlist=['render_numpy']).render_numpy(", patched)
        self.assertEqual(overlap.install_led_source(patched), patched)

    def test_legacy_ignores_all_new_slot_fields(self):
        options = render_options(timing_mode='legacy')
        result = render_frame([[200., 200.]], [[100., 100.]], **options)
        options.update(slot_a_gain=0., slot_b_gain=0., slot_a_tone=(0., 9.))
        self.assertEqual(render_frame([[200., 200.]], [[100., 100.]], **options), result)


if __name__ == '__main__':
    unittest.main()
