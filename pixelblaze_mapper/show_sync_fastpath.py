"""Reviewed source patches for idle Show synchronization; no native API on import."""

CALLBACK_MARKER = '# SHOW_IDLE_SYNC_FASTPATH_V1'
RENDER_MARKER = '# SHOW_FEEDBACK_SPLIT_V1'
REQUEST_PATHS = (
    'state_table', 'slot_a_adapter/material_request', 'slot_b_adapter/material_request',
    'slot_a_adapter/coordinate_request', 'slot_b_adapter/coordinate_request',
    'transition_adapter/mixer_request',
)


def sync_signature(sequence, plan, op):
    """Request edits invalidate idle skips even when cue/time did not change."""
    content = []
    for path in REQUEST_PATHS:
        table = op(path)
        content.append(None if table is None else table.text)
    render = op('render_sync')
    module = render.module if render is not None else None
    # Editing the same DAT can replace its module or reset its transient context.
    # Either event requires one full render sync before idle feedback can resume.
    feedback_ready = getattr(module, '_feedback_context', True) is not None
    return (id(sequence), sequence.state, sequence.show.loop, plan, tuple(content),
            id(render), id(module), feedback_ready)


CALLBACK_REPLACEMENTS = (
    ("_runtime_record = None\n", "_runtime_record = None\n" + CALLBACK_MARKER + "\n_sync_record = None\n"),
    ("""def sync():
    sequence = runtime()
    plan = sequence.plan()
""", """def sync(_sequence=None, _allow_skip=False):
    global _sync_record
    from pixelblaze_mapper.show_sync_fastpath import sync_signature
    sequence = runtime() if _sequence is None else _sequence
    plan = sequence.plan()
    if _allow_skip and sequence.state is not TransportState.PLAYING and _sync_record is not None:
        if _sync_record[0] == sync_signature(sequence, plan, op):
            render = op('render_sync')
            if render is not None:
                feedback = getattr(render.module, 'sync_feedback', None)
                if feedback is not None:
                    feedback()
                else:
                    render.module.sync_render()
            return plan
    # A failed full synchronization must never leave a successful skip token.
    _sync_record = None
"""),
    ("""    if render is not None:
        render.module.sync_render()
    return plan

def command""", """    if render is not None:
        render.module.sync_render()
    _sync_record = (sync_signature(sequence, plan, op), plan)
    return plan

def command"""),
    ("""def advance(seconds):
    runtime().advance(seconds)
    return sync()
""", """def advance(seconds):
    sequence = runtime()
    sequence.advance(seconds)
    return sync(_sequence=sequence, _allow_skip=True)
"""),
)

RENDER_REPLACEMENTS = (
    ("_last_feedback = 0.0\n", "_last_feedback = 0.0\n" + RENDER_MARKER + "\n_feedback_context = None\n"),
    ("def sync_render():\n    global _last_feedback\n", "def sync_render():\n    global _feedback_context\n"),
    ("""    now = time.monotonic()
    if now - _last_feedback < 0.25:
""", """    _feedback_context = (label_a, preset_a, targets_a, label_b, preset_b, targets_b,
                         mode, progress, output_b_mix, brightness, blackout)
    return sync_feedback()

def sync_feedback():
    global _last_feedback
    if _feedback_context is None:
        return
    (label_a, preset_a, targets_a, label_b, preset_b, targets_b,
     mode, progress, output_b_mix, brightness, blackout) = _feedback_context
    now = time.monotonic()
    if now - _last_feedback < 0.25:
"""),
)


def _restore(source, marker, replacements):
    if marker not in source:
        return source
    for old, new in reversed(replacements):
        if source.count(new) != 1:
            raise ValueError('Show synchronization differs from the reviewed patch: ' + marker)
        source = source.replace(new, old, 1)
    return source


def _install(source, marker, replacements):
    source = _restore(source, marker, replacements)
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Show synchronization anchor differs from reviewed source: ' + marker)
        source = source.replace(old, new, 1)
    compile(source, '<show sync fastpath>', 'exec')
    return source


def install_callback_source(source):
    return _install(source, CALLBACK_MARKER, CALLBACK_REPLACEMENTS)


def restore_callback_source(source):
    return _restore(source, CALLBACK_MARKER, CALLBACK_REPLACEMENTS)


def install_render_source(source):
    return _install(source, RENDER_MARKER, RENDER_REPLACEMENTS)


def restore_render_source(source):
    return _restore(source, RENDER_MARKER, RENDER_REPLACEMENTS)
