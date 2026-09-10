"""Current-view progress, independent of cumulative multi-view coverage."""
from collections import deque
import time


class ScanRate:
    """Observe completed counts only; never change scan timing or touch hardware."""
    def __init__(self):
        self.key = None
        self.samples = deque(maxlen=64)
        self.last_rate = None

    def update(self, status, now):
        key = status.get('directory')
        count = int(status.get('processed', 0) or 0)
        if key != self.key or (self.samples and count < self.samples[-1][1]):
            self.__init__()
            self.key = key
        if status.get('state') != 'capturing':
            return self.last_rate
        if self.samples and now <= self.samples[-1][0]:
            return self.last_rate
        self.samples.append((now, count))
        while len(self.samples) > 2 and self.samples[1][0] <= now - 10:
            self.samples.popleft()
        start, previous = self.samples[0]
        if now - start < 2:
            return None
        # Interpolate at the ten-second boundary for a stable rolling window.
        if start < now - 10 and len(self.samples) > 1:
            end, following = self.samples[1]
            previous += (following - previous) * (now - 10 - start) / (end - start)
            start = now - 10
        self.last_rate = max(0, (count - previous) / (now - start))
        return self.last_rate


_rates = {}


def presentation(status=None, planned_total=0, rate=None):
    status = status or {}
    total = max(0, int(status.get('total', planned_total) or 0))
    processed = min(total, max(0, int(status.get('processed', 0) or 0)))
    detected = min(processed, max(0, int(status.get('detected', 0) or 0)))
    fraction = processed / total if total else 0.0
    state = status.get('state', 'ready')
    labels = {
        'ready': 'BEREIT - Fortschritt der naechsten Ansicht',
        'starting': 'SCAN STARTET - Kamera und Objekt ruhig halten',
        'camera_starting': 'KAMERA WIRD VORBEREITET - noch keine LED geprueft',
        'capturing': 'SCAN LAEUFT - Kamera und Objekt ruhig halten',
        'movement_check': '100 % geprueft - Bewegungskontrolle laeuft',
        'view_ready': 'LED-Pruefung fertig - Kamera schliessen und Ansicht speichern',
        'complete': 'ANSICHT GESPEICHERT',
        'cancelled': 'SCAN ABGEBROCHEN - letzter bestaetigter Stand',
        'failed': 'SCAN FEHLGESCHLAGEN - letzter bestaetigter Stand',
        'connection_lost': 'VERBINDUNG VERLOREN - letzter bestaetigter Stand',
    }
    label = labels.get(state, 'SCAN: ' + str(state))
    if state == 'capturing' and status.get('current_source_index') is not None:
        label = 'AKTUELL: LED-ID %s (Position %s von %s)' % (
            status['current_source_index'], int(status['current_index']) + 1, total)
    if rate is not None:
        label += '  |  %s LEDs/s (aktuell)' % ('%.2f' % rate).replace('.', ',')
    elif state == 'capturing':
        label += '  |  LEDs/s wird gemessen'
    percent = ('%.1f' % (100 * fraction)).replace('.', ',')
    text = '%s\nGeprueft %d / %d  |  Erkannt %d  |  Nicht erkannt %d  |  %s %%' % (
        label, processed, total, detected, processed - detected, percent)
    color = (.9, .4, .2) if state in ('failed', 'cancelled', 'connection_lost') else (.2, .75, .9)
    if state == 'complete':
        color = (.25, .85, .55)
    return {'text': text, 'fraction': fraction, 'color': color}


def refresh(owner):
    node = owner.op('ui_panel/capture_progress')
    if node is None:
        return
    plan = owner.fetch('capture_plan', None) or {}
    total = len(plan.get('routing', {}).get('source_indices', []))
    status = owner.fetch('capture_status', None) or {}
    meter = _rates.setdefault(getattr(owner, 'path', 'guided_scan'), ScanRate())
    if not status:
        meter.__init__()
    rate = meter.update(status, time.monotonic())
    data = presentation(status, total, rate)
    node.par.text = data['text']
    track = owner.op('ui_panel/capture_progress_track')
    fill = track.op('fill') if track is not None and hasattr(track, 'op') else None
    if fill is not None:
        fill.par.w = 1120 * data['fraction']
        fill.par.display = data['fraction'] > 0
        fill.par.bgcolorr, fill.par.bgcolorg, fill.par.bgcolorb = data['color']


def install(owner, text):
    """Install just the read-only display; no dialog rebuild or hardware calls."""
    canvas = owner.op('ui_panel')
    text(canvas, 'capture_progress', '', 20, 128, 1120, 44, 14, (.7, .94, 1))
    track = text(canvas, 'capture_progress_track', '', 20, 114, 1120, 6)
    track.par.bgcolorr, track.par.bgcolorg, track.par.bgcolorb = .12, .18, .23
    text(track, 'fill', '', 0, 0, 1, 6)
    refresh(owner)
