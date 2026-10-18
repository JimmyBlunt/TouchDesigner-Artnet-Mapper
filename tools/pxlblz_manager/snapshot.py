import json
from pixelblaze_mapper.layout_workspace import export_workspace

owner = op('/project1/layout_scene_editor')
session = owner.fetch('layout_editor_session', None)
assert session is not None, 'Layout-Editor zuerst oeffnen'
assert session.preview is None, 'Aktuelle Layout-Bewegung zuerst abschliessen'
fixtures = owner.fetch('fixture_history', None)
assert fixtures is not None, 'Fixture-Editor nicht initialisiert'
paths = dict(map='/project1/pixelblaze_mapper/map_active',
             mask='/project1/layout_apply/active_source_mask',
             controllers='/project1/multi_controller_output/controller_config',
             segments='/project1/multi_controller_output/segment_config')
nodes = {key: op(path) for key, path in paths.items()}
assert all(node is not None for node in nodes.values()), 'Aktive Tabellen fehlen'
tables = {key: [[cell.val for cell in row] for row in node.rows()] for key, node in nodes.items()}
scene = session.current.scene
by_source = {b.source_index: o.object_id for o in scene.objects for b in o.leds}
result = json.dumps(dict(project=str(project.folder)+'/'+str(project.name), tables=tables,
    world=[dict(index=b.source_index, point=p, object_id=by_source[b.source_index], local_index=b.local_index)
           for b,p in scene.world_points()],
    objects=[dict(id=o.object_id, name=o.name, count=len(o.leds)) for o in scene.objects],
    workspace=export_workspace(session.current, fixtures.current) if include_workspace else None))
