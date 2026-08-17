"""Repair dormant legacy nodes without changing the production signal path.

The original project contains two disconnected Script CHOP experiments and a
Pixelblaze recorder prototype.  Their eager optional imports made TouchDesigner
report errors even though none of the nodes feed the current mapper.  This
idempotent repair keeps the prototypes available, makes imports lazy/safe and
restores four missing calibration parameters used by the background preview.
"""

from __future__ import annotations


LINEAR_INTERPOLATOR = r'''# Dormant legacy RGB interpolation experiment.
import numpy as np

def onSetupParameters(scriptOp):
    page = scriptOp.appendCustomPage('Custom')
    page.appendFloat('Valuea', label='Value A')
    page.appendFloat('Valueb', label='Value B')
    return

def onPulse(par):
    return

def onCook(scriptOp):
    scriptOp.clear()
    if not scriptOp.inputs:
        return
    source = scriptOp.inputs[0]
    if source.numSamples < 1 or source.numChans < 3:
        return
    count = source.numSamples
    output_count = count * 6
    source_axis = np.arange(count, dtype=float)
    target_axis = np.linspace(0.0, max(0, count - 1), output_count)
    for name in ('r', 'g', 'b'):
        input_channel = source[name]
        if input_channel is None:
            return
        output_channel = scriptOp.appendChan(name)
        output_channel.vals = np.interp(target_axis, source_axis, input_channel.vals)
    return
'''


def _repair_optional_websocket():
    recorder = op('/project1/pixelblaze_script')
    if recorder is None:
        return False
    source = recorder.text
    source = source.replace(
        'import websockets',
        "try:\n    import websockets\nexcept ImportError:\n    websockets = None",
    )
    source = source.replace(
        'self.websocket = self.loop.run_until_complete(websockets.connect(self.config[\'uri\']))',
        "if websockets is None:\n                raise RuntimeError('Optional package websockets is not installed')\n            self.websocket = self.loop.run_until_complete(websockets.connect(self.config['uri']))",
    )
    # A module import must never open a network connection.  The recorder can
    # still be started explicitly from its intended control.
    source = source.replace('recorder.start()\n', '# recorder.start() is an explicit user action\n')
    recorder.text = source
    return True


def _repair_calibration_parameters():
    owner = op('/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype')
    if owner is None:
        return False
    page = owner.appendCustomPage('Rear Split Compatibility')
    values = {
        'Rearmidtopx': (float(owner.par.Reartlx) + float(owner.par.Reartrx)) * 0.5,
        'Rearmidtopy': (float(owner.par.Reartly) + float(owner.par.Reartry)) * 0.5,
        'Rearmidbottomx': (float(owner.par.Rearblx) + float(owner.par.Rearbrx)) * 0.5,
        'Rearmidbottomy': (float(owner.par.Rearbly) + float(owner.par.Rearbry)) * 0.5,
    }
    for name, value in values.items():
        parameter = getattr(owner.par, name, None)
        if parameter is None:
            parameter = page.appendFloat(name, label=name.replace('Rear', 'Rear '))
            parameter.default = value
            parameter.val = value
    return True


def repair():
    interpolation = op('/project1/script1_callbacks')
    if interpolation is not None:
        interpolation.text = LINEAR_INTERPOLATOR
    websocket = _repair_optional_websocket()
    calibration = _repair_calibration_parameters()
    # Force a safe recook so stale error flags clear.  None of these nodes has
    # a downstream production connection.
    for path in ('/project1/script1', '/project1/null_rgb_stream1'):
        node = op(path)
        if node is not None:
            node.cook(force=True)
    prototype = op('/project1/pixelblaze_mapper/preview3d/phase2_interaction_background_prototype')
    if prototype is not None:
        for name in ('mesh_rear_left_pin', 'mesh_rear_right_pin'):
            if prototype.op(name) is not None:
                prototype.op(name).cook(force=True)
    stale_click = op('/project1/pixelblaze_mapper/output_config/click_revert_draft')
    if stale_click is not None:
        stale_click.clearScriptErrors()
    return {
        'legacyInterpolator': interpolation is not None,
        'optionalWebsocket': websocket,
        'calibrationParameters': calibration,
        'networkStarted': False,
        'productionRewired': False,
    }


print(repair())
