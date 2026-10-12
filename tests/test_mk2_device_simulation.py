"""Replay a fake HID endpoint through the actual Surface worker thread.

These are executable device-contract scenarios, not evidence that an unmeasured
physical button address or the LCD's visible appearance is correct.
"""
from collections import deque
from copy import deepcopy
from io import BytesIO
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.maschine_mk2 import Surface, render
from pixelblaze_mapper.mk2_workflow import Controller


def control(*, buttons=None, wheel=0, knobs=None):
    packet = bytearray(65)
    packet[0], packet[7], packet[8] = 1, 1, wheel
    for offset, mask in (buttons or {}).items():
        packet[offset] = mask
    for i, value in enumerate(knobs or [500]*8):
        packet[9+2*i:11+2*i] = value.to_bytes(2, 'little')
    return bytes(packet)


def pressure(pad_one=0):
    packet = bytearray(65); packet[0] = 0x20
    # Captured MK2 pressure reports contain two sets of 16 channel/value pairs.
    for start in (1,33):
        for channel in range(16):
            value = pad_one if channel == 12 else 0
            packet[start+channel*2] = value & 255
            packet[start+channel*2+1] = channel*16 | (value >> 8)
    return bytes(packet)


def state(version=1):
    controller = Controller()
    parameters = [dict(id='td'+str(i),label=label,value=.5,min=0,max=1,section='td')
                  for i,label in enumerate(('Master Speed','Scale','Width','Focus X',
                                            'Focus Y','Frame Zoom','Intensity','Contrast'))]
    material = dict(id='fixture', label='Fixture material', category='Test',
                    image=None, parameters=parameters)
    controller.set_context(dict(mode='material', active_material=material,
        catalog=[material], show=dict(material=material,parameters=parameters,
        duration=10.,elapsed=2.,transition='crossfade',transition_duration=1.,
        transition_progress=.5,playing=True)))
    view = controller.snapshot()
    return dict(version=version,controller=view,cards=view['cards'],selected=0,images={})


class Replay:
    """Deterministic connection/frame script; no sleeps, real USB or TD runtime."""
    def __init__(self, sessions, on_event=None):
        self.sessions = sessions
        self.session_index = 0
        self.now = 0.
        self.done = False
        self.ticks = 0
        self.events, self.pads, self.operations, self.statuses = [], [], [], []
        self.devices = []
        self.on_event = on_event
        self.surface = Surface(self.pad_event, self.control_event)
        self.surface.halt = self
        self.surface.snapshot = deepcopy(sessions[0]['frames'][0].get('snapshot', state()))
        self.hid = SimpleNamespace(enumerate=self.enumerate, device=self.device)

    def is_set(self):
        return self.done

    def set(self):
        self.done = True

    def wait(self, delay):
        self.now += max(delay, .2)
        self.ticks += 1
        if self.ticks > 256:
            self.done = True
            raise RuntimeError('Replay exceeded bounded frame budget')
        if delay == 1:
            self.statuses.append(self.surface.status)
            if self.session_index >= len(self.sessions):
                self.done = True
            return
        if self.devices:
            device = self.devices[-1]
            if device.frame_index+1 < len(device.frames):
                device.set_frame(device.frame_index+1)
            else:
                self.done = True

    def enumerate(self, vid, pid):
        self.operations.append(('enumerate',threading.get_ident(),vid,pid))
        if self.session_index >= len(self.sessions):
            return []
        if self.sessions[self.session_index].get('missing'):
            self.session_index += 1
            return []
        return [dict(interface_number=2,path=b'fixture'),dict(interface_number=0,path=b'wrong-interface')]

    def device(self):
        spec = self.sessions[self.session_index]
        device = FakeDevice(self, spec)
        self.devices.append(device)
        return device

    def control_event(self, event, version):
        self.operations.append(('event',threading.get_ident(),event['type'],version))
        self.events.append((deepcopy(event),version))
        if self.on_event:
            self.on_event(event,version,self)

    def pad_event(self, index, version):
        self.pads.append((index,version))

    def run(self):
        with patch.dict('sys.modules', {'hid':self.hid}), \
             patch('pixelblaze_mapper.maschine_mk2.dependencies'), \
             patch('pixelblaze_mapper.maschine_mk2.time.monotonic', side_effect=lambda:self.now):
            self.surface.start()
            self.surface.thread.join(timeout=5)
            if self.surface.thread.is_alive():
                self.done = True
                self.surface.thread.join(timeout=2)
                raise AssertionError('Fake HID worker did not finish')
        return self


class FakeDevice:
    def __init__(self, replay, spec):
        self.replay, self.spec, self.frames = replay, spec, spec['frames']
        self.writes = []
        self.closed = False
        self.set_frame(0)

    def set_frame(self, index):
        self.frame_index = index
        frame = self.frames[index]
        self.reports = deque(frame.get('reports', []))
        if 'snapshot' in frame:
            self.replay.surface.snapshot = deepcopy(frame['snapshot'])

    def open_path(self, path):
        self.replay.operations.append(('open',threading.get_ident(),path))

    def set_nonblocking(self, value):
        self.replay.operations.append(('nonblocking',threading.get_ident(),value))

    def read(self, size):
        self.replay.operations.append(('read',threading.get_ident(),size))
        value = self.reports.popleft() if self.reports else []
        if isinstance(value, Exception):
            raise value
        return value

    def write(self, packet):
        self.replay.operations.append(('write',threading.get_ident(),len(packet)))
        self.writes.append(bytes(packet))
        if len(self.writes) == self.spec.get('fail_write'):
            return len(packet)-1
        return len(packet)

    def close(self):
        self.closed = True
        self.replay.operations.append(('close',threading.get_ident()))
        self.replay.session_index += 1
        if self.spec.get('close_error'):
            raise OSError('fixture close failed after unplug')


class DeviceSimulationTests(unittest.TestCase):
    def test_close_failure_after_unplug_does_not_kill_worker_or_skip_retry(self):
        escaped = []
        with patch('threading.excepthook',side_effect=lambda args:escaped.append(args.exc_value)):
            simulation = Replay([
                dict(frames=[dict(reports=[control()]),dict(reports=[OSError('unplug')])],close_error=True),
                dict(frames=[dict(reports=[control()])]),
            ]).run()
        self.assertEqual(escaped,[])
        self.assertEqual(len(simulation.devices),2)
        self.assertTrue(any('close failed' in status for status in simulation.statuses))
        self.assertEqual(sum(p[0] in (0xe0,0xe1) for p in simulation.devices[1].writes),16)

    def test_missing_device_does_not_flood_connection_reset_events(self):
        simulation = Replay([
            dict(missing=True,frames=[{}]),dict(missing=True,frames=[{}]),
            dict(frames=[dict(reports=[control()])]),
        ]).run()
        self.assertEqual(simulation.events,[(dict(type='connection_reset'),1)])
        self.assertEqual(sum('nicht gefunden' in status for status in simulation.statuses),2)
        self.assertEqual(len(simulation.devices),1)

    def test_worker_thread_input_to_versioned_events_and_complete_lcd_led_output(self):
        simulation = Replay([dict(frames=[
            dict(reports=[control()]+[pressure()]*3),
            dict(reports=[control(buttons={2:4}),control(buttons={2:4})]+[pressure(300)]*2),
            dict(reports=[control(),control(buttons={2:2},wheel=1)],snapshot=state(9)),
        ])]).run()
        self.assertEqual(simulation.events, [
            (dict(type='connection_reset'),1),
            (dict(type='button',name='browse',down=True),1),
            (dict(type='button',name='browse',down=False),9),
            (dict(type='button',name='step',down=True),9),
            (dict(type='wheel',delta=1),9)])
        self.assertEqual(simulation.pads, [(0,1)])
        self.assertTrue(all(op[1] == simulation.surface.thread.ident for op in simulation.operations))
        self.assertNotEqual(simulation.surface.thread.ident,threading.get_ident())
        writes = simulation.devices[0].writes
        for report_id in (0xe0,0xe1):
            bands = [p for p in writes if p[0] == report_id]
            self.assertEqual([p[3] for p in bands],list(range(0,64,8)))
            self.assertTrue(all(len(p)==265 for p in bands))
            self.assertEqual(len(b''.join(p[9:] for p in bands)),2048)
        self.assertTrue(any(p[0]==0x80 and len(p)==49 for p in writes))
        self.assertTrue(any(p[0]==0x81 and len(p)==57 for p in writes))
        self.assertTrue(any(p[0]==0x82 and len(p)==32 for p in writes))
        self.assertTrue(simulation.devices[0].closed)

    def test_disconnect_reconnect_held_keys_pads_and_absolute_positions_are_baselines(self):
        held = control(buttons={2:4},wheel=13,knobs=[950]*8)
        released = control(wheel=13,knobs=[950]*8)
        simulation = Replay([
            dict(frames=[dict(reports=[control()]+[pressure()]*3),
                         dict(reports=[OSError('fixture disconnected')])]),
            dict(frames=[dict(reports=[held]*3+[pressure(300)]*4,snapshot=state(7)),
                         dict(reports=[released]+[pressure()]*3),
                         dict(reports=[control(buttons={2:4},wheel=14,knobs=[965]+[950]*7)]+[pressure(300)]*2)]),
        ]).run()
        self.assertEqual(simulation.events, [
            (dict(type='connection_reset'),1),
            (dict(type='connection_reset'),1),
            (dict(type='connection_reset'),7),
            (dict(type='button',name='browse',down=False),7),
            (dict(type='button',name='browse',down=True),7),
            (dict(type='wheel',delta=1),7),
            (dict(type='encoder',index=0,delta=1),7)])
        self.assertEqual(simulation.pads,[(0,7)])
        self.assertTrue(all(d.closed for d in simulation.devices))
        self.assertTrue(any('disconnected' in status for status in simulation.statuses))
        self.assertEqual([op[0] for op in simulation.operations if op[0] in ('open','close')],
                         ['open','close','open','close'])
        # Loss notification reaches the callback before close/backoff/reopen,
        # so a physically absent device cannot leave REC latched indefinitely.
        first_close = next(i for i,op in enumerate(simulation.operations) if op[0]=='close')
        self.assertEqual(simulation.operations[first_close-1][0:3:2],('event','connection_reset'))
        self.assertEqual(sum(p[0] in (0xe0,0xe1) for p in simulation.devices[1].writes),16)

    def test_short_write_reports_failure_closes_handle_and_retries_complete_frame(self):
        simulation = Replay([
            dict(frames=[dict(reports=[control()])],fail_write=3),
            dict(frames=[dict(reports=[control()])]),
        ]).run()
        self.assertTrue(any('Unvollständige USB-Übertragung' in status for status in simulation.statuses))
        self.assertEqual(len(simulation.devices[0].writes),3)
        self.assertEqual(sum(p[0] in (0xe0,0xe1) for p in simulation.devices[1].writes),16)
        self.assertTrue(all(device.closed for device in simulation.devices))
        self.assertEqual(simulation.surface.writes,21)  # first2 successful + fresh16LCD/3LED

    def test_browse_via_raw_button_runs_real_controller_and_changes_hardware_frame(self):
        controller = Controller()
        material = dict(id='chosen',label='Chosen fixture',parameters=[])
        controller.set_context(dict(mode='material',active_material=material,catalog=[material]))
        initial = state(); initial['controller'] = controller.snapshot()
        def event_handler(event,version,replay):
            controller.dispatch(event)
            updated = deepcopy(replay.surface.snapshot)
            updated['controller'] = controller.snapshot()
            replay.surface.snapshot = updated
        simulation = Replay([dict(frames=[dict(reports=[control()],snapshot=initial),
            dict(reports=[control(buttons={2:4})]),dict(reports=[control()])])],event_handler).run()
        self.assertEqual(controller.screen,'browse')
        self.assertGreater(simulation.surface.frame_version,1)
        from PIL import Image
        frame = Image.open(BytesIO(simulation.surface.frames[0]))
        self.assertEqual(frame.tobytes(),render(simulation.surface.snapshot)[0].tobytes())

    def test_snapshot_version_is_read_per_batch_and_never_relabels_queued_events(self):
        # Caller owns stale-version rejection. Worker must retain the version
        # belonging to the snapshot it read, even when the callback replaces it.
        def replace_snapshot(event,version,replay):
            if event['type'] != 'connection_reset':
                replay.surface.snapshot = state(88)
        simulation = Replay([dict(frames=[dict(reports=[control()]),
            dict(reports=[control(buttons={2:4}),control()]),
            dict(reports=[control(buttons={2:2})])])],replace_snapshot).run()
        self.assertEqual([version for event,version in simulation.events if event['type'] != 'connection_reset'],[1,1,88])

    def test_reconnect_marker_clears_pending_rec_before_held_baseline_release(self):
        controller = Controller()
        controller.set_context(dict(mode='show'))
        commands = []
        def workflow_event(event,version,replay):
            if event['type'] == 'connection_reset':
                # The runtime adapter owns resetting transient input state;
                # model that boundary without accessing the real TD Manager.
                controller.held.clear()
                controller.rec_pending = controller.rec_chord = False
            else:
                commands.extend(controller.dispatch(event))
        held = control(buttons={5:0x20})
        simulation = Replay([
            dict(frames=[dict(reports=[control()]),dict(reports=[held]),
                         dict(reports=[OSError('USB removed with REC held')])]),
            dict(frames=[dict(reports=[held]),dict(reports=[control()])]),
        ],workflow_event).run()
        self.assertEqual([event['type'] for event,_ in simulation.events],
                         ['connection_reset','button','connection_reset','connection_reset','button'])
        self.assertEqual(commands,[])
        self.assertFalse(controller.rec_pending)
        self.assertFalse(controller.held)


class RenderBoundarySimulationTests(unittest.TestCase):
    def test_all_views_accept_finite_zero_and_large_ranges_and_missing_images(self):
        from PIL import Image
        screens = ('home','browse','pad_grid','pad_menu','pad_edit',
                   'confirm_assign','confirm_delete','confirm_edit')
        for mode in ('material','show'):
            for screen in screens:
                for duration in (0.,.01,1e12):
                    with self.subTest(mode=mode,screen=screen,duration=duration):
                        s=state(); c=s['controller']
                        c.update(mode=mode,screen=screen,parameter_overflow=17)
                        c['material']['label']='Sehr langer Name ÄÖÜ '+('素材'*40)
                        c['show'].update(duration=duration,elapsed=duration/2,progress=.5,
                                         transition_in=0.,transition_out=duration,
                                         transition_duration=duration,transition_progress=.5)
                        c['parameter_pages'][0]['parameters'][0].update(min=2.,max=2.,value=2.)
                        c['parameter_pages'][0]['parameters'][1].update(min=-1e12,max=1e12,value=1e12)
                        c['confirm']=dict(label='Target',options=['Confirm','Cancel'],choice=0) if screen.startswith('confirm_') else None
                        s['images']['missing']='Z:/a-file-that-does-not-exist.png'
                        c['material']['image']='missing'
                        frames=render(s)
                        self.assertEqual([(f.size,f.mode) for f in frames],[((256,64),'1')]*2)
                        for frame in frames:
                            data=BytesIO();frame.save(data,format='PNG')
                            self.assertEqual(Image.open(BytesIO(data.getvalue())).tobytes(),frame.tobytes())

    def test_empty_catalog_empty_parameter_list_and_unavailable_pad_views(self):
        c=Controller(); c.set_context(dict(mode='material',active_material={},catalog=[]))
        for screen in ('home','browse','pad_grid','pad_menu','pad_edit'):
            c.screen=screen
            s=state();s['controller']=c.snapshot()
            with self.subTest(screen=screen):
                self.assertEqual([len(f.tobytes()) for f in render(s)],[2048,2048])


if __name__=='__main__':
    unittest.main()
