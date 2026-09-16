"""Save-safe plain-data layout histories; runtime classes are never TOE state.

TD's live OP.store docstring explicitly documents storeStartupValue as alternate
save/load storage. Verified read-only 2026-09-07. No calls here save a project.
"""
import json
from math import isfinite
from dataclasses import fields
import weakref

from .layout_scene import SceneError

# Audit 2026-09-16: the durable snapshot carried the complete undo stack, each
# entry a full copy of the ~9.3 MB layout document. Measured on the live system:
# 160,303,985 characters (152.9 MB) in TouchDesigner storage, re-encoded on every
# project save and decoded again on every load - the 82 s cold cook of
# layout_scene_editor/instances. The live editor keeps its full history in memory
# for the session; this only caps how much of it survives a reload.
# Set to 0 to persist no history at all, or raise it to trade start-up time for
# undo depth across restarts.
PERSISTED_HISTORY_DEPTH = 2


def _persisted_tail(entries):
    """Keep the entries nearest to `current`, so the restored timeline stays contiguous."""
    entries = list(entries)
    if PERSISTED_HISTORY_DEPTH <= 0:
        return []
    return entries[-PERSISTED_HISTORY_DEPTH:]


LAYOUT_KEY = "layout_session_snapshot"
FIXTURE_KEY = "fixture_session_snapshot"
TRANSIENT_KEYS = ("layout_editor_session", "fixture_history", "fixture_preview",
                  "layout_drag", "fixture_drag", "ui_prepared_context")

# Cache strings, never mutable decoded dictionaries shared with durable storage.
# Weak model refs make identity keys safe against id reuse and release discarded
# history entries. These module globals are not saved in TouchDesigner storage.
_SERIALIZED = {}


def clear_serialization_cache():
    _SERIALIZED.clear()


def _deeply_immutable(value, approved):
    if value is None or type(value) in (str, int, bool):
        return True
    if type(value) is float:
        return isfinite(value)
    if type(value) is tuple:
        return all(_deeply_immutable(item, approved) for item in value)
    if type(value) in approved and value.__dataclass_params__.frozen:
        return all(_deeply_immutable(getattr(value, item.name), approved) for item in fields(value))
    return False


def _encode_uncached(kind, value):
    if kind == "document":
        from .layout_scene_adapter import document_json
        return document_json(value)
    if kind == "scene":
        from .layout_scene import export_scene_json
        return export_scene_json(value)
    if kind == "fixture":
        from .fixture_scene import export_fixture_json
        return export_fixture_json(value)
    raise SceneError("Unknown serialization cache kind")


def serialized(kind, value, *, force=False):
    """Reuse only validated frozen model identities; old reload classes bypass.

    Models must be changed through their frozen-model replace/commit APIs.
    Deliberate object.__setattr__ mutation of frozen records is unsupported.
    """
    from .layout_scene import Scene, Scan, SceneObject, LedBinding, Transform
    from .layout_scene_adapter import LayoutDocument, RouteBinding
    from .fixture_scene import FixtureScene, Fixture, Transform2D
    generation = (Scene, Scan, SceneObject, LedBinding, Transform, LayoutDocument, RouteBinding,
                  FixtureScene, Fixture, Transform2D)
    key = (kind, id(value))
    cached = _SERIALIZED.get(key)
    # Constant-size generation check precedes every hit, including a reload of
    # only a nested model module while the outer document class stays current.
    if cached is not None and cached[2] != generation:
        _SERIALIZED.pop(key, None)
        cached = None
    if not force and cached is not None and cached[0]() is value:
        return cached[1]
    approved = set(generation)
    cacheable = _deeply_immutable(value, approved)
    text = _encode_uncached(kind, value)
    if cacheable:
        def discard(ref):
            entry = _SERIALIZED.get(key)
            if entry is not None and entry[0] is ref:
                _SERIALIZED.pop(key, None)
        _SERIALIZED[key] = (weakref.ref(value, discard), text, generation)
    return text


def _plain(value):
    return json.loads(json.dumps(value, allow_nan=False))


def layout_snapshot(editor, *, force=False):
    # Duck-type old module instances: reload makes isinstance unsafe, but their
    # immutable dataclass data is still serializable without pickling the class.
    encode = lambda document: serialized("document", document, force=force)
    return {"schema": "pixelblaze-layout-session", "version": 2,
            "current": encode(editor.current), "undo": [encode(v) for v in _persisted_tail(editor._undo)],
            "redo": [encode(v) for v in _persisted_tail(editor._redo)], "selected_object_id": editor.selected_object_id,
            "preview": serialized("scene", editor.preview, force=force) if editor.preview is not None else None}


def restore_layout(data):
    from .layout_scene_adapter import LayoutEditor, LayoutDocument, load_document_json
    from .layout_scene import SceneHistory, import_scene_json
    if not isinstance(data, dict) or set(data) != {"schema", "version", "current", "undo", "redo", "selected_object_id", "preview"} or data["schema"] != "pixelblaze-layout-session" or type(data["version"]) is not int or data["version"] not in (1, 2):
        raise SceneError("Unsupported durable layout-session snapshot")
    def source(value):
        if data["version"] == 2:
            if not isinstance(value, str):
                raise SceneError("Version 2 layout entries require immutable JSON text")
            return value
        return json.dumps(value, allow_nan=False)
    decode = lambda value: load_document_json(source(value))
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
        result.commit(LayoutDocument(import_scene_json(source(data["preview"])), current.routes))
    result.prepared = None
    return result


def fixture_snapshot(history, preview=None, *, force=False):
    encode = lambda scene: serialized("fixture", scene, force=force)
    return {"schema": "pixelblaze-fixture-session", "version": 2,
            "current": encode(history.current), "undo": [encode(v) for v in _persisted_tail(history._undo)],
            "redo": [encode(v) for v in _persisted_tail(history._redo)], "preview": encode(preview) if preview is not None else None}


def restore_fixtures(data):
    from .fixture_scene import FixtureHistory, import_fixture_json
    if not isinstance(data, dict) or set(data) != {"schema", "version", "current", "undo", "redo", "preview"} or data["schema"] != "pixelblaze-fixture-session" or type(data["version"]) is not int or data["version"] not in (1, 2):
        raise SceneError("Unsupported durable fixture-session snapshot")
    def decode(value):
        if data["version"] == 2:
            if not isinstance(value, str):
                raise SceneError("Version 2 fixture entries require immutable JSON text")
            return import_fixture_json(value)
        return import_fixture_json(json.dumps(value, allow_nan=False))
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


def persist_layout(owner, editor, *, force=False):
    data = layout_snapshot(editor, force=force)
    if force or owner.fetch(LAYOUT_KEY, None) != data:
        owner.store(LAYOUT_KEY, data)
    _startup_none(owner, ("layout_editor_session", "layout_drag", "ui_prepared_context"))
    return data


def persist_fixtures(owner, history, preview=None, *, force=False):
    data = fixture_snapshot(history, preview, force=force)
    if force or owner.fetch(FIXTURE_KEY, None) != data:
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
    # Build both complete candidates before publishing either durable snapshot.
    # A serialization failure must not replace just one side of the workspace.
    layout = layout_snapshot(editor(owner), force=True)
    fixtures = fixture_snapshot(history(owner), owner.fetch("fixture_preview", None), force=True)
    if not callable(getattr(owner, "storeStartupValue", None)):
        raise SceneError("TouchDesigner storeStartupValue is required for safe session storage")
    owner.store(LAYOUT_KEY, layout)
    owner.store(FIXTURE_KEY, fixtures)
    _startup_none(owner, TRANSIENT_KEYS)
    return _plain({"schema": "pixelblaze-layout-save-manifest", "version": 1,
                   "scene_id": json.loads(layout["current"])["scene"]["scene_id"],
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
