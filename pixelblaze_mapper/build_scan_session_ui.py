"""Additive guided scan UI. Planning and offline job preparation, never hardware.

The camera selection is a requested device ID, NOT a detected/connected camera.
No builder invocation on ordinary import. Existing helper widgets are reused.
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
from pixelblaze_mapper.build_scan_session_ui import plan_scene, select_scope, attach_existing_views, worker_command
from pixelblaze_mapper.scan_session import ScanSession
from pixelblaze_mapper.scan_worker import create_manifest, load_observations
OWNER = op('/project1/guided_scan')

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
    return str(OWNER.op('ui_panel/' + name + '/string')[0, 0]).strip()

def _show_scope(state):
    lookup = {target.led_id: target.source_index for target in state.targets}
    for name, ids in (('source_ids', state.selected_ids), ('anchors', state.anchor_ids)):
        node = OWNER.op('ui_panel/' + name + '/string')
        if node is not None:
            node[0, 0] = ','.join(str(lookup[item]) for item in ids)

def stage_scene(scene, object_id, selected_ids=None, anchor_ids=()):
    state = plan_scene(scene, object_id, selected_ids, anchor_ids)
    OWNER.store('session', state.to_dict())
    OWNER.store('manifest', None)
    OWNER.store('candidate', None)
    OWNER.store('merge_request', None)
    _show_scope(state)
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
    state, request = _state().request_merge(accepted_ids, current_scene_revision=current_scene_revision)
    OWNER.store('session', state.to_dict())
    OWNER.store('merge_request', request)
    _status('MERGE REQUEST STAGED | review explicit selected IDs in Layout; no active apply')
    return request, OWNER.fetch('candidate')

def act(command):
    try:
        if command == 'back':
            op('/project1/layout_scene_editor/ui_panel').openViewer()
            return True
        state = _state()
        if command == 'prepare':
            camera = int(_field('camera'))
            if camera < 0:
                raise ValueError('Requested camera ID must be nonnegative')
            state = select_scope(state, _field('source_ids'), _field('anchors'))
            OWNER.store('session', state.to_dict())
            OWNER.store('requested_camera', camera)
            OWNER.op('dry_run').text = json.dumps([asdict(step) for step in state.dry_run_schedule()], indent=2)
            _status('PREPARED DRY RUN: %d LEDs + %d anchors | camera %d NOT connected | output OFF' % (len(state.selected_ids), len(state.anchor_ids), camera))
        elif command == 'arm':
            raise ValueError('Cannot arm: exclusive router lease + camera adapter are not implemented. No LEDs or camera were touched.')
        elif command == 'offline':
            filenames = [value.strip() for value in _field('views').split('|') if value.strip()]
            candidate, views = attach_existing_views(state, filenames)
            workspace = Path(_field('workspace')).resolve(strict=True)
            manifest = create_manifest(candidate, views=views, source_roots=[Path(p).parent for p in filenames],
                workspace_root=workspace, output_directory=workspace / ('result-' + candidate.session_id))
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
            OWNER.store('session', state.cancel().to_dict())
            _status('SESSION CANCELLED | no automatic output resume; layout unchanged')
        else:
            raise ValueError('Unknown guided scan action')
        return True
    except Exception as error:
        _status('BLOCKED | ' + str(error))
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
    canvas = panel(node(owner, containerCOMP, 'ui_panel'), 0, 0, 1160, 780, 10)
    canvas.viewer = True
    text(canvas, 'title', 'GUIDED SCAN | FULL OBJECT / SELECTED REGION', 20, 727, 1120, 36, 23)
    text(canvas, 'notice', '1 Select scope + stable anchors. 2 Prepare a dry run. 3 Capture requires an adapter. Existing views can be reconstructed offline.', 20, 668, 1120, 48, 13)
    fields = [('camera', '0', 'REQUESTED CAMERA ID (not connected)'),
              ('source_ids', '', 'ZERO-BASED SOURCE INDICES: full object or explicit ranges, e.g. 0-49,78'),
              ('anchors', '', 'VERIFICATION ANCHOR SOURCE INDICES (never replaced)'),
              ('views', '', 'EXISTING 2D VIEW CSV PATHS, separated by | (at least two distinct views)'),
              ('workspace', '', 'EXISTING WORKSPACE FOLDER (new manifest/results only)'),
              ('python', r'C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe', 'ISOLATED MARIMAPPER PYTHON (not launched automatically)')]
    for index, (name, value, label) in enumerate(fields):
        y = 594 - index * 70
        text(canvas, name + '_label', label, 20, y + 32, 1120, 28, 11)
        existing = canvas.op(name + '/string')
        if existing is not None:
            value = str(existing[0, 0])
        field(canvas, name, value, 20, y, 1120)
    controls = [('prepare', 'PREPARE DRY RUN', 20, 165, 250), ('arm', 'ARM CAPTURE (UNAVAILABLE)', 285, 165, 350),
                ('offline', 'PREPARE OFFLINE JOB', 650, 165, 290), ('cancel', 'CANCEL', 955, 165, 185),
                ('back', 'BACK TO LAYOUT', 20, 108, 250)]
    for name, label, x, y, width in controls:
        control = button(canvas, 'btn_' + name, label, x, y, width)
        click(owner, 'click_' + name, control, "op('runtime').module.act(%r)" % name)
    text(canvas, 'capabilities', 'CAPTURE / OUTPUT: unavailable | Offline SfM: explicit separate worker | Registration + quality review: required before merge', 285, 98, 855, 52, 11)
    text(canvas, 'status', owner.fetch('message', 'Open Scan from Layout to stage an object. No camera or LED output is started.'), 20, 20, 1120, 64, 13)
    return owner


if globals().get('__name__') == '__main__' and 'op' in globals():
    build()
