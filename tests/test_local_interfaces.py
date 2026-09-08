import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pixelblaze_mapper import local_interfaces as module


class LocalInterfaceTests(unittest.TestCase):
    def test_single_and_empty(self):
        self.assertEqual(module.parse_interfaces('null'),[])
        self.assertEqual(module.parse_interfaces('{"IPAddress":"10.0.0.125","InterfaceAlias":"Ethernet 3"}'),
                         [{'address':'10.0.0.125','name':'Ethernet 3'}])

    def test_deduplicate_and_keep_virtual_interface_labels(self):
        rows=module.parse_interfaces('[{"IPAddress":"10.0.0.125","InterfaceAlias":"Ethernet"},{"IPAddress":"10.0.0.125","InterfaceAlias":"Duplicate"},{"IPAddress":"172.20.1.1","InterfaceAlias":"VPN"}]')
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[1]['name'],'VPN')

    def test_invalid_address_rejected(self):
        with self.assertRaises(ValueError): module.parse_interfaces('{"IPAddress":"bad","InterfaceAlias":"Unknown"}')

    def test_worker_timeout_becomes_error_not_ui_exception(self):
        with patch.object(module.subprocess,'run',side_effect=TimeoutError('timeout')):
            module._worker()
        self.assertEqual(module.take_result(),{'interfaces':[],'error':'timeout'})
        self.assertIsNone(module.take_result())

    def test_fixed_readonly_query_without_shell_and_bounded_timeout(self):
        with patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='null')) as run:
            module._worker()
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.kwargs['timeout'],12)
        self.assertIn('Get-NetIPAddress',run.call_args.args[0][-1])
        self.assertEqual(module.take_result(),{'interfaces':[],'error':''})

    def test_failed_query_does_not_report_available_interfaces(self):
        with patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='null')):
            module._worker()
        self.assertTrue(module.take_result()['error'])
