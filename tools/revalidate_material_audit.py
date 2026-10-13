"""Carry forward unchanged GPU evidence after only the shader-repair registry changes.

Read-only plan by default; --apply explicitly backs up and updates results.json.
No import, GPU or TouchDesigner calls are made. Changed shaders/dependencies keep
their old fingerprints so the normal audit --resume evaluates them again.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import publish_material_audit as publish

audit, adapter = publish.audit, publish.adapter
REPAIRS_KEY = 'shader_repairs_sha256'


@dataclass(frozen=True)
class RevalidationPlan:
    results_path: Path
    data: dict
    expected_files: dict
    runtime_hashes: dict
    adapter_hash: str
    summary: dict


def _runtime(provenance, current):
    return {key: provenance.get(key) for key in current}


def _compatible(provenance, current, adapter_hash):
    return (provenance.get('adapter_sha256') == adapter_hash
            and provenance.get('times') == list(audit.TIMES)
            and provenance.get('resolution') == list(audit.RESOLUTION)
            and isinstance(provenance.get(REPAIRS_KEY), str)
            and all(provenance.get(key) == value for key, value in current.items() if key != REPAIRS_KEY))


def _fingerprint(source_hash, adaptation, runtime, adapter_hash, quarantine):
    values = dict(source=source_hash, adaptation=adaptation, adapter_hash=adapter_hash,
                  runtime_hashes=runtime, quarantine=quarantine, import_status='ok')
    return publish._hash_bytes(json.dumps(values, sort_keys=True).encode('utf-8'))


def build_plan(results_path=publish.DEFAULT_RESULTS, catalog_path=audit.DEFAULT_CATALOG, import_root=None):
    results_path, catalog_path = Path(results_path).resolve(), Path(catalog_path).resolve()
    expected = {}
    publish._watch(results_path, expected)
    publish._watch(catalog_path, expected)
    data, catalog = publish._json(results_path), publish.load_catalog(catalog_path)
    publish._require(data.get('schema_version') == 1, 'Unsupported audit schema.')
    publish._require(data.get('transport_failed') is False, 'No carry-forward after transport failure or incomplete run.')
    publish._require(len(catalog.materials) == publish.EXPECTED_COUNT, 'Expected complete catalog coverage.')
    rows = data.get('results', [])
    ids = [row.get('id') for row in rows]
    publish._require(len(ids) == len(set(ids)) == len(catalog.materials)
                     and set(ids) == {m.id for m in catalog.materials}, 'Expected exact audit/catalog coverage.')
    runtime, adapter_hash = audit.runtime_fingerprints(), audit.sha256_file(adapter.__file__)
    provenance = data.get('provenance', {})
    publish._require(_compatible(provenance, runtime, adapter_hash),
                     'Only shader_repairs_sha256 may change; adapter, probe, harness, other runtimes, times and resolution must match.')
    candidates = [provenance] + data.get('previous_runs', [])
    # Explicit per-record carry-forward provenance also authenticates a journal
    # whose header is intentionally still old while one changed shader awaits GPU.
    for row in rows:
        for previous in row.get('carry_forward', []):
            candidates.append(previous.get('new_provenance', {}))
    candidates = [p for p in candidates if _compatible(p, runtime, adapter_hash)]
    import_root = Path(import_root or provenance.get('import_root') or ROOT/'material_library/imported').resolve()
    new_data = copy.deepcopy(data)
    by_id = {row['id']:row for row in new_data['results']}
    carried, unchanged, rerun = [], [], []
    now = audit.utc_now()
    for item in catalog.materials:
        record = by_id[item.id]
        try:
            publish._require(record.get('status') in publish.TERMINAL and record.get('completed_at')
                             and not record.get('interrupted_gpu'), 'incomplete/interrupted evidence')
            publish._require(record.get('import', {}).get('status') in ('existing', 'imported'), 'import did not succeed')
            publish._require(Path(record.get('source_path', '')).resolve() == Path(item.source_path).resolve(), 'source path changed')
            source_hash = publish._watch(item.source_path, expected)
            publish._require(source_hash and source_hash == record.get('source_sha256'), 'source hash changed')
            adaptation, fresh = publish._fresh_adaptation(catalog, item, expected)
            publish._require(fresh == record.get('adaptation'), 'shader/adaptation/texture evidence changed')
            quarantine = audit.quarantine_reason(item)
            # Includes current classify_probe for GPU records, exact sample times,
            # dimensions and finite-count consistency. Reviews remain reviews.
            publish._classify(record, adaptation, quarantine)
            target = publish._managed_shader_target(item, record, import_root, source_hash, expected)
            publish._require(target is not None, 'missing managed import manifest')
            new_fingerprint = _fingerprint(source_hash, fresh, runtime, adapter_hash, quarantine)
            if record.get('fingerprint') == new_fingerprint:
                unchanged.append(item.id)
                continue
            old_provenance = next((p for p in candidates if
                _fingerprint(source_hash, fresh, _runtime(p, runtime), adapter_hash, quarantine) == record.get('fingerprint')), None)
            publish._require(old_provenance is not None, 'old fingerprint cannot be authenticated against matching runtime provenance')
            old_runtime = _runtime(old_provenance, runtime)
            publish._require(old_runtime[REPAIRS_KEY] != runtime[REPAIRS_KEY], 'fingerprint difference is not a repair-registry change')
            new_provenance = dict(adapter_sha256=adapter_hash, times=list(audit.TIMES), resolution=list(audit.RESOLUTION), **runtime)
            entry = dict(at=now, reason='Only repair registry changed; source, full adaptation and GPU environment identical.',
                         old_fingerprint=record['fingerprint'], new_fingerprint=new_fingerprint,
                         old_shader_repairs_sha256=old_runtime[REPAIRS_KEY], new_shader_repairs_sha256=runtime[REPAIRS_KEY],
                         old_runtime_fingerprints=old_runtime, new_provenance=new_provenance,
                         preserved_gpu_completed_at=record['completed_at'], gpu_rerun=False)
            record.setdefault('carry_forward', []).append(entry)
            record['fingerprint'] = new_fingerprint
            carried.append(item.id)
        except (OSError, ValueError, KeyError, TypeError) as error:
            # Leave the whole original record intact, particularly fingerprint,
            # so audit --resume does not mistake changed work for verified work.
            by_id[item.id] = copy.deepcopy(next(r for r in rows if r['id'] == item.id))
            rerun.append(dict(id=item.id, name=item.name, reason=str(error)))
    new_data['results'] = [by_id[row['id']] for row in rows]
    all_fresh = not rerun
    if all_fresh:
        new_data.setdefault('previous_runs', []).append(copy.deepcopy(provenance))
        new_data['provenance'].update(runtime)
        new_data['provenance']['adapter_sha256'] = adapter_hash
    new_data['updated_at'] = now
    new_data['counts'] = dict(Counter(row['status'] for row in new_data['results']))
    new_data.setdefault('revalidations', []).append(dict(at=now, carried=len(carried), already_current=len(unchanged),
                                                        requires_reaudit=rerun, all_fingerprints_current=all_fresh,
                                                        gpu_calls=0, runtime_fingerprints=runtime))
    summary = dict(mode='plan', carried=len(carried), already_current=len(unchanged), requires_reaudit=rerun,
                   all_fingerprints_current=all_fresh, results=str(results_path), gpu_calls=0)
    return RevalidationPlan(results_path, new_data, expected, runtime, adapter_hash, summary)


def apply_plan(plan):
    publish._require(audit.runtime_fingerprints() == plan.runtime_hashes and audit.sha256_file(adapter.__file__) == plan.adapter_hash,
                     'Runtime changed after revalidation planning.')
    for path, digest in plan.expected_files.items():
        actual = audit.sha256_file(path) if path.is_file() else None
        publish._require(actual == digest, 'File changed after revalidation planning: ' + str(path))
    publish._require(plan.results_path.resolve() == plan.results_path, 'Results path redirected after planning.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = plan.results_path.parent/'revalidation-backups'/('results-'+stamp+'.json')
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as stream:
        stream.write(plan.results_path.read_bytes())
    publish._atomic_write(plan.results_path, publish._json_bytes(plan.data))
    return dict(plan.summary, mode='applied', original_results_backup=str(backup))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=publish.DEFAULT_RESULTS)
    parser.add_argument('--catalog', type=Path, default=audit.DEFAULT_CATALOG)
    parser.add_argument('--import-root', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.results, args.catalog, args.import_root)
        print(json.dumps(apply_plan(plan) if args.apply else plan.summary, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Revalidation refused: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
