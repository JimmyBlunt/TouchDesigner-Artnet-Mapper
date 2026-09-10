"""Keep LED Preview aligned with active source capacity and sparse availability.

Run ``build()`` explicitly in TouchDesigner. It upgrades the reviewed preview
callback and binds instance alpha; no output or project save is started.
"""

from __future__ import annotations

import sys
from pathlib import Path

LOCAL_ROOT = str(Path(__file__).resolve().parents[1])
if LOCAL_ROOT not in sys.path:
    sys.path.insert(0, LOCAL_ROOT)

from pixelblaze_mapper.installation_contract import TOTAL_PIXELS


PREVIEW = "/project1/pixelblaze_mapper/preview3d"
COUNT_MARKER = "# P0_CANONICAL_COUNT_GUARD"
MISSING_MARKER = "# P0_CANONICAL_MISSING_BLACK"


def patch_callback_source(source: str) -> str:
    """Return an idempotently patched instance-data callback."""

    if COUNT_MARKER not in source:
        anchor = "    if error or n == 0:\n"
        if anchor not in source:
            raise ValueError("LED Preview callback count anchor was not found")
        guard = (
            f"    {COUNT_MARKER}\n"
            f"    if not error and n != {TOTAL_PIXELS}:\n"
            f"        error = 'expected {TOTAL_PIXELS} canonical LED coordinates, got {{}}'.format(n)\n"
        )
        source = source.replace(anchor, guard + anchor, 1)

    if MISSING_MARKER not in source:
        anchor = "    for name,vals in zip(('r','g','b'),colors):\n"
        if anchor not in source:
            raise ValueError("LED Preview callback color anchor was not found")
        mask = (
            f"    {MISSING_MARKER}\n"
            "    for missing_index in missing:\n"
            "        if 0 <= missing_index < n:\n"
            "            colors[0][missing_index] = 0.0\n"
            "            colors[1][missing_index] = 0.0\n"
            "            colors[2][missing_index] = 0.0\n"
        )
        source = source.replace(anchor, mask + anchor, 1)
    return source


DYNAMIC_MARKER = '# ACTIVE_SOURCE_CAPACITY_V1'
DYNAMIC_REPLACEMENTS = (
    ("    # P0_CANONICAL_COUNT_GUARD\n    if not error and n != 3744:\n        error = 'expected 3744 canonical LED coordinates, got {}'.format(n)\n",
     "    # P0_CANONICAL_COUNT_GUARD\n    # ACTIVE_SOURCE_CAPACITY_V1\n    active = op('/project1/pixelblaze_mapper/map_active')\n    expected = active.numRows - 1 if active is not None else 0\n    if not error and (expected <= 0 or n != expected):\n        error = 'expected {} active LED coordinates, got {}'.format(expected, n)\n"),
    ("    sig = (src.path, src.cookFrame, src.numRows, mode)\n",
     "    from pixelblaze_mapper.output_slot_mask import ranges_for\n    inactive = ranges_for(op, src.numRows - 1)\n    sig = (src.path, src.cookFrame, src.numRows, mode, inactive)\n"),
    ("    missing = sorted(set(i for i in range(max_index + 1) if i not in points) | missing_from_state)\n",
     "    missing = sorted(set(i for i in range(max_index + 1) if i not in points) | missing_from_state | {i for first, last in inactive for i in range(first, last + 1)})\n"),
    ("    xs=[v[0] for v in raw]; ys=[v[1] for v in raw]; zs=[v[2] for v in raw]\n",
     "    unavailable = set(missing)\n    available = [point for index, point in enumerate(raw) if index not in unavailable]\n    if not available:\n        return src, [], missing, 'no active coordinate rows'\n    xs=[v[0] for v in available]; ys=[v[1] for v in available]; zs=[v[2] for v in available]\n"),
    ("        for name in ('tx','ty','tz','r','g','b'):\n",
     "        for name in ('tx','ty','tz','r','g','b','a'):\n"),
    ("    for name,vals in zip(('r','g','b'),colors):\n",
     "    unavailable = set(missing)\n    scriptOp.appendChan('a').vals = [0.0 if index in unavailable else 1.0 for index in range(n)]\n    for name,vals in zip(('r','g','b'),colors):\n"),
)


def patch_dynamic_source(source):
    """Upgrade only the reviewed callback; reversible normalization is idempotent.

    Alpha hides unavailable source slots, including placeholders at the origin.
    Geometry must bind its instance alpha to the emitted ``a`` channel.
    """
    from pixelblaze_mapper.preview_color_bulk import ensure_bulk_source
    if DYNAMIC_MARKER in source:
        for old, new in reversed(DYNAMIC_REPLACEMENTS):
            if source.count(new) != 1:
                raise ValueError('Dynamic LED Preview differs from the reviewed callback')
            source = source.replace(new, old, 1)
    source = ensure_bulk_source(source)
    for old, new in DYNAMIC_REPLACEMENTS:
        if source.count(old) != 1:
            raise ValueError('LED Preview capacity anchor differs from the reviewed callback')
        source = source.replace(old, new, 1)
    compile(source, '<active-capacity LED Preview>', 'exec')
    return source


def build():
    preview = op(PREVIEW)
    if preview is None:
        raise RuntimeError("Missing LED Preview: " + PREVIEW)
    coordinate_dat = preview.op(str(preview.par.Coordinatedat.eval()))
    if coordinate_dat is None:
        coordinate_dat = op(str(preview.par.Coordinatedat.eval()))
    rows = coordinate_dat.numRows - 1 if coordinate_dat is not None else 0
    active = op('/project1/pixelblaze_mapper/map_active')
    expected_count = active.numRows - 1 if active is not None else 0
    if expected_count <= 0 or rows != expected_count:
        raise RuntimeError("Preview contract expected %d active coordinate rows, got %d" % (expected_count, rows))

    callbacks = preview.op("instance_data_callbacks")
    instance_data = preview.op("instance_data")
    if callbacks is None or instance_data is None:
        raise RuntimeError("LED Preview instance callback chain is incomplete")
    patched = patch_dynamic_source(callbacks.text)
    geometry = preview.op('led_points_geo')
    alpha = getattr(geometry.par, 'instancea', None) if geometry is not None else None
    if alpha is None or str(alpha.eval()) not in ('', 'a'):
        raise RuntimeError('LED Preview instance alpha has an unreviewed binding')
    changed = patched != callbacks.text
    if changed:
        callbacks.text = patched
    alpha.val = 'a'
    instance_data.cook(force=True)
    if instance_data.numSamples != expected_count:
        raise RuntimeError("LED Preview did not produce %d samples" % expected_count)
    errors = list(preview.errors(recurse=True))
    if errors:
        raise RuntimeError("LED Preview contract errors: %s" % errors)
    return {
        "pixels": instance_data.numSamples,
        "missingDraftRender": "transparent-black",
        "callbackChanged": changed,
        "projectSaved": False,
        "networkChanged": False,
    }


if __name__ == "__main__":
    print(build())
