"""Execute inside TouchDesigner after offline relocation planning."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(project.folder)
out = root / 'docs/performance-program-20260913/relocation'
spec = importlib.util.spec_from_file_location('relocate_plan', root / 'tools/relocate_td_project_20260913.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
plan = json.loads((out / 'plan.json').read_text(encoding='utf-8'))
assert not plan['missing']
assert not any(bool(n.par.active.eval()) for n in op('/project1').findChildren(type=dmxoutCHOP))

protected = ['/project1/pixelblaze_mapper/map_active', '/project1/layout_apply/active_source_mask',
             '/project1/multi_controller_output/controller_config', '/project1/multi_controller_output/segment_config']
before_hash = {p: hashlib.sha256(op(p).text.encode()).hexdigest() for p in protected}
changes = plan['changes']
paths = {row['path'] for row in changes if row['kind'] == 'text'}
for n in op('/project1').findChildren():
    if n.family != 'DAT' or n.type not in ('text', 'execute') or n.path in paths:
        continue
    text = n.text
    if 'pixelblaze_mapper' not in text:
        continue
    try:
        tree = ast.parse(text)
    except SyntaxError:
        continue
    imports_package = any(
        (isinstance(a, ast.ImportFrom) and (a.module or '').startswith('pixelblaze_mapper')) or
        (isinstance(a, ast.Import) and any(v.name.startswith('pixelblaze_mapper') for v in a.names))
        for a in ast.walk(tree))
    if imports_package:
        updated = helper.portable_code(text)
        if updated != text:
            changes.append({'path': n.path, 'kind': 'text', 'before': text, 'after': updated})

# Reject a changed editor value instead of overwriting user work.
for row in changes:
    n = op(row['path'])
    assert n is not None, row['path']
    if row['kind'] == 'text':
        assert n.text == row['before'], row['path']
    elif row['kind'] == 'par':
        assert n.par[row['name']].eval() == row['before'], row['path']

(out / 'applied-changes.json').write_text(json.dumps(changes, indent=2), encoding='utf-8')
applied = []
try:
    sys.path.insert(0, str(root))
    for row in changes:
        n = op(row['path'])
        if row['kind'] == 'text':
            n.text = row['after']
        elif row['kind'] == 'par':
            n.par[row['name']] = row['after']
        else:
            n.store(row['name'], row['after'])
        applied.append(row)
    assert before_hash == {p: hashlib.sha256(op(p).text.encode()).hexdigest() for p in protected}
except Exception:
    for row in reversed(applied):
        n = op(row['path'])
        if row['kind'] == 'text':
            n.text = row['before']
        elif row['kind'] == 'par':
            n.par[row['name']] = row['before']
        else:
            n.store(row['name'], row['before'])
    raise
report = {'changes': len(changes), 'protected_table_hashes': before_hash,
          'protected_tables_unchanged': True, 'restart_required': True,
          'note': 'Runtime imports from the previous process require a clean restart.'}
(out / 'applied.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
result = json.dumps(report)
