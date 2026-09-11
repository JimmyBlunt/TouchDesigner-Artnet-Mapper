"""Measure the real TD mapping path while replacing all transmitted colors with black."""
import json
import argparse
import time
from pathlib import Path
from audit_20260907_capture import td
from controller_black_benchmark_20260912 import get, ROOT

OUT = ROOT/'docs/controller-performance-20260912'
STOP = '''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
report=s.status();s.stop()
if hasattr(s,'_original_live_frames'):
    s._live_frames=s._original_live_frames;del s._original_live_frames
result=json.dumps({'sender':report,'worker_final':r.fetch('last_external_sender_status',{}),'off':not s.status()['enabled'],'errors':op('/project1').errors(recurse=True)})
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix',default='native-final')
    parser.add_argument('--cases',default='8:2,30:0.5')
    parser.add_argument('--duration',type=float,default=10)
    args = parser.parse_args()
    assert 1 <= args.duration <= 60
    print(td('''import json,importlib
from pixelblaze_mapper import external_packet_sender,sender_external_source
r=op('/project1/multi_controller_output');d=r.op('artnet_510_sender_callbacks');assert not d.module.status()['enabled']
importlib.reload(external_packet_sender);importlib.reload(sender_external_source)
d.text=d.text+chr(10)+'# Reload updated worker adapter'+chr(10)
result=json.dumps({'off':True})'''),flush=True)
    for item in args.cases.split(','):
        rate,gap = map(float,item.split(':'))
        assert rate.is_integer() and 1 <= rate <= 40 and 0 <= gap <= 5
        rate=int(rate);duration=args.duration;label=args.prefix+'-%sfps-%sms'%(rate,gap)
        path = OUT/(label+'.json')
        assert not path.exists()
        try:
            start=td('''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
assert not s.status()['enabled']
r.op('controller_config')[3,'rate']=%r;r.store('live_packet_gap_ms',{'BACK_PANEL_249':%r})
s._original_live_frames=s._live_frames
def black_frames(configs):
    return {name:tuple(bytes(len(frame)) for frame in frames) for name,frames in s._original_live_frames(configs).items()}
s._live_frames=black_frames
s.set_live();assert s.set_enabled(True)
result=json.dumps(s.status())'''%(str(rate),gap))
            time.sleep(2)
            before=get('/api/status');sample_start=time.perf_counter()
            time.sleep(duration)
            after=get('/api/status');sample_seconds=time.perf_counter()-sample_start
        finally:
            end=td(STOP)
        data=dict(before=before,after=after,start=start,end=end,duration=duration,sample_seconds=sample_seconds,black_only=True)
        path.write_text(json.dumps(data,indent=2))
        print(label,json.dumps({'delta':{k:after[k]-before[k] for k in ['packets','framesComplete','framesIncomplete','outputFrames','timeouts']},'sender':end}),flush=True)
