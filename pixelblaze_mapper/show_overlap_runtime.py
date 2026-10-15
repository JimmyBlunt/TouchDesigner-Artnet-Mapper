"""Opt-in clip-local TD rendering, preserving the complete legacy path.

No operator access on import. Installers only return source; native calls occur
in installed callbacks on TD's main thread. Spatial transitions mask each clip's
envelope; crossfade uses the envelopes directly (normalizing only excess gain).
"""
from bisect import bisect_right
from functools import lru_cache
import json

from . import show_automation as automation

MARKER = '# SHOW_OVERLAP_EDITOR_V1'


def effective_parameters(cue, data, elapsed, live=None):
    result = dict(cue['parameters'])
    values = automation.values_at(data, cue['id'], elapsed)
    values.update(live or {})
    result.update({k: v for k, v in values.items() if k in result or k == 'global_master_speed'})
    return result


def _curve(data, cue_id, name):
    edited = data.get('edits', {}).get(cue_id, {}).get(name)
    if edited and edited.get('enabled', True):
        return edited['points'], edited['mode']
    return data.get('tracks', {}).get(cue_id, {}).get(name, []), 'linear'


@lru_cache(maxsize=64)
def _phase_curve(signature):
    base, speed, master = json.loads(signature)
    def rate(moment):
        a = automation.value_at(speed[0], moment, speed[1]) if speed[0] else base
        b = automation.value_at(master[0], moment, master[1]) if master[0] else 1.
        return a * b
    # Four-point Gaussian quadrature is exact for the product of two cubic
    # smooth curves; split at every keyframe so step curves remain exact too.
    def integral(start, end):
        half, mid = (end-start)*.5, (end+start)*.5
        return half * sum(weight*rate(mid+half*node) for node, weight in (
            (-.8611363115940526, .3478548451374538),
            (-.3399810435848563, .6521451548625461),
            (.3399810435848563, .6521451548625461),
            (.8611363115940526, .3478548451374538)))
    knots = sorted({0.} | {float(p[0]) for curve in (speed, master) for p in curve[0]})
    prefix = [0.]
    for start, end in zip(knots, knots[1:]):
        prefix.append(prefix[-1] + integral(start, end))
    return knots, prefix, integral


def clip_phase(cue, data, elapsed):
    """Seek/pause-safe animation phase from this clip's two recorded speeds."""
    signature = json.dumps([float(cue['parameters'].get('speed', 1.)),
                            _curve(data, cue['id'], 'speed'),
                            _curve(data, cue['id'], 'global_master_speed')], separators=(',', ':'))
    knots, prefix, integral = _phase_curve(signature)
    elapsed = max(0., float(elapsed))
    index = max(0, bisect_right(knots, elapsed)-1)
    return prefix[index] + integral(knots[index], elapsed)


def _value(resolve, path, key, default=''):
    table = resolve(path)
    if table is not None:
        for row in range(1, table.numRows):
            if str(table[row, 0]) == key:
                return str(table[row, 1])
    return default


def render_options(resolve):
    request = 'transition_adapter/mixer_request'
    if _value(resolve, request, 'timing_mode', 'legacy') != 'overlap':
        return {}
    values = {'timing_mode': 'overlap'}
    editor = resolve('editor_callbacks')
    for slot in ('a', 'b'):
        for suffix in ('gain', 'brightness'):
            key = 'slot_' + slot + '_' + suffix
            values[key] = float(_value(resolve, request, key, '0'))
        if editor is not None and hasattr(editor.module, 'overlap_slot_tone'):
            values['slot_' + slot + '_tone'] = editor.module.overlap_slot_tone(slot)
    return values


def sync_mixer(mixer, resolve):
    """Fill extra uniforms; never modify UVs, inputs or output routing."""
    options = render_options(resolve)
    if int(mixer.par.vec.sequence.numBlocks) < 5:
        mixer.par.vec.sequence.numBlocks = 5
    blocks = [('uOverlap', tuple(options.get('slot_'+s+'_'+key, 1.) for key in ('gain', 'brightness') for s in ('a', 'b'))),
              ('uOverlapMode', (float(bool(options)), 0., 0., 0.))]
    for slot in ('a', 'b'):
        tone = options.get('slot_' + slot + '_tone')
        blocks.append(('uSlotTone'+slot.upper(), (*tone, 1., 0.) if tone is not None else (1., 1., 0., 0.)))
    for index, (name, values) in enumerate(blocks, 1):
        getattr(mixer.par, 'vec%dname' % index).val = name
        for suffix, value in zip('xyzw', values):
            getattr(mixer.par, 'vec%dvalue%s' % (index, suffix)).val = value


def render_numpy(a, b, u, v, **options):
    """Compatibility for optionally installed, separately owned NumPy fastpath."""
    import numpy as np
    if options.get('timing_mode', 'legacy') != 'overlap':
        try:
            from .show_performance import render_numpy as fast
        except ImportError:
            fast = None
        if fast is not None:
            return fast(a, b, u, v, **options)
    from .show_renderer import render_frame
    return np.asarray(render_frame(np.asarray(a).tolist(), np.asarray(b).tolist(), u=u, v=v, **options), dtype=np.float32)


def install_editor_source(source):
    if MARKER not in source:
        # Existing DATs also receive the explicit new-show default. Existing
        # loaded JSON is never rewritten or migrated by this installer.
        source = source.replace('write(dict(editor.EMPTY_SHOW))', 'write(editor.empty_show())')
        source += EDITOR_HOOK
    compile(source, '<overlap editor>', 'exec')
    return source


def _insert(source, present, anchor, addition):
    if present in source:
        return source
    if source.count(anchor) != 1:
        raise ValueError('Unknown Show callback; overlap installation refused: ' + present)
    return source.replace(anchor, anchor+addition, 1)


def install_transport_source(source):
    source = _insert(source, "_put(path, 'local_time', slot_time)",
                     "        _put(path, 'animation_time', slot_time)\n", """        _put(path, 'cue_id', slot.id if slot else '')
        _put(path, 'local_time', slot_time)
        _put(path, 'timing_mode', getattr(plan, 'timing_mode', 'legacy'))
""")
    source = _insert(source, "_put('transition_adapter/mixer_request', 'timing_mode'",
                     "    _put('transition_adapter/mixer_request', 'brightness', plan.brightness)\n", """    _put('transition_adapter/mixer_request', 'timing_mode', getattr(plan, 'timing_mode', 'legacy'))
    for slot_name in ('a', 'b'):
        for suffix in ('gain', 'brightness'):
            key = 'slot_' + slot_name + '_' + suffix
            _put('transition_adapter/mixer_request', key, getattr(plan, key, 1.0))
""")
    compile(source, '<overlap transport>', 'exec')
    return source


def install_render_source(source):
    source = _insert(source, "editor.module.overlap_slot_phase(slot)",
                     "    for name, value in values.items():\n        _set_parameter(player, name, value)\n", """    if editor is not None and hasattr(editor.module, '_overlap_enabled') and editor.module._overlap_enabled():
        slot = 'a' if player_name == 'slot_a_player' else 'b'
        _set_parameter(player, 'vec0valuey', editor.module.overlap_slot_phase(slot))
""")
    source = _insert(source, '    sync_mixer(mixer, op)',
                     '        _set_parameter(mixer, name, value)\n', """    from pixelblaze_mapper.show_overlap_runtime import sync_mixer
    sync_mixer(mixer, op)
""")
    compile(source, '<overlap render sync>', 'exec')
    return source


def install_led_source(source):
    source = _insert(source, "fromlist=['render_options']",
                     '        targets_a=targets_a, targets_b=targets_b, source_groups=source_groups,\n',
                     "        **__import__('pixelblaze_mapper.show_overlap_runtime', fromlist=['render_options']).render_options(op),\n")
    if '# SHOW_NUMPY_MIX_V1' in source:
        source = source.replace('    frame = render_numpy(',
            "    frame = __import__('pixelblaze_mapper.show_overlap_runtime', fromlist=['render_numpy']).render_numpy(")
    compile(source, '<overlap LED renderer>', 'exec')
    return source


def prepare_install(owner):
    """Return validated DAT texts for review/apply; does not modify native TD.

    The host must preserve its transport state around DAT module replacement.
    Existing loaded Show JSON, cues, automation, UVs and outputs stay untouched.
    This upgrades an existing editor that already has Timeline/MK2 hooks.
    """
    from .integrate_live_show import TRANSITION_SHADER
    result = {}
    for name, installer in (('callbacks', install_transport_source),
                            ('editor_callbacks', install_editor_source),
                            ('render_sync', install_render_source),
                            ('show_led_renderer_callbacks', install_led_source)):
        node = owner.op(name)
        if node is None:
            raise ValueError('Missing existing Show DAT: ' + name)
        result[name] = installer(node.text)
    if owner.op('show_transition_fs') is None:
        raise ValueError('Missing existing Show transition shader')
    result['show_transition_fs'] = TRANSITION_SHADER
    return result


def install(owner):
    """Upgrade existing DATs atomically on TD's main thread, once per session.

    Return a retryable status for partial builds/recording. Preserve the actual
    running sequencer object across module replacement; never seek, play,
    rewrite Show JSON or change a material/output parameter here.
    """
    required = ('callbacks', 'editor_callbacks', 'render_sync', 'show_led_renderer_callbacks', 'show_transition_fs')
    if owner is None or any(owner.op(name) is None for name in required):
        return {'status': 'not_ready', 'installed': False, 'changed': []}
    editor_node = owner.op('editor_callbacks')
    editor = editor_node.module
    if hasattr(editor, '_state') and editor._state('recording', '0') == '1':
        return {'status': 'recording', 'installed': False, 'changed': []}
    prepared = prepare_install(owner)
    changed = [name for name, text in prepared.items() if owner.op(name).text != text]
    if not changed:
        return {'status': 'ready', 'installed': True, 'changed': []}
    originals = {name: owner.op(name).text for name in changed}
    transport = owner.op('callbacks').module
    runtime_record = getattr(transport, '_runtime_record', None)
    # A fresh module may have no transient record, in which case its existing
    # table-backed reopen policy stays in charge (never auto-resume a .toe).
    phases = getattr(editor, '_overlap_live_phases', {})
    applied = []
    try:
        for name in changed:
            applied.append(name)
            owner.op(name).text = prepared[name]
        if runtime_record is not None:
            owner.op('callbacks').module._runtime_record = runtime_record
            owner.op('callbacks').module._sync_record = None
        if phases:
            owner.op('editor_callbacks').module._overlap_live_phases = phases
    except Exception:
        failures = []
        for name in reversed(applied):
            try:
                owner.op(name).text = originals[name]
            except Exception as error:
                failures.append('%s: %s' % (name, error))
        if runtime_record is not None:
            owner.op('callbacks').module._runtime_record = runtime_record
        if failures:
            raise RuntimeError('Overlap installation rollback incomplete: ' + '; '.join(failures))
        raise
    return {'status': 'ready', 'installed': True, 'changed': changed}


EDITOR_HOOK = r'''
# SHOW_OVERLAP_EDITOR_V1
from pixelblaze_mapper import show_overlap_runtime as _overlap

def _overlap_enabled():
    return _cached_show().get('timing_mode', 'legacy') == 'overlap'

def _overlap_context(slot):
    request = 'slot_%s_adapter/material_request' % slot
    cue_id = _request_value(request, 'cue_id', '')
    cue = next((c for c in _cached_show().get('cues', ()) if c['id'] == cue_id), None)
    moment = float(_request_value(request, 'local_time', '0'))
    return cue, moment

_overlap_base_index = _slot_cue_index
def _slot_cue_index(slot):
    if not _overlap_enabled():
        return _overlap_base_index(slot)
    cue, moment = _overlap_context(str(slot).lower())
    return next((i for i, c in enumerate(_cached_show().get('cues', ())) if cue and c['id'] == cue['id']), None)

def _overlap_live(cue, slot):
    from pixelblaze_mapper.show_midi import live_values
    outgoing = str(OWNER.op('callbacks').module._get('outgoing_slot', 'A')).lower()
    return live_values(cue['id']) if slot == outgoing else {}

def _overlap_recording(cue, slot):
    outgoing = str(OWNER.op('callbacks').module._get('outgoing_slot', 'A')).lower()
    return slot == outgoing and _state('recording', '0') == '1' and _state('record_cue', '') == cue['id']

def _overlap_parameters(cue, slot, moment):
    values = _overlap.effective_parameters(cue, _cached_automation(), moment, _overlap_live(cue, slot))
    # Non-MK2 recordings still use the editor's existing live monitor.
    if _overlap_recording(cue, slot):
        host = getattr(_mk2, '_host', None)
        if not (host is not None and host.take):
            values.update(_live_monitor(values))
    return values

_overlap_base_overlay = overlay
def overlay(player_name, parameters):
    if not _overlap_enabled():
        return _overlap_base_overlay(player_name, parameters)
    slot = 'a' if str(player_name).endswith('slot_a_player') else 'b'
    cue, moment = _overlap_context(slot)
    if cue is None:
        return parameters
    values = _overlap_parameters(cue, slot, moment)
    # Core render_sync multiplies animation_time by speed. A dedicated phase
    # wrapper below writes the integrated clock after that legacy assignment.
    return values

_overlap_base_imported = _imported_overrides
def _imported_overrides(slot, cue_id):
    if not _overlap_enabled():
        return _overlap_base_imported(slot, cue_id)
    cue, moment = _overlap_context(slot)
    if cue is None:
        return {}
    values = _overlap.automation.values_at(_cached_automation(), cue_id, moment)
    host = getattr(_mk2, '_host', None)
    if _overlap_recording(cue, slot) and not (host is not None and host.take):
        values.update(live_imported_values())
    values.update(_overlap_live(cue, slot))
    return {k: v for k, v in values.items() if k.startswith('mat_')}

_overlap_live_phases = {}
def overlap_slot_phase(slot):
    cue, moment = _overlap_context(slot)
    if cue is None:
        return 0.
    data = _cached_automation()
    baseline = _overlap.clip_phase(cue, data, moment)
    recording = _overlap_recording(cue, slot)
    live_speed = any(key in _overlap_live(cue, slot) for key in ('speed', 'global_master_speed'))
    if not recording and not live_speed:
        _overlap_live_phases.pop(slot, None)
        return baseline
    values = _overlap_parameters(cue, slot, moment)
    rate = float(values.get('speed', 1.)) * float(values.get('global_master_speed', 1.))
    previous = _overlap_live_phases.get(slot)
    sequence = OWNER.op('callbacks').module.runtime()
    revision = (id(sequence), getattr(sequence, 'position_revision', 0))
    phase = baseline
    if previous and len(previous) > 4 and previous[4] == revision and previous[0] == cue['id'] and moment >= previous[1]:
        phase = previous[2] + (moment-previous[1])*previous[3]
    _overlap_live_phases[slot] = (cue['id'], moment, phase, rate, revision)
    return phase

_overlap_base_system = _write_system_uniforms
def _write_system_uniforms(renderer, parameters, coordinate_mode):
    result = _overlap_base_system(renderer, parameters, coordinate_mode)
    if _overlap_enabled() and renderer is not None:
        slot = 'a' if renderer.name == 'slot_a_import' else 'b'
        renderer.par.vec0valuex.val = overlap_slot_phase(slot)
    return result

_overlap_base_drive = drive_imported_slots
def drive_imported_slots():
    if not _overlap_enabled():
        return _overlap_base_drive()
    for slot in ('a', 'b'):
        cue, moment = _overlap_context(slot)
        renderer = OWNER.op('slot_%s_import' % slot)
        if cue is None or renderer is None or not editor.is_imported(cue):
            continue
        _write_system_uniforms(renderer, _overlap_parameters(cue, slot, moment), cue.get('coordinate_mode', 'global'))
        item = _library_item(editor.material_id(cue))
        adaptation, defaults = _library()._parameter_context(item)
        # Always restore this cue's values, even after an earlier take or
        # disabled automation left an old uniform in this reused A/B slot.
        values = imported_values(cue['id'], editor.material_id(cue), defaults)
        from pixelblaze_mapper import mk2_td as _overlap_mk2
        values = {p['id']: p['value'] for p in _overlap_mk2.native_parameters(adaptation.schema, values)}
        values.update(_imported_overrides(slot, cue['id']))
        _write_uniforms(renderer, adaptation, values)

def overlap_slot_tone(slot):
    if not _overlap_enabled():
        return None
    cue, moment = _overlap_context(slot)
    if cue is None or not editor.is_imported(cue):
        return None
    values = _overlap_parameters(cue, slot, moment)
    return (float(values.get('intensity', 1.)), float(values.get('contrast', 1.)))
'''
