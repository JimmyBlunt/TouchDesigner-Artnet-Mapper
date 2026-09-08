"""Guided scan surface: explicit camera probe, reviewed scan, offline review.

Import/build never launches hardware. Camera and scan each require their own
user action. Existing helper widgets are reused; fields survive a rebuild.
"""

from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import csv
import json
import re
from uuid import uuid4

from pixelblaze_mapper.layout_scene import export_scene_json
from pixelblaze_mapper.scan_session import ScanSession, ScanSessionError, ScanTarget
from pixelblaze_mapper.scan_worker import create_manifest, load_observations

ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
OWNER = '/project1/guided_scan'


def field_text(node):
    """Text DATs can have zero cells; read their text rather than cell [0,0]."""
    if node is None:
        raise ValueError('Required scan input field is missing')
    return '' if node.text is None else str(node.text).strip()


def plan_scene(scene, object_id, selected_ids=None, anchor_ids=()):
    """Stage one object's full/partial replacement; preserve canonical IDs."""
    obj = scene.object(object_id)
    selected = tuple(led.led_id for led in obj.leds) if selected_ids is None else tuple(selected_ids)
    if not set(selected) <= {led.led_id for led in obj.leds}:
        raise ScanSessionError('Selected IDs are outside the chosen object')
    targets = tuple(ScanTarget(led.led_id, item.object_id, led.local_index, led.source_index)
                    for item in scene.objects for led in item.leds)
    revision = sha256(export_scene_json(scene, indent=None).encode('utf-8')).hexdigest()
    return ScanSession(str(uuid4()), scene.scene_id, revision, targets, selected, tuple(anchor_ids))


def parse_indices(text):
    """Explicit zero-based source IDs/ranges, no inferred or wrapped indices."""
    result = []
    for part in str(text).split(','):
        part = part.strip()
        if not re.fullmatch(r'\d+(?:\s*-\s*\d+)?', part):
            raise ScanSessionError('Use source indices such as 0-49, 78, 92-100')
        bounds = [int(value.strip()) for value in part.split('-')]
        start, end = bounds[0], bounds[-1]
        if end < start or end - start > 100000:
            raise ScanSessionError('Invalid or excessive source range')
        result.extend(range(start, end + 1))
    if len(set(result)) != len(result) or len(result) > 100000:
        raise ScanSessionError('Duplicate or excessive source indices')
    return tuple(result)


def select_scope(session, source_text, anchor_text=''):
    lookup = {target.source_index: target.led_id for target in session.targets}
    selected = parse_indices(source_text)
    anchors = parse_indices(anchor_text) if anchor_text.strip() else ()
    if not set(selected + anchors) <= set(lookup):
        raise ScanSessionError('An index does not belong to the staged scene')
    if session.views:
        raise ScanSessionError('Start a new staged session before changing captured scope')
    return replace(session, selected_ids=tuple(lookup[i] for i in selected),
                   anchor_ids=tuple(lookup[i] for i in anchors))


def attach_existing_views(session, filenames):
    """Read existing observations, recording actual IDs; no capture is performed."""
    if session.views:
        raise ScanSessionError('Views already attached; stage a new session to replace them')
    paths = tuple(Path(name).resolve(strict=True) for name in filenames)
    if len(paths) < 2 or len(set(paths)) != len(paths):
        raise ScanSessionError('Choose at least two distinct view CSV files')
    lookup = {target.source_index: target.led_id for target in session.targets
              if target.led_id in session.capture_ids}
    views = {}
    for index, path in enumerate(paths):
        data = path.read_bytes()
        reader = csv.DictReader(data.decode('utf-8-sig').splitlines())
        if reader.fieldnames != ['index', 'u', 'v']:
            raise ScanSessionError('Expected a MariMapper 2D index,u,v CSV')
        ids = []
        for row in reader:
            try:
                ids.append(lookup[int(row['index'])])
            except (KeyError, ValueError, TypeError) as error:
                raise ScanSessionError('View contains malformed or outside-scope IDs') from error
        view_id = 'view-%d' % index
        session = session.start_view(view_id).finish_view(ids, str(path) + '#sha256=' + sha256(data).hexdigest())
        views[view_id] = str(path)
    return session.request_reconstruction(), views


def worker_command(interpreter, manifest_path, *, confirm=False):
    """Argument list only. Never shell interpolation or process launch."""
    executable = Path(interpreter).resolve(strict=True)
    manifest = Path(manifest_path).resolve(strict=True)
    if not executable.is_file() or executable.name.lower() != 'python.exe':
        raise ScanSessionError('Choose the reviewed isolated MariMapper python.exe')
    command = [str(executable), '-m', 'pixelblaze_mapper.scan_worker', str(manifest)]
    if confirm is True:
        command.append('--confirm-offline-reconstruction')
    elif confirm is not False:
        raise ScanSessionError('Confirmation must be an explicit boolean')
    return command


def _runtime_source():
    return r'''import json
from dataclasses import asdict
from pathlib import Path
import sys
ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.build_scan_session_ui import plan_scene, select_scope, attach_existing_views, worker_command, field_text
from pixelblaze_mapper.scan_session import ScanSession
from pixelblaze_mapper.scan_worker import create_manifest, load_observations
OWNER = op('/project1/guided_scan')
from pixelblaze_mapper import guided_scan_live as live
from pixelblaze_mapper import scan_offline_job as offline_job

def _status(message):
    OWNER.store('message', message)
    node = OWNER.op('ui_panel/status')
    if node is not None:
        node.par.text = message

def _state():
    value = OWNER.fetch('session', None)
    if value is None:
        raise ValueError('Open Scan from a selected Layout object first')
    return ScanSession.from_dict(value)

def _field(name):
    return field_text(OWNER.op('ui_panel/' + name + '/string'))

def _show_scope(state):
    lookup = {target.led_id: target.source_index for target in state.targets}
    updates = []
    for name, ids in (('source_ids', state.selected_ids), ('anchors', state.anchor_ids)):
        node = OWNER.op('ui_panel/' + name + '/string')
        if node is None:
            raise ValueError('Required scan input field is missing: ' + name)
        updates.append((node, ','.join(str(lookup[item]) for item in ids)))
    previous = [(node, node.text) for node, value in updates]
    try:
        for node, value in updates:
            node.text = value
    except Exception:
        for node, value in previous:
            node.text = value
        raise

def stage_scene(scene, object_id, selected_ids=None, anchor_ids=()):
    if live._capture is not None and live._capture.process.poll() is None:
        raise ValueError('Stop the current scan before staging another object')
    state = plan_scene(scene, object_id, selected_ids, anchor_ids)
    _show_scope(state)
    OWNER.store('standalone_capture', None)
    OWNER.store('session', state.to_dict())
    OWNER.store('manifest', None)
    OWNER.store('candidate', None)
    OWNER.store('merge_request', None)
    OWNER.store('capture_plan', None)
    OWNER.store('capture_signature', None)
    for name in ('worker_plan', 'dry_run'):
        node = OWNER.op(name)
        if node is not None:
            node.text = ''
    node = OWNER.op('ui_panel/routing_summary')
    if node is not None:
        node.par.text = 'Routing not checked for this selection. CHECK SCAN PLAN before starting.'
    _status('STAGED: %d LEDs + %d anchors | no camera or output | edit scope, then PREPARE' % (len(state.selected_ids), len(state.anchor_ids)))
    return state

def stage_registered_candidate(scan, candidates, registration_reference, quality_reference):
    # Caller supplies independently registered/verified results. No invented fit.
    state = _state().stage_candidate(scan.scan_id, candidates,
        registration_reference=registration_reference, quality_reference=quality_reference)
    OWNER.store('session', state.to_dict())
    OWNER.store('candidate', scan)
    _status('CANDIDATE READY FOR REVIEW | staged only; layout unchanged')

def request_handoff(accepted_ids, current_scene_revision):
    if OWNER.fetch('standalone_capture', None) is not None:
        raise ValueError('Separate acquisition: import and assign reviewed results in Layout; not a replacement request')
    state, request = _state().request_merge(accepted_ids, current_scene_revision=current_scene_revision)
    OWNER.store('session', state.to_dict())
    OWNER.store('merge_request', request)
    _status('MERGE REQUEST STAGED | review explicit selected IDs in Layout; no active apply')
    return request, OWNER.fetch('candidate')

def act(command):
    try:
        if command == 'offline_start':
            manifest = OWNER.fetch('manifest', None)
            if not manifest:
                raise ValueError('PREPARE 3D OFFLINE JOB first')
            answer = ui.messageBox('Start offline 3D reconstruction?',
                'Runs installed MariMapper in a separate process (maximum 5 minutes). No camera or LED output. Raw coordinates require alignment and review; no automatic layout replacement.',
                buttons=['Cancel', 'Start 3D'])
            if answer == 1:
                offline_job.start(op, _field('python'), manifest, confirmed=True)
            return True
        if command == 'offline_stop':
            offline_job.stop()
            return True
        if command == 'offline_result':
            offline_job.poll(op)
            OWNER.op('offline_result').openViewer()
            return True
        if command == 'new_capture':
            OWNER.op('new_capture_panel').openViewer()
            return True
        if command == 'stage_capture':
            def field(name):
                return field_text(OWNER.op('new_capture_panel/' + name + '/string'))
            settings = {name:field(name) for name in ('name','target','interface','universe','count','rate','order')}
            for name in ('universe','count','rate'):
                settings[name] = int(settings[name])
            state = live.stage_standalone(op, settings)
            OWNER.op('ui_panel').openViewer()
            return True
        if command == 'camera_start':
            live.camera_start(op)
            return True
        if command == 'camera_stop':
            live.camera_stop(op)
            return True
        if command == 'stop':
            live.stop(op)
            return True
        if command == 'ports':
            op('/project1/multi_controller_output/gico_port_config/ui_panel').openViewer()
            return True
        if command == 'back':
            op('/project1/layout_scene_editor/ui_panel').openViewer()
            return True
        state = _state()
        if command == 'prepare':
            live.prepare(op)
        elif command == 'arm':
            message = str(OWNER.op('ui_panel/routing_summary').par.text.eval())
            answer = ui.messageBox('Start one MariMapper view?', message + '\n\nThis switches ALL reserved universes of the listed controllers to black, then scans selected LEDs at max 5%. Camera and object must stay fixed. No automatic Live resume. Continue?', buttons=['Cancel', 'Start Scan'])
            if answer == 1:
                live.start(op, confirmed=True)
        elif command == 'offline':
            filenames = [value.strip() for value in _field('views').split('|') if value.strip() and value.strip() != 'None']
            if len(filenames) < 2:
                raise ValueError('Capture or select at least two distinct view CSV files before preparing a 3D job')
            candidate, views = attach_existing_views(state, filenames)
            workspace = Path(_field('workspace')).resolve(strict=True)
            manifest = create_manifest(candidate, views=views, source_roots=[Path(p).parent for p in filenames],
                workspace_root=workspace, output_directory=workspace / ('result-' + candidate.session_id),
                camera_model='camera_model_opencv')
            load_observations(manifest)
            manifest_path = workspace / ('scan-' + candidate.session_id + '.json')
            # Exclusive create: user-selected workspace only, never overwrite.
            with manifest_path.open('x', encoding='utf-8') as stream:
                json.dump(manifest, stream, indent=2)
            OWNER.store('session', candidate.to_dict())
            OWNER.store('manifest', str(manifest_path))
            OWNER.op('worker_plan').text = json.dumps({'cwd': str(ROOT), 'argv': worker_command(_field('python'), manifest_path),
                'explicit_run_argv': worker_command(_field('python'), manifest_path, confirm=True),
                'runs_automatically': False}, indent=2)
            _status('OFFLINE MANIFEST SAVED | worker_plan contains dry-run and explicit reconstruction command | nothing launched')
        elif command == 'cancel':
            offline_job.stop()
            live.stop(op)
            OWNER.store('session', state.cancel().to_dict())
            _status('SESSION CANCELLED | no automatic output resume; layout unchanged')
        else:
            raise ValueError('Unknown guided scan action')
        return True
    except Exception as error:
        _status('BLOCKED | ' + str(error))
        if command == 'stage_capture' and OWNER.op('new_capture_panel/notice') is not None:
            OWNER.op('new_capture_panel/notice').par.text = 'BLOCKED | ' + str(error)
        return False
'''


def build():
    scope = dict(globals())
    scope['__name__'] = 'guided_scan_helpers'
    path = ROOT / 'pixelblaze_mapper' / 'build_gico_port_config_ui.py'
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), scope, scope)
    node, panel, text, field, button, click = (scope[name] for name in ('_node', '_panel', '_text', '_field', '_button', '_click'))
    owner = node(op('/project1'), baseCOMP, 'guided_scan')
    for child in owner.children:
        if child.type == 'panelexec':
            child.par.active = False
    node(owner, textDAT, 'runtime').text = _runtime_source()
    node(owner, textDAT, 'dry_run')
    node(owner, textDAT, 'worker_plan')
    node(owner, textDAT, 'offline_result')
    canvas = panel(node(owner, containerCOMP, 'ui_panel'), 0, 0, 1160, 780, 10)
    canvas.viewer = True
    text(canvas, 'title', 'GUIDED SCAN | FULL OBJECT / SELECTED REGION', 20, 727, 1120, 36, 23)
    text(canvas, 'notice', '1 Check camera. 2 Select LEDs and review routing. 3 START SCAN captures ONE view. Move camera between views; never during a scan.', 20, 679, 1120, 42, 13)
    camera_fields = [('camera', '0', 'CAMERA DEVICE (OpenCV ID; try 0 / 1)', 20, 350),
                     ('exposure', '-10', 'EXPOSURE (camera-dependent)', 400, 350),
                     ('threshold', '160', 'DETECTION THRESHOLD (0-254)', 780, 360)]
    for name, value, label, x, width in camera_fields:
        text(canvas, name + '_label', label, x, 650, width, 24, 11)
        existing = canvas.op(name + '/string')
        field(canvas, name, field_text(existing) if existing is not None else value, x, 619, width)
    fields = [
              ('source_ids', '', 'ZERO-BASED SOURCE INDICES: full object or explicit ranges, e.g. 0-49,78'),
              ('anchors', '', 'VERIFICATION ANCHOR SOURCE INDICES (never replaced)'),
              ('views', '', 'EXISTING 2D VIEW CSV PATHS, separated by | (at least two distinct views)'),
              ('workspace', '', 'EXISTING WORKSPACE FOLDER (new manifest/results only)'),
              ('python', r'C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe', 'OFFLINE WORKER PYTHON (camera/scan uses the reviewed installed interpreter)')]
    for index, (name, value, label) in enumerate(fields):
        y = 466 - index * 58
        text(canvas, name + '_label', label, 20, y + 32, 1120, 28, 11)
        existing = canvas.op(name + '/string')
        if existing is not None:
            value = field_text(existing)
            if name in ('anchors', 'views') and value == 'None':
                value = ''
        field(canvas, name, value, 20, y, 1120)
    controls = [('new_capture', 'NEW CAPTURE (NO LAYOUT)', 480, 571, 420),
                ('camera_start', 'CHECK CAMERA', 20, 571, 220), ('camera_stop', 'CLOSE CAMERA', 250, 571, 220),
                ('ports', 'CONTROLLER / PORTS', 910, 571, 230),
                ('prepare', 'CHECK SCAN PLAN', 20, 146, 250), ('arm', 'START SCAN / NEXT VIEW', 285, 146, 350),
                ('stop', 'STOP SCAN', 650, 146, 240), ('back', 'BACK TO LAYOUT', 905, 146, 235),
                ('offline', 'PREPARE 3D OFFLINE JOB', 20, 98, 270),
                ('offline_start', 'START 3D', 300, 98, 200),
                ('offline_stop', 'STOP 3D', 510, 98, 190),
                ('offline_result', '3D RESULT / PATH', 710, 98, 220),
                ('cancel', 'CANCEL SESSION', 940, 98, 200)]
    for name, label, x, y, width in controls:
        control = button(canvas, 'btn_' + name, label, x, y, width)
        click(owner, 'click_' + name, control, "op('runtime').module.act(%r)" % name)
    text(canvas, 'camera_status', 'CAMERA NOT TESTED — device ID alone does not mean a connected camera', 20, 529, 1120, 32, 11)
    text(canvas, 'routing_summary', 'Routing not checked. Controller / Ports opens the existing universe configuration.', 20, 188, 1120, 38, 11)
    text(canvas, 'capabilities', '', 600, 90, 540, 1, 11)
    text(canvas, 'offline_status', '3D: not started | no automatic layout replacement', 20, 64, 1120, 26, 11)
    text(canvas, 'status', owner.fetch('message', 'Open Scan from Layout to stage an object. No camera or LED output is started.'), 20, 12, 1120, 46, 12)
    poller = node(owner, executeDAT, 'capture_poll')
    poller.text = "from pixelblaze_mapper import guided_scan_live as live\nfrom pixelblaze_mapper import scan_offline_job as offline_job\ndef onFrameStart(frame):\n    live.poll(op)\n    if frame % 30 == 0: offline_job.poll(op)\ndef onStart():\n    live.shutdown()\n    offline_job.stop()\ndef onExit():\n    live.shutdown()\n    offline_job.stop()\n"
    poller.par.active = True
    poller.par.framestart = True
    poller.par.exit = True
    poller.par.start = True
    fresh = panel(node(owner, containerCOMP, 'new_capture_panel'), 0, 0, 820, 530, 10)
    fresh.viewer = True
    text(fresh, 'title', 'NEW ACQUISITION | NO LAYOUT ASSIGNMENT', 20, 470, 780, 40, 20)
    entries = [('name','CAPTURE','CAPTURE NAME'), ('target','','CONTROLLER IPv4'),
               ('interface','','LOCAL IPv4 INTERFACE'), ('universe','0','START UNIVERSE (WIRE, ZERO-BASED)'),
               ('count','256','LED COUNT (LOCAL 0..COUNT-1)'), ('rate','30','FPS LIMIT'),
               ('order','RGB','NETWORK COLOR ORDER (not LED wiring)')]
    for index,(name,value,label) in enumerate(entries):
        x,y = 20+(index%2)*400, 395-(index//2)*82
        existing = fresh.op(name+'/string')
        if existing is not None:
            value = field_text(existing)
        text(fresh,name+'_label',label,x,y+32,380,27,11)
        field(fresh,name,value,x,y,380)
    text(fresh,'notice','Creates acquisition IDs and routing only. No camera, LED output, geometry or live controller assignment. Existing scans remain on disk.',20,67,780,64,12)
    control = button(fresh,'btn_stage','CREATE ACQUISITION (OUTPUT OFF)',20,20,780)
    click(owner,'click_stage_capture',control,"op('runtime').module.act('stage_capture')")
    return owner


if globals().get('__name__') == '__main__' and 'op' in globals():
    build()
