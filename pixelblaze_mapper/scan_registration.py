"""Explicit known-ID similarity registration and evidence-gated draft replacement.

No nearest-neighbour pairing, camera, process, output, or file writes. Horn's
proper quaternion rotation is solved with a bounded symmetric Jacobi eigensolver;
positive least-squares scale and translation complete the similarity transform.
"""
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import atan2, cos, degrees, hypot, isfinite, radians, sin, sqrt
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .layout_scene import SceneError, Transform, import_scan, replace_region
from .layout_scene_adapter import LayoutDocument, scene_revision
from .scan_result_review import inspect_saved_result
from .scan_session import ScanSession


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _eigen(matrix):
    """Eigenvalues/vectors of a small real symmetric matrix (columns are vectors)."""
    a = [list(row) for row in matrix]
    n = len(a)
    v = [[float(i == j) for j in range(n)] for i in range(n)]
    for _ in range(100):
        p, q = max(((i, j) for i in range(n) for j in range(i + 1, n)), key=lambda ij: abs(a[ij[0]][ij[1]]))
        if abs(a[p][q]) <= 1e-14 * max(1.0, max(abs(a[i][i]) for i in range(n))):
            return [a[i][i] for i in range(n)], v
        angle = 0.5 * atan2(2 * a[p][q], a[q][q] - a[p][p])
        c, s = cos(angle), sin(angle)
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        for i in range(n):
            if i not in (p, q):
                aip, aiq = a[i][p], a[i][q]
                a[i][p] = a[p][i] = c * aip - s * aiq
                a[i][q] = a[q][i] = s * aip + c * aiq
            vip, viq = v[i][p], v[i][q]
            v[i][p], v[i][q] = c * vip - s * viq, s * vip + c * viq
        a[p][p] = c*c*app - 2*s*c*apq + s*s*aqq
        a[q][q] = s*s*app + 2*s*c*apq + c*c*aqq
        a[p][q] = a[q][p] = 0.0
    raise SceneError('Registration solver did not converge; review the anchor geometry')


def _points(points):
    result = tuple(tuple(p) for p in points)
    if any(len(p) != 3 or any(type(x) not in (int, float) or not isfinite(x) for x in p) for p in result):
        raise SceneError('Registration requires finite 3D measurements')
    return result


def _center(points):
    mean = tuple(sum(p[i] for p in points) / len(points) for i in range(3))
    centered = tuple(tuple(p[i] - mean[i] for i in range(3)) for p in points)
    energy = sum(sum(x*x for x in p) for p in centered)
    if not isfinite(energy) or energy <= 0:
        raise SceneError('Coincident or numerically invalid anchors; choose separated LEDs')
    unit = tuple(tuple(x / sqrt(energy) for x in p) for p in centered)
    gram = [[sum(p[i]*p[j] for p in unit) for j in range(3)] for i in range(3)]
    eigenvalues, _ = _eigen(gram)
    eigenvalues.sort(reverse=True)
    if eigenvalues[1] <= eigenvalues[0] * 1e-8:
        raise SceneError('Collinear or nearly collinear anchors; choose LEDs spanning a surface')
    return mean, centered, energy, unit


def _rotate(matrix, point):
    return tuple(sum(row[i]*point[i] for i in range(3)) for row in matrix)


def fit_similarity(source, destination):
    """Fit paired measurements only; caller supplies known correspondences.

    Returns an existing serializable Transform and residuals. No reflection,
    anisotropic scale, correspondence search, outlier deletion or interpolation.
    """
    source, destination = _points(source), _points(destination)
    if len(source) != len(destination) or len(source) < 3:
        raise SceneError('Use at least three paired, noncollinear fit anchors')
    sm, sc, se, su = _center(source)
    dm, dc, _, du = _center(destination)
    m = [[sum(a[i]*b[j] for a, b in zip(su, du)) for j in range(3)] for i in range(3)]
    xx, xy, xz = m[0]; yx, yy, yz = m[1]; zx, zy, zz = m[2]
    horn = [[xx+yy+zz, yz-zy, zx-xz, xy-yx],
            [yz-zy, xx-yy-zz, xy+yx, zx+xz],
            [zx-xz, xy+yx, -xx+yy-zz, yz+zy],
            [xy-yx, zx+xz, yz+zy, -xx-yy+zz]]
    values, vectors = _eigen(horn)
    best = max(range(4), key=lambda i: values[i])
    w, x, y, z = (vectors[i][best] for i in range(4))
    rotation = ((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
                (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)),
                (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)))
    scale = sum(sum(a*b for a, b in zip(_rotate(rotation, p), q)) for p, q in zip(sc, dc)) / se
    if not isfinite(scale) or scale <= 0:
        raise SceneError('A positive similarity scale could not be fitted')
    translation = tuple(d - scale*s for d, s in zip(dm, _rotate(rotation, sm)))
    cy = hypot(rotation[0][0], rotation[1][0])
    ry = atan2(-rotation[2][0], cy)
    if cy > 1e-10:
        rx, rz = atan2(rotation[2][1], rotation[2][2]), atan2(rotation[1][0], rotation[0][0])
    else:
        rx, rz = atan2(-rotation[1][2], rotation[1][1]), 0.0
    transform = Transform(translation, tuple(map(degrees, (rx, ry, rz))), (scale, scale, scale))
    residuals = tuple(sqrt(sum((a-b)**2 for a, b in zip(transform.apply(p), q))) for p, q in zip(source, destination))
    return transform, residuals


def _inverse(transform, point):
    x, y, z = (p-c-t for p, c, t in zip(point, transform.pivot, transform.translation))
    rx, ry, rz = map(radians, transform.rotation_degrees)
    x, y = x*cos(rz)+y*sin(rz), -x*sin(rz)+y*cos(rz)
    x, z = x*cos(ry)-z*sin(ry), x*sin(ry)+z*cos(ry)
    y, z = y*cos(rx)+z*sin(rx), -y*sin(rx)+z*cos(rx)
    return tuple(v/s+c for v, s, c in zip((x, y, z), transform.scale, transform.pivot))


def _indices(values, label):
    result = tuple(values)
    if not result or len(set(result)) != len(result) or any(type(i) is not int or i < 0 for i in result):
        raise SceneError(label + ' must be explicit, unique non-negative source IDs')
    return result


def prepare_registration(document, session, review, *, fit_source_ids, check_source_ids, accepted_source_ids, max_error):
    """Create immutable-by-digest evidence; acceptance always recalculates it."""
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    if type(max_error) not in (int, float) or not isfinite(max_error) or max_error <= 0:
        raise SceneError('Enter a positive maximum anchor deviation in the target object coordinate units')
    revision = scene_revision(document.scene)
    if session.scene_id != document.scene.scene_id or session.scene_revision != revision:
        raise SceneError('Scene changed since scan planning; restage and review the original selection')
    current = inspect_saved_result(review['path'])
    if any(current[k] != review[k] for k in ('sha256', 'report_sha256', 'session_id', 'ids')):
        raise SceneError('Candidate changed after result review; reopen the result')
    if current['session_id'] != session.session_id:
        raise SceneError('Candidate belongs to a different scan session; restore its original session')
    fit = _indices(fit_source_ids, 'Fit anchors')
    check = _indices(check_source_ids, 'Verification anchors')
    accepted = _indices(accepted_source_ids, 'Replacement selection')
    if len(fit) < 3 or set(fit) & set(check):
        raise SceneError('Choose at least three fit anchors and a separate verification anchor')
    targets = {t.source_index: t for t in session.targets}
    anchor_sources = {t.source_index for t in session.targets if t.led_id in session.anchor_ids}
    selected_sources = {t.source_index for t in session.targets if t.led_id in session.selected_ids}
    if not set(current['ids']) <= anchor_sources | selected_sources:
        raise SceneError('Candidate contains IDs outside the original capture scope')
    if not set(fit + check) <= anchor_sources or not set(accepted) <= selected_sources:
        raise SceneError('Anchors must be fixed staged anchor IDs; replacement IDs must be staged selected LEDs')
    if not set(fit + check + accepted) <= set(current['ids']):
        raise SceneError('A requested anchor or replacement LED has no reconstructed point; add views or reduce the explicit selection')
    observed_twice = {t.source_index for t in session.targets if
                      sum(t.led_id in view.detected_ids for view in session.views) >= 2}
    if not set(fit + check + accepted) <= observed_twice:
        raise SceneError('Every accepted LED and anchor needs completed observations in at least two views')
    bindings = {led.led_id: (obj, led) for obj in document.scene.objects for led in obj.leds}
    for index in fit + check + accepted:
        t = targets[index]
        if t.led_id not in bindings:
            raise SceneError('A stable LED identity no longer exists')
        obj, led = bindings[t.led_id]
        if (obj.object_id, led.local_index, led.source_index) != (t.object_id, t.local_index, index):
            raise SceneError('A stable LED identity differs from the scan plan')
    target_object = document.scene.object(targets[accepted[0]].object_id)
    scans = {scan.scan_id: scan for scan in document.scene.scans}
    reference = {}
    for index in fit + check:
        obj, led = bindings[targets[index].led_id]
        scan = scans[led.scan_id]
        if led.scan_index in scan.missing_indices:
            raise SceneError('A reference anchor is a missing placeholder; select measured fixed LEDs')
        world = obj.transform.apply(scan.registration.apply(scan.points[led.scan_index]))
        reference[index] = _inverse(target_object.transform, world)
    data = Path(current['path']).read_bytes()
    if sha256(data).hexdigest() != current['sha256']:
        raise SceneError('Candidate changed while registration was read')
    raw = import_scan(data, format='marimapper-csv', name='Registered scan')
    transform, fit_errors = fit_similarity([raw.points[i] for i in fit], [reference[i] for i in fit])
    check_errors = tuple(sqrt(sum((a-b)**2 for a, b in zip(transform.apply(raw.points[i]), reference[i]))) for i in check)
    errors = fit_errors + check_errors
    evidence = {'schema': 'pixelblaze-known-id-registration', 'version': 1,
                'scene_revision': revision, 'session_digest': _digest(session.to_dict()),
                'review': current, 'object_id': target_object.object_id,
                'fit_source_ids': list(fit), 'check_source_ids': list(check), 'accepted_source_ids': list(accepted),
                'max_error': float(max_error), 'transform': asdict(transform),
                'fit_errors': list(fit_errors), 'check_errors': list(check_errors),
                'fit_rms': sqrt(sum(e*e for e in fit_errors)/len(fit_errors)),
                'check_rms': sqrt(sum(e*e for e in check_errors)/len(check_errors)),
                'worst_error': max(errors), 'passed': max(errors) <= max_error,
                'preserved_selected_source_ids': sorted(selected_sources-set(accepted)),
                'anchor_policy': 'explicit stable IDs, held-out verification, never replaced'}
    return dict(evidence, digest=_digest(evidence))


def apply_registration(document, session, proposal):
    """Revalidate all evidence and return a draft; caller commits one undo step."""
    if not isinstance(proposal, dict) or proposal.get('schema') != 'pixelblaze-known-id-registration':
        raise SceneError('Prepare and review registration before replacing LEDs')
    if proposal.get('digest') != _digest({k: v for k, v in proposal.items() if k != 'digest'}):
        raise SceneError('Registration evidence changed; calculate and review again')
    checked = prepare_registration(document, session, proposal['review'],
        **{key: proposal[key] for key in ('fit_source_ids', 'check_source_ids', 'accepted_source_ids', 'max_error')})
    if checked['digest'] != proposal['digest']:
        raise SceneError('Registration evidence is stale; calculate and review again')
    if not checked['passed']:
        raise SceneError('Anchor deviation exceeds the reviewed limit; improve views or reference anchors')
    raw_data = Path(checked['review']['path']).read_bytes()
    if sha256(raw_data).hexdigest() != checked['review']['sha256']:
        raise SceneError('Candidate changed before replacement')
    identifier = str(uuid5(NAMESPACE_URL, checked['review']['sha256'] + checked['digest']))
    scan = import_scan(raw_data, format='marimapper-csv', name='Registered scan', scan_id=identifier)
    scan = replace(scan, registration=Transform(**checked['transform']),
                   warnings=scan.warnings + ('Registration evidence: ' + json.dumps(checked, sort_keys=True, allow_nan=False),))
    session = ScanSession.from_dict(session) if isinstance(session, dict) else session
    targets = {t.source_index: t for t in session.targets}
    updated = replace_region(document.scene, checked['object_id'],
        tuple(targets[i].local_index for i in checked['accepted_source_ids']), scan,
        scan_indices=tuple(checked['accepted_source_ids']))
    return LayoutDocument(updated, document.routes)
