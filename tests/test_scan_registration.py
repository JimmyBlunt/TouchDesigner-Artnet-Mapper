"""Known correspondence, quality and immutable partial replacement regression tests."""
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.build_scan_session_ui import plan_scene
from pixelblaze_mapper.layout_scene import Scene, SceneError, Transform, import_scan, new_id, set_transform
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor
from pixelblaze_mapper.scan_registration import fit_similarity, prepare_registration, apply_registration
from pixelblaze_mapper.scan_result_review import inspect_saved_result


class SimilarityTests(unittest.TestCase):
    def test_rotation_scale_translation_and_euler_singularities(self):
        points = [(0., 0., 0.), (2., 0., 0.), (0., 3., 0.), (1., 1., 1.)]
        for rotation in ((31, -42, 123), (0, 180, 0), (41, 90, -27), (41, -90, -27), (180, 0, 0)):
            with self.subTest(rotation=rotation):
                target = Transform((3, 4, 5), rotation, (2, 2, 2))
                fitted, errors = fit_similarity(points, [target.apply(p) for p in points])
                self.assertLess(max(errors), 1e-7)
                self.assertAlmostEqual(fitted.scale[0], 2)
                self.assertEqual(fitted.scale[0], fitted.scale[1])

    def test_random_spatial_rotations_have_independent_point_accuracy(self):
        rng = random.Random(312)
        for _ in range(40):
            points = [tuple(rng.uniform(-5, 5) for _ in range(3)) for _ in range(6)]
            size = rng.uniform(.1, 10)
            truth = Transform(tuple(rng.uniform(-50, 50) for _ in range(3)),
                              tuple(rng.uniform(-180, 180) for _ in range(3)), (size,) * 3)
            fitted, _ = fit_similarity(points[:5], [truth.apply(p) for p in points[:5]])
            for actual, expected in zip(fitted.apply(points[5]), truth.apply(points[5])):
                self.assertAlmostEqual(actual, expected, places=7)

    def test_degenerate_nonfinite_and_mismatched_input_rejected(self):
        good = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        for bad in (good[:2], [(0, 0, 0)] * 3, [(0, 0, 0), (1, 0, 0), (2, 0, 0)],
                    [(0, 0, 0), (1, 0, 0), (2, 1e-9, 0)], [(float('nan'), 0, 0)] * 3):
            with self.subTest(bad=bad), self.assertRaises(SceneError):
                fit_similarity(bad, good)

    def test_reflection_is_not_silently_accepted_as_rotation(self):
        points = [(0, 0, 0), (1, 0, 0), (0, 2, 0), (0, 0, 3)]
        transform, errors = fit_similarity(points, [(-x, y, z) for x, y, z in points])
        self.assertGreater(max(errors), .1)
        self.assertGreater(transform.scale[0], 0)


class RegistrationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'candidate_3d.csv'
        self.points = [(1., 1., 1.), (2., 2., 1.), (0., 0., 0.), (3., 0., 0.), (0., 4., 0.), (0., 0., 5.)]
        self.truth = Transform((3, 4, 5), (31, -42, 123), (2, 2, 2))
        original = [self.truth.apply(p) for p in self.points]
        original[0] = tuple(v + 7 for v in original[0])
        self.editor = LayoutEditor(LayoutDocument(Scene(new_id(), 'draft')))
        self.editor.append(import_scan(json.dumps(original), format='pixelblaze', name='original'), source_start=0)
        self.object_id = self.editor.current.scene.objects[0].object_id
        self.editor.transform(Transform((10, 3, 7), (8, 12, 27), (2, 3, 4), (1, 2, 3)))
        self.before = self.editor.current
        obj = self.before.scene.object(self.object_id)
        self.session = plan_scene(self.before.scene, self.object_id,
            selected_ids=[led.led_id for led in obj.leds[:2]], anchor_ids=[led.led_id for led in obj.leds[2:]])
        for view in ('front', 'side'):
            self.session = self.session.start_view(view).finish_view(self.session.capture_ids, 'explicit-view-' + view)
        self.session = self.session.request_reconstruction()
        self.write_result()
        self.no_socket = patch('socket.socket', side_effect=AssertionError('no output')).start()
        self.no_process = patch('subprocess.Popen', side_effect=AssertionError('no process')).start()
        self.addCleanup(patch.stopall)

    def write_result(self, exclude=()):
        rows = ['index,x,y,z,xn,yn,zn,error']
        for index, point in enumerate(self.points):
            if index not in exclude:
                rows.append(','.join(map(str, (index, *point, 0, 0, 0, .1))))
        self.path.write_text('\n'.join(rows))
        (self.path.parent / 'quality_pending.json').write_text(json.dumps({
            'session_id': self.session.session_id, 'reconstructed_ids': [i for i in range(len(self.points)) if i not in exclude]}))
        self.review = inspect_saved_result(self.path)

    def prepare(self, **kwargs):
        args = dict(fit_source_ids=[2, 3, 4], check_source_ids=[5], accepted_source_ids=[0, 1], max_error=.001)
        args.update(kwargs)
        return prepare_registration(self.before, self.session, self.review, **args)

    def test_partial_replacement_preserves_identity_anchors_originals_and_undo(self):
        proposal = self.prepare(accepted_source_ids=[0])
        self.assertTrue(proposal['passed'])
        self.assertEqual(proposal['preserved_selected_source_ids'], [1])
        after = apply_registration(self.before, self.session, proposal)
        old = self.before.scene.object(self.object_id)
        new = after.scene.object(self.object_id)
        self.assertEqual(old.transform, new.transform)
        self.assertEqual(old.leds[1:], new.leds[1:])
        self.assertEqual((old.leds[0].led_id, old.leds[0].local_index, old.leds[0].source_index),
                         (new.leds[0].led_id, new.leds[0].local_index, new.leds[0].source_index))
        self.assertEqual(after.scene.scans[:-1], self.before.scene.scans)
        self.assertEqual(after.scene.scans[-1].points, tuple(self.points))
        self.assertIn('Registration evidence:', after.scene.scans[-1].warnings[-1])
        self.assertEqual(after.routes, self.before.routes)
        actual = dict((led.source_index, p) for led, p in after.scene.world_points())[0]
        expected = old.transform.apply(self.truth.apply(self.points[0]))
        for a, b in zip(actual, expected): self.assertAlmostEqual(a, b, places=7)
        self.editor.commit(after)
        self.editor.undo()
        self.assertEqual(self.editor.current, self.before)
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()

    def test_missing_points_require_explicit_smaller_replacement(self):
        self.write_result(exclude=(1,))
        with self.assertRaisesRegex(SceneError, 'no reconstructed point'): self.prepare()
        proposal = self.prepare(accepted_source_ids=[0])
        after = apply_registration(self.before, self.session, proposal)
        self.assertEqual(after.scene.objects[0].leds[1], self.before.scene.objects[0].leds[1])
        self.write_result(exclude=(5,))
        with self.assertRaisesRegex(SceneError, 'no reconstructed point'): self.prepare()

    def test_stale_scene_session_or_result_rejected(self):
        proposal = self.prepare()
        changed = replace(self.before, scene=set_transform(self.before.scene, self.object_id, Transform()))
        with self.assertRaisesRegex(SceneError, 'Scene changed'):
            apply_registration(changed, self.session, proposal)
        with self.assertRaisesRegex(SceneError, 'different scan session'):
            apply_registration(self.before, replace(self.session, session_id='other'), proposal)
        self.path.write_text(self.path.read_text().replace('1.0,1.0,1.0', '1.1,1.0,1.0'))
        with self.assertRaisesRegex(SceneError, 'changed'):
            apply_registration(self.before, self.session, proposal)

    def test_tampered_proposal_and_anchor_replacement_blocked(self):
        proposal = self.prepare()
        proposal['transform']['translation'] = [0, 0, 0]
        with self.assertRaisesRegex(SceneError, 'evidence changed'):
            apply_registration(self.before, self.session, proposal)
        with self.assertRaisesRegex(SceneError, 'staged'):
            self.prepare(accepted_source_ids=[2])
        with self.assertRaisesRegex(SceneError, 'separate'):
            self.prepare(check_source_ids=[4])

    def test_independent_wrong_point_fails_quality_and_cannot_commit(self):
        self.points[5] = (50., 50., 50.)
        self.write_result()
        proposal = self.prepare()
        self.assertLess(proposal['fit_rms'], .001)
        self.assertGreater(proposal['check_rms'], 1)
        self.assertFalse(proposal['passed'])
        with self.assertRaisesRegex(SceneError, 'exceeds'):
            apply_registration(self.before, self.session, proposal)

    def test_matching_numbers_with_changed_stable_identity_are_rejected(self):
        targets = list(self.session.targets)
        targets[0], targets[1] = replace(targets[0], led_id=targets[1].led_id), replace(targets[1], led_id=targets[0].led_id)
        mismatched = replace(self.session, targets=tuple(targets))
        with self.assertRaisesRegex(SceneError, 'stable LED identity differs'):
            prepare_registration(self.before, mismatched, self.review,
                fit_source_ids=[2, 3, 4], check_source_ids=[5], accepted_source_ids=[0], max_error=.001)

    def test_missing_reference_and_inadequate_view_evidence_rejected(self):
        scan = self.before.scene.scans[0]
        missing_scene = replace(self.before.scene, scans=(replace(scan, missing_indices=(2,)),))
        missing_document = replace(self.before, scene=missing_scene)
        from pixelblaze_mapper.layout_scene_adapter import scene_revision
        missing_session = replace(self.session, scene_revision=scene_revision(missing_scene))
        with self.assertRaisesRegex(SceneError, 'missing placeholder'):
            prepare_registration(missing_document, missing_session, self.review,
                fit_source_ids=[2, 3, 4], check_source_ids=[5], accepted_source_ids=[0], max_error=.001)
        views = list(self.session.views)
        views[0] = replace(views[0], detected_ids=tuple(i for i in views[0].detected_ids if i != self.session.anchor_ids[-1]))
        insufficient = replace(self.session, views=tuple(views))
        with self.assertRaisesRegex(SceneError, 'at least two views'):
            prepare_registration(self.before, insufficient, self.review,
                fit_source_ids=[2, 3, 4], check_source_ids=[5], accepted_source_ids=[0], max_error=.001)

    def test_ui_calculation_cancel_recheck_and_one_undoable_commit(self):
        from tests.test_guided_scan_live import Owner
        from pixelblaze_mapper import scan_registration_ui as ui
        owner, panel, layout_owner = Owner(), Owner(), Owner()
        panel.openViewer = lambda: None
        owner.children['registration_panel'] = panel
        owner.store('session', self.session.to_dict())
        owner.store('result_review', self.review)
        for name, value in (('fit_ids', '2,3,4'), ('check_ids', '5'), ('accepted_ids', '0'), ('max_error', '.001')):
            panel.children[name + '/string'] = SimpleNamespace(text=value)
        for name in ('status', 'summary'):
            panel.children[name] = SimpleNamespace(par=SimpleNamespace(text=''))
        for name in ('registration_evidence', 'registration_comparison'):
            owner.children[name] = SimpleNamespace(text='', openViewer=lambda: None)
        layout_owner.children['ui_panel'] = SimpleNamespace(openViewer=lambda: None)
        lookup = lambda path: owner if path == ui.OWNER else layout_owner
        with patch('pixelblaze_mapper.layout_scene_td.editor', return_value=self.editor), \
             patch('pixelblaze_mapper.layout_scene_td.refresh'), \
             patch('pixelblaze_mapper.layout_scene_td.frame_view'), \
             patch('pixelblaze_mapper.layout_scene_td.status'), \
             patch('pixelblaze_mapper.layout_fixture_td.action'):
            self.assertTrue(ui.act(lookup, 'calculate'))
            self.assertIn('independent check RMS', panel.op('summary').par.text)
            self.assertIn('world_displacement', owner.op('registration_comparison').text)
            self.assertEqual(self.editor.current, self.before)
            self.assertFalse(ui.act(lookup, 'replace', lambda message: False))
            self.assertEqual(self.editor.current, self.before)
            def changed_during_confirmation(message):
                panel.op('accepted_ids/string').text = '0,1'
                return True
            self.assertFalse(ui.act(lookup, 'replace', changed_during_confirmation))
            self.assertEqual(self.editor.current, self.before)
            panel.op('accepted_ids/string').text = '0'
            self.assertTrue(ui.act(lookup, 'replace', lambda message: True))
            self.assertNotEqual(self.editor.current, self.before)
            self.editor.undo()
            self.assertEqual(self.editor.current, self.before)
