"""Build an isolated interactive/background preview inside Pixelblaze Mapper.

Run this script inside TouchDesigner's Python environment. It intentionally owns
only this subtree:

    /project1/pixelblaze_mapper/preview3d/
        phase2_interaction_background_prototype

It never saves the project and never rewires mapping or DMX operators.
"""

import json


PREVIEW_PATH = "/project1/pixelblaze_mapper/preview3d"
PROTOTYPE_NAME = "phase2_interaction_background_prototype"
CAMERA_TEMPLATE = "/sys/TDTox/cameraViewport"
OUTPUT_RESOLUTION = 960


def _set_par(operator, name, value=None, expression=None):
    par = getattr(operator.par, name, None)
    if par is None:
        return False
    if expression is not None:
        par.expr = expression
    else:
        par.val = value
    return True


def _connect(source, destination, input_index=None):
    if input_index is None:
        source.outputConnectors[0].connect(destination)
    else:
        source.outputConnectors[0].connect(destination.inputConnectors[input_index])


def _clear_defaults(component):
    for child in list(component.children):
        child.destroy()


def _add_parameters(prototype):
    page = prototype.appendCustomPage("Phase 2 Preview")

    p = page.appendToggle("Backgroundenabled", label="Background Enabled")[0]
    p.val = False

    page.appendFile("Backgroundfile", label="Background Image File")
    page.appendPulse("Openbackground", label="Open Background...")
    page.appendPulse("Clearbackground", label="Clear Background")

    p = page.appendFloat("Backgroundopacity", label="Background Opacity")[0]
    p.val = 0.55
    p.min = 0
    p.max = 1
    p.clampMin = True
    p.clampMax = True

    p = page.appendMenu("Backgroundfit", label="Background Fit")[0]
    p.menuNames = ["contain", "cover", "stretch"]
    p.menuLabels = ["Contain / Fit Best", "Cover / Fit Outside", "Stretch / Fill"]
    p.val = "contain"

    p = page.appendMenu("Alignmentmode", label="Alignment Mode")[0]
    p.menuNames = ["simple", "cornerpin"]
    p.menuLabels = ["Simple 2D", "Perspective Corner Pin"]
    p.val = "simple"

    p = page.appendFloat("Ledopacity", label="LED Layer Opacity")[0]
    p.val = 1
    p.min = 0
    p.max = 1
    p.clampMin = True
    p.clampMax = True

    page.appendPulse("Homecamera", label="Home Camera")
    page.appendPulse("Framecamera", label="Frame All LEDs")
    page.appendPulse("Resetcamera", label="Reset Camera")

    p = page.appendToggle("Showaxes", label="Show Axes / Pivot")[0]
    p.val = True

    p = page.appendStr("Interactionhelp", label="Mouse Controls")[0]
    p.val = "LMB orbit | RMB pan | MMB/wheel dolly | F frame | H home"

    # Full-frame defaults. Values are public so a later UI can expose draggable
    # handles or numeric fields without changing the TOP network.
    pin_page = prototype.appendCustomPage("Background Corner Pin")
    pin_defaults = (
        ("Topleftx", "Top Left X", 0.0),
        ("Toplefty", "Top Left Y", 1.0),
        ("Toprightx", "Top Right X", 1.0),
        ("Toprighty", "Top Right Y", 1.0),
        ("Bottomleftx", "Bottom Left X", 0.0),
        ("Bottomlefty", "Bottom Left Y", 0.0),
        ("Bottomrightx", "Bottom Right X", 1.0),
        ("Bottomrighty", "Bottom Right Y", 0.0),
    )
    for name, label, default in pin_defaults:
        p = pin_page.appendFloat(name, label=label)[0]
        p.val = default
        p.min = -1
        p.max = 2

    p = page.appendStr("Status", label="Prototype Status")[0]
    p.val = "building"


def _create_camera(prototype, led_geometry):
    template = op(CAMERA_TEMPLATE)
    if template is None:
        raise RuntimeError("Official cameraViewport template is unavailable: " + CAMERA_TEMPLATE)

    camera = prototype.copy(template)
    camera.name = "interactive_camera"
    camera.nodeX = -100
    camera.nodeY = 420

    render = prototype.create(renderTOP, "interactive_led_render")
    render.nodeX = 230
    render.nodeY = 420
    _set_par(render, "camera", camera.path)
    _set_par(render, "geometry", led_geometry.path)
    _set_par(render, "resolutionw", OUTPUT_RESOLUTION)
    _set_par(render, "resolutionh", OUTPUT_RESOLUTION)
    _set_par(render, "antialias", "aa2")
    for channel in ("r", "g", "b", "a"):
        _set_par(render, "bgcolor" + channel, 0)
    _set_par(render, "premultrgbbyalpha", True)

    panel = camera.op("renderView")
    if panel is None:
        raise RuntimeError("Copied cameraViewport has no renderView panel")

    _set_par(camera, "Refpanel", panel.path)
    _set_par(camera, "Refrender", render.path)
    _set_par(camera, "Navigationmode", "viewport")
    _set_par(camera, "Tumblemouse", "left")
    _set_par(camera, "Panmouse", "right")
    _set_par(camera, "Dollymouse", "middle")
    _set_par(camera, "Boundsmode", "manual")
    _set_par(camera, "Minbounds1", -0.5)
    _set_par(camera, "Minbounds2", -0.5)
    _set_par(camera, "Minbounds3", -0.5)
    _set_par(camera, "Maxbounds1", 0.5)
    _set_par(camera, "Maxbounds2", 0.5)
    _set_par(camera, "Maxbounds3", 0.5)
    _set_par(camera, "Drawaxes", True)
    _set_par(camera, "Drawpivot", True)
    _set_par(camera, "Orthographic", False)
    panel.viewer = True

    return camera, panel, render


def _create_background_pipeline(prototype, led_render):
    placeholder = prototype.create(rampTOP, "background_placeholder")
    placeholder.nodeX = -760
    placeholder.nodeY = 100
    _set_par(placeholder, "resolutionw", OUTPUT_RESOLUTION)
    _set_par(placeholder, "resolutionh", OUTPUT_RESOLUTION)
    _set_par(placeholder, "type", "radial")
    # The exact ramp color parameter set varies between builds; defaults are a
    # safe neutral fallback when the optional settings are unavailable.

    movie = prototype.create(moviefileinTOP, "background_file")
    movie.nodeX = -760
    movie.nodeY = -40
    _set_par(movie, "file", expression="parent().par.Backgroundfile")
    _set_par(movie, "play", False)
    # A still image must stay on frame 0.  Movie File In otherwise keeps its
    # default timeline expression (me.time.frame), which walks past the only
    # frame of a JPEG/PNG and produces a black background.
    _set_par(movie, "index", 0)
    _set_par(movie, "indexunit", "frames")

    source_switch = prototype.create(switchTOP, "background_source_switch")
    source_switch.nodeX = -520
    source_switch.nodeY = 100
    _connect(placeholder, source_switch, 0)
    _connect(movie, source_switch, 1)
    _set_par(
        source_switch,
        "index",
        expression="1 if parent().par.Backgroundenabled and str(parent().par.Backgroundfile).strip() else 0",
    )

    fit = prototype.create(fitTOP, "background_fit")
    fit.nodeX = -300
    fit.nodeY = 100
    _connect(source_switch, fit)
    _set_par(fit, "outputresolution", "custom")
    _set_par(fit, "resolutionw", OUTPUT_RESOLUTION)
    _set_par(fit, "resolutionh", OUTPUT_RESOLUTION)
    _set_par(
        fit,
        "fit",
        expression="['fitbest','fitoutside','fill'][parent().par.Backgroundfit.menuIndex]",
    )
    for channel in ("r", "g", "b"):
        _set_par(fit, "bgcolor" + channel, 0.015)
    _set_par(fit, "bgcolora", 1)

    corner = prototype.create(cornerpinTOP, "background_cornerpin")
    corner.nodeX = -70
    corner.nodeY = 100
    _connect(fit, corner)
    _set_par(corner, "outputresolution", "custom")
    _set_par(corner, "resolutionw", OUTPUT_RESOLUTION)
    _set_par(corner, "resolutionh", OUTPUT_RESOLUTION)
    _set_par(corner, "extractmapping", "perspective")

    pin_bindings = {
        "pinp11": "Topleftx",
        "pinp12": "Toplefty",
        "pinp21": "Toprightx",
        "pinp22": "Toprighty",
        "pinp31": "Bottomleftx",
        "pinp32": "Bottomlefty",
        "pinp41": "Bottomrightx",
        "pinp42": "Bottomrighty",
    }
    for target, source in pin_bindings.items():
        _set_par(corner, target, expression="parent().par." + source)

    alignment_switch = prototype.create(switchTOP, "background_alignment_switch")
    alignment_switch.nodeX = 160
    alignment_switch.nodeY = 100
    _connect(fit, alignment_switch, 0)
    _connect(corner, alignment_switch, 1)
    _set_par(alignment_switch, "index", expression="parent().par.Alignmentmode.menuIndex")

    background_level = prototype.create(levelTOP, "background_opacity")
    background_level.nodeX = 380
    background_level.nodeY = 100
    _connect(alignment_switch, background_level)
    _set_par(
        background_level,
        "opacity",
        expression="parent().par.Backgroundopacity if parent().par.Backgroundenabled else 0",
    )

    led_level = prototype.create(levelTOP, "led_opacity")
    led_level.nodeX = 380
    led_level.nodeY = 370
    _connect(led_render, led_level)
    _set_par(led_level, "opacity", expression="parent().par.Ledopacity")

    composite = prototype.create(overTOP, "background_plus_leds")
    composite.nodeX = 620
    composite.nodeY = 260
    # Over TOP composites its first input over its second input.
    _connect(led_level, composite, 0)
    _connect(background_level, composite, 1)
    _set_par(composite, "outputresolution", "custom")
    _set_par(composite, "resolutionw", OUTPUT_RESOLUTION)
    _set_par(composite, "resolutionh", OUTPUT_RESOLUTION)
    _set_par(composite, "prefit", "fill")

    output = prototype.create(nullTOP, "prototype_out")
    output.nodeX = 870
    output.nodeY = 260
    _connect(composite, output)
    output.viewer = True

    return output


def _create_callbacks(prototype, camera):
    controller = prototype.create(textDAT, "background_controller")
    controller.nodeX = -720
    controller.nodeY = -220
    controller.text = '''def openBackground():
    path = ui.chooseFile(
        load=True,
        fileTypes=tdu.fileTypes['image'],
        title='Select wall/reference image'
    )
    if path:
        parent().par.Backgroundfile = path
        parent().par.Backgroundenabled = True
        parent().par.Status = 'background loaded: ' + path
    return path


def clearBackground():
    parent().par.Backgroundfile = ''
    parent().par.Backgroundenabled = False
    parent().par.Status = 'background cleared'
    return
'''

    callbacks = prototype.create(parameterexecuteDAT, "phase2_parameter_callbacks")
    callbacks.nodeX = -430
    callbacks.nodeY = -220
    callbacks.text = '''def onPulse(par):
    owner = parent()
    camera = owner.op('interactive_camera')
    if par.name == 'Openbackground':
        owner.op('background_controller').module.openBackground()
    elif par.name == 'Clearbackground':
        owner.op('background_controller').module.clearBackground()
    elif par.name == 'Homecamera' and camera is not None:
        camera.par.Home.pulse()
    elif par.name == 'Framecamera' and camera is not None:
        camera.par.Frame.pulse()
    elif par.name == 'Resetcamera' and camera is not None:
        camera.par.Reset.pulse()
    return


def onValueChange(par, prev):
    owner = parent()
    camera = owner.op('interactive_camera')
    if par.name == 'Showaxes' and camera is not None:
        camera.par.Drawaxes = bool(par.eval())
        camera.par.Drawpivot = bool(par.eval())
    elif par.name == 'Backgroundfile':
        movie = owner.op('background_file')
        if movie is not None:
            movie.par.reloadpulse.pulse()
        value = str(par.eval()).strip()
        if value:
            owner.par.Status = 'background loaded: ' + value
    return
'''
    _set_par(callbacks, "op", prototype.path)
    _set_par(
        callbacks,
        "pars",
        "Openbackground Clearbackground Homecamera Framecamera Resetcamera Showaxes Backgroundfile",
    )
    _set_par(callbacks, "onpulse", True)
    _set_par(callbacks, "valuechange", True)

    readme = prototype.create(textDAT, "README_phase2_prototype")
    readme.nodeX = -110
    readme.nodeY = -220
    readme.text = """PHASE 2 ISOLATED PROTOTYPE

INTERACTION
View interactive_camera or interactive_camera/renderView with Viewer Active.
LMB orbit, RMB pan, MMB/wheel dolly, F frame, H home.

BACKGROUND
Open Background uses ui.chooseFile with supported image file types.
Contain preserves the full image, Cover fills while cropping, Stretch distorts.
Corner Pin offers a 4-point perspective adjustment for one planar wall.

OUTPUT
prototype_out is an independent 960x960 output. Existing preview_out,
mapping data and DMX nodes are not modified.
"""


def build():
    preview = op(PREVIEW_PATH)
    if preview is None:
        raise RuntimeError("Missing preview component: " + PREVIEW_PATH)

    led_geometry = preview.op("led_points_geo")
    if led_geometry is None:
        raise RuntimeError("Missing preview LED geometry: " + PREVIEW_PATH + "/led_points_geo")

    existing = preview.op(PROTOTYPE_NAME)
    if existing is not None:
        existing.destroy()

    prototype = preview.create(baseCOMP, PROTOTYPE_NAME)
    prototype.nodeX = 1100
    prototype.nodeY = -300
    prototype.color = (0.25, 0.33, 0.48)
    _clear_defaults(prototype)
    _add_parameters(prototype)

    camera, panel, led_render = _create_camera(prototype, led_geometry)
    output = _create_background_pipeline(prototype, led_render)
    _create_callbacks(prototype, camera)

    prototype.par.Status = "ready | isolated prototype | no background selected"
    prototype.viewer = True
    output.cook(force=True)

    result = {
        "prototype": prototype.path,
        "camera": camera.path,
        "interactive_panel": panel.path,
        "output": output.path,
        "resolution": [output.width, output.height],
        "children": [{"name": c.name, "type": c.OPType} for c in prototype.children],
        "project_saved": False,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()
