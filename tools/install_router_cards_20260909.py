"""Run inside TD globals. Hot-install UI only; never rebuild/start/stop sender."""
import ast
import importlib
import re
from pathlib import Path


def install(td_globals):
    from pixelblaze_mapper import router_dynamic_ui
    from pixelblaze_mapper.routing_transaction import table_rows
    importlib.reload(router_dynamic_ui)
    owner = td_globals['op']('/project1/multi_controller_output')
    before = {name: table_rows(owner.op(name)) for name in ('controller_config', 'segment_config')}
    enabled = owner.op('artnet_510_sender_callbacks').module.status()['enabled']
    path = Path('C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper/pixelblaze_mapper/build_multi_controller_output.py')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = {'_get_or_create', '_replace_dat_text', '_set_if_present', '_label', '_field', '_button', '_ui_callbacks_source'}
    scope = dict(td_globals, re=re)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
    previous = owner.op('ui_callbacks').text
    owner.store('router_card_previous_callbacks', previous)
    try:
        scope['_replace_dat_text'](owner.op('ui_callbacks'), scope['_ui_callbacks_source']())
        router_dynamic_ui.install(owner, scope)
        owner.op('ui_callbacks').module.refresh_status(force=True)
        assert before == {name: table_rows(owner.op(name)) for name in before}
        assert enabled == owner.op('artnet_510_sender_callbacks').module.status()['enabled']
    except Exception:
        scope['_replace_dat_text'](owner.op('ui_callbacks'), previous)
        raise
    return {'controllers': len(before['controller_config']) - 1, 'config_unchanged': True,
            'sender_enabled_unchanged': enabled, 'selected': owner.fetch('router_card_name', None)}
