"""Permanent acceptance checks for the MK2 protocol and display contract.

Fixture addresses are protocol facts from Ardour's packed device report, not
derived from the implementation mapping (which would hide reversed-bit bugs).
No USB device or running TouchDesigner instance is needed.
"""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.maschine_mk2 import (
    ControlEdges, PadEdges, Surface, _thumbnail, button_lights,
    display_packets, pad_lights, render, transition_tile,
)


def report(wheel=0, knobs=None):
    data = bytearray(25)
    data[0], data[8] = 1, wheel
    for i, value in enumerate(knobs or [0]*8):
        data[9+2*i:11+2*i] = value.to_bytes(2, 'little')
    return data


def state():
    parameters = [dict(id=str(i), name='Parameter '+str(i), abbreviation='P'+str(i),
                       value=.25, min=0, max=1) for i in range(8)]
    cards = [dict(number=i+1, label='Material '+str(i+1), image=None,
                  available=i < 8, kind='material', target=str(i)) for i in range(16)]
    c = dict(mode='material', screen='home', material=dict(id='a', label='Active material'),
             parameter_pages=[dict(label='TD', parameters=parameters)], page=0,
             cards=cards, pad_index=0, bank=0, group_has_content=[True, True]+[False]*6,
             recording=False, show=dict(playing=True, elapsed=2., duration=10.,
                  transition='fade', transition_duration=2., transition_progress=.2,
                  progress=.2, focus='duration', editing=False))
    return dict(controller=c, cards=cards, selected=0, images={}, version=1)


class InputAcceptanceTests(unittest.TestCase):
    def test_worker_routes_events_and_refreshes_value_without_version_change(self):
        now = [0.]
        posts, events, writes = [], [], []
        def pressure(value):
            data = bytearray(65); data[0] = 0x20
            data[25], data[26] = value & 255, 0xc0 | (value >> 8)
            return data
        surface = Surface(lambda *args: posts.append(args), lambda *args: events.append(args))
        surface.snapshot = state()
        class Device:
            closed = False
            queue = [report(), pressure(0), pressure(0), pressure(0)]
            def open_path(self, path):
                self.path = path
            def set_nonblocking(self, value):
                pass
            def read(self, size):
                return self.queue.pop(0) if self.queue else []
            def write(self, packet):
                writes.append(bytes(packet))
                return len(packet)
            def close(self):
                self.closed = True
        device = Device()
        class Halt:
            done = False
            cycles = 0
            def is_set(self):
                return self.done
            def wait(self, delay):
                now[0] += delay
                if delay != .01:
                    return
                self.cycles += 1
                if self.cycles == 1:
                    now[0] += .2
                    step = report(); step[2] = 0x02
                    device.queue = [step, pressure(300), pressure(300)]
                    updated = deepcopy(surface.snapshot)
                    updated['controller']['parameter_pages'][0]['parameters'][0]['value'] = .9
                    surface.snapshot = updated
                else:
                    self.done = True
        surface.halt = Halt()
        fake_hid = SimpleNamespace(enumerate=lambda *_: [dict(interface_number=2,path=b'mk2')], device=lambda:device)
        with patch.dict('sys.modules', {'hid':fake_hid}), patch('pixelblaze_mapper.maschine_mk2.dependencies'), patch('pixelblaze_mapper.maschine_mk2.time.monotonic', side_effect=lambda:now[0]):
            surface.run()
        self.assertEqual(posts, [(0,1)])
        self.assertEqual(events, [(dict(type='connection_reset'),1),
                                 (dict(type='button',name='step',down=True),1)])
        self.assertEqual(surface.frame_version, 2)
        self.assertTrue(device.closed)
        self.assertEqual(sum(p[0] == 0xe0 for p in writes), 8)  # unchanged left LCD not resent
        self.assertGreater(sum(p[0] == 0xe1 for p in writes), 8)

    def test_reconnect_held_pad_requires_release_then_new_hit(self):
        decoder = PadEdges()
        def pressure(value):
            data = bytearray(65); data[0] = 0x20
            data[25], data[26] = value & 255, 0xc0 | (value >> 8)
            return data
        for _ in range(20):
            self.assertEqual(decoder.read(pressure(300)), [])
        for _ in range(3):
            self.assertEqual(decoder.read(pressure(0)), [])
        self.assertEqual(decoder.read(pressure(300)), [])
        self.assertEqual(decoder.read(pressure(300)), [0])

    def test_all_named_button_addresses_and_edges(self):
        fixtures = [(2, 0x02, 'step', None), (2, 0x04, 'browse', None),
                    (6, 0x01, 'scene', None), (5, 0x01, 'restart', None),
                    (5, 0x02, 'previous', None), (5, 0x04, 'next', None),
                    (5, 0x10, 'play', None), (5, 0x20, 'rec', None),
                    (5, 0x40, 'erase', None)]
        fixtures += [(1, 1 << i, 'top', i) for i in range(8)]
        fixtures += [(4, 1 << i, 'group', i) for i in range(8)]
        for offset, bit, name, index in fixtures:
            with self.subTest(name=name, index=index):
                decoder = ControlEdges()
                self.assertEqual(decoder.read(report()), [])
                pressed = report(); pressed[offset] = bit
                expected = dict(type='button', name=name, down=True)
                if index is not None:
                    expected['index'] = index
                self.assertEqual(decoder.read(pressed), [expected])
                self.assertEqual(decoder.read(pressed), [])
                self.assertEqual(decoder.read(report()), [dict(expected, down=False)])

    def test_wheel_press_and_modulo_16_movement(self):
        decoder = ControlEdges()
        self.assertEqual(decoder.read(report(wheel=15)), [])
        self.assertEqual(decoder.read(report(wheel=0)), [dict(type='wheel', delta=1)])
        self.assertEqual(decoder.read(report(wheel=15)), [dict(type='wheel', delta=-1)])
        pressed = report(wheel=15); pressed[3] = 0x80
        self.assertEqual(decoder.read(pressed), [dict(type='wheel_press')])
        self.assertEqual(decoder.read(report(wheel=15)), [])

    def test_eight_absolute_encoder_counters_with_wrap(self):
        decoder = ControlEdges(encoder_quantum=1, encoder_hysteresis=0)
        self.assertEqual(decoder.read(report(knobs=[999]*8)), [])
        self.assertEqual(decoder.read(report(knobs=[0]*8)),
                         [dict(type='encoder', index=i, delta=1) for i in range(8)])
        self.assertEqual(decoder.read(report(knobs=[998]*8)),
                         [dict(type='encoder', index=i, delta=-2) for i in range(8)])
        self.assertEqual(decoder.read(report(knobs=[998]*8)), [])

    def test_observed_stationary_mk2_trace_emits_no_parameter_changes(self):
        # Captured on real hardware while untouched, encoder4 report bytes15/16.
        # Quiet-time debounce alone fails: excursions also persist >1 second.
        trace = [715,710,715,710,715,710,715,710,715,710,715,710,
                 715,710,715,710,705,710,705,710,715,710,705,710,
                 705,710,705,710,705,710,705,710,705,710,705]
        decoder = ControlEdges()
        for value in trace:
            knobs = [265,78,754,value,944,930,103,318]
            self.assertEqual(decoder.read(report(knobs=knobs)), [])

    def test_slow_one_count_turn_accumulates_and_reversal_has_hysteresis(self):
        decoder = ControlEdges()
        decoder.read(report(knobs=[500]*8))
        events = []
        for value in range(501,546):
            knobs = [500]*8; knobs[2] = value
            events.extend(decoder.read(report(knobs=knobs)))
        self.assertEqual(events, [dict(type='encoder',index=2,delta=1)]*4)
        # Stopped just after a step: an idle five-count oscillation is suppressed.
        for value in [540,545,540,545]:
            knobs[2] = value
            self.assertEqual(decoder.read(report(knobs=knobs)), [])
        events = []
        for value in range(544,524,-1):
            knobs[2] = value
            events.extend(decoder.read(report(knobs=knobs)))
        self.assertEqual(events, [dict(type='encoder',index=2,delta=-1)])

    def test_quantized_rollover_both_directions_and_wheel_remains_one_step(self):
        decoder = ControlEdges()
        decoder.read(report(wheel=15, knobs=[995]*8))
        self.assertEqual(decoder.read(report(wheel=0,knobs=[10]+[995]*7)),
                         [dict(type='wheel',delta=1),dict(type='encoder',index=0,delta=1)])
        self.assertEqual(decoder.read(report(wheel=15,knobs=[990]+[995]*7)),
                         [dict(type='wheel',delta=-1),dict(type='encoder',index=0,delta=-1)])

    def test_initial_pressed_report_is_baseline_and_invalid_ignored(self):
        decoder = ControlEdges()
        first = report(knobs=[550]*8); first[5] = 0x20
        self.assertEqual(decoder.read(first), [])
        self.assertEqual(decoder.read(b'\x01\xff'), [])
        self.assertEqual(decoder.read(b'\x20'+bytes(64)), [])
        self.assertEqual(decoder.read(report(knobs=[550]*8)),
                         [dict(type='button', name='rec', down=False)])

    def test_rec_erase_chord_keeps_both_edges(self):
        decoder = ControlEdges(); decoder.read(report())
        pressed = report(); pressed[5] = 0x60
        self.assertEqual(decoder.read(pressed), [dict(type='button', name='rec', down=True),
                                                dict(type='button', name='erase', down=True)])

    def test_surface_retains_legacy_callback_and_accepts_event_callback(self):
        post, event = lambda *_: None, lambda *_: None
        self.assertIs(Surface(post).post, post)
        self.assertIs(Surface(post, event_callback=event).event_callback, event)


class LightAcceptanceTests(unittest.TestCase):
    def test_browser_filter_leds_replace_parameter_pages_and_mark_favorite(self):
        s=state();c=s['controller'];c.update(screen='browse',browse_filter='all',browse_index=0,
                                          browse_items=[dict(id='a',favorite=False)])
        c['parameter_pages']=[dict(label='MM',parameters=[]) for _ in range(8)]
        c['page']=3
        before=deepcopy(s)
        self.assertEqual(button_lights(s,now=0)[1][9:17],bytes([100,20,0,0,0,0,0,20]))
        self.assertEqual(s,before)
        c['browse_filter']='favorites';c['browse_items'][0]['favorite']=True
        self.assertEqual(button_lights(s,now=0)[1][9:17],bytes([20,100,0,0,0,0,0,100]))
        c['browse_items']=[]
        self.assertEqual(button_lights(s,now=0)[1][9:17],bytes([20,100,0,0,0,0,0,0]))

    def test_groups_duplicate_rgb_and_fixed_colour_top_brightness(self):
        groups, top = button_lights(state(), now=0)
        self.assertEqual(len(groups), 57); self.assertEqual(groups[0], 0x81)
        self.assertEqual(len(top), 32); self.assertEqual(top[0], 0x82)
        self.assertEqual(groups[1:7], bytes([85,75,0])*2)
        self.assertEqual(groups[7:13], bytes([0,15,30])*2)
        self.assertEqual(top[9], 100)
        self.assertEqual(top[10:17], bytes(7))
        self.assertEqual(top[2], 0)
        s = state(); s['controller']['mode'] = 'show'
        self.assertEqual(button_lights(s, now=0)[1][2], 100)

    def test_record_and_erase_blink_without_changing_snapshot(self):
        s = state(); s['controller']['recording'] = 'automation'
        original = deepcopy(s)
        on, _ = button_lights(s, now=0)
        off, _ = button_lights(s, now=.3)
        self.assertEqual(on[54:56], bytes([100,100]))
        self.assertEqual(off[54:56], bytes([0,0]))
        self.assertEqual(s, original)

    def test_pad_hit_is_red_then_returns_to_assignment_colour(self):
        s = state(); s['_pad_flash_until'] = {0:1}
        self.assertEqual(pad_lights(s, now=.5)[37:40], bytes([100,0,0]))
        self.assertEqual(pad_lights(s, now=1.1)[37:40], bytes([75,75,75]))

    def test_automated_parameters_use_first_eight_pads(self):
        s = state(); c = s['controller']; c['mode'] = 'show'
        c['parameter_pages'][0]['parameters'][1]['automated'] = True
        rgb = pad_lights(s, now=0)
        self.assertEqual(rgb[37:40], bytes([85,75,0]))  # pad 1 selected parameter
        self.assertEqual(rgb[40:43], bytes([0,20,35]))  # pad 2 has automation
        self.assertEqual(rgb[1:25], bytes(24))          # pads 9..16 off


class DisplayAcceptanceTests(unittest.TestCase):
    def captured_labels(self, s):
        from PIL import ImageDraw
        labels = []
        original = ImageDraw.ImageDraw.text
        def capture(instance, xy, text, *args, **kwargs):
            labels.append(str(text))
            return original(instance, xy, text, *args, **kwargs)
        with patch.object(ImageDraw.ImageDraw, 'text', capture):
            render(s)
        return labels

    def test_actual_active_name_not_selected_pad_and_menu_correct_target(self):
        s = state()
        labels = self.captured_labels(s)
        self.assertIn('Active material', labels)
        self.assertNotIn('Material 1', labels)
        s['controller']['screen'] = 'pad_menu'
        s['controller']['options'] = ['select', 'edit', 'browse', 'delete']
        labels = self.captured_labels(s)
        self.assertIn('Material 1', labels)
        self.assertNotIn('Active material', labels)

    def test_browser_favorite_action_and_selection_are_display_only(self):
        s=state();c=s['controller'];c.update(screen='browse',browse_filter='all',favorites_count=1,
            browse_index=0,browse_items=[dict(id='a',label='Favorite material',favorite=True),
                                        dict(id='b',label='Other material',favorite=False)])
        before=deepcopy(s)
        labels=self.captured_labels(s)
        self.assertIn('-FAV',labels)
        self.assertIn('001 * Favorite material',labels)
        self.assertEqual(s,before)
        first=render(s)
        c['browse_index']=1
        labels=self.captured_labels(s)
        self.assertIn('+FAV',labels)
        self.assertNotEqual(first[1].tobytes(),render(s)[1].tobytes())
        self.assertEqual(c['material']['label'],'Active material')

    def test_empty_favorites_and_assignment_context_are_explicit(self):
        s=state();c=s['controller'];c.update(screen='browse',browse_filter='favorites',favorites_count=0,
                                          browse_items=[],browse_index=12,browse_purpose='assign',bank=2,pad_index=8)
        labels=self.captured_labels(s)
        for expected in ('ALLE','FAV','+FAV','Favoriten 0','0/0','Noch keine Favoriten','PAD C09 ZUORDNEN'):
            self.assertIn(expected,labels)
        c['browse_items']=[dict(id='a',label='Assignable favorite',favorite=True)]
        c['favorites_count']=1
        self.assertIn('Druecken: zuordnen',self.captured_labels(s))

    def test_unsupported_parameter_overflow_and_paused_are_visible(self):
        s = state(); c = s['controller']
        c['parameter_pages'][0]['parameters'][0]['editable'] = False
        c['parameter_overflow'] = 8
        labels = self.captured_labels(s)
        self.assertIn('N/A', labels)
        self.assertTrue(any('+8' in label for label in labels))
        c['mode'] = 'show'; c['show'].update(playing=False, state='paused')
        labels = self.captured_labels(s)
        self.assertTrue(any('Paused' in label for label in labels))

    def test_top_page_boxes_follow_eight_physical_button_positions(self):
        s = state(); c = s['controller']
        c['parameter_pages'] = [dict(label='TD' if i == 0 else 'MM '+str(i), parameters=[]) for i in range(8)]
        c['page'] = 5
        frames = render(s)
        # One 64px region per button, four per LCD. Chosen top6 is LCD right2.
        for side in range(2):
            for slot in range(4):
                self.assertEqual(frames[side].getpixel((slot*64,0)), 1)
                self.assertEqual(frames[side].getpixel((slot*64+55,5)), 1 if side == 1 and slot == 1 else 0)

    def test_all_supported_transitions_have_distinct_icons_and_fill_progress(self):
        from pixelblaze_mapper.show_sequencer import TRANSITION_TYPES
        icons = [transition_tile(kind, 0).tobytes() for kind in TRANSITION_TYPES]
        self.assertEqual(len(set(icons)), len(TRANSITION_TYPES))
        for kind in TRANSITION_TYPES:
            with self.subTest(transition=kind):
                self.assertNotEqual(transition_tile(kind, .2).tobytes(), transition_tile(kind, .8).tobytes())

    def test_real_workflow_default_overview_then_pad_focus_then_top_overview(self):
        from pixelblaze_mapper.mk2_workflow import Controller
        s = state(); workflow = Controller()
        workflow.set_context(dict(mode='show', show=dict(s['controller']['show'],
            material=s['controller']['material'], parameters=s['controller']['parameter_pages'][0]['parameters'])))
        s['controller'] = workflow.snapshot()
        self.assertIsNone(s['controller']['focused_parameter'])
        overview = render(s)[1].tobytes()
        workflow.dispatch(dict(type='button', name='pad', index=3, down=True))
        s['controller'] = workflow.snapshot()
        self.assertIsNotNone(s['controller']['focused_parameter'])
        self.assertNotEqual(overview, render(s)[1].tobytes())
        workflow.dispatch(dict(type='button', name='top', index=0, down=True))
        s['controller'] = workflow.snapshot()
        self.assertIsNone(s['controller']['focused_parameter'])
        self.assertEqual(overview, render(s)[1].tobytes())

    def test_dynamic_parameter_changes_update_right_lcd(self):
        s = state(); original = deepcopy(s)
        before = render(s)
        self.assertEqual(s, original)
        s['controller']['parameter_pages'][0]['parameters'][0]['value'] = .95
        after = render(s)
        self.assertEqual(before[0].tobytes(), after[0].tobytes())
        self.assertNotEqual(before[1].tobytes(), after[1].tobytes())

    def test_each_workflow_screen_renders_and_selection_changes_frame(self):
        s = state(); c = s['controller']
        c['browse_items'] = [dict(id=str(i), label='Material '+str(i), category='Test') for i in range(20)]
        c['options'] = ['Select', 'Browse', 'Edit', 'Delete']
        c['confirm'] = dict(label='Assign material?', options=['Confirm', 'Cancel'], choice=0)
        for screen in ('home', 'browse', 'pad_grid', 'pad_menu', 'pad_edit', 'confirm_assign', 'confirm_delete', 'confirm_edit'):
            c['screen'] = screen
            with self.subTest(screen=screen):
                frames = render(s)
                self.assertEqual([(f.size, f.mode) for f in frames], [((256,64),'1')]*2)
                self.assertTrue(all(f.getbbox() for f in frames))
                for side, frame in enumerate(frames):
                    packets = list(display_packets(side, frame.tobytes()))
                    self.assertEqual(b''.join(p[9:] for p in packets), frame.tobytes())
        c['screen'] = 'browse'; c['browse_index'] = 0
        first = render(s)
        c['browse_index'] = 7
        self.assertNotEqual(first[0].tobytes(), render(s)[0].tobytes())

    def test_progress_transition_and_focused_parameter_update(self):
        s = state(); c = s['controller']; c['mode'] = 'show'
        before = render(s)
        c['show'].update(elapsed=8., progress=.8, transition_progress=.8)
        self.assertNotEqual(before[0].tobytes(), render(s)[0].tobytes())
        c['focused_parameter'] = 0
        self.assertNotEqual(before[1].tobytes(), render(s)[1].tobytes())

    def test_real_thumbnail_cached_across_dynamic_repaints(self):
        from PIL import Image
        _thumbnail.cache_clear()
        with TemporaryDirectory() as directory:
            path = Path(directory)/'preview.png'
            Image.new('L', (24,24), 255).save(path)
            s = state(); s['images']['a'] = str(path)
            with patch('PIL.Image.open', wraps=Image.open) as opened:
                render(s)
                s['controller']['parameter_pages'][0]['parameters'][0]['value'] = .7
                render(s)
                self.assertEqual(opened.call_count, 1)
        _thumbnail.cache_clear()


if __name__ == '__main__':
    unittest.main()
