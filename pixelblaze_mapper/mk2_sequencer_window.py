"""Owned Chromium app window; all OS work runs outside TouchDesigner's thread.

``show(rect)`` accepts physical desktop pixels, including negative monitor origins.
``hide()`` retains the page/process. Neither method waits for the browser. Status:
idle/opening/visible/hidden/error. A closed owned window is relaunched on next show.
An unsuccessful launch is latched to prevent a recurring caller creating tabs.

Ownership requires title AND browser executable AND a process creation identity
captured from our own launch (PID alone is insufficient). Existing personal browser
windows, even those with the same title, are never adopted. An atomic receipt allows
a restarted owner to recover a previously launched, still-identical process.

API references:
https://www.chromium.org/developers/creating-and-using-profiles/
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setthreaddpiawarenesscontext
https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew
"""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import threading
import time


URL = 'http://127.0.0.1:9991/?mk2_window=sequencer'
TITLE = 'MK2 Sequencer'
_TITLES = {TITLE, TITLE+' - Microsoft Edge', TITLE+' - Google Chrome'}
_BROWSERS = {'msedge.exe', 'chrome.exe'}


def _rect(value):
    if not isinstance(value, dict):
        raise ValueError('Fensterposition muss x, y, width und height enthalten.')
    result = {}
    for name in ('x', 'y', 'width', 'height'):
        number = value.get(name)
        if type(number) not in (int, float) or not -1000000 <= number <= 1000000 or int(number) != number:
            raise ValueError('Ungültige Fensterkoordinate: '+name)
        result[name] = int(number)
    if not 160 <= result['width'] <= 32768 or not 100 <= result['height'] <= 32768:
        raise ValueError('Fenstergröße muss zwischen 160×100 und 32768×32768 Pixeln liegen.')
    return result


class _NativeWindows:
    def __init__(self):
        if os.name != 'nt':
            raise RuntimeError('Das Sequencer-Appfenster benötigt Windows.')
        self.u = ctypes.WinDLL('user32', use_last_error=True)
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        signatures = (
            (self.u.EnumWindows, [self.callback_type, wintypes.LPARAM], wintypes.BOOL),
            (self.u.IsWindow, [wintypes.HWND], wintypes.BOOL),
            (self.u.IsWindowVisible, [wintypes.HWND], wintypes.BOOL),
            (self.u.IsIconic, [wintypes.HWND], wintypes.BOOL),
            (self.u.GetWindowTextW, [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            (self.u.GetWindowThreadProcessId, [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
            (self.u.SetThreadDpiAwarenessContext, [ctypes.c_void_p], ctypes.c_void_p),
            (self.u.ShowWindowAsync, [wintypes.HWND, ctypes.c_int], wintypes.BOOL),
            (self.u.SetWindowPos, [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL),
            (self.u.GetWindowRect, [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
            (self.k.OpenProcess, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            (self.k.CloseHandle, [wintypes.HANDLE], wintypes.BOOL),
            (self.k.QueryFullProcessImageNameW, [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                               ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            (self.k.GetProcessTimes, [wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4, wintypes.BOOL),
        )
        for function, args, result in signatures:
            function.argtypes, function.restype = args, result

    def identity(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            return None
        try:
            size = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(size.value)
            times = [wintypes.FILETIME() for _ in range(4)]
            if (not self.k.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) or
                    not self.k.GetProcessTimes(handle, *(ctypes.byref(item) for item in times))):
                return None
            created = times[0].dwLowDateTime | (times[0].dwHighDateTime << 32)
            return created, os.path.normcase(path.value)
        finally:
            self.k.CloseHandle(handle)

    def window(self, hwnd):
        if not self.u.IsWindow(hwnd):
            return None
        title = ctypes.create_unicode_buffer(1024)
        self.u.GetWindowTextW(hwnd, title, len(title))
        if title.value not in _TITLES:
            return None
        pid = wintypes.DWORD()
        self.u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        identity = self.identity(pid.value)
        if not identity or Path(identity[1]).name.lower() not in _BROWSERS:
            return None
        return dict(hwnd=hwnd, pid=pid.value, identity=identity, title=title.value)

    def windows(self):
        found = []

        @self.callback_type
        def collect(hwnd, _):
            item = self.window(hwnd)
            if item:
                found.append(item)
            return True

        if not self.u.EnumWindows(collect, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return found

    def exists(self, hwnd):
        return bool(self.u.IsWindow(hwnd))

    def _check(self, window):
        current = self.window(window['hwnd'])
        if not current or current['pid'] != window['pid'] or current['identity'] != window['identity']:
            raise RuntimeError('Fensterbesitz konnte nicht bestätigt werden.')

    @contextmanager
    def _physical_pixels(self):
        # PER_MONITOR_AWARE_V2, thread-local: never change TD's process DPI mode.
        previous = self.u.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        if not previous:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            yield
        finally:
            self.u.SetThreadDpiAwarenessContext(previous)

    def place(self, window, rect):
        self._check(window)
        hwnd = window['hwnd']
        with self._physical_pixels():
            self.u.ShowWindowAsync(hwnd, 9)  # Restore a minimized/maximized app.
            expected = (rect['x'], rect['y'], rect['width'], rect['height'])
            for _ in range(12):
                self._check(window)
                # ASYNCWINDOWPOS | NOACTIVATE | SHOWWINDOW; HWND_TOP raises our app.
                if not self.u.SetWindowPos(hwnd, 0, *expected, 0x4000 | 0x0010 | 0x0040):
                    raise ctypes.WinError(ctypes.get_last_error())
                time.sleep(.05)
                actual = wintypes.RECT()
                if self.u.GetWindowRect(hwnd, ctypes.byref(actual)):
                    got = (actual.left, actual.top, actual.right-actual.left, actual.bottom-actual.top)
                    if got == expected:
                        return
            raise RuntimeError('Windows hat die gewünschte Monitorposition nicht übernommen.')

    def matches(self, window, rect):
        self._check(window)
        hwnd = window['hwnd']
        if not self.u.IsWindowVisible(hwnd) or self.u.IsIconic(hwnd):
            return False
        with self._physical_pixels():
            actual = wintypes.RECT()
            if not self.u.GetWindowRect(hwnd, ctypes.byref(actual)):
                return False
            return (actual.left, actual.top, actual.right-actual.left, actual.bottom-actual.top) == (
                rect['x'], rect['y'], rect['width'], rect['height'])

    def hide(self, window):
        self._check(window)
        # ShowWindowAsync returns the previous visibility, not a success flag.
        self.u.ShowWindowAsync(window['hwnd'], 0)
        for _ in range(12):
            if not self.u.IsWindowVisible(window['hwnd']):
                return
            self._check(window)
            time.sleep(.05)
        raise RuntimeError('Windows hat das eigene Sequencer-Fenster nicht ausgeblendet.')

    def browser(self):
        import winreg
        candidates = []
        for executable in ('msedge.exe', 'chrome.exe'):
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                    try:
                        with winreg.OpenKey(hive, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\'+executable,
                                            0, winreg.KEY_READ | view) as key:
                            candidates.append(Path(winreg.QueryValue(key, None).strip('"')))
                    except OSError:
                        pass
        for root in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA'):
            if os.environ.get(root):
                candidates.extend(Path(os.environ[root])/part for part in
                                  ('Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe'))
        for path in candidates:
            if path.name.lower() in _BROWSERS and path.is_file():
                return path.resolve()
        raise RuntimeError('Microsoft Edge oder Google Chrome wurde nicht gefunden.')

    def launch(self, profile, rect):
        executable = self.browser()
        profile.mkdir(parents=True, exist_ok=True)
        args = [str(executable), '--user-data-dir='+str(profile), '--app='+URL,
                '--no-first-run', '--no-default-browser-check', '--disable-background-mode',
                '--window-position=%d,%d' % (rect['x'], rect['y']),
                '--window-size=%d,%d' % (rect['width'], rect['height'])]
        return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, shell=False, close_fds=True)


class SequencerWindow:
    """One reusable owner; show/hide are nonblocking and coalesce pending requests."""
    START_TIMEOUT = 20.
    POLL_SECONDS = .1

    def __init__(self, project_dir):
        self.profile = Path(project_dir).resolve()/'.controller-runtime'/'mk2-sequencer'
        self.receipt = self.profile.parent/'mk2-sequencer-owner.json'
        self._receipt_loaded = False
        self._condition = threading.Condition()
        self._desired = ('hide', None)
        self._revision = 0
        self._worker = None
        self._native = None
        self._known = {}
        self._window = None
        self._process = None
        self._launch_allowed = True
        self._deadline = 0.
        self._placed = None
        self._status, self._error = 'idle', ''

    @property
    def status(self):
        with self._condition:
            return self._status

    @property
    def error(self):
        with self._condition:
            return self._error

    def _state(self, status, error=''):
        with self._condition:
            self._status, self._error = status, error

    def show(self, rect):
        try:
            rect = _rect(rect)
        except (ValueError, OverflowError) as error:
            self._state('error', str(error))
            return
        self._request('show', rect)

    def hide(self):
        self._request('hide', None)

    def _request(self, action, rect):
        with self._condition:
            self._desired = action, rect
            self._revision += 1
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._run, name='MK2-Sequencer-Window', daemon=True)
                self._worker.start()
            self._condition.notify_all()

    def _owned(self):
        candidates = [w for w in self._native.windows()
                      if w['title'] in _TITLES and Path(w['identity'][1]).name.lower() in _BROWSERS
                      and self._known.get(w['pid']) == w['identity']]
        if self._window:
            match = next((w for w in candidates if w['hwnd'] == self._window['hwnd']), None)
            if match:
                return match
        return candidates[0] if candidates else None

    def _load_receipt(self):
        self._receipt_loaded = True
        try:
            if self.receipt.stat().st_size > 65536:
                return
            data = json.loads(self.receipt.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or data.get('schema_version') != 1 or
                    data.get('profile') != str(self.profile)):
                return
            owners = data.get('owners')
            if not isinstance(owners, list) or len(owners) > 64:
                return
            for owner in owners:
                if not isinstance(owner, dict):
                    continue
                pid, created, executable = owner.get('pid'), owner.get('created'), owner.get('executable')
                if (type(pid) is not int or pid <= 0 or type(created) is not int or created <= 0 or
                        not isinstance(executable, str) or Path(executable).name.lower() not in _BROWSERS):
                    continue
                identity = (created, executable)
                if self._native.identity(pid) == identity:
                    self._known[pid] = identity
        except (OSError, ValueError, TypeError):
            pass  # Malformed/stale receipts never grant ownership.

    def _save_receipt(self):
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        owners = [dict(pid=pid, created=identity[0], executable=identity[1])
                  for pid, identity in self._known.items() if self._native.identity(pid) == identity]
        data = dict(schema_version=1, profile=str(self.profile), owners=owners[-64:])
        temporary = self.receipt.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        temporary.replace(self.receipt)

    def _step(self, action, rect):
        """One worker-only step. True requests bounded startup polling."""
        if self._native is None:
            self._native = _NativeWindows()
        if not self._receipt_loaded:
            self._load_receipt()
        window = self._owned()
        if window:
            self._window = window
            self._launch_allowed = True
            self._deadline = 0.
            if action == 'hide':
                self._native.hide(window)
                self._placed = None
                self._state('hidden')
            else:
                if self._placed != (window['hwnd'], rect) or not self._native.matches(window, rect):
                    self._native.place(window, rect)
                    self._placed = (window['hwnd'], dict(rect))
                self._state('visible')
            return False
        self._placed = None
        if self._window and self._native.exists(self._window['hwnd']):
            # A title/identity change is not evidence that the old app closed.
            # Do not touch it or open another window while it still exists.
            self._state('error', 'Bestehendes Fenster hat seinen bestätigten Titel oder Besitzer geändert.')
            return False
        self._window = None
        if action == 'show' and self._launch_allowed:
            self._launch_allowed = False  # Set before launch, including failure.
            self._process = self._native.launch(self.profile, rect)
            identity = self._native.identity(self._process.pid)
            if identity is None or Path(identity[1]).name.lower() not in _BROWSERS:
                raise RuntimeError('Browser-Prozessbesitz konnte nicht bestätigt werden; kein weiterer Start.')
            self._known[self._process.pid] = identity
            self._save_receipt()
            self._deadline = time.monotonic()+self.START_TIMEOUT
            self._state('opening')
        if self._deadline:
            if time.monotonic() < self._deadline:
                return True  # Also finish discovery after hide during startup.
            self._deadline = 0.
            raise RuntimeError('Das eigene Fenster „MK2 Sequencer“ wurde nicht gefunden; kein weiterer Start.')
        if action == 'hide':
            self._state('hidden')
        elif self.status != 'error':
            self._state('error', 'Browserstart nicht bestätigt. Kein weiterer Start, um doppelte Fenster zu vermeiden.')
        return False

    def _run(self):
        revision = -1
        polling = False
        while True:
            with self._condition:
                if revision == self._revision:
                    self._condition.wait(self.POLL_SECONDS if polling else None)
                if revision == self._revision and not polling:
                    continue
                revision = self._revision
                action, rect = self._desired
            try:
                polling = self._step(action, rect)
            except Exception as error:
                polling = False
                self._state('error', str(error))


__all__ = ['SequencerWindow']
