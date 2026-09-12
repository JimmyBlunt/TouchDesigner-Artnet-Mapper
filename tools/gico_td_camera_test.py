"""Start the reversible native TD optical test; loopback mode verifies transport."""
import argparse
import json
from pathlib import Path
import socket
import threading
import time
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install_td_performance_program_20260912 import td


def run(folder, loopback=False):
    folder = folder.resolve()
    if folder.exists(): raise ValueError('Use a new output folder')
    endpoint = ('127.0.0.1', 16455) if loopback else ('10.0.0.244', 6454)
    packets = []; stop = threading.Event(); sock = thread = None
    if loopback:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4*1024*1024)
        sock.bind(endpoint); sock.settimeout(.1)
        def receive():
            while not stop.is_set():
                try: packets.append(sock.recvfrom(2048)[0])
                except socket.timeout: pass
        thread = threading.Thread(target=receive, daemon=True); thread.start()
    try:
        result = td('''import json
from pixelblaze_mapper import gico_td_optical as g
report=g.prepare(op,ui,scriptCHOP,textDAT,%r,target=%r,port=%r,short=%r)
g.SESSION.start()
result=json.dumps({'started':True,'preflight_patterns':report['preflight_patterns_passed'],'transport_fps':30})
''' % (str(folder), endpoint[0], endpoint[1], loopback))
        print(json.dumps(result), flush=True)
        deadline = time.monotonic()+(45 if loopback else 250)
        while not (folder/'run.json').exists():
            if time.monotonic() > deadline: raise RuntimeError('Native test exceeded its wall-clock limit')
            time.sleep(.2)
        report = json.loads((folder/'run.json').read_text())
        if not report.get('complete'): raise RuntimeError('Native test failed: '+str(report.get('error')))
        print(json.dumps({'complete':report['complete'],'worker':report['worker_final'],
                          'restored':report['restored']}), flush=True)
    finally:
        try:
            td("import json\nfrom pixelblaze_mapper import gico_td_optical as g\ng.cancel()\nresult=json.dumps({'cancel_checked':True})")
        finally:
            stop.set()
            if thread: thread.join(1)
            if sock: sock.close()
    if loopback:
        from pixelblaze_mapper import gico_camera_benchmark as b
        allowed = b.payloads([1]*21)
        invalid = []; universes = set(); nonblack = 0
        for raw in packets:
            if len(raw) != 528 or raw[:14] != b.packet(0,bytes(510))[:14]:
                invalid.append('header'); continue
            u = int.from_bytes(raw[14:16], 'little'); universes.add(u)
            if u >= 24 or raw[16:18] != b'\x01\xfe': invalid.append('universe/length'); continue
            if any(v not in (0,16) or (v and allowed[u][i] != 16) for i,v in enumerate(raw[18:])):
                invalid.append('unexpected lit pixel or brightness')
            nonblack += any(raw[18:])
        evidence = {'packets':len(packets),'universes':sorted(universes),
                    'nonblack_packets':nonblack,'invalid':invalid,
                    'native_restored':report['restored'], 'worker':report['worker_final']}
        (folder/'loopback-validation.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        assert not invalid and universes == set(range(24)) and nonblack > 0
        print(json.dumps({'loopback_verified':True,'packets':len(packets)}),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','loopback'])
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run(a.output,a.action=='loopback')
