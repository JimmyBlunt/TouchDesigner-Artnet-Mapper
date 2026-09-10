"""Build an isolated, disabled multi-controller output network in TouchDesigner.

Execute this file from a TouchDesigner Text DAT.  The builder only creates or
updates ``/project1/multi_controller_output``.  All DMX Out CHOPs remain
disabled, existing production nodes are not reassigned, and the project is not
saved automatically.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


OWNER = "/project1/multi_controller_output"
SOURCE = "/project1/math1"
LOCAL_ROOT = str(Path(__file__).resolve().parents[1])
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
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS
from pixelblaze_mapper.native_dmx_gate import install_sink_gates


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


def _replace_dat_text(node, source):
    """Replace generated DAT contents even when TouchDesigner retained text."""

    node.clear()
    node.write(source)


def _bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _has_column(table, name):
    return any(str(table[0, column]) == name for column in range(table.numCols))


def _read_existing_config(owner):
    """Read valid-looking editable DATs so reruns preserve user changes."""

    controllers = owner.op("controller_config")
    segments = owner.op("segment_config")
    if controllers is None or segments is None or controllers.numRows < 1:
        return None
    controller_items = []
    for row in range(1, controllers.numRows):
        name = str(controllers[row, "name"])
        reserved = int(controllers[row, "reserved_universes"]) if _has_column(controllers, "reserved_universes") else (12 if name == "WS2812_NODE" else 0)
        controller_items.append(ControllerConfig(
            enabled=_bool(controllers[row, "enabled"]),
            name=name,
            target_address=str(controllers[row, "target_ip"]),
            local_interface=str(controllers[row, "local_interface"]),
            port=int(controllers[row, "port"]),
            start_universe=int(controllers[row, "start_universe"]),
            color_order=str(controllers[row, "color_order"]).upper(),
            brightness=float(controllers[row, "brightness"]),
            rate=int(controllers[row, "rate"]),
            art_sync=_bool(controllers[row, "art_sync"]),
            reserved_universes=reserved,
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
    source = op(SOURCE)
    source_count = int(source.numSamples) if source is not None else TOTAL_PIXELS
    return RouterConfig(tuple(controller_items), tuple(segment_items), source_pixel_count=source_count)


def _read_existing_calibration(owner):
    """Preserve calibration controls across safe builder reruns."""

    defaults = {"panel": "all", "pattern": "panel_id", "chase_index": "0"}
    table = owner.op("calibration_config")
    if table is None or table.numRows < 2:
        return defaults
    for row in range(1, table.numRows):
        key = str(table[row, 0]).strip()
        if key in defaults:
            defaults[key] = str(table[row, 1]).strip()
    return defaults


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
    return '''import sys
import time

LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

from pixelblaze_mapper.multi_controller import ControllerConfig, RouterConfig, SegmentConfig, build_router_plan
from pixelblaze_mapper.realtime_packer import compile_router_packer
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS

CONTROLLER = %r
_cache_signature = None
_compiled = None
_latest_frames = ()
_pack_count = 0
_cache_rebuilds = 0
_pack_ms_last = 0.0
_pack_ms_total = 0.0
_pack_ms_max = 0.0

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
            rate=int(table[row, 'rate']), art_sync=_bool(table[row, 'art_sync']),
            reserved_universes=int(table[row, 'reserved_universes'])))
    segments = []
    table = owner.op('segment_config')
    for row in range(1, table.numRows):
        override = str(table[row, 'color_override']).strip().upper() or None
        segments.append(SegmentConfig(
            name=str(table[row, 'name']), source_start=int(table[row, 'source_start']),
            count=int(table[row, 'count']), controller=str(table[row, 'controller']),
            destination_start=int(table[row, 'destination_start']), reverse=_bool(table[row, 'reverse']),
            color_override=override))
    source = op('/project1/math1')
    source_count = int(source.numSamples) if source is not None else TOTAL_PIXELS
    return RouterConfig(tuple(controllers), tuple(segments), source_pixel_count=source_count)

def _signature():
    owner = op('..')
    tables = (owner.op('controller_config'), owner.op('segment_config'))
    source = op('/project1/math1')
    count = int(source.numSamples) if source is not None else TOTAL_PIXELS
    return (count,) + tuple(tuple(str(table[row, col]) for col in range(table.numCols))
                            for table in tables for row in range(table.numRows))

def _controller_packer():
    global _cache_signature, _compiled, _cache_rebuilds
    signature = _signature()
    if _compiled is None or signature != _cache_signature:
        plan = build_router_plan(_config())
        _compiled = compile_router_packer(plan).controller(CONTROLLER)
        _cache_signature = signature
        _cache_rebuilds += 1
    return _compiled

def latest_frames():
    return _latest_frames

def telemetry():
    average = _pack_ms_total / _pack_count if _pack_count else 0.0
    return {'controller': CONTROLLER, 'pack_count': _pack_count,
            'cache_rebuilds': _cache_rebuilds, 'pack_ms_last': _pack_ms_last,
            'pack_ms_average': average, 'pack_ms_max': _pack_ms_max,
            'frame_count': len(_latest_frames)}

def onCook(scriptOp):
    global _latest_frames, _pack_count, _pack_ms_last, _pack_ms_total, _pack_ms_max
    scriptOp.clear()
    scriptOp.numSamples = 510
    if not scriptOp.inputs:
        return
    source = scriptOp.inputs[0]
    if source.numSamples < 1 or source.numChans < 3:
        return
    started = time.perf_counter()
    frames = _controller_packer().pack_channels(source[0], source[1], source[2])
    _latest_frames = frames
    for index, frame in enumerate(frames):
        channel = scriptOp.appendChan('Universe' + str(index))
        channel.vals = list(frame)
    elapsed = (time.perf_counter() - started) * 1000.0
    _pack_count += 1
    _pack_ms_last = elapsed
    _pack_ms_total += elapsed
    _pack_ms_max = max(_pack_ms_max, elapsed)
''' .replace('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper', LOCAL_ROOT.replace('\\', '/')) % controller_name


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
    for parameter, item in (("value0", False), ("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
                            ("w", width), ("h", height), ("display", True), ("fieldtype", "string")):
        _set_if_present(node, parameter, item)
    # The palette Field COMP exposes its editable value through the internal
    # ``string`` DAT; panel.field is read-only in TD 2025.
    node.op("string").text = str(value)
    return node


def _button(parent, name, label, x, y, width, color):
    node = _get_or_create(parent, buttonCOMP, name)
    # A Button COMP can retain an old internal Panel Execute error after the
    # callback it once invoked has been repaired. Recreate only that generated
    # button so a previously stored import error is not carried into the next
    # saved TOE version.
    panelexec = node.op("panelexec1")
    if panelexec is not None and panelexec.errors():
        node.destroy()
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
import sys
import time

PROJECT_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from pixelblaze_mapper.routing_transaction import table_rows, apply_router_transaction, stop_outputs
from pixelblaze_mapper.installation_contract import TOTAL_PIXELS
from pixelblaze_mapper.output_config_summary import build_output_summary
from pixelblaze_mapper.routing_transaction import records

_last_status_update = 0.0

BUILDER = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_multi_controller_output.py'

def _field(name):
    return str(op('ui_panel/' + name + '/string')[0, 0]).strip()

def _source_pixels():
    source = op('/project1/math1')
    return int(source.numSamples) if source is not None else TOTAL_PIXELS

def _set_status(text, color=(0.35, 0.90, 0.67)):
    node = op('ui_panel/action_status')
    node.par.text = 'LAST ACTION: ' + text
    node.par.fontcolorr, node.par.fontcolorg, node.par.fontcolorb = color

def refresh_status(force=False):
    global _last_status_update
    now = time.monotonic()
    if not force and now - _last_status_update < 0.25:
        return
    _last_status_update = now
    try:
        sender = op('artnet_510_sender_callbacks')
        state = sender.module.status() if sender is not None else {'enabled': False, 'error': 'Sender unavailable'}
        summary = build_output_summary(records(table_rows(op('controller_config'))),
            records(table_rows(op('segment_config'))), state, source_pixels=_source_pixels(),
            validation_rows=records(table_rows(op('validation'))))
        fps = state.get('telemetry', {}).get('actual_send_fps', 0.0)
        op('ui_panel/safety').par.text = '%s | sender %s | %.1f actual fps | %d RGB source pixels' % (
            summary.state, 'ON' if summary.sender_enabled else 'OFF', fps, _source_pixels())
        from pixelblaze_mapper.router_dynamic_ui import refresh
        refresh(op('/project1/multi_controller_output'), summary)
    except Exception as error:
        op('ui_panel/safety').par.text = 'STATUS UNAVAILABLE | ' + str(error)

def _controller_draft(rows, name, prefix):
    header = rows[0]
    row = next((row for row in rows[1:] if row[header.index('name')] == name), None)
    if row is None:
        return
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
    for key, value in (('target_ip', address), ('start_universe', universe),
                       ('brightness', brightness), ('enabled', enabled)):
        row[header.index(key)] = str(value)

def _write_calibration():
    panel = _field('cal_panel').lower()
    pattern = _field('cal_pattern').lower()
    chase = int(_field('cal_chase'))
    if panel not in ('all', 'middle', 'upper', 'lower'):
        raise ValueError('Calibration panel: all, middle, upper or lower')
    if pattern not in ('panel_id', 'rows', 'columns', 'chase'):
        raise ValueError('Calibration pattern: panel_id, rows, columns or chase')
    if not 0 <= chase < _source_pixels():
        raise ValueError('Chase index must be 0..%d' % (_source_pixels() - 1))
    return panel, pattern, chase

def _rebuild_router():
    # Preserve TouchDesigner's injected op and OP types.
    scope = dict(globals())
    scope['__name__'] = '__main__'
    exec(compile(open(BUILDER, encoding='utf-8').read(), BUILDER, 'exec'), scope, scope)

def apply_safe():
    try:
        rows = table_rows(op('controller_config'))
        from pixelblaze_mapper.router_dynamic_ui import apply_drafts
        rows = apply_drafts(op('/project1/multi_controller_output'), rows)
        panel, pattern, chase = _write_calibration()
        calibration = table_rows(op('calibration_config'))
        values = {'panel': panel, 'pattern': pattern, 'chase_index': str(chase)}
        for row in calibration[1:]:
            if row[0] in values:
                row[1] = values[row[0]]
        apply_router_transaction(op('/project1/multi_controller_output'), rows,
            table_rows(op('segment_config')), _rebuild_router,
            extra_tables=((op('calibration_config'), calibration),), source_pixels=_source_pixels())
        _set_status('VALIDATED - draft applied; network outputs remain OFF')
        return True
    except Exception as error:
        _set_status('BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False

def all_off():
    stop_outputs(op('/project1/multi_controller_output'))
    _set_status('SAFE - all Art-Net outputs are OFF')

def start_enabled():
    all_off()
    if not apply_safe():
        return False
    sender = op('artnet_510_sender_callbacks')
    sender.module.set_live()
    started = sender.module.set_enabled(True)
    state = sender.module.status()
    active = state.get('controllers', [])
    if started:
        _set_status('LIVE - shared 510-byte sender: ' + ', '.join(active), (0.98, 0.72, 0.24))
    else:
        _set_status('BLOCKED - ' + state.get('error', 'sender did not start'), (0.98, 0.38, 0.32))
    return started

def start_calibration():
    all_off()
    try:
        panel, pattern, chase = _write_calibration()
    except Exception as error:
        _set_status('BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False
    if not apply_safe():
        return False
    sender = op('artnet_510_sender_callbacks')
    try:
        sender.module.set_calibration(panel, pattern, chase)
        started = sender.module.set_enabled(True)
        state = sender.module.status()
        if not started:
            raise RuntimeError(state.get('error', 'sender did not start'))
        _set_status('CALIBRATION - %s / %s / index %d' % (panel, pattern, chase), (0.38, 0.76, 0.96))
        return True
    except Exception as error:
        sender.module.set_enabled(False)
        _set_status('BLOCKED - ' + str(error), (0.98, 0.38, 0.32))
        return False

def _cycle(field, values):
    current = _field(field).lower()
    index = values.index(current) if current in values else -1
    op('ui_panel/' + field + '/string').text = values[(index + 1) % len(values)]
    return start_calibration()

def next_panel():
    return _cycle('cal_panel', ['all', 'middle', 'upper', 'lower'])

def next_pattern():
    return _cycle('cal_pattern', ['panel_id', 'rows', 'columns', 'chase'])
'''.replace('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper', str(__import__('pathlib').Path(__file__).resolve().parents[1]).replace('\\', '/'))


def _artnet_510_sender_source():
    return r'''import importlib
import re
import socket
import sys
import time

LOCAL_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

# TouchDesigner keeps imported Python packages alive while a .toe is open.
# Reload the coordinate stack in dependency order so a rebuilt router never
# continues to use an older mapping implementation from the module cache.
import pixelblaze_mapper.effect_surface_uv as effect_surface_uv
import pixelblaze_mapper.spatial_map as spatial_map
import pixelblaze_mapper.router_calibration as router_calibration
importlib.reload(effect_surface_uv)
importlib.reload(spatial_map)
importlib.reload(router_calibration)

from pixelblaze_mapper.multi_controller import ControllerConfig, RouterConfig, SegmentConfig, build_router_plan
from pixelblaze_mapper.realtime_packer import compile_router_packer
from pixelblaze_mapper.router_calibration import calibration_source, load_coordinates, load_measurement_coordinates

_socket = None
_enabled = False
_last_send = 0.0
_target_override = None
_port_override = None
_last_error = ''
_mode = 'live'
_calibration = ('all', 'panel_id', 0)
_calibration_frames = None
_active_names = []
_tick_count = 0
_rate_skips = 0
_send_count = 0
_packet_count = 0
_send_ms_last = 0.0
_send_ms_total = 0.0
_send_ms_max = 0.0
_send_interval_ema = 0.0
_runtime_signature = None
_runtime_packer = None
_pack_count = 0
_pack_ms_last = 0.0
_pack_ms_total = 0.0
_pack_ms_max = 0.0
_plan_rebuilds = 0

def _bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

def _safe(value):
    return re.sub(r'[^a-z0-9_]+', '_', value.lower()).strip('_') or 'controller'

def _controllers(enabled_only=True):
    table = op('controller_config')
    result = []
    for row in range(1, table.numRows):
        enabled = _bool(table[row, 'enabled'])
        if enabled_only and not enabled:
            continue
        name = str(table[row, 'name'])
        configured_universe = int(table[row, 'start_universe'])
        # Router tables are canonical zero-based wire addresses. GICO's
        # one-based UI conversion happens exactly once in its draft adapter.
        wire_universe = configured_universe
        result.append({
                'name': name,
                'safe': _safe(name),
                'target': str(table[row, 'target_ip']),
                'local': str(table[row, 'local_interface']),
                'port': int(table[row, 'port']),
                'universe': wire_universe,
                'rate': float(table[row, 'rate']),
                'enabled': enabled,
            })
    return result

def _router_config():
    controllers = []
    table = op('controller_config')
    for row in range(1, table.numRows):
        controllers.append(ControllerConfig(
            enabled=_bool(table[row, 'enabled']), name=str(table[row, 'name']),
            target_address=str(table[row, 'target_ip']), local_interface=str(table[row, 'local_interface']),
            port=int(table[row, 'port']), start_universe=int(table[row, 'start_universe']),
            color_order=str(table[row, 'color_order']).upper(), brightness=float(table[row, 'brightness']),
            rate=int(table[row, 'rate']), art_sync=_bool(table[row, 'art_sync']),
            reserved_universes=int(table[row, 'reserved_universes'])))
    segments = []
    table = op('segment_config')
    for row in range(1, table.numRows):
        override = str(table[row, 'color_override']).strip().upper() or None
        segments.append(SegmentConfig(
            name=str(table[row, 'name']), source_start=int(table[row, 'source_start']),
            count=int(table[row, 'count']), controller=str(table[row, 'controller']),
            destination_start=int(table[row, 'destination_start']), reverse=_bool(table[row, 'reverse']),
            color_override=override))
    source = op('/project1/math1')
    source_count = int(source.numSamples) if source is not None else 0
    return RouterConfig(tuple(controllers), tuple(segments), source_pixel_count=source_count)

def _config_signature():
    tables = (op('controller_config'), op('segment_config'))
    source = op('/project1/math1')
    count = int(source.numSamples) if source is not None else 0
    return (count,) + tuple(tuple(str(table[row, col]) for col in range(table.numCols))
                            for table in tables for row in range(table.numRows))

def _compiled_router():
    global _runtime_signature, _runtime_packer, _plan_rebuilds
    signature = _config_signature()
    if _runtime_packer is None or signature != _runtime_signature:
        _runtime_packer = compile_router_packer(build_router_plan(_router_config()))
        _runtime_signature = signature
        _plan_rebuilds += 1
    return _runtime_packer

def _packet(universe, payload):
    # Router calibration frames are intentionally kept as immutable tuples of
    # channel values by the pure-Python mapping code.  Live CHOP frames already
    # arrive as ``bytes``.  Normalize both paths here before concatenating the
    # ArtDMX header so calibration and live output use the identical packet
    # serializer.
    payload = bytes(payload)
    length = len(payload)
    # GICO compatibility: sequence 0 disables Art-Net packet ordering and
    # duplicate filtering. Live hardware tests confirmed that this receiver
    # otherwise drops universes when one sequence value is reused in a frame.
    return (b'Art-Net\x00' + b'\x00\x50' + b'\x00\x0e' + b'\x00\x00'
            + bytes((universe & 255, (universe >> 8) & 127))
            + bytes((length >> 8, length & 255)) + payload)

def stop():
    global _socket, _enabled, _active_names
    _enabled = False
    _active_names = []
    if _socket is not None:
        try:
            _socket.close()
        except Exception:
            pass
    _socket = None

def set_enabled(value, target_override=None, port_override=None):
    global _socket, _enabled, _last_send, _target_override, _port_override, _last_error, _active_names
    global _tick_count, _rate_skips, _send_count, _packet_count
    global _send_ms_last, _send_ms_total, _send_ms_max, _send_interval_ema
    global _pack_count, _pack_ms_last, _pack_ms_total, _pack_ms_max
    stop()
    _target_override = target_override
    _port_override = port_override
    _last_error = ''
    if not value:
        return True
    _tick_count = 0
    _rate_skips = 0
    _send_count = 0
    _packet_count = 0
    _send_ms_last = 0.0
    _send_ms_total = 0.0
    _send_ms_max = 0.0
    _send_interval_ema = 0.0
    _pack_count = 0
    _pack_ms_last = 0.0
    _pack_ms_total = 0.0
    _pack_ms_max = 0.0
    configs = _controllers(True)
    if not configs:
        _last_error = 'No controller row has Enabled=1'
        return False
    locals_used = sorted(set(config['local'] for config in configs))
    if len(locals_used) != 1:
        _last_error = 'Enabled controllers must use one shared local interface'
        return False
    try:
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _socket.bind((locals_used[0], 6454))
        _enabled = True
        _active_names = [config['name'] for config in configs]
        _last_send = 0.0
        return True
    except Exception as error:
        _last_error = str(error)
        stop()
        return False

def set_live():
    global _mode, _calibration_frames
    _mode = 'live'
    _calibration_frames = None

def set_calibration(panel='all', pattern='panel_id', chase_index=0):
    global _mode, _calibration, _calibration_frames
    pixels = calibration_source(
        load_coordinates(),
        panel=panel,
        pattern=pattern,
        chase_index=int(chase_index),
        measurement_coordinates=load_measurement_coordinates(),
    )
    _calibration_frames = build_router_plan(_router_config()).pack_pixels(pixels)
    _calibration = (panel, pattern, int(chase_index))
    _mode = 'calibration'
    return True

def _live_frames(configs):
    global _pack_count, _pack_ms_last, _pack_ms_total, _pack_ms_max
    source = op('source_select')
    if source is None:
        raise RuntimeError('Missing common source_select')
    # A non-forced cook evaluates the current dependency graph only when dirty;
    # it does not recook an already evaluated render chain in onFrameStart.
    source.cook(force=False)
    if source.numSamples < 1 or source.numChans < 3:
        raise RuntimeError('Expected nonempty common source with 3 RGB channels')
    started = time.perf_counter()
    packer = _compiled_router()
    frames = {config['name']: packer.controller(config['name']).pack_channels(
              source[0], source[1], source[2]) for config in configs}
    elapsed = (time.perf_counter() - started) * 1000.0
    _pack_count += 1
    _pack_ms_last = elapsed
    _pack_ms_total += elapsed
    _pack_ms_max = max(_pack_ms_max, elapsed)
    return frames

def tick():
    global _last_send, _last_error, _tick_count, _rate_skips
    global _send_count, _packet_count, _send_ms_last, _send_ms_total, _send_ms_max, _send_interval_ema
    _tick_count += 1
    if not _enabled or _socket is None:
        return
    configs = _controllers(True)
    if not configs:
        _last_error = 'No controller row has Enabled=1'
        stop()
        return
    now = time.monotonic()
    if now - _last_send < 1.0 / max(1.0, max(config['rate'] for config in configs)):
        _rate_skips += 1
        return
    try:
        started = time.perf_counter()
        sent_packets = 0
        live_frames = _live_frames(configs) if _mode == 'live' else None
        for config in configs:
            frames = (_calibration_frames or {}).get(config['name']) if _mode == 'calibration' else live_frames.get(config['name'])
            if frames is None:
                raise RuntimeError('Missing calibration frames for ' + config['name'])
            target = (_target_override or config['target'], _port_override or config['port'])
            for offset, payload in enumerate(frames):
                if len(payload) != 510:
                    raise RuntimeError('Expected exactly 510-byte ArtDMX payload')
                _socket.sendto(_packet(config['universe'] + offset, payload), target)
                sent_packets += 1
        previous_send = _last_send
        _last_send = now
        elapsed = (time.perf_counter() - started) * 1000.0
        _send_count += 1
        _packet_count += sent_packets
        _send_ms_last = elapsed
        _send_ms_total += elapsed
        _send_ms_max = max(_send_ms_max, elapsed)
        if previous_send:
            interval = now - previous_send
            _send_interval_ema = interval if not _send_interval_ema else (_send_interval_ema * 0.9 + interval * 0.1)
    except Exception as error:
        _last_error = str(error)
        stop()

def status():
    average = _send_ms_total / _send_count if _send_count else 0.0
    pack_average = _pack_ms_total / _pack_count if _pack_count else 0.0
    return {'enabled': _enabled, 'error': _last_error, 'mode': _mode,
            'calibration': _calibration, 'controllers': list(_active_names),
            'target_override': _target_override, 'port_override': _port_override,
            'telemetry': {'tick_count': _tick_count, 'rate_skips': _rate_skips,
                          'send_count': _send_count, 'packet_count': _packet_count,
                          'send_ms_last': _send_ms_last, 'send_ms_average': average,
                          'send_ms_max': _send_ms_max,
                          'actual_send_fps': (1.0 / _send_interval_ema) if _send_interval_ema else 0.0,
                          'pack_count': _pack_count, 'pack_ms_last': _pack_ms_last,
                          'pack_ms_average': pack_average, 'pack_ms_max': _pack_ms_max,
                          'plan_rebuilds': _plan_rebuilds}}
'''.replace('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper', str(__import__('pathlib').Path(__file__).resolve().parents[1]).replace('\\', '/'))


def _artnet_510_execute_source():
    return r'''def onFrameStart(frame):
    op('artnet_510_sender_callbacks').module.tick()
    return

def onExit():
    op('artnet_510_sender_callbacks').module.stop()
    return
'''


def build():
    project = op("/project1")
    if project is None:
        raise RuntimeError("/project1 is missing")
    owner = _get_or_create(project, baseCOMP, "multi_controller_output")
    owner.nodeX, owner.nodeY = 900, -500

    # A rebuild is configuration work, never an implicit hardware action.
    # Stop the previous shared sender before touching any Button/Panel Execute
    # state; an old saved momentary value must not retrigger START ENABLED while
    # its callback DAT is being rebound.
    previous_sender = owner.op("artnet_510_sender_callbacks")
    if previous_sender is not None:
        try:
            previous_sender.module.set_enabled(False)
        except Exception:
            try:
                previous_sender.module.stop()
            except Exception:
                pass

    try:
        config = _read_existing_config(owner)
    except Exception as error:
        raise RuntimeError("Could not read controller/segment DATs: " + str(error))
    if config is None:
        config = default_router_config()
    # Always rewrite the preserved model through the canonical schema.  This
    # performs the one-time migration that adds fixed universe capacity to an
    # older controller_config without losing any editable values.
    controllers = _get_or_create(owner, tableDAT, "controller_config")
    segments = _get_or_create(owner, tableDAT, "segment_config")
    _write_table(controllers, controller_rows(config))
    _write_table(segments, segment_rows(config))

    calibration = _read_existing_calibration(owner)
    calibration_table = _get_or_create(owner, tableDAT, "calibration_config")
    _write_table(calibration_table, (
        ("key", "value"),
        ("panel", calibration["panel"]),
        ("pattern", calibration["pattern"]),
        ("chase_index", calibration["chase_index"]),
    ))

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
    native_gate_specs = []
    for index, controller_plan in enumerate(plan.controllers):
        controller = controller_plan.config
        safe = _safe_name(controller.name)
        pack = _get_or_create(owner, scriptCHOP, "pack_" + safe)
        callback_path = str(pack.par.callbacks.eval()) if pack.par.callbacks is not None else ""
        callbacks = op(callback_path) or _get_or_create(owner, textDAT, "pack_" + safe + "_callbacks")
        from pixelblaze_mapper.output_slot_mask import install_native_source
        _replace_dat_text(callbacks, install_native_source(_pack_callbacks(controller.name)))
        _set_if_present(pack, "callbacks", callbacks.path)
        _connect_first_input(pack, source)
        for candidate in owner.findChildren(name="pack_" + safe + "_callbacks*", depth=1):
            if candidate != callbacks and candidate.OPType == "textDAT":
                candidate.destroy()
        routing = _get_or_create(owner, tableDAT, "routing_" + safe)
        _write_table(routing, controller_plan.routing_rows())
        output = _get_or_create(owner, dmxoutCHOP, "dmxout_" + safe)
        # An intact demand gate is preserved across rebuilds. The gate helper
        # refuses unknown wiring instead of replacing a user's connection.
        if not output.inputs:
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
        if controller_plan.universe_count:
            native_gate_specs.append((output, pack, controller_plan.universe_count))

    install_sink_gates(native_gate_specs, constant_type=constantCHOP, select_type=selectCHOP)

    # The GICO controller is configured for 510 DMX channels per universe.
    # TouchDesigner's DMX Out CHOP pads ArtDMX payloads to 512 bytes, which
    # shifts RGB triplets in this firmware. Keep the DMX Out nodes as visible
    # disabled references and use one shared exact-510-byte sender for every
    # enabled controller. One socket prevents competing binds to UDP 6454.
    sender_callbacks = _get_or_create(owner, textDAT, "artnet_510_sender_callbacks")
    try:
        sender_callbacks.module.stop()
    except Exception:
        pass
    from pixelblaze_mapper.output_slot_mask import install_source as install_slot_mask
    from pixelblaze_mapper.sender_pacing import install_source as install_pacing
    _replace_dat_text(sender_callbacks, install_pacing(install_slot_mask(_artnet_510_sender_source())))
    sender_execute = _get_or_create(owner, executeDAT, "artnet_510_execute")
    _replace_dat_text(sender_execute, _artnet_510_execute_source())
    _set_if_present(sender_execute, "active", True)
    _set_if_present(sender_execute, "framestart", True)
    _set_if_present(sender_execute, "exit", True)
    sender_callbacks.nodeX, sender_callbacks.nodeY = 500, 80
    sender_execute.nodeX, sender_execute.nodeY = 700, 80

    canvas = _get_or_create(owner, containerCOMP, "ui_panel")
    for parameter, value in (("hmode", "fixed"), ("vmode", "fixed"), ("w", 1100), ("h", 620), ("bgcolorr", 0.008), ("bgcolorg", 0.014), ("bgcolorb", 0.023), ("bgalpha", 1)):
        _set_if_present(canvas, parameter, value)
    _label(canvas, "title", "ART-NET MULTI-CONTROLLER ROUTER", 24, 558, 1052, 44, (0.91, 0.96, 1), 23)
    _label(canvas, "safety", "SAFE DRAFT · OUTPUTS DISABLED · SOURCE /project1/math1 (3,740 RGB pixels)", 24, 510, 1052, 34, (0.35, 0.90, 0.67), 14)
    _label(canvas, "flow", "COMMON EFFECT SOURCE  →  SEGMENT ROUTER  →  PER-CONTROLLER RGB PACKER  →  UNICAST ART-NET", 24, 454, 1052, 42, (0.38, 0.76, 0.96), 15)
    _label(canvas, "ws", "WS2812_NODE   10.0.0.244   3 ports / 1,184 pixels   U1-U9   GRB   2%   DISABLED", 24, 370, 1052, 58)
    _label(canvas, "apa", "APA102_ESP    10.0.0.251   Source 1187-2353 -> Target 512-1678   U0-U9   RGB   2%   DISABLED\nTarget 0-511 remains black for current ESP firmware compatibility.", 24, 288, 1052, 70)
    _label(canvas, "edit", "EDITABLE TABLES\ncontroller_config: IP · interface · universe · reserved universes · color · brightness · rate · ArtSync · enabled\nsegment_config: source range · controller · target start · reverse · color override", 24, 154, 1052, 112)
    _label(canvas, "warning", "Validation warning: Source 2350-3739 is intentionally unassigned for later rear-panel mapping.", 24, 84, 1052, 54, (0.97, 0.72, 0.26), 14)
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
    # Keep the complete live and calibration controls visible in the normal
    # 1180 x 720 floating operator viewer used by this project.  The previous
    # 980 px canvas hid the calibration section below the window crop.
    _set_if_present(canvas, "h", 720)
    for obsolete in ("ws", "apa", "edit", "next"):
        if canvas.op(obsolete) is not None:
            canvas.op(obsolete).par.display = False
    _label(canvas, "title", "ART-NET MULTI-CONTROLLER ROUTER", 24, 674, 1132, 34, (0.91, 0.96, 1), 21)
    _label(canvas, "safety", "READING SENDER STATUS", 24, 640, 1132, 26, (0.35, 0.90, 0.67), 13)
    _label(canvas, "flow", "COMMON EFFECT -> SEGMENT ROUTER -> RGB PACKER -> ONE SHARED 510-BYTE ART-NET SENDER", 24, 604, 1132, 28, (0.38, 0.76, 0.96), 14)
    _label(canvas, "ws_title", "WS2812 NODE | reading live status", 24, 560, 544, 30, (0.91, 0.96, 1), 12)
    _label(canvas, "apa_title", "APA102 ESP | reading live status", 594, 560, 562, 30, (0.91, 0.96, 1), 12)
    field_rows = (("IP address", "ip", 522), ("First WIRE universe (0-based)", "universe", 484),
                  ("Brightness 0..1", "brightness", 446), ("Enabled 0/1", "enabled", 408))
    controllers_by_name = {item.name: item for item in config.controllers}
    for prefix, name in (("ws", "WS2812_NODE"), ("apa", "APA102_ESP")):
        if name not in controllers_by_name:
            for suffix in ('ip', 'universe', 'brightness', 'enabled'):
                for node_name in (prefix + '_' + suffix, prefix + '_' + suffix + '_label'):
                    missing_field = canvas.op(node_name)
                    if missing_field is not None:
                        _set_if_present(missing_field, 'display', False)
    controller_values = tuple((prefix, controllers_by_name[name], label_x, field_x)
        for prefix, name, label_x, field_x in (("ws", "WS2812_NODE", 24, 292),
                                             ("apa", "APA102_ESP", 594, 862))
        if name in controllers_by_name)
    for prefix, controller, label_x, field_x in controller_values:
        values = {"ip": controller.target_address, "universe": controller.start_universe,
                  "brightness": controller.brightness, "enabled": int(controller.enabled)}
        for label, suffix, y in field_rows:
            _label(canvas, prefix + "_" + suffix + "_label", label, label_x, y, 252, 34, (0.72, 0.79, 0.86), 13)
            _field(canvas, prefix + "_" + suffix, values[suffix], field_x, y, 276, 34)
    _label(canvas, "firmware_note", "Router and sender use zero-based WIRE universes. GICO UI universe = wire + 1. Port reserve is hardware capacity, not LED count.", 24, 370, 1132, 28, (0.97, 0.72, 0.26), 12)
    _label(canvas, "advanced", "Advanced mapping: controller_config + segment_config (ranges, targets, reverse, RGB order, NIC, rate, ArtSync).", 24, 338, 1132, 26, (0.72, 0.79, 0.86), 11)

    controls = (("apply", "APPLY SAFE DRAFT", 24, (0.10, 0.38, 0.42)),
                ("start", "START ENABLED", 224, (0.48, 0.31, 0.08)),
                ("off", "ALL OUTPUTS OFF", 424, (0.48, 0.08, 0.08)))
    callbacks = _get_or_create(owner, textDAT, "ui_callbacks")
    _replace_dat_text(callbacks, _ui_callbacks_source())
    for command, label, x, color in controls:
        button = _button(canvas, "btn_" + command, label, x, 292, 180, color)
        click = _get_or_create(owner, panelexecuteDAT, "click_" + command)
        _set_if_present(click, "active", False)
        click.par.fromop = button.path
        click.par.panels = button.path
        # Direct left press: do not depend on a momentary button's cooked state.
        click.par.panelvalue = "lselect"
        click.par.offtoon = True
        click.par.ontooff = False
        click.par.whileon = False
        click.par.whileoff = False
        click.par.valuechange = False
        action = {"apply": "apply_safe", "start": "start_enabled", "off": "all_off"}[command]
        _replace_dat_text(click, "def onOffToOn(panelValue):\n    op('ui_callbacks').module.%s()\n    return\n" % action)
        _set_if_present(click, "active", True)
    _label(canvas, "action_status", "READY - edit fields, then APPLY SAFE DRAFT", 624, 292, 532, 38, (0.35, 0.90, 0.67), 12)
    _label(canvas, "warning", "START ENABLED sends live Art-Net. ALL OUTPUTS OFF stops immediately.", 24, 258, 1132, 26, (0.97, 0.72, 0.26), 12)
    _label(canvas, "unassigned", "Reading source assignments", 24, 230, 1132, 24, (0.72, 0.79, 0.86), 11)

    _label(canvas, "cal_title", "MEASURED 3D-MAP CALIBRATION", 24, 194, 1132, 30, (0.38, 0.76, 0.96), 16)
    _label(canvas, "cal_panel_label", "Panel: all | middle | upper | lower", 24, 156, 260, 30, (0.72, 0.79, 0.86), 11)
    _field(canvas, "cal_panel", calibration["panel"], 284, 156, 190, 30)
    _label(canvas, "cal_pattern_label", "Pattern: panel_id | rows | columns | chase", 494, 156, 310, 30, (0.72, 0.79, 0.86), 11)
    _field(canvas, "cal_pattern", calibration["pattern"], 804, 156, 190, 30)
    _label(canvas, "cal_chase_label", "Chase index 0..%d" % (config.source_pixel_count - 1), 24, 122, 260, 28, (0.72, 0.79, 0.86), 11)
    _field(canvas, "cal_chase", calibration["chase_index"], 284, 122, 190, 28)

    calibration_controls = (
        ("cal_start", "START CALIBRATION", 24, "start_calibration", (0.08, 0.34, 0.52)),
        ("cal_panel", "NEXT PANEL", 224, "next_panel", (0.12, 0.28, 0.43)),
        ("cal_pattern", "NEXT PATTERN", 424, "next_pattern", (0.12, 0.28, 0.43)),
        ("cal_live", "RETURN TO LIVE", 624, "start_enabled", (0.48, 0.31, 0.08)),
    )
    for name, label, x, action, color in calibration_controls:
        button = _button(canvas, "btn_" + name, label, x, 70, 180, color)
        click = _get_or_create(owner, panelexecuteDAT, "click_" + name)
        _set_if_present(click, "active", False)
        click.par.fromop = button.path
        click.par.panels = button.path
        click.par.panelvalue = "lselect"
        click.par.offtoon = True
        click.par.ontooff = False
        click.par.whileon = False
        click.par.whileoff = False
        click.par.valuechange = False
        _replace_dat_text(click, "def onOffToOn(panelValue):\n    op('ui_callbacks').module.%s()\n    return\n" % action)
        _set_if_present(click, "active", True)
    _label(canvas, "cal_note", "Panel ID: middle=red, upper=green, lower=blue. Rows/columns use every measured coordinate. Chase: selected LED green, neighbours white.", 24, 24, 1132, 32, (0.72, 0.79, 0.86), 11)
    _set_if_present(preview, "resolutionw", 1180)
    _set_if_present(preview, "resolutionh", 720)

    readme = _get_or_create(owner, textDAT, "README")
    readme.text = """Isolated multi-controller Art-Net router.

Edit controller_config and segment_config, then use APPLY SAFE DRAFT. Both
receivers are transmitted by one shared exact-510-byte Art-Net sender so only
one local UDP 6454 socket is used. The visible DMX Out CHOPs are references and
always remain inactive.

The calibration section renders panel identification, rows, columns and chase
directly from the measured Pixelblaze 3D coordinates. It does not assume a
rectangular panel or estimate row lengths. ALL OUTPUTS OFF is the immediate
network stop. The builder never saves the TOE automatically.
"""
    # The GICO hardware exposes one global universe count for every physical
    # port.  Build its dedicated safe editor after the main router surface so
    # Ctrl+Shift+6 always contains the entry button.  The nested builder only
    # validates/edits drafts and never starts Art-Net.
    gico_builder = Path(LOCAL_ROOT) / "pixelblaze_mapper/build_gico_port_config_ui.py"
    gico_scope = dict(globals())
    gico_scope["__name__"] = "pixelblaze_mapper_embedded_gico_ui"
    exec(compile(gico_builder.read_text(encoding="utf-8"), str(gico_builder), "exec"), gico_scope, gico_scope)
    gico_scope["build"]()
    status_execute = _get_or_create(owner, executeDAT, 'router_status_execute')
    status_execute.par.active = True
    status_execute.par.framestart = True
    _replace_dat_text(status_execute, "def onFrameStart(frame):\n    op('ui_callbacks').module.refresh_status()\n    return\n")
    from pixelblaze_mapper.router_dynamic_ui import install as install_router_cards
    install_router_cards(owner, globals())
    callbacks.module.refresh_status(force=True)
    print({"owner": owner.path, "controllers": len(plan.controllers), "outputsActive": False, "productionTouched": False, "projectSaved": False})
    return owner


build()
