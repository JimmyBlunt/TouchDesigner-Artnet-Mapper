"""Connect the validated show controller to an A/B GLSL preview pipeline.

This integration modifies only the visual source selection.  It never enables
Art-Net output.  Run after ``build_show_sequencer.py`` and the core-effects
builder.  Repeated execution is idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = "/project1"
OWNER = ROOT + "/show_control"
MANIFEST = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/effects/effects_manifest.json")


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
    if (mode == 0) {
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


LED_RENDER_CALLBACK = r'''# Canonical 3,744-LED Show renderer: mask each slot before mixing.
import sys
LOCAL_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)
from pixelblaze_mapper.show_renderer import render_frame

def _value(path, key, default=''):
    table = op(path)
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return default

def _groups(path):
    return tuple(item for item in _value(path, 'target_groups', 'all').split(',') if item)

def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onCook(scriptOp):
    slot_a, slot_b = scriptOp.inputs
    coordinates = op('/project1/effect_sample_uv')
    if coordinates is None:
        raise RuntimeError('Canonical effect UV source is missing')
    count = coordinates.numSamples
    if slot_a.numSamples != count or slot_b.numSamples != count or count != 3744:
        raise RuntimeError('Show renderer requires two 3,744-sample slots and canonical UV')
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
        targets_a=targets_a, targets_b=targets_b,
    )
    scriptOp.clear()
    scriptOp.numSamples = count
    for name, values in zip(('r', 'g', 'b'), frame):
        scriptOp.appendChan(name).vals = values
    return
'''


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
    return '''import json
CATALOG = %s
MODES = {'global': 0, 'panel': 1, 'panel_local': 1, 'hybrid': 2}
TRANSITIONS = {'cut': 0, 'crossfade': 1, 'dissolve': 2, 'wipe': 3, 'radial': 4, 'glitch': 5}

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
    definition = CATALOG.get(effect, CATALOG['fluid_noise'])
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
    player.par.vec0valuex = definition['index']
    player.par.vec0valuey = float(_value('state_table', 'elapsed', '0')) * float(parameters['speed'])
    player.par.vec0valuez = parameters['scale']
    player.par.vec0valuew = parameters['width']
    player.par.vec1valuex = MODES.get(_value(request_path, 'coordinate_mode', 'global'), 0)
    player.par.vec1valuey = parameters['intensity']
    player.par.vec1valuez = parameters['contrast']
    player.par.vec1valuew = parameters['trail']
    player.par.vec2valuex = parameters['direction']
    player.par.vec2valuey = parameters['rotation_degrees']
    player.par.vec2valuez = parameters['seed']
    player.par.vec2valuew = parameters['effect_transition']
    player.par.vec3valuex = parameters['panel_columns']
    player.par.vec3valuey = parameters['panel_rows']
    player.par.vec3valuez = parameters['hybrid_mix']
    player.par.vec3valuew = parameters['density']
    player.par.vec4valuex = parameters['focus_x']
    player.par.vec4valuey = parameters['focus_y']
    player.par.vec4valuez = parameters['zoom']
    for index, component in enumerate(('r', 'g', 'b')):
        player.par['color0rgb' + component] = parameters['color_a'][index]
        player.par['color1rgb' + component] = parameters['color_b'][index]
    player.par.color0alpha = parameters['color_a'][3]
    player.par.color1alpha = parameters['color_b'][3]
    return definition['label'], _value(request_path, 'preset'), _value(request_path, 'target_groups', 'all')

def sync_render():
    label_a, preset_a, targets_a = _apply_slot('slot_a_player', 'slot_a_adapter/material_request')
    label_b, preset_b, targets_b = _apply_slot('slot_b_player', 'slot_b_adapter/material_request')
    mixer = op('show_transition_mixer')
    mode = _value('transition_adapter/mixer_request', 'mode', 'cut')
    progress = float(_value('transition_adapter/mixer_request', 'progress', '0'))
    output_b_mix = float(_value('transition_adapter/mixer_request', 'output_b_mix', '0'))
    brightness = float(_value('transition_adapter/mixer_request', 'brightness', '0'))
    blackout = int(float(_value('transition_adapter/mixer_request', 'blackout', '0')))
    mixer.par.vec0valuex = TRANSITIONS.get(mode, 0)
    mixer.par.vec0valuey = output_b_mix
    mixer.par.vec0valuez = brightness
    mixer.par.vec0valuew = blackout
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
    op('control_panel/cue_status').par.text = 'CUE %%02d  |  %%s\\nSlot %%s: %%s / %%s  |  targets %%s  |  t=%%.2f s  |  %%s' %% (cue_index + 1, cue_name, outgoing_slot, outgoing[0], outgoing[1], outgoing[2], elapsed, transport.upper())
    direction = outgoing_slot + (' -> ' + incoming_slot if incoming_slot else '')
    op('control_panel/transition_status').par.text = '%%s   %%s   %%d%%%%  |  B mix %%d%%%%\\nNext: %%s / %%s  |  Loop %%s  |  Blackout %%s' %% (direction, mode, round(progress * 100), round(output_b_mix * 100), incoming[0], incoming[1], 'ON' if loop else 'OFF', 'ON' if blackout else 'OFF')
    for name, enabled in (('btn_loop', loop), ('btn_blackout', blackout)):
        button = op('control_panel/' + name)
        button.par.label = ('LOOP' if name == 'btn_loop' else 'BLACKOUT') + (' ON' if enabled else ' OFF')
        button.par.bgcolorr = 0.05 if enabled else 0.04
        button.par.bgcolorg = 0.42 if enabled else 0.11
        button.par.bgcolorb = 0.24 if enabled else 0.16
    return {'a': label_a, 'b': label_b, 'outgoing': outgoing_slot, 'incoming': incoming_slot, 'mode': mode, 'progress': progress, 'output_b_mix': output_b_mix, 'brightness': brightness, 'loop': loop, 'blackout': blackout}
''' % repr(catalog)


def integrate():
    root = op(ROOT)
    owner = op(OWNER)
    if root is None or owner is None:
        raise RuntimeError("Build core effects and show_control before live-show integration")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

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
    coordinate_in.par.chop = coordinates.path
    for sampler, player in ((sampler_a, player_a), (sampler_b, player_b)):
        sampler.par.top = player.path
        if hasattr(sampler.par, "rgbaunit"):
            sampler.par.rgbaunit = "u256"
        for connector in sampler.inputConnectors:
            connector.disconnect()
        _connect(coordinate_in, sampler, 0)
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
    controls = op(ROOT + "/madmapper_player_controls")
    source_names = ["movie", "materials", "show"]
    source_labels = ["Movie / Existing Source", "Core Materials", "Show Sequencer"]
    if op(ROOT + "/madmapper_library/imported_material_out") is not None:
        source_names.append("imported")
        source_labels.append("Imported MadMapper Material")
    controls.par.Source.menuNames = source_names
    controls.par.Source.menuLabels = source_labels
    switch.par.index.expr = "op('/project1/madmapper_player_controls').par.Source.menuIndex"

    state = owner.op("state_table")
    for key, value in (("production_connected", 1), ("renderer_connected", 1),
                       ("network_output_enabled", 0)):
        found = False
        for row in range(1, state.numRows):
            if str(state[row, 0]) == key:
                state[row, 1] = value
                found = True
        if not found:
            state.appendRow([key, value])
    owner.op("control_panel/title").par.text = "SHOW CONTROL  |  A/B LIVE PREVIEW  |  ART-NET SAFE"
    owner.op("callbacks").module.sync()
    controls.par.Source = "show"
    for index, node in enumerate((source, player_a, player_b, transition_dat, mixer, output,
                                  coordinate_in, sampler_a, sampler_b, led_callback, led_renderer,
                                  render_sync, transport)):
        node.nodeX = -520 + (index % 4) * 230
        node.nodeY = -520 - (index // 4) * 150
    print({"owner": owner.path, "source": controls.par.Source.eval(),
           "rendererBridge": renderer_out.path, "liveSwitch": live_switch.path,
           "visualConnected": True, "networkOutputEnabled": False})
    return owner


if "op" in globals():
    integrate()
