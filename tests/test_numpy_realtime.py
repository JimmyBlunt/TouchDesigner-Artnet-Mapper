import unittest
import numpy as np
from pixelblaze_mapper.multi_controller import ControllerConfig,SegmentConfig,RouterConfig,build_router_plan
from pixelblaze_mapper.realtime_packer import compile_router_packer
from pixelblaze_mapper.numpy_realtime import NumpyControllerPacker, mask_array


class NumpyPackerTests(unittest.TestCase):
    def test_preview_position_cache_rebuilds_for_coordinate_replacements(self):
        from unittest.mock import patch
        from tests.test_dynamic_source_capacity import Script
        from pixelblaze_mapper import preview_numpy
        node=Script();node.store('coord_signature',('map',1))
        values=[(1.,2.,3.),(4.,5.,6.)]
        with patch.object(preview_numpy,'position_arrays',wraps=preview_numpy.position_arrays) as convert:
            preview_numpy.write_positions(node,values)
            preview_numpy.write_positions(node,values)
            self.assertEqual(convert.call_count,1)
            replacement=[(7.,8.,9.),(4.,5.,6.)]
            preview_numpy.write_positions(node,replacement)
            self.assertEqual(convert.call_count,2)
            self.assertEqual(node.channels['tx'].vals,[7.,4.])
            node.store('coord_signature',('map',2))
            preview_numpy.write_positions(node,replacement)
            self.assertEqual(convert.call_count,3)

    def test_sender_marker_without_reviewed_block_is_rejected(self):
        from pixelblaze_mapper.numpy_realtime import install_sender
        with self.assertRaises(ValueError):install_sender('# NUMPY_ROUTER_PACK_V1')

    def test_native_mask_revision_handles_same_frame_changes(self):
        from pixelblaze_mapper.output_slot_mask import _validated_table_ranges
        class Table:
            type='table';inputs=[];allowCooking=True;id=-8123;numRows=3;numCols=2
            def __init__(self):self.totalCooks=0;self.dirty=True;self.raw='index\tenabled\n0\t1\n1\t0';self.reads=0
            def cook(self,force=False):
                if self.dirty:self.totalCooks+=1;self.dirty=False
            @property
            def text(self):self.reads+=1;return self.raw
        table=Table()
        self.assertEqual(_validated_table_ranges(table,2),((1,1),))
        self.assertEqual(_validated_table_ranges(table,2),((1,1),));self.assertEqual(table.reads,1)
        table.raw='index\tenabled\n0\t0\n1\t1';table.dirty=True
        self.assertEqual(_validated_table_ranges(table,2),((0,0),))
        table.raw='bad';table.dirty=True
        for _ in range(2):
            with self.assertRaises(ValueError):_validated_table_ranges(table,2)
        table.raw='index\tenabled\n0\t1\n1\t1';table.dirty=True
        self.assertEqual(_validated_table_ranges(table,2),())

    def test_preview_channels_and_mask_preserve_float32_values(self):
        from pixelblaze_mapper.preview_numpy import color_arrays,position_arrays
        xyz=[(1.23456789,-3.,1e-8),(0.,20.,30.)]
        np.testing.assert_array_equal(position_arrays(xyz),np.asarray(xyz,dtype=np.float32).T)
        rgb,alpha=color_arrays([[.1,.2],[.3,.4],[.5,.6]],[1,-1,5],2)
        np.testing.assert_array_equal(rgb,np.asarray([[.1,0],[.3,0],[.5,0]],dtype=np.float32))
        np.testing.assert_array_equal(alpha,[1,0])

    def test_reference_equivalence_routing_and_rounding(self):
        rng=np.random.default_rng(412)
        for dtype in (np.float32,np.float64):
            rgb=rng.uniform(-.5,1.5,(3,6524)).astype(dtype)
            rgb[:,:6]=np.asarray([0,.5/255,1.5/255,2.5/255,254.5/255,1],dtype=dtype)
            for order in ('RGB','GRB','BGR'):
                for brightness in (0,.065,.7,1):
                    c=ControllerConfig(name='node',target_address='127.0.0.1',local_interface='127.0.0.1',color_order=order,brightness=brightness,reserved_universes=29)
                    segs=(SegmentConfig('first',0,203,'node',0),SegmentConfig('second',3744,738,'node',340,True,'GBR'),SegmentConfig('third',4482,880,'node',1190))
                    compiled=compile_router_packer(build_router_plan(RouterConfig((c,),segs,source_pixel_count=6524))).controller('node')
                    self.assertEqual(NumpyControllerPacker(compiled).pack(rgb),compiled.pack_channels(*rgb))

    def test_sparse_mask_holes_and_no_input_mutation(self):
        c=ControllerConfig(name='n',target_address='127.0.0.1',local_interface='127.0.0.1',reserved_universes=2)
        compiled=compile_router_packer(build_router_plan(RouterConfig((c,),(SegmentConfig('s',0,200,'n',0),),source_pixel_count=200))).controller('n')
        rgb=np.ones((3,200),dtype=np.float32);rgb[:,50]=np.nan
        result=NumpyControllerPacker(compiled).pack(rgb,((49,51),))
        expected=mask_array(rgb,((49,51),))
        self.assertEqual(result,compiled.pack_channels(*expected))
        self.assertTrue(np.isnan(rgb[:,50]).all())
        self.assertEqual(len(result),2)
        self.assertTrue(all(len(p)==510 for p in result))
        with self.assertRaises(ValueError):NumpyControllerPacker(compiled).pack(rgb)
        with self.assertRaises(ValueError):NumpyControllerPacker(compiled).pack(rgb,((0,200),))

    def test_unmapped_nan_is_ignored_like_reference(self):
        c=ControllerConfig(name='n',target_address='127.0.0.1',local_interface='127.0.0.1')
        compiled=compile_router_packer(build_router_plan(RouterConfig((c,),(SegmentConfig('s',1,2,'n',0),),source_pixel_count=3))).controller('n')
        rgb=np.ones((3,3));rgb[:,0]=np.nan
        self.assertEqual(NumpyControllerPacker(compiled).pack(rgb),compiled.pack_channels(*rgb))

    def test_extra_source_tail_mask_matches_scalar(self):
        c=ControllerConfig(name='n',target_address='127.0.0.1',local_interface='127.0.0.1')
        compiled=compile_router_packer(build_router_plan(RouterConfig((c,),(SegmentConfig('s',0,2,'n',0),),source_pixel_count=2))).controller('n')
        rgb=np.ones((3,4));rgb[:,3]=np.nan
        self.assertEqual(NumpyControllerPacker(compiled).pack(rgb,((3,3),)),compiled.pack_channels(*mask_array(rgb,((3,3),))))

    def test_cached_masks_follow_mutations_empty_masks_and_reversed_sources(self):
        c=ControllerConfig(name='n',target_address='127.0.0.1',local_interface='127.0.0.1',reserved_universes=2)
        compiled=compile_router_packer(build_router_plan(RouterConfig((c,),
            (SegmentConfig('s',0,200,'n',13,True,'BRG'),),source_pixel_count=200))).controller('n')
        packer=NumpyControllerPacker(compiled)
        rgb=np.arange(600,dtype=np.float32).reshape(3,200)/600
        inactive=[[2,8],[50,55]]
        for _ in range(2):
            self.assertEqual(packer.pack(rgb,inactive),compiled.pack_channels(*mask_array(rgb,inactive)))
        # Mutating the same list object must change the cached source-index mask.
        inactive[0][:]=[15,25]
        self.assertEqual(packer.pack(rgb,inactive),compiled.pack_channels(*mask_array(rgb,inactive)))
        self.assertEqual(packer.pack(rgb,()),compiled.pack_channels(*rgb))
        inactive[:]=[[10,30],[20,40]]  # Overlap remains equivalent to masking the union.
        self.assertEqual(packer.pack(rgb,inactive),compiled.pack_channels(*mask_array(rgb,inactive)))
        self.assertEqual(packer.pack(rgb,iter(inactive)),compiled.pack_channels(*mask_array(rgb,inactive)))

    def test_cache_never_bypasses_range_validation_or_nonfinite_active_samples(self):
        c=ControllerConfig(name='n',target_address='127.0.0.1',local_interface='127.0.0.1')
        compiled=compile_router_packer(build_router_plan(RouterConfig((c,),
            (SegmentConfig('s',0,4,'n',0),),source_pixel_count=4))).controller('n')
        packer=NumpyControllerPacker(compiled)
        rgb=np.ones((3,4));rgb[:,1]=np.nan
        good=packer.pack(rgb,((1,1),))
        for ranges in (((True,True),),((np.int64(1),1),),((1,4),),((2,1),),((1.0,1.0),)):
            with self.assertRaises(ValueError):packer.pack(rgb,ranges)
            self.assertEqual(packer.pack(rgb,((1,1),)),good)
        with self.assertRaises(ValueError):packer.pack(rgb,())
        self.assertEqual(packer.pack(rgb,((1,1),)),good)


if __name__=='__main__':unittest.main()
