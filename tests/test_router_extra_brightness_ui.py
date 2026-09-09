import unittest
from pixelblaze_mapper.router_extra_brightness_ui import parse_brightness

class BrightnessValidation(unittest.TestCase):
    def test_decimal_point(self): self.assertEqual(parse_brightness('0.3'),.3)
    def test_decimal_comma(self): self.assertEqual(parse_brightness(' 0,3 '),.3)
    def test_bounds(self):
        self.assertEqual(parse_brightness('0'),0)
        self.assertEqual(parse_brightness('1'),1)
    def test_outside(self):
        for value in ('-0.1','1.1','nan','inf','-inf'):
            with self.subTest(value=value), self.assertRaises(ValueError): parse_brightness(value)
    def test_invalid(self):
        for value in ('','foo','0,2,3'):
            with self.subTest(value=value), self.assertRaises(ValueError): parse_brightness(value)
