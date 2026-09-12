"""Temporary live callback profiling over the loopback-only benchmark."""
import json
from pathlib import Path
from install_td_performance_program_20260912 import td
from performance_callbacks_20260907 import START
from td_program_benchmark_20260912 import run

OUT=Path(__file__).resolve().parents[1]/'docs/performance-program-20260912/td'

if __name__=='__main__':
    target=OUT/'callback-profile.json'
    if target.exists():raise ValueError('Evidence exists')
    originals=td(START.replace("import time as _perf_clock", "import time as _perf_clock\nimport cProfile as _perf_cprofile\n_perf_profiler=_perf_cprofile.Profile()").replace('return _perf_original(frame)','return _perf_profiler.runcall(_perf_original,frame)'))
    (OUT/'profile-callback-originals.json').write_text(json.dumps(originals,indent=2),encoding='utf-8')
    try:
        run('callback-profile-loopback',20,'BACK_PANEL_249',30)
        result=td(r'''import json,pstats,io
data={}
for path in %r:
 m=op(path).module;v=list(m._perf_samples);stream=io.StringIO()
 pstats.Stats(m._perf_profiler,stream=stream).sort_stats('cumulative').print_stats(35)
 data[path]={'count':len(v),'mean_ms':sum(v)/len(v) if v else None,'max_ms':max(v) if v else None,'profile':stream.getvalue()}
result=json.dumps(data)'''%list(originals))
        target.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
    finally:
        td('import json\noriginals=%r\nfor path,text in originals.items():op(path).text=text\nresult=json.dumps({"restored":list(originals)})'%originals)
