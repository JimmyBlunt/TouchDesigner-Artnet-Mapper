"""Explicit 2026-09-09 draft migration. No TD, network or output access.

The approved face coordinates are horizontal=-v, vertical=-u for every panel.
Side view is from inside the cabinet towards its right wall: screen-right=-Y.
Therefore world XYZ=(-u,+v,-normal), a proper rotation, not reordered LEDs.
"""
from dataclasses import replace
from math import asin, atan2, degrees
from uuid import NAMESPACE_URL, uuid5
import numpy as np
from .layout_scene import Scan, SceneObject, Transform

SPECS = (
    ('upper', 'Seite oben', 517, 269, 20., 16., (.94,.875,.30)),
    ('middle', 'Seite Mitte', 0, 517, 29.5, 29., (.62,.875,.30)),
    ('lower', 'Seite unten', 786, 398, 23., 33., (.20,.90,.30)),
)
UNITS_PER_CM = .16875 / 30.

def uid(text):
    return str(uuid5(NAMESPACE_URL, 'side-alignment-20260909:'+text))

def prepare(document, repaired_points, estimated_indices=()):
    scene=document.scene
    if len(scene.objects)!=2 or document.routes:
        raise ValueError('Expected reviewed two-object draft without draft routes')
    before={led.source_index:(led,point) for led,point in scene.world_points()}
    if len(before)!=3691 or not set(range(1184))<=before.keys():
        raise ValueError('Unexpected source coverage; review before migration')
    if len(repaired_points)!=1184:
        raise ValueError('Expected 1184 repaired scan points')
    old=next(o for o in scene.objects if any(l.source_index==0 for l in o.leds))
    if not set(range(1184))<={l.source_index for l in old.leds}:
        raise ValueError('Side panels are not in the expected original object')
    kept=replace(old, leds=tuple(l for l in old.leds if l.source_index>=1184))
    objects=[kept if o.object_id==old.object_id else o for o in scene.objects]
    scans=list(scene.scans); panels=[]; identity_map={}
    for key,name,start,count,width,height,center in SPECS:
        p=np.array(repaired_points[start:start+count],dtype=float)
        if p.shape!=(count,3) or not np.isfinite(p).all():
            raise ValueError('Invalid scan coordinates')
        origin=p.mean(0)
        _,singular,basis=np.linalg.svd(p-origin,full_matrices=False)
        normal=basis[-1]
        if normal[2]<0: normal=-normal
        h=np.array([1.,0.,0.]); h-=normal*np.dot(h,normal); h/=np.linalg.norm(h)
        v=np.cross(normal,h)
        rotation=np.array([-h,v,-normal])
        assert np.allclose(rotation@rotation.T,np.eye(3)) and np.linalg.det(rotation)>.999999
        q=(p-origin)@rotation.T
        lo=q.min(0); hi=q.max(0); spans=hi-lo
        if min(spans[:2])<=1e-10: raise ValueError('Degenerate panel')
        scales=np.array([height*UNITS_PER_CM/spans[0],width*UNITS_PER_CM/spans[1],0.])
        scales[2]=min(scales[:2])
        angles=(atan2(rotation[2,1],rotation[2,2]),asin(float(np.clip(-rotation[2,0],-1,1))),atan2(rotation[1,0],rotation[0,0]))
        registration=Transform(translation=tuple(-rotation@origin),rotation_degrees=tuple(map(degrees,angles)))
        assert np.allclose([registration.apply(tuple(point)) for point in p],q)
        sid=uid(key+':scan'); oid=uid(key+':object')
        metadata=tuple((('global_source',str(start+i)),('quality','estimated' if start+i in estimated_indices else 'measured')) for i in range(count))
        scans.append(Scan(sid,name+' - archivierter reparierter Scan',tuple(map(tuple,p)),
                          source_format='pixelblaze-repaired-archive',row_metadata=metadata,
                          warnings=('Measured envelope; photo-estimated placement; raw depth retained',),
                          generator_source='mappings/sources/complete_new_0_1183_raw_2026-08-24.json',registration=registration))
        bindings=[]
        for i in range(count):
            previous=before[start+i][0]
            new=replace(previous,led_id=uid(previous.led_id+':'+key),local_index=i,scan_id=sid,scan_index=i)
            bindings.append(new); identity_map[previous.led_id]=new.led_id
        transform=Transform(translation=tuple(np.array(center)-scales*(lo+hi)/2),scale=tuple(scales))
        objects.append(SceneObject(oid,f'{name} | {width:g} x {height:g} cm',tuple(bindings),transform))
        fitted=np.array([transform.apply(registration.apply(tuple(point))) for point in p])
        assert np.allclose(np.ptp(fitted,axis=0)[:2],[height*UNITS_PER_CM,width*UNITS_PER_CM])
        panels.append(dict(key=key,object_id=oid,source_range=[start,start+count-1],count=count,
                           size_cm=[width,height],center=list(center),bounds=[fitted.min(0).tolist(),fitted.max(0).tolist()],
                           scale_xy_ratio=float(scales[0]/scales[1]),estimated_count=sum(start+i in estimated_indices for i in range(count)),
                           rotation_determinant=float(np.linalg.det(rotation)),singular_values=singular.tolist()))
    updated=replace(document,scene=replace(scene,scans=tuple(scans),objects=tuple(objects)))
    after={l.source_index:(l,p) for l,p in updated.scene.world_points()}
    assert before.keys()==after.keys()
    assert all(before[i]==after[i] for i in before if i>=1184)
    report=dict(panels=panels,units_per_cm=UNITS_PER_CM,reference='30cm rear envelope = .16875 existing world units',
                position_quality='estimated from annotated photo; cabinet depth not measured',
                side_plane_z=.30,source_indices_unchanged=True,rear_bindings_and_coordinates_unchanged=True,
                inactive_gap=list(range(1643,1696)),active_applied=False,
                internal_binding_id_map=identity_map,
                identity_reason='Grouping changes object/local identity; source/wire indices stay exactly unchanged',
                fixture_policy='Existing independent 2D draft preserved, not reprojected; requires explicit review before use')
    return updated,report
