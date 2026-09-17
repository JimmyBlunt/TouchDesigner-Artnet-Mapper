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
                          ("fontcolorr", 0.90), ("fontcolorg", 0.94), ("fontcolorb", 0.98),
                          ("fontalpha", 1), ("bgalpha", 1), ("bgcolorr", color[0]),
                          ("bgcolorg", color[1]), ("bgcolorb", color[2]), ("cursor", "pointer")):
            _set(node, par, item)
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
    text("ed_hint", "Feld aendern, dann UEBERNEHMEN", 820, 528, 160, 38, 10, DIM)

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
    click(button("ed_btn_record_clear", "AUFNAHME LOESCHEN", 230, 326, 200, 36), "clear_record")
    text("ed_record_info", "", 440, 326, 540, 36, 11, DIM)

    # A freshly created Table DAT already holds one empty cell, so test for the
    # header instead of an empty table; otherwise the keys are never written
    # and every lookup silently falls back to its default.
    state = _get_or_create(owner, tableDAT, "editor_state")
    defaults = (("selected", "0"), ("page", "0"), ("recording", "0"),
                ("record_cue", ""), ("message", ""))
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


def _effect_label(values):
    identifier = str(values.get('Material', '')).strip()
    if not identifier:
        return 'Fill'
    catalog = getattr(OWNER.op('render_sync').module, 'CATALOG', {})
    entry = catalog.get(identifier)
    if isinstance(entry, dict) and entry.get('label'):
        return str(entry['label'])
    return identifier.replace('_', ' ').title()


def repaint():
    document = show()
    rows = editor.summary_rows(document)
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
            node.par.bgcolorr = 0.05 if chosen else 0.022
            node.par.bgcolorg = 0.14 if chosen else 0.034
            node.par.bgcolorb = 0.20 if chosen else 0.049
        else:
            node.par.label = ''
            node.par.bgcolorr, node.par.bgcolorg, node.par.bgcolorb = 0.012, 0.018, 0.026
    _set_text('ed_page_info', 'Seite %d / %d' % (page + 1, pages))
    _set_field('ed_show_name', document.get('name', ''))
    _set_text('ed_show_info', '%d Cues\\n%.0f s' % (len(rows), editor.total_duration(document)))
    loop = PANEL.op('ed_btn_loop')
    if loop is not None:
        loop.par.label = 'LOOP: AN' if document.get('loop') else 'LOOP: AUS'
    data = automation_data()
    if 0 <= index < len(rows):
        cue = document['cues'][index]
        _set_field('ed_cue_name', cue['name'])
        _set_field('ed_cue_duration', '%.1f' % cue['duration'])
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
    recording = _state('recording', '0') == '1'
    record = PANEL.op('ed_btn_record')
    if record is not None:
        record.par.label = 'AUFNAHME LAEUFT' if recording else 'AUFNAHME'
        record.par.bgcolorr = 0.60 if recording else 0.22
        record.par.bgcolorg = 0.12 if recording else 0.07


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
        values = player_values()
        parameters = editor.parameters_from_player(values)
        mode = editor.PLAYER_COORDINATE_MODES.get(str(values.get('Coordinatemode', 'global')), 'global')
        label = _effect_label(values)
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
        _set_state('selected', index + 1)
        write(document)
        return
    if command == 'delete':
        if len(document['cues']) <= 1:
            raise ShowValidationError('Die letzte Cue kann nicht geloescht werden')
        removed = document['cues'][index]['id']
        document = editor.delete_cue(document, index)
        _write_automation(automation.clear_cue(automation_data(), removed))
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
    if command == 'clear_record':
        _write_automation(automation.clear_cue(automation_data(), document['cues'][index]['id']))
        _message('Aufnahme geloescht')
        return
    raise ShowValidationError('Unbekannter Befehl: %s' % command)


_recorder = None


def start_recording():
    global _recorder
    document = show()
    index = selected()
    if index < 0:
        raise ShowValidationError('Keine Cue ausgewaehlt')
    cue_id = document['cues'][index]['id']
    _recorder = automation.Recorder(cue_id)
    _set_state('recording', '1')
    _set_state('record_cue', cue_id)
    _message('Aufnahme laeuft fuer Cue ' + cue_id)


def stop_recording():
    global _recorder
    recorded = _recorder.result() if _recorder is not None else {}
    cue_id = _state('record_cue', '')
    _recorder = None
    _set_state('recording', '0')
    if recorded and cue_id:
        _write_automation(automation.merge(automation_data(), cue_id, recorded))
        _message('Aufnahme gesichert: %d Regler' % len(recorded))
    else:
        _message('Nichts aufgenommen - kein Regler bewegt')


def record_tick(elapsed):
    """Called once per frame by the transport while recording.

    Runs inside onFrameEnd, so a raising recorder would spam the textport
    every frame. A failure disarms the recording once and reports it in the
    panel instead.
    """

    global _recorder
    if _recorder is None or _state('recording', '0') != '1':
        return
    try:
        values = player_values()
        sample = {}
        for player_name, parameter in editor.PLAYER_PARAMETERS.items():
            if parameter in automation.RECORDABLE and player_name in values:
                try:
                    sample[parameter] = float(values[player_name])
                except (TypeError, ValueError):
                    continue
        if sample:
            _recorder.sample(max(0.0, float(elapsed)), sample)
    except Exception as error:
        _recorder = None
        _set_state('recording', '0')
        _message('Aufnahme abgebrochen: %s' % error)


PLAYER_BY_PARAMETER = {value: key for key, value in editor.PLAYER_PARAMETERS.items()}


def overlay(player_name, parameters):
    """Apply the recording of the on-air cue to one slot's parameters.

    Called from the render sync for each slot every frame. Only the slot that
    currently carries the cue is touched; the incoming slot of a transition
    keeps the next cue's own values.
    """

    data = automation_data()
    tracks = data.get('tracks')
    if not tracks:
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
    if cue_id not in tracks:
        return parameters
    values = automation.values_at(data, cue_id, float(transport._get('elapsed', '0') or 0))
    result = dict(parameters)
    for parameter, value in values.items():
        if parameter in result:
            result[parameter] = float(value)
    return result


def playback_values(cue_id, elapsed):
    return automation.values_at(automation_data(), cue_id, elapsed)
'''
