"""Build a draft editor with optional explicit Prepare/Apply/Revert hooks.

Call build(initial_path=...) inside TouchDesigner. Importing this module does
not build anything. Only /project1/layout_scene_editor is created/updated;
existing Mapper, active coordinates and routing are never rewired.
"""
from __future__ import annotations

from pathlib import Path

OWNER = "/project1/layout_scene_editor"
ROOT = str(Path(__file__).resolve().parents[1])

RUNTIME = '''import sys
ROOT = %r
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from pixelblaze_mapper import layout_scene_td as adapter
from pixelblaze_mapper import layout_fixture_td as fixtures
def owner(): return op(%r)
def action(name):
    def confirm(message):
        return ui.messageBox('Layout draft', message, buttons=['Continue', 'Cancel']) == 0
    return adapter.action(owner(), name, ui.chooseFile, confirm)
def refresh(): return adapter.refresh(owner())
def set_uv_source(value):
    if value not in ('current', 'projection'):
        raise ValueError('Unknown 3D material UV choice')
    owner().store('layout_uv_source', value)
    owner().store('ui_prepared_context', None)
    adapter.status(owner(), '3D geometry: KEEP EXISTING MATERIAL UV' if value == 'current' else '3D geometry + PROJECT MATERIAL UV using the selected Axes. Values must already fit 0..1.')
def drag(phase, camera=False): return adapter.drag(owner(), phase, camera=camera)
def key(name, ctrl=False): return adapter.key(owner(), name, ctrl=ctrl)
def fixture_drag(domain, phase): return fixtures.drag(owner(), domain, phase)
def accept_scan_request(request, scan):
    adapter.editor(owner()).accept_scan_request(request, scan)
    adapter.refresh(owner())
    adapter.status(owner(), 'SCAN MERGED TO DRAFT | Active LEDs unchanged')
def get_scene(): return adapter.editor(owner()).current.scene
def prepare_save():
    from pixelblaze_mapper.layout_session_storage import prepare_save as snapshot
    return snapshot(owner())
''' % (ROOT, OWNER)


def _node(parent, kind, name):
    node = parent.op(name)
    if node is None:
        node = parent.create(kind, name)
        node.name = name
    return node


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _panel(node, x, y, w, h, layer=10):
    for name, value in (("x", x), ("y", y), ("w", w), ("h", h),
                        ("layer", layer), ("hmode", "fixed"), ("vmode", "fixed"),
                        ("display", True), ("enable", True)):
        _set(node, name, value)
    return node


def _text(parent, name, text, x, y, w, h, size=12):
    node = _panel(_node(parent, textCOMP, name), x, y, w, h, 20)
    for key, value in (("text", text), ("fontsize", size), ("wordwrap", True),
                       ("type", "multiline"), ("alignx", "left"), ("aligny", "center"),
                       ("bgalpha", 0), ("fontcolorr", .82), ("fontcolorg", .9),
                       ("fontcolorb", .96), ("clickthrough", True)):
        _set(node, key, value)
    return node


def _field(panel, name, label, default, x, y, width=175):
    _text(panel, name + "_label", label, x, y + 29, width, 22, 11)
    node = _panel(_node(panel, fieldCOMP, name), x, y, width, 28, 40)
    _set(node, "fieldtype", "string")
    _set(node, "bgalpha", 1)
    _set(node, "fontalpha", 1)
    value = node.op("string")
    if value is not None and (not value.text.strip() or value.text.strip().casefold() == "field"):
        value.text = str(default)
    return node


def _button(owner, panel, name, label, x, y, w=120):
    node = _panel(_node(panel, buttonCOMP, "btn_" + name), x, y, w, 32, 40)
    for key, value in (("label", label), ("buttontype", "momentary"), ("fontsize", 11),
                       ("bgcolorr", .04), ("bgcolorg", .17), ("bgcolorb", .24)):
        _set(node, key, value)
    callback = _node(owner, panelexecuteDAT, "click_" + name)
    callback.par.active = False
    callback.par.panels = node.path
    callback.par.fromop = node.path
    callback.par.panelvalue = "lselect"
    callback.par.offtoon = True
    callback.par.ontooff = False
    callback.par.valuechange = False
    _set(callback, "whileon", False)
    _set(callback, "whileoff", False)
    callback.text = "def onOffToOn(panelValue):\n    op(%r).module.action(%r)\n    return\n" % (OWNER + "/runtime", name)
    callback.par.active = True


def _only_led_shape(geometry, shape):
    """Disable auto-created torus/other child drawing without deleting any data."""
    children = tuple(geometry.children)
    if shape not in children:
        raise RuntimeError("LED shape must belong to the editor geometry")
    for child in children:
        if child != shape:
            for flag in ("display", "render"):
                if hasattr(child, flag):
                    setattr(child, flag, False)
    shape.display, shape.render = True, True


def _fixture_canvas(owner, panel, domain, x):
    """Two explicit domains; normalized display never changes stored points."""
    parent = _panel(_node(panel, containerCOMP, "fixtures_" + domain), x, 280, 370, 500)
    _text(parent, "title", "OUTPUT FIXTURE LAYOUT" if domain == "output" else "MATERIAL SAMPLING UV (0..1)", 5, 478, 360, 22, 12)
    _text(parent, "info", "", 5, 5, 360, 108, 11)
    prefix = "fixture_" + domain
    callbacks = _node(owner, textDAT, prefix + "_callbacks")
    callbacks.text = ("import sys\nif %r not in sys.path: sys.path.insert(0, %r)\n"
                      "from pixelblaze_mapper import layout_fixture_td\n"
                      "def onCook(scriptOp):\n    layout_fixture_td.cook(op(%r), scriptOp, %r)\n    return\n") % (ROOT, ROOT, OWNER, domain)
    instances = _node(owner, scriptCHOP, prefix + "_instances")
    instances.par.callbacks = callbacks.path
    geometry = _node(owner, geometryCOMP, prefix + "_geometry")
    shape = _node(geometry, boxSOP, "led_shape")
    _only_led_shape(geometry, shape)
    for axis in "xyz":
        getattr(shape.par, "size" + axis).val = .007
    geometry.par.material = owner.op("led_material").path
    geometry.par.instancing = True
    geometry.par.instanceop, geometry.par.instancecolorop = instances.path, instances.path
    for axis in "xyz":
        getattr(geometry.par, "instancet" + axis).val = "t" + axis
    for channel in "rgba":
        _set(geometry, "instance" + channel, channel)
    camera = _node(owner, cameraCOMP, prefix + "_camera")
    target = _node(owner, nullCOMP, prefix + "_target")
    camera.par.tx, camera.par.ty, camera.par.tz = .5, .5, 2
    target.par.tx, target.par.ty, target.par.tz = .5, .5, 0
    camera.par.lookat = target.path
    camera.par.projection = "ortho"
    camera.par.orthowidth = 1.0
    render = _node(owner, renderTOP, prefix + "_render")
    render.par.camera, render.par.geometry = camera.path, geometry.path
    render.par.resolutionw, render.par.resolutionh = 360, 360
    _set(render, "outputresolution", "custom")
    _set(render, "lights", "")
    _set(render, "bgcolora", 0)
    displayed = render
    # Read-only material preview input. No sampling/output consumer is rewired.
    if domain == "uv" and op("/project1/res1") is not None:
        background = _node(owner, selectTOP, "fixture_material_preview")
        background.par.top = "/project1/res1"
        composite = _node(owner, overTOP, "fixture_uv_preview")
        composite.inputConnectors[0].connect(render)
        composite.inputConnectors[1].connect(background)
        displayed = composite
    viewport = _panel(_node(parent, containerCOMP, "viewport"), 5, 115, 360, 360)
    viewport.par.top = displayed.path
    _set(viewport, "bgalpha", 1)
    callback = _node(owner, panelexecuteDAT, "drag_" + prefix)
    callback.par.panels, callback.par.fromop = viewport.path, viewport.path
    callback.par.panelvalue = "lselect"
    callback.par.offtoon, callback.par.ontooff, callback.par.valuechange = True, True, False
    callback.text = ("def onOffToOn(panelValue):\n    op(%r).module.fixture_drag(%r, 'start')\n    return\n"
                     "def onOnToOff(panelValue):\n    op(%r).module.fixture_drag(%r, 'end')\n    return\n") % (OWNER + "/runtime", domain, OWNER + "/runtime", domain)
    callback.par.active = True
    move = _node(owner, panelexecuteDAT, "drag_" + prefix + "_motion")
    move.par.panels, move.par.fromop = viewport.path, viewport.path
    move.par.panelvalue, move.par.valuechange = "u v", True
    move.par.offtoon, move.par.ontooff = False, False
    move.text = "def onValueChange(panelValue, prev):\n    if op(%r).panel.lselect: op(%r).module.fixture_drag(%r, 'update')\n    return\n" % (viewport.path, OWNER + "/runtime", domain)
    move.par.active = True
    parent.par.display = False
    return viewport


def build(initial_path=""):
    """Create the editor, preserving its persistent draft and field values."""
    project = op("/project1")
    if project is None:
        raise RuntimeError("/project1 is missing")
    owner = _node(project, baseCOMP, "layout_scene_editor")
    # Disable existing callbacks during a rebuild; no production paths touched.
    for child in owner.children:
        if child.name.startswith(("click_", "drag_", "keyboard")) and hasattr(child.par, "active"):
            child.par.active = False
    runtime = _node(owner, textDAT, "runtime")
    runtime.text = RUNTIME
    draft = _node(owner, textDAT, "draft_document")
    _node(owner, textDAT, "fixture_document")
    panel = _panel(_node(owner, containerCOMP, "ui_panel"), 0, 0, 1440, 960)
    for key, value in (("bgcolorr", .009), ("bgcolorg", .017), ("bgcolorb", .025), ("bgalpha", 1)):
        _set(panel, key, value)
    _text(panel, "title", "3D LAYOUT + 2D FIXTURES  |  DRAFT WORKSPACE", 20, 915, 1080, 34, 22)
    _button(owner, panel, "loadactive", "LOAD ACTIVE SNAPSHOT", 1110, 915, 300)
    _text(panel, "draft_badge", "DRAFT ONLY — ACTIVE UNCHANGED", 20, 878, 1360, 28, 14)
    for name, label, x, width in (
        ("loadcurrent", "LOAD CURRENT FILE", 20, 170), ("openscene", "OPEN SCENE", 200, 125),
        ("append", "APPEND SCAN", 335, 130), ("replace", "REPLACE REGION", 475, 145),
        ("undo", "UNDO", 630, 85), ("redo", "REDO", 725, 85),
        ("frame", "FRAME / RESET VIEW", 820, 180), ("scan", "GUIDED SCAN", 1010, 150),
        ("fituv", "FIT UV", 1170, 100), ("exportuv", "EXPORT UV", 1280, 130),
    ):
        _button(owner, panel, name, label, x, 832, width)

    # Rendering uses conversion-only display coordinates: user(Y,X,-Z).
    callbacks = _node(owner, textDAT, "instances_callbacks")
    callbacks.text = "import sys\nif %r not in sys.path: sys.path.insert(0, %r)\nfrom pixelblaze_mapper import layout_scene_td\ndef onCook(scriptOp):\n    layout_scene_td.cook_instances(op(%r), scriptOp)\n    return\n" % (ROOT, ROOT, OWNER)
    instances = _node(owner, scriptCHOP, "instances")
    instances.par.callbacks = callbacks.path
    geometry = _node(owner, geometryCOMP, "led_geometry")
    shape = _node(geometry, boxSOP, "led_shape")
    _only_led_shape(geometry, shape)
    material = _node(owner, constantMAT, "led_material")
    geometry.par.material = material.path
    geometry.par.instancing = True
    geometry.par.instanceop = instances.path
    geometry.par.instancecolorop = instances.path
    for axis in "xyz":
        getattr(geometry.par, "instancet" + axis).val = "t" + axis
    for channel in "rgb":
        getattr(geometry.par, "instance" + channel).val = channel
    _set(geometry, "instancea", "a")
    camera = _node(owner, cameraCOMP, "camera")
    target = _node(owner, nullCOMP, "camera_target")
    camera.par.lookat = target.path
    render = _node(owner, renderTOP, "scene_render")
    render.par.camera = camera.path
    render.par.geometry = geometry.path
    render.par.resolutionw, render.par.resolutionh = 760, 500
    _set(render, "outputresolution", "custom")
    _set(render, "lights", "")
    viewport = _panel(_node(panel, containerCOMP, "viewport"), 20, 280, 760, 500, 10)
    viewport.par.top = render.path
    viewport.par.uvbuttonsright = True
    viewport.par.mousewheel = True
    _set(viewport, "bgcolorr", .015)
    _set(viewport, "bgalpha", 1)
    _button(owner, panel, "view3d", "3D LAYOUT", 20, 790, 140)
    _button(owner, panel, "view2d", "2D FIXTURES", 170, 790, 150)
    _text(panel, "projection_label", "Axes", 330, 793, 45, 24, 10)
    projection = _panel(_node(panel, fieldCOMP, "projection"), 375, 790, 55, 28, 40)
    _set(projection, "fieldtype", "string")
    if projection.op("string") is not None and projection.op("string").text.strip().lower() in ("", "field"):
        projection.op("string").text = "YX"
    _text(panel, "fixturerange_label", "2D local LEDs (blank = whole object)", 440, 817, 330, 14, 10)
    fixture_range = _panel(_node(panel, fieldCOMP, "fixturerange"), 440, 790, 160, 28, 40)
    _set(fixture_range, "fieldtype", "string")
    if fixture_range.op("string") is not None and fixture_range.op("string").text.strip().lower() == "field":
        fixture_range.op("string").text = ""
    _button(owner, panel, "project2d", "PROJECT RANGE TO 2D", 610, 790, 170)
    for name, label, value, x, width in (
            ('uv_current', '3D: KEEP EXISTING MATERIAL UV', 'current', 810, 365),
            ('uv_projection', '3D: PROJECT UV (AXES)', 'projection', 1185, 225)):
        _button(owner, panel, name, label, x, 790, width)
        owner.op('click_' + name).text = "def onOffToOn(panelValue):\n    op(%r).module.set_uv_source(%r)\n" % (runtime.path, value)
        control = panel.op('btn_' + name)
        selected = "op(%r).fetch('layout_uv_source', 'current') == %r" % (owner.path, value)
        control.par.colorr.expr = '0.3 if ' + selected + ' else 0.75'
        control.par.colorg.expr = '0.85'
        control.par.colorb.expr = '1.0 if ' + selected + ' else 0.95'
    fixture_views = [_fixture_canvas(owner, panel, "output", 20), _fixture_canvas(owner, panel, "uv", 410)]
    _text(panel, "axes", "X = HEIGHT | Y = RIGHT | Z = BACK. RMB drag: orbit VIEW. Wheel: zoom VIEW.\nLMB drag / arrows: CHANGE selected object. Page Up/Down: Z. Ctrl+Z/Y: undo/redo.\nFRAME / RESET VIEW resets camera only. View buttons never move LEDs.",
          20, 180, 760, 56, 11)
    for name, label, x, method, value in (
            ('orbit_left', 'VIEW LEFT', 20, 'orbit_view', -15),
            ('orbit_right', 'VIEW RIGHT', 180, 'orbit_view', 15),
            ('zoom_in', 'ZOOM +', 340, 'zoom_view', 1),
            ('zoom_out', 'ZOOM -', 500, 'zoom_view', -1)):
        _button(owner, panel, name, label, x, 240, 150)
        owner.op('click_' + name).text = "def onOffToOn(panelValue):\n    op(%r).module.adapter.%s(op(%r), %r)\n" % (runtime.path, method, owner.path, value)
    _text(panel, "objects", "", 20, 72, 760, 105, 11)
    _text(panel, "provenance", "", 810, 150, 600, 55, 11)

    fields = (
        ("initialfile", "Current layout file (read only)", initial_path, 810, 745, 600),
        ("format", "Import format: auto / marimapper-csv / pixelblaze", "auto", 810, 676, 285),
        ("objectname", "New object / scan name", "", 1110, 676, 300),
        ("sourcestart", "Explicit global source start", "0", 810, 607, 285),
        ("scanrange", "Original scan indices (blank = all)", "", 1110, 607, 300),
        ("localrange", "LOCAL LEDs: scan / replace (blank scan = all)", "", 810, 538, 285),
        ("expectedcount", "Expected final count (blank = any)", "", 1110, 538, 170),
        ("objectno", "Object number", "1", 810, 469, 110),
        ("mode", "Drag/key mode: move,rotate,scale", "move", 980, 469, 190),
        ("axis", "Rotate/scale axis: x,y,z", "z", 1180, 469, 110),
        ("step", "Key step (units/degrees)", "0.01", 1300, 469, 110),
        ("controller", "Controller identity (draft intent)", "", 810, 242, 285),
        ("port", "Physical port", "1", 1110, 242, 110),
    )
    for args in fields:
        _field(panel, *args)
    for row, (prefix, label, default) in enumerate((("t", "Translate", "0"), ("r", "Rotate degrees", "0"), ("s", "Scale", "1"))):
        for column, axis in enumerate("xyz"):
            _field(panel, prefix + axis, label + " " + axis.upper(), default, 810 + column * 202, 402 - row * 53, 190)
    _button(owner, panel, "select", "SELECT", 925, 469, 50)
    _button(owner, panel, "count", "SET COUNT", 1290, 538, 120)
    _button(owner, panel, "transform", "SET TRANSFORM", 810, 205, 170)
    _button(owner, panel, "route", "BIND ROUTE DRAFT", 1110, 205, 300)
    for name, label, x, width in (("exportscene", "EXPORT WORKSPACE", 810, 195),
                                 ("exportpb", "EXPORT PIXELBLAZE 3D", 1015, 195),
                                 ("prepare", "VALIDATE / PREPARE", 1220, 190)):
        _button(owner, panel, name, label, x, 112, width)
    opt_in = _panel(_node(panel, fieldCOMP, "preserverouting"), 810, 65, 70, 28, 40)
    _set(opt_in, "fieldtype", "string")
    if opt_in.op("string") is not None:
        # Rebuild always revokes consent, while preserving the entire workspace.
        opt_in.op("string").text = "NO"
    owner.store("ui_prepared_context", None)
    _text(panel, "routing_opt_in", "Keep live routes: YES / NO\nDraft routes are NOT applied", 890, 62, 225, 42, 10)
    _button(owner, panel, "apply", "APPLY (OUTPUT OFF)", 1120, 65, 140)
    _button(owner, panel, "revert", "REVERT LAST", 1270, 65, 140)
    _text(panel, "status", "Draft ready | Active apply requires separate reviewed runtime + output OFF + routing opt-in", 20, 8, 1390, 44, 12)

    for camera_drag, name, value in ((False, "object", "lselect"), (True, "camera", "rselect")):
        callback = _node(owner, panelexecuteDAT, "drag_" + name)
        callback.par.panels = viewport.path
        callback.par.fromop = viewport.path
        callback.par.panelvalue = value
        callback.par.offtoon, callback.par.ontooff = True, True
        callback.par.valuechange = False
        callback.text = ("def onOffToOn(panelValue):\n    op(%r).module.drag('start', camera=%r)\n    return\n"
                         "def onOnToOff(panelValue):\n    op(%r).module.drag('end', camera=%r)\n    return\n") % (
                             runtime.path, camera_drag, runtime.path, camera_drag)
        callback.par.active = True
    move = _node(owner, panelexecuteDAT, "drag_motion")
    move.par.panels, move.par.fromop = viewport.path, viewport.path
    move.par.panelvalue = "u v"
    move.par.valuechange = True
    move.par.offtoon, move.par.ontooff = False, False
    move.text = "def onValueChange(panelValue, prev):\n    panel=op(%r).panel\n    if panel.lselect: op(%r).module.drag('update', camera=False)\n    elif panel.rselect: op(%r).module.drag('update', camera=True)\n    return\n" % (viewport.path, runtime.path, runtime.path)
    move.par.active = True
    wheel = _node(owner, panelexecuteDAT, 'view_wheel')
    wheel.par.panels, wheel.par.fromop = viewport.path, viewport.path
    wheel.par.panelvalue = 'wheel'
    wheel.par.offtoon, wheel.par.ontooff = False, False
    wheel.par.valuechange = True
    wheel.text = "def onValueChange(panelValue, prev):\n    if float(panelValue): op(%r).module.adapter.zoom_view(op(%r), float(panelValue))\n" % (runtime.path, owner.path)
    wheel.par.active = True
    keys = _node(owner, keyboardinDAT, "keyboard")
    keyboard_callback = _node(owner, textDAT, "keyboard_callbacks")
    keyboard_callback.text = "def keyEvent(dat,key,character,alt,lalt,ralt,ctrl,lctrl,rctrl,shift,lshift,rshift,state,time):\n    if state and not alt:\n        op(%r).module.key(key,ctrl=ctrl)\n    return\ndef shortcutEvent(dat,shortcutName,time):\n    return\n" % runtime.path
    keys.par.keys = "up down left right pageup pagedown z y escape"
    keys.par.panels = viewport.path + " " + " ".join(v.path for v in fixture_views)
    keys.par.callbacks = keyboard_callback.path
    keys.par.perform = False
    keys.par.active = True
    readme = _node(owner, textDAT, "README")
    readme.text = "Draft layout editor. Optional /project1/layout_apply/runtime exposes explicit Prepare/Apply/Revert; output must be OFF and live routing preserved. Builder never applies. User axes X height/Y right/Z back. See docs/LAYOUT_SCENE_EDITOR_DE.md."
    runtime.module.refresh()
    runtime.module.adapter.frame_view(owner, reset=True)
    runtime.module.fixtures.frame_output(owner)
    runtime.module.action("view2d" if owner.fetch("layout_view", "3d") == "2d" else "view3d")
    runtime.module.prepare_save()
    panel.viewer = True
    return {"owner": owner.path, "target": panel.path, "activeModified": False,
            "routeModified": False, "applyInstalled": op("/project1/layout_apply/runtime") is not None, "projectSaved": False}
