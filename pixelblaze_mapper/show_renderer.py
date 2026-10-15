"""Pure per-LED contracts for the Show Control live renderer.

The live Show renderer samples slot A and slot B independently before calling
these helpers.  Target masks therefore operate on canonical LED indices and
remain correct even when several panels use the same panel-local UV values.
"""

from __future__ import annotations

from functools import lru_cache
from math import atan2, hypot, isfinite, pi, sin
from typing import Iterable, Sequence

from pixelblaze_mapper.installation_contract import PANEL_BY_NAME, TOTAL_PIXELS


TARGET_GROUPS = frozenset({"all", "middle", "upper", "lower", "rear"})
SOURCE_GROUP_NAMES = TARGET_GROUPS - {"all"}
# Ordered so the UI can list them by family; the set is what validates.
TRANSITION_INFO = (
    ("cut", "blend", "harter Schnitt"),
    ("crossfade", "blend", "lineare Überblendung"),
    ("fade_black", "blend", "über Schwarz blenden"),
    ("burn", "blend", "weiche, gefaserte Auflösung"),
    ("dissolve", "reveal", "zufällige LEDs zuerst"),
    ("glitch", "reveal", "blockweise, springend"),
    ("wipe", "reveal", "Wisch nach rechts"),
    ("wipe_left", "reveal", "Wisch nach links"),
    ("wipe_up", "reveal", "Wisch nach oben"),
    ("wipe_down", "reveal", "Wisch nach unten"),
    ("radial", "reveal", "von der Mitte nach außen"),
    ("iris", "reveal", "von außen zur Mitte"),
    ("bars", "reveal", "senkrechte Lamellen"),
    ("checker", "reveal", "Schachbrettfelder"),
    ("spiral", "reveal", "Winkel-Sweep um die Mitte"),
)
TRANSITIONS = frozenset(name for name, _family, _label in TRANSITION_INFO)
# Reveals compare a per-LED threshold against the mix; blends do not.
_REVEALS = frozenset(name for name, family, _label in TRANSITION_INFO if family == "reveal")
BAR_COUNT = 12.0
CHECKER_COLUMNS = 16
CHECKER_ROWS = 10
BURN_FEATHER = 0.18


def _clamp(value: float) -> float:
    return 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)


def _reveal_threshold(transition: str, index: int, u: float, v: float, mix: float) -> float:
    """Per-LED reveal threshold in 0..1; the LED flips once mix passes it."""

    if transition == "wipe":
        return _clamp(u)
    if transition == "wipe_left":
        return 1.0 - _clamp(u)
    if transition == "wipe_up":
        return 1.0 - _clamp(v)
    if transition == "wipe_down":
        return _clamp(v)
    if transition == "radial":
        return _clamp(hypot(u - 0.5, v - 0.5) * 1.42)
    if transition == "iris":
        return 1.0 - _clamp(hypot(u - 0.5, v - 0.5) * 1.42)
    if transition == "bars":
        return (_clamp(u) * BAR_COUNT) % 1.0
    if transition == "checker":
        column = int(_clamp(u) * CHECKER_COLUMNS)
        row = int(_clamp(v) * CHECKER_ROWS)
        return _hash(column + row * 31)
    if transition == "spiral":
        return (atan2(v - 0.5, u - 0.5) / (2.0 * pi)) % 1.0
    if transition == "dissolve":
        return _hash(index)
    # glitch: whole blocks jump together, re-salted as the mix advances
    return _hash(index // 16, float(int(mix * 30.0)))


def transition_gain_scale(transition: str, output_b_mix: float) -> float:
    """Brightness factor during the transition; only fade_black dips."""

    if transition != "fade_black":
        return 1.0
    return abs(2.0 * float(output_b_mix) - 1.0)


def slot_uv_frame(global_u, global_v, local_u, local_v, *, mode='global', hybrid_mix=0.5):
    """Choose a cue's own UVs without consulting the external material player."""
    if mode not in ('global', 'panel', 'panel_local', 'hybrid'):
        raise ValueError('Unknown slot coordinate mode')
    if len({len(values) for values in (global_u, global_v, local_u, local_v)}) != 1:
        raise ValueError('Slot UV columns must have identical lengths')
    blend = float(hybrid_mix)
    if not isfinite(blend) or not 0 <= blend <= 1:
        raise ValueError('Slot hybrid mix must be finite and inside 0..1')
    columns = tuple(tuple(float(value) for value in values) for values in (global_u, global_v, local_u, local_v))
    if any(not isfinite(value) for values in columns for value in values):
        raise ValueError('Slot UV values must be finite')
    gu, gv, lu, lv = columns
    if mode == 'global':
        return gu, gv
    if mode in ('panel', 'panel_local'):
        return lu, lv
    return (tuple(a + (b - a) * blend for a, b in zip(gu, lu)),
            tuple(a + (b - a) * blend for a, b in zip(gv, lv)))


@lru_cache(maxsize=32)
def _target_mask_frame(selected: tuple[str, ...]) -> tuple[float, ...]:
    """Build a target mask once per group combination, not once per frame."""

    if "all" in selected:
        return (1.0,) * TOTAL_PIXELS
    ranges = tuple((PANEL_BY_NAME[group].start, PANEL_BY_NAME[group].stop) for group in selected)
    return tuple(float(any(start <= index < stop for start, stop in ranges))
                 for index in range(TOTAL_PIXELS))


@lru_cache(maxsize=32)
def source_groups_from_panels(panels: tuple[str, ...]) -> tuple[str | None, ...]:
    """Resolve explicit material panel labels; unknown labels never imply rear.

    The rear_ namespace is used for individually acquired rear panels. A source
    address alone is never evidence that a new fixture belongs to that group.
    """
    return tuple(panel if panel in SOURCE_GROUP_NAMES else
                 "rear" if panel.startswith("rear_") else None for panel in panels)


@lru_cache(maxsize=32)
def _explicit_target_mask(selected, source_groups):
    if "all" in selected:
        return (1.0,) * len(source_groups)
    return tuple(float(group in selected) for group in source_groups)


def normalize_target_groups(groups: Iterable[str]) -> tuple[str, ...]:
    """Validate and canonicalize a non-empty renderer target selection."""

    if isinstance(groups, (str, bytes)):
        raise ValueError("target groups must be an iterable of group names")
    result = tuple(groups)
    if not result:
        raise ValueError("at least one target group is required")
    if any(not isinstance(group, str) or group not in TARGET_GROUPS for group in result):
        raise ValueError("target groups must use all, middle, upper, lower, or rear")
    if len(set(result)) != len(result):
        raise ValueError("target groups must not contain duplicates")
    if "all" in result and len(result) != 1:
        raise ValueError("all cannot be combined with another target group")
    return result


def target_mask(groups: Iterable[str], led_index: int) -> float:
    """Return the exact canonical per-LED mask for ``groups``."""

    selected = normalize_target_groups(groups)
    if isinstance(led_index, bool) or not isinstance(led_index, int):
        raise IndexError("LED index must be an integer")
    if not 0 <= led_index < TOTAL_PIXELS:
        raise IndexError(f"LED index must be 0..{TOTAL_PIXELS - 1}")
    return _target_mask_frame(selected)[led_index]


def _hash(index: int, salt: float = 0.0) -> float:
    return (sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


def transition_b_weight(
    transition: str,
    output_b_mix: float,
    led_index: int,
    uv: Sequence[float],
) -> float:
    """Return the slot-B selection weight for one canonical LED."""

    if transition not in TRANSITIONS:
        raise ValueError("unknown Show Control transition")
    mix = float(output_b_mix)
    if not isfinite(mix) or not 0.0 <= mix <= 1.0:
        raise ValueError("output_b_mix must be finite and inside 0..1")
    if len(uv) != 2:
        raise ValueError("uv must contain exactly two values")
    u, v = float(uv[0]), float(uv[1])
    if not isfinite(u) or not isfinite(v):
        raise ValueError("uv values must be finite")
    if mix == 0.0 or mix == 1.0:
        return mix
    if transition == "crossfade":
        return mix
    if transition in ("cut", "fade_black"):
        return float(mix >= 0.5)
    if transition == "burn":
        # Feathered edge: a band of LEDs is mid-blend instead of flipping.
        return _clamp((mix * (1.0 + BURN_FEATHER) - _hash(led_index)) / BURN_FEATHER)
    return float(_reveal_threshold(transition, led_index, u, v, mix) <= mix)


def render_led(
    color_a: Sequence[float],
    color_b: Sequence[float],
    *,
    led_index: int,
    uv: Sequence[float],
    transition: str,
    output_b_mix: float,
    brightness: float,
    blackout: bool,
    targets_a: Iterable[str],
    targets_b: Iterable[str],
) -> tuple[float, ...]:
    """Mask both slots, transition them, then apply cue brightness/blackout."""

    if len(color_a) != len(color_b) or not color_a:
        raise ValueError("slot colors must have the same non-zero component count")
    level = float(brightness)
    if not isfinite(level) or not 0.0 <= level <= 1.0:
        raise ValueError("brightness must be finite and inside 0..1")
    mask_a = target_mask(targets_a, led_index)
    mask_b = target_mask(targets_b, led_index)
    weight_b = transition_b_weight(transition, output_b_mix, led_index, uv)
    gain = 0.0 if blackout else level * transition_gain_scale(transition, output_b_mix)
    return tuple(
        ((1.0 - weight_b) * float(a) * mask_a + weight_b * float(b) * mask_b) * gain
        for a, b in zip(color_a, color_b)
    )


def render_frame(
    slot_a: Sequence[Sequence[float]],
    slot_b: Sequence[Sequence[float]],
    *,
    u: Sequence[float],
    v: Sequence[float],
    transition: str,
    output_b_mix: float,
    brightness: float,
    blackout: bool,
    targets_a: Iterable[str],
    targets_b: Iterable[str],
    source_groups: Sequence[str | None] | None = None,
    timing_mode: str = 'legacy',
    slot_a_gain: float = 1.0,
    slot_b_gain: float = 1.0,
    slot_a_brightness: float = 1.0,
    slot_b_brightness: float = 1.0,
    slot_a_tone=None,
    slot_b_tone=None,
) -> tuple[list[float], ...]:
    """Render all canonical LEDs without per-pixel validation/function calls.

    This is the TouchDesigner hot path. Panel masks are cached by group tuple;
    transition weights and the two masked gains are calculated once per frame,
    then each RGB channel is handled by one tight list comprehension.
    """

    if transition not in TRANSITIONS:
        raise ValueError("unknown Show Control transition")
    mix = float(output_b_mix)
    level = float(brightness)
    if not isfinite(mix) or not 0.0 <= mix <= 1.0:
        raise ValueError("output_b_mix must be finite and inside 0..1")
    if not isfinite(level) or not 0.0 <= level <= 1.0:
        raise ValueError("brightness must be finite and inside 0..1")
    if not slot_a or len(slot_a) != len(slot_b):
        raise ValueError("slot frames must have the same non-zero channel count")
    count = len(u)
    if not count or len(v) != count:
        raise ValueError("UV frames must have the same positive source count")
    if any(len(channel) != count for channel in tuple(slot_a) + tuple(slot_b)):
        raise ValueError("slot channels must match the canonical UV source count")

    selected_a = normalize_target_groups(targets_a)
    selected_b = normalize_target_groups(targets_b)
    if source_groups is None:
        if count != TOTAL_PIXELS:
            raise ValueError("Expanded source capacity requires explicit source groups")
        mask_a = _target_mask_frame(selected_a)
        mask_b = _target_mask_frame(selected_b)
    else:
        source_groups = tuple(source_groups)
        if len(source_groups) != count or any(group is not None and group not in SOURCE_GROUP_NAMES
                                              for group in source_groups):
            raise ValueError("Source groups must match the UV count and use canonical group names or None")
        mask_a = _explicit_target_mask(selected_a, source_groups)
        mask_b = _explicit_target_mask(selected_b, source_groups)
    overlap = timing_mode == 'overlap'
    if timing_mode not in ('legacy', 'overlap'):
        raise ValueError('Unknown Show timing mode')
    levels = (slot_a_gain, slot_b_gain, slot_a_brightness, slot_b_brightness)
    if overlap and any(not isfinite(float(x)) or not 0 <= float(x) <= 1 for x in levels):
        raise ValueError('Slot envelopes and brightness must be finite inside 0..1')
    gain = 0.0 if blackout else (1.0 if overlap else level) * transition_gain_scale(transition, mix)
    if gain == 0.0:
        return tuple([0.0] * count for _ in slot_a)

    if mix == 0.0 or mix == 1.0:
        weights_b: Sequence[float] = (mix,) * count
    elif transition == "crossfade":
        weights_b: Sequence[float] = (mix,) * count
    elif transition in ("cut", "fade_black"):
        weights_b = (float(mix >= 0.5),) * count
    elif transition == "burn":
        edge = mix * (1.0 + BURN_FEATHER)
        weights_b = tuple(_clamp((edge - _hash(index)) / BURN_FEATHER) for index in range(count))
    elif transition == "wipe":
        weights_b = tuple(float(_clamp(float(value)) <= mix) for value in u)
    elif transition == "wipe_left":
        weights_b = tuple(float(1.0 - _clamp(float(value)) <= mix) for value in u)
    elif transition == "wipe_down":
        weights_b = tuple(float(_clamp(float(value)) <= mix) for value in v)
    elif transition == "wipe_up":
        weights_b = tuple(float(1.0 - _clamp(float(value)) <= mix) for value in v)
    elif transition == "radial":
        weights_b = tuple(float(_clamp(hypot(float(x) - 0.5, float(y) - 0.5) * 1.42) <= mix)
                          for x, y in zip(u, v))
    elif transition == "iris":
        weights_b = tuple(float(1.0 - _clamp(hypot(float(x) - 0.5, float(y) - 0.5) * 1.42) <= mix)
                          for x, y in zip(u, v))
    elif transition == "dissolve":
        weights_b = tuple(float(_hash(index) <= mix) for index in range(count))
    elif transition in ("bars", "checker", "spiral"):
        weights_b = tuple(
            float(_reveal_threshold(transition, index, float(x), float(y), mix) <= mix)
            for index, (x, y) in enumerate(zip(u, v)))
    else:
        salt = float(int(mix * 30.0))
        weights_b = tuple(float(_hash(index // 16, salt) <= mix) for index in range(count))

    if overlap and transition == 'crossfade':
        # The clip envelopes ARE the crossfade. Applying mix again would
        # square matched fades and create a dark midpoint. Normalize only
        # excess opacity; intentionally unmatched fades may dip to black.
        denominator = max(1.0, slot_a_gain + slot_b_gain)
        gains_a = [mask * gain * slot_a_gain * slot_a_brightness / denominator for mask in mask_a]
        gains_b = [mask * gain * slot_b_gain * slot_b_brightness / denominator for mask in mask_b]
    else:
        a_level = slot_a_gain * slot_a_brightness if overlap else 1.0
        b_level = slot_b_gain * slot_b_brightness if overlap else 1.0
        gains_b = [weight * mask * gain * b_level for weight, mask in zip(weights_b, mask_b)]
        gains_a = [(1.0 - weight) * mask * gain * a_level for weight, mask in zip(weights_b, mask_a)]
    def tone(value, settings):
        if not overlap or settings is None:
            return float(value)
        intensity, contrast = map(float, settings)
        if not isfinite(intensity) or not isfinite(contrast) or intensity < 0 or contrast < 0:
            raise ValueError('Invalid slot tone')
        # TOP-to-CHOP samplers use rgbaunit=u256 (0..255); GPU textures use
        # normalized RGB. Convert only for tone, preserving the LED units.
        return _clamp((float(value) / 255.0 - .5) * contrast + .5) * intensity * 255.0
    return tuple(
        [tone(a, slot_a_tone) * gain_a + tone(b, slot_b_tone) * gain_b
         for a, b, gain_a, gain_b in zip(channel_a, channel_b, gains_a, gains_b)]
        for channel_a, channel_b in zip(slot_a, slot_b)
    )
