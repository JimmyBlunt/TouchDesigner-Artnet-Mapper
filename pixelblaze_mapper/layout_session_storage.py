"""Save-safe plain-data layout histories; runtime classes are never TOE state.

TD's live OP.store docstring explicitly documents storeStartupValue as alternate
save/load storage. Verified read-only 2026-09-07. No calls here save a project.
"""
import json
from math import isfinite

from .layout_scene import SceneError

LAYOUT_KEY = "layout_session_snapshot"
FIXTURE_KEY = "fixture_session_snapshot"
TRANSIENT_KEYS = ("layout_editor_session", "fixture_history", "fixture_preview",
                  "layout_drag", "fixture_drag", "ui_prepared_context")


def _plain(value):
    return json.loads(json.dumps(value, allow_nan=False))


def layout_snapshot(editor):
    # Duck-type old module instances: reload makes isinstance unsafe, but their
    # immutable dataclass data is still serializable without pickling the class.
    from .layout_scene_adapter import document_json
    from .layout_scene import export_scene_json
    encode = lambda document: json.loads(document_json(document))
    return {"schema": "pixelblaze-layout-session", "version": 1,
            "current": encode(editor.current), "undo": [encode(v) for v in editor._undo],
            "redo": [encode(v) for v in editor._redo], "selected_object_id": editor.selected_object_id,
            "preview": json.loads(export_scene_json(editor.preview)) if editor.preview is not None else None}


def restore_layout(data):
    from .layout_scene_adapter import LayoutEditor, LayoutDocument, load_document_json
    from .layout_scene import SceneHistory, import_scene_json
    if not isinstance(data, dict) or set(data) != {"schema", "version", "current", "undo", "redo", "selected_object_id", "preview"} or data["schema"] != "pixelblaze-layout-session" or type(data["version"]) is not int or data["version"] != 1:
        raise SceneError("Unsupported durable layout-session snapshot")
    decode = lambda value: load_document_json(json.dumps(value, allow_nan=False))
    current = decode(data["current"])
    undo, redo = [decode(v) for v in data["undo"]], [decode(v) for v in data["redo"]]
    timeline = undo + [current] + list(reversed(redo))
    for before, after in zip(timeline, timeline[1:]):
        SceneHistory(before.scene).commit(after.scene)
    result = LayoutEditor(current)
    result._undo, result._redo = undo, redo
    selected = data["selected_object_id"]
    if selected is not None:
        current.scene.object(selected)
    result.selected_object_id = selected
    if data["preview"] is not None:
        # Recover the visible in-progress gesture as one undoable draft change;
        # never resume mouse-down state or activate any output after reopening.
        result.commit(LayoutDocument(import_scene_json(json.dumps(data["preview"])), current.routes))
    result.prepared = None
    return result


def fixture_snapshot(history, preview=None):
    from .fixture_scene import export_fixture_json
    encode = lambda scene: json.loads(export_fixture_json(scene))
    return {"schema": "pixelblaze-fixture-session", "version": 1,
            "current": encode(history.current), "undo": [encode(v) for v in history._undo],
            "redo": [encode(v) for v in history._redo], "preview": encode(preview) if preview is not None else None}


def restore_fixtures(data):
    from .fixture_scene import FixtureHistory, import_fixture_json
    if not isinstance(data, dict) or set(data) != {"schema", "version", "current", "undo", "redo", "preview"} or data["schema"] != "pixelblaze-fixture-session" or type(data["version"]) is not int or data["version"] != 1:
        raise SceneError("Unsupported durable fixture-session snapshot")
    decode = lambda value: import_fixture_json(json.dumps(value, allow_nan=False))
    current = decode(data["current"])
    undo, redo = [decode(v) for v in data["undo"]], [decode(v) for v in data["redo"]]
    timeline = undo + [current] + list(reversed(redo))
    for before, after in zip(timeline, timeline[1:]):
        FixtureHistory(before).commit(after)
    result = FixtureHistory(current)
    result._undo, result._redo = undo, redo
    if data["preview"] is not None:
        result.commit(decode(data["preview"]))
    return result


def _startup_none(owner, keys):
    # No silent fallback to saving unpickleable classes on a real TD owner.
    setter = getattr(owner, "storeStartupValue", None)
    if not callable(setter):
        raise SceneError("TouchDesigner storeStartupValue is required for safe session storage")
    for key in keys:
        setter(key, None)


def persist_layout(owner, editor):
    data = layout_snapshot(editor)
    owner.store(LAYOUT_KEY, data)
    _startup_none(owner, ("layout_editor_session", "layout_drag", "ui_prepared_context"))
    return data


def persist_fixtures(owner, history, preview=None):
    data = fixture_snapshot(history, preview)
    owner.store(FIXTURE_KEY, data)
    _startup_none(owner, ("fixture_history", "fixture_preview", "fixture_drag"))
    return data


def prepare_save(owner):
    """Explicit root preflight hook: migrate old live instances before TOE save.

    Writes only this editor's plain snapshots/startup overrides; no live map,
    routing, sender, file or project-save calls. Returns a plain manifest.
    """
    from .layout_scene_td import editor
    from .layout_fixture_td import history
    # Getters also recover plain snapshots when runtime objects are absent.
    layout = persist_layout(owner, editor(owner))
    fixtures = persist_fixtures(owner, history(owner), owner.fetch("fixture_preview", None))
    _startup_none(owner, TRANSIENT_KEYS)
    return _plain({"schema": "pixelblaze-layout-save-manifest", "version": 1,
                   "scene_id": layout["current"]["scene"]["scene_id"],
                   "layout_undo": len(layout["undo"]), "layout_redo": len(layout["redo"]),
                   "fixture_undo": len(fixtures["undo"]), "fixture_redo": len(fixtures["redo"]),
                   "selected_object_id": layout["selected_object_id"],
                   "selected_fixture_id": owner.fetch("selected_fixture_id", None),
                   "transient_startup_none": TRANSIENT_KEYS,
                   "prepared_invalidated_on_reopen": True,
                   "preview_recovered_as_one_undo_step": layout["preview"] is not None or fixtures["preview"] is not None})


def _verify_plain(value, path="storage"):
    """Validate without changing tuple/list identity semantics used by Revert."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and isfinite(value):
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _verify_plain(item, path + "[" + str(index) + "]")
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for key, item in value.items():
            _verify_plain(item, path + "." + key)
        return
    raise SceneError("Non-primitive durable storage at " + path + ": " + type(value).__name__)


def prepare_apply_save(owner):
    """Prepared class plans expire on reopen; primitive Revert state survives."""
    snapshot = owner.fetch("last_snapshot", None)
    applied_hash = owner.fetch("last_applied_hash", None)
    _verify_plain(snapshot, "last_snapshot")
    _verify_plain(applied_hash, "last_applied_hash")
    if snapshot is not None and (not isinstance(applied_hash, str) or not applied_hash):
        raise SceneError("Last apply snapshot has no matching hash; refusing silent Revert loss")
    _startup_none(owner, ("prepared_plan", "prepared_workspace_key", "prepared_workspace_hash"))
    setter = getattr(owner, "storeStartupValue")
    setter("applying", False)
    return {"schema": "pixelblaze-layout-apply-save-manifest", "version": 1,
            "prepared_invalidated_on_reopen": True, "revert_snapshot_preserved": snapshot is not None,
            "last_applied_hash": applied_hash}
