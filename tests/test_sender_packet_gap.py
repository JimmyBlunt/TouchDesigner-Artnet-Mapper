import ast
import unittest
from types import SimpleNamespace

from pixelblaze_mapper.sender_packet_gap import install_source, seconds
from tests.test_sender_pacing import sender_source


class PacketGapTests(unittest.TestCase):
    def test_target_scope_and_invalid_settings(self):
        self.assertEqual(seconds({'rear': 1}, 'rear'), .001)
        self.assertEqual(seconds({'rear': 1}, 'side'), 0)
        for value in (-1, 6, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                seconds({'rear': value}, 'rear')

    def test_actual_send_loop_spacing_and_payloads(self):
        source = install_source(sender_source())
        self.assertEqual(install_source(source), source)
        compile(source, '<sender>', 'exec')
        with self.assertRaises(ValueError):
            install_source('unknown source')
        tick = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'tick')
        loop = next(n for n in ast.walk(tick) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'config')
        code = compile(ast.Module(body=[loop], type_ignores=[]), '<send-loop>', 'exec')
        events = []
        frames = [bytes([i]) * 510 for i in range(3)]
        config = lambda name: dict(name=name, target=name, port=6454, universe=120)
        env = dict(configs=[config('rear'), config('side')], _mode='live',
                   live_frames={'rear': frames, 'side': frames}, _target_override=None,
                   _port_override=None, sent_packets=0,
                   _packet=lambda u, p: (u, p),
                   _socket=SimpleNamespace(sendto=lambda p, t: events.append(('send', p, t))),
                   time=SimpleNamespace(sleep=lambda s: events.append(('sleep', s))),
                   me=SimpleNamespace(parent=lambda: SimpleNamespace(fetch=lambda k, d: {'rear': 1})))
        exec(code, env)
        self.assertEqual([e[0] for e in events], ['send', 'sleep', 'send', 'sleep', 'send', 'send', 'send', 'send'])
        self.assertEqual(env['sent_packets'], 6)
        self.assertEqual([e[1] for e in events if e[0] == 'send'], list(enumerate(frames, 120)) * 2)
