"""Black-only raw UDP error/re-arm regression on the identified .151 test node."""
import argparse
import json
from pathlib import Path
import socket
import time
from benchmark import api,packet,TARGET


def run(output):
    if output.exists():raise RuntimeError('Evidence already exists')
    report={}
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(('10.0.0.125',0))
        status=api('/api/status');config=api('/api/config')
        assert status['firmware']=='experimental-esp-artnet-30fps-v1'
        assert status['receiveMode']=='raw-udp-queue64' and config['experimental']
        report.update(identity=status,config=config)
        universes=[o['universe']+i for o in config['outputs'] for i in range((o['count']+169)//170)]
        assert len(universes) in (6,12) and len(set(universes))==len(universes)
        try:
            api('/api/arm?enabled=false',post=True);time.sleep(.1)
            before=api('/api/status')
            for payload in (b'bad',bytes(600)):
                for _ in range(8):
                    sock.sendto(payload,(TARGET,6454));time.sleep(.002)
            time.sleep(.15);after=api('/api/status')
            report['invalid_packets']={'before':before,'after':after}
            assert after['malformedPackets']-before['malformedPackets']==8
            assert after['rawUdpOversizePackets']-before['rawUdpOversizePackets']==8
            assert after['outputFrames']==before['outputFrames']
            # Old candidate must not complete when only its remaining half is
            # supplied after ARM. All valid test payloads are black.
            half=len(universes)//2
            for universe in universes[:half]:sock.sendto(packet(universe,173),(TARGET,6454))
            time.sleep(.05)
            armed=api('/api/arm?enabled=true',post=True)
            for universe in universes[half:]:sock.sendto(packet(universe,173),(TARGET,6454))
            time.sleep(.08);partial=api('/api/status')
            report['rearm_partial']={'armed':armed,'after':partial}
            assert partial['completedFrames']==armed['completedFrames']
            assert partial['outputFrames']==armed['outputFrames']
            for universe in universes:sock.sendto(packet(universe,174),(TARGET,6454))
            time.sleep(.15);fresh=api('/api/status')
            report['fresh_frame']=fresh
            assert fresh['completedFrames']==partial['completedFrames']+1
            assert fresh['outputFrames']==partial['outputFrames']+1
            assert fresh['rawUdpQueueDrops']==before['rawUdpQueueDrops']
            report['passed']=True
        except BaseException as error:
            report['error']=repr(error)
            raise
        finally:
            try:
                api('/api/arm?enabled=false',post=True);time.sleep(.1)
                report['final']=api('/api/status')
                assert not report['final']['armed']
            finally:output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'final_armed':report['final']['armed']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.run:parser.error('Explicit --run required')
    run(args.output)
