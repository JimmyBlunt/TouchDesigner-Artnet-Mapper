import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pixelblaze_mapper import led_search as search, led_search_ui as ui


BASE = dict(name='panel6', target='10.0.0.253', interface='10.0.0.125',
            universe=142, count=1122, rate=30, order='RGB',
            frame_start_universe=120, frame_universe_count=33,
            ports=[{'universe':142, 'count':610}, {'universe':146, 'count':512}])
OUTPUTS = [dict(id=i, enabled=True, startUniverse=u, pixelCount=n)
           for i, (u,n) in enumerate(zip([120,122,127,133,139,142,146,150],
                                         [203,738,880,810,352,610,512,509]))]


class SearchUITests(unittest.TestCase):
    def test_open_refreshes_even_when_device_is_cached(self):
        panel = SimpleNamespace(op=lambda _: object(), openViewer=Mock())
        owner = SimpleNamespace(op=lambda _: panel,
                                fetch=lambda *_: {'outputs': OUTPUTS})
        with patch.object(ui, 'action', return_value=True) as load, patch.object(ui, 'render'):
            self.assertTrue(search.act(lambda path: panel if path.endswith('/led_search_panel') else owner, 'open'))
        load.assert_called_once()
        self.assertEqual(load.call_args.args[1], 'load')
        panel.openViewer.assert_called_once()

    def test_show_cannot_send_using_stale_outputs_when_reload_fails(self):
        panel = SimpleNamespace(op=lambda _: object())
        owner = SimpleNamespace(op=lambda _: panel)
        with patch.object(search, 'stop') as stop, \
                patch.object(ui, 'action', return_value=False) as load, \
                patch.object(search, 'frames') as frames:
            self.assertFalse(search.act(lambda path: panel if path.endswith('/led_search_panel') else owner, 'show'))
        stop.assert_called_once()
        load.assert_called_once()
        frames.assert_not_called()

    def test_selected_port_uses_hardware_address_and_keeps_acquisition_intact(self):
        for output, local, universe, slot in ((5,609,145,297), (6,448,148,324), (6,511,149,3)):
            with self.subTest(output=output, local=local):
                settings = ui.port_settings(BASE, OUTPUTS, output)
                packets = dict(search.frames(settings, local, .05, single=True))
                self.assertEqual(packets[universe][slot:slot+3], bytes((13,13,13)))
                self.assertEqual(sum(v != 0 for p in packets.values() for v in p), 3)
                self.assertEqual(list(packets), list(range(120,153)))
        self.assertEqual(BASE['count'], 1122)
        self.assertEqual(BASE['ports'][1]['universe'], 146)

    def test_missing_or_disabled_port_is_rejected(self):
        for output in (None, 8):
            with self.assertRaises(ValueError):
                ui.port_settings(BASE, OUTPUTS, output)
        with self.assertRaises(ValueError):
            ui.port_settings(BASE, [dict(p, enabled=False) for p in OUTPUTS], 6)

    def test_direct_editor_text_wins_over_old_dat_value(self):
        field = SimpleNamespace(panel=SimpleNamespace(field=SimpleNamespace(val='448')),
                                op=lambda _: SimpleNamespace(text='609\r\n'))
        self.assertEqual(ui.field_value(field), '448')

    def test_selecting_output_never_starts_light_or_changes_scan_state(self):
        values = {'standalone_capture':BASE, 'led_search_device':{'target':BASE['target'], 'outputs':OUTPUTS},
                  'led_search_output':5, 'session':{'session_id':'original'}, 'capture_plan':{'original':True}}
        fields = {'controller': SimpleNamespace(panel=SimpleNamespace(field=SimpleNamespace(val=BASE['target']))),
                  'index': SimpleNamespace(panel=SimpleNamespace(field=SimpleNamespace(val='609'))),
                  'index/string': SimpleNamespace(text='609')}
        panel = SimpleNamespace(op=lambda name: fields[name])
        owner = SimpleNamespace(fetch=lambda key, default=None: values.get(key,default),
                                store=lambda key,value: values.__setitem__(key,value),
                                op=lambda _: panel)
        with patch.object(search, 'stop'), patch.object(ui, 'render'), \
                patch.object(search, 'act') as send:
            self.assertTrue(ui.action(lambda _:owner, 'select', 6))
            send.assert_not_called()
        self.assertEqual(fields['index/string'].text, '0')
        self.assertEqual(values['session'], {'session_id':'original'})
        self.assertEqual(values['capture_plan'], {'original':True})
        self.assertEqual(values['standalone_capture'], BASE)

    def test_changed_ip_requires_fresh_output_list(self):
        panel = SimpleNamespace(op=lambda _: SimpleNamespace(panel=SimpleNamespace(
            field=SimpleNamespace(val='10.0.0.249'))))
        owner = SimpleNamespace(op=lambda _:panel, fetch=lambda *_:{'target':'10.0.0.253'})
        with self.assertRaisesRegex(ValueError, 'IP geaendert'):
            ui.selected_settings(lambda _:owner)


if __name__ == '__main__':
    unittest.main()
