from pathlib import Path
import tempfile
import unittest
from pixelblaze_mapper.release_web_help import approved_help_asset


class ReleaseHelpAssetsTests(unittest.TestCase):
    def test_catalog_and_help_allowed_but_private_or_traversal_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ('help_catalog.json','secret.json','scan.html','script.py'):
                (root/name).write_text('{}')
            self.assertEqual(approved_help_asset('/release-help/catalog.json',root)[0],root/'help_catalog.json')
            self.assertIsNotNone(approved_help_asset('/release-help/scan.html',root))
            for path in ('/release-help/secret.json','/release-help/../secret.json',
                         '/release-help/%2e%2e/secret.json','/release-help/script.py',
                         '/release-help/C:/secret.json','/release-help/missing.html','/api/state'):
                self.assertIsNone(approved_help_asset(path,root),path)


if __name__=='__main__': unittest.main()
