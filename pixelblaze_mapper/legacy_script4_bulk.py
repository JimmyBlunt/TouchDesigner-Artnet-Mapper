"""Opt-in transfer-only replacement for the captured legacy Script CHOP.

No TD lookup, install, cook, source write, simulation reset or RNG call here.
The caller may bind the returned function to an EXISTING callback module.
Reloading source_for_bulk output requires an explicit synchronous state/RNG
handoff by the caller. This module never performs that live operation.
"""
import ast
import hashlib
from types import FunctionType


REFERENCE_SHA256 = 'a5301a6b07e1a17d6943fe57cff9b3d0922fb56fb0db0bbf710048d216c828e2'
BULK_WRITES = '''r_channel.vals = [value[0] for value in led_data]
g_channel.vals = [value[1] for value in led_data]
b_channel.vals = [value[2] for value in led_data]
'''


def _callback_node(source):
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError('Legacy callback source differs from reviewed capture; refusing replacement')
    tree = ast.parse(source)
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'onCook')


def _compile_function(node):
    namespace = {}
    tree = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(tree, '<reviewed script4 transfer>', 'exec'), namespace)
    return namespace['onCook']


def _code_contract(function):
    code = function.__code__
    return (code.co_code, code.co_consts, code.co_names, code.co_varnames,
            code.co_argcount, code.co_kwonlyargcount, code.co_posonlyargcount,
            code.co_freevars, code.co_cellvars)


def source_for_bulk(source):
    """Replace only the reviewed transfer loop's full source lines.

    Initialization, generator, comments outside that loop, whitespace, and
    all other callback code are retained byte for byte. Unknown source fails
    closed. This is not an idempotent installer: retain the original source
    for rollback and verify an already-patched source separately.
    """
    node = _callback_node(source)
    loops = [value for value in node.body if isinstance(value, ast.For)]
    if len(loops) != 1:
        raise ValueError('Expected exactly one reviewed transfer loop')
    loop = loops[0]
    lines = source.splitlines(keepends=True)
    first = lines[loop.lineno - 1]
    # AST column offsets are UTF-8 byte offsets. The reviewed indentation is
    # whitespace, but still honor that contract instead of indexing characters.
    indent = first.encode('utf-8')[:loop.col_offset].decode('utf-8')
    if indent.strip():
        raise ValueError('Transfer loop must start on its own source line')
    newline = '\r\n' if first.endswith('\r\n') else '\n'
    replacement = ''.join(indent + line + newline for line in BULK_WRITES.splitlines())
    result = ''.join(lines[:loop.lineno - 1]) + replacement + ''.join(lines[loop.end_lineno:])
    compile(result, '<reviewed script4 bulk source>', 'exec')
    return result


def make_bulk_callback(original_callback, source):
    """Return a new onCook sharing the old callback's exact global namespace.

    Requires both captured source SHA-256 and actual live onCook code to match.
    Saving/reopening the unchanged DAT intentionally restores the original
    callback. Reapply explicitly after native output/state parity is accepted.
    """
    node = _callback_node(source)
    expected = _compile_function(node)
    if not isinstance(original_callback, FunctionType) or _code_contract(original_callback) != _code_contract(expected):
        raise ValueError('Running onCook differs from reviewed source; refusing replacement')
    loops = [index for index, value in enumerate(node.body) if isinstance(value, ast.For)]
    if len(loops) != 1:
        raise ValueError('Expected exactly one reviewed transfer loop')
    index = loops[0]
    node.body[index:index + 1] = ast.parse(BULK_WRITES).body
    replacement = _compile_function(node)
    result = FunctionType(replacement.__code__, original_callback.__globals__,
                          original_callback.__name__, original_callback.__defaults__,
                          original_callback.__closure__)
    result.__doc__ = 'Reviewed transfer-only bulk callback; simulation globals are retained.'
    return result
