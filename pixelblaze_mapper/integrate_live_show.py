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
    player.par.vec.sequence.numBlocks = 4
    player.par.color.sequence.numBlocks = 2
    for index, name in enumerate(("uParams0", "uParams1", "uParams2", "uParams3")):
        player.par["vec" + str(index) + "name"] = name
    player.par.color0name = "uColorA"
    player.par.color1name = "uColorB"
    player.par.vec0valuey.expr = "absTime.seconds * 0.45"
    player.par.vec1valuey = 1.0
    player.par.vec1valuez = 1.25
    player.par.vec2valuex = 0.125
    player.par.vec2valuey = 0.0
    player.par.vec2valuez = 0.0
    player.par.vec2valuew = 0.5
    player.par.vec3valuex = 2.0
    player.par.vec3valuey = 5.0
    player.par.vec3valuez = 0.5
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
    return '''CATALOG = %s
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
    effect = _value(request_path, 'effect')
    definition = CATALOG.get(effect, CATALOG['fluid_noise'])
    preset = definition['preset']
    player.par.vec0valuex = definition['index']
    player.par.vec0valuez = preset['scale']
    player.par.vec0valuew = preset['width']
    player.par.vec1valuex = MODES.get(_value(request_path, 'coordinate_mode', 'global'), 0)
    player.par.vec1valuew = preset['trail']
    player.par.vec3valuew = preset['density']
    return definition['label']

def sync_render():
    label_a = _apply_slot('slot_a_player', 'slot_a_adapter/material_request')
    label_b = _apply_slot('slot_b_player', 'slot_b_adapter/material_request')
    mixer = op('show_transition_mixer')
    mode = _value('transition_adapter/mixer_request', 'mode', 'cut')
    progress = float(_value('transition_adapter/mixer_request', 'progress', '0'))
    brightness = float(_value('transition_adapter/mixer_request', 'brightness', '0'))
    blackout = int(float(_value('transition_adapter/mixer_request', 'blackout', '0')))
    mixer.par.vec0valuex = TRANSITIONS.get(mode, 0)
    mixer.par.vec0valuey = progress
    mixer.par.vec0valuez = brightness
    mixer.par.vec0valuew = blackout
    state = op('state_table')
    cue_index = int(float(_value('state_table', 'cue_index', '0')))
    elapsed = float(_value('state_table', 'elapsed', '0'))
    transport = _value('state_table', 'transport', 'stopped')
    cue = op('cue_table')
    cue_name = str(cue[cue_index + 1, 'name']) if cue_index + 1 < cue.numRows else ''
    op('control_panel/cue_status').par.text = 'CUE %%02d  |  %%s\\n%%s  |  %%s  |  t=%%.2f s  |  %%s' %% (cue_index + 1, cue_name, label_a, _value('slot_a_adapter/material_request', 'coordinate_mode', 'global'), elapsed, transport.upper())
    op('control_panel/transition_status').par.text = 'A -> B   %%s   %%d%%%%\\nNext: %%s  |  Brightness %%d%%%%  |  Blackout %%s' %% (mode, round(progress * 100), label_b, round(brightness * 100), 'ON' if blackout else 'OFF')
    return {'a': label_a, 'b': label_b, 'mode': mode, 'progress': progress, 'brightness': brightness, 'blackout': blackout}
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
    controls.par.Source.menuNames = ["movie", "materials", "show"]
    controls.par.Source.menuLabels = ["Movie / Existing Source", "Core Materials", "Show Sequencer"]
    switch.par.index.expr = "op('/project1/madmapper_player_controls').par.Source.menuIndex"

    state = owner.op("state_table")
    for key, value in (("production_connected", 1), ("network_output_enabled", 0)):
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
    for index, node in enumerate((source, player_a, player_b, transition_dat, mixer, output, render_sync, transport)):
        node.nodeX = -520 + (index % 4) * 230
        node.nodeY = -520 - (index // 4) * 150
    print({"owner": owner.path, "source": controls.par.Source.eval(), "visualConnected": True, "networkOutputEnabled": False})
    return owner


if "op" in globals():
    integrate()
