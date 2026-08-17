"""Install the Core Effects suite into the existing live PixelblazeMapper project.

This script deliberately modifies only the already present material player,
its controls, its source switch, and its browser. The LED map, GRB packing,
universe allocation, routing table, and DMX Out CHOP are not touched.
"""

import json
from pathlib import Path


ROOT = "/project1"
ASSET_DIR = Path("C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/effects")
SHADER_FILE = ASSET_DIR / "core_effects.frag"
MANIFEST_FILE = ASSET_DIR / "effects_manifest.json"

MANIFEST = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
EFFECT_DEFINITIONS = MANIFEST["effectDefinitions"]
EFFECT_NAMES = [effect["id"] for effect in EFFECT_DEFINITIONS]
EFFECT_LABELS = [effect["label"] for effect in EFFECT_DEFINITIONS]
EFFECT_PRESETS = [effect["preset"] for effect in EFFECT_DEFINITIONS]
BROWSER_COLUMNS = int(MANIFEST.get("browser", {}).get("columns", 5))
BROWSER_ROWS = (len(EFFECT_DEFINITIONS) + BROWSER_COLUMNS - 1) // BROWSER_COLUMNS


def _page(owner, name):
    return next((page for page in owner.customPages if page.name == name), None) or owner.appendCustomPage(name)


def _set_range(par, minimum, maximum, default):
    par.min = minimum
    par.max = maximum
    par.normMin = minimum
    par.normMax = maximum
    par.clampMin = True
    par.clampMax = True
    par.default = default


def _ensure_float(owner, page, name, label, default, minimum, maximum):
    par = owner.par[name]
    if par is None:
        par = page.appendFloat(name, label=label)[0]
        par.val = default
    _set_range(par, minimum, maximum, default)
    return par


def _ensure_int(owner, page, name, label, default, minimum, maximum):
    par = owner.par[name]
    if par is None:
        par = page.appendInt(name, label=label)[0]
        par.val = default
    _set_range(par, minimum, maximum, default)
    return par


def _ensure_menu(owner, page, name, label, names, labels, default):
    par = owner.par[name]
    if par is None:
        par = page.appendMenu(name, label=label)[0]
        par.menuNames = names
        par.menuLabels = labels
        par.val = default
    else:
        old_value = str(par.eval())
        par.menuNames = names
        par.menuLabels = labels
        par.val = old_value if old_value in names else default
    return par


def _ensure_rgba(owner, page, name, label, default):
    first = owner.par[name + "r"]
    if first is None:
        pars = page.appendRGBA(name, label=label)
        for par, value in zip(pars, default):
            par.default = value
            par.val = value
        return pars
    return tuple(owner.par[name + suffix] for suffix in "rgba")


def _set_expr(par, expression):
    par.expr = expression


def _configure_uniforms(player, preview_mode=None):
    player.par.vec.sequence.numBlocks = 4
    player.par.color.sequence.numBlocks = 2
    player.par.nval = 1

    for index, uniform_name in enumerate(("uParams0", "uParams1", "uParams2", "uParams3")):
        player.par[f"vec{index}name"] = uniform_name
    player.par.color0name = "uColorA"
    player.par.color1name = "uColorB"

    if preview_mode is None:
        controls = f"op('{ROOT}/madmapper_player_controls').par"
        _set_expr(player.par.vec0valuex, f"{controls}.Material.menuIndex")
        _set_expr(player.par.vec0valuey, f"absTime.seconds * {controls}.Speed")
        _set_expr(player.par.vec0valuez, f"{controls}.Scale")
        _set_expr(player.par.vec0valuew, f"{controls}.Width")
        _set_expr(player.par.vec1valuex, f"{controls}.Coordinatemode.menuIndex")
        _set_expr(player.par.vec1valuey, f"{controls}.Intensity")
        _set_expr(player.par.vec1valuez, f"{controls}.Contrast")
        _set_expr(player.par.vec1valuew, f"{controls}.Trail")
        _set_expr(player.par.vec2valuex, f"{controls}.Direction")
        _set_expr(player.par.vec2valuey, f"{controls}.Rotation")
        _set_expr(player.par.vec2valuez, f"{controls}.Seed")
        _set_expr(player.par.vec2valuew, f"{controls}.Transition")
        _set_expr(player.par.vec3valuex, f"{controls}.Panelcolumns")
        _set_expr(player.par.vec3valuey, f"{controls}.Panelrows")
        _set_expr(player.par.vec3valuez, f"{controls}.Hybridmix")
        _set_expr(player.par.vec3valuew, f"{controls}.Density")
        for suffix in "rgb":
            _set_expr(player.par[f"color0rgb{suffix}"], f"{controls}.Color{suffix}")
            _set_expr(player.par[f"color1rgb{suffix}"], f"{controls}.Color2{suffix}")
        player.par.color0alpha = 1.0
        _set_expr(player.par.color1alpha, f"{controls}.Color2a")
    else:
        preset = EFFECT_PRESETS[preview_mode]
        player.par.vec0valuex = preview_mode
        _set_expr(player.par.vec0valuey, "absTime.seconds * 0.45")
        player.par.vec0valuez = preset["scale"]
        player.par.vec0valuew = preset["width"]
        player.par.vec1valuex = 0
        player.par.vec1valuey = 1.0
        player.par.vec1valuez = 1.35
        player.par.vec1valuew = preset["trail"]
        player.par.vec2valuex = 0.125
        player.par.vec2valuey = 0.0
        player.par.vec2valuez = preview_mode * 0.173
        if preview_mode == 12:
            _set_expr(player.par.vec2valuew, "(absTime.seconds * 0.15) % 1.0")
        else:
            player.par.vec2valuew = 0.5
        player.par.vec3valuex = 2.0
        player.par.vec3valuey = 5.0
        player.par.vec3valuez = 0.5
        player.par.vec3valuew = preset["density"]
        player.par.color0rgbr = 0.92
        player.par.color0rgbg = 0.08
        player.par.color0rgbb = 1.0
        player.par.color0alpha = 1.0
        player.par.color1rgbr = 0.0
        player.par.color1rgbg = 0.72
        player.par.color1rgbb = 0.86
        player.par.color1alpha = 1.0


def _configure_controls():
    controls = op(f"{ROOT}/madmapper_player_controls")
    page = _page(controls, "Core Effects")

    _ensure_menu(controls, page, "Coordinatemode", "Coordinate Mode", ["global", "panel", "hybrid"], ["Global Canvas", "Panel Local", "Hybrid"], "global")
    _ensure_float(controls, page, "Intensity", "Intensity", 1.0, 0.0, 2.0)
    _ensure_float(controls, page, "Contrast", "Contrast", 1.25, 0.1, 4.0)
    _ensure_float(controls, page, "Trail", "Trail", 0.55, 0.0, 1.0)
    _ensure_float(controls, page, "Direction", "Direction", 0.125, 0.0, 1.0)
    _ensure_float(controls, page, "Rotation", "Rotation", 0.0, -180.0, 180.0)
    _ensure_float(controls, page, "Seed", "Seed", 0.0, 0.0, 100.0)
    _ensure_float(controls, page, "Transition", "Transition", 0.5, 0.0, 1.0)
    _ensure_float(controls, page, "Hybridmix", "Hybrid Mix", 0.5, 0.0, 1.0)
    _ensure_float(controls, page, "Density", "Particle Density", 1.0, 0.25, 2.0)
    _ensure_int(controls, page, "Panelcolumns", "Panel Columns", 2, 1, 16)
    _ensure_int(controls, page, "Panelrows", "Panel Rows", 5, 1, 16)
    _ensure_rgba(controls, page, "Color2", "Color B", (0.0, 0.72, 0.86, 1.0))

    material = controls.par.Material
    old_material = str(material.eval())
    material.menuNames = EFFECT_NAMES
    material.menuLabels = EFFECT_LABELS
    material.val = old_material if old_material in EFFECT_NAMES else "fluid_noise"
    controls.par.Source.menuNames = ["movie", "materials"]
    controls.par.Source.menuLabels = ["Movie / Existing Source", "Core Materials"]

    if controls.par.Colorr is not None:
        controls.par.Colorr.label = "Color A"
    return controls


def _configure_browser(shader_dat):
    browser = op(f"{ROOT}/material_browser")
    source_preview = browser.op("preview_0")
    source_card = browser.op("card_top_0")
    source_button = browser.op("material_card_0")
    source_execute = browser.op("select_material_0")
    preview_source = browser.op("preview_source") or browser.create("selectTOP", "preview_source")
    preview_source.par.top = f"{ROOT}/moviefilein1"
    preview_source.nodeX = source_preview.nodeX - 180
    preview_source.nodeY = source_preview.nodeY

    cards = []
    for index, definition in enumerate(EFFECT_DEFINITIONS):
        label = definition["label"]
        preview = browser.op(f"preview_{index}") or browser.copy(source_preview, name=f"preview_{index}", includeDocked=False)
        preview.par.glslversion = "glsl430"
        preview.par.mode = "vertexpixel"
        preview.par.pixeldat = shader_dat.path
        preview.par.outputresolution = "custom"
        preview.par.resolutionw = 256
        preview.par.resolutionh = 256
        _configure_uniforms(preview, preview_mode=index)
        preview_source.outputConnectors[0].connect(preview)

        card = browser.op(f"card_top_{index}") or browser.copy(source_card, name=f"card_top_{index}", includeDocked=False)
        card.par.text = label
        card.par.fontsizex = 16
        card.par.fontsizey = 20
        preview.outputConnectors[0].connect(card)
        cards.append(card)

        button = browser.op(f"material_card_{index}") or browser.copy(source_button, name=f"material_card_{index}", includeDocked=False)
        button.par.label = label
        button.store("effect_id", definition["id"])
        button.store("effect_category", definition["category"])
        button.store("effect_preset", definition["preset"])
        column = index % BROWSER_COLUMNS
        row = index // BROWSER_COLUMNS
        button.par.x = column * 240
        button.par.y = (BROWSER_ROWS - 1 - row) * 180
        button.par.w = 240
        button.par.h = 180

        execute = browser.op(f"select_material_{index}") or browser.copy(source_execute, name=f"select_material_{index}", includeDocked=False)
        execute.par.active = True
        execute.par.fromop = button.path
        execute.par.panels = button.path
        execute.par.panelvalue = "state"
        execute.par.offtoon = True
        execute.par.valuechange = False
        execute.text = "def onOffToOn(panelValue):\n    controls = op('/project1/madmapper_player_controls')\n    controls.par.Source = 'materials'\n    controls.par.Material = %d\n    return\n" % index

    # The browser background also supports direct coordinate clicks.  This is
    # the path used when the cards are shown as one composite panel.
    mouse = browser.op("material_browser_mouse")
    if mouse is not None:
        mouse.par.active = True
        mouse.par.fromop = browser.path
        mouse.par.panels = browser.path
        mouse.par.panelvalue = "select"
        mouse.par.offtoon = True
        mouse.par.valuechange = False
        mouse.text = """MATERIALS = %r
COLUMNS = %d
ROWS = %d

def onOffToOn(panelValue):
    panel = panelValue.owner.panel
    column = max(0, min(COLUMNS - 1, int(float(panel.u) * COLUMNS)))
    row = max(0, min(ROWS - 1, int((1.0 - float(panel.v)) * ROWS)))
    index = row * COLUMNS + column
    if index < len(MATERIALS):
        controls = op('/project1/madmapper_player_controls')
        controls.par.Source = 'materials'
        controls.par.Material = MATERIALS[index]
    return
""" % (EFFECT_NAMES, BROWSER_COLUMNS, BROWSER_ROWS)

    layout = browser.op("thumbnail_layout")
    layout.par.tops = cards
    layout.par.align = "gridrows"
    layout.par.rowlayout = "exact"
    layout.par.numrows = BROWSER_ROWS
    layout.par.fit = "fill"
    layout.par.outputresolution = "custom"
    layout.par.resolutionw = BROWSER_COLUMNS * 240
    layout.par.resolutionh = BROWSER_ROWS * 180
    browser.par.w = BROWSER_COLUMNS * 240
    browser.par.h = BROWSER_ROWS * 180
    return browser


def install():
    shader_source = SHADER_FILE.read_text(encoding="utf-8")
    shader_dat = op(f"{ROOT}/madmapper_material_fs")
    shader_dat.text = shader_source

    controls = _configure_controls()
    player = op(f"{ROOT}/madmapper_material_player")
    player.par.glslversion = "glsl430"
    player.par.mode = "vertexpixel"
    player.par.pixeldat = shader_dat.path
    _configure_uniforms(player)

    source_switch = op(f"{ROOT}/visual_source_switch")
    source_switch.par.index.expr = f"op('{ROOT}/madmapper_player_controls').par.Source.menuIndex"
    _configure_browser(shader_dat)

    controls.store("core_effects_version", MANIFEST["version"])
    controls.store("core_effects_shader", str(SHADER_FILE))

    return {
        "effects": EFFECT_LABELS,
        "effectCount": len(EFFECT_LABELS),
        "shaderDat": shader_dat.path,
        "player": player.path,
        "controls": controls.path,
        "sourceSwitch": source_switch.path,
        "browser": f"{ROOT}/material_browser",
    }


result = install()
