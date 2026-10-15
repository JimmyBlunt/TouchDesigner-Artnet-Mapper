"""Editing operations for Show Control shows.

Every mutation returns a NEW show dictionary and is validated by
``show_sequencer.Show.from_dict`` before it is handed back, so an edit that
would break the running sequencer is refused while the caller still holds the
old, working show. Nothing here touches TouchDesigner; the panel adapter in
``build_show_editor.py`` supplies plain values and writes the result back.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence
import re

from pixelblaze_mapper.material_control_surface import GRADIENT_PRESETS
from pixelblaze_mapper.show_renderer import TRANSITION_INFO
from pixelblaze_mapper.show_sequencer import (
    COORDINATE_MODES,
    Show,
    ShowValidationError,
    TARGET_GROUPS,
    TRANSITION_TYPES,
)

# Ordered for menus; the sets above remain what validates.
TRANSITION_ORDER = tuple(name for name, _family, _label in TRANSITION_INFO)
TRANSITION_LABELS = {name: label for name, _family, label in TRANSITION_INFO}
COORDINATE_ORDER = ("global", "panel_local", "hybrid")
GRADIENT_ORDER = tuple(GRADIENT_PRESETS)
DEFAULT_DURATION = 15.0
DEFAULT_TRANSITION = "crossfade"
DEFAULT_TRANSITION_DURATION = 3.0
DEFAULT_BRIGHTNESS = 0.25
# An imported MadMapper material is identified in cue.effect by this prefix
# plus its catalog id; cue.preset then carries the readable label. Keeping the
# identity inside the existing string field leaves the show schema untouched.
IMPORT_PREFIX = "madmapper:"

# The Material Player exposes one custom parameter per cue parameter. Kept as
# an explicit table so a renamed parameter fails loudly instead of silently
# writing a default into every recorded cue.
PLAYER_PARAMETERS = {
    "Speed": "speed",
    "Scale": "scale",
    "Width": "width",
    "Focusx": "focus_x",
    "Focusy": "focus_y",
    "Framezoom": "zoom",
    "Gradientpreset": "gradient",
    "Intensity": "intensity",
    "Contrast": "contrast",
    "Trail": "trail",
    "Direction": "direction",
    "Rotation": "rotation_degrees",
    "Seed": "seed",
    "Transition": "effect_transition",
    "Panelcolumns": "panel_columns",
    "Panelrows": "panel_rows",
    "Hybridmix": "hybrid_mix",
    "Density": "density",
}
# The player calls panel-local coordinates 'panel'; the show schema spells it out.
PLAYER_COORDINATE_MODES = {"global": "global", "panel": "panel_local", "hybrid": "hybrid"}
EMPTY_SHOW = {"schema_version": 2, "name": "Neue Show", "loop": True, "cues": []}


def empty_show():
    """New projects use visible clip-local time; old documents remain legacy."""
    return dict(EMPTY_SHOW, timing_mode='overlap', cues=[])


def _validated(show: Mapping[str, Any]) -> dict:
    """Round-trip through the sequencer so only runnable shows escape."""

    candidate = deepcopy(dict(show))
    if not candidate.get("cues"):
        # A show with no cues cannot be validated, but must stay editable.
        Show.from_dict(dict(candidate, cues=[_placeholder_cue()]))
        return candidate
    return Show.from_dict(candidate).to_dict()


def _placeholder_cue() -> dict:
    return new_cue("Fill", parameters_from_player({}), name="Platzhalter")


def slugify(value: str, *, fallback: str = "cue") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    return slug or fallback


def unique_cue_id(show: Mapping[str, Any], base: str) -> str:
    used = {cue["id"] for cue in show.get("cues", ())}
    slug = slugify(base)
    if slug not in used:
        return slug
    index = 2
    while "%s-%d" % (slug, index) in used:
        index += 1
    return "%s-%d" % (slug, index)


def parameters_from_player(values: Mapping[str, Any]) -> dict:
    """Build a complete cue parameter block from Material Player values.

    Missing entries fall back to the documented defaults rather than raising,
    so a player that gains or loses a control still yields a runnable cue.
    """

    defaults = {
        "speed": 1.0, "scale": 4.0, "width": 0.45, "focus_x": 0.5, "focus_y": 0.5,
        "zoom": 1.0, "gradient": "neon_cyan_magenta", "intensity": 1.0, "contrast": 1.25,
        "trail": 0.4, "direction": 0.125, "rotation_degrees": 0.0, "seed": 0.0,
        "effect_transition": 0.5, "panel_columns": 2.0, "panel_rows": 5.0,
        "hybrid_mix": 0.5, "density": 1.0,
    }
    parameters = dict(defaults)
    for player_name, field in PLAYER_PARAMETERS.items():
        if player_name not in values:
            continue
        raw = values[player_name]
        parameters[field] = str(raw) if field == "gradient" else float(raw)
    gradient = parameters["gradient"]
    preset = GRADIENT_PRESETS.get(gradient)
    color_a = _color(values, ("Colorr", "Colorg", "Colorb", "Colora"),
                     preset.color_a if preset else (0.91, 0.0, 1.0))
    color_b = _color(values, ("Color2r", "Color2g", "Color2b", "Color2a"),
                     preset.color_b if preset else (0.0, 0.72, 0.86))
    parameters["color_a"] = list(color_a)
    parameters["color_b"] = list(color_b)
    return parameters


def _color(values: Mapping[str, Any], names: Sequence[str], fallback) -> tuple:
    components = []
    for index, name in enumerate(names):
        if name in values:
            components.append(min(1.0, max(0.0, float(values[name]))))
        elif index < 3:
            components.append(min(1.0, max(0.0, float(fallback[index]))))
        else:
            components.append(1.0)
    return tuple(components)


def new_cue(effect: str, parameters: Mapping[str, Any], *, name: str = "",
            preset: str = "", coordinate_mode: str = "global",
            duration: float = DEFAULT_DURATION, transition: str = DEFAULT_TRANSITION,
            transition_duration: float = DEFAULT_TRANSITION_DURATION,
            brightness: float = DEFAULT_BRIGHTNESS,
            target_groups: Sequence[str] = ("all",), cue_id: str = "") -> dict:
    label = str(name).strip() or str(effect).strip() or "Cue"
    if transition == "cut":
        transition_duration = 0.0
    return {
        "id": cue_id or slugify(label),
        "name": label,
        "effect": str(effect).strip() or "Fill",
        "preset": str(preset),
        "parameters": deepcopy(dict(parameters)),
        "coordinate_mode": coordinate_mode,
        "duration": float(duration),
        "transition": transition,
        "transition_duration": float(transition_duration),
        "brightness": float(brightness),
        "target_groups": list(target_groups),
    }


def append_cue(show: Mapping[str, Any], cue: Mapping[str, Any]) -> dict:
    result = deepcopy(dict(show))
    entry = deepcopy(dict(cue))
    entry["id"] = unique_cue_id(result, entry.get("id") or entry.get("name", "cue"))
    if result.get('timing_mode') == 'overlap':
        fade = min(float(entry['duration']), float(entry['transition_duration']))
        entry.setdefault('fade_out', fade)
    result["cues"] = list(result.get("cues", ())) + [entry]
    if result.get('timing_mode') == 'overlap':
        from .show_sequencer import overlap_duration
        incoming = overlap_duration(Show.from_dict(result), len(result['cues'])-2) if len(result['cues']) > 1 else fade
        entry.setdefault('fade_in', incoming)
    return _validated(result)


def duplicate_cue(show: Mapping[str, Any], index: int) -> dict:
    cues = list(show.get("cues", ()))
    _check_index(cues, index)
    copy = deepcopy(cues[index])
    copy["id"] = unique_cue_id(show, copy["id"])
    copy["name"] = copy["name"] + " (Kopie)"
    result = deepcopy(dict(show))
    result["cues"] = cues[: index + 1] + [copy] + cues[index + 1:]
    return _validated(result)


def delete_cue(show: Mapping[str, Any], index: int) -> dict:
    cues = list(show.get("cues", ()))
    _check_index(cues, index)
    result = deepcopy(dict(show))
    result["cues"] = cues[:index] + cues[index + 1:]
    return _validated(result)


def move_cue(show: Mapping[str, Any], index: int, delta: int) -> dict:
    cues = list(show.get("cues", ()))
    _check_index(cues, index)
    target = index + int(delta)
    if not 0 <= target < len(cues):
        return _validated(dict(show))
    cues[index], cues[target] = cues[target], cues[index]
    result = deepcopy(dict(show))
    result["cues"] = cues
    return _validated(result)


def update_cue(show: Mapping[str, Any], index: int, field: str, value: Any) -> dict:
    """Change one field of one cue, with the coupling the schema implies."""

    cues = [deepcopy(cue) for cue in show.get("cues", ())]
    _check_index(cues, index)
    cue = cues[index]
    if field == "name":
        cue["name"] = str(value).strip() or cue["name"]
    elif field == "duration":
        cue["duration"] = max(0.1, float(value))
        # A shorter cue must not keep a transition longer than itself.
        cue["transition_duration"] = min(cue["transition_duration"], cue["duration"])
        for fade in ('fade_in', 'fade_out'):
            if fade in cue:
                cue[fade] = min(cue[fade], cue['duration'])
    elif field == "transition":
        if value not in TRANSITION_TYPES:
            raise ShowValidationError("Unbekannter Uebergang: %s" % value)
        cue["transition"] = value
        if value == "cut":
            cue["transition_duration"] = 0.0
        elif cue["transition_duration"] <= 0.0:
            cue["transition_duration"] = min(DEFAULT_TRANSITION_DURATION, cue["duration"])
    elif field == "transition_duration":
        if cue["transition"] == "cut":
            cue["transition_duration"] = 0.0
        else:
            cue["transition_duration"] = min(max(0.1, float(value)), cue["duration"])
    elif field == "coordinate_mode":
        if value not in COORDINATE_MODES:
            raise ShowValidationError("Unbekannter Koordinatenmodus: %s" % value)
        cue["coordinate_mode"] = value
    elif field == "brightness":
        cue["brightness"] = min(1.0, max(0.0, float(value)))
    elif field == "gradient":
        preset = GRADIENT_PRESETS.get(str(value))
        if preset is None:
            raise ShowValidationError("Unbekannter Farbverlauf: %s" % value)
        cue["parameters"]["gradient"] = preset.key
        # The gradient is the pair of colours; changing one without the other
        # would leave a cue whose name and appearance disagree.
        cue["parameters"]["color_a"] = list(preset.color_a) + [1.0]
        cue["parameters"]["color_b"] = list(preset.color_b) + [1.0]
    elif field == "target_groups":
        groups = [item for item in value if item in TARGET_GROUPS]
        if not groups:
            raise ShowValidationError("Mindestens eine Zielflaeche noetig")
        cue["target_groups"] = ["all"] if "all" in groups else groups
    elif field in ("speed", "scale", "density", "intensity", "contrast", "trail"):
        cue["parameters"][field] = float(value)
    else:
        raise ShowValidationError("Feld nicht editierbar: %s" % field)
    result = deepcopy(dict(show))
    result["cues"] = cues
    return _validated(result)


def set_show_field(show: Mapping[str, Any], field: str, value: Any) -> dict:
    result = deepcopy(dict(show))
    if field == "name":
        result["name"] = str(value).strip() or result.get("name", "Show")
    elif field == "loop":
        result["loop"] = bool(value)
    else:
        raise ShowValidationError("Feld nicht editierbar: %s" % field)
    return _validated(result)


def is_imported(cue: Mapping[str, Any]) -> bool:
    return str(cue.get("effect", "")).startswith(IMPORT_PREFIX)


def material_id(cue: Mapping[str, Any]) -> str:
    effect = str(cue.get("effect", ""))
    return effect[len(IMPORT_PREFIX):] if effect.startswith(IMPORT_PREFIX) else ""


def display_effect(cue: Mapping[str, Any]) -> str:
    """What to show in the cue list: a label, never a catalog id."""

    if is_imported(cue):
        return str(cue.get("preset") or material_id(cue))
    return str(cue.get("effect", ""))


def summary_rows(show: Mapping[str, Any]) -> list:
    """One display row per cue: index, name, effect, timing, transition."""

    rows = []
    for index, cue in enumerate(show.get("cues", ())):
        transition = cue["transition"]
        timing = ("%.0f s" % cue["duration"] if transition == "cut"
                  else "%.0f s + %.1f s" % (cue["duration"], cue["transition_duration"]))
        rows.append({
            "index": index,
            "position": "%02d" % (index + 1),
            "name": cue["name"],
            "effect": display_effect(cue),
            "imported": is_imported(cue),
            "timing": timing,
            "transition": transition,
            "coordinate_mode": cue["coordinate_mode"],
            "gradient": cue["parameters"].get("gradient", ""),
            "brightness": cue["brightness"],
        })
    return rows


def total_duration(show: Mapping[str, Any]) -> float:
    return float(sum(cue["duration"] for cue in show.get("cues", ())))


def _check_index(cues: Sequence[Any], index: int) -> None:
    if not isinstance(index, int) or not 0 <= index < len(cues):
        raise ShowValidationError("Cue-Index ausserhalb der Show")
