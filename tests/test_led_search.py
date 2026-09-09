import unittest
from unittest.mock import patch
from pixelblaze_mapper import led_search as s

CONFIG=dict(name='test',target='10.0.0.249',interface='10.0.0.125',universe=122,count=450,rate=30,order='RGB')

class SearchTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
