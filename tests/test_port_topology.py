import unittest
from dataclasses import replace

from pixelblaze_mapper.multi_controller import ControllerConfig, default_router_config
from pixelblaze_mapper.port_topology import (
    ControllerDraft, PortDraft, add_port, build_topology, merge_controller,
    remove_controller, remove_port, ui_to_wire, wire_to_ui,
)


class PortTopologyTests(unittest.TestCase):
    def controller(self, name='new_controller'):
        return ControllerConfig(name, '10.0.0.245', '10.0.0.125', start_universe=ui_to_wire(1))

    def test_gico_six_six_six_six_is_preserved(self):
        draft = ControllerDraft(self.controller('WS2812_NODE'), 'gico_equal', (
            PortDraft(1, 'Middle', True, 0, 517, 6), PortDraft(2, 'Upper', True, 517, 269, 6),
            PortDraft(3, 'Lower', True, 786, 398, 6), PortDraft(4, 'Rear', True, 1284, 896, 6)))
        plan = build_topology(draft)
        self.assertEqual(plan.controller.reserved_universes, 24)
        self.assertEqual([item.destination_start for item in plan.ports], [0, 1020, 2040, 3060])
        self.assertEqual([item.used_universes for item in plan.ports], [4, 2, 3, 6])
        self.assertEqual([item.first_wire_universe for item in plan.ports], [0, 6, 12, 18])

    def test_generic_independent_capacities_are_cumulative(self):
        draft = ControllerDraft(self.controller(), 'independent', (
            PortDraft(1, source_start=0, pixel_count=517, reserved_universes=4),
            PortDraft(2, source_start=517, pixel_count=269, reserved_universes=2),
            PortDraft(3, source_start=786, pixel_count=398, reserved_universes=6)))
        plan = build_topology(draft)
        self.assertEqual([item.destination_start for item in plan.ports], [0, 680, 1020])
        self.assertEqual(plan.controller.reserved_universes, 12)
        with self.assertRaisesRegex(ValueError, 'same reserved universe'):
            build_topology(replace(draft, profile='gico_equal'))

    def test_create_edit_remove_preserves_other_controllers(self):
        old = default_router_config()
        draft = ControllerDraft(self.controller(), 'independent', (PortDraft(1, source_start=0, pixel_count=10, reserved_universes=1),))
        added = merge_controller(old, draft)
        self.assertEqual(added.controllers[:-1], old.controllers)
        self.assertEqual(added.segments[:-1], old.segments)
        edited = merge_controller(added, replace(draft, controller=replace(draft.controller, target_address='10.0.0.246')))
        self.assertEqual(len(edited.controllers), 3)
        self.assertEqual(remove_controller(edited, draft.controller.name).controllers, old.controllers)
        self.assertEqual(remove_controller(edited, draft.controller.name).segments, old.segments)

    def test_port_create_remove_retains_stable_numbers(self):
        draft = ControllerDraft(self.controller(), 'independent', (PortDraft(1),))
        draft = add_port(draft)
        draft = remove_port(draft, 1)
        self.assertEqual(draft.ports[0].number, 2)

    def test_explicit_legacy_apa_prefix_preserved(self):
        draft = ControllerDraft(self.controller(), 'independent',
            (PortDraft(1, 'APA', True, 1187, 1167, 7, destination_start=512),))
        plan = build_topology(draft)
        self.assertEqual(plan.segments[0].destination_start, 512)
        self.assertEqual(plan.controller.reserved_universes, 10)
        self.assertEqual(plan.ports[0].capacity_pixels, 1188)

    def test_block_and_source_overlap_rejected(self):
        one = PortDraft(1, source_start=0, pixel_count=10, reserved_universes=1)
        for two in (PortDraft(2, source_start=5, pixel_count=10, reserved_universes=1),
                    PortDraft(2, source_start=10, pixel_count=10, reserved_universes=1, destination_start=0)):
            with self.assertRaises(ValueError):
                build_topology(ControllerDraft(self.controller(), 'independent', (one, two)))

    def test_capacity_source_end_and_universe_end_rejected(self):
        for port in (PortDraft(1, pixel_count=171, reserved_universes=1),
                     PortDraft(1, source_start=3740, pixel_count=10, reserved_universes=1)):
            with self.assertRaises(ValueError):
                build_topology(ControllerDraft(self.controller(), 'independent', (port,)))
        draft = ControllerDraft(replace(self.controller(), start_universe=32767), 'independent', (PortDraft(1, reserved_universes=2),))
        with self.assertRaises(ValueError):
            build_topology(draft)

    def test_ui_wire_roundtrip_and_bounds(self):
        for value in (1, 2, 7, 32768):
            self.assertEqual(wire_to_ui(ui_to_wire(value)), value)
        for value in (0, 32769, True):
            with self.assertRaises(ValueError):
                ui_to_wire(value)

    def test_unassigned_port_reserves_capacity_without_routing(self):
        plan = build_topology(ControllerDraft(self.controller(), 'independent', (PortDraft(1, pixel_count=100),)))
        self.assertFalse(plan.ports[0].routable)
        self.assertEqual(plan.segments, ())
        self.assertEqual(plan.controller.reserved_universes, 6)


if __name__ == '__main__':
    unittest.main()
