"""Apply the full three-panel rescan to the open TouchDesigner project."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


LOCAL_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
SOURCE_SCAN = LOCAL_ROOT / "mappings" / "sources" / "complete_new_0_1183_raw_2026-08-24.json"
if str(LOCAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_ROOT))

from pixelblaze_mapper import complete_side_rescan as _rescan  # noqa: E402
from pixelblaze_mapper import multi_controller as _router  # noqa: E402
from pixelblaze_mapper.lower_side_rewire import load_coordinate_array  # noqa: E402

_rescan = importlib.reload(_rescan)
_router = importlib.reload(_router)


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


def _write_segments(table):
    table.clear()
    for row in _router.segment_rows(_router.default_router_config("10.0.0.125")):
        table.appendRow(row)


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
    combined, report = _rescan.rebuild_complete_side_mapping(current, scan)

    parent = op("/project1/pixelblaze_mapper")
    backup = parent.op("map_before_complete_new_3740")
    if backup is None:
        backup = parent.create(tableDAT, "map_before_complete_new_3740")
        _write_mapping(backup, current)
    _write_mapping(table, combined)

    segments = op("/project1/multi_controller_output/segment_config")
    if segments is not None:
        _write_segments(segments)

    for path in (
        "/project1/LedMap",
        "/project1/null4",
        "/project1/effect_sample_uv",
        "/project1/topto1",
        "/project1/math1",
        "/project1/LED_PREVIEW_OUT",
    ):
        node = op(path)
        if node is not None:
            node.cook(force=True)

    if table.numRows != _rescan.NEW_TOTAL_POINTS + 1:
        raise RuntimeError("Active mapping must contain 3,744 points plus header")
    written = _table_coordinates(table)
    if not _coordinates_match(
        written[_rescan.NEW_REAR_START:], current[_rescan.OLD_REAR_START:]
    ):
        raise RuntimeError("Rear-wall coordinates changed unexpectedly")
    return report


if "op" in globals():
    print(apply())
