"""Mock acceptance for the owned app window; never opens a browser/OS window."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import threading
import time
from unittest.mock import Mock, patch

from pixelblaze_mapper import mk2_sequencer_window as module


RECT = dict(x=-1920, y=-120, width=1920, height=1080)


class FakeNative:
    def __init__(self):
        self.items, self.launches, self.places, self.hides = [], [], [], []
        self.identities = {100:(1234, 'msedge.exe'), 101:(2345, 'chrome.exe')}
        self.pid = 100

    def windows(self):
        return list(self.items)

    def exists(self, hwnd):
        return any(item['hwnd'] == hwnd for item in self.items)

    def identity(self, pid):
        return self.identities.get(pid)

    def launch(self, profile, rect):
        self.launches.append((profile, dict(rect)))
        return SimpleNamespace(pid=self.pid)

    def expose(self, hwnd=1, pid=100, title=module.TITLE, identity=None):
        self.items.append(dict(hwnd=hwnd, pid=pid, title=title,
                               identity=identity or self.identities.get(pid, (9999, 'chrome.exe'))))

    def place(self, window, rect):
        self.places.append((window['hwnd'], dict(rect)))

    def matches(self, window, rect):
        return bool(self.places) and self.places[-1] == (window['hwnd'], rect)

    def hide(self, window):
        self.hides.append(window['hwnd'])


class WindowLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.window = module.SequencerWindow(self.temp.name)
        self.api = FakeNative()
        self.window._native = self.api
        self.clock = patch.object(module.time, 'monotonic', return_value=10.)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def opened(self):
        self.assertTrue(self.window._step('show', RECT))
        self.api.expose()
        self.assertFalse(self.window._step('show', RECT))
        self.assertEqual(self.window.status, 'visible')

    def test_launch_once_while_pending_then_reuse_and_move(self):
        for _ in range(15):
            self.assertTrue(self.window._step('show', RECT))
        self.assertEqual(len(self.api.launches), 1)
        self.assertEqual(self.window.status, 'opening')
        self.assertEqual(self.api.launches[0][0], Path(self.temp.name)/'.controller-runtime'/'mk2-sequencer')
        self.api.expose()
        self.window._step('show', RECT)
        self.window._step('show', RECT)
        self.assertEqual(self.api.places, [(1, RECT)])
        other = dict(x=0, y=100, width=2560, height=1440)
        self.window._step('show', other)
        self.assertEqual(self.api.places[-1], (1, other))
        self.assertEqual(len(self.api.launches), 1)

    def test_hide_and_show_preserve_process_and_page_without_reload(self):
        self.opened()
        self.window._step('hide', None)
        self.assertEqual(self.window.status, 'hidden')
        self.assertEqual(self.api.hides, [1])
        self.window._step('show', RECT)
        self.assertEqual(self.window.status, 'visible')
        self.assertEqual(len(self.api.places), 2)
        self.assertEqual(len(self.api.launches), 1)

    def test_show_restores_owned_window_if_user_moved_or_minimized_it(self):
        self.opened()
        self.api.matches = Mock(return_value=False)
        self.window._step('show', RECT)
        self.assertEqual(len(self.api.places), 2)
        self.assertEqual(len(self.api.launches), 1)

    def test_hide_before_start_does_not_launch_and_hide_during_start_waits_for_owner(self):
        self.window._step('hide', None)
        self.assertEqual(self.api.launches, [])
        self.window._step('show', RECT)
        self.assertTrue(self.window._step('hide', None))
        self.api.expose()
        self.window._step('hide', None)
        self.assertEqual(self.api.places, [])
        self.assertEqual(self.api.hides, [1])
        self.assertEqual(self.window.status, 'hidden')

    def test_closed_window_restarts_only_on_next_show(self):
        self.opened()
        self.api.items.clear()
        self.window._step('hide', None)
        self.assertEqual(len(self.api.launches), 1)
        self.api.pid = 101
        self.assertTrue(self.window._step('show', RECT))
        self.api.expose(hwnd=2, pid=101)
        self.window._step('show', RECT)
        self.assertEqual(len(self.api.launches), 2)
        self.assertEqual(self.api.places[-1][0], 2)

    def test_restarted_owner_reuses_receipt_verified_live_browser_without_launch(self):
        self.opened()
        receipt = json.loads(self.window.receipt.read_text())
        self.assertEqual(receipt['owners'][0]['pid'], 100)
        self.assertFalse(self.window.receipt.with_suffix('.tmp').exists())
        resumed = module.SequencerWindow(self.temp.name)
        resumed._native = self.api
        resumed._step('hide', None)
        self.assertEqual(self.api.hides, [1])
        resumed._step('show', RECT)
        self.assertEqual(resumed.status, 'visible')
        self.assertEqual(len(self.api.launches), 1)

    def test_receipt_reused_pid_or_executable_mismatch_does_not_grant_ownership(self):
        self.opened()
        self.api.identities[100] = (9999, 'chrome.exe')
        self.api.items[0]['identity'] = self.api.identity(100)
        resumed = module.SequencerWindow(self.temp.name)
        resumed._native = self.api
        resumed._step('hide', None)
        self.assertEqual(resumed._known, {})
        self.assertEqual(self.api.hides, [])

    def test_malformed_wrong_profile_and_wrong_schema_receipts_are_ignored(self):
        owner = dict(pid=100, created=1234, executable='msedge.exe')
        for data in ('not json', [], dict(schema_version=999, profile=str(self.window.profile), owners=[owner]),
                     dict(schema_version=1, profile='other profile', owners=[owner]),
                     dict(schema_version=1, profile=str(self.window.profile), owners='bad')):
            with self.subTest(data=data):
                self.window.receipt.parent.mkdir(parents=True, exist_ok=True)
                self.window.receipt.write_text(data if isinstance(data,str) else json.dumps(data))
                resumed = module.SequencerWindow(self.temp.name)
                resumed._native = self.api
                resumed._step('hide', None)
                self.assertEqual(resumed._known, {})
        self.assertFalse(self.api.launches)
        self.assertFalse(self.api.hides)

    def test_matching_title_personal_browser_is_never_adopted(self):
        self.api.expose(hwnd=66, pid=777)
        self.window._step('show', RECT)
        self.window._step('hide', None)
        self.assertEqual(self.api.places, [])
        self.assertEqual(self.api.hides, [])
        self.api.expose()
        self.window._step('show', RECT)
        self.assertEqual(self.api.places, [(1, RECT)])

    def test_wrong_title_wrong_executable_and_recycled_pid_fail_ownership(self):
        self.window._step('show', RECT)
        for item in (
            dict(hwnd=1,pid=100,title='MK2 Sequencer other',identity=(1234,'msedge.exe')),
            dict(hwnd=2,pid=100,title=module.TITLE,identity=(1234,'notepad.exe')),
            dict(hwnd=3,pid=100,title=module.TITLE,identity=(9999,'msedge.exe')),
        ):
            self.api.items = [item]
            self.window._step('show', RECT)
        self.assertEqual(self.api.places, [])
        self.assertEqual(len(self.api.launches), 1)

    def test_existing_hwnd_changed_title_or_owner_blocks_relaunch(self):
        self.opened()
        self.api.items[0]['title'] = 'Other page'
        self.window._step('show', RECT)
        self.assertEqual(self.window.status, 'error')
        self.assertEqual(len(self.api.launches), 1)
        self.window._step('hide', None)
        self.assertEqual(self.api.hides, [])

    def test_start_timeout_latches_without_tab_flood(self):
        self.window._step('show', RECT)
        with patch.object(module.time, 'monotonic', return_value=40.):
            with self.assertRaisesRegex(RuntimeError, 'nicht gefunden'):
                self.window._step('show', RECT)
            for _ in range(10):
                self.window._step('show', RECT)
        self.assertEqual(len(self.api.launches), 1)
        self.assertEqual(self.window.status, 'error')

    def test_launch_failure_latches_and_position_failure_can_be_retried_without_launch(self):
        self.api.launch = Mock(side_effect=OSError('launch denied'))
        with self.assertRaises(OSError):
            self.window._step('show', RECT)
        self.window._step('show', RECT)
        self.assertEqual(self.api.launch.call_count, 1)
        self.window._known[100] = self.api.identity(100)
        self.api.expose()
        self.api.place = Mock(side_effect=OSError('position denied'))
        with self.assertRaises(OSError):
            self.window._step('show', RECT)
        self.api.place.side_effect = None
        self.window._step('show', RECT)
        self.assertEqual(self.window.status, 'visible')
        self.assertEqual(self.api.launch.call_count, 1)

    def test_public_calls_only_schedule_and_coalesce_latest_rect(self):
        thread = Mock()
        thread.is_alive.return_value = True
        with patch.object(module.threading, 'Thread', return_value=thread) as create:
            with patch.object(self.window, '_step') as step:
                self.window.show(RECT)
                self.window.show(dict(RECT, x=-3840))
                self.window.hide()
                self.assertEqual(create.call_count, 1)
                self.assertTrue(create.call_args.kwargs['daemon'])
                self.assertEqual(thread.start.call_count, 1)
                self.assertEqual(self.window._desired, ('hide', None))
                step.assert_not_called()

    def test_real_worker_does_not_block_show_and_reports_launch_error(self):
        entered, release = threading.Event(), threading.Event()

        def blocked_launch(*args):
            entered.set()
            release.wait(2.)
            raise OSError('mock browser denied')

        self.api.launch = blocked_launch
        before = time.perf_counter()
        self.window.show(RECT)
        self.assertLess(time.perf_counter()-before, .25)
        self.assertTrue(entered.wait(1.))
        release.set()
        until = time.perf_counter()+1.
        while self.window.status != 'error' and time.perf_counter() < until:
            time.sleep(.005)
        self.assertEqual(self.window.status, 'error')
        self.assertIn('mock browser denied', self.window.error)

    def test_bad_rect_never_schedules_and_valid_negative_multimonitor_coordinates_survive(self):
        for invalid in (None, {}, dict(RECT,width=0), dict(RECT,height=99), dict(RECT,x=True),
                        dict(RECT,x=float('nan')), dict(RECT,y=float('inf')), dict(RECT,width=40000),
                        dict(RECT,x=2.5), dict(RECT,x='-1920')):
            with self.subTest(rect=invalid), patch.object(self.window, '_request') as request:
                self.window.show(invalid)
                self.assertEqual(self.window.status, 'error')
                request.assert_not_called()
        with patch.object(self.window, '_request') as request:
            self.window.show(RECT)
            request.assert_called_once_with('show', RECT)


class NativeBoundaryTests(unittest.TestCase):
    def test_launch_uses_argument_list_dedicated_profile_and_fixed_url_no_shell(self):
        native = object.__new__(module._NativeWindows)
        with TemporaryDirectory(prefix='mk2 space ') as directory:
            profile = Path(directory)/'profile with spaces'
            with patch.object(native, 'browser', return_value=Path('C:/Apps/Edge/msedge.exe')):
                with patch.object(module.subprocess, 'Popen') as launch:
                    native.launch(profile, RECT)
            args = launch.call_args.args[0]
            self.assertIsInstance(args, list)
            self.assertIn('--app='+module.URL, args)
            self.assertIn('--user-data-dir='+str(profile), args)
            self.assertIn('--window-position=-1920,-120', args)
            self.assertFalse(launch.call_args.kwargs['shell'])
            self.assertTrue(profile.is_dir())

    def test_place_verifies_physical_rect_and_restores_only_thread_dpi_context(self):
        native = object.__new__(module._NativeWindows)
        native.u = Mock()
        native.u.SetThreadDpiAwarenessContext.return_value = 123
        native._check = Mock()

        def get_rect(hwnd, pointer):
            rect = ctypes.cast(pointer, ctypes.POINTER(wintypes.RECT)).contents
            rect.left, rect.top = -1920, -120
            rect.right, rect.bottom = 0, 960
            return True

        native.u.GetWindowRect.side_effect = get_rect
        with patch.object(module.time, 'sleep'):
            native.place(dict(hwnd=7), RECT)
        args = native.u.SetWindowPos.call_args.args
        self.assertEqual(args[0:6], (7, 0, -1920, -120, 1920, 1080))
        self.assertEqual(args[6], 0x4000 | 0x10 | 0x40)
        self.assertEqual(native.u.SetThreadDpiAwarenessContext.call_args.args, (123,))
        self.assertEqual(native._check.call_count, 2)

    def test_wrong_applied_geometry_reports_failure_and_restores_dpi_context(self):
        native = object.__new__(module._NativeWindows)
        native.u = Mock()
        native.u.SetThreadDpiAwarenessContext.return_value = 456
        native._check = Mock()
        native.u.GetWindowRect.return_value = False
        with patch.object(module.time, 'sleep'), self.assertRaisesRegex(RuntimeError, 'Monitorposition'):
            native.place(dict(hwnd=7), RECT)
        self.assertEqual(native.u.SetThreadDpiAwarenessContext.call_args.args, (456,))

    def test_native_hide_checks_ownership_before_calling_windows(self):
        native = object.__new__(module._NativeWindows)
        native.u = Mock()
        native._check = Mock(side_effect=RuntimeError('ownership changed'))
        with self.assertRaises(RuntimeError):
            native.hide(dict(hwnd=2))
        native.u.ShowWindowAsync.assert_not_called()


if __name__ == '__main__':
    unittest.main()
