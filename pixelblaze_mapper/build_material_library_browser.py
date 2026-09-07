"""Build an isolated MadMapper material-library browser in TouchDesigner.

Run this file from a Text DAT in the open project.  Repeated execution updates
only ``/project1/madmapper_library`` and preserves its editable paths.  The
browser reads a local JSON catalog, offers search/facets/paging, and makes
preview/import available as explicit user actions.  It never connects to a
production source, enables Art-Net/DMX, accesses the network, or saves the TOE.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


OWNER = "/project1/madmapper_library"
LOCAL_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
DEFAULT_CATALOG = LOCAL_ROOT / "material_library" / "catalogs" / "madmapper-official-d7ff211.json"
DEFAULT_IMPORT_ROOT = LOCAL_ROOT / "material_library" / "imported"
DEFAULT_PAGE_SIZE = 8
CARD_COUNT = 32

if str(LOCAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_ROOT))


def _get_or_create(parent, op_type, name):
    node = op(parent.path + "/" + name)
    if node is not None:
        return node
    numbered = [
        child for child in parent.children
        if re.fullmatch(re.escape(name) + r"\d+", child.name)
    ]
    if numbered:
        node = numbered[0]
        node.name = name
        for duplicate in numbered[1:]:
            duplicate.destroy()
        return node
    node = parent.create(op_type, name)
    node.name = name
    return node


def _set_if_present(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _page(owner, name):
    return next(
        (page for page in owner.customPages if page.name == name), None
    ) or owner.appendCustomPage(name)


def _ensure_string(owner, page, name, label, default):
    parameter = owner.par[name]
    if parameter is None:
        parameter = page.appendStr(name, label=label)[0]
        parameter.default = str(default)
        parameter.val = str(default)
    return parameter


def _ensure_int(owner, page, name, label, default, minimum, maximum):
    parameter = owner.par[name]
    if parameter is None:
        parameter = page.appendInt(name, label=label)[0]
        parameter.default = int(default)
        parameter.val = int(default)
    parameter.min = minimum
    parameter.max = maximum
    parameter.normMin = minimum
    parameter.normMax = maximum
    parameter.clampMin = True
    parameter.clampMax = True
    return parameter


def _ensure_float(owner, page, name, label, default, minimum, maximum):
    parameter = owner.par[name]
    if parameter is None:
        parameter = page.appendFloat(name, label=label)[0]
        parameter.default = float(default)
        parameter.val = float(default)
    parameter.min = minimum
    parameter.max = maximum
    parameter.normMin = minimum
    parameter.normMax = maximum
    parameter.clampMin = True
    parameter.clampMax = True
    return parameter


def _ensure_menu(owner, page, name, label, names, labels, default):
    parameter = owner.par[name]
    if parameter is None:
        parameter = page.appendMenu(name, label=label)[0]
        parameter.menuNames = list(names)
        parameter.menuLabels = list(labels)
        parameter.default = default
        parameter.val = default
    return parameter


def _write_table(node, rows):
    node.clear()
    for row in rows:
        node.appendRow(row)


def _panel_style(node, x, y, width, height):
    for name, value in (
        ("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
        ("w", width), ("h", height), ("display", True),
    ):
        _set_if_present(node, name, value)


def _text(parent, name, value, x, y, width, height, size=13,
          color=(0.75, 0.84, 0.91), bg=(0.018, 0.027, 0.040), align="left"):
    node = _get_or_create(parent, textCOMP, name)
    _panel_style(node, x, y, width, height)
    for parameter, item in (
        ("text", value), ("type", "multiline"), ("wordwrap", True),
        ("fontsize", size), ("font", "Verdana"), ("bgalpha", 1),
        ("alignx", align), ("aligny", "center"), ("textpaddingl", 10),
        ("textpaddingr", 10), ("textpaddingt", 5), ("textpaddingb", 5),
        ("clickthrough", True), ("fontalpha", 1), ("layer", 30),
    ):
        _set_if_present(node, parameter, item)
    for suffix, item in zip("rgb", color):
        _set_if_present(node, "fontcolor" + suffix, item)
    for suffix, item in zip("rgb", bg):
        _set_if_present(node, "bgcolor" + suffix, item)
    return node


def _button(parent, name, label, x, y, width, height=40,
            color=(0.075, 0.19, 0.28)):
    node = _get_or_create(parent, buttonCOMP, name)
    _panel_style(node, x, y, width, height)
    for parameter, value in (
        ("buttontype", "momentary"), ("label", label), ("fontsize", 12),
        ("fontcolorr", 0.88), ("fontcolorg", 0.93), ("fontcolorb", 0.98),
        ("fontalpha", 1), ("bgalpha", 1), ("cursor", "pointer"), ("layer", 40),
    ):
        _set_if_present(node, parameter, value)
    for suffix, item in zip("rgb", color):
        _set_if_present(node, "bgcolor" + suffix, item)
    return node


def _field(parent, name, value, x, y, width, height=38):
    node = _get_or_create(parent, fieldCOMP, name)
    _panel_style(node, x, y, width, height)
    _set_if_present(node, "fieldtype", "string")
    _set_if_present(node, "bgalpha", 1)
    _set_if_present(node, "fontalpha", 1)
    _set_if_present(node, "layer", 40)
    string_dat = node.op("string")
    if string_dat is not None:
        current = str(string_dat[0, 0]) if string_dat.numRows and string_dat.numCols else ""
        if current.strip().casefold() in {"", "field"}:
            string_dat.text = str(value)
    return node


def _viewer(parent, name, target, x, y, width, height):
    node = _get_or_create(parent, opviewerCOMP, name)
    _panel_style(node, x, y, width, height)
    _set_if_present(node, "opviewer", target.path)
    _set_if_present(node, "allowpanel", False)
    _set_if_present(node, "layer", 20)
    return node


def _card_hit_area(parent, name, x, y, width, height):
    """Transparent panel that owns mouse hover and clicks for a whole card.

    OP Viewer COMPs are reliable image displays, but their rollover panel value
    is not updated consistently when the parent UI is opened directly in TD
    2025.  A regular Container COMP provides a stable interaction surface while
    leaving the viewer and label visible below it.
    """

    node = _get_or_create(parent, containerCOMP, name)
    _panel_style(node, x, y, width, height)
    for parameter, value in (
        ("bgalpha", 0.001), ("clickthrough", False), ("cursor", "pointer"),
        ("layer", 80),
    ):
        _set_if_present(node, parameter, value)
    return node


def _execute(parent, name, source, callback, panel_value="state"):
    existing = parent.op(name)
    if existing is not None and existing.type != "panelexec":
        existing.destroy()
    node = _get_or_create(parent, panelexecuteDAT, name)
    node.par.active = True
    node.par.fromop = source.path
    node.par.panels = source.path
    node.par.panelvalue = panel_value
    node.par.offtoon = True
    node.par.valuechange = False
    node.text = (
        "def onOffToOn(panelValue):\n"
        "    op(%r).module.%s\n"
        "    return\n"
    ) % (OWNER + "/runtime", callback)
    return node


def _button_chop_execute(parent, name, source, callback):
    """Legacy helper name: use the panel press, not a frame-sampled CHOP.

    Short presses can disappear from a momentary output CHOP between cooks.
    The direct panel selection is independent of that downstream sample.
    """
    return _execute(parent, name, source, callback, panel_value='lselect')


def _hover_execute(parent, name, source, slot):
    """Call the runtime when the pointer enters or leaves a material card."""

    existing = parent.op(name)
    if existing is not None and existing.type != "panelexec":
        existing.destroy()
    node = _get_or_create(parent, panelexecuteDAT, name)
    node.par.active = True
    node.par.fromop = source.path
    node.par.panels = source.path
    node.par.panelvalue = "rollover"
    node.par.offtoon = True
    node.par.ontooff = True
    node.par.valuechange = False
    node.text = (
        "def onOffToOn(panelValue):\n"
        "    op(%r).module.hover_slot(%d, True)\n"
        "    return\n\n"
        "def onOnToOff(panelValue):\n"
        "    op(%r).module.hover_slot(%d, False)\n"
        "    return\n"
    ) % (OWNER + "/runtime", slot, OWNER + "/runtime", slot)
    return node


def _runtime_source():
    """Return the self-contained runtime installed into the library COMP."""

    return r'''import json
import importlib
import re
from dataclasses import asdict, is_dataclass
from difflib import SequenceMatcher
from pathlib import Path

import pixelblaze_mapper.madmapper_parameters as _madmapper_parameters_module
import pixelblaze_mapper.madmapper_td_adapter as _madmapper_adapter_module
from pixelblaze_mapper.material_library_paging import clamped_page, page_count

OWNER = op('/project1/madmapper_library')
VIEW_HEADERS = ('slot', 'id', 'label', 'category', 'tags', 'compatibility', 'source_path', 'preview_path')
READY_COMPATIBILITY = {'native', 'touchdesigner', 'ready', 'compatible', 'adapted', 'glsl'}

_items = []
_filtered = []
_hover_context_cache = OWNER.fetch('material_hover_context_cache', {})
_parameter_context_cache = OWNER.fetch('material_parameter_context_cache', {})
OWNER.store('material_hover_context_cache', _hover_context_cache)
OWNER.store('material_parameter_context_cache', _parameter_context_cache)
_CATALOG_CACHE_KEY = 'material_library_catalog_cache_v1'
_RUNTIME_PAGE_KEY = 'material_browser_runtime_page'

from pixelblaze_mapper.imported_material_state import ImportedMaterialStateStore

_stored_parameter_store = (OWNER.fetch('madmapper_parameter_store', None)
                           if hasattr(OWNER, 'fetch') else None)
PARAMETER_STORE = (_stored_parameter_store
                   if isinstance(_stored_parameter_store, ImportedMaterialStateStore)
                   else ImportedMaterialStateStore())

def _parameter(name, default=''):
    par = getattr(OWNER.par, name, None)
    return str(par.eval()) if par is not None else str(default)

def _catalog_signature():
    stamps = []
    for value in (_parameter('Catalogfile'), _parameter('Importroot')):
        path = Path(value).expanduser().resolve()
        try:
            stat = path.stat()
            stamps.append((str(path), stat.st_mtime_ns, stat.st_size))
        except OSError:
            stamps.append((str(path), None, None))
    return (tuple(stamps), _parameter('Approvedroots'))

def _cache_catalog():
    OWNER.store(_CATALOG_CACHE_KEY, {'signature': _catalog_signature(), 'items': _items, 'filtered': _filtered})
    OWNER.store('material_labels_by_id', {item['id']: item['label'] for item in _items})

def _restore_catalog_cache():
    global _items, _filtered
    cached = OWNER.fetch(_CATALOG_CACHE_KEY, None)
    if not isinstance(cached, dict) or cached.get('signature') != _catalog_signature():
        return False
    _items, _filtered = cached['items'], cached['filtered']
    return True

def _restore_active_label():
    active = _state('active_id') or _state('live_preview_id')
    if not active:
        return
    label = OWNER.fetch('material_labels_by_id', {}).get(active)
    if label and (_state('active_label_id') != active or _state('active_label') != label):
        _set_state('active_label', label)
        _set_state('active_label_id', active)

def _field(name):
    node = OWNER.op('ui_panel/' + name + '/string')
    return str(node[0, 0]).strip() if node is not None and node.numRows else ''

def _set_text(name, value, color=None):
    node = OWNER.op('ui_panel/' + name)
    if node is None:
        return
    node.par.text = str(value)
    if color is not None:
        node.par.fontcolorr, node.par.fontcolorg, node.par.fontcolorb = color

def _set_button(name, value):
    node = OWNER.op('ui_panel/' + name)
    if node is not None:
        node.par.label = str(value)

def _state(name, default=''):
    if name == 'page':
        runtime_page = OWNER.fetch(_RUNTIME_PAGE_KEY, None)
        if runtime_page is not None:
            return str(runtime_page)
    table = OWNER.op('browser_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == name:
            return str(table[row, 1])
    return str(default)

def _set_state(name, value):
    if name == 'page':
        OWNER.store(_RUNTIME_PAGE_KEY, int(value))
    table = OWNER.op('browser_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == name:
            table[row, 1] = value
            return
    table.appendRow((name, value))

def _persist_parameter_store():
    OWNER.store('madmapper_parameter_store', PARAMETER_STORE)
    document = json.dumps(PARAMETER_STORE.to_dict(), sort_keys=True, separators=(',', ':'))
    table = OWNER.op('material_parameter_state')
    table.clear()
    table.appendRow(('key', 'json'))
    table.appendRow(('document', document))

def _restore_parameter_store():
    global PARAMETER_STORE
    if not hasattr(OWNER, 'op'):
        return
    table = OWNER.op('material_parameter_state')
    if table is None or table.numRows < 2:
        return
    try:
        document = json.loads(str(table[1, 1]))
        PARAMETER_STORE = ImportedMaterialStateStore.from_dict(document)
        OWNER.store('madmapper_parameter_store', PARAMETER_STORE)
    except Exception:
        pass

def _record_dict(record):
    if isinstance(record, dict):
        return dict(record)
    if is_dataclass(record):
        return asdict(record)
    if hasattr(record, 'to_dict'):
        return dict(record.to_dict())
    result = {}
    for name in ('id', 'name', 'label', 'relative_path', 'source_path', 'kind',
                 'groups', 'category', 'tags', 'compatibility',
                 'compatibility_reasons', 'compatibility_reason', 'metadata',
                 'preview_path', 'prepared_shader_path', 'touchdesigner_shader_path'):
        if hasattr(record, name):
            result[name] = getattr(record, name)
    return result

def _list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in re.split(r'[,;|]', value) if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(part).strip() for part in value if str(part).strip()]
    return [str(value).strip()]

def _compatibility(value):
    if hasattr(value, 'value'):
        value = value.value
    return str(value or 'unknown').strip().lower()

def _managed_import_status(material_id):
    """Resolve a persisted managed import without trusting catalogue paths."""
    if not re.fullmatch(r'mat_[0-9a-f]{20}', str(material_id or '')):
        return False, ''
    try:
        import_root = _validated_import_root(_parameter('Importroot'))
        package = (import_root / material_id).resolve(strict=True)
        if package.parent != import_root or not package.is_dir():
            return False, ''
        manifest = _validated_file(package / 'material-import.json', {'.json'})
        manifest_data = json.loads(manifest.read_text(encoding='utf-8'))
        if manifest_data.get('material_id') != material_id:
            return False, ''
        prepared = package / 'prepared.frag'
        if not prepared.is_file():
            return True, ''
        return True, str(_validated_file(prepared, {'.frag'}))
    except Exception:
        return False, ''

def _normalize(raw, catalog_path):
    item = _record_dict(raw)
    groups = _list(item.get('groups') or item.get('category'))
    tags = _list(item.get('tags'))
    reasons = _list(item.get('compatibility_reasons') or item.get('compatibility_reason'))
    source = str(item.get('source_path') or item.get('relative_path') or '').strip()
    if source and not Path(source).is_absolute():
        source = str((catalog_path.parent / source).resolve())
    preview = str(item.get('preview_path') or '').strip()
    if preview and not Path(preview).is_absolute():
        preview = str((catalog_path.parent / preview).resolve())
    material_id = str(item.get('id') or item.get('slug') or source).strip()
    label = str(item.get('name') or item.get('label') or Path(source).stem or material_id).strip()
    imported, managed_prepared = _managed_import_status(material_id)
    if imported:
        if 'imported' not in [value.lower() for value in groups]:
            groups.append('imported')
        if 'imported' not in [value.lower() for value in tags]:
            tags.append('imported')
    return {
        'id': material_id,
        'label': label,
        'source_path': source,
        'relative_path': str(item.get('relative_path') or ''),
        'kind': str(item.get('kind') or 'material'),
        'groups': groups,
        'category': groups[0] if groups else 'Other',
        'tags': tags,
        'compatibility': _compatibility(item.get('compatibility')),
        'compatibility_reason': '; '.join(reasons),
        'metadata': item.get('metadata') or {},
        'preview_path': preview,
        # A validated managed package is authoritative after restart.  This
        # avoids a stale catalogue alias shadowing its local prepared shader.
        'prepared_shader_path': str(managed_prepared or item.get('prepared_shader_path') or item.get('touchdesigner_shader_path') or ''),
        'imported': imported,
    }

def _load_direct(catalog_path):
    data = json.loads(catalog_path.read_text(encoding='utf-8'))
    if isinstance(data, list):
        return data
    for key in ('materials', 'items', 'entries'):
        if isinstance(data.get(key), list):
            return data[key]
    return []

def _load(catalog_path):
    try:
        from pixelblaze_mapper.material_library import load_catalog
        catalog = load_catalog(catalog_path)
        records = getattr(catalog, 'materials', getattr(catalog, 'items', catalog))
        return list(records)
    except Exception:
        return _load_direct(catalog_path)

def _approved_roots():
    roots = []
    for value in _parameter('Approvedroots').split(';'):
        value = value.strip()
        if value:
            try:
                roots.append(Path(value).expanduser().resolve())
            except Exception:
                pass
    try:
        roots.append(Path(_parameter('Catalogfile')).expanduser().resolve().parent)
    except Exception:
        pass
    return roots

def _validated_file(value, extensions=None):
    if not value:
        return None
    candidate = Path(value).expanduser().resolve(strict=True)
    if not candidate.is_file():
        raise ValueError('Not a file: ' + str(candidate))
    if not any(candidate == root or root in candidate.parents for root in _approved_roots()):
        raise ValueError('Path is outside Approved Roots: ' + str(candidate))
    if extensions and candidate.suffix.lower() not in extensions:
        raise ValueError('Unsupported file type: ' + candidate.suffix)
    return candidate

def _validated_import_root(value):
    candidate = Path(value).expanduser().resolve()
    if not any(candidate == root or root in candidate.parents for root in _approved_roots()):
        raise ValueError('Import Folder is outside Approved Roots: ' + str(candidate))
    return candidate

def _write_table(name, rows):
    table = OWNER.op(name)
    table.clear()
    for row in rows:
        table.appendRow(row)

def _categories():
    return ['All'] + sorted({group for item in _items for group in item['groups']}, key=str.lower)

def _compatibilities():
    return ['All'] + sorted({item['compatibility'] for item in _items}, key=str.lower)

def _layout_mode():
    return '8x4' if _state('layout', '4x2') == '8x4' else '4x2'

def _page_size():
    return 32 if _layout_mode() == '8x4' else 8

def _compatibility_label(value):
    labels = {
        'all': 'ALL',
        'adaptable': 'AUTO-PREPARE',
        'unsupported': 'MANUAL / BLOCKED',
    }
    return labels.get(str(value or 'unknown').lower(), str(value or 'unknown').upper())

def _group_label(value):
    labels = {
        'all': 'ALL', 'factory': 'FACTORY', 'demos': 'DEMOS / TEMPLATES',
        'online_library': 'ONLINE LIBRARY', 'audio_reactive': 'AUDIO REACTIVE',
        'color_generators': 'COLOR GENERATORS', 'fluid_organic': 'FLUID / ORGANIC',
        'image_filters': 'IMAGE FILTERS', 'lines_geometry': 'LINES / GEOMETRY',
        'noise_texture': 'NOISE / TEXTURE', 'particles': 'PARTICLES',
        'transitions': 'TRANSITIONS', 'utility_testing': 'UTILITY / TESTING',
    }
    return labels.get(str(value or 'Other').lower(), str(value or 'Other').replace('_', ' ').upper())

def _close_dropdowns():
    for name in ('group_dropdown', 'compat_dropdown'):
        node = OWNER.op('ui_panel/' + name)
        if node is not None:
            node.par.display = False

def toggle_dropdown(kind):
    names = {'group': 'group_dropdown', 'compat': 'compat_dropdown'}
    target_name = names.get(str(kind))
    if target_name is None:
        return
    target = OWNER.op('ui_panel/' + target_name)
    if target is None:
        return
    opening = not bool(target.par.display.eval())
    _close_dropdowns()
    target.par.display = opening

def toggle_layout():
    _set_state('layout', '8x4' if _layout_mode() == '4x2' else '4x2')
    _set_state('page', 0)
    _close_dropdowns()
    render()

def select_category(value):
    allowed = _categories()
    match = next((entry for entry in allowed if entry.lower() == str(value).lower()), 'All')
    _set_state('category', match)
    _close_dropdowns()
    apply_filters()

def select_compatibility(value):
    allowed = _compatibilities()
    match = next((entry for entry in allowed if entry.lower() == str(value).lower()), 'All')
    _set_state('compatibility', match)
    _close_dropdowns()
    apply_filters()

def _query_token_matches(token, searchable):
    if token in searchable:
        return True
    words = re.findall(r'[a-z0-9]+', searchable)
    return any(SequenceMatcher(None, token, word).ratio() >= 0.78 for word in words)

def refresh(reset_page=True):
    if reset_page:
        _parameter_context_cache.clear()
    global _items
    try:
        catalog_path = Path(_parameter('Catalogfile')).expanduser().resolve(strict=True)
        _items = [_normalize(item, catalog_path) for item in _load(catalog_path)]
        _items = [item for item in _items if item['id']]
        _items.sort(key=lambda item: (item['category'].lower(), item['label'].lower()))
        if reset_page:
            _set_state('page', 0)
        apply_filters(reset_page=False)
        _set_text('action_status', 'CATALOG READY - %d materials loaded' % len(_items), (0.35, 0.90, 0.67))
        return True
    except Exception as error:
        _items = []
        apply_filters(reset_page=False)
        _set_text('action_status', 'CATALOG BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False

def apply_filters(reset_page=True):
    global _filtered
    query = _field('search_field').lower()
    category = _state('category', 'All')
    compatibility = _state('compatibility', 'All')
    tokens = [part for part in query.split() if part]
    _filtered = []
    for item in _items:
        searchable = ' '.join((item['label'], item['id'], item['category'], item['kind'],
                               ' '.join(item['groups']), ' '.join(item['tags']),
                               item['compatibility'], item['compatibility_reason'])).lower()
        if tokens and not all(_query_token_matches(token, searchable) for token in tokens):
            continue
        if category.lower() != 'all' and category.lower() not in [group.lower() for group in item['groups']]:
            continue
        if compatibility.lower() != 'all' and item['compatibility'].lower() != compatibility.lower():
            continue
        _filtered.append(item)
    if reset_page:
        _set_state('page', 0)
    _set_state('search', query)
    _cache_catalog()
    render()

def change_page(delta):
    size = _page_size()
    page, _ = clamped_page(_state('page', 0), delta, len(_filtered), size)
    _set_state('page', page)
    render()

def _safe_preview_path(item):
    try:
        return _validated_file(item.get('preview_path'), {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.exr', '.webp'})
    except Exception:
        return None

def render():
    size = _page_size()
    count = page_count(len(_filtered), size)
    page, _ = clamped_page(_state('page', 0), 0, len(_filtered), size)
    _set_state('page', page)
    _set_state('page_count', count)
    _set_state('result_count', len(_filtered))
    _set_button('group_filter', 'GROUP: ' + _group_label(_state('category', 'All')))
    _set_button('compat_filter', 'COMPAT: ' + _compatibility_label(_state('compatibility', 'All')))
    _set_button('layout_toggle', 'VIEW: ' + _layout_mode().replace('x', ' x '))
    _set_text('page_status', 'PAGE %d / %d  |  %d RESULTS' % (page + 1, count, len(_filtered)))
    previous = OWNER.op('ui_panel/previous_page')
    next_button = OWNER.op('ui_panel/next_page')
    if previous is not None:
        previous.par.enable = page > 0
        previous.par.opacity = 1.0 if page > 0 else 0.35
    if next_button is not None:
        next_button.par.enable = page < count - 1
        next_button.par.opacity = 1.0 if page < count - 1 else 0.35
    start = page * size
    visible = _filtered[start:start + size]
    rows = [VIEW_HEADERS]
    compact = _layout_mode() == '8x4'
    for slot in range(32):
        button = OWNER.op('ui_panel/material_card_%d' % slot)
        viewer = OWNER.op('ui_panel/card_viewer_%d' % slot)
        hit = OWNER.op('ui_panel/material_hit_%d' % slot)
        fallback = OWNER.op('card_fallback_%d' % slot)
        image = OWNER.op('card_image_%d' % slot)
        if slot < len(visible):
            item = visible[slot]
            button.par.display = True
            viewer.par.display = True
            imported_badge = '  |  IMPORTED' if item.get('imported') else ''
            if compact:
                button.par.label = item['label'] + imported_badge
                column, row = slot % 8, slot // 8
                x, y, width, image_height, button_height = 26 + column * 117, 499 - row * 148, 112, 110, 34
                button.par.fontsize = 9
            else:
                button.par.label = '%s\n%s  |  %s%s' % (item['label'], item['category'], _compatibility_label(item['compatibility']), imported_badge)
                column, row = slot % 4, slot // 4
                x, y, width, image_height, button_height = 26 + column * 238, 436 - row * 276, 218, 168, 54
                button.par.fontsize = 12
            button.par.x, button.par.y, button.par.w, button.par.h = x, y, width, button_height
            viewer.par.x, viewer.par.y, viewer.par.w, viewer.par.h = x, y + button_height + 4, width, image_height
            if hit is not None:
                hit.par.display = True
                hit.par.x, hit.par.y, hit.par.w, hit.par.h = x, y, width, button_height + 4 + image_height
            button.store('material_id', item['id'])
            fallback.par.text = item['label'] + '\n\n' + '  '.join(item['tags'][:4])
            preview = _safe_preview_path(item)
            if preview is not None:
                # Reassigning the same path asks Movie File In TOP to reopen
                # the file on some TD builds.  Render may run for paging,
                # filters, or layout changes, so leave an unchanged image
                # alone to keep the card preview stable.
                if str(image.par.file.eval()) != str(preview):
                    image.par.file = str(preview)
                viewer.par.opviewer = image.path
                viewer.store('stored_preview', image.path)
            else:
                viewer.par.opviewer = fallback.path
                viewer.store('stored_preview', fallback.path)
            rows.append((slot, item['id'], item['label'], item['category'], ', '.join(item['tags']),
                         item['compatibility'], item['source_path'], item['preview_path']))
        else:
            button.par.display = False
            viewer.par.display = False
            if hit is not None:
                hit.par.display = False
            button.unstore('material_id')
    _write_table('catalog_view', rows)
    _sync_preview_activity()

def _selected():
    material_id = _state('selected_id')
    return next((item for item in _items if item['id'] == material_id), None)

def _item_for_slot(slot):
    index = int(_state('page', 0)) * _page_size() + int(slot)
    return _filtered[index] if 0 <= index < len(_filtered) else None

def _sync_preview_activity():
    # Lock only diagnostic TOPs. This suppresses their absTime-driven cooks
    # while retaining the last image; the production live_preview is excluded.
    hover = OWNER.op('hover_preview')
    detail = OWNER.op('detail_preview')
    viewer = OWNER.op('ui_panel/detail_viewer')
    target = str(viewer.par.opviewer.eval()) if viewer is not None else ''
    hover_active = False
    slot = str(_state('hover_slot'))
    if hover is not None and slot and _state('hover_material_id'):
        try:
            item = _item_for_slot(int(slot))
        except (TypeError, ValueError):
            item = None
        card = OWNER.op('ui_panel/card_viewer_' + slot)
        visible = card is not None and bool(card.par.display.eval())
        referenced = (target == hover.path or (card is not None and str(card.par.opviewer.eval()) == hover.path))
        hover_active = bool(visible and referenced and item and item['id'] == _state('hover_material_id'))
    detail_active = bool(detail is not None and target == detail.path and _state('selected_id')
                         and _state('detail_preview_id') == _state('selected_id'))
    for node, active in ((hover, hover_active), (detail, detail_active)):
        if node is not None and bool(node.lock) != (not active):
            node.lock = not active

def select_slot(slot):
    size = _page_size()
    index = int(_state('page', 0)) * size + int(slot)
    if not 0 <= index < len(_filtered):
        return
    item = _filtered[index]
    _set_state('selected_id', item['id'])
    _set_state('import_confirm_id', '')
    _set_button('import_selected', 'IMPORT SELECTED')
    metadata = item['metadata'] if isinstance(item['metadata'], dict) else {'value': item['metadata']}
    _write_table('selected_detail', (
        ('field', 'value'), ('id', item['id']), ('name', item['label']),
        ('group', ', '.join(item['groups'])), ('tags', ', '.join(item['tags'])),
        ('kind', item['kind']), ('compatibility', item['compatibility']),
        ('reason', item['compatibility_reason']), ('source', item['source_path']),
        ('metadata', json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
    ))
    _set_text('selection_title', item['label'])
    if item['compatibility'] == 'adaptable':
        explanation = ('AUTO-PREPARE: the converter can create a TouchDesigner wrapper. '
                       'The GPU compile is verified when OPEN LIVE PREVIEW is used.')
    elif item['compatibility'] == 'unsupported':
        explanation = ('MANUAL / BLOCKED: this material uses a feature that the automatic '
                       'converter cannot safely translate. Stored preview and source import remain available.')
    else:
        explanation = item['compatibility_reason'] or 'No compatibility warning.'
    reason = item['compatibility_reason']
    if reason and reason not in explanation:
        explanation += '\nReason: ' + reason
    _set_text('selection_meta', '%s\n%s\n\n%s\n\nTags: %s' % (
        item['category'], _compatibility_label(item['compatibility']), explanation,
        ', '.join(item['tags']) or '-'))
    _set_text('action_status', 'SELECTED - choose Preview, Import, or Open Live Preview')
    _sync_preview_activity()

def preview_selected():
    item = _selected()
    if item is None:
        _set_text('action_status', 'PREVIEW BLOCKED - select a material first', (0.98, 0.38, 0.32))
        return False
    preview = _safe_preview_path(item)
    viewer = OWNER.op('ui_panel/detail_viewer')
    if preview is not None:
        image = OWNER.op('preview_image')
        image.par.file = str(preview)
        viewer.par.opviewer = image.path
        _set_text('action_status', 'PREVIEW - local catalog image for ' + item['label'], (0.38, 0.76, 0.96))
    else:
        fallback = OWNER.op('preview_fallback')
        fallback.par.text = item['label'] + '\n\nNo stored image preview\nUse OPEN LIVE PREVIEW for TouchDesigner-ready GLSL.'
        viewer.par.opviewer = fallback.path
        _set_text('action_status', 'PREVIEW - metadata fallback; no image was supplied', (0.97, 0.72, 0.26))
    _sync_preview_activity()
    return True

def _result_path(result):
    if isinstance(result, (str, Path)):
        return str(result)
    for name in ('source_path', 'destination', 'path', 'imported_path', 'shader_path'):
        value = getattr(result, name, None)
        if value:
            return str(value)
    if is_dataclass(result):
        data = asdict(result)
        for name in ('source_path', 'destination', 'path', 'imported_path', 'shader_path'):
            if data.get(name):
                return str(data[name])
    return ''

def import_selected():
    item = _selected()
    if item is None:
        _set_text('action_status', 'IMPORT BLOCKED - select a material first', (0.98, 0.38, 0.32))
        return False
    if _state('import_confirm_id') != item['id']:
        _set_state('import_confirm_id', item['id'])
        _set_button('import_selected', 'CONFIRM IMPORT')
        _set_text('action_status', 'CONFIRM - click CONFIRM IMPORT to copy only this material', (0.97, 0.72, 0.26))
        return False
    try:
        catalog_path = Path(_parameter('Catalogfile')).expanduser().resolve(strict=True)
        import_root = _validated_import_root(_parameter('Importroot'))
        from pixelblaze_mapper.material_library import import_material, load_catalog
        from pixelblaze_mapper.madmapper_td_adapter import adapt_material, write_prepared_shader
        catalog = load_catalog(catalog_path)
        result = import_material(catalog, item['id'], import_root)
        destination = _result_path(result)
        adaptation = adapt_material(
            result.source_path,
            library_roots=(
                Path(catalog.source_root), Path(catalog.source_root).parent,
                result.directory, result.source_path.parent,
            ),
        )
        adaptation_status = adaptation.status
        if adaptation.adaptable:
            prepared = write_prepared_shader(adaptation, result.directory / 'prepared.frag')
            item['prepared_shader_path'] = str(prepared)
            destination = str(prepared)
            adaptation_status = 'prepared for TouchDesigner'
        elif adaptation.reasons:
            item['compatibility_reason'] = '; '.join(adaptation.reasons)
        table = OWNER.op('import_history')
        item['imported'] = True
        if 'imported' not in [value.lower() for value in item['groups']]:
            item['groups'].append('imported')
        if 'imported' not in [value.lower() for value in item['tags']]:
            item['tags'].append('imported')
        table.appendRow((item['id'], item['label'], destination, 'imported / ' + adaptation_status))
        _set_state('last_import_path', destination)
        _set_state('last_import_id', item['id'])
        _set_state('import_confirm_id', '')
        _cache_catalog()
        _set_button('import_selected', 'IMPORT SELECTED')
        unified = op('/project1/material_browser/unified_runtime')
        if unified is not None:
            unified.module.refresh()
        if adaptation.adaptable:
            message = 'IMPORTED + PREPARED - now use OPEN LIVE PREVIEW'
            color = (0.35, 0.90, 0.67)
        else:
            message = 'IMPORTED - adaptation unavailable: ' + (item['compatibility_reason'] or adaptation.status)
            color = (0.97, 0.72, 0.26)
        _set_text('action_status', message, color)
        return True
    except Exception as error:
        _set_state('import_confirm_id', '')
        _set_button('import_selected', 'IMPORT SELECTED')
        _set_text('action_status', 'IMPORT BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False

def _live_shader_candidate(item):
    last_import = _state('last_import_path') if _state('last_import_id') == item['id'] else ''
    candidates = [item.get('prepared_shader_path'), last_import, item.get('source_path')]
    for value in candidates:
        try:
            candidate = _validated_file(value, {'.frag', '.glsl', '.fs', '.txt'})
            if candidate is not None:
                return candidate
        except Exception:
            pass
    raise ValueError('No approved shader file exists for this material')

def _diagnostic_messages(value):
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return [str(entry) for entry in value if str(entry)]
    except TypeError:
        return [str(value)]

def _shader_for_hover(item):
    """Return a TouchDesigner GLSL shader without importing the material."""
    from pixelblaze_mapper.madmapper_td_adapter import prepared_shader_is_current
    try:
        candidate = _live_shader_candidate(item)
        source = candidate.read_text(encoding='utf-8')
        if ('TDOutputSwizzle' in source and 'vUV' in source
                and prepared_shader_is_current(source)):
            return source
    except Exception:
        pass
    source_path = _validated_file(item.get('source_path'), {'.fs'})
    from pixelblaze_mapper.madmapper_td_adapter import adapt_material, write_prepared_shader
    from pixelblaze_mapper.material_library import load_catalog
    catalog_path = Path(_parameter('Catalogfile')).expanduser().resolve(strict=True)
    catalog = load_catalog(catalog_path)
    source_root = Path(catalog.source_root).resolve()
    adaptation = adapt_material(
        source_path,
        library_roots=(source_root, source_root.parent,
                       source_path.parent, source_path.parent.parent),
    )
    if not adaptation.adaptable or not adaptation.shader:
        raise ValueError('; '.join(adaptation.reasons) or 'material is not adaptable')
    if item.get('imported'):
        import_root = _validated_import_root(_parameter('Importroot'))
        package = (import_root / item['id']).resolve(strict=True)
        if package.parent != import_root:
            raise ValueError('Managed material package is outside Import Folder')
        prepared = write_prepared_shader(adaptation, package / 'prepared.frag')
        item['prepared_shader_path'] = str(prepared)
    return adaptation.shader

def _adaptation_for_item(item, input_values=None):
    """Adapt the approved original source and retain its native INPUT schema."""
    source_path = _validated_file(item.get('source_path'), {'.fs'})
    import importlib
    import pixelblaze_mapper.madmapper_parameters as madmapper_parameters
    import pixelblaze_mapper.madmapper_td_adapter as madmapper_td_adapter
    importlib.reload(madmapper_parameters)
    importlib.reload(madmapper_td_adapter)
    from pixelblaze_mapper.material_library import load_catalog
    catalog_path = Path(_parameter('Catalogfile')).expanduser().resolve(strict=True)
    catalog = load_catalog(catalog_path)
    source_root = Path(catalog.source_root).resolve()
    return madmapper_td_adapter.adapt_material(
        source_path,
        library_roots=(source_root, source_root.parent,
                       source_path.parent, source_path.parent.parent),
        input_values=input_values,
    )

def _parameter_context(item):
    # Runtime uniforms must not re-read/re-adapt a complete shader on every drag.
    # Check dependency stamps; Refresh also clears this cache for source edits.
    source_path = _validated_file(item.get('source_path'), {'.fs'})
    cached = _parameter_context_cache.get(item['id'])
    def stamps(paths):
        return tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in paths)
    valid = cached is not None and cached['stamp'] == stamps(cached['paths'])
    if valid:
        initial = cached['initial']
    else:
        initial = _adaptation_for_item(item)
        from pixelblaze_mapper.material_library import load_catalog
        from pixelblaze_mapper.madmapper_td_adapter import _INCLUDE_RE, _resolve_include
        catalog_path = Path(_parameter('Catalogfile')).expanduser().resolve(strict=True)
        source_root = Path(load_catalog(catalog_path).source_root).resolve()
        roots = (source_root, source_root.parent, source_path.parent, source_path.parent.parent)
        paths = {source_path, catalog_path}
        def dependencies(path):
            for match in _INCLUDE_RE.finditer(path.read_text(encoding='utf-8-sig')):
                child = _resolve_include(match.group(1), path.parent, roots)
                if child is not None and child not in paths:
                    paths.add(child)
                    dependencies(child)
        dependencies(source_path)
        cached = {'initial': initial, 'paths': tuple(sorted(paths)), 'signature': None}
        cached['stamp'] = stamps(cached['paths'])
        _parameter_context_cache[item['id']] = cached
    values = PARAMETER_STORE.merge(item['id'], initial.schema)
    signature = json.dumps({p.name: values[p.name] for p in initial.schema if p.compile_time}, sort_keys=True)
    if cached['signature'] != signature:
        cached['adaptation'] = _adaptation_for_item(item, values)
        cached['signature'] = signature
    adaptation = cached['adaptation']
    if not adaptation.adaptable or not adaptation.shader:
        raise ValueError('; '.join(adaptation.reasons) or 'material is not adaptable')
    values = PARAMETER_STORE.merge(item['id'], adaptation.schema)
    return adaptation, values

def _active_item():
    material_id = _state('active_id') or _state('live_preview_id')
    return next((item for item in _items if item['id'] == material_id), None)

def _configure_parameter_uniforms(preview, adaptation, values, publish_schema=True):
    from pixelblaze_mapper.madmapper_parameters import uniform_vector
    preview.par.vec.sequence.numBlocks = 3 + len(adaptation.schema)
    rows = [('index', 'name', 'label', 'group', 'type', 'uniform', 'compile_time',
             'components', 'min', 'max', 'values', 'value')]
    for parameter in adaptation.schema:
        block = 3 + parameter.index
        getattr(preview.par, 'vec%dname' % block).val = (
            '' if parameter.compile_time else parameter.uniform)
        vector = uniform_vector(parameter, values[parameter.name])
        for suffix, component in zip('xyzw', vector):
            value_par = getattr(preview.par, 'vec%dvalue%s' % (block, suffix))
            value_par.expr = ''
            value_par.val = component
        rows.append((
            parameter.index, parameter.name, parameter.display_label,
            ' / '.join(parameter.groups), parameter.kind, parameter.uniform,
            int(parameter.compile_time), parameter.components,
            json.dumps(parameter.minimum), json.dumps(parameter.maximum),
            json.dumps(parameter.values), json.dumps(values[parameter.name]),
        ))
    if publish_schema:
        _write_table('material_parameter_schema', rows)
        _persist_parameter_store()

def parameter_snapshot():
    item = _active_item()
    if item is None:
        return {'material_id': '', 'parameters': [], 'page': 0, 'page_count': 1}
    adaptation, values = _parameter_context(item)
    page_count = max(1, (len(adaptation.schema) + 5) // 6)
    page = PARAMETER_STORE.page(item['id'], page_count)
    return {
        'material_id': item['id'], 'label': item['label'], 'page': page,
        'page_count': page_count,
        'parameters': [dict(parameter.to_dict(), value=values[parameter.name])
                       for parameter in adaptation.schema],
    }

def set_parameter_page(delta):
    snapshot = parameter_snapshot()
    if not snapshot['material_id']:
        return 0
    page = PARAMETER_STORE.set_page(
        snapshot['material_id'], snapshot['page'] + int(delta), snapshot['page_count'])
    _persist_parameter_store()
    return page

def _compile_errors(preview, info_name='live_preview_info'):
    errors = _diagnostic_messages(preview.errors())
    info = OWNER.op(info_name)
    info_text = str(info.text) if info is not None else ''
    compile_lines = [line.strip() for line in info_text.splitlines()
                     if 'error:' in line.lower() or 'failed' in line.lower()]
    return errors + compile_lines

def _activate_parameter_shader(item):
    adaptation, values = _parameter_context(item)
    # Compile in a detached candidate before replacing the published renderer.
    candidate = OWNER.op('detail_preview')
    previous_lock = bool(candidate.lock)
    candidate.lock = False
    try:
        OWNER.op('detail_shader').text = adaptation.shader
        _configure_parameter_uniforms(candidate, adaptation, values, publish_schema=False)
        candidate.cook(force=True)
        errors = _compile_errors(candidate, 'detail_preview_info')
    finally:
        candidate.lock = previous_lock
    if errors:
        raise ValueError('; '.join(errors)[:900])
    preview = OWNER.op('live_preview')
    previous_shader = str(OWNER.op('preview_shader').text)
    previous_uniforms = _renderer_uniforms(preview)
    try:
        OWNER.op('preview_shader').text = adaptation.shader
        _configure_parameter_uniforms(preview, adaptation, values)
        preview.cook(force=True)
        errors = _compile_errors(preview)
        if errors:
            raise ValueError('; '.join(errors)[:900])
    except Exception:
        OWNER.op('preview_shader').text = previous_shader
        _restore_renderer_uniforms(preview, previous_uniforms)
        preview.cook(force=True)
        raise
    # Compilation is not an export action: never rewrite managed source files
    # as a side effect of dragging a parameter or selecting a material.
    _persist_parameter_store()
    return True

def reset_material_parameters():
    global PARAMETER_STORE
    item = _active_item()
    if item is None:
        return False
    before = PARAMETER_STORE.to_dict()
    document = PARAMETER_STORE.to_dict()
    document.get('materials', {}).pop(item['id'], None)
    try:
        PARAMETER_STORE = ImportedMaterialStateStore.from_dict(document)
        result = _activate_parameter_shader(item)
        OWNER.store('madmapper_parameter_store', PARAMETER_STORE)
        return result
    except Exception:
        PARAMETER_STORE = ImportedMaterialStateStore.from_dict(before)
        _persist_parameter_store()
        raise

def _renderer_uniforms(preview):
    return (int(preview.par.vec.sequence.numBlocks),
            [(p.name, p.eval(), p.expr, str(p.mode)) for p in preview.pars('vec*')
             if p.name != 'vec'])

def _restore_renderer_uniforms(preview, snapshot):
    preview.par.vec.sequence.numBlocks = snapshot[0]
    for name, value, expression, mode in snapshot[1]:
        parameter = preview.par[name]
        if parameter is not None:
            parameter.expr = ''
            parameter.val = value
            if expression and 'EXPRESSION' in mode.upper():
                parameter.expr = expression

def set_material_parameter(name, component, value):
    global PARAMETER_STORE
    item = _active_item()
    if item is None:
        raise ValueError('select an imported material first')
    adaptation, values = _parameter_context(item)
    parameter = next((entry for entry in adaptation.schema if entry.name == str(name)), None)
    if parameter is None:
        raise KeyError(name)
    previous_document = PARAMETER_STORE.to_dict()
    previous_uniforms = _renderer_uniforms(OWNER.op('live_preview'))
    try:
        component = None if component is None or int(component) < 0 else int(component)
        updated = PARAMETER_STORE.set_value(item['id'], parameter, value, component=component)
        if updated == values[parameter.name]:
            return updated
        if parameter.compile_time:
            _activate_parameter_shader(item)
        else:
            current = PARAMETER_STORE.values(item['id'])
            _configure_parameter_uniforms(OWNER.op('live_preview'), adaptation, current)
            OWNER.op('live_preview').cook(force=True)
        _persist_parameter_store()
        return PARAMETER_STORE.values(item['id'])[parameter.name]
    except Exception:
        PARAMETER_STORE = ImportedMaterialStateStore.from_dict(previous_document)
        OWNER.store('madmapper_parameter_store', PARAMETER_STORE)
        _restore_renderer_uniforms(OWNER.op('live_preview'), previous_uniforms)
        _persist_parameter_store()
        raise

def pulse_material_parameter(name):
    set_material_parameter(name, -1, 1)
    run("op('/project1/madmapper_library/runtime').module.set_material_parameter(%r, -1, 0)" % str(name), delayFrames=1)
    return True

def _compile_hover_item(item):
    """Compile a fully bound hover shader while no viewer points at it.

    Adapter/schema work is cached per material and invalidated whenever its
    persisted native values change.  The single GLSL TOP still has to compile
    when a different material becomes active, but callers keep it detached
    until this function has completed successfully.
    """
    global _hover_context_cache
    material_id = str(item['id'])
    source_path = _validated_file(item.get('source_path'), {'.fs'})
    source_stat = source_path.stat()
    source_stamp = (str(source_path), int(source_stat.st_mtime_ns), int(source_stat.st_size))
    current_values = (PARAMETER_STORE.values(material_id)
                      if material_id in PARAMETER_STORE.material_ids else None)
    cached = _hover_context_cache.get(material_id)
    if (current_values is not None and cached is not None
            and cached[1] == current_values and cached[2] == source_stamp):
        adaptation, values = cached[0], dict(cached[1])
    else:
        adaptation, values = _parameter_context(item)
        if len(_hover_context_cache) >= 16 and material_id not in _hover_context_cache:
            _hover_context_cache.pop(next(iter(_hover_context_cache)))
        _hover_context_cache[material_id] = (adaptation, dict(values), source_stamp)
    source = adaptation.shader
    if 'void main' not in source:
        raise ValueError('Shader has no void main() entry point')
    # Hover is a diagnostic preview only.  Never write into ``preview_shader``
    # or cook ``live_preview`` here: that TOP is published through
    # ``imported_material_out`` and may currently drive the physical LEDs.
    preview = OWNER.op('hover_preview')
    shader = OWNER.op('hover_shader')
    compiled_id = str(OWNER.fetch('hover_compiled_id', ''))
    source_changed = compiled_id != material_id or str(shader.text) != source
    previous_lock = bool(preview.lock)
    preview.lock = False
    try:
        _configure_parameter_uniforms(preview, adaptation, values, publish_schema=False)
        if source_changed:
            shader.text = source
        preview.cook(force=True)
    finally:
        preview.lock = previous_lock
    errors = _diagnostic_messages(preview.errors())
    info = OWNER.op('hover_preview_info')
    info_text = str(info.text) if info is not None else ''
    compile_lines = [line.strip() for line in info_text.splitlines()
                     if 'error:' in line.lower() or 'failed' in line.lower()]
    if errors or compile_lines:
        OWNER.store('hover_compiled_id', '')
        raise ValueError('; '.join(errors + compile_lines)[:900] or 'TouchDesigner rejected the shader')
    OWNER.store('hover_compiled_id', material_id)
    return preview

def _restore_active_hover():
    """Restore both viewers before the shared hover TOP is recompiled."""
    active = str(_state('hover_slot'))
    if active:
        card = OWNER.op('ui_panel/card_viewer_%s' % active)
        if card is not None:
            stored = card.fetch('stored_preview', '')
            if stored and op(stored) is not None:
                card.par.opviewer = stored
    detail = OWNER.op('ui_panel/detail_viewer')
    restore = str(_state('hover_detail_restore'))
    if detail is not None:
        target = op(restore) if restore else None
        hover = OWNER.op('hover_preview')
        # Recover safely if a project was saved mid-hover or comes from the
        # older implementation which did not persist a restore target.
        if target is None and hover is not None and str(detail.par.opviewer.eval()) == hover.path:
            selected_id = str(_state('selected_id'))
            target = (OWNER.op('detail_preview')
                      if selected_id and _state('detail_preview_id') == selected_id
                      else OWNER.op('preview_fallback'))
        if target is not None:
            detail.par.opviewer = target.path
    _set_state('hover_slot', '')
    _set_state('hover_material_id', '')
    _set_state('hover_detail_restore', '')
    _sync_preview_activity()

def hover_slot(slot, entered):
    slot = int(slot)
    viewer = OWNER.op('ui_panel/card_viewer_%d' % slot)
    if viewer is None:
        return False
    if not entered:
        if _state('hover_slot') == str(slot):
            _restore_active_hover()
        _set_text('action_status', 'HOVER READY - stored/detail preview restored',
                   (0.35, 0.90, 0.67))
        return True
    item = _item_for_slot(slot)
    if item is None:
        return False
    if _state('hover_slot') == str(slot) and _state('hover_material_id') == item['id']:
        return True
    # Detach the shared TOP from every visible viewer before changing its
    # shader. This prevents checkerboard/recompile frames from leaking into
    # the UI while moving between cards.
    _restore_active_hover()
    detail = OWNER.op('ui_panel/detail_viewer')
    detail_restore = str(detail.par.opviewer.eval()) if detail is not None else ''
    try:
        preview = _compile_hover_item(item)
        # Compilation and native-uniform validation succeeded. Only now may
        # the new animation become visible.
        viewer.par.opviewer = preview.path
        if detail is not None:
            detail.par.opviewer = preview.path
        OWNER.store('hover_started_at', absTime.seconds)
        _set_state('hover_detail_restore', detail_restore)
        _set_state('hover_slot', slot)
        _set_state('hover_material_id', item['id'])
        _sync_preview_activity()
        _set_text('action_status', 'HOVER LIVE - %s | %.1f s loop' % (
            item['label'], float(OWNER.par.Hoverloopseconds.eval())), (0.38, 0.76, 0.96))
        return True
    except Exception as error:
        _set_text('action_status', 'HOVER STORED PREVIEW - %s | %s' % (
            item['label'], str(error)[:180]), (0.97, 0.72, 0.26))
        _sync_preview_activity()
        return False

def open_live_preview():
    item = _selected()
    if item is None:
        _set_text('action_status', 'LIVE PREVIEW BLOCKED - select a material first', (0.98, 0.38, 0.32))
        return False
    last_import = _state('last_import_path') if _state('last_import_id') == item['id'] else ''
    has_prepared = bool(item.get('prepared_shader_path')) or (
        bool(last_import) and Path(last_import).suffix.lower() in {'.frag', '.glsl'}
    )
    if item['compatibility'] not in READY_COMPATIBILITY and not has_prepared:
        reason = item['compatibility_reason'] or 'material is not marked TouchDesigner-ready'
        if item['compatibility'] == 'adaptable':
            reason = 'import and confirm this material first so its TouchDesigner wrapper can be created'
        _set_text('action_status', 'LIVE PREVIEW BLOCKED - ' + reason, (0.98, 0.38, 0.32))
        return False
    try:
        adaptation, values = _parameter_context(item)
        source = adaptation.shader
        if 'void main' not in source:
            raise ValueError('Shader has no void main() entry point')
        if 'TDOutputSwizzle' not in source or 'vUV' not in source:
            raise ValueError('Shader is imported but still needs TouchDesigner GLSL adaptation')
        OWNER.op('detail_shader').text = source
        preview = OWNER.op('detail_preview')
        preview.lock = False
        _configure_parameter_uniforms(preview, adaptation, values, publish_schema=False)
        preview.cook(force=True)
        errors = _diagnostic_messages(preview.errors())
        warnings = _diagnostic_messages(preview.warnings())
        info = OWNER.op('detail_preview_info')
        info_text = str(info.text) if info is not None else ''
        compile_lines = [line.strip() for line in info_text.splitlines()
                         if 'error:' in line.lower() or 'failed' in line.lower()]
        if errors or compile_lines:
            details = '; '.join(errors + compile_lines)
            details = details[:900] or 'TouchDesigner rejected the shader'
            item['compatibility'] = 'unsupported'
            item['compatibility_reason'] = 'Live GLSL compile failed: ' + details
            fallback = OWNER.op('compile_error_preview')
            fallback.par.text = ('LIVE PREVIEW COULD NOT COMPILE\n\n%s\n\n'
                                 'The stored preview and imported source are still available.' % details[:520])
            OWNER.op('ui_panel/detail_viewer').par.opviewer = fallback.path
            _set_text('selection_meta', '%s\n%s\n\n%s' % (
                item['category'], _compatibility_label(item['compatibility']), item['compatibility_reason']))
            _set_text('action_status', 'LIVE PREVIEW FAILED - material now marked MANUAL / BLOCKED', (0.98, 0.38, 0.32))
            render()
            return False
        viewer = OWNER.op('ui_panel/detail_viewer')
        viewer.par.opviewer = preview.path
        _set_state('detail_preview_id', item['id'])
        note = 'LIVE PREVIEW - compiled successfully; isolated local TOP'
        if warnings:
            note += ' (with warning)'
        _set_text('action_status', note + '; production source unchanged', (0.38, 0.76, 0.96))
        return True
    except Exception as error:
        _set_text('action_status', 'LIVE PREVIEW BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False
    finally:
        _sync_preview_activity()

def activate_selected():
    """The only catalog action allowed to publish a different import."""
    item = _selected()
    if item is None:
        return False
    try:
        _activate_parameter_shader(item)
        _set_state('active_id', item['id'])
        _set_state('live_preview_id', item['id'])
        _set_state('active_label', item['label'])
        _set_state('active_label_id', item['id'])
        return True
    except Exception as error:
        _set_text('action_status', 'APPLY BLOCKED - previous material retained: ' + str(error), (0.98, 0.38, 0.32))
        return False

# Recreating a DAT module must not re-read 638 packages or repaint 32 cards.
# Source/include stamps remain checked separately by _parameter_context.
if hasattr(OWNER, 'op'):
    if not isinstance(_stored_parameter_store, ImportedMaterialStateStore):
        _restore_parameter_store()
    if not _restore_catalog_cache():
        refresh(reset_page=False)
    _restore_active_label()
'''


FALLBACK_SHADER = r'''#version 430
out vec4 fragColor;
in vec3 vUV;
void main()
{
    vec2 uv = vUV.xy;
    float cell = mod(floor(uv.x * 12.0) + floor(uv.y * 12.0), 2.0);
    vec3 a = vec3(0.015, 0.035, 0.055);
    vec3 b = vec3(0.03, 0.18, 0.25);
    fragColor = TDOutputSwizzle(vec4(mix(a, b, cell), 1.0));
}
'''


def build():
    project = op("/project1")
    if project is None:
        raise RuntimeError("/project1 is missing")

    owner = _get_or_create(project, baseCOMP, "madmapper_library")
    owner.nodeX, owner.nodeY = 1180, -360
    page = _page(owner, "Material Library")
    _ensure_string(owner, page, "Catalogfile", "Catalog File", DEFAULT_CATALOG)
    _ensure_string(owner, page, "Importroot", "Import Folder", DEFAULT_IMPORT_ROOT)
    _ensure_string(owner, page, "Approvedroots", "Approved Roots", LOCAL_ROOT)
    _ensure_int(owner, page, "Pagesize", "Cards Per Page", DEFAULT_PAGE_SIZE, 1, CARD_COUNT)
    _ensure_menu(owner, page, "Coordinatemode", "Coordinate Mode",
                 ("global", "panel", "hybrid"),
                 ("Global Canvas", "Panel Local", "Hybrid"), "global")
    _ensure_int(owner, page, "Panelcolumns", "Panel Columns", 2, 1, 32)
    _ensure_int(owner, page, "Panelrows", "Panel Rows", 5, 1, 32)
    _ensure_float(owner, page, "Hybridmix", "Hybrid Mix", 0.5, 0.0, 1.0)
    _ensure_float(owner, page, "Hoverloopseconds", "Hover Loop Seconds", 6.0, 1.0, 15.0)

    state = _get_or_create(owner, tableDAT, "browser_state")
    if state.numRows < 2:
        _write_table(state, (
            ("key", "value"), ("page", 0), ("page_count", 1),
            ("result_count", 0), ("search", ""), ("category", "All"),
            ("compatibility", "All"), ("selected_id", ""),
            ("import_confirm_id", ""), ("last_import_path", ""),
            ("last_import_id", ""),
            ("live_preview_id", ""),
            ("hover_slot", ""), ("hover_material_id", ""),
            ("hover_detail_restore", ""),
            ("layout", "4x2"),
        ))
    existing_state = {str(state[row, 0]) for row in range(1, state.numRows)}
    for key, value in (("layout", "4x2"), ("hover_slot", ""),
                       ("hover_material_id", ""), ("hover_detail_restore", "")):
        if key not in existing_state:
            state.appendRow((key, value))
    catalog_view = _get_or_create(owner, tableDAT, "catalog_view")
    if catalog_view.numRows == 0:
        _write_table(catalog_view, (("slot", "id", "label", "category", "tags", "compatibility", "source_path", "preview_path"),))
    selected = _get_or_create(owner, tableDAT, "selected_detail")
    if selected.numRows == 0:
        _write_table(selected, (("field", "value"), ("status", "Select a material card")))
    history = _get_or_create(owner, tableDAT, "import_history")
    if history.numRows == 0:
        _write_table(history, (("id", "name", "destination", "status"),))
    parameter_state = _get_or_create(owner, tableDAT, "material_parameter_state")
    if parameter_state.numRows == 0:
        _write_table(parameter_state, (("key", "json"), ("document", '{"schema":1,"materials":{}}')))
    parameter_schema_table = _get_or_create(owner, tableDAT, "material_parameter_schema")
    if parameter_schema_table.numRows == 0:
        _write_table(parameter_schema_table, (("index", "name", "label", "group", "type", "uniform", "compile_time", "components", "min", "max", "values", "value"),))

    runtime = _get_or_create(owner, textDAT, "runtime")
    runtime.text = _runtime_source()

    preview_shader = _get_or_create(owner, textDAT, "preview_shader")
    if not str(preview_shader.text).strip():
        preview_shader.text = FALLBACK_SHADER
    live_preview = _get_or_create(owner, glslTOP, "live_preview")
    _set_if_present(live_preview, "glslversion", "glsl430")
    _set_if_present(live_preview, "mode", "vertexpixel")
    _set_if_present(live_preview, "pixeldat", preview_shader.path)
    _set_if_present(live_preview, "outputresolution", "custom")
    _set_if_present(live_preview, "resolutionw", 512)
    _set_if_present(live_preview, "resolutionh", 512)
    # Use the same Vector Constants path as the proven Core renderer.  The
    # first block carries continuous phase plus the generic material controls;
    # the second applies framing and the third retains coordinate metadata.
    # TD 2025 requires at least one Constant block. Keep the mandatory block
    # neutral instead of attempting the invalid numBlocks=0 assignment.
    live_preview.par.const.sequence.numBlocks = 1
    live_preview.par.const0name.val = ""
    live_preview.par.const0value.val = 0.0
    live_preview.par.vec.sequence.numBlocks = 3
    # Sequence parameters must be written through Par.val. Assigning through
    # ParCollection.__setattr__ aliases later blocks back to block zero in
    # TouchDesigner 2025 and silently overwrites the earlier uniform name.
    live_preview.par.vec0name.val = "uTDMaterial0"
    live_preview.par.vec0valuex.expr = (
        "op('/project1/material_state_runtime').module.phase() if "
        "op('/project1/material_state_runtime') is not None else "
        "absTime.seconds"
    )
    live_preview.par.vec0valuey.expr = "op('/project1/madmapper_player_controls').par.Scale"
    live_preview.par.vec0valuez.expr = "op('/project1/madmapper_player_controls').par.Width"
    live_preview.par.vec0valuew.expr = "op('/project1/madmapper_player_controls').par.Framezoom"
    live_preview.par.vec1name.val = "uTDMaterial1"
    live_preview.par.vec1valuex.expr = "op('/project1/madmapper_player_controls').par.Focusx"
    live_preview.par.vec1valuey.expr = "op('/project1/madmapper_player_controls').par.Focusy"
    live_preview.par.vec1valuez.val = 0.0
    live_preview.par.vec1valuew.val = 0.0
    live_preview.par.vec2name.val = "uTDCoordinate"
    live_preview.par.vec2valuex.expr = "parent().par.Coordinatemode.menuIndex"
    live_preview.par.vec2valuey.expr = "parent().par.Panelcolumns"
    live_preview.par.vec2valuez.expr = "parent().par.Panelrows"
    live_preview.par.vec2valuew.expr = "parent().par.Hybridmix"
    live_preview.nodeX, live_preview.nodeY = 420, 50

    # Publish the currently compiled imported material through the Base COMP
    # boundary.  It remains unconnected until the unified browser explicitly
    # appends it as visual-source index 3.
    imported_output = _get_or_create(owner, outTOP, "imported_material_out")
    live_preview.outputConnectors[0].connect(imported_output)
    imported_output.nodeX, imported_output.nodeY = 600, 160

    live_preview_info = _get_or_create(owner, infoDAT, "live_preview_info")
    _set_if_present(live_preview_info, "op", live_preview.path)
    live_preview_info.nodeX, live_preview_info.nodeY = 600, 50

    # A completely separate shader/TOP pair is used for card hover.  It is
    # intentionally not connected to imported_material_out, so moving the
    # pointer across cards can never replace the active imported material.
    hover_shader = _get_or_create(owner, textDAT, "hover_shader")
    if not str(hover_shader.text).strip():
        hover_shader.text = FALLBACK_SHADER
    hover_preview = _get_or_create(owner, glslTOP, "hover_preview")
    _set_if_present(hover_preview, "glslversion", "glsl430")
    _set_if_present(hover_preview, "mode", "vertexpixel")
    _set_if_present(hover_preview, "pixeldat", hover_shader.path)
    _set_if_present(hover_preview, "outputresolution", "custom")
    _set_if_present(hover_preview, "resolutionw", 512)
    _set_if_present(hover_preview, "resolutionh", 512)
    hover_preview.par.const.sequence.numBlocks = 1
    hover_preview.par.const0name.val = ""
    hover_preview.par.const0value.val = 0.0
    hover_preview.par.vec.sequence.numBlocks = 3
    hover_preview.par.vec0name.val = "uTDMaterial0"
    hover_preview.par.vec0valuex.expr = (
        "(absTime.seconds - parent().fetch('hover_started_at', absTime.seconds)) % "
        "max(1.0, parent().par.Hoverloopseconds)"
    )
    hover_preview.par.vec0valuey.expr = "op('/project1/madmapper_player_controls').par.Scale"
    hover_preview.par.vec0valuez.expr = "op('/project1/madmapper_player_controls').par.Width"
    hover_preview.par.vec0valuew.expr = "op('/project1/madmapper_player_controls').par.Framezoom"
    hover_preview.par.vec1name.val = "uTDMaterial1"
    hover_preview.par.vec1valuex.expr = "op('/project1/madmapper_player_controls').par.Focusx"
    hover_preview.par.vec1valuey.expr = "op('/project1/madmapper_player_controls').par.Focusy"
    hover_preview.par.vec1valuez.val = 0.0
    hover_preview.par.vec1valuew.val = 0.0
    hover_preview.par.vec2name.val = "uTDCoordinate"
    hover_preview.par.vec2valuex.expr = "parent().par.Coordinatemode.menuIndex"
    hover_preview.par.vec2valuey.expr = "parent().par.Panelcolumns"
    hover_preview.par.vec2valuez.expr = "parent().par.Panelrows"
    hover_preview.par.vec2valuew.expr = "parent().par.Hybridmix"
    hover_preview.nodeX, hover_preview.nodeY = 420, -200
    hover_preview_info = _get_or_create(owner, infoDAT, "hover_preview_info")
    _set_if_present(hover_preview_info, "op", hover_preview.path)
    hover_preview_info.nodeX, hover_preview_info.nodeY = 600, -200

    # Selected/detail preview has its own shader and uniforms, separate from
    # both transient hover and the production imported_material_out renderer.
    detail_shader = _get_or_create(owner, textDAT, "detail_shader")
    if not str(detail_shader.text).strip():
        detail_shader.text = FALLBACK_SHADER
    detail_preview = _get_or_create(owner, glslTOP, "detail_preview")
    for name in ('glslversion', 'mode', 'outputresolution', 'resolutionw', 'resolutionh'):
        _set_if_present(detail_preview, name, hover_preview.par[name].eval())
    detail_preview.par.pixeldat = detail_shader.path
    detail_preview.par.vec.sequence.numBlocks = max(3, int(detail_preview.par.vec.sequence.numBlocks))
    for block, uniform in enumerate(('uTDMaterial0', 'uTDMaterial1', 'uTDCoordinate')):
        detail_preview.par['vec%dname' % block].val = uniform
        for suffix in 'xyzw':
            template = hover_preview.par['vec%dvalue%s' % (block, suffix)]
            target = detail_preview.par['vec%dvalue%s' % (block, suffix)]
            target.val = template.eval()
            if template.expr:
                target.expr = template.expr
    detail_preview.par.vec0valuex.expr = 'absTime.seconds'
    detail_preview.nodeX, detail_preview.nodeY = 420, -340
    detail_info = _get_or_create(owner, infoDAT, 'detail_preview_info')
    detail_info.par.op = detail_preview.path

    compile_error_preview = _get_or_create(owner, textTOP, "compile_error_preview")
    _set_if_present(compile_error_preview, "text", "LIVE PREVIEW COULD NOT COMPILE")
    _set_if_present(compile_error_preview, "outputresolution", "custom")
    _set_if_present(compile_error_preview, "resolutionw", 512)
    _set_if_present(compile_error_preview, "resolutionh", 512)
    _set_if_present(compile_error_preview, "fontsize", 15)
    _set_if_present(compile_error_preview, "wordwrap", True)
    _set_if_present(compile_error_preview, "bgcolorr", 0.09)
    _set_if_present(compile_error_preview, "bgcolorg", 0.015)
    _set_if_present(compile_error_preview, "bgcolorb", 0.02)
    compile_error_preview.nodeX, compile_error_preview.nodeY = 600, -80

    preview_image = _get_or_create(owner, moviefileinTOP, "preview_image")
    preview_image.nodeX, preview_image.nodeY = 220, -80
    preview_fallback = _get_or_create(owner, textTOP, "preview_fallback")
    _set_if_present(preview_fallback, "text", "SELECT A MATERIAL\n\nPreview stays local\nOutputs stay off")
    _set_if_present(preview_fallback, "outputresolution", "custom")
    _set_if_present(preview_fallback, "resolutionw", 512)
    _set_if_present(preview_fallback, "resolutionh", 512)
    _set_if_present(preview_fallback, "fontsize", 18)
    preview_fallback.nodeX, preview_fallback.nodeY = 220, -200

    canvas = _get_or_create(owner, containerCOMP, "ui_panel")
    for name, value in (
        ("hmode", "fixed"), ("vmode", "fixed"), ("w", 1440), ("h", 900),
        ("bgcolorr", 0.008), ("bgcolorg", 0.014), ("bgcolorb", 0.023),
        ("bgalpha", 1),
    ):
        _set_if_present(canvas, name, value)

    _text(canvas, "title", "MADMAPPER MATERIAL LIBRARY", 26, 842, 1388, 44, 23, (0.91, 0.96, 1))
    _text(canvas, "subtitle", "Browse local materials safely - nothing is imported until you confirm it", 26, 804, 1388, 30, 13, (0.35, 0.90, 0.67))
    _text(canvas, "search_label", "SEARCH", 26, 753, 100, 38, 12)
    _field(canvas, "search_field", "", 126, 753, 390, 38)
    search = _button(canvas, "apply_search", "SEARCH / APPLY", 528, 753, 150, 38, (0.07, 0.34, 0.45))
    group = _button(canvas, "group_filter", "GROUP: ALL", 690, 753, 190, 38)
    compat = _button(canvas, "compat_filter", "COMPAT: ALL", 892, 753, 190, 38)
    refresh = _button(canvas, "refresh_catalog", "REFRESH CATALOG", 1094, 753, 180, 38)
    layout_toggle = _button(canvas, "layout_toggle", "VIEW: 4 x 2", 1286, 753, 128, 38, (0.12, 0.24, 0.34))

    _execute(owner, "apply_search_click", search, "apply_filters()")
    _execute(owner, "group_filter_click", group, "toggle_dropdown('group')")
    _execute(owner, "compat_filter_click", compat, "toggle_dropdown('compat')")
    _execute(owner, "refresh_catalog_click", refresh, "refresh()")
    _execute(owner, "layout_toggle_click", layout_toggle, "toggle_layout()")

    # Real direct-select menus replace the former click-to-cycle facets.  The
    # containers are overlays, so cards underneath stay unchanged.
    group_options = (
        ("All", "ALL"),
        ("factory", "FACTORY"),
        ("demos", "DEMOS / TEMPLATES"),
        ("online_library", "ONLINE LIBRARY"),
        ("audio_reactive", "AUDIO REACTIVE"),
        ("color_generators", "COLOR GENERATORS"),
        ("fluid_organic", "FLUID / ORGANIC"),
        ("image_filters", "IMAGE FILTERS"),
        ("lines_geometry", "LINES / GEOMETRY"),
        ("noise_texture", "NOISE / TEXTURE"),
        ("particles", "PARTICLES"),
        ("transitions", "TRANSITIONS"),
        ("utility_testing", "UTILITY / TESTING"),
        ("imported", "IMPORTED"),
    )
    group_height = len(group_options) * 30
    group_menu = _get_or_create(canvas, containerCOMP, "group_dropdown")
    _panel_style(group_menu, 690, 753 - group_height, 190, group_height)
    _set_if_present(group_menu, "bgcolorr", 0.018)
    _set_if_present(group_menu, "bgcolorg", 0.026)
    _set_if_present(group_menu, "bgcolorb", 0.038)
    _set_if_present(group_menu, "bgalpha", 1)
    _set_if_present(group_menu, "layer", 100)
    group_menu.par.display = False
    for index, (value, label) in enumerate(group_options):
        option = _button(group_menu, "group_option_%d" % index, label,
                         0, group_height - (index + 1) * 30, 190, 30,
                         (0.06, 0.10, 0.14))
        _execute(owner, "group_option_click_%d" % index, option,
                 "select_category(%r)" % value)

    compat_options = (
        ("All", "ALL"),
        ("adaptable", "AUTO-PREPARE"),
        ("unsupported", "MANUAL / BLOCKED"),
    )
    compat_height = len(compat_options) * 34
    compat_menu = _get_or_create(canvas, containerCOMP, "compat_dropdown")
    _panel_style(compat_menu, 892, 753 - compat_height, 190, compat_height)
    _set_if_present(compat_menu, "bgcolorr", 0.018)
    _set_if_present(compat_menu, "bgcolorg", 0.026)
    _set_if_present(compat_menu, "bgcolorb", 0.038)
    _set_if_present(compat_menu, "bgalpha", 1)
    _set_if_present(compat_menu, "layer", 100)
    compat_menu.par.display = False
    for index, (value, label) in enumerate(compat_options):
        option = _button(compat_menu, "compat_option_%d" % index, label,
                         0, compat_height - (index + 1) * 34, 190, 34,
                         (0.06, 0.10, 0.14))
        _execute(owner, "compat_option_click_%d" % index, option,
                 "select_compatibility(%r)" % value)

    for slot in range(CARD_COUNT):
        column, row = slot % 8, slot // 8
        x, y = 26 + column * 117, 499 - row * 148
        fallback = _get_or_create(owner, textTOP, "card_fallback_%d" % slot)
        _set_if_present(fallback, "text", "MATERIAL")
        _set_if_present(fallback, "outputresolution", "custom")
        _set_if_present(fallback, "resolutionw", 448)
        _set_if_present(fallback, "resolutionh", 300)
        _set_if_present(fallback, "fontsize", 28)
        fallback.nodeX, fallback.nodeY = -500 + slot * 90, -250
        image = _get_or_create(owner, moviefileinTOP, "card_image_%d" % slot)
        image.nodeX, image.nodeY = -500 + slot * 90, -380
        _viewer(canvas, "card_viewer_%d" % slot, fallback, x, y + 38, 112, 110)
        hit = _card_hit_area(canvas, "material_hit_%d" % slot, x, y, 112, 148)
        _hover_execute(owner, "material_card_hover_%d" % slot,
                       hit, slot)
        _execute(owner, "material_hit_click_%d" % slot, hit,
                 "select_slot(%d)" % slot, panel_value="lselect")
        button = _button(canvas, "material_card_%d" % slot, "MATERIAL", x, y, 112, 34)
        _execute(owner, "material_card_click_%d" % slot, button, "select_slot(%d)" % slot)

    _text(canvas, "detail_header", "SELECTED MATERIAL", 982, 695, 432, 40, 16, (0.91, 0.96, 1))
    _text(canvas, "selection_title", "No material selected", 982, 650, 432, 40, 16, (0.38, 0.76, 0.96))
    _viewer(canvas, "detail_viewer", preview_fallback, 982, 390, 432, 250)
    _text(canvas, "selection_meta", "Choose a card to see group, tags and compatibility.", 982, 194, 432, 184, 13)
    preview_button = _button(canvas, "preview_selected", "SHOW STORED PREVIEW", 982, 142, 210, 42, (0.07, 0.34, 0.45))
    live_button = _button(canvas, "open_live_preview", "OPEN LIVE PREVIEW", 1204, 142, 210, 42, (0.15, 0.23, 0.38))
    import_button = _button(canvas, "import_selected", "IMPORT SELECTED", 982, 90, 432, 42, (0.12, 0.38, 0.25))
    _execute(owner, "preview_selected_click", preview_button, "preview_selected()")
    _execute(owner, "open_live_preview_click", live_button, "open_live_preview()")
    _execute(owner, "import_selected_click", import_button, "import_selected()")

    previous = _button(canvas, "previous_page", "< PREVIOUS", 26, 24, 140, 40)
    next_button = _button(canvas, "next_page", "NEXT >", 820, 24, 140, 40)
    # The compact 8x4 layout places the final card hit areas nine pixels over
    # the navigation row.  Keep navigation above those layer-80 surfaces so a
    # click on the lower edge can never be intercepted by a material card.
    for navigation in (previous, next_button):
        _set_if_present(navigation, "layer", 120)
        _set_if_present(navigation, "clickthrough", False)
    _text(canvas, "page_status", "PAGE 1 / 1 | 0 RESULTS", 178, 24, 630, 40, 13, (0.72, 0.79, 0.86), align="center")
    _text(canvas, "action_status", "READY - set Catalog File and choose REFRESH CATALOG", 982, 24, 432, 54, 12, (0.35, 0.90, 0.67))
    _button_chop_execute(owner, "previous_page_click", previous, "change_page(-1)")
    _button_chop_execute(owner, "next_page_click", next_button, "change_page(1)")

    # Interactive browsing belongs on an OP Viewer Component in TD 2025.
    # The TOP remains a capture-only surface for screenshots and monitoring.
    browser_ui = _get_or_create(owner, opviewerCOMP, "browser_ui")
    _panel_style(browser_ui, 0, 0, 1280, 800)
    _set_if_present(browser_ui, "opviewer", canvas.path)
    browser_ui.viewer = True
    browser_ui.nodeX, browser_ui.nodeY = 650, 180

    ui_preview = _get_or_create(owner, opviewerTOP, "ui_preview")
    _set_if_present(ui_preview, "opviewer", canvas.path)
    _set_if_present(ui_preview, "allowpanel", False)
    _set_if_present(ui_preview, "outputresolution", "custom")
    _set_if_present(ui_preview, "resolutionw", 1280)
    _set_if_present(ui_preview, "resolutionh", 800)
    _set_if_present(ui_preview, "preservealpha", False)
    ui_preview.viewer = True
    ui_preview.nodeX, ui_preview.nodeY = 850, 50

    owner.store("material_library_contract", 1)
    owner.store("isolated", True)
    # Local-only refresh: a reopened project is immediately browsable while
    # keeping the user-selected search/facet state and all output isolation.
    runtime.module.refresh()
    print({
        "owner": owner.path,
        "catalog": str(owner.par.Catalogfile.eval()),
        "cards": CARD_COUNT,
        "outputsActive": False,
        "productionTouched": False,
        "projectSaved": False,
    })
    return owner


if "op" in globals():
    result = build()
