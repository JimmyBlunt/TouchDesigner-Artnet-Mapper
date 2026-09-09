"""Monotonic, per-controller pacing without catch-up packet bursts.

The TD callback can only send as often as it runs. Deadlines prevent the old
elapsed-since-last-send gate from halving output near the requested frame rate;
they do not manufacture frames or promise hardware delivery.
"""
from math import floor, isfinite


class ControllerPacer:
    def __init__(self):
        self._deadlines = {}
        self._last_now = None

    def reset(self):
        self._deadlines.clear()
        self._last_now = None

    def due(self, configs, now):
        now = float(now)
        if not isfinite(now):
            raise ValueError('Clock must be finite')
        if self._last_now is not None and now < self._last_now:
            self.reset()
        self._last_now = now
        names = {item['name'] for item in configs}
        self._deadlines = {k: v for k, v in self._deadlines.items() if k in names}
        due = []
        for config in configs:
            name, rate = config['name'], float(config['rate'])
            if not isfinite(rate) or rate < 1 or rate > 120:
                raise ValueError('Controller rate must be 1..120')
            interval = 1.0 / rate
            previous = self._deadlines.get(name)
            deadline = previous[1] if previous and previous[0] == rate else now
            if now + 1e-9 < deadline:
                continue
            # Advance past missed slots but send only once this callback.
            steps = max(1, floor((now - deadline + 1e-9) / interval) + 1)
            self._deadlines[name] = (rate, deadline + steps * interval)
            due.append(config)
        return due


def install_source(source):
    """Apply a small fail-closed patch to the generated shared sender DAT."""
    marker = '# PER_CONTROLLER_DEADLINE_PACING'
    if marker in source:
        return source
    replacements = (
        ('_socket = None\n_enabled = False',
         marker + '\nfrom pixelblaze_mapper.sender_pacing import ControllerPacer\n'
         '_pacer = ControllerPacer()\n_socket = None\n_enabled = False'),
        ("    _target_override = target_override\n", "    _pacer.reset()\n    _target_override = target_override\n"),
        ("    if now - _last_send < 1.0 / max(1.0, max(config['rate'] for config in configs)):\n",
         "    configs = _pacer.due(configs, now)\n    if not configs:\n"),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Shared sender pacing patch does not match expected source')
        source = source.replace(old, new, 1)
    return source
