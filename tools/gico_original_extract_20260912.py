"""Offline original-video analysis with a frozen, calibration-only local model.

No network or controller calls. Saves optical scores so decoding can be audited
without repeatedly transcoding the video. Local model is produced by the
versioned calibration probe; its held-out results must be reviewed separately.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pixelblaze_mapper.gico_optical_erasure import decode_scores
from pixelblaze_mapper.gico_camera_benchmark import decode_levels, summarize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', type=Path, required=True)
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--offset', type=float, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cv2.setNumThreads(2)
    model = np.load(args.model)
    dark, pts, coords = (model[k] for k in ('dark', 'pts', 'coords'))
    low, weight = (model[k] for k in ('low', 'weight'))
    gray = cv2.cvtColor(dark, cv2.COLOR_BGR2GRAY)
    phases = [p for p in json.loads(args.run.read_text())['phases']
              if p['name'].startswith('measure_')]
    rows = {p['name']: [] for p in phases}
    direct = {p['name']: [] for p in phases}
    reasons = {p['name']: Counter() for p in phases}
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise ValueError('Cannot open video')
    cap.set(cv2.CAP_PROP_POS_MSEC, (args.offset+phases[0]['start'])*1000)
    previous = None; saved = []; stats = []; decoded = 0; start = time.perf_counter()
    try:
        while True:
            ok, image = cap.read()
            if not ok: break
            pts_s = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if previous is not None and pts_s <= previous:
                raise ValueError('Non-increasing camera presentation timestamps')
            previous = pts_s; capture = pts_s-args.offset
            if capture > phases[-1]['end']: break
            index = next((i for i, p in enumerate(phases)
                          if p['start']+.25 <= capture < p['end']-.25), None)
            if index is None: continue
            name = phases[index]['name']
            image = cv2.resize(image, (540, 960))
            current = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            q, status, _ = cv2.calcOpticalFlowPyrLK(gray, current, pts, None,
                                                   winSize=(31, 31), maxLevel=3)
            good = status.ravel() == 1
            matrix, inliers = cv2.estimateAffinePartial2D(
                pts[good], q[good], method=cv2.RANSAC, ransacReprojThreshold=1.5)
            ni = int(inliers.sum()) if inliers is not None else 0
            value = strict = None; reason = 'registration_failed'; erasures = 0
            score = np.full(21, np.nan); residual = float('nan')
            if matrix is not None and ni >= 100:
                source = pts[good].reshape(-1, 2)
                predicted = source @ matrix[:, :2].T + matrix[:, 2]
                errors = np.linalg.norm(predicted-q[good].reshape(-1, 2), axis=1)
                residual = float(np.median(errors[inliers.ravel() == 1]))
                if residual <= 1.0:
                    aligned = cv2.warpAffine(image, matrix, (540, 960),
                        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
                    aligned = cv2.GaussianBlur(aligned, (3, 3), .65)
                    patches = np.array([cv2.getRectSubPix(aligned, (19, 19),
                        tuple(xy.astype(float))).reshape(-1) for xy in coords], float)
                    score = np.sum((patches-low)*weight, axis=-1)
                    strict = decode_levels(score*100, np.zeros(21), np.ones(21)*100)[0]
                    value, reason, erasures = decode_scores(score)
            rows[name].append({'time': capture, 'id': value})
            direct[name].append({'time': capture, 'id': strict})
            reasons[name][reason] += 1
            saved.append(score)
            stats.append([pts_s, index, ni, residual, -1 if strict is None else strict,
                          -1 if value is None else value, erasures])
            decoded += 1
            if decoded % 1000 == 0:
                print(json.dumps({'samples': decoded, 'video_s': round(pts_s, 2),
                                  'elapsed_s': round(time.perf_counter()-start, 1)}), flush=True)
    finally:
        cap.release()
    np.savez_compressed(args.output/'optical-scores.npz', scores=np.array(saved), stats=np.array(stats))
    result = {'video': str(args.video), 'model_sha256': hashlib.sha256(args.model.read_bytes()).hexdigest(),
              'time_offset': args.offset, 'time_scale': 1, 'timestamp_monotonic': True,
              'method': 'Frozen local RGB model with static-board registration; strict and bounded-erasure CRC reported separately',
              'limits': ['Local calibration uses one illuminated marker at a time, not known simultaneous combinations.',
                         'Recovered CRC IDs are not the same as directly measured bits.',
                         '60 FPS camera undersamples a 30 FPS optical test for conservative two-frame confirmation.',
                         'Do not interpret missing IDs or sparse observations as controller losses.'], 'cases': []}
    for p in phases:
        name = p['name']
        result['cases'].append({'name': name, 'requested_fps': p['fps'],
            'classifications': dict(reasons[name]),
            'direct_only': summarize(direct[name], p['fps']),
            'including_bounded_erasures': summarize(rows[name], p['fps'])})
    (args.output/'analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    for case in result['cases']:
        print(json.dumps({'name': case['name'], 'classifications': case['classifications'],
            'summary': {k: v for k, v in case['including_bounded_erasures'].items()
                        if k != 'unobserved_ranges'}}), flush=True)


if __name__ == '__main__': main()
