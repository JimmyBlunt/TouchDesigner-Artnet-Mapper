"""Repair the live 3D-to-2D effect sampler in TouchDesigner.

This changes only texture coordinates. Pixel indices, the rear-wall mapping,
Art-Net routing, universes and controller parameters remain untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pixelblaze_mapper.effect_surface_uv import (  # noqa: E402
    CONTRACT,
    build_effect_coordinates,
    rear_wall_uv,
)


CALLBACK_SOURCE = r'''# Select reviewed global or true per-panel local UV by LED index.
# /project1/pixelblaze_mapper/effect_panel_uv owns the four real panel ranges:
# middle 0..516, upper 517..785, lower 786..1183, rear 1184..3743.

LOOKUP = '/project1/pixelblaze_mapper/effect_panel_uv'
CONTROLS = '/project1/madmapper_player_controls'


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def onCook(scriptOp):
    source = scriptOp.inputs[0]
    count = source.numSamples
    table = op(LOOKUP)
    controls = op(CONTROLS)
    if table is None or table.numRows != count + 1:
        raise RuntimeError('True panel UV lookup is missing or incomplete')
    mode = str(controls.par.Coordinatemode.eval()) if controls is not None else 'global'
    blend = float(controls.par.Hybridmix.eval()) if controls is not None else 0.5
    blend = max(0.0, min(1.0, blend))

    scriptOp.clear()
    scriptOp.numSamples = count
    out_u = scriptOp.appendChan('tx')
    out_v = scriptOp.appendChan('ty')
    out_z = scriptOp.appendChan('tz')

    for index in range(count):
        row = index + 1
        global_u = float(table[row, 'global_u'])
        global_v = float(table[row, 'global_v'])
        local_u = float(table[row, 'local_u'])
        local_v = float(table[row, 'local_v'])
        if mode in ('panel', 'panel_local'):
            out_u[index], out_v[index] = local_u, local_v
        elif mode == 'hybrid':
            out_u[index] = global_u + (local_u - global_u) * blend
            out_v[index] = global_v + (local_v - global_v) * blend
        else:
            out_u[index], out_v[index] = global_u, global_v
        out_z[index] = 0.0
    return
'''


def _global_uv(reference, coordinates):
    values = {}
    for row in range(1, reference.numRows):
        index = int(float(reference[row, "index"]))
        if index < 1184:
            values[index] = (
                float(reference[row, "u"]),
                float(reference[row, "v"]),
            )
    source_x = coordinates["tx"]
    source_z = coordinates["tz"]
    for index in range(1184, 3744):
        values[index] = rear_wall_uv(float(source_x[index]), float(source_z[index]))
    return values


def _write_lookup(parent, values):
    table = parent.op("effect_panel_uv") or parent.create(tableDAT, "effect_panel_uv")
    table.clear()
    table.appendRow(
        ("index", "panel_id", "panel", "global_u", "global_v", "local_u", "local_v")
    )
    for item in values:
        table.appendRow(
            (
                item.index,
                item.panel_id,
                item.panel,
                item.global_uv[0],
                item.global_uv[1],
                item.local_uv[0],
                item.local_uv[1],
            )
        )
    return table


def build():
    callback = op(CONTRACT.callback_dat)
    output = op(CONTRACT.output_chop)
    sampler = op(CONTRACT.sampler_chop)
    reference = op(CONTRACT.side_source)
    coordinates = op(CONTRACT.coordinate_source)
    parent = op("/project1/pixelblaze_mapper")
    if None in (callback, output, sampler, reference, coordinates, parent):
        raise RuntimeError("The effect-sampling chain is incomplete")
    if reference.numRows < 1185:
        raise RuntimeError("The current active side-wall table is incomplete")
    if output.numSamples != 3744:
        raise RuntimeError("Expected the current 3744-pixel mapping")

    values = build_effect_coordinates(_global_uv(reference, coordinates))
    lookup = _write_lookup(parent, values)
    if lookup.numRows != 3745:
        raise RuntimeError("Expected one panel UV row for every LED index")

    from pixelblaze_mapper.show_performance import install_effect_uv_source
    callback.text = install_effect_uv_source(CALLBACK_SOURCE)
    output.par.callbacks = callback.path
    output.cook(force=True)
    sampler.cook(force=True)

    if output.numSamples != 3744 or output.numChans != 3:
        raise RuntimeError("Effect UV output contract changed unexpectedly")
    errors = list(output.errors(recurse=False)) + list(sampler.errors(recurse=False))
    if errors:
        raise RuntimeError("Effect UV repair failed: %s" % errors)

    return {
        "panelRanges": "middle 0-516 | upper 517-785 | lower 786-1183 | rear 1184-3743",
        "coordinateModes": "global room UV | true panel local UV | hybrid",
        "panelLookup": lookup.path,
        "samples": output.numSamples,
        "networkParametersChanged": False,
        "universeRoutingChanged": False,
        "projectSaved": False,
    }


print(build())
