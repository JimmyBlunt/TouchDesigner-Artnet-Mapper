"""Compare actual TD output in Perform Mode, restoring the prior UI mode."""
import argparse,json
from install_td_performance_program_20260912 import td,OUT
from td_program_benchmark_20260912 import run

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--seconds',type=float,default=45)
    p.add_argument('--frame-pacing',action='store_true',default=None)
    p.add_argument('--rate',type=int,default=30)
    p.add_argument('--worker-priority',choices=('normal','above_normal'))
    a=p.parse_args();path=OUT/(a.label+'-mode.json')
    if path.exists():raise ValueError('Evidence exists')
    before=td('import json\nresult=json.dumps(ui.performMode)')
    report={'before':before}
    try:
        report['during']=td('import json\nui.performMode=True\nresult=json.dumps(ui.performMode)')
        run(a.label,a.seconds,'BACK_PANEL_249',a.rate,a.frame_pacing,a.worker_priority)
    finally:
        report['restored']=td('import json\nui.performMode=%r\nresult=json.dumps(ui.performMode)'%before)
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
