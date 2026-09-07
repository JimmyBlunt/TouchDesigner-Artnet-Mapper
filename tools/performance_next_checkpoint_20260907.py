"""Scoped bulk-transfer installation and save/reopen evidence; hardware stays off."""
import json
import sys
from pathlib import Path
from audit_20260907_capture import td
from performance_checkpoint_20260907 import CHECK, SAVE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/implementation-2026-09-07/performance-next'
INSTALL=r'''
import json,hashlib,importlib
from pixelblaze_mapper import legacy_script4_bulk as bulk
importlib.reload(bulk)
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
for p in ('/project1/esp_artnet_out','/project1/multi_controller_output/dmxout_ws2812_node','/project1/multi_controller_output/dmxout_apa102_esp'):
    assert not op(p).par.active.eval()
dat=op('/project1/script4_callbacks')
original_source=dat.text
replacement=bulk.source_for_bulk(original_source)
module=dat.module
bulk.make_bulk_callback(module.onCook,original_source) # Verify live function, not only stored text.
states=module.led_states
frame_count=module.frame_count
rng=module.random
rng_before=rng.getstate()
old_function=module.onCook
# One synchronous TD call; no cooks, yield, I/O or status queries until handoff completes.
try:
    dat.text=replacement
    updated=dat.module
    updated.led_states=states
    updated.frame_count=frame_count
    rng.setstate(rng_before)
    assert updated.led_states is states and updated.frame_count==frame_count
    assert updated.random is rng and rng.getstate()==rng_before
except Exception:
    dat.text=original_source
    restored=dat.module
    restored.led_states=states
    restored.frame_count=frame_count
    rng.setstate(rng_before)
    raise
result=json.dumps({'source_before_sha256':hashlib.sha256(original_source.encode()).hexdigest(),
 'source_after_sha256':hashlib.sha256(dat.text.encode()).hexdigest(),'state_identity_preserved':True,
 'frame_count_preserved_at_handoff':True,'rng_preserved_at_handoff':True,
 'trigger_unchanged':op('/project1/chopexec1').text,
 'no_hardware_activation':True,'errors':op('/project1').errors(recurse=True)})
'''
CHECK_EXTRA=CHECK+r'''
value=json.loads(result)
value['bulk_source_sha256']=digest(op('/project1/script4_callbacks').text)
value['native_active']={p:bool(op(p).par.active.eval()) for p in ('/project1/esp_artnet_out',
 '/project1/multi_controller_output/dmxout_ws2812_node','/project1/multi_controller_output/dmxout_apa102_esp')}
result=json.dumps(value)
'''

if __name__=='__main__':
    action=sys.argv[1]
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(action+'.json')
    if target.exists(): raise ValueError('Evidence exists')
    if action in ('before-install','before-save','after-reopen'):
        data=td(CHECK_EXTRA)
    elif action=='bulk-install':
        assert json.loads((OUT/'legacy-bulk-native-probe.json').read_text())['passed']
        assert (OUT/'before-install.json').exists()
        data=td(INSTALL)
    elif action=='save':
        toe=ROOT/'Backup/Implementation/PixelblazeMapper_20260907_DEMAND_BULK_VERIFIED.toe'
        if toe.exists(): raise ValueError('Candidate exists')
        data=td(SAVE%toe.as_posix())
    elif action=='reload':
        saved=json.loads((OUT/'save.json').read_text())
        toe=Path(saved['folder'])/saved['file']
        assert saved['saved'] and toe.is_file()
        data=td("import json; assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']; run('project.load(args[0])',%r,delayFrames=10); result=json.dumps({'scheduled':%r})"%(toe.as_posix(),toe.as_posix()))
    elif action=='compare':
        before=json.loads((OUT/'before-save.json').read_text())
        after=json.loads((OUT/'after-reopen.json').read_text())
        initial=json.loads((OUT/'before-install.json').read_text())
        keys=('controls','workspace_hash','material_id','library_parameter_store',
              'layout_history_hash','fixture_history_hash','fixture_history_depth','native_active')
        checks={k:before[k]==after[k]==initial[k] for k in keys}
        def settings(store):
            return {**store,'materials':{key:{k:v for k,v in value.items() if k not in ('phase','last_time')}
                    for key,value in store['materials'].items()}}
        checks['p1_settings']=settings(before['p1_store'])==settings(after['p1_store'])==settings(initial['p1_store'])
        checks.update({p:before['table_hashes'][p]==after['table_hashes'][p]==initial['table_hashes'][p]
            for p in before['table_hashes'] if p!='/project1/material_state_table'})
        installed=json.loads((OUT/'bulk-install.json').read_text())
        checks.update(no_errors=not after['errors'],no_pickle_errors=not after['runtime_pickle_failures'],
            sender_off=not after['sender']['enabled'],no_packets_sent=after['sender']['telemetry']['packet_count']==0,
            bulk_source_persisted=before['bulk_source_sha256']==after['bulk_source_sha256']==installed['source_after_sha256'])
        data={'checks':checks,'passed':all(checks.values()),'file':after['folder']+'/'+after['file']}
    else: raise ValueError(action)
    target.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('controls','p1_store','library_parameter_store','table_hashes','trigger_unchanged','sender')},indent=2))
    if action=='compare': assert data['passed']
