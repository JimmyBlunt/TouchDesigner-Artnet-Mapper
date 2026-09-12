"""Unit and localhost-only process tests. No LED controller or TD access."""
import base64
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pixelblaze_mapper.external_packet_sender import ExternalPacketSender, _decode, _packet, _wait_until, _latest_queued_batch, _FrameDeadline, _write, _periodic_status, _StopCheck, _worker


def packet(universe, level=17):
    return (b'Art-Net\0\0P\0\x0e\0\0' + int(universe).to_bytes(2, 'little')
            + b'\x01\xfe' + bytes([level]) * 510)


class ExternalPacketSenderTests(unittest.TestCase):
    def test_stop_cache_expires_at_20ms_and_forced_boundaries_are_fresh(self):
        path = Mock()
        path.exists.side_effect = [False, True]
        stop = _StopCheck(path)
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=0.) as clock:
            self.assertFalse(stop.check(force=True))
            clock.return_value = .019999
            self.assertFalse(stop.check())
            path.exists.assert_called_once()
            clock.return_value = .02
            self.assertTrue(stop.check())
            self.assertTrue(stop.check(force=True))
            self.assertEqual(path.exists.call_count, 2)
        path.exists.reset_mock(side_effect=True)
        path.exists.side_effect = [False, True]
        stop = _StopCheck(path)
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=1.):
            self.assertFalse(stop.check())
            self.assertTrue(stop.check(force=True))

    def run_mock_worker(self, outgoing, packets, extra_patches=()):
        # Exercise the actual worker, sockets simulated; no port binding.
        from contextlib import ExitStack
        incoming = Mock()
        incoming.getsockname.return_value = ('127.0.0.1', 42000)
        raw = json.dumps(dict(token='secret', packets=[
            base64.b64encode(p).decode() for p in packets])).encode()
        incoming.recvfrom.side_effect = [(raw, ('127.0.0.1', 42001)), BlockingIOError()]
        outgoing.getsockopt.return_value = 1024 * 1024
        snapshots = []
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps(dict(token='secret', local=['127.0.0.1', 42002],
                                             target=['127.0.0.1', 42003], gap=0.)))
            stack.enter_context(patch('pixelblaze_mapper.external_packet_sender.socket.socket',
                                      side_effect=[outgoing, incoming]))
            stack.enter_context(patch('pixelblaze_mapper.external_packet_sender._write',
                                      side_effect=lambda path, value: snapshots.append((path.name, dict(value)))))
            stack.enter_context(patch('pixelblaze_mapper.external_packet_sender.time.sleep'))
            for context in extra_patches:
                stack.enter_context(context)
            _worker(config)
        outgoing.close.assert_called_once()
        incoming.close.assert_called_once()
        return snapshots[-1][1]

    def test_nonblocking_send_failure_is_visible_and_blackout_restores_timeout(self):
        for successful_packets in (0, 1):
            with self.subTest(successful_packets=successful_packets):
                outgoing = Mock()
                outgoing.sendto.side_effect = ([528] * successful_packets +
                                              [BlockingIOError(10035, 'would block')] + [528] * 4)
                values = [packet(120), packet(121)]
                report = self.run_mock_worker(outgoing, values)
                outgoing.setblocking.assert_called_once_with(False)
                outgoing.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
                outgoing.settimeout.assert_called_once_with(.2)
                calls = outgoing.method_calls
                timeout_index = calls.index(unittest.mock.call.settimeout(.2))
                self.assertEqual(sum(call[0] == 'sendto' for call in calls[:timeout_index]), successful_packets + 1)
                self.assertEqual(report['sent_packets'], successful_packets)
                self.assertEqual(report['sent_batches'], 0)
                self.assertEqual(report['send_errors'], 1)
                self.assertEqual(report['stop_reason'], 'error')
                self.assertIn('would block', report['error'])
                self.assertEqual(report['blackout_packets'], 4)
                self.assertEqual([call.args[0] for call in outgoing.sendto.call_args_list[-4:]],
                                 [p[:18] + bytes(510) for p in values] * 2)

    def test_stop_during_long_batch_uses_bounded_cache_then_blackens_all_universes(self):
        now = [0.]
        path = Mock()
        path.exists.side_effect = lambda: now[0] >= .009
        stop = _StopCheck(path)
        outgoing = Mock()
        def send(value, _target):
            if any(value[18:]):
                now[0] += .004
            return len(value)
        outgoing.sendto.side_effect = send
        values = [packet(i) for i in range(29)]
        report = self.run_mock_worker(outgoing, values, [
            patch('pixelblaze_mapper.external_packet_sender._StopCheck', return_value=stop),
            patch('pixelblaze_mapper.external_packet_sender.time.monotonic', side_effect=lambda: now[0]),
            patch('pixelblaze_mapper.external_packet_sender.time.perf_counter', side_effect=lambda: now[0])])
        self.assertEqual(report['sent_packets'], 5)
        self.assertEqual(report['sent_batches'], 0)
        self.assertEqual(report['stop_reason'], 'requested')
        self.assertEqual(report['send_errors'], 0)
        self.assertLessEqual(now[0] - .009, .02)
        self.assertEqual(path.exists.call_count, 3)  # Loop, batch start, expired cache.
        self.assertEqual(report['blackout_packets'], 58)

    def test_periodic_status_skips_locked_replace_then_catches_up(self):
        stats = dict(sent_batches=1, status_write_ms=0., max_status_write_ms=0.,
                     status_write_skipped=0, status_write_errors=0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            original_replace = Path.replace
            calls = []
            def locked_once(temporary, destination):
                calls.append(destination)
                if len(calls) == 1:
                    raise PermissionError('reader holds status file')
                return original_replace(temporary, destination)
            with patch.object(Path, 'replace', autospec=True, side_effect=locked_once), \
                 patch('pixelblaze_mapper.external_packet_sender.time.sleep') as sleep, \
                 patch('pixelblaze_mapper.external_packet_sender.time.perf_counter', side_effect=[0., .003, .1, .101]):
                _periodic_status(path, stats)
                self.assertFalse(path.exists())
                self.assertEqual(len(calls), 1)
                self.assertEqual(stats['status_write_skipped'], 1)
                stats['sent_batches'] = 2
                _periodic_status(path, stats)
                sleep.assert_not_called()
            saved = json.loads(path.read_text())
            self.assertEqual(saved['sent_batches'], 2)
            self.assertEqual(saved['status_write_skipped'], 1)
            self.assertEqual(saved['status_write_errors'], 0)
            self.assertAlmostEqual(saved['status_write_ms'], 3.)
            self.assertAlmostEqual(stats['status_write_ms'], 1.)
            self.assertAlmostEqual(stats['max_status_write_ms'], 3.)

    def test_periodic_status_os_error_is_measured_without_stopping_output(self):
        stats = dict(status_write_ms=0., max_status_write_ms=0.,
                     status_write_skipped=0, status_write_errors=0)
        with patch('pixelblaze_mapper.external_packet_sender._write', side_effect=OSError('disk unavailable')) as write, \
             patch('pixelblaze_mapper.external_packet_sender.time.perf_counter', side_effect=[1., 1.2]):
            _periodic_status(Path('status.json'), stats)
        write.assert_called_once_with(Path('status.json'), stats, retry=False)
        self.assertEqual(stats['status_write_errors'], 1)
        self.assertEqual(stats['status_write_skipped'], 0)
        self.assertAlmostEqual(stats['max_status_write_ms'], 200.)

    def test_final_write_keeps_bounded_permission_retries_and_final_counters(self):
        path = Mock()
        temporary = path.with_suffix.return_value
        temporary.replace.side_effect = [PermissionError('locked'), None]
        final = dict(sent_batches=42, blackout_packets=4, stop_reason='requested')
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', side_effect=[1., 1.01]), \
             patch('pixelblaze_mapper.external_packet_sender.time.sleep') as sleep:
            _write(path, final)
        self.assertEqual(temporary.replace.call_count, 2)
        sleep.assert_called_once_with(.005)
        self.assertEqual(json.loads(temporary.write_text.call_args.args[0]), final)
        temporary.replace.side_effect = PermissionError('still locked')
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', side_effect=[1., 1.201]), \
             patch('pixelblaze_mapper.external_packet_sender.time.sleep') as sleep:
            with self.assertRaises(PermissionError):
                _write(path, final)
            sleep.assert_not_called()

    def fake_sender(self):
        sender = ExternalPacketSender.__new__(ExternalPacketSender)
        sender._directory = Path(tempfile.mkdtemp(prefix='worker-close-test-'))
        sender._process = Mock()
        sender._process.poll.return_value = 0
        sender._ipc = Mock()
        sender._closed = False
        sender._last_status = {}
        sender._status_checked_at = float('-inf')
        sender._last_process_running = None
        sender._cleanup_errors = []
        sender._forced_termination = False
        sender.target = ('127.0.0.1', 6454)
        sender._address = ('127.0.0.1', 42000)
        sender._token = 'test-token'
        self.addCleanup(sender.close)
        return sender

    def test_status_caches_disk_reads_but_polls_process_every_time(self):
        sender = self.fake_sender()
        sender._process.poll.return_value = None
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=10.) as clock, \
             patch.object(Path, 'read_text', side_effect=[
                 '{"sent_batches":1}', '{"sent_batches":2}', '{"sent_batches":3}']) as read:
            self.assertEqual(sender.status()['sent_batches'], 1)
            clock.return_value = 10.05
            self.assertEqual(sender.status()['sent_batches'], 1)
            self.assertEqual(read.call_count, 1)
            self.assertEqual(sender._process.poll.call_count, 2)
            clock.return_value = 10.101
            self.assertEqual(sender.status()['sent_batches'], 2)
            self.assertEqual(read.call_count, 2)
            self.assertEqual(sender.status(force=True)['sent_batches'], 3)
            self.assertEqual(read.call_count, 3)
        sender._process.poll.return_value = 0

    def test_worker_exit_inside_cache_window_reads_final_watchdog_status(self):
        sender = self.fake_sender()
        sender._process.poll.return_value = None
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=10.), \
             patch.object(Path, 'read_text', side_effect=[
                 '{"sent_batches":1,"stop_reason":""}',
                 '{"sent_batches":2,"stop_reason":"idle_watchdog","blackout_packets":4}']) as read:
            self.assertTrue(sender.status()['running'])
            sender._process.poll.return_value = 0
            report = sender.status()
            self.assertFalse(report['running'])
            self.assertEqual(report['stop_reason'], 'idle_watchdog')
            self.assertEqual(report['blackout_packets'], 4)
            self.assertEqual(read.call_count, 2)

    def test_close_forces_final_counters_even_if_process_was_already_stopped(self):
        sender = self.fake_sender()
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=10.), \
             patch.object(Path, 'read_text', side_effect=[
                 '{"sent_batches":1}',
                 '{"sent_batches":2,"blackout_packets":4,"stop_reason":"requested"}']) as read:
            sender.status()
            report = sender.close()
            self.assertEqual(report['sent_batches'], 2)
            self.assertEqual(report['blackout_packets'], 4)
            self.assertFalse(sender._directory.exists())
            self.assertEqual(read.call_count, 2)
            self.assertEqual(sender.close()['sent_batches'], 2)

    def test_transient_status_read_failure_keeps_counters_and_live_health(self):
        sender = self.fake_sender()
        sender._process.poll.return_value = None
        with patch('pixelblaze_mapper.external_packet_sender.time.monotonic', return_value=10.) as clock, \
             patch.object(Path, 'read_text', side_effect=[
                 '{"sent_batches":1}', PermissionError('atomic file replacement'),
                 '{"sent_batches":2}']) as read:
            sender.status()
            clock.return_value = 10.101
            self.assertEqual(sender.status()['sent_batches'], 1)
            self.assertTrue(sender.status()['running'])
            self.assertEqual(read.call_count, 2)
            clock.return_value = 10.202
            self.assertEqual(sender.status()['sent_batches'], 2)
        sender._process.poll.return_value = 0

    def test_submit_validates_before_enqueue_without_decoding_own_envelope(self):
        sender = self.fake_sender()
        sender._process.poll.return_value = None
        values = [packet(120), packet(121, 33)]
        with patch('pixelblaze_mapper.external_packet_sender._decode', side_effect=AssertionError('redundant decode')):
            self.assertTrue(sender.submit((p, sender.target) for p in values))
        raw, endpoint = sender._ipc.sendto.call_args.args
        self.assertEqual(endpoint, sender._address)
        self.assertEqual(_decode(raw, sender._token), tuple(values))
        sender._ipc.sendto.reset_mock()
        bad_batches = [[], [(values[0],sender.target)]*2,
                       [(values[0][:-1],sender.target)],
                       [(packet(32768),sender.target)],
                       [(values[0],('127.0.0.2',6454))],
                       [(packet(i),sender.target) for i in range(90)]]
        for batch in bad_batches:
            with self.subTest(packets=len(batch)), self.assertRaises(ValueError):
                sender.submit(batch)
            sender._ipc.sendto.assert_not_called()
        sender._process.poll.return_value = 0

    def test_submit_exact_ipc_size_boundary_is_checked_on_encoded_bytes(self):
        sender = self.fake_sender()
        sender._process.poll.return_value = None
        batch = [(packet(120),sender.target)]
        self.assertTrue(sender.submit(batch))
        size = len(sender._ipc.sendto.call_args.args[0])
        sender._ipc.sendto.reset_mock()
        with patch('pixelblaze_mapper.external_packet_sender.MAX_BATCH', size):
            self.assertTrue(sender.submit(batch))
        sender._ipc.sendto.reset_mock()
        with patch('pixelblaze_mapper.external_packet_sender.MAX_BATCH', size-1):
            with self.assertRaisesRegex(ValueError, 'IPC limit'):
                sender.submit(batch)
        sender._ipc.sendto.assert_not_called()
        sender._process.poll.return_value = 0

    def test_stop_marker_failure_does_not_skip_ipc_close_or_worker_termination(self):
        sender = self.fake_sender()
        sender._process.wait.side_effect = [subprocess.TimeoutExpired('worker', 1.8), 0]
        with patch.object(Path, 'touch', side_effect=PermissionError('blocked stop marker')):
            report = sender.close()
        sender._ipc.close.assert_called_once()
        sender._process.kill.assert_called_once()
        self.assertEqual(sender._process.wait.call_count, 2)
        self.assertTrue(report['forced_termination'])
        self.assertTrue(any('stop marker' in error for error in report['cleanup_errors']))
        self.assertFalse(sender._directory.exists())

    def test_temporary_cleanup_failure_is_reported_and_retryable(self):
        sender = self.fake_sender()
        with patch('pixelblaze_mapper.external_packet_sender.shutil.rmtree',
                   side_effect=PermissionError('temporarily locked')):
            report = sender.close()
        self.assertFalse(report['running'])
        self.assertTrue(sender._directory.exists())
        self.assertTrue(any('temporary files' in error for error in report['cleanup_errors']))
        sender.close()
        self.assertFalse(sender._directory.exists())

    def test_configuration_write_failure_cleans_temp_directory_before_raising(self):
        directory = Path(tempfile.mkdtemp(prefix='worker-start-test-'))
        with patch('pixelblaze_mapper.external_packet_sender.tempfile.mkdtemp', return_value=str(directory)), \
             patch('pixelblaze_mapper.external_packet_sender._write', side_effect=PermissionError('no config')):
            with self.assertRaisesRegex(PermissionError, 'no config'):
                ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1')
        self.assertFalse(directory.exists())

    def test_worker_start_timeout_is_five_seconds_and_cleans_up(self):
        directory = Path(tempfile.mkdtemp(prefix='worker-start-timeout-test-'))
        process = Mock()
        state = dict(now=0., stopped=False)
        process.poll.side_effect = lambda: 0 if state['stopped'] else None
        process.kill.side_effect = lambda: state.update(stopped=True)
        def advance(_seconds):
            state['now'] += .25
        with patch('pixelblaze_mapper.external_packet_sender.tempfile.mkdtemp', return_value=str(directory)), \
             patch('pixelblaze_mapper.external_packet_sender.subprocess.Popen', return_value=process), \
             patch('pixelblaze_mapper.external_packet_sender.time.monotonic', side_effect=lambda: state['now']), \
             patch('pixelblaze_mapper.external_packet_sender.time.sleep', side_effect=advance):
            with self.assertRaisesRegex(TimeoutError, 'exceeded 5 seconds'):
                ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1')
        self.assertEqual(state['now'], 5.)
        process.kill.assert_called_once()
        self.assertFalse(directory.exists())

    def test_worker_priority_validation_precedes_process_start(self):
        with patch('pixelblaze_mapper.external_packet_sender.subprocess.Popen') as start:
            for priority in ('high', 'realtime', 'AboveNormal', '', None, 3, []):
                with self.subTest(priority=priority), self.assertRaisesRegex(ValueError, 'Worker priority'):
                    ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1', priority=priority)
            start.assert_not_called()

    def test_worker_priority_creation_flags_and_default(self):
        for options, expected in (({}, 0x08000000), ({'priority': 'normal'}, 0x08000000),
                                  ({'priority': 'above_normal'}, 0x08008000)):
            with self.subTest(options=options), \
                 patch('pixelblaze_mapper.external_packet_sender.subprocess.CREATE_NO_WINDOW', 0x08000000, create=True), \
                 patch('pixelblaze_mapper.external_packet_sender.subprocess.ABOVE_NORMAL_PRIORITY_CLASS', 0x8000, create=True), \
                 patch('pixelblaze_mapper.external_packet_sender.subprocess.Popen', side_effect=OSError('mock launch')) as start:
                with self.assertRaisesRegex(OSError, 'mock launch'):
                    ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1', **options)
                self.assertEqual(start.call_args.kwargs['creationflags'], expected)

    def test_worker_priority_portable_without_windows_flag(self):
        import pixelblaze_mapper.external_packet_sender as module
        original = module.subprocess
        class PortableSubprocess:
            DEVNULL = original.DEVNULL
            TimeoutExpired = original.TimeoutExpired
            Popen = Mock(side_effect=OSError('mock launch'))
        with patch.object(module, 'subprocess', PortableSubprocess):
            with self.assertRaisesRegex(OSError, 'mock launch'):
                ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1', priority='above_normal')
        self.assertEqual(PortableSubprocess.Popen.call_args.kwargs['creationflags'], 0)

    def test_bounded_queue_drain_does_not_consume_unprocessed_129th_batch(self):
        def envelope(level):
            return json.dumps(dict(token='secret', packets=[
                base64.b64encode(packet(120, level)).decode()])).encode()

        class Queue:
            def __init__(self):
                self.values = [envelope(level) for level in range(1, 129)]

            def recvfrom(self, size):
                if not self.values:
                    raise BlockingIOError()
                return self.values.pop(0), ('127.0.0.1', 12345)

        queue = Queue()
        stats = dict(stale_batches=0, submitted_batches=0, rejected_batches=0)
        latest = _latest_queued_batch(queue, envelope(0), ('127.0.0.1', 12345), 'secret', stats)
        self.assertEqual(latest, (packet(120, 127),))
        self.assertEqual(stats['submitted_batches'], 128)
        self.assertEqual(stats['stale_batches'], 127)
        self.assertEqual(queue.values, [envelope(128)])
    def test_precise_wait_never_returns_before_deadline_and_only_sleeps_coarsely(self):
        class Clock:
            now = 0.

            def __init__(self):
                self.sleeps = []

            def perf_counter(self):
                result = self.now
                self.now += .00001
                return result

            def sleep(self, seconds):
                self.sleeps.append(seconds)
                self.now += seconds

        for delay in (.001, .002, .005):
            clock = Clock()
            with patch('pixelblaze_mapper.external_packet_sender.time', clock):
                _wait_until(delay)
            self.assertGreaterEqual(clock.now, delay)
            self.assertLess(clock.now, delay + .00003)
            if delay <= .002:
                self.assertEqual(clock.sleeps, [])
            else:
                self.assertEqual(len(clock.sleeps), 1)
                self.assertAlmostEqual(clock.sleeps[0], delay - .001)

    def receiver(self):
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        receiver.bind(('127.0.0.1', 0))
        receiver.settimeout(2.)
        self.addCleanup(receiver.close)
        return receiver

    def sender(self, receiver, gap=0, frame_rate=None):
        # Reserve then release an ephemeral local source port; never binds6454.
        reserve = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        reserve.bind(('127.0.0.1', 0))
        local_port = reserve.getsockname()[1]
        reserve.close()
        sender = ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1',
                                      receiver.getsockname()[1], local_port, gap, frame_rate=frame_rate)
        self.addCleanup(sender.close)
        return sender

    def test_packet_validation_preserves_exact_bytes(self):
        original = packet(32767)
        self.assertEqual(_packet(original), original)
        for invalid in (original[:-1], packet(32768), b'x' * 528,
                        original[:16] + b'\x02\x00' + original[18:]):
            with self.assertRaises(ValueError):
                _packet(invalid)

    def test_authentication_empty_duplicates_and_size_fail_closed(self):
        raw = lambda packets, token='right': json.dumps(dict(
            token=token, packets=[base64.b64encode(p).decode() for p in packets])).encode()
        self.assertEqual(_decode(raw([packet(120)]), 'right'), (packet(120),))
        for invalid in (raw([packet(120)], 'wrong'), raw([]),
                        raw([packet(120), packet(120)]), b'[]', b'null',
                        raw([packet(i) for i in range(90)])):
            with self.assertRaises(ValueError):
                _decode(invalid, 'right')

    def test_exact_delivery_and_close_blackout(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        submitted = [packet(120, 23), packet(121, 45)]
        self.assertTrue(sender.submit([(p, receiver.getsockname()) for p in submitted]))
        self.assertEqual([receiver.recvfrom(600)[0] for _ in range(2)], submitted)
        report = sender.close()
        black = [receiver.recvfrom(600)[0] for _ in range(4)]
        self.assertEqual(black, [p[:18] + bytes(510) for p in submitted] * 2)
        self.assertEqual(report['sent_batches'], 1)
        self.assertEqual(report['blackout_packets'], 4)
        self.assertEqual(report['stop_reason'], 'requested')
        self.assertFalse(report['running'])
        self.assertFalse(sender._directory.exists())
        self.assertEqual(sender.close()['sent_batches'], 1)

    def test_target_mismatch_rejected_before_submission(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        with self.assertRaises(ValueError):
            sender.submit([(packet(120), ('127.0.0.2', receiver.getsockname()[1]))])

    def test_idle_watchdog_blackens_last_frame_and_exits(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        sender.submit([(packet(120), receiver.getsockname())])
        self.assertEqual(receiver.recvfrom(600)[0], packet(120))
        self.assertEqual(receiver.recvfrom(600)[0], packet(120)[:18] + bytes(510))
        self.assertEqual(receiver.recvfrom(600)[0], packet(120)[:18] + bytes(510))
        deadline = time.monotonic() + 2
        while sender.status()['running'] and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(sender.status()['stop_reason'], 'idle_watchdog')
        with self.assertRaises(RuntimeError):
            sender.submit([(packet(120), receiver.getsockname())])

    def test_initial_grace_allows_delayed_first_tick_then_one_second_watchdog(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        # TD may finish the bridge/start callback more than one second before
        # its first frame tick. No LED data has been sent during this grace.
        time.sleep(1.2)
        self.assertTrue(sender.status()['running'])
        self.assertEqual(sender.status()['sent_packets'], 0)
        sender.submit([(packet(120), receiver.getsockname())])
        self.assertEqual(receiver.recvfrom(600)[0], packet(120))
        started = time.monotonic()
        self.assertEqual(receiver.recvfrom(600)[0], packet(120)[:18] + bytes(510))
        self.assertLess(time.monotonic() - started, 1.8)
        self.assertEqual(receiver.recvfrom(600)[0], packet(120)[:18] + bytes(510))
        report = sender.close()
        self.assertEqual(report['stop_reason'], 'idle_watchdog')

    def test_initial_grace_is_bounded_without_any_submission(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        started = time.monotonic()
        deadline = started + 6.5
        while sender.status()['running'] and time.monotonic() < deadline:
            time.sleep(.05)
        report = sender.close()
        self.assertFalse(report['forced_termination'])
        self.assertGreaterEqual(time.monotonic() - started, 4.5)
        self.assertLess(time.monotonic() - started, 6.5)
        self.assertEqual(report['stop_reason'], 'startup_watchdog')
        self.assertEqual(report['sent_packets'], 0)
        self.assertEqual(report['blackout_packets'], 0)

    def test_latest_queue_drops_stale_frames_without_blocking_producer(self):
        receiver = self.receiver()
        sender = self.sender(receiver, gap=5)
        batches = [[(packet(120 + i, level), receiver.getsockname()) for i in range(10)]
                   for level in range(1, 21)]
        started = time.monotonic()
        for batch in batches:
            sender.submit(batch)
        self.assertLess(time.monotonic() - started, .5)
        # Observe newest image before closing; old queued images should collapse.
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            data = receiver.recvfrom(600)[0]
            if data == packet(129, 20):
                break
        else:
            self.fail('Newest submitted frame not observed')
        report = sender.close()
        self.assertGreater(report['stale_batches'], 0)
        self.assertLess(report['sent_batches'], 20)
        self.assertEqual(report['gap_ms'], 5.)

    def test_worker_fps_counts_sends_separately_from_producer_and_watchdog(self):
        receiver = self.receiver()
        sender = self.sender(receiver)
        for level in range(1, 4):
            sender.submit([(packet(120, level), receiver.getsockname())])
            self.assertEqual(receiver.recvfrom(600)[0], packet(120, level))
            if level < 3:
                time.sleep(.1)
        report = sender.close()
        self.assertEqual(report['sent_batches'], 3)
        self.assertGreater(report['active_seconds'], .18)
        self.assertGreater(report['actual_send_fps'], 4.)
        self.assertLess(report['actual_send_fps'], 12.)
        self.assertAlmostEqual(report['active_average_fps'], 2 / report['active_seconds'])

    def test_frame_rate_invalid_values_fail_before_starting_worker(self):
        with patch('pixelblaze_mapper.external_packet_sender.subprocess.Popen') as start:
            for rate in (0, -1, float('inf'), float('nan'), 5e-324, 120.01, 1e308):
                with self.subTest(rate=rate), self.assertRaises(ValueError):
                    ExternalPacketSender(sys.executable, '127.0.0.1', '127.0.0.1', frame_rate=rate)
            start.assert_not_called()

    def test_frame_deadline_latest_whole_batch_empty_slots_and_stall(self):
        pacer = _FrameDeadline(30.)
        stats = dict(stale_batches=0)
        first = (packet(120, 1), packet(121, 1))
        newest = (packet(120, 3), packet(121, 3))
        self.assertEqual(pacer.wait_seconds(100.), .05)
        pacer.offer(first, stats)
        self.assertEqual(pacer.take(100.), first)
        pacer.offer((packet(120, 2),), stats)
        pacer.offer(newest, stats)
        self.assertEqual(stats['stale_batches'], 1)
        self.assertIsNone(pacer.take(100.02))
        self.assertAlmostEqual(pacer.wait_seconds(100.02), 1 / 30 - .02)
        # A long stalled clock discards elapsed slots, not whole-frame atomicity.
        self.assertEqual(pacer.take(105.012), newest)
        self.assertGreater(pacer.deadline, 105.012)
        self.assertLessEqual(pacer.deadline, 105.012 + 1 / 30)
        pacer.offer(first, stats)
        self.assertIsNone(pacer.take(105.012))
        self.assertEqual(pacer.take(pacer.deadline), first)
        # Empty intervals never repeat the last data.
        self.assertIsNone(pacer.take(200.))
        self.assertIsNone(pacer.take(201.))

    def test_phase_clock_does_not_accumulate_repeated_wakeup_delay(self):
        pacer = _FrameDeadline(30.)
        stats = dict(stale_batches=0)
        pacer.offer((packet(120),), stats)
        pacer.take(10.)
        for slot in range(1, 301):
            pacer.offer((packet(120),), stats)
            self.assertIsNotNone(pacer.take(10 + slot / 30 + .003))
        self.assertAlmostEqual(pacer.deadline, 10 + 301 / 30, places=9)
        self.assertEqual(stats['stale_batches'], 0)

    def test_paced_latest_batch_no_repeat_and_responsive_stop(self):
        receiver = self.receiver()
        sender = self.sender(receiver, frame_rate=2)
        target = receiver.getsockname()
        sender.submit([(packet(120, 1), target)])
        self.assertEqual(receiver.recvfrom(600)[0], packet(120, 1))
        for level in range(2, 21):
            sender.submit([(packet(120, level), target), (packet(121, level), target)])
        self.assertEqual([receiver.recvfrom(600)[0] for _ in range(2)],
                         [packet(120, 20), packet(121, 20)])
        receiver.settimeout(.2)
        with self.assertRaises(socket.timeout):
            receiver.recvfrom(600)
        # Pending frame must not delay stop to the next (500 ms) slot.
        sender.submit([(packet(122, 99), target)])
        time.sleep(.03)
        started = time.monotonic()
        report = sender.close()
        self.assertLess(time.monotonic() - started, .35)
        self.assertEqual(report['sent_batches'], 2)
        self.assertGreaterEqual(report['stale_batches'], 18)
        self.assertEqual(report['frame_rate'], 2.)
        self.assertEqual(report['blackout_packets'], 6)
        receiver.settimeout(1.)
        black = [receiver.recvfrom(600)[0] for _ in range(6)]
        self.assertEqual({int.from_bytes(p[14:16], 'little') for p in black}, {120, 121, 122})
        self.assertTrue(all(not any(p[18:]) for p in black))

    def test_paced_watchdog_ignores_invalid_inputs_and_does_not_send_pending(self):
        receiver = self.receiver()
        sender = self.sender(receiver, frame_rate=.2)
        target = receiver.getsockname()
        sender.submit([(packet(120, 1), target)])
        self.assertEqual(receiver.recvfrom(600)[0], packet(120, 1))
        sender.submit([(packet(121, 2), target)])
        started = time.monotonic()
        while time.monotonic() - started < 1.25:
            sender._ipc.sendto(b'{"token":"wrong","packets":[]}', sender._address)
            time.sleep(.03)
        report = sender.close()
        self.assertEqual(report['stop_reason'], 'idle_watchdog')
        self.assertEqual(report['sent_batches'], 1)
        self.assertEqual(report['submitted_batches'], 2)
        self.assertGreater(report['rejected_batches'], 0)
        self.assertEqual(report['blackout_packets'], 4)

    def test_paced_overfed_loopback_average_rate_and_latest_values(self):
        receiver = self.receiver()
        receiver.setblocking(False)
        sender = self.sender(receiver, frame_rate=30)
        target = receiver.getsockname()
        observed = []
        start = time.monotonic()
        duration = 1.5
        level = 0
        while time.monotonic() - start < duration:
            level = level % 250 + 1
            sender.submit([(packet(120, level), target), (packet(121, level), target)])
            while True:
                try:
                    data = receiver.recvfrom(600)[0]
                except BlockingIOError:
                    break
                observed.append((time.monotonic(), data))
            time.sleep(.004)
        time.sleep(.06)
        while True:
            try:
                data = receiver.recvfrom(600)[0]
            except BlockingIOError:
                break
            observed.append((time.monotonic(), data))
        report = sender.close()
        self.assertEqual(len(observed), 2 * report['sent_batches'])
        for first, second in zip(observed[::2], observed[1::2]):
            self.assertEqual(first[1][18:], second[1][18:])
        self.assertEqual(observed[-1][1], packet(121, level))
        self.assertEqual(report['submitted_batches'], report['sent_batches'] + report['stale_batches'])
        self.assertGreater(report['stale_batches'], report['sent_batches'])
        self.assertGreater(report['active_average_fps'], 27)
        self.assertLess(report['active_average_fps'], 32)


if __name__ == '__main__':
    unittest.main()
