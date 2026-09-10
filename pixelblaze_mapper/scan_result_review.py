"""Review raw SfM and explicitly append to a draft. Never apply or infer a fit."""
from hashlib import sha256
import csv
import json
from math import isfinite
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from .layout_scene import import_scan, append_scan, set_transform, Transform, SceneError
from .layout_scene_adapter import LayoutDocument


def compact_ids(values, *, limit=8):
    """Bounded, human-readable source ranges; never renumber sparse IDs."""
    values = sorted(set(values))
    if not values:
        return 'none'
    ranges = []
    start = end = values[0]
    for value in values[1:]:
        if value == end + 1:
            end = value
        else:
            ranges.append(str(start) if start == end else '%s-%s' % (start, end))
            start = end = value
    ranges.append(str(start) if start == end else '%s-%s' % (start, end))
    return ', '.join(ranges[:limit]) + (' ... (%d IDs)' % len(values) if len(ranges) > limit else '')


def _inspect_file(path):
    try:
        path = Path(path).resolve(strict=True)
        data = path.read_bytes()
        report_data = (path.parent / 'quality_pending.json').read_bytes()
        report = json.loads(report_data)
        reader = csv.DictReader(data.decode('utf-8-sig').splitlines())
        if reader.fieldnames != ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error']:
            raise SceneError('Expected the original candidate_3d.csv columns')
        for row in reader:
            if (None in row or any(value is None for value in row.values())
                    or not all(isfinite(float(row[key])) for key in ('x', 'y', 'z', 'xn', 'yn', 'zn', 'error'))):
                raise SceneError('Candidate contains malformed or nonfinite measurements')
        scan = import_scan(data, format='marimapper-csv', name='Raw scan review')
        missing = set(scan.missing_indices)
        ids = tuple(i for i in range(len(scan.points)) if i not in missing)
        if (not ids or not isinstance(report, dict)
                or not isinstance(report.get('session_id'), str) or not report['session_id'].strip()
                or report.get('reconstructed_ids') != list(ids)
                or any(type(i) is not int for i in report['reconstructed_ids'])):
            raise SceneError('Result IDs differ from the saved reconstruction report')
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SceneError('Cannot review saved result: %s. Choose candidate_3d.csv with its quality_pending.json in the same folder.' % error) from error
    points = [scan.points[i] for i in ids]
    return {'path': str(path), 'sha256': sha256(data).hexdigest(),
            'report_sha256': sha256(report_data).hexdigest(), 'session_id': report['session_id'],
            'ids': list(ids), 'count': len(ids), 'missing_observed_ids': None,
            'bounds_min': [min(p[a] for p in points) for a in range(3)],
            'bounds_max': [max(p[a] for p in points) for a in range(3)],
            'coordinate_units': 'arbitrary_sfm', 'registration': False}


def inspect_saved_result(path):
    """Reopen a persisted raw result for explicit draft review, without a job.

    Sparse CSV gaps are not evidence of failed observations. Older reports do
    not retain the observed input IDs, so their missing count remains unknown.
    """
    return _inspect_file(path)


def inspect_result(status):
    if status.get('state') != 'review_required' or status.get('running'):
        raise SceneError('No completed, validated 3D result is available')
    review = _inspect_file(status['candidate'])
    if (review['count'] != status['reconstructed'] or review['session_id'] != status['session_id']):
        raise SceneError('Result identity differs from completed worker')
    review['missing_observed_ids'] = list(status['missing_ids'])
    return review


def review_defaults(document, review):
    """Suggest an explicit collision-free additive offset, not a hardware route."""
    from .scan_partial_acceptance import occupied_sources
    used = occupied_sources(document)
    ids = set(review['ids'])
    offset = 0 if not used.intersection(ids) else max(0, max(used) + 1 - min(ids))
    names = {obj.name for obj in document.scene.objects}
    name, suffix = 'Raw scan', 2
    while name in names:
        name = 'Raw scan %d' % suffix
        suffix += 1
    return {'name': name, 'offset': str(offset)}


def format_review_summary(review):
    missing = review.get('missing_observed_ids')
    quality = ('Missing observed IDs: unknown in saved report' if missing is None else
               'Missing observed IDs: %d (%s)' % (len(missing), compact_ids(missing)))
    return ('%d reconstructed LEDs | source IDs: %s\n%s\n'
            'Raw SfM coordinates: scale and alignment require review.\n'
            'Next: confirm the source offset, add to draft, then align in Layout 3D.\n'
            'Saved result: %s') % (review['count'], compact_ids(review['ids']), quality, Path(review['path']).parent.name)


def append_reviewed(document, review, *, source_offset, name, transform=Transform()):
    if type(source_offset) is not int or source_offset < 0:
        raise SceneError('Global source offset must be a non-negative integer')
    if not isinstance(name, str) or not name.strip():
        raise SceneError('Enter a name for the draft scan object')
    name = name.strip()
    path = Path(review['path'])
    data = path.read_bytes()
    if (sha256(data).hexdigest() != review['sha256'] or
        sha256((path.parent/'quality_pending.json').read_bytes()).hexdigest() != review['report_sha256']):
        raise SceneError('Result changed after review; review it again')
    scan_id = str(uuid5(NAMESPACE_URL, str(path.resolve()) + review['sha256']))
    if any(s.scan_id == scan_id for s in document.scene.scans):
        raise SceneError('This candidate is already in the draft; select and align that object')
    scan = import_scan(data, format='marimapper-csv', name=name, scan_id=scan_id)
    ids = tuple(review['ids'])
    actual = tuple(i for i in range(len(scan.points)) if i not in set(scan.missing_indices))
    if ids != actual:
        raise SceneError('Reviewed LED selection no longer matches candidate')
    from .scan_partial_acceptance import occupied_sources
    used = occupied_sources(document)
    collisions = used.intersection(source_offset + i for i in ids)
    if collisions:
        suggestion = review_defaults(document, review)['offset']
        raise SceneError('overlapping global source IDs: %s. For an additional object, use offset %s; for replacement, return to the selected Layout object.' % (compact_ids(collisions), suggestion))
    # Keep source gaps: never pack observed LEDs into consecutive addresses.
    updated = append_scan(document.scene, scan, scan_indices=ids,
                          source_indices=tuple(source_offset+i for i in ids), name=name)
    updated = set_transform(updated, updated.objects[-1].object_id, transform)
    return LayoutDocument(updated, document.routes)


def open_review(op, path=None):
    owner = op('/project1/guided_scan')
    review = inspect_saved_result(path) if path is not None else inspect_result(owner.fetch('offline_status', {}))
    previous = owner.fetch('result_review', {}) or {}
    owner.store('result_review', review)
    panel = owner.op('review_panel')
    panel.op('summary').par.text = format_review_summary(review)
    # Keep user edits on repeated opens; initialise defaults for each new result.
    if (previous.get('path'), previous.get('sha256')) != (review['path'], review['sha256']):
        from . import layout_scene_td as layout
        target = op('/project1/layout_scene_editor')
        defaults = review_defaults(layout.editor(target).current, review)
        for name, value in defaults.items():
            node = panel.op(name + '/string')
            if node is not None:
                node.text = value
        for prefix, value in (('t', '0'), ('r', '0'), ('s', '1')):
            for axis in 'xyz':
                node = panel.op(prefix + axis + '/string')
                if node is not None:
                    node.text = value
    notice = panel.op('notice')
    if notice is not None:
        notice.par.text = 'Offset is added to each original source ID; gaps stay intact. The suggestion is draft placement, not controller assignment. Alignment and Undo are available in Layout 3D.'
    panel.openViewer()
    return review


def add_to_draft(op, confirm):
    from . import layout_scene_td as layout
    from .build_scan_session_ui import field_text
    owner = op('/project1/guided_scan')
    target = op('/project1/layout_scene_editor')
    read = lambda name: field_text(owner.op('review_panel/'+name+'/string'))
    transform = Transform(translation=tuple(float(read('t'+a)) for a in 'xyz'),
                          rotation_degrees=tuple(float(read('r'+a)) for a in 'xyz'),
                          scale=tuple(float(read('s'+a)) for a in 'xyz'))
    session = layout.editor(target)
    if session.preview is not None:
        raise SceneError('Finish the current layout drag first')
    review = owner.fetch('result_review', {})
    acquisition = owner.fetch('session', {}) or {}
    if acquisition.get('session_id') == review.get('session_id'):
        from .scan_partial_acceptance import append_partial_reviewed
        from .scan_workflow_ux import view_paths
        updated = append_partial_reviewed(session.current, review, acquisition,
            view_paths(field_text(owner.op('ui_panel/views/string'))),
            source_offset=int(read('offset')), name=read('name'), transform=transform)
    else:
        updated = append_reviewed(session.current, review,
                                 source_offset=int(read('offset')), name=read('name'), transform=transform)
    if not confirm('Add raw scan as a NEW draft object? Existing objects and live output remain unchanged. Source gaps are preserved. Alignment is manual, not verified registration. Undo is available in the 3D tab.'):
        return False
    session.commit(updated)
    session.select(updated.scene.objects[-1].object_id)
    from . import layout_fixture_td
    layout_fixture_td.action(target, 'view3d', None, None)
    layout.refresh(target)
    layout.frame_view(target, reset=True)
    layout.status(target, 'RAW SCAN ADDED TO DRAFT | align selected object; active map unchanged; registration NOT verified')
    target.op('ui_panel').openViewer()
    return True
