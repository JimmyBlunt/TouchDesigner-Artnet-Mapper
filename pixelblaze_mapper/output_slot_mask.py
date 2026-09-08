"""Explicit nonphysical output slots. Never changes array length or routing."""
def channels(values, ranges):
    if not ranges:
        return values
    output = [[float(v) for v in getattr(channel, 'vals', channel)] for channel in values]
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
    marker = '# EXPLICIT_INACTIVE_OUTPUT_SLOTS'
    if marker in source:
        return source
    live = "    frames = {config['name']: packer.controller(config['name']).pack_channels(\n              source[0], source[1], source[2]) for config in configs}"
    cal = "    _calibration_frames = build_router_plan(_router_config()).pack_pixels(pixels)"
    if source.count(live) != 1 or source.count(cal) != 1:
        raise ValueError('Unreviewed sender source; mask not installed')
    source=source.replace(live,"    " + marker + "\n    from pixelblaze_mapper.output_slot_mask import channels\n    rgb = channels((source[0],source[1],source[2]), op('/project1/multi_controller_output').fetch('inactive_source_ranges', []))\n    frames = {config['name']: packer.controller(config['name']).pack_channels(*rgb) for config in configs}")
    return source.replace(cal,"    from pixelblaze_mapper.output_slot_mask import pixels as mask_pixels\n    pixels = mask_pixels(pixels, op('/project1/multi_controller_output').fetch('inactive_source_ranges', []))\n"+cal)
