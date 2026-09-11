"""Passive timings around single-LED capture and native camera reads."""
from collections import deque
import time


PHASES = ('dark_before_ms', 'send_on_ms', 'detect_ms', 'send_off_ms', 'dark_after_ms')


class CaptureTimings:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.active = False
        self.samples = 0
        self.recent = deque(maxlen=20)
        self.totals = {}

    def begin(self):
        self.active = True
        self.started = self.phase_started = self.clock()
        self.phase = 'dark_before_ms'
        self.values = dict.fromkeys(PHASES, 0.0)
        self.values.update(camera_read_ms=0.0, camera_frames=0)

    def enter(self, phase):
        if self.active:
            now = self.clock()
            self.values[self.phase] += 1000 * (now - self.phase_started)
            self.phase_started, self.phase = now, phase

    def read(self, action):
        if not self.active:
            return action()
        started = self.clock()
        try:
            return action()
        finally:
            self.values['camera_read_ms'] += 1000 * (self.clock() - started)
            self.values['camera_frames'] += 1

    def finish(self, *, completed=True, timeout_seconds=None):
        self.enter(self.phase)
        values = dict(self.values, cycle_ms=1000 * (self.phase_started - self.started))
        self.active = False
        if completed:
            self.samples += 1
            self.recent.append(values)
            for key, value in values.items():
                self.totals[key] = self.totals.get(key, 0.0) + value
        rounded = lambda row: {key: round(value, 3) for key, value in row.items()}
        return {
            'completed_samples': self.samples,
            'last_completed': completed,
            'last': rounded(values),
            'mean': rounded({key: value / self.samples for key, value in self.totals.items()}) if self.samples else {},
            'recent_mean': rounded({key: sum(row[key] for row in self.recent) / len(self.recent)
                                    for key in values}) if self.recent else {},
            'search_timeout_ms': round(timeout_seconds * 1000, 3) if timeout_seconds is not None else None,
        }


class TimedBackend:
    def __init__(self, backend, timing):
        self.backend, self.timing = backend, timing

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def set_led(self, index, on):
        self.timing.enter('send_on_ms' if on else 'send_off_ms')
        try:
            return self.backend.set_led(index, on)
        finally:
            self.timing.enter('detect_ms' if on else 'dark_after_ms')
