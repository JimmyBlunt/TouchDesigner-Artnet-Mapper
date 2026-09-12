"""Expanded Show/preview sources retain addresses and honor explicit grouping."""
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from pixelblaze_mapper.show_renderer import render_frame, source_groups_from_panels
from pixelblaze_mapper.integrate_live_show import LED_RENDER_CALLBACK, _slot_uv_source, REPO_ROOT
from pixelblaze_mapper.build_led_preview_contract import patch_dynamic_source
from tests.test_preview_color_bulk import captured


class Table:
    def __init__(self, rows, path="table"):
        self.rows, self.path, self.cookFrame = rows, path, 1
    @property
    def numRows(self): return len(self.rows)
    @property
    def numCols(self): return len(self.rows[0]) if self.rows else 0
    @property
    def text(self): return "\n".join("\t".join(map(str, row)) for row in self.rows)
    def __getitem__(self, key):
        row, col = key
        if isinstance(col, str): col = self.rows[0].index(col)
        return self.rows[row][col]
    def clear(self): self.rows = []
    def appendRow(self, row): self.rows.append(row)


class Script:
    def __init__(self, count=0, channels=None):
        self.numSamples, self.channels, self.storage = count, channels or {}, {}
    def __getitem__(self, name): return self.channels.get(name)
    def clear(self): self.channels = {}
    def appendChan(self, name):
        channel = NS(vals=[])
        channel.copyNumpyArray=lambda array: setattr(channel,'vals',array.tolist())
        self.channels[name] = channel
        return channel
    def numpyArray(self):
        import numpy as np
        return np.asarray([ch.vals for ch in self.channels.values()],dtype=np.float32)
    def store(self, key, value): self.storage[key] = value
    def fetch(self, key, default=None): return self.storage.get(key, default)


def parameter(value): return NS(eval=lambda: value)


class DynamicSourceCapacityTests(unittest.TestCase):
    def frame(self, count=4482, **changes):
        kwargs = dict(u=[.5]*count, v=[.5]*count, transition="crossfade", output_b_mix=0,
                      brightness=1, blackout=False, targets_a=("all",), targets_b=("all",),
                      source_groups=("rear",)*count)
        kwargs.update(changes)
        return render_frame(([1.]*count,), ([0.]*count,), **kwargs)[0]

    def test_generated_callbacks_pin_current_repository(self):
        from pixelblaze_mapper.build_led_preview_contract import LOCAL_ROOT
        self.assertEqual(Path(LOCAL_ROOT).resolve(), REPO_ROOT)
        for source in (LED_RENDER_CALLBACK, _slot_uv_source()):
            self.assertIn(REPO_ROOT.as_posix(), source)
            self.assertNotIn("TouchDesignerLocal", source)

    def test_expanded_frame_keeps_tail_and_explicit_panel_selection(self):
        groups = source_groups_from_panels(("middle",)*3744 + ("rear",)*738)
        result = self.frame(targets_a=("rear",), source_groups=groups)
        self.assertEqual(result[:3744], [0.]*3744)
        self.assertEqual(result[3744:], [1.]*738)
        self.assertEqual(len(self.frame()), 4482)
        self.assertEqual(self.frame(blackout=True), [0.]*4482)

    def test_new_source_index_does_not_imply_rear(self):
        groups = source_groups_from_panels(("rear",)*3744 + ("middle",)*738)
        self.assertEqual(self.frame(targets_a=("rear",), source_groups=groups)[3744:], [0.]*738)
        self.assertEqual(source_groups_from_panels(("rear_panel2", "unknown", "__inactive__")), ("rear", None, None))

    def test_expanded_frames_require_consistent_explicit_source_metadata(self):
        for changes in ({"source_groups": None}, {"source_groups": ("rear",)},
                        {"source_groups": ("all",)*4482}, {"v": [0.]*3744}):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError): self.frame(**changes)

    def test_native_show_callback_uses_current_count_and_panel_lookup(self):
        count = 4482
        slot = Script(count, {name: NS(vals=[1.]*count) for name in ("r", "g", "b")})
        coords = Script(count, {name: NS(vals=[.5]*count) for name in ("tx", "ty")})
        panels = Table([["index", "panel"]]+[[i,"middle" if i<3744 else "rear"] for i in range(count)])
        values = Table([["key","value"],["mode","crossfade"],["brightness","1"],["blackout","0"],["output_b_mix","0"]])
        group = Table([["key","value"],["target_groups","rear"]])
        nodes = {"effect_uv_in": coords, "/project1/pixelblaze_mapper/effect_panel_uv": panels,
                 "transition_adapter/mixer_request": values,
                 "slot_a_adapter/material_request":group,"slot_b_adapter/material_request":group}
        scope = {"op": nodes.get}
        exec(LED_RENDER_CALLBACK, scope)
        output = Script(); output.inputs = [slot,slot]
        scope["onCook"](output)
        self.assertEqual(output.numSamples, count)
        self.assertEqual(output["r"].vals[-1],1)
        self.assertEqual(output["r"].vals[3743],0)
        cached = scope["_source_groups"](panels,count)
        self.assertIs(scope["_source_groups"](panels,count),cached)
        panels.rows[-1][1] = "middle"
        scope["onCook"](output)
        self.assertEqual(output["r"].vals[-1],0)
        slot.numSamples = 3744
        with self.assertRaisesRegex(RuntimeError,"matching"): scope["onCook"](output)
        slot.numSamples = count
        panels.rows[-1][0] = 4479
        with self.assertRaisesRegex(RuntimeError,"ordered"): scope["onCook"](output)

    def test_preview_patch_is_idempotent_and_rejects_changed_source(self):
        source = patch_dynamic_source(captured())
        self.assertEqual(patch_dynamic_source(source),source)
        with self.assertRaises(ValueError): patch_dynamic_source(source.replace("color_source='animated fallback'", "color_source='changed'"))

    def test_native_preview_hides_missing_slots_and_invalidates_fit_on_mask_change(self):
        count = 4482
        rows = [["index","tx","ty","tz"]]+[[i,10.,20.,30.] for i in range(count)]
        rows[1] = [0,0.,0.,0.]; rows[-1] = [count-1,0.,0.,0.]
        rows[2] = [1,12.,22.,32.]
        coords = Table(rows,"/project1/pixelblaze_mapper/map_active")
        mask = Table([["index","enabled"]]+[[i,int(i not in (0,count-1))] for i in range(count)])
        colors = Script(count,{name:NS(vals=[1.]*count,index=i) for i,name in enumerate(("r","g","b"))}); colors.path="colors"
        status = Table([])
        nodes = {coords.path:coords,"coords":coords,"colors":colors,
                 "/project1/layout_apply/active_source_mask":mask}
        owner = NS(par=NS(Coordinatedat=parameter("coords"),Fitmode=parameter("none"),Colorchop=parameter("colors")),
                   op=lambda name: {"preview_status":status,"preview_out":NS(path="out")}.get(name,nodes.get(name)))
        script = Script(); script.parent=lambda: owner
        scope = {"op":nodes.get}
        exec(patch_dynamic_source(captured()), scope)
        scope["onCook"](script)
        self.assertEqual(script.numSamples,count)
        self.assertEqual(script["a"].vals[0],0)
        self.assertEqual(script["a"].vals[-1],0)
        self.assertEqual(script["a"].vals[1],1)
        self.assertEqual(script["r"].vals[-1],0)
        self.assertEqual(script["tx"].vals[2],-1.)  # Missing origin does not alter fit center.
        mask.rows[1][1] = 1
        scope["onCook"](script)
        self.assertEqual(script["a"].vals[0],1)
        self.assertEqual(script["tx"].vals[2],4.)


if __name__ == "__main__": unittest.main()
