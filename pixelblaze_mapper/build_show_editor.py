"""Extend the Show Control panel into a full cue editor.

Run inside TouchDesigner AFTER build_show_sequencer.py, in a scope that has
the TouchDesigner globals (``op`` and the OP type constructors)::

    scope = dict(globals()); scope['__name__'] = '__main__'
    scope['__file__'] = PATH
    exec(compile(open(PATH).read(), PATH, 'exec'), scope, scope)
    scope['build']()

Only ``/project1/show_control/control_panel`` and a handful of siblings are
created or updated. No production node is touched, no output is enabled and
the project is never saved here.
"""

from __future__ import annotations

PANEL_WIDTH = 1000
TRANSPORT_HEIGHT = 300
PANEL_HEIGHT = 1000
ROW_COUNT = 10
ROW_HEIGHT = 26
ROW_TOP = 846
OWNER_PATH = "/project1/show_control"

INK = (0.80, 0.87, 0.94)
DIM = (0.55, 0.63, 0.72)
ACCENT = (0.35, 0.86, 0.98)
PANEL_BG = (0.015, 0.025, 0.038)
ROW_BG = (0.022, 0.034, 0.049)
ROW_SELECTED = (0.05, 0.14, 0.20)


def _get_or_create(parent, op_type, name):
    node = parent.op(name)
    if node is not None:
        return node
    node = parent.create(op_type, name)
    node.name = name
    return node


def _set(node, name, value):
    par = getattr(node.par, name, None)
    if par is not None:
        par.val = value


def paint_button(node, color, ink=(0.90, 0.94, 0.98)):
    """Give a buttonCOMP the colour it was asked for.

    A buttonCOMP ignores its own Bgcolor: the inner `text` child draws the
    button, and its stock expressions derive the fill from the parent's text
    Color, scaled to 40%. Every coloured button in this panel was therefore
    the same grey - the record button included, which is the one that is
    supposed to shout. Writing the inner text is what actually paints it; the
    rollover brightening stays.
    """

    text = node.op("text")
    if text is None:
        return node
    rollover = "op('%s').panel.rollover" % node.path
    for channel, value in (("bgcolorr", color[0]), ("bgcolorg", color[1]), ("bgcolorb", color[2])):
        par = getattr(text.par, channel, None)
        if par is None:
            continue
        par.expr = "%s + 0.07 * %s" % (round(float(value), 4), rollover)
        par.mode = par.mode.__class__.EXPRESSION
    for channel, value in (("fontcolorr", ink[0]), ("fontcolorg", ink[1]), ("fontcolorb", ink[2])):
        par = getattr(text.par, channel, None)
        if par is not None:
            par.mode = par.mode.__class__.CONSTANT
            par.val = value
    return node


def _place(node, x, y, width, height, layer=50):
    for name, value in (("hmode", "fixed"), ("vmode", "fixed"), ("x", x), ("y", y),
                        ("w", width), ("h", height), ("display", True), ("layer", layer)):
        _set(node, name, value)
    return node


def build():
    owner = op(OWNER_PATH)
    if owner is None:
        raise RuntimeError("Show Control is not built yet; run build_show_sequencer.py first")
    canvas = owner.op("control_panel")
    if canvas is None:
        raise RuntimeError("control_panel is missing; run build_show_sequencer.py first")

    callbacks = _get_or_create(owner, textDAT, "editor_callbacks")
    callbacks.clear()
    callbacks.write(EDITOR_RUNTIME)

    # The transport keeps the bottom 300 px it was built with; the editor is
    # added above it, so re-running the base builder cannot move the buttons.
    _set(canvas, "h", PANEL_HEIGHT)
    _set(canvas, "w", PANEL_WIDTH)

    def text(name, value, x, y, width, height, size=12, color=INK,
             background=PANEL_BG, align="left"):
        node = _get_or_create(canvas, textCOMP, name)
        _place(node, x, y, width, height, 10)
        for par, item in (("text", value), ("type", "multiline"), ("wordwrap", False),
                          ("font", "Verdana"), ("fontsize", size), ("fontalpha", 1),
                          ("fontcolorr", color[0]), ("fontcolorg", color[1]),
                          ("fontcolorb", color[2]), ("bgalpha", 1),
                          ("bgcolorr", background[0]), ("bgcolorg", background[1]),
                          ("bgcolorb", background[2]), ("alignx", align),
                          ("aligny", "center"), ("textpaddingl", 8), ("clickthrough", True)):
            _set(node, par, item)
        return node

    def button(name, label, x, y, width, height=34, color=(0.05, 0.13, 0.19), size=11):
        node = _get_or_create(canvas, buttonCOMP, name)
        _place(node, x, y, width, height, 60)
        for par, item in (("buttontype", "momentary"), ("label", label), ("fontsize", size),
                          ("fontalpha", 1), ("bgalpha", 1), ("bgcolorr", color[0]),
                          ("bgcolorg", color[1]), ("bgcolorb", color[2]), ("cursor", "pointer")):
            _set(node, par, item)
        paint_button(node, color)
        return node

    def field(name, x, y, width, height=34):
        node = _get_or_create(canvas, fieldCOMP, name)
        _place(node, x, y, width, height, 60)
        for par, item in (("fieldtype", "string"), ("fontsize", 12), ("bgalpha", 1),
                          ("fontalpha", 1), ("cursor", "ibeam")):
            _set(node, par, item)
        return node

    def click(node, command):
        name = "ed_click_" + node.name
        exec_dat = owner.op(name)
        if exec_dat is not None and exec_dat.type != "panelexec":
            exec_dat.destroy()
            exec_dat = None
        exec_dat = exec_dat or owner.create(panelexecuteDAT, name)
        exec_dat.name = name
        exec_dat.par.active = False
        exec_dat.par.fromop = node.path
        exec_dat.par.panels = node.path
        exec_dat.par.panelvalue = "lselect"
        for par, value in (("offtoon", True), ("ontooff", False), ("whileon", False),
                           ("whileoff", False), ("valuechange", False)):
            _set(exec_dat, par, value)
        exec_dat.clear()
        exec_dat.write("def onOffToOn(panelValue):\n"
                       "    op(%r).module.action(%r)\n    return\n"
                       % (callbacks.path, command))
        exec_dat.par.active = True
        return exec_dat

    text("ed_title", "SHOW EDITOR", 20, 952, 960, 34, 17, ACCENT)

    field("ed_show_name", 20, 908, 300)
    click(button("ed_btn_loop", "LOOP", 330, 908, 110), "toggle_loop")
    click(button("ed_btn_new", "NEUE SHOW", 450, 908, 110), "new_show")
    click(button("ed_btn_save", "SPEICHERN", 570, 908, 140, color=(0.06, 0.16, 0.12)), "save_show")
    click(button("ed_btn_load", "LADEN", 720, 908, 140), "load_show")
    text("ed_show_info", "", 870, 908, 110, 34, 11, DIM, align="center")

    text("ed_list_head", "  #   NAME                        EFFEKT              DAUER          "
                         "UEBERGANG      MODUS        VERLAUF", 20, 872, 960, 24, 11, DIM)
    for index in range(ROW_COUNT):
        row = button("ed_row_%d" % index, "", 20, ROW_TOP - index * ROW_HEIGHT, 960,
                     ROW_HEIGHT - 2, ROW_BG, 11)
        _set(row, "alignx", "left")
        click(row, "select_%d" % index)

    click(button("ed_btn_page_prev", "<", 20, 574, 60, 30), "page_prev")
    text("ed_page_info", "", 90, 574, 220, 30, 11, DIM, align="center")
    click(button("ed_btn_page_next", ">", 320, 574, 60, 30), "page_next")
    text("ed_selection_info", "", 400, 574, 580, 30, 11, ACCENT)

    click(button("ed_btn_add", "+ AKTUELLES MATERIAL", 20, 528, 250, 38,
                 (0.06, 0.18, 0.14), 12), "add_material")
    click(button("ed_btn_duplicate", "DUPLIZIEREN", 280, 528, 140, 38), "duplicate")
    click(button("ed_btn_delete", "LOESCHEN", 430, 528, 120, 38, (0.20, 0.06, 0.07)), "delete")
    click(button("ed_btn_up", "NACH OBEN", 560, 528, 120, 38), "move_up")
    click(button("ed_btn_down", "NACH UNTEN", 690, 528, 120, 38), "move_down")
    text("ed_hint", "", 820, 528, 160, 38, 10, DIM)

    for name, label, x, width in (("ed_lbl_name", "NAME", 20, 300),
                                  ("ed_lbl_duration", "DAUER s", 330, 120),
                                  ("ed_lbl_transdur", "UEBERGANG s", 460, 120),
                                  ("ed_lbl_brightness", "HELLIGKEIT 0..1", 590, 120)):
        text(name, label, x, 490, width, 22, 10, DIM)
    field("ed_cue_name", 20, 452, 300)
    field("ed_cue_duration", 330, 452, 120)
    field("ed_cue_transdur", 460, 452, 120)
    field("ed_cue_brightness", 590, 452, 120)
    click(button("ed_btn_apply", "UEBERNEHMEN", 720, 452, 140, 34, (0.06, 0.16, 0.12), 12), "apply_fields")

    for name, label, x, width in (("ed_lbl_trans", "UEBERGANG", 20, 270),
                                  ("ed_lbl_mode", "KOORDINATEN", 330, 226),
                                  ("ed_lbl_grad", "FARBVERLAUF", 570, 266)):
        text(name, label, x, 410, width, 22, 10, DIM)
    click(button("ed_btn_trans_prev", "<", 20, 372, 34, 34), "trans_prev")
    text("ed_cue_trans", "", 58, 372, 194, 34, 11, INK, ROW_BG, "center")
    click(button("ed_btn_trans_next", ">", 256, 372, 34, 34), "trans_next")
    click(button("ed_btn_mode_prev", "<", 330, 372, 34, 34), "mode_prev")
    text("ed_cue_mode", "", 368, 372, 150, 34, 11, INK, ROW_BG, "center")
    click(button("ed_btn_mode_next", ">", 522, 372, 34, 34), "mode_next")
    click(button("ed_btn_grad_prev", "<", 570, 372, 34, 34), "grad_prev")
    text("ed_cue_grad", "", 608, 372, 190, 34, 11, INK, ROW_BG, "center")
    click(button("ed_btn_grad_next", ">", 802, 372, 34, 34), "grad_next")

    click(button("ed_btn_record", "AUFNAHME", 20, 326, 200, 36, (0.22, 0.07, 0.09), 12), "toggle_record")
    click(button("ed_btn_record_new", "AUFNAHME -> NEUE CUE", 230, 326, 220, 36,
                 (0.16, 0.08, 0.20), 12), "record_new")
    click(button("ed_btn_record_clear", "AUFNAHME LOESCHEN", 460, 326, 190, 36), "clear_record")
    text("ed_record_info", "", 660, 326, 320, 36, 11, DIM)

    # A freshly created Table DAT already holds one empty cell, so test for the
    # header instead of an empty table; otherwise the keys are never written
    # and every lookup silently falls back to its default.
    _build_imported_slots(owner)

    state = _get_or_create(owner, tableDAT, "editor_state")
    defaults = (("selected", "0"), ("page", "0"), ("recording", "0"),
                ("record_cue", ""), ("recording_new", "0"), ("core_moved", "0"),
                ("message", ""))
    if state.numRows < 2 or str(state[0, 0]) != "key":
        state.clear()
        state.appendRow(["key", "value"])
        for key, value in defaults:
            state.appendRow([key, value])
    else:
        present = {str(state[row, 0]) for row in range(1, state.numRows)}
        for key, value in defaults:
            if key not in present:
                state.appendRow([key, value])

    imported = _get_or_create(owner, textDAT, "imported_json")
    if not imported.text.strip():
        imported.clear()
        imported.write("{}")

    automation = _get_or_create(owner, textDAT, "automation_json")
    if not automation.text.strip():
        automation.clear()
        automation.write('{"schema": "pixelblaze-show-automation", "version": 1, "tracks": {}}')

    preview = owner.op("control_panel_preview")
    if preview is not None:
        _set(preview, "resolutionw", PANEL_WIDTH)
        _set(preview, "resolutionh", PANEL_HEIGHT)

    callbacks.module.repaint()
    print({"owner": canvas.path, "rows": ROW_COUNT, "height": PANEL_HEIGHT,
           "productionTouched": False, "outputEnabled": False, "projectSaved": False})
    return canvas



def _build_imported_slots(owner):
    """Give each A/B slot a second renderer for imported MadMapper materials.

    The core player runs one shared shader with an effect index; an imported
    material is its own adapted fragment shader, so it needs its own GLSL TOP.
    A switch per slot feeds both consumers - the LED sampler reads it through
    its `top` parameter, the preview mixer through its input - so routing a cue
    is one index, and the core path is byte-for-byte what it was.
    """

    source = owner.op("show_source")
    mixer = owner.op("show_transition_mixer")
    if source is None or mixer is None:
        raise RuntimeError("Show slots are not integrated yet; run integrate_live_show.py first")
    for position, slot in enumerate(("a", "b")):
        player = owner.op("slot_%s_player" % slot)
        sampler = owner.op("slot_%s_led_sampler" % slot)
        if player is None or sampler is None:
            raise RuntimeError("Show slot %s is missing" % slot.upper())
        shader = _get_or_create(owner, textDAT, "slot_%s_import_fs" % slot)
        if not shader.text.strip():
            shader.clear()
            shader.write(IMPORT_PLACEHOLDER_SHADER)
        renderer = _get_or_create(owner, glslTOP, "slot_%s_import" % slot)
        _set(renderer, "pixeldat", shader.path)
        for name, value in (("outputresolution", "custom"),
                            ("resolutionw", player.par.resolutionw.eval()),
                            ("resolutionh", player.par.resolutionh.eval())):
            _set(renderer, name, value)
        if not renderer.inputs:
            source.outputConnectors[0].connect(renderer)
        renderer.nodeX, renderer.nodeY = player.nodeX, player.nodeY - 180
        mux = _get_or_create(owner, switchTOP, "slot_%s_mux" % slot)
        mux.nodeX, mux.nodeY = player.nodeX + 200, player.nodeY - 90
        # Never loop on .inputs here: disconnecting connector 0 while connector
        # 1 stays wired leaves .inputs non-empty, and `while node.inputs` then
        # spins forever on TouchDesigner's main thread. Walk the connectors.
        for connector in mux.inputConnectors:
            connector.disconnect()
        player.outputConnectors[0].connect(mux.inputConnectors[0])
        renderer.outputConnectors[0].connect(mux.inputConnectors[1])
        if len(mux.inputs) != 2:
            raise RuntimeError("Slot %s switch needs both renderers" % slot.upper())
        # The LED path reads the switch through the sampler's `top` parameter.
        _set(sampler, "top", mux.path)
    # The preview mixer is rewired once, after BOTH switches exist - doing it
    # inside the loop would reach for a slot that has not been created yet.
    _rewire_mixer(owner, mixer)
    return True


def _rewire_mixer(owner, mixer):
    """Point the preview mixer at the two switches, A first, B second."""

    for connector in mixer.inputConnectors:
        connector.disconnect()
    for position, slot in enumerate(("a", "b")):
        owner.op("slot_%s_mux" % slot).outputConnectors[0].connect(mixer.inputConnectors[position])
    if len(mixer.inputs) != 2:
        raise RuntimeError("Transition mixer needs both slots")


IMPORT_PLACEHOLDER_SHADER = """out vec4 fragColor;
void main()
{
    fragColor = TDOutputSwizzle(vec4(0.0, 0.0, 0.0, 1.0));
}
"""

EDITOR_RUNTIME = '''# Show editor runtime: reads the panel, edits the show, writes it back.
import json
import sys

_ROOT = str(project.folder)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pixelblaze_mapper import show_automation as automation
from pixelblaze_mapper import show_editor as editor
from pixelblaze_mapper.show_sequencer import ShowValidationError

OWNER = op('/project1/show_control')
PANEL = OWNER.op('control_panel')
ROW_COUNT = 10


def _paint(node, colour, ink=None):
    """Colour a panel button for real.

    A buttonCOMP ignores its own Bgcolor: the inner `text` child draws it, and
    its stock expressions derive the fill from the parent's text Color scaled
    to 40%. Writing Bgcolor from outside changed nothing, which is why the
    selected row never looked selected and the record button never went red.
    """

    if node is None:
        return node
    text = node.op('text')
    if text is None:
        return node
    for channel, value in zip(('bgcolorr', 'bgcolorg', 'bgcolorb'), colour):
        par = getattr(text.par, channel, None)
        if par is None:
            continue
        par.mode = par.mode.__class__.CONSTANT
        par.val = value
    if ink is None:
        return node
    for channel, value in zip(('fontcolorr', 'fontcolorg', 'fontcolorb'), ink):
        par = getattr(text.par, channel, None)
        if par is not None:
            par.mode = par.mode.__class__.CONSTANT
            par.val = value
    return node


def _state(key, fallback=''):
    table = OWNER.op('editor_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return fallback


def _set_state(key, value):
    table = OWNER.op('editor_state')
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            table[row, 1] = str(value)
            return
    table.appendRow([key, str(value)])


def _field(name):
    node = PANEL.op(name)
    if node is None:
        return ''
    string = node.op('string')
    return str(string[0, 0]) if string is not None and string.numRows else ''


def _set_field(name, value):
    node = PANEL.op(name)
    if node is None:
        return
    string = node.op('string')
    if string is not None:
        string.text = str(value)


def _set_text(name, value):
    node = PANEL.op(name)
    if node is not None and str(node.par.text.eval()) != str(value):
        node.par.text = str(value)


def _show_path(name):
    import os
    folder = os.path.join(str(project.folder), 'shows')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, str(name) + '.json')


def show():
    return json.loads(OWNER.op('show_json').text)


def automation_data():
    try:
        return automation.validate(json.loads(OWNER.op('automation_json').text))
    except Exception:
        return automation.empty()


def _write_automation(data):
    node = OWNER.op('automation_json')
    node.clear()
    node.write(json.dumps(data))


def write(document):
    """Persist a show and pull every dependent surface along with it."""

    node = OWNER.op('show_json')
    node.clear()
    node.write(json.dumps(document, indent=2))
    _refresh_cue_table(document)
    broken = unresolved(document)
    if broken:
        # The transport refuses the whole show over one unplayable cue, and
        # its RuntimeError names an id nobody recognises. The edit itself is
        # saved; say which cue is at fault and what to do about it.
        repaint()
        raise ShowValidationError(
            'Gespeichert, aber nicht abspielbar - Cue %s hat kein Material. '
            'Cue loeschen oder Material importieren.'
            % ', '.join('%02d "%s"' % entry for entry in broken))
    _sync_transport()
    repaint()


def _sync_transport():
    """Rebuild the transport from the JSON that was just written.

    Reloading show_sequencer during a session leaves the transport DAT holding
    classes from the previous import, and its cached runtime then fails its own
    isinstance check. Dropping that cache and retrying once recovers, instead
    of reporting a failure for an edit that was in fact saved.
    """
    node = OWNER.op('callbacks')
    try:
        node.module.sync()
        return
    except Exception:
        # importlib.reload() on show_sequencer swaps the classes inside the
        # module dict while this DAT keeps the ones it imported, so the
        # sequencer's own isinstance check rejects a perfectly valid Show.
        # Re-executing the DAT rebinds every name from a single import.
        text = node.text
        node.clear()
        node.write(text)
        module = node.module
        module._runtime_record = None
        module.sync()


def _refresh_cue_table(document):
    # The base builder writes this table once. Loading a show without
    # refreshing it leaves the panel describing the previous show.
    table = OWNER.op('cue_table')
    table.clear()
    table.appendRow(['id', 'name', 'effect', 'preset', 'parameters_json', 'coordinate_mode',
                     'duration', 'transition', 'transition_duration', 'brightness',
                     'target_groups'])
    for cue in document['cues']:
        table.appendRow([cue['id'], cue['name'], cue['effect'], cue['preset'],
                         json.dumps(cue['parameters'], separators=(',', ':')),
                         cue['coordinate_mode'], cue['duration'], cue['transition'],
                         cue['transition_duration'], cue['brightness'],
                         ','.join(cue['target_groups'])])


def selected():
    rows = editor.summary_rows(show())
    if not rows:
        return -1
    return max(0, min(len(rows) - 1, int(float(_state('selected', '0') or 0))))


def player_values():
    node = op('/project1/madmapper_player_controls')
    if node is None:
        return {}
    return {par.name: par.eval() for par in node.customPars}


def current_material():
    """What the Material Browser actually has active, as (kind, id).

    madmapper_player_controls.Material only ever tracks CORE effects. Picking
    an imported MadMapper material leaves it at whatever core effect was
    selected before, which is why reading it reported the same name no matter
    what was playing. The material state store is the one place both kinds of
    material write to.
    """

    key = ''
    runtime = op('/project1/material_state_runtime')
    if runtime is not None:
        try:
            key = str(runtime.module._current_key() or '')
        except Exception:
            key = ''
    if not key:
        store = op('/project1').fetch('p1_material_state_store', None) or {}
        key = str(store.get('active_key') or '')
    if not key:
        # No state runtime in this build: the player's core selection is all
        # there is, and it is correct whenever only core effects are used.
        key = 'core:' + str(player_values().get('Material', '')).strip()
    kind, _, identifier = key.partition(':')
    return kind, identifier


def _effect_label(identifier):
    identifier = str(identifier).strip()
    if not identifier:
        return 'Fill'
    catalog = getattr(OWNER.op('render_sync').module, 'CATALOG', {})
    entry = catalog.get(identifier)
    if isinstance(entry, dict) and entry.get('label'):
        return str(entry['label'])
    return identifier.replace('_', ' ').title()


def _catalog():
    sync = OWNER.op('render_sync')
    return getattr(sync.module, 'CATALOG', {}) if sync is not None else {}


def _resolvable(effect):
    """Whether a cue effect can actually be played.

    The transport refuses to start a show that holds an effect it cannot
    resolve, and it refuses for the WHOLE show - so one bad cue stops
    everything, including recording. The editor therefore checks before it
    writes a cue, rather than leaving the operator with a show that will not
    roll and a raw RuntimeError in the message line.
    """

    effect = str(effect)
    if effect.startswith(IMPORT_PREFIX):
        try:
            return any(item['id'] == effect[len(IMPORT_PREFIX):] for item in _library()._items)
        except Exception:
            return False
    return effect in _catalog()


def unresolved(document):
    """Every cue in the show whose material is gone, as (number, name)."""

    return [(index + 1, str(cue.get('name') or cue['id']))
            for index, cue in enumerate(document.get('cues', ()))
            if not _resolvable(cue.get('effect'))]


def material_hint():
    kind, identifier = current_material()
    if kind == 'core':
        return 'Aktuell: ' + _effect_label(identifier)
    if kind == 'madmapper':
        try:
            return 'Aktuell: ' + str(_library().parameter_snapshot().get('label') or 'importiert')
        except Exception:
            return 'Aktuell: importiertes Material'
    # Neither kind means nothing addable is loaded - almost always because the
    # player is showing the show itself. Saying "unbekannt" left the operator
    # pressing + AKTUELLES MATERIAL anyway; say what to do instead.
    if str(player_values().get('Source', '')).strip().lower() == 'show':
        return 'Player auf SHOW - fuer neue Cues auf MATERIAL schalten'
    return 'Kein spielbares Material aktiv'


def repaint():
    document = show()
    rows = editor.summary_rows(document)
    total = editor.total_duration(document)
    if _state('recording', '0') == '1':
        # While a take runs, the cue carries the ceiling, not its length. Showing
        # that number invited the obvious question of why a cue is five minutes
        # long; the answer is that nobody knows yet - so neither the row, the
        # field, nor the running total repeats it.
        recorded = _state('record_cue', '')
        for position, cue in enumerate(document.get('cues', ())):
            if cue['id'] == recorded and position < len(rows):
                rows[position]['timing'] = 'Aufnahme...'
                total -= float(cue['duration'])
    page = max(0, int(float(_state('page', '0') or 0)))
    pages = max(1, (len(rows) + ROW_COUNT - 1) // ROW_COUNT)
    page = min(page, pages - 1)
    _set_state('page', page)
    index = selected()
    for slot in range(ROW_COUNT):
        position = page * ROW_COUNT + slot
        node = PANEL.op('ed_row_%d' % slot)
        if node is None:
            continue
        if position < len(rows):
            row = rows[position]
            node.par.label = '%s  %-24s %-18s %-13s %-13s %-11s %s' % (
                row['position'], row['name'][:24], row['effect'][:18], row['timing'],
                row['transition'], row['coordinate_mode'], row['gradient'])
            chosen = position == index
            _paint(node, (0.10, 0.26, 0.36) if chosen else (0.022, 0.034, 0.049),
                   (0.97, 0.98, 1.0) if chosen else (0.62, 0.68, 0.74))
        else:
            node.par.label = ''
            _paint(node, (0.012, 0.018, 0.026))
    _set_text('ed_page_info', 'Seite %d / %d' % (page + 1, pages))
    _set_field('ed_show_name', document.get('name', ''))
    _set_text('ed_show_info', '%d Cues\\n%.0f s' % (len(rows), max(0.0, total)))
    loop = PANEL.op('ed_btn_loop')
    if loop is not None:
        loop.par.label = 'LOOP: AN' if document.get('loop') else 'LOOP: AUS'
    data = automation_data()
    if 0 <= index < len(rows):
        cue = document['cues'][index]
        _set_field('ed_cue_name', cue['name'])
        _set_field('ed_cue_duration',
                   'AUFNAHME' if (_state('recording', '0') == '1'
                                  and _state('record_cue', '') == cue['id'])
                   else '%.1f' % cue['duration'])
        _set_field('ed_cue_transdur', '%.1f' % cue['transition_duration'])
        _set_field('ed_cue_brightness', '%.2f' % cue['brightness'])
        _set_text('ed_cue_trans', '%s  -  %s' % (cue['transition'],
                  editor.TRANSITION_LABELS.get(cue['transition'], '')))
        _set_text('ed_cue_mode', cue['coordinate_mode'])
        _set_text('ed_cue_grad', cue['parameters'].get('gradient', ''))
        _set_text('ed_selection_info', 'Cue %02d von %d  |  %s' % (index + 1, len(rows),
                  _state('message', '')))
        length = automation.track_length(data, cue['id'])
        tracks = data.get('tracks', {}).get(cue['id'], {})
        _set_text('ed_record_info', ('Aufnahme: %d Regler, %.1f s' % (len(tracks), length))
                  if tracks else 'Keine Aufnahme fuer diese Cue')
    else:
        for name in ('ed_cue_name', 'ed_cue_duration', 'ed_cue_transdur', 'ed_cue_brightness'):
            _set_field(name, '')
        for name in ('ed_cue_trans', 'ed_cue_mode', 'ed_cue_grad'):
            _set_text(name, '')
        _set_text('ed_selection_info', 'Show ist leer  |  ' + _state('message', ''))
        _set_text('ed_record_info', '')
    _set_text('ed_hint', material_hint())
    recording = _state('recording', '0') == '1'
    # recording_new survives a failed arming or a DAT reload; on its own it
    # would light the button red with no take behind it.
    new_take = recording and _state('recording_new', '0') == '1'
    live = (0.78, 0.13, 0.16)
    record = PANEL.op('ed_btn_record')
    if record is not None:
        armed = recording and not new_take
        record.par.label = ('AUFNAHME LAEUFT' if armed else 'AUFNAHME')
        _paint(record, live if armed else (0.22, 0.07, 0.09),
               (1.0, 0.96, 0.96) if armed else (0.90, 0.94, 0.98))
    record_new = PANEL.op('ed_btn_record_new')
    if record_new is not None:
        record_new.par.label = ('AUFNAHME LAEUFT' if new_take else 'AUFNAHME -> NEUE CUE')
        _paint(record_new, live if new_take else (0.16, 0.08, 0.20),
               (1.0, 0.96, 0.96) if new_take else (0.90, 0.94, 0.98))


def _cycle(values, current, delta):
    order = list(values)
    if current in order:
        return order[(order.index(current) + delta) % len(order)]
    return order[0]


def _message(text):
    _set_state('message', text)


def action(command):
    # Clear first: clearing afterwards would wipe the confirmation the command
    # itself just wrote ("Aufnahme gesichert", "geladen: ...").
    _message('')
    try:
        _apply(command)
    except (ShowValidationError, automation.AutomationError, ValueError) as error:
        _message(str(error))
    except Exception as error:  # surface, never swallow
        _message('%s: %s' % (type(error).__name__, error))
    repaint()
    return command


def _apply(command):
    document = show()
    index = selected()
    if command.startswith('select_'):
        page = int(float(_state('page', '0') or 0))
        _set_state('selected', page * ROW_COUNT + int(command.split('_')[1]))
        return
    if command == 'page_prev':
        _set_state('page', max(0, int(float(_state('page', '0') or 0)) - 1))
        return
    if command == 'page_next':
        _set_state('page', int(float(_state('page', '0') or 0)) + 1)
        return
    if command == 'add_material':
        kind, identifier = current_material()
        if kind not in ('core', 'madmapper'):
            # Anything else (a movie, an empty store, a half-initialised
            # state) has no effect the transport could resolve. Writing it
            # anyway produced a cue named after nothing that stopped the
            # whole show from starting - recording included.
            raise ShowValidationError(
                'Kein spielbares Material aktiv (%s) - im Material Browser eines waehlen'
                % (kind or 'leer'))
        values = player_values()
        parameters = editor.parameters_from_player(values)
        mode = editor.PLAYER_COORDINATE_MODES.get(str(values.get('Coordinatemode', 'global')), 'global')
        if kind == 'madmapper':
            snapshot = _library().parameter_snapshot()
            if str(snapshot.get('material_id') or '') != identifier:
                raise ShowValidationError('Die Bibliothek meldet ein anderes aktives Material')
            label = str(snapshot.get('label') or identifier)
            document = editor.append_cue(document, editor.new_cue(
                IMPORT_PREFIX + identifier, parameters, name=label,
                coordinate_mode=mode, preset=label))
            cue_id = document['cues'][-1]['id']
            data = imported_data()
            # The slider values belong to the cue, not to the material, so two
            # cues can use one material with different settings.
            data[cue_id] = {'material_id': identifier, 'label': label,
                            'values': {str(item['name']): item['value']
                                       for item in snapshot.get('parameters', ())}}
            _write_imported(data)
        else:
            label = _effect_label(identifier)
            if not _resolvable(label):
                raise ShowValidationError(
                    'Core-Effekt "%s" steht nicht im Katalog - Cue nicht angelegt' % label)
            document = editor.append_cue(document, editor.new_cue(
                label, parameters, name=label, coordinate_mode=mode,
                preset=str(values.get('Gradientpreset', ''))))
        _set_state('selected', len(document['cues']) - 1)
        _set_state('page', (len(document['cues']) - 1) // ROW_COUNT)
        write(document)
        return
    if command == 'duplicate':
        source_id = document['cues'][index]['id']
        document = editor.duplicate_cue(document, index)
        copy_id = document['cues'][index + 1]['id']
        data = automation_data()
        if source_id in data.get('tracks', {}):
            _write_automation(automation.merge(data, copy_id, data['tracks'][source_id]))
        imported = imported_data()
        if source_id in imported:
            imported[copy_id] = dict(imported[source_id])
            _write_imported(imported)
        _set_state('selected', index + 1)
        write(document)
        return
    if command == 'delete':
        if len(document['cues']) <= 1:
            raise ShowValidationError('Die letzte Cue kann nicht geloescht werden')
        removed = document['cues'][index]['id']
        document = editor.delete_cue(document, index)
        _write_automation(automation.clear_cue(automation_data(), removed))
        imported = imported_data()
        if imported.pop(removed, None) is not None:
            _write_imported(imported)
        _set_state('selected', max(0, index - 1))
        write(document)
        return
    if command in ('move_up', 'move_down'):
        delta = -1 if command == 'move_up' else 1
        document = editor.move_cue(document, index, delta)
        _set_state('selected', max(0, min(len(document['cues']) - 1, index + delta)))
        write(document)
        return
    if command == 'apply_fields':
        for field_name, cue_field, cast in (('ed_cue_name', 'name', str),
                                            ('ed_cue_duration', 'duration', float),
                                            ('ed_cue_transdur', 'transition_duration', float),
                                            ('ed_cue_brightness', 'brightness', float)):
            raw = _field(field_name).strip()
            if raw:
                document = editor.update_cue(document, index, cue_field, cast(raw))
        write(document)
        return
    if command in ('trans_prev', 'trans_next'):
        current = document['cues'][index]['transition']
        value = _cycle(editor.TRANSITION_ORDER, current, -1 if command == 'trans_prev' else 1)
        write(editor.update_cue(document, index, 'transition', value))
        return
    if command in ('mode_prev', 'mode_next'):
        current = document['cues'][index]['coordinate_mode']
        value = _cycle(editor.COORDINATE_ORDER, current, -1 if command == 'mode_prev' else 1)
        write(editor.update_cue(document, index, 'coordinate_mode', value))
        return
    if command in ('grad_prev', 'grad_next'):
        current = document['cues'][index]['parameters'].get('gradient', '')
        value = _cycle(editor.GRADIENT_ORDER, current, -1 if command == 'grad_prev' else 1)
        write(editor.update_cue(document, index, 'gradient', value))
        return
    if command == 'toggle_loop':
        write(editor.set_show_field(document, 'loop', not document.get('loop')))
        return
    if command == 'new_show':
        _set_state('selected', 0)
        _set_state('page', 0)
        write(dict(editor.EMPTY_SHOW))
        return
    if command == 'save_show':
        name = _field('ed_show_name').strip() or document.get('name', 'show')
        document = editor.set_show_field(document, 'name', name)
        path = _show_path(editor.slugify(name, fallback='show'))
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(document, stream, indent=2)
        with open(path[:-5] + '.automation.json', 'w', encoding='utf-8') as stream:
            json.dump(automation_data(), stream, indent=2)
        with open(path[:-5] + '.materials.json', 'w', encoding='utf-8') as stream:
            json.dump(imported_data(), stream, indent=2)
        _message('gespeichert: ' + path)
        write(document)
        return
    if command == 'load_show':
        name = editor.slugify(_field('ed_show_name').strip() or 'show', fallback='show')
        path = _show_path(name)
        with open(path, encoding='utf-8') as stream:
            loaded = json.load(stream)
        try:
            with open(path[:-5] + '.automation.json', encoding='utf-8') as stream:
                _write_automation(automation.validate(json.load(stream)))
        except OSError:
            pass
        try:
            with open(path[:-5] + '.materials.json', encoding='utf-8') as stream:
                _write_imported(json.load(stream))
        except OSError:
            pass
        _set_state('selected', 0)
        _set_state('page', 0)
        _message('geladen: ' + path)
        write(loaded)
        return
    if command == 'toggle_record':
        if _state('recording', '0') == '1':
            stop_recording()
        else:
            start_recording()
        return
    if command == 'record_new':
        if _state('recording', '0') == '1':
            stop_recording()
        else:
            start_recording(as_new_cue=True)
        return
    if command == 'clear_record':
        _write_automation(automation.clear_cue(automation_data(), document['cues'][index]['id']))
        _message('Aufnahme geloescht')
        return
    raise ShowValidationError('Unbekannter Befehl: %s' % command)


TAKE_KEY = 'record_take'
STATE_KEY = 'record_start_state'
# The length a cue carries WHILE it is being recorded, before the take sets the
# real one. It cannot grow during the take - writing the show mid-take rebuilds
# the transport, and the rebuild pauses a running show, which would freeze the
# cue clock the samples are stamped with. So it is a ceiling, not a guess: five
# minutes is longer than any cue anyone performs, and short enough to look like
# a number rather than a bug. The panel shows "AUFNAHME" instead of it anyway.
RECORD_LIMIT = 300.0


def _take():
    """The running take, or None.

    Held in COMP storage rather than a module global: TouchDesigner
    re-executes a DAT module whenever it likes, and a recorder kept in a
    global vanishes mid-take. The take then looked exactly like "no control
    was touched", which is what this whole mechanism kept reporting.
    """

    state = OWNER.fetch(TAKE_KEY, None)
    if not isinstance(state, dict):
        return None
    try:
        return automation.Recorder.from_state(state)
    except automation.AutomationError:
        OWNER.unstore(TAKE_KEY)
        return None


def start_recording(as_new_cue=False):
    """Arm the recorder and roll the transport from the top of the cue.

    Samples are stamped with CUE time. If the transport is not playing that
    clock never moves, every sample lands on the same instant and the take
    collapses to nothing - which looked exactly like "no slider was touched".
    So recording starts the show itself, at the beginning of the cue, the way
    pressing record on a recorder rolls the tape.
    """

    document = show()
    blocked = unresolved(document)
    if blocked:
        # The transport refuses to roll while any cue is unplayable, so
        # recording would fail on a cue that has nothing to do with it.
        raise ShowValidationError(
            'Aufnahme nicht moeglich - Cue %s hat kein Material. Erst loeschen.'
            % ', '.join('%02d "%s"' % entry for entry in blocked))
    created_id = None
    if as_new_cue:
        # Record straight from the browser: the cue is created first so the
        # take has something to attach to and the slot can already play the
        # material while it is being performed. Its length is set on stop.
        _apply('add_material')
        document = show()
        index = len(document['cues']) - 1
        created_id = document['cues'][index]['id']
        # Open-ended while performing: a cue created at the default length
        # would cut the take off at 15 seconds. The real length is set from
        # the take when recording stops.
        document = editor.update_cue(document, index, 'duration', RECORD_LIMIT)
        write(document)
        _set_state('recording_new', '1')
    else:
        index = selected()
        _set_state('recording_new', '0')
    if index < 0:
        raise ShowValidationError('Keine Cue ausgewaehlt')
    cue = document['cues'][index]
    _require_matching_material(index, cue)
    cue_id = cue['id']
    try:
        _arm(index, cue_id)
    except Exception:
        # Whatever went wrong, do not leave a half-armed recorder behind or,
        # worse, a 900-second cue nobody asked for sitting in the show.
        _disarm(created_id)
        raise
    if editor.is_imported(cue):
        # The single most common way to end up with an empty take: turning the
        # Material Player while an imported cue records. Those sliders are not
        # in an imported cue's signal path at all, so say it before the take,
        # not after it.
        where = ' - dafuer die Regler im MATERIAL BROWSER nehmen, die Player-Regler wirken hier nicht'
    else:
        where = ''
    if as_new_cue:
        _message('Aufnahme laeuft - neue Cue %02d, Laenge folgt der Aufnahme%s' % (index + 1, where))
    else:
        _message('Aufnahme laeuft - Cue %02d spielt von vorn%s' % (index + 1, where))


def _require_matching_material(index, cue):
    """Refuse to overdub an imported cue while a different material is loaded.

    A take on an imported cue records the controls of whatever the browser has
    active - there is only one set of sliders. With the wrong material loaded
    that writes one material's controls into another material's cue, and the
    cue quietly stops looking like itself. Better to say so.
    """

    if not editor.is_imported(cue):
        return
    wanted = editor.material_id(cue)
    kind, active = current_material()
    if kind == 'madmapper' and active == wanted:
        return
    try:
        label = str(_library_item(wanted).get('label') or wanted)
    except Exception:
        label = wanted
    raise ShowValidationError(
        'Cue %02d spielt "%s" - dieses Material erst im Browser aktivieren' % (index + 1, label))


def _arm(index, cue_id):
    """Roll the transport to the top of the cue and open a take on it."""

    transport = OWNER.op('callbacks').module
    for key, value in (('cue_index', index), ('elapsed', '0'),
                       ('outgoing_slot', 'A'), ('incoming_slot', '')):
        transport._set(key, value)
    transport._runtime_record = None
    transport.runtime()
    transport.command('play')
    # Deliberately NOT seeding the controls from the cue. Writing the Material
    # Player fires controls_changed(), which overwrites the ACTIVE material's
    # stored settings - so arming the recorder reset the material the operator
    # had just dialled in. A take starts from what is on screen; the opening
    # sample captures it, and stop_recording() writes it into the cue.
    OWNER.store(STATE_KEY, _live_state())
    OWNER.store(TAKE_KEY, automation.new_take(cue_id))
    _set_state('recording', '1')
    _set_state('core_moved', '0')
    _set_state('record_cue', cue_id)


def _disarm(created_id=None):
    """Undo an arming that failed, including the cue it had just created."""

    OWNER.unstore(TAKE_KEY)
    OWNER.unstore(STATE_KEY)
    _set_state('recording', '0')
    _set_state('recording_new', '0')
    _set_state('core_moved', '0')
    _set_state('record_cue', '')
    _remove_cue(created_id, resync=False)


def _remove_cue(cue_id, resync=True):
    """Take back a cue that only ever existed to hold a take."""

    if not cue_id:
        return False
    document = show()
    index = next((i for i, cue in enumerate(document['cues']) if cue['id'] == cue_id), None)
    if index is None or len(document['cues']) <= 1:
        return False
    data = imported_data()
    if cue_id in data:
        del data[cue_id]
        _write_imported(data)
    document = editor.delete_cue(document, index)
    _set_state('selected', max(0, index - 1))
    _set_state('page', max(0, index - 1) // ROW_COUNT)
    if resync:
        write(document)
    else:
        node = OWNER.op('show_json')
        node.clear()
        node.write(json.dumps(document, indent=2))
    return True


def _trim_new_cue(cue_id, span):
    """Make a freshly recorded cue exactly as long as its take.

    A cue created for recording starts with the default length. Leaving it
    there would replay the move and then sit on the last value for the rest of
    the cue, which is not what was performed.
    """

    document = show()
    index = next((i for i, cue in enumerate(document['cues']) if cue['id'] == cue_id), None)
    if index is None:
        return
    duration = max(1.0, round(float(span) + 0.5, 1))
    if duration >= RECORD_LIMIT:
        duration = RECORD_LIMIT
    document = editor.update_cue(document, index, 'duration', duration)
    _set_state('selected', index)
    _set_state('page', index // ROW_COUNT)
    write(document)


def _live_state():
    """Everything the operator currently has set, for both kinds of material."""

    return {'player': {name: value for name, value in player_values().items()
                       if isinstance(value, (int, float)) and not isinstance(value, bool)},
            'imported': live_imported_values()}


def _store_state_in_cue(cue_id):
    """Fold the state the take started from into the cue itself.

    Controls that never moved produce no track, so without this the cue would
    keep whatever it was created with and replay something other than what was
    performed. Recording captures the state, not only the movement.
    """

    state = OWNER.fetch(STATE_KEY, None) or {}
    OWNER.unstore(STATE_KEY)
    document = show()
    index = next((i for i, cue in enumerate(document['cues']) if cue['id'] == cue_id), None)
    if index is None:
        return
    cue = document['cues'][index]
    if editor.is_imported(cue):
        values = state.get('imported') or {}
        if not values:
            return
        data = imported_data()
        record = dict(data.get(cue_id) or {})
        record.setdefault('material_id', editor.material_id(cue))
        record.setdefault('label', cue.get('preset') or cue['name'])
        merged = dict(record.get('values') or {})
        merged.update(values)
        record['values'] = merged
        data[cue_id] = record
        _write_imported(data)
        return
    player = state.get('player') or {}
    if not player:
        return
    parameters = dict(cue['parameters'])
    for player_name, parameter in editor.PLAYER_PARAMETERS.items():
        if player_name in player and parameter in parameters:
            parameters[parameter] = float(player[player_name])
    cues = [dict(entry) for entry in document['cues']]
    cues[index] = dict(cue, parameters=parameters)
    write(dict(document, cues=cues))


def stop_recording(reason=''):
    recorder = _take()
    recorded = recorder.result() if recorder is not None else {}
    cue_id = _state('record_cue', '')
    OWNER.unstore(TAKE_KEY)
    _set_state('recording', '0')
    if recorded and cue_id:
        _write_automation(automation.merge(automation_data(), cue_id, recorded))
        _store_state_in_cue(cue_id)
        if _state('recording_new', '0') == '1':
            _set_state('recording_new', '0')
            _trim_new_cue(cue_id, recorder.span)
            _message('Neue Cue aufgenommen: %d Regler, %.1f s' % (len(recorded), recorder.span))
            return
        ending = ' (Cue zu Ende)' if reason == 'cue-ended' else ''
        _message('Aufnahme gesichert: %d Regler, %.1f s%s'
                 % (len(recorded), recorder.span, ending))
        return
    OWNER.unstore(STATE_KEY)
    if _state('recording_new', '0') == '1':
        _set_state('recording_new', '0')
        # The cue was created by pressing record and holds nothing that was
        # performed. Leaving it behind is how a show collects empty cues that
        # are as long as the recording ceiling.
        if _remove_cue(cue_id):
            _message(_empty_reason() + ' - die neue Cue wurde wieder entfernt')
            return
    if reason == 'cue-ended':
        # Truthful cause: the cue simply ran out first. Saying "kein Regler
        # bewegt" sent the operator looking for a fault in the recorder.
        _message('Cue war zu Ende, bevor ein Regler bewegt wurde - '
                 'Cue verlaengern oder AUFNAHME -> NEUE CUE nehmen')
        return
    reason = recorder.diagnosis() if recorder is not None else 'no-movement'
    _message({'no-time': 'Nichts aufgenommen - die Show lief nicht, die Cue-Zeit stand still',
              'too-short': 'Nichts aufgenommen - die Bewegung war zu kurz',
              }.get(reason, _empty_reason()))


def _empty_reason():
    """Why a take came back empty, in the operator's terms."""

    if _state('core_moved', '0') == '1':
        _set_state('core_moved', '0')
        return ('Nichts aufgenommen - bewegt wurden die PLAYER-Regler, die bei '
                'importiertem Material nichts tun. Im MATERIAL BROWSER unter '
                'NATIVE PARAMS aufnehmen')
    return 'Nichts aufgenommen - kein Regler bewegt'


def record_tick(elapsed):
    """Called once per frame by the transport while recording.

    Runs inside onFrameEnd, so a raising recorder would spam the textport
    every frame. A failure disarms the recording once and reports it in the
    panel instead.
    """

    if _state('recording', '0') != '1':
        return
    recorder = _take()
    if recorder is None:
        _set_state('recording', '0')
        return
    try:
        # The show does not stop at the end of the cue being recorded. Sampling
        # past that boundary stamps the NEXT cue's timeline onto this take, and
        # because its clock restarts at zero the samples then collapse into one
        # instead of growing - which looked like nothing had been recorded.
        transport = OWNER.op('callbacks').module
        document = show()
        index = int(float(transport._get('cue_index', '0') or 0))
        cue_id = _state('record_cue', '')
        cues = document.get('cues', ())
        if not (0 <= index < len(cues)) or cues[index]['id'] != cue_id:
            stop_recording(reason='cue-ended')
            return
        moment = max(0.0, float(elapsed))
        if recorder.last_time is not None and moment + 1e-6 < recorder.last_time:
            stop_recording(reason='cue-ended')
            return
        # An imported cue is driven by the material's own controls, so those are
        # what the operator turns. The core sliders are ignored there: touching
        # a mat_ control writes back through the material state and nudges them,
        # which would litter the take with tracks nobody moved.
        if editor.is_imported(cues[index]):
            sample = live_imported_values()
            _watch_core_movement()
        else:
            values = player_values()
            sample = {}
            for player_name, parameter in editor.PLAYER_PARAMETERS.items():
                if parameter in automation.RECORDABLE and player_name in values:
                    try:
                        sample[parameter] = float(values[player_name])
                    except (TypeError, ValueError):
                        continue
        if sample:
            recorder.sample(moment, sample)
    except Exception as error:
        OWNER.unstore(TAKE_KEY)
        _set_state('recording', '0')
        _message('Aufnahme abgebrochen: %s' % error)


IMPORT_PREFIX = editor.IMPORT_PREFIX
_slot_signature = {}


def _watch_core_movement():
    """Notice the Material Player being turned during an imported take.

    Nothing comes of it - an imported cue is rendered by the material's own
    shader, with the player's sliders nowhere in that path - but knowing it
    happened is the difference between "nichts aufgenommen" and an answer.
    """

    if _state('core_moved', '0') == '1':
        return
    start = (OWNER.fetch(STATE_KEY, None) or {}).get('player') or {}
    if not start:
        return
    values = player_values()
    for name, was in start.items():
        now = values.get(name)
        if isinstance(now, (int, float)) and abs(float(now) - float(was)) > 1e-4:
            _set_state('core_moved', '1')
            return


def _library():
    node = op('/project1/madmapper_library/runtime')
    if node is None:
        raise ShowValidationError('MadMapper-Bibliothek ist nicht geladen')
    return node.module


def _library_item(material_id):
    module = _library()
    item = next((entry for entry in module._items if entry['id'] == material_id), None)
    if item is None:
        module.refresh(reset_page=False)
        item = next((entry for entry in module._items if entry['id'] == material_id), None)
    if item is None:
        raise ShowValidationError('Importiertes Material nicht im Katalog: ' + str(material_id))
    return item


def imported_data():
    try:
        return json.loads(OWNER.op('imported_json').text) or {}
    except Exception:
        return {}


def _write_imported(data):
    node = OWNER.op('imported_json')
    node.clear()
    node.write(json.dumps(data))


def _request_value(path, key, fallback=''):
    table = OWNER.op(path)
    if table is None:
        return fallback
    for row in range(1, table.numRows):
        if str(table[row, 0]) == key:
            return str(table[row, 1])
    return fallback


def _slot_cue_index(slot):
    """Which cue a slot is carrying, from the transport's own plan.

    The outgoing slot holds the running cue; during a transition the incoming
    slot already holds the next one, which is why this cannot simply read
    cue_index for both.
    """

    transport = OWNER.op('callbacks').module
    document = show()
    count = len(document.get('cues', ()))
    if not count:
        return None
    index = int(float(transport._get('cue_index', '0') or 0))
    outgoing = str(transport._get('outgoing_slot', 'A')).strip().upper()
    incoming = str(transport._get('incoming_slot', '')).strip().upper()
    slot = slot.upper()
    if slot == outgoing:
        return index if 0 <= index < count else None
    if incoming and slot == incoming:
        following = index + 1
        if following >= count:
            return 0 if document.get('loop') else None
        return following
    return None


def live_imported_values():
    """Current control values of the active imported material, scalars only.

    Vector controls (colours and the like) are skipped: an automation track is
    one number over time, and splitting a colour into components would record
    something the operator never sees as one control.
    """

    try:
        snapshot = _library().parameter_snapshot()
    except Exception:
        return {}
    values = {}
    for item in snapshot.get('parameters', ()):
        name = str(item.get('name', ''))
        if not automation.recordable(name):
            continue
        value = item.get('value')
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        values[name] = float(value)
    return values


def _write_uniforms(renderer, adaptation, values):
    """Update only the named uniforms on a slot renderer.

    The library's full configure rebinds textures and republishes the schema -
    far too much for every frame. Playing a recorded move only needs the value
    parameters of the controls that actually move.
    """

    from pixelblaze_mapper.madmapper_parameters import uniform_vector
    for parameter in adaptation.schema:
        if parameter.name not in values or parameter.compile_time:
            continue
        block = 3 + parameter.index
        try:
            vector = uniform_vector(parameter, values[parameter.name])
        except Exception:
            continue
        for suffix, component in zip('xyzw', vector):
            par = getattr(renderer.par, 'vec%dvalue%s' % (block, suffix), None)
            if par is not None:
                par.val = component


def imported_values(cue_id, material_id, defaults):
    """Captured slider values for one cue, falling back to the material's own."""

    values = dict(defaults)
    record = imported_data().get(str(cue_id))
    if record and record.get('material_id') == material_id:
        for name, value in (record.get('values') or {}).items():
            if name in values:
                values[name] = value
    return values


def route_slot(player_name, request_path, effect):
    """Send one A/B slot to the core player or to its imported renderer.

    Returns None for core effects so the caller keeps its existing path, and
    the usual (label, preset, targets) triple once an imported material has
    been loaded into this slot.
    """

    slot = 'a' if str(player_name).endswith('slot_a_player') else 'b'
    mux = OWNER.op('slot_%s_mux' % slot)
    if mux is None:
        return None
    effect = str(effect)
    if not effect.startswith(IMPORT_PREFIX):
        if int(mux.par.index.eval()) != 0:
            mux.par.index = 0
        return None
    material_id = effect[len(IMPORT_PREFIX):]
    item = _library_item(material_id)
    adaptation, defaults = _library()._parameter_context(item)
    index = _slot_cue_index(slot)
    cue_id = ''
    if index is not None:
        cue_id = show()['cues'][index]['id']
    values = imported_values(cue_id, material_id, defaults)
    signature = (material_id, tuple(sorted((k, repr(v)) for k, v in values.items())))
    if _slot_signature.get(slot) != signature:
        shader = OWNER.op('slot_%s_import_fs' % slot)
        renderer = OWNER.op('slot_%s_import' % slot)
        # Recompiling a 12k shader every frame would stall the render; only
        # swap the source when the material itself changed.
        if _slot_signature.get(slot, ('',))[0] != material_id:
            shader.clear()
            shader.write(adaptation.shader)
        _library()._configure_parameter_uniforms(renderer, adaptation, values,
                                                 publish_schema=False)
        _slot_signature[slot] = signature
    # Recorded moves ride on top of the cue's stored values, written as bare
    # uniforms so a moving control costs a few parameter writes, not a full
    # reconfigure with texture rebinding.
    live = _imported_overrides(slot, cue_id)
    if live:
        _write_uniforms(OWNER.op('slot_%s_import' % slot), adaptation, live)
    if int(mux.par.index.eval()) != 1:
        mux.par.index = 1
    return (item['label'], material_id, _request_value(request_path, 'target_groups', 'all'))


def _imported_overrides(slot, cue_id):
    """What should override the cue's stored controls right now.

    While a take is running this is the operator's hand on the live controls,
    so the recording can be heard while it is made; otherwise it is whatever
    was recorded earlier for this moment of the cue.
    """

    if not cue_id:
        return {}
    transport = OWNER.op('callbacks').module
    if str(transport._get('outgoing_slot', 'A')).strip().lower() != slot:
        return {}
    if _state('recording', '0') == '1' and _state('record_cue', '') == cue_id:
        return live_imported_values()
    moment = float(transport._get('elapsed', '0') or 0)
    recorded = automation.values_at(automation_data(), cue_id, moment)
    return {name: value for name, value in recorded.items()
            if name.startswith(automation.IMPORT_PARAMETER_PREFIX)}


PLAYER_BY_PARAMETER = {value: key for key, value in editor.PLAYER_PARAMETERS.items()}


def overlay(player_name, parameters):
    """Apply the recording of the on-air cue to one slot's parameters.

    Called from the render sync for each slot every frame. Only the slot that
    currently carries the cue is touched; the incoming slot of a transition
    keeps the next cue's own values.
    """

    data = automation_data()
    tracks = data.get('tracks') or {}
    if not tracks and _state('recording', '0') != '1':
        return parameters
    transport = OWNER.op('callbacks').module
    slot = str(transport._get('outgoing_slot', 'A')).strip().upper() or 'A'
    if not str(player_name).endswith('slot_%s_player' % slot.lower()):
        return parameters
    document = show()
    index = int(float(transport._get('cue_index', '0') or 0))
    if not 0 <= index < len(document['cues']):
        return parameters
    cue_id = document['cues'][index]['id']
    if _state('recording', '0') == '1' and _state('record_cue', '') == cue_id:
        return _live_monitor(parameters)
    if cue_id not in tracks:
        return parameters
    values = automation.values_at(data, cue_id, float(transport._get('elapsed', '0') or 0))
    result = dict(parameters)
    for parameter, value in values.items():
        if parameter in result:
            result[parameter] = float(value)
    return result


def _live_monitor(parameters):
    """During a take, put the operator's hands on the output.

    The show drives the slot from the cue's stored parameters, so moving a
    Material Player slider while recording would change nothing on the wall -
    the take would be made blind. Feeding the live values through instead
    makes the recording audible while it happens.
    """

    values = player_values()
    result = dict(parameters)
    for player_name, parameter in editor.PLAYER_PARAMETERS.items():
        if parameter in result and parameter in automation.RECORDABLE and player_name in values:
            try:
                result[parameter] = float(values[player_name])
            except (TypeError, ValueError):
                continue
    return result


def playback_values(cue_id, elapsed):
    return automation.values_at(automation_data(), cue_id, elapsed)


# The flag and the take live in the same COMP, so a reload cannot separate
# them. Only a genuinely missing take clears the flag.
if _state('recording', '0') == '1' and OWNER.fetch(TAKE_KEY, None) is None:
    _set_state('recording', '0')
    _set_state('record_cue', '')
'''
