"""Overlap editing acceptance; legacy documents remain explicitly unmigrated."""
from copy import deepcopy
import json
import unittest

from pixelblaze_mapper import show_timeline as timeline
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer, timeline_rows
from pixelblaze_mapper.show_timeline_ui import Bridge
from tests.test_show_timeline import sample, FakeHost


class OverlapTimelineTests(unittest.TestCase):
    def setUp(self):
        self.show, self.data = sample()
        self.cue = self.show['cues'][0]['id']

    def migrate(self):
        self.show, self.data = timeline.edit(self.show, self.data, dict(action='enable_overlap'))

    def test_explicit_migration_preserves_duration_tracks_and_creates_independent_fades(self):
        before = deepcopy((self.show, self.data))
        self.migrate()
        self.assertNotIn('timing_mode', before[0])
        self.assertEqual(self.show['timing_mode'], 'overlap')
        self.assertEqual([c['duration'] for c in self.show['cues']], [12,12,12])
        self.assertEqual([c.get('fade_in',0) for c in self.show['cues']], [0,3,3])
        self.assertEqual([c.get('fade_out',0) for c in self.show['cues']], [3,3,3])
        self.assertEqual(self.data, before[1])
        self.assertEqual(timeline.edit(self.show, self.data, dict(action='enable_overlap')), (self.show,self.data))

    def test_shared_rows_real_start_offsets_and_seek_earliest_active(self):
        self.migrate()
        rows = timeline.layout(self.show)
        self.assertEqual(rows, timeline_rows(Show.from_dict(self.show)))
        self.assertEqual([r['start'] for r in rows], [0,9,18])
        self.assertEqual(rows[-1]['end'],30)
        self.assertEqual(timeline.locate(self.show,9.5),(0,9.5))
        self.assertEqual(timeline.locate(self.show,12),(1,3))
        self.assertEqual(timeline.locate(self.show,21),(2,3))

    def test_requested_overlaps_are_clamped_by_shared_core_without_three_active_clips(self):
        for cue in self.show['cues']:
            cue['transition_duration'] = 12
        self.migrate()
        rows = timeline.layout(self.show)
        self.assertLess(rows[0]['overlap_out'],12)
        self.assertLessEqual(rows[1]['overlap_in']+rows[1]['overlap_out'],12)
        self.assertEqual(rows[-1]['overlap_out'],0)
        for step in range(300):
            moment=step/10
            self.assertLessEqual(sum(r['start'] <= moment < r['end'] for r in rows),2)

    def test_edit_fades_changes_only_target_envelope_not_overlap_duration_or_recording(self):
        self.migrate()
        before = deepcopy((self.show,self.data))
        show,data=timeline.edit(self.show,self.data,dict(action='clip_fades',cue=self.cue,
            fade_in=2,fade_out=5,fade_in_curve='ease_in',fade_out_curve='smooth'))
        self.assertEqual(show['cues'][0]['fade_in'],2)
        self.assertEqual(show['cues'][0]['fade_out'],5)
        self.assertEqual(show['cues'][0]['transition_duration'],3)
        self.assertEqual(show['cues'][1:],self.show['cues'][1:])
        self.assertEqual(data,self.data)
        self.assertEqual((self.show,self.data),before)
        self.assertEqual(Show.from_dict(json.loads(json.dumps(show))).to_dict(),show)

    def test_invalid_fades_reject_atomically_and_legacy_requires_explicit_migration(self):
        with self.assertRaises(ValueError):
            timeline.edit(self.show,self.data,dict(action='clip_fades',cue=self.cue,fade_in=1))
        self.migrate()
        before=deepcopy((self.show,self.data))
        for fields in (dict(fade_in=-1),dict(fade_out=13),dict(fade_in=float('nan')),
                       dict(fade_out=float('inf')),dict(fade_in_curve='step'),dict(fade_out_curve=[])):
            with self.subTest(fields=fields),self.assertRaises(ValueError):
                timeline.edit(self.show,self.data,dict(action='clip_fades',cue=self.cue,**fields))
        self.assertEqual((self.show,self.data),before)

    def test_resize_clamps_fades_and_preserves_original_automation(self):
        self.migrate()
        show,data=timeline.edit(self.show,self.data,dict(action='resize',cue=self.cue,duration=1))
        self.assertLessEqual(show['cues'][0].get('fade_out',0),1)
        self.assertEqual(data,self.data)
        self.assertEqual(timeline.layout(show),timeline_rows(Show.from_dict(show)))

    def test_transition_grips_preserve_legacy_contract_but_move_true_next_start(self):
        self.migrate()
        show,data=timeline.edit(self.show,self.data,dict(action='transition',cue=self.cue,edge='start',time=5))
        self.assertEqual(show['cues'][0]['duration'],12)
        self.assertEqual(timeline.layout(show)[1]['start'],5)
        self.assertEqual(show['cues'][0]['fade_out'],3)
        self.assertEqual(data,self.data)
        show,_=timeline.edit(self.show,self.data,dict(action='transition',cue=self.cue,edge='end',time=16))
        self.assertEqual(show['cues'][0]['duration'],16)
        self.assertEqual(timeline.layout(show)[0]['fade_start'],9)
        self.assertEqual(timeline.layout(show)[1]['start'],9)

    def test_loop_validation_and_migration_use_actual_shortened_duration(self):
        self.data['loop_region']=dict(start=0,end=36,enabled=True)
        self.migrate()
        self.assertEqual(self.data['loop_region']['end'],30)
        with self.assertRaises(ValueError):
            timeline.edit(self.show,self.data,dict(action='loop',start=0,end=31,enabled=True))
        _,data=timeline.edit(self.show,self.data,dict(action='loop',start=9,end=20,enabled=True))
        sequence=ShowSequencer(Show.from_dict(self.show))
        sequence.play()
        sequence.seek(*timeline.locate(self.show,19))
        timeline.advance_with_loop(sequence,4,data)
        index,elapsed=timeline.locate(self.show,12)
        self.assertEqual((sequence.cue_index,sequence.elapsed),(index,elapsed))

    def test_migration_loop_remaps_late_endpoint_by_cue_local_time(self):
        self.data['loop_region']=dict(start=32,end=36,enabled=True)
        self.migrate()
        self.assertEqual(self.data['loop_region'],dict(start=26,end=30,enabled=True))

    def test_migration_inverted_local_loop_range_is_disabled_not_played_backwards(self):
        self.data['loop_region']=dict(start=11,end=13,enabled=True)
        self.migrate()
        self.assertEqual(self.data['loop_region'],dict(start=0,end=30,enabled=False))

    def test_bridge_migration_envelope_edit_undo_redo_and_save(self):
        host=FakeHost()
        host.data['loop_region']=dict(start=32,end=36,enabled=True)
        bridge=Bridge(host)
        def command(**kwargs):
            return bridge.execute(dict(kwargs,revision=bridge.state['revision']))
        original=deepcopy(host.show)
        command(action='enable_overlap')
        self.assertEqual(bridge.state['rows'][1]['start'],9)
        self.assertEqual(host.data['loop_region'],dict(start=26,end=30,enabled=True))
        command(action='clip_fades',cue=host.show['cues'][1]['id'],fade_in=1,fade_out=4)
        command(action='undo')
        self.assertEqual(host.show['cues'][1]['fade_in'],3)
        command(action='undo')
        self.assertEqual(host.show,original)
        self.assertEqual(host.data['loop_region'],dict(start=32,end=36,enabled=True))
        command(action='redo');command(action='redo');command(action='save')
        self.assertEqual(host.saved[0]['cues'][1]['fade_in'],1)

    def test_empty_new_show_and_explicit_empty_migration_render_without_core_parse(self):
        from pixelblaze_mapper import show_editor, show_automation
        empty=show_editor.empty_show()
        self.assertEqual(timeline.layout(empty),[])
        migrated,data=timeline.edit(dict(empty,timing_mode='legacy'),show_automation.empty(),dict(action='enable_overlap'))
        self.assertEqual(migrated['timing_mode'],'overlap')
        self.assertEqual(timeline.layout(migrated),[])
        host=FakeHost();host.show=migrated;host.data=data
        bridge=Bridge(host)
        self.assertEqual(bridge.state['rows'],[])
        with self.assertRaises(ValueError):
            timeline.locate(empty,0)

    def test_fresh_transport_imports_midi_before_use_and_repairs_previous_bad_order(self):
        import ast
        from pathlib import Path
        from pixelblaze_mapper.show_sync_fastpath import install_callback_source
        path=Path(__file__).parents[1]/'pixelblaze_mapper/build_show_sequencer.py'
        raw=next(n.value for n in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
                 if isinstance(n,ast.Constant) and isinstance(n.value,str)
                 and n.value.startswith('# Isolated transport UI callbacks'))
        patched=timeline.install_sync_source(install_callback_source(raw))
        sync=next(n for n in ast.parse(patched).body if isinstance(n,ast.FunctionDef) and n.name=='sync')
        imports=[n.lineno for n in ast.walk(sync) if isinstance(n,ast.ImportFrom)
                 and n.module=='pixelblaze_mapper.show_midi' and any(a.name=='apply_plan' for a in n.names)]
        calls={name:[n.lineno for n in ast.walk(sync) if isinstance(n,ast.Call)
                     and isinstance(n.func,ast.Name) and n.func.id==name]
               for name in ('apply_plan','playback_plan')}
        self.assertEqual(len(imports),1)
        self.assertEqual(len(calls['apply_plan']),1)
        self.assertLess(imports[0],calls['apply_plan'][0])
        self.assertLess(calls['playback_plan'][0],calls['apply_plan'][0])
        self.assertEqual(timeline.install_sync_source(patched),patched)
        block='    # SHOW_TIMELINE_MIDI_V1\n    from pixelblaze_mapper.show_midi import apply_plan\n'
        call='    plan = apply_plan(plan, sequence.cue.id)\n'
        broken=patched.replace(block,'').replace(call,call+block)
        self.assertEqual(timeline.install_sync_source(broken),patched)


if __name__ == '__main__':
    unittest.main()
