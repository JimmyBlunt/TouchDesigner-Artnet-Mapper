"""Non-destructive live audit for shortcut dialog 7: OUTPUT CONFIG.

Run this file inside TouchDesigner, or through the local TouchDesigner API.
The audit temporarily changes only custom parameters on the isolated
``/project1/pixelblaze_mapper/output_config`` COMP.  Every value is restored in
``finally``.  It never calls project.save(), never edits controller/segment
tables, never changes a DMX node's Active parameter and never invokes the
Art-Net sender.

The returned dictionary is deliberately descriptive instead of raising on
known defects.  That makes it usable as a before/after regression report while
the dialog is being repaired.
"""

from __future__ import annotations


OWNER = "/project1/pixelblaze_mapper/output_config"
ROUTER = "/project1/multi_controller_output"

INPUT_CASES = (
    ("Enabled", False),
    ("Pixelcount", 3715),
    ("Channelorder", "rgb"),
    ("Autoallocate", False),
    ("Startuniverse", 1),
    ("Startchannel", 2),
    ("Protocol", "artnet_broadcast"),
    ("Targetaddress", "10.0.0.245"),
    ("Localaddress", "10.0.0.125"),
    ("Port", 6455),
    ("Rate", 60),
    ("Priority", 101),
    ("Artsync", False),
)

DERIVED_CASES = (
    ("Universesrequired", 23),
    ("Lastuniversepixels", 145),
    ("Draftstate", "AUDIT_MODIFIED"),
    ("Validationstate", "AUDIT_TEST"),
    ("Allocatorstatus", "AUDIT_TEST"),
)

DMX_PATHS = (
    "/project1/dmxout1",
    "/project1/esp_artnet_out",
    ROUTER + "/dmxout_ws2812_node",
    ROUTER + "/dmxout_apa102_esp",
)


def _eval(parameter):
    try:
        return parameter.eval()
    except Exception:
        return str(parameter)


def _table(path):
    table = op(path)
    if table is None:
        return None
    return tuple(
        tuple(str(table[row, column]) for column in range(table.numCols))
        for row in range(table.numRows)
    )


def _visible_text(owner):
    panel = owner.op("ui_panel")
    if panel is None:
        return ()
    rows = []
    for child in panel.children:
        if child.OPType != "textCOMP":
            continue
        display = getattr(child.par, "display", None)
        if display is not None and not bool(display.eval()):
            continue
        rows.append((child.name, str(child.par.text.eval())))
    return tuple(rows)


def _visible_buttons(owner):
    panel = owner.op("ui_panel")
    if panel is None:
        return ()
    rows = []
    for child in panel.children:
        if child.OPType != "buttonCOMP":
            continue
        rows.append(
            {
                "name": child.name,
                "label": str(child.par.label.eval()),
                "enabled": bool(child.par.enable.eval()),
                "rect": (
                    int(child.par.x.eval()),
                    int(child.par.y.eval()),
                    int(child.par.w.eval()),
                    int(child.par.h.eval()),
                ),
            }
        )
    return tuple(rows)


def _dmx_state():
    state = {}
    for path in DMX_PATHS:
        node = op(path)
        active = getattr(node.par, "active", None) if node is not None else None
        state[path] = None if active is None else bool(active.eval())
    return state


def _router_snapshot():
    sender = op(ROUTER + "/artnet_510_sender_callbacks")
    try:
        sender_status = dict(sender.module.status()) if sender is not None else None
    except Exception as error:
        sender_status = {"error": str(error)}
    return {
        "controller_config": _table(ROUTER + "/controller_config"),
        "segment_config": _table(ROUTER + "/segment_config"),
        "sender_status": sender_status,
        "dmx_active": _dmx_state(),
    }


def run():
    owner = op(OWNER)
    if owner is None:
        return {"status": "BLOCKED", "reason": "missing owner", "path": OWNER}

    original = {parameter.name: _eval(parameter) for parameter in owner.customPars}
    baseline_visible = _visible_text(owner)
    baseline_draft = _table(OWNER + "/config_draft")
    baseline_router = _router_snapshot()
    findings = []

    try:
        for name, alternate in INPUT_CASES:
            parameter = getattr(owner.par, name, None)
            if parameter is None:
                findings.append({"parameter": name, "result": "MISSING"})
                continue
            before = _eval(parameter)
            parameter.val = alternate
            after = _eval(parameter)
            visible_after = _visible_text(owner)
            draft_after = _table(OWNER + "/config_draft")
            router_after = _router_snapshot()
            findings.append(
                {
                    "parameter": name,
                    "kind": "input",
                    "before": before,
                    "requested": alternate,
                    "after": after,
                    "parameter_changed": after != before,
                    "visible_ui_changed": visible_after != baseline_visible,
                    "draft_table_changed": draft_after != baseline_draft,
                    "router_unchanged": router_after == baseline_router,
                    "assessment": (
                        "FAIL_NO_UI_OR_DRAFT_EFFECT"
                        if after != before
                        and visible_after == baseline_visible
                        and draft_after == baseline_draft
                        else "CHECK"
                    ),
                }
            )
            parameter.val = before

        for name, alternate in DERIVED_CASES:
            parameter = getattr(owner.par, name, None)
            if parameter is None:
                findings.append({"parameter": name, "result": "MISSING"})
                continue
            before = _eval(parameter)
            parameter.val = alternate
            after = _eval(parameter)
            findings.append(
                {
                    "parameter": name,
                    "kind": "derived/status",
                    "before": before,
                    "requested": alternate,
                    "after": after,
                    "read_only": bool(parameter.readOnly),
                    "assessment": (
                        "FAIL_EDITABLE_DERIVED_VALUE"
                        if after == alternate and not bool(parameter.readOnly)
                        else "PASS_REJECTED"
                    ),
                }
            )
            parameter.val = before

        # Public pulse parameters are expected to be the stable controller API.
        # Both are safe here: Review/Apply is integration-locked and neither
        # pulse is allowed to reach the production router.
        owner.par.Draftstate = "AUDIT_MODIFIED"
        owner.par.Revertdraft.pulse()
        revert_pulse_result = str(owner.par.Draftstate.eval())
        owner.par.Draftstate = original["Draftstate"]

        owner.par.Validationstate = "AUDIT_TEST"
        owner.par.Reviewapply.pulse()
        apply_pulse_result = str(owner.par.Validationstate.eval())
        owner.par.Validationstate = original["Validationstate"]

        # The local callback itself is tested separately.  This distinguishes
        # a healthy implementation function from a broken button/pulse wire.
        owner.par.Draftstate = "AUDIT_MODIFIED"
        owner.par.Validationstate = "AUDIT_TEST"
        callback = owner.op("callbacks")
        callback_return = callback.module.revert_draft() if callback else None
        direct_callback_state = (
            str(owner.par.Draftstate.eval()),
            str(owner.par.Validationstate.eval()),
        )

        click = owner.op("click_revert_draft")
        click_target = str(click.par.fromop.eval()) if click is not None else None
        click_target_exists = op(click_target) is not None if click_target else False

        source = op("/project1/math1")
        return {
            "status": "COMPLETED_AND_RESTORED",
            "project": project.name,
            "source": {
                "path": "/project1/math1",
                "pixel_samples": source.numSamples if source is not None else None,
                "channels": source.numChans if source is not None else None,
                "timeline_fps": project.cookRate,
            },
            "visible_buttons": _visible_buttons(owner),
            "button_instance_count": len(_visible_buttons(owner)),
            "click_target": click_target,
            "click_target_exists": click_target_exists,
            "revert_pulse_result": revert_pulse_result,
            "review_apply_pulse_result": apply_pulse_result,
            "direct_callback_return": callback_return,
            "direct_callback_state": direct_callback_state,
            "parameter_findings": tuple(findings),
            "baseline_visible_text": baseline_visible,
            "baseline_draft": baseline_draft,
            "baseline_router": baseline_router,
        }
    finally:
        for name, value in original.items():
            parameter = getattr(owner.par, name, None)
            if parameter is not None and parameter.style != "Pulse":
                parameter.val = value

        # Safety assertion: the audit must leave all production-facing state
        # byte-for-byte equivalent to the entry snapshot.
        if _router_snapshot() != baseline_router:
            raise RuntimeError("SAFETY FAILURE: router/output state changed during audit")


# This is intentionally a TouchDesigner-only executable audit script.
result = run()
