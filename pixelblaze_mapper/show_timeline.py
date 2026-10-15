"""Pure timeline editing: sequential cues, original takes and editable overlays."""
from copy import deepcopy
import hashlib
import json
import math

from . import show_automation as automation
from . import show_editor as editor


def revision(show, data):
    return hashlib.sha256(json.dumps([show, data], sort_keys=True).encode()).hexdigest()[:20]


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Wert muss endlich sein')
    return value


def layout(show):
    start = 0.0
    rows = []
    for cue in show.get('cues', []):
        rows.append(dict(id=cue['id'], start=start, end=start+cue['duration'],
                         fade_start=start+cue['duration']-cue['transition_duration']))
        start += cue['duration']
    return rows


def locate(show, seconds):
    rows = layout(show)
    if not rows:
        raise ValueError('Die Show enthält keine Clips')
    seconds = max(0., min(finite(seconds), rows[-1]['end'] - 1e-6))
    for index, row in enumerate(rows):
        if seconds < row['end']:
            return index, seconds - row['start']


def lane(data, cue_id, name):
    overlay = data.get('edits', {}).get(cue_id, {}).get(name)
    if overlay is not None:
        return deepcopy(overlay)
    points = data.get('tracks', {}).get(cue_id, {}).get(name)
    if points:
        # Historic recordings allow duplicate times; editor points are unique.
        return dict(points=[list(p) for p in sorted(dict(points).items())], mode='linear', enabled=True)
    return None


def edit(show, data, command):
    """Return validated copies, so failed changes cannot damage the live show."""
    show, data = deepcopy(show), automation.validate(data)
    if command['action'] == 'loop':
        total = sum(c['duration'] for c in show['cues'])
        start, end = finite(command['start']), finite(command['end'])
        if not 0 <= start < end <= total:
            raise ValueError('Loop muss innerhalb der Show liegen; Ende muss nach dem Start liegen.')
        data['loop_region'] = dict(start=start, end=end, enabled=command['enabled'])
        return editor._validated(show), automation.validate(data)
    cue_id = command.get('cue')
    index = next((i for i, c in enumerate(show['cues']) if c['id'] == cue_id), None)
    if index is None:
        raise ValueError('Clip nicht mehr vorhanden; Ansicht neu laden')
    cue = show['cues'][index]
    action = command['action']
    if action == 'resize':
        show = editor.update_cue(show, index, 'duration', finite(command['duration']))
    elif action == 'move':
        seconds = max(0., finite(command['time']))
        rows = layout(show)
        # Drop before the first other clip whose centre lies beyond the pointer.
        target = sum(1 for row in rows if row['id'] != cue_id and (row['start']+row['end'])/2 <= seconds)
        show['cues'].pop(index)
        show['cues'].insert(target, cue)
    elif action == 'transition':
        if 'edge' in command:
            if cue['transition'] == 'cut':
                raise ValueError('Ein harter Schnitt hat keine Überblendungsgriffe.')
            moment = finite(command['time'])
            if command['edge'] == 'start':
                start = max(0., min(moment, cue['duration'] - .1))
                cue['transition_duration'] = cue['duration'] - start
            elif command['edge'] == 'end':
                start = cue['duration'] - cue['transition_duration']
                cue['duration'] = max(start + .1, moment)
                cue['transition_duration'] = cue['duration'] - start
            else:
                raise ValueError('Unbekannter Überblendungsgriff.')
            # Move the boundary atomically; normalized curve points and original
            # parameter recordings are retained, including samples past the end.
        if 'kind' in command:
            show = editor.update_cue(show, index, 'transition', command['kind'])
        if 'duration' in command:
            show = editor.update_cue(show, index, 'transition_duration', finite(command['duration']))
        if 'curve' in command:
            data.setdefault('transitions', {})[cue_id] = command['curve']
    elif action in ('lane', 'reset_lane'):
        name = command['parameter']
        if not automation.recordable(name):
            raise ValueError('Parameter kann nicht automatisiert werden')
        layers = data.setdefault('edits', {}).setdefault(cue_id, {})
        if action == 'reset_lane':
            layers.pop(name, None)
        else:
            curve = automation._clean_curve(command['curve'])
            # Existing samples beyond a shortened clip remain recoverable.
            # The UI only adds points within the visible clip.
            layers[name] = curve
    else:
        raise ValueError('Unbekannter Timeline-Befehl')
    return editor._validated(show), automation.validate(data)


class History:
    """Bounded combined-document undo with protection against external edits."""
    def __init__(self, limit=80):
        self.undo_stack, self.redo_stack = [], []
        self.limit = limit
        self.current = None

    def observe(self, show, data):
        signature = revision(show, data)
        if self.current is not None and signature != self.current:
            self.undo_stack.clear()
            self.redo_stack.clear()
        self.current = signature

    def push(self, before, after):
        if before == after:
            return
        self.undo_stack.append(deepcopy(before))
        self.undo_stack = self.undo_stack[-self.limit:]
        self.redo_stack.clear()
        self.current = revision(*after)

    def travel(self, current, redo=False):
        self.observe(*current)
        source, destination = (self.redo_stack, self.undo_stack) if redo else (self.undo_stack, self.redo_stack)
        if not source:
            raise ValueError('Keine weitere Änderung verfügbar')
        target = source.pop()
        destination.append(deepcopy(current))
        self.current = revision(*target)
        return deepcopy(target)


SYNC_MARKER = '# SHOW_TIMELINE_CURVE_V1'


def install_sync_source(source):
    if '# SHOW_TIMELINE_LOOP_V1' not in source:
        anchor = '    sequence.advance(seconds)\n'
        if source.count(anchor) != 1:
            raise ValueError('Unbekannte Transport-Version; Loop-Hook nicht installiert')
        source = source.replace(anchor, '''    # SHOW_TIMELINE_LOOP_V1
    from pixelblaze_mapper.show_timeline import advance_with_loop
    editor = op('editor_callbacks').module
    data = editor._cached_automation() if editor._state('recording', '0') != '1' else {}
    advance_with_loop(sequence, seconds, data)
''')
    if '# SHOW_TIMELINE_MIDI_V1' not in source:
        anchor = '    plan = sequence.plan()\n'
        source = source.replace(anchor, anchor + '''    # SHOW_TIMELINE_MIDI_V1
    from pixelblaze_mapper.show_midi import apply_plan
''', 1)
        # Brightness override must be applied after recorded automation.
        anchor = '        plan = playback_plan(plan, editor_node.module._cached_automation(), sequence.cue.id, sequence.elapsed)\n'
        if anchor in source:
            source = source.replace(anchor, anchor + '    plan = apply_plan(plan, sequence.cue.id)\n', 1)
    if SYNC_MARKER in source:
        compile(source, '<timeline transport>', 'exec')
        return source
    anchor = '    plan = sequence.plan()\n'
    if source.count(anchor) != 1:
        raise ValueError('Unbekannte Transport-Version; Timeline-Hook nicht installiert')
    replacement = anchor + '''    # SHOW_TIMELINE_CURVE_V1
    from pixelblaze_mapper.show_automation import playback_plan
    editor_node = op('editor_callbacks')
    if editor_node is not None:
        plan = playback_plan(plan, editor_node.module._cached_automation(), sequence.cue.id, sequence.elapsed)
'''
    patched = source.replace(anchor, replacement + '    plan = apply_plan(plan, sequence.cue.id)\n', 1)
    compile(patched, '<timeline transport>', 'exec')
    return patched


def install_editor_source(source):
    """Small idempotent patches also used when upgrading the live editor DAT."""
    replacements = (
        ("if cue_id not in (data.get('tracks') or {}):", "if cue_id not in (data.get('tracks') or {}) and cue_id not in (data.get('edits') or {}):"),
        ("        if source_id in data.get('tracks', {}):\n            _write_automation(automation.merge(data, copy_id, data['tracks'][source_id]))",
         "        _write_automation(automation.copy_cue(data, source_id, copy_id))"),
        ("    return {name: value for name, value in recorded.items()\n            if name.startswith(automation.IMPORT_PARAMETER_PREFIX)}",
         "    values = {automation.imported_track_name(name): value for name, value in imported_data().get(cue_id, {}).get('values', {}).items()\n              if isinstance(value, (int, float)) and not isinstance(value, bool)}\n    values.update({name: value for name, value in recorded.items()\n                   if name.startswith(automation.IMPORT_PARAMETER_PREFIX)})\n    return values"),
        ("        name = str(item.get('name', ''))\n        if not automation.recordable(name):",
         "        name = automation.imported_track_name(str(item.get('name', '')))\n        if not automation.recordable(name):"),
        ("        if parameter.name not in values or parameter.compile_time:",
         "        key = automation.imported_track_name(parameter.name)\n        if key not in values or parameter.compile_time:"),
        ("            vector = uniform_vector(parameter, values[parameter.name])",
         "            vector = uniform_vector(parameter, values[key])"),
        ("    if command == 'new_show':\n        _set_state('selected', 0)",
         "    if command == 'new_show':\n        _write_automation(automation.empty())\n        _write_imported({})\n        _set_state('selected', 0)"),
        ("                _write_automation(automation.validate(json.load(stream)))\n        except OSError:\n            pass",
         "                _write_automation(automation.validate(json.load(stream)))\n        except OSError:\n            _write_automation(automation.empty())"),
        ("                _write_imported(json.load(stream))\n        except OSError:\n            pass",
         "                _write_imported(json.load(stream))\n        except OSError:\n            _write_imported({})"),
    )
    for old, new in replacements:
        if new in source:
            continue
        if source.count(old) != 1:
            raise ValueError('Unbekannte Editor-Version; Timeline-Hook nicht installiert')
        source = source.replace(old, new, 1)
    if '# SHOW_MIDI_OVERLAY_V1' not in source:
        source = source.replace('        if sample:\n            recorder.sample(moment, sample)',
                                '        from pixelblaze_mapper.show_midi import live_values\n        sample.update(live_values(cue_id))\n        if sample:\n            recorder.sample(moment, sample)')
        source += '''
# SHOW_MIDI_OVERLAY_V1
_midi_base_effective = _effective_parameters
def _effective_parameters(cue, on_air):
    from pixelblaze_mapper.show_midi import live_values
    result = dict(_midi_base_effective(cue, on_air))
    if on_air:
        result.update({k:v for k,v in live_values(cue['id']).items() if k in result})
    return result

_midi_base_imported = _imported_overrides
def _imported_overrides(slot, cue_id):
    from pixelblaze_mapper.show_midi import live_values
    result = dict(_midi_base_imported(slot, cue_id))
    transport = OWNER.op('callbacks').module
    if str(transport._get('outgoing_slot', 'A')).strip().lower() == slot:
        result.update({k:v for k,v in live_values(cue_id).items() if k.startswith('mat_')})
    return result
'''
    from .mk2_hooks import install_editor_source as install_mk2
    source = install_mk2(source)
    compile(source, '<timeline editor>', 'exec')
    return source


def advance_with_loop(sequence, seconds, data):
    """Use the existing clock, including large deltas and multi-cue ranges."""
    from .show_sequencer import TransportState
    delta = finite(seconds)
    if delta < 0:
        raise ValueError('advance seconds must be positive')
    region = data.get('loop_region', {})
    if not region.get('enabled') or sequence.state is not TransportState.PLAYING or delta == 0:
        return sequence.advance(delta)
    durations = [c.duration for c in sequence.show.cues]
    end = min(region['end'], sum(durations))
    start = min(region['start'], end)
    if end <= start:
        return sequence.advance(delta)
    position = sum(durations[:sequence.cue_index]) + sequence.elapsed
    if start <= position and position + delta < end:
        return sequence.advance(delta)
    if not start <= position < end:
        position = start
    target = start + (position - start + delta) % (end - start)
    for index, duration in enumerate(durations):
        if target < duration:
            sequence.seek(index, target)
            return
        target -= duration
