"""Black-only baseline of USB-identified original firmware at its actual .251 IP."""
import argparse
import copy
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.request
from benchmark import packet, send_stream

TARGET = '10.0.0.251'
EXPECTED_MAC = 'E8-68-E7-0D-38-A4'
ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'docs/performance-program-20260912/esp/original-baseline.json'

def api(path, value=None):
    request = urllib.request.Request('http://' + TARGET + path,
        data=None if value is None else json.dumps(value).encode(),
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.load(response)

def main(virtual=False,gap_ms=0):
    global REPORT
    if virtual: REPORT=REPORT.with_name("original-baseline-virtual1755.json")
    if gap_ms: REPORT=REPORT.with_name(REPORT.stem+'-gap'+str(gap_ms)+'.json')
    ws_count,apa_count=(731,1024) if virtual else (256,512)
    apa_start=(ws_count+169)//170
    used_universes=apa_start+(apa_count+169)//170
    if REPORT.exists():
        raise RuntimeError('Do not overwrite an existing baseline')
    original = api('/api/config')
    expected = json.loads((REPORT.parent/'config-before-redacted.json').read_text())
    if original != expected:
        raise RuntimeError('Original controller config does not match verified USB backup')
    neighbor = subprocess.check_output(['powershell','-NoProfile','-Command',
        "Get-NetNeighbor -IPAddress 10.0.0.251 | Select-Object -ExpandProperty LinkLayerAddress"],
        timeout=10).decode(errors='replace')
    if EXPECTED_MAC not in neighbor.upper():
        raise RuntimeError('IP/MAC does not match the USB-identified ESP')
    if api('/api/test-pattern').get('active'):
        raise RuntimeError('An original firmware test pattern is active')
    report = {'target':TARGET, 'mac':EXPECTED_MAC, 'pattern':'black', 'original_config':original,
              'physical_counts_user_approximate':[256,512], 'virtual_load_test':virtual, 'optical_fps_measured':False, 'cases':[]}
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(('10.0.0.125',0))
        def black(universes):
            for seq in range(1,5):
                for u in universes: sock.sendto(packet(u,seq), (TARGET,6454))
                time.sleep(.05)
        try:
            for ceiling,rate in ([(60,30)] if gap_ms else ([(30,30),(60,30)] if virtual else [(30,5),(30,15),(30,30),(60,30)])):
                value = copy.deepcopy(original)
                value.update(pixelCount=ws_count+apa_count,universeCount=used_universes,startUniverse=0,targetFps=ceiling)
                value['outputs'][0].update(pixelCount=ws_count,startPixel=0,startUniverse=0,targetFps=ceiling)
                value['outputs'][1].update(pixelCount=apa_count,startPixel=ws_count,startUniverse=apa_start,targetFps=ceiling)
                api('/api/config',value)
                if api('/api/config') != value: raise RuntimeError('Temporary config readback mismatch')
                time.sleep(.4)
                before=api('/api/status')
                sent=send_stream(sock,TARGET,list(range(used_universes)),20,rate,gap_ms=gap_ms)
                time.sleep(.15)
                after=api('/api/status')
                delta={k:(after[k]-before[k])&0xffffffff for k in
                    ('packets','framesComplete','framesIncomplete','outputFrames','timeouts','droppedPackets','sequenceErrors')}
                case={'requested_fps':rate,'output_ceiling_fps':ceiling,**sent,'delta':delta,
                      'before':before,'after':after,'config':value,
                      'original_reported_output_fps':delta['outputFrames']/sent['send_elapsed_seconds']}
                report['cases'].append(case)
                REPORT.write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps({k:case[k] for k in ('requested_fps','output_ceiling_fps','sender_fps','original_reported_output_fps','delta')}),flush=True)
                black(range(used_universes));time.sleep(1.1)
        finally:
            black(range(used_universes))
            api('/api/config',original)
            black(range(11))
            report['restored_exactly']=api('/api/config')==original
            report['final_black_sent']=True
            REPORT.write_text(json.dumps(report,indent=2)+'\n')
            if not report['restored_exactly']: raise RuntimeError('Original config restoration failed')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--virtual',action='store_true',help='Use731WS+1024APA transmitted pixels; physical panels unchanged')
    parser.add_argument('--gap-ms',type=float,default=0,choices=[0,0.5,1])
    args=parser.parse_args()
    main(args.virtual,args.gap_ms)
