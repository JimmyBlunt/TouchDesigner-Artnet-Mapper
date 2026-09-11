"""Packet-spacing configuration and transport tests; all hardware is mocked."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import scan_capture as capture
from pixelblaze_mapper.scan_routing import create_snapshot

try:
    from tests.test_scan_capture import Harness, snapshot
except ModuleNotFoundError:
    from test_scan_capture import Harness, snapshot


CAMERA = {'device': 0, 'exposure': -10, 'threshold': 160}


class PacketSpacingManifestTests(unittest.TestCase):
    def test_legacy_default_and_none_omit_optional_field(self):
        with tempfile.TemporaryDirectory() as folder:
            for options in ({}, {'packet_gap_ms': None}):
                plan = capture.prepare_capture(snapshot(), CAMERA, folder, **options)
                self.assertNotIn('packet_gap_ms', plan)
                self.assertNotIn('packet_gap_ms', capture.validate_capture_manifest(plan))
                with patch.object(capture.subprocess, 'Popen', return_value=Mock()), \
                     patch.object(capture.threading, 'Thread'):
                    handle = capture.start_capture(plan, confirmed=True)
                saved = json.loads((handle.directory / 'capture.json').read_text(encoding='utf-8'))
                self.assertNotIn('packet_gap_ms', saved)

    def test_explicit_gap_survives_validation_and_fresh_start_with_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            for gap in (0, 1, 2):
                with self.subTest(gap=gap):
                    identity = {'503': 'led-a', '500': 'led-b'}
                    plan = capture.prepare_capture(snapshot(), CAMERA, folder, packet_gap_ms=gap,
                                                   identity=identity, scene_revision='revision-a')
                    checked = capture.validate_capture_manifest(plan)
                    self.assertEqual(checked['packet_gap_ms'], gap)
                    self.assertEqual(checked['directory_name'], plan['directory_name'])
                    directories = []
                    for _ in range(2):
                        with patch.object(capture.subprocess, 'Popen', return_value=Mock()), \
                             patch.object(capture.threading, 'Thread'):
                            handle = capture.start_capture(plan, confirmed=True)
                        saved = json.loads((handle.directory / 'capture.json').read_text(encoding='utf-8'))
                        self.assertEqual(saved['packet_gap_ms'], gap)
                        self.assertEqual(saved['identity'], identity)
                        self.assertEqual(saved['scene_revision'], 'revision-a')
                        self.assertEqual(saved['routing'], plan['routing'])
                        self.assertNotEqual(saved['directory_name'], plan['directory_name'])
                        directories.append(handle.directory)
                    self.assertNotEqual(directories[0], directories[1])

    def test_invalid_gap_is_rejected_before_process_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = capture.prepare_capture(snapshot(), CAMERA, folder)
            for gap in (True, False, -.001, 2.001, float('nan'), float('inf')):
                with self.subTest(gap=gap):
                    with self.assertRaises(ValueError):
                        capture.prepare_capture(snapshot(), CAMERA, folder, packet_gap_ms=gap)
                    invalid = dict(plan, packet_gap_ms=gap)
                    with self.assertRaises(ValueError):
                        capture.validate_capture_manifest(invalid)
                    with patch.object(capture.subprocess, 'Popen') as launch:
                        with self.assertRaises(ValueError):
                            capture.start_capture(invalid, confirmed=True)
                        launch.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])


class GapHarness(Harness):
    def __init__(self, gap=1, **options):
        super().__init__(request={'action': 'set_led', 'index': 0, 'on': True, 'request_id': 1}, **options)
        source = snapshot()
        config = replace(source.config, controllers=(replace(source.config.controllers[0], reserved_universes=13),))
        self.manifest['routing'] = create_snapshot(config, source.source_indices).to_dict()
        self.manifest['packet_gap_ms'] = gap
        self.child_start_time = None
        self.ack_times = []

    def start(self):
        super().start()
        if self.starts == 2:
            self.child_start_time = self.now

    def send(self, value):
        super().send(value)
        self.ack_times.append((value, self.now, len(self.socket.packets)))


class PacketSpacingTransportTests(unittest.TestCase):
    def test_spacing_only_between_packets_and_emergency_black_bypasses_gap(self):
        for gap in (1, 2):
            with self.subTest(gap=gap):
                harness = GapHarness(gap)
                outcome, _ = harness.run()
                self.assertEqual(outcome['state'], 'complete')
                batches = [harness.socket.times[i:i + 13] for i in range(0, len(harness.socket.times), 13)]
                self.assertTrue(all(len(batch) == 13 for batch in batches))
                emergency_index = len(batches) - 3
                for index, batch in enumerate(batches):
                    expected = 0 if index == emergency_index else gap / 1000
                    for earlier, later in zip(batch, batch[1:]):
                        self.assertAlmostEqual(later - earlier, expected)
                self.assertAlmostEqual(harness.child_start_time, 12 * gap / 1000)
                for ack, when, count in harness.ack_times:
                    self.assertTrue(ack['ok'])
                    self.assertAlmostEqual(when, harness.socket.times[count - 1])
                self.assertTrue(all(not any(packet[18:]) for packet, _ in harness.socket.packets[-39:]))

    def test_zero_spacing_keeps_packets_in_each_batch_together(self):
        harness = GapHarness(0)
        outcome, _ = harness.run()
        self.assertEqual(outcome['state'], 'complete')
        for offset in range(0, len(harness.socket.times), 13):
            self.assertEqual(len(set(harness.socket.times[offset:offset + 13])), 1)

    def test_transport_counts_successful_packets_and_batches(self):
        harness = GapHarness(1)
        outcome, _ = harness.run()
        transport = outcome['transport']
        self.assertEqual(transport['packets_sent'], len(harness.socket.packets))
        self.assertEqual(transport['batches_sent'], len(harness.socket.packets) // 13)
        self.assertEqual(transport['send_errors'], 0)
        self.assertEqual(transport['packet_gap_ms'], 1)

    def test_packet_errors_are_recorded_and_not_counted_as_successful_packets(self):
        harness = GapHarness(1, fail_after=2)
        outcome, _ = harness.run()
        self.assertEqual(outcome['state'], 'failed')
        transport = outcome['transport']
        self.assertEqual(transport['packets_sent'], 2)
        self.assertGreater(transport['send_errors'], 0)
        self.assertFalse(outcome['blackout_sent'])
        self.assertTrue(harness.socket.closed)

    def test_spacing_does_not_bypass_rate_limit_between_regular_batches(self):
        harness = GapHarness(2)
        harness.run()
        batches = [harness.socket.times[i:i + 13] for i in range(0, len(harness.socket.times), 13)]
        for previous, current in zip(batches, batches[1:]):
            if current is batches[-3]:  # First emergency blackout may send immediately.
                continue
            self.assertGreaterEqual(current[0] - previous[-1], .05 - 1e-12)


if __name__ == '__main__':
    unittest.main()
