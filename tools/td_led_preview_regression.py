"""Non-destructive live audit for shortcut dialog 1 (LED Preview).

Run inside TouchDesigner's Textport.  The tool reads the live project and
temporarily changes preview-only parameters to prove their bindings.  Every
changed value is restored in a finally block.  It does not save the project,
write a mapping or touch Art-Net.
"""

from __future__ import annotations

import json


PREVIEW = "/project1/LED_PREVIEW_OUT"
PROTOTYPE = "/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype"
COLOR_SOURCE = "/project1/null5"
CURRENT_LED_COUNT = 3744
CURRENT_SIDE_COUNT = 1184
PANEL_COUNT = 10
PANEL_SIZE = 256

SUFFIX_TARGET = {
    "tlx": "pintopleftx",
    "tly": "pintoplefty",
    "trx": "pintoprightx",
    "try": "pintoprighty",
    "blx": "pinbotleftx",
    "bly": "pinbotlefty",
    "brx": "pinbotrightx",
    "bry": "pinbotrighty",
}


def _bound_value(owner, parameter_name, target, target_parameter, delta=0.001):
    parameter = getattr(owner.par, parameter_name)
    original = parameter.eval()
    try:
        parameter.val = float(original) + delta
        actual = getattr(target.par, target_parameter).eval()
        expected = float(original) + delta
        return {
            "parameter": parameter_name,
            "target": target.path + "." + target_parameter,
            "expected": expected,
            "actual": actual,
            "ok": abs(float(actual) - expected) < 1e-7,
        }
    finally:
        parameter.val = original


def audit():
    preview = op(PREVIEW)
    owner = op(PROTOTYPE)
    source = owner.op("cal_source_instances") if owner else None
    side = owner.op("cal_side_instances") if owner else None
    rear = owner.op("cal_rear_instances") if owner else None
    color = op(COLOR_SOURCE)
    callback = op("/project1/shortcut_hub/shortcut_callbacks")

    report = {
        "projectSaved": False,
        "networkChanged": False,
        "exists": bool(preview and owner and source and side and rear and color),
        "errors": list(owner.errors(recurse=True)) if owner else ["prototype missing"],
        "preview": {
            "path": preview.path if preview else None,
            "resolution": [preview.width, preview.height] if preview else None,
            "selectedTOP": preview.par.top.eval() if preview else None,
        },
        "counts": {
            "expectedCurrent": CURRENT_LED_COUNT,
            "preview": source.numSamples if source else None,
            "colorSource": color.numSamples if color else None,
            "expectedSide": CURRENT_SIDE_COUNT,
            "previewSide": side.numSamples if side else None,
            "previewRear": rear.numSamples if rear else None,
            "expectedRear": PANEL_COUNT * PANEL_SIZE,
            "displayedRearStart": owner.par.Panelsstartindex.eval() if owner else None,
            "actualRearStart": int(rear.par.start.eval()) if rear else None,
        },
        "shortcutCallback": {
            "hasOnKey": hasattr(callback.module, "onKey") if callback else False,
            "hasKeyEvent": hasattr(callback.module, "keyEvent") if callback else False,
        },
        "bindings": [],
    }

    if not report["exists"]:
        return report

    for prefix, node_name in (("Side", "cal_side_cornerpin"), ("Rear", "cal_rear_cornerpin")):
        target = owner.op(node_name)
        for suffix, target_parameter in SUFFIX_TARGET.items():
            report["bindings"].append(
                _bound_value(owner, prefix + suffix, target, target_parameter)
            )
    for panel in range(PANEL_COUNT):
        target = owner.op("tile_mesh_pin_%02d" % panel)
        for suffix, target_parameter in SUFFIX_TARGET.items():
            report["bindings"].append(
                _bound_value(owner, "F%02d%s" % (panel, suffix), target, target_parameter)
            )

    report["bindingSummary"] = {
        "tested": len(report["bindings"]),
        "passed": sum(1 for item in report["bindings"] if item["ok"]),
    }
    return report


print(json.dumps(audit(), indent=2, default=str))
