"""Bulk transfers for preview attributes; leave coordinate/missing logic intact."""
import numpy as np
from collections import OrderedDict
from .preview_color_bulk import normalize_rgb

# Derived arrays are transient. TD storage is serialized and dependency tracked.
_position_cache = OrderedDict()
_POSITION_CACHE_LIMIT = 8

MARKER = '# NUMPY_PREVIEW_TRANSFERS_V1'
REPLACEMENTS = (
    ("""    for axis,ci in [('tx',0),('ty',1),('tz',2)]:
        ch=scriptOp.appendChan(axis)
        ch.vals=[v[ci] for v in values]
""", """    # NUMPY_PREVIEW_TRANSFERS_V1
    from pixelblaze_mapper.preview_numpy import write_positions, write_colors
    write_positions(scriptOp, values)
"""),
    ("""        from pixelblaze_mapper.preview_color_bulk import normalized_chop_colors
        colors=normalized_chop_colors(colorop, n)
""", """        from pixelblaze_mapper.preview_numpy import read_colors
        colors=read_colors(colorop, n)
"""),
    ("""    # P0_CANONICAL_MISSING_BLACK
    for missing_index in missing:
        if 0 <= missing_index < n:
            colors[0][missing_index] = 0.0
            colors[1][missing_index] = 0.0
            colors[2][missing_index] = 0.0
    unavailable = set(missing)
    scriptOp.appendChan('a').vals = [0.0 if index in unavailable else 1.0 for index in range(n)]
    for name,vals in zip(('r','g','b'),colors):
        ch=scriptOp.appendChan(name)
        ch.vals=vals
""", """    # P0_CANONICAL_MISSING_BLACK
    write_colors(scriptOp, colors, missing, n)
"""),
)


def restore_source(source):
    if MARKER not in source:
        return source
    for old,new in reversed(REPLACEMENTS):
        if source.count(new) != 1:
            raise ValueError('Preview bulk transfer differs from reviewed block')
        source=source.replace(new,old,1)
    return source


def install_source(source):
    source=restore_source(source)
    for old,new in REPLACEMENTS:
        if source.count(old) != 1:
            raise ValueError('Preview bulk transfer source differs from reviewed block')
        source=source.replace(old,new,1)
    compile(source,'<numpy preview>','exec')
    return source


def read_colors(source,n):
    indices=[source[name].index for name in ('r','g','b')]
    return normalize_rgb(source.numpyArray()[indices],n)


def position_arrays(values):
    return np.ascontiguousarray(np.asarray(values,dtype=np.float32).T)


def color_arrays(colors,missing,n):
    rgb=np.array(colors,dtype=np.float32,copy=True,order='C')
    if rgb.shape != (3,n):
        raise ValueError('Preview color shape mismatch')
    indices=np.asarray([i for i in missing if 0<=i<n],dtype=np.intp)
    rgb[:,indices]=0
    alpha=np.ones(n,dtype=np.float32);alpha[indices]=0
    return rgb,alpha


def write_positions(script_op,values):
    # Read only our own cache metadata without making the operator depend on
    # a storage key it updates during onCook. External map reads remain tracked.
    signature=script_op.storage.get('coord_signature')
    key=id(script_op)
    cached=_position_cache.get(key)
    if (signature is not None and cached is not None
            and cached[0] is script_op and cached[1] == signature and cached[2] is values):
        positions=cached[3]
        _position_cache.move_to_end(key)
    else:
        positions=position_arrays(values)
        if signature is not None:
            _position_cache[key]=(script_op,signature,values,positions)
            _position_cache.move_to_end(key)
            while len(_position_cache)>_POSITION_CACHE_LIMIT:
                _position_cache.popitem(last=False)
    for name,row in zip(('tx','ty','tz'),positions):
        script_op.appendChan(name).copyNumpyArray(row)


def write_colors(script_op,colors,missing,n):
    rgb,alpha=color_arrays(colors,missing,n)
    script_op.appendChan('a').copyNumpyArray(alpha)
    for name,row in zip(('r','g','b'),rgb):
        script_op.appendChan(name).copyNumpyArray(row)
