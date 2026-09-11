"""Remove explicit local bindings from a draft while preserving scan archives."""
from dataclasses import replace
from .layout_scene import SceneError


def prepare(document, object_id, local_indices):
    obj = document.scene.object(object_id)
    wanted = set(local_indices)
    if not wanted or any(type(i) is not int or i < 0 for i in wanted):
        raise SceneError('Enter an explicit LOCAL LEDs range before removing')
    available = {b.local_index for b in obj.leds}
    if not wanted <= available:
        raise SceneError('The LOCAL LEDs range includes LEDs outside the selected object')
    if wanted == available:
        raise SceneError('This action removes a partial range; keep at least one LED in the object')
    removed = tuple(b for b in obj.leds if b.local_index in wanted)
    cleaned = replace(obj, leds=tuple(b for b in obj.leds if b.local_index not in wanted))
    scene = replace(document.scene, objects=tuple(cleaned if o.object_id == object_id else o
                                                  for o in document.scene.objects))
    return replace(document, scene=scene), removed


def remove_from_ui(owner, confirm):
    from . import layout_scene_td as layout
    from .layout_scene_adapter import parse_indices
    if owner.fetch('layout_view', '3d') != '3d':
        raise SceneError('Remove LEDs is available in 3D LAYOUT')
    session = layout.editor(owner)
    if session.preview is not None:
        raise SceneError('Finish the current layout drag first')
    obj = session.current.scene.object(session.selected_object_id)
    text = layout.field(owner, 'localrange')
    updated, removed = prepare(session.current, obj.object_id, parse_indices(text))
    sources = [b.source_index for b in removed]
    message = ('Remove %d LEDs from "%s" in the draft?\nLOCAL LEDs: %s\n'
               'Global source IDs: %d to %d (only selected bindings).\n'
               'Original scan files and active output stay unchanged. UNDO restores this step.') % (
                   len(removed), obj.name, text, min(sources), max(sources))
    if not confirm(message):
        return
    session.commit(updated)
    owner.store('ui_prepared_context', None)
    layout.write_field(owner, 'localrange', '')
    layout.refresh(owner)
    layout.status(owner, 'REMOVED %d DRAFT LEDs | %s | UNDO available; active output unchanged' %
                  (len(removed), obj.name))
