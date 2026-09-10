"""Offline behavioral regressions; never execute TD or create a network socket."""

import ast
import copy
import unittest
from pathlib import Path
from types import SimpleNamespace

from pixelblaze_mapper.multi_controller import controller_rows, default_router_config, segment_rows


ROOT = Path(__file__).resolve().parents[1]


def embedded(filename, function):
    tree = ast.parse((ROOT / 'pixelblaze_mapper' / filename).read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    # The extracted factory uses the same project root as the real module.
    scope = {'PROJECT_ROOT': ROOT, '__file__': str(ROOT / 'pixelblaze_mapper' / filename)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<factory>', 'exec'), scope)
    return scope[function]()


class Table:
    def __init__(self, rows=()):
        self.rows = [[str(v) for v in row] for row in rows]

    @property
    def numRows(self):
        return len(self.rows)

    @property
    def numCols(self):
        return len(self.rows[0]) if self.rows else 0

    def __getitem__(self, key):
        row, col = key
        return self.rows[row][self.rows[0].index(col) if isinstance(col, str) else col]

    def __setitem__(self, key, value):
        row, col = key
        self.rows[row][self.rows[0].index(col) if isinstance(col, str) else col] = str(value)

    def clear(self):
        self.rows.clear()

    def appendRow(self, row):
        self.rows.append([str(v) for v in row])


class RoutingApplyRegressionTests(unittest.TestCase):
    def setUp(self):
        config = default_router_config()
        self.tables = {
            'controller_config': Table(controller_rows(config)),
            'segment_config': Table(segment_rows(config)),
            'calibration_config': Table((('key', 'value'), ('panel', 'all'), ('pattern', 'panel_id'), ('chase_index', '0'))),
            'validation': Table((('severity', 'code', 'field', 'message'),)),
            'controller_summary': Table((('controller', 'status'),)),
        }
        self.enabled = True
        self.stop_calls = 0
        def stop(value=False):
            self.enabled = False
            self.stop_calls += 1
            return True
        self.sender = SimpleNamespace(module=SimpleNamespace(set_enabled=stop, stop=stop, status=lambda: {'enabled': self.enabled}))
        self.router = SimpleNamespace(op=lambda name: self.sender if name == 'artnet_510_sender_callbacks' else self.tables.get(name), findChildren=lambda **kw: [])
        self.values = dict(ws_ip='10.0.0.245', ws_universe='0', ws_brightness='0.04', ws_enabled='1',
                           apa_ip='10.0.0.251', apa_universe='0', apa_brightness='0.02', apa_enabled='0',
                           cal_panel='all', cal_pattern='panel_id', cal_chase='0')
        # The router now uses configuration-driven controller cards. Model the
        # cards' stored drafts, including stale-baseline checks; the retired
        # ws_/apa_ fields are no longer read by apply_safe().
        from pixelblaze_mapper.routing_transaction import records
        baselines = {r['name']: r for r in records(self.tables['controller_config'].rows)}
        storage = {'router_card_name': None, 'router_card_baselines': baselines}
        def fetch(key, default=None):
            if key == 'router_card_drafts':
                drafts = {}
                for name, prefix in (('WS2812_NODE', 'ws'), ('APA102_ESP', 'apa')):
                    base = baselines[name]
                    drafts[name] = dict(target_ip=self.values[prefix + '_ip'],
                        start_universe=self.values[prefix + '_universe'],
                        brightness=self.values[prefix + '_brightness'],
                        enabled=self.values[prefix + '_enabled'], rate=base['rate'])
                return drafts
            return storage.get(key, default)
        self.router.fetch = fetch
        self.router.store = storage.__setitem__
        self.scope = {'op': lambda name: self.router if name == '/project1/multi_controller_output' else self.router.op(name), 'parent': lambda: self.router}
        exec(embedded('build_multi_controller_output.py', '_ui_callbacks_source'), self.scope)
        self.messages = []
        self.scope['_field'] = self.values.__getitem__
        self.scope['_set_status'] = lambda message, *args: self.messages.append(message)

    def snapshot(self):
        return {key: copy.deepcopy(value.rows) for key, value in self.tables.items()}

    def test_invalid_later_controller_does_not_change_any_router_table(self):
        before = self.snapshot()
        self.values['apa_ip'] = 'INVALID'
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_invalid_calibration_does_not_change_controller_tables(self):
        before = self.snapshot()
        self.values['cal_chase'] = '3744'
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)

    def test_sender_uses_canonical_wire_universe_without_second_conversion(self):
        source = embedded('build_multi_controller_output.py', '_artnet_510_sender_source')
        tree = ast.parse(source)
        names = {'_controllers', '_bool', '_safe'}
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        import re
        scope = {'op': self.router.op, 're': re}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<sender-config>', 'exec'), scope)
        for ui_start in (1, 2, 7):
            self.tables['controller_config'][1, 'enabled'] = '1'
            self.tables['controller_config'][1, 'start_universe'] = ui_start - 1
            self.assertEqual(scope['_controllers']()[0]['universe'], ui_start - 1)

    def test_successful_apply_stops_before_rebuild_and_preserves_six_port_blocks(self):
        self.tables['controller_config'][1, 'reserved_universes'] = 24
        self.tables['segment_config'][2, 'destination_start'] = 1020
        self.tables['segment_config'][3, 'destination_start'] = 2040
        # Reload the card after changing its routing reservation externally.
        from pixelblaze_mapper.routing_transaction import records
        self.router.fetch('router_card_baselines').update(
            {r['name']: r for r in records(self.tables['controller_config'].rows)})
        expected_segments = copy.deepcopy(self.tables['segment_config'].rows)
        calls = []
        def rebuild():
            self.assertFalse(self.enabled)
            calls.append(True)
        self.scope['_rebuild_router'] = rebuild
        self.assertTrue(self.scope['apply_safe']())
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.tables['controller_config'][1, 'reserved_universes'], '24')
        self.assertEqual(self.tables['segment_config'].rows, expected_segments)
        self.assertFalse(self.enabled)

    def test_failed_builder_rolls_back_all_tables_and_stays_off(self):
        before = self.snapshot()
        calls = []
        def rebuild():
            calls.append(True)
            if len(calls) == 1:
                self.tables['validation'].appendRow(('error', 'injected', '', 'injected builder failure'))
                raise RuntimeError('injected')
        self.scope['_rebuild_router'] = rebuild
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.enabled)
        self.assertEqual(len(calls), 2)
        self.assertIn('previous tables restored', self.messages[-1])

    def test_builder_returning_blocked_is_not_success(self):
        before = self.snapshot()
        def rebuild():
            self.tables['validation'].appendRow(('error', 'injected', '', 'blocked rebuild'))
        self.scope['_rebuild_router'] = rebuild
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.enabled)

    def test_stop_failure_blocks_commit_without_losing_tables(self):
        before = self.snapshot()
        def failure(*args):
            raise RuntimeError('stop failed')
        self.sender.module.set_enabled = failure
        self.sender.module.stop = failure
        self.scope['_rebuild_router'] = lambda: self.fail('must not rebuild')
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertIn('Stop not confirmed', self.messages[-1])

    def test_controller_row_order_is_not_identity(self):
        self.tables['controller_config'].rows[1:] = list(reversed(self.tables['controller_config'].rows[1:]))
        self.scope['_rebuild_router'] = lambda: None
        self.assertTrue(self.scope['apply_safe']())
        rows = self.tables['controller_config']
        self.assertEqual(rows[1, 'name'], 'APA102_ESP')
        self.assertEqual(rows[1, 'target_ip'], self.values['apa_ip'])
        self.assertEqual(rows[2, 'target_ip'], self.values['ws_ip'])

    def test_one_shot_partial_table_write_is_rolled_back(self):
        before = self.snapshot()
        table = self.tables['controller_config']
        original = table.appendRow
        calls = []
        def injected(row):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError('injected table write')
            original(row)
        table.appendRow = injected
        self.scope['_rebuild_router'] = lambda: None
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.enabled)

    def test_failed_recovery_is_explicit(self):
        before = self.snapshot()
        def rebuild():
            raise RuntimeError('builder unavailable')
        self.scope['_rebuild_router'] = rebuild
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.enabled)
        self.assertIn('RECOVERY REQUIRED', self.messages[-1])

    def test_full_router_validation_precedes_commit(self):
        self.values['ws_ip'] = '224.0.0.1'
        before = self.snapshot()
        self.assertFalse(self.scope['apply_safe']())
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def gico_scope(self):
        self.draft_tables = {'settings': Table((('key', 'value'), ('universes_per_port', '6'), ('first_universe', '1'))),
                             'ports': Table((('port', 'label', 'enabled', 'source_start', 'pixel_count', 'reverse', 'color_order'),))}
        owner = SimpleNamespace(op=self.draft_tables.get)
        scope = {'op': lambda path: owner if path.endswith('/gico_port_config') else
                 (None if path == '/project1/math1' else self.router)}
        exec(embedded('build_gico_port_config_ui.py', '_runtime_source'), scope)
        values = dict(universes_per_port='6', first_universe='0')
        for n, start, count in ((1, '0', 517), (2, '517', 269), (3, '786', 398), (4, '', 896)):
            values.update({f'p{n}_label': f'Port {n}', f'p{n}_enabled': '1',
                           f'p{n}_source': start, f'p{n}_count': str(count),
                           f'p{n}_reverse': '0', f'p{n}_order': 'GRB'})
        scope['_field'] = values.__getitem__
        scope['_status'] = lambda text, *args: self.messages.append(text)
        scope['_rebuild_router'] = lambda: None
        return scope, values

    def test_gico_rejects_invalid_flags_before_any_mutation(self):
        for field, value in (('p1_enabled', '2'), ('p1_reverse', '-1')):
            scope, values = self.gico_scope()
            values[field] = value
            before = self.snapshot()
            self.assertFalse(scope['apply_safe_draft']())
            self.assertEqual(self.snapshot(), before)
            self.assertTrue(self.enabled)

    def test_gico_rejects_source_overflow_before_any_mutation(self):
        scope, values = self.gico_scope()
        values['p1_source'] = '99999'
        before = self.snapshot()
        self.assertFalse(scope['apply_safe_draft']())
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_gico_rejects_universe_overflow_before_any_mutation(self):
        scope, values = self.gico_scope()
        values['first_universe'] = '32768'
        before = self.snapshot()
        self.assertFalse(scope['apply_safe_draft']())
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_gico_apply_converts_ui_once_and_preserves_other_controller(self):
        for first in (0, 1, 6, 120):
            scope, values = self.gico_scope()
            values['first_universe'] = str(first)
            apa = copy.deepcopy(self.tables['controller_config'].rows[2])
            self.assertTrue(scope['apply_safe_draft'](), self.messages)
            self.assertEqual(self.tables['controller_config'][1, 'start_universe'], str(first))
            self.assertEqual(self.tables['controller_config'][1, 'reserved_universes'], '24')
            self.assertEqual(self.tables['controller_config'].rows[2], apa)
            self.assertEqual([row[4] for row in self.tables['segment_config'].rows[2:]], ['0', '1020', '2040'])
            self.assertFalse(self.enabled)

    def test_gico_failed_rebuild_restores_router_and_draft_tables(self):
        scope, values = self.gico_scope()
        before = self.snapshot()
        draft_before = {key: copy.deepcopy(table.rows) for key, table in self.draft_tables.items()}
        count = []
        def rebuild():
            count.append(1)
            if len(count) == 1:
                raise RuntimeError('injected gico failure')
        scope['_rebuild_router'] = rebuild
        self.assertFalse(scope['apply_safe_draft']())
        self.assertEqual(self.snapshot(), before)
        self.assertEqual({key: table.rows for key, table in self.draft_tables.items()}, draft_before)
        self.assertFalse(self.enabled)

    def test_transaction_uses_explicit_current_source_count(self):
        from pixelblaze_mapper.routing_transaction import apply_router_transaction
        controllers = copy.deepcopy(self.tables['controller_config'].rows)
        segments = copy.deepcopy(self.tables['segment_config'].rows)
        segments[1][1] = '4000'
        self.assertTrue(apply_router_transaction(self.router, controllers, segments, lambda: None,
                                               source_pixels=5000))

    def test_malformed_rows_and_duplicate_headers_are_rejected(self):
        from pixelblaze_mapper.routing_transaction import records
        for rows in ((('name', 'name'), ('x', 'y')), (('name', 'count'), ('x',)), (('',),)):
            with self.assertRaises(ValueError):
                records(rows)


if __name__ == '__main__':
    unittest.main()
