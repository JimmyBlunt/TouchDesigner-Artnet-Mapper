"""Camera/process fakes only. No MariMapper native imports or camera access."""
import io
import json
import subprocess
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pixelblaze_mapper import camera_probe as bridge
from pixelblaze_mapper import camera_probe_worker as worker


def fake_native(event):
    image = SimpleNamespace(shape=(480, 640, 3), private_pixels="not serializable pixels")
    cam = SimpleNamespace(read=Mock(return_value=image), get_exposure=Mock(return_value=-10),
                          reset=Mock(), device=SimpleNamespace(release=Mock()))
    api = SimpleNamespace(camera=Mock(return_value=cam), dark=Mock(return_value=True),
        detect=Mock(return_value=SimpleNamespace(u=lambda: .25, v=lambda: .75)),
        draw=Mock(return_value=image), show=Mock(side_effect=lambda _: event.set()), destroy=Mock())
    return api, cam


class WorkerTests(unittest.TestCase):
    def test_native_import_precedes_blocking_stdin_thread(self):
        events = []
        with patch.object(worker, '_emit'), \
             patch.object(worker, '_native_api', side_effect=lambda: events.append('native') or object()), \
             patch.object(worker.threading, 'Thread') as thread, \
             patch.object(worker, 'run_probe', return_value=0) as run:
            thread.return_value.start.side_effect = lambda: events.append('stdin')
            self.assertEqual(worker.main(['--confirm-camera']), 0)
        self.assertEqual(events, ['native', 'stdin'])
        self.assertIn('native', run.call_args.kwargs)

    def run_fake(self, mutate=None):
        event = threading.Event()
        api, cam = fake_native(event)
        if mutate:
            mutate(api, cam)
        messages = []
        result = worker.run_probe(bridge.prepare_camera_probe(), confirmed=True,
            stop_event=event, native=api, emit=messages.append)
        return result, messages, api, cam

    def test_unconfirmed_and_default_cli_do_not_import_native(self):
        with patch.object(worker, '_native_api') as native, patch.object(worker, '_emit') as emit:
            with self.assertRaises(ValueError):
                worker.run_probe(bridge.prepare_camera_probe())
            self.assertEqual(worker.main([]), 0)
            native.assert_not_called()
            self.assertFalse(emit.call_args.args[0]['camera_opened'])

    def test_cancel_before_start_opens_nothing(self):
        event = threading.Event()
        event.set()
        with patch.object(worker, '_native_api') as native:
            messages = []
            self.assertEqual(worker.run_probe(bridge.prepare_camera_probe(), confirmed=True,
                stop_event=event, emit=messages.append), 0)
            native.assert_not_called()
            self.assertEqual(messages[-1]['frames'], 0)

    def test_real_detection_contract_and_only_scalar_metadata(self):
        result, messages, api, cam = self.run_fake()
        self.assertEqual(result, 0)
        api.camera.assert_called_once_with(0)
        wrapped, exposure = api.dark.call_args.args
        self.assertIs(wrapped._camera, cam)
        self.assertEqual(exposure, -10)
        api.detect.assert_called_once_with(cam.read.return_value, 160)
        api.draw.assert_called_once_with(cam.read.return_value, api.detect.return_value)
        self.assertEqual(messages[-2], dict(state='running', phase='preview', frames=1, height=480,
            width=640, detected=True, u=.25, v=.75))
        for item in messages:
            self.assertTrue(all(value is None or type(value) in (bool, int, float, str)
                                for value in item.values()))
        self.assertNotIn('pixels', json.dumps(messages))
        cam.reset.assert_called_once()
        cam.device.release.assert_called_once()
        api.destroy.assert_called_once()

    def test_exposure_rejection_reported_not_claimed_applied(self):
        _, messages, _, _ = self.run_fake(lambda api, cam: setattr(api.dark, 'return_value', False))
        self.assertFalse(next(m for m in messages if m['state'] == 'ready')['exposure_applied'])

    def test_escape_is_cooperative_cleanup(self):
        result, messages, api, cam = self.run_fake(lambda api, cam: setattr(api.show, 'side_effect', KeyboardInterrupt))
        self.assertEqual(result, 0)
        self.assertEqual(messages[-1]['reason'], 'escape_or_interrupt')
        cam.device.release.assert_called_once()
        api.destroy.assert_called_once()

    def test_camera_read_failure_still_cleans_up(self):
        result, messages, api, cam = self.run_fake(lambda api, cam: setattr(cam.read, 'side_effect', RuntimeError('read failed')))
        self.assertEqual(result, 1)
        self.assertEqual(messages[-1]['state'], 'error')
        self.assertIn('read failed', messages[-2]['error'])
        cam.reset.assert_called_once()
        cam.device.release.assert_called_once()
        api.destroy.assert_called_once()

    def test_cleanup_failures_independent(self):
        def errors(api, cam):
            cam.reset.side_effect = RuntimeError('reset')
            cam.device.release.side_effect = RuntimeError('release')
        result, messages, api, cam = self.run_fake(errors)
        self.assertEqual(result, 1)
        self.assertFalse(messages[-1]['cleanup_confirmed'])
        self.assertIn('camera_reset', messages[-1]['cleanup_errors'])
        self.assertIn('camera_release', messages[-1]['cleanup_errors'])
        api.destroy.assert_called_once()

    def test_stop_eof_and_invalid_protocol(self):
        for value in ('', '{"command":"stop"}\n', 'not json\n', 'x' * 5000, '{"command":"scan"}\n'):
            with self.subTest(value=value[:50]):
                event = threading.Event()
                worker._listen_for_stop(io.StringIO(value), event)
                self.assertTrue(event.is_set())

    def test_unreviewed_install_rejected_before_native_import(self):
        dist = SimpleNamespace(version='9.0', read_text=lambda _: '{}')
        with patch.object(worker.importlib.metadata, 'distribution', return_value=dist):
            with self.assertRaisesRegex(RuntimeError, 'unreviewed'):
                worker._native_api()

    def test_metadata_throttled_while_all_frames_are_displayed(self):
        event = threading.Event()
        api, cam = fake_native(event)
        seen = []
        def show(image):
            seen.append(image)
            if len(seen) == 20:
                event.set()
        api.show.side_effect = show
        clock = Mock(side_effect=[i * .01 for i in range(20)])
        messages = []
        worker.run_probe(bridge.ProbePlan(), confirmed=True, stop_event=event,
                         native=api, emit=messages.append, clock=clock)
        self.assertEqual(len(seen), 20)
        self.assertEqual(sum(item['state'] == 'running' for item in messages), 1)
        self.assertEqual(messages[-1]['frames'], 20)


class BridgeTests(unittest.TestCase):
    def tearDown(self):
        bridge._active = None

    def test_prepare_validation_no_launch(self):
        with patch.object(bridge.subprocess, 'Popen') as launch:
            self.assertEqual(bridge.prepare_camera_probe(0, -10, 160), bridge.ProbePlan())
            for args in ((True, -10, 1), (-1, -10, 1), (0, -10, 255),
                         (0, -10, -1), (0, 1.5, 1), (0, 'x', 1)):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    bridge.prepare_camera_probe(*args)
            launch.assert_not_called()

    def test_launch_requires_confirmation_and_fixed_argv(self):
        with patch.object(bridge.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):
                bridge.start_camera_probe(bridge.ProbePlan())
            launch.assert_not_called()
        process = Mock(stdin=io.StringIO(), stdout=io.StringIO(), stderr=io.StringIO())
        process.poll.return_value = None
        with patch.object(bridge.INTERPRETER.__class__, 'is_file', return_value=True), \
             patch.object(bridge.subprocess, 'Popen', return_value=process) as launch:
            handle = bridge.start_camera_probe(bridge.ProbePlan(), confirmed=True)
            for thread in handle.readers:
                thread.join(1)
            args, kwargs = launch.call_args
            self.assertEqual(args[0], bridge.probe_argv(bridge.ProbePlan()))
            self.assertFalse(kwargs['shell'])
            self.assertEqual(args[0][0], str(bridge.INTERPRETER))
            self.assertIn('-B', args[0])
            self.assertNotIn('scanner', ' '.join(args[0]))
            with self.assertRaisesRegex(RuntimeError, 'already running'):
                bridge.start_camera_probe(bridge.ProbePlan(), confirmed=True)
            self.assertEqual(launch.call_count, 1)
            handle.startup_done.set()

    def test_startup_watchdog_preserves_timeout_phase_after_clean_stop(self):
        process = Mock()
        process.poll.return_value = None
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        handle.status.update(state='configuring', phase='camera_warmup')
        with patch.object(bridge, 'stop_camera_probe') as stop:
            bridge._startup_watchdog(handle, 0)
            stop.assert_called_once_with(handle)
        handle.status.update(state='stopped', cleanup_confirmed=True)
        process.poll.return_value = 0
        status = bridge.poll_camera_probe(handle)
        self.assertEqual(status['state'], 'startup_timeout')
        self.assertEqual(status['startup_timeout_phase'], 'camera_warmup')
        self.assertIn('camera_warmup', status['error'])

    def test_startup_watchdog_does_not_stop_working_preview(self):
        handle = bridge.ProbeHandle(Mock(), bridge.ProbePlan())
        handle.startup_done.set()
        with patch.object(bridge, 'stop_camera_probe') as stop:
            bridge._startup_watchdog(handle, 0)
            stop.assert_not_called()

    def test_cooperative_stop_protocol(self):
        process = Mock(stdin=Mock())
        process.poll.side_effect = [None, 0]
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        handle.status.update(state='stopped', cleanup_confirmed=True)
        status = bridge.stop_camera_probe(handle)
        process.stdin.write.assert_called_once_with('{"command":"stop"}\n')
        process.stdin.flush.assert_called_once()
        process.stdin.close.assert_called_once()
        process.terminate.assert_not_called()
        self.assertTrue(status['cleanup_confirmed'])
        self.assertIsNone(status['settings_restored'])

    def test_forced_stop_overrides_stale_cleanup_claim(self):
        process = Mock(stdin=Mock())
        process.poll.side_effect = [None, 1]
        process.wait.side_effect = [subprocess.TimeoutExpired('probe', 0), 1]
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        handle.status.update(state='stopped', cleanup_confirmed=True)
        status = bridge.stop_camera_probe(handle, grace_seconds=0)
        process.terminate.assert_called_once()
        self.assertEqual(status['state'], 'forced_stopped')
        self.assertFalse(status['cleanup_confirmed'])
        self.assertTrue(status['forced_stop'])

    def test_forced_stop_failure_not_reported_stopped(self):
        process = Mock(stdin=Mock())
        process.poll.return_value = None
        process.wait.side_effect = subprocess.TimeoutExpired('probe', 0)
        process.terminate.side_effect = OSError('denied')
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        self.assertEqual(bridge.stop_camera_probe(handle, grace_seconds=0)['state'], 'stop_failed')

    def test_stdout_metadata_whitelist_and_no_disk_output(self):
        message = dict(protocol=bridge.PROTOCOL, state='running', frames=3, pixels=[1, 2],
                       contours=[[1]], arbitrary='no', u=.2)
        process = Mock(stdout=io.StringIO(json.dumps(message) + '\n'))
        process.poll.return_value = None
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        bridge._read_stdout(handle)
        self.assertEqual(handle.status['frames'], 3)
        self.assertFalse({'pixels', 'contours', 'arbitrary'} & handle.status.keys())
        self.assertFalse(handle.status['image_storage'])
        self.assertFalse(handle.status['hardware_output'])

    def test_dead_process_without_final_message_is_unconfirmed(self):
        process = Mock()
        process.poll.return_value = 1
        status = bridge.poll_camera_probe(bridge.ProbeHandle(process, bridge.ProbePlan()))
        self.assertEqual(status['state'], 'exited_unconfirmed')
        self.assertFalse(status['cleanup_confirmed'])

    def test_invalid_stop_timeout(self):
        for value in (-1, 11, float('nan'), float('inf'), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bridge.stop_camera_probe(None, grace_seconds=value)

    def test_real_pipe_protocol_with_inert_child_no_native_camera(self):
        # Real OS pipes/threads, but the child is ONLY this fixed inert script.
        source = ('import sys,json\n'
                  'line=sys.stdin.readline()\n'
                  'assert json.loads(line)=={"command":"stop"}\n'
                  'print(json.dumps({"protocol":"pixelblaze-camera-probe-v1",'
                  '"state":"stopped","frames":0,"cleanup_confirmed":True}),flush=True)\n')
        process = subprocess.Popen([sys.executable, '-B', '-u', '-c', source], shell=False,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        handle = bridge.ProbeHandle(process, bridge.ProbePlan())
        for target in (bridge._read_stdout, bridge._drain_stderr):
            thread = threading.Thread(target=target, args=(handle,), daemon=True)
            handle.readers.append(thread)
            thread.start()
        status = bridge.stop_camera_probe(handle, grace_seconds=3)
        self.assertEqual(status['returncode'], 0)
        self.assertEqual(status['state'], 'stopped')
        self.assertTrue(status['cleanup_confirmed'])
        self.assertFalse(status['forced_stop'])


if __name__ == '__main__':
    unittest.main()
