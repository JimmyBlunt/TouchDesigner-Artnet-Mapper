"""Owned MK2 selection stills; never activate materials or alter player controls.

Called on browse entry/settled selection by the window director, not every frame.
Compilation uses the library's isolated hover API, then immediately captures its
result into our own locked Select TOP. Later browser hover cannot change it.
"""
from pathlib import Path


PARENT = '/project1/mk2_windows'
PANEL = PARENT + '/preview_panel'
LIBRARY = '/project1/madmapper_library/runtime'
EDITOR = '/project1/show_control/editor_callbacks'
THUMBNAIL_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}


def _set(node, **values):
    for name, value in values.items():
        parameter = getattr(node.par, name, None)
        if parameter is not None:
            parameter.val = value


class MaterialPreview:
    def __init__(self, resolve, tdmodule):
        self.resolve = resolve
        self.td = tdmodule
        self.material_id = None
        self.state = {}

    def _node(self, parent, typename, name):
        node = parent.op(name)
        if node is None:
            node = parent.create(getattr(self.td, typename), name)
        return node

    def _panel(self):
        parent = self.resolve(PARENT)
        if parent is None:
            raise RuntimeError('MK2-Fensterverwaltung fehlt: ' + PARENT)
        panel = self._node(parent, 'containerCOMP', 'preview_panel')
        _set(panel, w=1280, h=850, hmode='fixed', vmode='fixed',
             bgcolorr=.012, bgcolorg=.018, bgcolorb=.028, bgalpha=1)
        for name, y, height, size in (('title', 794, 44, 32), ('status', 724, 64, 22),
                                      ('hint', 18, 38, 22)):
            node = self._node(panel, 'textCOMP', name)
            _set(node, x=32, y=y, w=1216, h=height, hmode='fixed', vmode='fixed',
                 fontsize=size, text='', type='multiline', wordwrap=True,
                 fontcolorr=.94, fontcolorg=.96, fontcolorb=1, fontalpha=1,
                 bgalpha=0, alignx='left', aligny='center', clickthrough=True)
        viewer = self._node(panel, 'opviewerCOMP', 'image')
        _set(viewer, x=32, y=70, w=1216, h=646, hmode='fixed', vmode='fixed',
             allowpanel=False, display=False, opviewer='')
        return panel

    def _library(self):
        node = self.resolve(LIBRARY)
        return node.module if node is not None else None

    def _capture(self, panel, target):
        if target is None:
            raise ValueError('Kein Vorschau-Bild verfügbar.')
        frame = self._node(panel, 'selectTOP', 'captured_frame')
        frame.lock = False
        try:
            _set(frame, top=target.path)
            frame.cook(force=True)
            errors = frame.errors()
            if errors:
                raise ValueError('Vorschau konnte nicht erfasst werden: ' + str(errors))
            frame.lock = True
        finally:
            # Locked pixels belong to this panel. Do not retain a live link to
            # the shared hover TOP or to a changing Core browser preview.
            frame.lock = True
            _set(frame, top='')
        _set(panel.op('image'), opviewer=frame.path, display=True)
        return frame.path

    def _core(self, key):
        node = self.resolve(EDITOR)
        if node is None:
            raise ValueError('TouchDesigner-Materialkatalog fehlt.')
        catalog = node.module._catalog()
        entry = catalog.get(key)
        if entry is None:
            matches = [value for name, value in catalog.items() if name.casefold() == key.casefold()]
            if matches and len({value.get('index') for value in matches}) == 1:
                entry = matches[0]
        if not isinstance(entry, dict):
            raise ValueError('TouchDesigner-Material nicht verfügbar: ' + key)
        index = entry.get('index')
        if type(index) is not int or not 0 <= index < 25:
            raise ValueError('Ungültiger TouchDesigner-Vorschauindex.')
        preview = self.resolve('/project1/material_browser/preview_%d' % index)
        if preview is None:
            raise ValueError('TouchDesigner-Vorschau fehlt: ' + key)
        return str(entry.get('label') or key), preview

    def _thumbnail(self, library, item, descriptor):
        if library is None:
            return None
        candidates = [descriptor.get('preview_path'), descriptor.get('image')]
        if item is not None:
            candidates.append(item.get('preview_path'))
        validator = getattr(library, '_validated_file', None)
        for value in candidates:
            if not isinstance(value, (str, Path)) or not value:
                continue
            try:
                # Descriptor paths are hints, never authority to read an
                # arbitrary local file. Re-use the library's Approved Roots.
                approved = validator(value, THUMBNAIL_EXTENSIONS) if callable(validator) else None
                if approved is not None:
                    path = Path(approved)
                    if path.is_file() and path.stat().st_size <= 3_000_000:
                        return path
            except (OSError, ValueError):
                pass
        if item is not None:
            try:
                safe_path = getattr(library, '_safe_preview_path', lambda _: None)(item)
                if safe_path:
                    path = Path(safe_path)
                    if path.suffix.lower() in THUMBNAIL_EXTENSIONS and path.is_file() and path.stat().st_size <= 3_000_000:
                        return path
            except (OSError, ValueError):
                pass
        return None

    def select(self, material_id, descriptor=None):
        key = str(material_id or '').strip()
        if key.startswith('madmapper:'):
            key = key[len('madmapper:'):]
        if self.material_id == key and self.resolve(PANEL) is not None:
            return PANEL
        descriptor = descriptor if isinstance(descriptor, dict) else {}
        if descriptor.get('id') not in (None, key, material_id):
            descriptor = {}
        panel = self._panel()
        label = str(descriptor.get('label') or key or 'Kein Material ausgewählt')
        library, item = self._library(), None
        status, error, target_path = 'error', '', None
        try:
            if key.startswith('core:'):
                label, target = self._core(key[5:])
            else:
                if library is None:
                    raise ValueError('Materialbibliothek nicht verfügbar.')
                item = next((i for i in library._items if i.get('id') == key), None)
                if item is None:
                    raise ValueError('Material nicht verfügbar: ' + (key or '(leer)'))
                label = str(item.get('label') or item.get('name') or label)
                if item.get('compatibility') == 'unsupported':
                    raise ValueError('Material ist für die Shader-Vorschau gesperrt.')
                target = library._compile_hover_item(item)
                # This must remain the isolated hover TOP, never a mistakenly
                # returned live output. No live-player operator is cooked here.
                if target is None or target.path != '/project1/madmapper_library/hover_preview':
                    raise ValueError('Materialbibliothek lieferte keine isolierte Vorschau.')
            target_path = self._capture(panel, target)
            status = 'ready'
            message = 'Vorschau (Standbild)'
        except Exception as exc:
            error = str(exc)
            thumbnail = self._thumbnail(library, item, descriptor)
            if thumbnail is not None:
                try:
                    image = self._node(panel, 'moviefileinTOP', 'thumbnail')
                    _set(image, file=str(thumbnail))
                    image.cook(force=True)
                    if image.errors():
                        raise ValueError(str(image.errors()))
                    target_path = self._capture(panel, image)
                    status = 'thumbnail'
                except Exception as thumbnail_error:
                    error += ' | Vorschaubild: ' + str(thumbnail_error)
            message = ('Gespeichertes Vorschaubild · ' if status == 'thumbnail' else 'Vorschau nicht verfügbar · ') + error
        if status == 'error':
            _set(panel.op('image'), opviewer='', display=False)
        _set(panel.op('title'), text=label)
        _set(panel.op('status'), text=message[:400])
        _set(panel.op('hint'), text='Rad drücken: laden' if status != 'error' else 'Weiterblättern, um ein anderes Material zu prüfen.')
        self.material_id = key
        self.state = dict(material_id=key, label=label, status=status, target=target_path, error=error)
        return PANEL
