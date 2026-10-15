"""Recorded parameter moves for Show Control cues.

A cue stores one static parameter block. Automation adds the missing
dimension: what a control did *during* the cue. Tracks live beside the show
rather than inside it, keyed by cue id, so the validated show schema stays
untouched and an existing show file remains loadable by an older build.

Times are seconds from the start of the cue. Playback interpolates linearly
between samples and holds the first/last value outside the recorded range, so
a track that covers only part of a cue still behaves predictably.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Mapping

SCHEMA = "pixelblaze-show-automation"
SCHEMA_VERSION = 1
# Parameters a recording may touch. Anything else is refused so a stray UI
# control cannot write a field the renderer will not read back.
RECORDABLE = (
    "global_master_speed",
    "speed", "scale", "width", "focus_x", "focus_y", "zoom", "intensity",
    "contrast", "trail", "direction", "rotation_degrees", "effect_transition",
    "hybrid_mix", "density", "brightness",
)
# An imported MadMapper material brings its own controls, named mat_<something>
# by the adapter. They cannot be listed up front - every material has different
# ones - so they are admitted by shape instead of by name.
IMPORT_PARAMETER_PREFIX = "mat_"
MAX_SAMPLES_PER_TRACK = 4000
MIN_INTERVAL = 1.0 / 60.0
EPSILON = 1e-4


class AutomationError(ValueError):
    """Raised when a recording or track is malformed."""


def recordable(name: str) -> bool:
    """Whether a parameter may be automated.

    Core parameters are a fixed list. An imported material's controls are not
    knowable in advance, so a mat_ prefix plus a plain identifier is the rule;
    anything else is refused so a stray key cannot reach the renderer.
    """

    name = str(name)
    if name in RECORDABLE:
        return True
    if not name.startswith(IMPORT_PARAMETER_PREFIX):
        return False
    rest = name[len(IMPORT_PARAMETER_PREFIX):]
    return bool(rest) and rest.replace("_", "").isalnum()


def imported_track_name(name):
    """Keep existing mat_* identities; namespace other imported uniforms."""
    return name if name.startswith(IMPORT_PARAMETER_PREFIX) else 'mat__' + name


def empty() -> dict:
    return {"schema": SCHEMA, "version": SCHEMA_VERSION, "tracks": {}}


def _number(value: Any, field: str) -> float:
    result = float(value)
    if not isfinite(result):
        raise AutomationError("%s must be finite" % field)
    return result


def validate(automation: Mapping[str, Any]) -> dict:
    if not isinstance(automation, Mapping):
        raise AutomationError("automation must be an object")
    if automation.get("schema") != SCHEMA or automation.get("version") != SCHEMA_VERSION:
        raise AutomationError("unknown automation schema")
    tracks = automation.get("tracks")
    if not isinstance(tracks, Mapping):
        raise AutomationError("automation.tracks must be an object")
    result = {}
    for cue_id, parameters in tracks.items():
        if not isinstance(cue_id, str) or not cue_id.strip():
            raise AutomationError("track keys must be cue ids")
        if not isinstance(parameters, Mapping):
            raise AutomationError("each track must map parameters to samples")
        clean = {}
        for name, samples in parameters.items():
            if not recordable(name):
                raise AutomationError("parameter not recordable: %s" % name)
            clean[name] = _clean_samples(samples, name)
        if clean:
            result[cue_id] = clean
    document = {"schema": SCHEMA, "version": SCHEMA_VERSION, "tracks": result}
    # Optional, non-destructive editor layers. Version-one recordings stay valid.
    for section in ('edits', 'transitions'):
        if section not in automation:
            continue
        entries = automation[section]
        if not isinstance(entries, Mapping):
            raise AutomationError(section + ' must be an object')
        layers = {}
        for cue_id, entry in entries.items():
            if not isinstance(cue_id, str) or not cue_id.strip() or not isinstance(entry, Mapping):
                raise AutomationError('invalid editor layer')
            if section == 'transitions':
                layers[cue_id] = _clean_curve(entry, transition=True)
            else:
                layers[cue_id] = {}
                for name, curve in entry.items():
                    if not recordable(name):
                        raise AutomationError('parameter not recordable: ' + str(name))
                    layers[cue_id][name] = _clean_curve(curve)
        document[section] = layers
    if 'loop_region' in automation:
        region = automation['loop_region']
        start, end = _number(region['start'], 'loop start'), _number(region['end'], 'loop end')
        if start < 0 or end <= start or not isinstance(region.get('enabled'), bool):
            raise AutomationError('invalid loop region')
        document['loop_region'] = dict(start=start, end=end, enabled=region['enabled'])
    return document


INTERPOLATIONS = ('linear', 'step', 'smooth', 'ease_in', 'ease_out')


def _clean_curve(curve, transition=False):
    if not isinstance(curve, Mapping):
        raise AutomationError('curve must be an object')
    mode = curve.get('mode', 'linear')
    if mode not in INTERPOLATIONS:
        raise AutomationError('unknown interpolation')
    points = _clean_samples(curve.get('points'), 'curve')
    if any(a[0] >= b[0] for a, b in zip(points, points[1:])):
        raise AutomationError('curve times must be unique')
    enabled = curve.get('enabled', True)
    if not isinstance(enabled, bool):
        raise AutomationError('enabled must be boolean')
    if transition:
        if points[0] != [0., 0.] or points[-1] != [1., 1.]:
            raise AutomationError('transition endpoints must be [0,0] and [1,1]')
        if any(not 0 <= t <= 1 or not 0 <= v <= 1 for t, v in points):
            raise AutomationError('transition curve must be normalized')
        if any(a[1] > b[1] for a, b in zip(points, points[1:])):
            raise AutomationError('transition curve must move forwards')
    return dict(points=points, mode=mode, enabled=enabled)


def _clean_samples(samples: Any, name: str) -> list:
    if not isinstance(samples, (list, tuple)) or not samples:
        raise AutomationError("track %s needs at least one sample" % name)
    if len(samples) > MAX_SAMPLES_PER_TRACK:
        raise AutomationError("track %s exceeds %d samples" % (name, MAX_SAMPLES_PER_TRACK))
    cleaned = []
    previous = None
    for sample in samples:
        if not isinstance(sample, (list, tuple)) or len(sample) != 2:
            raise AutomationError("samples must be [time, value] pairs")
        time = _number(sample[0], "sample time")
        value = _number(sample[1], "sample value")
        if time < 0.0:
            raise AutomationError("sample time must not be negative")
        if previous is not None and time < previous:
            raise AutomationError("samples must be ordered by time")
        previous = time
        cleaned.append([time, value])
    return cleaned


def value_at(samples: Iterable[Any], elapsed: float, mode: str = 'linear') -> float:
    """Linear interpolation with held ends."""

    track = list(samples)
    if not track:
        raise AutomationError("cannot read an empty track")
    time = _number(elapsed, "elapsed")
    if time <= track[0][0]:
        return float(track[0][1])
    if time >= track[-1][0]:
        return float(track[-1][1])
    low, high = 0, len(track) - 1
    while high - low > 1:
        middle = (low + high) // 2
        if track[middle][0] <= time:
            low = middle
        else:
            high = middle
    start_time, start_value = track[low]
    end_time, end_value = track[high]
    span = end_time - start_time
    if span <= 0.0:
        return float(end_value)
    ratio = (time - start_time) / span
    if mode == 'step':
        ratio = 0.0
    elif mode == 'smooth':
        ratio = ratio * ratio * (3.0 - 2.0 * ratio)
    elif mode == 'ease_in':
        ratio = ratio * ratio
    elif mode == 'ease_out':
        ratio = 1.0 - (1.0 - ratio) ** 2
    return float(start_value) + (float(end_value) - float(start_value)) * ratio


def values_at(automation: Mapping[str, Any], cue_id: str, elapsed: float) -> dict:
    """Every automated parameter of one cue at one moment."""

    tracks = automation.get("tracks", {}).get(str(cue_id))
    values = {name: value_at(samples, elapsed) for name, samples in (tracks or {}).items()}
    for name, curve in automation.get('edits', {}).get(str(cue_id), {}).items():
        if curve.get('enabled', True):
            values[name] = value_at(curve['points'], elapsed, curve['mode'])
    return values


def transition_plan(plan, automation, cue_id):
    """Shape the existing A/B plan, keeping the sequencer as the only clock."""
    from dataclasses import replace
    curve = automation.get('transitions', {}).get(cue_id)
    if not curve or not curve.get('enabled', True) or plan.transition == 'cut' or not plan.incoming_slot:
        return plan
    progress = value_at(curve['points'], plan.progress, curve['mode'])
    return replace(plan, progress=progress,
                   output_b_mix=progress if plan.outgoing_slot == 'A' else 1.0-progress)


def playback_plan(plan, data, cue_id, elapsed):
    from dataclasses import replace
    plan = transition_plan(plan, data, cue_id)
    if getattr(plan, 'timing_mode', 'legacy') == 'overlap':
        levels = {}
        for slot in ('a', 'b'):
            cue = getattr(plan, 'slot_' + slot)
            moment = getattr(plan, 'slot_' + slot + '_time')
            value = values_at(data, cue.id, moment).get('brightness', cue.brightness) if cue else 0.0
            levels['slot_' + slot + '_brightness'] = max(0., min(1., float(value)))
        return replace(plan, **levels)
    recorded = data.get('tracks', {}).get(cue_id, {}).get('brightness')
    curve = data.get('edits', {}).get(cue_id, {}).get('brightness')
    brightness = value_at(recorded, elapsed) if recorded else None
    if curve and curve.get('enabled', True):
        brightness = value_at(curve['points'], elapsed, curve['mode'])
    if brightness is not None:
        plan = replace(plan, brightness=0.0 if plan.blackout else max(0., min(1., brightness)))
    return plan


def copy_cue(data, source_id, target_id):
    """Duplicate original and edited lanes together without moving the source."""
    from copy import deepcopy
    result = validate(data)
    for section in ('tracks', 'edits', 'transitions'):
        if source_id in result.get(section, {}):
            result[section][target_id] = deepcopy(result[section][source_id])
    return result


def cue_ids(automation: Mapping[str, Any]) -> tuple:
    return tuple(sorted(automation.get("tracks", {})))


def track_length(automation: Mapping[str, Any], cue_id: str) -> float:
    tracks = automation.get("tracks", {}).get(str(cue_id)) or {}
    return max((samples[-1][0] for samples in tracks.values() if samples), default=0.0)


def clear_cue(automation: Mapping[str, Any], cue_id: str) -> dict:
    result = validate(automation)
    result["tracks"].pop(str(cue_id), None)
    for section in ('edits', 'transitions'):
        result.get(section, {}).pop(str(cue_id), None)
    return result


def rename_cue(automation: Mapping[str, Any], old_id: str, new_id: str) -> dict:
    """Keep recordings attached when a cue is duplicated or renamed."""

    result = validate(automation)
    track = result["tracks"].pop(str(old_id), None)
    if track:
        result["tracks"][str(new_id)] = track
    for section in ('edits', 'transitions'):
        layer = result.get(section, {}).pop(str(old_id), None)
        if layer is not None:
            result[section][str(new_id)] = layer
    return result


def merge(automation: Mapping[str, Any], cue_id: str, tracks: Mapping[str, Any]) -> dict:
    """Replace the recording of one cue, leaving the other cues alone."""

    result = validate(automation)
    clean = {}
    for name, samples in tracks.items():
        if not recordable(name):
            raise AutomationError("parameter not recordable: %s" % name)
        clean[name] = _clean_samples(samples, name)
    if clean:
        result["tracks"][str(cue_id)] = clean
    else:
        result["tracks"].pop(str(cue_id), None)
    return validate(result)


class Recorder:
    """Collects samples while a cue plays.

    All of the take lives in a plain dict (``state``) so a host can keep it
    somewhere that survives its own reloads. TouchDesigner re-executes a DAT
    module whenever it feels like it, and a recorder held only in a module
    global silently disappears mid-take - the take then looks as though no
    control was ever touched.

    Only changes are kept: a control that is not touched costs two samples,
    not one per frame. ``MIN_INTERVAL`` bounds the rate so a fast render loop
    cannot fill the track, and the first sample of every touched parameter is
    always written so playback starts from the value the operator saw.
    """

    def __init__(self, cue_id: str, *, epsilon: float = EPSILON,
                 max_samples: int = MAX_SAMPLES_PER_TRACK, state: dict | None = None) -> None:
        if not str(cue_id).strip():
            raise AutomationError("recorder needs a cue id")
        self.cue_id = str(cue_id)
        self.epsilon = float(epsilon)
        self.max_samples = int(max_samples)
        if state is None:
            state = new_take(self.cue_id)
        self.state = state

    @classmethod
    def from_state(cls, state: Mapping[str, Any], **kwargs) -> "Recorder":
        """Resume a take that was stored outside this process."""

        if not isinstance(state, dict):
            raise AutomationError("take state must be a dict")
        for key in ("cue_id", "tracks", "last", "changes"):
            if key not in state:
                raise AutomationError("take state is missing %s" % key)
        return cls(state["cue_id"], state=state, **kwargs)

    @property
    def _tracks(self) -> dict:
        return self.state["tracks"]

    @property
    def _last(self) -> dict:
        return self.state["last"]

    @property
    def changes(self) -> int:
        return int(self.state["changes"])

    @property
    def dropped(self) -> int:
        return int(self.state.get("dropped", 0))

    @property
    def first_time(self):
        return self.state.get("first_time")

    @property
    def last_time(self):
        return self.state.get("last_time")

    def sample(self, elapsed: float, values: Mapping[str, Any]) -> None:
        time = _number(elapsed, "elapsed")
        if time < 0.0:
            raise AutomationError("elapsed must not be negative")
        state = self.state
        if state.get("first_time") is None:
            state["first_time"] = time
        state["last_time"] = time
        for name, raw in values.items():
            if not recordable(name):
                continue
            value = _number(raw, name)
            track = state["tracks"].setdefault(name, [])
            if not track:
                track.append([time, value])
                state["last"][name] = [time, value]
                continue
            last_time, last_value = state["last"][name]
            if abs(value - last_value) <= self.epsilon:
                continue
            state["changes"] = int(state["changes"]) + 1
            if time - last_time < MIN_INTERVAL:
                # Keep the newest value inside one frame instead of stacking.
                track[-1] = [time, value]
                state["last"][name] = [time, value]
                continue
            if len(track) >= self.max_samples:
                state["dropped"] = int(state.get("dropped", 0)) + 1
                continue
            track.append([time, value])
            state["last"][name] = [time, value]

    def result(self) -> dict:
        """Tracks with a trailing sample so playback holds the final value."""

        tracks = {}
        for name, track in self.state["tracks"].items():
            if len(track) < 2:
                continue
            tracks[name] = [list(sample) for sample in track]
        return tracks

    def is_empty(self) -> bool:
        return not self.result()

    @property
    def span(self) -> float:
        """Seconds of cue time the take covered; 0.0 means the clock stood still."""

        first, last = self.state.get("first_time"), self.state.get("last_time")
        if first is None or last is None:
            return 0.0
        return max(0.0, float(last) - float(first))

    def diagnosis(self) -> str:
        """Why result() is empty, in the operator's terms."""

        if self.result():
            return ''
        if not self.changes:
            return 'no-movement'
        if self.span <= 0.0:
            return 'no-time'
        return 'too-short'


def new_take(cue_id: str) -> dict:
    """A blank, host-storable take."""

    return {"cue_id": str(cue_id), "tracks": {}, "last": {},
            "changes": 0, "dropped": 0, "first_time": None, "last_time": None}
