"""Native searchable scan library. Disk work happens on explicit actions only."""
from collections import OrderedDict
from pathlib import Path
import re

from . import scan_library as library
from .scan_session import ScanSession, ScanSessionError
from .scan_workflow_ux import compact_indices, view_paths

OWNER = '/project1/guided_scan'
PAGE_SIZE = 8
_previews = OrderedDict()
_images = {}

BUTTON_COLORS = {
    'secondary': (.16, .22, .30), 'primary': (.07, .60, .50),
    'selected': (.10, .70, .90), 'replace': (.90, .58, .12),
    'disabled': (.09, .12, .16),
}


def _caption(button, foreground):
    """Use a click-through TextCOMP because ButtonCOMP couples label/skin color."""
    if not hasattr(button, 'create'):
        return  # Lightweight pure-test widgets have no native children.
    caption = button.op('scan_label')
    if caption is None:
        import td
        caption = button.create(td.textCOMP, 'scan_label')
    label = str(button.par.label) or button.fetch('scan_label_text', '')
    button.store('scan_label_text', label)
    button.par.label = ''
    values = {'text': label, 'x': 0, 'y': 0, 'hmode': 'fill', 'vmode': 'fill',
              'alignx': 'center', 'aligny': 'center', 'type': 'multiline', 'wordwrap': False,
              'font': 'Verdana', 'fontsize': 12, 'fontalpha': 1, 'bgalpha': 0,
              'opacity': 1, 'layer': 100, 'display': True, 'clickthrough': True,
              'fontcolorr': foreground[0], 'fontcolorg': foreground[1], 'fontcolorb': foreground[2]}
    for name, value in values.items():
        if getattr(caption.par, name, None) is not None:
            setattr(caption.par, name, value)


def style_button(button, role='secondary', *, enabled=True):
    """Native role-color skin plus independent high-contrast click-through label."""
    if button is None:
        return
    fill = BUTTON_COLORS[role if enabled else 'disabled']
    foreground = (.96, .98, 1) if enabled else (.65, .72, .78)
    values = {'alpha': 1, 'bgalpha': 1, 'fontalpha': 1, 'textalpha': 1, 'opacity': 1,
              'dodisablecolor': False, 'enable': enabled}
    for channel, color, text in zip('rgb', fill, foreground):
        values['color' + channel] = color
        values['bgcolor' + channel] = color
        values['fontcolor' + channel] = text
        values['textcolor' + channel] = text
    for name, value in values.items():
        if getattr(button.par, name, None) is not None:
            setattr(button.par, name, value)
    _caption(button, foreground)


def friendly_name(item):
    """Display a readable acquisition context while retaining a short stable ID."""
    parts = item['name'].replace('\\', '/').split('/')
    name = parts[-1]
    folder = parts[-2] if len(parts) > 1 else ''
    match = re.search(r'([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', folder, re.I)
    context = parts[-3] if match and len(parts) > 2 else ('' if match else folder)
    if match:
        name = ('View' if item['kind'] == '2D view' else '3D result') + ' ' + match.group(1)
    context = context.replace('_', ' ')
    name = name.replace('_', ' ')
    return (context + ' / ' if context else '') + name


def _field(owner, name):
    node = owner.op('library_panel/' + name + '/string')
    return node.text.strip() if node is not None else ''


def cached_preview(path):
    path = Path(path).resolve(strict=True)
    stamp = path.stat()
    key = (str(path), stamp.st_mtime_ns, stamp.st_size)
    if key not in _previews:
        _previews[key] = library.inspect_preview(path)
        while len(_previews) > 8:
            _previews.popitem(last=False)
    _previews.move_to_end(key)
    return _previews[key]


def render(owner):
    """Render cached index and selection; never inspect files or metadata."""
    index = owner.fetch('scan_library_index', {'items': []})
    items = library.filter_items(index, _field(owner, 'query'), owner.fetch('scan_library_kind', 'all'))
    page = max(0, min(owner.fetch('scan_library_page', 0), max(0, (len(items)-1)//PAGE_SIZE)))
    owner.store('scan_library_page', page)
    visible = items[page*PAGE_SIZE:(page+1)*PAGE_SIZE]
    owner.store('scan_library_visible', visible)
    selected = owner.fetch('scan_library_selected', [])
    for i in range(PAGE_SIZE):
        button = owner.op('library_panel/row_' + str(i))
        if button is None:
            continue
        button.par.display = i < len(visible)
        if i < len(visible):
            item = visible[i]
            name = friendly_name(item)
            label = ('[x] ' if item['path'] in selected else '[ ] ') + item['kind'] + ' | '
            button.par.label = label + (name if len(name) <= 66 else '...' + name[-63:])
            style_button(button, 'selected' if item['path'] in selected else 'secondary')
    known = {item['path']: item for item in index['items']}
    selected_items = [known[path] for path in selected if path in known]
    only_views = bool(selected_items) and len(selected_items) == len(selected) and all(item['kind'] == '2D view' for item in selected_items)
    one_result = len(selected) == len(selected_items) == 1 and selected_items[0]['kind'] == '3D scan'
    has_session = bool(owner.fetch('session', None))
    for name, ready, role in (
            ('attach', only_views and has_session, 'primary'),
            ('resume', only_views and len(selected_items) == 1, 'primary'),
            ('missing', only_views and has_session, 'secondary'),
            ('weak', only_views and has_session, 'secondary'),
            ('review', one_result, 'primary'), ('clear', bool(selected), 'secondary'),
            ('previous', page > 0, 'secondary'), ('next', (page+1)*PAGE_SIZE < len(items), 'secondary')):
        style_button(owner.op('library_panel/btn_' + name), role, enabled=ready)
    for name, kind in (('all', 'all'), ('views', '2D view'), ('results', '3D scan')):
        style_button(owner.op('library_panel/btn_' + name),
                     'selected' if owner.fetch('scan_library_kind', 'all') == kind else 'secondary')
    node = owner.op('library_panel/list_status')
    if node is not None:
        node.par.text = '%d found | Page %d/%d | %d selected%s' % (
            len(items), page+1, max(1, (len(items)+PAGE_SIZE-1)//PAGE_SIZE), len(selected),
            ' | LIMIT REACHED: choose a narrower folder' if index.get('truncated') else '')


def _status(owner, text):
    owner.op('library_panel/status').par.text = text


def _selected(owner, kind=None):
    selected = owner.fetch('scan_library_selected', [])
    known = {item['path']: item for item in owner.fetch('scan_library_index', {'items': []})['items']}
    if not selected or any(path not in known for path in selected):
        raise ScanSessionError('Select a file in the library first')
    if kind and any(known[path]['kind'] != kind for path in selected):
        raise ScanSessionError('This action requires only selected ' + kind + ' files')
    return selected


def stage_restored(owner, payload):
    """Replace only draft scan state after validating every destination widget."""
    state = ScanSession.from_dict(payload['session'])
    lookup = {target.led_id: target.source_index for target in state.targets}
    values = {'ui_panel/source_ids': compact_indices(lookup[i] for i in state.selected_ids),
              'ui_panel/anchors': compact_indices(lookup[i] for i in state.anchor_ids),
              'ui_panel/views': '', 'ui_panel/workspace': payload['workspace']}
    if payload.get('settings') is not None:
        values.update({'new_capture_panel/' + key: value for key, value in payload['settings'].items()})
        for key in ('frame_start_universe', 'frame_universe_count'):
            path = 'new_capture_panel/' + key
            if key not in payload['settings'] and owner.op(path + '/string') is not None:
                values[path] = ''
    if payload.get('camera'):
        camera = payload['camera']
        values.update({'ui_panel/camera': camera['device'], 'ui_panel/exposure': camera['exposure'],
                       'ui_panel/threshold': camera['threshold'], 'ui_panel/brightness': payload['brightness']})
    writes = []
    for path, value in values.items():
        node = owner.op(path + '/string')
        if node is None:
            raise ScanSessionError('Required scan field is missing: ' + path)
        writes.append((node, node.text, str(value)))
    try:
        for node, previous, value in writes:
            node.text = value
    except Exception:
        for node, previous, value in writes:
            node.text = previous
        raise
    owner.store('session', state.to_dict())
    owner.store('standalone_capture', payload.get('settings'))
    for key in ('capture_plan', 'capture_signature', 'manifest', 'manifest_view_paths',
                'candidate', 'merge_request', 'result_review'):
        owner.store(key, None)
    for key in ('capture_status', 'offline_status', 'coverage_summary'):
        owner.store(key, {})
    for name in ('worker_plan', 'dry_run'):
        node = owner.op(name)
        if node is not None:
            node.text = ''
    owner.store('workflow_page', 'capture')
    return state


def act(op, ui, command, argument=None):
    owner = op(OWNER)
    runtime = owner.op('runtime').module
    try:
        if command in ('open', 'refresh', 'folder'):
            if command == 'folder':
                folder = ui.chooseFolder(title='Scan library folder', start=_field(owner, 'folder'))
                if not folder:
                    return False
                owner.op('library_panel/folder/string').text = folder
            if command == 'open' and not _field(owner, 'folder'):
                workspace = owner.op('ui_panel/workspace/string').text.strip()
                owner.op('library_panel/folder/string').text = workspace or str(Path(__file__).resolve().parents[1] / 'Scans')
            # Reopening uses the cached index. Refresh is explicit and bounded.
            if command != 'open' or not owner.fetch('scan_library_index', None):
                index = library.library_index(_field(owner, 'folder'))
                owner.store('scan_library_index', index)
                owner.store('scan_library_selected', [])
                owner.store('scan_library_page', 0)
                _status(owner, '%d files indexed. Select rows to preview and choose an action.%s' % (
                    len(index['items']), (' %d unreadable files/folders.' % len(index['errors'])) if index['errors'] else ''))
            owner.op('library_panel').openViewer()
        elif command == 'search':
            owner.store('scan_library_page', 0)
        elif command == 'kind':
            owner.store('scan_library_kind', argument)
            owner.store('scan_library_page', 0)
        elif command == 'page':
            owner.store('scan_library_page', owner.fetch('scan_library_page', 0) + argument)
        elif command == 'clear':
            owner.store('scan_library_selected', [])
        elif command == 'row':
            visible = owner.fetch('scan_library_visible', [])
            if not 0 <= argument < len(visible):
                raise ScanSessionError('The selected row is no longer available; search again')
            item = visible[argument]
            preview = cached_preview(item['path'])
            owner.store('scan_library_preview', preview)
            owner.store('scan_library_angle', 30)
            chosen = list(owner.fetch('scan_library_selected', []))
            if item['path'] in chosen:
                chosen.remove(item['path'])
            else:
                chosen.append(item['path'])
            owner.store('scan_library_selected', chosen)
            from .scan_result_review import compact_ids
            owner.op('library_panel/details').par.text = '%s\n%s | %d measured LEDs%s | IDs %s\nSource: %s\nRaw measurement geometry; alignment and quality remain unverified.' % (
                friendly_name(item), preview['kind'], preview['count'], ' (display sample)' if preview['sampled'] else '',
                compact_ids(preview['ids']), item['name'])
            owner.op('library_preview').cook(force=True)
            _status(owner, 'Preview: %s. %d explicitly selected file(s).' % (item['name'], len(chosen)))
        elif command == 'rotate':
            owner.store('scan_library_angle', owner.fetch('scan_library_angle', 30) + argument)
            owner.op('library_preview').cook(force=True)
        elif command == 'attach':
            runtime._require_idle()
            from .build_scan_session_ui import offline_scope
            state = offline_scope(ScanSession.from_dict(owner.fetch('session')),
                                  owner.op('ui_panel/source_ids/string').text,
                                  owner.op('ui_panel/anchors/string').text)
            paths = library.verified_view_paths(_selected(owner, '2D view'), state)
            # Validate existing selection too; never silently merge foreign view IDs.
            current = view_paths(owner.op('ui_panel/views/string').text)
            combined = library.verified_view_paths(current + paths, state)
            runtime._set_views(combined)
            _status(owner, '%d identity-verified views selected for 3D. Prepare 3D next.' % len(combined))
            runtime._status('%d identity-verified library views selected. Prepare 3D next.' % len(combined))
        elif command == 'resume':
            runtime._require_idle()
            paths = _selected(owner, '2D view')
            if len(paths) != 1:
                raise ScanSessionError('Select exactly one original 2D view to resume its acquisition')
            payload = library.resume_acquisition(paths[0])
            state = stage_restored(owner, payload)
            runtime._set_views(paths)
            runtime._status('ORIGINAL ACQUISITION RESUMED | %d LEDs. Check camera and scan plan before another view.' % len(state.selected_ids))
            _status(owner, 'Original IDs restored. Select more matching views and Add selected views, or return to Capture.')
        elif command == 'review':
            paths = _selected(owner, '3D scan')
            if len(paths) != 1:
                raise ScanSessionError('Select exactly one 3D result for review')
            from .scan_result_review import open_review
            open_review(op, path=paths[0])
        elif command in ('missing', 'weak'):
            runtime._require_idle()
            paths = _selected(owner, '2D view')
            from .build_scan_session_ui import offline_scope
            scoped = offline_scope(ScanSession.from_dict(owner.fetch('session')),
                                   owner.op('ui_panel/source_ids/string').text,
                                   owner.op('ui_panel/anchors/string').text)
            state, coverage = library.coverage_selection(scoped, paths, command)
            payload = {'session': state.to_dict(), 'settings': owner.fetch('standalone_capture'),
                       'workspace': owner.op('ui_panel/workspace/string').text}
            stage_restored(owner, payload)
            runtime._status('NEW %s SCOPE | %d LEDs. Previous views remain on disk; new scope starts with an empty view list. Check scan plan.' %
                            (command.upper(), len(state.selected_ids)))
            _status(owner, '%d %s LEDs selected for a fresh capture scope. Previous files retained. Coverage is not 3D quality.' %
                    (len(state.selected_ids), command))
        elif command == 'back':
            owner.op('ui_panel').openViewer()
        elif command == 'help':
            ui.messageBox('Scan library help',
                'Search and click rows: checked rows determine every action; the last clicked file is previewed.\n\n'
                '2D: Add selected views verifies original LED identities. Resume original restores the saved acquisition IDs and settings; check the camera and plan again before capture.\n\n'
                'Missing = not seen in selected views. Weak = seen fewer than three times, including missing. These actions create a fresh sub-scope and clear its view list; existing files are retained.\n\n'
                '3D: Review requires candidate_3d.csv plus quality_pending.json. Other 3D CSVs can be previewed and imported through Layout.\n\n'
                'Folder discovery is bounded to two subfolder levels. Refresh explicitly after adding files. No Live output is started.', buttons=['Close'])
        else:
            raise ScanSessionError('Unknown library action')
        render(owner)
        from .scan_workflow_ux import refresh
        refresh(owner)
        return True
    except Exception as error:
        _status(owner, 'BLOCKED: ' + str(error))
        return False


def preview_image(preview, angle=30, width=610, height=265):
    """CPU point projection from cached data; no files, cameras or networking."""
    import numpy as np
    image = np.empty((height, width, 4), dtype=np.float32)
    image[:] = (.018, .032, .05, 1)
    image[::50, :, :3] = (.045, .065, .09)
    image[:, ::50, :3] = (.045, .065, .09)
    if not preview or not preview['points']:
        return image
    data = np.asarray(preview['points'], dtype=float)[:, 1:]
    if preview['kind'] == '2D view':
        x, y = data[:, 0], data[:, 1]
        colors = np.tile((.2, .85, 1), (len(data), 1))
        px, py = x*(width-40)+20, y*(height-40)+20
    else:
        data = data - (np.asarray(preview['bounds_min']) + np.asarray(preview['bounds_max'])) / 2
        a = np.deg2rad(angle)
        x = data[:, 0]*np.cos(a) + data[:, 2]*np.sin(a)
        depth = -data[:, 0]*np.sin(a) + data[:, 2]*np.cos(a)
        y = data[:, 1]*.92 + depth*.38
        span = max(float(np.ptp(x)), float(np.ptp(y)), 1e-9)
        factor = min(width-50, height-50)/span
        px, py = x*factor + width/2, y*factor + height/2
        shade = (depth-depth.min())/max(float(np.ptp(depth)), 1e-9)
        colors = np.column_stack((.25 + shade*.55, .65 + shade*.25, np.ones(len(data))*.95))
    px, py = np.clip(px.astype(int), 3, width-4), np.clip(py.astype(int), 3, height-4)
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        image[py+dy, px+dx, :3] = colors
    return image


def cook_preview(owner, script):
    preview = owner.fetch('scan_library_preview', None)
    angle = owner.fetch('scan_library_angle', 30)
    # ScriptTOP may cook repeatedly while visible; only project on explicit change.
    key = (id(preview), angle)
    cached = _images.get(owner.path)
    if cached is None or cached[0] != key:
        cached = (key, preview_image(preview, angle))
        _images[owner.path] = cached
    script.copyNumpyArray(cached[1])


def install(ns):
    """Install reusable native widgets and preview; no discovery or output starts."""
    import td
    scope = dict(ns, __name__='scan_library_helpers')
    path = Path(__file__).resolve().parent / 'build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    node, panel, text, field, button, click = (scope[k] for k in ('_node', '_panel', '_text', '_field', '_button', '_click'))
    owner = ns['op'](OWNER)
    p = panel(node(owner, ns.get('containerCOMP', td.containerCOMP), 'library_panel'), 0, 0, 1280, 860, 10)
    p.viewer = True
    text(p, 'title', 'SCAN LIBRARY | SAVED VIEWS + 3D RESULTS', 20, 800, 1240, 40, 22)
    for name, label, value, x, y, width in (
            ('folder', 'Folder (two levels deep; Refresh loads new files)', '', 20, 723, 1050),
            ('query', 'Search file / folder / 2D / 3D', '', 20, 640, 800)):
        existing = p.op(name + '/string')
        text(p, name + '_label', label, x, y+34, width, 28, 12)
        field(p, name, existing.text if existing is not None else value, x, y, width)
    expression = "__import__('pixelblaze_mapper.scan_library_ui',fromlist=['act']).act(op, ui, %r, %r)"
    controls = [('folder', 'CHOOSE FOLDER', 1090, 723, 170, 'folder', None),
                ('search', 'SEARCH', 840, 640, 200, 'search', None),
                ('refresh', 'REFRESH FILES', 1050, 640, 210, 'refresh', None),
                ('all', 'ALL', 20, 590, 110, 'kind', 'all'), ('views', '2D VIEWS', 140, 590, 145, 'kind', '2D view'),
                ('results', '3D RESULTS', 295, 590, 150, 'kind', '3D scan'),
                ('clear', 'CLEAR SELECTION', 455, 590, 170, 'clear', None),
                ('previous', 'PREVIOUS', 20, 173, 150, 'page', -1), ('next', 'NEXT', 180, 173, 150, 'page', 1),
                ('rotate_left', 'ORBIT -', 650, 173, 160, 'rotate', -25), ('rotate_right', 'ORBIT +', 820, 173, 160, 'rotate', 25),
                ('attach', 'ADD SELECTED VIEWS', 20, 115, 280, 'attach', None),
                ('resume', 'RESUME ORIGINAL', 310, 115, 250, 'resume', None),
                ('missing', 'NEW SCOPE: MISSING', 570, 115, 235, 'missing', None),
                ('weak', 'NEW SCOPE: WEAK', 815, 115, 215, 'weak', None),
                ('review', 'REVIEW 3D', 1040, 115, 220, 'review', None),
                ('back', 'BACK TO SCAN', 980, 12, 180, 'back', None), ('help', 'HELP', 1170, 12, 90, 'help', None)]
    for name, label, x, y, width, command, arg in controls:
        b = button(p, 'btn_' + name, label, x, y, width)
        style_button(b, 'primary' if name in ('search', 'attach', 'resume', 'review') else 'secondary')
        click(owner, 'click_library_' + name, b, expression % (command, arg))
    for i in range(PAGE_SIZE):
        b = button(p, 'row_' + str(i), '', 20, 534-i*43, 605)
        style_button(b)
        click(owner, 'click_library_row_' + str(i), b, expression % ('row', i))
    text(p, 'list_status', '', 20, 211, 605, 20, 11)
    text(p, 'details', 'Click a file to preview its measured LED points.\nChecked rows determine actions; previews never change the layout.', 650, 513, 610, 112, 12)
    callback = node(owner, ns.get('textDAT', td.textDAT), 'library_preview_callbacks')
    callback.text = "def onCook(scriptOp):\n    from pixelblaze_mapper.scan_library_ui import cook_preview\n    cook_preview(op('/project1/guided_scan'), scriptOp)\n"
    preview = node(owner, ns.get('scriptTOP', td.scriptTOP), 'library_preview')
    preview.par.callbacks = callback.path
    viewport = panel(node(p, ns.get('containerCOMP', td.containerCOMP), 'preview'), 650, 235, 610, 265, 20)
    viewport.par.top = preview.path
    text(p, 'preview_hint', '2D: image U/V. 3D: raw XYZ projection; Orbit changes the view only.', 650, 209, 610, 25, 11)
    text(p, 'status', 'Choose a folder, refresh, then select saved files. No camera or LED output.', 20, 12, 945, 90, 12)
    button_node = owner.op('ui_panel/btn_discover_views')
    if button_node is not None:
        button_node.par.label = 'OPEN SCAN LIBRARY'
        style_button(button_node, 'primary')
    render(owner)
    return {'panel': p.path, 'disk_scan_started': False, 'output_started': False}
