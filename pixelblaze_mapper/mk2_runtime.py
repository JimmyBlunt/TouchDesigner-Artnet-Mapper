"""Main-thread integration of the MK2 workflow, TD host and USB worker."""
from copy import deepcopy
import json
from pathlib import Path
from queue import Queue, Empty, Full
import time

from .mk2_workflow import Controller, validate_config, VERSION, material_categories


class Manager:
    def __init__(self, owner):
        import td
        from .mk2_td import Host
        self.owner = owner
        self.host = Host(owner)
        self.path = Path(td.project.folder)/'config'/'material_pads.json'
        self.version = 0
        self.catalog_version = 0
        self.last = self.error = ''
        self.worker = None
        self.windows = None
        self.window_error = ''
        self.events = Queue(maxsize=128)
        self.catalog, self.images = [], {}
        self.last_show = None
        self.refresh_catalog()
        from .show_editor import material_id, is_imported
        ids = list(dict.fromkeys(material_id(c) for c in self.editor.show()['cues'] if is_imported(c)))[:16]
        config = dict(hardware=False,pads=[dict(kind='material',target=ids[i] if i<len(ids) else '') for i in range(16)])
        if self.path.exists():
            config = json.loads(self.path.read_text(encoding='utf-8'))
        self.controller = Controller(config)
        if callable(getattr(self.host, 'resolve', None)):
            try:
                from .mk2_windows import WindowDirector
                self.windows = WindowDirector(self.host.resolve)
            except Exception as error:
                self.window_error = str(error)
        self._refresh_context()
        self.update_surface()

    @property
    def editor(self):
        return self.owner.op('editor_callbacks').module

    def refresh_catalog(self):
        library = self.editor._library()
        catalog, images = [], {}
        for item in library._items:
            if item.get('compatibility') == 'unsupported':
                continue
            key = item['id']
            try:
                path = library._safe_preview_path(item)
                if path and path.suffix.lower() in ('.png','.jpg','.jpeg','.webp') and path.stat().st_size <= 3000000:
                    images[key] = str(path)
            except (OSError,ValueError):
                pass
            categories = material_categories(item)
            category = ' / '.join(categories)
            catalog.append(dict(id=key,label=item['label'],kind='material',category=category,
                                categories=categories,
                                image=key if key in images else None))
        for key,entry in getattr(self.editor,'_catalog',lambda:{})().items():
            label = entry.get('label',key) if isinstance(entry,dict) else key
            catalog.append(dict(id='core:'+key,label=label,kind='material',category='TouchDesigner',
                                categories=['TouchDesigner'],image=None))
        self.catalog = sorted(catalog,key=lambda x:x['label'].casefold())
        self.images = images
        self.catalog_source = library._items
        self.catalog_version += 1

    def choices(self):
        from .show_editor import material_id, is_imported
        return self.catalog + [dict(id=c['id'],label='%02d · %s'%(i+1,c['name']),kind='cue',
                                   image=material_id(c) if is_imported(c) and material_id(c) in self.images else None)
                              for i,c in enumerate(self.editor.show()['cues'])]

    def _refresh_context(self):
        controller = self.controller
        controller.set_context(dict(catalog=self.catalog))
        target = controller.edit_material.get('id') if controller.edit_material else None
        if not target and controller.screen == 'browse':
            target = controller.browse_selected_id()
        if not target and controller.screen in ('pad_menu','confirm_assign'):
            target = controller.assign_target or controller.config['groups'][controller.bank]['pads'][controller.pad_index]['target']
        context = self.host.context(target)
        context['catalog'] = self.catalog
        context['allow_automation_recording'] = True
        controller.set_context(context)

    def update_surface(self):
        view = self.controller.snapshot()
        bank = self.controller.config['groups'][self.controller.bank]
        self.config = dict(hardware=self.controller.config['hardware'],pads=deepcopy(bank['pads']))
        self.selected = self.controller.pad_index
        self.cards = view['cards']
        # Keep pre-existing cue-pad assignments usable in the web configuration.
        cues = {c['id']:c for c in self.choices() if c['kind']=='cue'}
        for card in self.cards:
            if card['kind']=='cue' and card['target'] in cues:
                card.update(label=cues[card['target']]['label'],image=cues[card['target']]['image'],available=True)
        if self.worker:
            self.worker.snapshot = dict(cards=deepcopy(self.cards),selected=self.selected,images=dict(self.images),
                                        version=self.version,controller=view)
        self.view = view
        self._window_action('observe', view, self.images)

    def _window_action(self, method, *args):
        if self.windows is not None:
            try:
                getattr(self.windows, method)(*args)
                if method != 'observe':
                    self.window_error = ''
            except Exception as error:
                # A missing desktop window must not undo a successful mode or
                # material change, nor interrupt controller/event processing.
                self.window_error = str(error)
                self.controller.error = 'Fenster: '+str(error)

    def snapshot(self):
        # The large library stays on the dedicated catalog endpoint.
        view = {k:v for k,v in self.view.items() if k not in ('browse_items',)}
        return dict(config=deepcopy(self.config),cards=deepcopy(self.cards),selected=self.selected,
                    version=self.version,status=self.worker.status if self.worker else 'Direkte MK2-Anbindung aus',
                    last=self.last,error=self.error or self.view.get('error',''),catalog_version=self.catalog_version,
                    frame_version=self.worker.frame_version if self.worker else 0,controller=view,
                    bank=self.controller.bank,groups=[dict(name=g['name'],count=sum(bool(p['target']) for p in g['pads'])) for g in self.controller.config['groups']],
                    release=VERSION, window_error=self.window_error,
                    windows=self.windows.status() if self.windows is not None else None)

    def _write_config(self, config):
        clean = validate_config(config)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
        temporary.replace(self.path)
        return clean

    def save(self):
        self._write_config(self.controller.export_config())

    def post(self, index, version):
        self.post_event(dict(type='button',name='pad',index=index,down=True),version)
        self.post_event(dict(type='button',name='pad',index=index,down=False),version)

    def post_event(self,event,version):
        if event.get('type') == 'connection_reset':
            # Only queue operations on the USB thread. Drop pre-disconnect
            # actions, then clear key latches on the TD main thread below.
            while True:
                try:
                    self.events.get_nowait()
                except Empty:
                    break
        try:
            self.events.put_nowait((deepcopy(event),version,time.monotonic()))
        except Full:
            self.error = 'Zu viele Controller-Eingaben; bitte kurz loslassen.'

    def _execute(self, commands):
        for command in commands:
            if command['action']=='persist_config':
                try:
                    self._write_config(command['config'])
                except Exception as error:
                    self.controller.dispatch(dict(type='command_result',request_id=command['request_id'],success=False,error=str(error)))
                    raise
                self.controller.dispatch(dict(type='command_result',request_id=command['request_id'],success=True))
                self.version += 1
                self.last = 'Favoriten gespeichert.' if command.get('purpose') == 'favorites' else 'Pad-Preset gespeichert.'
            elif command['action']=='flash_pad':
                pass  # Flash deadline is part of the immutable controller snapshot.
            else:
                self.host.execute(command)
                if command['action'] == 'set_mode':
                    self._window_action('show_mode', command['mode'])
                elif command['action'] == 'load_material':
                    self._window_action('material_loaded', command['material_id'])

    def dispatch(self,event):
        activity = event.get('type') != 'button' or event.get('down', True)
        if activity:
            self.controller.error = ''
        self._refresh_context()
        previous_bank = self.controller.bank
        try:
            commands = self.controller.dispatch(event)
            self._execute(commands)
        except Exception as error:
            self.error = str(error)
            self.controller.dispatch(dict(type='command_result', success=False, error=self.error))
            raise
        if self.controller.bank != previous_bank:
            self.version += 1
        self._refresh_context()
        if activity or commands:
            self.error = ''
        self.update_surface()

    def trigger(self,index,load=True):
        if type(index) is not int or not 0<=index<16:
            raise ValueError('Pad muss zwischen 1 und 16 liegen')
        if self.controller.screen in ('pad_edit','confirm_edit') and self.controller.snapshot()['dirty']:
            raise ValueError('Zuerst den Pad-Entwurf speichern oder verwerfen.')
        self.controller.pad_index = index
        self.update_surface()
        if load:
            if self.editor._state('recording','0')=='1':
                raise ValueError('Zuerst Aufnahme beenden.')
            pad = self.config['pads'][index]
            if not self.cards[index]['available']:
                raise ValueError('Dieses Pad hat kein verfügbares Ziel.')
            if pad['kind']=='cue':
                t = self.owner.op('callbacks').module
                self.owner.op('render_sync').module.preflight()
                t.runtime().seek(pad['target'],0)
                t.command('play')
            else:
                self.host.execute(dict(action='load_material',material_id=pad['target'],values=pad.get('values',{})))
            self.last = 'Pad %s%d: %s'%(chr(65+self.controller.bank),index+1,self.cards[index]['label'])
            self._refresh_context()
            self.update_surface()
        self.error = ''

    def command(self,command):
        action = command['action']
        if action in ('pads_config','pad_trigger','pads_bank') and command.get('pads_version') != self.version:
            raise ValueError('Pad-Zuweisungen wurden geändert. Ansicht neu öffnen.')
        if action=='pads_config':
            from .show_pads import validate
            candidate = validate(command['config'])
            full = self.controller.export_config()
            old = full['groups'][self.controller.bank]['pads']
            choices = {(c['kind'],c['id']) for c in self.choices()}
            for index,(new,previous) in enumerate(zip(candidate['pads'],old)):
                changed = (new['kind'],new['target']) != (previous['kind'],previous['target'])
                if changed and new['target'] and (new['kind'],new['target']) not in choices:
                    raise ValueError('Pad-Ziel ist nicht verfügbar.')
                new['values'] = {} if changed else deepcopy(previous.get('values',{}))
            if self.controller.snapshot()['dirty']:
                raise ValueError('Zuerst den Pad-Entwurf speichern oder verwerfen.')
            full['groups'][self.controller.bank]['pads'] = candidate['pads']
            full['hardware'] = candidate['hardware']
            self._write_config(full)
            self.controller.set_context(dict(config=full))
            self.version += 1
        elif action=='pads_bank':
            bank = command.get('bank')
            if type(bank) is not int or not 0<=bank<8:
                raise ValueError('Ungültige Pad-Gruppe')
            if self.controller.snapshot()['dirty']:
                raise ValueError('Zuerst den Pad-Entwurf speichern oder verwerfen.')
            self.controller.bank = bank
            self.controller.pad_index = 0
            self.version += 1
        elif action in ('pad_select','pad_trigger'):
            self.trigger(command['index'],load=action=='pad_trigger')
        else:
            raise ValueError('Unbekannter Pad-Befehl')
        self.error = ''
        self.update_surface()

    def tick(self):
        if self.editor._library()._items is not getattr(self,'catalog_source',None):
            self.refresh_catalog()
        self._refresh_context()
        self._execute(self.controller.tick())
        enabled = self.controller.config['hardware']
        if enabled and self.worker is None:
            from .maschine_mk2 import Surface
            self.worker = Surface(self.post,event_callback=self.post_event)
            self.update_surface()
            self.worker.start()
        elif not enabled and self.worker:
            self.worker.stop()
            self.worker = None
            self.controller.held.clear()
        browse_moved = False
        for _ in range(32):
            try:
                event,version,when = self.events.get_nowait()
            except Empty:
                break
            if event.get('type') == 'connection_reset':
                self.controller.held.clear()
                self.controller.rec_pending = self.controller.rec_chord = False
                self.controller.flash_until.clear()
                self.controller.reset_browse_motion()
                continue
            if not enabled or version!=self.version or time.monotonic()-when>1:
                # Release stale keys so a dropped release cannot latch REC/ERASE.
                if event.get('type')=='button' and event.get('down') is False:
                    self.controller.held.discard((event.get('name'),event.get('index',0)))
                    if event.get('name')=='rec':
                        self.controller.rec_pending = self.controller.rec_chord = False
                continue
            try:
                if event.get('type') == 'wheel':
                    event = dict(event,timestamp=when)
                    if getattr(self.controller, 'screen', None) == 'browse':
                        # Browsing only changes selection, never the live host.
                        # Preserve every receive timestamp/order but publish one
                        # final frame: rebuilding 635 materials per detent used
                        # to cost ~70+ ms and could outrun the one-second queue.
                        self.controller.error = ''
                        self._execute(self.controller.dispatch(event))
                        self.error = ''
                        browse_moved = True
                        continue
                self.dispatch(event)
                browse_moved = False
            except Exception as error:
                self.error = str(error)
        if browse_moved:
            self._refresh_context()
        self.update_surface()
