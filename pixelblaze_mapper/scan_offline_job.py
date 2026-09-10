"""Bounded isolated SfM job. No cameras, sockets, routing or automatic merge."""
import csv
import json
import math
from pathlib import Path
import subprocess
import time
import threading
from uuid import uuid4

from .scan_worker import load_observations


class OfflineJob:
    def __init__(self, interpreter, manifest_path, *, confirmed=False):
        if confirmed is not True:
            raise ValueError('Explicit offline reconstruction confirmation required')
        executable = Path(interpreter).resolve(strict=True)
        if executable.name.lower() != 'python.exe' or not executable.is_file():
            raise ValueError('Select the installed MariMapper python.exe')
        checked, observations = load_observations(json.loads(Path(manifest_path).read_text(encoding='utf-8')))
        self.document = checked
        self.allowed = {row[0] for row in observations}
        self.output = Path(checked['output_directory'])
        self.started = time.monotonic()
        self.process = None
        self.status = {'state': 'starting', 'running': False, 'output': str(self.output),
                       'session_id': checked['session']['session_id'], 'review_required': True}
        workspace = Path(checked['workspace_root'])
        stem = 'offline-job-' + str(uuid4())
        frozen = workspace / (stem + '.json')
        with frozen.open('x', encoding='utf-8') as stream:
            json.dump(checked, stream, indent=2)
        self.log_path = workspace / (stem + '.log')
        self.status['log'] = str(self.log_path)
        self.log = self.log_path.open('xb')
        try:
            self.process = subprocess.Popen(
                [str(executable), '-m', 'pixelblaze_mapper.scan_worker', str(frozen),
                 '--confirm-offline-reconstruction'],
                cwd=str(Path(__file__).resolve().parents[1]), stdin=subprocess.DEVNULL,
                stdout=self.log, stderr=subprocess.STDOUT, shell=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            self.log.close()
            raise
        self.status.update(state='running', running=True)
        self.deadline = threading.Timer(300, self.stop, args=('timeout',))
        self.deadline.daemon = True
        self.deadline.start()

    def stop(self, reason='cancelled'):
        if self.process.poll() is None:
            self.process.kill()
            self.status['stop_reason'] = reason

    def poll(self):
        if not self.status['running']:
            return dict(self.status)
        self.status['elapsed_seconds'] = round(time.monotonic() - self.started, 1)
        if self.status['elapsed_seconds'] > 300 and not self.status.get('stop_reason'):
            self.stop('timeout')
        code = self.process.poll()
        if code is None:
            return dict(self.status)
        self.log.close()
        self.deadline.cancel()
        self.status.update(running=False, exit_code=code)
        if self.status.get('stop_reason'):
            self.status['state'] = self.status['stop_reason']
        elif code:
            self.status.update(state='failed', error='Worker failed; see log: ' + str(self.log_path))
        else:
            try:
                report = json.loads((self.output / 'quality_pending.json').read_text(encoding='utf-8'))
                candidate = self.output / 'candidate_3d.csv'
                with candidate.open(encoding='utf-8-sig', newline='') as stream:
                    reader = csv.DictReader(stream)
                    if reader.fieldnames != ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error']:
                        raise ValueError('Invalid candidate columns')
                    rows = list(reader)
                ids = [int(row['index']) for row in rows]
                if (not ids or len(set(ids)) != len(ids) or not set(ids) <= self.allowed
                    or sorted(ids) != report['reconstructed_ids']
                    or report['session_id'] != self.status['session_id']
                    or any(None in row or any(not math.isfinite(float(row[axis]))
                           for axis in ('x','y','z','xn','yn','zn','error')) for row in rows)):
                    raise ValueError('Candidate identity/coordinates do not match the job')
                self.status.update(state='review_required', candidate=str(candidate),
                    reconstructed=len(ids), missing_ids=sorted(self.allowed - set(ids)),
                    coordinate_units='arbitrary_sfm', registration=False, layout_applied=False)
            except Exception as error:
                self.status.update(state='failed', error='Invalid worker result: ' + str(error))
        return dict(self.status)


_job = None  # Never put a process or handle in OP.store.


def start(op, interpreter, manifest, *, confirmed=False):
    global _job
    if _job is not None and _job.poll()['running']:
        raise ValueError('A 3D reconstruction is already running')
    from .guided_scan_live import assert_outputs_off, _capture
    assert_outputs_off(op)
    if _capture is not None and _capture.process.poll() is None:
        raise ValueError('Finish the camera scan first')
    session = op('/project1/guided_scan').fetch('session', None)
    planned = json.loads(Path(manifest).read_text(encoding='utf-8'))['session']
    if session != planned:
        # JSON roundtrip removes tuple/list differences from OP.store.
        if json.loads(json.dumps(session)) != planned:
            raise ValueError('Scan selection changed; prepare a new offline job')
    from .build_scan_session_ui import parse_indices, field_text
    lookup = {target['led_id']: target['source_index'] for target in planned['targets']}
    for field, key in (('source_ids', 'selected_ids'), ('anchors', 'anchor_ids')):
        value = field_text(op('/project1/guided_scan').op('ui_panel/' + field + '/string'))
        indices = set(parse_indices(value)) if value else set()
        if indices != {lookup[item] for item in planned[key]}:
            raise ValueError('Scan fields changed; prepare a new offline job')
    _job = OfflineJob(interpreter, manifest, confirmed=confirmed)
    poll(op)


def stop():
    if _job is not None:
        _job.stop()


def poll(op):
    if _job is None:
        return
    owner = op('/project1/guided_scan')
    status = _job.poll()
    previous = owner.fetch('offline_status', {}) or {}
    if previous == status:
        return
    owner.store('offline_status', status)
    node = owner.op('offline_result')
    if node is not None:
        node.text = json.dumps(status, indent=2)
    label = owner.op('ui_panel/offline_status')
    if label is not None:
        label.par.text = '3D: %s | %ss | %s' % (status['state'], status.get('elapsed_seconds', 0),
            ('%s LEDs; raw SfM, align/review in Layout before apply' % status['reconstructed'])
            if 'reconstructed' in status else status.get('error', 'no camera / no LED output / no automatic merge'))
    if (previous.get('output'), previous.get('state')) != (status.get('output'), status['state']):
        message = ('3D RESULT READY | %s reconstructed LEDs; review alignment before adding to the draft.' % status['reconstructed']
                   if status['state'] == 'review_required' else
                   '3D JOB: %s%s' % (status['state'], ' | ' + status['error'] if status.get('error') else ''))
        owner.store('message', message)
        action = owner.op('ui_panel/status')
        if action is not None:
            action.par.text = message
