"""Transactional output installation: preflight, write, verify or restore.

Never starts output. Restores callback texts, changed wires and existing gate
shapes on failure, and removes only helpers created by this transaction.
"""
import ast
from copy import deepcopy
from hashlib import sha256
import importlib
import json
from math import isfinite
from pathlib import Path

from tools.install_scan_workflow_ux import SNAPSHOT

ROOT = Path(__file__).resolve().parents[1]


def _required(op, path):
    node = op(path)
    if node is None:
        raise ValueError('Missing output install node: ' + path)
    return node


def _preflight_gate(mask, sink, source, count):
    if (sink.type != 'dmxout' or source.type not in ('script', 'merge')
            or source.parent() != sink.parent() or type(count) is not int or count < 1
            or not isfinite(float(source.rate)) or float(source.rate) <= 0
            or getattr(sink.par, 'active', None) is None):
        raise ValueError('Invalid output gate source/sink/shape: ' + sink.path)
    parent = sink.parent()
    gate, idle = parent.op(sink.name + '_demand_gate'), parent.op(sink.name + '_idle_black')
    if gate is None and idle is None:
        if list(sink.inputs) != [source]:
            raise ValueError('Unknown sink wiring: ' + sink.path)
    elif gate is None or idle is None or list(sink.inputs) != [gate]:
        raise ValueError('Partial or conflicting owned gate: ' + sink.path)
    else:
        mask._masked_sink(None, sink, source)


def _set_inputs(node, sources):
    for connector in node.inputConnectors:
        connector.disconnect()
    for index, source in enumerate(sources):
        if source is not None:
            source.outputConnectors[0].connect(node.inputConnectors[index])


def _shape_snapshot(node, gate):
    if node is None:
        return None
    shape = deepcopy(node.fetch(gate.SHAPE_KEY, None))
    parameters = {name: (getattr(node.par, name).val, getattr(node.par, name).expr,
                         getattr(node.par, name).mode)
                  for name in gate._settings(shape['count'], shape['rate'])}
    return node, shape, parameters


def _transaction(op, replacements, *, mask, gate, specs, create_mask, types, snapshot, before):
    """Apply a preflighted plan. Kept separate for deterministic fault tests."""
    project = _required(op, '/project1')
    shuffle = _required(op, '/project1/shuffle1')
    helper_paths = ['/project1/legacy_source_mask_callbacks', '/project1/legacy_source_mask']
    for sink, _, _ in specs:
        helper_paths.extend(sink.parent().path + '/' + sink.name + suffix for suffix in ('_idle_black', '_demand_gate'))
    helper_before = {path: op(path) for path in helper_paths}
    wire_before = [(node, list(node.inputs)) for node in [shuffle] + [s[0] for s in specs]]
    shapes = [_shape_snapshot(sink.parent().op(sink.name + '_idle_black'), gate) for sink, _, _ in specs]
    originals = [(node, node.text) for node, _ in replacements]
    try:
        for node, source in replacements:
            node.text = source
        if create_mask:
            callback = project.create(types['textDAT'], 'legacy_source_mask_callbacks')
            callback.text = mask.LEGACY_MASK_CALLBACK
            node = project.create(types['scriptCHOP'], 'legacy_source_mask')
            node.par.callbacks = callback.path
            _set_inputs(node, [_required(op, '/project1/merge2')])
            _set_inputs(shuffle, [node])
            node.viewer = False
        gates = gate.install_sink_gates(specs, constant_type=types['constantCHOP'],
            select_type=types['selectCHOP'], allowed_source_types=('script', 'merge'))
        mask.assert_sparse_contract(op)
        after = snapshot()
        checks = {'data_unchanged': before['hashes'] == after['hashes'],
                  'errors_empty': not after['errors'],
                  'outputs_off': not after['sender']['enabled'] and not any(after['native'].values())}
        if not all(checks.values()):
            raise RuntimeError('Output install verification failed: ' + json.dumps(checks, sort_keys=True))
        return {'before': before, 'after': after, 'gates': gates, 'checks': checks,
                'callback_changes': [{'path': node.path, 'before_sha256': sha256(old.encode()).hexdigest(),
                                      'after_sha256': sha256(node.text.encode()).hexdigest()}
                                     for node, old in originals if old != node.text],
                'created_nodes': [path for path, old in helper_before.items() if old is None and op(path) is not None]}
    except Exception as error:
        rollback_errors = []
        for node, sources in reversed(wire_before):
            try:
                _set_inputs(node, sources)
            except Exception as failure:
                rollback_errors.append(node.path + ' wiring: ' + str(failure))
        for saved in shapes:
            if saved is None:
                continue
            node, shape, parameters = saved
            try:
                for name, (value, expression, mode) in parameters.items():
                    par = getattr(node.par, name)
                    par.val = value
                    if expression is not None:
                        par.expr = expression
                    par.mode = mode
                node.store(gate.SHAPE_KEY, shape)
            except Exception as failure:
                rollback_errors.append(node.path + ' shape: ' + str(failure))
        for node, source in reversed(originals):
            try:
                node.text = source
            except Exception as failure:
                rollback_errors.append(node.path + ' callback: ' + str(failure))
        for path, previous in reversed(list(helper_before.items())):
            if previous is None:
                try:
                    node = op(path)
                    if node is not None:
                        node.destroy()
                except Exception as failure:
                    rollback_errors.append(path + ' cleanup: ' + str(failure))
        try:
            if any(node.text != source for node, source in originals):
                raise RuntimeError('Callback text restoration mismatch')
            if any(list(node.inputs) != sources for node, sources in wire_before):
                raise RuntimeError('Output wiring restoration mismatch')
            if any(op(path) != previous for path, previous in helper_before.items()):
                raise RuntimeError('Owned helper restoration mismatch')
            for saved in shapes:
                if saved is not None and _shape_snapshot(saved[0], gate) != saved:
                    raise RuntimeError('Existing gate shape restoration mismatch')
            restored = snapshot()
            if (restored['hashes'] != before['hashes'] or restored['sender']['enabled'] != before['sender']['enabled']
                    or restored['native'] != before['native']):
                raise RuntimeError('Protected data or output state differs after rollback')
        except Exception as failure:
            rollback_errors.append(str(failure))
        if rollback_errors:
            raise RuntimeError('Output install failed: %s; ROLLBACK FAILED: %s' % (error, '; '.join(rollback_errors))) from error
        raise RuntimeError('Output install failed; callback/wiring/helper changes restored: ' + str(error)) from error


def install_output(namespace, root, *, snapshot):
    """Install reviewed callback versions in an already-stopped project."""
    op = namespace['op']
    root = Path(root)
    before = snapshot()
    if before['sender']['enabled'] or any(before['native'].values()):
        raise ValueError('Stop all output before installing output callbacks')
    from pixelblaze_mapper import output_slot_mask as mask, legacy_esp_bulk, native_dmx_gate as gate
    for module in (mask, legacy_esp_bulk, gate):
        importlib.reload(module)
    from pixelblaze_mapper.sender_pacing import install_source as pacing
    from pixelblaze_mapper.routing_transaction import records, table_rows
    path = root / 'pixelblaze_mapper/build_multi_controller_output.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    tree.body = [node for node in tree.body if not (isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'build')]
    scope = dict(namespace, __file__=str(path), __name__='completion_output')
    exec(compile(tree, str(path), 'exec'), scope, scope)
    owner = _required(op, '/project1/multi_controller_output')
    replacements = {}
    def stage(node, source):
        if node is None or node.type != 'text':
            raise ValueError('Expected an existing text callback DAT')
        compile(source, node.path, 'exec')
        previous = replacements.get(node.path)
        if previous is not None and previous[1] != source:
            raise ValueError('Different controllers share a callback DAT: ' + node.path)
        replacements[node.path] = node, source
    stage(owner.op('artnet_510_sender_callbacks'), pacing(mask.install_source(scope['_artnet_510_sender_source']())))
    stage(owner.op('ui_callbacks'), scope['_ui_callbacks_source']())
    for row in records(table_rows(owner.op('controller_config'))):
        pack = owner.op('pack_' + scope['_safe_name'](row['name']))
        if pack is not None:
            stage(op(str(pack.par.callbacks.eval())), mask.install_native_source(scope['_pack_callbacks'](row['name'])))
    legacy = _required(op, '/project1/esp_artnet_live_pack_callbacks')
    baseline = json.loads((root / 'docs/completion-20260910/legacy-output-before.json').read_text(encoding='utf-8'))['pack']
    replacement = legacy_esp_bulk.source_for_bulk(baseline, sha256(baseline.encode()).hexdigest())
    if legacy.text not in (baseline, replacement, replacement.replace("for key in 'rgb'", "for key in 'RGB'")):
        raise ValueError('Legacy callback changed outside the reviewed installer')
    stage(legacy, replacement)
    legacy_pack = _required(op, '/project1/esp_artnet_live_pack')
    if str(legacy_pack.par.callbacks.eval()) != legacy.path:
        raise ValueError('Legacy ESP callback binding differs from the reviewed baseline')
    mask_node, callback = op('/project1/legacy_source_mask'), op('/project1/legacy_source_mask_callbacks')
    shuffle, source = _required(op, '/project1/shuffle1'), _required(op, '/project1/merge2')
    if mask_node is None:
        if callback is not None or list(shuffle.inputs) != [source]:
            raise ValueError('Legacy mask name collision or unknown shuffle wiring')
        compile(mask.LEGACY_MASK_CALLBACK, '<legacy source mask>', 'exec')
    else:
        if (mask_node.type != 'script' or callback is None or callback.type != 'text'
                or str(mask_node.par.callbacks.eval()) != callback.path
                or list(mask_node.inputs) != [source] or list(shuffle.inputs) != [mask_node]
                or mask.CONTRACT not in callback.text):
            raise ValueError('Existing legacy mask is not the reviewed owned mask')
        stage(callback, mask.LEGACY_MASK_CALLBACK)
    specs = [(_required(op, '/project1/esp_artnet_out'), legacy_pack, 10),
             (_required(op, '/project1/dmxout1'), _required(op, '/project1/merge1'), 22)]
    for sink, source, count in specs:
        _preflight_gate(mask, sink, source, count)
    names = ('textDAT', 'scriptCHOP', 'constantCHOP', 'selectCHOP')
    if all(name in namespace for name in names):
        types = {name: namespace[name] for name in names}
    else:
        import td
        types = {name: namespace.get(name, getattr(td, name)) for name in names}
    return _transaction(op, list(replacements.values()), mask=mask, gate=gate, specs=specs,
        create_mask=mask_node is None, types=types, snapshot=snapshot, before=before)


SCRIPT = SNAPSHOT + r'''
import importlib
from tools import install_completion_output as installer
importlib.reload(installer)
result = json.dumps(installer.install_output(globals(), __ROOT__, snapshot=snapshot))
'''

if __name__ == '__main__':
    from tools.audit_20260907_capture import td
    result = td(SCRIPT.replace('__ROOT__', repr(str(ROOT))))
    (ROOT / 'docs/completion-20260910/output-install.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['checks'], indent=2))
