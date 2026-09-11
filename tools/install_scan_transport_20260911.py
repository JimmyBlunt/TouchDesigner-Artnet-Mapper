"""Install the measured Panel 3 transport setting while capture is stopped."""
import json
from pathlib import Path
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/panel3-preparation-20260911/transport-comparison'

SCRIPT = r'''
import ast, importlib, json
from pathlib import Path
from pixelblaze_mapper import guided_scan_live as live, scan_capture, scan_workflow_ux
p=op('/project1/guided_scan')
assert live._capture is None or live._capture.process.poll() is not None
assert live._probe is None or live._probe.process.poll() is not None
live.assert_outputs_off(op)
original=json.loads(Path(%r).read_text(encoding='utf-8'))
assert p.op('ui_panel/views/string').text == original['fields']['views']
assert p.op('ui_panel/source_ids/string').text.strip() == '0-879'
importlib.reload(scan_capture)
importlib.reload(scan_workflow_ux)
source=Path(live.__file__)
tree=ast.parse(source.read_text(encoding='utf-8'))
names={'scan_packet_gap','_routing_signature','prepare'}
nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
assert len(nodes)==len(names)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),live.__dict__)
helper=source.parent/'build_gico_port_config_ui.py'
scope=dict(globals(),__name__='scan_transport_helpers',__file__=str(helper))
exec(compile(helper.read_text(encoding='utf-8'),str(helper),'exec'),scope,scope)
canvas=p.op('ui_panel')
scope['_text'](canvas,'packet_gap_label','PACKET GAP (ms, 0-2)',460,219,300,26,11)
scope['_field'](canvas,'packet_gap','1',460,183,300)
scope['_text'](canvas,'packet_gap_help','Small gaps can improve controller reception. Check scan plan after changes.',780,183,360,62,11)
p.store('capture_packet_gap_ms',1.0)
live.prepare(op)
scan_workflow_ux.refresh(p)
plan=p.fetch('capture_plan')
assert plan['packet_gap_ms']==1.0
assert len(plan['identity'])==880
assert p.fetch('capture_signature')==live._routing_signature(op)
assert p.op('ui_panel/views/string').text==original['fields']['views']
assert p.op('ui_panel/workspace/string').text==original['fields']['workspace']
assert not op('/project1').errors(recurse=True)
live.assert_outputs_off(op)
result=json.dumps({'plan':plan,'views':p.op('ui_panel/views/string').text,
 'source_ids':p.op('ui_panel/source_ids/string').text,
 'routing_summary':p.op('ui_panel/routing_summary').par.text.eval(),
 'errors':list(op('/project1').errors(recurse=True)), 'output_off':True,
 'capture_running':False,'probe_running':False})
'''

if __name__ == '__main__':
    data=td(SCRIPT % str(OUT/'native-original.json'))
    (OUT/'native-gap-ready.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in data.items() if key!='plan'},indent=2))
