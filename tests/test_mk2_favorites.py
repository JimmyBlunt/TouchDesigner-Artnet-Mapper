"""Favorites acceptance: real workflow and Manager, no USB or live TD required."""
from copy import deepcopy
import json
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper.mk2_workflow import Controller, validate_config
from pixelblaze_mapper.mk2_runtime import Manager
from tests.test_mk2_workflow import material
from tests.test_mk2_runtime import FakeHost, FakeSurface


def button(controller, name, index=0):
    result = controller.dispatch(dict(type='button', name=name, index=index, down=True))
    released = controller.dispatch(dict(type='button', name=name, index=index, down=False))
    return (result or []) + (released or [])


def press(controller):
    return controller.dispatch(dict(type='wheel_press'))


def wheel(controller, delta):
    return controller.dispatch(dict(type='wheel', delta=delta))


class FavoritesWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [material(i, 64 if i == 0 else 8) for i in range(3)]
        core = material(3)
        core.update(id='core:gradient', label='Core Gradient')
        self.catalog.append(core)
        self.c = Controller()
        self.c.set_context(dict(catalog=self.catalog, active_material=self.catalog[0]))

    def configure(self, favorites):
        config = self.c.export_config()
        config['favorites'] = favorites
        self.c.set_context(dict(config=config))

    def browse(self, favorites=False):
        button(self.c, 'browse')
        if favorites:
            button(self.c, 'top', 1)

    def ack(self, command, success=True):
        return self.c.dispatch(dict(type='command_result', request_id=command['request_id'],
                                    success=success, error='disk full'))

    def test_legacy_migration_starts_empty_preserves_presets_and_cue(self):
        pads = [dict(kind='material', target='m0', values={'p0': .25})] * 16
        pads[3] = dict(kind='cue', target='cue42')
        config = validate_config(dict(hardware=True, pads=pads))
        self.assertEqual(config['favorites'], [])
        self.assertTrue(config['hardware'])
        self.assertEqual(config['groups'][0]['pads'][0]['values'], {'p0': .25})
        self.assertEqual(config['groups'][0]['pads'][3]['target'], 'cue42')
        config.pop('favorites')
        self.assertEqual(validate_config(config)['favorites'], [])

    def test_favorite_ids_validate_deduplicate_and_preserve_core_and_missing_ids(self):
        config = self.c.export_config()
        config['favorites'] = ['m1', 'core:gradient', 'm1', 'missing']
        self.assertEqual(validate_config(config)['favorites'], ['m1', 'core:gradient', 'missing'])
        for invalid in (None, 'm1', [1], [''], ['x'*201]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_config(dict(config, favorites=invalid))

    def test_toggle_only_persists_after_matching_ack_and_never_loads(self):
        self.browse()
        wheel(self.c, 1)
        command, = button(self.c, 'top', 7)
        self.assertEqual(command['action'], 'persist_config')
        self.assertEqual(command['purpose'], 'favorites')
        self.assertEqual(command['config']['favorites'], ['m1'])
        self.assertEqual(self.c.export_config()['favorites'], [])
        self.assertTrue(self.c.snapshot()['saving'])
        self.c.dispatch(dict(type='command_result', request_id=999, success=True))
        self.assertEqual(self.c.export_config()['favorites'], [])
        self.assertEqual(press(self.c), [])
        self.ack(command)
        self.assertEqual(self.c.export_config()['favorites'], ['m1'])
        self.assertEqual(self.c.screen, 'browse')
        self.assertTrue(self.c.snapshot()['browse_items'][1]['favorite'])
        restored = Controller(json.loads(json.dumps(self.c.export_config())))
        self.assertEqual(restored.export_config(), self.c.export_config())

    def test_failed_save_retry_retains_selection_and_original_config(self):
        self.browse()
        wheel(self.c, 2)
        command, = button(self.c, 'top', 7)
        self.ack(command, False)
        self.assertFalse(self.c.snapshot()['saving'])
        self.assertIn('disk full', self.c.snapshot()['error'])
        self.assertEqual(self.c.export_config()['favorites'], [])
        self.assertEqual(self.c.browse_selected_id(), 'm2')
        retry, = button(self.c, 'top', 7)
        self.assertNotEqual(command['request_id'], retry['request_id'])
        self.ack(retry)
        self.assertEqual(self.c.export_config()['favorites'], ['m2'])

    def test_empty_favorites_and_removing_last_are_safe(self):
        self.browse(True)
        self.assertEqual(self.c.snapshot()['browse_items'], [])
        wheel(self.c, 127)
        self.assertEqual(self.c.browse_index, 0)
        self.assertEqual(press(self.c), [])
        self.assertEqual(button(self.c, 'top', 7), [])
        self.configure(['m2'])
        self.assertEqual(self.c.browse_selected_id(), 'm2')
        command, = button(self.c, 'top', 7)
        self.assertEqual(len(self.c.snapshot()['browse_items']), 1)
        self.ack(command)
        self.assertEqual(self.c.snapshot()['browse_items'], [])
        self.assertEqual(self.c.browse_index, 0)
        self.assertEqual(press(self.c), [])
        button(self.c, 'top', 0)
        self.assertEqual(len(self.c.snapshot()['browse_items']), 4)

    def test_catalog_reorder_rename_and_temporary_removal_keep_ids_stable(self):
        self.configure(['m1', 'm2', 'core:gradient', 'temporarily_missing'])
        self.browse(True)
        wheel(self.c, 1)
        self.assertEqual(self.c.browse_selected_id(), 'm2')
        reordered = deepcopy(self.catalog[::-1])
        next(x for x in reordered if x['id'] == 'm2')['label'] = 'Renamed'
        self.c.set_context(dict(catalog=reordered))
        self.assertEqual(self.c.browse_selected_id(), 'm2')
        self.assertEqual(self.c.snapshot()['browse_items'][self.c.browse_index]['label'], 'Renamed')
        self.c.set_context(dict(catalog=[self.catalog[1]]))
        self.assertEqual(self.c.browse_selected_id(), 'm1')
        self.assertIn('m2', self.c.export_config()['favorites'])
        self.c.set_context(dict(catalog=self.catalog))
        self.assertEqual([x['id'] for x in self.c.browse_catalog()], ['m1', 'm2', 'core:gradient'])

    def test_core_favorite_load_and_filters_retain_selected_id(self):
        self.configure(['m1', 'core:gradient'])
        self.browse()
        wheel(self.c, 3)
        button(self.c, 'top', 1)
        self.assertEqual(self.c.browse_index, 1)
        self.assertEqual(press(self.c), [dict(action='load_material', material_id='core:gradient', values={})])
        button(self.c, 'top', 0)
        self.assertEqual(self.c.browse_index, 3)

    def test_duplicate_down_and_pending_toggle_cannot_double_toggle(self):
        self.browse()
        event = dict(type='button', name='top', index=7, down=True)
        command, = self.c.dispatch(event)
        self.assertEqual(self.c.dispatch(event), [])
        self.ack(command)
        self.assertEqual(self.c.dispatch(event), [])
        self.c.dispatch(dict(event, down=False))
        command, = self.c.dispatch(event)
        self.assertEqual(command['config']['favorites'], [])
        self.c.dispatch(dict(event, down=False))
        self.assertEqual(button(self.c, 'top', 7), [])
        self.ack(command)
        self.assertEqual(self.c.export_config()['favorites'], [])

    def test_assignment_from_favorites_requires_confirm_and_preserves_other_presets(self):
        config = self.c.export_config()
        config['favorites'] = ['core:gradient']
        config['groups'][7]['pads'][15] = dict(kind='material', target='m2', values={'p0': .125})
        self.c.set_context(dict(config=config))
        button(self.c, 'scene')
        press(self.c)
        press(self.c)
        button(self.c, 'top', 1)
        self.assertEqual(press(self.c), [])
        self.assertEqual(self.c.snapshot()['confirm']['label'], 'Core Gradient')
        wheel(self.c, 1)
        self.assertEqual(press(self.c), [])  # Cancel has no side effect.
        self.assertEqual(self.c.export_config(), config)
        press(self.c)
        press(self.c)
        press(self.c)
        command, = press(self.c)
        self.assertEqual(self.c.export_config(), config)
        self.ack(command)
        saved = self.c.export_config()
        self.assertEqual(saved['groups'][0]['pads'][0]['target'], 'core:gradient')
        self.assertEqual(saved['groups'][7]['pads'][15], config['groups'][7]['pads'][15])
        self.assertEqual(saved['favorites'], ['core:gradient'])

    def test_top_keys_remain_parameter_pages_outside_browser_and_show_rejects_browse(self):
        for mode in ('material', 'show'):
            with self.subTest(mode=mode):
                self.c.set_context(dict(mode=mode, show=dict(parameters=self.catalog[0]['parameters'])))
                for index in (0, 1, 7):
                    self.assertEqual(button(self.c, 'top', index), [])
                    self.assertEqual(self.c.page, index)
                self.assertEqual(self.c.export_config()['favorites'], [])
        button(self.c, 'browse')
        self.assertEqual(self.c.screen, 'home')

    def test_top_buttons_do_not_toggle_favorites_in_pad_grid_or_preset_editor(self):
        config = self.c.export_config()
        config['favorites'] = ['m0']
        config['groups'][0]['pads'][0] = dict(kind='material', target='m0', values={'p0': .2})
        self.c.set_context(dict(config=config))
        button(self.c, 'scene')
        self.assertEqual(button(self.c, 'top', 7), [])
        self.assertEqual(self.c.screen, 'pad_grid')
        press(self.c)
        wheel(self.c, 1)
        press(self.c)
        self.assertEqual(self.c.screen, 'pad_edit')
        self.assertEqual(button(self.c, 'top', 7), [])
        self.assertEqual(self.c.page, 7)
        self.assertEqual(self.c.export_config(), config)
        self.assertFalse(self.c.snapshot()['saving'])


class HydrationHost(FakeHost):
    def __init__(self, owner):
        super().__init__(owner)
        self.requests = []
        self.materials['m2'] = material(2)
        self.materials['core:gradient'] = dict(material(3), id='core:gradient', label='Core Gradient')

    def context(self, target=None, *, metadata_only=False):
        self.requests.append(target)
        return super().context(target)


class FavoritesManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for mock in (patch.dict('sys.modules', td=SimpleNamespace(project=SimpleNamespace(folder=self.temp.name))),
                     patch('pixelblaze_mapper.mk2_td.Host', HydrationHost),
                     patch('pixelblaze_mapper.maschine_mk2.Surface', FakeSurface)):
            mock.start()
            self.addCleanup(mock.stop)
        self.library = SimpleNamespace(_items=[dict(id='m%d'%i, label='Material %d'%i) for i in range(3)],
                                       _safe_preview_path=lambda _: None)
        self.editor = SimpleNamespace(show=lambda:dict(cues=[]), _library=lambda:self.library,
                                      _catalog=lambda:{'gradient':dict(label='Core Gradient')},
                                      _state=lambda key, default='':default)
        self.owner = SimpleNamespace(op=lambda name:SimpleNamespace(module=self.editor))
        self.manager = Manager(self.owner)

    def favorites(self, ids):
        config = self.manager.controller.export_config()
        config['favorites'] = ids
        self.manager.controller.set_context(dict(config=config))
        self.manager.update_surface()

    def test_filtered_metadata_and_load_use_selected_id_not_unfiltered_index(self):
        self.favorites(['m2'])
        button(self.manager, 'browse')
        button(self.manager, 'top', 1)
        self.assertIsNone(self.manager.host.requests[-1])
        self.assertEqual(self.manager.controller.browse_index, 0)
        self.assertEqual(self.manager.controller.snapshot()['browse_items'][0]['id'], 'm2')
        self.assertFalse(self.manager.host.commands)
        press(self.manager)
        self.assertEqual(self.manager.host.commands[-1]['material_id'], 'm2')

    def test_disk_save_restart_core_id_and_version_then_web_edit_preserves_favorites(self):
        button(self.manager, 'browse')
        wheel(self.manager, -127)  # Core Gradient sorts before Material 0.
        version = self.manager.version
        button(self.manager, 'top', 7)
        self.assertEqual(self.manager.version, version+1)
        self.assertEqual(self.manager.controller.export_config()['favorites'], ['core:gradient'])
        self.assertFalse(self.manager.host.commands)
        restored = Manager(self.owner)
        self.assertEqual(restored.controller.export_config()['favorites'], ['core:gradient'])
        config = deepcopy(restored.config)
        config['pads'][0] = dict(kind='material', target='m1')
        restored.command(dict(action='pads_config', pads_version=restored.version, config=config))
        disk = json.loads(restored.path.read_text())
        self.assertEqual(disk['favorites'], ['core:gradient'])
        self.assertEqual(disk['groups'][0]['pads'][0]['target'], 'm1')

    def test_failed_write_release_then_retry_persists_once(self):
        button(self.manager, 'browse')
        event = dict(type='button', name='top', index=7, down=True)
        version = self.manager.version
        with patch.object(self.manager, '_write_config', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.manager.dispatch(event)
        self.manager.dispatch(dict(event, down=False))
        self.assertEqual(self.manager.version, version)
        self.assertEqual(self.manager.controller.export_config()['favorites'], [])
        self.assertIn('disk full', self.manager.snapshot()['error'])
        self.assertFalse(self.manager.path.exists())
        button(self.manager, 'top', 7)
        self.assertEqual(self.manager.version, version+1)
        self.assertEqual(json.loads(self.manager.path.read_text())['favorites'], ['m0'])

    def test_catalog_tick_reorder_retains_filtered_selection_without_hydration(self):
        self.favorites(['m1', 'm2'])
        button(self.manager, 'browse')
        button(self.manager, 'top', 1)
        wheel(self.manager, 1)
        self.library._items = [dict(id='m2', label='AAA renamed'), dict(id='m1', label='ZZZ renamed')]
        self.manager.tick()
        self.assertEqual(self.manager.controller.browse_selected_id(), 'm2')
        self.assertEqual(self.manager.controller.browse_index, 0)
        self.assertIsNone(self.manager.host.requests[-1])
        press(self.manager)
        self.assertEqual(self.manager.host.commands[-1]['material_id'], 'm2')

    def test_filtered_assignment_saves_correct_descriptor_without_activation(self):
        self.favorites(['m2'])
        button(self.manager, 'scene')
        press(self.manager)
        press(self.manager)
        button(self.manager, 'top', 1)
        press(self.manager)
        self.assertEqual(self.manager.controller.assign_target, 'm2')
        self.assertEqual(self.manager.host.requests[-1], 'm2')
        press(self.manager)
        disk = json.loads(self.manager.path.read_text())
        self.assertEqual(disk['groups'][0]['pads'][0]['target'], 'm2')
        self.assertEqual(disk['favorites'], ['m2'])
        self.assertFalse(self.manager.host.commands)

    def test_queued_save_version_change_drops_duplicate_but_releases_key(self):
        config = self.manager.controller.export_config()
        config['hardware'] = True
        self.manager.controller.set_context(dict(config=config))
        button(self.manager, 'browse')
        down = dict(type='button', name='top', index=7, down=True)
        version = self.manager.version
        for event in (down, down, dict(down, down=False)):
            self.manager.post_event(event, version)
        self.manager.tick()
        self.assertEqual(self.manager.version, version+1)
        self.assertEqual(self.manager.controller.export_config()['favorites'], ['m0'])
        self.assertNotIn(('top', 7), self.manager.controller.held)
        self.manager.post_event(down, self.manager.version)
        self.manager.post_event(dict(down, down=False), self.manager.version)
        self.manager.tick()
        self.assertEqual(self.manager.version, version+2)
        self.assertEqual(json.loads(self.manager.path.read_text())['favorites'], [])
        self.assertFalse(self.manager.host.commands)


if __name__ == '__main__':
    unittest.main()
