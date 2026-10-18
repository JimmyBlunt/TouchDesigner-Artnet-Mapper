"""Apply the prepared lower-side-panel scan to the open TouchDesigner project.

Run inside TouchDesigner. Network output is stopped first. The script updates
only ``/project1/pixelblaze_mapper/map_active`` indices 781..1179 and the lower
WS2812 routing length. It deliberately does not save the TOE or restart Art-Net.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


LOCAL_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
SOURCE_SCAN = LOCAL_ROOT / "mappings" / "sources" / "lower_side_scan_0_398_raw_2026-08-24.json"
if str(LOCAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_ROOT))

from pixelblaze_mapper import lower_side_rewire as _rewire  # noqa: E402

_rewire = importlib.reload(_rewire)
EXPECTED_NEW_POINTS = _rewire.EXPECTED_NEW_POINTS
LOWER_START = _rewire.LOWER_START
REAR_START = _rewire.REAR_START
load_coordinate_array = _rewire.load_coordinate_array
replace_lower_panel = _rewire.replace_lower_panel


def _stop_outputs():
    for path in (
        "/project1/multi_controller_output/dmxout_ws2812_node",
        "/project1/multi_controller_output/dmxout_apa102_esp",
        "/project1/dmxout1",
        "/project1/esp_artnet_out",
    ):
        node = op(path)
        if node is not None and getattr(node.par, "active", None) is not None:
            node.par.active = False


def _table_coordinates(table):
    return tuple(
        (float(table[row, "tx"]), float(table[row, "ty"]), float(table[row, "tz"]))
        for row in range(1, table.numRows)
    )


def _write_mapping(table, coordinates):
    table.clear()
    table.appendRow(("index", "tx", "ty", "tz"))
    for index, point in enumerate(coordinates):
        table.appendRow((index,) + tuple("%.12g" % value for value in point))


def _coordinates_match(left, right, tolerance=1e-9):
    """Compare DAT coordinates without rejecting harmless text rounding."""
    return len(left) == len(right) and all(
        abs(a - b) <= tolerance
        for point_a, point_b in zip(left, right)
        for a, b in zip(point_a, point_b)
    )


def apply():
    _stop_outputs()
    table = op("/project1/pixelblaze_mapper/map_active")
    if table is None:
        raise RuntimeError("Missing /project1/pixelblaze_mapper/map_active")
    current = _table_coordinates(table)
    scan = load_coordinate_array(SOURCE_SCAN)
    combined, report = replace_lower_panel(current, scan)

    backup = op("/project1/pixelblaze_mapper/map_before_lower_side_rewire_399")
    if backup is None:
        backup = op("/project1/pixelblaze_mapper").create(tableDAT, "map_before_lower_side_rewire_399")
        _write_mapping(backup, current)
    _write_mapping(table, combined)

    # Route indices 0..398. The remaining three physical Port-3 slots stay
    # black instead of leaking the first rear-panel pixels.
    segments = op("/project1/multi_controller_output/segment_config")
    if segments is not None:
        for row in range(1, segments.numRows):
            if str(segments[row, "name"]) == "WS_SIDE_LOWER":
                segments[row, "count"] = EXPECTED_NEW_POINTS

    led_map = op("/project1/LedMap")
    if led_map is not None:
        led_map.cook(force=True)
    for path in ("/project1/math1", "/project1/LED_PREVIEW_OUT"):
        node = op(path)
        if node is not None:
            node.cook(force=True)

    if table.numRows != 3741:
        raise RuntimeError("Active mapping must remain 3740 points plus header")
    written = _table_coordinates(table)
    if not _coordinates_match(written[:LOWER_START], current[:LOWER_START]):
        raise RuntimeError("Preceding side panels changed unexpectedly")
    if not _coordinates_match(written[REAR_START:], current[REAR_START:]):
        raise RuntimeError("Rear panels changed unexpectedly")
    return report


if "op" in globals():
    print(apply())
