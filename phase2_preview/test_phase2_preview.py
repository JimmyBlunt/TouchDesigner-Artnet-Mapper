"""Read-only validation for the isolated Phase 2 preview prototype."""

import json
import os


PROTOTYPE_PATH = (
    "/project1/pixelblaze_mapper/preview3d/"
    "phase2_interaction_background_prototype"
)
SCREENSHOT_PATH = (
    r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/"
    r"phase2_preview/phase2-prototype-out.png"
)


def check():
    prototype = op(PROTOTYPE_PATH)
    if prototype is None:
        raise RuntimeError("Prototype is missing: " + PROTOTYPE_PATH)

    required = {
        "interactive_camera": "cameraCOMP",
        "interactive_led_render": "renderTOP",
        "background_file": "moviefileinTOP",
        "background_fit": "fitTOP",
        "background_cornerpin": "cornerpinTOP",
        "background_alignment_switch": "switchTOP",
        "background_opacity": "levelTOP",
        "led_opacity": "levelTOP",
        "background_plus_leds": "overTOP",
        "prototype_out": "nullTOP",
    }

    problems = []
    for name, expected_type in required.items():
        node = prototype.op(name)
        if node is None:
            problems.append("missing node: " + name)
        elif node.OPType != expected_type:
            problems.append(
                "wrong type for {}: {} != {}".format(name, node.OPType, expected_type)
            )

    output = prototype.op("prototype_out")
    render = prototype.op("interactive_led_render")
    camera = prototype.op("interactive_camera")

    if output is not None:
        output.cook(force=True)
        if [output.width, output.height] != [960, 960]:
            problems.append("unexpected output resolution")
        output.save(SCREENSHOT_PATH)

    expected_geometry = "/project1/pixelblaze_mapper/preview3d/led_points_geo"
    if render is not None and str(render.par.geometry.eval()) != expected_geometry:
        problems.append("interactive render does not reference preview-only LED geometry")
    if render is not None and camera is not None and str(render.par.camera.eval()) != camera.path:
        problems.append("interactive render does not use local interactive camera")

    composite = prototype.op("background_plus_leds")
    if composite is not None:
        input_paths = [node.path for node in composite.inputs]
        expected_inputs = [
            prototype.op("led_opacity").path,
            prototype.op("background_opacity").path,
        ]
        if input_paths != expected_inputs:
            problems.append(
                "Over TOP input order is wrong: {} != {}".format(
                    input_paths, expected_inputs
                )
            )

    callbacks = prototype.op("phase2_parameter_callbacks")
    if callbacks is not None:
        onpulse = getattr(callbacks.par, "onpulse", None)
        if onpulse is None or not bool(onpulse.eval()):
            problems.append("Parameter Execute DAT pulse callback is not enabled")

    expected_parameters = [
        "Backgroundenabled",
        "Backgroundfile",
        "Openbackground",
        "Clearbackground",
        "Backgroundopacity",
        "Backgroundfit",
        "Alignmentmode",
        "Ledopacity",
        "Homecamera",
        "Framecamera",
        "Resetcamera",
        "Showaxes",
        "Status",
    ]
    for name in expected_parameters:
        if getattr(prototype.par, name, None) is None:
            problems.append("missing public parameter: " + name)

    result = {
        "prototype": prototype.path,
        "output": output.path if output is not None else None,
        "resolution": [output.width, output.height] if output is not None else None,
        "camera": camera.path if camera is not None else None,
        "camera_panel": camera.op("renderView").path if camera is not None and camera.op("renderView") else None,
        "screenshot": SCREENSHOT_PATH,
        "screenshot_exists": os.path.isfile(SCREENSHOT_PATH),
        "problems": problems,
        "passed": not problems,
        "project_saved": False,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    check()
