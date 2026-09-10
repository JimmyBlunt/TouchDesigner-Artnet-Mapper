"""Current-layout diagnostic generation is pure and source-address preserving."""
import ast
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS
from pixelblaze_mapper.router_calibration import active_calibration_source, calibration_source
from tests.test_guided_scan_live import _artnet_510_sender_source
from pixelblaze_mapper.output_slot_mask import install_source, pixels, ranges_for
from tests.test_dynamic_source_capacity import Table


class ActiveCalibrationTests(unittest.TestCase):
    def rows(self):
        return [["index","panel","local_u","local_v"]]+[[str(i),"middle" if i<3744 else "rear",(i%24)/24,(i%17)/17] for i in range(4482)]

    def test_all_and_rear_include_new_sources_and_preserve_chase_address(self):
        rows=self.rows()
        with patch("pathlib.Path.read_text",side_effect=AssertionError("no historical disk reads")):
            all_pixels=active_calibration_source(rows,source_count=4482)
            rear=active_calibration_source(rows,source_count=4482,panel="rear")
            chase=active_calibration_source(rows,source_count=4482,panel="rear",pattern="chase",chase_index=4481)
        self.assertEqual(len(all_pixels),4482)
        self.assertNotEqual(all_pixels[-1],(0,0,0))
        self.assertEqual(rear[:3744],((0,0,0),)*3744)
        self.assertEqual(chase[-1],(0,1,0))
        self.assertEqual(chase[-2],(1,1,1))
        self.assertEqual(chase[-5],(0,0,0))

    def test_uv_stripes_follow_coordinates_not_index_grid(self):
        rows=self.rows()
        rows[3745][2:]=[.1,.2]; rows[3746][2:]=[.2,.1]
        horizontal=active_calibration_source(rows,source_count=4482,pattern="rows")
        vertical=active_calibration_source(rows,source_count=4482,pattern="columns")
        self.assertEqual(horizontal[3744],vertical[3745])
        self.assertEqual(horizontal[3745],vertical[3744])
        self.assertNotEqual(horizontal[3744],vertical[3744])

    def test_bad_scope_order_uv_and_chase_fail_before_output(self):
        for kind in ("count","index","uv","chase"):
            rows=self.rows(); kwargs=dict(source_count=4482)
            if kind=="count": rows.pop()
            elif kind=="index": rows[-1][0]="7"
            elif kind=="uv": rows[-1][2]=float("nan")
            else: kwargs["chase_index"]=4482
            with self.subTest(kind=kind),self.assertRaises(ValueError): active_calibration_source(rows,**kwargs)
        with self.assertRaises(ValueError): calibration_source(None,source_count=4482)

    def test_generated_sender_builds_full_masked_buffer_without_starting(self):
        tree=ast.parse(install_source(_artnet_510_sender_source()))
        tree.body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="set_calibration"]
        uv=Table(self.rows())
        missing=set(range(4424,4482))
        mask=Table([["index","enabled"]]+[[i,int(i not in missing)] for i in range(4482)])
        nodes={"/project1/pixelblaze_mapper/effect_panel_uv":uv,"source_select":NS(numSamples=4482),
               "/project1/layout_apply/active_source_mask":mask}
        packed=[]
        def pack(values): packed.append(values);return {"rear": values}
        scope={"op":nodes.get,"calibration_source":calibration_source,
               "build_router_plan":lambda _:NS(pack_pixels=pack),"_router_config":lambda:None}
        exec(compile(tree,"<active calibration>","exec"),scope)
        scope["set_calibration"](panel="rear",pattern="panel_id")
        self.assertEqual(len(packed[0]),4482)
        self.assertTrue(any(packed[0][3744]))
        self.assertTrue(all(packed[0][i]==(0,0,0) for i in missing))
        self.assertEqual(scope["_mode"],"calibration")
        self.assertNotIn("_enabled",scope)


if __name__=="__main__":unittest.main()
