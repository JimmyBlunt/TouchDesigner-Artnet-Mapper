"""Build the isolated TouchDesigner show-control adapter and transport panel.

Run in a TouchDesigner Text DAT with::

    exec(open(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/'
              r'pixelblaze_mapper/build_show_sequencer.py').read())

Only ``/project1/show_control`` and its descendants are created or updated.
The builder never connects to production nodes, enables output, or saves the
project.  The two TOP slots are intentionally explicit adapter endpoints.
"""

from __future__ import annotations

import json
from pathlib import Path
import re


OWNER = "/project1/show_control"
DEMO_SHOW = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/shows/demo_show.json")


def _get_or_create(parent, op_type, name):
    node = op(parent.path + "/" + name)
    if node is not None:
        return node
    # Some Palette-derived COMPs (notably Button COMP) ignore the requested
    # name during creation and append a number.  Adopt and normalize such a
    # node so a second builder run cannot duplicate the UI.
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


def _table(node, rows):
    node.clear()
    for row in rows:
        node.appendRow(row)


def _fixed(node, x, y, width, height):
    node.par.hmode = "fixed"
    node.par.vmode = "fixed"
    node.par.x, node.par.y = x, y
    node.par.w, node.par.h = width, height
    node.par.display = True


def _text(canvas, name, value, x, y, width, height, size=13, color=(0.8, 0.87, 0.94)):
    node = _get_or_create(canvas, textCOMP, name)
    _fixed(node, x, y, width, height)
    node.par.text = value
    node.par.type = "multiline"
    node.par.wordwrap = True
    node.par.font = "Verdana"
    node.par.fontsize = size
    node.par.fontcolorr, node.par.fontcolorg, node.par.fontcolorb = color
    node.par.fontalpha = 1
    node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = (0.015, 0.025, 0.038)
    node.par.bgalpha = 1
    node.par.alignx, node.par.aligny = "left", "center"
    node.par.textpaddingl = 10
    node.par.layer = 10
    node.par.clickthrough = True
    return node


def _button(canvas, name, label, x, width, toggle=False):
    node = _get_or_create(canvas, buttonCOMP, name)
    _fixed(node, x, 25, width, 42)
    node.par.label = label
    # Semantic loop/blackout toggles use one momentary pulse on every click.
    node.par.buttontype = "momentary"
    node.par.value0 = False
    node.par.fontsize = 12
    node.par.cursor = "pointer"
    node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = (0.04, 0.11, 0.16)
    node.par.bgalpha = 1
    node.par.layer = 20
    return node


def _load_demo():
    return json.loads(DEMO_SHOW.read_text(encoding="utf-8"))


def build():
    project_root = op("/project1")
    if project_root is None:
        raise RuntimeError("/project1 was not found")
    owner = _get_or_create(project_root, baseCOMP, "show_control")
    owner.nodeX, owner.nodeY = 900, -300
    for child in owner.children:
        if child.type == 'panelexec':
            child.par.active = False

    old_show = owner.op('show_json')
    data = json.loads(old_show.text) if old_show is not None and old_show.text.strip() else _load_demo()
    cues = _get_or_create(owner, tableDAT, "cue_table")
    cue_rows = [[
        "id", "name", "effect", "preset", "parameters_json", "coordinate_mode", "duration",
        "transition", "transition_duration", "brightness", "target_groups",
    ]]
    for cue in data["cues"]:
        cue_rows.append([
            cue["id"], cue["name"], cue["effect"], cue["preset"],
            json.dumps(cue["parameters"], separators=(",", ":")),
            cue["coordinate_mode"], cue["duration"], cue["transition"],
            cue["transition_duration"], cue["brightness"],
            ",".join(cue["target_groups"]),
        ])
    _table(cues, cue_rows)

    state = _get_or_create(owner, tableDAT, "state_table")
    # Preserve transport state on an idempotent rebuild; initialize only once.
    state_defaults = [
        ["transport", "stopped"], ["cue_index", 0], ["elapsed", 0.0],
        ["loop", int(data["loop"])], ["blackout", 0],
        ["transport_request", ""], ["outgoing_slot", "A"],
        ["incoming_slot", "B"], ["transition", "cut"], ["progress", 0.0],
        ["output_b_mix", 0.0], ["production_connected", 0],
        ["network_output_enabled", 0],
        ["slot_time_offset", 0.0],
    ]
    if state.numRows < 2:
        _table(state, [["key", "value"]] + state_defaults)
    else:
        existing_keys = {str(state[row, 0]) for row in range(1, state.numRows)}
        for row in state_defaults:
            if row[0] not in existing_keys:
                state.appendRow(row)

    show_json = _get_or_create(owner, textDAT, "show_json")
    show_json.text = json.dumps(data, indent=2)

    modes = _get_or_create(owner, tableDAT, "transition_modes")
    _table(modes, [
        ["name", "parameter", "meaning"],
        ["cut", "progress", "instant switch at cue boundary"],
        ["crossfade", "progress", "linear A/B blend"],
        ["dissolve", "progress", "threshold/noise reveal"],
        ["wipe", "progress", "linear spatial reveal"],
        ["radial", "progress", "radial spatial reveal"],
        ["glitch", "progress", "segmented/noisy reveal"],
    ])

    for slot_name in ("slot_a_adapter", "slot_b_adapter"):
        adapter = _get_or_create(owner, baseCOMP, slot_name)
        request = _get_or_create(adapter, tableDAT, "material_request")
        _table(request, [["key", "value"], ["status", "UNCONNECTED"],
                         ["effect", ""], ["preset", ""],
                         ["parameters_json", "{}"], ["target_groups", "all"],
                         ["coordinate_mode", "global"],
                         ["production_connected", 0]])
        uv_request = _get_or_create(adapter, tableDAT, 'coordinate_request')
        if uv_request.numRows < 2:
            _table(uv_request, [['key', 'value'], ['mode', 'global'], ['hybrid_mix', 0.5]])
        endpoint = _get_or_create(adapter, nullTOP, "material_top_in")
        endpoint.nodeX, endpoint.nodeY = 0, 0
        readme = _get_or_create(adapter, textDAT, "README")
        readme.text = (
            "Isolated A/B input adapter. Connect a future material resolver inside "
            "show_control only. This builder never rewires production."
        )

    mixer = _get_or_create(owner, baseCOMP, "transition_adapter")
    mixer_config = _get_or_create(mixer, tableDAT, "mixer_request")
    _table(mixer_config, [
        ["key", "value"], ["mode", "cut"], ["progress", 0.0],
        ["output_b_mix", 0.0], ["brightness", 0.0], ["blackout", 0],
        ["status", "UNCONNECTED"],
    ])
    _get_or_create(mixer, nullTOP, "slot_a_in")
    _get_or_create(mixer, nullTOP, "slot_b_in")
    _get_or_create(mixer, nullTOP, "show_preview_out")

    callbacks = _get_or_create(owner, textDAT, "callbacks")
    callbacks.text = '''# Isolated transport UI callbacks; adapters only, no production writes.
import json
import sys
LOCAL_ROOT = r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer, TransportState

def _set(key, value):
    table = op('state_table')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            if str(table[row, 1]) != str(value):
                table[row, 1] = value
            return
    table.appendRow([key, value])

def _get(key, fallback=0):
    table = op('state_table')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return fallback

def _put(table_path, key, value):
    table = op(table_path)
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            if str(table[row, 1]) != str(value):
                table[row, 1] = value
            return
    table.appendRow([key, value])

def runtime():
    owner = op('callbacks').parent()
    signature = op('show_json').text
    record = owner.fetch('show_runtime_record', None)
    if not record or record[0] != signature or not isinstance(record[1], ShowSequencer):
        sequence = ShowSequencer(Show.from_dict(json.loads(signature)))
        # Rebuild/module reload restores transport; it is not a PLAY/STOP command.
        index = int(_get('cue_index', 0))
        if 0 <= index < len(sequence.show.cues):
            sequence.cue_index = index
            sequence.elapsed = min(sequence.cue.duration, max(0.0, float(_get('elapsed', 0))))
            sequence._current_slot = str(_get('outgoing_slot', 'A'))
            sequence._current_time_offset = max(0.0, float(_get('slot_time_offset', 0)))
        sequence.set_loop(bool(int(_get('loop', int(sequence.show.loop)))))
        sequence.set_blackout(bool(int(_get('blackout', 0))))
        sequence.state = TransportState(str(_get('transport', 'stopped')))
        record = (signature, sequence)
        owner.store('show_runtime_record', record)
    return record[1]

def sync():
    sequence = runtime()
    plan = sequence.plan()
    _set('transport', sequence.state.value)
    _set('cue_index', sequence.cue_index)
    _set('elapsed', sequence.elapsed)
    _set('slot_time_offset', getattr(sequence, '_current_time_offset', 0.0))
    _set('loop', int(sequence.show.loop))
    _set('blackout', int(sequence.blackout))
    _set('outgoing_slot', plan.outgoing_slot)
    _set('incoming_slot', plan.incoming_slot or '')
    _set('transition', plan.transition)
    _set('progress', plan.progress)
    _set('output_b_mix', plan.output_b_mix)
    for path, slot, slot_time in (('slot_a_adapter/material_request', plan.slot_a, plan.slot_a_time),
                                 ('slot_b_adapter/material_request', plan.slot_b, plan.slot_b_time)):
        _put(path, 'status', 'READY' if slot else 'EMPTY')
        _put(path, 'effect', slot.effect if slot else '')
        _put(path, 'preset', slot.preset if slot else '')
        _put(path, 'parameters_json', json.dumps(slot.parameters.to_dict(), separators=(',', ':')) if slot else '{}')
        _put(path, 'target_groups', ','.join(slot.target_groups) if slot else 'all')
        _put(path, 'coordinate_mode', slot.coordinate_mode if slot else '')
        _put(path, 'animation_time', slot_time)
        uv_path = path.replace('material_request', 'coordinate_request')
        _put(uv_path, 'mode', slot.coordinate_mode if slot else 'global')
        _put(uv_path, 'hybrid_mix', slot.parameters.hybrid_mix if slot else 0.5)
    _put('transition_adapter/mixer_request', 'mode', plan.transition)
    _put('transition_adapter/mixer_request', 'progress', plan.progress)
    _put('transition_adapter/mixer_request', 'output_b_mix', plan.output_b_mix)
    _put('transition_adapter/mixer_request', 'brightness', plan.brightness)
    _put('transition_adapter/mixer_request', 'blackout', int(plan.blackout))
    _put('transition_adapter/mixer_request', 'outgoing_slot', plan.outgoing_slot)
    _put('transition_adapter/mixer_request', 'incoming_slot', plan.incoming_slot or '')
    _put('transition_adapter/mixer_request', 'loop', int(sequence.show.loop))
    _put('transition_adapter/mixer_request', 'status', 'READY')
    render = op('render_sync')
    if render is not None:
        render.module.sync_render()
    return plan

def command(name):
    sequence = runtime()
    render = op('render_sync')
    if name in ('play', 'go', 'next', 'previous') and render is not None and hasattr(render.module, 'preflight'):
        render.module.preflight()
    if name == 'play': sequence.play()
    elif name == 'pause': sequence.pause()
    elif name == 'stop': sequence.stop()
    elif name == 'previous': sequence.previous()
    elif name == 'next': sequence.next()
    elif name == 'go': sequence.go()
    elif name == 'loop': sequence.set_loop(not sequence.show.loop)
    elif name == 'blackout': sequence.toggle_blackout()
    else: raise ValueError('unknown transport command: ' + str(name))
    _set('transport_request', name)
    sync()
    return name

def advance(seconds):
    runtime().advance(seconds)
    return sync()

'''

    canvas = _get_or_create(owner, containerCOMP, "control_panel")
    _fixed(canvas, 0, 0, 1000, 300)
    canvas.par.bgcolorr, canvas.par.bgcolorg, canvas.par.bgcolorb = (0.008, 0.015, 0.025)
    canvas.par.bgalpha = 1
    _text(canvas, "title", "SHOW CONTROL | SENDER STATUS NOT YET READ", 20, 232, 960, 50, 18, (0.35, 0.86, 0.98))
    _text(canvas, "cue_status", "CUE 01 · Fluid Opening\nFluid Noise / Ocean Blue · global · 20.0 s", 20, 130, 470, 86, 15)
    _text(canvas, "transition_status", "A → B   crossfade   0%\nBrightness 20% · targets: all", 510, 130, 470, 86, 15)
    button_specs = [
        ("btn_previous", "PREV", 20, 86, False), ("btn_play", "PLAY", 116, 86, False),
        ("btn_pause", "PAUSE", 212, 86, False), ("btn_stop", "STOP", 308, 86, False),
        ("btn_next", "NEXT", 404, 86, False), ("btn_go", "GO", 500, 110, False),
        ("btn_loop", "LOOP", 620, 100, True), ("btn_blackout", "BLACKOUT", 730, 120, True),
    ]
    for name, label, x, width, toggle in button_specs:
        button = _button(canvas, name, label, x, width, toggle)
        click = _get_or_create(owner, panelexecuteDAT, "click_" + name[4:])
        click.par.active = False
        click.par.fromop = button.path
        click.par.panels = button.path
        click.par.panelvalue = "lselect"
        click.par.offtoon = True
        click.par.ontooff = False
        click.par.whileon = False
        click.par.whileoff = False
        click.par.valuechange = False
        command = name[4:]
        click.text = "def onOffToOn(panelValue):\n    op('callbacks').module.command(%r)\n    return\n" % command
        click.par.active = True

    preview = _get_or_create(owner, opviewerTOP, "control_panel_preview")
    preview.par.opviewer = canvas.path
    preview.par.allowpanel = True
    preview.par.outputresolution = "custom"
    preview.par.resolutionw, preview.par.resolutionh = 1000, 300
    preview.viewer = True

    interface = _get_or_create(owner, tableDAT, "adapter_contract")
    _table(interface, [
        ["endpoint", "direction", "state", "description"],
        ["cue_table", "show -> host", "READY", "validated cue definitions"],
        ["state_table", "core -> host", "READY", "deterministic transport state"],
        ["slot_a_adapter/material_request", "host -> material", "UNCONNECTED", "A material request"],
        ["slot_b_adapter/material_request", "host -> material", "UNCONNECTED", "B material request"],
        ["transition_adapter/mixer_request", "host -> mixer", "UNCONNECTED", "transition plan"],
        ["transition_adapter/show_preview_out", "mixer -> preview", "UNCONNECTED", "preview only"],
        ["production", "show_control -> output", "DISABLED", "must be integrated explicitly later"],
    ])

    readme = _get_or_create(owner, textDAT, "README_show_control")
    readme.text = (
        "Isolated A/B show-control scaffold. Core transport: "
        "pixelblaze_mapper.show_sequencer. No production nodes are inspected or "
        "rewired. No Art-Net output is enabled. The builder does not save the project."
    )
    callbacks.module.sync()
    print({"owner": owner.path, "cues": len(data["cues"]),
           "productionTouched": False, "outputEnabled": False, "projectSaved": False})
    return owner


if "op" in globals():
    build()
