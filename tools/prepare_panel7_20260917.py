"""Fit measured Panel 7 into the fourth-row left slot, preserving LED IDs.

Front view convention (same as Panel 5 / Panel 6): X up, Y rear-wall depth,
decreasing Z toward screen-right.  Target slot: under Panel 5, left of Panel 8.
The operator confirmed the physical orientation against the measured plot:
the large filled block (scan indices 356..548) belongs in the LOWER LEFT
corner, the full-width strip (0..240) runs along the TOP edge.
"""
from dataclasses import replace, asdict
from math import asin, atan2, degrees
from pathlib import Path
import csv
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pixelblaze_mapper.layout_scene_adapter import load_document_json, document_json, RouteBinding
from pixelblaze_mapper.layout_scene import Transform
from pixelblaze_mapper.scan_result_review import inspect_result
from pixelblaze_mapper.scan_partial_acceptance import append_partial_reviewed
from pixelblaze_mapper.layout_remove_leds import prepare as remove_leds
from pixelblaze_mapper.scan_workflow_ux import view_paths

OUT = ROOT / 'docs/panel7-integration-20260917'
OFFSET = 7646
COUNT = 8195
RETIRED = set(range(2976, 3232))
TEMPLATE_ID = '33ef5c9a-877d-5d46-a359-13632f057db5'
BLOCK_STRIP = 240      # scan indices 0..240   -> full width strip
BLOCK_SQUARE = 356     # scan indices 356..548 -> large filled block


def prepare():
    original = load_document_json((OUT / 'before-document.json').read_text(encoding='utf-8'))
    status = json.loads((OUT / 'reconstruction-status.json').read_text(encoding='utf-8'))
    session = json.loads((OUT / 'reconstruction-session.json').read_text(encoding='utf-8'))
    paths = view_paths(json.loads((OUT / 'before-fields.json').read_text(encoding='utf-8'))['views'])
    review = inspect_result(status)
    assert review['count'] == 549 and set(review['ids']) == set(range(549))
    updated = append_partial_reviewed(
        original, review, session, paths, source_offset=OFFSET,
        name='Panel 7 | unter Panel 5, links neben Panel 8 | 30 x 30 cm')
    panel = updated.scene.objects[-1]
    scan = next(s for s in updated.scene.scans if s.scan_id == panel.leds[0].scan_id)
    ids = np.array([b.scan_index for b in panel.leds])
    points = np.array([scan.registration.apply(scan.points[i]) for i in ids])
    center = points.mean(0)
    _, singular, basis = np.linalg.svd(points - center, full_matrices=False)
    planarity = float(singular[2] / singular[1])
    assert planarity < .05, 'Scan is not planar enough to fit (%.3f)' % planarity
    normal = basis[2]; u = basis[0]; v = np.cross(normal, u)
    strip = ids <= BLOCK_STRIP
    square = ids >= BLOCK_SQUARE
    assert strip.sum() and square.sum()
    candidates = []
    for angle in np.linspace(0, 2 * np.pi, 1440, endpoint=False):
        horizontal = u * np.cos(angle) + v * np.sin(angle)
        vertical = -u * np.sin(angle) + v * np.cos(angle)
        # Both signs are proper rotations; the operator-confirmed block layout
        # resolves which side of the plane faces the room.
        for sign in (1, -1):
            rotation = np.array([vertical, -normal * sign, -horizontal * sign])
            q = (points - center) @ rotation.T
            a = q[strip].mean(0); b = q[square].mean(0)
            middle = q[~strip & ~square].mean(0)
            if b[0] >= a[0]:            # filled block must sit BELOW the strip
                continue
            if b[2] <= middle[2]:       # ... and further LEFT than the middle steps
                continue
            extent = np.ptp(q, axis=0)
            candidates.append((extent[0] * extent[2], rotation, q))
    assert candidates, 'Requested physical orientation not supported by measured blocks'
    _, rotation, q = min(candidates, key=lambda c: c[0])
    assert np.linalg.det(rotation) > .999
    world = {b.source_index: p for b, p in original.scene.world_points()}
    template = np.array([world[i] for i in sorted(RETIRED)])
    assert np.allclose(template.min(0), [.215625, 1., .515625])
    assert np.allclose(template.max(0), [.384375, 1., .684375])
    destination = (template.min(0) + template.max(0)) / 2
    scale = .16875 / max(np.ptp(q, axis=0)[[0, 2]])
    midpoint = (q.min(0) + q.max(0)) / 2
    translation = destination - scale * (rotation @ center + midpoint)
    ry = asin(float(np.clip(-rotation[2, 0], -1, 1)))
    rx = atan2(rotation[2, 1], rotation[2, 2]); rz = atan2(rotation[1, 0], rotation[0, 0])
    transform = Transform(translation=tuple(translation),
                          rotation_degrees=tuple(map(degrees, (rx, ry, rz))),
                          scale=(scale,) * 3)
    fitted = replace(panel, transform=transform)
    transformed = np.array([transform.apply(tuple(p)) for p in points])
    assert np.allclose(transformed, destination + (q - midpoint) * scale)
    updated = replace(updated, scene=replace(updated.scene, expected_count=COUNT,
        objects=tuple(fitted if o.object_id == panel.object_id else o for o in updated.scene.objects)))
    old_template = updated.scene.object(TEMPLATE_ID)
    updated, removed = remove_leds(updated, old_template.object_id,
        [b.local_index for b in old_template.leds if b.source_index in RETIRED])
    assert {b.source_index for b in removed} == RETIRED
    updated = replace(updated, routes=updated.routes + (RouteBinding(panel.object_id, 'PANEL8_251', 2),))
    before = {b.source_index: (b, p) for b, p in original.scene.world_points()}
    after = {b.source_index: (b, p) for b, p in updated.scene.world_points()}
    assert set(before) - set(after) == RETIRED
    assert all(after[i] == value for i, value in before.items() if i not in RETIRED)
    assert set(after) - set(before) == {OFFSET + i for i in review['ids']}
    report = {'panel_id': panel.object_id, 'expected_leds': 549, 'measured_leds': int(len(ids)),
              'source_offset': OFFSET, 'source_count': COUNT,
              'retired_template_sources': [min(RETIRED), max(RETIRED)],
              'view_count': len(paths), 'transform': asdict(transform),
              'center': destination.tolist(),
              'bounds': [transformed.min(0).tolist(), transformed.max(0).tolist()],
              'orientation': 'Filled block (scan 356-548) lower left; full-width strip (0-240) along top',
              'block_scan_indices': {'strip_top': [0, BLOCK_STRIP],
                                     'steps_middle': [BLOCK_STRIP + 1, BLOCK_SQUARE - 1],
                                     'filled_square': [BLOCK_SQUARE, 548]},
              'similarity_only': True, 'planarity_ratio': planarity,
              'physical_size_cm': [30, 30],
              'size_reference': 'Same .16875 LED envelope as existing 30 cm panels',
              'slot': 'fourth row left: under Panel 5, left of Panel 8',
              'other_objects_unchanged': True, 'active_applied': False,
              'outputs': [{'controller': 'PANEL8_251', 'port': 2, 'universe': 158, 'count': 549,
                           'source_start': OFFSET, 'destination_start': 340}]}
    (OUT / 'draft-prepared.json').write_text(document_json(updated), encoding='utf-8')
    (OUT / 'draft-plan.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (OUT / 'panel7-world.csv').open('w', newline='') as stream:
        writer = csv.writer(stream); writer.writerow(['index', 'source_index', 'x', 'y', 'z'])
        writer.writerows((int(i), OFFSET + int(i), *p) for i, p in zip(ids, transformed))
    draw(updated, panel.object_id, ids, transformed)
    return report


def draw(document, panel_id, ids, points):
    import cv2
    image = np.full((950, 1650, 3), 24, np.uint8)
    def label(text, x, y, size=.65, color=(220, 220, 220)):
        cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, size, color, 1, cv2.LINE_AA)
    label('PANEL 7 | 549 / 549 measured LEDs', 40, 42, .85)
    label('Filled block lower left | strip along top', 40, 78)
    for i, p in zip(ids, points):
        xy = (int(60 + (.69 - p[2]) * 4000), int(120 + (.39 - p[0]) * 4000))
        color = ((215, 145, 70) if i <= BLOCK_STRIP else
                 (40, 200, 245) if i < BLOCK_SQUARE else (95, 210, 100))
        cv2.circle(image, xy, 3, color, -1, cv2.LINE_AA)
    label('REAR WALL | front view', 875, 42, .85)
    all_world = {b.source_index: p for b, p in document.scene.world_points()}
    for obj in document.scene.objects:
        if obj.name.startswith('Seite'):
            continue
        color = (80, 200, 255) if obj.object_id == panel_id else (150, 150, 150)
        for b in obj.leds:
            p = all_world[b.source_index]
            xy = (int(890 + (.7 - p[2]) * 1700), int(100 + (1. - p[0]) * 800))
            cv2.circle(image, xy, 1, color, -1)
    for name, x, z in [('Panel 1', .9, .6), ('Panel 2', .9, .4), ('Panel 3', .7, .6),
                       ('Panel 4', .7, .4), ('Panel 5', .5, .6), ('Panel 6', .5, .4),
                       ('Panel 7', .3, .6), ('Panel 8', .3, .4)]:
        label(name, int(870 + (.7 - z) * 1700), int(90 + (1 - x) * 800), .55)
    cv2.imwrite(str(OUT / 'panel7-placement.png'), image)


if __name__ == '__main__':
    print(json.dumps(prepare(), indent=2))
