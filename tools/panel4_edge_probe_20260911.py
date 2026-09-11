"""User-requested bounded visual probe; never changes scan/layout data."""
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pixelblaze_mapper import scan_output_guard
from pixelblaze_mapper.led_search import packet
from pixelblaze_mapper.scan_routing import create_snapshot
from pixelblaze_mapper.standalone_scan import routing

INDICES = (0, 1, 2, 807, 808, 809)
_thread = None
_stop = threading.Event()
_status = {}
_folder = None
PYTHON = Path('C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe')


def prepared_frames(settings):
    assert settings['target']=='10.0.0.249' and settings['universe']==133 and settings['count']==810
    assert settings['frame_start_universe']==120 and settings['frame_universe_count']==18
    snapshot=create_snapshot(routing(settings),tuple(range(810)),brightness_cap=.05)
    black=snapshot.packet_descriptors()
    frames={i:snapshot.packet_descriptors(i,on=True) for i in INDICES}
    for index,items in frames.items():
        assert len(items)==18
        lit=[f for f in items if any(f.payload)]
        assert len(lit)==1 and lit[0].wire_universe==133+index//170
        assert {j//3 for j,v in enumerate(lit[0].payload) if v}=={index%170}
    return black,frames


def stop():
    _stop.set()
    if _folder is not None:
        (_folder/'stop.request').touch()


def status():
    current = dict(_status)
    if _folder is not None:
        try:
            current.update(json.loads((_folder/'status.json').read_text(encoding='utf-8')))
        except (OSError, ValueError):
            pass
    return dict(current, running=bool(_thread and _thread.is_alive()))


def _run_output(black,frames,folder):
    global _status
    sock=None
    report={'indices':list(INDICES),'rounds':2,'brightness_percent':5,'on_seconds':2,
            'black_seconds':1,'packet_gap_ms':1,'events':[],'packets_sent':0,'errors':[]}
    started=time.monotonic()
    def send(items,cleanup=False):
        for n,f in enumerate(items):
            if not cleanup and ((folder/'stop.request').exists() or time.monotonic()-started>44):
                raise InterruptedError('Test stopped or time limit reached')
            if n:time.sleep(.001)
            sock.sendto(packet(f.wire_universe,f.payload),(f.target_address,f.port))
            report['packets_sent']+=1
    def hold(items,seconds,label):
        global _status
        report['events'].append({'elapsed':round(time.monotonic()-started,3),'phase':label})
        _status={'phase':label,'elapsed':round(time.monotonic()-started,1)}
        (folder/'status.json').write_text(json.dumps(_status),encoding='utf-8')
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            send(items)
            _stop.wait(min(.08,max(0,end-time.monotonic())))
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(.15)
        sock.bind((black[0].local_interface,0))
        hold(black,2,'initial black')
        for run in range(1,3):
            for index in INDICES:
                hold(frames[index],2,'round %d LED %d'%(run,index))
                hold(black,1,'black after LED %d'%index)
    except Exception as error:
        report['errors'].append(str(error))
    finally:
        black_sent=False
        if sock:
            try:
                for _ in range(3):send(black,cleanup=True)
                black_sent=True
            except Exception as error:report['errors'].append('blackout: '+str(error))
            sock.close()
        report.update(elapsed_seconds=round(time.monotonic()-started,3),blackout_sent=black_sent,
                      optical_blackout_confirmed=False)
        _status={'phase':'finished','errors':report['errors'],'blackout_sent':black_sent}
        (folder/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (folder/'status.json').write_text(json.dumps(_status),encoding='utf-8')


def _supervise(process,token,folder):
    """Only supervise here: timed network output must run outside TD's interpreter."""
    global _status
    try:
        process.wait(timeout=60)
        report=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        _status={'phase':'finished','errors':report['errors'],
                 'blackout_sent':report['blackout_sent'],'exit_code':process.returncode}
    except Exception as error:
        (folder/'stop.request').touch()
        # Give the worker's finally block time to transmit black before releasing ownership.
        try:
            process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        _status={'phase':'failed','errors':[str(error)],'blackout_sent':False}
    finally:
        scan_output_guard.release(token)
        (folder/'supervisor.json').write_text(json.dumps(_status,indent=2),encoding='utf-8')


def start(op,folder):
    global _thread,_status,_folder
    from pixelblaze_mapper import guided_scan_live as live
    assert _thread is None or not _thread.is_alive()
    assert live._capture is None or live._capture.process.poll() is not None
    assert live._probe is None or live._probe.process.poll() is not None
    live.assert_outputs_off(op)
    with urllib.request.urlopen('http://10.0.0.249/api/test-pattern',timeout=4) as response:
        test=json.load(response)
    assert not test['active'] and not test['blackout'], 'Stop internal controller test first'
    settings=op('/project1/guided_scan').fetch('standalone_capture')
    black,frames=prepared_frames(settings)
    assert PYTHON.is_file(), 'Standalone scan Python is missing'
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    (folder/'request.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
    live.install_sender_guard(op)
    token=scan_output_guard.acquire();_stop.clear();_status={'phase':'starting'}
    _folder=folder
    process=None
    try:
        with (folder/'worker.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([str(PYTHON),str(Path(__file__).resolve()),str(folder)],
                cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        _thread=threading.Thread(target=_supervise,args=(process,token,folder),daemon=True)
        _thread.start()
    except Exception:
        if process is not None:
            (folder/'stop.request').touch()
            process.wait(timeout=15)
        scan_output_guard.release(token)
        raise
    return status()


if __name__ == '__main__':
    folder=Path(sys.argv[1]).resolve()
    settings=json.loads((folder/'request.json').read_text(encoding='utf-8'))
    black,frames=prepared_frames(settings)
    _run_output(black,frames,folder)
