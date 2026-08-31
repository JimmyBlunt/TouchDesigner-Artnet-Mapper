"""Build the safe navigation shortcut hub in the running TouchDesigner project.

The shortcuts only open viewers. They never change effects, save the project,
or start/stop network output.
"""

from __future__ import annotations

import importlib
import sys


LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

import pixelblaze_mapper.shortcut_hub as _shortcut_hub_module  # noqa: E402
importlib.reload(_shortcut_hub_module)
from pixelblaze_mapper.shortcut_hub import SHORTCUTS, shortcut_rows, validate_shortcuts  # noqa: E402


PHOTO_PREVIEW = "/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype/prototype_out"
CANONICAL_PREVIEW = "/project1/LED_PREVIEW_OUT"


def _get_or_create(parent, op_type, name):
    return parent.op(name) or parent.create(op_type, name)


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _label(parent, name, text, x, y, width, height, color=(0.82, 0.88, 0.94), size=13):
    node = _get_or_create(parent, textCOMP, name)
    for parameter, value in (("x", x), ("y", y), ("w", width), ("h", height),
                             ("text", text), ("fontsize", size), ("fontcolorr", color[0]),
                             ("fontcolorg", color[1]), ("fontcolorb", color[2]),
                             ("bgalpha", 0), ("display", True),
                             ("align", "centerleft"), ("valign", "center")):
        _set(node, parameter, value)
    return node


def _callback_source():
    targets = {item.key.lower(): (item.label, item.target) for item in SHORTCUTS}
    return f'''# Generated safe navigation callbacks. No DMX or project-save actions.
TARGETS = {targets!r}

def keyEvent(dat, key, character, alt, lalt, ralt, ctrl, lctrl, rctrl, shift, lshift, rshift, state, time):
    key = str(key).lower()
    if not state or not ctrl or not shift or alt or key not in TARGETS:
        return
    label, path = TARGETS[key]
    target = op(path)
    if target is None:
        ui.status = 'Shortcut target missing: ' + path
        return
    target.openViewer()
    ui.status = label + ' | ' + path
    return

def shortcutEvent(dat, shortcutName, time):
    return
'''


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
    for parameter, value in (("w", 1120), ("h", 700), ("hmode", "fixed"), ("vmode", "fixed"),
                             ("bgcolorr", 0.008), ("bgcolorg", 0.014), ("bgcolorb", 0.023), ("bgalpha", 1)):
        _set(panel, parameter, value)
    _label(panel, "title", "TOUCHDESIGNER SHORTCUTS", 28, 640, 1060, 42, (0.91, 0.96, 1), 23)
    _label(panel, "safety", "Navigation only - no shortcut starts DMX or changes the selected effect.", 28, 600, 1060, 30, (0.35, 0.90, 0.67), 13)
    active_row_names = {
        prefix + item.key for item in SHORTCUTS for prefix in ("combo_", "name_", "purpose_")
    }
    for child in panel.children:
        if child.name.startswith(("combo_", "name_", "purpose_")) and child.name not in active_row_names:
            _set(child, "display", False)
    for index, item in enumerate(SHORTCUTS):
        y = 548 - index * 54
        _label(panel, "combo_" + item.key, item.combo, 28, y, 180, 38, (0.38, 0.76, 0.96), 15)
        _label(panel, "name_" + item.key, item.label, 220, y, 250, 38, (0.91, 0.96, 1), 14)
        _label(panel, "purpose_" + item.key, item.purpose, 480, y, 608, 38, (0.72, 0.79, 0.86), 12)
    _label(panel, "footer", "Tip: click an empty network area first. Text-entry fields can consume keyboard input.", 28, 22, 1060, 34, (0.97, 0.72, 0.26), 12)

    preview = _get_or_create(owner, opviewerTOP, "help_preview")
    _set(preview, "opviewer", panel.path)
    _set(preview, "allowpanel", True)
    _set(preview, "outputresolution", "custom")
    _set(preview, "resolutionw", 1120)
    _set(preview, "resolutionh", 700)

    readme = _get_or_create(owner, textDAT, "README")
    readme.text = "Safe navigation-only shortcuts. Source: pixelblaze_mapper/build_shortcut_hub.py"
    print({"owner": owner.path, "shortcuts": len(SHORTCUTS), "preview": photo_preview.path,
           "networkOutputTouched": False, "projectSaved": False})
    return owner


build()
