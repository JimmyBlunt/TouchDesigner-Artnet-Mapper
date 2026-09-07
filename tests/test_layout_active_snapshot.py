"""Pure snapshot/TD-read-boundary behavior; no live calls or hardware sends."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper.layout_active_snapshot import MAP_PATH, ROUTER_PATH, snapshot_document, read_active_snapshot
from pixelblaze_mapper.layout_scene import SceneError
from pixelblaze_mapper.multi_controller import ControllerConfig, SegmentConfig, RouterConfig, controller_rows, segment_rows


def mapping(count=6):
    return [("index", "tx", "ty", "tz")] + [(str(i), str(i * .1), str(-i), str(i + 1)) for i in range(count)]


def router():
    return RouterConfig((ControllerConfig("controller", "10.0.0.244", "10.0.0.178"),),
        (SegmentConfig("upper", 0, 2, "controller", 4, True), SegmentConfig("lower", 3, 2, "controller", 10)), 6)


def stringify(rows):
    return [[str(v) for v in row] for row in rows]


class Table:
    def __init__(self, rows):
        self.rows = stringify(rows)
        self.numRows, self.numCols = len(rows), len(rows[0])

    def __getitem__(self, key):
        return self.rows[key[0]][key[1]]


class SnapshotTests(unittest.TestCase):
    def snapshot(self, config=None):
        config = config or router()
        return snapshot_document(mapping(), stringify(controller_rows(config)), stringify(segment_rows(config)))

    def test_disjoint_ranges_and_unmapped_preserve_every_source_index(self):
        doc, warnings = self.snapshot()
        self.assertEqual(warnings, ())
        self.assertEqual([o.name for o in doc.scene.objects], ["upper [controller]", "lower [controller]", "Unmapped"])
        self.assertEqual([[led.source_index for led in o.leds] for o in doc.scene.objects], [[0, 1], [3, 4], [2, 5]])
        self.assertEqual(doc.scene.expected_count, 6)
        self.assertEqual([led.source_index for led, _ in doc.scene.world_points()], list(range(6)))
        self.assertEqual([p for _, p in doc.scene.world_points()], [(i * .1, -float(i), float(i + 1)) for i in range(6)])
        self.assertEqual(doc.routes, ())  # UDP port is NOT a guessed physical port.
        self.assertIn(("reverse", "True"), doc.scene.scans[0].row_metadata[0])

    def test_missing_invalid_overlapping_route_data_falls_back_without_led_loss(self):
        config = router()
        cases = [(None, None), ([], []),
                 (stringify(controller_rows(config)), stringify(segment_rows(replace(config, segments=(config.segments[0], replace(config.segments[1], source_start=1)))))),
                 (stringify(controller_rows(config)), stringify(segment_rows(replace(config, segments=(replace(config.segments[0], count=99),)))))]
        for controllers, segments in cases:
            with self.subTest(segments=segments):
                doc, warnings = snapshot_document(mapping(), controllers, segments)
                self.assertTrue(warnings)
                self.assertEqual(len(doc.scene.objects), 1)
                self.assertEqual(len(doc.scene.objects[0].leds), 6)
                doc.scene.validate_output()

    def test_led_ids_stable_by_source_namespace_not_coordinate_values(self):
        first, _ = snapshot_document(mapping())
        altered = mapping()
        altered[1] = ("0", "99", "0", "1")
        second, _ = snapshot_document(altered)
        self.assertEqual([led.led_id for led, _ in first.scene.world_points()], [led.led_id for led, _ in second.scene.world_points()])
        self.assertNotEqual(first.scene.scans[0].scan_id, second.scene.scans[0].scan_id)
        self.assertEqual(first.scene.scans[0].points[0], (0, 0, 1))

    def test_malformed_nonfinite_reordered_map_rejected(self):
        for rows in ([], [("tx", "ty", "tz")], [("index", "tx", "ty", "tz"), ("1", "0", "0", "0")],
                     [("index", "tx", "ty", "tz"), ("0", "nan", "0", "0")]):
            with self.subTest(rows=rows), self.assertRaises(SceneError):
                snapshot_document(rows)

    def test_read_boundary_uses_authoritative_table_twice(self):
        config = router()
        nodes = {MAP_PATH: Table(mapping()), ROUTER_PATH + "/controller_config": Table(controller_rows(config)),
                 ROUTER_PATH + "/segment_config": Table(segment_rows(config))}
        owner = Mock()
        owner.op.side_effect = nodes.get
        doc, warnings = read_active_snapshot(owner)
        self.assertEqual(doc.scene.expected_count, 6)
        self.assertEqual(warnings, ())
        self.assertTrue(all(call.args[0] in nodes for call in owner.op.call_args_list))

    def test_changed_snapshot_rejected_before_draft_mutation(self):
        owner = Mock()
        owner.op.side_effect = lambda path: Table(mapping()) if path == MAP_PATH else None
        changed = mapping()
        changed[1] = ("0", "999", "0", "0")
        with patch("pixelblaze_mapper.layout_active_snapshot.table_rows", side_effect=[stringify(mapping()), stringify(changed)]):
            with self.assertRaisesRegex(SceneError, "changed during snapshot"):
                read_active_snapshot(owner)


if __name__ == "__main__":
    unittest.main()
