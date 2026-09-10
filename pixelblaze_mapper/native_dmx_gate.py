"""Demand gates for inactive native DMX references, never for the real sender.

No Active assignment, socket access, packer change, or project save occurs here.
TouchDesigner types are injected by the caller; the module imports offline.
"""
from __future__ import annotations

import math


MARKER = 'INACTIVE NATIVE DMX DEMAND GATE v2 SELECT: '
SHAPE_KEY = 'native_dmx_gate_shape'
KNOWN = (
    ('esp_artnet_out', 'esp_artnet_live_pack'),
    ('multi_controller_output/dmxout_ws2812_node', 'multi_controller_output/pack_ws2812_node'),
    ('multi_controller_output/dmxout_apa102_esp', 'multi_controller_output/pack_apa102_esp'),
)


def _value(par):
    return par.eval()


def _settings(count, rate):
    return {'const0name': 'Universe[0-%d]' % (count - 1), 'const0value': 0,
            'single': False, 'startunit': 'samples', 'endunit': 'samples',
            'start': 0, 'end': 509, 'rate': rate, 'timeslice': False}


SELECT_SETTINGS = {'channames': '*', 'renamefrom': '', 'renameto': '',
                   'filterdigits': False, 'stripdigits': False,
                   'align': 'none', 'autoprefix': False,
                   'timeslice': False, 'srselect': 'err', 'scope': '*'}


def _check_settings(node, values):
    for name, expected in values.items():
        par = getattr(node.par, name, None)
        if par is None or str(getattr(par, 'mode', 'CONSTANT')).upper().split('.')[-1] != 'CONSTANT' or _value(par) != expected:
            raise RuntimeError('Modified gate parameter: ' + node.path + '.' + name)


def _connect(node, source, index=0):
    node.inputConnectors[index].disconnect()
    source.outputConnectors[0].connect(node.inputConnectors[index])


def install_sink_gates(specs, *, constant_type, select_type, allowed_source_types=('script',)):
    """Install preflighted ``(sink, original_source, universe_count)`` gates.

    Count comes from a validated routing plan or the current source metadata.
    Only a direct original connection or an intact owned gate is accepted.
    Preflight failures write nothing; construction failures restore sink wires
    and remove only newly created helper nodes. Existing Active values,
    expressions and parameter modes are deliberately neither read nor written.
    """
    prepared = []
    seen = set()
    for sink, source, count in specs:
        if sink is None or source is None:
            raise ValueError('Missing expected native DMX sink/source')
        if sink.path in seen:
            raise ValueError('Duplicate sink: ' + sink.path)
        seen.add(sink.path)
        parent = sink.parent()
        if sink.type != 'dmxout' or source.type not in allowed_source_types or source.parent() != parent:
            raise ValueError('Expected sibling DMX Out and Script CHOP: ' + sink.path)
        if getattr(sink.par, 'active', None) is None:
            raise ValueError('Missing Active parameter: ' + sink.path)
        if type(count) is not int or count < 1:
            raise ValueError('Positive explicit universe count required')
        rate = float(source.rate)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError('Invalid source sample rate')
        idle = parent.op(sink.name + '_idle_black')
        gate = parent.op(sink.name + '_demand_gate')
        # String-only branches: evaluating the expression never resolves either
        # source. A wired Switch still cooked its unselected input in native TD.
        idle_path = parent.path + '/' + sink.name + '_idle_black'
        expression = "%r if op(%r).par.active.eval() else %r" % (source.path, sink.path, idle_path)
        marker = MARKER + sink.path
        if idle is None and gate is None:
            if list(sink.inputs) != [source]:
                raise RuntimeError('Unknown sink wiring: ' + sink.path)
        elif idle is None or gate is None:
            raise RuntimeError('Partial gate/name collision: ' + sink.path)
        else:
            if idle.type != 'constant' or gate.type != 'select' or idle.comment != marker or gate.comment != marker:
                raise RuntimeError('Gate name collision: ' + sink.path)
            if list(idle.inputs) or list(gate.inputs) or list(sink.inputs) != [gate]:
                raise RuntimeError('Modified gate wiring: ' + sink.path)
            shape = idle.fetch(SHAPE_KEY, None)
            if not isinstance(shape, dict) or set(shape) != {'count', 'rate'}:
                raise RuntimeError('Missing owned gate shape: ' + sink.path)
            _check_settings(idle, _settings(shape['count'], shape['rate']))
            if idle.par.const0name.sequence.numBlocks != 1:
                raise RuntimeError('Modified idle channel sequence: ' + sink.path)
            _check_settings(gate, SELECT_SETTINGS)
            if str(gate.par.chops.mode).upper().split('.')[-1] != 'EXPRESSION' or gate.par.chops.expr != expression:
                raise RuntimeError('Modified gate demand expression: ' + sink.path)
        prepared.append((sink, source, count, rate, parent, idle, gate, expression, marker))

    created, rewired, updated = [], [], []
    try:
        for sink, source, count, rate, parent, idle, gate, expression, marker in prepared:
            if gate is not None:
                new_shape = {'count': count, 'rate': rate}
                if idle.fetch(SHAPE_KEY) != new_shape:
                    old_shape = idle.fetch(SHAPE_KEY)
                    updated.append((idle, old_shape))
                    for name, value in _settings(count, rate).items():
                        getattr(idle.par, name).val = value
                    idle.store(SHAPE_KEY, new_shape)
                continue
            idle = parent.create(constant_type, sink.name + '_idle_black')
            created.append(idle)
            idle.par.const0name.sequence.numBlocks = 1
            for name, value in _settings(count, rate).items():
                getattr(idle.par, name).val = value
            idle.store(SHAPE_KEY, {'count': count, 'rate': rate})
            idle.comment = marker
            idle.viewer = False
            gate = parent.create(select_type, sink.name + '_demand_gate')
            created.append(gate)
            for name, value in SELECT_SETTINGS.items():
                getattr(gate.par, name).val = value
            gate.par.chops.expr = expression
            gate.comment = marker
            gate.viewer = False
            rewired.append((sink, source))
            _connect(sink, gate)
    except Exception:
        for sink, source in reversed(rewired):
            _connect(sink, source)
        for idle, shape in reversed(updated):
            for name, value in _settings(shape['count'], shape['rate']).items():
                getattr(idle.par, name).val = value
            idle.store(SHAPE_KEY, shape)
        for node in reversed(created):
            node.destroy()
        raise
    return {'sinks': [item[0].path for item in prepared],
            'created': [node.path for node in created],
            'updated_shapes': [node.path for node, _ in updated],
            'active_parameters_changed': False, 'sender_changed': False}


def install_known_sink_gates(project, *, constant_type, select_type):
    """Scoped live migration: three known sinks, present packer shape required."""
    if project.path != '/project1':
        raise ValueError('Expected /project1')
    specs = []
    for sink_path, source_path in KNOWN:
        sink, source = project.op(sink_path), project.op(source_path)
        if sink is None or source is None:
            raise ValueError('Missing expected sink/source: ' + sink_path)
        count = int(source.numChans)
        if int(source.numSamples) != 510 or [channel.name for channel in source.chans()] != ['Universe%d' % i for i in range(count)]:
            raise ValueError('Expected current 510-sample Universe channels: ' + source.path)
        specs.append((sink, source, count))
    return install_sink_gates(specs, constant_type=constant_type, select_type=select_type)
