"""Correct Panel 2 to the user reference: clockwise rotation then top-bottom flip."""
from dataclasses import replace, asdict
from math import asin, atan2, degrees
import numpy as np
from pixelblaze_mapper.layout_scene import Transform


def prepare(document):
    scene=document.scene
    obj=scene.object('eeb92daf-cb0b-4ddf-952b-d3c49897b0f9')
    original=obj.transform
    assert original.pivot==(0.,0.,0.)
    pure=Transform(rotation_degrees=original.rotation_degrees)
    rotation=np.array([pure.apply(tuple(v)) for v in np.eye(3)]).T
    # Screen coordinates (right,up)=(-Z,X): swapping them preserves the upper-right corner.
    mirror=np.array([[0.,0.,-1.],[0.,1.,0.],[-1.,0.,0.]]);local_flip=np.diag([-1.,1.,1.])
    center=np.array([.9,1.,.4])
    matrix=mirror@rotation@local_flip
    assert np.allclose(np.linalg.det(matrix),1.)
    ry=asin(float(np.clip(-matrix[2,0],-1,1)))
    rx=atan2(matrix[2,1],matrix[2,2]);rz=atan2(matrix[1,0],matrix[0,0])
    translation=center+mirror@(np.array(original.translation)-center)
    transform=Transform(translation=tuple(translation),rotation_degrees=tuple(map(degrees,(rx,ry,rz))),
                        scale=(-original.scale[0],original.scale[1],original.scale[2]))
    revised=replace(obj,transform=transform)
    updated=replace(document,scene=replace(scene,objects=tuple(revised if o.object_id==obj.object_id else o for o in scene.objects)))
    ids={b.led_id for b in obj.leds}
    old=np.array([p for b,p in scene.world_points() if b.led_id in ids])
    new=np.array([p for b,p in updated.scene.world_points() if b.led_id in ids])
    assert np.allclose(new,center+(old-center)@mirror.T)
    assert np.allclose(new[:,1],old[:,1])
    assert np.allclose(new[:,0]-.9,-(old[:,2]-.4))
    assert np.allclose(-(new[:,2]-.4),old[:,0]-.9)
    assert np.allclose((new.max(0)+new.min(0))/2,center)
    assert np.allclose(np.ptp(old,axis=0)[[2,1,0]],np.ptp(new,axis=0))
    assert updated.scene.scans==scene.scans and updated.routes==document.routes and revised.leds==obj.leds
    assert all(a==b for a,b in zip(scene.objects,updated.scene.objects) if a.object_id!=obj.object_id)
    return updated,{'operation':'90 degree clockwise rotation followed by top-bottom mirror; screen axes swapped',
        'center':center.tolist(),'transform_before':asdict(original),'transform_after':asdict(transform),
        'bounds_after':[new.min(0).tolist(),new.max(0).tolist()],
        'center_depth_uniform_size_preserved':True,'raw_scans_bindings_routes_preserved':True,
        'other_objects_unchanged':True,'bindings':len(obj.leds),'active_applied':False}
