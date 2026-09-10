"""Read-only, bounded discovery of saved MariMapper views.

Only views whose persisted LED identities and scene revision match the staged
session are suggested automatically. CSV filenames or equal numeric indices
alone cannot prove that a view belongs to the same physical object.
"""
import csv
import json
from math import isfinite
from pathlib import Path

from .scan_session import ScanSession, ScanSessionError

MAX_FILES = 250
MAX_FILE_BYTES = 16 * 1024 * 1024


def _read(path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('file exceeds 16 MB discovery limit; select it explicitly')
    return path.read_text(encoding='utf-8-sig')


def _view_ids(path):
    reader = csv.DictReader(_read(path).splitlines())
    if reader.fieldnames != ['index', 'u', 'v']:
        raise ValueError('expected 2D index,u,v CSV')
    ids = set()
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('malformed observation columns')
        index = int(row['index'])
        values = (float(row['u']), float(row['v']))
        if index < 0 or index in ids or not all(isfinite(v) and 0 <= v <= 1 for v in values):
            raise ValueError('duplicate ID or invalid image coordinates')
        ids.add(index)
    if not ids:
        raise ValueError('empty view')
    return ids


def discover_saved_views(workspace, session=None):
    """List root CSVs and capture-*/view.csv without mutation or reconstruction.

    ``paths`` contains identity-verified matches only. ``available`` also lists
    valid legacy/mismatched views with an actionable reason. The UI can report
    those but must not silently attach them. No directory recursion is used.
    """
    if not str(workspace).strip():
        raise ScanSessionError('Choose a scan workspace folder before finding saved views')
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise ScanSessionError('Choose an existing scan workspace folder')
    if isinstance(session, dict):
        session = ScanSession.from_dict(session)
    expected = ({str(t.source_index): t.led_id for t in session.targets if t.led_id in session.capture_ids}
                if session is not None else {})
    available, skipped, matches = [], [], []
    seen = set()
    truncated = False
    candidates = 0
    # Stop discovery itself at the bound, not only result rendering.
    for examined, entry in enumerate(root.iterdir()):
        if candidates >= MAX_FILES or examined >= MAX_FILES * 4:
            truncated = True
            break
        if entry.is_file() and entry.suffix.lower() == '.csv':
            path = entry
        elif entry.is_dir() and entry.name.startswith('capture-'):
            path = entry / 'view.csv'
            if not path.is_file():
                continue
        else:
            continue
        candidates += 1
        try:
            path = path.resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError('linked file is outside the selected workspace')
            if path in seen:
                continue
            seen.add(path)
            ids = _view_ids(path)
            compatible = False
            reason = 'Legacy view: no identity evidence; choose explicitly after checking its object and source IDs'
            manifest_path = path.parent / 'capture.json'
            result_path = path.parent / 'result.json'
            if manifest_path.is_file() and result_path.is_file():
                for evidence in (manifest_path, result_path):
                    if not evidence.resolve(strict=True).is_relative_to(root):
                        raise ValueError('linked metadata is outside the selected workspace')
                manifest = json.loads(_read(manifest_path))
                result = json.loads(_read(result_path))
                if result.get('state') != 'complete':
                    raise ValueError('capture did not finish successfully')
                identity = manifest.get('identity')
                if session is None:
                    reason = 'Stage the matching object/acquisition to verify saved LED identity'
                elif (isinstance(identity, dict) and identity
                      and manifest.get('scene_revision') == session.scene_revision
                      and all(key in expected and expected[key] == value for key, value in identity.items())
                      and all(str(index) in identity for index in ids)):
                    compatible = True
                    reason = 'LED identities and scene revision match the current scan selection'
                else:
                    reason = 'Different LED identity, scene revision or scan scope; stage the original selection'
            available.append({'path': str(path), 'count': len(ids), 'compatible': compatible, 'reason': reason})
            if compatible:
                matches.append(str(path))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            skipped.append(entry.name + ': ' + str(error))
    available.sort(key=lambda item: item['path'])
    matches.sort()
    message = ('%d matching saved views found; %d other views require explicit selection; %d unreadable or incomplete.' %
               (len(matches), len(available) - len(matches), len(skipped)))
    if session is None:
        message += ' Select a Layout object or create an acquisition first.'
    if truncated:
        message += ' Discovery stopped at %d files; choose a narrower folder.' % MAX_FILES
    return {'paths': matches, 'available': available, 'skipped': skipped,
            'truncated': truncated, 'message': message}
