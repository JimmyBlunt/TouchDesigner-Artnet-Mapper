"""Explicit partial activation with fixed-size, black reserved output slots.

Does not claim a complete sparse workspace apply; does not start hardware.
"""
import json
from pixelblaze_mapper.routing_transaction import table_rows, write_rows, router_from_rows, apply_router_transaction
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.effect_surface_uv import rear_wall_uv
from pixelblaze_mapper import guided_scan_live as live, layout_scene_td


def apply(op):
    live.assert_outputs_off(op)
    router=op(live.ROUTER); editor=op('/project1/layout_scene_editor')
    assert not router.fetch('back_panel_partial_activation',None), 'Already activated; review rather than repeat'
    scene=layout_scene_td.editor(editor).current.scene
    points={led.source_index:point for led,point in scene.world_points()}
    report=editor.fetch('back_panel_replacement_report')
    assert report['new_sources']==[1440,1642] and report['vacant_sources']==[1643,1695]
    target=set(range(1440,1643)); holes=set(range(1643,1696))
    assert len(points)==3691 and not holes.intersection(points)
    map_op=op('/project1/pixelblaze_mapper/map_active');uv_op=op('/project1/pixelblaze_mapper/effect_panel_uv')
    old_map=table_rows(map_op);old_uv=table_rows(uv_op)
    assert len(old_map)==len(old_uv)==3745
    maps=[row[:] for row in old_map];uvs=[row[:] for row in old_uv]
    for i in sorted(target):
        assert int(maps[i+1][0])==i
        maps[i+1]=[str(i)]+[repr(float(v)) for v in points[i]]
        u,v=rear_wall_uv(points[i][0],points[i][2])
        uvs[i+1][3:7]=[repr(u),repr(v),repr(u),repr(v)]
    controllers=table_rows(router.op('controller_config'))
    old_controllers=[r[:] for r in controllers]
    assert all(r[2]!='10.0.0.249' for r in controllers[1:])
    controllers.append(['1','BACK_PANEL_249','10.0.0.249','10.0.0.125','6454','120','RGB','0.05','30','0','2'])
    segments=table_rows(router.op('segment_config'));old_segments=[r[:] for r in segments]
    segments=[segments[0]]+[r for r in segments[1:] if r[0]!='GICO_PORT_4_PORT_4']
    segments.append(['BACK_TOP_LEFT','1440','203','BACK_PANEL_249','0','0','RGB'])
    ports=router.op('gico_port_config/ports');old_ports=table_rows(ports);new_ports=[r[:] for r in old_ports]
    for row in new_ports[1:]:
        if row[0]=='4':row[2]='0'
    config=router_from_rows(controllers,segments,3744)
    build_router_plan(config)
    enabled={c.name for c in config.controllers if c.enabled}
    assert all(not holes.intersection(range(s.source_start,s.source_start+s.count))
               for s in config.segments if s.controller in enabled)
    xyz=op('/project1/null4')
    old_xyz={axis:[float(xyz[axis][i]) for i in range(3744)] for axis in ('tx','ty','tz')}
    original_draft=editor.op('draft_document').text
    old_mask=router.fetch('inactive_source_ranges',[])
    snapshot=dict(map=old_map,uv=old_uv,controllers=old_controllers,segments=old_segments,
                  ports=old_ports,mask=old_mask)
    def rebuild(): router.op('ui_callbacks').module._rebuild_router()
    def cook():
        for path in ('/project1/LedMap','/project1/null4','/project1/effect_sample_uv','/project1/topto1','/project1/math1'):
            op(path).cook(force=True)
            assert not op(path).errors(),path
    try:
        write_rows(map_op,maps);write_rows(uv_op,uvs)
        router.store('inactive_source_ranges',[[1643,1695]])
        apply_router_transaction(router,controllers,segments,rebuild,extra_tables=((ports,new_ports),),source_pixels=3744)
        cook();live.assert_outputs_off(op)
        assert table_rows(map_op)==maps and table_rows(uv_op)==uvs
        for i in set(range(3744))-target:
            assert maps[i+1]==old_map[i+1] and uvs[i+1]==old_uv[i+1]
            assert all(abs(float(xyz[axis][i])-old_xyz[axis][i])<1e-7 for axis in old_xyz)
        assert editor.op('draft_document').text==original_draft
        assert op('/project1/math1').numSamples==3744
    except Exception:
        write_rows(map_op,old_map);write_rows(uv_op,old_uv)
        router.store('inactive_source_ranges',old_mask)
        apply_router_transaction(router,old_controllers,old_segments,rebuild,extra_tables=((ports,old_ports),),source_pixels=3744)
        cook()
        raise
    router.store('back_panel_partial_activation_backup',snapshot)
    result=dict(controller='BACK_PANEL_249',ip='10.0.0.249',wire_universes=[120,121],
                physical_port=1,leds=203,source_range=[1440,1642],black_slots=[1643,1695],
                output_slots=3744,mode='partial fixed-slot activation; not full workspace apply',
                other_coordinates_unchanged=True,normal_output_started=False)
    router.store('back_panel_partial_activation',result)
    layout_scene_td.status(editor,'PANEL ACTIVE DATA | 203 LEDs to .249 U120/121 | 53 slots black | network output OFF')
    return result
