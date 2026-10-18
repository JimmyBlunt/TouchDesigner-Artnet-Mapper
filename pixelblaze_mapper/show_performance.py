"""Cached static TD UV tables and bulk RGB mixing; no output on import."""
import numpy as np
from . import show_renderer as reference

_table_cache = {}


def panel_data(table):
    table.cook(force=False)
    signature = (id(table), table.totalCooks, table.numRows, table.numCols)
    cached = _table_cache.get(table.path)
    if cached is not None and cached[0] == signature:
        return cached[1]
    rows = [line.split('\t') for line in table.text.splitlines() if line]
    header = rows[0]
    required = ('index', 'panel', 'global_u', 'global_v', 'local_u', 'local_v')
    if len(rows) != table.numRows or len(set(header)) != len(header) or not set(required) <= set(header):
        raise ValueError('Invalid canonical panel UV table')
    index = header.index('index')
    if any(len(row) != len(header) or row[index] != str(i) for i, row in enumerate(rows[1:])):
        raise ValueError('Canonical panel UV indices must remain ordered')
    columns = tuple(tuple(float(row[header.index(key)]) for row in rows[1:])
                    for key in required[2:])
    groups = reference.source_groups_from_panels(tuple(row[header.index('panel')] for row in rows[1:]))
    data = dict(columns=columns, groups=groups, frames={})
    _table_cache[table.path] = (signature, data)
    return data


def uv_cook(script_op, table, mode, blend):
    data = panel_data(table)
    key = (mode, float(blend))
    values = data['frames'].get(key)
    if values is None:
        u, v = reference.slot_uv_frame(*data['columns'], mode=mode, hybrid_mix=blend)
        values = np.asarray((u, v, (0.,)*len(u)), dtype=np.float32)
        if len(data['frames']) >= 8:
            data['frames'].clear()
        data['frames'][key] = values
    write_channels(script_op, values, ('tx', 'ty', 'tz'))


def write_channels(script_op, values, names):
    script_op.clear()
    script_op.numSamples = values.shape[1]
    for name, row in zip(names, values):
        script_op.appendChan(name).copyNumpyArray(row)


def render_numpy(a, b, u, v, **options):
    """Bulk snapshots and blends; retain reference rules for complex reveals."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    count = len(u)
    if a.shape != b.shape or a.ndim != 2 or not a.shape[0] or a.shape[1] != count or len(v) != count:
        raise ValueError('Slot arrays must match canonical UV source count')
    transition = options['transition']
    mix, brightness = float(options['output_b_mix']), float(options['brightness'])
    if transition not in reference.TRANSITIONS or not np.isfinite([mix, brightness]).all() or not 0 <= mix <= 1 or not 0 <= brightness <= 1:
        raise ValueError('Invalid transition mix or brightness')
    if not count:
        raise ValueError('Empty UV source')
    if transition not in ('cut', 'crossfade', 'fade_black') and mix not in (0., 1.):
        return np.asarray(reference.render_frame(a.tolist(), b.tolist(), u=u, v=v, **options), dtype=np.float32)
    groups = options.get('source_groups')
    if groups is None:
        if count != reference.TOTAL_PIXELS:
            raise ValueError('Expanded sources need explicit groups')
        masks = [reference._target_mask_frame(reference.normalize_target_groups(options[key]))
                 for key in ('targets_a', 'targets_b')]
    else:
        groups = tuple(groups)
        if len(groups) != count or any(g is not None and g not in reference.SOURCE_GROUP_NAMES for g in groups):
            raise ValueError('Invalid source groups')
        masks = [reference._explicit_target_mask(reference.normalize_target_groups(options[key]), groups)
                 for key in ('targets_a', 'targets_b')]
    gain = 0. if options['blackout'] else brightness*reference.transition_gain_scale(transition, mix)
    weight = mix if transition == 'crossfade' or mix in (0., 1.) else float(mix >= .5)
    return np.asarray(a*((1-weight)*gain*np.asarray(masks[0])) + b*(weight*gain*np.asarray(masks[1])), dtype=np.float32)


def install_uv_source(source):
    if '# SHOW_UV_CACHE_V1' in source:
        return source
    start = source.index('    count = table.numRows - 1', source.index('def onCook('))
    return source[:start] + '''    # SHOW_UV_CACHE_V1
    from pixelblaze_mapper.show_performance import uv_cook
    uv_cook(scriptOp, table, mode, blend)
    return
'''


def install_effect_uv_source(source):
    if '# EFFECT_UV_CACHE_V1' in source:
        return source
    anchor = '    blend = max(0.0, min(1.0, blend))\n'
    if source.count(anchor) != 1:
        raise ValueError('Unknown material UV callback')
    start = source.index(anchor) + len(anchor)
    return source[:start] + '''    # EFFECT_UV_CACHE_V1
    from pixelblaze_mapper.show_performance import uv_cook
    uv_cook(scriptOp, table, mode if mode in ('global', 'panel', 'panel_local', 'hybrid') else 'global', blend)
    return
'''


def install_renderer_source(source):
    if '# SHOW_NUMPY_MIX_V1' in source:
        return source
    first = source.index('    source_groups = _source_groups(panels, count)')
    source = source[:first] + source[first:].replace('    source_groups = _source_groups(panels, count)',
        '    # SHOW_NUMPY_MIX_V1\n    from pixelblaze_mapper.show_performance import panel_data, render_numpy\n    source_groups = panel_data(panels)["groups"]',1)
    start = source.index('    input_a = [slot_a[name].vals')
    end = source.index('    frame = render_frame(', start)
    source = source[:start] + '''    input_a = slot_a.numpyArray()[[slot_a[name].index for name in ('r', 'g', 'b')]]
    input_b = slot_b.numpyArray()[[slot_b[name].index for name in ('r', 'g', 'b')]]
    uv = coordinates.numpyArray()
    coord_u, coord_v = uv[coordinates['tx'].index], uv[coordinates['ty'].index]
''' + source[end:].replace('    frame = render_frame(', '    frame = render_numpy(', 1)
    start = source.index('    scriptOp.clear()', source.index('    frame = render_numpy('))
    source = source[:start] + '''    from pixelblaze_mapper.show_performance import write_channels
    write_channels(scriptOp, frame, ('r', 'g', 'b'))
    return
'''
    return source
