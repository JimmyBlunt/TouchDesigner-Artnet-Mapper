"""Build the read-only Output Config summary (shortcut 7).

The Art-Net Router at ``/project1/multi_controller_output`` is the single
editable output configuration. This builder recreates only dialog 7 as an
idempotent live summary and provides one navigation button to that Router.
It never mutates Router tables, starts output, touches hardware, or saves the
TouchDesigner project.
"""

from __future__ import annotations


ROOT = "/project1/pixelblaze_mapper"
OWNER = ROOT + "/output_config"
ROUTER = "/project1/multi_controller_output"


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _fixed(node, x, y, width, height, layer=0):
    for name, value in (
        ("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
        ("w", width), ("h", height), ("layer", layer), ("display", True),
    ):
        _set(node, name, value)
    return node


def _create(parent, op_type, name):
    node = parent.create(op_type, name)
    node.name = name
    return node


def _text(parent, name, value, x, y, width, height, *, size=14,
          color=(0.76, 0.84, 0.91), align="left"):
    node = _fixed(_create(parent, textCOMP, name), x, y, width, height, 10)
    for parameter, item in (
        ("text", value), ("type", "multiline"), ("wordwrap", True),
        ("font", "Verdana"), ("fontsize", size), ("fontalpha", 1),
        ("fontcolorr", color[0]), ("fontcolorg", color[1]), ("fontcolorb", color[2]),
        ("bgcolorr", 0.018), ("bgcolorg", 0.027), ("bgcolorb", 0.040),
        ("bgalpha", 1), ("alignx", align), ("aligny", "center"),
        ("textpaddingl", 12), ("textpaddingr", 12), ("clickthrough", True),
    ):
        _set(node, parameter, item)
    return node


def _button(parent, name, label, x, y, width, height):
    node = _fixed(_create(parent, buttonCOMP, name), x, y, width, height, 20)
    for parameter, item in (
        ("label", label), ("buttontype", "momentary"), ("fontsize", 13),
        ("fontalpha", 1), ("fontcolorr", 0.92), ("fontcolorg", 0.96),
        ("fontcolorb", 1.0), ("bgcolorr", 0.06), ("bgcolorg", 0.18),
        ("bgcolorb", 0.27), ("bgalpha", 1), ("cursor", "pointer"),
    ):
        _set(node, parameter, item)
    return node


def _runtime_source():
    return r'''import sys
import time

PROJECT_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pixelblaze_mapper.output_config_summary import build_output_summary, display_rows

OWNER = op('/project1/pixelblaze_mapper/output_config')
ROUTER = op('/project1/multi_controller_output')
_last_update = 0.0

def _rows(table):
    if table is None or table.numRows < 1:
        return []
    headers = [str(table[0, column]) for column in range(table.numCols)]
    return [
        {headers[column]: str(table[row, column]) for column in range(table.numCols)}
        for row in range(1, table.numRows)
    ]

def _sender_status():
    sender = ROUTER.op('artnet_510_sender_callbacks') if ROUTER is not None else None
    if sender is None:
        return {'enabled': False, 'mode': 'unavailable', 'error': 'sender status unavailable', 'controllers': []}
    try:
        return sender.module.status()
    except Exception as error:
        return {'enabled': False, 'mode': 'error', 'error': str(error), 'controllers': []}

def update(force=False):
    global _last_update
    now = time.monotonic()
    if not force and now - _last_update < 0.25:
        return
    _last_update = now
    source = op('/project1/math1')
    summary = build_output_summary(
        _rows(ROUTER.op('controller_config') if ROUTER else None),
        _rows(ROUTER.op('segment_config') if ROUTER else None),
        _sender_status(),
        source_pixels=int(source.numSamples) if source is not None else None,
        validation_rows=_rows(ROUTER.op('validation') if ROUTER else None),
    )
    rows = display_rows(summary)
    values = dict(rows)
    OWNER.op('ui_panel/state_value').par.text = values.get('STATE', 'UNAVAILABLE')
    OWNER.op('ui_panel/source_value').par.text = values.get('SOURCE', 'unavailable')
    OWNER.op('ui_panel/sender_value').par.text = values.get('SENDER', 'unavailable')
    controller_lines = ['%s\n%s' % (key, value) for key, value in rows
                        if key not in ('STATE', 'SOURCE', 'SENDER', 'VALIDATION')]
    OWNER.op('ui_panel/controllers_value').par.text = '\n\n'.join(controller_lines) or 'No controller rows available'
    OWNER.op('ui_panel/validation_value').par.text = values.get('VALIDATION', 'unavailable')

def open_router():
    target = op('/project1/multi_controller_output/ui_panel')
    if target is None:
        raise RuntimeError('Art-Net Router UI is missing')
    target.openViewer()
    return True
'''


def build():
    root = op(ROOT)
    if root is None:
        raise RuntimeError(ROOT + " is missing")

    # Recreate only this isolated COMP. This removes legacy draft fields and
    # duplicate handlers while preserving the public shortcut target path.
    old = op(OWNER)
    if old is not None:
        old.destroy()
    owner = _create(root, baseCOMP, "output_config")
    owner.nodeX, owner.nodeY = 750, -300

    canvas = _create(owner, containerCOMP, "ui_panel")
    for name, value in (
        ("hmode", "fixed"), ("vmode", "fixed"), ("w", 1100), ("h", 650),
        ("bgcolorr", 0.009), ("bgcolorg", 0.015), ("bgcolorb", 0.024), ("bgalpha", 1),
    ):
        _set(canvas, name, value)
    canvas.viewer = True

    _text(canvas, "title", "OUTPUT CONFIG | LIVE SUMMARY", 20, 590, 1060, 44,
          size=23, color=(0.94, 0.97, 1.0))
    _text(canvas, "notice", "READ ONLY · Edit output settings only in the Art-Net Router",
          20, 542, 1060, 34, size=13, color=(0.35, 0.90, 0.67), align="center")
    _text(canvas, "state_label", "OUTPUT STATE", 20, 474, 200, 38,
          color=(0.38, 0.76, 0.96))
    _text(canvas, "state_value", "UNAVAILABLE", 230, 474, 270, 38)
    _text(canvas, "source_label", "LIVE SOURCE", 520, 474, 180, 38,
          color=(0.38, 0.76, 0.96))
    _text(canvas, "source_value", "unavailable", 710, 474, 370, 38)
    _text(canvas, "sender_label", "SENDER", 20, 420, 200, 38,
          color=(0.38, 0.76, 0.96))
    _text(canvas, "sender_value", "unavailable", 230, 420, 850, 38)
    _text(canvas, "controllers_label", "CONTROLLERS · LIVE ROUTER TABLE + SENDER STATE",
          20, 360, 1060, 36, color=(0.38, 0.76, 0.96))
    _text(canvas, "controllers_value", "No controller rows available", 20, 142, 1060, 210, size=13)
    _text(canvas, "validation_label", "VALIDATION", 20, 92, 200, 38,
          color=(0.38, 0.76, 0.96))
    _text(canvas, "validation_value", "unavailable", 230, 92, 490, 38)
    router_button = _button(canvas, "open_router", "OPEN ART-NET ROUTER", 750, 82, 330, 48)
    _text(canvas, "source_note",
          "Values are derived from /project1/math1 and Router-owned live tables. No editable copies exist here.",
          20, 24, 1060, 42, size=12, color=(0.68, 0.76, 0.84), align="center")

    runtime = _create(owner, textDAT, "live_summary_runtime")
    runtime.text = _runtime_source()
    execute = _create(owner, executeDAT, "live_summary_execute")
    execute.par.active = True
    execute.par.framestart = True
    execute.text = (
        "def onFrameStart(frame):\n"
        "    if int(frame) % 15:\n"
        "        return\n"
        "    op('live_summary_runtime').module.update()\n"
        "    return\n"
    )
    click = _create(owner, panelexecuteDAT, "open_router_click")
    click.par.active = True
    click.par.fromop = router_button.path
    click.par.panels = router_button.path
    click.par.panelvalue = "state"
    click.par.offtoon = True
    click.par.valuechange = False
    click.text = "def onOffToOn(panelValue):\n    op('live_summary_runtime').module.open_router()\n    return\n"

    preview = _create(owner, opviewerTOP, "ui_preview")
    _set(preview, "opviewer", canvas.path)
    _set(preview, "allowpanel", True)
    _set(preview, "outputresolution", "custom")
    _set(preview, "resolutionw", 1100)
    _set(preview, "resolutionh", 650)
    preview.viewer = True

    readme = _create(owner, textDAT, "README_output_config")
    readme.text = """Read-only live output summary (shortcut 7).

Single editable authority: /project1/multi_controller_output (Art-Net Router).
Live sources: /project1/math1, Router controller/segment/validation tables,
and artnet_510_sender_callbacks.status(). Derived fields are labels, not
editable parameters. This builder never starts output or saves the project.
"""
    runtime.module.update(force=True)
    print({"owner": owner.path, "mode": "read-only live summary",
           "editableAuthority": ROUTER, "networkOutputChanged": False,
           "projectSaved": False})
    return owner


if "op" in globals():
    result = build()
