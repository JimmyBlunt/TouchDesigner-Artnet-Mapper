"""Sixteen material/clip pads, with an optional MK2 HID display surface."""
from copy import deepcopy
import json
from pathlib import Path
from queue import Queue, Empty, Full
import time

_manager = None


def validate(config):
    if not isinstance(config, dict):
        raise ValueError('Ungültige Pad-Konfiguration')
    pads = config.get('pads', [])
    if not isinstance(pads, list) or len(pads) != 16:
        raise ValueError('Eine Pad-Bank braucht genau 16 Plätze.')
    clean = []
    for pad in pads:
        if not isinstance(pad, dict):
            raise ValueError('Ungültige Pad-Zuweisung')
        kind, target = pad.get('kind', 'material'), str(pad.get('target', ''))
        if kind not in ('material', 'cue') or len(target) > 200:
            raise ValueError('Ungültiges Pad-Ziel')
        clean.append(dict(kind=kind, target=target))
    return dict(pads=clean, hardware=bool(config.get('hardware', False)))


class Manager:
    def __init__(self, owner):
        import td
        self.owner = owner
        self.path = Path(td.project.folder)/'config'/'material_pads.json'
        self.version = 0
        self.selected = 0
        self.last = ''
        self.error = ''
        self.worker = None
        self.events = Queue(maxsize=16)
        self.catalog = []
        self.images = {}
        self.last_show = None
        self.catalog_version = 0
        self.refresh_catalog()
        # A useful initial bank uses distinct materials already in this show.
        from .show_editor import material_id, is_imported
        ids = list(dict.fromkeys(material_id(c) for c in self.editor.show()['cues'] if is_imported(c)))[:16]
        self.config = dict(hardware=False, pads=[dict(kind='material',target=ids[i] if i<len(ids) else '') for i in range(16)])
        if self.path.exists():
            self.config = validate(json.loads(self.path.read_text(encoding='utf-8')))
        self.update_surface()

    @property
    def editor(self):
        return self.owner.op('editor_callbacks').module

    def refresh_catalog(self):
        e = self.editor
        library = e._library()
        self.catalog, self.images = [], {}
        for item in library._items:
            if item.get('compatibility') == 'unsupported':
                continue
            key = item['id']
            try:
                path = library._safe_preview_path(item)
                if path and path.suffix.lower() in ('.png','.jpg','.jpeg','.webp') and path.stat().st_size <= 3000000:
                    self.images[key] = str(path)
            except (OSError, ValueError):
                pass
            self.catalog.append(dict(id=key, label=item['label'], kind='material', image=key if key in self.images else None))
        self.catalog.sort(key=lambda item:item['label'].casefold())
        self.catalog_version += 1

    def choices(self):
        from .show_editor import material_id, is_imported
        return self.catalog + [dict(id=c['id'],label='%02d · %s'%(i+1,c['name']),kind='cue',
                                    image=material_id(c) if is_imported(c) and material_id(c) in self.images else None)
                               for i,c in enumerate(self.editor.show()['cues'])]

    def update_surface(self):
        choices = {(c['kind'],c['id']):c for c in self.choices()}
        self.cards = []
        for i,pad in enumerate(self.config['pads']):
            item = choices.get((pad['kind'],pad['target']))
            self.cards.append(dict(number=i+1,label=item['label'] if item else ('Nicht verfügbar' if pad['target'] else 'Leer'),
                                   image=item.get('image') if item else None, available=item is not None, **pad))
        if self.worker:
            self.worker.snapshot = dict(cards=deepcopy(self.cards), selected=self.selected,
                                        images=dict(self.images), version=self.version)

    def snapshot(self):
        status = self.worker.status if self.worker else 'Direkte MK2-Anbindung aus'
        return dict(config=deepcopy(self.config),cards=deepcopy(self.cards),selected=self.selected,
                    version=self.version,status=status,last=self.last,error=self.error,catalog_version=self.catalog_version,
                    frame_version=self.worker.frame_version if self.worker else 0)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.config,ensure_ascii=False,indent=2),encoding='utf-8')
        temporary.replace(self.path)

    def post(self, index, version):
        try:
            self.events.put_nowait((int(index),version,time.monotonic()))
        except Full:
            pass

    def trigger(self, index, load=True):
        if not isinstance(index,int) or not 0 <= index < 16:
            raise ValueError('Pad muss zwischen 1 und 16 liegen')
        if self.editor._state('recording','0') == '1' and load:
            raise ValueError('Zuerst Aufnahme beenden.')
        pad = self.config['pads'][index]
        card = self.cards[index]
        if load and not card['available']:
            raise ValueError('Dieses Pad hat kein verfügbares Ziel.')
        self.selected = index
        self.update_surface()
        if not load:
            return
        if pad['kind'] == 'material':
            library = self.editor._library()
            previous = library._state('selected_id','')
            library._set_state('selected_id',pad['target'])
            if not library.activate_selected():
                library._set_state('selected_id',previous)
                raise ValueError('Material konnte nicht aktiviert werden; vorheriges Material bleibt erhalten.')
            self.last = 'Pad %d: %s im Material Player geladen'%(index+1,card['label'])
        else:
            t = self.owner.op('callbacks').module
            # Existing transport and material preflight remain authoritative.
            render = self.owner.op('render_sync')
            if render is not None and hasattr(render.module,'preflight'):
                if render.module.preflight() is False:
                    raise ValueError('Show konnte nicht vorbereitet werden.')
            t.runtime().seek(pad['target'],0)
            t.command('play')
            self.last = 'Pad %d: %s gestartet'%(index+1,card['label'])
        self.error = ''

    def command(self, command):
        action = command['action']
        if action == 'pads_config':
            if command.get('pads_version') != self.version:
                raise ValueError('Pad-Zuweisungen wurden geändert. Ansicht neu öffnen.')
            config = validate(command['config'])
            choices = {(c['kind'],c['id']) for c in self.choices()}
            for new,old in zip(config['pads'],self.config['pads']):
                if new['target'] and new != old and (new['kind'],new['target']) not in choices:
                    raise ValueError('Pad-Ziel ist nicht verfügbar.')
            previous = self.config
            self.config = config
            try:
                self.save()
            except Exception:
                self.config = previous
                raise
            self.version += 1
            self.update_surface()
        elif action == 'pad_select':
            self.trigger(command['index'],load=False)
        elif action == 'pad_trigger':
            if command.get('pads_version') != self.version:
                raise ValueError('Pad-Zuweisung wurde geändert. Erneut wählen.')
            self.trigger(command['index'])
        else:
            raise ValueError('Unbekannter Pad-Befehl')
        self.error = ''

    def tick(self):
        show = self.owner.op('show_json').text
        if show != self.last_show:
            self.last_show = show
            self.update_surface()
        if self.config['hardware'] and self.worker is None:
            from .maschine_mk2 import Surface
            self.worker = Surface(self.post)
            self.update_surface()
            self.worker.start()
        elif not self.config['hardware'] and self.worker is not None:
            self.worker.stop()
            self.worker = None
        for _ in range(4):
            try:
                index,version,when = self.events.get_nowait()
            except Empty:
                break
            if not self.config['hardware'] or version != self.version or time.monotonic()-when > 2:
                continue
            try:
                self.trigger(index)
            except Exception as error:
                self.error = str(error)


def tick(owner):
    global _manager
    if _manager is None:
        from .mk2_runtime import Manager as WorkflowManager
        _manager = WorkflowManager(owner)
    try:
        _manager.tick()
    except Exception as error:
        _manager.error = str(error)
