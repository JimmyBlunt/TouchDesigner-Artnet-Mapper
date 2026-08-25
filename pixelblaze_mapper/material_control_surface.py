"""Non-destructive Material Browser controls for colour and framing.

This module deliberately owns only the parameters of
``/project1/madmapper_player_controls`` and uniforms of the material GLSL TOP.
It never touches Art-Net, controller routing, or project saving.  Calling
``install()`` is idempotent and is intended to be done from TouchDesigner's
Textport after the change has been reviewed.

The active core shader already exposes Speed, Scale, Width, Color A and Color
B.  This surface adds named colour presets and a *framing* transform:

* ``Focus X/Y`` choose the point that remains at the centre of the output.
* ``Frame Zoom`` is a magnification: 1.0 is unchanged, 2.0 shows half as much
  material around the selected focus, and 0.5 shows twice as much.

Framing is applied before global/panel/hybrid coordinate conversion.  Thus it
works consistently with the existing 3-D UV lookup without moving any LEDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


ROOT = "/project1"
CONTROLS_PATH = ROOT + "/madmapper_player_controls"
PLAYER_PATH = ROOT + "/madmapper_material_player"
SHADER_PATH = ROOT + "/madmapper_material_fs"


@dataclass(frozen=True)
class GradientPreset:
    key: str
    label: str
    color_a: Tuple[float, float, float]
    color_b: Tuple[float, float, float]


GRADIENT_PRESETS: Dict[str, GradientPreset] = {
    "neon_cyan_magenta": GradientPreset("neon_cyan_magenta", "Neon Cyan / Magenta", (0.91, 0.00, 1.00), (0.00, 0.72, 0.86)),
    "amber_violet": GradientPreset("amber_violet", "Amber / Violet", (1.00, 0.42, 0.02), (0.30, 0.00, 0.72)),
    "acid_lime_blue": GradientPreset("acid_lime_blue", "Acid Lime / Blue", (0.76, 1.00, 0.00), (0.00, 0.18, 1.00)),
    "fire_ice": GradientPreset("fire_ice", "Fire / Ice", (1.00, 0.10, 0.02), (0.00, 0.80, 1.00)),
    "mono_white": GradientPreset("mono_white", "Monochrome White", (1.00, 1.00, 1.00), (0.04, 0.04, 0.04)),
}


FRAME_SHADER_MARKER = "// MATERIAL_BROWSER_FRAME_TRANSFORM"


def framed_uv_glsl() -> str:
    """GLSL injected into the core shader exactly once by ``install``."""
    return r'''
// MATERIAL_BROWSER_FRAME_TRANSFORM
// uParams4 = focus X, focus Y, frame zoom, reserved
uniform vec4 uParams4;

vec2 materialBrowserFrame(vec2 sourceUV)
{
    vec2 focus = clamp(uParams4.xy, vec2(0.0), vec2(1.0));
    float zoom = clamp(uParams4.z, 0.25, 8.0);
    return focus + (sourceUV - vec2(0.5)) / zoom;
}
'''


def patch_shader_source(source: str) -> str:
    """Return shader source with frame support, preserving all effect code."""
    if FRAME_SHADER_MARKER in source:
        return source
    anchor = "const float PI ="
    if anchor not in source:
        raise ValueError("Core material shader does not contain the expected PI anchor")
    source = source.replace(anchor, framed_uv_glsl() + "\n" + anchor, 1)
    old_uv = "vec2 sourceUV = vUV.st;"
    if old_uv not in source:
        raise ValueError("Core material shader does not contain the expected main UV expression")
    return source.replace(old_uv, "vec2 sourceUV = materialBrowserFrame(vUV.st);", 1)


def preset_names() -> Tuple[str, ...]:
    return tuple(GRADIENT_PRESETS)


def _add_float(page, name, label, default, minimum, maximum):
    par = next((item for item in page.pars if item.name == name), None)
    if par is None:
        par = page.appendFloat(name, label=label)[0]
        par.val = default
        par.default = default
        par.normMin = minimum
        par.normMax = maximum
        par.min = minimum
        par.max = maximum
    return par


def _add_menu(page, name, label, names, labels, default):
    par = next((item for item in page.pars if item.name == name), None)
    if par is None:
        par = page.appendMenu(name, label=label)[0]
    par.menuNames = list(names)
    par.menuLabels = list(labels)
    if not par.eval():
        par.val = default
    return par


def _page(controls):
    for page in controls.customPages:
        if page.name == "Materialframing":
            return page
    return controls.appendCustomPage("Material Framing")


def _install_parameters(controls):
    page = _page(controls)
    _add_float(page, "Focusx", "Focus X", 0.5, 0.0, 1.0)
    _add_float(page, "Focusy", "Focus Y", 0.5, 0.0, 1.0)
    _add_float(page, "Framezoom", "Frame Zoom", 1.0, 0.25, 8.0)
    _add_menu(
        page,
        "Gradientpreset",
        "Gradient Preset",
        preset_names(),
        tuple(item.label for item in GRADIENT_PRESETS.values()),
        "neon_cyan_magenta",
    )


def install():
    """Install controls and the safe shader transform in the current TD file.

    This only edits the current in-memory project.  It does not save it and it
    does not modify any output/Art-Net operators.
    """
    controls = op(CONTROLS_PATH)
    player = op(PLAYER_PATH)
    shader = op(SHADER_PATH)
    if controls is None or player is None or shader is None:
        raise RuntimeError("Material controls, player, or core shader is missing")
    _install_parameters(controls)
    shader.text = patch_shader_source(str(shader.text))
    player.par.vec.sequence.numBlocks = max(int(player.par.vec.sequence.numBlocks), 5)
    player.par.vec4name = "uParams4"
    player.par.vec4valuex.expr = "op(%r).par.Focusx" % CONTROLS_PATH
    player.par.vec4valuey.expr = "op(%r).par.Focusy" % CONTROLS_PATH
    player.par.vec4valuez.expr = "op(%r).par.Framezoom" % CONTROLS_PATH
    player.par.vec4valuew = 0.0
    apply_gradient(controls.par.Gradientpreset.eval())
    return {"installed": True, "networkOutputEnabled": False, "projectSaved": False}


def apply_gradient(key: str):
    """Apply a named gradient to the existing A/B colour controls."""
    if key not in GRADIENT_PRESETS:
        raise KeyError("Unknown gradient preset: %s" % key)
    controls = op(CONTROLS_PATH)
    if controls is None:
        raise RuntimeError("Material controls are missing")
    preset = GRADIENT_PRESETS[key]
    controls.par.Colorr, controls.par.Colorg, controls.par.Colorb = preset.color_a
    controls.par.Color2r, controls.par.Color2g, controls.par.Color2b = preset.color_b
    if hasattr(controls.par, "Gradientpreset"):
        controls.par.Gradientpreset.val = key
    return preset


def reset_frame():
    controls = op(CONTROLS_PATH)
    if controls is None:
        raise RuntimeError("Material controls are missing")
    controls.par.Focusx = 0.5
    controls.par.Focusy = 0.5
    controls.par.Framezoom = 1.0
    return (0.5, 0.5, 1.0)
