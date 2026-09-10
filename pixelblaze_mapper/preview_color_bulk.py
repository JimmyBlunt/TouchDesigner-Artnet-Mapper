"""Vectorized normalization for the reviewed LED Preview input-color branch.

No coordinate, fallback animation, mask or output behavior lives in this helper.
Source replacement is tied to the captured callback and its exact scalar block.
"""
from hashlib import sha256
import numpy as np


CAPTURED_SHA256 = 'bb890e8140ee00735d78b16c080eaa46b777bc11910e660d4a1e35626688accf'
MARKER = '# PREVIEW_RGB_BULK_V1'
SCALAR_BLOCK = """        maxv=max(max(colorop[name].vals[:n]) for name in ('r','g','b'))
        scale=(1.0/65025.0 if maxv > 255.0001 else 1.0/255.0) if maxv > 1.0001 else 1.0
        colors=[[max(0.0,min(1.0,float(v)*scale)) for v in colorop[name].vals[:n]] for name in ('r','g','b')]
"""
BULK_BLOCK = """        # PREVIEW_RGB_BULK_V1
        from pixelblaze_mapper.preview_color_bulk import normalized_chop_colors
        colors=normalized_chop_colors(colorop, n)
"""


def normalize_rgb(channels, n):
    """Return detached float64 RGB rows with the legacy global-range heuristic.

    Float64 preserves the Python float multiplication used in the scalar code.
    NaN/infinity use the original ordered max/min operations because their
    behavior is order-dependent and cannot be replaced by NumPy nan reduction.
    """
    if type(n) is not int or n < 0:
        raise ValueError('Preview sample count must be a non-negative integer')
    values = np.asarray(channels, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 3 or values.shape[1] < n:
        raise ValueError('Expected three RGB channels with at least n samples')
    values = values[:, :n].copy()
    if n == 0:
        return values
    if not np.isfinite(values).all():
        rows = values.tolist()
        maxv = max(max(row) for row in rows)
        scale = (1.0/65025.0 if maxv > 255.0001 else 1.0/255.0) if maxv > 1.0001 else 1.0
        return np.asarray([[max(0.0, min(1.0, float(v)*scale)) for v in row] for row in rows])
    maxv = float(values.max())
    scale = (1.0/65025.0 if maxv > 255.0001 else 1.0/255.0) if maxv > 1.0001 else 1.0
    np.multiply(values, scale, out=values)
    np.clip(values, 0.0, 1.0, out=values)
    return values


def normalized_chop_colors(colorop, n):
    """Read r/g/b exactly once each; preserve the callback's list-of-lists API."""
    return normalize_rgb([colorop[name].vals[:n] for name in ('r', 'g', 'b')], n).tolist()


def source_for_bulk(source, expected_sha256=CAPTURED_SHA256):
    """Validate the captured hash AND exact block, then replace only that block."""
    if sha256(source.encode('utf-8')).hexdigest() != expected_sha256:
        raise ValueError('LED Preview callback differs from the captured baseline')
    if source.count(SCALAR_BLOCK) != 1 or MARKER in source:
        raise ValueError('Expected exactly one reviewed scalar RGB normalization block')
    changed = source.replace(SCALAR_BLOCK, BULK_BLOCK, 1)
    compile(changed, '<LED Preview bulk colors>', 'exec')
    return changed


def ensure_bulk_source(source):
    """Idempotent builder upgrade, verifying the original source by reversal."""
    if MARKER not in source:
        return source_for_bulk(source)
    if source.count(BULK_BLOCK) != 1 or SCALAR_BLOCK in source:
        raise ValueError('LED Preview bulk block differs from the reviewed helper call')
    restored = source.replace(BULK_BLOCK, SCALAR_BLOCK, 1)
    if sha256(restored.encode('utf-8')).hexdigest() != CAPTURED_SHA256:
        raise ValueError('Optimized LED Preview differs from the reviewed callback')
    return source
