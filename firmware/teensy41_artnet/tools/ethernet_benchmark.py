"""Bounded, black-only Teensy test; verifies target IP from USB before sending.

Use --arm-unwired-bench only on the explicitly confirmed board with no LEDs.
This sends to the Teensy alone and never owns UDP source port 6454.
"""
import argparse
import json
from pathlib import Path
import socket
import struct
import subprocess
import threading
import time
import serial


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', required=True)
    p.add_argument('--target', required=True)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--rates', type=int, nargs='+', default=[10, 20, 30, 40])
    p.add_argument('--arm-unwired-bench', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or not 5 <= args.seconds <= 600:
        raise ValueError('Output must be new and duration between 5 and 600 seconds')
    if any(r < 1 or r > 120 for r in args.rates):
        raise ValueError('Rates must be 1..120')
    ser = serial.Serial(args.port, 115200, timeout=.2, write_timeout=1)
    samples = []
    read_errors = []
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            try:
                line = ser.readline()
                sample = json.loads(line)
                if sample.get('firmware') == 'teensy41-artnet-0.1':
                    samples.append({'host_time': time.perf_counter(), **sample})
            except (ValueError, UnicodeDecodeError):
                pass
            except serial.SerialException as exc:
                read_errors.append(str(exc))
                break

    worker = threading.Thread(target=reader, daemon=True)
    worker.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('10.0.0.125', 0))
    result = {'target': args.target, 'source': sock.getsockname(), 'cases': [],
              'physical_led_measurement': False, 'black_payload_only': True}
    try:
        ser.write(b'STOP\nSTATUS\n')
        deadline = time.monotonic() + 8
        while not samples and time.monotonic() < deadline:
            time.sleep(.05)
        if not samples:
            raise RuntimeError('No expected firmware telemetry over USB')
        status = samples[-1]
        if status['ip'] != args.target or not status['link']:
            raise RuntimeError('Target does not match the USB-identified Ethernet link/IP')
        if args.arm_unwired_bench and not (status['pinout_confirmed'] and status.get('unwired_bench')):
            raise RuntimeError('Output timing requires the explicitly marked unwired bench image')
        # Resolve ARP before the measured UDP burst. The cold smoke test lost the
        # first 27 packets before the socket/firmware saw them; do not hide it in RX loss.
        warmup = subprocess.run(['ping', '-S', '10.0.0.125', '-n', '1', '-w', '2000', args.target],
                                capture_output=True, text=True, timeout=5)
        result['arp_warmup'] = {'returncode': warmup.returncode, 'output': warmup.stdout}
        if warmup.returncode:
            raise RuntimeError('Identified Teensy did not answer the pre-test Ethernet ping')
        seq = 1
        for rate in args.rates:
            ser.write(b'STOP\n')
            time.sleep(.15)
            if args.arm_unwired_bench:
                ser.write(b'ARM\n')
            before = samples[-1]
            first = len(samples)
            start = time.perf_counter()
            next_frame = start
            count = 0
            max_interval = 0
            previous = None
            while time.perf_counter() - start < args.seconds:
                now = time.perf_counter()
                remaining = next_frame - now
                if remaining > .001:
                    time.sleep(remaining - .0005)
                    continue
                if remaining > 0:
                    continue
                if previous is not None:
                    max_interval = max(max_interval, now-previous)
                previous = now
                for universe in range(120, 149):
                    if universe == 138:
                        continue
                    header = b'Art-Net\0' + struct.pack('<H', 0x5000)
                    header += struct.pack('>HBB', 14, seq, 0)
                    header += struct.pack('<H', universe) + struct.pack('>H', 510)
                    sock.sendto(header + bytes(510), (args.target, 6454))
                count += 1
                seq = seq % 255 + 1
                next_frame += 1 / rate
                if time.perf_counter() - next_frame > 1 / rate:
                    next_frame = time.perf_counter() + 1 / rate
            elapsed = time.perf_counter()-start
            ser.write(b'STATUS\n')
            time.sleep(.25)
            rows = samples[first:]
            result['cases'].append({'requested_fps': rate, 'frames_sent': count,
                                    'elapsed_seconds': elapsed, 'send_fps': count/elapsed,
                                    'max_send_interval_ms': max_interval*1000,
                                    'before': before, 'telemetry': rows})
            print(json.dumps({'requested_fps': rate, 'send_fps': count/elapsed,
                              'latest_status': rows[-1] if rows else None}), flush=True)
    except BaseException as exc:
        result['error'] = repr(exc)
        raise
    finally:
        stop_requested_at = time.perf_counter()
        try:
            ser.write(b'STOP\nSTATUS\n')
            time.sleep(.5)
        except serial.SerialException as exc:
            result['stop_error'] = str(exc)
        result['final_status'] = samples[-1] if samples else None
        result['stop_confirmed'] = bool(samples and samples[-1]['host_time'] > stop_requested_at
                                        and not samples[-1]['armed'] and samples[-1]['black'])
        result['serial_read_errors'] = read_errors
        stop.set()
        worker.join(1)
        ser.close()
        sock.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
