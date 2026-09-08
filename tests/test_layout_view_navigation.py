import unittest
from unittest.mock import patch
from pixelblaze_mapper import layout_scene_td as td


class Owner:
    def __init__(self): self.values = {}
    def fetch(self, key, default=None): return self.values.get(key, default)
    def store(self, key, value): self.values[key] = value


class NavigationTests(unittest.TestCase):
    @patch.object(td, '_camera')
    def test_zoom_and_limits(self, camera):
        owner=Owner()
        td.zoom_view(owner,1)
        self.assertAlmostEqual(owner.fetch('view_zoom'),1.15)
        td.zoom_view(owner,-1)
        self.assertAlmostEqual(owner.fetch('view_zoom'),1)
        for _ in range(100): td.zoom_view(owner,10)
        self.assertEqual(owner.fetch('view_zoom'),20)
        for _ in range(100): td.zoom_view(owner,-10)
        self.assertEqual(owner.fetch('view_zoom'),.1)

    @patch.object(td, '_camera')
    def test_orbit_changes_camera_storage_only(self, camera):
        owner=Owner()
        td.orbit_view(owner,15)
        self.assertEqual(owner.values,{'view_angles':(40.,15.)})

    @patch.object(td, '_camera')
    def test_2d_and_zero_wheel_ignored(self,camera):
        owner=Owner();td.zoom_view(owner,0)
        owner.store('layout_view','2d');td.zoom_view(owner,1)
        self.assertNotIn('view_zoom',owner.values)
        camera.assert_not_called()
