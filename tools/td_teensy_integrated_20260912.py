"""Reversible real TD -> identified, unwired Teensy -> seven DMA ports test."""
import argparse
import json
import threading
import time
import serial
from serial.tools import list_ports
from install_td_performance_program_20260912 import td,OUT


def run(label,seconds,rate):
    path=OUT/(label+'.json')
    if path.exists() or not 10<=seconds<=180 or not 1<=rate<=60:raise ValueError('Invalid/new evidence required')
    ports=[p for p in list_ports.comports() if p.device=='COM4']
    assert len(ports)==1 and (ports[0].vid,ports[0].pid,ports[0].serial_number)==(0x16c0,0x0483,'7858800')
    baseline=td(r'''import json,hashlib
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
from pixelblaze_mapper.routing_transaction import table_rows
assert_outputs_off(op)
r=op('/project1/multi_controller_output')
result=json.dumps({'controllers':table_rows(r.op('controller_config')),'gap':r.fetch('live_packet_gap_ms',{}),
 'external':r.fetch('external_sender_settings',{}),'perform':ui.performMode,
 'segments_sha256':hashlib.sha256(r.op('segment_config').text.encode()).hexdigest()})''')
    ser=serial.Serial('COM4',115200,timeout=.2,write_timeout=1)
    samples=[];quit_event=threading.Event();report={'baseline':baseline,'target':'10.0.0.253',
        'rate':rate,'seconds':seconds,'physical_led_measurement':False,'td_animation_payloads':True}
    def reader():
        while not quit_event.is_set():
            try:
                data=json.loads(ser.readline())
                if data.get('firmware')=='teensy41-artnet-0.1':samples.append({'host_time':time.perf_counter(),**data})
            except (ValueError,UnicodeDecodeError):pass
            except serial.SerialException:return
    thread=threading.Thread(target=reader,daemon=True);thread.start()
    def snapshot(command=b'STATUS\n'):
        requested=time.perf_counter();ser.write(command)
        while time.perf_counter()-requested<4:
            if samples and samples[-1]['host_time']>=requested:return dict(samples[-1])
            time.sleep(.02)
        raise RuntimeError('Fresh Teensy snapshot unavailable')
    try:
        identity=snapshot(b'STOP\nSTATUS\n');report['identity']=identity
        assert identity['unwired_bench'] and identity['pinout_confirmed'] and identity['led_limit']==880
        assert identity['ip']=='10.0.0.253' and identity['link'] and not identity['armed']
        snapshot(b'ARM\nSTATUS\n')
        report['start']=td(r'''import json
r=op('/project1/multi_controller_output');t=r.op('controller_config');s=r.op('artnet_510_sender_callbacks').module
for row in range(1,t.numRows):
 t[row,'enabled']='1' if str(t[row,'name'])=='BACK_PANEL_249' else '0'
 if str(t[row,'name'])=='BACK_PANEL_249':t[row,'rate']=%r;t[row,'local_interface']='10.0.0.125'
r.store('live_packet_gap_ms',{'BACK_PANEL_249':0.0})
settings=dict(r.fetch('external_sender_settings',{}));settings.update(enabled=True,frame_pacing=True,worker_priority='normal')
r.store('external_sender_settings',settings)
ui.performMode=True
s.set_live();assert s.set_enabled(True,target_override='10.0.0.253',port_override=6454)
result=json.dumps(s.status())'''%str(rate))
        time.sleep(3)
        # ARM watchdog can expire during a slow worker start: re-arm only the
        # same previously identified unwired bench after the stream is running.
        state=snapshot()
        if not state['armed']:state=snapshot(b'ARM\nSTATUS\n');time.sleep(.2)
        before=snapshot();first=len(samples);time.sleep(seconds);after=snapshot()
        elapsed=after['host_time']-before['host_time']
        keys=('packets','complete','incomplete','submitted','dma_completed','blackouts','overwritten','udp_queue_drops','ignored')
        delta={k:after[k]-before[k] for k in keys}
        report['measurement']={'before':before,'after':after,'elapsed':elapsed,'delta':delta,
            'dma_fps':(delta['dma_completed']-delta['blackouts'])/elapsed,
            'complete_fps':delta['complete']/elapsed,'telemetry':samples[first:]}
    except BaseException as error:
        report['error']=repr(error);raise
    finally:
        try:
            report['td_final']=td(r'''import json,hashlib
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
state=s.status();s.stop();baseline=json.loads(%r)
t=r.op('controller_config');t.clear()
for row in baseline['controllers']:t.appendRow(row)
r.store('live_packet_gap_ms',baseline['gap']);r.store('external_sender_settings',baseline['external'])
ui.performMode=baseline['perform']
assert hashlib.sha256(r.op('segment_config').text.encode()).hexdigest()==baseline['segments_sha256']
result=json.dumps({'sender_before_stop':state,'worker_final':r.fetch('last_external_sender_status'),
 'off':not s.status()['enabled'],'errors':op('/project1').errors(recurse=True),'routing_restored':True})'''%json.dumps(baseline))
        finally:
            try:
                snapshot(b'STOP\nSTATUS\n');time.sleep(.2)
                report['teensy_final']=snapshot()
                assert not report['teensy_final']['armed'] and report['teensy_final']['black']
            finally:
                quit_event.set();thread.join(1);ser.close()
                path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'measurement':{k:v for k,v in report['measurement'].items() if k not in ('before','after','telemetry')},
                     'td_off':report['td_final']['off'],'teensy_off':not report['teensy_final']['armed']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('--seconds',type=float,default=60)
    parser.add_argument('--rate',type=int,default=32);parser.add_argument('--frame-pacing',action='store_true')
    args=parser.parse_args();run(args.label,args.seconds,args.rate)
