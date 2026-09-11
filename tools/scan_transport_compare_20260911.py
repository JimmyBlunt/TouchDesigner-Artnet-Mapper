"""Explicit user-authorized short A/B scans through the native output guard."""
import csv
import json
from pathlib import Path
import sys
import time
import urllib.request

from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/panel3-preparation-20260911/transport-comparison'
WORKSPACE = ROOT / 'Scans/panel3_transport_diagnostic_20260911'


def controller():
    with urllib.request.urlopen('http://10.0.0.249/api/status', timeout=4) as response:
        return {'time': time.monotonic(), 'status': json.load(response)}


SNAPSHOT = """
import json
from pixelblaze_mapper import guided_scan_live as live
p=op('/project1/guided_scan')
assert live._capture is None or live._capture.process.poll() is not None
assert live._probe is None or live._probe.process.poll() is not None
live.assert_outputs_off(op)
keys=('session','capture_plan','capture_signature','capture_status','message','coverage_summary','workflow_page')
fields=('source_ids','anchors','views','workspace')
labels=('title','routing_summary','status')
result=json.dumps({'storage':{key:p.fetch(key,None) for key in keys},
 'fields':{key:p.op('ui_panel/'+key+'/string').text for key in fields},
 'labels':{key:p.op('ui_panel/'+key).par.text.eval() for key in labels},
 'dats':{key:p.op(key).text for key in ('worker_plan','dry_run')}})
"""


def prepare():
    OUT.mkdir(exist_ok=True)
    WORKSPACE.mkdir(exist_ok=True)
    path = OUT/'native-original.json'
    if path.exists():
        raise RuntimeError('Original snapshot already exists; do not overwrite')
    original = td(SNAPSHOT)
    sets = []
    for name in original['fields']['views'].strip().split(' | '):
        with open(name.strip(), newline='', encoding='utf-8-sig') as stream:
            sets.append({int(row['index']) for row in csv.DictReader(stream)})
    ids = sorted(set.intersection(*sets))[:20]
    assert len(ids) == 20
    original['test_ids'] = ids
    path.write_text(json.dumps(original, indent=2), encoding='utf-8')
    print(json.dumps({'test_ids': ids, 'views_preserved': len(sets)}))


def start(label, gap):
    original = json.loads((OUT/'native-original.json').read_text())
    marker = OUT/(label+'-start.json')
    if marker.exists():
        raise RuntimeError('Test label already used')
    before = controller()
    script = """
import json,importlib
from pixelblaze_mapper import guided_scan_live as live, scan_capture, scan_coverage
p=op('/project1/guided_scan')
assert live._capture is None or live._capture.process.poll() is not None
assert live._probe is None or live._probe.process.poll() is not None
live.assert_outputs_off(op)
importlib.reload(scan_capture)
original=json.loads(%r)
p.store('session',original['storage']['session'])
p.store('capture_status',{})
p.op('ui_panel/source_ids/string').text=%r
p.op('ui_panel/anchors/string').text=''
p.op('ui_panel/views/string').text=''
p.op('ui_panel/workspace/string').text=%r
live.prepare(op)
plan=p.fetch('capture_plan')
plan['packet_gap_ms']=%r
plan=scan_capture.validate_capture_manifest(plan)
p.store('capture_plan',plan)
p.op('worker_plan').text=json.dumps(plan,indent=2)
p.op('ui_panel/title').par.text=%r
scan_coverage._last_key=None
scan_coverage.refresh(op)
live.start(op,confirmed=True)
result=json.dumps({'plan':plan,'directory':str(live._capture.directory),'pid':live._capture.process.pid})
""" % (json.dumps(original), ','.join(map(str, original['test_ids'])),
           str(WORKSPACE), gap, 'TRANSPORT TEST '+label+' | 20 LEDs | packet gap '+str(gap)+' ms')
    started = td(script)
    marker.write_text(json.dumps({'before_controller': before, 'started': started}, indent=2), encoding='utf-8')
    print(json.dumps({'label': label, 'packet_gap_ms': gap, 'directory': started['directory']}))


def observe(label):
    data = td("""
import json
from pixelblaze_mapper import guided_scan_live as live
p=op('/project1/guided_scan')
result=json.dumps({'running':live._capture is not None and live._capture.process.poll() is None,
 'capture':p.fetch('capture_status',{}),'errors':list(p.errors(recurse=True))})
""")
    data['controller'] = controller()
    path = OUT/(label+'-observations.jsonl')
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(data)+'\n')
    if not data['running']:
        (OUT/(label+'-result.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps(data, indent=2))


def restore():
    original = json.loads((OUT/'native-original.json').read_text())
    script = """
import json
from pixelblaze_mapper import guided_scan_live as live, scan_coverage, scan_workflow_ux
p=op('/project1/guided_scan')
assert live._capture is None or live._capture.process.poll() is not None
assert live._token is None
live.assert_outputs_off(op)
original=json.loads(%r)
for key,value in original['storage'].items():p.store(key,value)
for key,value in original['fields'].items():p.op('ui_panel/'+key+'/string').text=value
for key,value in original['labels'].items():p.op('ui_panel/'+key).par.text=value
for key,value in original['dats'].items():p.op(key).text=value
scan_coverage._last_key=None
scan_coverage.refresh(op)
scan_workflow_ux.refresh(p)
assert live._routing_signature(op)==p.fetch('capture_signature')
result=json.dumps({'restored':True,'source_ids':p.op('ui_panel/source_ids/string').text,
 'views':p.op('ui_panel/views/string').text,'errors':list(p.errors(recurse=True))})
""" % json.dumps(original)
    data = td(script)
    (OUT/'native-restored.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps(data))


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'prepare': prepare()
    elif action == 'start': start(sys.argv[2], float(sys.argv[3]))
    elif action == 'observe': observe(sys.argv[2])
    elif action == 'restore': restore()
    else: raise ValueError(action)
