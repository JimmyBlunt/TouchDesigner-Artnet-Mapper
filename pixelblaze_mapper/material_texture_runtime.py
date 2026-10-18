"""Bind resolved MadMapper image dependencies to an isolated material TOP."""
import json

def bind_textures(preview, adaptation):
    from .material_paths import resolve_asset_path
    textures = []
    for original in getattr(adaptation, 'textures', ()):
        texture = dict(original)
        if texture.get('resolved_path'):
            texture['resolved_path'] = resolve_asset_path(texture['resolved_path'])
        if texture.get('resolved_paths'):
            texture['resolved_paths'] = [resolve_asset_path(path) for path in texture['resolved_paths']]
        textures.append(texture)
    signature = tuple((str(t.get('TYPE', '2d')).lower(),
                       tuple(t.get('resolved_paths') or [t['resolved_path']]),
                       t.get('GL_TEXTURE_WRAP'), t.get('GL_TEXTURE_MIN_FILTER'),
                       json.dumps(t,sort_keys=True) if str(t.get('TYPE','')).lower() in ('audio','audiofft') else None)
                      for t in textures)
    if preview.fetch('material_texture_signature', None) == signature:
        return
    from td import moviefileinTOP
    parent = preview.parent()
    prefix = preview.name + '_asset_'
    nodes = []
    retained = []

    def image_node(name, path):
        node = parent.op(name)
        if node is None:
            node = parent.create(moviefileinTOP, name)
        node.par.file = path
        node.cook(force=True)
        if node.errors():
            raise ValueError('Cannot load material texture: ' + path + ': ' + str(node.errors()))
        retained.append(node)
        return node

    for index, texture in enumerate(textures):
        if str(texture.get('TYPE', '2d')).lower() in ('audio', 'audiofft'):
            from .material_audio_runtime import bind_audio_texture, audio_component
            node = bind_audio_texture(preview, texture, index)
            retained.extend((node, audio_component(node)))
        elif str(texture.get('TYPE', '2d')).lower() == 'cube':
            # Both MadMapper PATH arrays and Cube Map TOP inputs use GL face
            # order: +X, -X, +Y, -Y, +Z, -Z. Keep each face as a real texture.
            from td import cubemapTOP
            paths = texture.get('resolved_paths', ())
            if len(paths) != 6:
                raise ValueError('Cube texture requires six ordered faces')
            faces = [image_node(prefix+str(index)+'_face_'+str(i), path)
                     for i,path in enumerate(paths)]
            name = prefix+str(index)+'_cube'
            node = parent.op(name)
            if node is None:
                node = parent.create(cubemapTOP, name)
            node.par.mode = 'onepersidetocubemap'
            node.setInputs(faces)
            node.cook(force=True)
            if node.errors():
                raise ValueError('Cannot build cube texture: '+str(node.errors()))
            retained.append(node)
        else:
            node = image_node(prefix+str(index), texture['resolved_path'])
        nodes.append(node)
    preview.setInputs(nodes)
    preview.par.inputextenduv = 'repeat' if any(t.get('GL_TEXTURE_WRAP') == 'REPEAT' for t in textures) else 'hold'
    preview.par.inputfiltertype = 'nearest' if textures and all(t.get('GL_TEXTURE_MIN_FILTER') == 'NEAREST' for t in textures) else 'linear'
    for node in list(parent.children):
        if node.name.startswith(prefix) and node not in retained:
            node.destroy()
    preview.store('material_texture_signature', signature)
