"""Temporary black-only native producer comparison; restore controller rows."""
import json
import time
from audit_20260907_capture import td
from controller_black_benchmark_20260912 import ROOT

if __name__=='__main__':
    baseline=td('''import json,importlib
from pixelblaze_mapper import sender_external_source
from pixelblaze_mapper.routing_transaction import table_rows
r=op('/project1/multi_controller_output');d=r.op('artnet_510_sender_callbacks')
assert not d.module.status()['enabled']
importlib.reload(sender_external_source);d.text=sender_external_source.install_source(d.text)
result=json.dumps({'controllers':table_rows(r.op('controller_config')),'gap':r.fetch('live_packet_gap_ms',{})})''')
    report={'baseline':baseline,'target':'10.0.0.244','black_only':True,'receiver_fps':None}
    try:
        report['start']=td('''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
t=r.op('controller_config')
for row in range(1,t.numRows):t[row,'enabled']='1' if str(t[row,'name'])=='WS2812_NODE' else '0'
t[1,'rate']='30';r.store('live_packet_gap_ms',{'WS2812_NODE':0})
s._original_live_frames=s._live_frames
def black_frames(configs):
    return {name:tuple(bytes(len(frame)) for frame in frames) for name,frames in s._original_live_frames(configs).items()}
s._live_frames=black_frames;s.set_live();assert s.set_enabled(True)
result=json.dumps(s.status())''')
        time.sleep(20)
    finally:
        report['end']=td('''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
state=s.status();s.stop()
if hasattr(s,'_original_live_frames'):s._live_frames=s._original_live_frames;del s._original_live_frames
baseline=json.loads(%r);t=r.op('controller_config');t.clear()
for row in baseline['controllers']:t.appendRow(row)
r.store('live_packet_gap_ms',baseline['gap'])
result=json.dumps({'sender':state,'worker_final':r.fetch('last_external_sender_status'),'off':not s.status()['enabled'],'errors':op('/project1').errors(recurse=True)})'''%json.dumps(baseline))
        (ROOT/'docs/controller-performance-20260912/gico244-native-comparison.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report['end'],indent=2))
