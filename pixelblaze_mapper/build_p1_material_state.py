"""Install P1 per-material state and the continuous phase clock in TD.

The builder is idempotent, does not save the project, and never addresses a
network-output operator.  Run it only after the offline tests pass.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
ROOT = "/project1"
CONTROLS = ROOT + "/madmapper_player_controls"
RUNTIME = ROOT + "/material_state_runtime"
STATE_TABLE = ROOT + "/material_state_table"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _page(owner, name):
    return next((page for page in owner.customPages if page.name == name), None) or owner.appendCustomPage(name)


def _ensure_float(owner, page, name, label, default, minimum, maximum):
    parameter = owner.par[name]
    if parameter is None:
        parameter = page.appendFloat(name, label=label)[0]
        parameter.default = default
        parameter.val = default
    parameter.min = minimum
    parameter.max = maximum
    parameter.normMin = minimum
    parameter.normMax = maximum
    parameter.clampMin = True
    parameter.clampMax = True
    return parameter


def _runtime_source():
    return r'''import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pixelblaze_mapper.material_state import MaterialSettings, MaterialStateStore

CONTROLS = op('/project1/madmapper_player_controls')
TABLE = op('/project1/material_state_table')
STORE = MaterialStateStore()
_applying = False


def _now():
    return float(absTime.seconds)


def _table_document():
    if TABLE is None or TABLE.numRows < 2:
        return None
    for row in range(1, TABLE.numRows):
        if str(TABLE[row, 0]) == 'document':
            value = str(TABLE[row, 1]).strip()
            return json.loads(value) if value else None
    return None


def _persist():
    document = json.dumps(STORE.to_dict(), sort_keys=True, separators=(',', ':'))
    TABLE.clear()
    TABLE.appendRow(('key', 'json'))
    TABLE.appendRow(('document', document))


def _rgba(prefix):
    values = []
    for suffix in 'rgba':
        parameter = getattr(CONTROLS.par, prefix + suffix, None)
        values.append(float(parameter.eval()) if parameter is not None else 1.0)
    return tuple(values)


def _settings_from_controls():
    gradient = CONTROLS.par.Gradientpreset
    return MaterialSettings(
        speed=float(CONTROLS.par.Speed.eval()),
        scale=float(CONTROLS.par.Scale.eval()),
        width=float(CONTROLS.par.Width.eval()),
        focus_x=float(CONTROLS.par.Focusx.eval()),
        focus_y=float(CONTROLS.par.Focusy.eval()),
        zoom=float(CONTROLS.par.Framezoom.eval()),
        gradient=str(gradient.eval()) if gradient is not None else 'custom',
        color_a=_rgba('Color'),
        color_b=_rgba('Color2'),
        coordinate_mode=str(CONTROLS.par.Coordinatemode.eval()),
    )


def _apply(settings):
    global _applying
    _applying = True
    try:
        CONTROLS.par.Speed = settings.speed
        CONTROLS.par.Scale = settings.scale
        CONTROLS.par.Width = settings.width
        CONTROLS.par.Focusx = settings.focus_x
        CONTROLS.par.Focusy = settings.focus_y
        CONTROLS.par.Framezoom = settings.zoom
        if CONTROLS.par.Gradientpreset is not None:
            CONTROLS.par.Gradientpreset = settings.gradient
        for suffix, value in zip('rgba', settings.color_a):
            parameter = getattr(CONTROLS.par, 'Color' + suffix, None)
            if parameter is not None:
                parameter.val = value
        for suffix, value in zip('rgba', settings.color_b):
            parameter = getattr(CONTROLS.par, 'Color2' + suffix, None)
            if parameter is not None:
                parameter.val = value
        CONTROLS.par.Coordinatemode = settings.coordinate_mode
    finally:
        _applying = False


def _current_key():
    source = str(CONTROLS.par.Source.eval())
    if source == 'materials':
        return 'core:' + str(CONTROLS.par.Material.eval())
    if source == 'imported':
        state = op('/project1/madmapper_library/browser_state')
        if state is not None:
            for row in range(1, state.numRows):
                if str(state[row, 0]) == 'selected_id' and str(state[row, 1]).strip():
                    return 'madmapper:' + str(state[row, 1]).strip()
    return source + ':default'


def initialize():
    global STORE
    document = _table_document()
    if document:
        STORE = MaterialStateStore.from_dict(document)
    CONTROLS.par.Globalmasterspeed = STORE.global_master_speed
    key = _current_key()
    if STORE.active_key != key:
        state = STORE.activate(key, _now(), initial=_settings_from_controls())
    else:
        # A persisted timestamp belongs to the previous TD runtime.  Keep the
        # exact stored phase, but anchor future integration at this launch so
        # closed/reload time can never be counted as material animation.
        state = STORE.rebase_active(_now())
    _apply(state.settings)
    _persist()
    return key


def activate(key, preset=None):
    now = _now()
    if STORE.active_key is not None:
        STORE.set_active_settings(_settings_from_controls(), now)
    initial = _settings_from_controls()
    if preset:
        initial = replace(
            initial,
            scale=float(preset.get('scale', initial.scale)),
            width=float(preset.get('width', initial.width)),
        )
    state = STORE.activate(str(key), now, initial=initial)
    _apply(state.settings)
    _persist()
    return state.settings.to_dict()


def controls_changed():
    if _applying:
        return
    now = _now()
    STORE.set_global_master_speed(float(CONTROLS.par.Globalmasterspeed.eval()), now)
    settings = _settings_from_controls()
    key = _current_key()
    if STORE.active_key != key:
        state = STORE.activate(key, now, initial=settings)
        _apply(state.settings)
    else:
        STORE.set_active_settings(settings, now)
    _persist()


def tick():
    return STORE.tick(_now())


def phase():
    return STORE.phase_at(_now())


initialize()
'''


def _parameter_callback_source():
    return """def onValueChange(par, prev):\n    op('/project1/material_state_runtime').module.controls_changed()\n    return\n"""


def _frame_callback_source():
    return """def onFrameStart(frame):\n    op('/project1/material_state_runtime').module.tick()\n    return\n"""


def build():
    project = op(ROOT)
    controls = op(CONTROLS)
    player = op(ROOT + "/madmapper_material_player")
    if project is None or controls is None or player is None:
        raise RuntimeError("Material player controls are incomplete")

    # Reuse the reviewed framing implementation.  It adds Focus/Zoom and the
    # fifth uniform block but never touches output or saves the project.
    from pixelblaze_mapper import material_control_surface

    # Regular Python imports do not inherit TouchDesigner's injected globals.
    # Pass the current project lookup explicitly before calling the adapter.
    material_control_surface.op = op
    material_control_surface.install()
    page = _page(controls, "Material State")
    _ensure_float(controls, page, "Globalmasterspeed", "Global Master Speed", 1.0, 0.0, 4.0)

    table = op(STATE_TABLE) or project.create(tableDAT, "material_state_table")
    if table.numRows == 0:
        table.appendRow(("key", "json"))

    runtime = op(RUNTIME) or project.create(textDAT, "material_state_runtime")
    runtime.text = _runtime_source()

    callback = project.op("material_state_callbacks") or project.create(parameterexecuteDAT, "material_state_callbacks")
    callback.par.op = controls.path
    callback.par.pars = "Source Material Speed Scale Width Focusx Focusy Framezoom Gradientpreset Color* Coordinatemode Globalmasterspeed"
    callback.par.valuechange = True
    callback.text = _parameter_callback_source()

    frame = project.op("material_phase_execute") or project.create(executeDAT, "material_phase_execute")
    frame.par.framestart = True
    frame.text = _frame_callback_source()

    player.par.vec0valuey.expr = "op('/project1/material_state_runtime').module.phase()"
    imported = op(ROOT + "/madmapper_library/live_preview")
    if imported is not None:
        imported.par.const0value.expr = "op('/project1/material_state_runtime').module.phase()"

    runtime.module.initialize()
    return {
        "runtime": runtime.path,
        "stateTable": table.path,
        "globalMasterSpeed": float(controls.par.Globalmasterspeed.eval()),
        "networkOutputEnabled": False,
        "projectSaved": False,
    }


if "op" in globals():
    print(build())
