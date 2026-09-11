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


def _write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    # Windows can briefly deny replacement while status() has the target open.
    deadline = time.monotonic() + .2
    while True:
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(.005)


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


class ExternalPacketSender:
    def __init__(self, python_executable, local_address, target_address,
                 target_port=6454, local_port=6454, gap_ms=0.0):
        self.target = _endpoint(target_address, target_port)
        local = _endpoint(local_address, local_port)
        gap = float(gap_ms)
        if not math.isfinite(gap) or not 0 <= gap <= 5:
            raise ValueError('Packet gap must be 0..5 ms')
        self._directory = Path(tempfile.mkdtemp(prefix='td-artnet-worker-'))
        self._process = None
        self._ipc = None
        self._closed = False
        self._last_status = {}
        self._cleanup_errors = []
        self._forced_termination = False
        self._token = secrets.token_hex(32)
        config = dict(token=self._token, local=local, target=self.target, gap=gap / 1000)
        config_path = self._directory / 'config.json'
        try:
            _write(config_path, config)
            self._process = subprocess.Popen(
                [str(python_executable), str(Path(__file__).resolve()), '--worker', str(config_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            deadline = time.monotonic() + 2.0
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
            raise TimeoutError('Packet worker startup exceeded two seconds')
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
        for packet, target in packets_and_targets:
            if tuple(target) != self.target:
                raise ValueError('External sender target differs from configured target')
            packets.append(base64.b64encode(_packet(packet)).decode('ascii'))
        raw = json.dumps(dict(token=self._token, packets=packets), separators=(',', ':')).encode()
        _decode(raw, self._token)  # Fail before enqueueing malformed or oversized frames.
        try:
            self._ipc.sendto(raw, self._address)
        except BlockingIOError:
            return False
        return True

    def status(self):
        try:
            self._last_status = json.loads((self._directory / 'status.json').read_text())
        except (FileNotFoundError, OSError, ValueError):
            pass
        return dict(self._last_status, running=bool(
            self._process is not None and self._process.poll() is None), closed=self._closed,
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
        result = self.status()
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
    stats = dict(submitted_batches=0, sent_batches=0, sent_packets=0,
                 stale_batches=0, rejected_batches=0, blackout_packets=0,
                 error='', stop_reason='', last_send_ms=0., max_send_ms=0.,
                 actual_send_fps=0., active_seconds=0., active_average_fps=0.,
                 gap_ms=config['gap'] * 1000)
    last_packets = {}
    target = _endpoint(*config['target'])
    gap = config['gap']
    last_received = time.monotonic()
    received_first_batch = False
    last_report = 0.
    first_send = previous_send = None
    interval_ema = 0.
    try:
        outgoing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        outgoing.bind(_endpoint(*config['local']))
        outgoing.settimeout(.2)
        incoming = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        incoming.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        incoming.bind(('127.0.0.1', 0))
        incoming.settimeout(.05)
        _write(folder / 'status.json', stats)
        _write(folder / 'ready.json', dict(port=incoming.getsockname()[1]))
        while not (folder / 'stop').exists():
            timeout = WATCHDOG_SECONDS if received_first_batch else INITIAL_GRACE_SECONDS
            if time.monotonic() - last_received > timeout:
                stats['stop_reason'] = 'idle_watchdog' if received_first_batch else 'startup_watchdog'
                break
            try:
                raw, origin = incoming.recvfrom(MAX_BATCH + 1)
            except socket.timeout:
                continue
            incoming.setblocking(False)
            # A finite queue drain avoids starvation if a producer outruns us.
            latest = _latest_queued_batch(incoming, raw, origin, config['token'], stats)
            incoming.settimeout(.05)
            if latest is None:
                continue
            last_received = time.monotonic()
            received_first_batch = True
            last_packets.update((packet[14:16], packet) for packet in latest)
            started = time.perf_counter()
            for index, packet in enumerate(latest):
                if (folder / 'stop').exists():
                    break
                if index and gap:
                    _wait_until(time.perf_counter() + gap)
                outgoing.sendto(packet, target)
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
                _write(folder / 'status.json', stats)
                last_report = time.monotonic()
        if not stats['stop_reason']:
            stats['stop_reason'] = 'requested'
    except Exception as error:
        stats['error'] = str(error)
        stats['stop_reason'] = 'error'
    finally:
        if outgoing is not None:
            try:
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
