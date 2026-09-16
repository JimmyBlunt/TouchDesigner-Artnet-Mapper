"""Bounded manual LED-count probe; no acquisition/layout edits or auto-resume."""
import math
import json
import os
import socket
import subprocess
import threading
import time
from . import scan_output_guard
from .standalone_scan import routing

OWNER='/project1/guided_scan'
_thread=None
_stop=threading.Event()
_message='OFF — select a local LED index; no scan data is changed.'
_chase_state=None


def frames(settings,index,brightness, *, single=False):
    routing(settings)  # Full address/count/order validation before any socket.
    capacity=math.ceil(settings['count']/170)*170
    if type(index) is not int or not 0 <= index < capacity:
        raise ValueError('Index must be 0..%d within the selected universe range'%(capacity-1))
    if not math.isfinite(brightness) or not .01 <= brightness <= .10:
        raise ValueError('Test brightness must be 1–10 percent')
    level=round(255*brightness); order=settings['order']
    payloads=[bytearray(510) for _ in range(capacity//170)]
    for i,rgb in ((index-1,(0,level,0)),(index,(level,level,level)),(index+1,(level,0,0))):
        if single and i != index:
            continue
        if 0<=i<capacity:
            values=dict(zip('RGB',rgb));offset=(i%170)*3
            payloads[i//170][offset:offset+3]=bytes(values[c] for c in order)
    panel = {settings['universe']+i:bytes(p) for i,p in enumerate(payloads)}
    first = settings.get('frame_start_universe', settings['universe'])
    count = settings.get('frame_universe_count', len(payloads))
    return [(u,panel.get(u,bytes(510))) for u in range(first,first+count)]


def packet(u,p):
    return b'Art-Net\0\x00\x50\x00\x0e\x00\x00'+bytes((u&255,u>>8))+b'\x01\xfe'+p


def stop():
    global _message
    _stop.set()
    if _thread and _thread.is_alive():
        _thread.join(1)
        if _thread.is_alive():raise RuntimeError('Waiting for test output to stop')
    if _chase_state and _chase_state.get('index') is not None:
        if _chase_state.get('state') in ('stopped','limit_reached','error'):
            return
        _message='STOP | LED %d (Index %d) | Nummer gemerkt; Schwarz nicht bestaetigt.'%(_chase_state['index']+1,_chase_state['index'])
    else:
        _message='OFF — test range black; animation is not restarted.'


def _chase_worker(settings,start,brightness,step,emit):
    """One white LED, complete frames, bounded at the configured port count."""
    prepared=frames(settings,start,brightness,single=True)
    if not 0 <= start < settings['count'] or not .5 <= step <= 10:
        raise ValueError('Invalid chase start or step duration')
    sock=None;last=None;error=None
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(.2)
        sock.bind((settings['interface'],0))
        for index in range(start,settings['count']):
            if _stop.is_set():break
            prepared=frames(settings,index,brightness,single=True)
            deadline=None
            while not _stop.is_set():
                for u,p in prepared:
                    sock.sendto(packet(u,p),(settings['target'],6454));time.sleep(.001)
                if deadline is None:
                    last=index
                    emit({'state':'running','index':index,'led_number':index+1,'step_seconds':step})
                    deadline=time.monotonic()+step
                if time.monotonic()>=deadline:break
                _stop.wait(min(.08,max(0,deadline-time.monotonic())))
    except Exception as e:error=str(e)
    finally:
        if sock:
            try:
                for _ in range(3):
                    for u,p in prepared:
                        sock.sendto(packet(u,bytes(510)),(settings['target'],6454));time.sleep(.001)
            except Exception as e:error=str(e)
            sock.close()
        emit({'state':'error' if error else 'stopped' if _stop.is_set() else 'limit_reached',
              'index':last,'led_number':last+1 if last is not None else None,'error':error,
              'black_sent':error is None,'count_confirmed':False})


def _chase_process(settings,start,brightness,token):
    global _message,_chase_state
    child=None;reader=None
    try:
        from .camera_probe import INTERPRETER, REPOSITORY
        child=subprocess.Popen([str(INTERPRETER),'-B','-u','-m','pixelblaze_mapper.led_search'],
            cwd=str(REPOSITORY),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        def read_progress():
            global _message,_chase_state
            for line in child.stdout:
                item=json.loads(line);_chase_state=item
                number=item.get('led_number')
                if item['state']=='running':
                    _message='LAUFLICHT | LED %s (Index %s) | 2 Sekunden pro LED | STOP bei der letzten LED'%(number,item['index'])
                else:
                    _message='%s | LED %s (Index %s) | %s'%(item['state'].upper(),number,item['index'],item.get('error') or 'Nummer gemerkt; Schwarz gesendet')
                    from pathlib import Path
                    folder=REPOSITORY/'docs'/'panel6-teensy-20260914'
                    folder.mkdir(parents=True,exist_ok=True)
                    (folder/'chase-last.json').write_text(json.dumps(dict(item,settings=settings),indent=2),encoding='utf-8')
        reader=threading.Thread(target=read_progress,daemon=True);reader.start()
        child.stdin.write(json.dumps({'settings':settings,'chase':True,'start':start,'brightness':brightness,'step':2.0})+'\n');child.stdin.flush()
        while child.poll() is None and not _stop.wait(.02):pass
        if child.poll() is None:
            child.stdin.write('STOP\n');child.stdin.flush()
        child.wait(timeout=2);reader.join(1)
        if child.returncode:_message='ERROR: '+child.stderr.read().strip()
    except Exception as e:_message='ERROR: '+str(e)
    finally:
        if child is not None and child.poll() is None:
            child.kill();child.wait();_message+='; blackout unconfirmed'
        scan_output_guard.release(token)


def _worker(settings,prepared,token):
    global _message
    sock=None;error=None
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(.2)
        sock.bind((settings['interface'],0))
        deadline=time.monotonic()+30
        while not _stop.is_set() and time.monotonic()<deadline:
            for u,p in prepared:
                sock.sendto(packet(u,p),(settings['target'],6454))
                time.sleep(.001)
            _stop.wait(.1)
    except Exception as e:error=str(e)
    finally:
        if sock:
            try:
                for _ in range(3):
                    for u,_ in prepared:
                        sock.sendto(packet(u,bytes(510)),(settings['target'],6454))
                        time.sleep(.001)
            except Exception as e:error=str(e)
            sock.close()
        scan_output_guard.release(token)
        _message=('ERROR: '+error) if error else 'OFF — 30-second test ended/stopped; black sent.'


def legacy_settings_from_ui(op):
    p=op(OWNER+'/new_capture_panel')
    s={k:p.op(k+'/string').text.strip() for k in ('name','target','interface','universe','count','rate','order')}
    for k in ('universe','count','rate'):s[k]=int(s[k])
    frame = {k:p.op(k+'/string').text.strip() if p.op(k+'/string') else ''
             for k in ('frame_start_universe','frame_universe_count')}
    if any(frame.values()):
        if not all(frame.values()):
            raise ValueError('Enter both controller frame start and universe count')
        s.update({k:int(v) for k,v in frame.items()})
    routing(s)
    return s


def settings_from_ui(op):
    owner = op(OWNER)
    if owner.op('led_search_panel/controller') is not None:
        from .led_search_ui import selected_settings
        return selected_settings(op)
    return legacy_settings_from_ui(op)


def _process_worker(settings,prepared,token):
    """Keep complete controller frames independent of TouchDesigner's Python GIL."""
    global _message
    child=None
    try:
        from .camera_probe import INTERPRETER, REPOSITORY
        child=subprocess.Popen([str(INTERPRETER),'-B','-u','-m','pixelblaze_mapper.led_search'],
            cwd=str(REPOSITORY),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        child.stdin.write(json.dumps({'settings':settings,'frames':[(u,list(p)) for u,p in prepared]})+'\n')
        child.stdin.flush()
        while child.poll() is None and not _stop.wait(.03):
            pass
        if child.poll() is None:
            child.stdin.write('STOP\n');child.stdin.flush()
        output,error=child.communicate(timeout=2)
        _message=output.strip() if child.returncode==0 else 'ERROR: '+error.strip()
    except Exception as e:
        _message='ERROR: '+str(e)
    finally:
        if child is not None and child.poll() is None:
            child.kill();child.wait()
            _message+='; worker forced to stop, blackout unconfirmed'
        scan_output_guard.release(token)


def act(op,action,delta=0):
    global _thread,_message,_chase_state
    try:
        if action=='stop':stop();return True
        p=op(OWNER+'/led_search_panel')
        if action=='open' and p.op('controller') is not None:
            from .led_search_ui import action as ui_action, render
            if not op(OWNER).fetch('led_search_device',None):
                ui_action(op,'load')
            render(op)
            p.openViewer()
            return True
        if action not in ('open','show','chase'):
            raise ValueError('Unknown LED search action')
        settings=settings_from_ui(op)
        capacity=math.ceil(settings['count']/170)*170
        limit=settings['count'] if p.op('controller') is not None else capacity
        target='%s | WIRE U%d–U%d | local test indices 0–%d'%(settings['target'],settings['universe'],settings['universe']+capacity//170-1,limit-1)
        if 'frame_start_universe' in settings:
            target+=' | SEND U%d–U%d; other ports BLACK'%(settings['frame_start_universe'],settings['frame_start_universe']+settings['frame_universe_count']-1)
        p.op('target').par.text=target
        if action=='open':p.openViewer();return True
        from .led_search_ui import field_value
        index=int(field_value(p.op('index')))+delta
        if p.op('controller') is not None:
            if not 0 <= index < settings['count']:
                raise ValueError('LED-Index fuer diesen Ausgang: 0-%d' % (settings['count']-1))
            from .led_search_ui import render
            render(op)
        from .guided_scan_live import assert_outputs_off,install_sender_guard,scan_brightness
        prepared=frames(settings,index,scan_brightness(op))
        assert_outputs_off(op)
        stop()  # Wait for previous black frame before switching the lit index.
        _chase_state=None
        install_sender_guard(op)
        token=scan_output_guard.acquire()
        _stop.clear()
        _message='%s | GREEN %s | WHITE %d | RED %s | ON for 30s'%(target,index-1 if index else 'none',index,index+1 if index+1<capacity else 'outside range')
        p.op('index/string').text=str(index)
        try:
            worker=_chase_process if action=='chase' else _process_worker if 'frame_start_universe' in settings else _worker
            args=(settings,index,scan_brightness(op),token) if action=='chase' else (settings,prepared,token)
            _thread=threading.Thread(target=worker,args=args,daemon=True)
            _thread.start()
        except Exception:
            scan_output_guard.release(token);raise
        return True
    except Exception as e:
        _message='BLOCKED: '+str(e)
        return False


def status():return _message


def install(ns):
    """UI only, using the project's existing widgets. Never starts output."""
    from .led_search_ui import install as install_ui
    return install_ui(ns)


if __name__=='__main__':
    import sys
    request=json.loads(sys.stdin.readline())
    def stop_on_input():
        sys.stdin.readline()  # STOP or parent EOF both terminate the bounded test.
        _stop.set()
    threading.Thread(target=stop_on_input,daemon=True).start()
    if request.get('chase'):
        _chase_worker(request['settings'],request['start'],request['brightness'],request['step'],
                      lambda item:print(json.dumps(item),flush=True))
    else:
        _worker(request['settings'],[(u,bytes(p)) for u,p in request['frames']],scan_output_guard.acquire())
        print(_message)
