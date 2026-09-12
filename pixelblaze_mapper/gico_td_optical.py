"""Temporary optical fixture through the actual TD source, router and sender.

The test replaces the material source with a Script CHOP; it measures TD
source/packing/pacing/transport, not the cost of rendering an arbitrary effect.
One 30-FPS transport runs throughout; optical content changes at 15/25/30 FPS.
No controller firmware changes. All native changes are restored on finish.
"""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from . import gico_camera_benchmark as bench
from .routing_transaction import table_rows

SESSION = None
NAME = 'WS2812_NODE'
ROUTER = '/project1/multi_controller_output'
SOURCES = ((0, 517, 0), (517, 269, 1020), (786, 398, 2040))


def schedule(short=False):
    phases = [('all_on', 3., 20, [1]*21), ('black_reference', 1., 20, [0]*21)]
    phases += [('marker_%02d'%i, 1., 20, [int(j == i) for j in range(21)]) for i in range(21)]
    for fps in (15, 25, 30):
        phases += [('warmup_%d'%fps, 3., fps, None),
                   ('measure_%d'%fps, 60., fps, None), ('pause_%d'%fps, 2., 20, [0]*21)]
    if short:
        return [(n, .08 if n.startswith('marker_') else (.8 if n.startswith('measure_') else .2), f, b)
                for n, _, f, b in phases]
    return phases


def source_array(bits, count):
    if count < 1184 or len(bits) != 21 or any(x not in (0, 1) for x in bits):
        raise ValueError('Invalid optical source shape or bits')
    pixels = np.zeros((3, count), dtype=np.float32)
    for source, length, _ in SOURCES:
        for index, enabled in zip(bench.marker_indices(length), bits):
            pixels[:, source+index] = bench.LEVEL/255. if enabled else 0.
    return pixels


def cook(script_op):
    if SESSION is None:
        raise RuntimeError('Optical session is not installed')
    script_op.clear(); script_op.numSamples = SESSION.count
    for name, row in zip(('r', 'g', 'b'), SESSION.pixels):
        script_op.appendChan(name).copyNumpyArray(row)


class Session:
    def __init__(self, op, ui, folder, target, port, short):
        self.op, self.ui = op, ui
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=False)
        self.target, self.port, self.short = target, port, short
        if (target, port) not in (('10.0.0.244', 6454), ('127.0.0.1', 16455)):
            raise ValueError('Unreviewed optical test endpoint')
        from .guided_scan_live import assert_outputs_off
        assert_outputs_off(op)
        self.r = op(ROUTER); self.s = self.r.op('artnet_510_sender_callbacks').module
        if self.s.status()['mode'] != 'live': raise ValueError('Expected stopped live sender')
        source = self.r.op('source_select')
        if str(source.par.chops.mode) != 'ParMode.CONSTANT': raise ValueError('Source selector must be constant')
        self.count = int(op('/project1/math1').numSamples)
        self.baseline = {'controllers': table_rows(self.r.op('controller_config')),
            'source': str(source.par.chops.eval()), 'execute': self.r.op('artnet_510_execute').text,
            'gap': self.r.fetch('live_packet_gap_ms', {}),
            'external': self.r.fetch('external_sender_settings', {}), 'perform': ui.performMode,
            'segments_sha256': hashlib.sha256(self.r.op('segment_config').text.encode()).hexdigest(),
            'sender_sha256': hashlib.sha256(self.r.op('artnet_510_sender_callbacks').text.encode()).hexdigest(),
            'target_override': self.s._target_override, 'port_override': self.s._port_override}
        actual = [(int(row[1]), int(row[2]), int(row[4])) for row in table_rows(self.r.op('segment_config'))[1:]
                  if row[3] == NAME]
        if actual != list(SOURCES): raise ValueError('GICO source/destination routing differs from reviewed fixture')
        self.pixels = source_array([0]*21, self.count)
        self.created = []; self.running = False; self.finished = False
        self.phases = schedule(short); self.phase_index = -1; self.current = None
        self.log = []; self.report = {'schema': 1, 'plan': bench.plan(), 'phases': [],
            'baseline': self.baseline, 'td_native_router': True, 'target': target,
            'transport_fps': 30, 'test_source': 'temporary Script CHOP replacing material source',
            'short_loopback': short, 'complete': False}

    def install(self, script_type, text_type):
        for name in ('codex_gico_optical_source', 'codex_gico_optical_callbacks'):
            if self.r.op(name) is not None: raise ValueError('Temporary node already exists: '+name)
        cb = self.r.create(text_type, 'codex_gico_optical_callbacks'); self.created.append(cb)
        cb.text = 'def onCook(scriptOp):\n from pixelblaze_mapper import gico_td_optical as g\n g.cook(scriptOp)\n'
        self.source = self.r.create(script_type, 'codex_gico_optical_source'); self.created.append(self.source)
        self.source.par.callbacks = cb.path
        self.source.cook(force=True)
        self.r.op('source_select').par.chops = self.source.path
        t = self.r.op('controller_config')
        for row in range(1, t.numRows):
            selected = str(t[row, 'name']) == NAME
            t[row, 'enabled'] = '1' if selected else '0'
            if selected:
                t[row, 'rate'] = '30'; t[row, 'brightness'] = '1'
                t[row, 'local_interface'] = '127.0.0.1' if self.short else '10.0.0.125'
        self.r.store('live_packet_gap_ms', {NAME: 0.})
        settings = dict(self.baseline['external']); settings.update(enabled=True, frame_pacing=True, worker_priority='normal')
        self.r.store('external_sender_settings', settings)
        self.r.op('artnet_510_execute').text = (
            'def onFrameStart(frame):\n from pixelblaze_mapper import gico_td_optical as g\n g.tick()\n'
            'def onExit():\n from pixelblaze_mapper import gico_td_optical as g\n g.cancel()\n')
        patterns = [[0]*21, [1]*21, bench.encode(194), bench.encode(237)]
        patterns += [[int(i == j) for i in range(21)] for j in range(21)]
        for bits in patterns:
            self.pixels = source_array(bits, self.count); self.source.cook(force=True)
            frames = self.s._live_frames(self.s._controllers(True))[NAME]
            if tuple(frames) != tuple(bench.payloads(bits)):
                raise ValueError('Native packed bytes differ from reference; inspect masks/routing')
            for u, payload in enumerate(frames):
                if self.s._packet(u, payload) != bench.packet(u, payload):
                    raise ValueError('Native ArtDmx header differs from reference')
        self.pixels = source_array([0]*21, self.count); self.source.cook(force=True)
        self.report['preflight_patterns_passed'] = len(patterns)
        self.report['native_max_channel_value'] = bench.LEVEL
        return self.report

    def start(self):
        self.s.set_live()
        if not self.s.set_enabled(True, target_override=self.target, port_override=self.port):
            raise RuntimeError(self.s.status()['error'])
        self.ui.performMode = True
        self.clock = time.perf_counter(); self.report['started_unix_seconds'] = time.time()
        self.running = True

    def step(self):
        if not self.running: return
        now = time.perf_counter(); elapsed = now-self.clock
        edge = 0.; index = None
        for i, (_, seconds, _, _) in enumerate(self.phases):
            if elapsed < edge+seconds: index = i; break
            edge += seconds
        if index is None:
            self.finish(True); return
        if index != self.phase_index:
            if self.current: self.current['end'] = elapsed
            name, seconds, fps, _ = self.phases[index]
            self.current = {'name': name, 'start': elapsed, 'planned_start': edge,
                'duration_requested': seconds, 'fps': fps, 'submitted': 0, 'local_rejections': 0}
            self.report['phases'].append(self.current); self.phase_index = index
        name, seconds, fps, fixed = self.phases[index]
        frame_id = int((elapsed-edge)*fps) % bench.MODULUS if fixed is None else None
        bits = bench.encode(frame_id) if fixed is None else fixed
        self.pixels = source_array(bits, self.count); self.source.cook(force=True)
        before = self.s._send_count
        self.s.tick()
        if not self.s._enabled: raise RuntimeError('Native sender stopped: '+self.s._last_error)
        if self.s._send_count != before:
            self.current['submitted'] += 1
            self.log.append({'phase': name, 'time': elapsed, 'id': frame_id,
                'sequence': 0, 'accepted': True, 'meaning': 'native TD batch queued; worker may replace stale batches'})

    def finish(self, complete=False, error=None):
        global SESSION
        if self.finished: return
        self.running = False; self.finished = True
        if self.current: self.current['end'] = time.perf_counter()-self.clock
        if error: self.report['error'] = str(error)
        try:
            self.report['sender_final'] = self.s.status()
            self.s.stop()
            self.report['worker_final'] = self.r.fetch('last_external_sender_status') if hasattr(self, 'clock') else None
        finally:
            t = self.r.op('controller_config'); t.clear()
            for row in self.baseline['controllers']: t.appendRow(row)
            self.r.op('source_select').par.chops = self.baseline['source']
            self.r.op('artnet_510_execute').text = self.baseline['execute']
            self.r.store('live_packet_gap_ms', self.baseline['gap'])
            self.r.store('external_sender_settings', self.baseline['external'])
            self.ui.performMode = self.baseline['perform']
            self.s._target_override = self.baseline['target_override']; self.s._port_override = self.baseline['port_override']
            for node in reversed(self.created): node.destroy()
            self.report['restored'] = {
                'outputs_off': not self.s._enabled,
                'controllers': table_rows(t) == self.baseline['controllers'],
                'source': str(self.r.op('source_select').par.chops.eval()) == self.baseline['source'],
                'segments': hashlib.sha256(self.r.op('segment_config').text.encode()).hexdigest() == self.baseline['segments_sha256'],
                'sender_source': hashlib.sha256(self.r.op('artnet_510_sender_callbacks').text.encode()).hexdigest() == self.baseline['sender_sha256']}
            self.report['complete'] = complete and all(self.report['restored'].values())
            self.report['ended_unix_seconds'] = time.time()
            (self.folder/'run.json').write_text(json.dumps(self.report, indent=2), encoding='utf-8')
            (self.folder/'submitted-frames.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in self.log), encoding='utf-8')
            SESSION = None


def prepare(op, ui, script_type, text_type, folder, target='10.0.0.244', port=6454, short=False):
    global SESSION
    if SESSION is not None: raise ValueError('An optical session is already installed')
    SESSION = Session(op, ui, folder, target, port, short)
    try: return SESSION.install(script_type, text_type)
    except Exception as error:
        SESSION.finish(error=error); raise


def tick():
    if SESSION is None: return
    try: SESSION.step()
    except Exception as error: SESSION.finish(error=error)


def cancel():
    if SESSION is not None: SESSION.finish(error='Cancelled')
