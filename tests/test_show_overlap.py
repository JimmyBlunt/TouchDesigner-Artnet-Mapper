"""Acceptance for opt-in clip overlap, independent fades and legacy documents."""
from dataclasses import replace
import json
from pathlib import Path
import random
import unittest

from pixelblaze_mapper.show_sequencer import (
    Cue, Show, ShowSequencer, ShowValidationError, TransportState,
    cue_envelope, overlap_duration, timeline_rows,
)
from tests.test_show_sequencer import cue


def overlap_show(*items, loop=False):
    return Show('Overlap', tuple(items or (cue('a'), cue('b'), cue('c'))),
                loop=loop, timing_mode='overlap')


class OverlapSchemaTests(unittest.TestCase):
    def test_existing_schema_two_document_serializes_without_new_defaults(self):
        path = Path(__file__).resolve().parents[1]/'shows'/'demo_show.json'
        raw = json.loads(path.read_text(encoding='utf-8'))
        restored = Show.from_dict(raw)
        self.assertEqual(restored.timing_mode, 'legacy')
        self.assertEqual(restored.to_dict(), raw)
        self.assertNotIn('timing_mode', restored.to_dict())
        self.assertNotIn('fade_in', restored.cues[0].to_dict())

    def test_opt_in_and_nondefault_fades_round_trip_without_input_mutation(self):
        show = overlap_show(replace(cue('a'),fade_in=1,fade_out=2,
                                    fade_in_curve='smooth',fade_out_curve='ease_out'))
        raw = show.to_dict(); original = json.dumps(raw,sort_keys=True)
        self.assertEqual(raw['timing_mode'],'overlap')
        self.assertEqual(Show.from_dict(raw),show)
        self.assertEqual(json.dumps(raw,sort_keys=True),original)

    def test_invalid_mode_fade_and_curve_fail_with_validation_error(self):
        for value in ('other',None,[],False):
            with self.subTest(mode=value), self.assertRaises(ShowValidationError):
                replace(overlap_show(),timing_mode=value)
        for field in ('fade_in','fade_out'):
            for value in (-1,float('inf'),float('nan'),True,'1'):
                with self.subTest(field=field,value=value), self.assertRaises(ShowValidationError):
                    replace(cue('a'),**{field:value})
        for field in ('fade_in_curve','fade_out_curve'):
            for value in ('other',None,[],False):
                with self.subTest(field=field,value=value), self.assertRaises(ShowValidationError):
                    replace(cue('a'),**{field:value})


class OverlapTimelineTests(unittest.TestCase):
    def test_actual_clip_intervals_and_legacy_preroll_are_distinct(self):
        show = overlap_show()
        rows = timeline_rows(show)
        self.assertEqual([(r['start'],r['end']) for r in rows],[(0,10),(8,18),(16,26)])
        self.assertEqual([r['fade_start'] for r in rows],[8,16,26])
        self.assertEqual([r['overlap_in'] for r in rows],[0,2,2])
        self.assertEqual([overlap_duration(show,i) for i in range(3)],[2,2,0])
        legacy = replace(show,timing_mode='legacy')
        self.assertEqual([(r['start'],r['end'],r['fade_start']) for r in timeline_rows(legacy)],
                         [(0,10,8),(10,20,18),(20,30,28)])

    def test_short_middle_clip_limits_both_neighbors_and_keeps_solo_margin(self):
        show = overlap_show(cue('a',transition_duration=9),cue('b',duration=3,transition_duration=3),cue('c'))
        self.assertAlmostEqual(overlap_duration(show,0),2.999)
        self.assertAlmostEqual(overlap_duration(show,1),0,places=10)
        self.assertLessEqual(overlap_duration(show,0)+overlap_duration(show,1),3-.001+1e-12)

    def test_seeded_difficult_durations_never_create_three_active_clips(self):
        rng = random.Random(4602)
        items=[]
        for i in range(60):
            duration = rng.choice((.001,.01,.5,2,10))
            items.append(cue(str(i),duration=duration,transition_duration=duration*rng.uniform(.1,1)))
        rows = timeline_rows(overlap_show(*items))
        for i,row in enumerate(rows):
            self.assertGreater(row['end'],row['start'])
            if i+1<len(rows):
                self.assertGreater(rows[i+1]['end'],row['end'])
            if i+2<len(rows):
                self.assertGreaterEqual(rows[i+2]['start']+1e-10,row['end'])
        points = sorted({v for row in rows for v in (row['start'],row['end'])})
        for moment in points+[.5*(a+b) for a,b in zip(points,points[1:])]:
            self.assertLessEqual(sum(r['start']<=moment<r['end'] for r in rows),2)

    def test_cuts_and_minimum_duration_remain_valid_without_overlap(self):
        show = overlap_show(cue('a',.001,transition_duration=.001),
                            cue('b',.001,transition='cut',transition_duration=0),cue('c'))
        self.assertEqual([overlap_duration(show,i) for i in range(3)],[0,0,0])
        self.assertAlmostEqual(timeline_rows(show)[-1]['end'],10.002)


class FadeEnvelopeTests(unittest.TestCase):
    def test_linear_fade_from_black_and_to_black_at_exact_endpoints(self):
        item=replace(cue('a'),fade_in=2,fade_out=4)
        for moment,expected in ((0,0),(1,.5),(2,1),(6,1),(7,.75),(9,.25),(10,0)):
            self.assertAlmostEqual(cue_envelope(item,moment),expected)
        self.assertEqual(cue_envelope(item,-1),0)
        self.assertEqual(cue_envelope(item,11),0)

    def test_curves_are_directional_and_do_not_change_clip_duration(self):
        expected={'linear':.25,'smooth':.15625,'ease_in':.0625,'ease_out':.4375}
        for curve,value in expected.items():
            item=replace(cue('a'),fade_in=4,fade_out=4,fade_in_curve=curve,fade_out_curve=curve)
            self.assertAlmostEqual(cue_envelope(item,1),value)
            self.assertAlmostEqual(cue_envelope(item,7),1-value)
            self.assertEqual(item.duration,10)

    def test_intersecting_and_oversized_fades_are_bounded_and_multiply(self):
        item=replace(cue('a'),fade_in=8,fade_out=8)
        self.assertAlmostEqual(cue_envelope(item,5),.625*.625)
        oversized=replace(item,fade_in=50,fade_out=50)
        self.assertAlmostEqual(cue_envelope(oversized,5),.25)
        for moment in range(11):
            self.assertTrue(0<=cue_envelope(oversized,moment)<=1)

    def test_invalid_envelope_time_is_rejected(self):
        for value in (True,'2',float('nan'),float('inf')):
            with self.assertRaises(ShowValidationError):cue_envelope(cue('a'),value)


class OverlapTransportTests(unittest.TestCase):
    def test_incoming_preroll_is_invisible_until_overlap_start(self):
        sequence=ShowSequencer(overlap_show())
        for moment in (0,7,7.99999):
            sequence.seek(0,moment);plan=sequence.plan()
            self.assertEqual((plan.slot_a_gain,plan.slot_b_gain),(1,0))
            self.assertEqual(plan.slot_b.id,'b')  # Still preloaded.
        sequence.seek(0,8);plan=sequence.plan()
        self.assertEqual((plan.slot_a_gain,plan.slot_b_gain),(1,1))
        self.assertEqual((plan.slot_b_time,plan.progress),(0,0))
        sequence.seek(2,0);self.assertEqual(sequence.plan().slot_b_gain,0)

    def test_cuts_do_not_reveal_incoming_even_with_zero_fade_in(self):
        show=overlap_show(cue('a',transition='cut',transition_duration=0),cue('b'))
        sequence=ShowSequencer(show);sequence.seek(0,9.99)
        self.assertEqual(sequence.plan().slot_b_gain,0)

    def test_handover_preserves_incoming_local_time_without_extra_duration(self):
        sequence=ShowSequencer(overlap_show());sequence.play();sequence.advance(9)
        before=sequence.plan()
        self.assertEqual((before.slot_a_time,before.slot_b_time,before.progress),(9,1,.5))
        sequence.advance(1)
        self.assertEqual((sequence.cue_index,sequence.elapsed),(1,2))
        self.assertEqual(sequence.plan().slot_b_time,2)
        sequence.advance(8)
        self.assertEqual((sequence.cue_index,sequence.elapsed),(2,2))
        self.assertEqual(sequence.plan().slot_a_time,2)
        sequence.advance(8)
        self.assertEqual((sequence.state,sequence.elapsed),(TransportState.STOPPED,10))

    def test_slot_envelopes_and_brightness_are_independent(self):
        show=overlap_show(replace(cue('a'),fade_out=2,brightness=.3),
                          replace(cue('b'),fade_in=2,brightness=.7))
        sequence=ShowSequencer(show);sequence.seek(0,9);plan=sequence.plan()
        self.assertEqual((plan.slot_a_gain,plan.slot_b_gain),(.5,.5))
        self.assertEqual((plan.slot_a_brightness,plan.slot_b_brightness),(.3,.7))
        sequence.set_blackout(True)
        self.assertEqual(sequence.plan().brightness,0)
        self.assertEqual(sequence.plan().slot_a_gain,.5)

    def test_timeline_seek_and_continuous_advance_agree_through_both_boundaries(self):
        show=overlap_show(replace(cue('a'),fade_out=2),replace(cue('b'),fade_in=2,fade_out=2),
                          replace(cue('c'),fade_in=2,fade_out=2))
        rows=timeline_rows(show)
        for moment in (0,7.999,8,9.75,10,15.99,16,17.99,18,25.99):
            played=ShowSequencer(show);played.play();played.advance(moment)
            index=next(i for i,row in enumerate(rows) if moment<row['end'])
            sought=ShowSequencer(show);sought.seek(index,moment-rows[index]['start'])
            self.assertEqual(played.cue_index,sought.cue_index)
            self.assertAlmostEqual(played.elapsed,sought.elapsed)
            p,q=played.plan(),sought.plan()
            for field in ('slot_a_time','slot_b_time','slot_a_gain','slot_b_gain','progress'):
                self.assertAlmostEqual(getattr(p,field),getattr(q,field),msg=str((moment,field)))

    def test_loop_has_no_last_to_first_overlap_and_restarts_at_exact_total(self):
        show=overlap_show(replace(cue('a'),fade_in=1),cue('b'),replace(cue('c'),fade_out=1),loop=True)
        sequence=ShowSequencer(show);sequence.play();sequence.advance(25.5)
        plan=sequence.plan()
        self.assertIsNone(plan.incoming_slot)
        self.assertAlmostEqual(plan.slot_a_gain,.5)
        sequence.advance(.5)
        self.assertEqual((sequence.cue_index,sequence.elapsed),(0,0))
        plan=sequence.plan()
        self.assertEqual(plan.slot_a_gain+plan.slot_b_gain,0)
        sequence.advance(26*3+.5)
        self.assertEqual(sequence.cue_index,0)
        self.assertAlmostEqual(sequence.elapsed,.5)

    def test_single_clip_loop_fades_to_black_without_overlapping_itself(self):
        show=overlap_show(replace(cue('solo'),fade_in=2,fade_out=2),loop=True)
        sequence=ShowSequencer(show);sequence.play()
        self.assertEqual(overlap_duration(show,0),0)
        self.assertEqual(sequence.plan().slot_a_gain,0)
        sequence.advance(9)
        plan=sequence.plan()
        self.assertIsNone(plan.slot_b)
        self.assertEqual((plan.slot_a_gain,plan.slot_b_gain),(.5,0))
        sequence.advance(1)
        self.assertEqual(sequence.elapsed,0)
        self.assertEqual(sequence.plan().slot_a_gain+sequence.plan().slot_b_gain,0)
        sequence.advance(1)
        self.assertEqual(sequence.plan().slot_b_gain,.5)

    def test_partitioned_advance_pause_and_manual_jumps_keep_consistent_times(self):
        show=overlap_show(loop=True)
        one=ShowSequencer(show);one.play();one.advance(100)
        many=ShowSequencer(show);many.play()
        for _ in range(1000):many.advance(.1)
        self.assertEqual(one.cue_index,many.cue_index)
        self.assertAlmostEqual(one.elapsed,many.elapsed,places=8)
        many.pause();before=many.plan();many.advance(100)
        self.assertEqual(many.plan(),before)
        many.next();self.assertEqual(many.elapsed,0)
        many.previous();self.assertEqual(many.elapsed,0)
        many.set_loop(False);self.assertEqual(many.show.timing_mode,'overlap')
        many.stop();self.assertEqual((many.cue_index,many.elapsed),(0,0))

    def test_legacy_ignores_fades_and_keeps_historic_elapsed_and_offset(self):
        show=Show('Old',(replace(cue('a'),fade_out=2),replace(cue('b'),fade_in=2)))
        sequence=ShowSequencer(show);sequence.play();sequence.advance(10)
        self.assertEqual((sequence.cue_index,sequence.elapsed),(1,0))
        plan=sequence.plan()
        self.assertEqual((plan.slot_b_time,plan.slot_a_gain,plan.slot_b_gain),(2,1,1))
        self.assertEqual(plan.timing_mode,'legacy')


if __name__=='__main__':
    unittest.main()
