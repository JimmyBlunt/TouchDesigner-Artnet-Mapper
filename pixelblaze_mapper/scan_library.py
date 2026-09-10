"""Read-only, bounded discovery of saved MariMapper views.

Only views whose persisted LED identities and scene revision match the staged
session are suggested automatically. CSV filenames or equal numeric indices
alone cannot prove that a view belongs to the same physical object.
"""
import csv
import json
from collections import deque
from dataclasses import replace
from math import isfinite
from pathlib import Path

from .scan_session import ScanSession, ScanSessionError

MAX_FILES = 250
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_SELECTION_BYTES = 32 * 1024 * 1024


def _read(path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('file exceeds 16 MB discovery limit; select it explicitly')
    return path.read_text(encoding='utf-8-sig')


def _view_ids(path):
    reader = csv.DictReader(_read(path).splitlines())
    if reader.fieldnames != ['index', 'u', 'v']:
        raise ValueError('expected 2D index,u,v CSV')
    ids = set()
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('malformed observation columns')
        index = int(row['index'])
        values = (float(row['u']), float(row['v']))
        if index < 0 or index in ids or not all(isfinite(v) and 0 <= v <= 1 for v in values):
            raise ValueError('duplicate ID or invalid image coordinates')
        ids.add(index)
    if not ids:
        raise ValueError('empty view')
    return ids


def discover_saved_views(workspace, session=None):
    """List root CSVs and capture-*/view.csv without mutation or reconstruction.

    ``paths`` contains identity-verified matches only. ``available`` also lists
    valid legacy/mismatched views with an actionable reason. The UI can report
    those but must not silently attach them. No directory recursion is used.
    """
    if not str(workspace).strip():
        raise ScanSessionError('Choose a scan workspace folder before finding saved views')
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise ScanSessionError('Choose an existing scan workspace folder')
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    expected = ({str(t.source_index): t.led_id for t in session.targets if t.led_id in session.capture_ids}
                if session is not None else {})
    available, skipped, matches = [], [], []
    seen = set()
    truncated = False
    candidates = 0
    # Stop discovery itself at the bound, not only result rendering.
    for examined, entry in enumerate(root.iterdir()):
        if candidates >= MAX_FILES or examined >= MAX_FILES * 4:
            truncated = True
            break
        if entry.is_file() and entry.suffix.lower() == '.csv':
            path = entry
        elif entry.is_dir() and entry.name.startswith('capture-'):
            path = entry / 'view.csv'
            if not path.is_file():
                continue
        else:
            continue
        candidates += 1
        try:
            path = path.resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError('linked file is outside the selected workspace')
            if path in seen:
                continue
            seen.add(path)
            ids = _view_ids(path)
            compatible = False
            reason = 'Legacy view: no identity evidence; choose explicitly after checking its object and source IDs'
            manifest_path = path.parent / 'capture.json'
            result_path = path.parent / 'result.json'
            if manifest_path.is_file() and result_path.is_file():
                for evidence in (manifest_path, result_path):
                    if not evidence.resolve(strict=True).is_relative_to(root):
                        raise ValueError('linked metadata is outside the selected workspace')
                manifest = json.loads(_read(manifest_path))
                result = json.loads(_read(result_path))
                if result.get('state') != 'complete':
                    raise ValueError('capture did not finish successfully')
                identity = manifest.get('identity')
                if session is None:
                    reason = 'Stage the matching object/acquisition to verify saved LED identity'
                elif (isinstance(identity, dict) and identity
                      and manifest.get('scene_revision') == session.scene_revision
                      and all(key in expected and expected[key] == value for key, value in identity.items())
                      and all(str(index) in identity for index in ids)):
                    compatible = True
                    reason = 'LED identities and scene revision match the current scan selection'
                else:
                    reason = 'Different LED identity, scene revision or scan scope; stage the original selection'
            available.append({'path': str(path), 'count': len(ids), 'compatible': compatible, 'reason': reason})
            if compatible:
                matches.append(str(path))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            skipped.append(entry.name + ': ' + str(error))
    available.sort(key=lambda item: item['path'])
    matches.sort()
    message = ('%d matching saved views found; %d other views require explicit selection; %d unreadable or incomplete.' %
               (len(matches), len(available) - len(matches), len(skipped)))
    if session is None:
        message += ' Select a Layout object or create an acquisition first.'
    if truncated:
        message += ' Discovery stopped at %d files; choose a narrower folder.' % MAX_FILES
    return {'paths': matches, 'available': available, 'skipped': skipped,
            'truncated': truncated, 'message': message}


def library_index(workspace, *, max_files=MAX_FILES, max_entries=1000, max_depth=2):
    """Cheap explicit index: headers only, bounded directory breadth and depth.

    No CSV body parsing, recursive glob, or filesystem work on UI frame callbacks.
    A fresh explicit refresh is required to discover new files.
    """
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise ScanSessionError('Choose an existing scan folder')
    queue = deque([(root, 0)])
    seen, entries, items, errors = set(), 0, [], []
    truncated = False
    while queue and not truncated:
        folder, depth = queue.popleft()
        try:
            for entry in folder.iterdir():
                entries += 1
                if entries > max_entries or len(items) >= max_files:
                    truncated = True
                    break
                resolved = entry.resolve(strict=True)
                if not resolved.is_relative_to(root) or resolved in seen:
                    continue
                seen.add(resolved)
                if entry.is_dir():
                    if depth < max_depth:
                        queue.append((resolved, depth + 1))
                    continue
                if entry.suffix.lower() != '.csv':
                    continue
                size = entry.stat().st_size
                if size > MAX_FILE_BYTES:
                    errors.append(str(entry.relative_to(root)) + ': exceeds 16 MB limit')
                    continue
                with entry.open(encoding='utf-8-sig') as stream:
                    header = stream.readline(1024).strip()
                columns = next(csv.reader([header]), [])
                kind = ('2D view' if columns == ['index', 'u', 'v'] else
                        '3D scan' if columns[:4] == ['index', 'x', 'y', 'z'] else None)
                if kind:
                    items.append({'path': str(resolved), 'name': str(entry.relative_to(root)),
                                  'kind': kind, 'bytes': size})
        except (OSError, ValueError) as error:
            errors.append(folder.name + ': ' + str(error))
    items.sort(key=lambda item: item['name'].casefold())
    return {'root': str(root), 'items': items, 'errors': errors,
            'truncated': truncated, 'examined': min(entries, max_entries)}


def filter_items(index, query='', kind='all'):
    words = query.casefold().split()
    return [item for item in index['items'] if (kind == 'all' or item['kind'] == kind)
            and all(word in (item['name'] + ' ' + item['kind']).casefold() for word in words)]


def inspect_preview(path, *, max_points=8000):
    """Read and validate one explicitly selected CSV; retain bounded display points."""
    path = Path(path).resolve(strict=True)
    reader = csv.DictReader(_read(path).splitlines())
    columns = reader.fieldnames or []
    if columns == ['index', 'u', 'v']:
        axes, kind = ('u', 'v'), '2D view'
    elif columns[:4] == ['index', 'x', 'y', 'z']:
        axes, kind = ('x', 'y', 'z'), '3D scan'
    else:
        raise ScanSessionError('Select a 2D view CSV or a 3D index,x,y,z CSV')
    points, ids = [], set()
    bounds_min, bounds_max = [float('inf')] * len(axes), [-float('inf')] * len(axes)
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ScanSessionError('Malformed CSV columns')
        index = int(row['index'])
        point = tuple(float(row[key]) for key in axes)
        if index < 0 or index in ids or not all(isfinite(value) for value in point):
            raise ScanSessionError('Duplicate/negative ID or nonfinite coordinate')
        if kind == '2D view' and not all(0 <= value <= 1 for value in point):
            raise ScanSessionError('2D view coordinates must be in 0..1')
        ids.add(index)
        if len(ids) > 100000:
            raise ScanSessionError('Preview supports at most 100000 LED measurements')
        for axis, value in enumerate(point):
            bounds_min[axis] = min(bounds_min[axis], value)
            bounds_max[axis] = max(bounds_max[axis], value)
        points.append((index, *point))
    if not points:
        raise ScanSessionError('The selected CSV is empty')
    stride = max(1, (len(points) + max_points - 1) // max_points)
    return {'path': str(path), 'kind': kind, 'count': len(ids), 'ids': sorted(ids),
            'points': points[::stride], 'sampled': stride > 1,
            'bounds_min': bounds_min, 'bounds_max': bounds_max}


def verified_view_paths(paths, session):
    """Validate every explicitly selected view against exact persisted identities.

    Equal numeric IDs never authorize mixing independent acquisition namespaces.
    Legacy CSVs are still available through the existing explicit expert import.
    """
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    expected = {str(t.source_index): t.led_id for t in session.targets
                if t.led_id in session.capture_ids}
    result, total_bytes = [], 0
    filenames = list(dict.fromkeys(paths))
    if len(filenames) > 64:
        raise ScanSessionError('Select at most 64 views per reconstruction')
    for filename in filenames:
        path = Path(filename).resolve(strict=True)
        total_bytes += sum(file.stat().st_size for file in
                           (path, path.parent / 'capture.json', path.parent / 'result.json'))
        if total_bytes > MAX_SELECTION_BYTES:
            raise ScanSessionError('Selected views and metadata exceed the 32 MB analysis limit; select fewer views')
        ids = _view_ids(path)
        manifest = json.loads(_read(path.parent / 'capture.json'))
        final = json.loads(_read(path.parent / 'result.json'))
        identity = manifest.get('identity', {})
        if (final.get('state') != 'complete' or not identity
                or manifest.get('scene_revision') != session.scene_revision
                or not all(key in expected and value == expected[key] for key, value in identity.items())
                or not all(str(index) in identity for index in ids)):
            raise ScanSessionError('Selected view belongs to another acquisition, revision or LED range. Resume its original acquisition first.')
        result.append(str(path))
    return result


def resume_acquisition(view_path):
    """Recover a standalone acquisition's ORIGINAL namespace from saved evidence.

    Settings and all persisted IDs must agree with the original deterministic
    settings revision. This creates a planned session only; no outputs or files.
    """
    from uuid import UUID
    from .scan_session import ScanTarget
    from .scan_routing import ScanRoutingSnapshot
    from .standalone_scan import revision, routing
    from .camera_probe import ProbePlan
    path = Path(view_path).resolve(strict=True)
    manifest = json.loads(_read(path.parent / 'capture.json'))
    final = json.loads(_read(path.parent / 'result.json'))
    if manifest.get('schema') != 'pixelblaze-single-view-capture' or final.get('state') != 'complete':
        raise ScanSessionError('Resume requires a completed original capture with identity metadata')
    ProbePlan(**manifest['camera'])
    snapshot = ScanRoutingSnapshot.from_dict(manifest['routing'])
    config = snapshot.config
    if len(config.controllers) != 1 or len(config.segments) != 1:
        raise ScanSessionError('This is a Layout scan. Stage its original Layout object first.')
    c = config.controllers[0]
    settings = {'name': c.name, 'target': c.target_address, 'interface': c.local_interface,
                'universe': c.start_universe, 'count': config.source_pixel_count,
                'rate': c.rate, 'order': c.color_order}
    routing(settings)
    if revision(settings) != manifest.get('scene_revision'):
        raise ScanSessionError('Original acquisition settings cannot be verified. Stage its original Layout object instead.')
    identity = manifest.get('identity', {})
    if not identity or set(identity) != {str(i) for i in snapshot.source_indices}:
        raise ScanSessionError('Saved capture lacks complete LED identity metadata')
    namespace = next(iter(identity.values())).split(':led:')[0]
    if not namespace.startswith('capture-') or namespace != 'capture-' + str(UUID(namespace[8:])):
        raise ScanSessionError('Original acquisition namespace is invalid')
    if any(value != namespace + ':led:' + key for key, value in identity.items()):
        raise ScanSessionError('Saved capture mixes acquisition identities')
    targets = tuple(ScanTarget(namespace + ':led:' + str(i), namespace, i, i)
                    for i in range(settings['count']))
    selected = tuple(targets[i].led_id for i in snapshot.source_indices)
    session = ScanSession(namespace, namespace, manifest['scene_revision'], targets, selected)
    verified_view_paths([path], session)
    return {'session': session.to_dict(), 'settings': settings,
            'workspace': str(path.parent.parent), 'camera': manifest['camera'],
            'brightness': snapshot.brightness_cap * 100}


def coverage_selection(session, paths, kind):
    """Explicit analysis and a fresh planned sub-scope, preserving stable IDs."""
    from .scan_coverage import coverage
    from .scan_session import Stage
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    paths = verified_view_paths(paths, session)
    if not paths:
        raise ScanSessionError('Select at least one identity-verified view to analyse coverage')
    lookup = {t.source_index: t.led_id for t in session.targets if t.led_id in session.selected_ids}
    data = coverage(paths, lookup)
    if data['errors']:
        raise ScanSessionError('A selected view is invalid; refresh the library')
    if kind == 'missing':
        sources = data['missing']
    elif kind == 'weak':
        sources = sorted(set(data['missing']) | set(data['weak']))
    else:
        raise ScanSessionError('Choose missing or weak coverage')
    if not sources:
        raise ScanSessionError('No LEDs match this coverage filter. The existing scope is unchanged.')
    fresh = replace(session, stage=Stage.PLANNED, selected_ids=tuple(lookup[i] for i in sources),
                    views=(), active_view=None, candidate_scan_id=None, candidates=(),
                    registration_reference=None, quality_reference=None, failure_reason=None)
    return fresh, data
