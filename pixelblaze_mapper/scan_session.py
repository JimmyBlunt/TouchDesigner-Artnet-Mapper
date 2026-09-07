"""Offline guided-scan plans and staged, identity-preserving merge requests.

This module does not scan, reconstruct, register coordinates, control a camera,
send patterns, acquire an output lease, or apply a layout. Every pattern is a
dry-run descriptor. Evidence references are caller-supplied provenance, not
proof verified by this module. Device adapters must independently authorize and
validate acquisition, and the layout consumer must check the scene revision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from math import isfinite


class ScanSessionError(ValueError):
    """An invalid transition or unsafe/ambiguous identity contract."""


class Stage(str, Enum):
    PLANNED = "planned"
    CAPTURING = "capturing"
    RECONSTRUCTING = "reconstructing"
    REVIEW = "review"
    MERGE_REQUESTED = "merge_requested"
    CANCELLED = "cancelled"
    FAILED = "failed"


def _text(value, field):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ScanSessionError(f"{field} must be a non-empty trimmed string")
    return value


def _index(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ScanSessionError(f"{field} must be a non-negative integer")
    return value


def _ids(values, field, *, allow_empty=False):
    result = tuple(_text(value, field) for value in values)
    if len(set(result)) != len(result) or (not result and not allow_empty):
        raise ScanSessionError(f"{field} must be non-empty and unique")
    return result


@dataclass(frozen=True)
class ScanTarget:
    led_id: str
    object_id: str
    local_index: int
    source_index: int

    def __post_init__(self):
        _text(self.led_id, "led_id")
        _text(self.object_id, "object_id")
        _index(self.local_index, "local_index")
        _index(self.source_index, "source_index")


@dataclass(frozen=True)
class PatternStep:
    """A proposed step, never a packet or device command.

    ``dark`` means request blackout of the explicitly leased scan domain, not
    a blind broadcast. ``observe`` keeps the same target on until capture ack.
    """

    action: str
    led_id: str | None
    source_index: int | None
    brightness: float
    settle_ms: int
    dry_run: bool = True


@dataclass(frozen=True)
class ViewEvidence:
    view_id: str
    detected_ids: tuple[str, ...]
    observation_reference: str

    def __post_init__(self):
        _text(self.view_id, "view_id")
        object.__setattr__(self, "detected_ids", _ids(self.detected_ids, "detected_ids", allow_empty=True))
        _text(self.observation_reference, "observation_reference")


@dataclass(frozen=True)
class CandidatePoint:
    """An externally produced scan slot; zero XYZ is not treated as missing."""

    led_id: str
    scan_index: int
    provenance: str = "reconstructed"

    def __post_init__(self):
        _text(self.led_id, "led_id")
        _index(self.scan_index, "scan_index")
        if self.provenance not in ("reconstructed", "interpolated", "unknown"):
            raise ScanSessionError("unsupported candidate provenance")


@dataclass(frozen=True)
class Replacement:
    led_id: str
    object_id: str
    local_index: int
    source_index: int
    scan_index: int


@dataclass(frozen=True)
class MergeRequest:
    session_id: str
    scene_id: str
    expected_scene_revision: str
    scan_id: str
    replacements: tuple[Replacement, ...]
    registration_reference: str
    quality_reference: str
    applies_layout: bool = False

    def replacement_args(self, object_id: str):
        """Arguments for layout_scene.replace_region, after revision validation.

        The caller supplies the reviewed Scan whose explicit registration maps
        raw scan points into this object's ORIGINAL frame. No index reassignment.
        """
        rows = tuple(row for row in self.replacements if row.object_id == object_id)
        if not rows:
            raise ScanSessionError("object has no approved replacements")
        return {
            "object_id": object_id,
            "local_indices": tuple(row.local_index for row in rows),
            "scan_indices": tuple(row.scan_index for row in rows),
        }


@dataclass(frozen=True)
class ScanSession:
    session_id: str
    scene_id: str
    scene_revision: str
    targets: tuple[ScanTarget, ...]
    selected_ids: tuple[str, ...]
    anchor_ids: tuple[str, ...] = ()
    stage: Stage = Stage.PLANNED
    views: tuple[ViewEvidence, ...] = ()
    active_view: str | None = None
    candidate_scan_id: str | None = None
    candidates: tuple[CandidatePoint, ...] = ()
    registration_reference: str | None = None
    quality_reference: str | None = None
    failure_reason: str | None = None

    def __post_init__(self):
        for field in ("session_id", "scene_id", "scene_revision"):
            _text(getattr(self, field), field)
        object.__setattr__(self, "stage", Stage(self.stage))
        object.__setattr__(self, "targets", tuple(self.targets))
        object.__setattr__(self, "views", tuple(self.views))
        object.__setattr__(self, "candidates", tuple(self.candidates))
        if not self.targets or any(not isinstance(t, ScanTarget) for t in self.targets):
            raise ScanSessionError("targets must contain ScanTarget entries")
        ids = _ids((t.led_id for t in self.targets), "target IDs")
        if len({t.source_index for t in self.targets}) != len(self.targets):
            raise ScanSessionError("two target IDs cannot own the same source index")
        if len({(t.object_id, t.local_index) for t in self.targets}) != len(self.targets):
            raise ScanSessionError("two target IDs cannot own one object-local index")
        selected = _ids(self.selected_ids, "selected_ids")
        anchors = _ids(self.anchor_ids, "anchor_ids", allow_empty=True)
        if not set(selected + anchors) <= set(ids) or set(selected) & set(anchors):
            raise ScanSessionError("selected/anchor IDs must be known and disjoint")
        if len({t.object_id for t in self.targets if t.led_id in selected}) != 1:
            raise ScanSessionError("one session reviews one object's original frame; split multi-object merges")
        object.__setattr__(self, "selected_ids", selected)
        object.__setattr__(self, "anchor_ids", anchors)
        if any(not isinstance(v, ViewEvidence) for v in self.views):
            raise ScanSessionError("views must contain ViewEvidence")
        if len({v.view_id for v in self.views}) != len(self.views):
            raise ScanSessionError("view IDs must be unique")
        if any(not set(v.detected_ids) <= set(self.capture_ids) for v in self.views):
            raise ScanSessionError("view contains IDs outside this scan scope")
        if self.stage in (Stage.RECONSTRUCTING, Stage.REVIEW, Stage.MERGE_REQUESTED):
            if len(self.views) < 2 or not any(
                sum(led_id in v.detected_ids for v in self.views) >= 2 for led_id in selected
            ):
                raise ScanSessionError("reconstruction state requires completed multi-view evidence")
        if self.stage == Stage.CAPTURING:
            _text(self.active_view, "active_view")
            if self.active_view in {v.view_id for v in self.views}:
                raise ScanSessionError("active view already completed")
        elif self.active_view is not None:
            raise ScanSessionError("only a capturing session may have an active view")
        if any(not isinstance(c, CandidatePoint) for c in self.candidates):
            raise ScanSessionError("candidates must contain CandidatePoint")
        if len({c.led_id for c in self.candidates}) != len(self.candidates):
            raise ScanSessionError("candidate LED IDs must be unique")
        if len({c.scan_index for c in self.candidates}) != len(self.candidates):
            raise ScanSessionError("candidate scan slots must be unique")
        if not {c.led_id for c in self.candidates} <= set(self.capture_ids):
            raise ScanSessionError("candidate contains IDs outside this scan scope")
        if self.stage in (Stage.REVIEW, Stage.MERGE_REQUESTED):
            for field in ("candidate_scan_id", "registration_reference", "quality_reference"):
                _text(getattr(self, field), field)
            if not self.candidates:
                raise ScanSessionError("review requires externally produced candidates")

    @property
    def capture_ids(self):
        """Explicit scan domain: selected replacements plus read-only anchors."""
        return self.selected_ids + self.anchor_ids

    def dry_run_schedule(self, *, brightness=0.05, settle_ms=150):
        if isinstance(brightness, bool) or not isinstance(brightness, (int, float)) or not isfinite(brightness) or not 0 < brightness <= 0.1:
            raise ScanSessionError("dry-run brightness must be finite and within (0, 0.1]")
        _index(settle_ms, "settle_ms")
        if settle_ms == 0:
            raise ScanSessionError("settle_ms must be positive")
        lookup = {target.led_id: target for target in self.targets}
        steps = [PatternStep("dark", None, None, 0.0, settle_ms)]
        for led_id in self.capture_ids:
            target = lookup[led_id]
            for action, level in (("illuminate", brightness), ("observe", brightness), ("dark", 0.0)):
                steps.append(PatternStep(action, led_id, target.source_index, level, settle_ms))
        return tuple(steps)

    def start_view(self, view_id: str):
        self._require(Stage.PLANNED)
        _text(view_id, "view_id")
        if view_id in {view.view_id for view in self.views}:
            raise ScanSessionError("view ID already completed")
        return replace(self, stage=Stage.CAPTURING, active_view=view_id)

    def finish_view(self, detected_ids, observation_reference: str):
        self._require(Stage.CAPTURING)
        view = ViewEvidence(self.active_view, tuple(detected_ids), observation_reference)
        return replace(self, stage=Stage.PLANNED, active_view=None, views=self.views + (view,))

    def request_reconstruction(self):
        self._require(Stage.PLANNED)
        if len(self.views) < 2:
            raise ScanSessionError("3D reconstruction requires at least two completed views")
        if not any(sum(led_id in v.detected_ids for v in self.views) >= 2 for led_id in self.selected_ids):
            raise ScanSessionError("no selected LED has correspondence in two views")
        # This is necessary, not sufficient for COLMAP initialization/success.
        return replace(self, stage=Stage.RECONSTRUCTING)

    def stage_candidate(self, scan_id, candidates, *, registration_reference, quality_reference):
        self._require(Stage.RECONSTRUCTING)
        return replace(self, stage=Stage.REVIEW, candidate_scan_id=scan_id,
                       candidates=tuple(candidates), registration_reference=registration_reference,
                       quality_reference=quality_reference)

    def request_merge(self, accepted_ids, *, current_scene_revision, allow_interpolated=False):
        self._require(Stage.REVIEW)
        if current_scene_revision != self.scene_revision:
            raise ScanSessionError("scene changed since scan planning; rebase/review explicitly")
        accepted = _ids(accepted_ids, "accepted_ids")
        lookup = {candidate.led_id: candidate for candidate in self.candidates}
        if not set(accepted) <= set(self.selected_ids) or not set(accepted) <= set(lookup):
            raise ScanSessionError("merge IDs must be selected, reconstructed candidates; anchors cannot merge")
        if type(allow_interpolated) is not bool:
            raise ScanSessionError("allow_interpolated must be an explicit boolean")
        allowed = {"reconstructed", "interpolated"} if allow_interpolated else {"reconstructed"}
        if any(lookup[led_id].provenance not in allowed for led_id in accepted):
            raise ScanSessionError("unknown/interpolated provenance is not approved")
        targets = {target.led_id: target for target in self.targets}
        rows = tuple(Replacement(led_id, targets[led_id].object_id, targets[led_id].local_index,
                                 targets[led_id].source_index, lookup[led_id].scan_index)
                     for led_id in accepted)
        request = MergeRequest(self.session_id, self.scene_id, self.scene_revision,
                               self.candidate_scan_id, rows, self.registration_reference,
                               self.quality_reference)
        return replace(self, stage=Stage.MERGE_REQUESTED), request

    def cancel(self):
        self._require(Stage.PLANNED, Stage.CAPTURING, Stage.RECONSTRUCTING, Stage.REVIEW)
        return replace(self, stage=Stage.CANCELLED, active_view=None)

    def fail(self, reason):
        self._require(Stage.PLANNED, Stage.CAPTURING, Stage.RECONSTRUCTING, Stage.REVIEW)
        return replace(self, stage=Stage.FAILED, active_view=None, failure_reason=_text(reason, "reason"))

    def _require(self, *stages):
        if self.stage not in stages:
            raise ScanSessionError(f"transition invalid from {self.stage.value}")

    def to_dict(self):
        document = asdict(self)
        document["stage"] = self.stage.value
        return {"schema": "pixelblaze-scan-session", "version": 1, **document}

    @classmethod
    def from_dict(cls, document):
        data = dict(document)
        if data.pop("schema", None) != "pixelblaze-scan-session" or data.pop("version", None) != 1:
            raise ScanSessionError("unsupported scan session schema/version; not MariMapper JSON")
        data["targets"] = tuple(ScanTarget(**target) for target in data.get("targets", ()))
        data["views"] = tuple(ViewEvidence(**view) for view in data.get("views", ()))
        data["candidates"] = tuple(CandidatePoint(**point) for point in data.get("candidates", ()))
        return cls(**data)
