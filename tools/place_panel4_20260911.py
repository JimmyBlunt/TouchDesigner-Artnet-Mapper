"""Reversible Panel 4 draft placement in the second-row right slot.

Uniform similarity only: original measurements and binding identities survive.
Front view: X up, Y rear-wall depth, decreasing Z toward screen-right.
The known 30 cm reference uses a normalized .16875 LED envelope, not meters.
Camera orientation is a provisional cue requiring visual review.
"""
from dataclasses import replace, asdict
from hashlib import sha256
from math import asin, atan2, degrees
from pathlib import Path
import csv
import json
import numpy as np
from pixelblaze_mapper.layout_scene import Transform
from pixelblaze_mapper.scan_partial_acceptance import PREFIX


def prepare(document):
    scene=document.scene
    panel=scene.objects[-1]
    assert len(panel.leds)==809
    reference=scene.object('70cd6e54-b201-4123-85dd-37a7885a4d1f')
    assert '30x30 cm' in reference.name
    scan=next(s for s in scene.scans if s.scan_id==panel.leds[0].scan_id)
    evidence=json.loads(next(w[len(PREFIX):] for w in scan.warnings if w.startswith(PREFIX)))
    points=np.array([scan.registration.apply(scan.points[b.scan_index]) for b in panel.leds])
    indices={b.scan_index:i for i,b in enumerate(panel.leds)}
    views=[]
    for path,digest in evidence['view_sha256'].items():
        if Path(path).name!='view.csv':continue
        data=Path(path).read_bytes()
        assert sha256(data).hexdigest()==digest, 'Observation changed since acceptance'
        rows={int(r['index']):(float(r['u']),float(r['v'])) for r in csv.DictReader(data.decode('utf-8-sig').splitlines())}
        common=sorted(set(rows)&set(indices))
        views.append((len(common),path,common,rows))
    _,view_path,common,rows=max(views,key=lambda v:v[0])
    center=points.mean(0)
    _,singular,basis=np.linalg.svd(points-center,full_matrices=False)
    assert singular[2]/singular[1]<.1, 'Review non-planar scan before fitting'
    normal=basis[2]
    u=basis[0];v=np.cross(normal,u)
    uv=np.array([rows[i] for i in common])
    point_indices=[indices[i] for i in common]
    candidates=[]
    for angle in np.linspace(0,2*np.pi,1440,endpoint=False):
        horizontal=u*np.cos(angle)+v*np.sin(angle)
        vertical=-u*np.sin(angle)+v*np.cos(angle)
        # Both signs are proper rotations; choose the camera-facing version.
        for sign in (1,-1):
            rotation=np.array([vertical,-normal*sign,-horizontal*sign])
            q=(points-center)@rotation.T
            extent=np.ptp(q,axis=0)
            camera=q[point_indices]
            score=np.corrcoef(-camera[:,2],uv[:,0])[0,1]+np.corrcoef(camera[:,0],-uv[:,1])[0,1]
            candidates.append((extent[0]*extent[2],score,rotation,q))
    minimum=min(c[0] for c in candidates)
    _,score,rotation,q=max((c for c in candidates if c[0]<=minimum*1.001),key=lambda c:c[1])
    assert np.linalg.det(rotation)>.999 and score>1.0
    # Existing upper-right template bounds supply the destination only.
    target=[p for b,p in scene.world_points() if 1696<=b.source_index<1952]
    assert len(target)==256
    target=np.array(target)
    assert np.allclose(target.min(0),[.615625,1.,.315625])
    assert np.allclose(target.max(0),[.784375,1.,.484375])
    destination=(target.min(0)+target.max(0))/2
    extent=np.ptp(q,axis=0)
    scale=.16875/max(extent[0],extent[2])
    midpoint=(q.max(0)+q.min(0))/2
    translation=destination-scale*(rotation@center+midpoint)
    ry=asin(float(np.clip(-rotation[2,0],-1,1)))
    rx=atan2(rotation[2,1],rotation[2,2]);rz=atan2(rotation[1,0],rotation[0,0])
    transform=Transform(translation=tuple(translation),rotation_degrees=tuple(map(degrees,(rx,ry,rz))),scale=(scale,)*3)
    transformed=np.array([transform.apply(tuple(p)) for p in points])
    assert np.allclose(transformed,destination+(q-midpoint)*scale)
    fitted=replace(panel,name='Panel 4 | unter Panel 2 | 30 x 30 cm',transform=transform)
    result=replace(document,scene=replace(scene,objects=tuple(fitted if o.object_id==panel.object_id else o for o in scene.objects)))
    assert result.scene.scans==scene.scans and result.routes==document.routes and fitted.leds==panel.leds
    assert all(a==b for a,b in zip(scene.objects,result.scene.objects) if a.object_id!=panel.object_id)
    report={'panel_cm':[30,30],'position':'second row right, below Panel 2','center':destination.tolist(),
            'bounds':[transformed.min(0).tolist(),transformed.max(0).tolist()],
            'transform':asdict(transform),'camera_orientation_reference':view_path,'camera_score':score,
            'fit':'uniform similarity to same normalized LED envelope as first panel',
            'orientation_verified':False,'physical_registration_verified':False,
            'original_scan_unchanged':True,'all_809_bindings_unchanged':True,'missing_count':len(scan.missing_indices),
            'other_objects_unchanged':True,'routes_unchanged':True,'existing_template_preserved':True,
            'active_applied':False}
    return result,report
