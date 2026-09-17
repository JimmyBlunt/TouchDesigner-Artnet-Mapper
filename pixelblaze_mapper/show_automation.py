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
    "speed", "scale", "width", "focus_x", "focus_y", "zoom", "intensity",
    "contrast", "trail", "direction", "rotation_degrees", "effect_transition",
    "hybrid_mix", "density", "brightness",
)
MAX_SAMPLES_PER_TRACK = 4000
MIN_INTERVAL = 1.0 / 60.0
EPSILON = 1e-4


class AutomationError(ValueError):
    """Raised when a recording or track is malformed."""


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
            if name not in RECORDABLE:
                raise AutomationError("parameter not recordable: %s" % name)
            clean[name] = _clean_samples(samples, name)
        if clean:
            result[cue_id] = clean
    return {"schema": SCHEMA, "version": SCHEMA_VERSION, "tracks": result}


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


def value_at(samples: Iterable[Any], elapsed: float) -> float:
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
    return float(start_value) + (float(end_value) - float(start_value)) * ratio


def values_at(automation: Mapping[str, Any], cue_id: str, elapsed: float) -> dict:
    """Every automated parameter of one cue at one moment."""

    tracks = automation.get("tracks", {}).get(str(cue_id))
    if not tracks:
        return {}
    return {name: value_at(samples, elapsed) for name, samples in tracks.items()}


def cue_ids(automation: Mapping[str, Any]) -> tuple:
    return tuple(sorted(automation.get("tracks", {})))


def track_length(automation: Mapping[str, Any], cue_id: str) -> float:
    tracks = automation.get("tracks", {}).get(str(cue_id)) or {}
    return max((samples[-1][0] for samples in tracks.values() if samples), default=0.0)


def clear_cue(automation: Mapping[str, Any], cue_id: str) -> dict:
    result = validate(automation)
    result["tracks"].pop(str(cue_id), None)
    return result


def rename_cue(automation: Mapping[str, Any], old_id: str, new_id: str) -> dict:
    """Keep recordings attached when a cue is duplicated or renamed."""

    result = validate(automation)
    track = result["tracks"].pop(str(old_id), None)
    if track:
        result["tracks"][str(new_id)] = track
    return result


def merge(automation: Mapping[str, Any], cue_id: str, tracks: Mapping[str, Any]) -> dict:
    """Replace the recording of one cue, leaving the other cues alone."""

    result = validate(automation)
    clean = {}
    for name, samples in tracks.items():
        if name not in RECORDABLE:
            raise AutomationError("parameter not recordable: %s" % name)
        clean[name] = _clean_samples(samples, name)
    if clean:
        result["tracks"][str(cue_id)] = clean
    else:
        result["tracks"].pop(str(cue_id), None)
    return validate(result)


class Recorder:
    """Collects samples while a cue plays.

    Only changes are kept: a control that is not touched costs two samples,
    not one per frame. ``MIN_INTERVAL`` bounds the rate so a fast render loop
    cannot fill the track, and the first sample of every touched parameter is
    always written so playback starts from the value the operator saw.
    """

    def __init__(self, cue_id: str, *, epsilon: float = EPSILON,
                 max_samples: int = MAX_SAMPLES_PER_TRACK) -> None:
        if not str(cue_id).strip():
            raise AutomationError("recorder needs a cue id")
        self.cue_id = str(cue_id)
        self.epsilon = float(epsilon)
        self.max_samples = int(max_samples)
        self._tracks: dict = {}
        self._last: dict = {}
        self.dropped = 0

    def sample(self, elapsed: float, values: Mapping[str, Any]) -> None:
        time = _number(elapsed, "elapsed")
        if time < 0.0:
            raise AutomationError("elapsed must not be negative")
        for name, raw in values.items():
            if name not in RECORDABLE:
                continue
            value = _number(raw, name)
            track = self._tracks.setdefault(name, [])
            if not track:
                track.append([time, value])
                self._last[name] = (time, value)
                continue
            last_time, last_value = self._last[name]
            if abs(value - last_value) <= self.epsilon:
                continue
            if time - last_time < MIN_INTERVAL:
                # Keep the newest value inside one frame instead of stacking.
                track[-1] = [time, value]
                self._last[name] = (time, value)
                continue
            if len(track) >= self.max_samples:
                self.dropped += 1
                continue
            track.append([time, value])
            self._last[name] = (time, value)

    def result(self) -> dict:
        """Tracks with a trailing sample so playback holds the final value."""

        tracks = {}
        for name, track in self._tracks.items():
            if len(track) < 2:
                continue
            tracks[name] = [list(sample) for sample in track]
        return tracks

    def is_empty(self) -> bool:
        return not self.result()
