import tempfile
import unittest
from pathlib import Path
from pixelblaze_mapper.scan_coverage import coverage, description


class CoverageTests(unittest.TestCase):
    def test_unique_views_and_weak_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a.csv'; b=Path(folder)/'b.csv'
            a.write_text('index,u,v\n0,0.2,0.3\n1,0.4,0.5\n')
            b.write_text('index,u,v\n0,0.3,0.4\n')
            data=coverage([a,a,b],range(3))
            self.assertEqual((data['views'],data['seen'],data['twice']),(2,2,1))
            self.assertEqual(data['missing'],[2])
            self.assertEqual(data['weak'],{0:2,1:1})
            self.assertIn('3D-Qualitaet noch nicht',description(data,{}))

    def test_invalid_view_not_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a.csv'
            for body in ('index,u,v\n','index,u,v\n0,nan,0.3\n','index,u,v\n0,.1,.2\n0,.2,.3\n'):
                a.write_text(body)
                data=coverage([a],range(2))
                self.assertEqual(data['views'],0)
                self.assertEqual(len(data['errors']),1)
