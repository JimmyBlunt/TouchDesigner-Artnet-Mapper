
import json
from pixelblaze_mapper import guided_scan_live as live, scan_workflow_ux, scan_coverage
p=op(live.OWNER)
live.assert_outputs_off(op)
settings={'name':'BACK_PANEL2_738_249','target':'10.0.0.249','interface':'10.0.0.125','universe':122,'count':738,'rate':30,'order':'RGB'}
state=live.stage_standalone(op,settings)
p.op('ui_panel/workspace/string').text='C:\\Users\\jbhtz\\OneDrive\\Desktop\\Pictures\\Documents\\ChatGPT\\LED-Touchdesigner-Controller\\PixelblazeMapper\\Scans\\back_panel2_738_249_20260910_220957'
p.op('ui_panel/source_ids/string').text='0,170,340,510,737'
for key in ['offline_status','result_review','coverage_summary','registration_context','registration_proposal']:
    p.store(key,{})
p.store('manifest_view_paths',[])
summary=live.prepare(op)
scan_workflow_ux.refresh(p)
scan_coverage._last_key=None
scan_coverage.refresh(op)
result=json.dumps({'summary':summary,'plan':p.fetch('capture_plan'),'session':p.fetch('session'),'settings':settings})
