"""Read-only observation coverage. Detection counts are not 3D quality."""
import csv
import math
from collections import Counter
from pathlib import Path
from functools import lru_cache
from itertools import islice


@lru_cache(maxsize=32)
def _view_ids(path, stamp, size):
    """Cache unchanged observations across capture progress/status refreshes."""
    if size > 16 * 1024 * 1024:
        raise ValueError('view exceeds 16 MiB; choose a bounded observation file')
    with open(path, newline='', encoding='utf-8-sig') as stream:
        rows = list(islice(csv.DictReader(stream), 100001))
    if len(rows) > 100000:
        raise ValueError('view exceeds 100000 observations')
    ids = [int(r['index']) for r in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError('empty view or duplicate LED IDs')
    if any(not all(math.isfinite(float(r[k])) and 0 <= float(r[k]) <= 1
                   for k in ('u', 'v')) for r in rows):
        raise ValueError('invalid image coordinates')
    return frozenset(ids)


def coverage(paths, expected):
    expected = set(expected)
    counts = Counter()
    accepted, errors = [], []
    for path in dict.fromkeys(str(Path(p).resolve()) for p in paths):
        try:
            stamp = Path(path).stat()
            ids = _view_ids(path, stamp.st_mtime_ns, stamp.st_size)
            counts.update(ids & expected)
            accepted.append(path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(Path(path).name + ': ' + str(error))
    return dict(views=len(accepted), total=len(expected),
                seen=sum(counts[i] > 0 for i in expected),
                twice=sum(counts[i] >= 2 for i in expected),
                three=sum(counts[i] >= 3 for i in expected),
                missing=sorted(i for i in expected if not counts[i]),
                weak={i:counts[i] for i in sorted(expected) if 0 < counts[i] < 3},
                errors=errors)


def description(data, last):
    def short(values):
        values=list(values)
        return ', '.join(map(str, values[:18])) + (' ...' if len(values)>18 else '') or 'keine'
    total=data['total']
    weak=short('%s (%sx)' % (i,n) for i,n in data['weak'].items())
    state=last.get('state', 'noch keine Aufnahme')
    end=('Erfassung vollstaendig - 3D-Qualitaet noch nicht geprueft.'
         if total and data['twice']==total else 'Weitere Ansichten empfohlen - 3D-Qualitaet noch nicht geprueft.')
    return ('Ansichten: %d | Erfasst: %d/%d | mind. 2x: %d/%d | mind. 3x: %d/%d\n'
            'Fehlende IDs: %s | Schwach erfasst: %s\n'
            'Letzter Scan: %s | erkannt %s/%s%s\n%s%s') % (
                data['views'],data['seen'],total,data['twice'],total,data['three'],total,
                short(data['missing']),weak,state,last.get('detected','-'),last.get('total','-'),
                (' | '+str(last['error'])) if last.get('error') else '',end,
                (' | Nicht lesbare/ungueltige Ansichten: %d' % len(data['errors'])) if data['errors'] else '')


_last_key = None
def refresh(op):
    global _last_key
    root=op('/project1/guided_scan')
    panel=op('/project1/guided_scan/ui_panel/coverage')
    if root is None or panel is None:
        return
    try:
        from .scan_session import ScanSession
        from .guided_scan_live import _field
        state=ScanSession.from_dict(root.fetch('session'))
        wanted=set(state.capture_ids)
        expected=[t.source_index for t in state.targets if t.led_id in wanted]
        paths=[p.strip() for p in _field(op,'views').split('|') if p.strip() not in ('','None')]
        last=root.fetch('capture_status',{}) or {}
        stamps=[]
        for path in paths:
            try:
                s=Path(path).stat(); stamps.append((path,s.st_mtime_ns,s.st_size))
            except OSError: stamps.append((path,None,None))
        key=repr((stamps,expected,last))
        if key==_last_key: return
        data=coverage(paths,expected)
        panel.par.text=description(data,last)
        root.store('coverage_summary',data)
        _last_key=key
    except Exception as error:
        panel.par.text='Abdeckung nicht verfuegbar: '+str(error)
