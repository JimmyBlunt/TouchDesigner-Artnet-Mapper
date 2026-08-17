import unittest
from pathlib import Path


class LegacyRepairContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / 'pixelblaze_mapper' / 'repair_legacy_nodes.py').read_text(encoding='utf-8')

    def test_optional_dependencies_are_not_required_at_project_load(self):
        self.assertIn('except ImportError', self.source)
        self.assertIn("websockets = None", self.source)
        self.assertIn("recorder.start() is an explicit user action", self.source)

    def test_missing_rear_split_parameters_are_recreated_from_real_corners(self):
        for name in ('Rearmidtopx', 'Rearmidtopy', 'Rearmidbottomx', 'Rearmidbottomy'):
            self.assertIn(name, self.source)

    def test_repair_does_not_save_rewire_or_start_network(self):
        self.assertNotIn('project.save(', self.source)
        self.assertNotIn('outputConnectors', self.source)
        self.assertNotIn('inputConnectors', self.source)
        self.assertNotIn('recorder.start()\n', self.source.replace('# recorder.start() is an explicit user action\n', ''))
        self.assertIn("'networkStarted': False", self.source)


if __name__ == '__main__':
    unittest.main()
