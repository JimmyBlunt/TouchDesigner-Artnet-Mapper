import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pixelblaze_mapper import scan_coverage as coverage


class CoverageCacheTests(unittest.TestCase):
    def test_status_refresh_avoids_reread_but_changed_file_is_revalidated(self):
        coverage._view_ids.cache_clear()
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / 'view.csv'
            file.write_text('index,u,v\n0,.2,.3\n')
            with patch('builtins.open', wraps=open) as reader:
                self.assertEqual(coverage.coverage([file], [0,1])['missing'], [1])
                self.assertEqual(coverage.coverage([file], [0,1])['missing'], [1])
                self.assertEqual(reader.call_count, 1)
            file.write_text('index,u,v\n0,.2,.3\n1,.5,.6\n')
            self.assertEqual(coverage.coverage([file], [0,1])['missing'], [])
            file.write_text('index,u,v\n0,invalid,.3\n')
            self.assertEqual(len(coverage.coverage([file], [0,1])['errors']), 1)

    def test_oversized_view_rejected_before_open(self):
        with patch('builtins.open', side_effect=AssertionError('must not open')):
            with self.assertRaises(ValueError): coverage._view_ids('huge.csv', 0, 16*1024*1024+1)
