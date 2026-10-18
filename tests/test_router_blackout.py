import unittest
from unittest.mock import Mock
from pixelblaze_mapper.multi_controller import ControllerConfig,SegmentConfig,RouterConfig
from pixelblaze_mapper.router_blackout import send_blackout


class BlackoutTests(unittest.TestCase):
    def config(self):
        return RouterConfig((ControllerConfig('esp','10.0.0.251','10.0.0.125',
            enabled=True,start_universe=156,reserved_universes=6),),
            (SegmentConfig('p8',0,256,'esp',destination_start=0),
             SegmentConfig('p7',256,553,'esp',destination_start=340)),source_pixel_count=809)

    def test_full_reserved_frames_black_both_esp_ports(self):
        sock=Mock(); factory=Mock(return_value=sock)
        report=send_blackout(self.config(),socket_factory=factory,sleep=lambda _:None)
        packets=[call.args[0] for call in sock.sendto.call_args_list]
        self.assertEqual(len(packets),18)
        self.assertEqual([int.from_bytes(p[14:16],'little') for p in packets],list(range(156,162))*3)
        self.assertTrue(all(len(p)==528 and not any(p[18:]) for p in packets))
        self.assertTrue(all(call.args[1]==('10.0.0.251',6454) for call in sock.sendto.call_args_list))
        self.assertEqual(report['universes'],6)
        sock.close.assert_called_once()

    def test_send_failure_is_reported_and_socket_closed(self):
        sock=Mock();sock.sendto.side_effect=OSError('synthetic failure')
        with self.assertRaisesRegex(RuntimeError,'blackout send failed'):
            send_blackout(self.config(),socket_factory=lambda *_:sock,sleep=lambda _:None)
        sock.close.assert_called_once()
