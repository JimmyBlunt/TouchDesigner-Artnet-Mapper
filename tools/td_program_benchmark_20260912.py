"""Measure real TD packing/transport to loopback; restore all routing in finally."""
import argparse
import json
from pathlib import Path
import socket
import threading
import time
import zlib
from audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/performance-program-20260912/td'


def run(label, seconds=30, controller='BACK_PANEL_249', rate=30):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (label + '.json')
    if path.exists():
        raise ValueError('Refusing to overwrite benchmark evidence')
    baseline = td(r'''import json
from pixelblaze_mapper.routing_transaction import table_rows
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
assert not s.status()['enabled'], 'Stop current output before benchmarking'
assert not hasattr(s,'_original_live_frames')
result=json.dumps({'controllers':table_rows(r.op('controller_config')),
 'gap':r.fetch('live_packet_gap_ms',{}),'external':r.fetch('external_sender_settings',{}),
 'project':project.name,'rate':project.cookRate})''')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4*1024*1024)
    sock.bind(('127.0.0.1', 16454));sock.settimeout(.2)
    records=[];running=threading.Event();running.set()
    def receive():
        while running.is_set():
            try:
                raw,_=sock.recvfrom(2048)
                if len(raw)==528 and raw[:12]==b'Art-Net\0\0P\0\x0e':
                    records.append((time.perf_counter(),int.from_bytes(raw[14:16],'little'),zlib.crc32(raw[18:])))
            except socket.timeout: pass
    thread=threading.Thread(target=receive,daemon=True);thread.start()
    report={'baseline':baseline,'controller':controller,'requested_fps':rate,'loopback_only':True}
    try:
        report['start']=td(r'''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
t=r.op('controller_config')
name=%r
for row in range(1,t.numRows):
 t[row,'enabled']='1' if str(t[row,'name'])==name else '0'
 if str(t[row,'name'])==name:t[row,'rate']=%r;t[row,'local_interface']='127.0.0.1'
r.store('live_packet_gap_ms',{name:0.0})
settings=dict(r.fetch('external_sender_settings',{}));settings['enabled']=True;r.store('external_sender_settings',settings)
s.set_live();assert s.set_enabled(True,target_override='127.0.0.1',port_override=16454)
result=json.dumps(s.status())''' % (controller,str(rate)))
        time.sleep(3)
        begin=time.perf_counter();time.sleep(seconds);end=time.perf_counter()
        report['measured_seconds']=end-begin
        sampled=[row for row in records if begin<=row[0]<end]
        by_universe={}
        for stamp,universe,crc in sampled:
            by_universe.setdefault(universe,[]).append((stamp,crc))
        for universe,rows in by_universe.items():
            times=[r[0] for r in rows]
            intervals=sorted((b-a)*1000 for a,b in zip(times,times[1:]))
            by_universe[universe]={'packets':len(rows),'fps':len(rows)/(end-begin),
                'distinct_payloads':len(set(r[1] for r in rows)),
                'mean_interval_ms':sum(intervals)/len(intervals) if intervals else None,
                'p99_interval_ms':intervals[min(len(intervals)-1,int(len(intervals)*.99))] if intervals else None,
                'max_interval_ms':max(intervals) if intervals else None}
        report['received']=by_universe
    finally:
        try:
            report['end']=td(r'''import json
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
state=s.status();s.stop()
baseline=json.loads(%r);t=r.op('controller_config');t.clear()
for row in baseline['controllers']:t.appendRow(row)
r.store('live_packet_gap_ms',baseline['gap']);r.store('external_sender_settings',baseline['external'])
result=json.dumps({'sender':state,'worker_final':r.fetch('last_external_sender_status'),
 'off':not s.status()['enabled'],'errors':op('/project1').errors(recurse=True)})''' % json.dumps(baseline))
        finally:
            running.clear();thread.join(1);sock.close()
            path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'label':label,'received':report.get('received'), 'end':report.get('end')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--seconds',type=float,default=30)
    p.add_argument('--controller',default='BACK_PANEL_249');p.add_argument('--rate',type=int,default=30)
    a=p.parse_args();run(a.label,a.seconds,a.controller,a.rate)
