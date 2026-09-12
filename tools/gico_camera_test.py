"""Prepare or explicitly run the low-brightness GICO optical benchmark."""
import argparse
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pixelblaze_mapper import gico_camera_benchmark as bench


def assert_td_off():
    script = "import json;from pixelblaze_mapper import guided_scan_live as live;live.assert_outputs_off(op);result=json.dumps({'off':True})"
    request = urllib.request.Request("http://127.0.0.1:9981/api/td/server/exec",
        data=json.dumps({"script": script}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        answer = json.load(response)
    if not answer.get("success") or not json.loads(answer["data"]["result"]).get("off"):
        raise RuntimeError("TouchDesigner output-off verification failed: " + repr(answer))


def wait_until(deadline):
    while True:
        remaining = deadline-time.perf_counter()
        if remaining <= 0:
            return
        if remaining > .002:
            time.sleep(remaining-.001)


def run(folder, plan, sender_factory=None):
    # This read is only performed by the explicit 'run' command.
    assert_td_off()
    from pixelblaze_mapper.external_packet_sender import ExternalPacketSender
    factory = sender_factory or ExternalPacketSender
    sender = factory(sys.executable, plan["interface"], plan["target"], gap_ms=0)
    target = (plan["target"], 6454)
    clock_start = time.perf_counter()
    report = {"plan": plan, "started_unix_seconds": time.time(), "complete": False,
              "timestamp_kind": "producer submission, not controller reception", "phases": []}
    stream = None
    try:
        stream = (folder / "submitted-frames.jsonl").open("x", encoding="utf-8")
        def phase(name, seconds, fps, frame_ids=False, bits=None):
            start = time.perf_counter()
            row = {"name": name, "start": start-clock_start, "fps": fps,
                   "duration_requested": seconds, "submitted": 0, "local_rejections": 0}
            report["phases"].append(row)
            print(f"{name}: {seconds}s / {fps} FPS", flush=True)
            deadline = start
            while True:
                wait_until(deadline)
                now = time.perf_counter()
                if now-start >= seconds:
                    break
                frame_id = row["submitted"] % bench.MODULUS if frame_ids else None
                pattern = bench.encode(frame_id) if frame_ids else bits
                # The live GICO path disables ArtDmx sequencing for compatibility.
                # Optical frame identity is carried by Gray+CRC payload markers.
                batch = [(bench.packet(u, p, sequence=0), target) for u, p in enumerate(bench.payloads(pattern))]
                accepted = sender.submit(batch)
                if not accepted:
                    row["local_rejections"] += 1
                stream.write(json.dumps({"phase": name, "time": now-clock_start,
                    "id": frame_id, "sequence": 0, "accepted": accepted})+"\n")
                row["submitted"] += 1
                deadline += 1/fps
                # A stalled producer never compresses the next frame interval.
                if deadline <= time.perf_counter():
                    deadline = time.perf_counter()+1/fps
            row["end"] = time.perf_counter()-clock_start
            row["worker_after"] = sender.status()
            stream.flush()
        phase("all_on", 3, 20, bits=[1]*bench.MARKERS)
        phase("black_reference", 1, 20, bits=[0]*bench.MARKERS)
        for marker in range(bench.MARKERS):
            phase("marker_%02d" % marker, 1, 20, bits=[int(i == marker) for i in range(bench.MARKERS)])
        for case in plan["cases"]:
            fps = case["fps"]
            phase("warmup_%d" % fps, case["warmup_seconds"], fps, frame_ids=True)
            phase("measure_%d" % fps, case["seconds"], fps, frame_ids=True)
            phase("pause_%d" % fps, 2, 20, bits=[0]*bench.MARKERS)
        report["complete"] = True
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        report["worker_final"] = sender.close()  # Worker sends black to touched universes twice.
        report["ended_unix_seconds"] = time.time()
        if stream:
            stream.close()
        (folder / "run.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Output stopped. Worker report: " + str(report["worker_final"]), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    parser.add_argument("--output", type=Path, required=True, help="New output directory; never overwrite a run")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    prepared = bench.plan()
    (args.output / "plan.json").write_text(json.dumps(prepared, indent=2), encoding="utf-8")
    if args.action == "prepare":
        print("Prepared offline. No sockets or TouchDesigner calls. " + str(args.output))
    else:
        run(args.output, prepared)


if __name__ == "__main__":
    main()
