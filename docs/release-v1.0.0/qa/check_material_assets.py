"""Offline/read-only dependency audit for every bundled catalog shader."""
import json
from collections import Counter
from pathlib import Path
from pixelblaze_mapper.material_paths import load_catalog_document
from pixelblaze_mapper.madmapper_td_adapter import adapt_material

root = Path(__file__).resolve().parents[3]
catalog = load_catalog_document(root/'material_library/catalogs/madmapper-official-d7ff211.json')
source_root = Path(catalog['source']['root'])
statuses = Counter()
missing = []
failures = []
texture_paths = set()
for item in catalog['materials']:
    source = Path(item['source_path'])
    try:
        adaptation = adapt_material(source,library_roots=(source_root,source_root.parent,source.parent,source.parent.parent))
        statuses[adaptation.status] += 1
        for texture in adaptation.textures:
            for value in texture.get('resolved_paths') or [texture.get('resolved_path')]:
                if not value or texture.get('TYPE','').lower() in ('audio','audiofft') and texture.get('source') != 'audio_file':
                    continue
                texture_paths.add(value)
                if not Path(value).is_file(): missing.append({'id':item['id'],'path':value})
    except Exception as error:
        failures.append({'id':item['id'],'error':str(error)})
report = {'catalog_records':len(catalog['materials']),'adapter_statuses':dict(statuses),'native_texture_files':len(texture_paths),'missing_files':missing,'exceptions':failures,'read_only':True}
(root/'docs/release-v1.0.0/qa/material-assets-offline.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
assert not missing and not failures
