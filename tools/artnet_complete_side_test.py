"""Send a bounded low-brightness row test for the complete three-panel scan."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelblaze_mapper.complete_side_rescan import NEW_TOTAL_POINTS, PANEL_SPECS
from pixelblaze_mapper.multi_controller import build_router_plan, default_router_config
from pixelblaze_mapper.spatial_map import build_side_spatial_map


def artdmx_packet(universe: int, payload: bytes) -> bytes:
    return (
        b"Art-Net\x00" + b"\x00\x50" + b"\x00\x0e" + b"\x00\x00"
        + bytes((universe & 0xFF, (universe >> 8) & 0x7F))
        + bytes((len(payload) >> 8, len(payload) & 0xFF)) + payload
    )


ROW_PALETTE = (
    (1.0, 0.0, 0.0),  # red
    (1.0, 1.0, 1.0),  # white
    (0.0, 0.0, 1.0),  # blue
)

def row_test_source(coordinates, bands: int = 18):
    """Color measured logical rows, retaining every LED's exact XYZ/UV entry.

    ``bands`` is kept for command compatibility but is no longer used to guess
    row lengths or row counts.  Physical row membership comes from the spatial
    lookup derived from the Pixelblaze coordinates.
    """

    if len(coordinates) != NEW_TOTAL_POINTS:
        raise ValueError("Expected the complete 3,744-point mapping")
    if bands < 1:
        raise ValueError("At least one coordinate band is required")
    source = [(0.0, 0.0, 0.0)] * NEW_TOTAL_POINTS
    for panel in build_side_spatial_map(coordinates):
        for led in panel.leds:
            source[led.index] = ROW_PALETTE[led.row % len(ROW_PALETTE)]
    return tuple(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, default=Path("mappings/mapping_complete_new_0_1183_full_2026-08-24.json"))
    parser.add_argument("--target", default="10.0.0.244")
    parser.add_argument("--local-address", default="10.0.0.125")
    parser.add_argument("--source-port", type=int, default=6454)
    # GICO labels its ports 1..9 in the UI, but ArtDMX uses wire addresses 0..8.
    parser.add_argument("--start-universe", type=int, default=0)
    parser.add_argument("--bands", type=int, default=18)
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    coordinates = json.loads(args.mapping.read_text(encoding="utf-8"))
    source = row_test_source(coordinates, args.bands)
    plan = build_router_plan(default_router_config(args.local_address))
    frames = plan.pack_pixels(source)["WS2812_NODE"]
    if len(frames) != 12 or any(len(frame) != 510 for frame in frames):
        raise RuntimeError("Expected twelve 510-channel WS universes, including reserved black gaps")

    destination = (args.target, 6454)
    sent = 0
    deadline = time.monotonic() + args.seconds
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((args.local_address, args.source_port))
        while time.monotonic() < deadline:
            started = time.monotonic()
            for offset, frame in enumerate(frames):
                udp.sendto(artdmx_packet(args.start_universe + offset, bytes(frame)), destination)
                sent += 1
            time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - started)))
    print(
        f"sent={sent} target={args.target} wire_universes=0-11 "
        f"coordinate_bands=logical-lattice sampling=per-led-xyz-lookup "
        f"colors=red/white/blue "
        "hardware_starts=0/680/1360 reserved_universes=6-7,11 exact_channels=510 sequence=0"
    )


if __name__ == "__main__":
    main()
