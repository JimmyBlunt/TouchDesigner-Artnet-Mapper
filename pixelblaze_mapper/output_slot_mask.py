"""Explicit nonphysical output slots. Never changes array length or routing."""
from functools import lru_cache

CONTRACT = 'SPARSE_SOURCE_MASK_V1'
MASK_PATH = '/project1/layout_apply/active_source_mask'
_native_ranges_cache = {}


def _validated_table_ranges(table, count):
    # Manual TD tables increment totalCooks after a non-forced cook, even for
    # multiple cell edits in the same frame. Never use cookFrame alone: a
    # same-frame invalid mask must not reuse an earlier validated result.
    # Unknown objects/dynamic table inputs retain the text-validation path.
    if (getattr(table, 'type', None) != 'table' or getattr(table,'inputs',None)
            or not getattr(table,'allowCooking',False) or getattr(table,'lock',False)):
        return _table_ranges(table.text,count)
    table.cook(force=False)
    revision=(table.totalCooks,table.numRows,table.numCols,count)
    key=table.id
    cached=_native_ranges_cache.get(key)
    if cached is not None and cached[0] is table and cached[1] == revision:
        return cached[2]
    # Do not replace a successful cache entry until the new content validates.
    ranges=_table_ranges(table.text,count)
    if len(_native_ranges_cache)>=4:
        _native_ranges_cache.clear()
    _native_ranges_cache[key]=(table,revision,ranges)
    return ranges


@lru_cache(maxsize=4)
def _table_ranges(text, count):
    rows = [line.split('\t') for line in text.splitlines()]
    if not rows or rows[0] != ['index', 'enabled'] or len(rows) != count + 1:
        raise ValueError('Source mask header/length differs from active source')
    ranges = []
    for index, row in enumerate(rows[1:]):
        if row not in ([str(index), '0'], [str(index), '1']):
            raise ValueError('Source mask must contain ordered indices and strict 0/1 flags')
        if row[1] == '0':
            if ranges and ranges[-1][1] == index - 1:
                ranges[-1] = (ranges[-1][0], index)
            else:
                ranges.append((index, index))
    return tuple(ranges)


def ranges_for(op, count):
    """An applied layout mask supersedes historical reserved ranges completely."""
    if type(count) is not int or count < 0:
        raise ValueError('Source mask requires a non-negative integer source count')
    table = op(MASK_PATH)
    if table is not None:
        return _validated_table_ranges(table, count)
    owner = op('/project1/multi_controller_output')
    ranges = owner.fetch('inactive_source_ranges', []) if owner is not None else []
    if not isinstance(ranges, (list, tuple)):
        raise ValueError('Inactive source ranges must be an explicit list')
    for pair in ranges:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or any(type(i) is not int for i in pair) or not 0 <= pair[0] <= pair[1] < count):
            raise ValueError('Invalid inactive source range')
    return tuple(tuple(pair) for pair in ranges)


def signature(op, count):
    """Validate every read; changed or malformed DATs cannot reuse cached frames."""
    return count, tuple(ranges_for(op, count))


def _masked_sink(op, sink, source):
    """Accept a direct masked source or an intact owned demand gate only."""
    if sink is None or source is None:
        raise ValueError('Missing native sink or masked source')
    if list(sink.inputs) == [source]:
        return
    from .native_dmx_gate import MARKER, SHAPE_KEY, SELECT_SETTINGS, _check_settings, _settings
    parent = sink.parent()
    gate, idle = parent.op(sink.name + '_demand_gate'), parent.op(sink.name + '_idle_black')
    if (gate is None or idle is None or gate.type != 'select' or idle.type != 'constant'
            or list(sink.inputs) != [gate] or list(gate.inputs) or list(idle.inputs)
            or gate.comment != MARKER + sink.path or idle.comment != MARKER + sink.path):
        raise ValueError('Native sink bypasses its masked source: ' + sink.path)
    expected = '%r if op(%r).par.active.eval() else %r' % (source.path, sink.path, idle.path)
    if str(gate.par.chops.mode).upper().split('.')[-1] != 'EXPRESSION' or gate.par.chops.expr != expected:
        raise ValueError('Native gate selects an unreviewed source: ' + sink.path)
    shape = idle.fetch(SHAPE_KEY, None)
    if not isinstance(shape, dict) or set(shape) != {'count', 'rate'}:
        raise ValueError('Native idle mask shape is missing: ' + sink.path)
    _check_settings(gate, SELECT_SETTINGS)
    _check_settings(idle, _settings(shape['count'], shape['rate']))
    if idle.par.const0name.sequence.numBlocks != 1:
        raise ValueError('Native idle mask has extra channel blocks: ' + sink.path)


def _masked_callback(op, pack):
    if pack is None or pack.type != 'script':
        raise ValueError('Missing native mask packer')
    callback = op(str(pack.par.callbacks.eval()))
    if callback is None or CONTRACT not in callback.text:
        raise ValueError('Unmasked native packer: ' + pack.path)


def assert_sparse_contract(op):
    owner = op('/project1/multi_controller_output')
    sender = owner.op('artnet_510_sender_callbacks') if owner else None
    if sender is None or CONTRACT not in sender.text:
        raise ValueError('Sparse layout requires a mask-aware shared sender')
    if 'CALIBRATION_SOURCE_MASK_V1' not in sender.text:
        raise ValueError('Sparse layout requires mask-aware calibration cache invalidation')
    for node in owner.children:
        if node.type == 'script' and node.name.startswith('pack_'):
            _masked_callback(op, node)
        if node.type == 'dmxout':
            if not node.name.startswith('dmxout_'):
                raise ValueError('Unknown native sink in router: ' + node.path)
            pack = owner.op('pack_' + node.name[len('dmxout_'):])
            _masked_callback(op, pack)
            _masked_sink(op, node, pack)
    legacy = op('/project1/esp_artnet_out')
    if legacy is not None:
        pack = op('/project1/esp_artnet_live_pack')
        _masked_callback(op, pack)
        _masked_sink(op, legacy, pack)
    if op('/project1/dmxout1') is not None:
        mask = op('/project1/legacy_source_mask')
        shuffle = op('/project1/shuffle1')
        if mask is None or shuffle is None or list(shuffle.inputs) != [mask] or list(mask.inputs) != [op('/project1/merge2')]:
            raise ValueError('Legacy DMX source mask wiring is missing')
        callback = op(str(mask.par.callbacks.eval()))
        if callback is None or CONTRACT not in callback.text:
            raise ValueError('Legacy DMX mask callback is missing')
        expected = {'merge1': ('math2', 'select2'), 'math2': ('select1',),
                    'select1': ('rename2',), 'select2': ('rename2',),
                    'rename2': ('lookup1',), 'lookup1': ('Universe_Config', 'rename1'),
                    'rename1': ('shuffle1',)}
        for name, inputs in expected.items():
            node = op('/project1/' + name)
            if node is None or list(node.inputs) != [op('/project1/' + item) for item in inputs]:
                raise ValueError('Legacy DMX bypasses reviewed mask chain: ' + name)
        _masked_sink(op, op('/project1/dmxout1'), op('/project1/merge1'))
    return True
def channels(values, ranges):
    if not ranges:
        return values
    output = [list(getattr(channel, 'vals', channel)) for channel in values]
    if not output:
        raise ValueError('Expected source channels')
    count = len(output[0])
    if any(len(c) != count for c in output):
        raise ValueError('Channel lengths differ')
    for first, end in ranges:
        if type(first) is not int or type(end) is not int or not 0 <= first <= end < count:
            raise ValueError('Invalid inactive source range')
        for channel in output:
            channel[first:end+1] = [0.0] * (end-first+1)
    return output


def pixels(values, ranges):
    if not ranges:
        return values
    output = list(values)
    for first,end in ranges:
        if type(first) is not int or type(end) is not int or not 0 <= first <= end < len(output):
            raise ValueError('Invalid inactive source range')
        output[first:end+1] = [(0.,0.,0.)] * (end-first+1)
    return output


def install_source(source):
    marker = '# SPARSE_SOURCE_MASK_V1'
    live = "    frames = {config['name']: packer.controller(config['name']).pack_channels(\n              source[0], source[1], source[2]) for config in configs}"
    cal = "    _calibration_frames = build_router_plan(_router_config()).pack_pixels(pixels)"
    if marker not in source:
        if source.count(live) != 1 or source.count(cal) != 1:
            raise ValueError('Unreviewed sender source; mask not installed')
        source=source.replace(live,"    " + marker + "\n    from pixelblaze_mapper.output_slot_mask import channels, ranges_for\n    rgb = channels((source[0],source[1],source[2]), ranges_for(op, source.numSamples))\n    frames = {config['name']: packer.controller(config['name']).pack_channels(*rgb) for config in configs}")
        source=source.replace(cal,"    from pixelblaze_mapper.output_slot_mask import pixels as mask_pixels, ranges_for\n    pixels = mask_pixels(pixels, ranges_for(op, len(pixels)))\n"+cal)
    cache_marker = '# CALIBRATION_SOURCE_MASK_V1'
    if cache_marker in source:
        return source
    old = "    global _mode, _calibration, _calibration_frames\n"
    prepare = "    pixels = mask_pixels(pixels, ranges_for(op, len(pixels)))\n" + cal
    tick = "        live_frames = _live_frames(configs) if _mode == 'live' else None"
    changes = ((old, old.rstrip() + ', _calibration_mask_signature\n'),
               (prepare, "    from pixelblaze_mapper.output_slot_mask import signature\n"
                "    mask_signature = signature(op, len(pixels))\n"
                "    pixels = mask_pixels(pixels, mask_signature[1])\n" + cal +
                "\n    _calibration_mask_signature = mask_signature"),
               ('def tick():\n', cache_marker + "\n_calibration_mask_signature = None\n\n"
                "def _refresh_calibration_mask():\n"
                "    if _mode != 'calibration':\n        return\n"
                "    from pixelblaze_mapper.output_slot_mask import signature\n"
                "    source = op('source_select')\n"
                "    if source is None:\n        raise RuntimeError('Missing calibration source')\n"
                "    if signature(op, int(source.numSamples)) != _calibration_mask_signature:\n"
                "        set_calibration(*_calibration)\n\n"
                "def tick():\n"),
               (tick, "        _refresh_calibration_mask()\n" + tick))
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError('Unreviewed calibration cache source; mask not installed')
        source = source.replace(old, new, 1)
    return source


def install_native_source(source):
    if CONTRACT in source:
        return source
    old = '    frames = _controller_packer().pack_channels(source[0], source[1], source[2])'
    if source.count(old) != 1:
        raise ValueError('Unreviewed native pack callback')
    return source.replace('    scriptOp.clear()\n', '    scriptOp.clear()\n    _latest_frames = ()\n', 1).replace(old, '    # ' + CONTRACT + '\n'
        '    from pixelblaze_mapper.output_slot_mask import channels, ranges_for\n'
        '    rgb = channels((source[0], source[1], source[2]), ranges_for(op, source.numSamples))\n'
        '    frames = _controller_packer().pack_channels(*rgb)')


LEGACY_MASK_CALLBACK = '''# SPARSE_SOURCE_MASK_V1
# NUMPY_LEGACY_MASK_V1
def onCook(scriptOp):
    from pixelblaze_mapper.numpy_realtime import legacy_mask_cook
    legacy_mask_cook(scriptOp, op)
'''
