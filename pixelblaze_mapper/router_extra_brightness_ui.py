"""Compact extra-controller brightness editor; no sender restart or routing edit."""
import math

def parse_brightness(text):
    value=float(str(text).strip().replace(',', '.'))
    if not math.isfinite(value) or not 0<=value<=1:
        raise ValueError('Helligkeit muss zwischen 0 und 1 liegen')
    return value

def extras(owner):
    t=owner.op('controller_config')
    return [(str(t[i,'name']),i) for i in range(1,t.numRows) if str(t[i,'name']) not in ('WS2812_NODE','APA102_ESP')]

def refresh(owner, step=0):
    entries=extras(owner); canvas=owner.op('ui_panel')
    if not entries:
        canvas.op('extra_controller_label').par.text='Keine weiteren Controller'
        owner.store('extra_brightness_target',None)
        return
    old=owner.fetch('extra_brightness_target',None)
    pos=next((i for i,(name,_) in enumerate(entries) if name==old),0)
    pos=(pos+step)%len(entries); name,row=entries[pos]; t=owner.op('controller_config')
    owner.store('extra_brightness_target',name)
    owner.store('extra_brightness_ip',str(t[row,'target_ip']))
    canvas.op('extra_controller_label').par.text=f'{name} | {t[row,"target_ip"]} | U{t[row,"start_universe"]} | {pos+1}/{len(entries)}'
    canvas.op('extra_brightness/string').text=str(t[row,'brightness'])
    canvas.op('extra_brightness_status').par.text=f'Aktiv: {float(t[row,"brightness"])*100:g} %'

def apply(owner):
    canvas=owner.op('ui_panel')
    try:
        name=owner.fetch('extra_brightness_target',None)
        row=next((row for found,row in extras(owner) if found==name),None)
        if row is None: raise ValueError('Controller entfernt; zuerst neu laden')
        t=owner.op('controller_config')
        if str(t[row,'target_ip'])!=owner.fetch('extra_brightness_ip',None):
            raise ValueError('Controller geaendert; zuerst neu laden')
        value=parse_brightness(canvas.op('extra_brightness/string')[0,0])
        previous=str(t[row,'brightness'])
        # One DAT cell only. The compiled sender cache keys include config text.
        try:
            t[row,'brightness']=str(value)
            assert float(t[row,'brightness'])==value
        except:
            t[row,'brightness']=previous
            raise
        canvas.op('extra_brightness_status').par.text=f'Aktiv: {value*100:g} %'
        owner.store('extra_brightness_last_apply',{'controller':name,'value':value})
        owner.op('ui_callbacks').module._set_status(f'{name}: Helligkeit {value*100:g}% live gesetzt; Sender unveraendert')
        return True
    except Exception as error:
        canvas.op('extra_brightness_status').par.text='FEHLER: '+str(error)
        return False

def install(owner, helpers):
    label,field,button=helpers['_label'],helpers['_field'],helpers['_button']
    get=helpers['_get_or_create']; settext=helpers['_replace_dat_text']
    c=owner.op('ui_panel')
    for name in ('firmware_note','advanced'):
        if c.op(name): c.op(name).par.display=False
    label(c,'extra_controller_label','Weitere Controller',24,378,1050,22,size=12)
    label(c,'extra_brightness_label','Helligkeit 0..1 (0,3 = 30%)',24,338,280,34,size=12)
    field(c,'extra_brightness','',304,338,130,34)
    label(c,'extra_brightness_status','',900,338,256,34,size=12)
    for suffix,title,x,w,action in (
        ('apply','HELLIGKEIT LIVE SETZEN',444,240,'apply(parent())'),
        ('refresh','LADEN',694,86,'refresh(parent())'),
        ('prev','<',790,44,'refresh(parent(), -1)'),
        ('next','>',844,44,'refresh(parent(), 1)')):
        b=button(c,'extra_brightness_'+suffix,title,x,338,w,(.10,.38,.42))
        b.par.h=34
        cb=get(owner,helpers['panelexecuteDAT'],'extra_brightness_click_'+suffix)
        cb.par.active=False;cb.par.fromop=b.path;cb.par.panels=b.path
        cb.par.panelvalue='lselect';cb.par.offtoon=True
        cb.par.ontooff=False;cb.par.whileon=False;cb.par.whileoff=False;cb.par.valuechange=False
        settext(cb,'def onOffToOn(panelValue):\n    from pixelblaze_mapper import router_extra_brightness_ui as ui\n    ui.'+action+'\n    return\n')
        cb.par.active=True
    refresh(owner)
