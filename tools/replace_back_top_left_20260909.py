"""Explicit draft-only replacement, preserving raw scan and other source IDs.

Front view looks from the cabinet interior toward the Y=1 back wall:
X is up, increasing Z is screen-left. This differs from material UV direction.
Fit to the old LED envelope, not a claim of calibrated room units.
"""
from dataclasses import replace
from math import atan2, asin, degrees
from uuid import uuid5, NAMESPACE_URL
import numpy as np
from pixelblaze_mapper.layout_scene import Transform


def prepare(document):
    scene = document.scene
    assert len(scene.objects) == 2, 'Review changed scene before using this migration'
    old, incoming = scene.objects
    assert len(old.leds) == 3744 and len(incoming.leds) == 203
    assert [l.source_index for l in incoming.leds] == list(range(3744,3947))
    target = set(range(1440,1696))
    before = {l.source_index:(l,p) for l,p in scene.world_points()}
    destination = np.array([before[i][1] for i in sorted(target)])
    assert np.allclose(destination[:,1],1)
    assert np.allclose(destination.min(0),[.815625,1,.515625])
    assert np.allclose(destination.max(0),[.984375,1,.684375])
    scan = next(s for s in scene.scans if s.scan_id == incoming.leds[0].scan_id)
    assert not scan.missing_indices and len(scan.points)==203
    points = np.array([scan.registration.apply(p) for p in scan.points])
    center = points.mean(0)
    _, singular, basis = np.linalg.svd(points-center)
    normal = basis[2]
    if normal[2] < 0: normal = -normal
    u = basis[0]; v = np.cross(normal,u)
    candidates=[]
    # Oriented bounding rectangle; no point reshaping or flattening.
    for angle in np.linspace(0,2*np.pi,1440,endpoint=False):
        horizontal=u*np.cos(angle)+v*np.sin(angle)
        vertical=-u*np.sin(angle)+v*np.cos(angle)
        rotation=np.array([vertical,-normal,-horizontal])
        q=(points-center) @ rotation.T
        lo=q.min(0);hi=q.max(0);span=hi-lo
        corner=((hi[0]-q[0,0])/span[0])**2+((hi[2]-q[0,2])/span[2])**2
        candidates.append((corner,span[0]*span[2],rotation,q))
    # LED0 fixes top-left; among near-corner solutions pick tight rectangle.
    best_corner=min(c[0] for c in candidates)
    _,_,rotation,q=min((c for c in candidates if c[0]<=best_corner+.002),key=lambda c:c[1])
    assert np.linalg.det(rotation)>.999
    extent=q.max(0)-q.min(0)
    scale=.16875/max(extent[0],extent[2])
    target_center=np.array([.9,1.,.6])
    midpoint=(q.max(0)+q.min(0))/2
    translation=target_center-scale*(rotation @ center+midpoint)
    ry=asin(float(np.clip(-rotation[2,0],-1,1)))
    rx=atan2(rotation[2,1],rotation[2,2]); rz=atan2(rotation[1,0],rotation[0,0])
    transform=Transform(translation=tuple(translation),rotation_degrees=tuple(map(degrees,(rx,ry,rz))),scale=(scale,)*3)
    check=np.array([transform.apply(tuple(map(float,p))) for p in points])
    assert np.allclose(check, target_center+(q-midpoint)*scale)
    kept=replace(old,leds=tuple(l for l in old.leds if l.source_index not in target))
    fitted=replace(incoming,name='Rueckwand oben links (Front) - 30x30 cm',
                   leds=tuple(replace(l,led_id=str(uuid5(NAMESPACE_URL,l.led_id+':back-top-left-replacement')),
                                      source_index=1440+l.scan_index) for l in incoming.leds),transform=transform)
    updated=replace(scene,objects=(kept,fitted))
    after={l.source_index:(l,p) for l,p in updated.world_points()}
    for i in set(before)-target-set(range(3744,3947)):
        assert after[i]==before[i], 'Unrelated LED changed'
    assert len(after)==3691
    report=dict(panel_cm=[30,30],target_sources=[1440,1695],new_sources=[1440,1642],
                vacant_sources=[1643,1695],count=3691,remaining_fields_unchanged=True,
                fit='uniform rotation/scale to old normalized LED envelope; not metric calibration',
                singular_values=singular.tolist(),led0=check[0].tolist(),
                bounds=[check.min(0).tolist(),check.max(0).tolist()],
                physical_registration_verified=False,active_applied=False)
    report['new_binding_identity_reason']='Explicit replacement allocation; original scan IDs and measurements archived unchanged'
    return replace(document,scene=updated),report
