"""Repair saved runtime references after the user moved the workspace.

Uses the read-only before.json snapshot; does not modify source scan files.
Historical storage backups are retained. Source code is compiled before applying.
"""
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import tokenize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/performance-program-20260913/relocation'
OLD = 'C:/Users/jbhtz/OneDrive/Desktop/Pictures/Documents/ChatGPT/LED-Touchdesigner-Controller/PixelblazeMapper'
LOCAL = 'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper'
BOOT = "# PORTABLE_PROJECT_IMPORT_V1\nimport sys as _project_sys\n_project_root = str(project.folder)\nif _project_root in _project_sys.path:\n    _project_sys.path.remove(_project_root)\n_project_sys.path.insert(0, _project_root)\n"


def portable_code(source):
    """Replace exact root string literals, never prose or relative data paths."""
    tree = ast.parse(source)
    tokens = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.STRING:
            try:
                value = ast.literal_eval(token.string)
            except (ValueError, SyntaxError):
                value = None
            if isinstance(value, str) and value.replace('\\', '/').rstrip('/').lower() in (OLD.lower(), LOCAL.lower()):
                token = token._replace(string='str(project.folder)')
            elif isinstance(value, str):
                normalized = value.replace('\\', '/')
                if normalized.lower().startswith(OLD.lower() + '/'):
                    relative = normalized[len(OLD) + 1:]
                    if not (ROOT / relative).exists():
                        raise ValueError('Missing active code reference: ' + value)
                    token = token._replace(string="(str(project.folder).rstrip('/\\\\') + " + repr('/' + relative) + ")")
        tokens.append(token)
    result = tokenize.untokenize(tokens)
    if 'pixelblaze_mapper' in source and 'PORTABLE_PROJECT_IMPORT_V1' not in result:
        lines = result.splitlines(keepends=True)
        tree = ast.parse(result)
        end = 0
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                end = node.end_lineno
            elif isinstance(node, ast.ImportFrom) and node.module == '__future__':
                end = node.end_lineno
            else:
                break
        lines.insert(end, BOOT)
        result = ''.join(lines)
    compile(result, '<relocated DAT>', 'exec')
    return result


def prepare():
    snapshot = OUT / 'before.json'
    before = json.loads(snapshot.read_text(encoding='utf-8') if snapshot.exists()
                        else gzip.decompress((OUT / 'before.json.gz').read_bytes()).decode('utf-8'))
    changes, missing, targets = [], set(), {}

    def path_value(value):
        if not isinstance(value, str):
            return value
        if '|' in value:
            parts = value.split('|')
            if all(not s.strip() or s.strip() == 'None' or (len(s.strip()) > 2 and s.strip()[1] == ':') for s in parts):
                return '|'.join(path_value(s) for s in parts)
            return value
        normalized = value.strip().replace('\\', '/')
        if normalized.lower() != OLD.lower() and not normalized.lower().startswith(OLD.lower() + '/'):
            return value
        raw, sep, digest = normalized.partition('#sha256=')
        target = ROOT / raw[len(OLD) + 1:]
        if not target.exists():
            missing.add(value)
            return value
        if sep and hashlib.sha256(target.read_bytes()).hexdigest() != digest.lower():
            raise ValueError('Reference digest mismatch: ' + str(target))
        targets[str(target)] = {'exists': True, 'digest_verified': bool(sep)}
        return value[:len(value)-len(value.lstrip())] + target.as_posix() + (sep + digest if sep else '') + value[len(value.rstrip()):]

    def walk(value):
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        return path_value(value)

    for item in before['nodes']:
        source = item.get('text')
        if source is not None and item['type'] in ('text', 'execute', 'table'):
            updated = source
            try:
                data = json.loads(source)
            except (ValueError, TypeError):
                data = None
            if isinstance(data, (dict, list)):
                data2 = walk(data)
                if data2 != data:
                    updated = json.dumps(data2, indent=2)
            elif item['type'] in ('text', 'execute'):
                try:
                    updated = portable_code(source)
                except SyntaxError:
                    updated = path_value(source)
            else:
                updated = path_value(source)
            if updated != source:
                changes.append({'path': item['path'], 'kind': 'text', 'before': source, 'after': updated})
        for par in item.get('pars', []):
            updated = path_value(par['value'])
            if updated != par['value'] and par['mode'] == 'ParMode.CONSTANT':
                changes.append({'path': item['path'], 'kind': 'par', 'name': par['name'], 'before': par['value'], 'after': updated})
        if item['path'] == '/project1/guided_scan':
            for key, value in item.get('storage', {}).items():
                if key in ('manifest', 'capture_plan', 'capture_signature', 'manifest_view_paths'):
                    updated = None
                elif key in ('session', 'offline_status', 'result_review', 'capture_status', 'registration_context', 'registration_proposal', 'scan_library_selected', 'scan_library_preview', 'scan_library_index', 'scan_library_visible'):
                    updated = walk(value)
                else:
                    continue
                if updated != value:
                    changes.append({'path': item['path'], 'kind': 'storage', 'name': key, 'before': value, 'after': updated})
    plan = {'changes': changes, 'missing': sorted(missing), 'targets': targets}
    (OUT / 'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print(json.dumps({'changes': len(changes), 'targets': len(targets), 'missing': sorted(missing)}))


if __name__ == '__main__':
    prepare()
