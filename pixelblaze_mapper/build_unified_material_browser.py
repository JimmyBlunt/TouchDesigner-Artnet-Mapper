"""Build the combined Core + imported MadMapper material browser.

The existing core players and their first three visual-source indices remain
unchanged.  A fourth source is appended for a successfully prepared imported
material.  The browser itself is additive and never enables a DMX output or
saves the project.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = "/project1"
OWNER = ROOT + "/material_browser"
PROJECT_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
MANIFEST = PROJECT_ROOT / "effects" / "effects_manifest.json"
CATALOG = PROJECT_ROOT / "material_library" / "catalogs" / "madmapper-official-d7ff211.json"
IMPORT_ROOT = PROJECT_ROOT / "material_library" / "imported"
SLOT_COUNT = 32
GROUP_OPTION_COUNT = 20

# Exact public names created by this builder. TouchDesigner suffixes a name
# when an older builder left a same-name sibling behind; these prefixes let us
# remove only such generated duplicates without touching material sources.
GENERATED_SINGLETON_PREFIXES = (
    "mb_control_speed", "mb_control_focusx", "mb_control_focusy",
    "mb_control_zoom", "mb_control_view_reset",
    "unified_apply", "unified_source", "unified_group", "unified_layout",
    "unified_previous", "unified_next",
)


def _get_or_create(parent, op_type, name):
    node = parent.op(name)
    if node is not None:
        return node
    node = parent.create(op_type, name)
    node.name = name
    return node


def _is_generated_duplicate_name(name):
    suffix = r"(?:\d+(?:_change|_click)?|(?:_change|_click)\d+)"
    return re.match(
        r"^(?:%s)%s$" % (
            "|".join(re.escape(value) for value in GENERATED_SINGLETON_PREFIXES),
            suffix,
        ),
        str(name),
    ) is not None


def _remove_generated_duplicates(parent):
    """Remove numeric-suffixed duplicate controls from older builder runs.

    Only generated singleton families are considered. The canonical unsuffixed
    OP, material cards, preview sources, and imported material state survive.
    """
    for child in tuple(parent.children):
        if _is_generated_duplicate_name(child.name):
            child.destroy()


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _panel(node, x, y, width, height, layer=20):
    for name, value in (
        ("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
        ("w", width), ("h", height), ("display", True), ("layer", layer),
    ):
        _set(node, name, value)
    return node


def _text(parent, name, value, x, y, width, height, size=13, color=(0.78, 0.85, 0.92)):
    node = _panel(_get_or_create(parent, textCOMP, name), x, y, width, height, 30)
    for par, item in (
        ("text", value), ("type", "multiline"), ("wordwrap", True),
        ("fontsize", size), ("font", "Verdana"), ("bgalpha", 1),
        ("fontalpha", 1),
        ("bgcolorr", 0.018), ("bgcolorg", 0.027), ("bgcolorb", 0.040),
        ("fontcolorr", color[0]), ("fontcolorg", color[1]), ("fontcolorb", color[2]),
        ("aligny", "center"), ("textpaddingl", 8), ("clickthrough", True),
    ):
        _set(node, par, item)
    return node


def _button(parent, name, label, x, y, width, height=38, color=(0.07, 0.18, 0.26)):
    node = _panel(_get_or_create(parent, buttonCOMP, name), x, y, width, height, 50)
    for par, item in (
        ("buttontype", "momentary"), ("label", label), ("fontsize", 11),
        ("fontcolorr", 0.9), ("fontcolorg", 0.94), ("fontcolorb", 0.98),
        ("fontalpha", 1),
        ("bgalpha", 1), ("bgcolorr", color[0]), ("bgcolorg", color[1]),
        ("bgcolorb", color[2]), ("cursor", "pointer"),
    ):
        _set(node, par, item)
    return node


def _field(parent, name, x, y, width, height=38):
    node = _panel(_get_or_create(parent, fieldCOMP, name), x, y, width, height, 50)
    _set(node, "fieldtype", "string")
    _set(node, "bgalpha", 1)
    _set(node, "fontalpha", 1)
    string_dat = node.op("string")
    if string_dat is not None:
        current = str(string_dat[0, 0]) if string_dat.numRows and string_dat.numCols else ""
        if current.strip().casefold() in {"", "field"}:
            string_dat.text = ""
    return node


def _viewer(parent, name, target, x, y, width, height):
    node = _panel(_get_or_create(parent, opviewerCOMP, name), x, y, width, height, 20)
    _set(node, "opviewer", target.path)
    _set(node, "allowpanel", False)
    node.viewer = True
    return node


def _execute(parent, name, source, callback):
    node = parent.op(name)
    if node is not None and node.type != "panelexec":
        node.destroy()
        node = None
    node = node or parent.create(panelexecuteDAT, name)
    node.name = name
    node.par.active = True
    node.par.fromop = source.path
    node.par.panels = source.path
    node.par.panelvalue = "state"
    node.par.offtoon = True
    node.par.valuechange = False
    node.text = "def onOffToOn(panelValue):\n    op(%r).module.%s\n    return\n" % (OWNER + "/unified_runtime", callback)


def _viewer_execute(parent, name, source, callback):
    """Apply a material when its visual preview, not just its label, is clicked."""
    node = _get_or_create(parent, 'panelexecuteDAT', name)
    node.par.active = True
    node.par.panels = source.path
    node.par.panelvalue = "select"
    node.par.offtoon = True
    node.par.whileon = False
    node.par.ontooff = False
    node.par.whileoff = False
    node.par.valuechange = False
    node.text = "def onOffToOn(panelValue):\n    op(%r).module.%s\n    return\n" % (OWNER + "/unified_runtime", callback)
    return node


def _value_execute(parent, name, source, parameter):
    """Bind a visible slider to one central material-control parameter."""
    node = _get_or_create(parent, 'panelexecuteDAT', name)
    node.par.active = True
    node.par.fromop = source.path
    node.par.panels = source.path
    node.par.panelvalue = "value"
    node.par.offtoon = False
    node.par.valuechange = True
    node.text = (
        "def onValueChange(panelValue):\n"
        "    op('/project1/madmapper_player_controls').par.%s = float(panelValue)\n"
        "    return\n" % parameter
    )
    return node


def _momentary_execute(parent, name, source, body):
    """Create one canonical momentary handler, replacing a wrong OP type."""
    node = parent.op(name)
    if node is not None and node.type != "panelexec":
        node.destroy()
        node = None
    node = node or parent.create(panelexecuteDAT, name)
    node.name = name
    node.par.active = True
    node.par.fromop = source.path
    node.par.panels = source.path
    node.par.panelvalue = "state"
    node.par.offtoon = True
    node.par.valuechange = False
    node.text = "def onOffToOn(panelValue):\n    %s\n    return\n" % body
    return node


def _slider(parent, name, label, x, y, width, low, high, value, parameter):
    node = _panel(_get_or_create(parent, sliderCOMP, name), x, y, width, 28, 50)
    _set(node, "label", label)
    _set(node, "valuerange0l", low)
    _set(node, "valuerange0h", high)
    _set(node, "value0", value)
    _value_execute(parent, name + "_change", node, parameter)
    return node


def _material_control_runtime_source():
    return r'''SOURCE = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/material_control_surface.py'
def _module():
    namespace = {'op': op}
    exec(compile(open(SOURCE, encoding='utf-8').read(), SOURCE, 'exec'), namespace)
    return namespace
def apply_gradient(key):
    return _module()['apply_gradient'](key)
def reset_frame():
    return _module()['reset_frame']()
'''


def _material_controls(browser):
    """Create the central speed, framing, and gradient strip below the browser."""
    controls = op('/project1/madmapper_player_controls')
    runtime = _get_or_create(browser, textDAT, 'mb_control_runtime')
    runtime.text = _material_control_runtime_source()
    _slider(browser, 'mb_control_speed', 'SPEED', 20, 754, 250, 0.0, 2.0, controls.par.Speed.eval(), 'Speed')
    _slider(browser, 'mb_control_focusx', 'FOCUS X', 285, 754, 190, 0.0, 1.0, controls.par.Focusx.eval(), 'Focusx')
    _slider(browser, 'mb_control_focusy', 'FOCUS Y', 490, 754, 190, 0.0, 1.0, controls.par.Focusy.eval(), 'Focusy')
    _slider(browser, 'mb_control_zoom', 'FRAME ZOOM', 695, 754, 220, 0.25, 4.0, controls.par.Framezoom.eval(), 'Framezoom')
    for index, (label, value) in enumerate((('STOP', 0.0), ('0.5x', 0.5), ('1x', 1.0), ('2x', 2.0))):
        button = _button(browser, 'mb_control_speed_%d' % index, label, 20 + index * 76, 790, 70, 28)
        _momentary_execute(
            browser, 'mb_control_speed_%d_click' % index, button,
            "op('/project1/madmapper_player_controls').par.Speed = %s" % value,
        )
    reset = _button(browser, 'mb_control_view_reset', 'RESET VIEW', 340, 790, 110, 28)
    _momentary_execute(
        browser, 'mb_control_view_reset_click', reset,
        "op('/project1/material_browser/mb_control_runtime').module.reset_frame()",
    )
    for index, (label, key) in enumerate((('NEON', 'neon_cyan_magenta'), ('AMBER', 'amber_violet'), ('ACID', 'acid_lime_blue'), ('FIRE/ICE', 'fire_ice'), ('MONO', 'mono_white'))):
        button = _button(browser, 'mb_control_gradient_%d' % index, label, 470 + index * 88, 790, 82, 28)
        _momentary_execute(
            browser, 'mb_control_gradient_%d_click' % index, button,
            "op('/project1/material_browser/mb_control_runtime').module.apply_gradient('%s')" % key,
        )


def _runtime_source():
    return r'''import json
import re
from difflib import SequenceMatcher
from pathlib import Path

OWNER = op('/project1/material_browser')
MANIFEST = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/effects/effects_manifest.json')
CATALOG = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/material_library/catalogs/madmapper-official-d7ff211.json')
IMPORT_ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/material_library/imported')
ITEMS = []
FILTERED = []

def _state(name, default=''):
    table = OWNER.op('unified_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == name:
            return str(table[row, 1])
    return str(default)

def _set_state(name, value):
    table = OWNER.op('unified_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == name:
            table[row, 1] = value
            return
    table.appendRow((name, value))

def _field():
    dat = OWNER.op('unified_search/string')
    return str(dat[0, 0]).strip() if dat is not None and dat.numRows else ''

def _button(name, label):
    node = OWNER.op(name)
    if node is not None:
        node.par.label = label

def _status(value, good=True):
    node = OWNER.op('unified_status')
    node.par.text = value
    node.par.fontcolorr = 0.35 if good else 0.98
    node.par.fontcolorg = 0.90 if good else 0.38
    node.par.fontcolorb = 0.67 if good else 0.32

def _core_items():
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    result = []
    for definition in data['effectDefinitions']:
        category = str(definition['category'])
        tags = [category.lower(), definition['id'].replace('_', ' '), 'core', 'gpu', 'effect']
        result.append({
            'key': 'core:' + definition['id'], 'id': definition['id'],
            'label': definition['label'], 'source': 'core',
            'groups': ['core', category.lower()], 'tags': tags,
            'category': category, 'effect_index': int(definition['index']),
            'preset': dict(definition.get('preset', {})),
            'preview_path': '', 'prepared_path': '', 'compatibility': 'ready',
        })
    return result

def _imported_items():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    result = []
    for raw in data.get('materials', []):
        material_id = str(raw.get('id', ''))
        directory = IMPORT_ROOT / material_id
        if not (directory / 'material-import.json').is_file():
            continue
        groups = [str(value).lower() for value in raw.get('groups', [])]
        groups = list(dict.fromkeys(['imported'] + groups))
        tags = [str(value).lower() for value in raw.get('tags', [])]
        tags = list(dict.fromkeys(['imported', 'madmapper'] + tags))
        preview = str(raw.get('preview_path', ''))
        if preview and not Path(preview).is_absolute():
            preview = str((CATALOG.parent / preview).resolve())
        prepared = directory / 'prepared.frag'
        result.append({
            'key': 'madmapper:' + material_id, 'id': material_id,
            'label': str(raw.get('name') or material_id), 'source': 'imported',
            'groups': groups, 'tags': tags,
            'category': groups[1] if len(groups) > 1 else 'imported',
            'effect_index': -1, 'preview_path': preview,
            'preset': {},
            'prepared_path': str(prepared) if prepared.is_file() else '',
            'compatibility': str(raw.get('compatibility', 'unknown')),
        })
    return result

def _group_values():
    return ['All'] + sorted({group for item in ITEMS for group in item['groups']}, key=str.lower)

def _populate_group_menu():
    values = _group_values()[:20]
    menu = OWNER.op('unified_group_dropdown')
    for index in range(20):
        button = menu.op('group_option_%d' % index)
        if index < len(values):
            button.par.display = True
            button.par.label = values[index].replace('_', ' ').upper()
            button.store('group_value', values[index])
        else:
            button.par.display = False

def refresh():
    global ITEMS
    try:
        ITEMS = _core_items() + _imported_items()
        _populate_group_menu()
        apply_filters()
        imported = sum(item['source'] == 'imported' for item in ITEMS)
        _status('READY | %d CORE + %d IMPORTED | DMX OFF' % (len(ITEMS) - imported, imported))
        return True
    except Exception as error:
        ITEMS = []
        apply_filters()
        _status('BROWSER BLOCKED - ' + str(error), False)
        return False

def _matches(token, text):
    if token in text:
        return True
    return any(SequenceMatcher(None, token, word).ratio() >= 0.78 for word in re.findall(r'[a-z0-9]+', text))

def apply_filters():
    global FILTERED
    query = _field().lower()
    tokens = [value for value in query.split() if value]
    source = _state('source', 'All').lower()
    group = _state('group', 'All').lower()
    FILTERED = []
    for item in ITEMS:
        text = ' '.join([item['label'], item['id'], item['category'], item['source']] + item['groups'] + item['tags']).lower()
        if tokens and not all(_matches(token, text) for token in tokens):
            continue
        if source != 'all' and item['source'] != source:
            continue
        if group != 'all' and group not in item['groups']:
            continue
        FILTERED.append(item)
    _set_state('page', 0)
    render()

def cycle_source():
    values = ['All', 'core', 'imported']
    current = _state('source', 'All')
    try: index = [value.lower() for value in values].index(current.lower())
    except ValueError: index = 0
    _set_state('source', values[(index + 1) % len(values)])
    apply_filters()

def toggle_group():
    menu = OWNER.op('unified_group_dropdown')
    menu.par.display = not bool(menu.par.display.eval())

def select_group_slot(index):
    button = OWNER.op('unified_group_dropdown/group_option_%d' % int(index))
    value = button.fetch('group_value', 'All')
    _set_state('group', value)
    OWNER.op('unified_group_dropdown').par.display = False
    apply_filters()

def toggle_layout():
    _set_state('layout', '8x4' if _state('layout', '4x2') == '4x2' else '4x2')
    _set_state('page', 0)
    render()

def change_page(delta):
    size = 32 if _state('layout', '4x2') == '8x4' else 8
    count = max(1, (len(FILTERED) + size - 1) // size)
    page = max(0, min(count - 1, int(_state('page', 0)) + int(delta)))
    _set_state('page', page)
    render()

def render():
    compact = _state('layout', '4x2') == '8x4'
    size = 32 if compact else 8
    count = max(1, (len(FILTERED) + size - 1) // size)
    page = max(0, min(count - 1, int(_state('page', 0))))
    _set_state('page', page)
    _button('unified_source', 'SOURCE: ' + _state('source', 'All').upper())
    _button('unified_group', 'GROUP: ' + _state('group', 'All').replace('_', ' ').upper())
    _button('unified_layout', 'VIEW: ' + ('8 x 4' if compact else '4 x 2'))
    OWNER.op('unified_page').par.text = 'PAGE %d / %d | %d RESULTS' % (page + 1, count, len(FILTERED))
    visible = FILTERED[page * size:page * size + size]
    for slot in range(32):
        viewer = OWNER.op('unified_viewer_%d' % slot)
        button = OWNER.op('unified_card_%d' % slot)
        if slot >= len(visible):
            viewer.par.display = False
            button.par.display = False
            button.unstore('item_key')
            continue
        item = visible[slot]
        viewer.par.display = True
        button.par.display = True
        button.store('item_key', item['key'])
        if compact:
            column, row = slot % 8, slot // 8
            x, y, width, image_height, button_height = 20 + column * 154, 512 - row * 148, 146, 108, 34
            button.par.fontsize = 9
            button.par.label = item['label'] + (' | IMPORTED' if item['source'] == 'imported' else '')
        else:
            column, row = slot % 4, slot // 4
            x, y, width, image_height, button_height = 20 + column * 307, 365 - row * 296, 298, 236, 48
            button.par.fontsize = 12
            button.par.label = '%s\n%s | %s' % (item['label'], item['source'].upper(), item['category'].replace('_', ' ').upper())
        button.par.x, button.par.y, button.par.w, button.par.h = x, y, width, button_height
        viewer.par.x, viewer.par.y, viewer.par.w, viewer.par.h = x, y + button_height + 4, width, image_height
        if item['source'] == 'core':
            viewer.par.opviewer = OWNER.op('card_top_%d' % item['effect_index']).path
        else:
            image = OWNER.op('unified_image_%d' % slot)
            image.par.file = item['preview_path']
            viewer.par.opviewer = image.path if item['preview_path'] else OWNER.op('unified_fallback').path

def select_slot(slot):
    compact = _state('layout', '4x2') == '8x4'
    size = 32 if compact else 8
    index = int(_state('page', 0)) * size + int(slot)
    if not 0 <= index < len(FILTERED):
        return False
    item = FILTERED[index]
    controls = op('/project1/madmapper_player_controls')
    state_runtime = op('/project1/material_state_runtime')
    if state_runtime is not None:
        state_runtime.module.activate(item['key'], item.get('preset', {}))
    if item['source'] == 'core':
        controls.par.Source = 'materials'
        controls.par.Material = item['id']
        _status('ACTIVE CORE MATERIAL - ' + item['label'])
        return True
    library = op('/project1/madmapper_library/runtime')
    if library is None:
        _status('IMPORTED MATERIAL BLOCKED - library runtime is missing', False)
        return False
    module = library.module
    record = next((value for value in module._items if value['id'] == item['id']), None)
    if record is None:
        module.refresh()
        record = next((value for value in module._items if value['id'] == item['id']), None)
    if record is None:
        _status('IMPORTED MATERIAL BLOCKED - catalog record is missing', False)
        return False
    if item['prepared_path']:
        record['prepared_shader_path'] = item['prepared_path']
    module._set_state('selected_id', item['id'])
    if not module.open_live_preview():
        _status('IMPORTED MATERIAL NEEDS MANUAL ADAPTATION - ' + item['label'], False)
        return False
    controls.par.Source = 'imported'
    _status('ACTIVE IMPORTED MATERIAL - ' + item['label'])
    return True

# The Text DAT module is recreated when a .toe file is reopened.  Populate the
# runtime catalog on import so visible material cards can always resolve their
# selection, rather than relying on the one-time builder invocation.
refresh()
'''


def build():
    project = op(ROOT)
    browser = op(OWNER)
    if project is None or browser is None:
        raise RuntimeError("Build the existing Core Effects browser first")

    _remove_generated_duplicates(browser)

    browser.par.w = 1280
    browser.par.h = 900
    _set(browser, "top", "")
    for suffix, value in zip("rgb", (0.006, 0.012, 0.020)):
        _set(browser, "bgcolor" + suffix, value)
    _set(browser, "bgalpha", 1)

    old_mouse = browser.op("material_browser_mouse")
    if old_mouse is not None:
        old_mouse.par.active = False
    for index in range(25):
        old_button = browser.op("material_card_%d" % index)
        if old_button is not None:
            old_button.par.display = False

    runtime = _get_or_create(browser, textDAT, "unified_runtime")
    runtime.text = _runtime_source()
    state = _get_or_create(browser, tableDAT, "unified_state")
    if state.numRows < 2:
        for row in (("key", "value"), ("page", 0), ("source", "All"),
                    ("group", "All"), ("layout", "4x2")):
            state.appendRow(row)

    _text(browser, "unified_title", "MATERIAL BROWSER | CORE + IMPORTED MADMAPPER", 20, 850, 1240, 38, 21, (0.92, 0.96, 1.0))
    search = _field(browser, "unified_search", 20, 704, 315, 38)
    apply_button = _button(browser, "unified_apply", "SEARCH / APPLY", 345, 704, 130)
    source = _button(browser, "unified_source", "SOURCE: ALL", 485, 704, 155)
    group = _button(browser, "unified_group", "GROUP: ALL", 650, 704, 190)
    layout = _button(browser, "unified_layout", "VIEW: 4 x 2", 850, 704, 125)
    previous = _button(browser, "unified_previous", "<", 985, 704, 50)
    page = _text(browser, "unified_page", "PAGE 1 / 1", 1045, 704, 155, 38, 11)
    next_button = _button(browser, "unified_next", ">", 1210, 704, 50)
    _text(browser, "unified_status", "READY | DMX OFF", 20, 12, 1240, 38, 12, (0.35, 0.90, 0.67))
    _material_controls(browser)

    _execute(browser, "unified_apply_click", apply_button, "apply_filters()")
    _execute(browser, "unified_source_click", source, "cycle_source()")
    _execute(browser, "unified_group_click", group, "toggle_group()")
    _execute(browser, "unified_layout_click", layout, "toggle_layout()")
    _execute(browser, "unified_previous_click", previous, "change_page(-1)")
    _execute(browser, "unified_next_click", next_button, "change_page(1)")

    group_menu = _panel(_get_or_create(browser, containerCOMP, "unified_group_dropdown"), 650, 94, 190, 600, 100)
    for suffix, value in zip("rgb", (0.018, 0.026, 0.038)):
        _set(group_menu, "bgcolor" + suffix, value)
    _set(group_menu, "bgalpha", 1)
    group_menu.par.display = False
    for index in range(GROUP_OPTION_COUNT):
        button = _button(group_menu, "group_option_%d" % index, "GROUP", 0, 570 - index * 30, 190, 30)
        _execute(browser, "unified_group_option_click_%d" % index, button, "select_group_slot(%d)" % index)

    fallback = _get_or_create(browser, textTOP, "unified_fallback")
    _set(fallback, "text", "IMPORTED MATERIAL\nNO STORED PREVIEW")
    _set(fallback, "outputresolution", "custom")
    _set(fallback, "resolutionw", 512)
    _set(fallback, "resolutionh", 512)

    for slot in range(SLOT_COUNT):
        image = _get_or_create(browser, moviefileinTOP, "unified_image_%d" % slot)
        image.nodeX, image.nodeY = 900 + (slot % 8) * 70, -500 - (slot // 8) * 80
        viewer = _viewer(browser, "unified_viewer_%d" % slot, fallback, 20, 100, 146, 108)
        button = _button(browser, "unified_card_%d" % slot, "MATERIAL", 20, 60, 146, 34)
        _execute(browser, "unified_card_click_%d" % slot, button, "select_slot(%d)" % slot)
        _viewer_execute(browser, "unified_viewer_click_%d" % slot, viewer, "select_slot(%d)" % slot)

    ui_preview = _get_or_create(browser, opviewerTOP, "ui_preview")
    _set(ui_preview, "opviewer", browser.path)
    _set(ui_preview, "allowpanel", False)
    _set(ui_preview, "outputresolution", "custom")
    _set(ui_preview, "resolutionw", 1280)
    _set(ui_preview, "resolutionh", 800)
    ui_preview.nodeX, ui_preview.nodeY = 1220, -160

    controls = op(ROOT + "/madmapper_player_controls")
    names = list(controls.par.Source.menuNames)
    labels = list(controls.par.Source.menuLabels)
    if "imported" not in names:
        names.append("imported")
        labels.append("Imported MadMapper Material")
    controls.par.Source.menuNames = names
    controls.par.Source.menuLabels = labels

    switch = op(ROOT + "/visual_source_switch")
    imported_source = op(ROOT + "/madmapper_library")
    imported_path = ROOT + "/madmapper_library/imported_material_out"
    imported_indices = [index for index, node in enumerate(switch.inputs) if node.path == imported_path]
    for duplicate_index in reversed(imported_indices[1:]):
        switch.inputConnectors[duplicate_index].disconnect()
    if not imported_indices:
        imported_source.outputConnectors[0].connect(switch)
    switch.par.index.expr = "op('/project1/madmapper_player_controls').par.Source.menuIndex"

    browser.store("unified_material_browser_version", 1)
    runtime.module.refresh()
    print({"browser": browser.path, "slots": SLOT_COUNT, "sources": names,
           "networkOutputEnabled": False, "projectSaved": False})
    return browser


if "op" in globals():
    result = build()
