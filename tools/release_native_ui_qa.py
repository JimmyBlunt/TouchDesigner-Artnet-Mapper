"""Run inside TouchDesigner after install; exercises help only, never output actions."""
import json
from pathlib import Path
from unittest.mock import patch
from pixelblaze_mapper import build_release_ui as release


def run(capture=False):
    import td
    root=Path(td.project.folder)
    folder=root/'docs/release-v1.0.0'
    (folder/'screenshots').mkdir(parents=True,exist_ok=True)
    report=[]
    for screen in release.load_catalog():
        if not screen.get('target'): continue
        panel=td.op(screen['target'])
        result={'key':screen['key'],'target':screen['target'],'checks':{},'errors':[]}
        try:
            panel.store('release_v1_pinned',False)
            tip=panel.op('release_v1_tooltip')
            hover=panel.op('release_v1_info_hover').module
            hover.onOffToOn(None)
            result['checks']['info_hover']=bool(tip.par.display) and screen['summary'] in str(tip.par.text)
            hover.onOnToOff(None)
            result['checks']['info_leave']=not bool(tip.par.display)
            click=panel.op('release_v1_info_click').module
            click.onOffToOn(None);hover.onOnToOff(None)
            result['checks']['info_pin']=bool(tip.par.display)
            click.onOffToOn(None)
            result['checks']['info_close']=not bool(tip.par.display)
            with patch.object(release.webbrowser,'open',return_value=True) as browser:
                panel.op('release_v1_howto_click').module.onOffToOn(None)
                result['checks']['howto_link']=browser.call_count==1 and browser.call_args.args[0].endswith(screen['howto'])
            fields=[]
            for index,(name,hint) in enumerate(screen.get('fields',{}).items()):
                callback=panel.op('release_v1_field_'+str(index)).module
                callback.onOffToOn(None)
                fields.append(bool(tip.par.display) and str(hint['example']) in str(tip.par.text))
                callback.onOnToOff(None)
            result['checks']['field_hovers']=all(fields)
            result['field_count']=len(fields)
            result['checks']['unique_help_buttons']=len([n for n in panel.children if n.type=='button' and n.name.startswith(('release_v1_info','release_v1_howto'))])==2
            result['checks']['font_file_resolves']=Path(str(panel.op('release_v1_bar').par.fontfile)).is_file()
            result['checks']['help_inside_panel']=all(0<=int(panel.op(name).par.y) and int(panel.op(name).par.y)+int(panel.op(name).par.h)<=int(panel.par.h) for name in ('release_v1_info','release_v1_howto'))
            result['checks']['help_dat_errors']=not any(n.errors() for n in panel.children if n.name.startswith('release_v1_'))
        except Exception as error:
            result['errors'].append(str(error))
        result['passed']=not result['errors'] and all(result['checks'].values())
        report.append(result)
    (folder/'qa').mkdir(exist_ok=True)
    (folder/'qa/native-ui-help-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'screens':len(report),'fields':sum(r.get('field_count',0) for r in report),
            'failed':[r for r in report if not r['passed']]}


def prepare_captures():
    """Call finish_captures on a later frame so GPU text glyphs have rendered."""
    import td
    old=td.op('/project1/release_capture_batch')
    if old is not None:old.destroy()
    capture=td.op('/project1').create(td.baseCOMP,'release_capture_batch');capture.name='release_capture_batch'
    for screen in release.load_catalog():
        if not screen.get('target'):continue
        panel=td.op(screen['target']);top=capture.create(td.opviewerTOP,screen['key']);top.name=screen['key']
        top.par.allowpanel=False;top.par.outputresolution='custom';top.par.opviewer=panel.path
        top.par.resolutionw=int(panel.par.w);top.par.resolutionh=int(panel.par.h);top.cook(force=True)
    return len(capture.children)


def finish_captures():
    import td
    capture=td.op('/project1/release_capture_batch')
    folder=Path(td.project.folder)/'docs/release-v1.0.0/screenshots';folder.mkdir(parents=True,exist_ok=True)
    for top in capture.children:
        top.cook(force=True);top.save(str(folder/(top.name+'.png')))
    count=len(capture.children);capture.destroy();return count


if __name__=='__main__': print(json.dumps(run()))
