"""Resolve bundled material assets after a checkout move, without rewriting metadata."""
from copy import deepcopy
import json
from pathlib import Path, PureWindowsPath


def project_root_for_catalog(catalog_path):
    path = Path(catalog_path).resolve()
    for parent in path.parents:
        if parent.name.casefold() == 'material_library':
            return parent.parent
    return Path(__file__).resolve().parents[1]


def resolve_asset_path(value, *, project_root=None, base_dir=None):
    """Map only the material_library subtree to this checkout; reject traversal.

    An old copy that still exists must never shadow the bundled reviewed asset.
    Unknown external paths remain external and undergo the caller's root checks.
    """
    if not value:
        return value
    raw = str(value).replace('\\', '/')
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    marker = '/material_library/'
    lower = raw.casefold()
    if lower.startswith('material_library/'):
        tail = raw[len('material_library/'):]
    elif marker in lower:
        tail = raw[lower.index(marker) + len(marker):]
    elif lower.endswith('/material_library'):
        tail = ''
    else:
        if not Path(raw).is_absolute() and not PureWindowsPath(raw).is_absolute() and base_dir is not None:
            return str((Path(base_dir) / raw).resolve())
        return str(value)
    parts = tail.split('/')
    if any(part in ('.', '..') or ':' in part for part in parts):
        raise ValueError('Invalid bundled material asset path: ' + str(value))
    library = (root / 'material_library').resolve()
    target = (library / tail).resolve()
    if target != library and library not in target.parents:
        raise ValueError('Material asset escapes the bundled library: ' + str(value))
    return str(target)


def resolve_catalog_document(document, catalog_path):
    """Return a copy with runtime paths; stable IDs/validation metadata are intact."""
    result = deepcopy(document)
    base = Path(catalog_path).resolve().parent
    root = project_root_for_catalog(catalog_path)
    if isinstance(result, dict):
        source = result.get('source')
        if isinstance(source, dict) and source.get('root'):
            source['root'] = resolve_asset_path(source['root'], project_root=root, base_dir=base)
        records = next((result[key] for key in ('materials', 'items', 'entries') if isinstance(result.get(key), list)), [])
    elif isinstance(result, list):
        records = result
    else:
        return result
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in ('source_path', 'preview_path', 'prepared_shader_path', 'touchdesigner_shader_path'):
            if record.get(key):
                record[key] = resolve_asset_path(record[key], project_root=root, base_dir=base)
    return result


def load_catalog_document(path):
    source = Path(path)
    return resolve_catalog_document(json.loads(source.read_text(encoding='utf-8-sig')), source)
