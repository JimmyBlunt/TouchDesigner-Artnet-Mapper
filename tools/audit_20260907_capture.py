"""Read-only evidence collection for the 2026-09-07 audit; never starts output."""
import json
import time
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'audit-2026-09-07'

def td(script):
    request = urllib.request.Request('http://127.0.0.1:9981/api/td/server/exec',
        json.dumps({'script': script}).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        value = json.load(response)
    if not value.get('success'):
        raise RuntimeError(value)
    result = value['data']['result']
    return json.loads(result) if isinstance(result, str) else result

SNAPSHOT = r'''
import json
from pixelblaze_mapper.dialog_contracts import DIALOGS
def table(path):
    n=op(path)
    return n.text if n is not None else None
def values(n):
    out={}
    for p in n.customPars:
        try: out[p.name]={'value':str(p.eval()),'mode':str(p.mode),'expression':p.expr}
        except Exception as e: out[p.name]={'error':str(e)}
    return out
dialogs=[]
for d in DIALOGS:
    n=op(d.target)
    entry={'key':d.key,'label':d.label,'target':d.target,'exists':n is not None}
    if n is not None:
        entry['errors']=list(n.errors(recurse=True))
        entry['parameters']=values(n)
        children=n.findChildren(maxDepth=3) if n.isCOMP else []
        inventory=[]
        for c in children:
            if c.type not in ('button','slider','field','text','container','parameter'): continue
            item={'node':str(c.path),'type':str(c.type)}
            for key in ('label','text','value0','display','enable','x','y','w','h','help'):
                p=c.par[key]
                if p is not None:
                    try: item[key]=str(p.eval())
                    except Exception: pass
            inventory.append(item)
        entry['inventory']=inventory
    dialogs.append(entry)
paths=['/project1/multi_controller_output/controller_config','/project1/multi_controller_output/segment_config','/project1/multi_controller_output/gico_port_config/port_config','/project1/multi_controller_output/gico_port_config/global_config','/project1/material_browser/unified_state','/project1/madmapper_library/browser_state','/project1/material_state_table']
nodes=[]
for path in ['/project1/visual_source_switch','/project1/material_gradient_player','/project1/res1','/project1/madmapper_library/live_preview','/project1/madmapper_material_player','/project1/effect_sample_uv','/project1/math1']:
    n=op(path)
    if n is None: continue
    nodes.append({'node':path,'inputs':[str(i.path) for i in n.inputs],'errors':list(n.errors()),'cpu_ms':float(n.cpuCookTime),'total_cooks':int(n.totalCooks)})
result=json.dumps({'file':project.name,'folder':project.folder,'target_fps':project.cookRate,'dialogs':dialogs,'tables':{p:table(p) for p in paths},'controls':values(op('/project1/madmapper_player_controls')),'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status(),'nodes':nodes})
'''

SAMPLE = r'''
import json
nodes=[]
for path in ['/project1/material_gradient_player','/project1/madmapper_library/live_preview','/project1/madmapper_library/hover_preview','/project1/res1','/project1/effect_sample_uv','/project1/math1']:
 n=op(path)
 if n is not None: nodes.append({'node':path,'cooks':int(n.totalCooks),'cpu_ms':float(n.cpuCookTime)})
result=json.dumps({'seconds':float(absTime.seconds),'frame':int(absTime.frame),'nodes':nodes,'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()})
'''

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    baseline=td(SNAPSHOT)
    label=sys.argv[1] if len(sys.argv)>1 else 'baseline'
    if label not in ('baseline','final'):
        raise ValueError('snapshot label must be baseline or final')
    (OUT/f'live-{label}.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Baseline saved:', baseline['file'], 'dialogs:',len(baseline['dialogs']),flush=True)
    if label=='final':
        raise SystemExit(0)
    samples=[]
    for i in range(16):
        samples.append(td(SAMPLE))
        if i<15: time.sleep(2)
    (OUT/'timing-samples.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    duration=samples[-1]['seconds']-samples[0]['seconds']
    rates={b['node']:(b['cooks']-a['cooks'])/duration for a,b in zip(samples[0]['nodes'],samples[-1]['nodes'])}
    print(json.dumps({'duration':duration,'project_frames_per_second':(samples[-1]['frame']-samples[0]['frame'])/duration,'cook_rates':rates,'sender_enabled':samples[-1]['sender']['enabled']},indent=2))
