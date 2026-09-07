"""Explicit camera-only subprocess boundary. Importing/preparing opens no device.

ProbeHandle contains process/thread objects: keep it transient, never in saved TD
storage. No scanner, network backend, image writer or arbitrary command API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
import threading


INTERPRETER = Path(r"C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe")
REPOSITORY = Path(__file__).resolve().parent.parent
PROTOCOL = "pixelblaze-camera-probe-v1"
_active_lock = threading.Lock()
_active = None


@dataclass(frozen=True)
class ProbePlan:
    device: int = 0
    exposure: int = -10
    threshold: int = 160

    def __post_init__(self):
        for name in ("device", "exposure", "threshold"):
            if type(getattr(self, name)) is not int:
                raise ValueError(name + " must be an integer")
        if not 0 <= self.device <= 2147483647:
            raise ValueError("device must be a nonnegative OpenCV device index")
        if not -2147483648 <= self.exposure <= 2147483647:
            raise ValueError("exposure must fit a signed 32-bit integer")
        if not 0 <= self.threshold <= 254:
            raise ValueError("installed MariMapper threshold range is 0..254")


def prepare_camera_probe(device=0, exposure=-10, threshold=160):
    """Validate requested settings only; exposure support is camera-dependent."""
    return ProbePlan(device, exposure, threshold)


def probe_argv(plan):
    if type(plan) is not ProbePlan:
        raise ValueError("expected a current validated ProbePlan")
    ProbePlan(plan.device, plan.exposure, plan.threshold)
    return [str(INTERPRETER), "-B", "-u", "-m", "pixelblaze_mapper.camera_probe_worker",
            "--confirm-camera", "--device", str(plan.device), "--exposure", str(plan.exposure),
            "--threshold", str(plan.threshold)]


@dataclass
class ProbeHandle:
    process: object
    plan: ProbePlan
    lock: object = field(default_factory=threading.Lock)
    stop_lock: object = field(default_factory=threading.Lock)
    status: dict = field(default_factory=lambda: {
        "state": "starting", "frames": 0, "cleanup_confirmed": False,
        "forced_stop": False, "image_storage": False, "hardware_output": False,
        "settings_restored": None, "startup_timed_out": False})
    readers: list = field(default_factory=list)
    startup_done: object = field(default_factory=threading.Event)
    watchdog: object = None


def _read_stdout(handle):
    # Worker emits only small scalar metadata, never pixel/contour arrays.
    try:
        for line in handle.process.stdout:
            if len(line) > 8192:
                continue
            try:
                item = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(item, dict) or item.get("protocol") != PROTOCOL:
                continue
            if item.get("state") not in {"starting", "native_loading", "camera_opening",
                                         "configuring", "ready", "running", "error", "stopped"}:
                continue
            allowed = {"state", "frames", "width", "height", "detected", "u", "v",
                       "requested_exposure", "actual_exposure", "exposure_applied",
                       "reason", "error", "cleanup_confirmed", "cleanup_errors", "phase"}
            clean = {key: value for key, value in item.items() if key in allowed and
                     (value is None or type(value) in (str, int, float, bool))}
            with handle.lock:
                handle.status.update(clean)
            if clean.get("state") in ("error", "stopped") or (
                    clean.get("state") == "running" and clean.get("frames", 0) > 0):
                handle.startup_done.set()
    finally:
        handle.process.stdout.close()


def _drain_stderr(handle):
    # Drain continuously to avoid child pipe deadlocks. No disk logs or images.
    try:
        while handle.process.stderr.read(4096):
            pass
    finally:
        handle.process.stderr.close()


def _startup_watchdog(handle, timeout):
    """Wait off the TD thread; startup completes only after a displayed frame."""
    if handle.startup_done.wait(timeout) or handle.process.poll() is not None:
        return
    with handle.lock:
        if handle.status.get("frames", 0) > 0 or handle.status["state"] in ("error", "stopped"):
            return
        phase = handle.status.get("phase", handle.status["state"])
        handle.status.update(startup_timed_out=True, startup_timeout_phase=phase,
            startup_error="Camera startup timed out after %gs at %s; stopping probe" % (timeout, phase))
    stop_camera_probe(handle)


def start_camera_probe(plan, *, confirmed=False, startup_timeout_seconds=20.0):
    """Explicitly open ONE camera in an isolated worker with visible preview."""
    global _active
    if confirmed is not True:
        raise ValueError("camera preview requires explicit confirmation")
    if type(startup_timeout_seconds) not in (int, float) or not 0.05 <= startup_timeout_seconds <= 120:
        raise ValueError("startup_timeout_seconds must be finite and between 0.05 and 120")
    argv = probe_argv(plan)
    if not INTERPRETER.is_file():
        raise FileNotFoundError("reviewed MariMapper interpreter is unavailable")
    with _active_lock:
        if _active is not None and _active.process.poll() is None:
            raise RuntimeError("a camera probe is already running; stop it first")
        process = subprocess.Popen(
            argv, shell=False, cwd=str(REPOSITORY), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        handle = ProbeHandle(process, plan)
        _active = handle
        try:
            for target in (_read_stdout, _drain_stderr):
                thread = threading.Thread(target=target, args=(handle,), daemon=True)
                thread.start()
                handle.readers.append(thread)
            handle.watchdog = threading.Thread(target=_startup_watchdog,
                args=(handle, startup_timeout_seconds), daemon=True)
            handle.watchdog.start()
        except Exception:
            stop_camera_probe(handle, grace_seconds=0.2)
            raise
        return handle


def poll_camera_probe(handle):
    """Non-blocking plain metadata snapshot, suitable for a TD status label."""
    code = handle.process.poll()
    with handle.lock:
        result = dict(handle.status)
    result["returncode"] = code
    if result["forced_stop"]:
        result.update(state="forced_stopped" if code is not None else "stop_failed",
                      cleanup_confirmed=False)
    elif code is not None and result["state"] not in ("stopped", "error"):
        result.update(state="exited_unconfirmed", cleanup_confirmed=False)
    if result["startup_timed_out"]:
        result.update(state="startup_timeout", error=result["startup_error"],
                      reason="startup_timeout")
    return result


def stop_camera_probe(handle, *, grace_seconds=3.0):
    """Cooperative stop, then terminate only our worker if a camera read hangs.

    On Windows terminate cannot run finally. A forced stop NEVER confirms camera
    setting restoration, even if an earlier metadata message claimed cleanup.
    Call outside a time-critical TD cook; bounded waits can take grace + 1 sec.
    """
    if type(grace_seconds) not in (int, float) or not 0 <= grace_seconds <= 10:
        raise ValueError("grace_seconds must be finite and between 0 and 10")
    with handle.stop_lock:
        if handle.process.poll() is None:
            try:
                handle.process.stdin.write('{"command":"stop"}\n')
                handle.process.stdin.flush()
                handle.process.stdin.close()
            except (OSError, ValueError):
                pass
            try:
                handle.process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                with handle.lock:
                    handle.status.update(forced_stop=True, cleanup_confirmed=False)
                try:
                    handle.process.terminate()
                    handle.process.wait(timeout=1.0)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        else:
            try:
                handle.process.stdin.close()
            except (OSError, ValueError):
                pass
        for reader in handle.readers:
            reader.join(timeout=0.1)
        return poll_camera_probe(handle)
