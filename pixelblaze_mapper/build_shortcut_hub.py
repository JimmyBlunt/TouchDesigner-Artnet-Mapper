"""Build the safe navigation shortcut hub in the running TouchDesigner project.

The shortcuts only open viewers. They never change effects, save the project,
or start/stop network output.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


LOCAL_ROOT = str(Path(__file__).resolve().parents[1])
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

import pixelblaze_mapper.shortcut_hub as _shortcut_hub_module  # noqa: E402
importlib.reload(_shortcut_hub_module)
from pixelblaze_mapper.shortcut_hub import SHORTCUTS, shortcut_rows, validate_shortcuts  # noqa: E402


PHOTO_PREVIEW = "/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype/prototype_out"
CANONICAL_PREVIEW = "/project1/LED_PREVIEW_OUT"


def _get_or_create(parent, op_type, name):
    node = parent.op(name) or parent.create(op_type, name)
    node.name = name
    return node


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _label(parent, name, text, x, y, width, height, color=(0.82, 0.88, 0.94), size=13):
    node = _get_or_create(parent, textCOMP, name)
    for parameter, value in (("x", x), ("y", y), ("w", width), ("h", height),
                             ("hmode", "fixed"), ("vmode", "fixed"), ("layer", 30),
                             ("text", text), ("fontsize", size), ("fontcolorr", color[0]),
                             ("fontcolorg", color[1]), ("fontcolorb", color[2]),
                             ("bgalpha", 0), ("display", True),
                             ("clickthrough", True), ("wordwrap", True),
                             ("type", "multiline"), ("fontalpha", 1),
                             ("alignx", "left"), ("aligny", "center")):
        _set(node, parameter, value)
    return node


def _callback_source():
    targets = {item.key.lower(): (item.label, item.target) for item in SHORTCUTS}
    return f'''# Generated safe navigation callbacks. No DMX or project-save actions.
TARGETS = {targets!r}

def open_target(key):
    key = str(key).lower()
    if key not in TARGETS:
        ui.status = 'Unknown shortcut: ' + key
        return False
    label, path = TARGETS[key]
    # Resolve at the time of every click/key press; targets may be rebuilt.
    target = op(path)
    if target is None:
        ui.status = 'Shortcut target missing: ' + path
        return False
    try:
        if key == 's':
            import sys
            root = str(project.folder)
            if root not in sys.path:
                sys.path.insert(0, root)
            from pixelblaze_mapper.led_search import act
            return act(op, 'open')
        target.openViewer()
    except Exception as error:
        ui.status = 'Shortcut viewer failed: ' + path + ' | ' + str(error)
        return False
    ui.status = label + ' | ' + path
    return True

def keyEvent(dat, key, character, alt, lalt, ralt, ctrl, lctrl, rctrl, shift, lshift, rshift, state, time):
    key = str(key).lower()
    if not state or not ctrl or not shift or alt or key not in TARGETS:
        return
    open_target(key)
    return

def shortcutEvent(dat, shortcutName, time):
    return
'''


def _open_button(owner, panel, item, y):
    from pixelblaze_mapper.scan_library_ui import style_button
    button = _get_or_create(panel, buttonCOMP, "open_" + item.key)
    for name, value in (("x", 994), ("y", y), ("w", 94), ("h", 38),
                        ("hmode", "fixed"), ("vmode", "fixed"), ("label", "OPEN"),
                        ("buttontype", "momentary"), ("value0", False),
                        ("display", True), ("layer", 30), ("fontsize", 12)):
        _set(button, name, value)
    style_button(button)
    node = _get_or_create(owner, panelexecuteDAT, 'open_click_' + item.key)
    node.par.active = False
    node.par.fromop = button.path
    node.par.panels = button.path
    node.par.panelvalue = "lselect"
    node.par.offtoon = True
    node.par.ontooff = False
    node.par.whileon = False
    node.par.whileoff = False
    node.par.valuechange = False
    node.text = "def onOffToOn(panelValue):\n    op('shortcut_callbacks').module.open_target(%r)\n    return\n" % item.key
    node.par.active = True
    return button


def build():
    issues = validate_shortcuts()
    if issues:
        raise RuntimeError("Invalid shortcut configuration: " + "; ".join(issues))

    project = op("/project1")
    photo_preview = op(PHOTO_PREVIEW)
    if photo_preview is None:
        raise RuntimeError("Canonical photo preview is missing: " + PHOTO_PREVIEW)
    canonical_preview = op(CANONICAL_PREVIEW) or project.create(selectTOP, "LED_PREVIEW_OUT")
    _set(canonical_preview, "top", photo_preview.path)
    canonical_preview.nodeX, canonical_preview.nodeY = 1450, 700

    owner = _get_or_create(project, baseCOMP, "shortcut_hub")
    owner.nodeX, owner.nodeY = 1600, 700
    for child in owner.children:
        if child.name.startswith('open_click_'):
            _set(child, 'active', False)

    table = _get_or_create(owner, tableDAT, "shortcut_config")
    table.clear()
    for row in shortcut_rows():
        table.appendRow(row)

    callbacks = _get_or_create(owner, textDAT, "shortcut_callbacks")
    callbacks.text = _callback_source()
    keyboard = _get_or_create(owner, keyboardinDAT, "shortcut_keyboard")
    _set(keyboard, "active", True)
    _set(keyboard, "perform", False)
    _set(keyboard, "keys", " ".join(item.key for item in SHORTCUTS))
    _set(keyboard, "callbacks", callbacks.path)

    panel = _get_or_create(owner, containerCOMP, "help_panel")
    panel_height = 200 + len(SHORTCUTS) * 48
    for parameter, value in (("w", 1120), ("h", panel_height), ("hmode", "fixed"), ("vmode", "fixed"),
                             ("bgcolorr", 0.008), ("bgcolorg", 0.014), ("bgcolorb", 0.023), ("bgalpha", 1)):
        _set(panel, parameter, value)
    _label(panel, "title", "TOUCHDESIGNER SHORTCUTS", 28, panel_height - 60, 1060, 42, (0.91, 0.96, 1), 23)
    _label(panel, "safety", "Navigation only - no shortcut starts DMX or changes the selected effect.", 28, panel_height - 102, 1060, 30, (0.35, 0.90, 0.67), 13)
    active_row_names = {
        prefix + item.key for item in SHORTCUTS for prefix in ("combo_", "name_", "purpose_", "open_")
    }
    for child in panel.children:
        if child.name.startswith(("combo_", "name_", "purpose_", "open_")) and child.name not in active_row_names:
            _set(child, "display", False)
    for index, item in enumerate(SHORTCUTS):
        y = panel_height - 154 - index * 48
        _label(panel, "combo_" + item.key, item.combo, 28, y, 180, 38, (0.38, 0.76, 0.96), 15)
        _label(panel, "name_" + item.key, item.label, 220, y, 250, 38, (0.91, 0.96, 1), 14)
        _label(panel, "purpose_" + item.key, item.purpose, 480, y, 500, 38, (0.72, 0.79, 0.86), 12)
        _open_button(owner, panel, item, y)
    _label(panel, "footer", "Tip: click an empty network area first. Text-entry fields can consume keyboard input.", 28, 22, 1060, 34, (0.97, 0.72, 0.26), 12)

    preview = _get_or_create(owner, opviewerTOP, "help_preview")
    _set(preview, "opviewer", panel.path)
    _set(preview, "allowpanel", True)
    _set(preview, "outputresolution", "custom")
    _set(preview, "resolutionw", 1120)
    _set(preview, "resolutionh", panel_height)

    readme = _get_or_create(owner, textDAT, "README")
    readme.text = "Safe navigation-only shortcuts. Source: pixelblaze_mapper/build_shortcut_hub.py"
    print({"owner": owner.path, "shortcuts": len(SHORTCUTS), "preview": photo_preview.path,
           "networkOutputTouched": False, "projectSaved": False})
    return owner


build()
