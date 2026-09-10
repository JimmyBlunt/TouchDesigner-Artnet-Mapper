"""Build a safe GICO fixed-port configuration surface inside the Art-Net router.

The controller exposes one global universe count for every physical port.  The
UI therefore edits that global value once and derives each port's universe
block, destination offset and capacity. APPLY SAFE DRAFT validates without
mutation, then stops output before committing. A port without ``source_start``
remains visible but is not routed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTER = "/project1/multi_controller_output"
OWNER = ROUTER + "/gico_port_config"
MAIN_BUILDER = PROJECT_ROOT / "pixelblaze_mapper" / "build_multi_controller_output.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _node(parent, op_type, name):
    value = parent.op(name)
    duplicates = [child for child in parent.children
                  if re.fullmatch(re.escape(name) + r'\d+', child.name)]
    if value is None and duplicates:
        value = duplicates.pop(0)
        value.name = name
    for duplicate in duplicates:
        duplicate.destroy()
    if value is None:
        value = parent.create(op_type, name)
        value.name = name
    return value


def _set(node, name, value):
    parameter = getattr(node.par, name, None)
    if parameter is not None:
        parameter.val = value


def _panel(node, x, y, width, height, layer=20):
    for name, value in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
                        ("w", width), ("h", height), ("display", True), ("layer", layer)):
        _set(node, name, value)
    return node


def _text(parent, name, value, x, y, width, height, size=12, color=(0.76, 0.84, 0.92)):
    node = _panel(_node(parent, textCOMP, name), x, y, width, height, 30)
    for parameter, item in (("text", value), ("fontsize", size), ("font", "Verdana"),
                            ("type", "multiline"), ("wordwrap", True), ("bgalpha", 1),
                            ("bgcolorr", 0.012), ("bgcolorg", 0.022), ("bgcolorb", 0.038),
                            ("fontalpha", 1), ("fontcolorr", color[0]),
                            ("fontcolorg", color[1]), ("fontcolorb", color[2]),
                            ("aligny", "center"), ("textpaddingl", 8), ("clickthrough", True)):
        _set(node, parameter, item)
    return node


def _field(parent, name, value, x, y, width, height=32):
    node = _panel(_node(parent, fieldCOMP, name), x, y, width, height, 50)
    _set(node, "fieldtype", "string")
    node.op("string").text = str(value)
    return node


def _button(parent, name, label, x, y, width, color=(0.08, 0.25, 0.34)):
    node = _panel(_node(parent, buttonCOMP, name), x, y, width, 36, 60)
    for parameter, value in (("buttontype", "momentary"), ("label", label),
                             ("value0", False),
                             ("fontsize", 12), ("bgalpha", 1),
                             ("bgcolorr", color[0]), ("bgcolorg", color[1]),
                             ("bgcolorb", color[2])):
        _set(node, parameter, value)
    return node


def _click(parent, name, button, expression):
    node = parent.op(name)
    if node is not None and node.type != "panelexec":
        node.destroy()
        node = None
    node = _node(parent, panelexecuteDAT, name)
    node.par.active = False
    node.par.fromop = button.path
    node.par.panels = button.path
    # Used by GICO and the paged topology editor: fire at direct mouse press.
    node.par.panelvalue = "lselect"
    node.par.offtoon = True
    node.par.ontooff = False
    node.par.whileon = False
    node.par.whileoff = False
    node.par.valuechange = False
    node.text = "def onOffToOn(panelValue):\n    %s\n    return\n" % expression
    node.par.active = True
    return node


def _rows(table):
    return [[str(table[row, col]) for col in range(table.numCols)] for row in range(table.numRows)]


def _write(table, rows):
    table.clear()
    for row in rows:
        table.appendRow(row)


def _runtime_source():
    return r'''import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__PROJECT_ROOT__)
MAIN_BUILDER = PROJECT_ROOT / 'pixelblaze_mapper' / 'build_multi_controller_output.py'
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pixelblaze_mapper.gico_port_config import GicoConfig, GicoPortConfig, build_gico_plan
from pixelblaze_mapper.routing_transaction import (
    table_rows, write_rows, router_from_rows, apply_router_transaction, stop_outputs,
)
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS

OWNER = op('/project1/multi_controller_output/gico_port_config')
ROUTER = op('/project1/multi_controller_output')

def _field(name):
    dat = OWNER.op('ui_panel/' + name + '/string')
    return str(dat[0, 0]).strip()

def _status(value, good=True):
    node = OWNER.op('ui_panel/status')
    node.par.text = str(value)
    node.par.fontcolorr = 0.35 if good else 0.98
    node.par.fontcolorg = 0.90 if good else 0.38
    node.par.fontcolorb = 0.67 if good else 0.32

def _optional_int(value):
    value = str(value).strip()
    return None if value.lower() in ('', 'none', 'null') else int(value)

def _flag(name):
    value = _field(name)
    if value not in ('0', '1'):
        raise ValueError(name + ' must be 0 or 1')
    return value == '1'

def _draft():
    ports = []
    for number in range(1, 5):
        ports.append(GicoPortConfig(
            port=number,
            label=_field('p%d_label' % number),
            enabled=_flag('p%d_enabled' % number),
            source_start=_optional_int(_field('p%d_source' % number)),
            pixel_count=int(_field('p%d_count' % number)),
            reverse=_flag('p%d_reverse' % number),
            color_order=_field('p%d_order' % number).upper(),
        ))
    source = op('/project1/math1')
    return GicoConfig(
        universes_per_port=int(_field('universes_per_port')),
        # Legacy persisted GICO model remains one-based; the editor is wire-based.
        first_universe=int(_field('first_universe')) + 1,
        ports=tuple(ports),
        source_pixel_count=int(source.numSamples) if source is not None else TOTAL_PIXELS,
    )

def _draft_tables(config):
    settings = [('key', 'value'), ('universes_per_port', config.universes_per_port),
                ('first_universe', config.first_universe)]
    rows = [('port', 'label', 'enabled', 'source_start', 'pixel_count', 'reverse', 'color_order')]
    for item in config.ports:
        rows.append((item.port, item.label, int(item.enabled),
                         '' if item.source_start is None else item.source_start,
                         item.pixel_count, int(item.reverse), item.color_order))
    return ((OWNER.op('settings'), settings), (OWNER.op('ports'), rows))

def _candidate_rows(plan):
    controllers = table_rows(ROUTER.op('controller_config'))
    header = controllers[0]
    row = next((row for row in controllers[1:]
                if row[header.index('name')] == 'WS2812_NODE'), None)
    if row is None:
        raise ValueError('Missing controller WS2812_NODE')
    # This is the only conversion from GICO UI to canonical wire addresses.
    row[header.index('start_universe')] = str(plan.config.first_universe - 1)
    row[header.index('reserved_universes')] = str(plan.reserved_universes)
    segments = table_rows(ROUTER.op('segment_config'))
    names = segments[0]
    candidate = [names] + [row for row in segments[1:]
                           if row[names.index('controller')] != 'WS2812_NODE']
    for item in plan.ports:
        if not item.routable:
            continue
        values = dict(name='GICO_PORT_%d_%s' % (item.config.port, item.config.label.upper().replace(' ', '_')),
                      source_start=item.config.source_start, count=item.config.pixel_count,
                      controller='WS2812_NODE', destination_start=item.destination_pixel_start,
                      reverse=int(item.config.reverse), color_override=item.config.color_order)
        candidate.append([str(values.get(name, '')) for name in names])
    build_router_plan(router_from_rows(controllers, candidate, plan.config.source_pixel_count))
    return controllers, candidate

def validate_draft():
    try:
        config = _draft()
        plan = build_gico_plan(config)
        _candidate_rows(plan)
        for table, rows in _draft_tables(config):
            write_rows(table, rows)
        for item in plan.ports:
            label = OWNER.op('ui_panel/p%d_derived' % item.config.port)
            route = ('not routed: source missing' if not item.has_source_assignment
                     else 'source %d-%d' % (item.config.source_start, item.source_end_exclusive - 1))
            needed = (item.config.pixel_count + 169) // 170 if item.config.pixel_count else 0
            label.par.text = 'Art-Net U%d-U%d | target %d | %d/%d U needed/reserved | %s' % (
                item.start_universe - 1, item.end_universe - 1, item.destination_pixel_start,
                needed, config.universes_per_port, route)
        warnings = [issue.message for issue in plan.issues if not issue.blocking]
        _status('VALID DRAFT | reserved U%d-U%d (%d universes)%s' % (
            config.first_universe - 1, config.first_universe + plan.reserved_universes - 2,
            plan.reserved_universes, (' | ' + '; '.join(warnings)) if warnings else ''))
        return plan
    except Exception as error:
        _status('BLOCKED - ' + str(error), False)
        return None

def _stop_output():
    stop_outputs(ROUTER)

def _rebuild_router():
    # Keep TouchDesigner's injected op and OP types in the builder context.
    scope = dict(globals())
    scope['__name__'] = '__main__'
    exec(compile(MAIN_BUILDER.read_text(encoding='utf-8'), str(MAIN_BUILDER), 'exec'), scope, scope)

def apply_safe_draft():
    try:
        plan = build_gico_plan(_draft())
        controllers, segments = _candidate_rows(plan)
        apply_router_transaction(ROUTER, controllers, segments, _rebuild_router,
                                 extra_tables=_draft_tables(plan.config),
                                 source_pixels=plan.config.source_pixel_count)
        _status('APPLIED SAFELY - router rebuilt; all outputs remain OFF')
        return True
    except Exception as error:
        _status('APPLY BLOCKED - ' + str(error), False)
        return False
'''.replace('__PROJECT_ROOT__', repr(str(PROJECT_ROOT)))


def _table_value(table, key, default):
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return str(default)


def build():
    router = op(ROUTER)
    if router is None:
        raise RuntimeError("Build /project1/multi_controller_output first")
    owner = _node(router, baseCOMP, "gico_port_config")
    # Existing callbacks must not fire while their saved buttons are repaired.
    for parent, name in ((owner, 'validate_click'), (owner, 'apply_click'),
                         (owner, 'open_controller_ports_click'), (router, 'open_gico_config_click')):
        handler = parent.op(name)
        if handler is not None:
            handler.par.active = False
    settings = _node(owner, tableDAT, "settings")
    if settings.numRows < 2 or settings.numCols < 2 or str(settings[0, 0]) != "key":
        _write(settings, (("key", "value"), ("universes_per_port", 6), ("first_universe", 1)))
    ports = _node(owner, tableDAT, "ports")
    if ports.numRows < 5 or ports.numCols < 7 or str(ports[0, 0]) != "port":
        _write(ports, (
            ("port", "label", "enabled", "source_start", "pixel_count", "reverse", "color_order"),
            (1, "Middle", 1, 0, 517, 0, "GRB"),
            (2, "Upper", 1, 517, 269, 0, "GRB"),
            (3, "Lower", 1, 786, 398, 0, "GRB"),
            (4, "Port 4", 1, "", 896, 0, "GRB"),
        ))
    runtime = _node(owner, textDAT, "runtime")
    runtime.text = _runtime_source()

    canvas = _panel(_node(owner, containerCOMP, "ui_panel"), 0, 0, 1180, 720, 10)
    canvas.viewer = True
    for name, value in (("bgcolorr", 0.006), ("bgcolorg", 0.012),
                        ("bgcolorb", 0.020), ("bgalpha", 1)):
        _set(canvas, name, value)
    _text(canvas, "title", "GICO FIXED PORT CONFIGURATION", 20, 668, 1140, 36, 21, (0.91, 0.96, 1.0))
    _text(canvas, "help", "The controller uses one global universe count for every physical port. Derived blocks cannot overlap. Blank Source Start means visible draft only - no Art-Net routing.", 20, 620, 1140, 40, 12, (0.38, 0.76, 0.96))
    upp = _table_value(settings, "universes_per_port", 6)
    first = int(_table_value(settings, "first_universe", 1)) - 1
    _text(canvas, "upp_label", "UNIVERSES PER PORT", 20, 574, 220, 32)
    _field(canvas, "universes_per_port", upp, 240, 574, 150)
    _text(canvas, "first_label", "START-UNIVERSE (AB 0)", 420, 574, 190, 32)
    _field(canvas, "first_universe", first, 610, 574, 150)
    _text(canvas, "columns", "PORT / LABEL | ENABLED | SOURCE START | PIXELS | REVERSE | ORDER | DERIVED BLOCK", 20, 526, 1140, 30, 11, (0.72, 0.79, 0.86))

    rows = _rows(ports)
    for index in range(1, 5):
        values = rows[index] if index < len(rows) else [str(index), "Port %d" % index, "0", "", "0", "0", "RGB"]
        y = 446 - (index - 1) * 94
        _text(canvas, "p%d_number" % index, "P%d" % index, 20, y + 30, 48, 32, 15, (0.91, 0.96, 1.0))
        _field(canvas, "p%d_label" % index, values[1], 70, y + 30, 180)
        _field(canvas, "p%d_enabled" % index, values[2], 260, y + 30, 85)
        _field(canvas, "p%d_source" % index, values[3], 355, y + 30, 130)
        _field(canvas, "p%d_count" % index, values[4], 495, y + 30, 110)
        _field(canvas, "p%d_reverse" % index, values[5], 615, y + 30, 85)
        _field(canvas, "p%d_order" % index, values[6], 710, y + 30, 100)
        _text(canvas, "p%d_derived" % index, "Press VALIDATE to calculate", 820, y + 12, 340, 58, 11, (0.97, 0.72, 0.26))

    validate_button = _button(canvas, "validate", "VALIDATE DRAFT", 20, 54, 220, (0.08, 0.30, 0.40))
    apply_button = _button(canvas, "apply", "APPLY SAFE DRAFT", 250, 54, 240, (0.08, 0.38, 0.28))
    _click(owner, "validate_click", validate_button, "op('runtime').module.validate_draft()")
    _click(owner, "apply_click", apply_button, "op('runtime').module.apply_safe_draft()")
    _text(canvas, "status", "READY - validate before applying; outputs are not started here", 510, 54, 650, 36, 12, (0.35, 0.90, 0.67))

    # Reach the surface from the existing Ctrl+Shift+6 Art-Net Router dialog.
    router_canvas = router.op("ui_panel")
    if router_canvas is not None:
        open_button = _button(router_canvas, "open_gico_config", "GICO PORT CONFIG", 972, 674, 184, (0.14, 0.24, 0.40))
        _click(router, "open_gico_config_click", open_button,
               "op('gico_port_config/ui_panel').openViewer()")

    preview = _node(owner, opviewerTOP, "ui_preview")
    _set(preview, "opviewer", canvas.path)
    _set(preview, "outputresolution", "custom")
    _set(preview, "resolutionw", 1180)
    _set(preview, "resolutionh", 720)
    runtime.module.validate_draft()
    # Generic controller/port authoring shares the same safe router authority.
    topology_builder = PROJECT_ROOT / 'pixelblaze_mapper' / 'build_port_topology_ui.py'
    topology_scope = dict(globals())
    topology_scope['__name__'] = 'embedded_port_topology_ui'
    exec(compile(topology_builder.read_text(encoding='utf-8'), str(topology_builder), 'exec'), topology_scope, topology_scope)
    topology_scope['build']()
    open_topology = _button(canvas, 'open_controller_ports', 'CONTROLLERS & PORTS', 20, 100, 300)
    _click(owner, 'open_controller_ports_click', open_topology,
           "op('controller_ports/ui_panel').openViewer()")
    return owner


if globals().get("__name__") == "__main__" and "op" in globals():
    build()
