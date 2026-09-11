import unittest
from unittest.mock import Mock, patch
from pixelblaze_mapper.layout_scene import Scene, Scan, SceneError, append_scan
from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, LayoutEditor, RouteBinding
from pixelblaze_mapper.layout_remove_leds import prepare, remove_from_ui


class RemoveDraftLedsTests(unittest.TestCase):
    def setUp(self):
        scene = append_scan(Scene('room', 'Room'), Scan('scan', 'Grid', ((0,0,0),(1,0,0),(2,0,0))),
                            source_start=100, object_id='grid')
        scene = append_scan(scene, Scan('other', 'Panel', ((4,5,6),)), source_start=500, object_id='panel')
        self.document = LayoutDocument(scene, (RouteBinding('grid', 'controller', 1),))

    def test_preserve_archive_other_objects_ids_and_undo(self):
        updated, removed = prepare(self.document, 'grid', (1,))
        self.assertEqual([b.source_index for b in removed], [101])
        self.assertEqual([b.local_index for b in updated.scene.object('grid').leds], [0,2])
        self.assertEqual([b.source_index for b in updated.scene.object('grid').leds], [100,102])
        self.assertEqual(updated.scene.scans, self.document.scene.scans)
        self.assertEqual(updated.routes, self.document.routes)
        self.assertEqual(updated.scene.object('panel'), self.document.scene.object('panel'))
        editor = LayoutEditor(self.document)
        editor.commit(updated)
        self.assertEqual(editor.undo(), self.document)
        self.assertEqual(editor.redo(), updated)

    def test_invalid_or_all_ranges_rejected(self):
        for values in ((), (True,), (-1,), (3,), (0,1,2)):
            with self.subTest(values=values), self.assertRaises(SceneError):
                prepare(self.document, 'grid', values)

    def test_sparse_local_ids_are_not_row_numbers(self):
        sparse, _ = prepare(self.document, 'grid', (1,))
        with self.assertRaises(SceneError):
            prepare(sparse, 'grid', (1,))
        updated, removed = prepare(sparse, 'grid', (2,))
        self.assertEqual(removed[0].source_index, 102)
        self.assertEqual(len(updated.scene.object('grid').leds), 1)

    def test_cancel_does_not_commit_or_clear_field(self):
        editor = LayoutEditor(self.document)
        editor.select('grid')
        owner = Mock()
        owner.fetch.return_value = '3d'
        confirm = Mock(return_value=False)
        with patch('pixelblaze_mapper.layout_scene_td.editor', return_value=editor), \
             patch('pixelblaze_mapper.layout_scene_td.field', return_value='1'), \
             patch('pixelblaze_mapper.layout_scene_td.write_field') as write:
            remove_from_ui(owner, confirm)
        self.assertEqual(editor.current, self.document)
        write.assert_not_called()
        self.assertIn('Remove 1 LEDs', confirm.call_args.args[0])

    def test_confirmed_removal_has_one_undo_and_clears_range(self):
        editor = LayoutEditor(self.document)
        editor.select('grid')
        owner = Mock()
        owner.fetch.return_value = '3d'
        with patch('pixelblaze_mapper.layout_scene_td.editor', return_value=editor), \
             patch('pixelblaze_mapper.layout_scene_td.field', return_value='1'), \
             patch('pixelblaze_mapper.layout_scene_td.write_field') as write, \
             patch('pixelblaze_mapper.layout_scene_td.refresh'), \
             patch('pixelblaze_mapper.layout_scene_td.status'):
            remove_from_ui(owner, lambda message: True)
        self.assertEqual(len(editor.current.scene.object('grid').leds), 2)
        write.assert_called_once_with(owner, 'localrange', '')
        self.assertEqual(editor.undo(), self.document)
