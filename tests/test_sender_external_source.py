import unittest
import ast
from unittest.mock import Mock
from pixelblaze_mapper.sender_external_source import ExternalSocket, make_socket, install_source, rate_label
from pixelblaze_mapper.sender_packet_gap import install_source as gap
from pixelblaze_mapper.sender_pacing import install_source as pace
from pixelblaze_mapper.output_slot_mask import install_source as mask
from tests.test_sender_pacing import sender_source


class ExternalSourceTests(unittest.TestCase):
    def test_clocked_producer_headroom_is_opt_in_and_preserves_config(self):
        from pixelblaze_mapper.sender_external_source import producer_configs
        configs=[{'name':'rear','rate':30}]
        sock=ExternalSocket(Mock(),configs[0],{})
        self.assertIs(producer_configs(configs,sock),configs)
        sock.frame_rate=30
        self.assertEqual(producer_configs(configs,sock)[0]['rate'],60)
        self.assertEqual(configs[0]['rate'],30)
        sock.worker=Mock();sock.gap_ms=0;sock.owner.fetch.return_value={}
        configs[0]['rate']=40
        producer_configs(configs,sock)
        with self.assertRaisesRegex(RuntimeError,'Frame rate changed'):
            sock.flush()
        sock.worker.submit.assert_not_called()

    def test_patch_composes_and_preserves_guard_and_masks(self):
        from pixelblaze_mapper.guided_scan_live import guard_sender_source
        patched = guard_sender_source(install_source(gap(pace(mask(sender_source())))))
        compile(patched, '<sender>', 'exec')
        self.assertEqual(install_source(patched), patched)
        self.assertIn('assert_no_scan()', patched)
        self.assertIn('SPARSE_SOURCE_MASK_V1', patched)
        with self.assertRaises(ValueError):
            install_source('unexpected')

    def test_batch_and_stop(self):
        owner = Mock()
        owner.fetch.return_value = {}
        sock = ExternalSocket(owner, {'name':'rear'}, {})
        sock.gap_ms = 0
        sock.worker = Mock()
        sock.worker.submit.return_value = True
        sock.sendto(b'a', ('127.0.0.1', 1234))
        sock.sendto(b'b', ('127.0.0.1', 1234))
        sock.flush()
        sock.worker.submit.assert_called_once_with([(b'a', ('127.0.0.1',1234)),(b'b', ('127.0.0.1',1234))])
        self.assertEqual(sock.pending, [])
        sock.close()
        sock.worker.close.assert_called_once()

    def test_watchdog_status_does_not_claim_live_fps(self):
        label = rate_label({'transport':{'kind':'external','running':False,'actual_send_fps':30,'stop_reason':'idle_watchdog'}})
        self.assertIn('stopped',label)
        self.assertNotIn('30',label)

    def test_native_status_disables_dead_worker(self):
        source=install_source(gap(pace(mask(sender_source()))))
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='status')
        sock=ExternalSocket(Mock(),{},{});sock.worker=Mock()
        sock.worker.status.return_value={'running':False,'stop_reason':'idle_watchdog'}
        env={n.id:0 for n in ast.walk(node) if isinstance(n,ast.Name) and n.id.startswith('_')}
        env.update(ExternalSocket=ExternalSocket,_socket=sock,_enabled=True,_active_names=[])
        stopped=[]
        def stop():
            stopped.append(True);env['_enabled']=False;env['_socket']=None
        env['stop']=stop
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<status>','exec'),env)
        result=env['status']()
        self.assertEqual(stopped,[True])
        self.assertFalse(result['enabled'])
        self.assertIn('idle_watchdog',result['error'])

    def test_gap_change_requires_restart(self):
        owner=Mock();owner.fetch.return_value={'rear':2}
        sock=ExternalSocket(owner,{'name':'rear'},{});sock.gap_ms=1;sock.worker=Mock()
        with self.assertRaisesRegex(RuntimeError,'restart'):
            sock.flush()
        sock.worker.submit.assert_not_called()

    def test_no_silent_multicontroller_fallback(self):
        owner = Mock()
        owner.fetch.return_value = {'enabled': True}
        with self.assertRaisesRegex(RuntimeError, 'exactly one'):
            make_socket(owner, [{}, {}])
