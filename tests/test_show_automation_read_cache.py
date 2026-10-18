"""Playback reuses validated data; edits and live recording remain immediate."""
import ast
import json
from types import SimpleNamespace
from unittest.mock import patch

from pixelblaze_mapper import show_automation as automation
from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME


def runtime():
    document = automation.empty()
    document['tracks'] = {'cue': {'mat_scale': [[0, 1], [10, 3]], 'speed': [[0, 1]]}}
    node = SimpleNamespace(text=json.dumps(document))
    state = {'recording': '0', 'record_cue': 'cue', 'elapsed': '5', 'outgoing_slot': 'A'}
    transport = SimpleNamespace(_get=lambda name, default='': state.get(name, default))
    owner = SimpleNamespace(op=lambda name: node if name == 'automation_json' else SimpleNamespace(module=transport))
    names = {'automation_data', '_cached_automation', '_imported_overrides', 'playback_values'}
    functions = [n for n in ast.parse(EDITOR_RUNTIME).body if isinstance(n, ast.FunctionDef) and n.name in names]
    scope = dict(json=json, automation=automation, OWNER=owner, _automation_cache={},
                 _state=lambda name, default='': state.get(name, default),
                 live_imported_values=lambda: {'mat_scale': 9})
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<automation playback>', 'exec'), scope)
    return scope, node, state, document


def test_playback_validates_once_and_reloads_changed_automation():
    scope, node, state, document = runtime()
    with patch.object(automation, 'validate', wraps=automation.validate) as validate:
        for _ in range(20):
            assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 2}
            assert scope['playback_values']('cue', 10) == {'mat_scale': 3, 'speed': 1}
        assert validate.call_count == 1
        document['edits'] = {'cue': {'mat_scale': {'points': [[0, 7]], 'mode': 'linear'}}}
        node.text = json.dumps(document)
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 7}
        assert validate.call_count == 2
        document['edits']['cue']['mat_scale']['enabled'] = False
        node.text = json.dumps(document)
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 2}
        assert validate.call_count == 3
        node.text = 'broken JSON'
        assert scope['_imported_overrides']('a', 'cue') == {}
        node.text = json.dumps(document)
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 2}


def test_recording_and_slot_scope_bypass_cache_without_stale_values():
    scope, node, state, document = runtime()
    with patch.object(automation, 'validate', wraps=automation.validate) as validate:
        assert scope['_imported_overrides']('b', 'cue') == {}
        state['recording'] = '1'
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 9}
        assert validate.call_count == 0
        state['recording'] = '0'
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 2}
        state['elapsed'] = '10'
        assert scope['_imported_overrides']('a', 'cue') == {'mat_scale': 3}
        assert validate.call_count == 1


def test_edit_reads_and_playback_results_remain_independently_mutable():
    scope, node, state, document = runtime()
    cached = scope['_cached_automation']()
    edit = scope['automation_data']()
    edit['tracks']['cue']['mat_scale'][0][1] = 100
    assert cached['tracks']['cue']['mat_scale'][0][1] == 1
    result = scope['playback_values']('cue', 5)
    result['mat_scale'] = 999
    assert scope['playback_values']('cue', 5)['mat_scale'] == 2
