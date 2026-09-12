"""Reproducible native installation, parity checks and an output-off checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/performance-program-20260912/td'


def td(script):
    req=urllib.request.Request('http://127.0.0.1:9981/api/td/server/exec',json.dumps({'script':script}).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:data=json.load(response)
    if not data.get('success'):raise RuntimeError(data)
    return json.loads(data['data']['result'])


INSTALL=r'''
import json,hashlib,importlib,numpy as np
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
from pixelblaze_mapper import numpy_realtime,preview_numpy,output_slot_mask,build_led_preview_contract,external_packet_sender,sender_external_source
for module in (numpy_realtime,preview_numpy,output_slot_mask,build_led_preview_contract,external_packet_sender,sender_external_source):importlib.reload(module)
root=op('/project1');router=root.op('multi_controller_output')
sender=router.op('artnet_510_sender_callbacks');assert not sender.module.status()['enabled']
paths=[sender.path,'/project1/legacy_source_mask_callbacks','/project1/pixelblaze_mapper/preview3d/instance_data_callbacks']
originals={path:op(path).text for path in paths}
tables=['/project1/pixelblaze_mapper/map_active','/project1/layout_apply/active_source_mask',router.path+'/segment_config',router.path+'/controller_config']
def hashes():return {p:hashlib.sha256(op(p).text.encode()).hexdigest() for p in tables}
before=hashes()
try:
 sender.text=sender_external_source.install_source(numpy_realtime.install_sender(sender.text))
 op(paths[1]).text=numpy_realtime.LEGACY_CALLBACK
 op(paths[2]).text=build_led_preview_contract.patch_dynamic_source(op(paths[2]).text)
 source=router.op('source_select');source.cook(force=False)
 values=source.numpyArray();ranges=output_slot_mask.ranges_for(op,source.numSamples)
 compiled=sender.module._compiled_router()
 rgb=output_slot_mask.channels(values[:3],ranges)
 for c in compiled.controllers:
  assert numpy_realtime.NumpyControllerPacker(c).pack(values,ranges)==c.pack_channels(*rgb),c.name
 mask=root.op('legacy_source_mask');mask.cook(force=True)
 expected=numpy_realtime.mask_array(mask.inputs[0].numpyArray(),output_slot_mask.ranges_for(op,mask.numSamples))
 assert np.array_equal(expected,mask.numpyArray(),equal_nan=True)
 assert [c.name for c in mask.chans()]==[c.name for c in mask.inputs[0].chans()]
 preview=root.op('pixelblaze_mapper/preview3d/instance_data');preview.cook(force=True)
 assert preview.numSamples==root.op('pixelblaze_mapper/map_active').numRows-1
 assert not root.errors(recurse=True),root.errors(recurse=True)
 assert hashes()==before
 assert not sender.module.status()['enabled']
except:
 for path,source_text in originals.items():op(path).text=source_text
 raise
result=json.dumps({'installed':paths,'before_hashes':before,'after_hashes':hashes(),'routing_payloads_identical':True,
 'mask_array_identical':True,'sender_off':True,'source_slots':source.numSamples,'errors':root.errors(recurse=True)})
'''


SHOW_INSTALL=r'''
import json,importlib
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
from pixelblaze_mapper import show_sync_fastpath
importlib.reload(show_sync_fastpath)
root=op('/project1/show_control');cb=root.op('callbacks');render=root.op('render_sync')
assert str(cb.module.runtime().state) in ('TransportState.STOPPED','TransportState.PAUSED')
before_plan=repr(cb.module.runtime().plan())
originals={cb.path:cb.text,render.path:render.text}
before={p:root.op(p).text for p in show_sync_fastpath.REQUEST_PATHS}
try:
 render.text=show_sync_fastpath.install_render_source(render.text)
 cb.text=show_sync_fastpath.install_callback_source(cb.text)
 cb.module.sync();cb.module.advance(0);cb.module.advance(0)
 assert repr(cb.module.runtime().plan())==before_plan
 after={p:root.op(p).text for p in show_sync_fastpath.REQUEST_PATHS}
 assert before==after,'Show request/state changed'
 assert not op('/project1').errors(recurse=True)
 assert_outputs_off(op)
except:
 for path,source in originals.items():op(path).text=source
 raise
result=json.dumps({'installed':list(originals),'originals':originals,'requests_unchanged':True,
 'plan_unchanged':True,'sender_off':True,'errors':op('/project1').errors(recurse=True)})
'''


UI_INSTALL=r'''
import json,hashlib,importlib
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
from pixelblaze_mapper import router_status_source,router_dynamic_ui
for module in (router_status_source,router_dynamic_ui):importlib.reload(module)
root=op('/project1/multi_controller_output');node=root.op('ui_callbacks')
original=node.text
paths=['controller_config','segment_config','validation']
before={p:root.op(p).text for p in paths}
try:
 node.text=router_status_source.install_source(original)
 assert router_status_source.restore_source(node.text)==router_status_source.restore_source(original)
 node.module.refresh_status(force=True)
 node.module.refresh_status(force=True)
 assert before=={p:root.op(p).text for p in paths}
 assert not op('/project1').errors(recurse=True)
 assert_outputs_off(op)
except:
 node.text=original
 raise
result=json.dumps({'installed':node.path,'original':original,'tables_unchanged':True,
 'sender_off':True,'errors':op('/project1').errors(recurse=True)})
'''

CLOCK_INSTALL=r'''
import json
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
root=op('/project1/multi_controller_output')
assert '# EXTERNAL_FRAME_CLOCK_V2' in root.op('artnet_510_sender_callbacks').text
before=dict(root.fetch('external_sender_settings',{}))
after=dict(before,frame_pacing=True,worker_priority='normal')
root.store('external_sender_settings',after)
assert_outputs_off(op)
result=json.dumps({'before':before,'after':after,'sender_off':True,'controller_rates_unchanged':True})
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('install','show','ui','clock','save'));p.add_argument('--label',default='verified-install')
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True);report=OUT/(a.label+'.json')
    if report.exists():raise ValueError('Evidence already exists')
    if a.action=='install':result=td(INSTALL)
    elif a.action=='show':result=td(SHOW_INSTALL)
    elif a.action=='ui':result=td(UI_INSTALL)
    elif a.action=='clock':result=td(CLOCK_INSTALL)
    else:
        if not a.label.replace('-','').isalnum():raise ValueError('Invalid checkpoint label')
        path=ROOT/('PixelblazeMapper_30FPS_PROGRAM_20260912_'+a.label+'.toe')
        if path.exists():raise ValueError('Checkpoint already exists')
        result=td(r'''import json
from pixelblaze_mapper.guided_scan_live import assert_outputs_off
assert_outputs_off(op)
r=op('/project1/multi_controller_output');s=r.op('artnet_510_sender_callbacks').module
assert not s.status()['enabled'];assert not op('/project1').errors(recurse=True)
assert '# NUMPY_ROUTER_PACK_V1' in r.op('artnet_510_sender_callbacks').text
assert project.save(%r,saveExternalToxs=False)
result=json.dumps({'file':project.name,'folder':project.folder,'saved':True,'sender_off':not s.status()['enabled']})'''%path.as_posix())
        actual=(Path(result['folder'])/result['file']).resolve()
        if actual.parent != ROOT.resolve() or not actual.name.startswith(path.stem):
            raise ValueError('Unexpected saved checkpoint path: '+str(actual))
        result['sha256']=hashlib.sha256(actual.read_bytes()).hexdigest()
    report.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
