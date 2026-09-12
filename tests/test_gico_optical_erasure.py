import itertools
import unittest
from pixelblaze_mapper.gico_camera_benchmark import encode
from pixelblaze_mapper.gico_optical_erasure import decode_scores


class OpticalErasureTests(unittest.TestCase):
    def test_every_unmodified_id_and_each_single_known_bit_error(self):
        for value in range(4096):
            bits = encode(value)
            self.assertEqual(decode_scores(bits), (value, 'direct_crc', 0))
            for i in range(20):
                damaged = bits.copy(); damaged[i] ^= 1
                self.assertIsNone(decode_scores(damaged)[0])

    def test_bounded_unknown_bits_never_recover_a_different_id(self):
        recovered = 0
        for value in (0, 1, 194, 237, 449, 1023, 2048, 4095):
            for positions in itertools.combinations(range(20), 3):
                bits = encode(value)
                for i in positions: bits[i] = .5
                got, reason, count = decode_scores(bits)
                self.assertEqual(count, 3)
                self.assertIn(got, (None, value))
                if sum(i < 12 for i in positions) > 2:
                    self.assertEqual(reason, 'too_many_erasures')
                if got is not None: recovered += 1
        self.assertGreater(recovered, 1000)

    def test_limits_invalid_reference_and_no_time_input(self):
        scores = encode(194)
        for i in (12, 13, 14, 15): scores[i] = .5
        self.assertEqual(decode_scores(scores)[1], 'too_many_erasures')
        scores = encode(194); scores[-1] = 0
        self.assertEqual(decode_scores(scores)[1], 'reference_exposure')
        scores = encode(194); scores[0] = float('nan')
        self.assertEqual(decode_scores(scores)[1], 'invalid_scores')


if __name__ == '__main__': unittest.main()
