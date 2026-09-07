"""Camera-only worker. Default CLI does not open a camera; explicit opt-in does.

Uses installed MariMapper detection without importing its CLI/backend factories.
No image/file writer, scanner, reconstruction, LED backend, or network access.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import threading
import time
from types import SimpleNamespace

from .camera_probe import PROTOCOL, prepare_camera_probe

UPSTREAM_REVISION = "7dc5f799a1b7c180573c2632f6d12a3be0cbf4fa"


def _native_api():
    distribution = importlib.metadata.distribution("marimapper")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    if distribution.version != "3.4.2" or direct.get("vcs_info", {}).get("commit_id") != UPSTREAM_REVISION:
        raise RuntimeError("unreviewed MariMapper version/revision; camera was not opened")
    from marimapper.camera import Camera
    from marimapper.detector import set_cam_dark, find_led_in_image, draw_led_detections, show_image
    import cv2
    return SimpleNamespace(camera=Camera, dark=set_cam_dark, detect=find_led_in_image,
                           draw=draw_led_detections, show=show_image,
                           destroy=cv2.destroyAllWindows)


def _emit(item):
    print(json.dumps(dict(protocol=PROTOCOL, **item), allow_nan=False), flush=True)


def _listen_for_stop(stream, event):
    """Stop on explicit command, parent EOF, or malformed/oversized protocol."""
    try:
        while not event.is_set():
            line = stream.readline(4097)
            if not line or len(line) > 4096:
                break
            try:
                message = json.loads(line)
            except ValueError:
                break
            if message == {"command": "stop"}:
                break
            # No runtime configuration or arbitrary command execution.
            break
    finally:
        event.set()


class _CameraProgress:
    """Delegate native settings unchanged, report native eat() before it blocks."""
    def __init__(self, camera, emit):
        self._camera = camera
        self._emit = emit

    def __getattr__(self, name):
        return getattr(self._camera, name)

    def eat(self, *args, **kwargs):
        self._emit({"state": "configuring", "phase": "camera_warmup"})
        return self._camera.eat(*args, **kwargs)


def run_probe(plan, *, confirmed=False, stop_event=None, native=None, emit=_emit, clock=time.monotonic):
    """Run until cooperative stop/ESC/error. native injection is for offline tests."""
    if confirmed is not True:
        raise ValueError("camera preview requires explicit confirmation")
    plan = prepare_camera_probe(plan.device, plan.exposure, plan.threshold)
    event = stop_event if stop_event is not None else threading.Event()
    cam = None
    api = None
    frames = 0
    reason = "stop_requested"
    failed = False
    cleanup_errors = []
    try:
        if event.is_set():
            return 0
        emit({"state": "native_loading", "phase": "native_loading", "frames": 0})
        api = native if native is not None else _native_api()
        if event.is_set():
            return 0
        emit({"state": "camera_opening", "phase": "camera_opening"})
        cam = api.camera(plan.device)
        if event.is_set():
            return 0
        emit({"state": "configuring", "phase": "camera_settings"})
        applied = api.dark(_CameraProgress(cam, emit), plan.exposure)
        actual = cam.get_exposure()
        emit({"state": "ready", "phase": "first_frame", "requested_exposure": plan.exposure,
              "actual_exposure": int(actual), "exposure_applied": bool(applied)})
        next_report = 0.0
        while not event.is_set():
            image = cam.read()
            detection = api.detect(image, plan.threshold)
            api.show(api.draw(image, detection))
            frames += 1
            now = clock()
            if now >= next_report:
                emit({"state": "running", "phase": "preview", "frames": frames,
                      "height": int(image.shape[0]), "width": int(image.shape[1]),
                      "detected": detection is not None,
                      "u": float(detection.u()) if detection is not None else None,
                      "v": float(detection.v()) if detection is not None else None})
                next_report = now + 0.2
    except KeyboardInterrupt:
        reason = "escape_or_interrupt"
    except Exception as error:
        reason = "error"
        failed = True
        emit({"state": "error", "error": type(error).__name__ + ": " + str(error)[:512]})
    finally:
        # Independent cleanup: failed camera reset must not prevent release/window close.
        if cam is not None:
            for name, action in (("camera_reset", cam.reset), ("camera_release", cam.device.release)):
                try:
                    action()
                except Exception as error:
                    cleanup_errors.append(name + ": " + type(error).__name__)
        if api is not None:
            try:
                api.destroy()
            except Exception as error:
                cleanup_errors.append("window_close: " + type(error).__name__)
        # Native reset is best-effort and may only log driver rejection. This flag
        # confirms cleanup calls completed, NOT that hardware settings were restored.
        emit({"state": "error" if failed else "stopped", "frames": frames, "reason": reason,
              "cleanup_confirmed": not cleanup_errors,
              "cleanup_errors": "; ".join(cleanup_errors)})
    return 1 if failed or cleanup_errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--exposure", type=int, default=-10)
    parser.add_argument("--threshold", type=int, default=160)
    parser.add_argument("--confirm-camera", action="store_true")
    args = parser.parse_args(argv)
    plan = prepare_camera_probe(args.device, args.exposure, args.threshold)
    if not args.confirm_camera:
        _emit({"state": "prepared", "device": plan.device, "exposure": plan.exposure,
               "threshold": plan.threshold, "camera_opened": False})
        return 0
    # On this Windows NumPy/OpenCV build, loading the extension while another
    # thread blocks in stdin.readline stalls until that read returns. Load native
    # libraries first (no camera is opened); parent startup watchdog still applies.
    _emit({'state': 'native_loading', 'phase': 'native_loading', 'frames': 0})
    try:
        native = _native_api()
    except Exception as error:
        _emit({'state': 'error', 'error': str(error), 'frames': 0,
               'cleanup_confirmed': True, 'reason': 'native_load_failed'})
        return 1
    event = threading.Event()
    threading.Thread(target=_listen_for_stop, args=(sys.stdin, event), daemon=True).start()
    return run_probe(plan, confirmed=True, stop_event=event, native=native)


if __name__ == "__main__":
    raise SystemExit(main())
