"""Aligned Show cells over unchanged selection buttons; cached read-only data."""
from functools import lru_cache
import json
from . import show_editor

COLUMNS=(('position','#',8,30),('name','NAME',48,180),('effect','EFFEKT',236,164),
         ('timing','DAUER',408,98),('transition','ÜBERGANG',514,104),
         ('coordinate_mode','MODUS',626,90),('gradient','VERLAUF',724,228))


@lru_cache(maxsize=4)
def rows(raw,recorded):
    document=json.loads(raw)
    output=show_editor.summary_rows(document)
    for index,cue in enumerate(document.get('cues',[])):
        if cue.get('id')==recorded:output[index]['timing']='Aufnahme …'
    return output


def cell_text(slot,column):
    import td
    owner=td.op('/project1/show_control')
    runtime=owner.op('editor_callbacks').module
    page=max(0,int(float(runtime._state('page','0') or 0)))
    recorded=runtime._state('record_cue','') if runtime._state('recording','0')=='1' else ''
    data=rows(owner.op('show_json').text,recorded)
    index=page*10+int(slot)
    return str(data[index].get(column,'')) if index<len(data) else ''


def cell_selected(slot):
    import td
    runtime=td.op('/project1/show_control/editor_callbacks').module
    return int(float(runtime._state('selected','-1') or -1)) == int(float(runtime._state('page','0') or 0))*10+int(slot)


def install(panel):
    from .build_release_ui import _label, _color
    from .release_ui_theme import remember_set, THEME
    head=panel.op('ed_list_head')
    if head is not None:remember_set(head,'display',False)
    for key,label,x,width in COLUMNS:
        heading=_label(panel,'release_v1_show_head_'+key,label,20+x,872,width,24,size=10)
        heading.par.textpaddingl=0;heading.par.textpaddingr=2
    count=0
    for slot in range(10):
        row=panel.op('ed_row_'+str(slot))
        if row is None:continue
        text=row.op('text')
        if text is not None:remember_set(text,'fontalpha',0)
        for key,label,x,width in COLUMNS:
            cell=_label(row,'release_v1_show_cell_'+key,'',x,0,width,24,size=11)
            _color(cell,'fontcolor',THEME['value'])
            for channel,normal,active in zip('rgb',THEME['value'],THEME['button']):
                getattr(cell.par,'fontcolor'+channel).expr="%r if __import__('pixelblaze_mapper.release_show_table',fromlist=['cell_selected']).cell_selected(%d) else %r"%(active,slot,normal)
            cell.par.textpaddingl=0;cell.par.textpaddingr=2;cell.par.wordwrap=False
            cell.par.text.expr="__import__('pixelblaze_mapper.release_show_table',fromlist=['cell_text']).cell_text(%d,%r)"%(slot,key)
            count+=1
    return count
