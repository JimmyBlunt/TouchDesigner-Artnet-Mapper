"""Read-only presentation helpers for the native guided scan panel.

Navigation changes visibility only. Acquisition and reconstruction retain their
existing explicit commands, validation and output guards.
"""


def compact_indices(indices):
    """Lossless compact display of source IDs; never renumber or fill gaps."""
    values = sorted(set(indices))
    groups = []
    for value in values:
        if groups and value == groups[-1][-1] + 1:
            groups[-1].append(value)
        else:
            groups.append([value])
    return ', '.join(str(group[0]) if len(group) == 1 else
                     '%s-%s' % (group[0], group[-1]) for group in groups)


def view_paths(value):
    """Preserve order while ignoring empty/legacy None and duplicate paths."""
    result = []
    seen = set()
    for path in str(value or '').split('|'):
        path = path.strip()
        key = path.replace('\\', '/').casefold()
        if path and key != 'none' and key not in seen:
            seen.add(key)
            result.append(path)
    return result


def guidance(*, session=None, views='', capture=None, camera=None,
             offline=None, prepared=False, manifest=False, page='capture'):
    """Actionable stage hints, never an authorization or a readiness gate."""
    count = len(view_paths(views))
    capture, camera, offline = capture or {}, camera or {}, offline or {}
    if capture.get('running') or capture.get('state') == 'starting':
        return 'CAPTURING — Keep camera and object still. STOP SCAN ends capture safely.'
    if offline.get('running'):
        return 'BUILDING 3D — Wait for the result, or STOP 3D. The layout remains unchanged.'
    if offline.get('state') == 'review_required':
        return 'RESULT READY — Open Review result. Check missing LEDs and alignment before adding a draft object.'
    if session and session.get('stage') in ('cancelled', 'failed'):
        return 'SESSION ENDED — Select an object in Layout or create a new acquisition to continue.'
    if not session:
        return 'START HERE — Select an object in Layout to rescan it, or choose New acquisition. Saved 3D results open in the 3D tab.'
    if page == 'settings':
        return 'SETTINGS — Adjust only when needed. Camera, brightness, scope or workspace edits require Check scan plan again.'
    if page == 'offline':
        if count < 2:
            return 'NEED MORE VIEWS — %d saved. Capture at least two distinct viewpoints, or find matching saved views in your workspace.' % count
        if manifest:
            return '3D JOB PREPARED — Start 3D after reviewing the view list. Reconstructed coordinates still need alignment.'
        return '%d VIEWS SELECTED — Prepare 3D to validate IDs and save the job, then Start 3D.' % count
    if camera.get('running') or camera.get('state') in ('starting', 'native_loading', 'camera_opening', 'configuring', 'ready', 'running'):
        return 'CAMERA PREVIEW — Check focus and framing, then Close camera before starting a scan.'
    if count:
        return '%d VIEW(S) SAVED — Move the camera while capture is stopped. If settings changed, check the plan again before Start next view.%s' % (
            count, ' Continue in 2 · Build 3D when coverage is sufficient.' if count >= 2 else ' A 3D job needs at least two views.')
    if prepared:
        return 'PLAN CHECKED — Review the routing summary below, close camera preview, then Start scan. Changed settings need a fresh plan check.'
    return 'PREPARE — Check the LED range and workspace, preview the camera, then Check scan plan. One scan captures one viewpoint.'


HELP = (
    'NEW SCAN: Select an object in Layout (all LEDs or a selected region), or create a separate acquisition. '
    'Choose an existing workspace folder for saved views.\n\n'
    'CAPTURE: Preview the camera, close preview, then check the scan plan. Start scan requires confirmation '
    'of the affected controllers. Keep camera and object fixed during capture; move the camera only between views. '
    'Two views are the minimum for 3D; additional overlapping views improve coverage.\n\n'
    'EXISTING VIEWS: In Build 3D, Find saved views adds only files whose recorded LED identity and scene '
    'revision match this session. Other CSVs can be selected explicitly; check their provenance.\n\n'
    'PARTIAL RESCAN: Source indices are zero-based and retain their identity. Use ranges such as 0-49, 78. '
    'Optional verification anchors (Settings) are captured but never replaced.\n\n'
    'RESULTS: Review an existing 3D result without recapturing. Raw reconstruction needs alignment and '
    'quality review. Adding a draft object does not replace the original object or resume Live output.'
)


# Existing field and callback paths are kept stable for live capture adapters.
# Rectangles are x, y, width, height in native TouchDesigner panel coordinates.
COMMON = {
    'title': (20, 848, 1120, 36), 'notice': (20, 800, 1120, 40),
    'btn_page_capture': (20, 752, 280, 36), 'btn_page_offline': (310, 752, 280, 36),
    'btn_page_settings': (600, 752, 230, 36), 'btn_help': (840, 752, 300, 36),
    'next_step': (20, 676, 1120, 64), 'coverage': (20, 566, 1120, 100),
    'workspace_label': (20, 393, 1120, 26), 'workspace': (20, 359, 900, 32),
    'btn_browse_workspace': (940, 359, 200, 32),
    'btn_stop': (20, 68, 200, 36), 'btn_offline_stop': (230, 68, 200, 36),
    'btn_back': (440, 68, 210, 36), 'btn_cancel': (660, 68, 200, 36),
    'btn_new_capture': (870, 68, 270, 36),
    'status': (20, 12, 1120, 46),
}
CAPTURE = {
    'source_ids_label': (20, 524, 1120, 26), 'source_ids': (20, 490, 1120, 32),
    'btn_camera_start': (20, 302, 230, 36), 'btn_camera_stop': (260, 302, 230, 36),
    'camera_status': (500, 302, 640, 36),
    'brightness': (20, 246, 100, 32), 'brightness_slider': (135, 246, 1005, 36),
    'brightness_fill': (135, 246, 1, 7), 'brightness_marker': (135, 246, 3, 36),
    'btn_prepare': (20, 183, 400, 36), 'btn_arm': (440, 183, 700, 36),
    'routing_summary': (20, 112, 1120, 56),
}
OFFLINE = {
    'views_label': (20, 524, 1120, 26), 'views': (20, 490, 1120, 32),
    'btn_discover_views': (20, 438, 360, 36), 'btn_add_view': (400, 438, 360, 36),
    'btn_open_saved_result': (780, 438, 360, 36),
    'btn_offline': (20, 286, 355, 36), 'btn_offline_start': (390, 286, 355, 36),
    'btn_offline_result': (760, 286, 380, 36),
    'offline_status': (20, 206, 1120, 64),
}
SETTINGS = {
    'camera_label': (20, 524, 350, 26), 'camera': (20, 490, 350, 32),
    'exposure_label': (400, 524, 350, 26), 'exposure': (400, 490, 350, 32),
    'threshold_label': (780, 524, 360, 26), 'threshold': (780, 490, 360, 32),
    'anchors_label': (20, 464, 1120, 26), 'anchors': (20, 430, 1120, 32),
    'python_label': (20, 297, 1120, 26), 'python': (20, 263, 1120, 32),
    'btn_ports': (20, 183, 400, 36),
}


def refresh(owner):
    """Render navigation/help from stored facts; no hardware or file access."""
    page = owner.fetch('workflow_page', 'capture')
    if page not in ('capture', 'offline', 'settings'):
        page = 'capture'
    visible = dict(COMMON)
    visible.update({'capture': CAPTURE, 'offline': OFFLINE, 'settings': SETTINGS}[page])
    for name in set(COMMON) | set(CAPTURE) | set(OFFLINE) | set(SETTINGS) | {'capabilities'}:
        node = owner.op('ui_panel/' + name)
        if node is None:
            continue
        node.par.display = name in visible
        if name in visible:
            x, y, width, height = visible[name]
            # Preserve the brightness width/position expressions installed by the builder.
            if name != 'brightness_marker':
                node.par.x = x
            node.par.y = y
            if name != 'brightness_fill':
                node.par.w = width
            node.par.h = height
    for key in ('capture', 'offline', 'settings'):
        node = owner.op('ui_panel/btn_page_' + key)
        if node is not None:
            color = (.3, .85, 1) if key == page else (.75, .85, .95)
            node.par.colorr, node.par.colorg, node.par.colorb = color
    node = owner.op('ui_panel/btn_offline_stop')
    if node is not None:
        node.par.display = page == 'offline' or bool((owner.fetch('offline_status', {}) or {}).get('running'))
    camera = owner.fetch('camera_status', {}) or {}
    node = owner.op('ui_panel/camera_status')
    if node is not None and camera:
        node.par.text = 'CAMERA %s | %sx%s | frames %s%s' % (
            camera.get('state', 'unknown'), camera.get('width', '?'), camera.get('height', '?'),
            camera.get('frames', 0), ' | ' + str(camera['error']) if camera.get('error') else '')
    offline = owner.fetch('offline_status', {}) or {}
    node = owner.op('ui_panel/offline_status')
    if node is not None and offline:
        if offline.get('state') == 'review_required':
            node.par.text = 'SAVED 3D RESULT: %s LEDs. Review missing IDs and alignment before adding to the Layout draft.' % offline.get('reconstructed', '?')
        else:
            node.par.text = '3D: %s | %ss%s' % (offline.get('state', 'unknown'), offline.get('elapsed_seconds', 0),
                                               ' | ' + str(offline['error']) if offline.get('error') else '')
    node = owner.op('ui_panel/next_step')
    views = owner.op('ui_panel/views/string')
    if node is not None:
        node.par.text = guidance(session=owner.fetch('session', None),
            views=views.text if views is not None else '',
            capture=owner.fetch('capture_status', {}), camera=owner.fetch('camera_status', {}),
            offline=owner.fetch('offline_status', {}), prepared=bool(owner.fetch('capture_plan', None)),
            manifest=bool(owner.fetch('manifest', None)), page=page)
    advanced = bool(owner.fetch('review_advanced', False))
    for prefix in ('t', 'r', 's'):
        for axis in 'xyz':
            for suffix in ('', '_label'):
                node = owner.op('review_panel/' + prefix + axis + suffix)
                if node is not None:
                    node.par.display = advanced
    node = owner.op('review_panel/btn_review_advanced')
    if node is not None:
        node.par.label = 'HIDE ALIGNMENT SETTINGS' if advanced else 'ALIGNMENT SETTINGS (OPTIONAL)'
    node = owner.op('review_panel/alignment_hint')
    if node is not None:
        node.par.display = not advanced
        rows = []
        for prefix, label in (('t', 'Translation'), ('r', 'Rotation'), ('s', 'Scale')):
            fields = [owner.op('review_panel/' + prefix + axis + '/string') for axis in 'xyz']
            rows.append(label + ': ' + ', '.join(str(field.text).strip() if field is not None else '?' for field in fields))
        node.par.text = 'CURRENT ALIGNMENT\n' + '\n'.join(rows) + '\nAdjust optional settings here, or align the new draft in Layout 3D before applying it.'
