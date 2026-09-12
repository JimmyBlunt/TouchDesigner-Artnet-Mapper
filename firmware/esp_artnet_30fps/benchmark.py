"""Controlled black-frame test of the experimental .151 firmware only.

Explicit --run is mandatory. No output before identity/config validation.
Writes receiver counters separately from sender rates; never claims optical FPS.
"""
import argparse
import json
import socket
import time
import urllib.request
from pathlib import Path

TARGET = '10.0.0.151'

def api(path, post=False):
    req = urllib.request.Request('http://' + TARGET + path,
                                 data=b'' if post else None,
                                 method='POST' if post else 'GET')
    with urllib.request.urlopen(req, timeout=4) as response:
        return json.load(response)

def packet(universe, sequence, payload=None):
    return (b'Art-Net\0\x00\x50\x00\x0e' + bytes((sequence, 0))
            + universe.to_bytes(2, 'little') + b'\x01\xfe'
            + (bytes(510) if payload is None else payload))

def send_stream(sock, target_ip, universes, duration, fps, outputs=(), pattern='black', gap_ms=0):
    started = time.perf_counter()
    deadline = started
    count = overruns = 0
    max_interval = 0.0
    previous = None
    while time.perf_counter() - started < duration:
        remaining = deadline - time.perf_counter()
        if remaining > 0.002:
            time.sleep(remaining - 0.001)
        while time.perf_counter() < deadline:
            pass
        now = time.perf_counter()
        if now - started >= duration:
            break
        if previous is not None:
            max_interval = max(max_interval, now - previous)
        previous = now
        payloads = {u: bytearray(510) for u in universes}
        if pattern == 'moving-dot':
            for output in outputs:
                led = count % output['count']
                channel = (led % 170) * 3
                color = (0,0,255) if output['type'] == 'APA102' else (255,0,0)
                payloads[output['universe'] + led // 170][channel:channel+3] = bytes(color)
        for index,universe in enumerate(universes):
            if index and gap_ms:
                until=time.perf_counter()+gap_ms/1000
                while time.perf_counter()<until:
                    pass
            sock.sendto(packet(universe, count % 255 + 1, payloads[universe]), (target_ip, 6454))
        count += 1
        deadline += 1 / fps
        if deadline <= time.perf_counter():
            overruns += 1
            deadline = time.perf_counter() + 1 / fps
    elapsed = time.perf_counter() - started
    return {'sent_frames': count, 'send_elapsed_seconds': elapsed, 'sender_fps': count/elapsed,
            'sender_overruns': overruns, 'gap_ms':gap_ms,
            'max_sender_frame_interval_ms': max_interval*1000}

def run(local_ip, duration, rates, pattern='black', gap_ms=0):
    identity = api('/api/status')
    if identity.get('firmware') != 'experimental-esp-artnet-30fps-v1':
        raise RuntimeError('Target identity is not the experimental firmware; no output started')
    if identity.get('allowedSender') != local_ip:
        raise RuntimeError('Local source IP must match the firmware allowedSender')
    config = api('/api/config')
    if config.get('experimental') is not True:
        raise RuntimeError('Experimental config missing')
    universes = [o['universe'] + n for o in config['outputs']
                 for n in range((o['count'] + 169) // 170)]
    if len(set(universes)) != len(universes) or not 1 <= len(universes) <= 32:
        raise RuntimeError('Unsafe/invalid universe configuration')
    results = {'identity': identity, 'config': config, 'pattern': pattern, 'cases': [],
               'visible_host_level_255': 255 if pattern == 'moving-dot' else 0,
               'firmware_brightness_limit_255': identity['brightnessLimit255'],
               'optical_fps_measured': False}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((local_ip, 0))
        try:
            api('/api/arm?enabled=true', post=True)
            for fps in rates:
                before = api('/api/status')
                sent = send_stream(sock, TARGET, universes, duration, fps, config['outputs'], pattern, gap_ms)
                time.sleep(0.15)
                after = api('/api/status')
                delta = {k: (after[k] - before[k]) & 0xffffffff for k in (
                    'receivedPackets', 'completedFrames', 'incompleteFrames',
                    'outputFrames', 'supersededFrames', 'malformedPackets', 'latePackets',
                    'wsCompletedTransfers', 'apaCompletedTransfers')}
                for key in ('rawUdpDatagrams','rawUdpQueueDrops','rawUdpOversizePackets','rawUdpStaleEpochPackets'):
                    if key in before and key in after:delta[key]=(after[key]-before[key]) & 0xffffffff
                results['cases'].append({'requested_fps': fps, **sent,
                    'sent_datagrams': sent['sent_frames'] * len(universes),
                    'receiver_counter_delta': delta, 'before': before, 'after': after,
                    'driver_calls_per_send_second': delta['outputFrames'] / sent['send_elapsed_seconds']})
                # Let the sequence-reset idle timeout elapse before next case.
                time.sleep(1.1)
        finally:
            api('/api/arm?enabled=false', post=True)
    results['final_status'] = api('/api/status')
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--local-ip', default='10.0.0.125')
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--rates', type=float, nargs='+', default=[5,15,30])
    parser.add_argument('--pattern', choices=['black','moving-dot'], default='black')
    parser.add_argument('--gap-ms', type=float, choices=[0,0.5,1], default=0)
    parser.add_argument('--above-normal', action='store_true',
                        help='Windows: temporarily raise only this benchmark process priority')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error('Add --run after the experimental node has been identified and flashed')
    if not 2 <= args.seconds <= 120 or any(not 1 <= rate <= 60 for rate in args.rates):
        parser.error('seconds must be 2..120; rates 1..60')
    if args.output.exists():
        parser.error('Output already exists; choose a new measurement path')
    if args.above_normal:
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x8000):
            raise ctypes.WinError(ctypes.get_last_error())
    result = run(args.local_ip, args.seconds, args.rates, args.pattern, args.gap_ms)
    result['sender_process_priority'] = 'AboveNormal' if args.above_normal else 'inherited'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'cases': [{k:v for k,v in x.items() if k not in ('before','after')}
                              for x in result['cases']],
                      'final_armed': result['final_status']['armed']}, indent=2))
