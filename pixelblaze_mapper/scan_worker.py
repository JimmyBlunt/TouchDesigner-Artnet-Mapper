"""Explicit offline MariMapper worker; default CLI action only prints a plan.

No camera/backend imports, device selection, UDP, live capture or layout apply.
Native reconstruction is opt-in and runs only when this CLI is invoked in the
separately configured MariMapper Python. Source files are hash-checked; output
must be a NEW child directory. This module never installs dependencies.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from .scan_session import ScanSession, ScanSessionError, Stage


WORKER_SCHEMA = "pixelblaze-marimapper-offline-worker"
UPSTREAM_REVISION = "7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa"
CAMERA_MODELS = ("camera_model_pinhole", "camera_model_radial",
                 "camera_model_opencv", "camera_model_opencv_full")
DEFAULT_CAMERA_MODEL = "camera_model_radial"  # Preserve original sfm() default.


def _inside(path, roots):
    return any(path == root or root in path.parents for root in roots)


def create_manifest(session, *, views, source_roots, workspace_root, output_directory,
                    camera_model=DEFAULT_CAMERA_MODEL):
    """Create a plan without I/O writes or native imports.

    camera_model is a reviewed MariMapper model NAME, not arbitrary Python code.
    Interpolation remains disabled: native gap filling assumes rescaled LED
    spacing, unlike this worker's raw SfM coordinates and explicit sparse scope.
    """
    if type(camera_model) is not str or camera_model not in CAMERA_MODELS:
        raise ScanSessionError("unsupported MariMapper camera model")
    if not isinstance(session, ScanSession) or session.stage != Stage.RECONSTRUCTING:
        raise ScanSessionError("worker needs a reconstruction-requested session")
    roots = tuple(Path(root).resolve(strict=True) for root in source_roots)
    workspace = Path(workspace_root).resolve(strict=True)
    output = Path(output_directory).resolve()
    if not roots or not workspace.is_dir() or not all(root.is_dir() for root in roots):
        raise ScanSessionError("approved roots and workspace must be existing directories")
    if output == workspace or workspace not in output.parents or output.exists() or not output.parent.is_dir():
        raise ScanSessionError("output must be a NEW child directory of the workspace")
    known_views = {view.view_id for view in session.views}
    if set(views) != known_views:
        raise ScanSessionError("every completed view requires exactly one input CSV")
    inputs = []
    for view_id, filename in views.items():
        path = Path(filename).resolve(strict=True)
        if not _inside(path, roots) or path.suffix.lower() != ".csv" or not path.is_file():
            raise ScanSessionError("view CSV is outside approved source roots")
        data = path.read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        reader = csv.DictReader(lines)
        if reader.fieldnames != ["index", "u", "v"]:
            raise ScanSessionError("expected MariMapper 2D index,u,v CSV, not a 3D/JSON map")
        inputs.append({"view_id": view_id, "path": str(path), "sha256": sha256(data).hexdigest()})
    return {
        "schema": WORKER_SCHEMA, "version": 1, "upstream_revision": UPSTREAM_REVISION,
        "session": session.to_dict(), "source_roots": [str(root) for root in roots],
        "workspace_root": str(workspace), "output_directory": str(output), "inputs": inputs,
        "reconstruction": {"camera_model": camera_model, "interpolation": False},
        "capabilities": {"offline_reconstruction": True, "camera_capture": False,
                         "hardware_output": False, "registration": False, "layout_apply": False},
    }


def validate_manifest(document):
    if document.get("schema") != WORKER_SCHEMA or document.get("version") != 1:
        raise ScanSessionError("unsupported worker manifest schema")
    if document.get("upstream_revision") != UPSTREAM_REVISION:
        raise ScanSessionError("worker manifest targets an unreviewed MariMapper revision")
    # Old schema-1 manifests omitted this section and used sfm's radial default.
    options = document.get("reconstruction", {})
    if not isinstance(options, dict) or set(options) - {"camera_model", "interpolation"}:
        raise ScanSessionError("unsupported reconstruction options; interpolation is not implemented")
    if options.get("interpolation", False) is not False:
        raise ScanSessionError("interpolation is not implemented for raw SfM candidates")
    session = ScanSession.from_dict(document["session"])
    inputs = document["inputs"]
    if len({item["view_id"] for item in inputs}) != len(inputs):
        raise ScanSessionError("duplicate input view ID")
    checked = create_manifest(session, views={item["view_id"]: item["path"] for item in inputs},
                              source_roots=document["source_roots"],
                              workspace_root=document["workspace_root"],
                              output_directory=document["output_directory"],
                              camera_model=options.get("camera_model", DEFAULT_CAMERA_MODEL))
    stamps = {item["view_id"]: item["sha256"] for item in inputs}
    if any(stamps[item["view_id"]] != item["sha256"] for item in checked["inputs"]):
        raise ScanSessionError("input changed after manifest creation")
    return checked


def load_observations(document):
    """Parse validated observations without importing native libraries.

    CSV index means physical/source index for this explicit manifest. No dense
    renumbering: selected source indices plus anchors are the ONLY accepted IDs.
    A file containing any extra LED fails instead of silently expanding scope.
    """
    checked = validate_manifest(document)
    session = ScanSession.from_dict(checked["session"])
    target_by_source = {target.source_index: target.led_id for target in session.targets
                        if target.led_id in session.capture_ids}
    from math import isfinite
    result = []
    for view_index, item in enumerate(checked["inputs"]):
        seen = set()
        detected = set()
        # Decode already hash-checked bytes again; compare the bytes used to
        # reconstruct too, so changing a file between reads fails closed.
        data = Path(item["path"]).read_bytes()
        if sha256(data).hexdigest() != item["sha256"]:
            raise ScanSessionError("input changed while observations were read")
        for row in csv.DictReader(data.decode("utf-8-sig").splitlines()):
            if None in row or any(value is None for value in row.values()):
                raise ScanSessionError("malformed 2D observation column count")
            try:
                source_index = int(row["index"])
                u, v = float(row["u"]), float(row["v"])
            except (ValueError, TypeError, KeyError) as error:
                raise ScanSessionError("malformed 2D observation") from error
            if source_index not in target_by_source or source_index in seen or not all(map(isfinite, (u, v))):
                raise ScanSessionError("duplicate, nonfinite or outside-scope observation")
            seen.add(source_index)
            detected.add(target_by_source[source_index])
            result.append((source_index, view_index, u, v))
        evidence = next(view for view in session.views if view.view_id == item["view_id"])
        if detected != set(evidence.detected_ids):
            raise ScanSessionError("CSV detections differ from completed view evidence")
    return checked, tuple(result)


def reconstruct(document, *, confirmed=False):
    """Run real SfM only when explicitly called; no interpolation/registration.

    Native imports are delayed until after safety validation and confirmation.
    The dependency/version check uses installed package metadata, never launchers.
    """
    if confirmed is not True:
        raise ScanSessionError("explicit offline reconstruction confirmation required")
    checked, rows = load_observations(document)
    from importlib import metadata
    if metadata.version("marimapper") != "3.4.2" or metadata.version("pycolmap") != "3.11.1":
        raise ScanSessionError("unreviewed MariMapper/pycolmap version")
    dist = metadata.distribution("marimapper")
    origin = json.loads(dist.read_text("direct_url.json") or "{}")
    if origin.get("vcs_info", {}).get("commit_id") != UPSTREAM_REVISION:
        raise ScanSessionError("installed MariMapper commit is not the reviewed revision")
    from marimapper.led import LED2D, Point2D
    from marimapper.sfm import sfm
    from marimapper.database_populator import camera_models
    from marimapper.file_tools import write_3d_leds_to_file
    detections = [LED2D(index, view, Point2D(u, v)) for index, view, u, v in rows]
    model_name = checked["reconstruction"]["camera_model"]
    model = next((model for model in camera_models if model.__name__ == model_name), None)
    if model is None:
        raise ScanSessionError("reviewed camera model is unavailable in native installation")
    points = sfm(detections, camera_model=model)
    if not points:
        raise ScanSessionError("SfM returned no reconstruction; add valid overlapping views")
    allowed = {row[0] for row in rows}
    if any(point.led_id not in allowed for point in points):
        raise ScanSessionError("reconstructor returned an outside-scope ID")
    from math import isfinite
    if len({point.led_id for point in points}) != len(points) or any(
        not all(isfinite(float(value)) for value in point.point.position) for point in points
    ):
        raise ScanSessionError("reconstructor returned duplicate/nonfinite points")
    output = Path(checked["output_directory"])
    # Atomic directory reservation rejects existing results, including a race.
    output.mkdir(parents=False, exist_ok=False)
    write_3d_leds_to_file(points, output / "candidate_3d.csv")
    report = {
        "session_id": checked["session"]["session_id"], "upstream_revision": UPSTREAM_REVISION,
        # COLMAP returns NumPy integer scalars; JSON requires builtin integers.
        "input_observations": len(rows), "reconstructed_ids": sorted(int(point.led_id) for point in points),
        "camera_model": model_name, "interpolated_ids": [],
        "interpolation": False, "normal_estimation": False, "registration": False,
        "coordinate_units": "arbitrary_sfm", "review_required": True,
        "camera_used": False, "hardware_output_used": False, "layout_applied": False,
    }
    (output / "quality_pending.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--confirm-offline-reconstruction", action="store_true")
    args = parser.parse_args(argv)
    document = json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.confirm_offline_reconstruction:
        result = reconstruct(document, confirmed=True)
    else:
        checked, rows = load_observations(document)
        result = {"dry_run": True, "observations": len(rows),
                  "output_directory": checked["output_directory"], "capabilities": checked["capabilities"],
                  "reconstruction": checked["reconstruction"]}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
