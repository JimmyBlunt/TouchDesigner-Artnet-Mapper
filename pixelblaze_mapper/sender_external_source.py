"""Opt-in isolated packet pacing for one active controller in the shared sender."""
import socket


def rate_label(state):
    producer = state.get('telemetry', {}).get('actual_send_fps', 0.)
    transport = state.get('transport', {})
    if transport.get('kind') == 'external':
        if not transport.get('running', False):
            return 'UDP stopped (%s)' % (transport.get('stop_reason') or transport.get('error') or 'worker exited')
        return 'TD %.1f | UDP %.1f FPS | receiver unverified' % (
            producer, transport.get('actual_send_fps', 0.))
    return 'UDP %.1f FPS | receiver unverified' % producer


class ExternalSocket:
    def __init__(self, owner, config, settings):
        self.owner, self.config, self.settings = owner, config, settings
        self.worker = None
        self.pending = []
        self.queued_batches = 0
        self.local_drops = 0
        self.gap_ms = None
        self.frame_rate = None
        self.requested_rate = None

    def bind(self, endpoint):
        from .external_packet_sender import ExternalPacketSender
        from .sender_packet_gap import seconds
        self.gap_ms = seconds(self.owner.fetch('live_packet_gap_ms', {}), self.config['name'])*1000
        self.frame_rate = float(self.config['rate']) if self.settings.get('frame_pacing',False) else None
        self.requested_rate = self.frame_rate
        self.worker = ExternalPacketSender(
            self.settings['python'], endpoint[0], self.config['target'],
            target_port=self.config['port'], local_port=endpoint[1],
            gap_ms=self.gap_ms, frame_rate=self.frame_rate,
            priority=self.settings.get('worker_priority','normal'))

    def sendto(self, packet, target):
        self.pending.append((packet, target))

    def flush(self):
        from .sender_packet_gap import seconds
        if self.frame_rate is not None and self.requested_rate != self.frame_rate:
            raise RuntimeError('Frame rate changed; stop and restart output to apply it')
        if self.gap_ms != seconds(self.owner.fetch('live_packet_gap_ms', {}), self.config['name'])*1000:
            raise RuntimeError('Packet gap changed; stop and restart output to apply it')
        batch, self.pending = self.pending, []
        if self.worker.submit(batch):
            self.queued_batches += 1
        else:
            self.local_drops += 1

    def status(self):
        return dict(self.worker.status(), kind='external',
                    queued_batches=self.queued_batches, local_drops=self.local_drops)

    def close(self):
        self.pending.clear()
        if self.worker is not None:
            self.owner.store('last_external_sender_status', self.worker.close())


def make_socket(owner, configs, target_override=None, port_override=None):
    settings = owner.fetch('external_sender_settings', {})
    if not settings.get('enabled', False):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if len(configs) != 1:
        raise RuntimeError('External pacing currently supports exactly one enabled controller')
    config = dict(configs[0])
    config['target'] = target_override or config['target']
    config['port'] = port_override or config['port']
    return ExternalSocket(owner, config, settings)


def producer_configs(configs, transport):
    if not isinstance(transport,ExternalSocket) or transport.frame_rate is None:
        return configs
    if len(configs) != 1:
        # flush() is inside the sender's stop-on-error block. Invalidate there
        # instead of throwing outside tick's guarded transport section.
        transport.requested_rate=None
        return configs
    transport.requested_rate=float(configs[0]['rate'])
    return [dict(c,rate=min(120.,2*float(c['rate']))) for c in configs]


def install_frame_clock_source(source):
    setup=('    configs = _controllers(True)\n'
           '    if not configs:\n'
           "        _last_error = 'No controller row has Enabled=1'\n"
           '        stop()\n'
           '        return\n'
           '    now = time.monotonic()\n')
    old=setup+'    configs = _pacer.due(configs, now)\n'
    previous=setup+('    # EXTERNAL_FRAME_CLOCK_V1\n'
         '    from pixelblaze_mapper.sender_external_source import producer_configs\n'
         '    configs = _pacer.due(producer_configs(configs, _socket), now)\n')
    new=('    # EXTERNAL_FRAME_CLOCK_V2\n'
         '    try:\n'
         '        configs = _controllers(True)\n'
         '        if not configs:\n'
         "            raise RuntimeError('No controller row has Enabled=1')\n"
         '        now = time.monotonic()\n'
         '        from pixelblaze_mapper.sender_external_source import producer_configs\n'
         '        configs = _pacer.due(producer_configs(configs, _socket), now)\n'
         '    except Exception as error:\n'
         '        _last_error = str(error)\n'
         '        stop()\n'
         '        return\n')
    if '# EXTERNAL_FRAME_CLOCK_V2' in source:
        if source.count(new)!=1:raise ValueError('Changed external frame clock block')
        return source
    if '# EXTERNAL_FRAME_CLOCK_V1' in source:
        if source.count(previous)!=1:raise ValueError('Changed external frame clock block')
        return source.replace(previous,new,1)
    if source.count(old)!=1:raise ValueError('Expected reviewed controller pacing block')
    return source.replace(old,new,1)


def install_source(source):
    marker = '# EXTERNAL_PACKET_PROCESS_V1'
    if marker in source:
        return install_frame_clock_source(install_health_source(source))
    replacements = (
        ('_socket = None\n_enabled = False',
         marker+'\nfrom pixelblaze_mapper.sender_external_source import make_socket, ExternalSocket\n_socket = None\n_enabled = False'),
        ('        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n',
         '        _socket = make_socket(me.parent(), configs, target_override, port_override)\n'),
        ('                if offset and gap:\n',
         '                if offset and gap and not isinstance(_socket, ExternalSocket):\n'),
        ('        previous_send = _last_send\n',
         '        if isinstance(_socket, ExternalSocket):\n            _socket.flush()\n        previous_send = _last_send\n'),
        ("    return {'enabled': _enabled, 'error': _last_error, 'mode': _mode,\n",
         "    return {'transport': _socket.status() if isinstance(_socket, ExternalSocket) else {'kind': 'direct'},\n"
         "            'enabled': _enabled, 'error': _last_error, 'mode': _mode,\n"),
    )
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError('Shared sender external process patch does not match expected source')
        source = source.replace(before, after, 1)
    return install_frame_clock_source(install_health_source(source))


def install_health_source(source):
    marker = '# EXTERNAL_WORKER_HEALTH_V1'
    if marker in source:
        return source
    before = 'def status():\n'
    after = ('def status():\n    '+marker+'\n    global _last_error\n'
             '    if isinstance(_socket, ExternalSocket):\n'
             '        health = _socket.status()\n'
             "        if not health.get('running', False):\n"
             "            _last_error = 'Packet worker stopped: ' + str(health.get('stop_reason') or health.get('error'))\n"
             '            stop()\n')
    if source.count(before) != 1:
        raise ValueError('Sender health patch does not match expected source')
    return source.replace(before, after, 1)
