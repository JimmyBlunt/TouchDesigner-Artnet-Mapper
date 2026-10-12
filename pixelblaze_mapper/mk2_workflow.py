"""Deterministic MK2 workflows; no USB, TouchDesigner, filesystem or thread access.

Host state is authoritative. Runtime commands never pretend to have succeeded;
configuration writes are committed only after a successful ``command_result``.
See docs/MK2_WORKFLOW_API.md for the adapter contract.
"""
from copy import deepcopy
import math
from time import monotonic

VERSION = '0.2.2'
SCHEMA_VERSION = 2
EDIT_IDLE_SECONDS = 20.0
SHOW_FIELDS = ('duration', 'transition', 'transition_duration')
EDITABLE_TYPES = ('float', 'number', 'int', 'integer', 'bool', 'boolean', 'enum')


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def _empty_pad():
    return dict(kind='material', target='', values={})


def validate_config(config=None):
    """Return independent canonical v2 banks, preserving legacy cue assignments."""
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise ValueError('MK2-Konfiguration muss ein Objekt sein.')
    schema = config.get('schema_version', 1)
    if schema not in (1, SCHEMA_VERSION):
        raise ValueError('Unbekannte MK2-Konfigurationsversion.')
    groups = config.get('groups')
    if groups is None:
        old = config.get('pads', [_empty_pad() for _ in range(16)])
        groups = [dict(pads=old)] + [dict(pads=[_empty_pad() for _ in range(16)]) for _ in range(7)]
    if not isinstance(groups, list) or len(groups) != 8:
        raise ValueError('MK2 braucht genau acht Pad-Gruppen.')
    clean = []
    for i, group in enumerate(groups):
        pads = group.get('pads') if isinstance(group, dict) else None
        if not isinstance(pads, list) or len(pads) != 16:
            raise ValueError('Jede Gruppe braucht genau 16 Pads.')
        bank = []
        for pad in pads:
            if not isinstance(pad, dict):
                raise ValueError('Ungültige Pad-Zuweisung.')
            kind, target, values = pad.get('kind', 'material'), pad.get('target', ''), pad.get('values', {})
            if kind not in ('material', 'cue') or not isinstance(target, str) or len(target) > 200:
                raise ValueError('Ungültiges Pad-Ziel.')
            if not isinstance(values, dict) or len(values) > 256:
                raise ValueError('Ungültige Pad-Parameter.')
            if any(not isinstance(k, str) or not k or len(k) > 200 or not _finite(v) for k, v in values.items()):
                raise ValueError('Pad-Parameter müssen endliche Zahlen oder Wahrheitswerte sein.')
            bank.append(dict(kind=kind, target=target, values=deepcopy(values)))
        clean.append(dict(name=chr(65+i), pads=bank))
    return dict(schema_version=SCHEMA_VERSION, hardware=bool(config.get('hardware', False)), groups=clean)


def _parameter(source, i):
    p = deepcopy(source)
    key = str(p.get('id', p.get('target', 'parameter_%d' % i)))
    label = str(p.get('label', p.get('name', key)))
    kind = p.get('type', 'float')
    minimum = p.get('min', p.get('minimum', 0))
    maximum = p.get('max', p.get('maximum', 1))
    value = p.get('value', 0)
    numeric = _finite(minimum) and _finite(maximum) and _finite(value) and minimum <= maximum
    options = p.get('options', [])
    if kind == 'enum' and isinstance(options, list) and options:
        minimum, maximum = 0, len(options)-1
        numeric = _finite(value)
    step = p.get('step', 1 if kind in ('int', 'integer', 'enum', 'bool', 'boolean') else (maximum-minimum)/100 if numeric else 0)
    if not _finite(step) or step <= 0:
        step = .01
    short = {'global_master_speed': 'Speed', 'focus_x': 'Focus X', 'focus_y': 'Focus Y',
             'zoom': 'Zoom', 'intensity': 'Intens', 'contrast': 'Contr'}.get(key, label[:7])
    p.update(id=key, label=label, name=label, abbreviation=str(p.get('abbreviation', short)),
             type=kind, min=minimum if numeric else 0, max=maximum if numeric else 1,
             value=value if numeric else 0, step=step,
             editable=bool(p.get('editable', True)) and numeric and kind in EDITABLE_TYPES,
             section=p.get('section', 'td' if i < 8 else 'native'))
    return p


class Controller:
    def __init__(self, config=None, clock=monotonic):
        self.config = validate_config(config)
        self.clock = clock
        self.context = dict(mode='material', active_material={}, catalog=[], show={}, recording=False)
        self.mode = 'material'
        self.screen = 'home'
        self.bank = self.pad_index = self.page = self.browse_index = self.choice = 0
        self.parameter_group = self.parameter_index = 0
        self.parameter_focused = False
        self.show_focus = 0
        self.show_editing = False
        self.browse_purpose = 'load'
        self.assign_target = None
        self.edit_original = self.edit_values = None
        self.edit_material = None
        self._draft_base = None
        self.last_activity = self.clock()
        self.held = set()
        self.rec_pending = False
        self.rec_chord = False
        self.flash_until = {}
        self.error = ''
        self._request_id = 0
        self._pending_config = None

    def set_context(self, context):
        """Merge an authoritative host update. Unmentioned fields stay unchanged."""
        if not isinstance(context, dict):
            raise ValueError('Controller-Kontext muss ein Objekt sein.')
        incoming = deepcopy(context)
        if 'config' in incoming:
            self.config = validate_config(incoming.pop('config'))
            self._pending_config = None
        self.context.update(incoming)
        mode = self.context.get('mode', 'material')
        if mode not in ('material', 'show'):
            mode = 'material'
        if mode != self.mode:
            dirty = self._dirty()
            self.mode = mode
            self.screen = 'confirm_edit' if dirty else 'home'
            self.choice = 0
            self.page = self.parameter_group = self.parameter_index = 0
            self.parameter_focused = False
            self.show_editing = False
            if dirty:
                self.error = 'Modus extern geändert. Pad-Entwurf zuerst speichern oder verwerfen.'
            else:
                self._discard_edit()
        pages = self._pages()
        self.page = min(self.page, max(0, len(pages)-1))
        parameters = self._parameters()
        self.parameter_group = min(self.parameter_group, max(0, (len(parameters)-1)//8), 7)
        self.parameter_index = min(self.parameter_index, max(0, len(parameters)-1))
        self.browse_index = min(self.browse_index, max(0, len(self._catalog())-1))

    def export_config(self):
        return deepcopy(self.config)

    def _catalog(self):
        return [item for item in self.context.get('catalog', []) if isinstance(item, dict)]

    def _lookup(self, target):
        item = next((item for item in self._catalog() if item.get('id') == target), None)
        if item is None:
            return None
        result = deepcopy(item)
        result.update(deepcopy(self.context.get('materials', {}).get(target, {})))
        return result

    def _pad(self):
        return self.config['groups'][self.bank]['pads'][self.pad_index]

    def _material(self):
        if self.edit_material is not None and self.screen in ('pad_edit', 'confirm_edit'):
            if not self.edit_material.get('parameters'):
                detailed = self._lookup(self.edit_material.get('id'))
                if detailed:
                    self.edit_material.update(detailed)
            return self.edit_material
        if self.mode == 'show':
            return self.context.get('show', {}).get('material', self.context.get('active_material', {}))
        return self.context.get('active_material', {})

    def _parameters(self):
        material = self._material()
        source = material.get('parameters', [])
        if self.mode == 'show' and self.screen not in ('pad_edit', 'confirm_edit'):
            source = self.context.get('show', {}).get('parameters', source)
        result = [_parameter(p, i) for i, p in enumerate(source) if isinstance(p, dict)]
        if self.edit_values is not None and self.screen in ('pad_edit', 'confirm_edit'):
            for p in result:
                if p['id'] in self.edit_values:
                    p['value'] = self.edit_values[p['id']]
        show = self.context.get('show', {})
        automated, modified = show.get('automated_ids', []), show.get('modified_ids', [])
        for p in result:
            p.update(automated=p['id'] in automated, modified=p['id'] in modified)
        return result

    def _pages(self):
        parameters = self._parameters()
        td = [p for p in parameters if p['section'] == 'td']
        native = [p for p in parameters if p['section'] != 'td']
        # The adapter provides exactly the eight common TD controls first.
        # Retain extra TD parameters rather than silently dropping their values.
        pages = []
        for start in range(0, len(td), 8):
            pages.append(dict(label='TD' if start == 0 else 'TD %d' % (start//8+1), parameters=td[start:start+8]))
        for start in range(0, len(native), 8):
            pages.append(dict(label='MM %d' % (start//8+1), parameters=native[start:start+8]))
        return pages[:8]

    def _recording(self):
        return self.context.get('recording', False)

    def _blocked_recording(self):
        if self._recording():
            self.error = 'Zuerst Aufnahme beenden.'
            return True
        return False

    def _discard_edit(self):
        self.edit_material = self.edit_original = self.edit_values = None

    def _dirty(self):
        if self.edit_values is None:
            return False
        defaults = {p['id']: p['value'] for i, raw in enumerate(self._material().get('parameters', []))
                    for p in [_parameter(raw, i)]}
        return dict(defaults, **self.edit_values) != dict(defaults, **self.edit_original)

    def _guard_edit(self):
        if self.screen == 'pad_edit' and self._dirty():
            self.screen, self.choice = 'confirm_edit', 0
            return True
        return self.screen.startswith('confirm_') or self._pending_config is not None

    def _persist(self, candidate):
        if self._pending_config is not None:
            self.error = 'Speicherung läuft bereits.'
            return []
        self._request_id += 1
        command = dict(action='persist_config', request_id=self._request_id, config=validate_config(candidate))
        self._pending_config = deepcopy(command)
        return [command]

    def _result(self, event):
        pending = self._pending_config
        if pending is not None and event.get('request_id') == pending['request_id']:
            if event.get('success') is True:
                self.config = pending['config']
                self.error = ''
                self.screen = 'home' if self.mode == 'show' else 'pad_grid'
                self._discard_edit()
            else:
                self.error = str(event.get('error') or 'Zuweisung konnte nicht gespeichert werden.')
            self._pending_config = None
        elif event.get('success') is False:
            self.error = str(event.get('error') or 'Aktion konnte nicht ausgeführt werden.')
        return []

    def dispatch(self, event):
        """Consume one normalized physical/UI event and return host intentions."""
        if not isinstance(event, dict):
            return []
        kind = event.get('type')
        if kind == 'command_result':
            return self._result(event)
        self.last_activity = self.clock()
        if kind == 'button':
            name = event.get('name')
            index = event.get('index', 0)
            key = (name, index)
            if not event.get('down', True):
                was_held = key in self.held
                self.held.discard(key)
                if name == 'rec' and was_held:
                    return self._rec_release()
                return []
            if key in self.held:
                return []
            self.held.add(key)
            if name in ('wheel', 'wheel_press'):
                return self._wheel_press()
            return self._button(name, index)
        if kind == 'wheel_press':
            return self._wheel_press()
        if kind in ('encoder', 'wheel'):
            delta = event.get('delta', 0)
            if not _finite(delta) or not delta:
                return []
            delta = max(-127, min(127, delta))
            if kind == 'encoder':
                return self._encoder(event.get('index'), delta)
            return self._wheel(delta)
        return []

    def _button(self, name, index):
        if name == 'rec':
            return self._rec_down()
        if name == 'erase':
            if self.rec_pending and not self.rec_chord:
                self.rec_chord = True
                return self._record_start('automation')
            return []
        if name in ('play', 'previous', 'next', 'restart'):
            if self._blocked_recording():
                return []
            return [dict(action='transport', command=name)]
        if name == 'step':
            if self._blocked_recording() or self._guard_edit():
                return []
            return [dict(action='set_mode', mode='show' if self.mode == 'material' else 'material')]
        if name in ('browse', 'scene'):
            if self._blocked_recording() or self._guard_edit():
                return []
            self._discard_edit()
            if self.mode != 'material':
                self.error = 'Material-Browser und Pad-Zuweisung sind im Material Mode verfügbar.'
                return []
            if name == 'scene':
                self.screen = 'home' if self.screen == 'pad_grid' else 'pad_grid'
            else:
                self.screen = 'home' if self.screen == 'browse' else 'browse'
                self.browse_purpose = 'load'
                self._select_active_browse()
            return []
        if name in ('top', 'group', 'pad'):
            limit = 16 if name == 'pad' else 8
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < limit:
                return []
            if name == 'top':
                if self.screen in ('home', 'pad_edit') and index < len(self._pages()):
                    self.page = index
                    self.parameter_focused = False
                return []
            if name == 'group':
                if self._guard_edit():
                    return []
                if self.mode == 'material':
                    self.bank = index
                    self._discard_edit()
                    if self.screen not in ('home', 'pad_grid'):
                        self.screen = 'pad_grid'
                else:
                    self.parameter_group = index
                    self.parameter_index = index*8
                return []
            if self.mode == 'show':
                if index < 8 and self.parameter_group*8+index < len(self._parameters()):
                    self.parameter_index = self.parameter_group*8+index
                    self.parameter_focused = True
                return []
            if self._blocked_recording() or self._guard_edit():
                return []
            self.pad_index = index
            self.flash_until[(self.bank, index)] = self.clock()+.25
            commands = [dict(action='flash_pad', group=self.bank, index=index, color='red')]
            return commands+self._load_pad()
        return []

    def _select_active_browse(self):
        target = self._material().get('id')
        self.browse_index = next((i for i, item in enumerate(self._catalog()) if item.get('id') == target), 0)

    def _load_pad(self):
        pad = self._pad()
        if not pad['target']:
            self.error = 'Dieses Pad ist leer.'
            return []
        if pad['kind'] == 'cue':
            return [dict(action='load_cue', cue_id=pad['target'])]
        item = self._lookup(pad['target'])
        if not item or item.get('available', True) is False or item.get('compatibility') == 'unsupported':
            self.error = 'Dieses Material ist nicht verfügbar.'
            return []
        return [dict(action='load_material', material_id=pad['target'], values=deepcopy(pad['values']))]

    def _wheel(self, delta):
        direction = 1 if delta > 0 else -1
        steps = int(delta) or direction
        if self.screen == 'browse':
            self.browse_index = max(0, min(len(self._catalog())-1, self.browse_index+steps))
        elif self.screen == 'pad_grid':
            self.pad_index = max(0, min(15, self.pad_index+steps))
        elif self.screen == 'pad_menu':
            self.choice = max(0, min(len(self._menu())-1, self.choice+steps))
        elif self.screen.startswith('confirm_'):
            if self._pending_config is None:
                self.choice = max(0, min(1, self.choice+steps))
        elif self.mode == 'show' and self.screen == 'home':
            if not self.show_editing:
                self.show_focus = (self.show_focus+steps) % len(SHOW_FIELDS)
            elif not self._blocked_recording():
                show = self.context.get('show', {})
                field = SHOW_FIELDS[self.show_focus]
                if field == 'transition':
                    options = self.context.get('transitions', ['cut', 'crossfade'])
                    if not options:
                        return []
                    current = options.index(show.get(field)) if show.get(field) in options else 0
                    value = options[(current+steps) % len(options)]
                else:
                    current = show.get(field, 0)
                    if not _finite(current):
                        return []
                    minimum = .1 if field == 'duration' else 0
                    maximum = 86400 if field == 'duration' else max(0, show.get('duration', 86400))
                    value = round(max(minimum, min(maximum, current+delta*.1)), 6)
                return [dict(action='set_show_field', cue_id=show.get('id'), field=field, value=value)]
        return []

    def _menu(self):
        pad = self._pad()
        if not pad['target']:
            return ['browse']
        return ['select', 'edit', 'browse', 'delete'] if pad['kind'] == 'material' else ['select', 'browse', 'delete']

    def _wheel_press(self):
        if self._pending_config is not None:
            return []
        if self.screen == 'browse':
            items = self._catalog()
            if not items:
                self.error = 'Keine Materialien verfügbar.'
                return []
            item = items[self.browse_index]
            if item.get('available', True) is False or item.get('compatibility') == 'unsupported':
                self.error = 'Dieses Material ist nicht verfügbar.'
                return []
            if self.browse_purpose == 'assign':
                self.assign_target = item['id']
                self.screen, self.choice = 'confirm_assign', 0
                return []
            if self._blocked_recording():
                return []
            return [dict(action='load_material', material_id=item['id'], values={})]
        if self.screen == 'pad_grid':
            self._draft_base = deepcopy(self._pad())
            self.screen, self.choice = 'pad_menu', 0
        elif self.screen == 'pad_menu':
            option = self._menu()[self.choice]
            if option == 'select':
                if self._blocked_recording():
                    return []
                return self._load_pad()
            if option == 'edit':
                item = self._lookup(self._pad()['target'])
                if not item:
                    self.error = 'Dieses Material ist nicht verfügbar.'
                    return []
                self.edit_material = deepcopy(item)
                self.edit_original = deepcopy(self._pad()['values'])
                self.edit_values = deepcopy(self.edit_original)
                self.screen, self.page = 'pad_edit', 0
            elif option == 'browse':
                self.screen, self.browse_purpose = 'browse', 'assign'
                self.browse_index = 0
            elif option == 'delete':
                self.screen, self.choice = 'confirm_delete', 0
        elif self.screen.startswith('confirm_'):
            if self.choice == 1:
                self.screen = 'home' if self.mode == 'show' else 'pad_grid'
                self._discard_edit()
                self.assign_target = None
                return []
            if self._draft_base is not None and self._pad() != self._draft_base:
                self.error = 'Pad-Zuweisung wurde inzwischen geändert. Entwurf abbrechen und erneut öffnen.'
                return []
            candidate = self.export_config()
            bank = candidate['groups'][self.bank]['pads']
            if self.screen == 'confirm_assign':
                # Recheck availability after a catalog refresh while confirming.
                item = self._lookup(self.assign_target)
                if not item or item.get('available', True) is False or item.get('compatibility') == 'unsupported':
                    self.error = 'Dieses Material ist nicht mehr verfügbar.'
                    return []
                bank[self.pad_index] = dict(kind='material', target=self.assign_target, values={})
            elif self.screen == 'confirm_delete':
                bank[self.pad_index] = _empty_pad()
            elif self.screen == 'confirm_edit':
                bank[self.pad_index]['values'] = deepcopy(self.edit_values)
            return self._persist(candidate)
        elif self.screen == 'pad_edit':
            if self._dirty():
                self.screen, self.choice = 'confirm_edit', 0
            else:
                self.screen = 'pad_grid'
                self._discard_edit()
        elif self.mode == 'show' and self.screen == 'home':
            if not self._blocked_recording():
                self.show_editing = not self.show_editing
        return []

    def _encoder(self, index, delta):
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < 8:
            return []
        if self.screen not in ('home', 'pad_edit'):
            return []
        if self.mode == 'show' and not self._recording():
            return []
        pages = self._pages()
        if self.page >= len(pages) or index >= len(pages[self.page]['parameters']):
            return []
        p = pages[self.page]['parameters'][index]
        if not p['editable']:
            self.error = 'Dieser Parametertyp ist am Controller nicht editierbar.'
            return []
        value = max(p['min'], min(p['max'], p['value']+delta*p['step']))
        if p['type'] in ('bool', 'boolean'):
            value = delta > 0
        elif p['type'] in ('int', 'integer', 'enum'):
            value = int(round(value))
        else:
            value = round(value, 8)
        if self.screen == 'pad_edit':
            self.edit_values[p['id']] = value
            return []
        return [dict(action='set_parameter', parameter_id=p['id'], value=value,
                     material_id=self._material().get('id'))]

    def _record_start(self, kind):
        if self._guard_edit():
            self.error = 'Speicherung abwarten.' if self._pending_config is not None else 'Zuerst den Pad-Entwurf speichern oder verwerfen.'
            return []
        if self.mode != 'show':
            self.error = 'Aufnahme ist im Show Mode verfügbar.'
            return []
        if kind == 'automation' and not self.context.get('allow_automation_recording', True):
            self.error = 'REC + ERASE: Aufnahmeverhalten noch nicht bestätigt.'
            return []
        self.show_editing = False
        return [dict(action='record_start', kind=kind)]

    def _rec_down(self):
        if self._recording():
            self.rec_pending = False
            self.rec_chord = True
            return [dict(action='record_stop')]
        self.rec_pending = True
        self.rec_chord = ('erase', 0) in self.held
        return self._record_start('automation') if self.rec_chord else []

    def _rec_release(self):
        pending, chord = self.rec_pending, self.rec_chord
        self.rec_pending = self.rec_chord = False
        return self._record_start('new_cue') if pending and not chord else []

    def tick(self):
        if self.screen == 'pad_edit' and self.clock()-self.last_activity >= EDIT_IDLE_SECONDS:
            if self._dirty():
                self.screen, self.choice = 'confirm_edit', 0
            else:
                self.screen = 'pad_grid'
                self._discard_edit()
        return []

    def snapshot(self):
        catalog = self._catalog()
        cards = []
        assignments = {}
        for group_index, group in enumerate(self.config['groups']):
            for index, pad in enumerate(group['pads']):
                if pad['target'] and pad['kind'] == 'material':
                    assignments.setdefault(pad['target'], []).append(dict(group=group_index, pad=index))
        for i, pad in enumerate(self.config['groups'][self.bank]['pads']):
            item = self._lookup(pad['target']) if pad['kind'] == 'material' else None
            available = bool(item) and item.get('available', True) is not False and item.get('compatibility') != 'unsupported'
            cards.append(dict(number=i+1, label=item.get('label', item.get('name', pad['target'])) if item else 'Nicht verfügbar' if pad['target'] else 'Leer',
                              image=item.get('image') if item else None, available=available, **deepcopy(pad)))
        browse = []
        for i, item in enumerate(catalog):
            entry = deepcopy(item)
            entry.update(number=i+1, assignments=assignments.get(item.get('id'), []))
            browse.append(entry)
        parameters = self._parameters()
        focused = parameters[self.parameter_index] if self.parameter_focused and self.parameter_index < len(parameters) else None
        show = deepcopy(self.context.get('show', {}))
        duration, elapsed = show.get('duration', 0), show.get('elapsed', 0)
        duration = duration if _finite(duration) and duration > 0 else 0
        elapsed = elapsed if _finite(elapsed) else 0
        show.update(progress=max(0, min(1, elapsed/duration)) if duration else 0,
                    remaining=max(0, duration-elapsed), focus=SHOW_FIELDS[self.show_focus], editing=self.show_editing)
        confirm = None
        if self.screen.startswith('confirm_'):
            item = self._lookup(self.assign_target) if self.screen == 'confirm_assign' else self._lookup(self._pad()['target'])
            confirm = dict(kind=self.screen[8:], label=item.get('label', item.get('name', '')) if item else '',
                           group=self.bank, pad=self.pad_index,
                           options=['Save', 'Cancel'] if self.screen == 'confirm_edit' else ['Confirm', 'Cancel'], choice=self.choice)
        group_activity = []
        for i in range(8):
            group_activity.append(any(p['automated'] or p['modified'] for p in parameters[i*8:i*8+8]))
        result = dict(version=VERSION, mode=self.mode, screen=self.screen, material=deepcopy(self._material()),
                      parameter_pages=self._pages(), page=self.page, bank=self.bank, pad_index=self.pad_index,
                      cards=cards, browse_items=browse, browse_index=self.browse_index, browse_purpose=self.browse_purpose,
                      menu=self._menu(), options=self._menu(), choice=self.choice, confirm=confirm,
                      show=show, recording=self._recording(), rec_pending=self.rec_pending,
                      parameter_group=self.parameter_group, parameter_index=self.parameter_index,
                      focused_parameter=focused, parameter_focused=self.parameter_focused, group_activity=group_activity,
                      parameter_overflow=max(0, len(parameters)-sum(len(page['parameters']) for page in self._pages())),
                      group_has_content=[any(p['target'] for p in group['pads']) for group in self.config['groups']],
                      pad_flash=[self.flash_until.get((self.bank, i), 0) > self.clock() for i in range(16)],
                      dirty=self._dirty(), saving=self._pending_config is not None, error=self.error)
        return deepcopy(result)
