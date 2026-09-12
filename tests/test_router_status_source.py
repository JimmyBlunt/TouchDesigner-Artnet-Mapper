import ast
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper.router_status_source import install_source, restore_source, mapping_counts_cached
from pixelblaze_mapper.router_dynamic_ui import mapping_counts
from tests.test_routing_apply_regression import embedded


class RouterStatusSourceTests(unittest.TestCase):
    def test_builder_and_live_patch_match_and_roundtrip(self):
        current = embedded('build_multi_controller_output.py', '_ui_callbacks_source')
        legacy = restore_source(current)
        self.assertNotEqual(current, legacy)
        self.assertEqual(install_source(legacy), current)
        self.assertEqual(install_source(current), current)
        self.assertEqual(restore_source(legacy), legacy)
        compile(current, '<router UI>', 'exec')
        with self.assertRaises(ValueError):
            install_source(current.replace('source_pixels = _source_pixels()', 'source_pixels = 1'))
        with self.assertRaises(ValueError):
            install_source('unknown callback')

    def test_refresh_reads_source_once_and_keeps_throttle_and_forced_update(self):
        source = embedded('build_multi_controller_output.py', '_ui_callbacks_source')
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)
                    and n.name == 'refresh_status')
        safety = SimpleNamespace(par=SimpleNamespace(text=''))
        sender = SimpleNamespace(module=SimpleNamespace(status=lambda: {'enabled': False}))
        surfaces = {'ui_panel/safety': safety, 'artnet_510_sender_callbacks': sender}
        count = Mock(side_effect=[10, 20])
        summary = Mock(return_value=SimpleNamespace(state='STOPPED', sender_enabled=False))
        now = [1.]
        env = dict(_last_status_update=0., time=SimpleNamespace(monotonic=lambda: now[0]),
                   op=surfaces.get, records=lambda x:x, table_rows=lambda x:x,
                   _source_pixels=count, build_output_summary=summary)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<router refresh>', 'exec'), env)
        with patch('pixelblaze_mapper.router_dynamic_ui.refresh') as refresh:
            env['refresh_status']()
            count.assert_called_once()
            self.assertEqual(summary.call_args.kwargs['source_pixels'], 10)
            self.assertIn('10 RGB source pixels', safety.par.text)
            now[0] += .1
            env['refresh_status']()
            self.assertEqual(count.call_count, 1)
            env['refresh_status'](force=True)
            self.assertEqual(count.call_count, 2)
            self.assertEqual(summary.call_args.kwargs['source_pixels'], 20)
            self.assertIn('20 RGB source pixels', safety.par.text)
            self.assertEqual(refresh.call_count, 2)

    def cache_fixture(self):
        storage = {}
        owner = Mock()
        owner.fetch.side_effect = lambda key, default=None: storage.get(key, default)
        owner.store.side_effect = lambda key, value: storage.__setitem__(key, value)
        controllers = [dict(name='a', enabled='1')]
        segments = [dict(controller='a', source_start='0', count='4')]
        return owner, controllers, segments

    def test_counts_cache_tracks_contents_and_returns_independent_values(self):
        owner, controllers, segments = self.cache_fixture()
        inactive = [[1, 1]]
        with patch('pixelblaze_mapper.router_dynamic_ui.mapping_counts', wraps=mapping_counts) as compute:
            first = mapping_counts_cached(owner, controllers, segments, 6, inactive)
            first['enabled'] = 999
            second = mapping_counts_cached(owner, controllers, segments, 6, inactive)
            self.assertEqual(second['enabled'], 3)
            self.assertEqual(compute.call_count, 1)
            inactive[0][1] = 2
            self.assertEqual(mapping_counts_cached(owner, controllers, segments, 6, inactive)['enabled'], 2)
            controllers[0]['enabled'] = '0'
            self.assertEqual(mapping_counts_cached(owner, controllers, segments, 6, inactive)['disabled_only'], 2)
            segments[0]['count'] = '5'
            self.assertEqual(mapping_counts_cached(owner, controllers, segments, 6, inactive)['disabled_only'], 3)
            self.assertEqual(mapping_counts_cached(owner, controllers, segments, 7, inactive)['unassigned'], 2)
            self.assertEqual(compute.call_count, 5)

    def test_invalid_mutation_never_reuses_previous_valid_entry(self):
        owner, controllers, segments = self.cache_fixture()
        good = mapping_counts_cached(owner, controllers, segments, 6)
        segments[0]['count'] = 'invalid'
        for _ in range(2):
            with self.assertRaises(ValueError):
                mapping_counts_cached(owner, controllers, segments, 6)
        segments[0]['count'] = '4'
        self.assertEqual(mapping_counts_cached(owner, controllers, segments, 6), good)
        # 6 == 6.0 in Python, but range(6.0) must still reject float input.
        with self.assertRaises(TypeError):
            mapping_counts_cached(owner, controllers, segments, 6.)

    def test_generator_input_falls_back_without_consuming_it_for_signature(self):
        owner, controllers, segments = self.cache_fixture()
        inactive = ((i, i) for i in (1, 2))
        self.assertEqual(mapping_counts_cached(owner, controllers, segments, 6, inactive)['enabled'], 2)
        owner.store.assert_not_called()


if __name__ == '__main__':
    unittest.main()
