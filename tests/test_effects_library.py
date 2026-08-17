"""Static contract tests for the portable 25-effect GLSL library.

These tests intentionally do not need a TouchDesigner license. Live cooking and
visual screenshot checks remain integration tests in the running .toe project.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EFFECTS_DIR = ROOT / "effects"
MANIFEST_PATH = EFFECTS_DIR / "effects_manifest.json"
SHADER_PATH = EFFECTS_DIR / "core_effects.frag"
BUILDER_PATH = EFFECTS_DIR / "build_core_effects.py"


def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def shader_source():
    return SHADER_PATH.read_text(encoding="utf-8")


def builder_source():
    return BUILDER_PATH.read_text(encoding="utf-8")


def test_manifest_contains_exactly_25_ordered_effects():
    data = manifest()
    definitions = data["effectDefinitions"]

    assert data["version"] == 2
    assert len(data["effects"]) == 25
    assert len(definitions) == 25
    assert [effect["index"] for effect in definitions] == list(range(25))
    assert data["effects"] == [effect["label"] for effect in definitions]


def test_effect_ids_and_labels_are_unique_and_legacy_indices_are_stable():
    definitions = manifest()["effectDefinitions"]
    ids = [effect["id"] for effect in definitions]
    labels = [effect["label"] for effect in definitions]

    assert len(ids) == len(set(ids))
    assert len(labels) == len(set(labels))
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", effect_id) for effect_id in ids)
    assert ids[:13] == [
        "fill",
        "gradient",
        "diagonals",
        "fluid_noise",
        "cellular",
        "blobby",
        "spatial_pulse",
        "comet_tails",
        "arcs",
        "noisy_barcode",
        "particles",
        "bad_tv",
        "noise_dissolve_transition",
    ]
    assert ids[13:] == [
        "plasma",
        "fire",
        "aurora",
        "ocean_waves",
        "ripple_rings",
        "kaleidoscope",
        "tunnel",
        "matrix_rain",
        "twinkle_sparkle",
        "scanner",
        "reaction_diffusion",
        "geometric_grid_morph",
    ]


def test_every_effect_has_browser_category_and_complete_numeric_preset():
    data = manifest()
    allowed_categories = set(data["browser"]["categories"])
    assert data["browser"]["columns"] == 5

    for effect in data["effectDefinitions"]:
        assert effect["category"] in allowed_categories
        assert set(effect["preset"]) == {"scale", "width", "trail", "density"}
        assert effect["preset"]["scale"] > 0.0
        assert 0.0 <= effect["preset"]["width"] <= 1.0
        assert 0.0 <= effect["preset"]["trail"] <= 1.0
        assert 0.25 <= effect["preset"]["density"] <= 2.0


def test_uniform_contract_and_all_coordinate_modes_remain_compatible():
    data = manifest()
    assert set(data["coordinateModes"]) == {"global", "panel", "hybrid"}
    assert data["uniforms"] == {
        "uParams0": ["effect", "time", "scale", "width"],
        "uParams1": ["coordinateMode", "intensity", "contrast", "trail"],
        "uParams2": ["direction", "rotationDegrees", "seed", "transition"],
        "uParams3": ["panelColumns", "panelRows", "hybridMix", "density"],
        "uColorA": "primary RGBA",
        "uColorB": "secondary RGBA",
    }

    source = shader_source()
    assert "vec2 coordinateSpace(vec2 uv)" in source
    assert "return uv;" in source
    assert "return localUV;" in source
    assert "return mix(uv, localUV, clamp(uParams3.z" in source
    for uniform in ("uParams0", "uParams1", "uParams2", "uParams3", "uColorA", "uColorB"):
        assert re.search(rf"uniform\s+vec4\s+{uniform}\s*;", source)


def test_shader_has_explicit_dispatch_branch_for_every_effect_index():
    source = shader_source()
    indices = [int(value) for value in re.findall(r"effect\s*==\s*(\d+)", source)]
    assert indices == list(range(25))
    assert "else if (effect == 12)" in source
    assert "color = vec3(0.0);" in source


def test_all_new_effect_functions_are_present_and_used():
    source = shader_source()
    functions = [
        "plasma",
        "fire",
        "aurora",
        "oceanWaves",
        "rippleRings",
        "kaleidoscope",
        "tunnel",
        "matrixRain",
        "twinkleSparkle",
        "scanner",
        "reactionDiffusion",
        "geometricGridMorph",
    ]
    for function in functions:
        assert source.count(f"float {function}(vec2 uv)") == 1
        assert source.count(f"{function}(uv)") == 1


def test_reaction_diffusion_approximation_has_no_feedback_dependency():
    source = shader_source()
    start = source.index("float reactionDiffusion(vec2 uv)")
    end = source.index("float geometricGridMorph(vec2 uv)")
    implementation = source[start:end]
    assert "fbm(" in implementation
    assert "texture(" not in implementation
    assert "imageLoad(" not in implementation
    assert "imageStore(" not in implementation


def test_shader_structure_is_balanced_and_has_touchdesigner_output():
    source = shader_source()
    assert source.count("{") == source.count("}")
    assert source.count("(") == source.count(")")
    assert "void main()" in source
    assert "vUV.st" in source
    assert "TDOutputSwizzle" in source
    assert "fragColor" in source
    assert not re.search(r"\b(?:float|int|bool)\s+active\b", source)


def test_builder_uses_manifest_as_single_metadata_source_and_is_idempotent():
    source = builder_source()
    assert 'MANIFEST_FILE = ASSET_DIR / "effects_manifest.json"' in source
    assert 'EFFECT_DEFINITIONS = MANIFEST["effectDefinitions"]' in source
    assert 'EFFECT_NAMES = [effect["id"] for effect in EFFECT_DEFINITIONS]' in source
    assert 'EFFECT_LABELS = [effect["label"] for effect in EFFECT_DEFINITIONS]' in source
    assert 'EFFECT_PRESETS = [effect["preset"] for effect in EFFECT_DEFINITIONS]' in source
    assert "for index, definition in enumerate(EFFECT_DEFINITIONS):" in source
    assert "button.store(\"effect_id\", definition[\"id\"])" in source
    assert "button.store(\"effect_category\", definition[\"category\"])" in source
    assert 'execute.par.panelvalue = "state"' in source
    assert 'mouse = browser.op("material_browser_mouse")' in source
    assert "COLUMNS = %d" in source
    assert "or browser.copy" in source
    assert "old_material if old_material in EFFECT_NAMES else" in source
    assert 'controls.store("core_effects_version", MANIFEST["version"])' in source


def test_builder_manifest_and_shader_dispatch_counts_agree():
    data = manifest()
    indices = re.findall(r"effect\s*==\s*(\d+)", shader_source())
    assert len(data["effectDefinitions"]) == len(indices) == 25
    assert "len(EFFECT_DEFINITIONS)" in builder_source()


def load_tests(loader, tests, pattern):
    """Expose the lightweight contract functions to unittest discovery."""

    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            suite.addTest(unittest.FunctionTestCase(value, description=name))
    return suite
