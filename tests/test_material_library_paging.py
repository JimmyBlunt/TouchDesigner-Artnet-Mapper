import unittest

from pixelblaze_mapper.material_library_paging import clamped_page, page_count


class MaterialLibraryPagingTests(unittest.TestCase):
    def test_page_count_uses_ceil_and_keeps_empty_browser_on_page_one(self):
        self.assertEqual(page_count(0, 32), 1)
        self.assertEqual(page_count(32, 32), 1)
        self.assertEqual(page_count(33, 32), 2)
        self.assertEqual(page_count(638, 32), 20)

    def test_next_and_previous_are_clamped_at_both_boundaries(self):
        self.assertEqual(clamped_page(0, 1, 638, 32), (1, 20))
        self.assertEqual(clamped_page(19, 1, 638, 32), (19, 20))
        self.assertEqual(clamped_page(1, -1, 638, 32), (0, 20))
        self.assertEqual(clamped_page(0, -1, 638, 32), (0, 20))

    def test_invalid_counts_and_page_sizes_fail_closed(self):
        with self.assertRaises(ValueError):
            page_count(-1, 32)
        with self.assertRaises(ValueError):
            page_count(1, 0)


if __name__ == "__main__":
    unittest.main()
