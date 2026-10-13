"""Publish a complete, current material GPU audit to managed local packages.

Default is a read-only plan. --apply is required to write prepared shaders and
catalog validation; this tool never connects to TouchDesigner or deploys live.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import audit_material_library as audit
from pixelblaze_mapper import madmapper_td_adapter as adapter
from pixelblaze_mapper.material_library import Compatibility, load_catalog

EXPECTED_COUNT = 638
DEFAULT_RESULTS = ROOT / 'docs/material-audit-20261013/results.json'
TERMINAL = frozenset({'passed', 'review', 'compile_error', 'unsupported', 'quarantined'})
MARKER = re.compile(r'^// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION [0-9]+\s*$', re.M)


class PublicationError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise PublicationError(message)


def _hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda value: (_ for _ in ()).throw(PublicationError('Non-finite JSON constant: ' + value)))


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _within(path, root):
    resolved = Path(path).resolve()
    _require(resolved.is_relative_to(Path(root).resolve()), 'Path escapes managed import root: ' + str(path))
    return resolved


@dataclass(frozen=True)
class PublicationPlan:
    catalog_path: Path
    results_path: Path
    writes: tuple[tuple[Path, bytes], ...]
    expected_files: dict[Path, str | None]
    runtime_hashes: dict
    adapter_hash: str
    summary: dict


def _watch(path, expected):
    path = Path(path).resolve()
    value = audit.sha256_file(path) if path.is_file() else None
    if path in expected:
        _require(expected[path] == value, 'File changed during planning: ' + str(path))
    expected[path] = value
    return value


def _fresh_adaptation(catalog, item, expected):
    source = Path(item.source_path).resolve()
    root = Path(catalog.source_root)
    adaptation = adapter.adapt_material(source, library_roots=(root, root.parent, source.parent, source.parent.parent))
    textures = []
    for binding in adaptation.textures:
        entry = dict(binding)
        entry['sha256'] = _watch(entry['resolved_path'], expected)
        entry['files'] = [dict(path=str(p), sha256=_watch(p, expected))
                          for p in (entry.get('resolved_paths') or [entry['resolved_path']])]
        _require(all(f['sha256'] for f in entry['files']), 'Missing texture dependency: ' + item.name)
        textures.append(entry)
    evidence = dict(status=adaptation.status, reasons=list(adaptation.reasons), warnings=list(adaptation.warnings),
                    shader_sha256=_hash_bytes((adaptation.shader or '').encode('utf-8')),
                    texture_count=len(textures), textures=textures, parameter_count=len(adaptation.schema),
                    adapter_version=adapter.ADAPTER_VERSION)
    return adaptation, evidence


def _classify(record, adaptation, quarantine):
    status = record['status']
    if quarantine:
        _require(status == 'quarantined', 'Quarantine must be recorded, not overridden: ' + record['id'])
        return False, 'quarantined', [quarantine]
    if status == 'quarantined':
        return False, status, list(record.get('reasons', []))
    if status == 'unsupported':
        _require(not adaptation.adaptable, 'Unsupported record disagrees with fresh adapter: ' + record['id'])
        return False, status, list(record.get('reasons', []))
    probe = record.get('probe')
    _require(isinstance(probe, dict), 'Missing GPU evidence: ' + record['id'])
    actual, reasons = audit.classify_probe(probe)
    _require(actual == status, 'GPU classification mismatch: ' + record['id'])
    _require(actual != 'probe_error', 'Incomplete GPU evidence: ' + record['id'])
    if status == 'compile_error':
        return False, status, reasons
    _require(adaptation.adaptable, 'GPU success conflicts with fresh unsupported adaptation: ' + record['id'])
    samples = probe.get('samples', [])
    _require([s.get('time') for s in samples] == list(audit.TIMES), 'Wrong GPU sample times: ' + record['id'])
    _require(all(s.get('shape') == [audit.RESOLUTION[1], audit.RESOLUTION[0], 4] for s in samples),
             'Wrong GPU sample dimensions: ' + record['id'])
    for s in samples:
        _require(type(s.get('finite')) is bool and isinstance(s.get('nonfinite_count'), int),
                 'Missing finite-pixel evidence: ' + record['id'])
        _require(s['nonfinite_count'] >= 0 and (s['finite'] == (s['nonfinite_count'] == 0)),
                 'Contradictory finite-pixel evidence: ' + record['id'])
    finite = all(s['finite'] for s in samples)
    return finite, status if finite else 'nonfinite', reasons


def _managed_shader_target(item, record, import_root, source_hash, expected):
    package = _within(import_root / item.id, import_root)
    manifest = package / 'material-import.json'
    if not manifest.is_file():
        # A missing package is never created as a side effect of publishing.
        _watch(manifest, expected)
        return None
    _watch(manifest, expected)
    data = _json(manifest)
    _require(data.get('material_id') == item.id and data.get('source_sha256') == source_hash,
             'Imported manifest does not match source: ' + item.id)
    files = data.get('imported_files')
    _require(isinstance(files, dict) and files, 'Imported manifest lacks file hashes: ' + item.id)
    _require(data.get('imported_file') in files and files[data['imported_file']] == source_hash,
             'Imported main shader hash is not verified: ' + item.id)
    for name, digest in files.items():
        path = _within(package / name, package)
        _require(_watch(path, expected) == digest, 'Imported file changed: ' + str(path))
    target = _within(package / 'prepared.frag', package)
    previous = _watch(target, expected)
    if previous:
        _require(bool(MARKER.search(target.read_text(encoding='utf-8-sig'))),
                 'Foreign prepared.frag; refusing overwrite: ' + str(target))
    return target


def build_plan(results_path=DEFAULT_RESULTS, catalog_path=audit.DEFAULT_CATALOG, import_root=None):
    """Validate every record and return an in-memory plan; performs no writes."""
    results_path, catalog_path = Path(results_path).resolve(), Path(catalog_path).resolve()
    expected = {}
    _watch(results_path, expected)
    _watch(catalog_path, expected)
    data, catalog = _json(results_path), load_catalog(catalog_path)
    _require(data.get('schema_version') == 1, 'Unsupported audit schema.')
    _require(data.get('transport_failed') is False, 'Audit has not completed without transport failure.')
    _require(len(catalog.materials) == EXPECTED_COUNT, 'Catalog must contain exactly %d materials.' % EXPECTED_COUNT)
    records = data.get('results', [])
    ids = [r.get('id') for r in records]
    _require(len(ids) == EXPECTED_COUNT and len(set(ids)) == EXPECTED_COUNT
             and set(ids) == {m.id for m in catalog.materials}, 'Audit must cover every catalog material exactly once.')
    by_id = {r['id']: r for r in records}
    runtime_hashes, adapter_hash = audit.runtime_fingerprints(), audit.sha256_file(adapter.__file__)
    import_root = Path(import_root or data.get('provenance', {}).get('import_root') or ROOT/'material_library/imported').resolve()
    materials, writes, outcomes, missing_packages = [], [], Counter(), []
    for item in catalog.materials:
        _require(bool(re.fullmatch(r'mat_[0-9a-f]{20}', item.id)), 'Unsafe material ID: ' + item.id)
        record = by_id[item.id]
        _require(record.get('status') in TERMINAL and record.get('completed_at') and not record.get('interrupted_gpu'),
                 'Pending, interrupted, or unusable record: ' + item.id)
        _require(Path(record.get('source_path', '')).resolve() == Path(item.source_path).resolve(),
                 'Source path mismatch: ' + item.id)
        source_hash = _watch(item.source_path, expected)
        _require(source_hash and source_hash == record.get('source_sha256'), 'Source changed since audit: ' + item.id)
        adaptation, fresh = _fresh_adaptation(catalog, item, expected)
        _require(fresh == record.get('adaptation'), 'Adaptation or texture dependencies changed since audit: ' + item.id)
        quarantine = audit.quarantine_reason(item)
        import_status = record.get('import', {}).get('status')
        fingerprint_data = dict(source=source_hash, adaptation=fresh, adapter_hash=adapter_hash,
                                runtime_hashes=runtime_hashes, quarantine=quarantine,
                                import_status='ok' if import_status in ('existing', 'imported') else import_status)
        fingerprint = _hash_bytes(json.dumps(fingerprint_data, sort_keys=True).encode('utf-8'))
        _require(fingerprint == record.get('fingerprint'), 'Runtime/adapter fingerprint changed since audit: ' + item.id)
        eligible, validation_status, reasons = _classify(record, adaptation, quarantine)
        outcomes[validation_status] += 1
        reasons = list(dict.fromkeys(reasons + list(adaptation.warnings)))
        if eligible:
            _require(import_status in ('existing', 'imported'), 'GPU-ready record has an unsuccessful import: ' + item.id)
            reasons.insert(0, 'GPU compiled and finite at t=0,1,2; visual review remains.' if validation_status == 'review'
                           else 'GPU compiled and finite at t=0,1,2.')
            target = _managed_shader_target(item, record, import_root, source_hash, expected)
            if target is not None:
                _require(adaptation.shader and MARKER.search(adaptation.shader), 'Fresh shader lacks adapter marker: ' + item.id)
                writes.append((target, adaptation.shader.encode('utf-8')))
            else:
                missing_packages.append(item.id)
        metadata = dict(item.metadata)
        metadata.update(adaptation.metadata)
        metadata['_TD_VALIDATION'] = dict(
            status=validation_status, audit_status=record['status'], adapter_version=adapter.ADAPTER_VERSION,
            source_sha256=source_hash, shader_sha256=fresh['shader_sha256'], fingerprint=fingerprint,
            runtime_fingerprints=runtime_hashes, adapter_sha256=adapter_hash,
            completed_at=record['completed_at'], reasons=reasons, reason='; '.join(reasons),
            gpu_evidence=record.get('probe'), audit_path=str(results_path), audit_sha256=expected[results_path],
        )
        materials.append(replace(item, metadata=metadata,
                                 compatibility=Compatibility.ADAPTABLE if eligible else Compatibility.UNSUPPORTED,
                                 compatibility_reasons=tuple(reasons)))
    prepared_count = len(writes)
    writes.append((catalog_path, _json_bytes(replace(catalog, materials=tuple(materials)).to_dict())))
    summary = dict(mode='plan', catalog=str(catalog_path), results=str(results_path), catalog_count=EXPECTED_COUNT,
                   outcomes=dict(outcomes), prepared_shaders=prepared_count, missing_managed_packages=missing_packages,
                   writes=[str(p) for p, _ in writes], live_deployment=False)
    return PublicationPlan(catalog_path, results_path, tuple(writes), expected, runtime_hashes, adapter_hash, summary)


def _atomic_write(path, content):
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.publish-tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_plan(plan):
    """Explicit mutation boundary. Revalidate before backup or any write."""
    _require(audit.runtime_fingerprints() == plan.runtime_hashes and audit.sha256_file(adapter.__file__) == plan.adapter_hash,
             'Runtime changed after planning.')
    for path, digest in plan.expected_files.items():
        actual = audit.sha256_file(path) if path.is_file() else None
        _require(actual == digest, 'File changed after planning: ' + str(path))
    for path, _ in plan.writes:
        _require(path.resolve() == path, 'Write target redirected after planning: ' + str(path))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = plan.results_path.parent / 'publish-backups' / ('catalog-' + stamp + '.json')
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as stream:
        stream.write(plan.catalog_path.read_bytes())
    originals = {p: p.read_bytes() if p.exists() else None for p, _ in plan.writes}
    changed = []
    try:
        for path, content in plan.writes:
            _atomic_write(path, content)
            changed.append(path)
    except Exception:
        for path in reversed(changed):
            if originals[path] is None:
                path.unlink()
            else:
                _atomic_write(path, originals[path])
        raise
    return dict(plan.summary, mode='applied', catalog_backup=str(backup))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS)
    parser.add_argument('--catalog', type=Path, default=audit.DEFAULT_CATALOG)
    parser.add_argument('--import-root', type=Path)
    parser.add_argument('--apply', action='store_true', help='Explicitly write the verified plan; never deploys live.')
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.results, args.catalog, args.import_root)
        print(json.dumps(apply_plan(plan) if args.apply else plan.summary, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Publication refused: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
