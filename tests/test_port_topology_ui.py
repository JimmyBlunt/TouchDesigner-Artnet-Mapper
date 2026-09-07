"""Behavioral tests for the actual embedded editor runtime, with offline DATs."""

import copy
import unittest
from dataclasses import asdict
from types import SimpleNamespace

from pixelblaze_mapper.multi_controller import ControllerConfig, controller_rows, default_router_config, segment_rows
from pixelblaze_mapper.port_topology import ControllerDraft, PortDraft
from tests.test_routing_apply_regression import Table, embedded


class Storage:
    def __init__(self):
        self.data = {}

    def fetch(self, key, default=None):
        return self.data.get(key, default)

    def store(self, key, value):
        self.data[key] = value

    def op(self, name):
        return None


class PortTopologyUIRuntimeTests(unittest.TestCase):
    def setUp(self):
        old = default_router_config()
        self.tables = {'controller_config': Table(controller_rows(old)), 'segment_config': Table(segment_rows(old)),
                       'validation': Table((('severity', 'code', 'field', 'message'),))}
        self.enabled = True
        def stop(*args):
            self.enabled = False
        self.sender = SimpleNamespace(module=SimpleNamespace(set_enabled=stop, stop=stop, status=lambda: {'enabled': self.enabled}))
        self.router = SimpleNamespace(op=lambda path: self.sender if path == 'artnet_510_sender_callbacks' else self.tables.get(path),
                                      findChildren=lambda **kwargs: [])
        self.owner = Storage()
        self.scope = {'op': lambda path: self.owner if path.endswith('/controller_ports') else
                      (None if path == '/project1/math1' else self.router)}
        exec(embedded('build_port_topology_ui.py', '_runtime_source'), self.scope)
        self.scope['_repaint'] = lambda: None
        self.scope['_rebuild_router'] = lambda: None
        self.values = {'load_id': 'NEW_NODE'}
        self.scope['_field'] = self.values.__getitem__

    def snapshot(self):
        return {key: copy.deepcopy(table.rows) for key, table in self.tables.items()}

    def fields(self):
        draft = self.scope['_saved']()
        ctrl = draft.controller
        self.values.update(profile=draft.profile, target=ctrl.target_address, interface=ctrl.local_interface,
                           udp_port=str(ctrl.port), first_ui=str(ctrl.start_universe + 1), brightness=str(ctrl.brightness),
                           rate=str(ctrl.rate), enabled=str(int(ctrl.enabled)), order=ctrl.color_order)
        page = self.owner.fetch('page', 0)
        for slot, port in enumerate(draft.ports[page * 6:page * 6 + 6]):
            for field, value in dict(label=port.label, enabled=int(port.enabled), source='' if port.source_start is None else port.source_start,
                pixels=port.pixel_count, reserve=port.reserved_universes, reverse=int(port.reverse), order=port.color_order,
                target='' if port.destination_start is None else port.destination_start).items():
                self.values['row%d_%s' % (slot, field)] = str(value)

    def new(self):
        self.assertTrue(self.scope['act']('new'), self.owner.data)
        self.fields()

    def test_new_add_remove_and_pagination_only_change_draft(self):
        before = self.snapshot()
        self.new()
        for _ in range(7):
            self.assertTrue(self.scope['act']('add'))
            self.fields()
        self.assertEqual(len(self.scope['_saved']().ports), 8)
        self.assertEqual(self.owner.fetch('page'), 1)
        self.values['remove_number'] = '8'
        self.assertTrue(self.scope['act']('remove'))
        self.assertEqual(len(self.scope['_saved']().ports), 7)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_safe_apply_new_independent_controller_preserves_existing(self):
        before = self.snapshot()
        self.new()
        self.values.update(target='10.0.0.247', interface='10.0.0.125', row0_enabled='1', row0_source='2400', row0_pixels='100')
        self.assertTrue(self.scope['act']('validate'), self.owner.data)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.scope['act']('apply'), self.owner.data)
        self.assertEqual(self.tables['controller_config'].rows[:-1], before['controller_config'])
        self.assertEqual(self.tables['segment_config'].rows[:-1], before['segment_config'])
        self.assertFalse(self.enabled)

    def test_stale_controller_snapshot_blocks_apply(self):
        self.new()
        self.tables['controller_config'][1, 'brightness'] = '0.05'
        before = self.snapshot()
        self.assertFalse(self.scope['act']('apply'))
        self.assertIn('Router changed since LOAD', self.owner.fetch('message'))
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_load_legacy_apa_preserves_prefix_and_delete_is_staged(self):
        self.values['load_id'] = 'APA102_ESP'
        self.assertTrue(self.scope['act']('load'), self.owner.data)
        self.fields()
        self.assertEqual(self.scope['_saved']().ports[0].destination_start, 512)
        before = self.snapshot()
        self.assertTrue(self.scope['act']('delete'))
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)
        self.assertTrue(self.scope['act']('apply'), self.owner.data)
        self.assertEqual([row[1] for row in self.tables['controller_config'].rows[1:]], ['WS2812_NODE'])
        self.assertFalse(self.enabled)

    def test_invalid_per_port_reserve_does_not_apply(self):
        self.new()
        before = self.snapshot()
        self.values['row0_reserve'] = '0'
        self.assertFalse(self.scope['act']('apply'))
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.enabled)

    def test_failed_builder_keeps_all_live_tables(self):
        self.new()
        before = self.snapshot()
        def failure():
            raise RuntimeError('injected')
        self.scope['_rebuild_router'] = failure
        self.assertFalse(self.scope['act']('apply'))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.enabled)
        self.assertIn('RECOVERY REQUIRED', self.owner.fetch('message'))


if __name__ == '__main__':
    unittest.main()
