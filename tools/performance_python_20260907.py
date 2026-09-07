"""Bounded live Python profiler. Timer disables it even if the client disconnects."""
import json
import time
from pathlib import Path
from audit_20260907_capture import td
OUT=Path(__file__).resolve().parents[1]/'docs/implementation-2026-09-07/performance/python-profile.json'
START=r'''
import json,cProfile,builtins
assert not hasattr(builtins,'_codex_perf_profile')
builtins._codex_perf_profile=cProfile.Profile()
run("import builtins; builtins._codex_perf_profile.disable()",delayMilliSeconds=8000)
builtins._codex_perf_profile.enable()
result=json.dumps({'started':True})
'''
END=r'''
import json,pstats,builtins
builtins._codex_perf_profile.disable()
stats=pstats.Stats(builtins._codex_perf_profile)
rows=[{'file':key[0],'line':key[1],'function':key[2],'primitive_calls':v[0],
 'calls':v[1],'self_seconds':v[2],'cumulative_seconds':v[3]} for key,v in stats.stats.items()]
del builtins._codex_perf_profile
result=json.dumps(sorted(rows,key=lambda row:row['cumulative_seconds'],reverse=True))
'''
if __name__=='__main__':
    if OUT.exists(): raise ValueError('Evidence exists')
    td(START)
    try:
        time.sleep(10)
    finally:
        rows=td(END)
    OUT.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps(rows[:22],indent=2))
