"""Offline scan lifecycle tests; no optional/native libraries or devices."""

from dataclasses import FrozenInstanceError, replace
import json
import unittest

from pixelblaze_mapper.scan_session import (
    CandidatePoint, ScanSession, ScanSessionError, ScanTarget, Stage,
)


def session():
    return ScanSession(
        "session-a", "scene-a", "revision-sha-a",
        (ScanTarget("led-10", "object-a", 4, 10),
         ScanTarget("led-42", "object-a", 8, 42),
         ScanTarget("anchor-99", "object-b", 0, 99)),
        ("led-42", "led-10"), ("anchor-99",),
    )


def reconstructed():
    state = session()
    for number in range(2):
        state = state.start_view(f"view-{number}").finish_view(
            ("led-10", "led-42", "anchor-99"), f"observations-{number}.csv#sha"
        )
    return state.request_reconstruction()


def review(points=None):
    return reconstructed().stage_candidate(
        "scan-b", points or (CandidatePoint("led-10", 7), CandidatePoint("led-42", 3)),
        registration_reference="registration-to-original-object-frame#sha",
        quality_reference="reviewed-reprojection-report#sha",
    )


class ScanSessionTests(unittest.TestCase):
    def test_schedule_is_explicit_sparse_and_dry_run_only(self):
        state = session()
        steps = state.dry_run_schedule()
        self.assertEqual(len(steps), 10)
        self.assertEqual(steps[0].action, "dark")
        self.assertEqual(steps[-1].action, "dark")
        self.assertEqual([s.source_index for s in steps if s.action == "illuminate"], [42, 10, 99])
        self.assertEqual([s.led_id for s in steps if s.action == "observe"], list(state.capture_ids))
        self.assertTrue(all(s.dry_run for s in steps))
        self.assertEqual(state.stage, Stage.PLANNED)

    def test_pattern_limits_do_not_silently_coerce(self):
        for value in (0, -1, 0.11, float("nan"), float("inf"), True, "0.05"):
            with self.subTest(value=value), self.assertRaises(ScanSessionError):
                session().dry_run_schedule(brightness=value)
        for value in (0, -1, 1.1, True):
            with self.subTest(value=value), self.assertRaises(ScanSessionError):
                session().dry_run_schedule(settle_ms=value)

    def test_duplicate_or_unknown_scope_fails(self):
        for fields in (
            {"selected_ids": ()}, {"selected_ids": ("led-10", "led-10")},
            {"selected_ids": ("absent",)}, {"anchor_ids": ("led-10",)},
            {"anchor_ids": ("absent",)},
            {"selected_ids": ("led-10", "anchor-99"), "anchor_ids": ()},
        ):
            with self.subTest(fields=fields), self.assertRaises(ScanSessionError):
                replace(session(), **fields)

    def test_source_and_local_ownership_are_unique(self):
        base = session()
        for target in (ScanTarget("extra", "other", 0, 10),
                       ScanTarget("extra", "object-a", 4, 98)):
            with self.assertRaises(ScanSessionError):
                replace(base, targets=base.targets + (target,))
        for value in (-1, True, 1.5):
            with self.assertRaises(ScanSessionError):
                ScanTarget("bad", "object", 0, value)

    def test_no_implicit_reconstruction_or_missing_views(self):
        with self.assertRaises(ScanSessionError):
            session().request_reconstruction()
        state = session().start_view("v1").finish_view(("led-10",), "one.csv")
        with self.assertRaises(ScanSessionError):
            state.request_reconstruction()
        state = state.start_view("v2").finish_view(("led-42",), "two.csv")
        with self.assertRaises(ScanSessionError):
            state.request_reconstruction()

    def test_capture_scope_and_view_identity_are_checked(self):
        state = session().start_view("v1")
        with self.assertRaises(ScanSessionError):
            state.finish_view(("unknown",), "view.csv")
        state = state.finish_view((), "empty-view.csv")
        self.assertEqual(state.views[0].detected_ids, ())
        with self.assertRaises(ScanSessionError):
            state.start_view("v1")

    def test_merge_is_only_a_request_and_preserves_ids(self):
        state = review()
        updated, request = state.request_merge(("led-42", "led-10"), current_scene_revision="revision-sha-a")
        self.assertEqual(state.stage, Stage.REVIEW)
        self.assertEqual(updated.stage, Stage.MERGE_REQUESTED)
        self.assertFalse(request.applies_layout)
        self.assertEqual([r.led_id for r in request.replacements], ["led-42", "led-10"])
        self.assertEqual([r.source_index for r in request.replacements], [42, 10])
        self.assertEqual(request.replacement_args("object-a"),
                         {"object_id": "object-a", "local_indices": (8, 4), "scan_indices": (3, 7)})
        with self.assertRaises(ScanSessionError):
            request.replacement_args("object-b")

    def test_partial_acceptance_never_implicitly_fills_missing_ids(self):
        state = review((CandidatePoint("led-42", 8),))
        _, request = state.request_merge(("led-42",), current_scene_revision="revision-sha-a")
        self.assertEqual(len(request.replacements), 1)
        with self.assertRaises(ScanSessionError):
            state.request_merge(("led-10",), current_scene_revision="revision-sha-a")

    def test_anchor_and_stale_scene_cannot_merge(self):
        state = review((CandidatePoint("led-10", 0), CandidatePoint("anchor-99", 1)))
        with self.assertRaises(ScanSessionError):
            state.request_merge(("anchor-99",), current_scene_revision="revision-sha-a")
        with self.assertRaises(ScanSessionError):
            state.request_merge(("led-10",), current_scene_revision="new-revision")

    def test_registration_and_quality_references_are_required(self):
        for fields in ({"registration_reference": ""}, {"quality_reference": None}):
            with self.subTest(fields=fields), self.assertRaises(ScanSessionError):
                replace(review(), **fields)

    def test_provenance_requires_explicit_interpolation_approval(self):
        state = review((CandidatePoint("led-10", 0, "interpolated"),))
        with self.assertRaises(ScanSessionError):
            state.request_merge(("led-10",), current_scene_revision="revision-sha-a")
        _, request = state.request_merge(("led-10",), current_scene_revision="revision-sha-a", allow_interpolated=True)
        self.assertEqual(len(request.replacements), 1)
        state = review((CandidatePoint("led-10", 0, "unknown"),))
        with self.assertRaises(ScanSessionError):
            state.request_merge(("led-10",), current_scene_revision="revision-sha-a", allow_interpolated=True)

    def test_candidate_aliases_and_unknown_ids_are_rejected(self):
        for points in (
            (CandidatePoint("led-10", 0), CandidatePoint("led-42", 0)),
            (CandidatePoint("led-10", 0), CandidatePoint("led-10", 1)),
            (CandidatePoint("absent", 0),),
        ):
            with self.subTest(points=points), self.assertRaises(ScanSessionError):
                review(points)

    def test_cancellation_and_failure_do_not_mark_success(self):
        base = session().start_view("view")
        for terminal in (base.cancel(), base.fail("camera disconnected")):
            self.assertIsNone(terminal.active_view)
            self.assertNotEqual(terminal.stage, Stage.MERGE_REQUESTED)
            with self.assertRaises(ScanSessionError):
                terminal.start_view("other")
            with self.assertRaises(ScanSessionError):
                terminal.request_merge(("led-10",), current_scene_revision="revision-sha-a")

    def test_json_roundtrip_is_deeply_independent_and_versioned(self):
        state = review()
        document = state.to_dict()
        restored = ScanSession.from_dict(json.loads(json.dumps(document)))
        self.assertEqual(restored, state)
        document["targets"][0]["source_index"] = 123
        self.assertEqual(state.targets[0].source_index, 10)
        with self.assertRaises(ScanSessionError):
            ScanSession.from_dict({**state.to_dict(), "version": 2})
        with self.assertRaises(FrozenInstanceError):
            state.scene_id = "modified"

    def test_persisted_state_cannot_skip_multiview_evidence(self):
        document = review().to_dict()
        document["views"] = []
        with self.assertRaises(ScanSessionError):
            ScanSession.from_dict(document)

    def test_layout_replace_contract_keeps_other_points_and_source_ownership(self):
        from pixelblaze_mapper.layout_scene import Scan, Scene, append_scan, replace_region

        original = Scan("old", "Synthetic fixture", ((0., 0., 0.), (1., 0., 0.)))
        scene = append_scan(Scene("layout", "Test"), original,
                            source_indices=(10, 42), object_id="object-a")
        targets = tuple(ScanTarget(v.led_id, "object-a", v.local_index, v.source_index)
                        for v in scene.object("object-a").leds)
        target_id = targets[1].led_id
        state = ScanSession("s", "layout", "revision", targets, (target_id,))
        for number in range(2):
            state = state.start_view(str(number)).finish_view((target_id,), f"fixture-{number}.csv")
        state = state.request_reconstruction().stage_candidate(
            "new", (CandidatePoint(target_id, 0),), registration_reference="fixture-identity",
            quality_reference="synthetic-test-not-measurement")
        _, request = state.request_merge((target_id,), current_scene_revision="revision")
        candidate = Scan("new", "Synthetic registered fixture", ((2., 0., 0.),))
        updated = replace_region(scene, scan=candidate, **request.replacement_args("object-a"))
        old_leds = scene.object("object-a").leds
        new_leds = updated.object("object-a").leds
        self.assertEqual(old_leds[0], new_leds[0])
        self.assertEqual((new_leds[1].led_id, new_leds[1].source_index), (target_id, 42))
        self.assertEqual(updated.scans[0], original)


if __name__ == "__main__":
    unittest.main()
