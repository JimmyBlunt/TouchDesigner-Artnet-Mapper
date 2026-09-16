"""Rotate Panel 4 clockwise in front view, around its placed panel centre."""
from dataclasses import replace, asdict
from math import asin, atan2, degrees
import numpy as np
from pixelblaze_mapper.layout_scene import Transform


def prepare(document):
    scene=document.scene
    obj=scene.object('b5c6ab95-b0c7-462d-89e6-e20ca2f7d511')
    transform=obj.transform
    assert transform.pivot==(0.,0.,0.)
    pure=Transform(rotation_degrees=transform.rotation_degrees)
    rotation=np.array([pure.apply(tuple(v)) for v in np.eye(3)]).T
    # Front screen: right=-Z, up=X. Clockwise therefore maps (X,Z)->(Z,-X).
    clockwise=np.array([[0.,0.,1.],[0.,1.,0.],[-1.,0.,0.]])
    center=np.array([.7,1.,.4])
    matrix=clockwise@rotation
    ry=asin(float(np.clip(-matrix[2,0],-1,1)))
    rx=atan2(matrix[2,1],matrix[2,2]);rz=atan2(matrix[1,0],matrix[0,0])
    translation=center+clockwise@(np.array(transform.translation)-center)
    turned=Transform(translation=tuple(translation),rotation_degrees=tuple(map(degrees,(rx,ry,rz))),scale=transform.scale)
    revised=replace(obj,transform=turned)
    updated=replace(document,scene=replace(scene,objects=tuple(revised if o.object_id==obj.object_id else o for o in scene.objects)))
    ids={b.led_id for b in obj.leds}
    old=np.array([p for b,p in scene.world_points() if b.led_id in ids])
    new=np.array([p for b,p in updated.scene.world_points() if b.led_id in ids])
    assert np.allclose(new,center+(old-center)@clockwise.T)
    assert np.allclose(new[:,1],old[:,1])
    assert np.allclose((new.max(0)+new.min(0))/2,center)
    assert np.allclose(new[:,0]-center[0],old[:,2]-center[2])
    assert np.allclose(-(new[:,2]-center[2]),old[:,0]-center[0])
    assert updated.scene.scans==scene.scans and updated.routes==document.routes
    assert revised.leds==obj.leds and revised.transform.scale==obj.transform.scale
    assert all(a==b for a,b in zip(scene.objects,updated.scene.objects) if a.object_id!=obj.object_id)
    return updated,{'rotation':'90 degrees clockwise in front view','center':center.tolist(),
        'transform_before':asdict(transform),'transform_after':asdict(turned),'bindings':len(obj.leds),
        'bounds_after':[new.min(0).tolist(),new.max(0).tolist()],
        'position_scale_depth_preserved':True,'raw_scans_bindings_routes_preserved':True,
        'other_objects_unchanged':True,'active_applied':False}
