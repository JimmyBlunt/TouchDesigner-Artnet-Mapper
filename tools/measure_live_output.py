"""Bounded read-only TD / controller-253 frame-rate measurement."""
import json
import sys
import time
import urllib.request
from pathlib import Path
from audit_20260907_capture import td

SCRIPT = """import json,time
s=op('/project1/multi_controller_output/artnet_510_sender_callbacks').module
result=json.dumps({'time':time.perf_counter(),'frame':int(absTime.frame),'sender':s.status()},default=str)
"""

def receiver():
    with urllib.request.urlopen('http://10.0.0.253/api/status', timeout=4) as response:
        return json.load(response)

if __name__ == '__main__':
    label = sys.argv[1]
    if not label.replace('-', '').isalnum():
        raise ValueError(label)
    # TD's remote-exec/UI activity can disturb the render loop. Keep it
    # outside the receiver measurement, including a settling interval.
    td_before = td(SCRIPT)
    time.sleep(10)
    first = dict(receiver=receiver(), time=time.perf_counter())
    time.sleep(15)
    last = dict(receiver=receiver(), time=time.perf_counter())
    td_after = td(SCRIPT)
    elapsed = last['time'] - first['time']
    keys = ['artnet_complete', 'artnet_incomplete', 'artnet_stale', 'udp_queue_drops',
            'artnet_rejected', 'artnet_overwritten', 'frames_submitted']
    delta = {k: last['receiver'][k]-first['receiver'][k] for k in keys}
    summary = dict(elapsed=elapsed, receiver_fps=delta['artnet_complete']/elapsed,
                   submitted_fps=delta['frames_submitted']/elapsed, delta=delta)
    output = Path(__file__).resolve().parents[1]/'docs/release-v1.0.0/qa'/('performance-'+label+'.json')
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(dict(summary=summary, first=first, last=last,
        td_before=td_before, td_after=td_after, td_calls_during_interval=0), indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
