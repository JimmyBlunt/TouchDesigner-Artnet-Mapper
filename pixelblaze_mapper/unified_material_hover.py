"""One isolated animated hover renderer for imported material browser cards."""
import time

OWNER = '/project1/material_browser'


def stop(owner):
    active = owner.fetch('unified_hover_active',None)
    preview = owner.op('unified_hover_preview')
    if active:
        viewer = owner.op('unified_viewer_%d' % active['slot'])
        if viewer is not None and preview is not None and str(viewer.par.opviewer.eval()) == preview.path:
            viewer.par.opviewer = active['previous']
    owner.store('unified_hover_active',None)
    if preview is not None:
        preview.lock = True


def hover(op, slot, entered):
    owner = op(OWNER)
    slot = int(slot)
    active = owner.fetch('unified_hover_active',None)
    viewer = owner.op('unified_viewer_%d' % slot)
    button = owner.op('unified_card_%d' % slot)
    if not entered:
        if active and active['slot'] == slot and not any(bool(n.panel.rollover) for n in (viewer,button)):
            stop(owner)
        return
    key = button.fetch('item_key','')
    if active and active['key'] == key and active['slot'] == slot:
        return
    stop(owner)
    runtime = owner.op('unified_runtime').module
    item = next((i for i in runtime.ITEMS if i['key'] == key),None)
    if not item or item['source'] != 'imported' or not bool(viewer.par.display.eval()):
        return
    preview = owner.op('unified_hover_preview')
    shader = owner.op('unified_hover_shader')
    try:
        library = op('/project1/madmapper_library/runtime').module
        record = next((i for i in library._items if i['id'] == item['id']),None)
        if record is None:
            library.refresh(reset_page=False)
            record = next(i for i in library._items if i['id'] == item['id'])
        adaptation, values = library._parameter_context(record)
        if not adaptation.adaptable or not adaptation.shader:
            raise ValueError('; '.join(adaptation.reasons) or 'Keine unterstuetzte Shader-Vorschau')
        preview.lock = False
        library._configure_parameter_uniforms(preview,adaptation,values,publish_schema=False)
        if shader.text != adaptation.shader:
            shader.text = adaptation.shader
        owner.store('unified_hover_started',time.monotonic())
        preview.cook(force=True)
        errors = list(preview.errors())
        info = owner.op('unified_hover_info').text
        errors += [line for line in info.splitlines() if 'error:' in line.lower() or 'failed' in line.lower()]
        if errors:
            raise ValueError('; '.join(errors)[:350])
        previous = str(viewer.par.opviewer.eval())
        owner.store('unified_hover_active',dict(slot=slot,key=key,previous=previous))
        viewer.par.opviewer = preview.path
    except Exception as error:
        stop(owner)
        runtime._status('VORSCHAU NICHT VERFUEGBAR | %s | %s' % (item['label'],error),False)


def tick(op):
    owner = op(OWNER)
    active = owner.fetch('unified_hover_active',None)
    if not active:
        return
    viewer = owner.op('unified_viewer_%d' % active['slot'])
    button = owner.op('unified_card_%d' % active['slot'])
    if (button.fetch('item_key','') != active['key'] or not bool(viewer.par.display.eval())
            or not any(bool(n.panel.rollover) for n in (viewer,button))):
        stop(owner)


def install(op, types):
    owner = op(OWNER)
    def get(kind,name):
        return owner.op(name) or owner.create(types[kind],name)
    shader = get('textDAT','unified_hover_shader')
    preview = get('glslmultiTOP','unified_hover_preview')
    preview.lock = True
    preview.par.glslversion = 'glsl430'
    preview.par.mode = 'vertexpixel'
    preview.par.pixeldat = shader.path
    preview.par.outputresolution = 'custom'
    preview.par.resolutionw = 256
    preview.par.resolutionh = 256
    preview.par.vec.sequence.numBlocks = 3
    for block,(name,values) in enumerate((('uTDMaterial0',(0,4,.5,1)),
        ('uTDMaterial1',(.5,.5,0,0)),('uTDCoordinate',(0,2,5,.5)))):
        preview.par['vec%dname'%block] = name
        for suffix,value in zip('xyzw',values):
            preview.par['vec%dvalue%s'%(block,suffix)] = value
    preview.par.vec0valuex.expr = "absTime.seconds % 6.0"
    info = get('infoDAT','unified_hover_info')
    info.par.op = preview.path
    for slot in range(32):
        for prefix in ('unified_viewer_','unified_card_'):
            target = owner.op(prefix+str(slot))
            node = get('panelexecuteDAT','hover_'+prefix+str(slot))
            node.par.active = True
            node.par.fromop = target.path
            node.par.panels = target.path
            node.par.panelvalue = 'rollover'
            node.par.offtoon = True
            node.par.ontooff = True
            node.par.valuechange = False
            node.text = ('from pixelblaze_mapper.unified_material_hover import hover\n'
                'def onOffToOn(panelValue):\n    hover(op,%d,True)\n'
                'def onOnToOff(panelValue):\n    hover(op,%d,False)\n') % (slot,slot)
    watch = get('executeDAT','unified_hover_watch')
    watch.par.active = True
    watch.par.framestart = True
    watch.text = ('from pixelblaze_mapper.unified_material_hover import tick\n'
                  'def onFrameStart(frame):\n    tick(op)\n')
    return preview.path
