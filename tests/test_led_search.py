import unittest
import io
import json
from unittest.mock import patch
from pixelblaze_mapper import led_search as s

CONFIG=dict(name='test',target='10.0.0.249',interface='10.0.0.125',universe=122,count=450,rate=30,order='RGB')

class SearchTests(unittest.TestCase):
    def test_single_chase_pixel_has_no_neighbors(self):
        config=dict(CONFIG,universe=142,count=680,frame_start_universe=120,frame_universe_count=33)
        f=dict(s.frames(config,609,.1,single=True))
        self.assertEqual(f[145][297:300],bytes((26,26,26)))
        self.assertEqual(sum(v!=0 for p in f.values() for v in p),3)

    def test_chase_stop_records_last_complete_frame_and_blacks_all_ports(self):
        config=dict(CONFIG,universe=142,count=680,frame_start_universe=120,frame_universe_count=33)
        class Socket:
            def __init__(self):self.sent=[]
            def settimeout(self,v):pass
            def bind(self,v):pass
            def sendto(self,p,d):
                self.sent.append(p)
                if len(self.sent)==33:s._stop.set()
            def close(self):pass
        sock=Socket();events=[];s._stop.clear()
        with patch.object(s.socket,'socket',return_value=sock),patch.object(s.time,'sleep'):
            s._chase_worker(config,609,.05,2,events.append)
        self.assertEqual([e['state'] for e in events],['running','stopped'])
        self.assertEqual(events[-1]['led_number'],610)
        self.assertFalse(events[-1]['count_confirmed'])
        self.assertTrue(events[-1]['black_sent'])
        self.assertEqual(len(sock.sent),132)
        self.assertTrue(all(not any(p[18:]) for p in sock.sent[33:]))
    def test_colors_and_universe_boundary(self):
        f=s.frames(CONFIG,170,.1)
        self.assertEqual([u for u,_ in f],[122,123,124])
        self.assertEqual(f[0][1][-3:],bytes((0,26,0)))
        self.assertEqual(f[1][1][:6],bytes((26,26,26,26,0,0)))
        self.assertEqual(sum(v!=0 for _,p in f for v in p),5)
        self.assertTrue(all(len(p)==510 for _,p in f))
    def test_zero_and_capacity_edge(self):
        self.assertEqual(s.frames(CONFIG,0,.1)[0][1][:6],bytes((26,26,26,26,0,0)))
        self.assertEqual(s.frames(CONFIG,509,.1)[-1][1][-6:],bytes((0,26,0,26,26,26)))
    def test_guard(self):
        for index in (-1,510,1.2):
            with self.assertRaises(ValueError):s.frames(CONFIG,index,.05)
        for bright in (0,.11,float('nan')):
            with self.assertRaises(ValueError):s.frames(CONFIG,5,bright)
    def test_wire_order(self):
        self.assertEqual(s.frames(dict(CONFIG,order='GRB'),1,.1)[0][1][:9],bytes((26,0,0,26,26,26,0,26,0)))
    def test_packet(self):
        p=s.packet(122,bytes(510))
        self.assertEqual(len(p),528);self.assertEqual(p[14:18],b'\x7a\0\x01\xfe')
    def test_teensy_full_frame_keeps_other_outputs_black(self):
        config=dict(CONFIG,universe=142,count=536,frame_start_universe=120,frame_universe_count=33)
        frames=dict(s.frames(config,534,.1))
        self.assertEqual(list(frames),list(range(120,153)))
        self.assertEqual(frames[145][69:78],bytes((0,26,0,26,26,26,26,0,0)))
        self.assertFalse(any(v for u,p in frames.items() if u!=145 for v in p))
        self.assertTrue(all(len(p)==510 for p in frames.values()))
    def test_worker_stops_black_and_releases_lease(self):
        class Socket:
            def __init__(self):self.sent=[];self.closed=False
            def settimeout(self,v):pass
            def bind(self,v):pass
            def sendto(self,p,d):self.sent.append((p,d));s._stop.set()
            def close(self):self.closed=True
        sock=Socket();token=s.scan_output_guard.acquire();s._stop.clear()
        with patch.object(s.socket,'socket',return_value=sock):s._worker(CONFIG,s.frames(CONFIG,202,.05),token)
        self.assertEqual(len(sock.sent),12)
        self.assertTrue(all(not any(p[18:]) for p,_ in sock.sent[-9:]))
        self.assertTrue(sock.closed);self.assertFalse(s.scan_output_guard.active())

    def test_external_worker_passes_full_frame_and_releases_lease(self):
        class Child:
            stdin=io.StringIO()
            returncode=0
            def poll(self):return 0
            def communicate(self,timeout):return ('OFF - black sent','')
        child=Child();token=s.scan_output_guard.acquire()
        config=dict(CONFIG,frame_start_universe=120,frame_universe_count=5)
        with patch.object(s.subprocess,'Popen',return_value=child) as launch:
            s._process_worker(config,s.frames(config,202,.05),token)
        data=json.loads(child.stdin.getvalue())
        self.assertEqual([u for u,p in data['frames']],list(range(120,125)))
        self.assertIn('pixelblaze_mapper.led_search',launch.call_args.args[0])
        self.assertFalse(s.scan_output_guard.active())
        self.assertEqual(s.status(),'OFF - black sent')

    def test_external_launch_failure_releases_lease(self):
        token=s.scan_output_guard.acquire()
        with patch.object(s.subprocess,'Popen',side_effect=OSError('launch failed')):
            s._process_worker(CONFIG,s.frames(CONFIG,202,.05),token)
        self.assertFalse(s.scan_output_guard.active())
        self.assertIn('launch failed',s.status())

if __name__=='__main__':unittest.main()
