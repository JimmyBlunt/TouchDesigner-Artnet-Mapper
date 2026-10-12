"""Versioned, idempotent hooks for embedded TouchDesigner editor callbacks."""

MARKER = '# MK2_EDITOR_V020'


def install_editor_source(source):
    if MARKER in source:
        return source
    for name in ('record_tick','stop_recording','_store_state_in_cue','_effective_parameters','_write_uniforms','_material_phase'):
        if ('def '+name+'(') not in source:
            raise ValueError('MK2 benötigt Editor-Funktion '+name)
    source += '''
# MK2_EDITOR_V020
from pixelblaze_mapper import mk2_td as _mk2
_mk2_record_tick = record_tick
def record_tick(elapsed):
    host = _mk2._host
    if host is None or not host.take or not host.recording:
        return _mk2_record_tick(elapsed)
    try:
        drive_imported_slots()
        host.sample(elapsed)
    except Exception as error:
        stop_recording(reason='error')
        _message('MK2-Aufnahme beendet: ' + str(error))

_mk2_stop_recording = stop_recording
def stop_recording(reason=''):
    result = _mk2_stop_recording(reason)
    if _mk2._host is not None:
        _mk2._host.recording_stopped()
    return result

_mk2_store_state = _store_state_in_cue
def _store_state_in_cue(cue_id):
    host = _mk2._host
    if host is not None and host.take and host.take['kind'] == 'automation' and host.take['cue_id'] == cue_id:
        OWNER.unstore(STATE_KEY)
        return
    return _mk2_store_state(cue_id)

_mk2_effective = _effective_parameters
def _effective_parameters(cue, on_air):
    host = _mk2._host
    if on_air and host is not None and host.take and host.take['cue_id'] == cue['id']:
        result = dict(cue['parameters'])
        moment = float(OWNER.op('callbacks').module._get('elapsed',0))
        result.update({k:v for k,v in automation.values_at(_cached_automation(),cue['id'],moment).items() if not k.startswith('mat_')})
        result.update({k:v for k,v in _mk2.live_values(cue['id']).items() if not k.startswith('mat_')})
    else:
        result = dict(_mk2_effective(cue,on_air))
    if on_air and not editor.is_imported(cue):
        master = _mk2.show_value('global_master_speed',None)
        if master is not None:
            result['speed'] = result.get('speed',1.) * master
    return result

_mk2_imported_overrides = _imported_overrides
def _imported_overrides(slot,cue_id):
    host = _mk2._host
    if host is not None and host.take and host.take['cue_id'] == cue_id:
        transport = OWNER.op('callbacks').module
        if str(transport._get('outgoing_slot','A')).strip().lower() == slot:
            values = automation.values_at(_cached_automation(),cue_id,float(transport._get('elapsed',0)))
            values.update(_mk2.live_values(cue_id))
            return {k:v for k,v in values.items() if k.startswith('mat_')}
    return _mk2_imported_overrides(slot,cue_id)

_mk2_uniforms = _write_uniforms
def _write_uniforms(renderer,adaptation,values):
    # Defaults must come from this cue, not the unrelated browser material.
    slot = 'a' if renderer.name == 'slot_a_import' else 'b'
    index = _slot_cue_index(slot)
    cues = _cached_show().get('cues',())
    defaults = imported_data().get(cues[index]['id'],{}).get('values',{}) if index is not None and 0 <= index < len(cues) else {}
    return _mk2_uniforms(renderer,adaptation,_mk2.expand_native(adaptation.schema,values,defaults))

_mk2_phase = _material_phase
def _material_phase():
    return _mk2.show_phase(_mk2_phase())
'''
    compile(source,'<mk2 editor>','exec')
    return source


def install_transport_source(source):
    return source
