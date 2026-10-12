"""Local timeline window. Only tick() accesses TouchDesigner (main thread).

HTTP worker threads serve immutable snapshots and enqueue bounded commands.
No LED/network-output settings are changed by installation or opening the UI.
"""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Queue, Empty
import json
import secrets
import threading
import time
import webbrowser
from urllib.parse import urlsplit, parse_qs

from . import show_timeline as timeline
from . import show_automation as automation
from . import show_editor as editor

PORT = 9991
ROOT = Path(__file__).with_name('timeline_assets')
_bridge = None
_last_tick = 0.


class Bridge:
    def __init__(self, host, port=PORT):
        self.host = host
        self.history = timeline.History()
        self.commands = Queue(maxsize=32)
        self.token = secrets.token_urlsafe(32)
        self.state = {}
        self.saved = None
        self.raw = None
        self.port = port
        self.server = None
        self.error = None
        self.refresh()
        if hasattr(host, 'saved_revision'):
            self.saved = host.saved_revision()
            self.refresh()

    def refresh(self):
        raw = self.host.raw()
        if raw != self.raw:
            show, data, parameters = self.host.documents()
            self.history.observe(show, data)
            self.document = dict(show=show, automation=data, parameters=parameters,
                                 rows=timeline.layout(show), revision=timeline.revision(show, data),
                                 transitions=[dict(value=x, label=editor.TRANSITION_LABELS[x])
                                              for x in editor.TRANSITION_ORDER])
            self.raw = raw
        document = self.document
        self.error = None
        self.state = dict(document, transport=self.host.transport(),
                          undo=bool(self.history.undo_stack), redo=bool(self.history.redo_stack),
                          dirty=self.saved != document['revision'], error=self.error)
        if hasattr(self.host, 'midi_state'):
            self.state['midi'] = self.host.midi_state()
        if hasattr(self.host, 'pads_state'):
            self.state['pads'] = self.host.pads_state()
            self.pad_catalog, self.pad_images, self.pad_frames = self.host.pads_assets()
        self.updated = time.monotonic()

    def execute(self, command):
        self.refresh()
        action = command.get('action')
        if action in ('pads_config', 'pad_select', 'pad_trigger', 'pads_bank'):
            self.host.pads_command(command)
            self.refresh()
            return self.state
        if action in ('midi_config', 'midi_learn', 'midi_release'):
            self.host.midi_command(command)
            self.refresh()
            return self.state
        if action in ('play', 'pause', 'stop', 'seek', 'save', 'undo', 'redo',
                      'resize', 'move', 'transition', 'lane', 'reset_lane', 'loop'):
            if self.state['transport'].get('recording'):
                raise ValueError('Aufnahme läuft. Zuerst Aufnahme im Show-Editor beenden.')
        else:
            raise ValueError('Unbekannter Befehl')
        if command.get('revision') != self.state['revision']:
            raise ValueError('Show wurde anderswo geändert. Ansicht wurde aktualisiert; Änderung erneut ausführen.')
        current = (self.state['show'], self.state['automation'])
        if action in ('play', 'pause', 'stop', 'seek'):
            self.host.control(command)
        elif action == 'save':
            self.host.save()
            self.raw = None
            self.refresh()
            self.saved = self.state['revision']
        else:
            # History changes only survive a successful host write.
            previous_history = deepcopy(self.history)
            try:
                if action in ('undo', 'redo'):
                    after = self.history.travel(current, action == 'redo')
                else:
                    after = timeline.edit(*current, command)
                self.host.write(*after)
                if action not in ('undo', 'redo'):
                    self.history.push(current, after)
            except Exception:
                self.history = previous_history
                raise
        self.error = None
        self.refresh()
        return self.state

    def tick(self):
        for _ in range(4):
            try:
                job = self.commands.get_nowait()
            except Empty:
                break
            if time.monotonic() > job['deadline']:
                job['error'] = 'TouchDesigner antwortet nicht; Änderung wurde verworfen.'
            else:
                try:
                    job['result'] = self.execute(job['command'])
                except Exception as error:
                    job['error'] = str(error)
            job['done'].set()
        try:
            self.refresh()
        except Exception as error:
            self.error = str(error)
            self.state = dict(self.state, error=self.error)

    def start(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def respond(self, status, payload, mime='application/json; charset=utf-8'):
                body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if isinstance(payload, dict) else payload
                self.send_response(status)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

            def allowed(self):
                return self.headers.get('Host') in (f'127.0.0.1:{bridge.port}', f'localhost:{bridge.port}')

            def do_GET(self):
                if not self.allowed():
                    return self.respond(403, dict(error='Host nicht erlaubt'))
                path = self.path.split('?')[0]
                if path == '/api/state':
                    state = bridge.state
                    if self.path.partition('?revision=')[2] == state.get('revision'):
                        state = {k: state[k] for k in ('revision', 'transport', 'undo', 'redo', 'dirty', 'error', 'midi', 'pads') if k in state}
                    return self.respond(200, dict(state, token=bridge.token, stale=time.monotonic()-bridge.updated > 2.0))
                if path == '/api/pad_catalog':
                    return self.respond(200, dict(items=getattr(bridge, 'pad_catalog', [])))
                if path == '/api/pad_image':
                    key = parse_qs(urlsplit(self.path).query).get('id', [''])[0]
                    approved = getattr(bridge, 'pad_images', {}).get(key)
                    if approved:
                        try:
                            image = Path(approved)
                            mime = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[image.suffix.lower()]
                            return self.respond(200, image.read_bytes(), mime)
                        except (OSError, KeyError):
                            pass
                    return self.respond(404, dict(error='Kein Vorschaubild'))
                if path == '/api/pad_display':
                    side = parse_qs(urlsplit(self.path).query).get('side', [''])[0]
                    frames = getattr(bridge, 'pad_frames', ())
                    if side in ('0', '1') and len(frames) == 2:
                        return self.respond(200, frames[int(side)], 'image/png')
                    return self.respond(404, dict(error='Display noch nicht übertragen'))
                files = {'/': ('index.html', 'text/html; charset=utf-8'),
                         '/timeline.js': ('timeline.js', 'text/javascript; charset=utf-8'),
                         '/pads.js': ('pads.js', 'text/javascript; charset=utf-8'),
                         '/timeline.css': ('timeline.css', 'text/css; charset=utf-8')}
                if path not in files:
                    return self.respond(404, dict(error='Nicht gefunden'))
                name, mime = files[path]
                self.respond(200, (ROOT/name).read_bytes(), mime)

            def do_POST(self):
                origin = self.headers.get('Origin')
                if (not self.allowed() or self.headers.get('X-Timeline-Token') != bridge.token or
                    origin not in (None, f'http://127.0.0.1:{bridge.port}', f'http://localhost:{bridge.port}')):
                    return self.respond(403, dict(error='Sitzung neu laden'))
                if self.path != '/api/command':
                    return self.respond(404, dict(error='Nicht gefunden'))
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    if not 0 < length <= 1000000:
                        raise ValueError('Anfrage zu groß oder leer')
                    command = json.loads(self.rfile.read(length))
                    if not isinstance(command, dict):
                        raise ValueError('Befehl muss ein Objekt sein')
                    job = dict(command=command, deadline=time.monotonic()+5, done=threading.Event())
                    bridge.commands.put_nowait(job)
                    if not job['done'].wait(6):
                        return self.respond(503, dict(error='TouchDesigner antwortet nicht. Verbindung prüfen.'))
                    if 'error' in job:
                        return self.respond(409, dict(error=job['error']))
                    return self.respond(200, job['result'])
                except Exception as error:
                    self.respond(400, dict(error=str(error)))

        self.server = ThreadingHTTPServer(('127.0.0.1', self.port), Handler)
        threading.Thread(target=self.server.serve_forever, name='ShowTimelineHTTP', daemon=True).start()


class TDHost:
    def __init__(self, owner):
        self.owner = owner

    @property
    def editor(self):
        return self.owner.op('editor_callbacks').module

    @property
    def transport_module(self):
        return self.owner.op('callbacks').module

    def raw(self):
        return tuple(self.owner.op(name).text for name in ('show_json', 'automation_json', 'imported_json'))

    def midi_state(self):
        from .show_midi import _manager
        return _manager.snapshot() if _manager is not None else None

    def pads_state(self):
        from .show_pads import _manager
        return _manager.snapshot() if _manager else None

    def pads_assets(self):
        from .show_pads import _manager
        if not _manager:
            return [], {}, ()
        return _manager.choices(), dict(_manager.images), _manager.worker.frames if _manager.worker else ()

    def pads_command(self, command):
        from .show_pads import _manager
        if not _manager:
            raise ValueError('Material-Pads werden noch initialisiert')
        try:
            _manager.command(command)
        except Exception as error:
            _manager.error = str(error)
            raise

    def midi_command(self, command):
        from .show_midi import _manager
        if _manager is None:
            raise ValueError('MIDI wird noch initialisiert')
        try:
            _manager.command(command)
        except Exception as error:
            _manager.error = str(error)
            raise

    def documents(self):
        e = self.editor
        show, data = e.show(), automation.validate(json.loads(self.owner.op('automation_json').text))
        imported = e.imported_data()
        parameters = {}
        schemas = {}
        for cue in show['cues']:
            values = dict(cue['parameters'], brightness=cue['brightness'])
            values = {k: v for k, v in values.items() if automation.recordable(k)}
            is_imported = editor.is_imported(cue)
            supported = None
            if is_imported:
                values = {k: v for k, v in values.items() if k in e.IMPORTED_CORE or k == 'brightness'}
                material_id = editor.material_id(cue)
                if material_id not in schemas:
                    try:
                        adaptation, defaults = e._library()._parameter_context(e._library_item(material_id))
                        schemas[material_id] = {p.name for p in adaptation.schema if not p.compile_time}
                    except Exception:
                        schemas[material_id] = None
                supported = schemas[material_id]
            for key, value in imported.get(cue['id'], {}).get('values', {}).items():
                if isinstance(value, (float, int)) and not isinstance(value, bool) and (supported is None or key in supported):
                    values[automation.imported_track_name(key)] = float(value)
            for name in set(data.get('tracks', {}).get(cue['id'], {})) | set(data.get('edits', {}).get(cue['id'], {})):
                values.setdefault(name, 0.)
            parameters[cue['id']] = values
        return show, data, parameters

    def transport(self):
        t = self.transport_module
        index = int(t._get('cue_index', 0))
        return dict(index=index, elapsed=float(t._get('elapsed', 0)),
                    state=str(t._get('transport', 'stopped')), recording=self.editor._state('recording', '0') == '1')

    def write(self, show, data):
        e, t = self.editor, self.transport_module
        old_show, old_data = e.show(), e.automation_data()
        if e.unresolved(show):
            raise ValueError('Show enthält nicht verfügbare Materialien. Zuerst im Show-Editor korrigieren.')
        sequence = t.runtime() if old_show['cues'] else None
        cue_id = sequence.cue.id if sequence else None
        selected_id = old_show['cues'][e.selected()]['id'] if old_show['cues'] else None
        try:
            e._write_automation(data)
            if show != old_show:
                # Preserve the running sequence's identity/time across an edit.
                e.write(show)
                if sequence:
                    new = t.runtime()
                    new.cue_index = next((i for i, c in enumerate(new.show.cues) if c.id == cue_id), 0)
                    new.elapsed = min(sequence.elapsed, new.cue.duration-1e-6)
                    new.state = sequence.state
                    new._current_slot = sequence._current_slot
                    new._current_time_offset = sequence._current_time_offset
                if selected_id:
                    index = next((i for i, c in enumerate(show['cues']) if c['id'] == selected_id), 0)
                    e._set_state('selected', index)
                    e._set_state('page', index//10)
            t.sync()
            e.repaint()
        except Exception:
            e._write_automation(old_data)
            if show != old_show:
                e.write(old_show)
                if sequence:
                    t._runtime_record = (self.owner.op('show_json').text, sequence)
                    t.sync()
            raise

    def control(self, command):
        t = self.transport_module
        if command['action'] == 'seek':
            index, elapsed = timeline.locate(self.editor.show(), command['time'])
            t.runtime().seek(index, elapsed)
            t.sync()
        else:
            t.command(command['action'])

    def save(self):
        self.editor._apply('save_show')

    def saved_revision(self):
        import td
        show = self.editor.show()
        path = Path(td.project.folder)/'shows'/(editor.slugify(show['name'], fallback='show')+'.json')
        try:
            saved_show = editor._validated(json.loads(path.read_text(encoding='utf-8-sig')))
            saved_data = automation.validate(json.loads(path.with_suffix('.automation.json').read_text(encoding='utf-8-sig')))
            return timeline.revision(saved_show, saved_data)
        except (OSError, ValueError):
            return None


def tick():
    global _last_tick
    from . import show_midi
    if show_midi._manager is None:
        import td
        show_midi.install(td.op('/project1/show_control'))
    show_midi.tick()
    if time.monotonic()-_last_tick < .1:
        return
    _last_tick = time.monotonic()
    from . import show_pads
    import td
    show_pads.tick(td.op('/project1/show_control'))
    if _bridge is not None:
        _bridge.tick()


def launch(open_browser=True):
    global _bridge
    import td
    if _bridge is None:
        candidate = Bridge(TDHost(td.op('/project1/show_control')))
        candidate.start()
        _bridge = candidate
    if open_browser:
        webbrowser.open(f'http://127.0.0.1:{PORT}/', new=1)
    return f'http://127.0.0.1:{PORT}/'


def install():
    import td
    owner = td.op('/project1/show_control')
    if owner is None or owner.op('editor_callbacks') is None:
        raise RuntimeError('Show-Editor muss zuerst installiert werden')
    from . import show_midi
    show_midi.install(owner)
    transport = owner.op('callbacks')
    source = timeline.install_sync_source(transport.text)
    editor_node = owner.op('editor_callbacks')
    editor_source = timeline.install_editor_source(editor_node.text)
    if editor_source != editor_node.text:
        editor_node.text = editor_source
    if source != transport.text:
        # Rebinding callbacks otherwise pauses a currently playing show.
        record = getattr(transport.module, '_runtime_record', None)
        transport.text = source
        transport.module._runtime_record = record
    canvas = owner.op('control_panel')
    from .build_show_editor import _place, _set, paint_button
    button = canvas.op('ed_timeline') or canvas.create(td.buttonCOMP, 'ed_timeline')
    button.name = 'ed_timeline'
    _place(button, 870, 952, 110, 32, 260)
    _set(button, 'label', 'TIMELINE')
    _set(button, 'buttontype', 'momentary')
    _set(button, 'fontsize', 12)
    paint_button(button, (.06, .25, .27))
    click = owner.op('timeline_click') or owner.create(td.panelexecuteDAT, 'timeline_click')
    click.name = 'timeline_click'
    click.par.active = False
    for key, value in dict(fromop=button.path, panels=button.path, panelvalue='lselect',
                           offtoon=True, ontooff=False, whileon=False, whileoff=False, valuechange=False).items():
        _set(click, key, value)
    click.text = 'def onOffToOn(panelValue):\n    from pixelblaze_mapper.show_timeline_ui import launch\n    launch()\n'
    click.par.active = True
    driver = owner.op('timeline_driver') or owner.create(td.executeDAT, 'timeline_driver')
    driver.name = 'timeline_driver'
    driver.par.active = False
    driver.text = '''def onFrameStart(frame):
    from pixelblaze_mapper.show_timeline_ui import tick
    tick()
    return
'''
    _set(driver, 'framestart', True)
    _set(driver, 'frameend', False)
    driver.par.active = True
    return button.path
