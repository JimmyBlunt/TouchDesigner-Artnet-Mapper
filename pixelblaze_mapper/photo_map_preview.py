"""Photo-only projection of the active installation. Never writes mapping/output.

Rear F00..09 are photo slots in reading order, not consecutive source blocks.
Side quads are an adjustable photo calibration, independent of measured 3D size.
"""
import numpy as np

SIDE_RANGES = ((517, 786, 'Upper'), (0, 517, 'Middle'), (786, 1184, 'Lower'))
# TL, TR, BL, BR, pixel positions in the existing 960-square fitted photograph.
SIDE_DEFAULTS = {
    'Upper': ((580,39),(660,67),(580,94),(660,122)),
    'Middle': ((570,251),(689,280),(570,350),(689,387)),
    'Lower': ((570,535),(658,560),(570,659),(658,684)),
}
_CACHE = {}


def homography(uv, corners):
    """Project normalized face positions through a true planar homography."""
    a, b = [], []
    for (u,v),(x,y) in zip(((0,1),(1,1),(0,0),(1,0)), corners):
        a.extend(((u,v,1,0,0,0,-u*x,-v*x), (0,0,0,u,v,1,-u*y,-v*y)))
        b.extend((x,y))
    h = np.append(np.linalg.solve(a,b),1).reshape(3,3)
    q = np.column_stack((uv,np.ones(len(uv)))) @ h.T
    if np.any(np.abs(q[:,2]) < 1e-10):
        raise ValueError('Photo calibration crosses the projection horizon')
    return q[:,:2] / q[:,2,None]


def project(points, rear_quads, side_quads, inactive=()):
    """Return photo XY and visible mask, retaining exact source/color ordering."""
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all():
        raise ValueError('Expected finite XYZ points')
    xy = np.zeros((len(p),2)); visible = np.ones(len(p),dtype=bool)
    for first,end in inactive:
        if not 0 <= first <= end < len(p): raise ValueError('Invalid inactive range')
        visible[first:end+1] = False
    for first,end,name in SIDE_RANGES:
        end=min(end,len(p))
        if first >= end: continue
        face=np.column_stack((-p[first:end,1],p[first:end,0]))
        span=np.ptp(face,axis=0)
        if np.any(span <= 0): raise ValueError('Degenerate side face')
        xy[first:end]=homography((face-face.min(axis=0))/span,side_quads[name])
    # World axes: X up; front-view horizontal is -Z. Assign by spatial slot,
    # not 256-LED assumptions, so measured 203-point scans stay true geometry.
    centers=np.array([.9,.7,.5,.3,.1])
    rear=p[1184:]
    if len(rear):
        rows=np.argmin(abs(rear[:,0,None]-centers),axis=1)
        cols=(rear[:,2] < .5).astype(int)
        for row in range(5):
            for col in range(2):
                indices=np.flatnonzero((rows==row)&(cols==col))+1184
                if not len(indices): continue
                center_z=.6 if col == 0 else .4
                uv=np.column_stack(((center_z+.084375-p[indices,2])/.16875,
                                    (p[indices,0]-centers[row]+.084375)/.16875))
                xy[indices]=homography(uv,rear_quads[row*2+col])
    return xy,visible


def cook(script):
    owner=script.parent(); src=script.inputs[0]
    m=owner.op('/project1/pixelblaze_mapper/map_active')
    router=owner.op('/project1/multi_controller_output')
    inactive=router.fetch('inactive_source_ranges',[])
    def corners(prefix):
        return [(float(getattr(owner.par,prefix+k+'x')),float(getattr(owner.par,prefix+k+'y')))
                for k in ('tl','tr','bl','br')]
    rear=[corners('F%02d'%i) for i in range(10)]
    side={name:corners('Photo'+name.lower()) for _,_,name in SIDE_RANGES}
    signature=(m.path,m.cookFrame,m.numRows,repr(rear),repr(side),repr(inactive))
    cached=_CACHE.get(owner.path)
    if not cached or cached[0] != signature:
        points=[[float(m[r,c]) for c in (1,2,3)] for r in range(1,m.numRows)]
        xy,visible=project(points,rear,side,inactive)
        _CACHE[owner.path]=(signature,xy,visible)
    _,xy,visible=_CACHE[owner.path]
    n=len(xy)
    if src.numSamples != n: raise ValueError('Photo map/color length mismatch')
    show_side=bool(owner.par.Showside); show_rear=bool(owner.par.Showrear)
    alpha=visible.astype(float)
    alpha[:1184]*=float(owner.par.Sideopacity)*show_side
    alpha[1184:]*=float(owner.par.Rearopacity)*show_rear
    alpha*=float(owner.par.Ledopacity)
    script.clear(); script.numSamples=n
    for name,vals in [('tx',2*xy[:,0]-1),('ty',2*xy[:,1]-1),('tz',np.zeros(n)),
                      ('r',src['r'].vals),('g',src['g'].vals),('b',src['b'].vals),('a',alpha)]:
        script.appendChan(name).vals=vals


def install(ns):
    """Non-destructive alternative render path. Old calibration network retained."""
    op=ns['op']; p=op('/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype')
    page=next((x for x in p.customPages if x.name=='Photo panels'),None) or p.appendCustomPage('Photo panels')
    for name,pixels in SIDE_DEFAULTS.items():
        for k,(x,y) in zip(('tl','tr','bl','br'),pixels):
            for axis,value in (('x',x/960),('y',1-y/960)):
                key='Photo'+name.lower()+k+axis
                if getattr(p.par,key,None) is None:
                    par=page.appendFloat(key,label=name+' '+k.upper()+' '+axis.upper())[0]
                    par.default=value; par.val=value
    def create(type_name,name):
        return p.op(name) or p.create(ns[type_name],name)
    cb=create('textDAT','photo_map_callbacks')
    cb.text='from pixelblaze_mapper.photo_map_preview import cook\ndef onCook(scriptOp):\n    cook(scriptOp)\n'
    data=create('scriptCHOP','photo_map_instances');data.par.callbacks=cb
    data.inputConnectors[0].connect(p.op('cal_source_instances'))
    camera=create('cameraCOMP','photo_map_camera');camera.par.tz=2;camera.par.projection='ortho';camera.par.orthowidth=2
    geo=p.op('photo_map_geo') or p.copy(p.op('tile_mesh_geo_00'),name='photo_map_geo')
    for key in ('rx','ry','rz','tx','ty','tz'): getattr(geo.par,key).val=0
    for key in ('sx','sy','sz'): getattr(geo.par,key).val=1
    geo.par.instanceop=data;geo.par.instancecolorop=data;geo.par.instancea='a'
    dot=geo.op('led_point')
    for key in ('radx','rady','radz'): getattr(dot.par,key).val=.0017
    render=create('renderTOP','photo_map_render');render.par.camera=camera;render.par.geometry=geo
    render.par.resolutionw=960;render.par.resolutionh=960
    leds=p.op('cal_leds')
    if not p.fetch('photo_map_previous_inputs',None):
        p.store('photo_map_previous_inputs',[x.path for x in leds.inputs])
    # Keep the old composite valid and available for a one-wire rollback.
    for i,path in enumerate(p.fetch('photo_map_previous_inputs')):
        leds.inputConnectors[i].connect(op(path))
    leds.cook(force=True)
    p.op('cal_over_background').inputConnectors[0].connect(render)
    data.cook(force=True);render.cook(force=True)
    p.store('photo_map_version',1)
    return {'instances':data.numSamples,'errors':list(data.errors())+list(render.errors()),
            'old_inputs':p.fetch('photo_map_previous_inputs'),'render':render.path}
