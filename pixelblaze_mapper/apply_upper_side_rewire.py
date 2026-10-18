"""Apply the prepared upper-panel scan to the open TouchDesigner project."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


LOCAL_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
SOURCE_SCAN = LOCAL_ROOT / "mappings" / "sources" / "upper_side_scan_0_269_raw_2026-08-24.json"
if str(LOCAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_ROOT))

from pixelblaze_mapper import upper_side_rewire as _rewire  # noqa: E402
from pixelblaze_mapper.lower_side_rewire import load_coordinate_array  # noqa: E402

_rewire = importlib.reload(_rewire)


def _stop_outputs():
    sender = op("/project1/multi_controller_output/artnet_510_sender_callbacks")
    if sender is not None:
        try:
            sender.module.stop()
        except Exception:
            pass
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
    combined, report = _rewire.replace_upper_panel(current, scan)

    backup = op("/project1/pixelblaze_mapper/map_before_upper_side_rewire_270")
    if backup is None:
        backup = op("/project1/pixelblaze_mapper").create(tableDAT, "map_before_upper_side_rewire_270")
        _write_mapping(backup, current)
    _write_mapping(table, combined)

    segments = op("/project1/multi_controller_output/segment_config")
    if segments is not None:
        for row in range(1, segments.numRows):
            if str(segments[row, "name"]) == "WS_SIDE_UPPER_TAIL":
                segments[row, "count"] = 100

    for path in (
        "/project1/LedMap",
        "/project1/effect_sample_uv",
        "/project1/topto1",
        "/project1/math1",
        "/project1/LED_PREVIEW_OUT",
    ):
        node = op(path)
        if node is not None:
            node.cook(force=True)

    if table.numRows != 3741:
        raise RuntimeError("Active mapping must remain 3740 points plus header")
    written = _table_coordinates(table)
    if not _coordinates_match(written[:_rewire.UPPER_START], current[:_rewire.UPPER_START]):
        raise RuntimeError("Middle panel changed unexpectedly")
    if not _coordinates_match(written[_rewire.UPPER_END:], current[_rewire.UPPER_END:]):
        raise RuntimeError("Lower or rear panels changed unexpectedly")
    return report


if "op" in globals():
    print(apply())
