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
NATIVE_PARAMETER_SLOT_COUNT = 16
NATIVE_PARAMETER_COMPONENT_COUNT = 4
NATIVE_PARAMETER_COLUMN_COUNT = 2
NATIVE_PARAMETER_ROWS_PER_COLUMN = 8

# Exact public names created by this builder. TouchDesigner suffixes a name
# when an older builder left a same-name sibling behind; these prefixes let us
# remove only such generated duplicates without touching material sources.
GENERATED_SINGLETON_PREFIXES = (
    "mb_control_speed", "mb_control_focusx", "mb_control_focusy",
    "mb_control_zoom", "mb_control_view_reset",
    "unified_apply", "unified_source", "unified_group", "unified_layout",
    "unified_previous", "unified_next",
    "native_parameter_drawer", "native_params_open", "native_params_close",
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
    node = parent.op(name)
    if node is not None and node.type != "parameterexec":
        node.destroy()
        node = None
    node = node or parent.create(parameterexecuteDAT, name)
    node.par.active = True
    node.par.op = source.path
    node.par.pars = "value0"
    node.par.valuechange = True
    node.text = (
        "def onValueChange(par, prev):\n"
        "    op('/project1/madmapper_player_controls').par.%s = float(par.eval())\n"
        "    return\n" % parameter
    )
    return node


def _native_editor_value_execute(parent, name, source, component):
    """Bind one of the four shared native-parameter editor sliders."""
    node = parent.op(name)
    if node is not None and node.type != "parameterexec":
        node.destroy()
        node = None
    node = node or parent.create(parameterexecuteDAT, name)
    node.par.active = True
    node.par.op = source.path
    node.par.pars = "value0"
    node.par.valuechange = True
    node.text = (
        "def onValueChange(par, prev):\n"
        "    op(%r).module.native_editor_value_changed(%d, float(par.eval()))\n"
        "    return\n"
    ) % (OWNER + "/unified_runtime", component)
    return node


def _remove_native_parameter_children(drawer):
    """Remove only generated native row/editor controls from older builds."""
    pattern = re.compile(
        r"^native_param_(?:"
        r"label_\d+|action_\d+(?:_click)?|\d+_\d+(?:_change)?|"
        r"row_\d+(?:_click)?|editor(?:_title|_action(?:_click)?|_\d+(?:_change)?)"
        r")$"
    )
    for child in tuple(drawer.children):
        if pattern.match(child.name):
            child.destroy()


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
    _slider(browser, 'mb_control_speed', 'MASTER SPEED', 20, 754, 250, 0.0, 2.0, controls.par.Speed.eval(), 'Speed')
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


def _material_player_runtime_source():
    return r'''OWNER = op('/project1/madmapper_player_controls/ui_panel')
CONTROLS = op('/project1/madmapper_player_controls')

def update():
    source = str(CONTROLS.par.Source.eval())
    material = str(CONTROLS.par.Material.eval())
    imported = op('/project1/madmapper_library/material_parameter_state')
    selected = ''
    if imported is not None:
        for row in range(1, imported.numRows):
            if str(imported[row, 0]) == 'selected_id':
                selected = str(imported[row, 1])
                break
    OWNER.op('player_status').par.text = (
        'SOURCE: %s  |  MATERIAL: %s%s' % (
            source.upper(), material,
            ('  |  IMPORTED ID: ' + selected) if source == 'imported' and selected else '')
    )
    sender = op('/project1/multi_controller_output/artnet_510_sender_callbacks')
    sender_state = sender.module.status() if sender is not None else {}
    telemetry = sender_state.get('telemetry', {})
    actual = float(telemetry.get('actual_send_fps', 0.0))
    controller_table = op('/project1/multi_controller_output/controller_config')
    configured = []
    if controller_table is not None:
        for row in range(1, controller_table.numRows):
            if str(controller_table[row, 'enabled']).lower() in ('1', 'true', 'yes', 'on'):
                configured.append('%s %s FPS' % (
                    str(controller_table[row, 'name']), str(controller_table[row, 'rate'])))
    OWNER.op('player_fps').par.text = (
        'TOUCHDESIGNER TARGET: %.1f FPS  |  ART-NET ACTUAL: %.1f FPS  |  CONFIG: %s%s' % (
            float(project.cookRate), actual, ', '.join(configured) or 'no enabled controller',
            '' if sender_state.get('enabled') else '  |  OUTPUT OFF')
    )
    return True
'''


def _material_player_surface(controls):
    """Build the actual control surface opened by Ctrl+Shift+4."""
    panel = _panel(_get_or_create(controls, containerCOMP, 'ui_panel'), 0, 0, 1180, 720, 10)
    for suffix, value in zip('rgb', (0.006, 0.012, 0.020)):
        _set(panel, 'bgcolor' + suffix, value)
    _set(panel, 'bgalpha', 1)
    panel.viewer = True
    _text(panel, 'player_title', 'MATERIAL PLAYER | RAW MATERIAL + LIVE CONTROLS', 20, 670, 1140, 36, 21, (0.92, 0.96, 1.0))
    _text(panel, 'player_status', 'SOURCE / MATERIAL', 20, 632, 1140, 28, 12, (0.38, 0.76, 0.96))
    _text(panel, 'player_fps', 'FPS', 20, 598, 1140, 26, 11, (0.35, 0.90, 0.67))
    # Show the same canonical source that feeds the live mapping pipeline.
    # ``material_preview`` is a legacy Select TOP wired to
    # ``/project1/madmapper_material_player``; imported materials bypass that
    # player and therefore appeared as TouchDesigner's solid-magenta error
    # image in this dialog even while the live source was valid.
    raw = (
        op('/project1/visual_source_switch')
        or controls.op('material_preview')
        or op('/project1/material_source')
    )
    if raw is not None:
        _viewer(panel, 'player_preview', raw, 20, 82, 720, 506)
    _text(panel, 'controls_title', 'LIVE PLAYER CONTROLS', 770, 580, 380, 32, 16, (0.91, 0.96, 1.0))
    rows = (
        ('player_speed', 'MASTER SPEED', 'Speed', 0.0, 2.0, 530),
        ('player_scale', 'SCALE', 'Scale', 0.1, 4.0, 470),
        ('player_width', 'WIDTH', 'Width', 0.0, 1.0, 410),
        ('player_focusx', 'FOCUS X', 'Focusx', 0.0, 1.0, 350),
        ('player_focusy', 'FOCUS Y', 'Focusy', 0.0, 1.0, 290),
        ('player_zoom', 'FRAME ZOOM', 'Framezoom', 0.25, 8.0, 230),
        ('player_intensity', 'INTENSITY', 'Intensity', 0.0, 2.0, 170),
        ('player_contrast', 'CONTRAST', 'Contrast', 0.1, 4.0, 110),
    )
    for name, label, parameter, low, high, y in rows:
        _slider(panel, name, label, 770, y, 380, low, high,
                getattr(controls.par, parameter).eval(), parameter)
    open_browser = _button(panel, 'player_open_browser', 'OPEN MATERIAL BROWSER', 770, 54, 250, 38, (0.14, 0.24, 0.40))
    reset_view = _button(panel, 'player_reset_view', 'RESET VIEW', 1030, 54, 120, 38, (0.38, 0.20, 0.08))
    _momentary_execute(
        panel, 'player_open_browser_click', open_browser,
        "op('/project1/material_browser').openViewer()",
    )
    _momentary_execute(
        panel, 'player_reset_view_click', reset_view,
        "op('/project1/material_browser/mb_control_runtime').module.reset_frame()",
    )
    runtime = _get_or_create(controls, textDAT, 'player_ui_runtime')
    runtime.text = _material_player_runtime_source()
    execute = _get_or_create(controls, executeDAT, 'player_ui_update')
    execute.par.active = True
    execute.par.framestart = True
    # UI telemetry does not need to cook at render rate. Four updates per
    # second at 60 FPS keep the label readable without burdening Art-Net.
    execute.text = (
        "def onFrameStart(frame):\n"
        "    if int(frame) % 15:\n"
        "        return\n"
        "    op('player_ui_runtime').module.update()\n"
        "    return\n"
    )
    runtime.module.update()
    return panel


def _native_parameter_controls(browser):
    """Build a dense 16-row page with one shared four-component editor."""
    open_button = _button(browser, 'native_params_open', 'NATIVE PARAMS', 1120, 790, 140, 28, (0.14, 0.24, 0.40))
    _momentary_execute(
        browser, 'native_params_open_click', open_button,
        "op('/project1/material_browser/unified_runtime').module.toggle_native_parameters(True)",
    )
    drawer = _panel(
        _get_or_create(browser, containerCOMP, 'native_parameter_drawer'),
        20, 364, 1240, 456, 120,
    )
    _remove_native_parameter_children(drawer)
    for name, value in (
        ('bgcolorr', 0.065), ('bgcolorg', 0.072), ('bgcolorb', 0.082),
        ('bgalpha', 1), ('display', False),
    ):
        _set(drawer, name, value)
    title = _text(
        drawer, 'native_parameter_title', 'NATIVE MADMAPPER PARAMETERS',
        16, 410, 970, 30, 14, (0.91, 0.96, 1.0),
    )
    for suffix, value in zip('rgb', (0.035, 0.041, 0.050)):
        _set(title, 'bgcolor' + suffix, value)
    message = _text(
        drawer, 'native_parameter_message', '', 16, 70, 1208, 336, 13,
        (0.98, 0.52, 0.30),
    )
    message.par.display = False
    back_top = _button(
        drawer, 'native_params_back_top', 'ZURÜCK ZU MATERIALIEN',
        1000, 410, 224, 30, (0.20, 0.12, 0.13),
    )
    _momentary_execute(
        drawer, 'native_params_back_top_click', back_top,
        "op('/project1/material_browser/unified_runtime').module.toggle_native_parameters(False)",
    )
    for slot in range(NATIVE_PARAMETER_SLOT_COUNT):
        column = slot % NATIVE_PARAMETER_COLUMN_COUNT
        row = slot // NATIVE_PARAMETER_COLUMN_COUNT
        cell_x = 16 + column * 604
        y = 374 - row * 32
        shade = 0.105 if slot % 2 == 0 else 0.085
        row_button = _button(
            drawer, 'native_param_row_%d' % slot, 'PARAMETER | VALUE',
            cell_x, y, 588, 26, (shade, shade, shade),
        )
        _set(row_button, 'fontsize', 9)
        _momentary_execute(
            drawer, 'native_param_row_%d_click' % slot, row_button,
            "op('/project1/material_browser/unified_runtime').module.native_select(%d)" % slot,
        )
        row_button.par.display = False
    editor_title = _text(
        drawer, 'native_param_editor_title', 'SELECT A PARAMETER',
        16, 70, 300, 34, 10, (0.91, 0.96, 1.0),
    )
    editor_action = _button(
        drawer, 'native_param_editor_action', 'ACTION',
        324, 70, 900, 34, (0.14, 0.22, 0.30),
    )
    _momentary_execute(
        drawer, 'native_param_editor_action_click', editor_action,
        "op('/project1/material_browser/unified_runtime').module.native_editor_action()",
    )
    editor_action.par.display = False
    for component in range(NATIVE_PARAMETER_COMPONENT_COUNT):
        slider = _panel(
            _get_or_create(drawer, sliderCOMP, 'native_param_editor_%d' % component),
            324 + component * 226, 70, 222, 34, 150,
        )
        _set(slider, 'fontsize', 10)
        _set(slider, 'label', ('VALUE', 'Y', 'Z', 'W')[component])
        _set(slider, 'valuerange0l', 0.0)
        _set(slider, 'valuerange0h', 1.0)
        _set(slider, 'value0', 0.0)
        slider.par.display = False
        _native_editor_value_execute(
            drawer, 'native_param_editor_%d_change' % component,
            slider, component,
        )
    previous = _button(drawer, 'native_params_previous', '< PREVIOUS 16', 16, 20, 150, 28, (0.11, 0.13, 0.15))
    next_button = _button(drawer, 'native_params_next', 'NEXT 16 >', 176, 20, 150, 28, (0.11, 0.13, 0.15))
    reset = _button(drawer, 'native_params_reset', 'RESET MATERIAL', 336, 20, 180, 28, (0.24, 0.18, 0.10))
    close = _button(drawer, 'native_params_close', 'ZURÜCK', 1054, 20, 170, 28, (0.20, 0.12, 0.13))
    for name, button, body in (
        ('native_params_previous_click', previous, "op('/project1/material_browser/unified_runtime').module.native_page(-1)"),
        ('native_params_next_click', next_button, "op('/project1/material_browser/unified_runtime').module.native_page(1)"),
        ('native_params_reset_click', reset, "op('/project1/material_browser/unified_runtime').module.native_reset()"),
        ('native_params_close_click', close, "op('/project1/material_browser/unified_runtime').module.toggle_native_parameters(False)"),
    ):
        _momentary_execute(drawer, name, button, body)
    return drawer


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
NATIVE_PARAMETER_SLOT_COUNT = 16
NATIVE_PAGE = 0
NATIVE_PARAMETER_COLUMN_COUNT = 2
NATIVE_PARAMETER_ROWS_PER_COLUMN = 8
NATIVE_SELECTED_SLOT = 0
NATIVE_PAGE_STORE_KEY = 'native_parameter_page'
NATIVE_SLOT_STORE_KEY = 'native_parameter_selected_slot'

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

def _native_library():
    runtime = op('/project1/madmapper_library/runtime')
    if runtime is None:
        raise RuntimeError('MadMapper library runtime is missing')
    return runtime.module

def _native_component_labels(kind):
    return {
        'point2d': ('X', 'Y'), 'size2d': ('WIDTH', 'HEIGHT'),
        'floatrange': ('MIN', 'MAX'), 'color': ('R', 'G', 'B', 'A'),
    }.get(str(kind).lower(), ('VALUE',))

def _native_bounds(parameter, component):
    kind = str(parameter.get('type', 'float')).lower()
    if kind == 'color':
        return 0.0, 1.0
    values = parameter.get('values') or []
    if kind == 'long' and values:
        return 0.0, float(max(0, len(values) - 1))
    minimum, maximum = parameter.get('min'), parameter.get('max')
    if isinstance(minimum, (list, tuple)):
        minimum = minimum[component] if component < len(minimum) else None
    if isinstance(maximum, (list, tuple)):
        maximum = maximum[component] if component < len(maximum) else None
    current = parameter.get('value', 0.0)
    if isinstance(current, (list, tuple)):
        current = current[component] if component < len(current) else 0.0
    current = float(current or 0.0)
    low = float(minimum) if minimum is not None else min(0.0, current - max(1.0, abs(current)))
    high = float(maximum) if maximum is not None else max(1.0, current + max(1.0, abs(current)))
    if high <= low:
        high = low + 1.0
    return low, high

def toggle_native_parameters(show=None):
    drawer = OWNER.op('native_parameter_drawer')
    if drawer is None:
        return False
    if show is None:
        show = not bool(drawer.par.display.eval())
    drawer.par.display = bool(show)
    if show:
        render_native_parameters()
    return bool(show)

def _native_control(name):
    return OWNER.op('native_parameter_drawer/' + str(name))

def _layout_native_drawer(visible_count):
    """Keep the drawer dense while preserving room for one shared editor."""
    drawer = OWNER.op('native_parameter_drawer')
    row_count = max(1, min(NATIVE_PARAMETER_ROWS_PER_COLUMN,
                           (int(visible_count) + NATIVE_PARAMETER_COLUMN_COUNT - 1)
                           // NATIVE_PARAMETER_COLUMN_COUNT))
    height = 200 + row_count * 32
    drawer.par.h = height
    drawer.par.y = 820 - height
    title_y = height - 46
    _native_control('native_parameter_title').par.y = title_y
    _native_control('native_params_back_top').par.y = title_y
    message = _native_control('native_parameter_message')
    message.par.y = 70
    message.par.h = max(80, height - 120)
    for slot in range(NATIVE_PARAMETER_SLOT_COUNT):
        row = slot // NATIVE_PARAMETER_COLUMN_COUNT
        _native_control('native_param_row_%d' % slot).par.y = height - 82 - row * 32
    _native_control('native_param_editor_title').par.y = 70
    _native_control('native_param_editor_action').par.y = 70
    for component in range(4):
        _native_control('native_param_editor_%d' % component).par.y = 70

def _clear_native_parameter_rows():
    """Hide and detach the compact master rows and shared editor."""
    for slot in range(NATIVE_PARAMETER_SLOT_COUNT):
        row = _native_control('native_param_row_%d' % slot)
        row.par.display = False
        row.unstore('parameter_name')
        row.unstore('parameter_type')
    title = _native_control('native_param_editor_title')
    action = _native_control('native_param_editor_action')
    title.par.text = 'SELECT A PARAMETER'
    title.unstore('parameter_name')
    title.unstore('parameter_type')
    action.par.display = False
    action.unstore('parameter_name')
    action.unstore('parameter_type')
    action.unstore('parameter_values')
    for component in range(4):
        slider = _native_control('native_param_editor_%d' % component)
        handler = _native_control('native_param_editor_%d_change' % component)
        slider.par.display = False
        slider.unstore('parameter_name')
        slider.unstore('parameter_type')
        if handler is not None:
            handler.par.active = False

def _native_value_text(parameter):
    kind = str(parameter.get('type', 'float')).lower()
    value = parameter.get('value')
    if kind == 'bool':
        return 'ON' if bool(value) else 'OFF'
    if kind == 'event':
        return 'TRIGGER'
    if kind in ('long', 'enum'):
        options = list(parameter.get('values') or [])
        index = int(value or 0)
        return str(options[index]) if 0 <= index < len(options) else str(index)
    values = list(value) if isinstance(value, (list, tuple)) else [value]
    return ', '.join('%.4g' % float(item or 0.0) for item in values)

def _native_row_text(parameter):
    name = str(parameter.get('name', ''))
    label = str(parameter.get('display_label') or parameter.get('label') or name)
    group = ' / '.join(parameter.get('groups') or [])
    prefix = (group + ' / ') if group else ''
    compile_note = ' *' if parameter.get('compile_time') else ''
    return '%s%s%s  |  %s' % (prefix, label, compile_note, _native_value_text(parameter))

def _render_native_editor(parameter):
    title = _native_control('native_param_editor_title')
    action = _native_control('native_param_editor_action')
    name = str(parameter['name'])
    kind = str(parameter['type']).lower()
    title.par.text = 'EDIT | %s | %s' % (
        parameter.get('display_label') or parameter.get('label') or name,
        kind.upper())
    title.store('parameter_name', name)
    title.store('parameter_type', kind)
    value = parameter.get('value')
    values = list(value) if isinstance(value, (list, tuple)) else [value]
    component_labels = _native_component_labels(kind)
    component_count = max(1, min(4, int(parameter.get('components') or 1)))
    scalar_action = kind in ('bool', 'event', 'long', 'enum')
    action.par.display = scalar_action
    action.store('parameter_name', name)
    action.store('parameter_type', kind)
    action.store('parameter_values', list(parameter.get('values') or []))
    if kind == 'bool':
        action.par.label = 'ON' if bool(value) else 'OFF'
    elif kind == 'event':
        action.par.label = 'TRIGGER'
    elif kind in ('long', 'enum'):
        action.par.label = _native_value_text(parameter)
    component_width = int((900 - max(0, component_count - 1) * 6) / component_count)
    for component in range(4):
        slider = _native_control('native_param_editor_%d' % component)
        handler = _native_control('native_param_editor_%d_change' % component)
        visible = component < component_count and not scalar_action
        slider.par.display = visible
        if not visible:
            continue
        if handler is not None:
            handler.par.active = False
        low, high = _native_bounds(parameter, component)
        slider.par.x = 324 + component * (component_width + 6)
        slider.par.w = component_width
        slider.par.valuerange0l = low
        slider.par.valuerange0h = high
        component_value = values[component] if component < len(values) else 0.0
        slider.par.value0 = float(component_value or 0.0)
        slider.par.label = component_labels[component]
        slider.store('parameter_name', name)
        slider.store('parameter_type', kind)
        if handler is not None:
            handler.par.active = True

def _native_error(message):
    _layout_native_drawer(2)
    _clear_native_parameter_rows()
    _native_control('native_parameter_title').par.text = 'NATIVE PARAMETERS NICHT VERFÜGBAR'
    detail = _native_control('native_parameter_message')
    detail.par.text = (
        'Dieses Material benötigt Funktionen, die der automatische TouchDesigner-Adapter '
        'nicht sicher übersetzen kann. Wähle ZURÜCK ZU MATERIALIEN und ein kompatibles '
        'importiertes Material.\n\nDetails: ' + str(message)
    )
    detail.par.display = True
    for name in ('native_params_previous', 'native_params_next', 'native_params_reset'):
        _native_control(name).par.display = False
    return False

def render_native_parameters():
    global NATIVE_PAGE, NATIVE_SELECTED_SLOT
    NATIVE_PAGE = int(OWNER.fetch(NATIVE_PAGE_STORE_KEY, NATIVE_PAGE))
    NATIVE_SELECTED_SLOT = int(OWNER.fetch(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT))
    drawer = OWNER.op('native_parameter_drawer')
    if drawer is None or not bool(drawer.par.display.eval()):
        return False
    _clear_native_parameter_rows()
    _native_control('native_parameter_message').par.display = False
    try:
        snapshot = _native_library().parameter_snapshot()
    except Exception as error:
        return _native_error(error)
    parameters = snapshot.get('parameters', [])
    if not parameters:
        return _native_error('Für das ausgewählte Material wurden keine veränderbaren nativen Parameter gefunden.')
    page_count = max(1, (len(parameters) + NATIVE_PARAMETER_SLOT_COUNT - 1) // NATIVE_PARAMETER_SLOT_COUNT)
    NATIVE_PAGE = max(0, min(page_count - 1, int(NATIVE_PAGE)))
    visible = parameters[
        NATIVE_PAGE * NATIVE_PARAMETER_SLOT_COUNT:
        NATIVE_PAGE * NATIVE_PARAMETER_SLOT_COUNT + NATIVE_PARAMETER_SLOT_COUNT
    ]
    _layout_native_drawer(len(visible))
    NATIVE_SELECTED_SLOT = max(0, min(len(visible) - 1, int(NATIVE_SELECTED_SLOT)))
    OWNER.store(NATIVE_PAGE_STORE_KEY, NATIVE_PAGE)
    OWNER.store(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)
    overflow = page_count > 1
    _native_control('native_params_previous').par.display = overflow
    _native_control('native_params_next').par.display = overflow
    _native_control('native_params_reset').par.display = True
    page_note = (' | PAGE %d / %d' % (NATIVE_PAGE + 1, page_count)) if overflow else ''
    _native_control('native_parameter_title').par.text = (
        'NATIVE MADMAPPER PARAMETERS | %s | %d PARAMS%s' % (
            snapshot.get('label', '-'), len(parameters), page_note))
    for slot in range(NATIVE_PARAMETER_SLOT_COUNT):
        row = _native_control('native_param_row_%d' % slot)
        if slot >= len(visible):
            row.par.display = False
            continue
        parameter = visible[slot]
        name = str(parameter['name'])
        kind = str(parameter['type']).lower()
        row.par.display = True
        row.par.label = _native_row_text(parameter)
        row.store('parameter_name', name)
        row.store('parameter_type', kind)
        selected = slot == NATIVE_SELECTED_SLOT
        row.par.bgcolorr = 0.12 if selected else 0.085
        row.par.bgcolorg = 0.28 if selected else 0.095
        row.par.bgcolorb = 0.40 if selected else 0.105
    _render_native_editor(visible[NATIVE_SELECTED_SLOT])
    return True

def native_select(slot):
    global NATIVE_SELECTED_SLOT
    row = _native_control('native_param_row_%d' % int(slot))
    if row is None or not row.fetch('parameter_name', ''):
        return False
    NATIVE_SELECTED_SLOT = int(slot)
    OWNER.store(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)
    return render_native_parameters()

def native_editor_value_changed(component, value):
    title = _native_control('native_param_editor_title')
    name = title.fetch('parameter_name', '')
    if not name:
        return False
    try:
        library = _native_library()
        snapshot = library.parameter_snapshot()
        parameter = next(item for item in snapshot['parameters'] if item['name'] == name)
        target_component = -1 if int(parameter.get('components') or 1) <= 1 else int(component)
        library.set_material_parameter(name, target_component, float(value))
        snapshot = library.parameter_snapshot()
        parameter = next(item for item in snapshot['parameters'] if item['name'] == name)
        selected_slot = int(OWNER.fetch(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT))
        row = _native_control('native_param_row_%d' % selected_slot)
        row.par.label = _native_row_text(parameter)
        _status('NATIVE PARAMETER UPDATED - ' + name)
        return True
    except Exception as error:
        _status('NATIVE PARAMETER BLOCKED - ' + str(error), False)
        return False

def native_editor_action():
    action = _native_control('native_param_editor_action')
    name = action.fetch('parameter_name', '')
    kind = action.fetch('parameter_type', '')
    if not name:
        return False
    try:
        snapshot = _native_library().parameter_snapshot()
        parameter = next(item for item in snapshot['parameters'] if item['name'] == name)
        value = parameter.get('value')
        if kind == 'event':
            _native_library().pulse_material_parameter(name)
        elif kind == 'bool':
            _native_library().set_material_parameter(name, -1, not bool(value))
        elif kind in ('long', 'enum'):
            options = action.fetch('parameter_values', [])
            _native_library().set_material_parameter(name, -1, (int(value or 0) + 1) % max(1, len(options)))
        render_native_parameters()
        _status('NATIVE PARAMETER UPDATED - ' + name)
        return True
    except Exception as error:
        _status('NATIVE PARAMETER BLOCKED - ' + str(error), False)
        return False

def native_page(delta):
    global NATIVE_PAGE, NATIVE_SELECTED_SLOT
    try:
        snapshot = _native_library().parameter_snapshot()
        parameters = snapshot.get('parameters', [])
        page_count = max(1, (len(parameters) + NATIVE_PARAMETER_SLOT_COUNT - 1) // NATIVE_PARAMETER_SLOT_COUNT)
        NATIVE_PAGE = max(0, min(page_count - 1, int(NATIVE_PAGE) + int(delta)))
        NATIVE_SELECTED_SLOT = 0
        OWNER.store(NATIVE_PAGE_STORE_KEY, NATIVE_PAGE)
        OWNER.store(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)
        return render_native_parameters()
    except Exception as error:
        _status('NATIVE PARAMETER PAGE BLOCKED - ' + str(error), False)
        return False

def native_reset():
    try:
        _native_library().reset_material_parameters()
        render_native_parameters()
        _status('NATIVE PARAMETERS RESET TO MATERIAL DEFAULTS')
        return True
    except Exception as error:
        _status('NATIVE PARAMETER RESET BLOCKED - ' + str(error), False)
        return False

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

def refresh(reset_page=True):
    global ITEMS
    try:
        ITEMS = _core_items() + _imported_items()
        _populate_group_menu()
        apply_filters(reset_page=reset_page)
        imported = sum(item['source'] == 'imported' for item in ITEMS)
        _status('READY | %d CORE + %d IMPORTED | DMX OFF' % (len(ITEMS) - imported, imported))
        return True
    except Exception as error:
        ITEMS = []
        apply_filters(reset_page=reset_page)
        _status('BROWSER BLOCKED - ' + str(error), False)
        return False

def _matches(token, text):
    if token in text:
        return True
    return any(SequenceMatcher(None, token, word).ratio() >= 0.78 for word in re.findall(r'[a-z0-9]+', text))

def apply_filters(reset_page=True):
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
    if reset_page:
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
    global NATIVE_PAGE, NATIVE_SELECTED_SLOT
    compact = _state('layout', '4x2') == '8x4'
    size = 32 if compact else 8
    index = int(_state('page', 0)) * size + int(slot)
    if not 0 <= index < len(FILTERED):
        return False
    item = FILTERED[index]
    NATIVE_PAGE = 0
    NATIVE_SELECTED_SLOT = 0
    OWNER.store(NATIVE_PAGE_STORE_KEY, NATIVE_PAGE)
    OWNER.store(NATIVE_SLOT_STORE_KEY, NATIVE_SELECTED_SLOT)
    controls = op('/project1/madmapper_player_controls')
    state_runtime = op('/project1/material_state_runtime')
    if state_runtime is not None:
        state_runtime.module.activate(item['key'], item.get('preset', {}))
    if item['source'] == 'core':
        controls.par.Source = 'materials'
        controls.par.Material = item['id']
        toggle_native_parameters(False)
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
    toggle_native_parameters(True)
    _status('ACTIVE IMPORTED MATERIAL - ' + item['label'])
    return True

# The Text DAT module is recreated when a .toe file is reopened.  Populate the
# runtime catalog on import so visible material cards can always resolve their
# selection, rather than relying on the one-time builder invocation.
refresh(reset_page=False)
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
    _native_parameter_controls(browser)

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
    _material_player_surface(controls)

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
