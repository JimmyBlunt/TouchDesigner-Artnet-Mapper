"""Add a non-destructive two-plane photo calibration to the Phase-2 preview.

Run inside TouchDesigner after build_phase2_preview.py.  It modifies only the
isolated Phase-2 prototype and never calls project.save().
"""

import json
import sys

LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

from pixelblaze_mapper.installation_contract import REAR, SIDE_PIXEL_COUNT, TOTAL_PIXELS


PROTOTYPE = "/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype"
SOURCE_GEO = "/project1/pixelblaze_mapper/preview3d/led_points_geo"
SOURCE_INSTANCES = "/project1/pixelblaze_mapper/preview3d/instance_data"
SIDE_FIRST = 0
SIDE_LAST = SIDE_PIXEL_COUNT - 1
REAR_FIRST = REAR.start
REAR_LAST = TOTAL_PIXELS - 1
RESOLUTION = 960


OWNED_NODES = (
    "cal_source_instances", "cal_side_instances", "cal_rear_instances",
    "cal_side_geo", "cal_rear_geo", "cal_side_render", "cal_rear_render",
    "cal_side_crop", "cal_rear_crop",
    "cal_side_cornerpin", "cal_rear_cornerpin", "cal_side_level",
    "cal_rear_level", "cal_leds", "cal_over_background",
    "calibration_output_switch", "calibration_callbacks",
    "README_two_plane_calibration",
)


def _set(node, name, value=None, expression=None):
    par = getattr(node.par, name, None)
    if par is None:
        return False
    if expression is not None:
        par.expr = expression
    else:
        par.val = value
    return True


def _connect(source, target, index=0):
    target.inputConnectors[index].connect(source)


def _add_float(page, name, label, default):
    p = page.appendFloat(name, label=label)[0]
    p.default = default
    p.val = default
    p.min = -2
    p.max = 3
    p.clampMin = False
    p.clampMax = False
    return p


def _ensure_parameters(owner):
    if getattr(owner.par, "Calibrationenabled", None) is not None:
        return
    page = owner.appendCustomPage("Photo Calibration")
    p = page.appendToggle("Calibrationenabled", label="Two-plane calibration")[0]
    p.default = True
    p.val = True
    p = page.appendToggle("Showside", label="Show side wall LEDs")[0]
    p.default = True
    p.val = True
    p = page.appendToggle("Showrear", label="Show rear panel LEDs")[0]
    p.default = True
    p.val = True
    p = page.appendFloat("Sideopacity", label="Side wall opacity")[0]
    p.default = 1
    p.val = 1
    p.min = 0
    p.max = 1
    p.clampMin = True
    p.clampMax = True
    p = page.appendFloat("Rearopacity", label="Rear panel opacity")[0]
    p.default = 1
    p.val = 1
    p.min = 0
    p.max = 1
    p.clampMin = True
    p.clampMax = True

    page.appendHeader("Sidecorners", label="Side wall corners")
    for name, label, default in (
        ("Sidetlx", "Top left X", 0.605), ("Sidetly", "Top left Y", 0.94),
        ("Sidetrx", "Top right X", 0.70), ("Sidetry", "Top right Y", 0.90),
        ("Sideblx", "Bottom left X", 0.59), ("Sidebly", "Bottom left Y", 0.18),
        ("Sidebrx", "Bottom right X", 0.73), ("Sidebry", "Bottom right Y", 0.14),
    ):
        _add_float(page, name, label, default)

    page.appendHeader("Rearcorners", label="Rear panel corners")
    for name, label, default in (
        ("Reartlx", "Top left X", 0.292), ("Reartly", "Top left Y", 0.94),
        ("Reartrx", "Top right X", 0.584), ("Reartry", "Top right Y", 0.93),
        ("Rearblx", "Bottom left X", 0.287), ("Rearbly", "Bottom left Y", 0.21),
        ("Rearbrx", "Bottom right X", 0.574), ("Rearbry", "Bottom right Y", 0.21),
    ):
        _add_float(page, name, label, default)

    page.appendPulse("Resetcalibration", label="Reset both planes")
    split = page.appendInt("Panelsstartindex", label="Rear panels start index")[0]
    split.default = REAR_FIRST
    split.val = REAR_FIRST
    split.readOnly = True


def _trim(parent, name, source, start, end):
    node = parent.create(trimCHOP, name)
    _connect(source, node)
    _set(node, "relative", "abs")
    _set(node, "start", start)
    _set(node, "startunit", "samples")
    _set(node, "end", end)
    _set(node, "endunit", "samples")
    _set(node, "discard", "exterior")
    _set(node, "shiftstart", True)
    _set(node, "timeslice", False)
    return node


def _render(parent, name, camera, geometry):
    node = parent.create(renderTOP, name)
    _set(node, "camera", camera.path)
    _set(node, "geometry", geometry.path)
    _set(node, "lights", "")
    _set(node, "antialias", "aa2")
    for channel in "rgba":
        _set(node, "bgcolor" + channel, 0)
    _set(node, "premultrgbbyalpha", True)
    _set(node, "outputresolution", "custom")
    _set(node, "resolutionw", RESOLUTION)
    _set(node, "resolutionh", RESOLUTION)
    return node


def _corner(parent, name, source, prefix):
    node = parent.create(cornerpinTOP, name)
    _connect(source, node)
    _set(node, "outputresolution", "custom")
    _set(node, "resolutionw", RESOLUTION)
    _set(node, "resolutionh", RESOLUTION)
    _set(node, "extractmapping", "perspective")
    bindings = (
        ("pinp11", prefix + "tlx"), ("pinp12", prefix + "tly"),
        ("pinp21", prefix + "trx"), ("pinp22", prefix + "try"),
        ("pinp31", prefix + "blx"), ("pinp32", prefix + "bly"),
        ("pinp41", prefix + "brx"), ("pinp42", prefix + "bry"),
    )
    for target, custom in bindings:
        _set(node, target, expression="parent().par." + custom)
    return node


def _crop(parent, name, source, left, right, bottom, top):
    """Remove transparent render margins before perspective placement."""
    node = parent.create(cropTOP, name)
    _connect(source, node)
    for par_name, value in (
        ("cropleft", left), ("cropright", right),
        ("cropbottom", bottom), ("croptop", top),
    ):
        _set(node, par_name, value)
    _set(node, "extend", "zero")
    _set(node, "outputresolution", "custom")
    _set(node, "resolutionw", RESOLUTION)
    _set(node, "resolutionh", RESOLUTION)
    return node


def _level(parent, name, source, show_par, opacity_par):
    node = parent.create(levelTOP, name)
    _connect(source, node)
    _set(
        node,
        "opacity",
        expression="parent().par.%s if parent().par.%s else 0" % (opacity_par, show_par),
    )
    return node


def build():
    owner = op(PROTOTYPE)
    source_geo = op(SOURCE_GEO)
    camera = owner.op("interactive_camera") if owner else None
    background = owner.op("background_opacity") if owner else None
    simple_composite = owner.op("background_plus_leds") if owner else None
    output = owner.op("prototype_out") if owner else None
    if None in (owner, source_geo, camera, background, simple_composite, output):
        raise RuntimeError("Phase-2 base preview is incomplete")

    _ensure_parameters(owner)
    for name in OWNED_NODES:
        node = owner.op(name)
        if node is not None:
            node.destroy()

    source = owner.create(selectCHOP, "cal_source_instances")
    _set(source, "chop", SOURCE_INSTANCES)
    _set(source, "channames", "tx ty tz r g b")
    side_data = _trim(owner, "cal_side_instances", source, SIDE_FIRST, SIDE_LAST)
    rear_data = _trim(owner, "cal_rear_instances", source, REAR_FIRST, REAR_LAST)

    side_geo = owner.copy(source_geo, name="cal_side_geo")
    rear_geo = owner.copy(source_geo, name="cal_rear_geo")
    for geo, data in ((side_geo, side_data), (rear_geo, rear_data)):
        geo.par.instanceop = data.path
        geo.par.instancecolorop = data.path
        # The source preview GEO has a presentation-only rotation.  Calibrated
        # world-space rendering must use the actual mapping axes; the camera,
        # not the geometry, owns the view transform.
        geo.par.rx = 0
        geo.par.ry = 0
        geo.par.rz = 0
        geo.par.render = True

    side_render = _render(owner, "cal_side_render", camera, side_geo)
    rear_render = _render(owner, "cal_rear_render", camera, rear_geo)
    # Bounds measured from the transparent 960x960 renders.  Cropping them
    # makes the public corner coordinates describe the LEDs, not empty canvas.
    side_crop = _crop(owner, "cal_side_crop", side_render, 0.13, 0.89, 0.18, 0.84)
    # Crop TOP uses absolute edge positions for fraction units.  The previous
    # values treated the right edge as a width, which discarded the right-hand
    # column and part of the bottom row of the 2x5 rear panel grid.
    rear_crop = _crop(owner, "cal_rear_crop", rear_render, 0.36, 0.64, 0.16, 0.84)
    side_pin = _corner(owner, "cal_side_cornerpin", side_crop, "Side")
    rear_pin = _corner(owner, "cal_rear_cornerpin", rear_crop, "Rear")
    side_level = _level(owner, "cal_side_level", side_pin, "Showside", "Sideopacity")
    rear_level = _level(owner, "cal_rear_level", rear_pin, "Showrear", "Rearopacity")

    leds = owner.create(overTOP, "cal_leds")
    _connect(side_level, leds, 0)
    _connect(rear_level, leds, 1)
    _set(leds, "outputresolution", "custom")
    _set(leds, "resolutionw", RESOLUTION)
    _set(leds, "resolutionh", RESOLUTION)

    combined = owner.create(overTOP, "cal_over_background")
    _connect(leds, combined, 0)
    _connect(background, combined, 1)
    _set(combined, "outputresolution", "custom")
    _set(combined, "resolutionw", RESOLUTION)
    _set(combined, "resolutionh", RESOLUTION)

    switch = owner.create(switchTOP, "calibration_output_switch")
    _connect(simple_composite, switch, 0)
    _connect(combined, switch, 1)
    _set(switch, "index", expression="1 if parent().par.Calibrationenabled else 0")
    output.inputConnectors[0].connect(switch)

    callbacks = owner.create(parameterexecuteDAT, "calibration_callbacks")
    callbacks.par.op = owner.path
    callbacks.par.pars = "Resetcalibration"
    callbacks.par.onpulse = True
    callbacks.text = '''def onPulse(par):
    if par.name != 'Resetcalibration':
        return
    owner = parent()
    defaults = {
        'Sidetlx':0.605, 'Sidetly':0.94, 'Sidetrx':0.70, 'Sidetry':0.90,
        'Sideblx':0.59, 'Sidebly':0.18, 'Sidebrx':0.73, 'Sidebry':0.14,
        'Reartlx':0.292, 'Reartly':0.94, 'Reartrx':0.584, 'Reartry':0.93,
        'Rearblx':0.287, 'Rearbly':0.21, 'Rearbrx':0.574, 'Rearbry':0.21,
    }
    for name, value in defaults.items():
        getattr(owner.par, name).val = value
    owner.par.Status = 'two-plane calibration reset'
    return
'''

    readme = owner.create(textDAT, "README_two_plane_calibration")
    readme.text = """TWO-PLANE PHOTO CALIBRATION

Index 0-1183: side-wall contour mapping.
Index 1184-3743: ten rear-wall 16x16 panels.

The interactive camera moves both groups together.  The Side* and Rear*
corner parameters then align each wall plane independently over the photo.
Switch Calibrationenabled off to return to the original one-layer preview.
"""

    # Keep the added network readable.
    positions = {
        "cal_source_instances": (-980, -520), "cal_side_instances": (-780, -470),
        "cal_rear_instances": (-780, -620), "cal_side_geo": (-560, -470),
        "cal_rear_geo": (-560, -620), "cal_side_render": (-320, -470),
        "cal_rear_render": (-320, -620), "cal_side_cornerpin": (-80, -470),
        "cal_side_crop": (-190, -470), "cal_rear_crop": (-190, -620),
        "cal_rear_cornerpin": (-80, -620), "cal_side_level": (150, -470),
        "cal_rear_level": (150, -620), "cal_leds": (380, -540),
        "cal_over_background": (600, -500), "calibration_output_switch": (820, -420),
        "calibration_callbacks": (380, -700), "README_two_plane_calibration": (600, -700),
    }
    for name, (x, y) in positions.items():
        node = owner.op(name)
        if node:
            node.nodeX, node.nodeY = x, y

    output.cook(force=True)
    result = {
        "prototype": owner.path,
        "side_samples": side_data.numSamples,
        "rear_samples": rear_data.numSamples,
        "split_index": REAR_FIRST,
        "output": output.path,
        "errors": list(owner.errors(recurse=True)),
        "project_saved": False,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()
