"""Build explicit coverage inventories from audit evidence, not pass claims."""
import csv
import json
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'docs'/'audit-2026-09-07'
baseline=json.loads((OUT/'live-baseline.json').read_text(encoding='utf-8'))
rows=[]
tested={'player_speed','player_scale','player_width','player_focusx','player_focusy','player_zoom','player_intensity','player_contrast'}
for dialog in baseline['dialogs']:
    for field in dialog.get('inventory',[]):
        name=field['node'].rsplit('/',1)[-1]
        test='READ_ONLY_INVENTORY; no individual interaction assertion'
        if '/madmapper_player_controls/ui_panel/' in field['node'] and name in tested:
            test='MOUSE_PARAMETER_PASS; effects/restore see UI_TESTS_DE.md'
        rows.append({'dialog':dialog['key'],'title':dialog['label'],'node':field['node'],'type':field['type'],
            'label':field.get('label',field.get('text','')),'value':field.get('value0',''),
            'display':field.get('display',''),'enabled':field.get('enable',''),'test':test})
with (OUT/'CONTROL_INVENTORY.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
summary={d['key']:{'label':d['label'],'inventory_nodes':len(d.get('inventory',[])),'custom_parameters':len(d.get('parameters',{}))} for d in baseline['dialogs']}
(OUT/'coverage-summary.json').write_text(json.dumps({'total_inventory_nodes':len(rows),'dialogs':summary},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'total_inventory_nodes':len(rows),'dialogs':summary},ensure_ascii=False,indent=2))

sequence=['before','speed','scale','width','focusx','focusy','zoom','intensity','contrast']
probes=[json.loads((OUT/f'ui-{label}.json').read_text(encoding='utf-8')) for label in sequence]
changes=[]
for label,prev,current in zip(sequence[1:],probes,probes[1:]):
    diff={key:{'before':value,'after':current['controls'][key]} for key,value in prev['controls'].items() if value!=current['controls'][key]}
    changes.append({'action':label,'changed':diff,'sender_enabled':current['sender_enabled']})
restored=json.loads((OUT/'ui-restored.json').read_text(encoding='utf-8'))
def state(snapshot):
    return json.loads(snapshot['states']['/project1/material_state_table'].splitlines()[1].split('\t',1)[1])
a,b=state(probes[0]),state(restored)
result={'changes':changes,'controls_restored':restored['controls']==probes[0]['controls'],
        'native_state_restored':restored['states']['/project1/madmapper_library/material_parameter_state']==probes[0]['states']['/project1/madmapper_library/material_parameter_state'],
        'active_identity_restored':a['active_key']==b['active_key'],
        'all_material_settings_restored':all(value['settings']==b['materials'][key]['settings'] for key,value in a['materials'].items()),
        'all_probe_senders_off':all(not p['sender_enabled'] for p in probes+[restored]),
        'phase_note':'Animation phase advances during running application; not rewound.'}
(OUT/'ui-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key!='changes'},indent=2))
