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

ROOT = Path(__file__).resolve().parents[1]
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


def offline_scope(session, source_text, anchor_text=''):
    """Snapshot edited scope for offline work, independent of hardware routing.

    Re-preparing an attached job receives a new identity/output directory while
    retaining canonical target IDs and the staged scene revision.
    """
    from pixelblaze_mapper.scan_session import Stage
    if session.stage not in (Stage.PLANNED, Stage.RECONSTRUCTING):
        raise ScanSessionError('Stage a new session before preparing more views')
    if session.views:
        session = ScanSession(str(uuid4()), session.scene_id, session.scene_revision,
                              session.targets, session.selected_ids, session.anchor_ids)
    return select_scope(session, source_text, anchor_text)


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
ROOT = Path(__PROJECT_ROOT__)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.build_scan_session_ui import plan_scene, select_scope, attach_existing_views, worker_command, field_text, offline_scope
from pixelblaze_mapper.scan_session import ScanSession
from pixelblaze_mapper.scan_worker import create_manifest, load_observations
OWNER = op('/project1/guided_scan')
from pixelblaze_mapper import guided_scan_live as live
from pixelblaze_mapper import scan_offline_job as offline_job
from pixelblaze_mapper import scan_workflow_ux as workflow

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

def _require_idle():
    for handle in (live._capture, offline_job._job):
        if handle is not None and handle.process.poll() is None:
            raise ValueError('Stop the current capture or 3D job before changing its selection')

def _set_views(paths):
    current = workflow.view_paths(_field('views'))
    if paths != current:
        _require_idle()
        OWNER.op('ui_panel/views/string').text = ' | '.join(paths)
        OWNER.store('manifest', None)

def _show_scope(state):
    lookup = {target.led_id: target.source_index for target in state.targets}
    updates = []
    for name, ids in (('source_ids', state.selected_ids), ('anchors', state.anchor_ids)):
        node = OWNER.op('ui_panel/' + name + '/string')
        if node is None:
            raise ValueError('Required scan input field is missing: ' + name)
        updates.append((node, workflow.compact_indices(lookup[item] for item in ids)))
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
    _require_idle()
    state = plan_scene(scene, object_id, selected_ids, anchor_ids)
    _show_scope(state)
    OWNER.store('standalone_capture', None)
    OWNER.store('session', state.to_dict())
    OWNER.store('manifest', None)
    OWNER.store('candidate', None)
    OWNER.store('merge_request', None)
    OWNER.store('capture_plan', None)
    OWNER.store('capture_signature', None)
    OWNER.store('workflow_page', 'capture')
    OWNER.store('capture_status', {})
    OWNER.store('offline_status', {})
    views = OWNER.op('ui_panel/views/string')
    if views is not None:
        views.text = ''
    for name in ('worker_plan', 'dry_run'):
        node = OWNER.op(name)
        if node is not None:
            node.text = ''
    node = OWNER.op('ui_panel/routing_summary')
    if node is not None:
        node.par.text = 'Routing not checked for this selection. CHECK SCAN PLAN before starting.'
    _status('STAGED: %d LEDs + %d anchors. Check the scan plan when ready.' % (len(state.selected_ids), len(state.anchor_ids)))
    workflow.refresh(OWNER)
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
        if command in ('page_capture', 'page_offline', 'page_settings'):
            OWNER.store('workflow_page', command.removeprefix('page_'))
            return True
        if command == 'help':
            ui.messageBox('Scan workflow help', workflow.HELP, buttons=['Close'])
            return True
        if command == 'review_advanced':
            OWNER.store('review_advanced', not OWNER.fetch('review_advanced', False))
            return True
        if command == 'browse_workspace':
            folder = ui.chooseFolder(title='Choose scan workspace', start=_field('workspace') or str(ROOT))
            if folder:
                OWNER.op('ui_panel/workspace/string').text = folder
                _status('Workspace selected. Check scan plan again before capture.')
            return True
        if command == 'add_view':
            filename = ui.chooseFile(load=True, fileTypes=['csv'], title='Add a MariMapper 2D view CSV',
                                     start=_field('workspace') or str(ROOT))
            if filename:
                paths = workflow.view_paths(_field('views') + ' | ' + filename)
                _set_views(paths)
                _status('%d view file(s) selected. Prepare 3D validates their IDs; check that manually added views belong to this scan.' % len(paths))
            return True
        if command == 'open_saved_result':
            filename = ui.chooseFile(load=True, fileTypes=['csv'], title='Open saved candidate_3d.csv',
                                     start=_field('workspace') or str(ROOT))
            if filename:
                from pixelblaze_mapper.scan_result_review import open_review
                open_review(op, path=filename)
            return True
        if command == 'discover_views':
            from pixelblaze_mapper.scan_library_ui import act as library_action
            return library_action(op, ui, 'open')
        if command == 'offline_start':
            manifest = OWNER.fetch('manifest', None)
            if not manifest:
                raise ValueError('PREPARE 3D OFFLINE JOB first')
            if OWNER.fetch('manifest_view_paths', None) != workflow.view_paths(_field('views')):
                raise ValueError('View list changed. PREPARE 3D again before starting the job')
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
            from pixelblaze_mapper.scan_result_review import open_review
            open_review(op)
            return True
        if command == 'review_add':
            from pixelblaze_mapper.scan_result_review import add_to_draft
            add_to_draft(op, lambda message: ui.messageBox('Raw scan to draft', message, buttons=['Cancel','Add to draft']) == 1)
            return True
        if command == 'review_back':
            OWNER.op('ui_panel').openViewer()
            return True
        if command == 'new_capture':
            OWNER.op('new_capture_panel').openViewer()
            return True
        if command == 'stage_capture':
            _require_idle()
            def field(name):
                return field_text(OWNER.op('new_capture_panel/' + name + '/string'))
            settings = {name:field(name) for name in ('name','target','interface','universe','count','rate','order')}
            for name in ('universe','count','rate'):
                settings[name] = int(settings[name])
            frame_values = {name: field(name) for name in ('frame_start_universe', 'frame_universe_count')}
            if any(frame_values.values()):
                if not all(frame_values.values()):
                    raise ValueError('Enter both controller frame start and universe count, or leave both blank')
                settings.update({name: int(value) for name, value in frame_values.items()})
            state = live.stage_standalone(op, settings)
            OWNER.store('workflow_page', 'capture')
            OWNER.store('capture_status', {})
            OWNER.store('offline_status', {})
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
            answer = ui.messageBox('Start one MariMapper view?', message + '\n\nThis switches ALL reserved universes of the listed controllers to black, then scans selected LEDs at the selected scan brightness (1-10%). Camera and object must stay fixed. No automatic Live resume. Continue?', buttons=['Cancel', 'Start Scan'])
            if answer == 1:
                live.start(op, confirmed=True)
        elif command == 'offline':
            _require_idle()
            filenames = workflow.view_paths(_field('views'))
            if len(filenames) < 2:
                raise ValueError('Capture or select at least two distinct view CSV files before preparing a 3D job')
            scoped = offline_scope(state, _field('source_ids'), _field('anchors'))
            candidate, views = attach_existing_views(scoped, filenames)
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
            OWNER.store('manifest_view_paths', filenames)
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
        if command.startswith('review_') and OWNER.op('review_panel/notice') is not None:
            OWNER.op('review_panel/notice').par.text = 'BLOCKED | ' + str(error)
        if command == 'stage_capture' and OWNER.op('new_capture_panel/notice') is not None:
            OWNER.op('new_capture_panel/notice').par.text = 'BLOCKED | ' + str(error)
        return False
    finally:
        workflow.refresh(OWNER)
'''.replace('__PROJECT_ROOT__', repr(str(ROOT)))


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
    canvas = panel(node(owner, containerCOMP, 'ui_panel'), 0, 0, 1160, 900, 10)
    canvas.viewer = True
    def existing_label(name, fallback):
        existing = canvas.op(name)
        return str(existing.par.text.eval()) if existing is not None else fallback
    text(canvas, 'title', 'GUIDED SCAN | FULL OBJECT / SELECTED REGION', 20, 847, 1120, 36, 23)
    text(canvas, 'notice', '1 Check camera. 2 Select LEDs and review routing. 3 START SCAN captures ONE view. Move camera between views; never during a scan.', 20, 799, 1120, 42, 13)
    old_coverage = canvas.op('coverage')
    coverage_text = str(old_coverage.par.text.eval()) if old_coverage is not None else 'Coverage appears after selecting an object or acquisition.'
    text(canvas, 'coverage', coverage_text, 20, 680, 1120, 108, 13)
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
        control.par.colorr, control.par.colorg, control.par.colorb = .75, .85, .95
        click(owner, 'click_' + name, control, "op('runtime').module.act(%r)" % name)
    for name, label in (
            ('page_capture', '1  CAPTURE VIEWS'), ('page_offline', '2  BUILD 3D / SAVED SCANS'),
            ('page_settings', 'SETTINGS'), ('help', 'WORKFLOW HELP'),
            ('discover_views', 'FIND MATCHING VIEWS'), ('open_saved_result', 'OPEN SAVED 3D RESULT'),
            ('browse_workspace', 'BROWSE FOLDER'), ('add_view', 'ADD VIEW CSV')):
        control = button(canvas, 'btn_' + name, label, 20, 752, 280)
        control.par.colorr, control.par.colorg, control.par.colorb = .75, .85, .95
        click(owner, 'click_' + name, control, "op('runtime').module.act(%r)" % name)
    text(canvas, 'next_step', '', 20, 676, 1120, 64, 14, (.68, .90, 1))
    canvas.op('title').par.text = 'MARIMAPPER | SCAN WORKSPACE'
    canvas.op('notice').par.text = 'Capture views, build 3D, then review in Layout. Existing scan files stay available; Live output requires a separate start.'
    canvas.op('source_ids_label').par.text = 'LEDS TO SCAN — source indices, e.g. 0-49, 78 (original IDs are preserved)'
    canvas.op('workspace_label').par.text = 'WORKSPACE FOLDER — existing folder for saved views and 3D results'
    canvas.op('views_label').par.text = 'SELECTED 2D VIEWS — paths separated by |; matching saved views can be added below'
    canvas.op('anchors_label').par.text = 'OPTIONAL VERIFICATION ANCHORS — source indices; captured but never replaced'
    canvas.op('python_label').par.text = 'MARI MAPPER PYTHON — offline reconstruction interpreter'
    canvas.op('btn_offline').par.label = '1  PREPARE 3D'
    canvas.op('btn_offline_start').par.label = '2  START 3D'
    canvas.op('btn_offline_result').par.label = '3  REVIEW RESULT'
    canvas.op('btn_new_capture').par.label = 'NEW ACQUISITION'
    canvas.op('btn_stop').par.bgcolorr = .55
    canvas.op('btn_stop').par.bgcolorg = .12
    canvas.op('btn_stop').par.bgcolorb = .12
    canvas.op('btn_stop').par.colorr, canvas.op('btn_stop').par.colorg, canvas.op('btn_stop').par.colorb = .95, .35, .35
    canvas.op('btn_offline_stop').par.bgcolorr = .55
    canvas.op('btn_offline_stop').par.bgcolorg = .12
    canvas.op('btn_offline_stop').par.bgcolorb = .12
    canvas.op('btn_offline_stop').par.colorr, canvas.op('btn_offline_stop').par.colorg, canvas.op('btn_offline_stop').par.colorb = .95, .35, .35
    text(canvas, 'camera_status', existing_label('camera_status', 'CAMERA NOT TESTED'), 20, 529, 480, 32, 11)
    existing = canvas.op('brightness/string')
    field(canvas, 'brightness', field_text(existing) if existing is not None else '5', 510, 529, 100)
    slider = button(canvas, 'brightness_slider', 'SCAN BRIGHTNESS % | 1 — drag — 10', 625, 529, 515)
    position = "__import__('pixelblaze_mapper.guided_scan_live', fromlist=['brightness_position']).brightness_position(op)"
    fill = text(canvas, 'brightness_fill', '', 625, 529, 1, 7)
    fill.par.layer = 61
    fill.par.bgcolorr, fill.par.bgcolorg, fill.par.bgcolorb = .18, .65, .85
    fill.par.w.expr = '1005 * (' + position + ')'
    marker = text(canvas, 'brightness_marker', '', 625, 529, 3, 36)
    marker.par.layer = 62
    marker.par.bgcolorr, marker.par.bgcolorg, marker.par.bgcolorb = .9, .96, 1
    marker.par.x.expr = '135 + 1002 * (' + position + ')'
    expression = "__import__('pixelblaze_mapper.guided_scan_live', fromlist=['set_scan_brightness']).set_scan_brightness(op, float(op(%r).panel.u))" % slider.path
    callback = click(owner, 'click_brightness', slider, expression)
    callback.par.panelvalue = 'lselect u'
    callback.par.valuechange = True
    callback.text = 'def onOffToOn(panelValue):\n    ' + expression + '\ndef onValueChange(panelValue):\n    if op(%r).panel.lselect:\n        ' % slider.path + expression + '\n'
    text(canvas, 'routing_summary', existing_label('routing_summary', 'Routing not checked. Controller / Ports opens the existing universe configuration.'), 20, 188, 1120, 38, 11)
    text(canvas, 'capabilities', '', 600, 90, 540, 1, 11)
    text(canvas, 'offline_status', existing_label('offline_status', '3D: not started | no automatic layout replacement'), 20, 64, 1120, 26, 11)
    text(canvas, 'status', owner.fetch('message', 'Open Scan from Layout to stage an object. No camera or LED output is started.'), 20, 12, 1120, 46, 12)
    poller = node(owner, executeDAT, 'capture_poll')
    poller.text = "from pixelblaze_mapper import guided_scan_live as live\nfrom pixelblaze_mapper import scan_offline_job as offline_job\ndef onFrameStart(frame):\n    live.poll(op)\n    if frame % 30 == 0: offline_job.poll(op)\ndef onStart():\n    live.shutdown()\n    offline_job.stop()\ndef onExit():\n    live.shutdown()\n    offline_job.stop()\n"
    poller.par.active = True
    poller.text += "\n# Read-only coverage refresh; no camera or output calls.\n_base_frame = onFrameStart\ndef onFrameStart(frame):\n    _base_frame(frame)\n    if frame % 60 == 0:\n        from pixelblaze_mapper.scan_coverage import refresh\n        refresh(op)\n"
    poller.par.framestart = True
    poller.par.exit = True
    poller.par.start = True
    poller.text += "\n# Navigation and next-step hints read stored facts only.\n_scan_frame = onFrameStart\ndef onFrameStart(frame):\n    _scan_frame(frame)\n    if frame % 30 == 0:\n        from pixelblaze_mapper.scan_workflow_ux import refresh\n        refresh(op('/project1/guided_scan'))\n"
    fresh = panel(node(owner, containerCOMP, 'new_capture_panel'), 0, 0, 820, 640, 10)
    fresh.viewer = True
    text(fresh, 'title', 'NEW ACQUISITION | NO LAYOUT ASSIGNMENT', 20, 580, 780, 40, 20)
    entries = [('name','CAPTURE','CAPTURE NAME'), ('target','','CONTROLLER IPv4'),
               ('interface','','LOCAL IPv4 INTERFACE'), ('universe','0','PANEL START UNIVERSE (ZERO-BASED)'),
               ('count','256','LED COUNT (LOCAL 0..COUNT-1)'), ('rate','30','FPS LIMIT'),
               ('order','RGB','NETWORK COLOR ORDER (not LED wiring)'),
               ('frame_start_universe','','CONTROLLER FRAME START (optional)'),
               ('frame_universe_count','','CONTROLLER UNIVERSE COUNT (optional)')]
    for index,(name,value,label) in enumerate(entries):
        x,y = 20+(index%2)*400, 505-(index//2)*82
        existing = fresh.op(name+'/string')
        if existing is not None:
            value = field_text(existing)
        text(fresh,name+'_label',label,x,y+32,380,27,11)
        field(fresh,name,value,x,y,380)
    text(fresh,'notice','Optional controller range: fill BOTH fields to send companion universes black. Leave both blank for this panel only. Creates IDs and routing; no camera or LED output.',20,67,780,84,12)
    control = button(fresh,'btn_stage','CREATE ACQUISITION (OUTPUT OFF)',20,20,780)
    click(owner,'click_stage_capture',control,"op('runtime').module.act('stage_capture')")
    review = panel(node(owner, containerCOMP, 'review_panel'), 0, 0, 1000, 710, 10)
    review.viewer = True
    text(review, 'title', '3D RESULT REVIEW | RAW SCAN TO DRAFT', 20, 660, 960, 35, 21)
    summary = 'Open a completed 3D result first.'
    saved_review = owner.fetch('result_review', None)
    if saved_review:
        from pixelblaze_mapper.scan_result_review import format_review_summary
        summary = format_review_summary(saved_review)
    text(review, 'summary', summary, 20, 485, 960, 170, 12)
    for name, label, value, x, width in (
            ('name','NEW OBJECT NAME','Raw scan',20,460),
            ('offset','GLOBAL SOURCE OFFSET (added to original scan ID)','',500,480)):
        text(review,name+'_label',label,x,450,width,26,11)
        existing=review.op(name+'/string')
        field(review,name,field_text(existing) if existing is not None else value,x,420,width)
    for row,(prefix,label,default) in enumerate((('t','TRANSLATION',0),('r','ROTATION DEGREES',0),('s','SCALE',1))):
        for column,axis in enumerate('xyz'):
            name=prefix+axis; x=20+column*320; y=302-row*70
            text(review,name+'_label',label+' '+axis.upper(),x,y+31,300,26,11)
            existing=review.op(name+'/string')
            field(review,name,field_text(existing) if existing is not None else str(default),x,y,300)
    text(review,'notice','X=height, Y=right, Z=depth. Missing IDs keep gaps. Existing objects and live routing stay unchanged. Fine alignment in Layout 3D; Undo removes the draft addition.',20,78,960,72,12)
    for name,label,x,width in (('review_add','ADD AS NEW DRAFT OBJECT',20,600),('review_back','BACK TO GUIDED SCAN',640,340)):
        control=button(review,'btn_'+name,label,x,30,width)
        click(owner,'click_'+name,control,"op('runtime').module.act(%r)"%name)
    control = button(review, 'btn_review_advanced', 'ALIGNMENT SETTINGS (OPTIONAL)', 20, 375, 960)
    click(owner, 'click_review_advanced', control, "op('runtime').module.act('review_advanced')")
    text(review, 'alignment_hint', '', 20, 188, 960, 170, 13)
    from pixelblaze_mapper.scan_workflow_ux import refresh
    plan = owner.fetch('capture_plan', None)
    if plan and plan.get('routing'):
        from pixelblaze_mapper.scan_routing import ScanRoutingSnapshot
        try:
            routing = ScanRoutingSnapshot.from_dict(plan['routing'])
            frames = routing.packet_descriptors()
            lines = []
            for name in routing.controller_names:
                selected = [frame for frame in frames if frame.controller == name]
                lines.append('%s %s | Art-Net U%d-U%d (zero-based)' %
                             (name, selected[0].target_address, selected[0].wire_universe, selected[-1].wire_universe))
            canvas.op('routing_summary').par.text = '%d LEDs | scan %.1f%% | %s' % (
                len(routing.source_indices), routing.brightness_cap * 100, '; '.join(lines))
        except (ValueError, KeyError, TypeError, IndexError):
            canvas.op('routing_summary').par.text = 'Saved plan could not be read. Check scan plan again.'
    refresh(owner)
    from pixelblaze_mapper import scan_coverage
    scan_coverage._last_key = None
    scan_coverage.refresh(op)
    from pixelblaze_mapper.led_search import install as install_led_search
    install_led_search(globals())
    from pixelblaze_mapper.scan_library_ui import install as install_library
    install_library(globals())
    from pixelblaze_mapper.scan_registration_ui import install as install_registration
    install_registration(globals())
    from pixelblaze_mapper.scan_ui_style import install as install_scan_style
    install_scan_style(owner)
    return owner


if globals().get('__name__') == '__main__' and 'op' in globals():
    build()
