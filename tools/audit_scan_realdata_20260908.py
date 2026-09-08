"""Read-only source audit; generated evidence lives only in --output."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pixelblaze_mapper.layout_scene import (Scene, SceneHistory, import_scan,
    append_scan, replace_region, export_scene_json, import_scene_json,
    export_pixelblaze_3d)
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget
from pixelblaze_mapper.build_scan_session_ui import attach_existing_views
from pixelblaze_mapper.scan_worker import create_manifest, load_observations


def audit(root, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {'source': str(root), 'files': [], 'groups': [], 'checks': 0}
    groups = defaultdict(list)
    hashes = {}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in ('.csv', '.json', '.txt'):
            continue
        data = path.read_bytes()
        hashes[path] = hashlib.sha256(data).hexdigest()
        item = {'path': str(path.relative_to(root)), 'sha256': hashes[path]}
        report['files'].append(item)
        try:
            text = data.decode('utf-8-sig')
            rows = list(csv.DictReader(text.splitlines())) if path.suffix.lower() == '.csv' else None
            if rows is not None and rows and {'index','u','v'} <= set(rows[0]):
                ids = [int(r['index']) for r in rows]
                item.update(kind='2d', rows=len(rows), first=min(ids), last=max(ids), duplicates=len(ids)-len(set(ids)))
                groups[path.parent].append(path)
                continue
            fmt = 'marimapper-csv' if rows is not None else 'pixelblaze'
            scan = import_scan(path, format=fmt, name=path.name)
            present = tuple(i for i in range(len(scan.points)) if i not in scan.missing_indices)
            item.update(kind='3d/import', slots=len(scan.points), present=len(present), missing=len(scan.missing_indices), warnings=scan.warnings)
            if rows is not None:
                expected = {int(r['index']): tuple(float(r[k]) for k in ('x','y','z')) for r in rows}
                for i, xyz in expected.items():
                    assert scan.points[i] == xyz, ('coordinate or ID changed', i)
                assert set(present) == set(expected), 'missing/index identity mismatch'
                report['checks'] += len(expected) + 1
            # Explicit global assignment: never silently reindex sparse source IDs.
            scene = append_scan(Scene('audit', 'audit'), scan, source_indices=present, scan_indices=present)
            assert import_scene_json(export_scene_json(scene)) == scene
            report['checks'] += 1
            # A distinct import of the same real measurements tests partial replacement.
            other = replace(scan, scan_id=scan.scan_id + '-rescan')
            chosen = tuple(range(min(7, len(present))))
            replaced = replace_region(scene, scene.objects[0].object_id, chosen, other,
                                      scan_indices=tuple(present[i] for i in chosen))
            assert [(b.led_id,b.source_index,p) for b,p in replaced.world_points()] == [(b.led_id,b.source_index,p) for b,p in scene.world_points()]
            history = SceneHistory(scene)
            history.commit(replaced)
            assert history.undo() == scene and history.redo() == replaced
            report['checks'] += 2
            if present == tuple(range(len(present))):
                assert json.loads(export_pixelblaze_3d(scene)) == [list(scan.points[i]) for i in present]
                item['pixelblaze_export'] = 'exact'
            else:
                try:
                    export_pixelblaze_3d(scene)
                except ValueError:
                    item['pixelblaze_export'] = 'sparse IDs correctly blocked'
                else:
                    raise AssertionError('sparse export silently renumbered')
            report['checks'] += 1
            item['result'] = 'pass'
        except Exception as error:
            item.update(result='rejected/error', error=type(error).__name__ + ': ' + str(error))
    for folder, paths in sorted(groups.items()):
        item = {'folder': str(folder.relative_to(root)), 'views': len(paths)}
        report['groups'].append(item)
        if len(paths) < 2:
            item['result'] = 'insufficient views'
            continue
        try:
            ids = sorted({int(r['index']) for p in paths for r in csv.DictReader(p.read_text(encoding='utf-8-sig').splitlines())})
            state = ScanSession('audit-'+str(len(report['groups'])), 'audit', 'unchanged',
                tuple(ScanTarget('led-'+str(i), 'object', j, i) for j,i in enumerate(ids)),
                tuple('led-'+str(i) for i in ids), ())
            state, views = attach_existing_views(state, paths)
            manifest = create_manifest(state, views=views, source_roots=[root], workspace_root=output,
                output_directory=output/('native-'+str(len(report['groups']))), camera_model='camera_model_opencv')
            checked, observations = load_observations(manifest)
            expected = tuple((int(r['index']),v,float(r['u']),float(r['v'])) for v,p in enumerate(paths)
                             for r in csv.DictReader(p.read_text(encoding='utf-8-sig').splitlines()))
            assert observations == expected
            report['checks'] += len(expected)
            item.update(result='pass', unique_ids=len(ids), observations=len(observations), first=min(ids), last=max(ids))
            manifest_path = output/('manifest-'+str(len(report['groups']))+'.json')
            manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
            item['manifest'] = str(manifest_path)
        except Exception as error:
            item.update(result='rejected/error', error=type(error).__name__+': '+str(error))
    report['sources_unchanged'] = all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p,h in hashes.items())
    assert report['sources_unchanged']
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    audit(args.source,args.output)
