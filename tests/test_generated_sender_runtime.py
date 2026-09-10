"""Execute the generated sender unchanged against fake TD and UDP surfaces.

No TouchDesigner connection, UDP bind, hardware output, or sleep is performed.
"""
from collections import Counter
from types import SimpleNamespace
import unittest

from pixelblaze_mapper.output_slot_mask import install_source as install_mask
from pixelblaze_mapper.sender_pacing import install_source as install_pacing
from tests.test_sender_pacing import sender_source


class Table:
    def __init__(self, rows):
        self.rows = rows
        self.numRows, self.numCols = len(rows), len(rows[0])

    def __getitem__(self, address):
        row, column = address
        if isinstance(column, str):
            column = self.rows[0].index(column)
        return self.rows[row][column]


class Source:
    numSamples, numChans = 4, 3

    def __init__(self):
        self.channels = ([1.0, 0.5, 0.2, 0.1], [0.0, 0.25, 0.3, 0.2], [0.5, 1.0, 0.4, 0.3])
        self.cooks = []

    def __getitem__(self, index):
        return self.channels[index]

    def cook(self, force):
        self.cooks.append(force)


class Clock:
    now = 100.0
    timer = 0.0

    def monotonic(self):
        return self.now

    def perf_counter(self):
        self.timer += 0.00001
        return self.timer


class DatagramRecorder:
    def __init__(self):
        self.packets = []
        self.closed = False

    def bind(self, address):
        self.bound = address

    def sendto(self, packet, address):
        if self.closed:
            raise RuntimeError('Closed fake socket')
        self.packets.append((packet, address))

    def close(self):
        self.closed = True


class GeneratedSenderRuntimeTests(unittest.TestCase):
    def harness(self):
        controllers = Table([
            ['enabled', 'name', 'target_ip', 'local_interface', 'port', 'start_universe', 'color_order', 'brightness', 'rate', 'art_sync', 'reserved_universes'],
            ['1', 'side', '10.0.0.244', '10.0.0.125', '6454', '0', 'GRB', '0.7', '60', '0', '2'],
            ['1', 'back', '10.0.0.249', '10.0.0.125', '6454', '120', 'RGB', '0.9', '30', '0', '2'],
        ])
        segments = Table([
            ['name', 'source_start', 'count', 'controller', 'destination_start', 'reverse', 'color_override'],
            ['side_segment', '0', '2', 'side', '0', '0', ''],
            ['back_segment', '2', '2', 'back', '0', '0', ''],
        ])
        source, clock, recorder = Source(), Clock(), DatagramRecorder()
        router = SimpleNamespace(fetch=lambda key, default: [[3, 3]] if key == 'inactive_source_ranges' else default)
        surfaces = {'controller_config': controllers, 'segment_config': segments,
                    '/project1/math1': source, 'source_select': source,
                    '/project1/multi_controller_output': router}
        namespace = {'op': surfaces.get}
        exec(compile(install_pacing(install_mask(sender_source())), '<generated-sender>', 'exec'), namespace)
        namespace['socket'] = SimpleNamespace(AF_INET=2, SOCK_DGRAM=2, socket=lambda *args: recorder)
        namespace['time'] = clock
        self.assertTrue(namespace['set_enabled'](True))
        self.assertEqual(recorder.bound, ('10.0.0.125', 6454))
        return namespace, clock, recorder, source

    def run_ticks(self, namespace, clock, count=600, hz=60):
        for index in range(count):
            clock.now = 100 + index / hz
            namespace['tick']()

    def assert_packets(self, recorder, side_frames, back_frames):
        counts = Counter((target[0], int.from_bytes(packet[14:16], 'little')) for packet, target in recorder.packets)
        self.assertEqual(counts, {('10.0.0.244', 0): side_frames, ('10.0.0.244', 1): side_frames,
                                  ('10.0.0.249', 120): back_frames, ('10.0.0.249', 121): back_frames})
        for packet, target in recorder.packets:
            self.assertEqual(len(packet), 528)
            self.assertEqual(packet[:14], b'Art-Net\x00\x00\x50\x00\x0e\x00\x00')
            self.assertEqual(int.from_bytes(packet[16:18], 'big'), 510)
            self.assertEqual(target[1], 6454)

    def test_live_real_packing_and_socket_calls_respect_both_rates(self):
        namespace, clock, recorder, source = self.harness()
        self.run_ticks(namespace, clock)
        self.assert_packets(recorder, 600, 300)
        telemetry = namespace['status']()['telemetry']
        self.assertEqual(telemetry['send_count'], 600)
        self.assertEqual(telemetry['pack_count'], 600)
        self.assertEqual(telemetry['packet_count'], 1800)
        self.assertEqual(telemetry['tick_count'], 600)
        self.assertEqual(telemetry['plan_rebuilds'], 1)
        self.assertEqual(telemetry['rate_skips'], 0)
        self.assertAlmostEqual(telemetry['actual_send_fps'], 60, places=6)
        self.assertEqual(source.cooks, [False] * 600)
        # First frame preserves GRB order and brightness; inactive source 3 black.
        first = {(target[0], int.from_bytes(packet[14:16], 'little')): packet[18:]
                 for packet, target in recorder.packets[:4]}
        self.assertEqual(first['10.0.0.244', 0][:3], bytes((0, 178, 89)))
        self.assertEqual(first['10.0.0.249', 120][:6], bytes((46, 69, 92, 0, 0, 0)))
        self.assertEqual(first['10.0.0.249', 121], bytes(510))
        self.assertEqual(namespace['status']()['error'], '')
        namespace['stop']()
        namespace['tick']()
        self.assertTrue(recorder.closed)
        self.assertEqual(len(recorder.packets), 1800)

    def test_calibration_due_subset_does_not_require_live_frames(self):
        namespace, clock, recorder, source = self.harness()
        namespace['_mode'] = 'calibration'
        namespace['_calibration_frames'] = {
            'side': (tuple([12] * 510), tuple([13] * 510)),
            'back': (tuple([21] * 510), tuple([22] * 510)),
        }
        # This fixture seeds an already-reviewed cache without generating a
        # calibration pattern. Real set_calibration binds the mask signature.
        from pixelblaze_mapper.output_slot_mask import signature
        namespace['_calibration_mask_signature'] = signature(namespace['op'], source.numSamples)
        self.run_ticks(namespace, clock)
        self.assert_packets(recorder, 600, 300)
        self.assertEqual(source.cooks, [])
        self.assertEqual(namespace['status']()['telemetry']['pack_count'], 0)
        self.assertEqual(namespace['status']()['telemetry']['packet_count'], 1800)
        self.assertEqual(namespace['status']()['error'], '')
        for packet, target in recorder.packets:
            universe = int.from_bytes(packet[14:16], 'little')
            self.assertEqual(packet[18:], bytes([{0: 12, 1: 13, 120: 21, 121: 22}[universe]] * 510))

    def test_fast_callback_skips_without_extra_source_cooks(self):
        namespace, clock, recorder, source = self.harness()
        self.run_ticks(namespace, clock, count=120, hz=120)
        self.assert_packets(recorder, 60, 30)
        telemetry = namespace['status']()['telemetry']
        self.assertEqual(telemetry['rate_skips'], 60)
        self.assertEqual(telemetry['send_count'], 60)
        self.assertEqual(telemetry['pack_count'], 60)
        self.assertEqual(len(source.cooks), 60)


if __name__ == '__main__':
    unittest.main()
