import unittest
import numpy as np
from pixelblaze_mapper.show_renderer import render_frame, TRANSITIONS
from pixelblaze_mapper.show_performance import render_numpy, panel_data, write_channels, _table_cache


class ShowPerformanceTests(unittest.TestCase):
    def test_bulk_writer_keeps_explicit_channel_names(self):
        class Channel:
            def copyNumpyArray(self, row): self.values=row.copy()
        class Output:
            def clear(self): self.channels={}
            def appendChan(self, name):
                channel=Channel();self.channels[name]=channel;return channel
        output=Output()
        values=np.arange(18,dtype=np.float32).reshape(3,6)
        write_channels(output,values,('tx','ty','tz'))
        self.assertEqual(output.numSamples,6)
        self.assertEqual(list(output.channels),['tx','ty','tz'])
        for name,row in zip(output.channels,values):
            np.testing.assert_array_equal(output.channels[name].values,row)

    def test_all_transitions_masks_brightness_and_blackout_match_reference(self):
        rng = np.random.default_rng(91)
        a, b = rng.random((3, 127))*255, rng.random((3, 127))*255
        u, v = rng.random(127), rng.random(127)
        groups = tuple(('rear','upper','middle','lower',None)[i%5] for i in range(127))
        for transition in TRANSITIONS:
            for mix in (0., .27, .5, 1.):
                for blackout in (False, True):
                    options = dict(transition=transition, output_b_mix=mix, brightness=.71,
                                   blackout=blackout, targets_a=('rear','upper'), targets_b=('middle','lower'),
                                   source_groups=groups)
                    expected=render_frame(a.tolist(),b.tolist(),u=u,v=v,**options)
                    actual=render_numpy(a,b,u,v,**options)
                    np.testing.assert_allclose(actual,expected,rtol=1e-6,atol=2e-5)

    def test_uv_cache_invalidates_on_edit_even_in_same_frame(self):
        class Table:
            path='test-panel-cache'
            totalCooks=1
            numRows=2
            numCols=6
            text='index\tpanel\tglobal_u\tglobal_v\tlocal_u\tlocal_v\n0\trear\t0.1\t0.2\t0.3\t0.4\n'
            def cook(self,force=False): pass
        t=Table()
        first=panel_data(t)
        self.assertIs(panel_data(t),first)
        t.text=t.text.replace('0.1','0.9')
        t.totalCooks+=1
        second=panel_data(t)
        self.assertIsNot(first,second)
        self.assertEqual(second['columns'][0],(.9,))
        _table_cache.pop(t.path)

    def test_rejects_invalid_source_group_and_mix(self):
        for extra in ({'source_groups':('unknown',)}, {'output_b_mix':float('nan')}):
            kwargs=dict(transition='crossfade',output_b_mix=.5,brightness=1,blackout=False,
                        targets_a=('all',),targets_b=('all',),source_groups=('rear',))
            kwargs.update(extra)
            with self.assertRaises(ValueError):
                render_numpy(np.ones((3,1)),np.ones((3,1)),[.1],[.2],**kwargs)
