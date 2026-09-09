"""Targeted active data update. Does not start output or alter routing."""
from pixelblaze_mapper.routing_transaction import table_rows, write_rows, router_from_rows
from pixelblaze_mapper.multi_controller import build_router_plan
from pixelblaze_mapper.effect_surface_uv import BACK_X_MIN, BACK_X_MAX, BACK_Z_MIN, BACK_Z_MAX
from pixelblaze_mapper import guided_scan_live, layout_scene_td

def prepare_rows(old_map,old_uv,points):
    if len(old_map)!=3745 or len(old_uv)!=3745: raise ValueError('Expected fixed 3744-slot tables')
    if not set(range(1184))<=points.keys(): raise ValueError('Missing side coordinates')
    maps=[r[:] for r in old_map]; uvs=[r[:] for r in old_uv]
    global_uv={i:((1.-points[i][1])/(BACK_Z_MAX-BACK_Z_MIN),
                  (points[i][0]-BACK_X_MIN)/(BACK_X_MAX-BACK_X_MIN)) for i in range(1184)}
    for start,count in ((0,517),(517,269),(786,398)):
        values=[global_uv[i] for i in range(start,start+count)]
        lo=[min(p[a] for p in values) for a in (0,1)]
        hi=[max(p[a] for p in values) for a in (0,1)]
        for i in range(start,start+count):
            assert int(maps[i+1][0])==int(uvs[i+1][0])==i
            raw_u,raw_v=global_uv[i]
            assert -.01<=raw_u<=1.01 and -.01<=raw_v<=1.01
            u,v=(max(0.,min(1.,value)) for value in (raw_u,raw_v))
            maps[i+1]=[str(i)]+[repr(float(x)) for x in points[i]]
            local=[(global_uv[i][a]-lo[a])/(hi[a]-lo[a]) for a in (0,1)]
            uvs[i+1][3:7]=list(map(repr,(u,v,*local)))
    assert maps[1185:]==old_map[1185:] and uvs[1185:]==old_uv[1185:]
    return maps,uvs

def apply(op):
    guided_scan_live.assert_outputs_off(op)
    owner=op('/project1/layout_scene_editor'); router=op('/project1/multi_controller_output')
    assert not router.fetch('side_panel_partial_activation',None),'Already applied'
    report=owner.fetch('side_alignment_report')
    assert layout_scene_td.active_hash(owner)==report['active_hash_before'],'Active state changed since draft review'
    scene=layout_scene_td.editor(owner).current.scene
    points={l.source_index:p for l,p in scene.world_points()}
    assert len(points)==3691 and not set(range(1643,1696)).intersection(points)
    controllers=table_rows(router.op('controller_config')); segments=table_rows(router.op('segment_config'))
    build_router_plan(router_from_rows(controllers,segments,3744))
    m=op('/project1/pixelblaze_mapper/map_active'); u=op('/project1/pixelblaze_mapper/effect_panel_uv')
    old_map=table_rows(m);old_uv=table_rows(u)
    maps,uvs=prepare_rows(old_map,old_uv,points)
    backup=dict(map=old_map,uv=old_uv,active_hash=layout_scene_td.active_hash(owner))
    def cook():
        for path in ('/project1/LedMap','/project1/null4','/project1/effect_sample_uv','/project1/topto1','/project1/math1',
                     '/project1/pixelblaze_mapper/preview3d/instance_data'):
            op(path).cook(force=True)
            assert not op(path).errors(),path
    try:
        write_rows(m,maps);write_rows(u,uvs);cook()
        assert table_rows(m)==maps and table_rows(u)==uvs
        assert table_rows(router.op('controller_config'))==controllers
        assert table_rows(router.op('segment_config'))==segments
        assert router.fetch('inactive_source_ranges')==[[1643,1695]]
        assert op('/project1/math1').numSamples==3744
        guided_scan_live.assert_outputs_off(op)
    except:
        write_rows(m,old_map);write_rows(u,old_uv);cook();raise
    router.store('side_panel_partial_activation_backup',backup)
    result=dict(source_range=[0,1183],changed_leds=1184,output_slots=3744,rear_rows_unchanged=True,
                routing_unchanged=True,global_projection='u=(1-Y)/rear_width; v=(X-rear_min)/rear_height',
                shared_height_with_rear=True,normal_output_started=False,
                active_hash=layout_scene_td.active_hash(owner),mode='partial fixed-slot data activation')
    router.store('side_panel_partial_activation',result)
    layout_scene_td.status(owner,'SIDE PANELS ACTIVE DATA | 1184 LEDs / measured geometry | photo-estimated positions | network OFF')
    return result
