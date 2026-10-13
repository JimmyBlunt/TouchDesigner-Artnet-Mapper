"""Resumable sequential material import/adaptation/isolated-GPU acceptance.

Examples (from the repository root)::

    python tools/audit_material_library.py --offline-only --ids mat_...
    python tools/audit_material_library.py --resume
    python tools/audit_material_library.py --resume --retry review,compile_error

Never selects a library material, connects an output or writes a live player.
Quarantines cannot be overridden by retry. Interrupted GPU probes require an
explicit retry; the next material is never submitted after a transport failure.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelblaze_mapper import madmapper_td_adapter as adapter
from pixelblaze_mapper.material_library import import_material, load_catalog, MaterialImportError
from pixelblaze_mapper.madmapper_parameters import uniform_vector

DEFAULT_CATALOG = ROOT/'material_library/catalogs/madmapper-official-d7ff211.json'
DEFAULT_OUTPUT = ROOT/'docs/material-audit-20261013'
TIMES = (0., 1., 2.)
RESOLUTION = (96, 64)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temporary.replace(path)


def quarantine_reason(item):
    validation = item.metadata.get('_TD_VALIDATION', {})
    if isinstance(validation, dict) and str(validation.get('status', '')).casefold() == 'quarantined':
        return 'Catalog _TD_VALIDATION.status is quarantined: '+str(validation.get('reason', validation.get('reasons', 'GPU validation prohibited')))
    names = (item.name, Path(item.source_path).stem)
    if any(re.sub(r'[^a-z0-9]', '', name.casefold()) == 'twistedtunnel' for name in names):
        return 'Twisted Tunnel previously crashed TouchDesigner during a GPU probe; offline adaptation only.'
    return None


def classify_probe(probe, epsilon=1e-7):
    """Image anomalies are review evidence, never invented shader failures."""
    if probe.get('errors') or re.search(r'\berror\s*:', str(probe.get('info', '')), re.I):
        return 'compile_error', ['GPU compiler/TOP reported an error.']
    if probe.get('exception'):
        return 'probe_error', [str(probe['exception'])]
    samples = probe.get('samples', [])
    if len(samples) != len(TIMES):
        return 'probe_error', ['Expected three image samples at t=0,1,2.']
    reasons = []
    for sample in samples:
        prefix = 't=%s: ' % sample.get('time')
        if not sample.get('finite', False):
            reasons.append(prefix+'nonfinite pixel values; inspect the shader/default parameters.')
        rgb_min, rgb_max = sample.get('rgb_min'), sample.get('rgb_max')
        if rgb_min is not None and rgb_max is not None and max(abs(rgb_min), abs(rgb_max)) <= epsilon:
            reasons.append(prefix+'black/blank RGB; a valid default or static material may be intentional.')
        if sample.get('alpha_max') is not None and sample['alpha_max'] <= epsilon:
            reasons.append(prefix+'fully transparent output.')
        if sample.get('spatial_variance') is not None and sample['spatial_variance'] <= epsilon:
            reasons.append(prefix+'spatially uniform output; inspect rather than automatically fail.')
    return ('review' if reasons else 'passed'), reasons


def should_run(previous, fingerprint, resume=False, retry=()):
    if not resume or previous is None:
        return True
    if previous.get('status') in set(retry):
        return True
    # Never silently resubmit a shader that may have crashed the GPU, even if
    # files changed after the interruption. An operator must explicitly retry.
    if previous.get('status') == 'in_progress' or previous.get('interrupted_gpu'):
        return False
    return previous.get('fingerprint') != fingerprint


def import_one(catalog, item, import_root):
    target = Path(import_root)/item.id/Path(item.relative_path).name
    try:
        imported = import_material(catalog, item.id, import_root)
        return dict(status='imported' if imported.created else 'existing', path=str(imported.source_path),
                    manifest=str(imported.manifest_path), created=imported.created)
    except MaterialImportError as error:
        # The importer refuses overwrites; do not remove/rename or repair the
        # destination to force success. Intentional local changes stay intact.
        return dict(status='conflict' if target.parent.exists() else 'error', path=str(target), error=str(error))
    except OSError as error:
        return dict(status='error', path=str(target), error=str(error))


class Journal:
    def __init__(self, path, provenance, resume=False):
        self.path = Path(path)
        self.data = dict(schema_version=1, provenance=provenance, updated_at=utc_now(), counts={}, results=[])
        if resume and self.path.exists():
            existing = json.loads(self.path.read_text(encoding='utf-8'))
            if existing.get('schema_version') != 1 or not isinstance(existing.get('results'), list):
                raise ValueError('Unsupported audit journal schema.')
            # Keep records outside a requested subset and retain provenance of
            # prior runs; individual source/adaptation fingerprints gate reuse.
            self.data['results'] = existing['results']
            self.data['previous_runs'] = existing.get('previous_runs', [])+[existing.get('provenance', {})]
        self.records = {record['id']: record for record in self.data['results']}

    def put(self, record):
        self.records[record['id']] = record
        self.flush()

    def flush(self):
        self.data.update(updated_at=utc_now(), results=list(self.records.values()),
                         counts=dict(Counter(r['status'] for r in self.records.values())))
        atomic_json(self.path, self.data)


def td(script, endpoint='http://127.0.0.1:9981/api/td/server/exec', timeout=45):
    request = urllib.request.Request(endpoint, json.dumps(dict(script=script)).encode('utf-8'),
                                     {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    if not data.get('success'):
        raise RuntimeError('TouchDesigner execution failed: '+str(data))
    result = data['data']['result']
    return json.loads(result) if isinstance(result, str) else result


PROBE_SCRIPT = r'''
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
settings=json.loads(__SETTINGS__)
parent=op('/project1')
if parent is None: raise RuntimeError('Expected /project1')
owner=op(settings['probe_path'])
if owner is None:
 owner=parent.create(baseCOMP,settings['probe_name'])
 owner.store('material_audit_owner',settings['token'])
elif owner.fetch('material_audit_owner',None)!=settings['token']:
 raise RuntimeError('Probe ownership mismatch; refusing to use existing nodes')
result_data={'errors':[],'info':'','samples':[],'temporal_mean_abs_delta':[]}
try:
 source=owner.op('shader')
 if source is None: source=owner.create(textDAT,'shader')
 preview=owner.op('preview')
 if preview is None: preview=owner.create(glslmultiTOP,'preview')
 info=owner.op('info')
 if info is None: info=owner.create(infoDAT,'info')
 preview.viewer=False
 preview.par.pixeldat=source.path
 preview.par.outputresolution='custom'
 preview.par.resolutionw=96; preview.par.resolutionh=64
 preview.par.format='rgba32float'
 info.par.op=preview.path
 binding=json.loads(Path(settings['binding_path']).read_text(encoding='utf-8'))
 from pixelblaze_mapper.material_texture_runtime import bind_textures
 bind_textures(preview,SimpleNamespace(textures=binding['textures']))
 result_data['texture_count']=len(binding['textures'])
 uniforms={'uTDMaterial0':[0.,4.,.5,1.],'uTDMaterial1':[.5,.5,0.,0.],
           'uTDCoordinate':[0.,2.,5.,.5],**binding['values']}
 preview.par.vec.sequence.numBlocks=len(uniforms)
 for i,(name,values) in enumerate(uniforms.items()):
  preview.par['vec%dname'%i]=name
  for suffix,value in zip('xyzw',values): preview.par['vec%dvalue%s'%(i,suffix)]=value
 source.text=Path(settings['shader_path']).read_text(encoding='utf-8')
 frames=[]
 def finite_stat(values,operation):
  good=values[np.isfinite(values)]
  return float(operation(good.astype(np.float64))) if good.size else None
 for phase in settings['times']:
  preview.par.vec0valuex=phase
  from pixelblaze_mapper.material_audio_runtime import set_audio_probe_time
  set_audio_probe_time(owner,phase)
  preview.cook(force=True)
  errors=list(preview.errors())
  info_text=info.text
  if errors or 'error:' in info_text.lower():
   result_data.update(errors=errors,info=info_text)
   break
  pixels=preview.numpyArray(delayed=False)
  if pixels is None: raise RuntimeError('GPU image readback returned None')
  pixels=np.array(pixels,dtype=np.float32,copy=True)
  if pixels.shape != (64,96,4): raise RuntimeError('Unexpected image shape: '+str(pixels.shape))
  rgb,alpha=pixels[:,:,:3],pixels[:,:,3]
  finite=bool(np.isfinite(pixels).all())
  spatial=float(np.max(np.var(rgb.astype(np.float64),axis=(0,1)))) if np.isfinite(rgb).all() else None
  sample={'time':phase,'shape':list(pixels.shape),'finite':finite,
          'nonfinite_count':int(pixels.size-np.count_nonzero(np.isfinite(pixels))),
          'rgb_min':finite_stat(rgb,np.min),'rgb_max':finite_stat(rgb,np.max),
          'rgb_mean':finite_stat(rgb,np.mean),'rgb_variance':finite_stat(rgb,np.var),
          'spatial_variance':spatial,'alpha_min':finite_stat(alpha,np.min),
          'alpha_max':finite_stat(alpha,np.max),'alpha_mean':finite_stat(alpha,np.mean)}
  if frames:
   difference=np.abs(rgb.astype(np.float64)-frames[-1][:,:,:3].astype(np.float64))
   result_data['temporal_mean_abs_delta'].append(finite_stat(difference,np.mean))
  frames.append(pixels)
  result_data['samples'].append(sample)
  result_data['info']=info_text
 if len(frames)==3:
  from pixelblaze_mapper.maschine_mk2 import dependencies
  dependencies()
  from PIL import Image
  # Clamp only the evidence image. Statistics above retain raw float HDR/NaN.
  tiles=[np.uint8(np.clip(np.nan_to_num(f[:,:,:3],nan=0.,posinf=1.,neginf=0.),0,1)*255) for f in frames]
  strip=np.concatenate([np.flipud(tile) for tile in tiles],axis=1)
  Image.fromarray(strip,'RGB').save(settings['thumbnail'])
  result_data['thumbnail']=settings['thumbnail']
 result_data['pixel_format']=str(preview.par.format.eval())
except Exception as error:
 result_data['exception']=type(error).__name__+': '+str(error)
result=json.dumps(result_data,allow_nan=False)
'''


class GPUProbe:
    def __init__(self, output, execute=td):
        self.output = Path(output)
        self.execute = execute
        self.token = uuid.uuid4().hex
        self.name = 'material_audit_'+self.token[:12]
        self.path = '/project1/'+self.name
        self.used = False

    def run(self, item, adaptation):
        work = self.output/'probe-work'
        thumbnails = self.output/'thumbnails'
        work.mkdir(parents=True, exist_ok=True)
        thumbnails.mkdir(parents=True, exist_ok=True)
        shader = work/'probe.frag'
        binding = work/'bindings.json'
        shader.write_text(adaptation.shader, encoding='utf-8')
        atomic_json(binding, dict(textures=adaptation.textures, values={p.uniform: uniform_vector(p, p.default)
                    for p in adaptation.schema if not p.compile_time}))
        settings = dict(probe_name=self.name, probe_path=self.path, token=self.token, times=TIMES,
                        shader_path=str(shader.resolve()), binding_path=str(binding.resolve()),
                        thumbnail=str((thumbnails/(item.id+'.png')).resolve()))
        self.used = True
        return self.execute(PROBE_SCRIPT.replace('__SETTINGS__', repr(json.dumps(settings))))

    def close(self):
        if not self.used:
            return
        # Do not remove an arbitrary similarly named node or a different run.
        script = "owner=op(%r)\nif owner is not None and owner.fetch('material_audit_owner',None)==%r:\n owner.destroy()\nresult='{}'" % (self.path, self.token)
        self.execute(script)


def runtime_fingerprints():
    from pixelblaze_mapper import material_texture_runtime, madmapper_parameters, material_audio_runtime, material_shader_repairs, material_generator_glsl
    return dict(probe_script_sha256=hashlib.sha256(PROBE_SCRIPT.encode('utf-8')).hexdigest(),
                audit_harness_sha256=sha256_file(__file__),
                texture_runtime_sha256=sha256_file(material_texture_runtime.__file__),
                audio_runtime_sha256=sha256_file(material_audio_runtime.__file__),
                shader_repairs_sha256=sha256_file(material_shader_repairs.__file__),
                generator_sha256=sha256_file(material_generator_glsl.__file__),
                parameter_runtime_sha256=sha256_file(madmapper_parameters.__file__))


def prepare(catalog, item, import_root, adapter_hash, runtime_hashes=None):
    record = dict(id=item.id, name=item.name, source_path=item.source_path, preview_path=item.preview_path,
                  started_at=utc_now(), thumbnail=None, reasons=[], source_sha256=None)
    record['import'] = import_one(catalog, item, import_root)
    quarantine = quarantine_reason(item)
    try:
        source = Path(item.source_path)
        root = Path(catalog.source_root)
        record['source_sha256'] = sha256_file(source)
        adaptation = adapter.adapt_material(source, library_roots=(root, root.parent, source.parent, source.parent.parent))
        textures = []
        for texture in adaptation.textures:
            entry = dict(texture)
            entry['sha256'] = sha256_file(entry['resolved_path'])
            # Cube dependencies are ordered +X/-X/+Y/-Y/+Z/-Z. A changed
            # non-first face must invalidate a successful prior GPU result.
            entry['files'] = [dict(path=str(path), sha256=sha256_file(path))
                              for path in (entry.get('resolved_paths') or [entry['resolved_path']])]
            textures.append(entry)
        shader_hash = hashlib.sha256((adaptation.shader or '').encode('utf-8')).hexdigest()
        record['adaptation'] = dict(status=adaptation.status, reasons=list(adaptation.reasons), warnings=list(adaptation.warnings),
                                    shader_sha256=shader_hash, texture_count=len(textures), textures=textures,
                                    parameter_count=len(adaptation.schema), adapter_version=adapter.ADAPTER_VERSION)
        if quarantine:
            record.update(status='quarantined', reasons=[quarantine])
        elif record['import']['status'] == 'conflict':
            record.update(status='import_conflict', reasons=[record['import']['error']])
        elif record['import']['status'] == 'error':
            record.update(status='import_error', reasons=[record['import']['error']])
        elif not adaptation.adaptable:
            record.update(status='unsupported', reasons=list(adaptation.reasons))
        else:
            record['status'] = 'offline_adapted'
    except Exception as error:
        adaptation = None
        record.update(status='quarantined' if quarantine else 'adaptation_error',
                      reasons=([quarantine] if quarantine else [])+[type(error).__name__+': '+str(error)])
    fingerprint_data = dict(source=record['source_sha256'], adaptation=record.get('adaptation'),
                            adapter_hash=adapter_hash, runtime_hashes=runtime_hashes or runtime_fingerprints(), quarantine=quarantine,
                            import_status='ok' if record['import']['status'] in ('existing','imported') else record['import']['status'])
    record['fingerprint'] = hashlib.sha256(json.dumps(fingerprint_data, sort_keys=True).encode('utf-8')).hexdigest()
    return record, adaptation


def run_audit(catalog_path=DEFAULT_CATALOG, output=DEFAULT_OUTPUT, import_root=None, ids=(), resume=False,
              retry=(), offline_only=False, execute=td, limit=None):
    catalog_path, output = Path(catalog_path).resolve(), Path(output).resolve()
    catalog = load_catalog(catalog_path)
    import_root = Path(import_root or ROOT/'material_library/imported').resolve()
    selected = set(ids)
    unknown = selected-{item.id for item in catalog.materials}-{item.name for item in catalog.materials}
    if unknown:
        raise ValueError('Unknown material IDs/names: '+', '.join(sorted(unknown)))
    materials = [item for item in catalog.materials if not selected or item.id in selected or item.name in selected]
    if limit is not None:
        materials = materials[:limit]
    probe = GPUProbe(output, execute)
    adapter_hash = sha256_file(adapter.__file__)
    runtime_hashes = runtime_fingerprints()
    provenance = dict(started_at=utc_now(), catalog_path=str(catalog_path), catalog_sha256=sha256_file(catalog_path),
                      adapter_sha256=adapter_hash, **runtime_hashes, source_root=catalog.source_root, import_root=str(import_root),
                      catalog_count=len(catalog.materials), selected_count=len(materials), resolution=list(RESOLUTION),
                      times=list(TIMES), offline_only=offline_only, probe_path=probe.path,
                      command=sys.argv, quarantine_policy='metadata plus previous Twisted Tunnel GPU crash; never override')
    journal = Journal(output/'results.json', provenance, resume=resume)
    transport_failed = False
    try:
        for index, item in enumerate(materials):
            if not re.fullmatch(r'mat_[0-9a-f]{20}', item.id):
                raise ValueError('Unsafe material ID: '+item.id)
            record, adaptation = prepare(catalog, item, import_root, adapter_hash, runtime_hashes)
            previous = journal.records.get(item.id)
            do_run = should_run(previous, record['fingerprint'], resume, retry)
            # A newly asserted quarantine must supersede an old successful GPU
            # result; an old offline-only result may advance to GPU on resume.
            do_run |= bool(previous and record['status'] == 'quarantined' and previous.get('status') != 'quarantined')
            do_run |= bool(previous and previous.get('status') == 'offline_adapted' and not offline_only)
            if not do_run:
                continue
            if record['status'] == 'offline_adapted' and not offline_only:
                record.update(status='in_progress', phase='gpu', gpu_started_at=utc_now(), probe_path=probe.path)
                journal.put(record)  # Durable marker BEFORE any GPU/REST call.
                try:
                    result = probe.run(item, adaptation)
                    record['probe'] = result
                    record['status'], record['reasons'] = classify_probe(result)
                    record['thumbnail'] = result.get('thumbnail')
                    deltas = result.get('temporal_mean_abs_delta', [])
                    record['no_temporal_change'] = bool(deltas) and all(v is not None and v <= 1e-7 for v in deltas)
                except Exception as error:
                    transport_failed = True
                    record.update(status='probe_error', reasons=[type(error).__name__+': '+str(error)],
                                  interrupted_gpu=True)
            record['completed_at'] = utc_now()
            journal.put(record)
            print('%d/%d %s %s' % (index+1, len(materials), record['status'], item.name), flush=True)
            if transport_failed:
                break
    finally:
        try:
            probe.close()
        except Exception as error:
            journal.data['cleanup_error'] = type(error).__name__+': '+str(error)
        journal.data['transport_failed'] = transport_failed
        journal.flush()
    return journal.data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--import-root', type=Path, default=ROOT/'material_library/imported')
    parser.add_argument('--ids', nargs='+', default=[], help='IDs or exact material names; comma-separated IDs also accepted')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--retry', default='', help='Comma-separated result statuses; requires --resume')
    parser.add_argument('--offline-only', action='store_true')
    parser.add_argument('--limit', type=int, help='Optional bounded smoke-run subset')
    args = parser.parse_args(argv)
    if args.retry and not args.resume:
        parser.error('--retry requires --resume')
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    ids = [value for group in args.ids for value in group.split(',') if value]
    data = run_audit(args.catalog, args.output, args.import_root, ids, args.resume,
                     [value for value in args.retry.split(',') if value], args.offline_only, limit=args.limit)
    print(json.dumps(dict(counts=data['counts'], results=str(args.output/'results.json')), indent=2))
    return 2 if data.get('transport_failed') else 1 if data['counts'].get('compile_error', 0) else 0


if __name__ == '__main__':
    raise SystemExit(main())
