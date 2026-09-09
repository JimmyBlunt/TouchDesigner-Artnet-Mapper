import unittest
import ast
from pathlib import Path

from pixelblaze_mapper.sender_pacing import ControllerPacer, install_source

def sender_source():
    path = Path(__file__).resolve().parents[1] / 'pixelblaze_mapper/build_multi_controller_output.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_artnet_510_sender_source')
    return ast.literal_eval(function.body[0].value)


class SenderPacingTests(unittest.TestCase):
    def test_separate_rates(self):
        pacer = ControllerPacer()
        configs = [{'name': 'side', 'rate': 60}, {'name': 'back', 'rate': 30}]
        counts = dict(side=0, back=0)
        for i in range(600):
            for item in pacer.due(configs, i / 60):
                counts[item['name']] += 1
        self.assertEqual(counts, dict(side=600, back=300))

    def test_near_rate_does_not_halve(self):
        pacer = ControllerPacer()
        config = [{'name': 'side', 'rate': 60}]
        times = [i / 60.1 for i in range(601)]
        count = sum(bool(pacer.due(config, t)) for t in times)
        old_count, last = 0, -1
        for t in times:
            if t - last >= 1 / 60:
                old_count += 1
                last = t
        self.assertGreaterEqual(count, 599)
        self.assertLessEqual(old_count, 301)

    def test_slow_callback_and_long_pause_do_not_burst(self):
        pacer = ControllerPacer()
        config = [{'name': 'side', 'rate': 60}]
        self.assertTrue(pacer.due(config, 0))
        self.assertTrue(pacer.due(config, 20))
        self.assertFalse(pacer.due(config, 20))
        self.assertTrue(pacer.due(config, 20.05))

    def test_rate_changes_removal_reset_and_clock_rollback(self):
        pacer = ControllerPacer()
        config = [{'name': 'side', 'rate': 30}]
        self.assertTrue(pacer.due(config, 1))
        self.assertFalse(pacer.due(config, 1.001))
        config[0]['rate'] = 60
        self.assertTrue(pacer.due(config, 1.002))
        self.assertEqual(pacer.due([], 2), [])
        self.assertTrue(pacer.due(config, 2))
        self.assertTrue(pacer.due(config, 0))
        pacer.reset()
        self.assertTrue(pacer.due(config, 0))

    def test_invalid_rates(self):
        for rate in (0, 121, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                ControllerPacer().due([{'name': 'x', 'rate': rate}], 0)

    def test_installer(self):
        source = install_source(sender_source())
        compile(source, '<sender>', 'exec')
        self.assertEqual(install_source(source), source)
        with self.assertRaises(ValueError):
            install_source('unknown sender')


if __name__ == '__main__':
    unittest.main()
