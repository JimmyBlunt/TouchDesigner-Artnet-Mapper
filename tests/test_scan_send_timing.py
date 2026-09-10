"""Deterministic send scheduling; no camera, process or network is started."""
import unittest

try:
    from tests.test_scan_capture import Harness
except ModuleNotFoundError:
    from test_scan_capture import Harness


class TimedCommands(Harness):
    """ON arrives at 1 ms; the next command arrives during the next interval."""
    def __init__(self, *, stop_during_wait=False):
        super().__init__('timed')
        self.pending = [
            (.001, {'action': 'set_led', 'index': 0, 'on': True, 'request_id': 1}),
            (.065, {'action': 'set_led', 'index': 1, 'on': stop_during_wait, 'request_id': 2}),
        ]
        self.ack_times = []
        self.stop_during_wait = stop_during_wait

    def poll(self, timeout):
        self.polls += 1
        deadline = self.now + timeout
        if self.pending and self.pending[0][0] <= deadline:
            available, self.request = self.pending.pop(0)
            self.now = max(self.now, available)
            return True
        self.now = deadline
        return False

    def sleep(self, seconds):
        before = self.now
        super().sleep(seconds)
        if self.stop_during_wait and before < .08 <= self.now:
            self.messages.put({'action': 'stop'})

    def send(self, value):
        super().send(value)
        self.ack_times.append((value['request_id'], value['ok'], self.now, len(self.socket.packets)))
        if value['request_id'] == 2 and value['ok']:
            self.results.put({'state': 'view_ready', 'observations': [[0, .2, .3]]})
            self.results.put({'state': 'camera_closed', 'camera_cleanup_attempted': True,
                              'camera_cleanup_errors': []})
            self.exitcode = 0


class SendTimingTests(unittest.TestCase):
    def test_request_after_waited_send_uses_next_slot_without_extra_periodic_wait(self):
        harness = TimedCommands()
        outcome, _ = harness.run()
        self.assertEqual(outcome['state'], 'complete')
        first, second = harness.ack_times
        self.assertAlmostEqual(first[2], .05)
        # The stale pre-send timestamp used to resend ON at 100 ms and delay
        # this OFF until 150 ms. Its correct next available slot is 100 ms.
        self.assertAlmostEqual(second[2], .10)
        self.assertEqual((first[0:2], second[0:2]), ((1, True), (2, True)))
        self.assertEqual(second[3] - first[3], 2)  # One complete two-universe batch.
        for _, ok, ack_time, packet_count in harness.ack_times:
            self.assertTrue(ok)
            self.assertEqual(harness.socket.times[packet_count - 1], ack_time)

    def test_rate_limit_and_final_black_are_preserved(self):
        harness = TimedCommands()
        outcome, _ = harness.run()
        batches = harness.socket.times[::2]
        # First teardown blackout intentionally bypasses pacing; regular
        # command sends and the later teardown repeats retain the 20 Hz cap.
        regular, cleanup = batches[:-3], batches[-3:]
        for times in (regular, cleanup):
            self.assertTrue(all(b - a >= .05 - 1e-12 for a, b in zip(times, times[1:])))
        self.assertTrue(outcome['blackout_sent'])
        self.assertTrue(all(not any(packet[18:]) for packet, _ in harness.socket.packets[-6:]))
        self.assertTrue(harness.socket.closed)

    def test_stop_arriving_inside_rate_wait_prevents_pending_light(self):
        harness = TimedCommands(stop_during_wait=True)
        outcome, _ = harness.run()
        self.assertEqual(outcome['state'], 'cancelled')
        self.assertEqual([(request_id, ok) for request_id, ok, _, _ in harness.ack_times],
                         [(1, True), (2, False)])
        lit = [packet for packet, _ in harness.socket.packets if any(packet[18:])]
        self.assertEqual(len(lit), 1)
        self.assertTrue(outcome['blackout_sent'])
        self.assertTrue(all(not any(packet[18:]) for packet, _ in harness.socket.packets[-6:]))


if __name__ == '__main__':
    unittest.main()
