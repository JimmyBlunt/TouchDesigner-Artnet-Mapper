import unittest
from pixelblaze_mapper.output_slot_mask import channels, pixels, install_source
from tests.test_guided_scan_live import _artnet_510_sender_source

class MaskTests(unittest.TestCase):
    def test_only_reserved_slots_zero_and_input_unchanged(self):
        rgb=[[1]*3744,[.5]*3744,[.25]*3744]
        result=channels(rgb,[[1643,1695]])
        for original,masked in zip(rgb,result):
            self.assertEqual(masked[:1643],original[:1643])
            self.assertEqual(masked[1643:1696],[0]*53)
            self.assertEqual(masked[1696:],original[1696:])
        self.assertEqual(rgb[0],[1]*3744)
    def test_calibration_mask(self):
        result=pixels([(1,1,1)]*3744,[[1643,1695]])
        self.assertEqual(result[1643:1696],[(0,0,0)]*53)
    def test_td_noniterable_channel(self):
        from types import SimpleNamespace
        result=channels([SimpleNamespace(vals=[1,2,3])]*3,[[1,1]])
        self.assertEqual(result,[[1,0,3]]*3)
    def test_invalid_ranges_rejected(self):
        for ranges in ([[-1,2]],[[2,4]],[[2,1]]):
            with self.assertRaises(ValueError): channels([[1]*4]*3,ranges)
    def test_install_is_idempotent_compiles(self):
        source=install_source(_artnet_510_sender_source())
        compile(source,'sender','exec')
        self.assertEqual(install_source(source),source)
