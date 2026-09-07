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

GRADIENT_SHADER_SOURCE = r'''uniform vec4 uGradientA;
uniform vec4 uGradientB;
uniform vec4 uMaterialTone; // intensity, contrast, is import, colour mode
out vec4 fragColor;

void main()
{
    vec4 source = texture(sTD2DInputs[0], vUV.st);
    vec3 raw = source.rgb;
    if (uMaterialTone.z > 0.5) {
        // Imported shaders have no Core intensity/contrast stage. Keep black
        // black; apply contrast here and intensity after any recolouring.
        source.rgb = max(source.rgb, vec3(0.0));
        source.rgb = mix(vec3(0.0), clamp((source.rgb - 0.5) * uMaterialTone.y + 0.5, 0.0, 1.0),
                         step(vec3(0.000001), source.rgb));
    }
    float luma = clamp(dot(source.rgb, vec3(0.2126, 0.7152, 0.0722)), 0.0, 1.0);
    float position = smoothstep(0.0, 1.0, luma);
    vec3 palette = mix(uGradientB.rgb, uGradientA.rgb, position);
    vec3 recolored = palette * (uMaterialTone.w > 1.5 ? mix(0.38, 1.18, luma) : luma);
    vec3 result = mix(source.rgb, recolored, clamp(uGradientA.a, 0.0, 1.0));
    if (uMaterialTone.z > 0.5) result *= max(uMaterialTone.x, 0.0);
    // Even legacy recolouring must respect an explicit blackout value.
    if (uMaterialTone.x <= 0.0) result = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(result, source.a));
}
'''

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


def _set_expression(parameter, expression):
    parameter.mode = ParMode.EXPRESSION
    parameter.expr = expression


def _install_gradient_postprocess(controls):
    """Install one visible duotone stage shared by Core and imported materials."""
    project = op(ROOT)
    source = op(ROOT + "/visual_source_switch")
    output = op(ROOT + "/res1")
    if project is None or source is None or output is None:
        raise RuntimeError("Material source switch or canonical res1 output is missing")

    shader = project.op("material_gradient_fs") or project.create(textDAT, "material_gradient_fs")
    shader.text = GRADIENT_SHADER_SOURCE
    player = project.op("material_gradient_player") or project.create(glslTOP, "material_gradient_player")
    player.par.glslversion = "glsl430"
    player.par.mode = "vertexpixel"
    player.par.pixeldat = shader.path
    if player.par.outputresolution is not None:
        player.par.outputresolution = "useinput"
    player.par.vec.sequence.numBlocks = max(int(player.par.vec.sequence.numBlocks), 3)
    player.par.vec0name = "uGradientA"
    player.par.vec1name = "uGradientB"
    for suffix, component in zip("rgb", "xyz"):
        _set_expression(
            getattr(player.par, "vec0value" + component),
            "op(%r).par.Color%s" % (CONTROLS, suffix),
        )
        _set_expression(
            getattr(player.par, "vec1value" + component),
            "op(%r).par.Color2%s" % (CONTROLS, suffix),
        )
    # Recolour only material sources. Movie and show playback remain untouched.
    _set_expression(
        player.par.vec0valuew,
        "op(%r).par.Gradientstrength if op(%r).par.Source.eval() in ('materials', 'imported') and op(%r).par.Colormode.eval() != 'original' else 0.0" % (CONTROLS, CONTROLS, CONTROLS),
    )
    player.par.vec1valuew = 1.0
    player.par.vec2name = 'uMaterialTone'
    _set_expression(player.par.vec2valuex, "op(%r).par.Intensity if op(%r).par.Source.eval() in ('materials', 'imported') else 1.0" % (CONTROLS, CONTROLS))
    _set_expression(player.par.vec2valuey, "op(%r).par.Contrast" % CONTROLS)
    _set_expression(player.par.vec2valuez, "1.0 if op(%r).par.Source.eval() == 'imported' else 0.0" % CONTROLS)
    _set_expression(player.par.vec2valuew, "op(%r).par.Colormode.menuIndex" % CONTROLS)

    if not player.inputs or player.inputs[0] != source:
        if player.inputs:
            player.inputConnectors[0].disconnect()
        source.outputConnectors[0].connect(player)
    if not output.inputs or output.inputs[0] != player:
        if output.inputs:
            output.inputConnectors[0].disconnect()
        player.outputConnectors[0].connect(output)
    player.nodeX, player.nodeY = source.nodeX + 180, source.nodeY
    shader.nodeX, shader.nodeY = player.nodeX, player.nodeY - 130
    return player


def _runtime_source():
    return r'''import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pixelblaze_mapper.material_state import MaterialSettings, MaterialStateStore
from pixelblaze_mapper.material_storage import runtime_cache, state_document

CONTROLS = op('/project1/madmapper_player_controls')
TABLE = op('/project1/material_state_table')
STATE_OWNER = op('/project1')
STORE_KEY = 'p1_material_state_store'
INIT_KEY = 'p1_material_state_runtime_schema'
RUNTIME_SCHEMA = 3
_stored = STATE_OWNER.fetch(STORE_KEY, None)
_runtime_cache = runtime_cache(STATE_OWNER, 'p1_material_runtime_cache')
_runtime_store = _runtime_cache.get('store')
if isinstance(_runtime_store, MaterialStateStore):
    STORE = _runtime_store
else:
    # Convert stale pre-reload instances by their data, not class identity.
    _document = state_document(_runtime_store if _runtime_store is not None else _stored)
    STORE = MaterialStateStore.from_dict(_document) if _document is not None else MaterialStateStore()
    _runtime_cache['store'] = STORE
if _stored is not None and not isinstance(_stored, dict):
    STATE_OWNER.store(STORE_KEY, state_document(STORE))
_durable_document = STATE_OWNER.fetch(STORE_KEY, None)
# The live marker skips expensive reinitialization after DAT reload. It must
# not survive a file reopen, which needs to rebase the persisted phase clock.
if hasattr(STATE_OWNER, 'storeStartupValue'):
    STATE_OWNER.storeStartupValue(INIT_KEY, None)
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
    global _durable_document
    _durable_document = STORE.to_dict()
    STATE_OWNER.store(STORE_KEY, _durable_document)
    _runtime_cache['store'] = STORE
    STATE_OWNER.store(INIT_KEY, RUNTIME_SCHEMA)
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
        intensity=float(CONTROLS.par.Intensity.eval()),
        contrast=float(CONTROLS.par.Contrast.eval()),
        color_mode=str(CONTROLS.par.Colormode.eval()),
        gradient_strength=float(CONTROLS.par.Gradientstrength.eval()),
    )


def _apply(settings):
    global _applying
    previous_applying = _applying
    _applying = True
    try:
        CONTROLS.par.Speed = settings.speed
        CONTROLS.par.Scale = settings.scale
        CONTROLS.par.Width = settings.width
        CONTROLS.par.Focusx = settings.focus_x
        CONTROLS.par.Focusy = settings.focus_y
        CONTROLS.par.Framezoom = settings.zoom
        CONTROLS.par.Intensity = settings.intensity
        CONTROLS.par.Contrast = settings.contrast
        CONTROLS.par.Colormode = settings.color_mode
        CONTROLS.par.Gradientstrength = settings.gradient_strength
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
        _applying = previous_applying


def _current_key():
    source = str(CONTROLS.par.Source.eval())
    if source == 'materials':
        return 'core:' + str(CONTROLS.par.Material.eval())
    if source == 'imported':
        if STORE.active_key and STORE.active_key.startswith('madmapper:'):
            return STORE.active_key
        state = op('/project1/madmapper_library/browser_state')
        if state is not None:
            values = {str(state[row, 0]): str(state[row, 1]).strip() for row in range(1, state.numRows)}
            material_id = values.get('active_id') or values.get('live_preview_id')
            if material_id:
                return 'madmapper:' + material_id
            for row in range(1, state.numRows):
                if str(state[row, 0]) == 'selected_id' and str(state[row, 1]).strip():
                    return 'madmapper:' + str(state[row, 1]).strip()
    return source + ':default'


def initialize(force=False):
    global STORE
    if not force and STATE_OWNER.fetch(INIT_KEY, None) == RUNTIME_SCHEMA:
        existing = _runtime_cache.get('store')
        if isinstance(existing, MaterialStateStore):
            STORE = existing
            return STORE.active_key
    # Storage includes the most recent phase tick; the DAT is a recovery copy
    # updated only on settings/activation, not at frame rate.
    document = STATE_OWNER.fetch(STORE_KEY, None)
    if not isinstance(document, dict):
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
    global _applying
    now = _now()
    if STORE.active_key is not None:
        STORE.set_active_settings(_settings_from_controls(), now)
    initial = MaterialSettings()
    if preset:
        initial = replace(
            initial,
            scale=float(preset.get('scale', initial.scale)),
            width=float(preset.get('width', initial.width)),
        )
    state = STORE.activate(str(key), now, initial=initial)
    _applying = True
    try:
        if str(key).startswith('core:'):
            CONTROLS.par.Source = 'materials'
            CONTROLS.par.Material = str(key).split(':', 1)[1]
        elif str(key).startswith('madmapper:'):
            CONTROLS.par.Source = 'imported'
        _apply(state.settings)
    finally:
        _applying = False
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
    value = STORE.tick(_now())
    # Keep just two primitive clock scalars current in the existing dictionary.
    # No store(), DAT rewrite, JSON encoding, or all-material copy per frame.
    if isinstance(_durable_document, dict) and STORE.active_key is not None:
        saved = _durable_document.get('materials', {}).get(STORE.active_key)
        if saved is not None:
            state = STORE.state(STORE.active_key)
            saved['phase'] = float(state.phase)
            saved['last_time'] = state.last_time
    return value


def phase():
    return tick()


if STATE_OWNER.fetch(INIT_KEY, None) != RUNTIME_SCHEMA:
    initialize()
'''


def _parameter_callback_source():
    return """def onValueChange(par, prev):\n    op('/project1/material_state_runtime').module.controls_changed()\n    return\n"""


def _frame_callback_source():
    return """def onFrameStart(frame):
    runtime = op('/project1/material_state_runtime')
    runtime.module.tick()
    phase = runtime.module.phase()
    player = op('/project1/madmapper_material_player')
    if player is not None:
        player.par.vec0valuey.val = phase
    imported = op('/project1/madmapper_library/live_preview')
    if imported is not None:
        imported.par.vec0valuex.val = phase
        controls = op('/project1/madmapper_player_controls')
        if controls is not None and controls.par.Source.eval() == 'imported':
            imported.cook(force=True)
    return
"""


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
    _install_gradient_postprocess(controls)
    page = _page(controls, "Material State")
    _ensure_float(controls, page, "Globalmasterspeed", "Global Master Speed", 1.0, 0.0, 4.0)

    table = op(STATE_TABLE) or project.create(tableDAT, "material_state_table")
    if table.numRows == 0:
        table.appendRow(("key", "json"))

    runtime = op(RUNTIME) or project.create(textDAT, "material_state_runtime")
    runtime.text = _runtime_source()

    callback = project.op("material_state_callbacks") or project.create(parameterexecuteDAT, "material_state_callbacks")
    callback.par.op = controls.path
    callback.par.pars = "Source Material Speed Scale Width Focusx Focusy Framezoom Intensity Contrast Gradientpreset Gradientstrength Color* Coordinatemode Globalmasterspeed"
    callback.par.valuechange = True
    callback.text = _parameter_callback_source()

    frame = project.op("material_phase_execute") or project.create(executeDAT, "material_phase_execute")
    frame.par.framestart = True
    frame.text = _frame_callback_source()

    # A Python module call in a parameter expression does not establish a
    # TouchDesigner cook dependency. Push phase explicitly from the per-frame
    # Execute DAT so imported shaders actually render new frames.
    player.par.vec0valuey.expr = ""
    imported = op(ROOT + "/madmapper_library/live_preview")
    if imported is not None:
        imported.par.vec0valuex.expr = ""

    runtime.module.initialize(force=True)
    initial_phase = runtime.module.phase()
    player.par.vec0valuey.val = initial_phase
    if imported is not None:
        imported.par.vec0valuex.val = initial_phase
    return {
        "runtime": runtime.path,
        "stateTable": table.path,
        "globalMasterSpeed": float(controls.par.Globalmasterspeed.eval()),
        "networkOutputEnabled": False,
        "projectSaved": False,
    }


if "op" in globals():
    print(build())
