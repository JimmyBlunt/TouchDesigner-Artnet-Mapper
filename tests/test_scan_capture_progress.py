import unittest
from unittest.mock import patch
from pixelblaze_mapper.scan_capture_progress import presentation, refresh, ScanRate
from tests.test_guided_scan_live import Owner
from types import SimpleNamespace

class CaptureProgressTests(unittest.TestCase):
    def test_rate_uses_completed_leds_including_misses(self):
        meter = ScanRate()
        def state(n):
            return dict(state='capturing', directory='view-a', processed=n, detected=0)
        self.assertIsNone(meter.update(state(100), 0))
        self.assertAlmostEqual(meter.update(state(106), 2), 3)
        self.assertAlmostEqual(meter.update(state(118), 6), 3)
        self.assertIn('3,00 LEDs/s', presentation(state(118), 880, 3)['text'])

    def test_live_rate_falls_to_zero_during_stall(self):
        meter = ScanRate()
        for now in range(5):
            meter.update(dict(state='capturing', directory='a', processed=now*3), now)
        for now in range(5, 15):
            rate = meter.update(dict(state='capturing', directory='a', processed=12), now)
        self.assertEqual(rate, 0)

    def test_final_rate_freezes_and_new_view_resets(self):
        meter = ScanRate()
        meter.update(dict(state='capturing',directory='a',processed=0),0)
        self.assertEqual(meter.update(dict(state='capturing',directory='a',processed=8),2),4)
        self.assertEqual(meter.update(dict(state='complete',directory='a',processed=8),40),4)
        self.assertIsNone(meter.update(dict(state='capturing',directory='b',processed=0),41))

    def test_rate_window_ignores_older_fast_segment(self):
        meter = ScanRate()
        for now in range(21):
            count = now*5 if now<=10 else 50+(now-10)
            value = meter.update(dict(state='capturing',directory='a',processed=count),now)
        self.assertAlmostEqual(value,1)
        self.assertLessEqual(len(meter.samples), 12)

    def test_repeated_ui_refresh_does_not_invent_measurement(self):
        meter=ScanRate()
        status=dict(state='capturing',directory='a',processed=30)
        meter.update(status,5)
        self.assertIsNone(meter.update(status,5))
        self.assertEqual(len(meter.samples),1)

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
