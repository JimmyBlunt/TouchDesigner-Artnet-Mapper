"""Profile every enabled frame callback during a reversible localhost run."""
import argparse
import json
import time
from install_td_performance_program_20260912 import td, OUT
from td_program_benchmark_20260912 import run

START = r'''
import json
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
originals={}
for node in op('/project1').findChildren():
 if str(node.type)!='execute' or node.bypass or not node.par.active.eval():continue
 events=[name for name,par in [('onFrameStart','framestart'),('onFrameEnd','frameend')] if getattr(node.par,par).eval()]
 if not events:continue
 originals[node.path]=node.text
 suffix='\nimport cProfile as _acp\nimport time as _act\n_ac_profiles={}\n_ac_samples={}\n'
 suffix+='def _ac_wrap(name,fn):\n p=_acp.Profile();_ac_profiles[name]=p;_ac_samples[name]=[]\n def wrapped(frame):\n  start=_act.perf_counter()\n  try:return p.runcall(fn,frame)\n  finally:_ac_samples[name].append((_act.perf_counter()-start)*1000)\n return wrapped\n'
 for event in events:suffix+='\n'+event+'=_ac_wrap('+repr(event)+','+event+')\n'
 node.text+=suffix
result=json.dumps(originals)
'''

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--idle',action='store_true')
    parser.add_argument('--label',default='all-callbacks-profile')
    args=parser.parse_args()
    if not args.label.replace('-','').isalnum():raise ValueError('Invalid label')
    target=OUT/(args.label+'.json')
    if target.exists():raise ValueError('Evidence already exists')
    originals=td(START)
    (OUT/(args.label+'-originals.json')).write_text(json.dumps(originals,indent=2),encoding='utf-8')
    try:
        if args.idle:time.sleep(20)
        else:run(args.label+'-loopback',20,'BACK_PANEL_249',30,frame_pacing=True)
        result=td(r'''import json,pstats,io
data={}
for path in %r:
 m=op(path).module
 for event,p in m._ac_profiles.items():
  v=m._ac_samples[event];stream=io.StringIO()
  pstats.Stats(p,stream=stream).sort_stats('cumulative').print_stats(25)
  data[path+'/'+event]={'count':len(v),'mean_ms':sum(v)/len(v) if v else 0,'max_ms':max(v) if v else 0,'profile':stream.getvalue()}
result=json.dumps(data)'''%list(originals))
        target.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({p:{k:v for k,v in d.items() if k!='profile'} for p,d in result.items()},indent=2))
    finally:
        td('import json\noriginals=%r\nfor path,source in originals.items():op(path).text=source\nresult=json.dumps({"restored":list(originals)})'%originals)
