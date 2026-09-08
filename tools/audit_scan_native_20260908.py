"""Bounded offline native reconstruction and candidate import verification."""
import csv
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pixelblaze_mapper.layout_scene import import_scan

out = Path(sys.argv[1]).resolve()
interpreter = r'C:\Users\jbhtz\AppData\Roaming\uv\tools\marimapper\Scripts\python.exe'
report = []
for number in (3, 9, 10, 12):
    manifest_path = out / f'manifest-{number}.json'
    manifest = json.loads(manifest_path.read_text())
    result_dir = Path(manifest['output_directory'])
    if not result_dir.exists():
        try:
            run = subprocess.run([interpreter, '-m', 'pixelblaze_mapper.scan_worker', str(manifest_path),
                '--confirm-offline-reconstruction'], capture_output=True, text=True, timeout=120)
            (out/f'native-{number}.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
            if run.returncode:
                report.append({'group':number,'error':f'worker exit {run.returncode}'})
                continue
        except subprocess.TimeoutExpired:
            report.append({'group':number,'error':'120 second timeout; worker terminated'})
            continue
    quality = json.loads((result_dir/'quality_pending.json').read_text())
    scan = import_scan(result_dir/'candidate_3d.csv',format='marimapper-csv',name='native audit')
    rows = list(csv.DictReader((result_dir/'candidate_3d.csv').read_text().splitlines()))
    for row in rows:
        assert scan.points[int(row['index'])] == tuple(float(row[k]) for k in ('x','y','z'))
    requested = {t['source_index'] for t in manifest['session']['targets']}
    obtained = set(quality['reconstructed_ids'])
    assert obtained <= requested
    assert not quality['camera_used'] and not quality['hardware_output_used'] and not quality['layout_applied']
    report.append({'group':number,'observed_ids':len(requested),'reconstructed':len(obtained),
        'not_reconstructed':sorted(requested-obtained),'candidate_coordinates_and_ids_exact':True,
        'camera':False,'hardware':False,'layout_applied':False})
    print(json.dumps(report[-1]),flush=True)
(out/'native-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
