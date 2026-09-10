import unittest
from unittest.mock import patch
from pixelblaze_mapper.scan_capture_progress import presentation, refresh
from tests.test_guided_scan_live import Owner
from types import SimpleNamespace

class CaptureProgressTests(unittest.TestCase):
    def test_processed_not_detected_drives_progress(self):
        value=presentation(dict(state='capturing',processed=420,detected=395,total=880,current_index=420,current_source_index=700))
        self.assertIn('420 / 880',value['text'])
        self.assertIn('Erkannt 395',value['text'])
        self.assertIn('Nicht erkannt 25',value['text'])
        self.assertIn('47,7 %',value['text'])
        self.assertIn('LED-ID 700 (Position 421 von 880)',value['text'])
        self.assertAlmostEqual(value['fraction'],420/880)

    def test_idle_and_next_view_reset(self):
        self.assertIn('0 / 880',presentation(planned_total=880)['text'])
        self.assertEqual(presentation(dict(state='starting',total=880))['fraction'],0)
        self.assertEqual(presentation()['fraction'],0)

    def test_cancel_keeps_unprocessed_out_of_failed_count(self):
        value=presentation(dict(state='cancelled',total=880,processed=42,detected=40))
        self.assertIn('ABGEBROCHEN',value['text'])
        self.assertIn('Nicht erkannt 2',value['text'])
        self.assertAlmostEqual(value['fraction'],42/880)

    def test_last_led_is_not_yet_a_saved_view(self):
        data=dict(total=3,processed=3,detected=2)
        self.assertIn('Bewegungskontrolle',presentation(dict(data,state='movement_check'))['text'])
        self.assertNotIn('GESPEICHERT',presentation(dict(data,state='movement_check'))['text'])
        self.assertIn('GESPEICHERT',presentation(dict(data,state='complete'))['text'])

    def test_ui_consumes_stored_counts_without_hardware(self):
        owner=Owner()
        owner.store('capture_status',dict(state='capturing',processed=1,detected=0,total=2,current_index=1,current_source_index=500))
        owner.children['ui_panel/capture_progress']=SimpleNamespace(par=SimpleNamespace())
        fill=SimpleNamespace(par=SimpleNamespace())
        owner.children['ui_panel/capture_progress_track']=SimpleNamespace(op=lambda name:fill)
        with patch('socket.socket',side_effect=AssertionError('hardware')), patch('subprocess.Popen',side_effect=AssertionError('hardware')):
            refresh(owner)
        self.assertEqual(fill.par.w,560)
        self.assertTrue(fill.par.display)
        self.assertIn('LED-ID 500',owner.op('ui_panel/capture_progress').par.text)

if __name__=='__main__': unittest.main()
