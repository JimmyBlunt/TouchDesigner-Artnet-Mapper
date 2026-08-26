"""Restoring live regression audit for shortcut dialog 8 (Show Control).

Run inside TouchDesigner (Textport or the local TouchDesigner API).  The audit
never changes the selected visual source, never enables/disables Art-Net and
never saves the project.  Transport commands are exercised only while the
Show source is *not* selected.  Runtime state, tables, preview text and shader
parameters are restored in ``finally``.

Actual mouse clicks and a live-output blackout remain supervised acceptance
tests; this script tests the same callback command path without hardware risk.
"""

from __future__ import annotations

import json


OWNER = "/project1/show_control"
SOURCE_CONTROLS = "/project1/madmapper_player_controls"
SOURCE_SWITCH = "/project1/visual_source_switch"
SHOW_SOURCE_INDEX = 2


def _table(path):
    node = op(path)
    return tuple(
        tuple(str(node[row, column]) for column in range(node.numCols))
        for row in range(node.numRows)
    )


def _restore_table(path, rows):
    node = op(path)
    node.clear()
    for row in rows:
        node.appendRow(row)


def _text_state(owner):
    panel = owner.op("control_panel")
    return {
        "title": str(panel.op("title").par.text.eval()),
        "cue_status": str(panel.op("cue_status").par.text.eval()),
        "transition_status": str(panel.op("transition_status").par.text.eval()),
    }


def _button_state(owner):
    panel = owner.op("control_panel")
    rows = []
    for child in panel.children:
        if child.OPType != "buttonCOMP":
            continue
        rows.append(
            {
                "name": child.name,
                "label": str(child.par.label.eval()),
                "type": str(child.par.buttontype.eval()),
                "state": float(child.panel.state),
                "display": bool(child.par.display.eval()),
                "rect": (
                    int(child.par.x.eval()),
                    int(child.par.y.eval()),
                    int(child.par.w.eval()),
                    int(child.par.h.eval()),
                ),
            }
        )
    return tuple(sorted(rows, key=lambda item: item["rect"][0]))


def _mixer_uniform(owner):
    mixer = owner.op("show_transition_mixer")
    return tuple(float(getattr(mixer.par, "vec0value" + axis).eval()) for axis in "xyzw")


def _runtime_snapshot(sequence):
    return {
        "state": sequence.state,
        "cue_index": sequence.cue_index,
        "elapsed": sequence.elapsed,
        "blackout": sequence.blackout,
        "loop": sequence.show.loop,
        "current_slot": sequence._current_slot,
    }


def _restore_runtime(sequence, snapshot):
    sequence.state = snapshot["state"]
    sequence.cue_index = snapshot["cue_index"]
    sequence.elapsed = snapshot["elapsed"]
    sequence.blackout = snapshot["blackout"]
    sequence.set_loop(snapshot["loop"])
    sequence._current_slot = snapshot["current_slot"]


def run():
    owner = op(OWNER)
    controls = op(SOURCE_CONTROLS)
    switch = op(SOURCE_SWITCH)
    if owner is None or controls is None or switch is None:
        return {"status": "BLOCKED", "reason": "required operator missing"}

    callbacks = owner.op("callbacks")
    execute = owner.op("transport_execute")
    sequence = callbacks.module.runtime()
    active_source = int(switch.par.index.eval())
    source_name = str(controls.par.Source.eval())
    tables = (
        OWNER + "/state_table",
        OWNER + "/slot_a_adapter/material_request",
        OWNER + "/slot_b_adapter/material_request",
        OWNER + "/transition_adapter/mixer_request",
    )
    baseline = {
        "runtime": _runtime_snapshot(sequence),
        "tables": {path: _table(path) for path in tables},
        "text": _text_state(owner),
        "uniform": _mixer_uniform(owner),
        "execute_active": bool(execute.par.active.eval()),
        "source": source_name,
        "switch_index": active_source,
    }
    result = {
        "status": "INVENTORY_ONLY",
        "project": project.name,
        "errors": owner.errors(recurse=True),
        "source": source_name,
        "switch_index": active_source,
        "show_selected": active_source == SHOW_SOURCE_INDEX,
        "buttons": _button_state(owner),
        "visible_text": baseline["text"],
        "state_table": baseline["tables"][OWNER + "/state_table"],
        "cue_table": _table(OWNER + "/cue_table"),
        "commands": (),
    }
    if active_source == SHOW_SOURCE_INDEX:
        result["reason"] = "Show source is live; transport mutation requires supervision"
        return result

    observations = []
    try:
        execute.par.active = False

        callbacks.module.command("stop")
        observations.append(("stop", str(sequence.state.value), sequence.cue_index, sequence.elapsed))
        callbacks.module.command("play")
        observations.append(("play", str(sequence.state.value), sequence.cue_index, sequence.elapsed))
        callbacks.module.command("pause")
        observations.append(("pause", str(sequence.state.value), sequence.cue_index, sequence.elapsed))
        callbacks.module.command("next")
        observations.append(("next", str(sequence.state.value), sequence.cue_index, sequence.elapsed))
        callbacks.module.command("previous")
        observations.append(("previous", str(sequence.state.value), sequence.cue_index, sequence.elapsed))
        callbacks.module.command("go")
        observations.append(("go", str(sequence.state.value), sequence.cue_index, sequence.elapsed))

        before_loop = sequence.show.loop
        callbacks.module.command("loop")
        observations.append(("loop", sequence.show.loop, before_loop))
        before_blackout = sequence.blackout
        callbacks.module.command("blackout")
        observations.append(("blackout", sequence.blackout, before_blackout))

        result["commands"] = tuple(observations)
        result["status"] = "COMPLETED_PENDING_RESTORE"
    finally:
        _restore_runtime(sequence, baseline["runtime"])
        callbacks.module.sync()
        for path, rows in baseline["tables"].items():
            _restore_table(path, rows)
        panel = owner.op("control_panel")
        panel.op("title").par.text = baseline["text"]["title"]
        panel.op("cue_status").par.text = baseline["text"]["cue_status"]
        panel.op("transition_status").par.text = baseline["text"]["transition_status"]
        mixer = owner.op("show_transition_mixer")
        for axis, value in zip("xyzw", baseline["uniform"]):
            getattr(mixer.par, "vec0value" + axis).val = value
        execute.par.active = baseline["execute_active"]

    restored = {
        "source": str(controls.par.Source.eval()) == baseline["source"],
        "switch": int(switch.par.index.eval()) == baseline["switch_index"],
        "tables": all(_table(path) == rows for path, rows in baseline["tables"].items()),
        "text": _text_state(owner) == baseline["text"],
        "uniform": _mixer_uniform(owner) == baseline["uniform"],
        "execute_active": bool(execute.par.active.eval()) == baseline["execute_active"],
    }
    result["restored"] = restored
    result["status"] = "COMPLETED_AND_RESTORED" if all(restored.values()) else "RESTORE_FAILED"
    return result


result = run()
print(json.dumps(result, indent=2, default=str))
