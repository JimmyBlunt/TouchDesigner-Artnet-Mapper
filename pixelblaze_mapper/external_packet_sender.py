"""Bounded latest-frame ArtDMX sender in an isolated Python process.

Only the worker owns the physical UDP socket. Local submissions are authenticated
and never forwarded to an endpoint other than the constructor's fixed target.
"""
from __future__ import annotations

import base64
import ipaddress
import json
import math
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time

MAX_BATCH = 60_000
WATCHDOG_SECONDS = 1.0
INITIAL_GRACE_SECONDS = 5.0
STATUS_CACHE_SECONDS = .1
STARTUP_TIMEOUT_SECONDS = 5.0
SEND_BUFFER_BYTES = 1024 * 1024
STOP_CACHE_SECONDS = .02


def _endpoint(address, port):
    address = str(ipaddress.IPv4Address(address))
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError('Invalid UDP port')
    return address, port


def _packet(value):
    value = bytes(value)
    if (len(value) != 528 or value[:12] != b'Art-Net\0\0P\0\x0e'
            or value[16:18] != b'\x01\xfe' or value[15] & 128):
        raise ValueError('Expected ArtDMX with exactly 510 payload bytes')
    return value


def _decode(raw, token):
    if len(raw) > MAX_BATCH:
        raise ValueError('Batch exceeds IPC limit')
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('packets'), list):
        raise ValueError('Invalid batch envelope')
    if not secrets.compare_digest(str(data.get('token', '')), token):
        raise ValueError('Invalid sender token')
    packets = tuple(_packet(base64.b64decode(p, validate=True)) for p in data['packets'])
    if not packets:
        raise ValueError('Empty packet batch')
    universes = [p[14:16] for p in packets]
    if len(set(universes)) != len(universes):
        raise ValueError('Duplicate universe in frame')
    return packets


def _write(path, value, *, retry=True):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    # Windows can briefly deny replacement while status() has the target open.
    deadline = time.monotonic() + .2
    while True:
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if not retry or time.monotonic() >= deadline:
                raise
            time.sleep(.005)


def _periodic_status(path, stats):
    """Best-effort telemetry: never sleep/retry a contested status replacement.

    File creation/write/replace itself can still block in the OS. Measure that
    wall time separately from UDP send time. Measurements appear in the next
    successful snapshot (or final status), since this write measures itself.
    """
    started = time.perf_counter()
    try:
        _write(path, stats, retry=False)
    except PermissionError:
        stats['status_write_skipped'] += 1
    except OSError:
        stats['status_write_errors'] += 1
    finally:
        stats['status_write_ms'] = (time.perf_counter() - started) * 1000
        stats['max_status_write_ms'] = max(stats['max_status_write_ms'], stats['status_write_ms'])


def _wait_until(deadline):
    """Precise short waits in this isolated worker, never the TD thread.

    Windows sleep may overshoot millisecond requests substantially. Sleep for
    the coarse portion, then spin for the final <=2 ms. Each packet starts a
    fresh wait, so scheduler stalls do not produce catch-up packet bursts.
    """
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return
        if remaining > .002:
            time.sleep(remaining - .001)


def _latest_queued_batch(incoming, raw, origin, token, stats):
    latest = None
    for index in range(128):
        try:
            if origin[0] != '127.0.0.1':
                raise ValueError('Non-loopback batch')
            candidate = _decode(raw, token)
            if latest is not None:
                stats['stale_batches'] += 1
            latest = candidate
            stats['submitted_batches'] += 1
        except (ValueError, KeyError, TypeError):
            stats['rejected_batches'] += 1
        # Leave the next datagram queued when this bounded drain is full.
        if index == 127:
            break
        try:
            raw, origin = incoming.recvfrom(MAX_BATCH + 1)
        except BlockingIOError:
            break
    return latest


def _frame_rate(value):
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value) or not 0 < value <= 120 or not math.isfinite(1 / value):
        raise ValueError('Frame rate must be finite, greater than zero and at most 120')
    return value


class _FrameDeadline:
    """One pending complete frame, dispatched on a monotonic phase clock.

    Advance to a future slot, skipping every elapsed slot after a stall. This
    avoids catch-up bursts without accumulating normal OS wake-up jitter into
    a progressively slower rate. Adjacent actual starts may be closer than a
    period when a late dispatch is followed by an on-time slot.
    Empty intervals do not produce repeats or advance a synthetic FPS counter.
    """
    def __init__(self, frame_rate):
        self.period = 1 / frame_rate
        self.deadline = -math.inf
        self.pending = None

    def offer(self, packets, stats):
        if self.pending is not None:
            stats['stale_batches'] += 1
        self.pending = packets

    def wait_seconds(self, now):
        if self.pending is None:
            return .05
        return min(.05, max(0., self.deadline - now))

    def take(self, now):
        if self.pending is None or now < self.deadline:
            return None
        result, self.pending = self.pending, None
        if not math.isfinite(self.deadline):
            self.deadline = now + self.period
        else:
            elapsed_slots = math.floor((now - self.deadline) / self.period) + 1
            self.deadline += elapsed_slots * self.period
            if self.deadline <= now:  # Floating-point boundary protection.
                self.deadline += self.period
        return result


class _StopCheck:
    """Cache only negative stop checks for at most 20 ms within a batch.

    Batch/receive boundaries force a fresh check. This bounds cache-induced
    latency, not OS filesystem or scheduler stalls; a seen stop is permanent.
    """
    def __init__(self, path):
        self.path = path
        self.checked_at = -math.inf
        self.stopped = False

    def check(self, *, force=False):
        now = time.monotonic()
        if not self.stopped and (force or now - self.checked_at >= STOP_CACHE_SECONDS):
            self.stopped = self.path.exists()
            self.checked_at = now
        return self.stopped


class ExternalPacketSender:
    def __init__(self, python_executable, local_address, target_address,
                 target_port=6454, local_port=6454, gap_ms=0.0, frame_rate=None,
                 priority='normal'):
        self.target = _endpoint(target_address, target_port)
        local = _endpoint(local_address, local_port)
        gap = float(gap_ms)
        if not math.isfinite(gap) or not 0 <= gap <= 5:
            raise ValueError('Packet gap must be 0..5 ms')
        frame_rate = _frame_rate(frame_rate)
        if priority not in ('normal', 'above_normal'):
            raise ValueError('Worker priority must be normal or above_normal')
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        if priority == 'above_normal':
            # This flag exists only on Windows. Never use High or Realtime;
            # other platforms retain their normal process scheduling policy.
            creationflags |= getattr(subprocess, 'ABOVE_NORMAL_PRIORITY_CLASS', 0)
        self._directory = Path(tempfile.mkdtemp(prefix='td-artnet-worker-'))
        self._process = None
        self._ipc = None
        self._closed = False
        self._last_status = {}
        self._status_checked_at = -math.inf
        self._last_process_running = None
        self._cleanup_errors = []
        self._forced_termination = False
        self._token = secrets.token_hex(32)
        config = dict(token=self._token, local=local, target=self.target,
                      gap=gap / 1000, frame_rate=frame_rate)
        config_path = self._directory / 'config.json'
        try:
            _write(config_path, config)
            self._process = subprocess.Popen(
                [str(python_executable), str(Path(__file__).resolve()), '--worker', str(config_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=creationflags)
            deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                ready = self._directory / 'ready.json'
                if ready.exists():
                    self._address = ('127.0.0.1', json.loads(ready.read_text())['port'])
                    self._ipc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self._ipc.setblocking(False)
                    return
                if self._process.poll() is not None:
                    raise RuntimeError('Packet worker failed: ' + str(self.status()))
                time.sleep(.01)
            raise TimeoutError(f'Packet worker startup exceeded {STARTUP_TIMEOUT_SECONDS:g} seconds')
        except Exception:
            # No submissions can exist before startup succeeds; avoid another
            # graceful-shutdown timeout after the bounded readiness deadline.
            if self._process is not None and self._process.poll() is None:
                try:
                    self._process.kill()
                    self._process.wait(timeout=.2)
                except (OSError, subprocess.TimeoutExpired) as error:
                    self._cleanup_errors.append('startup cleanup: ' + str(error))
            self.close()
            raise

    def submit(self, packets_and_targets):
        if self._closed or self._process.poll() is not None:
            raise RuntimeError('Packet worker is not running: ' + str(self.status()))
        packets = []
        universes = set()
        for packet, target in packets_and_targets:
            if tuple(target) != self.target:
                raise ValueError('External sender target differs from configured target')
            packet = _packet(packet)
            universe = packet[14:16]
            if universe in universes:
                raise ValueError('Duplicate universe in frame')
            universes.add(universe)
            packets.append(base64.b64encode(packet).decode('ascii'))
        if not packets:
            raise ValueError('Empty packet batch')
        raw = json.dumps(dict(token=self._token, packets=packets), separators=(',', ':')).encode()
        if len(raw) > MAX_BATCH:
            raise ValueError('Batch exceeds IPC limit')
        # Values were validated before encoding; only the worker needs to decode
        # the transport envelope and authenticate its token again.
        try:
            self._ipc.sendto(raw, self._address)
        except BlockingIOError:
            return False
        return True

    def status(self, force=False):
        # File-backed counters can lag briefly, but process health never comes
        # from the cache. A worker exit refreshes final counters immediately.
        running = bool(self._process is not None and self._process.poll() is None)
        now = time.monotonic()
        if (force or running != self._last_process_running
                or now - self._status_checked_at >= STATUS_CACHE_SECONDS):
            try:
                self._last_status = json.loads((self._directory / 'status.json').read_text())
            except (FileNotFoundError, OSError, ValueError):
                pass
            self._status_checked_at = now
            self._last_process_running = running
        return dict(self._last_status, running=running, closed=self._closed,
            cleanup_errors=list(self._cleanup_errors), forced_termination=self._forced_termination)

    def close(self):
        if self._closed and not self.status()['running'] and not self._directory.exists():
            return self.status()
        self._closed = True
        try:
            (self._directory / 'stop').touch()
        except OSError as error:
            self._cleanup_errors.append('stop marker: ' + str(error))
        if self._ipc is not None:
            try:
                self._ipc.close()
            except OSError as error:
                self._cleanup_errors.append('IPC close: ' + str(error))
        if self._process is not None:
            try:
                self._process.wait(timeout=1.8)
            except (OSError, subprocess.TimeoutExpired) as error:
                self._forced_termination = True
                try:
                    self._process.kill()
                    self._process.wait(timeout=.2)
                except (OSError, subprocess.TimeoutExpired) as error:
                    self._cleanup_errors.append('worker termination: ' + str(error))
        result = self.status(force=True)
        self._last_status = result
        # Keep files if a process could not be stopped; close() remains retryable
        # while submit() stays blocked. Failed filesystem cleanup is retryable too.
        if not result['running']:
            try:
                shutil.rmtree(self._directory)
            except FileNotFoundError:
                pass
            except OSError as error:
                self._cleanup_errors.append('temporary files: ' + str(error))
        return self.status()


def _worker(config_path):
    folder = config_path.parent
    config = json.loads(config_path.read_text())
    incoming = outgoing = None
    frame_rate = _frame_rate(config.get('frame_rate'))
    pacer = _FrameDeadline(frame_rate) if frame_rate is not None else None
    stats = dict(submitted_batches=0, sent_batches=0, sent_packets=0,
                 stale_batches=0, rejected_batches=0, blackout_packets=0,
                 send_errors=0, send_buffer_bytes=0,
                 error='', stop_reason='', last_send_ms=0., max_send_ms=0.,
                 actual_send_fps=0., active_seconds=0., active_average_fps=0.,
                 gap_ms=config['gap'] * 1000, frame_rate=frame_rate,
                 status_write_ms=0., max_status_write_ms=0.,
                 status_write_skipped=0, status_write_errors=0)
    last_packets = {}
    target = _endpoint(*config['target'])
    gap = config['gap']
    last_received = time.monotonic()
    received_first_batch = False
    last_report = 0.
    first_send = previous_send = None
    interval_ema = 0.
    stop = _StopCheck(folder / 'stop')
    try:
        outgoing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        outgoing.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER_BYTES)
        outgoing.bind(_endpoint(*config['local']))
        outgoing.setblocking(False)
        stats['send_buffer_bytes'] = outgoing.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        incoming = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        incoming.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        incoming.bind(('127.0.0.1', 0))
        incoming.settimeout(.05)
        _write(folder / 'status.json', stats)
        _write(folder / 'ready.json', dict(port=incoming.getsockname()[1]))
        while not stop.check(force=True):
            timeout = WATCHDOG_SECONDS if received_first_batch else INITIAL_GRACE_SECONDS
            if time.monotonic() - last_received > timeout:
                stats['stop_reason'] = 'idle_watchdog' if received_first_batch else 'startup_watchdog'
                break
            if pacer is not None:
                # recv remains interruptible by input and bounded to 50 ms even
                # at very low output rates. A due frame uses a nonblocking drain.
                incoming.settimeout(pacer.wait_seconds(time.monotonic()))
            latest = None
            try:
                raw, origin = incoming.recvfrom(MAX_BATCH + 1)
            except (socket.timeout, BlockingIOError):
                if pacer is None:
                    continue
            else:
                incoming.setblocking(False)
                # A finite queue drain avoids starvation if a producer outruns us.
                latest = _latest_queued_batch(incoming, raw, origin, config['token'], stats)
                incoming.settimeout(.05)
            if latest is not None:
                last_received = time.monotonic()
                received_first_batch = True
                last_packets.update((packet[14:16], packet) for packet in latest)
                if pacer is not None:
                    pacer.offer(latest, stats)
            if pacer is not None:
                now = time.monotonic()
                # A socket wait may cross the watchdog boundary. Expired input
                # must not light a pending frame merely because its slot is due.
                if received_first_batch and now - last_received > WATCHDOG_SECONDS:
                    stats['stop_reason'] = 'idle_watchdog'
                    break
                latest = pacer.take(now)
            if latest is None:
                continue
            started = time.perf_counter()
            for index, packet in enumerate(latest):
                if index and gap:
                    _wait_until(time.perf_counter() + gap)
                if stop.check(force=index == 0):
                    break
                try:
                    outgoing.sendto(packet, target)
                except OSError:
                    # Includes EWOULDBLOCK: never count or silently discard a
                    # failed packet, and never spin/retry an incomplete frame.
                    stats['send_errors'] += 1
                    raise
                stats['sent_packets'] += 1
            else:
                stats['sent_batches'] += 1
                if first_send is None:
                    first_send = started
                if previous_send is not None:
                    interval = started - previous_send
                    interval_ema = interval if not interval_ema else .9 * interval_ema + .1 * interval
                    stats['actual_send_fps'] = 1 / interval_ema if interval_ema else 0.
                previous_send = started
                stats['active_seconds'] = started - first_send
                if stats['active_seconds']:
                    stats['active_average_fps'] = (stats['sent_batches'] - 1) / stats['active_seconds']
            stats['last_send_ms'] = (time.perf_counter() - started) * 1000
            stats['max_send_ms'] = max(stats['max_send_ms'], stats['last_send_ms'])
            if time.monotonic() - last_report >= .5:
                _periodic_status(folder / 'status.json', stats)
                last_report = time.monotonic()
        if not stats['stop_reason']:
            stats['stop_reason'] = 'requested'
    except Exception as error:
        stats['error'] = str(error)
        stats['stop_reason'] = 'error'
    finally:
        if outgoing is not None:
            try:
                # A full nonblocking send buffer must not immediately prevent
                # the final blackout. Retain the previous bounded send timeout.
                outgoing.settimeout(.2)
                # Send each universe that this worker touched as black, twice.
                # This confirms local send completion only, not receiver delivery.
                for repeat in range(2):
                    for index, packet in enumerate(last_packets.values()):
                        if index and gap:
                            _wait_until(time.perf_counter() + gap)
                        outgoing.sendto(packet[:18] + bytes(510), target)
                        stats['blackout_packets'] += 1
                    if last_packets and repeat == 0:
                        time.sleep(.05)
            except Exception as error:
                stats['error'] += '; blackout: ' + str(error)
            outgoing.close()
        if incoming is not None:
            incoming.close()
        _write(folder / 'status.json', stats)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3 or sys.argv[1] != '--worker':
        raise SystemExit('Expected --worker CONFIG_PATH')
    _worker(Path(sys.argv[2]))
