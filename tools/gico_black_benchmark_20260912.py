"""Black-only GICO comparison; ArtPoll is not a frame-reception acknowledgement."""
import json
from pathlib import Path
import socket
import sys
import time
from controller_black_benchmark_20260912 import ROOT, wait_until
from audit_20260907_capture import td
from pixelblaze_mapper.led_search import packet

TARGET=('10.0.0.244',6454)
POLL=b'Art-Net\0\0\x20\0\x0e\0\0'


def poll(sock):
    sock.sendto(POLL,TARGET)
    result=[];deadline=time.perf_counter()+1
    sock.settimeout(.15)
    while time.perf_counter()<deadline:
        try: data,origin=sock.recvfrom(4096)
        except socket.timeout: continue
        if origin[0]==TARGET[0] and data[:10]==b'Art-Net\0\0\x21':
            result.append(dict(short_name=data[26:44].decode(errors='replace').strip('\0 '),
                node_report=data[108:172].decode(errors='replace').strip('\0 '),
                good_output=list(data[182:186]),bind_index=data[211],hex=data.hex()))
    return result


if __name__=='__main__':
    td("import json;from pixelblaze_mapper import guided_scan_live as live;live.assert_outputs_off(op);result=json.dumps({'off':True})")
    out=ROOT/'docs/controller-performance-20260912/gico244-black-comparison.json'
    assert not out.exists()
    report=dict(target=TARGET,universe_range=[0,23],black_only=True,
                receiver_fps=None,receiver_fps_reason='No frame counter exposed by observed ArtPollReply or HTTP',cases=[])
    packets=[packet(u,bytes(510)) for u in range(24)]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(('10.0.0.125',6454))
        report['before']=poll(sock)
        assert report['before'] and all(r['short_name']=='GICO-6612pro' for r in report['before'])
        def send(gap):
            for index,data in enumerate(packets):
                if index and gap:wait_until(time.perf_counter()+gap/1000)
                sock.sendto(data,TARGET)
        try:
            for rate,gap in [(15,0),(30,0),(60,0),(30,.5)]:
                start=time.perf_counter();deadline=start;times=[];durations=[]
                while time.perf_counter()-start<10:
                    wait_until(deadline)
                    if time.perf_counter()-start>=10:break
                    tick=time.perf_counter();times.append(tick);send(gap)
                    durations.append((time.perf_counter()-tick)*1000)
                    deadline+=1/rate
                    if deadline<=time.perf_counter():deadline=time.perf_counter()+1/rate
                elapsed=time.perf_counter()-start
                intervals=[(b-a)*1000 for a,b in zip(times,times[1:])]
                row=dict(requested_fps=rate,gap_ms=gap,seconds=elapsed,sent_frames=len(times),
                    sent_packets=len(times)*24,sent_fps=len(times)/elapsed,
                    batch_ms_mean=sum(durations)/len(durations),batch_ms_max=max(durations),
                    interval_ms_max=max(intervals),poll_after=poll(sock),receiver_fps=None)
                report['cases'].append(row);out.write_text(json.dumps(report,indent=2))
                print(json.dumps({k:row[k] for k in ['requested_fps','gap_ms','sent_fps','batch_ms_mean','batch_ms_max','interval_ms_max','receiver_fps']}),flush=True)
        finally:
            for _ in range(4):send(1);time.sleep(.1)
            report['final_black_sent']=True
            report['after']=poll(sock);out.write_text(json.dumps(report,indent=2))
