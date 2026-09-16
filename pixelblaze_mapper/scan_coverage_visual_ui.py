"""Read-only camera-view coverage map; no camera, output or scan-scope actions."""
from pathlib import Path
from dataclasses import replace
from .scan_session import ScanSession
from .scan_workflow_ux import view_paths, compact_indices
from .scan_library_ui import style_button

OWNER = '/project1/guided_scan'
_images = {}
COLORS = {'good': (.10, .66, .65), 'weak': (1., .80, .15),
          'unreconstructed': (1., .29, .10), 'neighbor': (.88, .36, 1.)}


def image_for(view, width=560, height=560):
    """Top-origin square normalized camera coordinates (including sensor padding)."""
    import numpy as np
    image = np.empty((height, width, 4), dtype=np.float32)
    image[:] = (.014, .025, .04, 1)
    image[::max(1,height//8),:,:3] = (.045,.065,.085)
    image[:,::max(1,width//8),:3] = (.045,.065,.085)
    if not view:
        return image
    def xy(point):
        return round(point['u']*(width-1)), round(point['v']*(height-1))
    def dot(point, color, radius, ring=False):
        x,y=xy(point)
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                distance=dx*dx+dy*dy
                if (distance <= radius*radius and (not ring or distance >= (radius-2)**2)
                        and 0<=x+dx<width and 0<=y+dy<height):
                    image[y+dy,x+dx,:3]=color
    for group in view.get('neighbors',[]):
        a,b=group['before'],group['after']
        x1,y1=xy(a);x2,y2=xy(b)
        steps=max(abs(x2-x1),abs(y2-y1),1)+1
        for i in range(steps):
            if i%8<4:
                x=round(x1+(x2-x1)*i/max(1,steps-1));y=round(y1+(y2-y1)*i/max(1,steps-1))
                if 0<=x<width and 0<=y<height:image[y,x,:3]=COLORS['neighbor']
        dot(a,COLORS['neighbor'],9,True);dot(b,COLORS['neighbor'],9,True)
    for status in ('good','weak','unreconstructed'):
        for point in view.get('points',[]):
            if point['status']==status:
                dot(point,COLORS[status],2 if status=='good' else 4)
                if status=='unreconstructed':dot(point,COLORS[status],7,True)
    return image


def _view(owner):
    data=owner.fetch('coverage_visual_data',{}) or {}
    views=data.get('views',[])
    index=max(0,min(int(owner.fetch('coverage_visual_index',0)),max(0,len(views)-1)))
    return data,index,views[index] if views else None


def cook(owner,script):
    import numpy as np
    data,index,view=_view(owner)
    key=(owner.fetch('coverage_visual_revision',0),index)
    cached=_images.get(owner.path)
    if cached is None or cached[0]!=key:
        # TOP row zero is the bottom, unlike the detector's image coordinates.
        cached=(key,np.ascontiguousarray(image_for(view)[::-1]))
        _images[owner.path]=cached
    script.copyNumpyArray(cached[1])


def render(owner):
    data,index,view=_view(owner)
    p=owner.op('coverage_visual_panel')
    if not view:
        p.op('summary').par.text='Noch keine gueltigen gespeicherten Ansichten.'
        for name in ('view_name', 'detail'):
            p.op(name).par.text=''
        p.op('legend_good').par.text='TUERKIS: mindestens 3 Ansichten'
        p.op('legend_weak').par.text='GELB: weniger als 3 Ansichten'
        p.op('footer').par.text='Abgeschlossene Aufnahmen der aktuellen Sitzung auswaehlen, dann REFRESH.'
        for name in ('previous', 'next', 'best'):
            style_button(p.op('btn_'+name),enabled=False)
        return
    known=data.get('reconstructed_count') if data.get('has_candidate') else None
    result=('%s/%s in 3D' % (known,data['total'])) if known is not None else '3D noch nicht berechnet'
    p.op('summary').par.text=(('%s | %d ohne 3D | %d nie erkannt' % (
        result,len(data['unreconstructed_ids']),len(data['never_seen_ids']))) if known is not None else
        '%s | %d/%d erkannt | %d nie erkannt' % (
            result,data['total']-len(data['never_seen_ids']),data['total'],len(data['never_seen_ids'])))
    p.op('view_name').par.text='ANSICHT %d / %d | BLICKRICHTUNG DER GESPEICHERTEN AUFNAHME' % (index+1,len(data['views']))
    p.op('legend_good').par.text=('TUERKIS: 3D, mindestens 3 Ansichten' if known is not None
                                 else 'TUERKIS: mindestens 3 Ansichten')
    p.op('legend_weak').par.text=('GELB: 3D, weniger als 3 Ansichten' if known is not None
                                 else 'GELB: weniger als 3 Ansichten')
    groups=view.get('neighbors',[])
    hints=[]
    for group in groups:
        hints.append('%s: Nachbarn %s / %s' % (compact_indices(group['missing_ids']),
                                             group['before']['id'],group['after']['id']))
    p.op('detail').par.text=('NIE ERKANNT (Scanindizes ab 0):\n%s\n\n'
        '%d orange Punkte in dieser Ansicht\n'
        '%d nie erkannte LEDs mit Nachbarhinweis\n\n'
        'Violett zeigt gemessene Nachbarn, NICHT die Position fehlender LEDs. '
        'Verkabelung kann die Richtung wechseln.\n\n%s') % (
            compact_indices(data['never_seen_ids']) or 'keine',
            view['visible_unreconstructed'],view['neighbor_missing_count'],
            '\n'.join(hints[:8]) or 'Keine verlaesslichen Nachbarpaare in dieser Ansicht.')
    unlocated=data.get('unlocated_count',len(data['never_seen_ids']))
    guidance=('Orange Bereiche aus weiteren Blickwinkeln aufnehmen, mit gut sichtbaren gemeinsamen LEDs. '
              if known is not None else
              'Gelb bedeutet: in weniger als 3 Ansichten erkannt. 3D noch nicht berechnet. ')
    p.op('footer').par.text=('Gespeicherte Messpunkte, kein Kamerafoto. Oben im Bild bleibt oben. '
        + guidance + '%d nie erkannte LEDs sind in keiner Ansicht eingrenzbar. REFRESH nach neuen Aufnahmen.' % unlocated)
    style_button(p.op('btn_previous'),enabled=index>0)
    style_button(p.op('btn_next'),enabled=index+1<len(data['views']))
    style_button(p.op('btn_best'),enabled=True)


def _store_data(owner, data):
    owner.store('coverage_visual_data',data)
    owner.store('coverage_visual_revision',owner.fetch('coverage_visual_revision',0)+1)
    owner.store('coverage_visual_index',0)


def _cook_image(owner):
    # Storage changes do not reliably invalidate an already cooked Script TOP.
    preview=owner.op('coverage_visual_image')
    if preview is not None:
        preview.cook(force=True)


def act(op,command):
    owner=op(OWNER)
    try:
        if command in ('open','refresh'):
            from .scan_coverage_visual import build_data
            session=ScanSession.from_dict(owner.fetch('session'))
            if owner.fetch('standalone_capture',None) is not None:
                # A partial next scan must not hide already completed full views.
                # Expand only the read-only coverage snapshot, never the scan plan.
                session=replace(session,selected_ids=tuple(t.led_id for t in session.targets),
                                anchor_ids=())
            expected=[t.source_index for t in session.targets if t.led_id in session.capture_ids]
            paths=view_paths(owner.op('ui_panel/views/string').text)
            status=owner.fetch('offline_status',{}) or {}
            candidate=(status.get('candidate') if status.get('state')=='review_required'
                       and status.get('session_id')==session.session_id else None)
            data=build_data(paths,expected,candidate,session=session)
            _store_data(owner,data)
            best=next((i for i,v in enumerate(data['views']) if v['path']==data['best_view']),0)
            owner.store('coverage_visual_index',best)
        elif command in ('previous','next'):
            data,index,view=_view(owner)
            owner.store('coverage_visual_index',max(0,min(index+(-1 if command=='previous' else 1),len(data.get('views',[]))-1)))
        elif command=='best':
            data,index,view=_view(owner)
            owner.store('coverage_visual_index',next((i for i,v in enumerate(data['views']) if v['path']==data['best_view']),0))
        elif command=='back':
            owner.op('ui_panel').openViewer()
            return True
        else:
            raise ValueError('Unknown coverage-map action')
        render(owner)
        _cook_image(owner)
        if command=='open':owner.op('coverage_visual_panel').openViewer()
        return True
    except Exception as error:
        _store_data(owner,{})
        render(owner)
        _cook_image(owner)
        owner.op('coverage_visual_panel/footer').par.text='Anzeige nicht verfuegbar: '+str(error)
        if command=='open':owner.op('coverage_visual_panel').openViewer()
        return False


def install(ns):
    import td
    scope=dict(ns,__name__='coverage_visual_helpers')
    path=Path(__file__).resolve().parent/'build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
    node,panel,text,button,click=(scope[k] for k in ('_node','_panel','_text','_button','_click'))
    owner=ns['op'](OWNER)
    p=panel(node(owner,td.containerCOMP,'coverage_visual_panel'),0,0,960,820,10)
    p.viewer=True
    text(p,'title','FEHLENDE BEREICHE | GESPEICHERTE KAMERAANSICHTEN',20,772,920,34,19)
    text(p,'summary','Ansichten mit OPEN laden.',20,742,920,28,14)
    text(p,'view_name','',20,710,920,28,12)
    viewport=panel(node(p,td.containerCOMP,'image'),20,145,560,560,20)
    callback=node(owner,td.textDAT,'coverage_visual_callbacks')
    callback.text="def onCook(scriptOp):\n    from pixelblaze_mapper.scan_coverage_visual_ui import cook\n    cook(op('/project1/guided_scan'),scriptOp)\n"
    preview=node(owner,td.scriptTOP,'coverage_visual_image')
    preview.par.callbacks=callback.path
    viewport.par.top=preview.path
    for name,label,y,color in (
            ('good','TUERKIS: 3D, mindestens 3 Ansichten',656,COLORS['good']),
            ('weak','GELB: 3D, weniger als 3 Ansichten',610,COLORS['weak']),
            ('missing','ORANGE: erkannt, aber noch kein 3D',564,COLORS['unreconstructed']),
            ('neighbors','VIOLETT: Nachbarstellen fuer Luecken',518,COLORS['neighbor'])):
        text(p,'legend_'+name,label,600,y,340,42,12,color)
    text(p,'detail','',600,175,340,328,12)
    text(p,'footer','Nur Anzeige; kein Scan und keine LED-Ausgabe.',20,12,920,72,12)
    expression="__import__('pixelblaze_mapper.scan_coverage_visual_ui',fromlist=['act']).act(op,%r)"
    for name,label,x,width in (('previous','VORHERIGE ANSICHT',20,190),('next','NAECHSTE ANSICHT',220,190),
                               ('best','MEISTE HINWEISE',420,180),('refresh','REFRESH',610,120),('back','ZURUECK ZUM SCAN',740,200)):
        b=button(p,'btn_'+name,label,x,98,width)
        style_button(b,'primary' if name=='best' else 'secondary')
        click(owner,'click_coverage_visual_'+name,b,expression%name)
    b=button(owner.op('ui_panel'),'btn_coverage_visual','FEHLENDE BEREICHE ANZEIGEN',860,689,280)
    style_button(b,'primary')
    click(owner,'click_open_coverage_visual',b,expression%'open')
    review=owner.op('review_panel')
    if review is not None:
        review.op('btn_review_advanced').par.w=620
        b=button(review,'btn_coverage_visual','FEHLENDE BEREICHE',660,375,320)
        style_button(b,'primary')
        click(owner,'click_review_coverage_visual',b,expression%'open')
    return p.path
