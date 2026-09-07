"""Pure routing tests; no sockets, native imports, TD or hardware needed."""
from dataclasses import FrozenInstanceError, replace
import json
import unittest

from pixelblaze_mapper.multi_controller import ControllerConfig, RouterConfig, SegmentConfig, build_router_plan
from pixelblaze_mapper.scan_routing import (
    ScanRoutingError, ScanRoutingSnapshot, black_frames, create_snapshot, single_led_frames,
)


def six_universe_config(*, base=0, apa_enabled=False):
    """Explicit reviewed-shaped fixture, NOT production discovery/defaults."""
    return RouterConfig((
        ControllerConfig('WS2812_NODE', '10.0.0.244', '10.0.0.125', enabled=True,
                         start_universe=base, color_order='GRB', brightness=.02, reserved_universes=24),
        ControllerConfig('APA102_ESP', '10.0.0.251', '10.0.0.125', enabled=apa_enabled,
                         brightness=.03, reserved_universes=10),
    ), (
        SegmentConfig('middle', 0, 517, 'WS2812_NODE', 0),
        SegmentConfig('upper', 517, 269, 'WS2812_NODE', 1020),
        SegmentConfig('lower', 786, 398, 'WS2812_NODE', 2040),
        SegmentConfig('port4', 1284, 896, 'WS2812_NODE', 3060),
        SegmentConfig('apa', 1187, 1167, 'APA102_ESP', 512),
    ), source_pixel_count=3744)


class ScanRoutingTests(unittest.TestCase):
    def test_sparse_source_identity_dense_order_and_roundtrip(self):
        selected = [785, 517, 1284]
        snapshot = create_snapshot(six_universe_config(), selected)
        selected[0] = 0
        self.assertEqual(snapshot.source_indices, (785, 517, 1284))
        self.assertEqual(snapshot.get_led_count(), 3)
        self.assertEqual([snapshot.source_index(i) for i in range(3)], [785, 517, 1284])
        self.assertEqual(snapshot.worker_index(517), 1)
        with self.assertRaises(ScanRoutingError):
            snapshot.worker_index(518)
        with self.assertRaises(FrozenInstanceError):
            snapshot.brightness_cap = .05
        document = json.loads(json.dumps(snapshot.to_dict()))
        rebuilt = ScanRoutingSnapshot.from_dict(document)
        self.assertEqual(rebuilt.fingerprint, snapshot.fingerprint)
        self.assertEqual(single_led_frames(rebuilt, 0), single_led_frames(snapshot, 0))

    def test_six_reserved_per_port_exact_boundaries_and_nonzero_wire_base(self):
        sources = [0, 169, 170, 516, 517, 785, 786, 1183, 1284, 2179]
        destinations = [0, 169, 170, 516, 1020, 1288, 2040, 2437, 3060, 3955]
        snapshot = create_snapshot(six_universe_config(base=300), sources)
        for target, destination in zip(snapshot.targets, destinations):
            self.assertEqual(target.frame_index, destination // 170)
            self.assertEqual(target.wire_universe, 300 + destination // 170)
            self.assertEqual(target.slot, (destination % 170) * 3)
            self.assertEqual(target.component_indices, (1, 0, 2))
            packed = single_led_frames(snapshot, target.worker_index)['WS2812_NODE']
            self.assertEqual(len(packed), 24)
            self.assertTrue(all(type(frame) is bytes and len(frame) == 510 for frame in packed))
            expected = bytearray(24 * 510)
            expected[destination * 3:destination * 3 + 3] = bytes([5] * 3)
            self.assertEqual(b''.join(packed), bytes(expected))

    def test_full_black_scope_excludes_disabled_and_unselected_controllers(self):
        snapshot = create_snapshot(six_universe_config(apa_enabled=True), [0])
        self.assertEqual(snapshot.controller_names, ('WS2812_NODE',))
        frames = black_frames(snapshot)
        self.assertEqual(frames, {'WS2812_NODE': (bytes(510),) * 24})
        frames.clear()
        self.assertEqual(len(black_frames(snapshot)['WS2812_NODE']), 24)

    def test_two_selected_controllers_and_apa_non_aligned_prefix(self):
        snapshot = create_snapshot(six_universe_config(apa_enabled=True), [1187, 0])
        self.assertEqual(snapshot.controller_names, ('WS2812_NODE', 'APA102_ESP'))
        target = snapshot.targets[0]
        self.assertEqual((target.frame_index, target.wire_universe, target.slot), (3, 3, 6))
        frames = single_led_frames(snapshot, 0)
        self.assertEqual(frames['WS2812_NODE'], (bytes(510),) * 24)
        apa = b''.join(frames['APA102_ESP'])
        self.assertEqual(apa[:512 * 3], bytes(512 * 3))
        self.assertEqual(apa[512 * 3:515 * 3], bytes([8] * 3) + bytes(6))
        self.assertEqual(sum(value != 0 for value in apa), 3)

    def test_cap_never_increases_original_brightness_and_matches_reference(self):
        config = six_universe_config(apa_enabled=True)
        config = replace(config, controllers=(replace(config.controllers[0], brightness=.37), config.controllers[1]))
        snapshot = create_snapshot(config, [517, 1187], brightness_cap=.05)
        self.assertEqual(config.controllers[0].brightness, .37)
        effective = replace(config, controllers=tuple(replace(c, brightness=min(c.brightness, .05)) for c in config.controllers))
        for dense, source in enumerate(snapshot.source_indices):
            pixels = [(0.0, 0.0, 0.0)] * config.source_pixel_count
            pixels[source] = (1.0, 1.0, 1.0)
            reference = build_router_plan(effective).pack_pixels(pixels)
            self.assertEqual(single_led_frames(snapshot, dense),
                             {name:tuple(bytes(frame) for frame in reference[name]) for name in snapshot.controller_names})

    def test_reverse_override_and_derived_capacity_reuse_canonical_packer(self):
        config = RouterConfig((ControllerConfig('X', '10.0.0.2', '10.0.0.1', enabled=True, brightness=.02, start_universe=40),),
                              (SegmentConfig('reverse', 10, 3, 'X', 169, reverse=True, color_override='BGR'),),
                              source_pixel_count=20)
        snapshot = create_snapshot(config, [10, 11, 12])
        self.assertEqual([(t.frame_index,t.slot) for t in snapshot.targets], [(1,3),(1,0),(0,507)])
        self.assertTrue(all(t.component_indices == (2,1,0) for t in snapshot.targets))
        self.assertEqual(len(black_frames(snapshot)['X']), 2)
        for dense, source in enumerate(snapshot.source_indices):
            pixels = [(0,0,0)] * 20
            pixels[source] = (1,1,1)
            self.assertEqual(single_led_frames(snapshot, dense)['X'], tuple(bytes(f) for f in build_router_plan(config).pack_pixels(pixels)['X']))

    def test_unrouted_disabled_and_ambiguous_selected_ids_reject(self):
        for indices, config, message in (([1184], six_universe_config(), 'unrouted'),
                                         ([1187], six_universe_config(), 'disabled'),
                                         ([1284], six_universe_config(apa_enabled=True), 'Ambiguous')):
            with self.subTest(indices=indices, message=message), self.assertRaisesRegex(ScanRoutingError, message):
                create_snapshot(config, indices)
        # Router allows same-controller fanout, scan must not light both copies.
        config = six_universe_config()
        config = replace(config, segments=config.segments + (SegmentConfig('copy', 0, 1, 'WS2812_NODE', 600),))
        with self.assertRaisesRegex(ScanRoutingError, 'Ambiguous'):
            create_snapshot(config, [0])

    def test_disabled_duplicate_is_never_in_output_domain(self):
        snapshot = create_snapshot(six_universe_config(), [1284])
        self.assertEqual(snapshot.controller_names, ('WS2812_NODE',))

    def test_selection_indices_flags_and_brightness_reject_invalid_values(self):
        for selected in ([], [0,0], [True], [-1], [3744], ['0'], [0.0]):
            with self.subTest(selected=selected), self.assertRaises(ScanRoutingError):
                create_snapshot(six_universe_config(), selected)
        for cap in (True, 0, -.1, .10001, float('nan'), float('inf'), '0.05', .0001):
            with self.subTest(cap=cap), self.assertRaises(ScanRoutingError):
                create_snapshot(six_universe_config(), [0], brightness_cap=cap)
        config = six_universe_config()
        with self.assertRaises(ScanRoutingError):
            create_snapshot(replace(config, controllers=(replace(config.controllers[0], enabled='1'),)), [0])

    def test_each_frame_replaces_previous_led_and_off_always_validates_id(self):
        snapshot = create_snapshot(six_universe_config(), [0,517])
        first = single_led_frames(snapshot, 0)
        second = single_led_frames(snapshot, 1)
        self.assertNotEqual(first, second)
        self.assertEqual(second['WS2812_NODE'][0], bytes(510))
        self.assertEqual(single_led_frames(snapshot, 1, on=False), black_frames(snapshot))
        for index in (-1, 2, True, '0'):
            with self.assertRaises(ScanRoutingError):
                single_led_frames(snapshot, index, on=False)
        with self.assertRaises(ScanRoutingError):
            single_led_frames(snapshot, 0, on=1)

    def test_snapshot_tampering_unknown_fields_and_stale_addresses_reject(self):
        snapshot = create_snapshot(six_universe_config(), [517])
        changes = [lambda d:d.update(version=True), lambda d:d.update(extra=1),
                   lambda d:d['targets'][0].update(wire_universe=0),
                   lambda d:d['routing']['controllers'][0].update(start_universe=1),
                   lambda d:d['routing']['controllers'][0].pop('enabled'),
                   lambda d:d['routing']['segments'][0].update(unknown=1)]
        for change in changes:
            document = snapshot.to_dict()
            change(document)
            with self.assertRaises(ScanRoutingError):
                ScanRoutingSnapshot.from_dict(document)
        self.assertEqual(snapshot.targets[0].wire_universe, 6)

    def test_snapshot_binds_unselected_configuration_and_detaches_mutable_lists(self):
        config = six_universe_config()
        controllers, segments = list(config.controllers), list(config.segments)
        snapshot = create_snapshot(replace(config, controllers=controllers, segments=segments), [0])
        before = snapshot.fingerprint
        controllers.clear()
        segments.clear()
        self.assertEqual(snapshot.fingerprint, before)
        changed = replace(config, controllers=(config.controllers[0], replace(config.controllers[1], brightness=.04)))
        self.assertNotEqual(create_snapshot(changed,[0]).fingerprint, before)

    def test_addressed_descriptors_retain_endpoint_metadata_and_wire_numbers(self):
        config = six_universe_config(base=300)
        config = replace(config, controllers=(replace(config.controllers[0], port=6455, rate=60, art_sync=True), config.controllers[1]))
        snapshot = create_snapshot(config, [517])
        descriptors = snapshot.packet_descriptors(0, on=True)
        self.assertEqual(len(descriptors), 24)
        self.assertEqual([frame.wire_universe for frame in descriptors], list(range(300,324)))
        self.assertTrue(all((frame.target_address,frame.local_interface,frame.port,frame.rate,frame.art_sync) ==
                            ('10.0.0.244','10.0.0.125',6455,60,True) for frame in descriptors))
        self.assertEqual(tuple(frame.payload for frame in descriptors), snapshot.single_led_frames(0)['WS2812_NODE'])
        self.assertEqual(descriptors[6].payload[:3], bytes([5]*3))
        self.assertTrue(all(frame.payload == bytes(510) for frame in snapshot.packet_descriptors()))
        self.assertEqual(snapshot.single_led_frames(0, False), snapshot.black_frames())
        with self.assertRaises(ScanRoutingError):
            snapshot.packet_descriptors(on=True)


if __name__ == '__main__':
    unittest.main()
