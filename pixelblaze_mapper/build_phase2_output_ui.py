"""Idempotent TouchDesigner builder for isolated Phase 2 OUTPUT(DMX) UI.

Run inside TouchDesigner, for example from a Text DAT:

    exec(open(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/'
              r'pixelblaze_mapper/build_phase2_output_ui.py').read())

The builder only creates/updates /project1/pixelblaze_mapper/output_config.
It never writes production DMX nodes and never calls project.save().
"""

from __future__ import annotations

import sys


ROOT = "/project1/pixelblaze_mapper"
OWNER = ROOT + "/output_config"
CANVAS = OWNER + "/ui_panel"
LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)


def _get_or_create(parent, op_type, name):
    node = op(parent.path + "/" + name)
    if node is None:
        node = parent.create(op_type, name)
    return node


def _page(owner):
    for item in owner.customPages:
        if item.name == "Output DMX":
            return item
    return owner.appendCustomPage("Output DMX")


def _parameter(owner, page, name, kind, label, default=None, menu=None):
    existing = getattr(owner.par, name, None)
    if existing is not None:
        return existing
    if kind == "str":
        result = page.appendStr(name, label=label)[0]
    elif kind == "int":
        result = page.appendInt(name, label=label)[0]
    elif kind == "toggle":
        result = page.appendToggle(name, label=label)[0]
    elif kind == "pulse":
        result = page.appendPulse(name, label=label)[0]
    elif kind == "menu":
        result = page.appendMenu(name, label=label)[0]
        result.menuNames = [item[0] for item in menu]
        result.menuLabels = [item[1] for item in menu]
    else:
        raise ValueError(kind)
    if default is not None and kind != "pulse":
        result.val = default
    return result


def _fixed(node, x, y, width, height, layer=0):
    node.par.hmode = "fixed"
    node.par.vmode = "fixed"
    node.par.x = x
    node.par.y = y
    node.par.w = width
    node.par.h = height
    node.par.layer = layer
    node.par.display = True


def _panel(canvas, name, x, y, width, height, rgb, border=(0.12, 0.2, 0.3)):
    node = _get_or_create(canvas, containerCOMP, name)
    _fixed(node, x, y, width, height)
    node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = rgb
    node.par.bgalpha = 1
    node.par.leftborder = "bordera"
    node.par.rightborder = "bordera"
    node.par.topborder = "bordera"
    node.par.bottomborder = "bordera"
    node.par.borderar, node.par.borderag, node.par.borderab = border
    node.par.borderaalpha = 1
    return node


def _text(canvas, name, value, x, y, width, height, size=15,
          color=(0.75, 0.82, 0.9), bg=(0, 0, 0), alpha=0,
          align="left", bold=False, expression=None):
    node = _get_or_create(canvas, textCOMP, name)
    _fixed(node, x, y, width, height, layer=10)
    node.par.text = value
    if expression:
        node.par.text.expr = expression
    node.par.type = "multiline"
    node.par.wordwrap = True
    node.par.font = "Verdana"
    node.par.fontsize = size
    node.par.bold = bold
    node.par.fontcolorr, node.par.fontcolorg, node.par.fontcolorb = color
    node.par.fontalpha = 1
    node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = bg
    node.par.bgalpha = alpha
    node.par.alignx = align
    node.par.aligny = "center"
    node.par.textpaddingl = 10
    node.par.textpaddingr = 10
    node.par.textpaddingt = 4
    node.par.textpaddingb = 4
    node.par.clickthrough = True
    return node


def _button(canvas, name, label, x, y, width, height, enabled=True, warning=False):
    node = op(canvas.path + "/" + name)
    if node is None:
        node = canvas.create(buttonCOMP, name)
    _fixed(node, x, y, width, height, layer=20)
    node.par.label = label
    node.par.buttontype = "momentary"
    node.par.fontsize = 13
    node.par.enable = enabled
    node.par.cursor = "pointer" if enabled else "arrow"
    if warning:
        bg, border = (0.19, 0.075, 0.04), (0.95, 0.36, 0.14)
    elif enabled:
        bg, border = (0.06, 0.12, 0.17), (0.25, 0.52, 0.68)
    else:
        bg, border = (0.055, 0.06, 0.07), (0.17, 0.18, 0.20)
    node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = bg
    node.par.bgalpha = 1
    node.par.leftborder = "bordera"
    node.par.rightborder = "bordera"
    node.par.topborder = "bordera"
    node.par.bottomborder = "bordera"
    node.par.borderar, node.par.borderag, node.par.borderab = border
    node.par.borderaalpha = 1
    if not enabled:
        node.par.dodisablecolor = True
        node.par.disablecolorr = 0.42
        node.par.disablecolorg = 0.44
        node.par.disablecolorb = 0.46
        node.par.disablealpha = 0.62
    return node


def _fill_live_tables(owner, allocation=None, allocator_status="allocator pending"):
    live = _get_or_create(owner, tableDAT, "config_live")
    live.clear()
    live.appendRow(["key", "value"])
    for key, value in (
        ("state", "LIVE"), ("pixel_count", 3714), ("pixel_format", "rgb"),
        ("channel_order", "GRB"), ("start_universe", 0),
        ("start_channel", 1), ("universe_count", 22),
        ("last_universe_pixels", 144), ("target_address", "10.0.0.244"),
        ("local_address", "10.0.0.173"), ("port", 6454), ("rate", 30),
        ("art_sync", 1), ("source", "read-only verified baseline"),
    ):
        live.appendRow([key, value])

    draft = _get_or_create(owner, tableDAT, "config_draft")
    draft.clear()
    for row in range(live.numRows):
        draft.appendRow([str(live[row, col]) for col in range(live.numCols)])
    draft.appendRow(["allocator", allocator_status])

    universe_live = _get_or_create(owner, tableDAT, "universe_live")
    universe_live.clear()
    universe_live.appendRow([
        "channel", "logical", "net", "subnet", "universe", "pixel_start",
        "pixel_count", "dmx_range", "state",
    ])
    for logical in range(22):
        count = 170 if logical < 21 else 144
        universe_live.appendRow([
            "Universe" + str(logical), logical, logical // 256,
            (logical // 16) % 16, logical % 16, logical * 170, count,
            "1-" + str(count * 3), "LIVE",
        ])

    universe_draft = _get_or_create(owner, tableDAT, "universe_draft")
    universe_draft.clear()
    universe_draft.appendRow([
        "channel", "logical", "net", "subnet", "universe", "pixel_start",
        "pixel_count", "dmx_range", "state",
    ])
    if allocation is None:
        for row in range(1, universe_live.numRows):
            values = [str(universe_live[row, col]) for col in range(universe_live.numCols)]
            values[-1] = "BASELINE ONLY"
            universe_draft.appendRow(values)
    else:
        for row in allocation.rows:
            universe_draft.appendRow([
                row.channel, row.logical, row.net, row.subnet, row.universe,
                row.pixel_start, row.pixel_count,
                str(row.dmx_start) + "-" + str(row.dmx_end), "MATCHES LIVE",
            ])

    validation = _get_or_create(owner, tableDAT, "validation")
    validation.clear()
    validation.appendRow(["severity", "code", "field", "message"])
    if allocation is None:
        validation.appendRow([
            "INFO", "ALLOCATOR_PENDING", "Allocatorstatus",
            "Shared pure Python allocator not bound; baseline is read-only.",
        ])
    else:
        validation.appendRow([
            "OK", "ALLOCATOR_BOUND", "Allocatorstatus",
            allocator_status + " generated the draft universe preview.",
        ])
    validation.appendRow([
        "BLOCKED", "INTEGRATION_LOCKED", "Reviewapply",
        "Review/Apply remains disabled until transaction controller approval.",
    ])


def build():
    root = op(ROOT)
    if root is None:
        raise RuntimeError(ROOT + " is missing")
    owner = _get_or_create(root, baseCOMP, "output_config")
    owner.nodeX = 750
    owner.nodeY = -300
    page = _page(owner)

    definitions = (
        ("Enabled", "toggle", "Output Enabled", True, None),
        ("Pixelcount", "int", "Pixel Count", 3714, None),
        ("Pixelformat", "menu", "Pixel Format", "rgb", (("rgb", "RGB (3 ch)"),)),
        ("Channelorder", "menu", "Channel Order", "grb", tuple((x.lower(), x) for x in ("RGB", "RBG", "GRB", "GBR", "BRG", "BGR"))),
        ("Autoallocate", "toggle", "Auto Allocate", True, None),
        ("Startuniverse", "int", "Start Universe", 0, None),
        ("Startchannel", "int", "Start Channel", 1, None),
        ("Protocol", "menu", "Protocol", "artnet_unicast", (("artnet_unicast", "Art-Net Unicast"), ("artnet_broadcast", "Art-Net Broadcast"))),
        ("Targetaddress", "str", "Target Address", "10.0.0.244", None),
        ("Localaddress", "str", "Local Address", "10.0.0.173", None),
        ("Port", "int", "UDP Port", 6454, None),
        ("Rate", "int", "Frame Rate", 30, None),
        ("Priority", "int", "Priority", 100, None),
        ("Artsync", "toggle", "ArtSync", True, None),
        ("Universesrequired", "int", "Universes Required", 22, None),
        ("Lastuniversepixels", "int", "Last Universe Pixels", 144, None),
        ("Draftstate", "str", "Draft State", "MATCHES LIVE", None),
        ("Validationstate", "str", "Validation State", "BLOCKED", None),
        ("Allocatorstatus", "str", "Allocator Status", "PENDING SHARED ADAPTER", None),
        ("Revertdraft", "pulse", "Revert Draft", None, None),
        ("Reviewapply", "pulse", "Review Apply", None, None),
    )
    for name, kind, label, default, menu in definitions:
        _parameter(owner, page, name, kind, label, default, menu)

    allocation = None
    allocator_status = "allocator pending"
    try:
        from pixelblaze_mapper.phase2_output_ui_contract import (
            OutputDraft,
            build_with_shared_allocator,
        )
        allocation, allocator_status = build_with_shared_allocator(OutputDraft())
    except Exception as error:
        allocator_status = "allocator error: " + str(error)
    owner.par.Allocatorstatus = allocator_status
    _fill_live_tables(owner, allocation, allocator_status)

    interface = _get_or_create(owner, tableDAT, "interface")
    interface.clear()
    interface.appendRow(["name", "direction", "type", "description"])
    for row in (
        ("Pixelcount", "map -> output", "int", "Validated mapper slots"),
        ("config_draft", "allocator -> UI", "DAT", "Unapplied output draft"),
        ("universe_draft", "allocator -> UI", "DAT", "Universe preview"),
        ("validation", "validator -> UI", "DAT", "Structured issues"),
        ("Revertdraft", "UI -> controller", "pulse", "Copy live to draft"),
        ("Reviewapply", "UI -> integration", "pulse", "Locked in isolated phase"),
    ):
        interface.appendRow(row)

    canvas = _get_or_create(owner, containerCOMP, "ui_panel")
    canvas.par.w = 1100
    canvas.par.h = 650
    canvas.par.hmode = "fixed"
    canvas.par.vmode = "fixed"
    canvas.par.bgcolorr = 0.009
    canvas.par.bgcolorg = 0.015
    canvas.par.bgcolorb = 0.024
    canvas.par.bgalpha = 1
    canvas.nodeX = -250
    canvas.nodeY = 100

    _panel(canvas, "header_bg", 0, 578, 1100, 72, (0.02, 0.038, 0.058), (0.12, 0.30, 0.40))
    _panel(canvas, "requirement_bg", 20, 456, 1060, 106, (0.022, 0.032, 0.048))
    _panel(canvas, "allocation_bg", 20, 282, 510, 158, (0.021, 0.030, 0.044))
    _panel(canvas, "network_bg", 550, 282, 530, 158, (0.021, 0.030, 0.044))
    _panel(canvas, "universe_bg", 20, 104, 1060, 160, (0.012, 0.019, 0.030))
    _panel(canvas, "footer_bg", 20, 18, 1060, 70, (0.022, 0.030, 0.044))

    _text(canvas, "title", "OUTPUT (DMX)", 24, 598, 260, 36, 24, (0.94, 0.97, 1), bold=True)
    _text(canvas, "live_summary", "LIVE  ART-NET  |  10.0.0.244  |  U0-U21  |  3714 GRB PIXELS  |  30 FPS", 300, 598, 770, 36, 15, (0.31, 0.92, 0.70), align="right", bold=True)
    _text(canvas, "lock_badge", "ISOLATED DRAFT  |  PRODUCTION UNCHANGED", 754, 574, 316, 24, 11, (0.45, 0.78, 0.89), (0.015, 0.10, 0.13), 1, align="center", bold=True)

    _text(canvas, "req_title", "MAP REQUIREMENT", 34, 524, 230, 28, 13, (0.37, 0.79, 0.98), bold=True)
    _text(canvas, "req_source", "SOURCE\nApplied map", 34, 470, 230, 48, 14, bg=(0.03, 0.045, 0.065), alpha=1)
    _text(canvas, "req_pixels", "PIXELS\n3,714", 274, 470, 150, 48, 14, bg=(0.03, 0.045, 0.065), alpha=1, align="center")
    _text(canvas, "req_format", "FORMAT\nGRB / 3 channels", 434, 470, 200, 48, 14, bg=(0.03, 0.045, 0.065), alpha=1, align="center")
    _text(canvas, "req_channels", "CHANNELS\n11,142", 644, 470, 170, 48, 14, bg=(0.03, 0.045, 0.065), alpha=1, align="center")
    _text(canvas, "req_universes", "UNIVERSES\n22 required", 824, 470, 230, 48, 14, bg=(0.03, 0.045, 0.065), alpha=1, align="center")

    _text(canvas, "allocation_title", "ADDRESS ALLOCATION", 34, 400, 260, 28, 13, (0.37, 0.79, 0.98), bold=True)
    _text(canvas, "allocation_values", "AUTO ALLOCATE       ON\nSTART                 Universe 0 / Channel 1\nRANGE                 U0 - U21\nCAPACITY              3,740 pixels  |  spare 26", 34, 302, 472, 92, 14, (0.76, 0.84, 0.91), (0.016, 0.024, 0.036), 1)

    _text(canvas, "network_title", "NETWORK", 564, 400, 200, 28, 13, (0.37, 0.79, 0.98), bold=True)
    _text(canvas, "network_values", "MODE                  Art-Net Unicast\nTARGET                10.0.0.244 : 6454\nLOCAL                  10.0.0.173\nRATE                   30 fps  |  ArtSync ON", 564, 302, 492, 92, 14, (0.76, 0.84, 0.91), (0.016, 0.024, 0.036), 1)

    _text(canvas, "universe_title", "UNIVERSE PREVIEW", 34, 226, 230, 28, 13, (0.37, 0.79, 0.98), bold=True)
    table_text = (
        "CHANNEL       ART-NET ADDRESS      PIXEL RANGE       DMX USED       STATE\n"
        "Universe0     N0 / S0 / U0         0 - 169           1 - 510        LIVE\n"
        "Universe1     N0 / S0 / U1         170 - 339         1 - 510        LIVE\n"
        "Universe2     N0 / S0 / U2         340 - 509         1 - 510        LIVE\n"
        "...           ...                  ...               ...            ...\n"
        "Universe21    N0 / S1 / U5         3570 - 3713       1 - 432        LIVE"
    )
    _text(canvas, "universe_table", table_text, 34, 120, 1022, 100, 13, (0.64, 0.75, 0.84), (0.008, 0.014, 0.023), 1)

    _text(canvas, "draft_status", "DRAFT MATCHES LIVE", 34, 34, 250, 38, 13, (0.94, 0.72, 0.24), (0.11, 0.075, 0.015), 1, align="center", bold=True)
    validation_label = "BLOCKED: production apply locked"
    if allocation is None:
        validation_label = "BLOCKED: allocator + integration pending"
    _text(canvas, "validation_status", validation_label, 294, 34, 390, 38, 12, (0.95, 0.48, 0.30), (0.10, 0.025, 0.018), 1, align="center")
    revert_button = _button(
        canvas, "btn_revert_draft", "REVERT DRAFT", 698, 34, 150, 38,
        enabled=True,
    )
    _button(
        canvas, "btn_review_apply", "REVIEW & APPLY", 860, 34, 196, 38,
        enabled=False, warning=True,
    )

    callbacks = _get_or_create(owner, textDAT, "callbacks")
    callbacks.text = '''# Isolated Phase 2 UI callbacks. No production writes.
def revert_draft():
    owner = op('..')
    owner.par.Draftstate = 'MATCHES LIVE'
    owner.par.Validationstate = 'BLOCKED'
    return 'Draft reset to read-only live baseline'

def review_apply():
    owner = op('..')
    owner.par.Validationstate = 'BLOCKED'
    return 'Integration locked; production unchanged'
'''

    revert_click = _get_or_create(owner, panelexecuteDAT, "click_revert_draft")
    revert_click.par.fromop = revert_button.path
    revert_click.par.panels = revert_button.path
    revert_click.par.panelvalue = "state"
    revert_click.par.offtoon = True
    revert_click.par.valuechange = False
    revert_click.text = '''def onOffToOn(panelValue):
    op('callbacks').module.revert_draft()
    return
'''

    preview = _get_or_create(owner, opviewerTOP, "ui_preview")
    preview.par.opviewer = canvas.path
    preview.par.allowpanel = True
    preview.par.outputresolution = "custom"
    preview.par.resolutionw = 1100
    preview.par.resolutionh = 650
    preview.par.preservealpha = False
    preview.nodeX = -250
    preview.nodeY = -160
    preview.viewer = True

    readme = _get_or_create(owner, textDAT, "README_output_config")
    readme.text = """Phase 2 isolated OUTPUT(DMX) UI.

Production nodes are read-only and are not referenced by callbacks.
Review/Apply is disabled until the production transaction/rollback integration is approved.
Capture TOP: ./ui_preview
No project.save() is called by the builder.
"""

    for index, child in enumerate(canvas.children):
        child.nodeX = (index % 6) * 160
        child.nodeY = -(index // 6) * 90

    print({
        "owner": owner.path,
        "capture": preview.path,
        "live": "3714 pixels / 22 universes",
        "allocator": allocator_status,
        "reviewApplyEnabled": False,
        "productionTouched": False,
        "projectSaved": False,
    })
    return owner


build()
