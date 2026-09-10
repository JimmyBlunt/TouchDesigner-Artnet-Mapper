"""Install the scan UI in a running TD project, with before/after evidence.

Uses the project's existing localhost bridge. Never starts output or applies a
mapping. Save separately after visual verification. Run from the repository:
python -m tools.install_scan_workflow_ux
"""
import json
from pathlib import Path

from tools.audit_20260907_capture import td

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'scan-ux-20260910'

SNAPSHOT = r'''
import json, hashlib
from pixelblaze_mapper import guided_scan_live as live, scan_output_guard
live.assert_outputs_off(op)
assert not scan_output_guard.active(), 'Finish the current output operation first'
assert all(h is None or h.process.poll() is not None for h in (live._probe, live._capture)), 'Stop camera/capture first'
from pixelblaze_mapper import scan_offline_job
offline = op('/project1/guided_scan').fetch('offline_status', {}) or {}
assert not offline.get('running'), 'Stop the offline worker first'
paths = ['/project1/pixelblaze_mapper/map_active',
 '/project1/pixelblaze_mapper/effect_panel_uv',
 '/project1/multi_controller_output/controller_config',
 '/project1/multi_controller_output/segment_config',
 '/project1/layout_scene_editor/draft_document',
 '/project1/layout_scene_editor/fixture_document']
def snapshot():
    return {'file': project.folder + '/' + project.name,
      'hashes': {p: hashlib.sha256(op(p).text.encode()).hexdigest() if op(p) is not None else None for p in paths},
      'errors': list(op('/project1').errors(recurse=True)),
      'sender': op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status(),
      'native': {n.path: bool(n.par.active.eval()) for n in op('/project1').findChildren() if n.type == 'dmxout'}}
'''


def install_script(root):
    return SNAPSHOT + r'''
import sys, importlib
from pathlib import Path
root = Path(__ROOT__)
before = snapshot()
package = importlib.import_module('pixelblaze_mapper')
package.__path__ = [str(root / 'pixelblaze_mapper')]
if str(root) in sys.path: sys.path.remove(str(root))
sys.path.insert(0, str(root))
# Persist copied-project code roots in embedded Python DATs. Original TOE and
# filesystem scan data stay intact. Record every adjusted DAT for review.
old = 'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
rewritten = []
for node in op('/project1').findChildren():
    if node.family != 'DAT' or node.type != 'text': continue
    source = node.text
    if not any(token in source for token in ('import ', 'sys.path', 'exec(')): continue
    changed = source.replace(old, root.as_posix()).replace(old.replace('/', '\\'), str(root).replace('\\', '/'))
    if changed != source:
        rewritten.append({'path': node.path, 'before_sha256': hashlib.sha256(source.encode()).hexdigest(),
                          'after_sha256': hashlib.sha256(changed.encode()).hexdigest()})
        node.text = changed
modules = ['camera_probe', 'scan_capture', 'scan_offline_job', 'guided_scan_live', 'scan_coverage',
           'build_gico_port_config_ui', 'layout_scene_td', 'led_search',
           'scan_library', 'scan_result_review', 'scan_workflow_ux', 'build_scan_session_ui', 'build_layout_scene_ui']
loaded = {}
for name in modules:
    qualified = 'pixelblaze_mapper.' + name
    module = importlib.reload(sys.modules[qualified]) if qualified in sys.modules else importlib.import_module(qualified)
    loaded[name] = module.__file__
    assert Path(module.__file__).resolve().is_relative_to(root), module.__file__
for name in ('build_layout_scene_ui', 'build_scan_session_ui'):
    path = root / 'pixelblaze_mapper' / (name + '.py')
    scope = dict(globals(), __name__='scan_ux_install', __file__=str(path))
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    scope['build']()
op('/project1/guided_scan').store('scan_ux_revision', '2026-09-10')
format_field = op('/project1/layout_scene_editor/ui_panel/format/string')
if format_field.text.strip() == 'pixelblaze':
    format_field.text = 'auto'
after = snapshot()
checks = {'data_unchanged': before['hashes'] == after['hashes'],
          'sender_off': not after['sender']['enabled'],
          'native_off': not any(after['native'].values()),
          'no_packets_sent': before['sender']['telemetry']['packet_count'] == after['sender']['telemetry']['packet_count'],
          'no_operator_errors': not after['errors']}
result = json.dumps({'before': before, 'after': after, 'checks': checks,
                     'code_root': str(root), 'modules': loaded, 'rewritten_code_dats': rewritten})
'''.replace('__ROOT__', repr(str(root)))


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    result = td(install_script(ROOT))
    target = OUT / 'installation.json'
    index = 2
    while target.exists():
        target = OUT / ('installation-%02d.json' % index)
        index += 1
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['checks'], indent=2))
    if not all(result['checks'].values()):
        raise SystemExit('Installation needs review; see installation.json. Project was not saved.')
