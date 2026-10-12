"""Native MIDI learn and live overrides. All access occurs on TD's main thread."""
from copy import deepcopy
from dataclasses import replace
import json
import math
from pathlib import Path
import time

from . import show_automation as automation

_manager = None
ACTIONS = ('play', 'pause', 'stop', 'previous', 'next', 'record', 'loop', 'release')


def default_config():
    names = ('brightness', 'speed', 'scale', 'zoom', 'intensity', 'contrast', 'trail', 'rotation_degrees')
    ranges = ((0, 1), (0, 4), (.1, 4), (.1, 4), (0, 2), (0, 2), (0, 1), (0, 360))
    bindings = [dict(label='Regler %d' % (i+1), target=name, minimum=lo, maximum=hi,
                     mode='absolute', source=None) for i, (name, (lo, hi)) in enumerate(zip(names, ranges))]
    bindings += [dict(label=label, target='@'+action, minimum=0, maximum=1, mode='absolute', source=None)
                 for action, label in zip(ACTIONS, ('Play', 'Pause', 'Stopp', 'Vorheriger Clip', 'Nächster Clip', 'Aufnahme', 'Loop an/aus', 'Live-Werte freigeben'))]
    return dict(device='', enabled=False, bindings=bindings)


def validate(config):
    result = dict(device=str(config.get('device', '')), enabled=bool(config.get('enabled', False)), bindings=[])
    for item in config.get('bindings', [])[:32]:
        target = str(item['target'])
        if target not in ('@'+x for x in ACTIONS) and not automation.recordable(target):
            raise ValueError('Unbekanntes MIDI-Ziel')
        lo, hi = float(item['minimum']), float(item['maximum'])
        if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
            raise ValueError('MIDI-Wertebereich: Minimum muss kleiner als Maximum sein')
        mode = item.get('mode', 'absolute')
        if mode not in ('absolute', 'relative_twos', 'relative_offset'):
            raise ValueError('Unbekannter Regler-Modus')
        source = item.get('source')
        if source is not None:
            if source.get('kind') not in ('cc', 'note') or not 1 <= int(source['channel']) <= 16 or not 0 <= int(source['number']) <= 127:
                raise ValueError('Ungültige MIDI-Adresse')
            source = dict(kind=source['kind'], channel=int(source['channel']), number=int(source['number']))
        result['bindings'].append(dict(label=str(item.get('label', target))[:80], target=target,
                                      minimum=lo, maximum=hi, mode=mode, source=source))
    return result


def decode(raw):
    data = list(raw)
    if len(data) < 3:
        return None
    status, number, value = (int(x) for x in data[:3])
    kind = {0xB0: 'cc', 0x90: 'note'}.get(status & 0xF0)
    if kind is None or not 0 <= number <= 127 or not 0 <= value <= 127:
        return None
    if kind == 'note' and not value:
        return None
    return dict(kind=kind, channel=(status & 15)+1, number=number), value


def mapped_value(binding, raw, current):
    lo, hi = binding['minimum'], binding['maximum']
    mode = binding['mode']
    if mode == 'absolute':
        return lo + raw / 127 * (hi-lo)
    delta = (raw if raw < 64 else raw-128) if mode == 'relative_twos' else raw-64
    return max(lo, min(hi, current + delta * (hi-lo)/127))


def live_values(cue_id):
    result = {}
    if _manager is not None and _manager.config['enabled'] and _manager.cue_id == cue_id:
        result.update(_manager.values)
    from .mk2_td import live_values as mk2_live_values
    result.update(mk2_live_values(cue_id))
    return result


def apply_plan(plan, cue_id):
    value = live_values(cue_id).get('brightness')
    return plan if value is None else replace(plan, brightness=0. if plan.blackout else max(0., min(1., value)))


class Manager:
    def __init__(self, owner):
        self.owner = owner
        self.config = default_config()
        self.learning = None
        self.learn_until = 0.
        self.last = ''
        self.error = ''
        self.cue_id = None
        self.values = {}
        self.devices = []
        self.last_scan = 0.
        self.last_action = {}
        self.config_revision = 0
        self.parameter_cache = None
        self.parameter_raw = None
        self.path = Path(__import__('td').project.folder)/'config'/'timeline_midi.json'
        try:
            self.config = validate(json.loads(self.path.read_text(encoding='utf-8')))
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)
        self.config_revision += 1

    def tick(self):
        if self.learning is not None and time.monotonic() > self.learn_until:
            self.learning = None
            self.error = 'MIDI-Lernen nach 30 Sekunden beendet. Bei Bedarf erneut starten.'
        t = self.owner.op('callbacks').module
        try:
            cue_id = t.runtime().cue.id
            if self.cue_id != cue_id:
                self.values.clear()
                self.cue_id = cue_id
        except Exception:
            self.values.clear()
        if time.monotonic()-self.last_scan > 1:
            self.last_scan = time.monotonic()
            import td
            table = td.op('/local/midi/midi_inputs')
            self.devices = [str(row[0]) for row in table.rows() if row and str(row[0]).strip()]
            receiver = self.owner.op('timeline_midi_in')
            active = bool(self.config['enabled'] and self.config['device'] in self.devices)
            receiver.par.active = active
            if not active:
                self.values.clear()

    def snapshot(self):
        return dict(config=deepcopy(self.config), devices=list(self.devices), learning=self.learning,
                    last=self.last, error=self.error, revision=self.config_revision, live=dict(self.values))

    def command(self, command):
        action = command['action']
        if action == 'midi_config':
            if command.get('midi_revision') != self.config_revision:
                raise ValueError('MIDI-Mapping wurde anderswo geändert. Dialog neu öffnen.')
            config = validate(command['config'])
            if config['device'] != self.config['device']:
                self.values.clear()
            self.config = config
            self.learning = None
            if not config['enabled']:
                self.values.clear()
            self.configure_device()
            self.save()
        elif action == 'midi_learn':
            index = command.get('index')
            if index is not None and (not isinstance(index, int) or not 0 <= index < len(self.config['bindings'])):
                raise ValueError('Ungültiger MIDI-Lernplatz')
            if index is not None and (not self.config['enabled'] or self.config['device'] not in self.devices):
                raise ValueError('Zum Lernen zuerst einen verfügbaren MIDI-Eingang wählen und MIDI aktivieren.')
            self.learning = index
            self.learn_until = time.monotonic()+30
        elif action == 'midi_release':
            self.values.clear()
        else:
            raise ValueError('Unbekannter MIDI-Befehl')
        self.error = ''

    def configure_device(self):
        receiver = self.owner.op('timeline_midi_in')
        receiver.par.active = False
        table = self.owner.op('timeline_midi_device')
        table.clear()
        table.appendRow(['id', 'indevice', 'outdevice', 'definition', 'channel'])
        table.appendRow([1, self.config['device'], '', '', 1])
        self.last_scan = 0
        self.tick()

    def receive(self, raw):
        decoded = decode(raw)
        if decoded is None or not self.config['enabled']:
            return
        source, value = decoded
        self.last = '%s %d · Kanal %d · %d' % (source['kind'].upper(), source['number'], source['channel'], value)
        if self.learning is not None:
            # One physical control owns one destination; relearning moves it.
            for item in self.config['bindings']:
                if item['source'] == source:
                    item['source'] = None
            self.config['bindings'][self.learning]['source'] = source
            self.learning = None
            self.save()
            return
        self.tick()
        e, t = self.owner.op('editor_callbacks').module, self.owner.op('callbacks').module
        for index, binding in enumerate(self.config['bindings']):
            if binding['source'] != source:
                continue
            target = binding['target']
            if target.startswith('@'):
                if not value or time.monotonic()-self.last_action.get(index, 0) < .25:
                    continue
                self.last_action[index] = time.monotonic()
                action = target[1:]
                if action == 'release':
                    self.values.clear()
                elif action == 'record':
                    if e._state('recording', '0') == '1':
                        e.stop_recording()
                    else:
                        # Record the on-air cue, never an unrelated editor selection.
                        e._set_state('selected', t.runtime().cue_index)
                        e.start_recording()
                elif e._state('recording', '0') == '1':
                    self.error = 'Zuerst Aufnahme beenden.'
                elif action == 'loop':
                    data = e.automation_data()
                    region = data.setdefault('loop_region', dict(start=0., end=sum(c['duration'] for c in e.show()['cues']), enabled=False))
                    region['enabled'] = not region['enabled']
                    e._write_automation(automation.validate(data))
                else:
                    t.command(action)
                continue
            from .show_timeline_ui import TDHost
            host = TDHost(self.owner)
            raw = host.raw()
            if raw != self.parameter_raw:
                self.parameter_cache = host.documents()
                self.parameter_raw = raw
            show, data, parameters = self.parameter_cache
            available = parameters.get(self.cue_id, {})
            if target not in available:
                self.error = 'Parameter im laufenden Clip nicht vorhanden: '+target
                continue
            current = self.values.get(target, automation.values_at(data, self.cue_id, t.runtime().elapsed).get(target, available[target]))
            self.values[target] = mapped_value(binding, value, current)
            self.error = ''


def receive(raw):
    if _manager is not None:
        try:
            _manager.receive(raw)
        except Exception as error:
            _manager.error = str(error)


def tick():
    if _manager is not None:
        _manager.tick()


def install(owner):
    global _manager
    import td
    def create(kind, name):
        node = owner.op(name) or owner.create(kind, name)
        node.name = name
        return node
    table = create(td.tableDAT, 'timeline_midi_device')
    receiver = create(td.midiinDAT, 'timeline_midi_in')
    receiver.par.active = False
    callback = create(td.textDAT, 'timeline_midi_callbacks')
    callback.text = '''def onReceiveMIDI(dat, event):
    from pixelblaze_mapper.show_midi import receive
    receive(event.byteData)
    return
'''
    receiver.par.device = table.path
    receiver.par.id = 1
    receiver.par.callbacks = callback.path
    _manager = Manager(owner)
    _manager.configure_device()
    return _manager
