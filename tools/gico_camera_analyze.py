"""Calibrate GICO marker ROIs and conservatively analyze a recorded video."""
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixelblaze_mapper import gico_camera_benchmark as bench


def sample(image, xy, radius=2):
    import numpy as np
    x, y = (round(v) for v in xy)
    patch = image[max(0, y-radius):y+radius+1, max(0, x-radius):x+radius+1]
    if not patch.size:
        raise ValueError("Marker ROI is outside the video")
    return float(np.percentile(patch.mean(axis=2), 90))


def frame_at(cap, seconds):
    import cv2
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds*1000)
    ok, frame = cap.read()
    actual = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
    if not ok or abs(actual-seconds) > .25:
        raise ValueError("Cannot seek to calibration timestamp %.3fs (actual %.3fs)" % (seconds, actual))
    return frame


def calibrate(args, report):
    import cv2
    import numpy as np
    phases = {p["name"]: p for p in report["phases"]}
    def midpoint(name):
        phase = phases[name]
        return args.video_zero + (phase["start"]+phase["end"])/2*args.time_scale
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise ValueError("Cannot open video")
    try:
        all_on = frame_at(cap, midpoint("all_on"))
        dark = frame_at(cap, midpoint("black_reference"))
        if args.regions:
            regions = json.loads(args.regions.read_text(encoding="utf-8"))
        else:
            print("Draw one rectangle per visible panel, in side_1 / side_2 / side_3 order. SPACE accepts a rectangle; ENTER finishes.")
            rectangles = cv2.selectROIs("Panel regions - SPACE accept / ENTER finish", all_on, False, False)
            cv2.destroyAllWindows()
            if not 1 <= len(rectangles) <= 3:
                raise ValueError("Select 1..3 panel rectangles")
            regions = [{"name": bench.PANELS[i][0], "rect": [int(v) for v in rect]}
                       for i, rect in enumerate(rectangles)]
        if not regions or len(regions) > 3:
            raise ValueError("Select 1..3 panel rectangles")
        allowed = {p[0] for p in bench.PANELS}
        if len({r["name"] for r in regions}) != len(regions) or any(r["name"] not in allowed for r in regions):
            raise ValueError("Region names must be unique side_1, side_2, side_3")
        result = {"schema": 1, "video": str(args.video.resolve()), "video_zero": args.video_zero,
                  "time_scale": args.time_scale, "time_basis": args.time_basis,
                  "size": [all_on.shape[1], all_on.shape[0]], "panels": []}
        for region in regions:
            x, y, w, h = map(int, region["rect"])
            if min(x, y) < 0 or min(w, h) < 5 or x+w > all_on.shape[1] or y+h > all_on.shape[0]:
                raise ValueError("Invalid panel rectangle")
            coords = []; low = []; high = []
            for marker in range(bench.MARKERS):
                frame = frame_at(cap, midpoint("marker_%02d" % marker))
                difference = np.maximum(frame.astype(float)-dark.astype(float), 0).mean(axis=2)
                crop = difference[y:y+h, x:x+w]
                smoothed = cv2.GaussianBlur(crop, (3, 3), 0)
                py, px = np.unravel_index(smoothed.argmax(), smoothed.shape)
                xy = [int(px+x), int(py+y)]
                if any(math.dist(xy, old) < 4 for old in coords):
                    raise ValueError("Repeated marker location in %s; check timing, rectangle and camera exposure" % region["name"])
                off = sample(dark, xy); on = sample(frame, xy)
                if on-off < 15:
                    raise ValueError("Insufficient marker contrast in %s marker %d" % (region["name"], marker))
                coords.append(xy); low.append(off); high.append(on)
            result["panels"].append({"name": region["name"], "rect": [x,y,w,h],
                "xy": coords, "low": low, "high": high, "radius": 2})
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "calibration.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        overlay = all_on.copy()
        for panel in result["panels"]:
            for index, xy in enumerate(panel["xy"]):
                cv2.circle(overlay, tuple(xy), 6, (0,255,0), 1)
                cv2.putText(overlay, str(index), (xy[0]+6, xy[1]), cv2.FONT_HERSHEY_SIMPLEX, .45, (0,255,0), 1)
        cv2.imwrite(str(args.output / "calibration-review.png"), overlay)
        print("Calibration ready. Review calibration-review.png before interpreting measurements.")
    finally:
        cap.release()


def analyze(args, report):
    import cv2
    calibration = json.loads(args.calibration.read_text(encoding="utf-8"))
    if calibration["time_basis"] not in ("original_realtime_pts", "constant_slow_motion_verified"):
        raise ValueError("Unknown capture time basis; FPS results would be misleading")
    scale = calibration["time_scale"]
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid timestamp scale")
    if str(args.video.resolve()) != calibration["video"]:
        raise ValueError("Calibration belongs to a different video; recalibrate this recording")
    phases = [p for p in report["phases"] if p["name"].startswith("measure_")]
    if not phases:
        raise ValueError("Run has no measurement phases")
    samples = {p["name"]: {r["name"]: [] for r in calibration["panels"]} for p in phases}
    reasons = {p["name"]: Counter() for p in phases}
    cross = {p["name"]: {"all_selected_panels_valid": 0, "different_ids": 0} for p in phases}
    args.output.mkdir(parents=True, exist_ok=False)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise ValueError("Cannot open video")
    previous_pts = None
    decoded_frames = 0
    try:
        with (args.output / "decoded-samples.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(["video_pts_s", "capture_s", "phase", "panel", "frame_id", "classification"])
            while True:
                ok, image = cap.read()
                if not ok:
                    break
                pts = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                if not math.isfinite(pts) or (previous_pts is not None and pts <= previous_pts):
                    raise ValueError("Decoder does not provide strictly increasing presentation timestamps. No FPS fallback is used.")
                previous_pts = pts; decoded_frames += 1
                capture_time = (pts-calibration["video_zero"])/scale
                if capture_time > phases[-1]["end"]:
                    break
                phase = next((p for p in phases if p["start"]+.25 <= capture_time < p["end"]-.25), None)
                if phase is None:
                    continue
                if [image.shape[1], image.shape[0]] != calibration["size"]:
                    raise ValueError("Video dimensions differ from calibration")
                ids = []
                for panel in calibration["panels"]:
                    values = [sample(image, xy, panel["radius"]) for xy in panel["xy"]]
                    value, reason = bench.decode_levels(values, panel["low"], panel["high"])
                    ids.append(value)
                    samples[phase["name"]][panel["name"]].append({"time": capture_time, "id": value})
                    reasons[phase["name"]][reason] += 1
                    writer.writerow([pts, capture_time, phase["name"], panel["name"], "" if value is None else value, reason])
                if len(ids) > 1 and all(v is not None for v in ids):
                    row = cross[phase["name"]]
                    row["all_selected_panels_valid"] += 1
                    row["different_ids"] += int(len(set(ids)) > 1)
    finally:
        cap.release()
    result = {"schema": 1, "video": str(args.video.resolve()), "decoded_video_frames": decoded_frames,
              "timestamp_source": "OpenCV decoded video presentation timestamps (POS_MSEC), monotonicity checked",
              "time_basis": calibration["time_basis"], "time_scale": scale,
              "calibration_requires_visual_review": True,
              "receiver_electrical_fps": None, "cases": []}
    for phase in phases:
        name = phase["name"]
        result["cases"].append({"name": name, "requested_fps": phase["fps"],
            "producer_submitted": phase["submitted"], "producer_local_rejections": phase["local_rejections"],
            "panels": {panel: bench.summarize(rows, phase["fps"]) for panel, rows in samples[name].items()},
            "classifications": dict(reasons[name]), "cross_panel_observations": cross[name],
            "cross_panel_note": "Different IDs can reflect rolling shutter or exposure; not proof of controller tearing."})
    (args.output / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("calibrate", "analyze"):
        p = sub.add_parser(name)
        p.add_argument("--video", type=Path, required=True)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        if name == "calibrate":
            p.add_argument("--regions", type=Path, help='Optional JSON: [{"name":"side_1","rect":[x,y,w,h]}]')
            p.add_argument("--video-zero", type=float, required=True, help="Presentation seconds corresponding to sender start")
            p.add_argument("--time-scale", type=float, required=True, help="Playback duration / real capture duration; 1 for verified realtime PTS")
            p.add_argument("--time-basis", choices=["original_realtime_pts", "constant_slow_motion_verified"], required=True)
        else:
            p.add_argument("--calibration", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.run.read_text(encoding="utf-8"))
    if args.action == "calibrate":
        if not math.isfinite(args.time_scale) or args.time_scale <= 0 or not math.isfinite(args.video_zero):
            parser.error("Time scale must be positive and finite, video zero finite")
        if args.time_basis == "original_realtime_pts" and args.time_scale != 1:
            parser.error("Original realtime PTS requires time-scale 1")
        calibrate(args, report)
    else:
        analyze(args, report)


if __name__ == "__main__":
    main()
