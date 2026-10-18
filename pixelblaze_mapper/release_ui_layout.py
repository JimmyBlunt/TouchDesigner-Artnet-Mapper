"""Flat native labels, grouped surfaces and cached rounded control backgrounds."""
from .release_ui_theme import THEME, remember_set


def _node(parent,kind,name):
    import td
    result=parent.op(name)
    if result is None:result=parent.create(getattr(td,kind),name);result.name=name
    return result


def _set(node,**values):
    for name,value in values.items():
        par=getattr(node.par,name,None)
        if par is not None:par.val=value


def rounded_surface(width,height,color,radius=6):
    import td
    width,height=max(4,int(width)),max(4,int(height))
    rgb=tuple(round(max(0,min(1,x)),3) for x in color)
    key='shape_%d_%d_%s_%d'%(width,height,''.join('%02x'%round(c*255) for c in rgb),radius)
    owner=_node(td.op('/project1'),'baseCOMP','release_ui_assets')
    node=owner.op(key)
    if node is None:
        node=_node(owner,'rectangleTOP',key)
        geometry=surface_geometry(width,height,radius)
        _set(node,outputresolution='custom',**geometry,
             sizeunit='pixels',
             cornerradiusunit='pixels',fillcolorr=rgb[0],fillcolorg=rgb[1],fillcolorb=rgb[2],
             fillalpha=1,bgalpha=0,borderwidth=0,antialias=True)
    return node


def surface_geometry(width,height,radius):
    """Fit cached rasters within Non-Commercial limits at the same aspect ratio.

    COMP dimensions still use the requested size. Scaling radius and inset with
    the raster keeps their apparent size when that raster fills the panel.
    """
    scale=min(1.0,1280.0/max(width,height))
    raster_w=max(4,round(width*scale));raster_h=max(4,round(height*scale))
    return dict(resolutionw=raster_w,resolutionh=raster_h,
                sizex=raster_w-2*scale,sizey=raster_h-2*scale,cornerradius=radius*scale)


def _borderless(node):
    for side in ('leftborder','rightborder','topborder','bottomborder'):
        remember_set(node,side,'off')


def round_button(button):
    text=button.op('text')
    if text is None or not text.fetch('release_v1_stock_fill',False,search=False):return False
    normal=rounded_surface(button.par.w.eval(),button.par.h.eval(),THEME['surface'])
    hover=rounded_surface(button.par.w.eval(),button.par.h.eval(),tuple(c+.045 for c in THEME['surface']))
    pressed=rounded_surface(button.par.w.eval(),button.par.h.eval(),THEME['border'])
    remember_set(button,'top',normal.path)
    button.par.top.expr='%r if me.panel.lselect or me.par.value0 else (%r if me.panel.rollover else %r)'%(pressed.path,hover.path,normal.path)
    remember_set(button,'bgalpha',0);remember_set(text,'bgalpha',0);_borderless(text)
    return True


def round_field(field):
    text=field.op('text')
    if text is None or not text.fetch('release_v1_field_skin',False,search=False):return False
    normal=rounded_surface(field.par.w.eval(),field.par.h.eval(),THEME['surface'])
    focused=rounded_surface(field.par.w.eval(),field.par.h.eval(),THEME['border'])
    background=_node(field,'selectTOP','release_v1_round_background')
    background.par.top.expr='%r if op("i")["focus"] else %r'%(focused.path,normal.path)
    composite=_node(field,'compositeTOP','release_v1_round_display')
    composite.par.operand='over'
    composite.inputConnectors[0].connect(text)
    composite.inputConnectors[1].connect(background)
    remember_set(text,'bgalpha',0);remember_set(field,'bgalpha',0);remember_set(field,'top',composite.path);_borderless(field);_borderless(text)
    remember_set(text,'positionx',6)
    remember_set(text,'positionunit','pixels')
    return True


# Zones use the existing bottom-left native coordinates; controls are never moved.
ZONES={
    'router':[(12,280,-24,320),(12,54,-24,220)],
    'show':[(10,302,-20,650),(10,16,-20,272)],
    'scan':[(10,470,-20,300),(10,102,-20,356)],
    'ports':[(10,550,-20,222),(10,285,-20,250),(10,75,-20,110)],
    'layout':[(10,365,-20,450),(10,45,-20,300)],
}


def apply(panel,screen):
    counts={'flat_labels':0,'round_buttons':0,'round_fields':0}
    # Flatten direct labels only; stateful custom widgets retain their own skins.
    for child in list(panel.children):
        if child.name.startswith('release_v1_'):continue
        if child.type=='text' and getattr(child,'isCOMP',False):
            remember_set(child,'bgalpha',0);_borderless(child);counts['flat_labels']+=1
        elif child.type=='button':counts['round_buttons']+=int(round_button(child))
        elif child.type=='field':counts['round_fields']+=int(round_field(child))
    height=panel.fetch('release_v1_base_height',int(panel.par.h),search=False)
    zones=ZONES.get(screen['key'],[(10,70,-20,max(80,height-170))])
    if screen.get('embedded'):zones=[]
    for index,(x,y,offset,h) in enumerate(zones):
        w=int(panel.par.w)+offset
        shade=tuple(min(1,c+.014) for c in THEME['background'])
        bg=rounded_surface(w,h,shade,radius=8)
        group=_node(panel,'containerCOMP','release_v1_group_'+str(index))
        _set(group,x=x,y=y,w=w,h=h,hmode='fixed',vmode='fixed',layer=-100,
             bgalpha=0,top=bg.path,clickthrough=True,enable=False)
    return counts
