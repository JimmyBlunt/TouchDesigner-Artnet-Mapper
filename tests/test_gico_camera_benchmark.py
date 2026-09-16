import unittest

from pixelblaze_mapper import gico_camera_benchmark as b


class CodecTests(unittest.TestCase):
    def test_every_id_roundtrip_and_single_bit_error_rejection(self):
        for value in range(b.MODULUS):
            bits = b.encode(value)
            self.assertEqual(b.decode(bits), value)
            for i in range(b.MARKERS):
                broken = bits.copy(); broken[i] ^= 1
                self.assertIsNone(b.decode(broken), (value, i))

    def test_crc_known_check_value(self):
        self.assertEqual(b.crc8(b"123456789"), 0xF4)

    def test_mapping_addresses_and_black_reserved_universes(self):
        payload = b.payloads([1]*b.MARKERS)
        self.assertEqual(len(payload), 24)
        self.assertTrue(all(len(p) == 510 for p in payload))
        expected = {base+i for _, count, base in b.PANELS for i in b.marker_indices(count)}
        found = set()
        for universe, data in enumerate(payload):
            for pixel in range(170):
                rgb = data[pixel*3:pixel*3+3]
                if any(rgb):
                    found.add(universe*170+pixel)
                    self.assertEqual(rgb, bytes([16]*3))
        self.assertEqual(found, expected)
        self.assertEqual(len(found), 63)
        self.assertFalse(any(payload[23]))
        self.assertFalse(any(b"".join(b.payloads([0]*b.MARKERS))))

    def test_artdmx_header_wire_universe_and_sequence(self):
        packet = b.packet(23, bytes(510), 255)
        self.assertEqual(len(packet), 528)
        self.assertEqual(packet[:12], b"Art-Net\0\0P\0\x0e")
        self.assertEqual(packet[12:18], bytes([255, 0, 23, 0, 1, 254]))

    def test_default_gico_header_disables_sequence_without_losing_optical_id(self):
        self.assertEqual(b.plan()["artdmx_sequence"], 0)
        for value in (0, 1, 1234, 4095):
            self.assertEqual(b.decode(b.encode(value)), value)
            self.assertTrue(all(b.packet(u, payload)[12] == 0
                                for u, payload in enumerate(b.payloads(b.encode(value)))))

    def test_transition_low_contrast_and_exposure_rejected(self):
        bits = b.encode(349)
        values = [10+150*v for v in bits]
        self.assertEqual(b.decode_levels(values, [10]*21, [160]*21), (349, "valid"))
        values[0] = 85
        self.assertEqual(b.decode_levels(values, [10]*21, [160]*21)[1], "transition_or_pwm")
        self.assertEqual(b.decode_levels(values, [10]*21, [15]*21)[1], "calibration_contrast")
        values[-1] = 12
        self.assertEqual(b.decode_levels(values, [10]*21, [160]*21)[1], "reference_exposure")

    def test_brightness_frame_and_payload_validation(self):
        for value in (-1, 4096, True, 1.5):
            with self.assertRaises(ValueError): b.encode(value)
        for level in (-1, 0, 26, float("nan")):
            with self.assertRaises(ValueError): b.payloads([1]*21, level)
        with self.assertRaises(ValueError): b.packet(24, bytes(510))


class ObservationTests(unittest.TestCase):
    def samples(self, ids, camera_fps=120):
        return [{"time": i/camera_fps, "id": value} for i, value in enumerate(ids)]

    def test_perfect_30fps_at_120_camera_fps(self):
        result = b.summarize(self.samples([i//4 for i in range(240)]), 30)
        self.assertAlmostEqual(result["observed_unique_fps_estimate"], 30)
        self.assertEqual(result["unobserved_ids"], 0)
        self.assertAlmostEqual(result["camera_fps_median"], 120)

    def test_unobserved_id_is_not_claimed_controller_drop(self):
        result = b.summarize(self.samples([0]*4+[1]*4+[None]*4+[3]*4+[4]*4), 30)
        self.assertEqual(result["unobserved_ids"], 1)
        self.assertIsNone(result["proven_controller_drops"])
        self.assertLess(result["observed_unique_fps_estimate"], 30)

    def test_one_frame_false_code_does_not_become_observed_image(self):
        result = b.summarize(self.samples([0]*4+[500]+[1]*3+[2]*4), 30)
        self.assertEqual(result["stable_distinct_images"], 3)
        self.assertEqual(result["unexpected_discontinuities"], 0)

    def test_wraparound_and_backward_discontinuity(self):
        result = b.summarize(self.samples([4094]*4+[4095]*4+[0]*4+[1]*4), 30)
        self.assertEqual(result["unobserved_ids"], 0)
        self.assertAlmostEqual(result["observed_unique_fps_estimate"], 30)
        bad = b.summarize(self.samples([100]*4+[5]*4), 30)
        self.assertEqual(bad["unexpected_discontinuities"], 1)
        self.assertIsNone(bad["observed_unique_fps_estimate"])

    def test_repeated_camera_frames_not_controller_refresh_count(self):
        result = b.summarize(self.samples([1]*240), 30)
        self.assertEqual(result["stable_distinct_images"], 1)
        self.assertIsNone(result["observed_unique_fps_estimate"])

    def test_invalid_timebase_fails(self):
        with self.assertRaises(ValueError):
            b.summarize([{"time": 0, "id": 0}, {"time": 0, "id": 0}], 30)
        with self.assertRaises(ValueError):
            b.summarize([{"time": float("nan"), "id": 0}], 30)


if __name__ == "__main__":
    unittest.main()
