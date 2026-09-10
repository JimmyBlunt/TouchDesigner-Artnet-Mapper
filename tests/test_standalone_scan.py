import unittest
from unittest.mock import patch
from pixelblaze_mapper import standalone_scan, guided_scan_live, scan_capture
from pixelblaze_mapper.scan_routing import create_snapshot, ScanRoutingSnapshot
from tests.test_guided_scan_live import GuidedScanLiveTests

SETTINGS = dict(name='TEST_249',target='10.0.0.249',interface='10.0.0.125',universe=120,
                count=256,rate=30,order='RGB')


class StandaloneTests(unittest.TestCase):
    def test_panel_two_targets_and_companion_black_frames(self):
        settings = dict(SETTINGS, count=738, universe=122,
                        frame_start_universe=120, frame_universe_count=7)
        selected = (0,169,170,340,510,737)
        with patch('socket.socket', side_effect=AssertionError('No hardware')):
            snapshot = create_snapshot(standalone_scan.routing(settings), selected, brightness_cap=.05)
        self.assertEqual([(t.wire_universe,t.slot) for t in snapshot.targets],
                         [(122,0),(122,507),(123,0),(124,0),(125,0),(126,171)])
        for index in range(len(selected)):
            frames = snapshot.packet_descriptors(index,on=True)
            self.assertEqual([f.wire_universe for f in frames], list(range(120,127)))
            self.assertFalse(any(frames[0].payload + frames[1].payload))
            self.assertEqual(sum(value != 0 for f in frames for value in f.payload),3)

    def test_controller_frame_settings_require_complete_valid_envelope(self):
        base = dict(SETTINGS,count=738,universe=122,frame_start_universe=120,frame_universe_count=7)
        for changes in ({'frame_start_universe':True}, {'frame_universe_count':False},
                        {'frame_start_universe':123}, {'frame_start_universe':-1},
                        {'frame_universe_count':6}, {'frame_universe_count':32768}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                standalone_scan.routing(dict(base,**changes))
        for key in ('frame_start_universe','frame_universe_count'):
            settings=base.copy();del settings[key]
            with self.assertRaises(ValueError):standalone_scan.routing(settings)

    def test_exact_port_boundary_and_no_other_controller(self):
        with patch('socket.socket',side_effect=AssertionError('No hardware')):
            config = standalone_scan.routing(SETTINGS)
            snapshot = create_snapshot(config,tuple(range(256)),brightness_cap=.05)
        self.assertEqual(snapshot.controller_names,('TEST_249',))
        self.assertEqual([(snapshot.targets[i].wire_universe,snapshot.targets[i].slot) for i in (0,169,170,255)],
                         [(120,0),(120,507),(121,0),(121,255)])
        self.assertEqual(len(snapshot.black_frames()['TEST_249']),2)

    def test_stable_ids_within_session_unique_between_acquisitions(self):
        a,b = standalone_scan.session(SETTINGS),standalone_scan.session(SETTINGS)
        self.assertEqual([t.source_index for t in a.targets],list(range(256)))
        self.assertFalse(set(a.selected_ids)&set(b.selected_ids))
        self.assertEqual(a.scene_revision,b.scene_revision)

    def test_bad_settings_fail_before_io(self):
        for key,value in [('count',0),('count',True),('universe',-1),('universe',32767),
                          ('target','not-an-ip'),('rate',0),('order','BAD')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                standalone_scan.routing(dict(SETTINGS,**{key:value}))


class StandaloneBridgeTests(GuidedScanLiveTests):
    def test_normal_prepare_preserves_full_controller_envelope(self):
        settings = dict(SETTINGS,count=738,universe=122,frame_start_universe=120,frame_universe_count=7)
        guided_scan_live.stage_standalone(self.op,settings)
        summary=self.prepare()
        checked=scan_capture.validate_capture_manifest(self.owner.fetch('capture_plan'))
        snapshot=ScanRoutingSnapshot.from_dict(checked['routing'])
        self.assertEqual(len(snapshot.targets),738)
        self.assertEqual(len(snapshot.black_frames()['TEST_249']),7)
        self.assertIn('PANEL U122-U126',summary)
        self.assertIn('SEND U120-U126',summary)
        self.assertEqual(snapshot.targets[-1].slot,171)
        self.no_process.assert_not_called()
        self.no_socket.assert_not_called()

    # Inherit baseline regressions too: old layout-bound flow must still work.
    def test_prepare_separate_ignores_live_source_namespace_without_mutating_router(self):
        before={k:v.text for k,v in self.nodes.items() if k.endswith(('controller_config','segment_config'))}
        guided_scan_live.stage_standalone(self.op,SETTINGS)
        summary=self.prepare()
        plan=self.owner.fetch('capture_plan')
        checked=scan_capture.validate_capture_manifest(plan)
        snapshot=ScanRoutingSnapshot.from_dict(checked['routing'])
        self.assertEqual(snapshot.config.source_pixel_count,256)
        self.assertEqual(snapshot.config.controllers[0].start_universe,120)
        self.assertEqual(len(checked['identity']),256)
        self.assertIn('SEPARATE CAPTURE',summary)
        self.assertEqual(before,{k:self.nodes[k].text for k in before})
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()

    def test_changed_separate_settings_block_start(self):
        guided_scan_live.stage_standalone(self.op,SETTINGS)
        self.prepare()
        self.owner.store('standalone_capture',dict(SETTINGS,universe=122))
        with patch.object(scan_capture,'start_capture') as launch:
            with self.assertRaisesRegex(RuntimeError,'Prepare'):
                guided_scan_live.start(self.op,confirmed=True)
            launch.assert_not_called()

    def test_invalid_new_settings_do_not_replace_previous_session(self):
        before=self.owner.fetch('session')
        with self.assertRaises(ValueError):
            guided_scan_live.stage_standalone(self.op,dict(SETTINGS,count=0))
        self.assertEqual(self.owner.fetch('session'),before)
