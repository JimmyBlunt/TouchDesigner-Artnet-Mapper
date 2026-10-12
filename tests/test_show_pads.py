from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from pixelblaze_mapper.maschine_mk2 import PadEdges, display_packets, pad_lights, physical_pad, render
from pixelblaze_mapper.show_pads import Manager, validate


def snapshot():
    return dict(cards=[dict(number=i+1,kind='material',target='mat',label='Nested Cube',image=None,available=True) for i in range(16)],
                images={},selected=0,version=1)


class HardwareProtocolTests(unittest.TestCase):
    def test_full_frame_roundtrip_and_band_addresses(self):
        pixels=bytes(range(256))*8
        packets=list(display_packets(1,pixels))
        self.assertEqual(len(packets),8)
        self.assertEqual([len(p) for p in packets],[265]*8)
        self.assertEqual([p[:9] for p in packets], [bytes([0xe1,0,0,i*8,0,32,0,8,0]) for i in range(8)])
        self.assertEqual(b''.join(p[9:] for p in packets),pixels)
        with self.assertRaises(ValueError):
            list(display_packets(0,b''))

    def test_pad_order_matches_bottom_left_one(self):
        self.assertEqual([physical_pad(i) for i in range(16)],[12,13,14,15,8,9,10,11,4,5,6,7,0,1,2,3])
        lights=pad_lights(snapshot())
        self.assertEqual(len(lights),49)
        self.assertEqual(lights[1+12*3:1+13*3],bytes([75,75,75]))

    def test_press_hold_release_repress_and_noise(self):
        edges=PadEdges()
        def report(pressure):
            data=bytearray(65);data[0]=0x20
            data[25]=pressure&255;data[26]=0xc0|(pressure>>8)
            return data
        self.assertEqual(edges.read(b'\x01'),[])
        for _ in range(3): self.assertEqual(edges.read(report(0)),[])
        self.assertEqual(edges.read(report(100)),[])
        self.assertEqual(edges.read(report(0)),[])
        self.assertEqual(edges.read(report(0)),[])
        self.assertEqual(edges.read(report(300)),[])
        self.assertEqual(edges.read(report(300)),[0])
        for _ in range(5): self.assertEqual(edges.read(report(300)),[])
        for _ in range(3): edges.read(report(0))
        self.assertEqual(edges.read(report(300)),[])
        self.assertEqual(edges.read(report(300)),[0])

    def test_render_real_monochrome_frames_and_missing_image(self):
        frames=render(snapshot())
        self.assertEqual([(f.size,f.mode,len(f.tobytes())) for f in frames],[((256,64),'1',2048)]*2)
        self.assertTrue(all(f.getbbox() for f in frames))


class PadManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager=Manager.__new__(Manager)
        m=self.manager
        m.config=dict(hardware=False,pads=[dict(kind='material',target='mat') for _ in range(16)])
        m.cards=snapshot()['cards'];m.version=2;m.selected=0;m.error='';m.last=''
        m.choices=Mock(return_value=[dict(kind='material',id='mat')])
        m.save=Mock();m.update_surface=Mock()
        self.library=Mock()
        self.editor=SimpleNamespace(_state=lambda *args:'0',_library=lambda:self.library)
        self.transport=Mock()
        m.owner=SimpleNamespace(op=lambda name:SimpleNamespace(module=self.editor if name=='editor_callbacks' else self.transport))

    def test_invalid_config_and_unavailable_target(self):
        for config in (None,{},dict(pads=[None]*16),dict(pads=[dict(kind='bad')]*16)):
            with self.assertRaises(ValueError):validate(config)
        config=deepcopy(self.manager.config);config['pads'][0]['target']='missing'
        with self.assertRaises(ValueError):self.manager.command(dict(action='pads_config',config=config,pads_version=2))
        self.manager.save.assert_not_called()

    def test_stale_assignment_and_activation_rejected(self):
        for action in ('pads_config','pad_trigger'):
            with self.assertRaises(ValueError):self.manager.command(dict(action=action,pads_version=1,config=self.manager.config,index=0))
        self.library.activate_selected.assert_not_called()

    def test_selection_does_not_activate_and_recording_blocks_load(self):
        self.manager.trigger(3,load=False)
        self.assertEqual(self.manager.selected,3)
        self.library.activate_selected.assert_not_called()
        self.editor._state=lambda *args:'1'
        with self.assertRaises(ValueError):self.manager.trigger(3)
        self.library.activate_selected.assert_not_called()

    def test_failed_material_restores_selection(self):
        self.library._state.return_value='previous'
        self.library.activate_selected.return_value=False
        with self.assertRaises(ValueError):self.manager.trigger(0)
        self.library._set_state.assert_called_with('selected_id','previous')

    def test_successful_material_and_cue_actions(self):
        self.library.activate_selected.return_value=True
        self.manager.trigger(0)
        self.library._set_state.assert_called_with('selected_id','mat')
        self.manager.config['pads'][1]=dict(kind='cue',target='cue-2')
        self.manager.trigger(1)
        self.transport.runtime.return_value.seek.assert_called_with('cue-2',0)
        self.transport.command.assert_called_with('play')

    def test_failed_save_does_not_change_mapping_or_version(self):
        before=deepcopy(self.manager.config)
        config=deepcopy(before);config['pads'][0]['target']=''
        self.manager.save.side_effect=OSError('disk full')
        with self.assertRaises(OSError):self.manager.command(dict(action='pads_config',config=config,pads_version=2))
        self.assertEqual(self.manager.config,before)
        self.assertEqual(self.manager.version,2)


if __name__=='__main__':unittest.main()
