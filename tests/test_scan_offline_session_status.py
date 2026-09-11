import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pixelblaze_mapper import scan_offline_job


class OfflineSessionStatusTests(unittest.TestCase):
    def poll_session(self, session_id):
        values={'session':{'session_id':session_id},'offline_status':{}}
        owner=SimpleNamespace(fetch=lambda key,default=None:values.get(key,default),
                              store=lambda key,value:values.__setitem__(key,value),
                              op=lambda path:None)
        status={'session_id':'panel-3','state':'review_required','running':False,
                'output':'panel-3-result','reconstructed':880}
        with patch.object(scan_offline_job,'_job',SimpleNamespace(poll=lambda:dict(status))):
            scan_offline_job.poll(lambda path:owner)
        return values

    def test_finished_previous_panel_cannot_repopulate_new_panel_status(self):
        result=self.poll_session('panel-4')
        self.assertEqual(result['offline_status'],{})
        self.assertNotIn('message',result)

    def test_current_session_publishes_completed_result(self):
        result=self.poll_session('panel-3')
        self.assertEqual(result['offline_status']['reconstructed'],880)
        self.assertIn('880',result['message'])
