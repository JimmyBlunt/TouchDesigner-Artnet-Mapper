"""Install the exported Pixelblaze XYZ/UV lookup into the live TD project.

Run this file through TouchDesigner's Python environment.  It creates only
DAT tables and never enables or changes Art-Net output parameters.
"""

from __future__ import annotations

import json
from pathlib import Path


LOOKUP_FILE = (
    Path(__file__).resolve().parents[1]
    / "mappings/side_spatial_lookup_complete_new_2026-08-24.json"
)
ROOT = "/project1/pixelblaze_mapper"


def _table(parent, name):
    result = parent.op(name)
    return result if result is not None else parent.create(tableDAT, name)


def build():
    document = json.loads(LOOKUP_FILE.read_text(encoding="utf-8"))
    parent = op(ROOT)
    if parent is None:
        raise RuntimeError("Missing %s" % ROOT)

    lookup = _table(parent, "side_spatial_lookup")
    lookup.clear()
    lookup.appendRow(
        ["index", "panel", "x", "y", "z", "u", "v", "column", "row", "coordinate_quality"]
    )
    for panel in document["panels"]:
        for led in panel["leds"]:
            lookup.appendRow(
                [
                    led["index"], led["panel"], led["x"], led["y"], led["z"],
                    led["u"], led["v"], led["column"], led["row"],
                    led["coordinate_quality"],
                ]
            )

    status = _table(parent, "side_spatial_status")
    status.clear()
    status.appendRow(["property", "value"])
    status.appendRow(["schema", document["schema"]])
    status.appendRow(["source", document["source"]])
    status.appendRow(["wire_order_changed", int(document["wire_order_changed"])])
    status.appendRow(["measured", document["coordinate_quality"]["measured"]])
    status.appendRow(["estimated", document["coordinate_quality"]["estimated"]])
    status.appendRow(
        ["estimated_indices", ",".join(map(str, document["coordinate_quality"]["estimated_indices"]))]
    )
    for panel in document["panels"]:
        status.appendRow(
            [panel["name"], "%s LEDs | %sx%s logical" % (
                panel["count"], panel["width"], panel["height"]
            )]
        )

    lookup.nodeX, lookup.nodeY = -780, -1040
    status.nodeX, status.nodeY = -540, -1040
    return {
        "lookupRows": lookup.numRows - 1,
        "measured": document["coordinate_quality"]["measured"],
        "estimated": document["coordinate_quality"]["estimated"],
        "networkOutputsChanged": False,
        "projectSaved": False,
    }


print(build())
