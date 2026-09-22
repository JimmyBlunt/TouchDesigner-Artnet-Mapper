_last = None
def onFrameEnd(frame):
    global _last
    now = absTime.seconds
    if _last is None:
        _last = now
        return
    delta = max(0.0, min(1.0, now - _last))
    _last = now
    if delta > 0.0:
        op('callbacks').module.advance(delta)
        # Recording rides the same clock the transport advances, so a
        # recorded move lands at the cue time it plays back at.
        editor = op('editor_callbacks')
        if editor is not None:
            editor.module.record_tick(float(op('callbacks').module._get('elapsed', 0)))
    return
