"""Bounded, read-only visual coverage data in measured camera coordinates.

Neighborhoods identify two measured references around a short unseen ID run;
they are not estimated positions of missing LEDs, nor proof of physical wiring.
"""
from bisect import bisect_left
from collections import Counter
import csv
import json
from math import hypot, isfinite
from pathlib import Path

from .scan_session import ScanSession, ScanSessionError

MAX_VIEWS = 64
MAX_IDS = 100000
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_NEIGHBOR_GAP = 8
MAX_NEIGHBOR_DISTANCE = .15


def _read(path, budget):
    size = path.stat().st_size
    budget[0] += size
    if size > MAX_FILE_BYTES or budget[0] > MAX_TOTAL_BYTES:
        raise ScanSessionError('Coverage files exceed the bounded analysis limit')
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) != size:
        raise ScanSessionError('Coverage file changed while reading; refresh the view')
    return data.decode('utf-8-sig')


def _coordinates(path, budget, candidate=False):
    reader = csv.DictReader(_read(path, budget).splitlines())
    allowed = (['index', 'x', 'y', 'z'], ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error'])
    if (reader.fieldnames not in allowed if candidate else reader.fieldnames != ['index', 'u', 'v']):
        raise ScanSessionError('Unexpected coverage CSV columns')
    points = {}
    for row in reader:
        if len(points) >= MAX_IDS or None in row or any(value is None for value in row.values()):
            raise ScanSessionError('Malformed or oversized coverage CSV')
        try:
            index = int(row['index'])
            values = tuple(float(row[key]) for key in reader.fieldnames[1:])
        except (ValueError, TypeError) as error:
            raise ScanSessionError('Invalid coverage measurement') from error
        if (index < 0 or index in points or not all(isfinite(value) for value in values)
                or (not candidate and not all(0 <= value <= 1 for value in values))):
            raise ScanSessionError('Duplicate LED ID or invalid coverage coordinates')
        points[index] = values
    if not points:
        raise ScanSessionError('Coverage CSV has no measurements')
    return points


def _runs(ids):
    run = []
    for index in sorted(ids):
        if run and index != run[-1] + 1:
            yield run
            run = []
        run.append(index)
    if run:
        yield run


def build_data(view_paths, expected_ids, candidate_path=None, session=None):
    """Return JSON-safe measured coverage and explicitly unlocated missing IDs.

    ``best_view`` is a path or None. ``unreconstructed_ids`` includes unseen IDs
    when a candidate exists; without a candidate it is empty. Views contain only
    actual observations. Counts are independent-view counts after path deduping.
    """
    expected = set()
    for count, index in enumerate(expected_ids):
        if count >= MAX_IDS or type(index) is not int or index < 0:
            raise ScanSessionError('Expected LED IDs must be bounded non-negative integers')
        expected.add(index)
    if not expected:
        raise ScanSessionError('Select the expected LED scope before visualising coverage')
    paths, unique = [], set()
    for count, filename in enumerate(view_paths):
        if count >= MAX_VIEWS * 4:
            raise ScanSessionError('Too many coverage view paths')
        path = Path(filename).resolve(strict=True)
        if path not in unique:
            unique.add(path)
            paths.append(path)
            if len(paths) > MAX_VIEWS:
                raise ScanSessionError('Select at most 64 coverage views')
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    if session is not None:
        from .scan_library import verified_view_paths
        scope = {target.source_index for target in session.targets if target.led_id in session.capture_ids}
        if not expected <= scope:
            raise ScanSessionError('Expected coverage IDs exceed the verified session scope')
        verified_view_paths(paths, session)
    budget = [0]
    observations = [_coordinates(path, budget) for path in paths]
    for points in observations:
        if not set(points) <= expected:
            raise ScanSessionError('View contains LED IDs outside the expected coverage scope')
    counts = Counter(index for points in observations for index in points)
    reconstructed = set()
    if candidate_path is not None:
        candidate_path = Path(candidate_path).resolve(strict=True)
        reconstructed = set(_coordinates(candidate_path, budget, candidate=True))
        if not reconstructed <= expected:
            raise ScanSessionError('Candidate contains LED IDs outside the expected coverage scope')
        if session is not None:
            report = json.loads(_read(candidate_path.parent / 'quality_pending.json', budget))
            ids = report.get('reconstructed_ids') if isinstance(report, dict) else None
            if (not isinstance(report, dict) or report.get('session_id') != session.session_id or not isinstance(ids, list)
                    or any(type(index) is not int for index in ids)
                    or ids != sorted(reconstructed)):
                raise ScanSessionError('Candidate identity differs from the verified session')
    has_candidate = candidate_path is not None
    unseen = expected - counts.keys()
    unreconstructed = expected - reconstructed if has_candidate else set()
    weak = {index for index in (reconstructed if has_candidate else counts) if counts[index] < 3}
    measured = sorted(counts)
    brackets = []
    for run in _runs(unseen):
        position = bisect_left(measured, run[0])
        if len(run) > MAX_NEIGHBOR_GAP or position == 0 or position == len(measured):
            continue
        before, after = measured[position - 1], measured[position]
        # Do not bridge omitted source ranges or other observed LEDs.
        if before == run[0] - 1 and after == run[-1] + 1:
            brackets.append((run, before, after))
    views, located = [], set()
    for path, observations_for_view in zip(paths, observations):
        points, neighbors, covered = [], [], set()
        for index, (u, v) in sorted(observations_for_view.items()):
            status = ('unreconstructed' if has_candidate and index not in reconstructed else
                      'weak' if counts[index] < 3 else 'good')
            points.append({'id': index, 'u': u, 'v': v, 'status': status, 'count': counts[index]})
        for missing, before, after in brackets:
            if before not in observations_for_view or after not in observations_for_view:
                continue
            u0, v0 = observations_for_view[before]
            u1, v1 = observations_for_view[after]
            if hypot(u1-u0, v1-v0) > MAX_NEIGHBOR_DISTANCE:
                continue
            neighbors.append({'missing_ids': list(missing), 'kind': 'neighborhood_reference',
                              'before': {'id': before, 'u': u0, 'v': v0},
                              'after': {'id': after, 'u': u1, 'v': v1}})
            covered.update(missing)
        located.update(covered)
        views.append({'name': path.parent.name + '/' + path.name, 'path': str(path),
                      'points': points, 'neighbors': neighbors,
                      'visible_unreconstructed': sum(point['status'] == 'unreconstructed' for point in points),
                      'neighbor_missing_count': len(covered),
                      'unlocated_count': len(unseen - covered)})
    best = max(views, key=lambda view: view['visible_unreconstructed'] + view['neighbor_missing_count'], default=None)
    return {'total': len(expected), 'has_candidate': has_candidate,
            'reconstructed_count': len(reconstructed), 'never_seen_ids': sorted(unseen),
            'unreconstructed_ids': sorted(unreconstructed), 'weak_ids': sorted(weak),
            'unlocated_ids': sorted(unseen - located), 'unlocated_count': len(unseen - located),
            'views': views, 'best_view': best['path'] if best else None}
