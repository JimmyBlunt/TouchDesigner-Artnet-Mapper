"""Show mapped pixels red and per-port padding green on the GICO node."""

from __future__ import annotations

import argparse
import socket
import time


PIXELS_PER_UNIVERSE = 170
CHANNELS_PER_UNIVERSE = 510
PORTS = (
    # Art-Net wire start, universe count, declared physical pixel count.
    # The GICO UI displays these as 1, 5 and 7 respectively.
    (0, 4, 517),
    (4, 2, 269),
    (6, 3, 398),
)


def wire_grb(display_rgb: tuple[int, int, int]) -> bytes:
    red, green, blue = display_rgb
    return bytes((green, red, blue))


def artdmx_packet(universe: int, payload: bytes) -> bytes:
    return (
        b"Art-Net\x00" + b"\x00\x50" + b"\x00\x0e" + b"\x00\x00"
        + bytes((universe & 0xFF, (universe >> 8) & 0x7F))
        + bytes((len(payload) >> 8, len(payload) & 0xFF)) + payload
    )


def build_frames(
    active_rgb: tuple[int, int, int] = (20, 0, 0),
    padding_rgb: tuple[int, int, int] = (0, 20, 0),
) -> tuple[tuple[int, bytes], ...]:
    active = wire_grb(active_rgb)
    padding = wire_grb(padding_rgb)
    result = []
    for start_universe, universe_count, active_count in PORTS:
        capacity = universe_count * PIXELS_PER_UNIVERSE
        pixels = [active if index < active_count else padding for index in range(capacity)]
        for offset in range(universe_count):
            first = offset * PIXELS_PER_UNIVERSE
            payload = b"".join(pixels[first:first + PIXELS_PER_UNIVERSE])
            if len(payload) != CHANNELS_PER_UNIVERSE:
                raise AssertionError("ArtDMX payload must contain exactly 510 channels")
            result.append((start_universe + offset, payload))
    return tuple(result)


def build_identity_frames() -> tuple[tuple[int, bytes], ...]:
    """Color each configured physical output with one uninterrupted color."""
    result = []
    port_colors = ((20, 0, 0), (0, 20, 0), (0, 0, 20))
    for (start_universe, universe_count, _), color in zip(PORTS, port_colors):
        payload = wire_grb(color) * PIXELS_PER_UNIVERSE
        for offset in range(universe_count):
            result.append((start_universe + offset, payload))
    return tuple(result)


def build_panel_identity_frames() -> tuple[tuple[int, bytes], ...]:
    """Color panels while preserving each GICO port's universe capacity."""
    black = wire_grb((0, 0, 0))
    pixels = [black] * (9 * PIXELS_PER_UNIVERSE)
    for start, count, color in (
        (0, 510, (20, 0, 0)),
        (510, 269, (0, 20, 0)),
        (1020, 398, (0, 0, 20)),
    ):
        pixels[start:start + count] = [wire_grb(color)] * count

    result = []
    for offset, universe in enumerate(range(0, 9)):
        first = offset * PIXELS_PER_UNIVERSE
        payload = b"".join(pixels[first:first + PIXELS_PER_UNIVERSE])
        result.append((universe, payload))
    return tuple(result)


def build_one_universe_frames(active_universe: int) -> tuple[tuple[int, bytes], ...]:
    """Light one GICO UI universe (1..9) and blank all other universes."""
    if active_universe not in range(1, 10):
        raise ValueError("active_universe must be in the range 1..9")
    white = wire_grb((20, 20, 20)) * PIXELS_PER_UNIVERSE
    black = wire_grb((0, 0, 0)) * PIXELS_PER_UNIVERSE
    return tuple(
        (wire_universe, white if wire_universe == active_universe - 1 else black)
        for wire_universe in range(0, 9)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="10.0.0.244")
    parser.add_argument("--local-address", default="10.0.0.125")
    parser.add_argument("--source-port", type=int, default=6454)
    parser.add_argument("--mode", choices=("length", "identity", "panel"), default="length")
    parser.add_argument("--one-universe", type=int, choices=range(1, 10))
    parser.add_argument("--seconds", type=float, default=25.0)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    if args.one_universe is not None:
        frames = build_one_universe_frames(args.one_universe)
    elif args.mode == "identity":
        frames = build_identity_frames()
    elif args.mode == "panel":
        frames = build_panel_identity_frames()
    else:
        frames = build_frames()
    deadline = time.monotonic() + args.seconds
    sent = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((args.local_address, args.source_port))
        while time.monotonic() < deadline:
            started = time.monotonic()
            for universe, payload in frames:
                udp.sendto(artdmx_packet(universe, payload), (args.target, 6454))
                sent += 1
            time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - started)))
    descriptions = {
        "identity": "port1=red port2=green port3=blue",
        "panel": "middle=red upper=green lower=blue hardware_starts=0/510/1020",
        "length": "active=red padding=green",
    }
    description = (
        f"one_universe=U{args.one_universe} white others=black"
        if args.one_universe is not None
        else descriptions[args.mode]
    )
    print(f"sent={sent} target={args.target} ports=4/2/3 {description} exact_channels=510 sequence=0")


if __name__ == "__main__":
    main()
