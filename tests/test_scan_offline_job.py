import json
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_scan_worker import ScanWorkerTests
from pixelblaze_mapper.scan_offline_job import OfflineJob


class OfflineJobTests(ScanWorkerTests):
    def launch(self):
        path = self.root / 'manifest.json'
        path.write_text(json.dumps(self.manifest()), encoding='utf-8')
        exe = self.root / 'python.exe'
        exe.touch()
        self.code = None
        self.killed = False
        def kill():
            self.killed = True
            self.code = -9
        process = SimpleNamespace(poll=lambda: self.code, kill=kill)
        with patch('subprocess.Popen', return_value=process) as launch:
            job = OfflineJob(exe, path, confirmed=True)
        self.addCleanup(job.log.close)
        self.addCleanup(job.deadline.cancel)
        args, kwargs = launch.call_args
        self.assertFalse(kwargs['shell'])
        self.assertEqual(args[0][1:3], ['-m', 'pixelblaze_mapper.scan_worker'])
        self.assertEqual(args[0][-1], '--confirm-offline-reconstruction')
        return job

    def output(self, job, ids=(10,42)):
        job.output.mkdir()
        (job.output/'candidate_3d.csv').write_text('index,x,y,z,xn,yn,zn,error\n' + ''.join('%d,0,1,2,0,0,0,0.1\n'%i for i in ids))
        (job.output/'quality_pending.json').write_text(json.dumps({'session_id':'s','reconstructed_ids':list(ids)}))

    def test_completed_job_reports_sparse_candidate_not_apply(self):
        job = self.launch()
        self.assertTrue(job.poll()['running'])
        self.output(job)
        self.code = 0
        state = job.poll()
        self.assertEqual(state['state'], 'review_required')
        self.assertEqual(state['missing_ids'], [99])
        self.assertFalse(state['layout_applied'])
        self.assertFalse(state['registration'])
        self.assertTrue(job.log.closed)

    def test_failed_process_is_not_ready(self):
        job = self.launch()
        self.code = 1
        self.assertEqual(job.poll()['state'], 'failed')

    def test_invalid_result_rejected(self):
        job = self.launch()
        self.output(job, (10,111))
        self.code = 0
        self.assertEqual(job.poll()['state'], 'failed')

    def test_timeout_kills_only_owned_worker(self):
        job = self.launch()
        with patch('time.monotonic', return_value=job.started+301):
            self.assertEqual(job.poll()['state'], 'timeout')
        self.assertTrue(self.killed)

    def test_cancel_never_publishes_result(self):
        job = self.launch()
        job.stop()
        self.assertEqual(job.poll()['state'], 'cancelled')
        self.assertNotIn('candidate', job.status)

    def test_confirmation_before_any_launch(self):
        with patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'confirmation'):
                OfflineJob('missing', 'missing')
            launch.assert_not_called()
