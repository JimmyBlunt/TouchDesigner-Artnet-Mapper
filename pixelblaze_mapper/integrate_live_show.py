"""Connect the validated show controller to an A/B GLSL preview pipeline.

This integration updates the visual pipeline while preserving source selection. It never enables
Art-Net output.  Run after ``build_show_sequencer.py`` and the core-effects
builder.  Repeated execution is idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = "/project1"
OWNER = ROOT + "/show_control"
REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "effects/effects_manifest.json"


TRANSITION_SHADER = r'''out vec4 fragColor;
uniform vec4 uTransition;

float showHash(vec2 p)
{
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

void main()
{
    vec2 uv = vUV.st;
    int mode = int(uTransition.x + 0.5);
    float progress = clamp(uTransition.y, 0.0, 1.0);
    float brightness = clamp(uTransition.z, 0.0, 1.0);
    bool blackout = uTransition.w > 0.5;

    vec4 colorA = texture(sTD2DInputs[0], uv);
    vec2 uvB = uv;
    if (mode == 5) {
        float block = floor(uv.y * 24.0);
        uvB.x = fract(uvB.x + (showHash(vec2(block, floor(progress * 30.0))) - 0.5) * 0.16 * (1.0 - progress));
    }
    vec4 colorB = texture(sTD2DInputs[1], uvB);

    vec4 result = colorA;
    if (progress <= 0.0) {
        result = colorA;
    } else if (progress >= 1.0) {
        result = texture(sTD2DInputs[1], uv);
    } else if (mode == 0) {
        result = progress >= 1.0 ? colorB : colorA;
    } else if (mode == 1) {
        result = mix(colorA, colorB, progress);
    } else {
        float reveal = 0.0;
        if (mode == 2) reveal = showHash(floor(uv * 96.0));
        else if (mode == 3) reveal = uv.x;
        else if (mode == 4) reveal = clamp(length(uv - 0.5) * 1.42, 0.0, 1.0);
        else reveal = showHash(floor(uv * vec2(40.0, 24.0)));
        result = mix(colorA, colorB, step(reveal, progress));
    }
    result.rgb *= blackout ? 0.0 : brightness;
    fragColor = TDOutputSwizzle(result);
}
'''


LED_RENDER_CALLBACK = r'''# Dynamic canonical-source Show renderer: mask each slot before mixing.
import sys
LOCAL_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)
from pixelblaze_mapper.show_renderer import render_frame, source_groups_from_panels

def _value(path, key, default=''):
    table = op(path)
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return default

def _groups(path):
    return tuple(item for item in _value(path, 'target_groups', 'all').split(',') if item)

_panel_signature = None
_panel_groups = None


def _source_groups(panels, count):
    global _panel_signature, _panel_groups
    text = panels.text
    signature = (text, count)
    if signature == _panel_signature:
        return _panel_groups
    rows = [row.split('\t') for row in text.splitlines()]
    if not rows or len(rows) != count + 1 or 'index' not in rows[0] or 'panel' not in rows[0]:
        raise RuntimeError('Show renderer requires a complete canonical panel lookup')
    header = rows[0]
    if len(set(header)) != len(header):
        raise RuntimeError('Show panel lookup headers must be unique')
    index_column, panel_column = header.index('index'), header.index('panel')
    if any(len(row) != len(header) or row[index_column] != str(index) for index, row in enumerate(rows[1:])):
        raise RuntimeError('Show panel lookup source indices must remain ordered')
    groups = source_groups_from_panels(tuple(row[panel_column] for row in rows[1:]))
    _panel_signature, _panel_groups = signature, groups
    return groups


def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onCook(scriptOp):
    slot_a, slot_b = scriptOp.inputs
    coordinates = op('effect_uv_in')
    if coordinates is None:
        raise RuntimeError('Canonical effect UV source is missing')
    count = coordinates.numSamples
    if count <= 0 or slot_a.numSamples != count or slot_b.numSamples != count:
        raise RuntimeError('Show renderer requires two slots matching the canonical UV source count')
    panels = op('/project1/pixelblaze_mapper/effect_panel_uv')
    if panels is None or panels.numRows != count + 1:
        raise RuntimeError('Show renderer requires a complete canonical panel lookup')
    source_groups = _source_groups(panels, count)
    request = 'transition_adapter/mixer_request'
    transition = _value(request, 'mode', 'cut')
    b_mix = float(_value(request, 'output_b_mix', '0'))
    brightness = float(_value(request, 'brightness', '0'))
    blackout = bool(int(float(_value(request, 'blackout', '0'))))
    targets_a = _groups('slot_a_adapter/material_request')
    targets_b = _groups('slot_b_adapter/material_request')
    # td.Channel is indexable but not iterable. Snapshot channel values once so
    # the optimized bulk renderer receives normal Python sequences.
    input_a = [slot_a[name].vals for name in ('r', 'g', 'b')]
    input_b = [slot_b[name].vals for name in ('r', 'g', 'b')]
    coord_u, coord_v = coordinates['tx'].vals, coordinates['ty'].vals
    frame = render_frame(
        input_a, input_b, u=coord_u, v=coord_v,
        transition=transition, output_b_mix=b_mix,
        brightness=brightness, blackout=blackout,
        targets_a=targets_a, targets_b=targets_b, source_groups=source_groups,
    )
    scriptOp.clear()
    scriptOp.numSamples = count
    for name, values in zip(('r', 'g', 'b'), frame):
        scriptOp.appendChan(name).vals = values
    return
'''.replace('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper', REPO_ROOT.as_posix())


def _slot_uv_source(request_path=None):
    return 'REQUEST = %r\n' % request_path + r'''import sys
LOCAL_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)
from pixelblaze_mapper.show_renderer import slot_uv_frame

def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onCook(scriptOp):
    table = op('/project1/pixelblaze_mapper/effect_panel_uv')
    if table is None or table.numRows < 2:
        raise RuntimeError('Canonical panel UV lookup unavailable')
    mode, blend = 'global', 0.5
    if REQUEST is not None:
        request = op(REQUEST)
        values = {str(request[row, 0]): str(request[row, 1]) for row in range(1, request.numRows)}
        mode, blend = values.get('mode', 'global'), float(values.get('hybrid_mix', '0.5'))
    count = table.numRows - 1
    if any(int(table[row, 'index']) != row - 1 for row in range(1, table.numRows)):
        raise RuntimeError('Canonical UV lookup indices must remain ordered')
    columns = tuple(tuple(float(table[row, key]) for row in range(1, table.numRows))
                    for key in ('global_u', 'global_v', 'local_u', 'local_v'))
    u, v = slot_uv_frame(*columns, mode=mode, hybrid_mix=blend)
    scriptOp.clear()
    scriptOp.numSamples = count
    scriptOp.appendChan('tx').vals = u
    scriptOp.appendChan('ty').vals = v
    scriptOp.appendChan('tz').vals = [0.0] * count
    return
'''.replace('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper', REPO_ROOT.as_posix())


def _get_or_create(parent, op_type, name):
    node = parent.op(name)
    return node if node is not None else parent.create(op_type, name)


def _connect(source, target, input_index=None):
    if input_index is not None:
        target.inputConnectors[input_index].disconnect()
        source.outputConnectors[0].connect(target.inputConnectors[input_index])
        return
    if source not in target.inputs:
        source.outputConnectors[0].connect(target)


def _configure_player(player, shader_path, source):
    player.par.glslversion = "glsl430"
    player.par.mode = "vertexpixel"
    player.par.pixeldat = shader_path
    player.par.outputresolution = "custom"
    player.par.resolutionw = 512
    player.par.resolutionh = 512
    player.par.vec.sequence.numBlocks = 5
    player.par.color.sequence.numBlocks = 2
    for index, name in enumerate(("uParams0", "uParams1", "uParams2", "uParams3", "uParams4")):
        player.par["vec" + str(index) + "name"] = name
    player.par.color0name = "uColorA"
    player.par.color1name = "uColorB"
    player.par.vec0valuey = 0.0
    player.par.vec1valuey = 1.0
    player.par.vec1valuez = 1.25
    player.par.vec2valuex = 0.125
    player.par.vec2valuey = 0.0
    player.par.vec2valuez = 0.0
    player.par.vec2valuew = 0.5
    player.par.vec3valuex = 2.0
    player.par.vec3valuey = 5.0
    player.par.vec3valuez = 0.5
    player.par.vec4valuex = 0.5
    player.par.vec4valuey = 0.5
    player.par.vec4valuez = 1.0
    player.par.vec4valuew = 0.0
    player.par.color0rgbr, player.par.color0rgbg, player.par.color0rgbb = (0.92, 0.08, 1.0)
    player.par.color0alpha = 1.0
    player.par.color1rgbr, player.par.color1rgbg, player.par.color1rgbb = (0.0, 0.72, 0.86)
    player.par.color1alpha = 1.0
    player.inputConnectors[0].disconnect()
    source.outputConnectors[0].connect(player)


def _render_sync_source(effect_definitions):
    catalog = {
        item["id"]: {"index": item["index"], "label": item["label"], "preset": item["preset"]}
        for item in effect_definitions
    }
    catalog.update({item["label"]: catalog[item["id"]] for item in effect_definitions})
    source = '''import json
import time
CATALOG = %s
MODES = {'global': 0, 'panel': 1, 'panel_local': 1, 'hybrid': 2}
TRANSITIONS = {'cut': 0, 'crossfade': 1, 'dissolve': 2, 'wipe': 3, 'radial': 4, 'glitch': 5}
_last_feedback = 0.0

def _set_parameter(node, name, value):
    parameter = node.par[name]
    if parameter.eval() != value:
        parameter.val = value

def _text_if_changed(path, value):
    node = op(path)
    if node is not None:
        _set_parameter(node, 'text', value)

def _network_state(value):
    table = op('state_table')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == 'network_output_enabled':
            if str(table[row, 1]) != str(value):
                table[row, 1] = value
            return
    table.appendRow(['network_output_enabled', value])

def preflight():
    data = json.loads(op('show_json').text)
    missing = [(cue['id'], cue['effect']) for cue in data['cues'] if cue['effect'] not in CATALOG]
    if missing:
        raise RuntimeError('Unresolved Show cue/effect: ' + repr(missing) + ' (Core catalog only)')

def _sender_badge():
    try:
        controls = op('/project1/madmapper_player_controls')
        source = str(controls.par.Source.eval()) if controls is not None else 'unknown'
        sender = op('/project1/multi_controller_output/artnet_510_sender_callbacks')
        if sender is None:
            raise RuntimeError('Sender unavailable')
        status = sender.module.status()
        enabled = bool(status.get('enabled'))
        badge = ('SENDER ERROR: ' + str(status['error'])) if status.get('error') else (
            'LIVE SENDING' if enabled and source == 'show' else
            'PREVIEW ONLY / OTHER SOURCE SENDING' if enabled else 'OUTPUT OFF')
        _network_state(int(enabled))
        _text_if_changed('control_panel/title', 'SHOW CONTROL | ' + badge + ' | source ' + source)
    except Exception as error:
        _network_state('unknown')
        _text_if_changed('control_panel/title', 'SHOW CONTROL | STATUS UNKNOWN | ' + str(error))

def _value(path, key, default=''):
    table = op(path)
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return default

def _apply_slot(player_name, request_path):
    player = op(player_name)
    if _value(request_path, 'status', 'EMPTY') != 'READY':
        return '-', '-', 'all'
    effect = _value(request_path, 'effect')
    if effect not in CATALOG:
        raise RuntimeError('Unresolved Show effect: ' + effect + ' (Core catalog only)')
    definition = CATALOG[effect]
    try:
        parameters = json.loads(_value(request_path, 'parameters_json', '{}'))
    except Exception as exc:
        raise RuntimeError('invalid Show preset parameters: ' + str(exc))
    required = ('speed', 'scale', 'width', 'focus_x', 'focus_y', 'zoom', 'gradient',
                'color_a', 'color_b', 'intensity', 'contrast', 'trail', 'direction',
                'rotation_degrees', 'seed', 'effect_transition', 'panel_columns',
                'panel_rows', 'hybrid_mix', 'density')
    missing = [name for name in required if name not in parameters]
    if missing:
        raise RuntimeError('incomplete Show preset parameters: ' + ', '.join(missing))
    values = dict(vec0valuex=definition['index'],
        vec0valuey=float(_value(request_path, 'animation_time', '0')) * float(parameters['speed']),
        vec0valuez=parameters['scale'], vec0valuew=parameters['width'],
        vec1valuex=MODES.get(_value(request_path, 'coordinate_mode', 'global'), 0),
        vec1valuey=parameters['intensity'], vec1valuez=parameters['contrast'], vec1valuew=parameters['trail'],
        vec2valuex=parameters['direction'], vec2valuey=parameters['rotation_degrees'],
        vec2valuez=parameters['seed'], vec2valuew=parameters['effect_transition'],
        vec3valuex=parameters['panel_columns'], vec3valuey=parameters['panel_rows'],
        vec3valuez=parameters['hybrid_mix'], vec3valuew=parameters['density'],
        vec4valuex=parameters['focus_x'], vec4valuey=parameters['focus_y'], vec4valuez=parameters['zoom'])
    for name, value in values.items():
        _set_parameter(player, name, value)
    for index, component in enumerate(('r', 'g', 'b')):
        _set_parameter(player, 'color0rgb' + component, parameters['color_a'][index])
        _set_parameter(player, 'color1rgb' + component, parameters['color_b'][index])
    _set_parameter(player, 'color0alpha', parameters['color_a'][3])
    _set_parameter(player, 'color1alpha', parameters['color_b'][3])
    return definition['label'], _value(request_path, 'preset'), _value(request_path, 'target_groups', 'all')

def sync_render():
    global _last_feedback
    label_a, preset_a, targets_a = _apply_slot('slot_a_player', 'slot_a_adapter/material_request')
    label_b, preset_b, targets_b = _apply_slot('slot_b_player', 'slot_b_adapter/material_request')
    mixer = op('show_transition_mixer')
    mode = _value('transition_adapter/mixer_request', 'mode', 'cut')
    progress = float(_value('transition_adapter/mixer_request', 'progress', '0'))
    output_b_mix = float(_value('transition_adapter/mixer_request', 'output_b_mix', '0'))
    brightness = float(_value('transition_adapter/mixer_request', 'brightness', '0'))
    blackout = int(float(_value('transition_adapter/mixer_request', 'blackout', '0')))
    for name, value in (('vec0valuex', TRANSITIONS.get(mode, 0)), ('vec0valuey', output_b_mix),
                        ('vec0valuez', brightness), ('vec0valuew', blackout)):
        _set_parameter(mixer, name, value)
    now = time.monotonic()
    if now - _last_feedback < 0.25:
        return
    _last_feedback = now
    _sender_badge()
    state = op('state_table')
    cue_index = int(float(_value('state_table', 'cue_index', '0')))
    elapsed = float(_value('state_table', 'elapsed', '0'))
    transport = _value('state_table', 'transport', 'stopped')
    outgoing_slot = _value('state_table', 'outgoing_slot', 'A')
    incoming_slot = _value('state_table', 'incoming_slot', '')
    loop = int(float(_value('state_table', 'loop', '0')))
    cue = op('cue_table')
    cue_name = str(cue[cue_index + 1, 'name']) if cue_index + 1 < cue.numRows else ''
    outgoing = (label_a, preset_a, targets_a) if outgoing_slot == 'A' else (label_b, preset_b, targets_b)
    incoming = ((label_a, preset_a, targets_a) if incoming_slot == 'A' else
                (label_b, preset_b, targets_b) if incoming_slot == 'B' else ('-', '-', '-'))
    _text_if_changed('control_panel/cue_status', 'CUE %%02d  |  %%s\\nSlot %%s: %%s / %%s  |  targets %%s  |  t=%%.2f s  |  %%s' %% (cue_index + 1, cue_name, outgoing_slot, outgoing[0], outgoing[1], outgoing[2], elapsed, transport.upper()))
    direction = outgoing_slot + (' -> ' + incoming_slot if incoming_slot else '')
    _text_if_changed('control_panel/transition_status', '%%s   %%s   %%d%%%%  |  B mix %%d%%%%\\nNext: %%s / %%s  |  Loop %%s  |  Show Blackout %%s' %% (direction, mode, round(progress * 100), round(output_b_mix * 100), incoming[0], incoming[1], 'ON' if loop else 'OFF', 'ON' if blackout else 'OFF'))
    for name, enabled in (('btn_loop', loop), ('btn_blackout', blackout)):
        button = op('control_panel/' + name)
        _set_parameter(button, 'label', ('LOOP' if name == 'btn_loop' else 'BLACKOUT') + (' ON' if enabled else ' OFF'))
        _set_parameter(button, 'bgcolorr', 0.05 if enabled else 0.04)
        _set_parameter(button, 'bgcolorg', 0.42 if enabled else 0.11)
        _set_parameter(button, 'bgcolorb', 0.24 if enabled else 0.16)
    return {'a': label_a, 'b': label_b, 'outgoing': outgoing_slot, 'incoming': incoming_slot, 'mode': mode, 'progress': progress, 'output_b_mix': output_b_mix, 'brightness': brightness, 'loop': loop, 'blackout': blackout}
''' % repr(catalog)
    from pixelblaze_mapper.show_sync_fastpath import install_render_source
    return install_render_source(source)


def integrate():
    root = op(ROOT)
    owner = op(OWNER)
    if root is None or owner is None:
        raise RuntimeError("Build core effects and show_control before live-show integration")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    controls = op(ROOT + "/madmapper_player_controls")
    selected_source = str(controls.par.Source.eval())

    source = _get_or_create(owner, selectTOP, "show_source")
    source.par.top = ROOT + "/moviefilein1"
    shader = op(ROOT + "/madmapper_material_fs")
    if shader is None:
        raise RuntimeError("Core effect shader DAT is missing")
    player_a = _get_or_create(owner, glslTOP, "slot_a_player")
    player_b = _get_or_create(owner, glslTOP, "slot_b_player")
    _configure_player(player_a, shader.path, source)
    _configure_player(player_b, shader.path, source)

    transition_dat = _get_or_create(owner, textDAT, "show_transition_fs")
    transition_dat.text = TRANSITION_SHADER
    mixer = _get_or_create(owner, glslTOP, "show_transition_mixer")
    mixer.par.glslversion = "glsl430"
    mixer.par.mode = "vertexpixel"
    mixer.par.pixeldat = transition_dat.path
    mixer.par.outputresolution = "custom"
    mixer.par.resolutionw = 512
    mixer.par.resolutionh = 512
    mixer.par.vec.sequence.numBlocks = 1
    mixer.par.vec0name = "uTransition"
    for connector in mixer.inputConnectors:
        connector.disconnect()
    _connect(player_a, mixer, 0)
    _connect(player_b, mixer, 1)
    output = _get_or_create(owner, nullTOP, "show_preview_out")
    output.inputConnectors[0].disconnect()
    mixer.outputConnectors[0].connect(output)

    standard_sampler = root.op("topto1")
    coordinates = root.op("effect_sample_uv")
    if None in (coordinates, standard_sampler):
        raise RuntimeError("Canonical effect sampler/output chain is incomplete")
    sampler_a = _get_or_create(owner, toptoCHOP, "slot_a_led_sampler")
    sampler_b = _get_or_create(owner, toptoCHOP, "slot_b_led_sampler")
    coordinate_in = _get_or_create(owner, selectCHOP, "effect_uv_in")
    global_callback = _get_or_create(owner, textDAT, 'show_global_uv_callbacks')
    global_callback.text = _slot_uv_source()
    global_uv = _get_or_create(owner, scriptCHOP, 'show_global_uv')
    global_uv.par.callbacks = global_callback.path
    coordinate_in.par.chop = global_uv.path
    for sampler, player, slot in ((sampler_a, player_a, 'a'), (sampler_b, player_b, 'b')):
        uv_callback = _get_or_create(owner, textDAT, 'slot_' + slot + '_uv_callbacks')
        uv_callback.text = _slot_uv_source('slot_' + slot + '_adapter/coordinate_request')
        slot_uv = _get_or_create(owner, scriptCHOP, 'slot_' + slot + '_uv')
        slot_uv.par.callbacks = uv_callback.path
        sampler.par.top = player.path
        if hasattr(sampler.par, "rgbaunit"):
            sampler.par.rgbaunit = "u256"
        for connector in sampler.inputConnectors:
            connector.disconnect()
        _connect(slot_uv, sampler, 0)
    led_callback = _get_or_create(owner, textDAT, "show_led_renderer_callbacks")
    led_callback.text = LED_RENDER_CALLBACK
    led_renderer = _get_or_create(owner, scriptCHOP, "show_led_renderer")
    led_renderer.par.callbacks = led_callback.path
    for connector in led_renderer.inputConnectors:
        connector.disconnect()
    _connect(sampler_a, led_renderer, 0)
    _connect(sampler_b, led_renderer, 1)
    legacy_switch = owner.op("show_live_sample_switch")
    if legacy_switch is not None:
        legacy_switch.destroy()
    renderer_out = _get_or_create(root, selectCHOP, "show_led_renderer_out")
    renderer_out.par.chop = led_renderer.path
    live_switch = _get_or_create(root, switchCHOP, "show_live_sample_switch")

    # Insert the Show switch directly after the canonical TOP-to-CHOP sampler,
    # preserving the complete downstream mapping/output chain. On a rebuild,
    # recover the already connected downstream node from the existing switch.
    if live_switch in standard_sampler.outputs:
        downstream = live_switch.outputs[0] if live_switch.outputs else None
    else:
        downstream = standard_sampler.outputs[0] if standard_sampler.outputs else None
    if downstream is None:
        raise RuntimeError("Canonical sampler downstream is missing")
    while live_switch.inputs:
        live_switch.inputConnectors[0].disconnect()
    standard_sampler.outputConnectors[0].connect(live_switch)
    live_switch.cook(force=True)
    renderer_out.outputConnectors[0].connect(live_switch.inputConnectors[-1])
    live_switch.cook(force=True)
    if len(live_switch.inputs) != 2:
        raise RuntimeError("Show live switch requires standard and Show inputs")
    live_switch.par.index.expr = "int(op('/project1/madmapper_player_controls').par.Source.eval() == 'show')"
    downstream.inputConnectors[0].disconnect()
    _connect(live_switch, downstream, 0)

    render_sync = _get_or_create(owner, textDAT, "render_sync")
    render_sync.text = _render_sync_source(manifest["effectDefinitions"])

    transport = _get_or_create(owner, executeDAT, "transport_execute")
    transport.par.active = True
    transport.par.frameend = True
    transport.text = '''_last = None
def onFrameEnd(frame):
    global _last
    now = absTime.seconds
    if _last is None:
        _last = now
        return
    delta = max(0.0, min(1.0, now - _last))
    _last = now
    if delta > 0.0:
        op('callbacks').module.advance(delta)
    return
'''

    external = root.op("show_control_out") or root.create(selectTOP, "show_control_out")
    external.par.top = output.path
    switch = op(ROOT + "/visual_source_switch")
    if external not in switch.inputs:
        external.outputConnectors[0].connect(switch)
    source_names = ["movie", "materials", "show"]
    source_labels = ["Movie / Existing Source", "Core Materials", "Show Sequencer"]
    if op(ROOT + "/madmapper_library/imported_material_out") is not None:
        source_names.append("imported")
        source_labels.append("Imported MadMapper Material")
    controls.par.Source.menuNames = source_names
    controls.par.Source.menuLabels = source_labels
    controls.par.Source = selected_source
    switch.par.index.expr = "op('/project1/madmapper_player_controls').par.Source.menuIndex"

    state = owner.op("state_table")
    for key, value in (("production_connected", 1), ("renderer_connected", 1)):
        found = False
        for row in range(1, state.numRows):
            if str(state[row, 0]) == key:
                state[row, 1] = value
                found = True
        if not found:
            state.appendRow([key, value])
    owner.op("control_panel/title").par.text = "SHOW CONTROL | READING SENDER STATUS"
    owner.op("callbacks").module.sync()
    for index, node in enumerate((source, player_a, player_b, transition_dat, mixer, output,
                                  coordinate_in, sampler_a, sampler_b, led_callback, led_renderer,
                                  render_sync, transport)):
        node.nodeX = -520 + (index % 4) * 230
        node.nodeY = -520 - (index // 4) * 150
    print({"owner": owner.path, "source": controls.par.Source.eval(),
           "rendererBridge": renderer_out.path, "liveSwitch": live_switch.path,
           "visualConnected": True, "networkOutputChanged": False})
    return owner


if "op" in globals():
    integrate()
