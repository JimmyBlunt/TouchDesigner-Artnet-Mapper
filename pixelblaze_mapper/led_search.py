"""Bounded manual LED-count probe; no acquisition/layout edits or auto-resume."""
import math
import socket
import threading
import time
from . import scan_output_guard
from .standalone_scan import routing

OWNER='/project1/guided_scan'
_thread=None
_stop=threading.Event()
_message='OFF — select a local LED index; no scan data is changed.'


def frames(settings,index,brightness):
    routing(settings)  # Full address/count/order validation before any socket.
    capacity=math.ceil(settings['count']/170)*170
    if type(index) is not int or not 0 <= index < capacity:
        raise ValueError('Index must be 0..%d within the selected universe range'%(capacity-1))
    if not math.isfinite(brightness) or not .01 <= brightness <= .10:
        raise ValueError('Test brightness must be 1–10 percent')
    level=round(255*brightness); order=settings['order']
    payloads=[bytearray(510) for _ in range(capacity//170)]
    for i,rgb in ((index-1,(0,level,0)),(index,(level,level,level)),(index+1,(level,0,0))):
        if 0<=i<capacity:
            values=dict(zip('RGB',rgb));offset=(i%170)*3
            payloads[i//170][offset:offset+3]=bytes(values[c] for c in order)
    return [(settings['universe']+i,bytes(p)) for i,p in enumerate(payloads)]


def packet(u,p):
    return b'Art-Net\0\x00\x50\x00\x0e\x00\x00'+bytes((u&255,u>>8))+b'\x01\xfe'+p


def stop():
    global _message
    _stop.set()
    if _thread and _thread.is_alive():
        _thread.join(1)
        if _thread.is_alive():raise RuntimeError('Waiting for test output to stop')
    _message='OFF — test range black; animation is not restarted.'


def _worker(settings,prepared,token):
    global _message
    sock=None;error=None
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(.2)
        sock.bind((settings['interface'],0))
        deadline=time.monotonic()+30
        while not _stop.is_set() and time.monotonic()<deadline:
            for u,p in prepared:sock.sendto(packet(u,p),(settings['target'],6454))
            _stop.wait(.1)
    except Exception as e:error=str(e)
    finally:
        if sock:
            try:
                for _ in range(3):
                    for u,_ in prepared:sock.sendto(packet(u,bytes(510)),(settings['target'],6454))
            except Exception as e:error=str(e)
            sock.close()
        scan_output_guard.release(token)
        _message=('ERROR: '+error) if error else 'OFF — 30-second test ended/stopped; black sent.'


def settings_from_ui(op):
    p=op(OWNER+'/new_capture_panel')
    s={k:p.op(k+'/string').text.strip() for k in ('name','target','interface','universe','count','rate','order')}
    for k in ('universe','count','rate'):s[k]=int(s[k])
    routing(s)
    return s


def act(op,action,delta=0):
    global _thread,_message
    try:
        if action=='stop':stop();return True
        settings=settings_from_ui(op)
        p=op(OWNER+'/led_search_panel')
        capacity=math.ceil(settings['count']/170)*170
        target='%s | WIRE U%d–U%d | local test indices 0–%d'%(settings['target'],settings['universe'],settings['universe']+capacity//170-1,capacity-1)
        p.op('target').par.text=target
        if action=='open':p.openViewer();return True
        index=int(p.op('index/string').text.strip())+delta
        from .guided_scan_live import assert_outputs_off,install_sender_guard,scan_brightness
        prepared=frames(settings,index,scan_brightness(op))
        assert_outputs_off(op)
        stop()  # Wait for previous black frame before switching the lit index.
        install_sender_guard(op)
        token=scan_output_guard.acquire()
        _stop.clear()
        _message='%s | GREEN %s | WHITE %d | RED %s | ON for 30s'%(target,index-1 if index else 'none',index,index+1 if index+1<capacity else 'outside range')
        p.op('index/string').text=str(index)
        try:
            _thread=threading.Thread(target=_worker,args=(settings,prepared,token),daemon=True)
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
    import pathlib
    import td
    scope=dict(ns,__name__='led_search_helpers')
    path=pathlib.Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_gico_port_config_ui.py')
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    node,panel,text,field,button,click=(scope[k] for k in ('_node','_panel','_text','_field','_button','_click'))
    owner=ns['op'](OWNER); fresh=owner.op('new_capture_panel')
    fresh.op('btn_stage').par.w=380
    b=button(fresh,'btn_led_search','LED SEARCH / FIND LAST LED',420,20,380)
    command="__import__('pixelblaze_mapper.led_search',fromlist=['act']).act(op, %r%s)"
    click(owner,'click_led_search_open',b,command%('open',''))
    p=panel(node(owner,ns.get('containerCOMP',td.containerCOMP),'led_search_panel'),0,0,900,360,10)
    text(p,'title','FIND LAST LED | LOCAL INDEX, NOT GLOBAL SOURCE',20,305,860,40,19)
    text(p,'target','Open from NEW CAPTURE after entering IP / universe / count.',20,260,860,40,12)
    text(p,'legend','Previous GREEN  |  Selected WHITE  |  Next RED. Last visible index + 1 = LED count.',20,215,860,35,13)
    text(p,'input_label','Selected LED (0-based)',20,165,220,35,12)
    old=p.op('index/string');field(p,'index',old.text if old else '202',245,165,130)
    for name,label,x,w,action,delta in [('show','SHOW 30s',390,165,'show',0),('stop','STOP / BLACK',575,305,'stop',0),
        ('minus10','-10',20,190,'show',-10),('minus1','-1',225,190,'show',-1),('plus1','+1',430,190,'show',1),('plus10','+10',635,245,'show',10)]:
        b=button(p,name,label,x,165 if name in ('show','stop') else 110,w)
        click(owner,'click_led_search_'+name,b,command%(action,', '+str(delta)))
    label=text(p,'status','',20,20,860,75,12)
    label.par.text.expr="__import__('pixelblaze_mapper.led_search',fromlist=['status']).status()"
    callback=node(owner,ns.get('executeDAT',td.executeDAT),'led_search_exit')
    callback.text="def onExit():\n    from pixelblaze_mapper.led_search import stop\n    stop()\n"
    callback.par.exit=True;callback.par.active=True
    return {'panel':p.path,'output_started':False}
