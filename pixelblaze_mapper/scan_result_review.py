"""Review raw SfM and explicitly append to a draft. Never apply or infer a fit."""
from hashlib import sha256
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from .layout_scene import import_scan, append_scan, set_transform, Transform, SceneError
from .layout_scene_adapter import LayoutDocument


def inspect_result(status):
    if status.get('state') != 'review_required' or status.get('running'):
        raise SceneError('No completed, validated 3D result is available')
    path = Path(status['candidate']).resolve(strict=True)
    data = path.read_bytes()
    report_data = (path.parent/'quality_pending.json').read_bytes()
    report = json.loads(report_data)
    scan = import_scan(data, format='marimapper-csv', name='Raw scan review')
    ids = tuple(i for i in range(len(scan.points)) if i not in set(scan.missing_indices))
    if (sorted(ids) != report['reconstructed_ids'] or len(ids) != status['reconstructed']
            or report['session_id'] != status['session_id'] or not ids):
        raise SceneError('Result identity differs from completed worker')
    points = [scan.points[i] for i in ids]
    return {'path':str(path), 'sha256':sha256(data).hexdigest(),
            'report_sha256':sha256(report_data).hexdigest(), 'session_id':report['session_id'],
            'ids':list(ids), 'count':len(ids), 'missing_observed_ids':list(status['missing_ids']),
            'bounds_min':[min(p[a] for p in points) for a in range(3)],
            'bounds_max':[max(p[a] for p in points) for a in range(3)],
            'coordinate_units':'arbitrary_sfm', 'registration':False}


def append_reviewed(document, review, *, source_offset, name, transform=Transform()):
    if type(source_offset) is not int or source_offset < 0:
        raise SceneError('Global source offset must be a non-negative integer')
    if not name.strip():
        raise SceneError('Enter a name for the draft scan object')
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
    # Keep source gaps: never pack observed LEDs into consecutive addresses.
    updated = append_scan(document.scene, scan, scan_indices=ids,
                          source_indices=tuple(source_offset+i for i in ids), name=name)
    updated = set_transform(updated, updated.objects[-1].object_id, transform)
    return LayoutDocument(updated, document.routes)


def open_review(op):
    owner = op('/project1/guided_scan')
    review = inspect_result(owner.fetch('offline_status', {}))
    owner.store('result_review', review)
    panel = owner.op('review_panel')
    panel.op('summary').par.text = ('%s LEDs | missing observed IDs: %s\nRaw SfM units; NOT registered.\nBounds: %s to %s\n%s' %
        (review['count'], review['missing_observed_ids'],review['bounds_min'], review['bounds_max'], review['path']))
    panel.openViewer()


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
    updated = append_reviewed(session.current, owner.fetch('result_review', {}),
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
