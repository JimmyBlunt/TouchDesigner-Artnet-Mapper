"""Real-file-only audio contract, DSP, metadata and texture-binding acceptance."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

import numpy as np

from pixelblaze_mapper import material_audio_runtime as audio
from pixelblaze_mapper.material_texture_runtime import bind_textures


class AudioAnalysisTests(unittest.TestCase):
    def test_no_configuration_means_no_audio_and_missing_file_fails(self):
        with TemporaryDirectory() as directory:
            config = Path(directory)/'audio.json'
            self.assertIsNone(audio.configured_audio_path(config))
            config.write_text(json.dumps(dict(path=str(Path(directory)/'missing.mp3'))))
            with self.assertRaises(ValueError):
                audio.configured_audio_path(config)

    def test_config_selected_file_loop_and_disabled_state(self):
        with TemporaryDirectory() as directory:
            source = Path(directory)/'actual track.mp3'
            source.write_bytes(b'fixture file for path validation only')
            config = Path(directory)/'audio.json'
            config.write_text(json.dumps(dict(path=str(source), loop=False)))
            self.assertEqual(audio.configured_audio_path(config), str(source.resolve()))
            self.assertFalse(audio.load_audio_config(config)['loop'])
            config.write_text(json.dumps(dict(path=str(source), enabled=False)))
            self.assertIsNone(audio.configured_audio_path(config))

    def test_metadata_numeric_reference_and_live_parameter_override(self):
        spec = dict(TYPE='audioFFT', SIZE='width', ATTACK='attack', DECAY=.2, RELEASE='0.4',
                    _parameter_values={'width': 16, 'attack': .1})
        self.assertEqual(audio.audio_settings(spec), dict(kind='audiofft', size=16, attack=.1, decay=.2, release=.4))
        self.assertEqual(audio.audio_settings(spec, {'width':128, 'attack':.3})['size'], 128)
        self.assertEqual(audio.audio_settings(dict(TYPE='audio', SIZE=9999))['size'], 512)
        self.assertEqual(audio.audio_settings(dict(TYPE='audio', SIZE=0))['size'], 1)
        for invalid in ('missing_reference', float('nan'), True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                audio.audio_settings(dict(TYPE='audioFFT', SIZE=invalid))

    def test_loop_wrap_nonloop_silence_and_deterministic_window(self):
        samples = np.array([.1,.2,.3,.4], dtype=np.float32)
        np.testing.assert_array_equal(audio.sample_window(samples, 2, 1.5, 4, True), samples[[3,0,1,2]])
        np.testing.assert_array_equal(audio.sample_window(samples, 2, 1.5, 4, False), [samples[3],0,0,0])
        np.testing.assert_array_equal(audio.sample_window(samples, 2, 10, 4), samples)
        with self.assertRaises(ValueError):
            audio.sample_window(np.array([np.nan]), 48000, 0)

    def test_waveform_centred_at_half_and_contains_real_sample_variation(self):
        samples = np.linspace(-1,1,1024,dtype=np.float32)
        values, _ = audio.analyse(samples,48000,0,dict(TYPE='audio',SIZE=512))
        self.assertEqual(values.shape,(512,))
        self.assertAlmostEqual(float(values[0]),0)
        self.assertAlmostEqual(float(values[-1]),1)
        silent, _ = audio.analyse(np.zeros(1024),48000,0,dict(TYPE='audio',SIZE=128))
        np.testing.assert_array_equal(silent,np.full(128,.5))

    def test_fft_peak_tracks_known_input_frequency_and_zero_signal_stays_zero(self):
        # Synthetic fixtures test the FFT mathematically; runtime has no signal
        # generator or synthesized fallback, and always decodes the chosen file.
        waveform = np.sin(2*np.pi*32*np.arange(1024)/1024).astype(np.float32)
        values, _ = audio.analyse(waveform,48000,0,dict(TYPE='audioFFT',SIZE=512))
        self.assertEqual(int(np.argmax(values)),32)
        self.assertGreater(values[32],.99)
        small, _ = audio.analyse(waveform,48000,0,dict(TYPE='audioFFT',SIZE=16))
        self.assertEqual(int(np.argmax(small)),1)
        silent, _ = audio.analyse(np.zeros(1024),48000,0,dict(TYPE='audioFFT',SIZE=16))
        self.assertTrue(np.all(silent == 0))

    def test_adr_attack_release_decay_have_effect_without_changing_waveform(self):
        settings = dict(kind='audiofft',attack=.2,decay=0.,release=.4)
        rising = audio.smooth([1.],[0.],.1,settings)
        self.assertGreater(rising[0],0)
        self.assertLess(rising[0],1)
        falling = audio.smooth([0.],[1.],.1,settings)
        self.assertGreater(falling[0],0)
        self.assertLess(falling[0],1)
        tail = audio.smooth([0.],[1.],.1,dict(settings,release=0.,decay=.8))
        self.assertGreater(tail[0],falling[0])
        np.testing.assert_allclose(audio.smooth([.2],[.9],.1,dict(settings,kind='audio')), [.2])
        np.testing.assert_allclose(audio.smooth([.2],None,.1,settings), [.2])


class StoredNode:
    def __init__(self, name='node', parent=None):
        self.name, self._parent = name, parent
        self.path = (parent.path if parent else '')+'/'+name
        self.storage = {}
        self.children = []
        self.isCOMP = True
        self.par = NS()
        self.destroyed = False
        self.created_types = []

    def store(self, key, value):
        self.storage[key] = value

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def parent(self):
        return self._parent

    def op(self, name):
        return next((n for n in self.children if n.name == name), None)

    def create(self, kind, name):
        self.created_types.append(kind)
        node = StoredNode(name, self)
        self.children.append(node)
        return node

    def destroy(self):
        self.destroyed = True
        if self._parent:
            self._parent.children.remove(self)

    def cook(self, force=False):
        pass

    def errors(self):
        return []

    def copyNumpyArray(self, pixels):
        self.pixels = pixels.copy()

    def setInputs(self, inputs):
        self.inputs = inputs


class AudioBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name)/'actual.mp3'
        self.source.write_bytes(b'path fixture; decoding mocked separately')
        self.parent = StoredNode('test')
        self.preview = self.parent.create('preview', 'preview')
        self.td = NS(baseCOMP='base',textDAT='text',scriptTOP='script',selectTOP='select',moviefileinTOP='movie',
                     absTime=NS(seconds=10.))
        self.patch = patch.dict('sys.modules',td=self.td)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.spec = dict(TYPE='audioFFT',SIZE=16,resolved_path=str(self.source),loop=True)

    def test_audio_owned_component_retained_by_mixed_texture_binder_and_removed_on_switch(self):
        adaptation = NS(textures=(self.spec,dict(TYPE='2d',resolved_path='image.png')))
        bind_textures(self.preview,adaptation)
        self.assertEqual(len(self.preview.inputs),2)
        owner = audio.audio_component(self.preview.inputs[0])
        self.assertEqual(owner.fetch('material_audio_owner'),audio.OWNER_MARKER)
        self.assertFalse(owner.destroyed)
        self.assertEqual(self.preview.inputs[1].par.file,'image.png')
        bind_textures(self.preview,NS(textures=()))
        self.assertTrue(owner.destroyed)
        self.assertEqual(self.preview.inputs,[])

    def test_audio_signature_updates_size_smoothing_and_parameter_defaults(self):
        bind_textures(self.preview,NS(textures=(self.spec,)))
        owner = audio.audio_component(self.preview.inputs[0])
        for changes in (dict(SIZE=128),dict(ATTACK=.4),dict(_parameter_values={'size':32},SIZE='size')):
            changed = dict(self.spec,**changes)
            bind_textures(self.preview,NS(textures=(changed,)))
            self.assertEqual(owner.fetch('audio_spec'),changed)

    def test_multiple_audio_inputs_share_clock_and_only_create_analysis_nodes(self):
        first = audio.bind_audio_texture(self.preview,self.spec,0)
        self.td.absTime.seconds = 12.
        second = audio.bind_audio_texture(self.preview,dict(self.spec,TYPE='audio'),1)
        self.assertIs(first.parent(),self.preview.parent())
        self.assertIs(second.parent(),self.preview.parent())
        self.assertEqual(audio.audio_component(first).fetch('audio_start_seconds'),audio.audio_component(second).fetch('audio_start_seconds'))
        self.assertEqual(audio.audio_component(first).created_types,['text','script'])
        self.assertEqual(audio.audio_component(second).created_types,['text','script'])
        self.assertNotIn('audioDeviceOut',self.parent.created_types)

    def test_foreign_component_or_missing_audio_file_is_rejected(self):
        foreign = self.parent.create('base','preview_asset_0_audio')
        with self.assertRaises(ValueError):
            audio.bind_audio_texture(self.preview,self.spec)
        self.assertEqual(foreign.storage,{})
        with self.assertRaises(ValueError):
            audio.bind_audio_texture(self.preview,dict(self.spec,resolved_path='missing.mp3'),1)

    def test_seeking_cooks_only_owned_audio_resets_history_and_is_repeatable(self):
        top = audio.bind_audio_texture(self.preview,self.spec)
        owner = audio.audio_component(top)
        owner.store('audio_filter',np.ones(16))
        foreign = self.parent.create('base','unrelated')
        foreign.store('audio_probe_time','untouched')
        self.assertEqual(audio.set_audio_probe_time(self.parent,1.25),1)
        self.assertEqual(owner.fetch('audio_probe_time'),1.25)
        self.assertIsNone(owner.fetch('audio_filter'))
        self.assertEqual(foreign.fetch('audio_probe_time'),'untouched')
        self.assertEqual(audio.set_audio_probe_time(self.parent,None),1)
        self.assertIsNone(owner.fetch('audio_probe_time'))

    def test_cook_uses_decoded_file_samples_and_uploads_float_rgba(self):
        output = audio.bind_audio_texture(self.preview,self.spec)
        top = audio.audio_component(output).op('texture')
        track = np.concatenate([np.zeros(1024),np.sin(2*np.pi*32*np.arange(1024)/1024)]).astype(np.float32)
        with patch.object(audio,'_decode',return_value=(track,1024.)) as decode:
            audio.set_audio_probe_time(self.parent,0)
            audio.cook_audio_top(top,10.)
            first = top.pixels.copy()
            audio.set_audio_probe_time(self.parent,1)
            audio.cook_audio_top(top,99.)
            second = top.pixels.copy()
            self.assertEqual(second.shape,(1,16,4))
            self.assertEqual(second.dtype,np.float32)
            self.assertTrue(np.all(second[:,:,3] == 1))
            self.assertFalse(np.array_equal(first,second))
            self.assertEqual(decode.call_args.args[1],str(self.source))
            audio.set_audio_probe_time(self.parent,0)
            audio.cook_audio_top(top,200.)
            np.testing.assert_array_equal(top.pixels,first)

    def test_decode_cache_is_process_only_and_temporary_file_node_destroyed(self):
        owner = self.parent.create('base','decode_owner')
        decoder = StoredNode('decode_file',owner)
        decoder.numpyArray = lambda: np.array([[.1,.2],[.3,.4]],dtype=np.float32)
        decoder.rate = 48000.
        owner.children.append(decoder)
        owner.create = Mock(return_value=decoder)
        self.td.fileinCHOP = 'filein'
        with patch.object(audio,'_decoded',{}):
            first = audio._decode(owner,str(self.source))
            second = audio._decode(owner,str(self.source))
            self.assertIs(first,second)
            owner.create.assert_called_once_with('filein','decode_file')
            np.testing.assert_allclose(first[0],[.2,.3])
            self.assertTrue(decoder.destroyed)
            self.assertEqual(owner.storage,{})


if __name__ == '__main__':
    unittest.main()
