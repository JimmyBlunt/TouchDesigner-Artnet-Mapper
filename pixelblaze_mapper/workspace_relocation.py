"""Preflight portable runtime path references without editing files or TD state.

Only complete absolute path values (or a path-only ``|`` list) can move. Files
must already exist at both roots with byte-identical contents. This module does
not copy files, rewrite historical manifests, modify modules or launch workers.
"""
from hashlib import sha256
import json
from pathlib import Path
import re


class RelocationError(ValueError):
    """The complete relocation cannot be verified; no result may be applied."""


PROVENANCE_KEYS = ('observation_reference', 'registration_reference', 'quality_reference')
_DIGEST = re.compile(r'^(.*)(#sha256=([0-9a-fA-F]{64}))$')
_WINDOWS_ABSOLUTE = re.compile(r'^[A-Za-z]:[/\\]')


def _absolute(value):
    return bool(_WINDOWS_ABSOLUTE.match(value)) or value.startswith(('/', '\\\\'))


def _stamp(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ino


def _equal_files(source, target):
    """Compare actual bytes and bind the report to an unchanged read snapshot."""
    before = (_stamp(source), _stamp(target))
    if before[0][0] != before[1][0]:
        raise RelocationError('Copied file size differs: ' + str(target))
    digest = sha256()
    with source.open('rb') as old_stream, target.open('rb') as new_stream:
        while True:
            old = old_stream.read(1024 * 1024)
            new = new_stream.read(1024 * 1024)
            if old != new:
                raise RelocationError('Copied file bytes differ: ' + str(target))
            if not old:
                break
            digest.update(old)
    if before != (_stamp(source), _stamp(target)):
        raise RelocationError('A referenced file changed during relocation preflight')
    return {'sha256': digest.hexdigest(), 'bytes': before[0][0]}


def prepare_relocation(value, old_root, new_root, *, preserve_keys=PROVENANCE_KEYS):
    """Return ``value``, changes and evidence only after all references validate.

    ``value`` accepts JSON-compatible dictionaries, lists/tuples and scalars.
    Dictionary keys, arbitrary prose, embedded JSON strings, URLs and unrelated
    paths are preserved. Default provenance keys remain historical references;
    pass ``preserve_keys=()`` when intentionally relocating active references
    bearing those names. Even then, no referenced file is ever rewritten.

    The caller must invalidate prepared hardware/offline jobs and apply the
    returned copy in its own guarded runtime transaction. A successful report
    is read evidence, not a hardware authorization or a future file guarantee.
    """
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as error:
        raise RelocationError('Runtime snapshot must be finite JSON-compatible data') from error
    try:
        old_root, new_root = Path(old_root).resolve(strict=True), Path(new_root).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise RelocationError('Relocation roots must already exist: ' + str(error)) from error
    if not old_root.is_dir() or not new_root.is_dir():
        raise RelocationError('Both relocation roots must be existing directories')
    if old_root == new_root:
        raise RelocationError('Relocation roots must differ')
    old_prefix = old_root.as_posix().rstrip('/')
    windows = bool(_WINDOWS_ABSOLUTE.match(old_prefix)) or old_prefix.startswith('//')
    comparable = old_prefix.casefold() if windows else old_prefix
    protected = set(preserve_keys)
    if any(type(key) is not str for key in protected):
        raise RelocationError('preserve_keys must contain field names')
    changes, validated, preserved = [], {}, []

    def relocate_path(raw, location):
        stripped = raw.strip()
        normalized = stripped.replace('\\', '/')
        check = normalized.casefold() if windows else normalized
        if check != comparable and not check.startswith(comparable + '/'):
            return raw
        match = _DIGEST.fullmatch(normalized)
        suffix, expected_digest = '', None
        if match:
            normalized, suffix, expected_digest = match.groups()
        relative = normalized[len(old_prefix):].lstrip('/')
        components = relative.split('/') if relative else []
        if any(part in ('.', '..') for part in components) or any(':' in part for part in components):
            raise RelocationError('Ambiguous/traversing path at ' + location)
        source = (old_root / Path(*components)).resolve(strict=True)
        target = (new_root / Path(*components)).resolve(strict=True)
        if not source.is_relative_to(old_root) or not target.is_relative_to(new_root):
            raise RelocationError('Linked reference leaves its relocation root: ' + location)
        pair = (str(source), str(target))
        if pair not in validated:
            if source.is_file() and target.is_file():
                evidence = {'kind': 'file', **_equal_files(source, target)}
            elif source.is_dir() and target.is_dir():
                evidence = {'kind': 'directory'}
            else:
                raise RelocationError('Source/target type differs: ' + str(target))
            validated[pair] = {'old': source.as_posix(), 'new': target.as_posix(), **evidence}
        evidence = validated[pair]
        if expected_digest and (evidence.get('sha256') != expected_digest.lower()):
            raise RelocationError('Evidence hash does not match file bytes: ' + location)
        migrated = target.as_posix() + suffix
        # Preserve surrounding field/list whitespace; normalize only the path.
        left = raw[:len(raw) - len(raw.lstrip())]
        right = raw[len(raw.rstrip()):]
        result = left + migrated + right
        changes.append({'location': location, 'old': raw, 'new': result, 'kind': evidence['kind']})
        return result

    def relocate_string(raw, location):
        if '|' not in raw:
            return relocate_path(raw, location)
        parts = raw.split('|')
        # A status sentence containing a path is not a view-file list.
        if not all(not part.strip() or part.strip() == 'None' or _absolute(part.strip()) for part in parts):
            return raw
        return '|'.join(relocate_path(part, '%s|%d' % (location, index)) for index, part in enumerate(parts))

    def walk(item, location):
        if isinstance(item, dict):
            result = {}
            for key, child in item.items():
                if type(key) is not str:
                    raise RelocationError('Runtime dictionaries require string keys: ' + location)
                child_location = location + '/' + key.replace('~', '~0').replace('/', '~1')
                if key in protected:
                    # Clone protected values too: callers cannot mutate input
                    # through a shared nested historical reference afterwards.
                    result[key] = json.loads(json.dumps(child, allow_nan=False))
                    preserved.append(child_location)
                else:
                    result[key] = walk(child, child_location)
            return result
        if isinstance(item, (list, tuple)):
            rows = [walk(child, '%s/%d' % (location, index)) for index, child in enumerate(item)]
            return tuple(rows) if isinstance(item, tuple) else rows
        if isinstance(item, str):
            return relocate_string(item, location)
        return item

    try:
        relocated = walk(value, '')
    except (OSError, RuntimeError) as error:
        raise RelocationError('Reference preflight failed: ' + str(error)) from error
    return {'value': relocated, 'changes': changes, 'validated': list(validated.values()),
            'preserved': preserved, 'roots': {'old': old_root.as_posix(), 'new': new_root.as_posix()}}
