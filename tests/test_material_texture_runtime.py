import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pixelblaze_mapper.material_texture_runtime import bind_textures


class TextureBindingTests(unittest.TestCase):
    def test_cached_legacy_texture_paths_resolve_before_signature_without_mutation(self):
        old = 'C:/old/material_library/sources/face.png'
        current = 'D:/new/material_library/sources/face.png'
        texture = {'resolved_path': old, 'resolved_paths': [old]*6, 'TYPE': 'cube'}
        signature = (('cube', (current,)*6, None, None, None),)
        preview = SimpleNamespace(fetch=lambda key,default: signature)
        with patch('pixelblaze_mapper.material_paths.resolve_asset_path',return_value=current) as resolve:
            bind_textures(preview,SimpleNamespace(textures=(texture,)))
        self.assertEqual(resolve.call_count,7)
        self.assertEqual(texture['resolved_path'],old)
        self.assertEqual(texture['resolved_paths'],[old]*6)

    def test_multiple_assets_switch_and_disconnect_without_leaking_nodes(self):
        children = []
        def create(kind, name):
            node = SimpleNamespace(name=name, par=SimpleNamespace(), cook=lambda **kw: None,
                                   errors=lambda: [])
            node.destroy = lambda: children.remove(node)
            children.append(node)
            return node
        parent = SimpleNamespace(children=children, create=create,
                                 op=lambda name: next((n for n in children if n.name == name), None))
        stored = {}
        connected = []
        preview = SimpleNamespace(name='preview', parent=lambda: parent, par=SimpleNamespace(),
                                  fetch=lambda k, default: stored.get(k, default),
                                  store=lambda k, value: stored.update({k: value}),
                                  setInputs=lambda nodes: connected.__setitem__(slice(None), nodes))
        with patch.dict(sys.modules, {'td': SimpleNamespace(moviefileinTOP=object())}):
            textures = tuple({'resolved_path': str(i)+'.png', 'GL_TEXTURE_WRAP': 'REPEAT'} for i in range(4))
            bind_textures(preview, SimpleNamespace(textures=textures))
            self.assertEqual(4, len(connected))
            self.assertEqual('repeat', preview.par.inputextenduv)
            bind_textures(preview, SimpleNamespace(textures=textures))
            self.assertEqual(4, len(children))
            bind_textures(preview, SimpleNamespace(textures=textures[:1]))
            self.assertEqual(1, len(children))
            self.assertEqual(1, len(connected))
            bind_textures(preview, SimpleNamespace(textures=()))
            self.assertEqual([], children)
            self.assertEqual([], connected)


if __name__ == '__main__':
    unittest.main()
