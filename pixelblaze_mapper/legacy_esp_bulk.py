"""Reviewed legacy ESP transfer: identical 510-byte universes, bulk writes."""
import hashlib
import numpy as np


def frames(rgb, *, offset, count, order, master, inactive=()):
    from .output_slot_mask import channels
    values = np.asarray(channels(rgb, inactive), dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 3 or not np.isfinite(values).all():
        raise ValueError('Expected finite RGB source channels')
    if (not isinstance(order, str) or sorted(order) != ['B', 'G', 'R']
            or type(master) not in (int, float) or not 0 <= master <= 1):
        raise ValueError('Invalid color order/brightness')
    if type(offset) is not int or type(count) is not int or offset < 0 or not 0 <= count <= 1679:
        raise ValueError('Invalid legacy source extent')
    output = np.zeros(5100, dtype=np.float64)
    selected = values[['RGB'.index(key) for key in order], offset:offset+count].T
    # Keep multiplication order and round-to-even behavior of Python round.
    output[:selected.size] = np.rint(np.clip(selected, 0, 1) * 255.0 * master).reshape(-1)
    return output.reshape(10, 510)


def source_for_bulk(source, expected_sha256):
    if hashlib.sha256(source.encode()).hexdigest() != expected_sha256:
        raise ValueError('Legacy ESP source differs from captured baseline')
    start = source.index("    sources = {'R': source['r']")
    end = source.index('    # Unwritten channels', start)
    replacement = '''    # SPARSE_SOURCE_MASK_V1
    from pixelblaze_mapper.legacy_esp_bulk import frames
    from pixelblaze_mapper.output_slot_mask import ranges_for
    packed = frames([source[key].vals for key in 'rgb'], offset=source_offset,
        count=pixel_count, order=order, master=master,
        inactive=ranges_for(op, source.numSamples))
    for output, values in zip(outputs, packed):
        output.vals = values.tolist()

'''
    changed = source[:start] + replacement + source[end:]
    compile(changed, '<legacy ESP bulk>', 'exec')
    return changed
