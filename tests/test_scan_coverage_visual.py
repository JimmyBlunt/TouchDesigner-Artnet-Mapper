"""Visual coverage uses measurements, never synthetic missing LED positions."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pixelblaze_mapper import scan_coverage_visual as visual
from pixelblaze_mapper.scan_session import ScanSessionError
from pixelblaze_mapper.standalone_scan import session


class VisualCoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def view(self, name, rows):
        path = self.root / name
        path.write_text('index,u,v\n' + ''.join('%s,%s,%s\n' % row for row in rows), encoding='utf-8')
        return path

    def candidate(self, ids):
        path = self.root / 'candidate_3d.csv'
        path.write_text('index,x,y,z\n' + ''.join('%s,1,2,3\n' % index for index in ids), encoding='utf-8')
        return path

    def test_counts_are_deduplicated_and_status_depends_on_candidate(self):
        one = self.view('one.csv', [(0, .1, .2), (1, .2, .2), (2, .3, .2)])
        two = self.view('two.csv', [(0, .1, .2), (1, .2, .2)])
        three = self.view('three.csv', [(0, .1, .2)])
        candidate = self.candidate([0, 1])
        data = visual.build_data([one, one, two, three], range(4), candidate)
        self.assertEqual(len(data['views']), 3)
        self.assertEqual(data['never_seen_ids'], [3])
        self.assertEqual(data['unreconstructed_ids'], [2, 3])
        self.assertEqual(data['weak_ids'], [1])
        self.assertEqual(data['reconstructed_count'], 2)
        self.assertEqual([(point['status'], point['count']) for point in data['views'][0]['points']],
                         [('good', 3), ('weak', 2), ('unreconstructed', 1)])
        self.assertEqual(data['best_view'], str(one))
        json.dumps(data, allow_nan=False)

    def test_without_candidate_observations_are_weak_or_good(self):
        paths = [self.view('%d.csv' % index, [(0, .1, .1)]) for index in range(3)]
        data = visual.build_data(paths, [0, 1])
        self.assertFalse(data['has_candidate'])
        self.assertEqual(data['views'][0]['points'][0]['status'], 'good')
        self.assertEqual(data['unreconstructed_ids'], [])
        self.assertEqual(data['unlocated_ids'], [1])

    def test_neighborhoods_only_have_measured_bounds_not_missing_positions(self):
        path = self.view('near.csv', [(0, .1, .1), (3, .2, .1)])
        data = visual.build_data([path], range(4))
        view = data['views'][0]
        self.assertEqual([point['id'] for point in view['points']], [0, 3])
        self.assertEqual(view['neighbors'], [{'missing_ids': [1, 2], 'kind': 'neighborhood_reference',
                                             'before': {'id': 0, 'u': .1, 'v': .1},
                                             'after': {'id': 3, 'u': .2, 'v': .1}}])
        self.assertEqual(view['neighbor_missing_count'], 2)
        self.assertEqual(data['unlocated_count'], 0)

    def test_fold_distance_long_gaps_and_unbounded_endpoints_are_unlocated(self):
        for name, ids, scope, coordinates in [
            ('fold', [0, 2], range(3), [.1, .9]),
            ('long', [0, 10], range(11), [.1, .2]),
            ('end', [1, 2], range(4), [.1, .2]),
            ('scope-gap', [0, 3], [0, 2, 3], [.1, .2]),
        ]:
            with self.subTest(name=name):
                path = self.view(name+'.csv', [(i, u, .1) for i, u in zip(ids, coordinates)])
                data = visual.build_data([path], scope)
                self.assertEqual(data['views'][0]['neighbors'], [])
                self.assertEqual(data['unlocated_ids'], data['never_seen_ids'])

    def test_nearest_global_measured_bounds_must_both_exist_in_same_view(self):
        wide = self.view('wide.csv', [(0, .1, .1), (4, .2, .1)])
        other = self.view('other.csv', [(2, .15, .1)])
        data = visual.build_data([wide, other], range(5))
        self.assertEqual(data['never_seen_ids'], [1, 3])
        self.assertTrue(all(not view['neighbors'] for view in data['views']))
        self.assertEqual(data['unlocated_count'], 2)

    def test_best_view_uses_visible_failures_and_missing_neighborhood_coverage(self):
        poor = self.view('poor.csv', [(0, .1, .1)])
        useful = self.view('useful.csv', [(0, .1, .1), (3, .2, .1)])
        data = visual.build_data([poor, useful], range(4), self.candidate([0]))
        self.assertEqual(data['best_view'], str(useful))
        self.assertEqual(data['views'][1]['visible_unreconstructed'], 1)
        self.assertEqual(data['views'][1]['neighbor_missing_count'], 2)

    def test_bad_coordinates_duplicate_ids_extra_columns_and_unknown_ids_rejected(self):
        path = self.root / 'bad.csv'
        for body in ('index,u,v\n0,nan,.1\n', 'index,u,v\n0,1.1,.1\n',
                     'index,u,v\n0,.1,.1\n0,.2,.2\n', 'index,u,v\n0,.1,.1,extra\n',
                     'index,u,v\n1,.1,.1\n', 'index,u,v\n', 'index,u,v\n-1,.1,.1\n'):
            with self.subTest(body=body):
                path.write_text(body)
                with self.assertRaises(ScanSessionError):
                    visual.build_data([path], [0])

    def test_candidate_must_have_unique_finite_expected_measurements(self):
        path = self.view('view.csv', [(0, .1, .1)])
        candidate = self.candidate([0])
        for body in ('index,x,y,z\n0,inf,0,0\n', 'index,x,y,z\n0,0,0,0\n0,1,1,1\n',
                     'index,x,y,z\n1,0,0,0\n'):
            candidate.write_text(body)
            with self.assertRaises(ScanSessionError):
                visual.build_data([path], [0], candidate)

    def test_bounds_and_empty_view_selection(self):
        data = visual.build_data([], [0, 1])
        self.assertIsNone(data['best_view'])
        self.assertEqual(data['unlocated_ids'], [0, 1])
        with self.assertRaises(ScanSessionError):
            visual.build_data([], [True])
        path = self.view('view.csv', [(0, .1, .1)])
        with patch.object(visual, 'MAX_FILE_BYTES', 2), self.assertRaises(ScanSessionError):
            visual.build_data([path], [0])
        with patch.object(visual, 'MAX_IDS', 1), self.assertRaises(ScanSessionError):
            visual.build_data([], [0, 1])

    def test_session_provenance_and_candidate_identity_are_checked(self):
        state = session({'name': 'Test', 'target': '192.0.2.1', 'interface': '192.0.2.2',
                         'universe': 1, 'count': 2, 'rate': 30, 'order': 'RGB'})
        path = self.view('view.csv', [(0, .1, .1)])
        candidate = self.candidate([0])
        report = self.root / 'quality_pending.json'
        report.write_text(json.dumps({'session_id': state.session_id, 'reconstructed_ids': [0]}))
        with patch('pixelblaze_mapper.scan_library.verified_view_paths') as verify:
            data = visual.build_data([path, path], [0, 1], candidate, state.to_dict())
            verify.assert_called_once_with([path], state)
            self.assertEqual(data['reconstructed_count'], 1)
            report.write_text(json.dumps({'session_id': 'another', 'reconstructed_ids': [0]}))
            with self.assertRaisesRegex(ScanSessionError, 'identity'):
                visual.build_data([path], [0, 1], candidate, state)
        with patch('pixelblaze_mapper.scan_library.verified_view_paths', side_effect=ScanSessionError('wrong view')):
            with self.assertRaisesRegex(ScanSessionError, 'wrong view'):
                visual.build_data([path], [0, 1], session=state)


if __name__ == '__main__':
    unittest.main()
