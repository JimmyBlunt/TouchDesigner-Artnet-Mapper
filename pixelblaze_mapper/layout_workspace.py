"""Pure lossless editor workspace codec, including both fixture domains."""
import json

from .fixture_scene import import_fixture_json, export_fixture_json
from .layout_scene import SceneError
from .layout_scene_adapter import document_json, load_document_json


def export_workspace(document, fixtures):
    return json.dumps({"schema": "pixelblaze-layout-workspace", "version": 1,
                       "layout": json.loads(document_json(document)),
                       "fixtures": json.loads(export_fixture_json(fixtures))}, indent=2, allow_nan=False)


def import_workspace(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SceneError("duplicate workspace JSON key: " + key)
            result[key] = value
        return result
    try:
        data = json.loads(text, object_pairs_hook=unique)
        if not isinstance(data, dict) or data.get("schema") != "pixelblaze-layout-workspace":
            return load_document_json(text), None
        if data.get("version") != 1 or set(data) != {"schema", "version", "layout", "fixtures"}:
            raise SceneError("unsupported workspace schema/version/fields")
        document = load_document_json(json.dumps(data["layout"]))
        fixtures = import_fixture_json(json.dumps(data["fixtures"]))
        # Stale fixtures are deliberately round-trippable but cannot be exported
        # as sampling UV until their source scene passes validation.
        return document, fixtures
    except (TypeError, KeyError, json.JSONDecodeError) as error:
        raise SceneError("malformed workspace document") from error
