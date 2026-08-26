"""Apply the canonical 3,744/missing policy to the existing LED Preview.

Run ``build()`` explicitly inside TouchDesigner after the canonical 3,744-row
map has been loaded.  The builder only updates the preview Script CHOP callback;
it never saves the project and never touches Art-Net or a DMX Out node.
"""

from __future__ import annotations

import sys

LOCAL_ROOT = r"C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper"
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


def build():
    preview = op(PREVIEW)
    if preview is None:
        raise RuntimeError("Missing LED Preview: " + PREVIEW)
    coordinate_dat = preview.op(str(preview.par.Coordinatedat.eval()))
    if coordinate_dat is None:
        coordinate_dat = op(str(preview.par.Coordinatedat.eval()))
    rows = coordinate_dat.numRows - 1 if coordinate_dat is not None else 0
    if rows != TOTAL_PIXELS:
        raise RuntimeError(
            "Preview contract not applied: expected %d coordinate rows, got %d"
            % (TOTAL_PIXELS, rows)
        )

    callbacks = preview.op("instance_data_callbacks")
    instance_data = preview.op("instance_data")
    if callbacks is None or instance_data is None:
        raise RuntimeError("LED Preview instance callback chain is incomplete")
    patched = patch_callback_source(callbacks.text)
    changed = patched != callbacks.text
    if changed:
        callbacks.text = patched
    instance_data.cook(force=True)
    if instance_data.numSamples != TOTAL_PIXELS:
        raise RuntimeError("LED Preview did not produce %d samples" % TOTAL_PIXELS)
    errors = list(preview.errors(recurse=True))
    if errors:
        raise RuntimeError("LED Preview contract errors: %s" % errors)
    return {
        "pixels": instance_data.numSamples,
        "missingDraftRender": "black",
        "callbackChanged": changed,
        "projectSaved": False,
        "networkChanged": False,
    }


if __name__ == "__main__":
    print(build())
