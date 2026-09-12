"""Bounded optical erasure decoding; never infer IDs from time or target FPS.

Unknown bits may be recovered only if exactly one Gray+CRC8 codeword matches
every directly observed bit. Known-bit errors are never deliberately corrected.
This does not eliminate undetected mixed-frame errors; temporal confirmation
and separate reporting of recovered samples are still required.
"""
from functools import lru_cache
import math
from .gico_camera_benchmark import encode, decode, MODULUS, MARKERS


@lru_cache(maxsize=1)
def words():
    import numpy as np
    return np.array([sum(bit << i for i, bit in enumerate(encode(n)[:20]))
                     for n in range(MODULUS)], dtype=np.uint32)


def decode_scores(scores):
    if len(scores) != MARKERS or not all(math.isfinite(float(x)) for x in scores):
        return None, 'invalid_scores', 0
    reference = float(scores[20])
    if not .45 <= reference <= 1.8:
        return None, 'reference_exposure', 0
    ratios = [float(x)/reference for x in scores[:20]]
    unknown = [i for i, x in enumerate(ratios) if .25 < x < .75]
    count = len(unknown)
    if count > 3 or sum(i < 12 for i in unknown) > 2:
        return None, 'too_many_erasures', count
    bits = [int(x >= .75) for x in ratios] + [1]
    if not count:
        value = decode(bits)
        return value, 'direct_crc' if value is not None else 'crc_mismatch', 0
    # At most three erasures also preserves at least five observed CRC bits.
    known_mask = sum(1 << i for i in range(20) if i not in unknown)
    observed = sum(bit << i for i, bit in enumerate(bits[:20]))
    import numpy as np
    matches = np.flatnonzero((words() & known_mask) == (observed & known_mask))
    if len(matches) != 1:
        return None, 'ambiguous_codeword' if len(matches) > 1 else 'crc_mismatch', count
    return int(matches[0]), 'recovered_crc', count
