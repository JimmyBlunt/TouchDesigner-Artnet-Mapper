"""Real CHOP transfer parity in isolated nodes, without changing live simulation."""
import json
from pathlib import Path
from audit_20260907_capture import td

OUT=Path(__file__).resolve().parents[1]/'docs/implementation-2026-09-07/performance-next'
SCRIPT=r'''
import json,random,builtins,copy,time,hashlib,importlib
import numpy as np
from pixelblaze_mapper import legacy_script4_bulk as bulk
importlib.reload(bulk)
assert not op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()['enabled']
assert op('/native_bulk_acceptance_probe') is None
source=op('/project1/script4_callbacks').text
assert hashlib.sha256(source.encode()).hexdigest()==bulk.REFERENCE_SHA256
shared_rng_before=random.getstate()
b=op('/').create(baseCOMP,'native_bulk_acceptance_probe')
b.viewer=False
b.comment='Temporary isolated bulk transfer acceptance; no hardware outputs'
try:
    cb=b.create(textDAT,'no_auto_writes')
    cb.text='def onCook(scriptOp):\n    return\n'
    cb.viewer=False
    nodes=[]
    contexts=[]
    def load(seed):
        rng=random.Random(seed)
        imports=dict(vars(builtins))
        def isolated_import(name,*args,**kwargs):
            assert name=='random'
            return rng
        imports['__import__']=isolated_import
        ns={'__builtins__':imports}
        exec(compile(source,'<isolated captured callback>','exec'),ns)
        return ns,rng
    for name in ('reference','bulk'):
        n=b.create(scriptCHOP,name)
        n.par.callbacks=cb.path
        n.par.timeslice=False
        n.par.modoutsidecook=True
        n.viewer=False
        n.export=False
        n.cook(force=True)
        nodes.append(n)
        contexts.append(load(138))
    contexts[1][0]['onCook']=bulk.make_bulk_callback(contexts[1][0]['onCook'],source)
    for index,state in enumerate(contexts[0][0]['led_states']):
        state.update(active=True,brightness=(.010001,.5,1.)[index%3])
    contexts[1][0]['led_states'][:]=copy.deepcopy(contexts[0][0]['led_states'])
    identity=id(contexts[1][0]['led_states'])
    timings=[0.,0.]
    for count in range(120):
        for i,((ns,rng),node) in enumerate(zip(contexts,nodes)):
            started=time.perf_counter()
            ns['onCook'](node)
            timings[i]+=time.perf_counter()-started
        assert nodes[0].numpyArray().tobytes()==nodes[1].numpyArray().tobytes(),count
        assert contexts[0][0]['led_states']==contexts[1][0]['led_states'],count
        assert contexts[0][0]['frame_count']==contexts[1][0]['frame_count'],count
        assert contexts[0][1].getstate()==contexts[1][1].getstate(),count
    assert id(contexts[1][0]['led_states'])==identity
    assert random.getstate()==shared_rng_before
    assert not b.errors(recurse=True)
    result=json.dumps({'passed':True,'native_chop_comparisons':120,'shape':list(nodes[0].numpyArray().shape),
       'float32_bytes_equal':True,'simulation_states_equal':True,'private_rng_equal':True,
       'shared_rng_unchanged':True,'state_identity_retained':True,'callback_seconds':timings,
       'callback_reduction_percent':100*(1-timings[1]/timings[0]),'not_a_frame_rate_measurement':True})
finally:
    b.destroy()
'''
if __name__=='__main__':
    target=OUT/'legacy-bulk-native-probe.json'
    if target.exists(): raise ValueError('Evidence exists')
    data=td(SCRIPT)
    OUT.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2))
