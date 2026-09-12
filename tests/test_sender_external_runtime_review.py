"""Execute the actual external sender tick with mocked TD/worker surfaces."""
import ast
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from pixelblaze_mapper.output_slot_mask import install_source as mask
from pixelblaze_mapper.sender_packet_gap import install_source as gap
from pixelblaze_mapper.sender_pacing import ControllerPacer, install_source as pace
from pixelblaze_mapper.sender_external_source import ExternalSocket, install_source, producer_configs
from tests.test_sender_pacing import sender_source


class ExternalRuntimeReviewTests(unittest.TestCase):
    def tick_harness(self, rate=30):
        source = install_source(gap(pace(mask(sender_source()))))
        tick = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'tick')
        owner = Mock()
        owner.fetch.return_value = {}
        config = dict(name='rear', rate=rate, target='127.0.0.1', port=16454, universe=120)
        sock = ExternalSocket(owner, config, {})
        sock.frame_rate = sock.requested_rate = 30
        sock.gap_ms = 0.
        sock.worker = Mock()
        sock.worker.submit.return_value = True
        now = [100.]
        env = {node.id: 0 for node in ast.walk(tick)
               if isinstance(node, ast.Name) and node.id.startswith('_')}
        env.update(_enabled=True, _socket=sock, _pacer=ControllerPacer(),
                   _controllers=lambda _: [config], _mode='live',
                   _live_frames=lambda _: {'rear': [bytes([17]) * 510]},
                   _refresh_calibration_mask=lambda: None,
                   _packet=lambda universe, payload: bytes([universe]) + payload,
                   _target_override=None, _port_override=None,
                   time=SimpleNamespace(monotonic=lambda: now[0], perf_counter=lambda: now[0]),
                   me=SimpleNamespace(parent=lambda: owner), ExternalSocket=ExternalSocket)
        def stop():
            env['_enabled'] = False
            sock.close()
        env['stop'] = stop
        exec(compile(ast.Module(body=[tick], type_ignores=[]), '<external tick>', 'exec'), env)
        return env, config, now, sock

    def test_generated_tick_prepares_headroom_without_changing_requested_rate(self):
        env, config, now, sock = self.tick_harness()
        for index in range(120):
            now[0] = 100 + index / 120
            env['tick']()
        self.assertEqual(sock.worker.submit.call_count, 60)
        self.assertEqual(config['rate'], 30)
        self.assertEqual(sock.requested_rate, 30)
        self.assertTrue(env['_enabled'])

    def test_generated_tick_changed_valid_rate_stops_before_ipc(self):
        env, config, now, sock = self.tick_harness()
        env['tick']()
        sock.worker.submit.reset_mock()
        config['rate'] = 40
        now[0] += .1
        env['tick']()
        self.assertFalse(env['_enabled'])
        self.assertIn('Frame rate changed', env['_last_error'])
        sock.worker.submit.assert_not_called()
        sock.worker.close.assert_called_once()

    def test_generated_tick_invalid_rate_stops_before_ipc(self):
        for rate in (0, -1, 'invalid', float('nan'), float('inf')):
            env, config, now, sock = self.tick_harness(rate)
            with self.subTest(rate=rate):
                env['tick']()
            self.assertFalse(env['_enabled'])
            sock.worker.submit.assert_not_called()
            sock.worker.close.assert_called_once()

    def test_multiple_controllers_invalidate_clocked_flush_and_headroom_caps(self):
        env, config, now, sock = self.tick_harness()
        self.assertEqual(producer_configs([dict(config, rate=120)], sock)[0]['rate'], 120)
        producer_configs([config, dict(config, name='other')], sock)
        with self.assertRaisesRegex(RuntimeError, 'Frame rate changed'):
            sock.flush()
        sock.worker.submit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
