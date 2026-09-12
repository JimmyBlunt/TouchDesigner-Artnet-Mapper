"""A compressed synthetic video exercises timestamp decoding and ROI calibration."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from pixelblaze_mapper import gico_camera_benchmark as bench


@unittest.skipUnless(importlib.util.find_spec("cv2") and importlib.util.find_spec("numpy"), "OpenCV/numpy required")
class VideoRoundtrip(unittest.TestCase):
    def test_automatic_marker_calibration_and_optical_rates(self):
        import cv2
        import numpy as np
        from tools import gico_camera_analyze as tool
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); video = root / "synthetic.avi"
            camera_fps = 120
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), camera_fps, (480, 240))
            if not writer.isOpened():
                self.skipTest("MJPG encoder unavailable")
            positions = [[(15+(i % 7)*21+panel*160, 35+(i//7)*65) for i in range(21)] for panel in range(3)]
            phases = []; total = 0
            def phase(name, frames, fps, pattern):
                nonlocal total
                phases.append({"name": name, "start": total/camera_fps,
                    "end": (total+frames)/camera_fps, "fps": fps, "submitted": round(frames/camera_fps*fps),
                    "local_rejections": 0})
                for frame in range(frames):
                    image = np.full((240, 480, 3), 10, dtype=np.uint8)
                    bits = pattern(frame)
                    for points in positions:
                        for xy, state in zip(points, bits):
                            cv2.circle(image, xy, 4, (170, 170, 170) if state else (10, 10, 10), -1)
                    writer.write(image)
                total += frames
            phase("all_on", 24, 20, lambda f: [1]*21)
            phase("black_reference", 12, 20, lambda f: [0]*21)
            for marker in range(21):
                phase("marker_%02d" % marker, 12, 20, lambda f, m=marker: [int(i == m) for i in range(21)])
            for fps in (15, 25, 30):
                phase("measure_%d" % fps, 240, fps, lambda f, rate=fps: bench.encode(int(f*rate/camera_fps)))
            writer.release()
            report = {"phases": phases}
            regions = root / "regions.json"
            regions.write_text(json.dumps([{"name": "side_%d" % (i+1), "rect": [i*160, 0, 160, 240]} for i in range(3)]))
            calibration = root / "calibration"
            with contextlib.redirect_stdout(io.StringIO()):
                tool.calibrate(SimpleNamespace(video=video, video_zero=0, time_scale=1,
                    time_basis="original_realtime_pts", regions=regions, output=calibration), report)
                tool.analyze(SimpleNamespace(video=video, calibration=calibration / "calibration.json",
                    output=root / "analysis"), report)
            result = json.loads((root / "analysis" / "analysis.json").read_text())
            self.assertEqual(len(result["cases"]), 3)
            for case in result["cases"]:
                self.assertEqual(case["cross_panel_observations"]["different_ids"], 0)
                for panel in case["panels"].values():
                    self.assertEqual(panel["unobserved_ids"], 0)
                    self.assertEqual(panel["rejected_fraction"], 0)
                    self.assertAlmostEqual(panel["observed_unique_fps_estimate"], case["requested_fps"], delta=.25)
                    self.assertAlmostEqual(panel["camera_fps_median"], 120, delta=.01)


if __name__ == "__main__":
    unittest.main()
