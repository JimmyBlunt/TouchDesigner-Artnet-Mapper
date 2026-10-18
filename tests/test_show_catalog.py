import json
import tempfile
import unittest
from pathlib import Path
from pixelblaze_mapper.show_catalog import saved_shows


class SavedShowCatalogTests(unittest.TestCase):
    def test_lists_valid_shows_and_empty_drafts_but_not_sidecars(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            show = dict(schema_version=2, name='Meine Show', loop=True, cues=[])
            for name in ('different_filename.json', 'show.automation.json', 'show.materials.json'):
                (root / name).write_text(json.dumps(show), encoding='utf-8')
            (root / 'broken.json').write_text('{broken', encoding='utf-8')
            entries = saved_shows(root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]['label'], 'Meine Show')
            self.assertEqual(entries[0]['filename'], 'different_filename.json')
            self.assertEqual(entries[0]['cues'], 0)
            self.assertEqual(Path(entries[0]['path']), root / 'different_filename.json')

    def test_missing_folder_has_no_choices(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(saved_shows(Path(folder) / 'missing'), [])
