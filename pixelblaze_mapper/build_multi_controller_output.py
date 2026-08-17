"""Build an isolated, disabled multi-controller output network in TouchDesigner.

Execute this file from a TouchDesigner Text DAT.  The builder only creates or
updates ``/project1/multi_controller_output``.  All DMX Out CHOPs remain
disabled, existing production nodes are not reassigned, and the project is not
saved automatically.
"""

from __future__ import annotations

import re
import sys


OWNER = "/project1/multi_controller_output"
SOURCE = "/project1/math1"
LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

from pixelblaze_mapper.multi_controller import (  # noqa: E402
    ControllerConfig,
    RouterConfig,
    SegmentConfig,
    build_router_plan,
    controller_rows,
    default_router_config,
    segment_rows,
    validate_router,
)


def _safe_name(value):
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or "controller"


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


def _write_table(node, rows):
    node.clear()
    for row in rows:
        node.appendRow(row)


def _bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _read_existing_config(owner):
    """Read valid-looking editable DATs so reruns preserve user changes."""

    controllers = owner.op("controller_config")
    segments = owner.op("segment_config")
    if controllers is None or segments is None or controllers.numRows < 2:
        return None
    controller_items = []
    for row in range(1, controllers.numRows):
        controller_items.append(ControllerConfig(
            enabled=_bool(controllers[row, "enabled"]),
            name=str(controllers[row, "name"]),
            target_address=str(controllers[row, "target_ip"]),
            local_interface=str(controllers[row, "local_interface"]),
            port=int(controllers[row, "port"]),
            start_universe=int(controllers[row, "start_universe"]),
            color_order=str(controllers[row, "color_order"]).upper(),
            brightness=float(controllers[row, "brightness"]),
            rate=int(controllers[row, "rate"]),
            art_sync=_bool(controllers[row, "art_sync"]),
        ))
    segment_items = []
    for row in range(1, segments.numRows):
        override = str(segments[row, "color_override"]).strip().upper() or None
        segment_items.append(SegmentConfig(
            name=str(segments[row, "name"]),
            source_start=int(segments[row, "source_start"]),
            count=int(segments[row, "count"]),
            controller=str(segments[row, "controller"]),
            destination_start=int(segments[row, "destination_start"]),
            reverse=_bool(segments[row, "reverse"]),
            color_override=override,
        ))
    return RouterConfig(tuple(controller_items), tuple(segment_items), source_pixel_count=3740)


def _set_if_present(node, parameter, value):
    item = getattr(node.par, parameter, None)
    if item is not None:
        item.val = value


def _connect_first_input(node, source):
    """Connect input zero using the Connector API available in TD 2025."""

    if node.inputs and node.inputs[0] == source:
        return
    node.inputConnectors[0].disconnect()
    source.outputConnectors[0].connect(node)


def _pack_callbacks(controller_name):
    return '''from pixelblaze_mapper.multi_controller import ControllerConfig, RouterConfig, SegmentConfig, build_router_plan

CONTROLLER = %r

def _bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

def _config():
    owner = op('..')
    controllers = []
    table = owner.op('controller_config')
    for row in range(1, table.numRows):
        controllers.append(ControllerConfig(
            enabled=_bool(table[row, 'enabled']), name=str(table[row, 'name']),
            target_address=str(table[row, 'target_ip']), local_interface=str(table[row, 'local_interface']),
            port=int(table[row, 'port']), start_universe=int(table[row, 'start_universe']),
            color_order=str(table[row, 'color_order']).upper(), brightness=float(table[row, 'brightness']),
            rate=int(table[row, 'rate']), art_sync=_bool(table[row, 'art_sync'])))
    segments = []
    table = owner.op('segment_config')
    for row in range(1, table.numRows):
        override = str(table[row, 'color_override']).strip().upper() or None
        segments.append(SegmentConfig(
            name=str(table[row, 'name']), source_start=int(table[row, 'source_start']),
            count=int(table[row, 'count']), controller=str(table[row, 'controller']),
            destination_start=int(table[row, 'destination_start']), reverse=_bool(table[row, 'reverse']),
            color_override=override))
    return RouterConfig(tuple(controllers), tuple(segments), source_pixel_count=3740)

def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 510
    if not scriptOp.inputs:
        return
    source = scriptOp.inputs[0]
    if source.numSamples < 3740 or source.numChans < 3:
        return
    pixels = tuple((float(source[0][i]), float(source[1][i]), float(source[2][i])) for i in range(3740))
    plan = build_router_plan(_config())
    frames = plan.pack_pixels(pixels)[CONTROLLER]
    for index, frame in enumerate(frames):
        channel = scriptOp.appendChan('Universe' + str(index))
        for sample, value in enumerate(frame):
            channel[sample] = value
''' % controller_name


def _label(parent, name, text, x, y, width, height, color=(0.75, 0.84, 0.91), size=13):
    node = _get_or_create(parent, textCOMP, name)
    for parameter, value in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y), ("w", width), ("h", height), ("display", True)):
        _set_if_present(node, parameter, value)
    _set_if_present(node, "text", text)
    _set_if_present(node, "type", "multiline")
    _set_if_present(node, "wordwrap", True)
    _set_if_present(node, "fontsize", size)
    _set_if_present(node, "font", "Verdana")
    _set_if_present(node, "fontcolorr", color[0])
    _set_if_present(node, "fontcolorg", color[1])
    _set_if_present(node, "fontcolorb", color[2])
    _set_if_present(node, "bgcolorr", 0.018)
    _set_if_present(node, "bgcolorg", 0.027)
    _set_if_present(node, "bgcolorb", 0.040)
    _set_if_present(node, "bgalpha", 1)
    _set_if_present(node, "alignx", "left")
    _set_if_present(node, "aligny", "center")
    _set_if_present(node, "textpaddingl", 12)
    _set_if_present(node, "textpaddingr", 12)
    _set_if_present(node, "textpaddingt", 6)
    _set_if_present(node, "textpaddingb", 6)
    _set_if_present(node, "clickthrough", True)
    return node


def _field(parent, name, value, x, y, width=190, height=34):
    node = _get_or_create(parent, fieldCOMP, name)
    for parameter, item in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
                            ("w", width), ("h", height), ("display", True), ("fieldtype", "string")):
        _set_if_present(node, parameter, item)
    # The palette Field COMP exposes its editable value through the internal
    # ``string`` DAT; panel.field is read-only in TD 2025.
    node.op("string").text = str(value)
    return node


def _button(parent, name, label, x, y, width, color):
    node = _get_or_create(parent, buttonCOMP, name)
    for parameter, item in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
                            ("w", width), ("h", 42), ("display", True), ("buttontype", "momentary"),
                            ("label", label), ("fontsize", 13)):
        _set_if_present(node, parameter, item)
    for suffix, item in zip(("r", "g", "b"), color):
        _set_if_present(node, "bgcolor" + suffix, item)
    return node


def _ui_callbacks_source():
    return r'''import ipaddress

BUILDER = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_multi_controller_output.py'

def _field(name):
    return str(op('ui_panel/' + name + '/string')[0, 0]).strip()

def _set_status(text, color=(0.35, 0.90, 0.67)):
    node = op('ui_panel/action_status')
    node.par.text = text
    node.par.fontcolorr, node.par.fontcolorg, node.par.fontcolorb = color

def _write(row, prefix):
    table = op('controller_config')
    address = _field(prefix + '_ip')
    ipaddress.ip_address(address)
    universe = int(_field(prefix + '_universe'))
    brightness = float(_field(prefix + '_brightness'))
    enabled = int(_field(prefix + '_enabled'))
    if not 0 <= universe <= 32767:
        raise ValueError('Universe must be 0..32767')
    if not 0.0 <= brightness <= 1.0:
        raise ValueError('Brightness must be 0.0..1.0')
    if enabled not in (0, 1):
        raise ValueError('Enabled must be 0 or 1')
    table[row, 'target_ip'] = address
    table[row, 'start_universe'] = universe
    table[row, 'brightness'] = brightness
    table[row, 'enabled'] = enabled

def apply_safe():
    try:
        _write(1, 'ws')
        _write(2, 'apa')
        scope = {'__name__': '__main__'}
        exec(compile(open(BUILDER, encoding='utf-8').read(), BUILDER, 'exec'), scope, scope)
        validation = op('validation')
        errors = [str(validation[r, 'message']) for r in range(1, validation.numRows)
                  if str(validation[r, 'severity']).lower() == 'error']
        if errors:
            raise ValueError('; '.join(errors))
        _set_status('VALIDATED - draft applied; network outputs remain OFF')
        return True
    except Exception as error:
        _set_status('BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False

def all_off():
    for node in parent().findChildren(name='dmxout_*', depth=1):
        node.par.active = False
    _set_status('SAFE - all Art-Net outputs are OFF')

def start_enabled():
    all_off()
    if not apply_safe():
        return False
    table = op('controller_config')
    active = []
    for row in range(1, table.numRows):
        if str(table[row, 'enabled']).strip().lower() in ('1', 'true', 'yes', 'on'):
            safe = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(table[row, 'name']).lower()).strip('_')
            node = op('dmxout_' + safe)
            if node is not None:
                node.par.active = True
                active.append(str(table[row, 'name']))
    _set_status(('LIVE - ' + ', '.join(active)) if active else 'SAFE - no controller enabled',
                (0.98, 0.72, 0.24) if active else (0.35, 0.90, 0.67))
    return bool(active)
'''


def build():
    project = op("/project1")
    if project is None:
        raise RuntimeError("/project1 is missing")
    owner = _get_or_create(project, baseCOMP, "multi_controller_output")
    owner.nodeX, owner.nodeY = 900, -500

    try:
        config = _read_existing_config(owner)
    except Exception as error:
        raise RuntimeError("Could not read controller/segment DATs: " + str(error))
    if config is None:
        config = default_router_config()
        controllers = _get_or_create(owner, tableDAT, "controller_config")
        segments = _get_or_create(owner, tableDAT, "segment_config")
        _write_table(controllers, controller_rows(config))
        _write_table(segments, segment_rows(config))

    issues = validate_router(config)
    blocking = [item for item in issues if item.blocking]
    plan = None if blocking else build_router_plan(config)

    validation = _get_or_create(owner, tableDAT, "validation")
    _write_table(validation, (("severity", "code", "field", "message"),) + tuple(
        (issue.severity, issue.code, issue.field, issue.message) for issue in issues
    ))

    summary_rows = [("controller", "enabled", "target", "pixel_span", "universes", "status")]
    if plan is not None:
        for controller_plan in plan.controllers:
            controller = controller_plan.config
            summary_rows.append((controller.name, 0, controller.target_address, controller_plan.destination_pixel_count, controller_plan.universe_count, "SAFE / DISABLED"))
    else:
        for controller in config.controllers:
            summary_rows.append((controller.name, 0, controller.target_address, "-", "-", "BLOCKED / DISABLED"))
    summary = _get_or_create(owner, tableDAT, "controller_summary")
    _write_table(summary, summary_rows)

    # Invalid drafts remain visible for correction, while every isolated output
    # is explicitly stopped.  No routing/packer changes are attempted.
    if plan is None:
        for child in owner.findChildren(name="dmxout_*", depth=1):
            _set_if_present(child, "active", False)
        print({"owner": owner.path, "validation": "BLOCKED", "outputsActive": False, "productionTouched": False, "projectSaved": False})
        return owner

    # Cross-network wires are not allowed in TouchDesigner.  Reference the
    # shared production CHOP through a local Select CHOP, then fan it out to
    # the controller packers inside this COMP.
    source = _get_or_create(owner, selectCHOP, "source_select")
    _set_if_present(source, "chop", SOURCE)
    source.nodeX, source.nodeY = -520, 120
    for index, controller_plan in enumerate(plan.controllers):
        controller = controller_plan.config
        safe = _safe_name(controller.name)
        pack = _get_or_create(owner, scriptCHOP, "pack_" + safe)
        callback_path = str(pack.par.callbacks.eval()) if pack.par.callbacks is not None else ""
        callbacks = op(callback_path) or _get_or_create(owner, textDAT, "pack_" + safe + "_callbacks")
        callbacks.text = _pack_callbacks(controller.name)
        _set_if_present(pack, "callbacks", callbacks.path)
        _connect_first_input(pack, source)
        for candidate in owner.findChildren(name="pack_" + safe + "_callbacks*", depth=1):
            if candidate != callbacks and candidate.OPType == "textDAT":
                candidate.destroy()
        routing = _get_or_create(owner, tableDAT, "routing_" + safe)
        _write_table(routing, controller_plan.routing_rows())
        output = _get_or_create(owner, dmxoutCHOP, "dmxout_" + safe)
        _connect_first_input(output, pack)
        # Builder invariant: creating or rebuilding never starts network traffic.
        _set_if_present(output, "active", False)
        _set_if_present(output, "interface", "artnet")
        _set_if_present(output, "format", "packetperchan")
        _set_if_present(output, "rate", controller.rate)
        _set_if_present(output, "multicast", False)
        _set_if_present(output, "netaddress", controller.target_address)
        _set_if_present(output, "localaddress", controller.local_interface)
        _set_if_present(output, "customport", True)
        _set_if_present(output, "netport", controller.port)
        _set_if_present(output, "sendartsync", controller.art_sync)
        _set_if_present(output, "routingtable", routing.path)
        automatic_routing = owner.op(output.name + "_routingtable")
        if automatic_routing is not None and automatic_routing != routing:
            automatic_routing.destroy()
        callbacks.nodeX, callbacks.nodeY = -500, -180 * index
        pack.nodeX, pack.nodeY = -250, -180 * index
        routing.nodeX, routing.nodeY = 0, -180 * index - 70
        output.nodeX, output.nodeY = 250, -180 * index

    canvas = _get_or_create(owner, containerCOMP, "ui_panel")
    for parameter, value in (("hmode", "fixed"), ("vmode", "fixed"), ("w", 1100), ("h", 620), ("bgcolorr", 0.008), ("bgcolorg", 0.014), ("bgcolorb", 0.023), ("bgalpha", 1)):
        _set_if_present(canvas, parameter, value)
    _label(canvas, "title", "ART-NET MULTI-CONTROLLER ROUTER", 24, 558, 1052, 44, (0.91, 0.96, 1), 23)
    _label(canvas, "safety", "SAFE DRAFT · OUTPUTS DISABLED · SOURCE /project1/math1 (3,740 RGB pixels)", 24, 510, 1052, 34, (0.35, 0.90, 0.67), 14)
    _label(canvas, "flow", "COMMON EFFECT SOURCE  →  SEGMENT ROUTER  →  PER-CONTROLLER RGB PACKER  →  UNICAST ART-NET", 24, 454, 1052, 42, (0.38, 0.76, 0.96), 15)
    _label(canvas, "ws", "WS2812_NODE   10.0.0.244   Source 0–511 → Target 0–511   U0–U3   RGB   2%   DISABLED", 24, 370, 1052, 58)
    _label(canvas, "apa", "APA102_ESP    10.0.0.251   Source 512–1678 → Target 512–1678   U0–U9   RGB   2%   DISABLED\nTarget 0–511 remains black for current ESP firmware compatibility.", 24, 288, 1052, 70)
    _label(canvas, "edit", "EDITABLE TABLES\ncontroller_config: IP · interface · universe · color · brightness · rate · ArtSync · enabled\nsegment_config: source range · controller · target start · reverse · color override", 24, 154, 1052, 112)
    _label(canvas, "warning", "Validation warning: Source 1679–3739 is intentionally unassigned in this first hardware draft.", 24, 84, 1052, 54, (0.97, 0.72, 0.26), 14)
    _label(canvas, "next", "Activation remains a reviewed manual step after table validation and low-brightness hardware test.", 24, 24, 1052, 44, (0.72, 0.79, 0.86), 13)

    preview = _get_or_create(owner, opviewerTOP, "ui_preview")
    _set_if_present(preview, "opviewer", canvas.path)
    _set_if_present(preview, "allowpanel", True)
    _set_if_present(preview, "outputresolution", "custom")
    _set_if_present(preview, "resolutionw", 1100)
    _set_if_present(preview, "resolutionh", 620)
    _set_if_present(preview, "preservealpha", False)
    preview.viewer = True

    # Friendly editor layered over the same validated DAT contract.  The
    # advanced tables stay available for segment ranges, reverse, color order,
    # local interface, rate and ArtSync.
    _set_if_present(canvas, "w", 1180)
    _set_if_present(canvas, "h", 720)
    for obsolete in ("ws", "apa", "edit", "next"):
        if canvas.op(obsolete) is not None:
            canvas.op(obsolete).par.display = False
    _label(canvas, "title", "ART-NET MULTI-CONTROLLER ROUTER", 24, 654, 1132, 42, (0.91, 0.96, 1), 23)
    _label(canvas, "safety", "SAFE START: outputs OFF | source /project1/math1 | 3,740 RGB pixels", 24, 612, 1132, 30, (0.35, 0.90, 0.67), 14)
    _label(canvas, "flow", "COMMON EFFECT -> SEGMENT ROUTER -> RGB PACKER -> UNICAST ART-NET", 24, 568, 1132, 34, (0.38, 0.76, 0.96), 15)
    _label(canvas, "ws_title", "WS2812 NODE  |  pixels 0-511  |  4 universes", 24, 506, 544, 38, (0.91, 0.96, 1), 16)
    _label(canvas, "apa_title", "APA102 ESP  |  pixels 512-1678  |  10 universes", 594, 506, 562, 38, (0.91, 0.96, 1), 16)
    field_rows = (("IP address", "ip", 452), ("Start universe", "universe", 402),
                  ("Brightness 0..1", "brightness", 352), ("Enabled 0/1", "enabled", 302))
    controller_values = (("ws", config.controllers[0], 24, 292), ("apa", config.controllers[1], 594, 862))
    for prefix, controller, label_x, field_x in controller_values:
        values = {"ip": controller.target_address, "universe": controller.start_universe,
                  "brightness": controller.brightness, "enabled": int(controller.enabled)}
        for label, suffix, y in field_rows:
            _label(canvas, prefix + "_" + suffix + "_label", label, label_x, y, 252, 34, (0.72, 0.79, 0.86), 13)
            _field(canvas, prefix + "_" + suffix, values[suffix], field_x, y, 276, 34)
    _label(canvas, "firmware_note", "ESP compatibility: destination pixels 0-511 stay black; APA102 starts at target pixel 512.", 24, 246, 1132, 36, (0.97, 0.72, 0.26), 13)
    _label(canvas, "advanced", "Advanced mapping remains editable in controller_config and segment_config: source range, target start, reverse, RGB order, local NIC, rate and ArtSync.", 24, 202, 1132, 36, (0.72, 0.79, 0.86), 12)

    controls = (("apply", "APPLY SAFE DRAFT", 24, (0.10, 0.38, 0.42)),
                ("start", "START ENABLED", 224, (0.48, 0.31, 0.08)),
                ("off", "ALL OUTPUTS OFF", 424, (0.48, 0.08, 0.08)))
    callbacks = _get_or_create(owner, textDAT, "ui_callbacks")
    callbacks.text = _ui_callbacks_source()
    for command, label, x, color in controls:
        button = _button(canvas, "btn_" + command, label, x, 132, 180, color)
        click = _get_or_create(owner, panelexecuteDAT, "click_" + command)
        click.par.fromop = button.path
        click.par.panels = button.path
        click.par.panelvalue = "state"
        click.par.offtoon = True
        click.par.valuechange = False
        action = {"apply": "apply_safe", "start": "start_enabled", "off": "all_off"}[command]
        click.text = "def onOffToOn(panelValue):\n    op('ui_callbacks').module.%s()\n    return\n" % action
    _label(canvas, "action_status", "READY - edit fields, then APPLY SAFE DRAFT", 624, 132, 532, 42, (0.35, 0.90, 0.67), 13)
    _label(canvas, "warning", "START ENABLED transmits Art-Net only for rows with Enabled=1. Use ALL OUTPUTS OFF for immediate stop.", 24, 72, 1132, 40, (0.97, 0.72, 0.26), 13)
    _label(canvas, "unassigned", "Current draft intentionally leaves source pixels 1679-3739 unassigned for later 3D/pixel-chase mapping.", 24, 24, 1132, 34, (0.72, 0.79, 0.86), 12)
    _set_if_present(preview, "resolutionw", 1180)
    _set_if_present(preview, "resolutionh", 720)

    readme = _get_or_create(owner, textDAT, "README")
    readme.text = """Isolated multi-controller Art-Net router.

Edit controller_config and segment_config, then rerun this builder to rebuild
the preview/routing nodes.  DMX outputs are always forced inactive by the
builder.  It never modifies existing production nodes and never saves the TOE.
"""
    print({"owner": owner.path, "controllers": len(plan.controllers), "outputsActive": False, "productionTouched": False, "projectSaved": False})
    return owner


build()
