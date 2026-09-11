"""Bounded black-only hardware benchmark, with no persistent controller writes."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.led_search import packet
from audit_20260907_capture import td

BASE = 'http://10.0.0.248'


def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=8))


def wait_until(deadline):
    # A measured short spin avoids Windows sleep overshoot for sub-ms gaps.
    while True:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            return
        if remaining > .002:
            time.sleep(remaining - .001)


def run(label, cases, duration=6):
    assert 1 <= duration <= 30
    state = td("import json;from pixelblaze_mapper import guided_scan_live as l,scan_output_guard;l.assert_outputs_off(op);assert not scan_output_guard.active();result=json.dumps({'off':True})")
    config = get('/api/config')
    assert config['hardwareProfile'] == 'esp32-wroom-flex-8ws-2apa'
    assert not get('/api/test-pattern')['active']
    universes = sorted({u for o in config['outputs'] if o['enabled']
                        for u in range(o['startUniverse'], o['startUniverse'] + (o['pixelCount'] + 169) // 170)})
    assert universes and min(universes) >= 120 and max(universes) <= 148
    # Only subscribed universes: U138 has no output and need not be sent.
    packets = [packet(u, bytes(510)) for u in universes]
    folder = ROOT / 'docs/controller-performance-20260912'
    folder.mkdir(exist_ok=True)
    output = folder / (label + '.json')
    assert not output.exists(), output
    report = dict(label=label, config=config, universes=universes, black_only=True, cases=[])
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('10.0.0.125', 0))
        def send(gap):
            for index, payload in enumerate(packets):
                if index and gap:
                    wait_until(time.perf_counter() + gap / 1000)
                sock.sendto(payload, ('10.0.0.248', 6454))
        try:
            for rate, gap in cases:
                assert 1 <= rate <= 40 and 0 <= gap <= 2
                assert get('/api/config') == config, 'Configuration changed during test'
                before = get('/api/status')
                started = time.perf_counter()
                deadline = started
                sends, durations = 0, []
                while time.perf_counter() - started < duration:
                    wait_until(deadline)
                    now = time.perf_counter()
                    if now - started >= duration:
                        break
                    t = time.perf_counter(); send(gap)
                    durations.append((time.perf_counter() - t) * 1000)
                    sends += 1
                    deadline += 1 / rate
                    if deadline <= time.perf_counter():
                        deadline = time.perf_counter() + 1 / rate
                elapsed = time.perf_counter() - started
                # Drain pending frame/output without further packets.
                time.sleep(.25)
                after = get('/api/status')
                delta = {k: after[k] - before[k] for k in
                         ('packets', 'framesComplete', 'framesIncomplete', 'outputFrames', 'timeouts', 'droppedPackets', 'sequenceErrors')}
                row = dict(requested_fps=rate, gap_ms=gap, seconds=elapsed,
                           sent_frames=sends, sent_packets=sends*len(packets),
                           send_fps=sends/elapsed, complete_fps=delta['framesComplete']/elapsed,
                           completion_ratio=delta['framesComplete']/sends,
                           batch_ms_mean=sum(durations)/len(durations), batch_ms_max=max(durations),
                           before=before, after=after, delta=delta)
                report['cases'].append(row)
                output.write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(json.dumps({k: row[k] for k in ('requested_fps','gap_ms','send_fps','complete_fps','completion_ratio','batch_ms_mean','delta')}), flush=True)
        finally:
            for _ in range(4):
                send(1); time.sleep(.2)
            report['final_black_sent'] = True
            output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('--cases', required=True, help='rate:gap_ms comma separated')
    parser.add_argument('--duration', type=float, default=6)
    args = parser.parse_args()
    run(args.label, [tuple(map(float, s.split(':'))) for s in args.cases.split(',')], args.duration)
