"""Prepare the measured replacement offline; no live changes."""
from dataclasses import replace, asdict
from pathlib import Path
import json
import sys
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.layout_scene import Transform
from pixelblaze_mapper.layout_scene_adapter import document_json,load_document_json
from pixelblaze_mapper.layout_workspace import import_workspace
from pixelblaze_mapper.scan_partial_acceptance import append_partial_reviewed
from pixelblaze_mapper.scan_result_review import inspect_saved_result
from pixelblaze_mapper.effect_surface_uv import rear_wall_uv

OUT=ROOT/'docs/panel8-replacement-299-20261018'
PID='99fa5b92-0a88-41a3-abe9-2903e536a17a'
analysis=json.loads((OUT/'analysis.json').read_text())
candidate=Path(analysis['candidate'])
manifest=json.loads(next(candidate.parent.parent.glob('scan-*.json')).read_text())
review=inspect_saved_result(candidate)
data=np.genfromtxt(candidate,delimiter=',',names=True)
ids=data['index'].astype(int); pts=np.column_stack([data[a] for a in 'xyz'])
lookup=dict(zip(ids,pts)); center=pts.mean(0)
_,sv,basis=np.linalg.svd(pts-center,full_matrices=False)
normal=basis[-1]
# Fit the straight final row, rather than allowing a single endpoint to tilt it.
last=np.array([lookup[i] for i in range(283,299)])
_,_,rowbasis=np.linalg.svd(last-last.mean(0),full_matrices=False)
right=rowbasis[0]-normal*np.dot(rowbasis[0],normal); right/=np.linalg.norm(right)
if np.dot(right,lookup[298]-lookup[283])<0:right=-right
down=np.cross(normal,right)
if np.dot(down,lookup[0]-last.mean(0))<0:down=-down
normal=np.cross(right,down)
source=np.column_stack((right,down,normal))
target=np.column_stack(((0.,0.,-1.),(-1.,0.,0.),(0.,1.,0.)))
rot=target@source.T
assert np.allclose(rot@rot.T,np.eye(3)) and np.linalg.det(rot)>.999999
active,fixtures=import_workspace((OUT/'before-active-workspace.json').read_text())
draft=load_document_json((OUT/'before-draft.json').read_text())
old=active.scene.object(PID)
oldids={b.led_id for b in old.leds}
oldpoints=np.array([p for b,p in active.scene.world_points() if b.led_id in oldids])
destination=(oldpoints.min(0)+oldpoints.max(0))/2
rotated=pts@rot.T
scale=max(np.ptp(oldpoints,axis=0)[[0,2]])/max(np.ptp(rotated,axis=0)[[0,2]])
translation=destination-scale*(rotated.min(0)+rotated.max(0))/2
transform=Transform(translation=tuple(translation),rotation_degrees=tuple(Rotation.from_matrix(rot).as_euler('xyz',degrees=True)),scale=(scale,)*3)
fitted=np.array([transform.apply(tuple(p)) for p in pts]); world=dict(zip(ids,fitted))
assert world[0][0]<world[92][0] and world[0][0]<world[77][0]
assert world[92][2]>destination[2] and world[77][2]<destination[2]
short=float(np.linalg.norm(world[0]-world[92])); long=float(np.linalg.norm(world[0]-world[77]))
assert short<long

def replace_panel(document):
    # Keep object identity, all other objects and routing bindings intact.
    oldpanel=document.scene.object(PID)
    cleaned=replace(document,scene=replace(document.scene,objects=tuple(o for o in document.scene.objects if o.object_id!=PID)),routes=tuple(r for r in document.routes if r.object_id!=PID))
    appended=append_partial_reviewed(cleaned,review,manifest['session'],[i['path'] for i in manifest['inputs']],source_offset=2720,
        name='Panel 8 | 299 LEDs | Dreieck unten, kurze Kante innen',transform=transform)
    newpanel=replace(appended.scene.objects[-1],object_id=PID)
    result=replace(document,scene=replace(document.scene,scans=appended.scene.scans,
        objects=tuple(newpanel if o.object_id==PID else o for o in document.scene.objects)))
    assert len(newpanel.leds)==296
    assert {b.local_index for b in newpanel.leds}==set(range(299))-{1,61,93}
    assert all(b.source_index==2720+b.local_index for b in newpanel.leds)
    before={b.source_index:p for b,p in document.scene.world_points() if b.led_id not in {l.led_id for l in oldpanel.leds}}
    after={b.source_index:p for b,p in result.scene.world_points() if b.source_index not in range(2720,3019)}
    assert before==after
    return result

new_active=replace_panel(active); new_draft=replace_panel(draft)
# Both documents must share exactly the same newly imported geometry and IDs.
assert new_active.scene.object(PID)==new_draft.scene.object(PID)
(OUT/'prepared-active.json').write_text(document_json(new_active),encoding='utf-8')
(OUT/'prepared-draft.json').write_text(document_json(new_draft),encoding='utf-8')
tables=json.loads((OUT/'before-tables.json').read_text())
uv=[r.split('\t') for r in tables['/project1/pixelblaze_mapper/effect_panel_uv'].splitlines()]
for i in range(299):
    p=world.get(i)
    values=rear_wall_uv(p[0],p[2]) if p is not None else (0.,0.)
    uv[2721+i]=[str(2720+i),'3','rear',*[repr(v) for v in (*values,*values)]]
(OUT/'prepared-uv.json').write_text(json.dumps(uv),encoding='utf-8')
report={'object_id':PID,'expected':299,'measured':296,'missing':[1,61,93],'views':5,
    'transform':asdict(transform),'center':destination.tolist(),'bounds':[fitted.min(0).tolist(),fitted.max(0).tolist()],
    'source_range':[2720,3018],'orientation':'triangle down; shorter leg left/inward as seen from front',
    'triangle_landmarks':{'tip':0,'short_leg_end':92,'long_leg_end':77},'short_leg_length':short,'long_leg_length':long,
    'scale_policy':'uniform fit to previous panel maximum span; previous center retained; no new physical dimensions supplied',
    'plane_rms':float(np.sqrt(np.mean(((pts-center)@normal)**2))*scale),
    'candidate_sha256':review['sha256'],'other_geometry_and_routing_unchanged':True}
(OUT/'fit-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(13,8),gridspec_kw={'width_ratios':[1,1]})
for o in new_active.scene.objects:
    bs={b.led_id for b in o.leds}
    p=np.array([p for b,p in new_active.scene.world_points() if b.led_id in bs])
    ax1.scatter(-p[:,2],p[:,0],s=3 if o.object_id!=PID else 9,c='#1591ba' if o.object_id==PID else '#999999')
ax1.set_aspect('equal');ax1.set_title('Front: Panel 8 ersetzt');ax1.set_xlabel('links / rechts');ax1.set_ylabel('Hoehe')
ax2.scatter(-fitted[:,2],fitted[:,0],c=ids,cmap='turbo',s=20)
for i,label in ((0,'Spitze unten'),(92,'kurze Kante innen'),(77,'lange Kante aussen'),(283,'283'),(298,'298')):
    p=world[i];ax2.annotate(label,(-p[2],p[0]),xytext=(4,5),textcoords='offset points',fontsize=9)
ax2.set_aspect('equal');ax2.set_title('Panel 8: 296 gemessen / 299 Adressen\nKurze Dreiecksseite links zur Schrankmitte');ax2.grid(alpha=.15)
fig.tight_layout();fig.savefig(OUT/'replacement-preview.png',dpi=150)
print(json.dumps(report))
