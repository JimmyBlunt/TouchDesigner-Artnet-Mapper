"""Explicit scan checkpoint; evidence only, no camera or Art-Net activation."""
import argparse
import json
from pathlib import Path
from audit_20260907_capture import td
from performance_checkpoint_20260907 import CHECK, SAVE
from scan_integration_check import STATE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/implementation-2026-09-07/guided-scan-evidence'
SAFE = '''
from pixelblaze_mapper import guided_scan_live as live, scan_output_guard
live.assert_outputs_off(op)
assert not scan_output_guard.active()
assert all(h is None or h.process.poll() is not None for h in (live._probe, live._capture))
'''


def record(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
    return data


def compare():
    before = json.loads((OUT/'before-save.json').read_text())
    after = json.loads((OUT/'after-reopen.json').read_text())
    checks = {k: before[k] == after[k] for k in ('controls', 'workspace_hash',
        'material_id', 'library_parameter_store', 'layout_history_hash',
        'fixture_history_hash', 'fixture_history_depth')}
    def settings(store):
        return {**store, 'materials': {key: {k:v for k,v in value.items()
            if k not in ('phase', 'last_time')} for key,value in store['materials'].items()}}
    checks['p1_settings'] = settings(before['p1_store']) == settings(after['p1_store'])
    checks.update({path: before['table_hashes'][path] == after['table_hashes'][path]
        for path in before['table_hashes'] if path != '/project1/material_state_table'})
    checks.update(no_errors=not after['errors'], no_pickle_errors=not after['runtime_pickle_failures'],
        sender_off=not after['sender']['enabled'],
        no_packets_sent=after['sender']['telemetry']['packet_count'] == 0)
    state = td(SAFE + STATE)
    checks['native_outputs_off'] = all(not n['active'] for n in state['native'])
    checks['camera_stopped'] = state['camera'] is None or state['camera'].get('state') == 'stopped'
    result = record('roundtrip.json', {'checks':checks, 'passed':all(checks.values()),
        'file':after['folder']+'/'+after['file'], 'scan_state':state})
    assert result['passed'], result
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['camera-evidence','before-save','save','reload','after-reopen','compare'])
    action = parser.parse_args().action
    if action == 'camera-evidence':
        result = record('camera-live-test.json', td(SAFE + STATE))
    elif action in ('before-save','after-reopen'):
        result = record(action+'.json', td(SAFE + CHECK))
        result = {k:v for k,v in result.items() if k not in ('library_parameter_store','p1_store','controls','sender','table_hashes')}
    elif action == 'save':
        target = ROOT/'Backup/Implementation/PixelblazeMapper_20260907_GUIDED_SCAN_ARTNET.toe'
        if list(target.parent.glob(target.stem+'*.toe')) or (OUT/'save.json').exists():
            raise ValueError('Candidate or save evidence already exists')
        result = record('save.json', td(SAFE + (SAVE % target.as_posix())))
    elif action == 'reload':
        saved = json.loads((OUT/'save.json').read_text())
        target = Path(saved['folder'])/saved['file']
        assert saved['saved'] and target.is_file()
        result = td(SAFE + "\nimport json\nrun('project.load(args[0])',%r,delayFrames=10)\nresult=json.dumps({'scheduled':%r})" % (target.as_posix(), target.as_posix()))
    else:
        result = compare()
    print(json.dumps(result, indent=2))
