"""Offline editor state, routing drafts and explicitly prepared handoffs.

No active TouchDesigner map or router is reachable here. An integrator must
provide every callback to apply a prepared transaction, including rollback.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from math import isfinite

from .layout_scene import (
    Scene, SceneError, SceneHistory, Scan, Transform, append_scan, set_transform,
    replace_region, export_scene_json, import_scene_json, export_pixelblaze_3d,
    new_id,
)


def scene_revision(scene: Scene) -> str:
    return hashlib.sha256(export_scene_json(scene, indent=None).encode("utf-8")).hexdigest()


def parse_indices(text: str) -> tuple[int, ...]:
    """Explicit inclusive selections, e.g. '0-10,20,25-30'; no inferred offset."""
    if not text.strip():
        return ()
    result = []
    for part in text.split(","):
        try:
            values = [int(v.strip()) for v in part.split("-")]
        except ValueError as exc:
            raise SceneError("range must look like 0-10,20,25-30") from exc
        if len(values) == 1 and values[0] >= 0:
            result.append(values[0])
        elif len(values) == 2 and 0 <= values[0] <= values[1]:
            if values[1] - values[0] > 1000000:
                raise SceneError("selection too large")
            result.extend(range(values[0], values[1] + 1))
        else:
            raise SceneError("indices must be non-negative ascending ranges")
    if len(set(result)) != len(result):
        raise SceneError("selection has duplicate/overlapping indices")
    return tuple(result)


@dataclass(frozen=True)
class RouteBinding:
    object_id: str
    controller: str
    port: int

    def __post_init__(self):
        if not isinstance(self.object_id, str) or not self.object_id.strip():
            raise SceneError("route requires an object ID")
        if not isinstance(self.controller, str) or not self.controller.strip() or self.controller != self.controller.strip():
            raise SceneError("route requires an explicit controller name")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or self.port < 1:
            raise SceneError("physical port must be a positive integer")


@dataclass(frozen=True)
class LayoutDocument:
    scene: Scene
    routes: tuple[RouteBinding, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "routes", tuple(self.routes))
        if not isinstance(self.scene, Scene):
            raise SceneError("document requires a scene")
        ids = {o.object_id for o in self.scene.objects}
        assigned = set()
        for route in self.routes:
            if not isinstance(route, RouteBinding) or route.object_id not in ids:
                raise SceneError("route references an unknown object")
            if route.object_id in assigned:
                raise SceneError("object has duplicate route bindings")
            assigned.add(route.object_id)


@dataclass(frozen=True)
class PreparedTransaction:
    scene_id: str
    draft_revision: str
    base_active_hash: str
    coordinates_json: str
    routes: tuple[RouteBinding, ...]
    changes_active_output: bool = False


def prepare_transaction(document: LayoutDocument, *, base_active_hash: str,
                        require_routes: bool = True) -> PreparedTransaction:
    """Validate a complete draft; does not apply, arm, or enable anything.

    Controller capability/port capacity/universe conflict validation belongs to
    the root router adapter. These bindings are explicit intent, not allocation.
    """
    if not isinstance(base_active_hash, str) or not base_active_hash.strip():
        raise SceneError("read and provide an active-state hash before preparing")
    if require_routes and {r.object_id for r in document.routes} != {o.object_id for o in document.scene.objects}:
        raise SceneError("each object needs an explicit controller/port binding")
    coordinates = export_pixelblaze_3d(document.scene)
    return PreparedTransaction(document.scene.scene_id, scene_revision(document.scene),
                               base_active_hash, coordinates, document.routes)


def apply_prepared(transaction: PreparedTransaction, *, document: LayoutDocument,
                   read_active_hash, capture_snapshot, write_coordinates,
                   write_routes, verify_applied, restore_snapshot) -> None:
    """Root-only injected atomic handoff; no callbacks are supplied by the UI.

    Snapshot must include every affected map/UV/route/status consumer. Writers
    MUST NOT enable output. Compare-and-snapshot should be protected by the root
    adapter's exclusive transaction lock; this function does not claim thread
    safety or ownership of a TouchDesigner frame. Rollback errors are surfaced.
    """
    if scene_revision(document.scene) != transaction.draft_revision or document.routes != transaction.routes:
        raise SceneError("prepared draft is stale")
    if transaction.coordinates_json != export_pixelblaze_3d(document.scene):
        raise SceneError("prepared coordinate payload differs from validated draft")
    if read_active_hash() != transaction.base_active_hash:
        raise SceneError("active state changed after preparation")
    snapshot = capture_snapshot()
    if read_active_hash() != transaction.base_active_hash:
        raise SceneError("active state changed during snapshot; no writers called")
    try:
        write_coordinates(transaction.coordinates_json)
        write_routes(transaction.routes)
        if verify_applied(transaction) is not True:
            raise SceneError("active transaction verification failed")
    except Exception as error:
        try:
            restore_snapshot(snapshot)
        except Exception as rollback_error:
            raise SceneError(f"apply failed: {error}; ROLLBACK FAILED: {rollback_error}") from rollback_error
        raise SceneError(f"apply rolled back: {error}") from error


class LayoutEditor:
    """Immutable document history plus non-persistent selection and drag preview."""
    def __init__(self, document: LayoutDocument | None = None):
        self._current = document or LayoutDocument(Scene(new_id(), "Room layout"))
        self._undo = []
        self._redo = []
        self.selected_object_id = self._current.scene.objects[0].object_id if self._current.scene.objects else None
        self.preview = None
        self.prepared = None

    @property
    def current(self):
        return self._current

    @property
    def display_scene(self):
        return self.preview or self.current.scene

    def select(self, object_id):
        self.current.scene.object(object_id)
        self.preview = None
        self.selected_object_id = object_id

    def commit(self, document):
        SceneHistory(self.current.scene).commit(document.scene)
        if document != self.current:
            self._undo.append(self.current)
            self._current = document
            self._redo.clear()
            self.prepared = None
        self.preview = None
        return self.current

    def load_document(self, document):
        """Explicit replacement of the editor document; not an active-map apply."""
        self._current = document
        self._undo.clear()
        self._redo.clear()
        self.preview = None
        self.prepared = None
        self.selected_object_id = document.scene.objects[0].object_id if document.scene.objects else None

    def append(self, scan, **kwargs):
        updated = append_scan(self.current.scene, scan, **kwargs)
        self.commit(replace(self.current, scene=updated))
        self.selected_object_id = updated.objects[-1].object_id

    def transform(self, transform, *, preview=False):
        if self.selected_object_id is None:
            raise SceneError("select an object first")
        updated = set_transform(self.current.scene, self.selected_object_id, transform)
        if preview:
            self.preview = updated
        else:
            self.commit(replace(self.current, scene=updated))

    def finish_gesture(self):
        if self.preview is not None:
            self.commit(replace(self.current, scene=self.preview))

    def cancel_gesture(self):
        self.preview = None

    def bind_route(self, controller, port):
        if self.selected_object_id is None:
            raise SceneError("select an object first")
        route = RouteBinding(self.selected_object_id, controller, port)
        routes = tuple(r for r in self.current.routes if r.object_id != route.object_id) + (route,)
        self.commit(replace(self.current, routes=routes))

    def replace_selected(self, local_indices, scan, *, scan_indices=None):
        updated = replace_region(self.current.scene, self.selected_object_id, local_indices,
                                 scan, scan_indices=scan_indices)
        self.commit(replace(self.current, scene=updated))

    def accept_scan_request(self, request, scan: Scan):
        """Commit a registered, quality-gated scan-session proposal as one edit."""
        if request.scene_id != self.current.scene.scene_id or request.expected_scene_revision != scene_revision(self.current.scene):
            raise SceneError("scan proposal belongs to another or stale layout")
        if request.scan_id != scan.scan_id:
            raise SceneError("scan proposal does not match candidate scan identity")
        if not request.registration_reference or not request.quality_reference:
            raise SceneError("scan proposal requires registration and quality evidence")
        if not request.replacements:
            raise SceneError("scan proposal contains no replacements")
        bindings = {v.led_id: (o.object_id, v.local_index, v.source_index)
                    for o in self.current.scene.objects for v in o.leds}
        for item in request.replacements:
            if bindings.get(item.led_id) != (item.object_id, item.local_index, item.source_index):
                raise SceneError("scan proposal changed a stable LED identity")
        updated = self.current.scene
        for object_id in dict.fromkeys(v.object_id for v in request.replacements):
            updated = replace_region(updated, scan=scan, **request.replacement_args(object_id))
        self.commit(replace(self.current, scene=updated))

    def undo(self):
        if self._undo:
            self._redo.append(self.current)
            self._current = self._undo.pop()
        self._reset_ephemeral()
        return self.current

    def redo(self):
        if self._redo:
            self._undo.append(self.current)
            self._current = self._redo.pop()
        self._reset_ephemeral()
        return self.current

    def _reset_ephemeral(self):
        self.preview = None
        self.prepared = None
        if self.selected_object_id not in {o.object_id for o in self.current.scene.objects}:
            self.selected_object_id = self.current.scene.objects[0].object_id if self.current.scene.objects else None


def document_json(document: LayoutDocument) -> str:
    """Editor envelope retains route intent alongside the lossless scene."""
    from dataclasses import asdict
    return json.dumps({"schema": "pixelblaze-layout-editor", "version": 1,
                       "scene": json.loads(export_scene_json(document.scene)),
                       "routes": [asdict(r) for r in document.routes]}, indent=2, allow_nan=False)


def load_document_json(text: str) -> LayoutDocument:
    try:
        value = json.loads(text)
        if value.get("schema") == "pixelblaze-layout-scene":
            return LayoutDocument(import_scene_json(text))
        if set(value) != {"schema", "version", "scene", "routes"} or value["schema"] != "pixelblaze-layout-editor" or type(value["version"]) is not int or value["version"] != 1:
            raise SceneError("unsupported editor document schema")
        scene = import_scene_json(json.dumps(value["scene"]))
        return LayoutDocument(scene, tuple(RouteBinding(**r) for r in value["routes"]))
    except (TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise SceneError(f"invalid editor document: {exc}") from exc


def user_to_td(point):
    """Display only: user X=height,Y=right,Z=back -> TD (Y,X,-Z)."""
    x, y, z = point
    return y, x, -z


def object_color(object_id):
    """Stable bright RGB from object identity; unaffected by append order."""
    digest = hashlib.sha256(object_id.encode("utf-8")).digest()
    return tuple(0.25 + b / 255 * 0.7 for b in digest[:3])


# TouchDesigner's keyboardIn DAT reports these keys as 'pgup', 'pgdn' and 'esc',
# while the direction vocabulary below uses the long spellings. Before the audit
# of 2026-09-16 the two never met: the keyboard node listed the long names, which
# TouchDesigner rejected as invalid, so Escape and the third-axis nudge were dead
# without any visible error. Accept both spellings so either side can change.
KEY_ALIASES = {"pgup": "pageup", "pgdn": "pagedown", "esc": "escape",
               "page_up": "pageup", "page_down": "pagedown"}


def canonical_key(name) -> str:
    """Normalise a key name to this module's vocabulary."""
    name = str(name).lower()
    return KEY_ALIASES.get(name, name)


def nudge(transform: Transform, key: str, *, mode="move", axis="z", step=0.01) -> Transform:
    if not isinstance(step, (int, float)) or isinstance(step, bool) or not isfinite(step) or step <= 0:
        raise SceneError("step must be positive")
    directions = {"up": (0, 1), "down": (0, -1), "left": (1, -1), "right": (1, 1),
                  "pageup": (2, 1), "pagedown": (2, -1)}
    if key not in directions:
        return transform
    coordinate, direction = directions[key]
    if mode == "move":
        values = list(transform.translation)
        values[coordinate] += direction * step
        return replace(transform, translation=tuple(values))
    if mode not in ("rotate", "scale") or axis not in ("x", "y", "z"):
        raise SceneError("choose move/rotate/scale and X/Y/Z axis")
    field = "rotation_degrees" if mode == "rotate" else "scale"
    values = list(getattr(transform, field))
    values["xyz".index(axis)] += direction * step
    return replace(transform, **{field: tuple(values)})
