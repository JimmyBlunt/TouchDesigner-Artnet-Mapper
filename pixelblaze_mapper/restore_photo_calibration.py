"""Restore the last complete per-panel photo calibration in TouchDesigner.

The corner values come from
``PixelblazeMapper_WORKING_PHASE2_PHOTO.33.toe`` (2026-08-16 09:54).
The corner values were measured in an older project, but the current canonical
map contains 1184 side-wall points followed by ten complete 16x16 rear panels.

Run this file inside TouchDesigner's Textport. It modifies only the isolated
photo-preview component and never saves the project or touches network output.
"""

from __future__ import annotations

import sys

LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

from pixelblaze_mapper.installation_contract import REAR, REAR_PANEL_COUNT, REAR_PANEL_PIXELS, TOTAL_PIXELS


PROTOTYPE = "/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype"
CANONICAL_PREVIEW = "/project1/LED_PREVIEW_OUT"
CALIBRATION_SOURCE = "PixelblazeMapper_WORKING_PHASE2_PHOTO.33.toe"
REAR_START = REAR.start
PANEL_SIZE = REAR_PANEL_PIXELS
PANEL_COUNT = REAR_PANEL_COUNT

# Corner order: top-left, top-right, bottom-left, bottom-right. Each point is
# (x, y) in the 960x960 photo-preview's normalized coordinates.
PANEL_CORNERS = (
    ((0.290, 0.940), (0.402, 0.957), (0.284, 0.840), (0.411, 0.840)),
    ((0.450, 0.963), (0.556, 0.969), (0.444, 0.848), (0.556, 0.840)),
    ((0.290, 0.816), (0.411, 0.816), (0.290, 0.695), (0.407, 0.689)),
    ((0.427, 0.816), (0.556, 0.816), (0.427, 0.689), (0.556, 0.689)),
    ((0.284, 0.664), (0.411, 0.664), (0.284, 0.539), (0.411, 0.539)),
    ((0.427, 0.664), (0.556, 0.664), (0.427, 0.539), (0.556, 0.539)),
    ((0.284, 0.513), (0.411, 0.513), (0.284, 0.387), (0.411, 0.387)),
    ((0.427, 0.513), (0.556, 0.513), (0.427, 0.387), (0.556, 0.395)),
    ((0.281, 0.357), (0.411, 0.357), (0.281, 0.220), (0.411, 0.220)),
    ((0.427, 0.357), (0.556, 0.357), (0.427, 0.220), (0.556, 0.220)),
)

PARAMETER_SUFFIXES = ("tlx", "tly", "trx", "try", "blx", "bly", "brx", "bry")
PIN_PARAMETERS = (
    "pinp11", "pinp12", "pinp21", "pinp22",
    "pinp31", "pinp32", "pinp41", "pinp42",
)


def _flat_corners(corners):
    return tuple(value for point in corners for value in point)


def _custom_page(owner, name):
    for page in owner.customPages:
        if page.name == name:
            return page
    return owner.appendCustomPage(name)


def _ensure_panel_parameters(owner):
    page = _custom_page(owner, "Einzelfaecher")
    for panel, corners in enumerate(PANEL_CORNERS):
        header_name = "Fach%d" % (panel + 1)
        if getattr(owner.par, header_name, None) is None:
            page.appendHeader(header_name, label="Fach %d" % (panel + 1))
        for suffix, value in zip(PARAMETER_SUFFIXES, _flat_corners(corners)):
            name = "F%02d%s" % (panel, suffix)
            parameter = getattr(owner.par, name, None)
            if parameter is None:
                parameter = page.appendFloat(name, label=name)[0]
                parameter.min = -0.25
                parameter.max = 1.25
                parameter.clampMin = False
                parameter.clampMax = False
            parameter.default = value
            parameter.val = value


def _bind_panel_pins(owner):
    for panel in range(PANEL_COUNT):
        pin = owner.op("tile_mesh_pin_%02d" % panel)
        if pin is None:
            raise RuntimeError("Missing rear-panel Corner Pin %02d" % panel)
        for target, suffix in zip(PIN_PARAMETERS, PARAMETER_SUFFIXES):
            getattr(pin.par, target).expr = "parent().par.F%02d%s" % (panel, suffix)


def _validate_current_map(owner):
    source = owner.op("cal_source_instances")
    if source is None or source.numSamples != TOTAL_PIXELS:
        raise RuntimeError("Expected the current %d-pixel preview map" % TOTAL_PIXELS)
    rear = owner.op("cal_rear_instances")
    if rear is None or rear.numSamples != PANEL_COUNT * PANEL_SIZE:
        raise RuntimeError("Rear preview must contain ten complete 16x16 panels")
    if int(rear.par.start.eval()) != REAR_START:
        raise RuntimeError("Rear preview must start at sample %d" % REAR_START)


def restore():
    owner = op(PROTOTYPE)
    if owner is None:
        raise RuntimeError("Missing photo-preview component: " + PROTOTYPE)

    _validate_current_map(owner)
    _ensure_panel_parameters(owner)
    _bind_panel_pins(owner)

    # Restore presentation values from the same calibrated snapshot. Geometry
    # values for the side wall were already unchanged.
    owner.par.Backgroundopacity = 0.72
    owner.par.Rearopacity = 0.945
    owner.par.Panelsstartindex = REAR_START
    owner.par.Panelsstartindex.readOnly = True
    owner.par.Status = "restored complete per-panel calibration from PHOTO.33 | rear start %d" % REAR_START

    # Keep a still image pinned to frame zero. Older saved nodes retained the
    # default timeline expression and could turn the reference photo black.
    movie = owner.op("background_file")
    if movie is not None:
        movie.par.play = False
        movie.par.index.expr = ""
        movie.par.index = 0
        if getattr(movie.par, "indexunit", None) is not None:
            movie.par.indexunit = "frames"
        # Changing the file/index state does not reliably reload a still image
        # in every TouchDesigner build. Without this pulse the node may keep a
        # transparent 128x128 placeholder even though the file exists.
        reload_pulse = getattr(movie.par, "reloadpulse", None)
        if reload_pulse is not None:
            reload_pulse.pulse()
        movie.cook(force=True)

    output = owner.op("prototype_out")
    if output is None:
        raise RuntimeError("Missing photo-composite output: prototype_out")
    output.cook(force=True)

    # The project contains several historical previews. Keep one stable alias
    # for users and shortcuts; it must show the photo composite, not the old
    # black-background /project1/Preview/render1 output.
    preview_alias = op(CANONICAL_PREVIEW)
    if preview_alias is None:
        raise RuntimeError("Missing canonical LED preview: " + CANONICAL_PREVIEW)
    preview_alias.par.top = output.path
    preview_alias.cook(force=True)

    errors = list(owner.errors(recurse=True))
    if errors:
        raise RuntimeError("Photo-preview errors after restore: %s" % errors)

    return {
        "source": CALIBRATION_SOURCE,
        "rearStart": REAR_START,
        "panels": PANEL_COUNT,
        "cornerValues": PANEL_COUNT * 8,
        "output": output.path,
        "previewAlias": preview_alias.path,
        "projectSaved": False,
        "networkChanged": False,
    }


print(restore())
