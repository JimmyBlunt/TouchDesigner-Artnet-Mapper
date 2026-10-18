"""Add the v1 help layer to existing native dialogs without rebuilding their data.

Inside TouchDesigner: ``from pixelblaze_mapper.build_release_ui import install;
install()``. The complete rollback snapshot lives in operator storage and is
saved with the project. Call ``restore()`` to remove only this presentation layer.
"""
from __future__ import annotations

import json
from pathlib import Path
import webbrowser
from .release_ui_theme import THEME, remember_set, style_node, restore_node, select_theme

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'docs/release-v1.0.0/help_catalog.json'
PREFIX = 'release_v1_'
BAR_HEIGHT = 40


def load_catalog(path=CATALOG):
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    screens = document['screens']
    keys = [screen['key'] for screen in screens]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate release help screen key')
    return screens


def _set(node, **values):
    for name, value in values.items():
        par = getattr(node.par, name, None)
        if par is not None:
            par.val = value
    return node


def _color(node, prefix, color):
    return _set(node, **{prefix + c: v for c, v in zip('rgb', color)})


def _get(parent, kind, name):
    import td
    node = parent.op(name)
    if node is None:
        node = parent.create(getattr(td, kind), name)
        node.name = name
    return node


def _label(parent, name, text, x, y, width, height, *, size=12, background=False):
    node = _get(parent, 'textCOMP', name)
    _set(node, text=text, x=x, y=y, w=width, h=height, hmode='fixed', vmode='fixed',
         font=THEME['font'], fontfile=THEME.get('fontfile',''), fontsize=size, fontalpha=1, bgalpha=int(background),
         alignx='left', aligny='center', textpaddingl=12, textpaddingr=12,
         type='multiline', wordwrap=True, clickthrough=True, layer=800, display=True)
    _color(node, 'fontcolor', THEME['ink']); _color(node, 'bgcolor', THEME['surface'])
    return node


def _button(parent, name, label, x, y, width):
    node = _get(parent, 'buttonCOMP', name)
    _set(node, label='', x=x, y=y, w=width, h=28, hmode='fixed', vmode='fixed',
         buttontype='momentary', value0=False, fontsize=12, layer=810, display=True)
    _color(node, 'color', THEME['border'])
    caption=_label(node, PREFIX+'caption', label, 0, 0, width, 28, background=True)
    _color(caption,'fontcolor',THEME['button'])
    return node


def _callback(parent, name, source, *, click=None, enter=None, leave=None):
    node = _get(parent, 'panelexecuteDAT', name)
    _set(node, active=False, fromop=source.path, panels=source.path,
         panelvalue='lselect' if click else 'rollover', offtoon=True,
         ontooff=not bool(click), whileon=False, whileoff=False, valuechange=False)
    preamble = ('import sys\nimport td\nfrom pathlib import Path\n'
                'project_root = str(Path(td.project.folder))\n'
                'if project_root not in sys.path: sys.path.insert(0, project_root)\n'
                'from pixelblaze_mapper import build_release_ui as help_ui\n')
    body = preamble + 'def onOffToOn(panelValue):\n    ' + (click or enter) + '\n'
    if leave:
        body += 'def onOnToOff(panelValue):\n    ' + leave + '\n'
    node.text = body
    _set(node, active=True)
    return node


def _walk(panel):
    for child in list(panel.children):
        if child.name.startswith(PREFIX):
            continue
        yield child
        if getattr(child, 'isCOMP', False):
            yield from _walk(child)


def _summary(screen):
    lines = [screen['title'], screen.get('summary', '')]
    lines += [str(i+1) + '. ' + str(step) for i, step in enumerate(screen.get('steps', [])[:6])]
    return '\n'.join(lines)


def _resolve(path):
    import td
    return td.op(path)


def show_tip(panel_path, text='', visible=True, pinned=False):
    panel = _resolve(panel_path)
    if panel is None:
        return
    node = panel.op(PREFIX+'tooltip')
    if node is None:
        return
    if not pinned and panel.fetch(PREFIX+'pinned', False,search=False):
        return
    if pinned:
        state = not panel.fetch(PREFIX+'pinned', False,search=False)
        panel.store(PREFIX+'pinned', state)
        visible = state
    _set(node, display=visible)
    if text:
        _set(node, text=text)


def open_howto(key):
    screen = next(s for s in load_catalog() if s['key'] == key)
    path = (CATALOG.parent / screen['howto']).resolve()
    if not path.is_relative_to(CATALOG.parent.resolve()) or not path.is_file():
        raise ValueError('Help document missing or outside release documentation: ' + str(path))
    return webbrowser.open(path.as_uri(), new=2)


def install_screen(panel, screen):
    # ButtonCOMP's stock initialization may append a numeric suffix. Earlier
    # installs left duplicate visible skins over the callback-bound button.
    import re
    for child in list(panel.children):
        if re.fullmatch(r'release_v1_(info|howto)\d+', child.name):
            child.destroy()
    embedded=bool(screen.get('embedded'))
    base_height = int(panel.par.h) if embedded else panel.fetch(PREFIX+'base_height', None,search=False)
    if base_height is None:
        base_height = int(panel.par.h.eval())
        panel.store(PREFIX+'base_height', base_height)
    width = int(panel.par.w.eval())
    if not embedded:remember_set(panel, 'h', base_height + BAR_HEIGHT)
    remember_set(panel, 'bgalpha', 1)
    style_node(panel)
    for node in _walk(panel):
        style_node(node)
    bar=_label(panel, PREFIX+'bar', screen['title']+'  /  v1.0', 0, base_height,
           width, BAR_HEIGHT, background=True)
    info = _button(panel, PREFIX+'info', 'i  Info', width-(420 if embedded else 190), base_height+6, 72)
    howto = _button(panel, PREFIX+'howto', 'How-to  >', width-(338 if embedded else 110), base_height+6, 98)
    if embedded:
        _set(bar,display=False)
        info.par.y.expr='parent().par.h - 46';howto.par.y.expr='parent().par.h - 46'
        title=panel.op('native_parameter_title')
        if title is not None:remember_set(title,'w',790)
    tooltip = _label(panel, PREFIX+'tooltip', '', max(8,width-640), max(8,base_height-250),
                     min(620,width-16), 240, size=13, background=True)
    _set(tooltip, display=False, layer=999)
    if embedded:
        tooltip.par.y=10;tooltip.par.h.expr='min(240, parent().par.h - 60)'
    summary = _summary(screen)
    _callback(panel, PREFIX+'info_click', info,
              click='help_ui.show_tip(%r, %r, pinned=True)' % (panel.path, summary))
    _callback(panel, PREFIX+'info_hover', info,
              enter='help_ui.show_tip(%r, %r)' % (panel.path, summary),
              leave='help_ui.show_tip(%r, visible=False)' % panel.path)
    _callback(panel, PREFIX+'howto_click', howto,
              click='help_ui.open_howto(%r)' % screen['key'])
    fields_found, fields_missing = [], []
    for index, (name, field) in enumerate(screen.get('fields', {}).items()):
        node = panel.op(name)
        if node is None:
            fields_missing.append(name)
            continue
        message = field['description'] + '\n\nBeispiel: ' + str(field.get('example', ''))
        _callback(panel, PREFIX+'field_'+str(index), node,
                  enter='help_ui.show_tip(%r, %r)' % (panel.path, message),
                  leave='help_ui.show_tip(%r, visible=False)' % panel.path)
        fields_found.append(name)
    from . import release_ui_layout
    layout = release_ui_layout.apply(panel, screen)
    if screen['key']=='show':
        from .release_show_table import install as install_show_table
        layout['show_cells']=install_show_table(panel)
    panel.store(PREFIX+'screen', screen['key'])
    panel.store(PREFIX+'theme_version',1)
    return {'key': screen['key'], 'target': panel.path, 'fields': fields_found,
            'missing_fields': fields_missing, 'height': int(panel.par.h),'layout':layout}


def _update_previews(panel, resolver):
    """A fixed-resolution OP Viewer otherwise clips the newly added help bar."""
    owners = [panel.parent()]
    try:
        owners.append(panel.parent().parent())
    except Exception:
        pass
    updated = []
    seen = set()
    for owner in owners:
        for node in owner.children:
            if node.path in seen:
                continue
            seen.add(node.path)
            source = getattr(node.par, 'opviewer', None)
            height = getattr(node.par, 'resolutionh', None)
            if source is None or height is None:
                continue
            selected = source.eval()
            if getattr(selected, 'path', str(selected)) == panel.path:
                remember_set(node, 'resolutionh', int(panel.par.h.eval()))
                updated.append(node.path)
    return updated


def install(resolver=None, catalog_path=CATALOG, theme='03'):
    select_theme(theme)
    resolver = resolver or _resolve
    report = {'installed': [], 'missing': [], 'web': []}
    for screen in load_catalog(catalog_path):
        target = screen.get('target', '')
        if not target or screen.get('native') is False:
            report['web'].append(screen['key']); continue
        panel = resolver(target)
        if panel is None:
            report['missing'].append(target); continue
        result = install_screen(panel, screen)
        result['previews_resized'] = _update_previews(panel, resolver)
        report['installed'].append(result)
    root = resolver('/project1')
    if root is not None:
        root.store('release_v1_theme', str(theme).zfill(2))
        install_maintenance(root)
    return report


_last_maintenance=0.0


def maintenance_tick():
    """Two-second presence audit only; rebuild the layer solely when missing."""
    import time
    global _last_maintenance
    now=time.monotonic()
    if now-_last_maintenance<2:return
    _last_maintenance=now
    root=_resolve('/project1')
    select_theme(root.fetch('release_v1_theme','03',search=False))
    for screen in load_catalog():
        if not screen.get('target'):continue
        panel=_resolve(screen['target'])
        if panel is None:continue
        missing=panel.op(PREFIX+'info') is None or panel.op(PREFIX+'info_click') is None
        if not missing:
            # TextDAT callbacks also report type='text', but have no UI style.
            # Including them makes every panel reinstall on every audit.
            missing=any(node.isCOMP and node.type in ('button','field','text') and not node.name.startswith(PREFIX)
                        and node.fetch('release_v1_original_style',None,search=False) is None for node in panel.children)
        if missing:install_screen(panel,screen)


def install_maintenance(root):
    dat=_get(root,'executeDAT','release_ui_maintenance')
    dat.text=('import sys, td\nfrom pathlib import Path\n'
              'folder=str(Path(td.project.folder))\n'
              'if folder not in sys.path: sys.path.insert(0,folder)\n'
              'def onFrameStart(frame):\n'
              '    try:\n'
              '        from pixelblaze_mapper.build_release_ui import maintenance_tick\n'
              '        maintenance_tick()\n'
              '    except Exception as error:\n'
              '        me.store("release_help_error",str(error))\n')
    _set(dat,active=True,framestart=True,frameend=False)
    return dat


def restore(resolver=None, catalog_path=CATALOG):
    resolver = resolver or _resolve
    maintenance=resolver('/project1/release_ui_maintenance')
    if maintenance is not None:_set(maintenance,active=False)
    restored = []
    for screen in load_catalog(catalog_path):
        if not screen.get('target') or screen.get('native') is False:
            continue
        panel = resolver(screen['target'])
        if panel is None:
            continue
        for node in _walk(panel):
            restore_node(node)
            if getattr(node,'isCOMP',False):
                for child in list(node.children):
                    if child.name.startswith(PREFIX):child.destroy()
        restore_node(panel)
        for owner in (panel.parent(), panel.parent().parent()):
            for node in owner.children:
                if getattr(node.par, 'opviewer', None) is not None:
                    restore_node(node)
        for child in list(panel.children):
            if child.name.startswith(PREFIX):
                child.destroy()
        panel.store(PREFIX+'pinned', False)
        restored.append(panel.path)
    return restored
