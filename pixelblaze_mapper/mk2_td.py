"""MK2 0.2.0 adapter. TouchDesigner access is confined to the main thread.

Pad drafts belong to the workflow; only explicit load/set commands reach here.
The HID worker must never call this module.
"""
from copy import deepcopy
import math
import time

from . import show_automation as automation, show_editor, show_timeline

from .mk2_workflow import VERSION
TAKE_STORAGE_KEY = 'mk2_recording_context_v1'
_host = None
CORE = (
    ('global_master_speed', 'Globalmasterspeed', 'Master speed', 0., 4.),
    ('scale', 'Scale', 'Scale', .01, 128.),
    ('width', 'Width', 'Width', 0., 1.),
    ('focus_x', 'Focusx', 'Focus X', 0., 1.),
    ('focus_y', 'Focusy', 'Focus Y', 0., 1.),
    ('zoom', 'Framezoom', 'Frame zoom', .25, 8.),
    ('intensity', 'Intensity', 'Intensity', 0., 2.),
    ('contrast', 'Contrast', 'Contrast', .1, 4.),
)


def component_id(name, component=None):
    key = automation.imported_track_name(name)
    return key if component is None else key + '__component_%d' % component


def native_parameters(schema, values):
    """Scalar encoder descriptors, preserving declaration/component order."""
    result = []
    for p in schema:
        raw = values.get(p.name, p.default)
        for i in range(p.components):
            vector = p.components > 1
            value = raw[i] if vector and isinstance(raw, (tuple, list)) and i < len(raw) else (0 if vector else raw)
            def bound(raw_bound, fallback):
                if isinstance(raw_bound, (tuple, list)):
                    raw_bound = raw_bound[i] if i < len(raw_bound) else None
                return float(fallback if raw_bound is None else raw_bound)
            lo, hi = bound(p.minimum, 0), bound(p.maximum, 1)
            if p.kind in ('bool', 'event', 'color'):
                lo, hi = 0., 1.
            elif p.kind == 'long' and p.values:
                lo, hi = 0., float(len(p.values)-1)
            elif p.maximum is None:
                hi = max(1., abs(float(value or 0))*2)
            discrete = p.kind in ('int', 'long', 'bool', 'event')
            result.append(dict(id=component_id(p.name, i if vector else None),
                label=p.display_label + ((' ' + ('RGBA'[i] if p.kind == 'color' else 'XY'[i])) if vector else ''),
                value=float(value or 0), min=lo, max=hi, step=1. if discrete else max((hi-lo)/100., .0001),
                type='bool' if p.kind == 'bool' else ('int' if discrete else 'float'), section='native',
                editable=p.kind != 'event', recordable=not p.compile_time and p.kind != 'event',
                native_name=p.name, component=i if vector else None, compile_time=p.compile_time,
                choices=list(p.values)))
    return result


def expand_native(schema, values, defaults=None):
    """Reassemble flattened recorded components for the existing uniform writer."""
    result = dict(values)
    for p in schema:
        key = component_id(p.name)
        if p.components > 1:
            baseline = (defaults or {}).get(p.name, p.default)
            vector = list(baseline) if isinstance(baseline, (tuple, list)) else [0.] * p.components
            vector += [0.] * (p.components-len(vector))
            changed = False
            for i in range(p.components):
                if component_id(p.name, i) in values:
                    vector[i] = values[component_id(p.name, i)]
                    changed = True
            if changed:
                result[key] = vector
        elif p.kind == 'bool' and key in result:
            result[key] = float(result[key]) >= .5
    return result


def checked_value(descriptor, value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Parameterwert muss endlich sein')
    number = max(descriptor['min'], min(descriptor['max'], number))
    if descriptor['type'] in ('int', 'bool'):
        number = int(round(number))
    return number


def live_values(cue_id):
    if _host is None or not _host.take or _host.take['cue_id'] != cue_id or not _host.recording:
        return {}
    return dict(_host.values)


class Host:
    def __init__(self, owner, *, resolve=None, timeline_host=None):
        global _host
        self.owner = owner
        self.resolve = resolve or __import__('td').op
        if timeline_host is None:
            from .show_timeline_ui import TDHost
            timeline_host = TDHost(owner)
        self.timeline = timeline_host
        self.values = {}
        self.take = None
        self._catalog_source = None
        self._catalog = []
        self._phase = None
        self._last_material_id = ''
        self._restore_take()
        _host = self

    @property
    def editor(self):
        return self.owner.op('editor_callbacks').module

    @property
    def transport(self):
        return self.owner.op('callbacks').module

    @property
    def controls(self):
        return self.resolve('/project1/madmapper_player_controls')

    @property
    def recording(self):
        return self.editor._state('recording', '0') == '1'

    def _save_take(self):
        """Persist primitives alongside the editor's COMP-backed Recorder."""
        store = getattr(self.owner,'store',None)
        if self.take is not None and callable(store):
            document = dict(self.take)
            document['touched'] = sorted(self.take['touched'])
            store(TAKE_STORAGE_KEY,dict(version=1,take=document,values=dict(self.values),
                                       material_id=self._last_material_id))

    def _restore_take(self):
        fetch = getattr(self.owner,'fetch',None)
        if not callable(fetch):
            return
        saved = fetch(TAKE_STORAGE_KEY,None)
        if not isinstance(saved,dict) or saved.get('version') != 1:
            return
        take = saved.get('take',{})
        if not self.recording or take.get('cue_id') != self.editor._state('record_cue',''):
            unstore = getattr(self.owner,'unstore',None)
            if callable(unstore):
                unstore(TAKE_STORAGE_KEY)
            return
        if take.get('kind') not in ('new_cue','automation'):
            raise ValueError('Gespeicherter MK2-Aufnahmekontext ist ungültig')
        restored = deepcopy(take)
        restored['before'] = automation.validate(restored['before'])
        restored['touched'] = set(restored['touched'])
        for mapping in (restored['baseline'],saved.get('values',{})):
            if any(not automation.recordable(key) or not math.isfinite(float(value)) for key,value in mapping.items()):
                raise ValueError('Gespeicherte MK2-Aufnahmewerte sind ungültig')
        self.take = restored
        self.values = dict(saved.get('values',{}))
        self._last_material_id = str(saved.get('material_id',''))

    def _catalog_items(self):
        items = self.editor._library()._items
        if items is not self._catalog_source:
            self._catalog_source = items
            self._catalog = [dict(id=p['id'], label=p['label'], image=p['id'],
                category=' / '.join(p.get('groups') or p.get('categories') or []))
                for p in items if p.get('compatibility') != 'unsupported']
            self._catalog.sort(key=lambda p: p['label'].casefold())
        return self._catalog

    def material_identity(self, kind, identifier):
        """Separate the browser's loaded material from the Source selector.

        The legacy material-state runtime returns ``show:default`` while Show
        is selected. It is a source sentinel, never a material catalog ID.
        """
        if kind in ('core','madmapper') and identifier and identifier != 'default':
            self._last_material_id = 'core:'+identifier if kind=='core' else identifier
            return kind,identifier
        previous = self._last_material_id
        if previous:
            return ('core',previous[5:]) if previous.startswith('core:') else ('madmapper',previous)
        library = self.editor._library()
        loaded = library._state('active_id','') or library._state('live_preview_id','')
        if loaded and any(p['id']==loaded for p in library._items):
            return 'madmapper',loaded
        par = getattr(self.controls.par,'Material',None)
        core = str(par.eval()) if par is not None else ''
        if core and core in getattr(self.editor,'_catalog',lambda:{})():
            return 'core',core
        return '', ''

    def material(self, identifier):
        base = next((dict(p) for p in self._catalog_items() if p['id'] == identifier), None)
        if base is None:
            if identifier.startswith('core:'):
                base = dict(id=identifier, label=self.editor._effect_label(identifier[5:]), image=None, category='TouchDesigner')
            else:
                raise ValueError('Material nicht verfügbar: ' + str(identifier))
        player = self.editor.player_values()
        kind, active = self.material_identity(*self.editor.current_material())
        active = 'core:'+active if kind == 'core' else active
        stored = {}
        if identifier != active:
            runtime = self.resolve('/project1/material_state_runtime')
            if runtime is not None:
                try:
                    key = identifier if identifier.startswith('core:') else 'madmapper:'+identifier
                    stored = runtime.module.STORE.state(key).settings.to_dict()
                except (KeyError, AttributeError):
                    from .material_state import MaterialSettings
                    stored = MaterialSettings().to_dict()
        descriptors = []
        for key, par_name, label, lo, hi in CORE:
            par = getattr(self.controls.par, par_name, None)
            if par is not None:
                # Several shipped TD parameters retain the factory 0..1
                # norm range although Scale=4 is valid. Only actual clamps
                # constrain the semantic MaterialSettings range.
                if getattr(par,'clampMin',False):
                    lo = max(lo,float(getattr(par,'min',lo)))
                if getattr(par,'clampMax',False):
                    hi = min(hi,float(getattr(par,'max',hi)))
            descriptors.append(dict(id=key, label=label, value=float(stored.get(key,player.get(par_name, 1))),
                min=lo, max=hi, step=.1 if key=='scale' else .05 if key=='zoom' else .01,
                type='float', section='td', editable=par is not None, recordable=True))
        if not identifier.startswith('core:'):
            try:
                adaptation, values = self.editor._library()._parameter_context(self.editor._library_item(identifier))
                descriptors.extend(native_parameters(adaptation.schema, values))
            except Exception as error:
                base['error'] = str(error)
        base['parameters'] = descriptors
        return base

    def context(self, material_id=None):
        e = self.editor
        kind, identifier = self.material_identity(*e.current_material())
        active_id = 'core:'+identifier if kind == 'core' else identifier
        active = self.material(active_id) if active_id else dict(id='',label='Kein Material',image=None,parameters=[])
        source = str(self.controls.par.Source.eval())
        mode = 'show' if source == 'show' else 'material'
        recording = ('new_cue' if e._state('recording_new','0') == '1' else 'automation') if self.recording else False
        document, data = e.show(), e.automation_data()
        show = {}
        if document['cues']:
            sequence = self.transport.runtime()
            cue = next(c for c in document['cues'] if c['id'] == sequence.cue.id)
            if show_editor.is_imported(cue):
                key = show_editor.material_id(cue)
            else:
                core = getattr(e,'_catalog',lambda:{})()
                # Cue.effect contains the display label; the Material Player
                # menu and material-state store use the catalog identifier.
                effect_id = next((name for name,item in core.items()
                                  if name == cue['effect'] or item.get('label') == cue['effect']),cue['effect'])
                key = 'core:'+effect_id
            material = self.material(key)
            effective = dict(cue['parameters'])
            imported = e.imported_data().get(cue['id'], {}).get('values', {})
            for p in material['parameters']:
                if p['section'] == 'native':
                    raw = imported.get(p['native_name'])
                    if p['component'] is not None and isinstance(raw, (tuple,list)):
                        raw = raw[p['component']]
                    if isinstance(raw,(float,int,bool)):
                        effective[p['id']] = float(raw)
            effective.update(automation.values_at(data, cue['id'], sequence.elapsed))
            effective.update(live_values(cue['id']))
            for p in material['parameters']:
                p['value'] = effective.get(p['id'], p['value'])
                p['editable'] = bool(recording and p['recordable'])
            show = dict(id=cue['id'], name=cue['name'], material_id=key, material=material, image=material.get('image'),
                label=material['label'], duration=cue['duration'], elapsed=sequence.elapsed,
                transition=cue['transition'], transition_duration=cue['transition_duration'],
                transition_progress=sequence.plan().progress, playing=str(getattr(sequence.state,'value',sequence.state)) == 'playing',
                state=str(getattr(sequence.state,'value',sequence.state)),
                transition_in=(document['cues'][sequence.cue_index-1]['transition_duration'] if sequence.cue_index else 0.),
                transition_out=cue['transition_duration'],
                parameters=material['parameters'], automated_ids=list(data.get('tracks',{}).get(cue['id'],{})),
                modified_ids=list(data.get('edits',{}).get(cue['id'],{})))
        materials = {active_id:active}
        if material_id and material_id not in materials:
            materials[material_id] = self.material(material_id)
        return dict(mode=mode, active_material=active, catalog=deepcopy(self._catalog_items()), materials=materials,
                    show=show, recording=recording, transitions=list(show_editor.TRANSITION_ORDER), allow_automation_recording=True)

    def _set_parameter(self, material_id, parameter_id, value, *, explicit_load=False):
        context = self.context()
        if context['mode'] == 'show' and not explicit_load:
            if not self.recording or not self.take:
                raise ValueError('Show-Regler sind nur während einer MK2-Aufnahme aktiv')
            if material_id != context['show'].get('material_id'):
                raise ValueError('Material der laufenden Cue wurde geändert')
            descriptor = next((p for p in context['show']['parameters'] if p['id'] == parameter_id), None)
            if descriptor is None or not descriptor['recordable']:
                raise ValueError('Dieser Parameter ist nicht aufnehmbar')
            self.values[parameter_id] = checked_value(descriptor, value)
            self.take['touched'].add(parameter_id)
            self._save_take()
            return
        if material_id != context['active_material']['id']:
            raise ValueError('Entwurf ist nicht das aktive Material')
        descriptor = next((p for p in context['active_material']['parameters'] if p['id'] == parameter_id), None)
        if descriptor is None or not descriptor['editable']:
            raise ValueError('Parameter nicht bearbeitbar')
        value = checked_value(descriptor, value)
        if descriptor['section'] == 'native':
            self.editor._library().set_material_parameter(descriptor['native_name'], descriptor['component'], value)
        else:
            name = next(row[1] for row in CORE if row[0] == parameter_id)
            getattr(self.controls.par, name).val = value

    def _load(self, identifier, values=None):
        if self.recording:
            raise ValueError('Zuerst Aufnahme beenden')
        descriptor = self.material(identifier)
        available = {p['id']:p for p in descriptor['parameters']}
        clean = {}
        for key,value in (values or {}).items():
            if key not in available or not available[key]['editable']:
                raise ValueError('Gespeicherter Parameter ist nicht verfügbar: '+key)
            clean[key] = checked_value(available[key], value)
        library = self.editor._library()
        previous = library._state('selected_id','')
        previous_active = self.context()['active_material']
        source = str(self.controls.par.Source.eval())
        runtime = self.resolve('/project1/material_state_runtime')
        published = False
        try:
            if identifier.startswith('core:'):
                runtime.module.activate(identifier)
            else:
                library._set_state('selected_id', identifier)
                if not library.activate_selected():
                    raise ValueError('Material konnte nicht aktiviert werden')
                published = True
                if runtime is None:
                    raise ValueError('Material-Zustandsverwaltung fehlt')
                runtime.module.activate('madmapper:'+identifier)
            published = True
            self._last_material_id = identifier
            for key,value in clean.items():
                self._set_parameter(identifier,key,value,explicit_load=True)
        except Exception:
            try:
                if published and previous_active['id']:
                    old = previous_active['id']
                    if not old.startswith('core:'):
                        library._set_state('selected_id',old)
                        if not library.activate_selected():
                            raise RuntimeError('Materialwechsel fehlgeschlagen; vorheriges Material konnte nicht wiederhergestellt werden')
                    runtime.module.activate(old if old.startswith('core:') else 'madmapper:'+old)
                    self._last_material_id = old
                    for p in previous_active['parameters']:
                        if p['editable']:
                            self._set_parameter(old,p['id'],p['value'],explicit_load=True)
            finally:
                # Source=show reports only a sentinel, so the identity cache is
                # part of the transaction, including failures during rollback.
                self._last_material_id = previous_active['id']
                library._set_state('selected_id',previous)
                self.controls.par.Source.val = source
            raise
        if source == 'show':
            self.controls.par.Source.val = source

    def execute(self, command):
        action = command['action']
        if action == 'set_mode':
            if self.recording:
                raise ValueError('Zuerst Aufnahme beenden')
            if command['mode'] not in ('material','show'):
                raise ValueError('Unbekannter Player-Modus')
            self.controls.op('player_source_switch').module.choose(command['mode'])
        elif action == 'load_material':
            self._load(command['material_id'],command.get('values'))
        elif action == 'load_cue':
            if self.recording:
                raise ValueError('Zuerst Aufnahme beenden')
            cue_id = command.get('cue_id')
            if not any(c['id']==cue_id for c in self.editor.show()['cues']):
                raise ValueError('Cue ist nicht mehr verfügbar')
            render = self.owner.op('render_sync')
            if render is not None and hasattr(render.module,'preflight') and render.module.preflight() is False:
                raise ValueError('Show konnte nicht vorbereitet werden')
            self.transport.runtime().seek(cue_id,0.)
            self.transport.command('play')
        elif action == 'set_parameter':
            self._set_parameter(command['material_id'],command['parameter_id'],command['value'])
        elif action == 'set_show_field':
            if self.recording:
                raise ValueError('Clip-Einstellungen während der Aufnahme gesperrt')
            cue = self.transport.runtime().cue.id
            if command.get('cue_id') != cue:
                raise ValueError('Laufende Cue wurde geändert')
            field = command['field']
            edit = {'duration':dict(action='resize', duration=command['value']),
                    'transition':dict(action='transition', kind=command['value']),
                    'transition_duration':dict(action='transition', duration=command['value'])}.get(field)
            if edit is None:
                raise ValueError('Unbekanntes Clip-Feld')
            show,data = show_timeline.edit(self.editor.show(),self.editor.automation_data(),dict(edit,cue=cue))
            self.timeline.write(show,data)
        elif action == 'transport':
            if self.recording:
                raise ValueError('Zuerst Aufnahme beenden')
            operation = command['command']
            if operation == 'restart':
                self.transport.runtime().seek(0,0.)
                self.transport.command('play')
            elif operation in ('play','pause','stop','next','previous'):
                self.transport.command(operation)
            else:
                raise ValueError('Unbekannter Transport-Befehl')
        elif action == 'record_start':
            self._start_recording(command['kind'])
        elif action == 'record_stop':
            self.editor.stop_recording()
            self.recording_stopped()
        else:
            raise ValueError('Unbekannter MK2-Host-Befehl: '+action)

    def _start_recording(self, kind):
        if self.recording:
            raise ValueError('Aufnahme läuft bereits')
        if kind not in ('new_cue','automation'):
            raise ValueError('Unbekannte Aufnahmeart')
        context = self.context()
        if context['mode'] != 'show':
            raise ValueError('Aufnahme ist im Show Mode verfügbar')
        if not context['show']:
            raise ValueError('Keine Cue verfügbar')
        material_id = context['show']['material_id'] if context['mode']=='show' else context['active_material']['id']
        if context['mode']=='show' or context['active_material']['id'] != material_id:
            self._load(material_id)
        sequence = self.transport.runtime()
        self.editor._set_state('selected',sequence.cue_index)
        old = deepcopy(self.editor.automation_data())
        self.values.clear()
        self.editor.start_recording(as_new_cue=kind=='new_cue')
        if not self.recording:
            raise ValueError('Aufnahme konnte nicht gestartet werden')
        cue_id = self.editor._state('record_cue','')
        self.take = dict(kind=kind,cue_id=cue_id,before=old,touched=set())
        parameters = self.context()['show']['parameters']
        self.take['baseline'] = {p['id']:p['value'] for p in parameters if p['recordable']}
        self._save_take()
        # Seed before the first encoder movement, even when events share a frame.
        self.sample(0.)

    def sample(self, elapsed):
        if not self.take or not self.recording:
            return False
        e = self.editor
        sequence = self.transport.runtime()
        recorder = e._take()
        if sequence.cue.id != self.take['cue_id'] or (recorder and recorder.last_time is not None and elapsed+1e-6<recorder.last_time):
            e.stop_recording(reason='cue-ended')
            return True
        if recorder is not None:
            values = dict(self.take['baseline'])
            if self.take['kind'] == 'automation':
                values.update({k:v for k,v in automation.values_at(self.take['before'],self.take['cue_id'],elapsed).items() if k in values})
            values.update(self.values)
            recorder.sample(float(elapsed),values)
        return True

    def recording_stopped(self):
        if self.take is None:
            return
        take = self.take
        if take['kind'] == 'automation':
            e = self.editor
            current = e.automation_data()
            cue = take['cue_id']
            tracks = deepcopy(take['before'].get('tracks',{}).get(cue,{}))
            recorded = current.get('tracks',{}).get(cue,{})
            for name in take['touched']:
                if name in recorded:
                    tracks[name] = recorded[name]
            current.setdefault('tracks',{})[cue] = tracks
            # A previous hand-drawn edit would otherwise hide the new take.
            layers = deepcopy(take['before'].get('edits',{}).get(cue,{}))
            for name in take['touched']:
                layers.pop(name,None)
            if layers or cue in current.get('edits',{}):
                current.setdefault('edits',{})[cue] = layers
            e._write_automation(automation.validate(current))
        elif take['kind'] == 'new_cue':
            # Globals have no field in the legacy cue schema. Save their base
            # value as a constant lane when this take produced a retained cue.
            e = self.editor
            if any(c['id']==take['cue_id'] for c in e.show()['cues']):
                current = e.automation_data()
                tracks = current.setdefault('tracks',{}).setdefault(take['cue_id'],{})
                for key,_,_,_,_ in CORE:
                    if key in take['baseline']:
                        tracks.setdefault(key,[[0.,take['baseline'][key]]])
                e._write_automation(automation.validate(current))
        self.take = None
        self.values.clear()
        unstore = getattr(self.owner,'unstore',None)
        if callable(unstore):
            unstore(TAKE_STORAGE_KEY)


def show_value(parameter, fallback):
    """Expression helper: only recorded/live values override existing tone defaults."""
    if _host is None or str(_host.controls.par.Source.eval()) != 'show':
        return fallback
    sequence = _host.transport.runtime()
    if parameter in ('intensity','contrast'):
        cue = next((c for c in _host.editor.show()['cues'] if c['id']==sequence.cue.id),None)
        if cue is None or not show_editor.is_imported(cue):
            return fallback
    read_automation = getattr(_host.editor,'_cached_automation',_host.editor.automation_data)
    values = automation.values_at(read_automation(),sequence.cue.id,sequence.elapsed)
    values.update(live_values(sequence.cue.id))
    if parameter in ('intensity','contrast') and any(key in values for key in ('intensity','contrast')):
        # Enabling one tone control enables the shared stage; the untouched
        # control must come from this cue, never an unrelated browser material.
        fallback = cue['parameters'].get(parameter,fallback)
    return values.get(parameter,fallback)


def show_phase(fallback):
    """Independent continuous phase for recorded master speed; never rewrites the material store."""
    if _host is None:
        return fallback
    requested = show_value('global_master_speed',None)
    if requested is None:
        _host._phase = None
        return fallback
    now = time.monotonic()
    if _host._phase is None:
        _host._phase = (now,float(fallback),float(requested))
    last,phase,previous = _host._phase
    speed = float(_host.editor.player_values().get('Speed',1.))
    phase += max(0.,now-last) * previous * speed
    _host._phase = (now,phase,float(requested))
    return phase


def show_import_tone(fallback):
    """Enable the existing imported-material tone stage only for an explicit show override."""
    if _host is None or str(_host.controls.par.Source.eval()) != 'show':
        return fallback
    if show_value('intensity',None) is not None or show_value('contrast',None) is not None:
        return 1.
    return fallback
