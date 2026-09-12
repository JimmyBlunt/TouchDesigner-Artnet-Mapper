"""Vectorized TD snapshots; immutable routing and scalar rounding stay canonical."""
import numpy as np
from .multi_controller import MultiControllerValidationError, SLOTS_PER_UNIVERSE


class NumpyControllerPacker:
    def __init__(self, compiled):
        self.compiled = compiled
        writes = compiled.writes
        self.sources = np.asarray([w.source_index for w in writes], dtype=np.intp)
        self.components = np.asarray([w.component_indices for w in writes], dtype=np.intp).reshape(-1,3)
        self.destinations = np.asarray([w.frame_index*SLOTS_PER_UNIVERSE+w.slot for w in writes], dtype=np.intp)
        self._destination_slots = self.destinations[:,None] + np.arange(3)
        self._inactive_signature = None
        self._inactive_writes = np.empty(0,dtype=np.intp)

    def pack(self, rgb, inactive=()):
        values = np.asarray(rgb)
        if (values.ndim != 2 or values.shape[0] < 3
                or values.shape[1] < self.compiled.source_pixel_count
                or values.dtype.kind not in 'fiu'):
            raise MultiControllerValidationError('Expected numeric RGB array with enough source samples')
        # Promote before multiplying, matching round(float(channel)*scale).
        mapped = values[self.components, self.sources[:,None]].astype(np.float64)
        signature = []
        for first,last in inactive:
            if (type(first) is not int or type(last) is not int
                    or not 0 <= first <= last < values.shape[1]):
                raise ValueError('Invalid inactive source range')
            signature.append((first,last))
        signature = tuple(signature)
        if signature != self._inactive_signature:
            inactive_writes = np.zeros(len(self.sources),dtype=bool)
            for first,last in signature:
                inactive_writes |= (self.sources >= first) & (self.sources <= last)
            self._inactive_writes = np.flatnonzero(inactive_writes)
            self._inactive_signature = signature
        if self._inactive_writes.size:
            mapped[self._inactive_writes] = 0
        with np.errstate(over='ignore',invalid='ignore'):
            mapped *= 255.0*self.compiled.brightness
        if not np.isfinite(mapped).all():
            raise MultiControllerValidationError('Nonfinite mapped source value')
        np.rint(mapped,out=mapped)
        np.clip(mapped,0,255,out=mapped)
        output = np.zeros(self.compiled.frame_count*SLOTS_PER_UNIVERSE,dtype=np.uint8)
        output[self._destination_slots] = mapped.astype(np.uint8)
        return tuple(row.tobytes() for row in output.reshape(-1,SLOTS_PER_UNIVERSE))


def mask_array(values, inactive):
    output = np.array(values,dtype=np.float32,copy=True,order='C')
    if output.ndim != 2:
        raise ValueError('Expected channel/sample matrix')
    for first,last in inactive:
        if type(first) is not int or type(last) is not int or not 0 <= first <= last < output.shape[1]:
            raise ValueError('Invalid inactive source range')
        output[:,first:last+1] = 0
    return output


def legacy_mask_cook(script_op, op):
    from .output_slot_mask import ranges_for
    source = script_op.inputs[0]
    names = [c.name for c in source.chans()]
    values = mask_array(source.numpyArray(),ranges_for(op,source.numSamples))
    script_op.clear()
    script_op.numSamples=source.numSamples
    for name,row in zip(names,values):
        script_op.appendChan(name).copyNumpyArray(row)


LEGACY_CALLBACK = '''# SPARSE_SOURCE_MASK_V1
# NUMPY_LEGACY_MASK_V1
def onCook(scriptOp):
    from pixelblaze_mapper.numpy_realtime import legacy_mask_cook
    legacy_mask_cook(scriptOp, op)
'''


def install_sender(source):
    marker = '# NUMPY_ROUTER_PACK_V1'
    old = """    from pixelblaze_mapper.output_slot_mask import channels, ranges_for
    rgb = channels((source[0],source[1],source[2]), ranges_for(op, source.numSamples))
    frames = {config['name']: packer.controller(config['name']).pack_channels(*rgb) for config in configs}"""
    new = """    # NUMPY_ROUTER_PACK_V1
    from pixelblaze_mapper.output_slot_mask import ranges_for
    from pixelblaze_mapper.numpy_realtime import pack_td
    frames = pack_td(packer, source, configs, ranges_for(op, source.numSamples))"""
    if marker in source:
        if source.count(new) != 1 or old in source:
            raise ValueError('Installed sender packing block differs from reviewed block')
        return source
    if source.count(old) != 1:
        raise ValueError('Unreviewed sender packing block')
    return source.replace(old,new,1)


_cached_router = None
_cached_packers = {}


def pack_td(packer, source, configs, inactive):
    global _cached_router, _cached_packers
    if _cached_router is not packer:
        _cached_packers = {c.name:NumpyControllerPacker(c) for c in packer.controllers}
        _cached_router=packer
    rgb=source.numpyArray()
    return {c['name']:_cached_packers[c['name']].pack(rgb,inactive) for c in configs}
