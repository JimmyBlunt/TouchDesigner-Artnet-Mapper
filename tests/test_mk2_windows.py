"""Desktop routing acceptance without real windows, USB or material activation."""
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest.mock import Mock
import unittest

from pixelblaze_mapper.mk2_windows import WindowDirector, monitor_pair, browser_rect, ROOT, MATERIAL, SHOW_CONTROL, SHOW_PREVIEW
from tests import test_mk2_runtime as runtime_fixture


def monitor(index, primary=False, name='', description='', left=0, top=1199, width=1920, height=1200):
    return NS(index=index, isPrimary=primary, displayName=name, description=description,
              left=left, top=top, width=width, height=height)


class Parameter:
    def __init__(self, owner, name):
        self.owner, self.name, self.val, self.pulses = owner, name, None, 0
    def eval(self):
        return self.val
    def pulse(self):
        self.pulses += 1
        if self.name == 'winopen': self.owner.isOpen = True
        if self.name == 'winclose': self.owner.isOpen = False


class Parameters:
    def __init__(self, owner): self.owner, self.values = owner, {}
    def __getattr__(self, key):
        return self.values.setdefault(key, Parameter(self.owner, key))


class Node:
    def __init__(self, path, nodes):
        self.path, self.nodes, self.width, self.height = path, nodes, 1180, 720
        self.par, self.isOpen = Parameters(self), False
        nodes[path] = self
    def op(self, name): return self.nodes.get(self.path+'/'+name)
    def create(self, kind, name): return Node(self.path+'/'+name, self.nodes)


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.monitors = [monitor(0, name='laptop', left=-1920, top=1913, height=1280),
                         monitor(1, True, 'external', 'HP Z24i')]
        self.nodes = {}
        for path in ('/project1', MATERIAL, SHOW_CONTROL, SHOW_PREVIEW, ROOT+'/preview_panel'):
            Node(path, self.nodes)
        self.sequencer = NS(show=Mock(), hide=Mock(), error='', status='idle')
        self.preview = NS(select=Mock(return_value=ROOT+'/preview_panel'))
        self.now = 0
        td = NS(project=NS(folder=self.temp.name), monitors=self.monitors, baseCOMP='base', windowCOMP='window')
        self.director = WindowDirector(self.nodes.get, td, sequencer=self.sequencer,
                                       preview=self.preview, clock=lambda:self.now)

    def view(self, identifier='a', screen='browse', mode='material'):
        return dict(mode=mode, screen=screen, browse_items=[dict(id=identifier, label=identifier, image=identifier)], browse_index=0)

    def test_explicit_external_hp_even_when_windows_primary(self):
        external, laptop = monitor_pair(self.monitors, {})
        self.assertEqual((external.index, laptop.index), (1, 0))
        self.assertEqual(browser_rect(external, self.monitors), dict(x=0, y=0, width=1920, height=1152))
        self.assertEqual(browser_rect(laptop, self.monitors)['y'], -714)

    def test_saved_names_follow_changed_indexes_and_single_monitor_falls_back(self):
        pair = monitor_pair(self.monitors, dict(sequencer_monitor='laptop', workspace_monitor='external'))
        self.assertEqual([m.index for m in pair], [0, 1])
        self.assertEqual(monitor_pair(self.monitors[:1], {}), (self.monitors[0], self.monitors[0]))
        with self.assertRaises(RuntimeError): monitor_pair([], {})

    def test_mode_switch_reuses_owned_windows_on_correct_screens(self):
        d=self.director
        d.show_mode('material')
        material=self.nodes[ROOT+'/material']
        self.assertTrue(material.isOpen)
        self.assertEqual(material.par.display.eval(), 0)
        d.show_mode('show')
        show=self.nodes[ROOT+'/show']
        self.assertFalse(material.isOpen)
        self.assertEqual(show.par.winop.eval(), SHOW_CONTROL)
        self.assertEqual(show.par.display.eval(), 0)
        self.sequencer.show.assert_called_with(dict(x=0,y=0,width=1920,height=1152))
        d.show_mode('material')
        self.assertFalse(show.isOpen)
        self.assertIs(self.nodes[ROOT+'/material'], material)
        self.assertEqual(len([p for p in self.nodes if p in (ROOT+'/material', ROOT+'/show')]), 2)

    def test_raw_show_view_is_an_explicit_option(self):
        self.director.config['show_view']='preview'
        self.director.show_mode('show')
        self.assertEqual(self.nodes[ROOT+'/show'].par.winop.eval(), SHOW_PREVIEW)

    def test_missing_target_reports_failure_without_unrelated_windows(self):
        del self.nodes[MATERIAL]
        with self.assertRaisesRegex(RuntimeError, 'Fensterinhalt fehlt'):
            self.director.show_mode('material')
        self.assertNotIn('/perform', self.nodes)

    def test_browse_opens_selected_preview_but_debounces_fast_selection(self):
        d=self.director
        d.config['desktop_browse_preview']=True
        d.observe(self.view(screen='home'), {})
        self.assertFalse(self.preview.select.called)
        d.observe(self.view('a'), {'a':'a.png'})
        self.preview.select.assert_called_once_with('a', dict(id='a',label='a',image='a',preview_path='a.png'))
        self.assertEqual(self.nodes[ROOT+'/material'].par.winop.eval(), ROOT+'/preview_panel')
        for i in range(8):
            self.now += .05
            d.observe(self.view('m%d'%i), {})
        self.assertEqual(self.preview.select.call_count, 1)
        self.now += .31
        d.observe(self.view('m7'), {})
        self.assertEqual(self.preview.select.call_count, 2)
        self.assertEqual(self.preview.select.call_args.args[0], 'm7')

    def test_loading_opens_player_until_browse_selection_changes(self):
        d=self.director
        d.config['desktop_browse_preview']=True
        d.observe(self.view(), {})
        d.material_loaded('a')
        self.assertEqual(self.nodes[ROOT+'/material'].par.winop.eval(), MATERIAL)
        self.now += 1
        d.observe(self.view(), {})
        self.assertEqual(self.preview.select.call_count, 1)
        d.observe(self.view('b'), {})
        self.now += .31
        d.observe(self.view('b'), {})
        self.assertEqual(self.preview.select.call_count, 2)

    def test_browse_exit_restores_player_and_show_prevents_preview(self):
        d=self.director
        d.config['desktop_browse_preview']=True
        d.observe(self.view(), {})
        d.observe(self.view(screen='home'), {})
        self.assertEqual(self.nodes[ROOT+'/material'].par.winop.eval(), MATERIAL)
        d.observe(self.view('b', mode='show'), {})
        self.assertEqual(self.preview.select.call_count, 1)

    def test_default_browse_never_loads_desktop_preview_or_opens_window(self):
        d=self.director
        # Entry, rapid turning, settled selection and exit all stay on MK2.
        for i in range(100):
            self.now += 1
            d.observe(self.view('m%d'%i), {})
        d.observe(self.view(screen='categories'), {})
        d.observe(self.view(screen='home'), {})
        self.preview.select.assert_not_called()
        self.assertNotIn(ROOT+'/material', self.nodes)
        self.assertIsNone(d.pending)

    def test_disabled_preview_closes_legacy_and_loaded_player_while_browsing(self):
        d=self.director
        d.config['desktop_browse_preview']=True
        d.observe(self.view(), {})
        window=self.nodes[ROOT+'/material']
        self.assertTrue(window.isOpen)
        d.config['desktop_browse_preview']=False
        d.observe(self.view('b'), {})
        self.assertFalse(window.isOpen)
        self.assertEqual(self.preview.select.call_count, 1)
        d.material_loaded('b')
        self.assertTrue(window.isOpen)
        d.observe(self.view('c'), {})
        self.assertFalse(window.isOpen)
        self.assertEqual(window.par.winop.eval(), MATERIAL)
        self.assertEqual(self.preview.select.call_count, 1)

    def test_default_browse_and_categories_close_only_owned_window_for_any_target(self):
        d = self.director
        user_window = Node('/project1/user_material_window', self.nodes)
        user_window.par.winop.val = MATERIAL
        user_window.par.winopen.pulse()
        for screen in ('browse', 'categories'):
            for target in (MATERIAL, ROOT+'/preview_panel', SHOW_PREVIEW):
                with self.subTest(screen=screen, target=target):
                    d.show_mode('material')
                    window = self.nodes[ROOT+'/material']
                    window.par.winop.val = target
                    # winopen is a pulse parameter, not the window's open state.
                    self.assertIsNone(window.par.winopen.eval())
                    closes = window.par.winclose.pulses
                    d.observe(self.view(screen=screen), {})
                    self.assertFalse(window.isOpen)
                    self.assertEqual(window.par.winclose.pulses, closes + 1)
                    d.observe(self.view(screen=screen), {})
                    self.assertEqual(window.par.winclose.pulses, closes + 1)
                    self.assertTrue(user_window.isOpen)
        self.preview.select.assert_not_called()

    def test_default_observation_preserves_player_on_home_edit_and_show_mode(self):
        d = self.director
        for mode, screen in (('material', 'home'), ('material', 'edit'),
                             ('show', 'browse'), ('show', 'categories')):
            with self.subTest(mode=mode, screen=screen):
                d.show_mode('material')
                window = self.nodes[ROOT+'/material']
                closes = window.par.winclose.pulses
                d.observe(self.view(mode=mode, screen=screen), {})
                self.assertTrue(window.isOpen)
                self.assertEqual(window.par.winclose.pulses, closes)

    def test_disabled_legacy_preview_cleanup_still_applies_outside_browse(self):
        d = self.director
        d.config['desktop_browse_preview'] = True
        d.observe(self.view(), {})
        window = self.nodes[ROOT+'/material']
        d.config['desktop_browse_preview'] = False
        d.observe(self.view(screen='home'), {})
        self.assertFalse(window.isOpen)


class RuntimeWindowTests(unittest.TestCase):
    setUp=runtime_fixture.RuntimeTests.setUp
    button=runtime_fixture.RuntimeTests.button

    def test_mode_load_and_browse_are_forwarded_after_successful_host_actions(self):
        m=self.manager; m.windows=Mock()
        self.button('step')
        m.windows.show_mode.assert_called_once_with('show')
        self.assertEqual(m.controller.mode, 'show')
        self.button('step'); self.button('browse')
        self.assertEqual(m.windows.observe.call_args.args[0]['screen'], 'browse')
        m.dispatch(dict(type='wheel_press'))
        m.windows.material_loaded.assert_called_once_with('m0')

    def test_window_failure_does_not_undo_successful_mode_change(self):
        m=self.manager; m.windows=Mock()
        m.windows.show_mode.side_effect=RuntimeError('Bildschirm fehlt')
        self.button('step')
        self.assertEqual(m.controller.mode, 'show')
        self.assertIn('Bildschirm fehlt', m.window_error)


if __name__=='__main__': unittest.main()
