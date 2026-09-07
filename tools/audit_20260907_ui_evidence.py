"""Audit-only snapshots/restoration around reversible UI parameter checks.

Never saves a TOE or starts an output. Restoration requires an existing before
snapshot and only restores the eight material controls tested by this audit.
"""
import json
import sys
from audit_20260907_capture import td, OUT

READ = r'''
import json
c=op('/project1/madmapper_player_controls')
keys=('Speed','Scale','Width','Focusx','Focusy','Framezoom','Intensity','Contrast')
states=('/project1/material_state_table','/project1/madmapper_library/material_parameter_state')
nodes=('/project1/madmapper_material_player','/project1/madmapper_library/live_preview','/project1/material_gradient_player','/project1/effect_sample_uv')
uniforms={}
for path in nodes:
 n=op(path)
 if n is not None:
  uniforms[path]={p.name:{'value':str(p.eval()),'expr':p.expr} for p in n.pars() if p.name.startswith('vec')}
result=json.dumps({'controls':{k:float(c.par[k].eval()) for k in keys},'states':{p:op(p).text for p in states},'uniforms':uniforms,'sender_enabled':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']})
'''

if __name__ == '__main__':
    label=sys.argv[1]
    if label == 'restore':
        before=json.loads((OUT/'ui-before.json').read_text(encoding='utf-8'))
        script="c=op('/project1/madmapper_player_controls')\n"
        for name,value in before['controls'].items():
            script+=f"c.par[{name!r}].val={value!r}\n"
        document=json.loads(before['states']['/project1/material_state_table'].splitlines()[1].split('\t',1)[1])
        settings=document['materials'][document['active_key']]['settings']
        script+="m=op('/project1/material_state_runtime').module\n"
        script+=f"assert m.STORE.active_key == {document['active_key']!r}\n"
        script+=f"m.STORE.set_active_settings(m.MaterialSettings.from_dict({settings!r}),m._now())\nm._persist()\n"
        script+="import json\nresult=json.dumps('restored eight tested material controls; no TOE save or output start')"
        print(td(script))
    else:
        result=td(READ)
        (OUT/f'ui-{label}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'label':label,'controls':result['controls'],'sender_enabled':result['sender_enabled']},indent=2))
