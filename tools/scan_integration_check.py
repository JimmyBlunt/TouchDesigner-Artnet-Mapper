"""Read/install Guided Scan UI; never starts a camera or network output."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_20260907_capture import td

STATE = """
import json
result=json.dumps({'file':project.name, 'native':[{'path':n.path,'type':n.type,'active':bool(n.par.active.eval())} for n in op('/project1').findChildren() if n.type=='dmxout'], 'source_count':op('/project1/math1').numSamples, 'sender':op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status(), 'camera':op('/project1/guided_scan').fetch('camera_status',None),'scan':op('/project1/guided_scan').fetch('capture_status',None), 'config_paths':[n.path for n in op('/project1/multi_controller_output').children if 'config' in n.name]})
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['state', 'install', 'imports', 'thread-imports'])
    args = parser.parse_args()
    script = STATE
    if args.action == 'install':
        script = """
import importlib, json
from pathlib import Path
import pixelblaze_mapper.guided_scan_live as live
if any(h is not None and h.process.poll() is None for h in (live._probe, live._capture)):
    raise RuntimeError('Stop camera/capture before replacing the runtime')
import pixelblaze_mapper.scan_capture as capture
import pixelblaze_mapper.camera_probe as camera
import pixelblaze_mapper.scan_worker as worker
import pixelblaze_mapper.build_scan_session_ui as builder
import pixelblaze_mapper.routing_transaction as routing
importlib.reload(routing)
importlib.reload(capture)
importlib.reload(camera)
importlib.reload(worker)
importlib.reload(builder)
importlib.reload(live)
root=Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
path=root/'pixelblaze_mapper/build_scan_session_ui.py'
scope=dict(globals(), __name__='guided_scan_install')
exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),scope,scope)
node=scope['build']()
live.install_sender_guard(op)
result=json.dumps({'path':node.path,'errors':list(node.errors(recurse=True)), 'camera_started':False,'hardware_started':False})
"""
    elif args.action == 'imports':
        script = """
import subprocess, json, os
from pixelblaze_mapper.camera_probe import INTERPRETER, REPOSITORY
code='import faulthandler,time; faulthandler.dump_traceback_later(5); t=time.monotonic(); from pixelblaze_mapper.camera_probe_worker import _native_api; _native_api(); print(time.monotonic()-t); faulthandler.cancel_dump_traceback_later()'
p=subprocess.Popen([str(INTERPRETER),'-u','-c',code],cwd=str(REPOSITORY),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=False,creationflags=subprocess.CREATE_NO_WINDOW)
try:
    stdout,stderr=p.communicate(timeout=8)
except subprocess.TimeoutExpired:
    p.kill()
    stdout,stderr=p.communicate(timeout=2)
result=json.dumps({'returncode':p.returncode,'stdout':stdout,'stderr':stderr,'pythonhome':os.environ.get('PYTHONHOME'),'pythonpath':os.environ.get('PYTHONPATH')})
"""
    elif args.action == 'thread-imports':
        script = """
import subprocess, json
from pixelblaze_mapper.camera_probe import INTERPRETER, REPOSITORY
code='import faulthandler,time,threading,sys; faulthandler.dump_traceback_later(4); threading.Thread(target=lambda:sys.stdin.readline(),daemon=True).start(); t=time.monotonic(); from pixelblaze_mapper.camera_probe_worker import _native_api; _native_api(); print(time.monotonic()-t); faulthandler.cancel_dump_traceback_later()'
p=subprocess.Popen([str(INTERPRETER),'-u','-c',code],cwd=str(REPOSITORY),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=False,creationflags=subprocess.CREATE_NO_WINDOW)
try:
    p.wait(timeout=6)
except subprocess.TimeoutExpired:
    p.stdin.write('stop\\n');p.stdin.flush()
try:
    stdout,stderr=p.communicate(timeout=2)
except subprocess.TimeoutExpired:
    p.kill();stdout,stderr=p.communicate(timeout=2)
result=json.dumps({'returncode':p.returncode,'stdout':stdout,'stderr':stderr})
"""
    print(json.dumps(td(script), indent=2))
