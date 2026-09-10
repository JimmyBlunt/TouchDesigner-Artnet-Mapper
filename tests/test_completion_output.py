import itertools
import random
import unittest
from types import SimpleNamespace
from pixelblaze_mapper import output_slot_mask as mask
from pixelblaze_mapper.legacy_esp_bulk import frames


class OutputTests(unittest.TestCase):
    def test_layout_mask_supersedes_legacy_holes_and_rejects_malformed(self):
        table = SimpleNamespace(text='index\tenabled\n0\t1\n1\t0\n2\t1\n')
        owner = SimpleNamespace(fetch=lambda *_: [(0, 0)])
        op = lambda path: table if path == mask.MASK_PATH else owner
        self.assertEqual(mask.ranges_for(op, 3), ((1, 1),))
        table.text = 'index\tenabled\n0\t1\n1\t1\n2\t1'
        self.assertEqual(mask.ranges_for(op, 3), ())
        for value in ('index\tenabled', 'index\tenabled\n0\t1\n0\t0\n2\t1',
                      'index\tenabled\n0\t1\n1\t2\n2\t1'):
            table.text = value
            with self.assertRaises(ValueError): mask.ranges_for(op, 3)

    def test_bulk_exactly_matches_scalar_packer_all_orders_and_boundaries(self):
        random.seed(724)
        rgb = [[random.uniform(-.2, 1.2) for _ in range(3744)] for _ in range(3)]
        for order in map(''.join, itertools.permutations('RGB')):
            for count, offset, master in ((1679, 0, .02), (203, 1696, .062),
                                         (5, 3742, 1), (0, 0, 0), (170, 100, .5)):
                got = frames(rgb, offset=offset, count=count, order=order, master=master,
                             inactive=((1643, 1695),)).ravel().tolist()
                expected = [0.] * 5100
                for i in range(min(count, 3744-offset)):
                    for c, key in enumerate(order):
                        value = 0 if 1643 <= offset+i <= 1695 else rgb['RGB'.index(key)][offset+i]
                        expected[i*3+c] = round(max(0., min(1., value))*255.*master)
                self.assertEqual(got, expected)

    def test_mask_rebuilds_after_same_length_content_edit(self):
        self.assertEqual(mask._table_ranges('index\tenabled\n0\t0\n1\t1', 2), ((0, 0),))
        self.assertEqual(mask._table_ranges('index\tenabled\n0\t1\n1\t0', 2), ((1, 1),))
