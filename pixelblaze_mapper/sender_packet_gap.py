"""Optional per-controller UDP spacing for receivers with small packet queues."""
from math import isfinite


def seconds(settings, name):
    value = float(settings.get(name, 0.0))
    if not isfinite(value) or not 0 <= value <= 5:
        raise ValueError('Live packet gap must be 0..5 ms')
    return value / 1000.0


def install_source(source):
    marker = '# PER_CONTROLLER_PACKET_GAP_V1'
    if marker in source:
        return source
    old = "            for offset, payload in enumerate(frames):\n"
    new = ("            " + marker + "\n"
           "            from pixelblaze_mapper.sender_packet_gap import seconds\n"
           "            gap = seconds(me.parent().fetch('live_packet_gap_ms', {}), config['name'])\n"
           + old)
    send = "                _socket.sendto(_packet(config['universe'] + offset, payload), target)\n"
    spaced = "                if offset and gap:\n                    time.sleep(gap)\n" + send
    for before, after in ((old, new), (send, spaced)):
        if source.count(before) != 1:
            raise ValueError('Shared sender packet gap patch does not match expected source')
        source = source.replace(before, after, 1)
    return source
