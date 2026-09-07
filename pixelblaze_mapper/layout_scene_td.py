"""Draft editor UI with an optional explicitly gated active-apply boundary.

Callbacks receive the editor owner explicitly. The separately installed apply
runtime owns active transactions. No sender is enabled or stopped by this UI.
"""
from dataclasses import replace
import hashlib
import json
from math import cos, radians, sin
from pathlib import Path

from .layout_scene import Scene, SceneError, Transform, import_scan, export_pixelblaze_3d, new_id
from .layout_scene_adapter import (
    LayoutDocument, LayoutEditor, document_json, load_document_json,
    object_color, parse_indices, nudge, user_to_td,
)

PALETTE_VERSION = 1


def editor(owner):
    from .layout_scene_adapter import LayoutEditor
    from .layout_session_storage import LAYOUT_KEY, layout_snapshot, restore_layout, persist_layout
    value = owner.fetch("layout_editor_session", None)
    if value is not None and type(value) is not LayoutEditor:
        value = restore_layout(layout_snapshot(value))
        owner.store("layout_drag", None)
        owner.store("ui_prepared_context", None)
        owner.store("layout_editor_session", value)
        persist_layout(owner, value)
    elif value is None:
        saved = owner.op("draft_document")
        durable = owner.fetch(LAYOUT_KEY, None)
        value = restore_layout(durable) if durable is not None else LayoutEditor(load_document_json(saved.text) if saved is not None and saved.text.strip() else None)
        persist_layout(owner, value)
        owner.store("layout_editor_session", value)
    return value


def field(owner, name):
    node = owner.op("ui_panel/" + name + "/string")
    return str(node[0, 0]).strip() if node is not None and node.numRows else ""


def write_field(owner, name, value):
    node = owner.op("ui_panel/" + name + "/string")
    if node is not None:
        node.text = str(value)


def status(owner, message):
    owner.op("ui_panel/status").par.text = str(message)


def active_hash(owner):
    """Observed read-only baseline, not a claim that a root transaction is wired."""
    paths = (
        "/project1/pixelblaze_mapper/map_active",
        "/project1/pixelblaze_mapper/effect_panel_uv",
        "/project1/multi_controller_output/controller_config",
        "/project1/multi_controller_output/segment_config",
    )
    snapshots = {}
    for path in paths:
        node = owner.op(path)
        snapshots[path] = node.text if node is not None else None
    if snapshots[paths[0]] is None:
        raise SceneError("active map not found; preparation needs a verified baseline")
    return hashlib.sha256(json.dumps(snapshots, sort_keys=True).encode("utf-8")).hexdigest()


def refresh(owner, *, fields=True, save=True):
    session = editor(owner)
    from .layout_session_storage import persist_layout, serialized
    persist_layout(owner, session)
    scene = session.display_scene
    if save:
        text = serialized("document", session.current)
        if owner.op("draft_document").text != text:
            owner.op("draft_document").text = text
    menu_lines = []
    for index, obj in enumerate(scene.objects):
        sources = [v.source_index for v in obj.leds]
        marker = ">" if obj.object_id == session.selected_object_id else " "
        menu_lines.append(f"{marker} {index + 1}. {obj.name} | {len(sources)} LEDs | source {min(sources)}..{max(sources)} | {obj.object_id[:8]}")
    owner.op("ui_panel/objects").par.text = "\n".join(menu_lines) or "No objects. Load a current layout file or append a scan."
    owner.op("ui_panel/draft_badge").par.text = f"DRAFT WORKSPACE | {len(scene.objects)} objects | {sum(len(o.leds) for o in scene.objects)} LEDs | ACTIVE CHANGES REQUIRE SEPARATE APPLY"
    if session.selected_object_id:
        obj = scene.object(session.selected_object_id)
        scans = {s.scan_id: s for s in scene.scans}
        used = tuple(dict.fromkeys(v.scan_id for v in obj.leds))
        owner.op("ui_panel/provenance").par.text = "\n".join(
            f"{scans[id].name} | {scans[id].source_format} | scan {id[:12]} | missing {len(scans[id].missing_indices)}"
            for id in used
        )
        if fields:
            for prefix, values in (("t", obj.transform.translation), ("r", obj.transform.rotation_degrees), ("s", obj.transform.scale)):
                for axis, value in zip("xyz", values):
                    write_field(owner, prefix + axis, f"{value:.6g}")
            write_field(owner, "objectno", next(i + 1 for i, o in enumerate(scene.objects) if o.object_id == obj.object_id))
            route = next((r for r in session.current.routes if r.object_id == obj.object_id), None)
            write_field(owner, "controller", route.controller if route else "")
            write_field(owner, "port", route.port if route else "1")
    else:
        owner.op("ui_panel/provenance").par.text = "Original scans stay immutable; transformations affect this draft only."
    if fields:
        write_field(owner, "expectedcount", "" if scene.expected_count is None else scene.expected_count)
    owner.op("instances").cook(force=True)
    if owner.op("fixture_document") is not None:
        from . import layout_fixture_td
        layout_fixture_td.refresh(owner, save=save)


def cook_instances(owner, script_op):
    session = editor(owner)
    scene = session.display_scene
    colors = {o.object_id: object_color(o.object_id) for o in scene.objects}
    binding_object = {led.led_id: obj.object_id for obj in scene.objects for led in obj.leds}
    missing = {scan.scan_id: set(scan.missing_indices) for scan in scene.scans}
    points = scene.world_points()
    script_op.clear()
    script_op.numSamples = max(1, len(points))
    arrays = {name: [] for name in ("tx", "ty", "tz", "r", "g", "b", "a")}
    for led, point in points:
        xyz = user_to_td(point)
        color = colors[binding_object[led.led_id]]
        if binding_object[led.led_id] == session.selected_object_id:
            color = tuple(min(1, c * 1.2) for c in color)
        for name, value in zip(arrays, (*xyz, *color, 0.0 if led.scan_index in missing[led.scan_id] else 1.0)):
            arrays[name].append(value)
    for name, values in arrays.items():
        script_op.appendChan(name).vals = values or [0.0]


def frame_view(owner, *, reset=False):
    points = [user_to_td(p) for _, p in editor(owner).display_scene.world_points()]
    if points:
        lo = [min(p[a] for p in points) for a in range(3)]
        hi = [max(p[a] for p in points) for a in range(3)]
        center = tuple((a + b) / 2 for a, b in zip(lo, hi))
        span = max(hi[a] - lo[a] for a in range(3)) or 1.0
    else:
        center, span = (0.0, 0.0, 0.0), 1.0
    owner.store("view_center", center)
    owner.store("view_span", span)
    if reset:
        owner.store("view_angles", (25.0, 15.0))
    _camera(owner)


def _camera(owner):
    center = owner.fetch("view_center", (0, 0, 0))
    span = owner.fetch("view_span", 1.0)
    yaw, pitch = map(radians, owner.fetch("view_angles", (25, 15)))
    distance = span * 2.5
    camera = owner.op("camera")
    camera.par.tx = center[0] + distance * sin(yaw) * cos(pitch)
    camera.par.ty = center[1] + distance * sin(pitch)
    camera.par.tz = center[2] + distance * cos(yaw) * cos(pitch)
    target = owner.op("camera_target")
    target.par.tx, target.par.ty, target.par.tz = center
    camera.par.lookat = target.path
    shape = owner.op("led_geometry/led_shape")
    for axis in "xyz":
        getattr(shape.par, "size" + axis).val = span * 0.007


def _transform_fields(owner):
    obj = editor(owner).current.scene.object(editor(owner).selected_object_id)
    return Transform(
        translation=tuple(float(field(owner, "t" + a)) for a in "xyz"),
        rotation_degrees=tuple(float(field(owner, "r" + a)) for a in "xyz"),
        scale=tuple(float(field(owner, "s" + a)) for a in "xyz"), pivot=obj.transform.pivot,
    )


def active_action(owner, name, confirm):
    """Only this explicit boundary can invoke the reviewed active transaction."""
    runtime = owner.op("/project1/layout_apply/runtime")
    if runtime is None or any(not callable(getattr(runtime.module, method, None)) for method in ("prepare", "apply", "revert")):
        raise SceneError("Active apply runtime is not installed; export remains available. Ask for the reviewed layout-apply builder.")
    if editor(owner).display_scene != editor(owner).current.scene or owner.fetch("fixture_preview", None) is not None:
        raise SceneError("Finish or cancel the current drag before preparing/applying")
    mode = owner.fetch("layout_view", "3d")
    projection = (field(owner, "projection") or "YX").upper()
    if name in ("prepare", "apply") and field(owner, "preserverouting").upper() != "YES":
        raise SceneError("Type YES in Keep live routing. Draft controller/port bindings will NOT be applied.")
    if name == "prepare":
        owner.store("ui_prepared_context", None)
        if not confirm("Prepare " + mode.upper() + " using projection " + projection + "? Output must already be OFF. Preserve existing live routing; all draft controller/port bindings are ignored. Nothing is activated yet."):
            return
        plan = runtime.module.prepare(mode=mode, projection=projection, preserve_routing=True)
        owner.store("ui_prepared_context", (mode, projection, plan.workspace_revision))
        status(owner, "PREPARED " + mode.upper() + " | output OFF required | live routing preserved; draft routes NOT applied | click APPLY separately")
    elif name == "apply":
        context = owner.fetch("ui_prepared_context", None)
        if context is None or context[:2] != (mode, projection):
            raise SceneError("Prepare this tab and projection first; selection changed or no reviewed plan exists")
        impact = "physical XYZ + explicit projected UV" if mode == "3d" else "material UV + separate fixture-output representation; physical XYZ preserved"
        if not confirm("APPLY prepared " + mode.upper() + " now: " + impact + ". Output must stay OFF. Existing live routing is preserved; draft routing is NOT applied. Continue?"):
            return
        runtime.module.apply()
        owner.store("ui_prepared_context", None)
        status(owner, "APPLIED " + mode.upper() + " | output stays OFF | live routing preserved; draft routes NOT applied | REVERT LAST available while active state is unchanged")
    elif name == "revert":
        if not confirm("Revert the last active layout apply? Output must already be OFF. Only the unchanged last active transaction can be restored; draft workspace is retained."):
            return
        runtime.module.revert()
        owner.store("ui_prepared_context", None)
        status(owner, "LAST APPLY REVERTED | output stays OFF | draft workspace retained")
    else:
        raise SceneError("unknown active action")


def action(owner, name, chooser, confirm):
    """Draft actions plus three explicit optional active-transaction actions."""
    session = editor(owner)
    notice = None
    try:
        from . import layout_fixture_td
        if name in ("prepare", "apply", "revert"):
            return active_action(owner, name, confirm)
        if name in ("view3d", "view2d", "project2d", "fituv", "exportuv"):
            return layout_fixture_td.action(owner, name, chooser, confirm)
        if owner.fetch("layout_view", "3d") == "2d" and name in ("undo", "redo", "frame"):
            if name == "frame":
                layout_fixture_td.frame_output(owner)
            else:
                getattr(layout_fixture_td.history(owner), name)()
                owner.store("fixture_preview", None)
            layout_fixture_td.refresh(owner)
            status(owner, "2D " + name.upper() + " | 3D unchanged")
            return
        if name == "transform" and owner.fetch("layout_view", "3d") == "2d":
            raise SceneError("3D numeric transforms are only enabled in the 3D tab")
        if name in ("loadcurrent", "openscene", "loadactive"):
            if session.current.scene.objects and not confirm("Replace this draft? Export it first to keep a copy. Active LEDs stay unchanged."):
                return
            fixtures = None
            if name == "loadactive":
                from .layout_active_snapshot import read_active_snapshot
                document, warnings = read_active_snapshot(owner)
                notice = "ACTIVE SNAPSHOT LOADED TO DRAFT | " + str(document.scene.expected_count) + " LEDs | " + ("; ".join(warnings) if warnings else "valid disjoint source-route groups; live state unchanged")
            else:
                path = field(owner, "initialfile") if name == "loadcurrent" else chooser(load=True, title="Open layout scene", fileTypes=["json"])
                if not path:
                    return
                path = Path(path)
                if name == "openscene":
                    from .layout_workspace import import_workspace
                    document, fixtures = import_workspace(path.read_text(encoding="utf-8-sig"))
                else:
                    format = "marimapper-csv" if path.suffix.lower() == ".csv" else "pixelblaze"
                    scan = import_scan(path, format=format, name=path.name)
                    fresh = LayoutEditor(LayoutDocument(Scene(new_id(), path.stem)))
                    fresh.append(scan, source_start=0, name=path.stem)
                    document = fresh.current
            session.load_document(document)
            owner.store("ui_prepared_context", None)
            from .fixture_scene import FixtureHistory, FixtureScene
            from .layout_scene_adapter import scene_revision
            source = document.scene
            owner.store("fixture_history", FixtureHistory(fixtures or FixtureScene(source.scene_id, scene_revision(source), (), source.expected_count if source.expected_count is not None else sum(len(o.leds) for o in source.objects))))
            owner.store("fixture_preview", None)
            layout_fixture_td.frame_output(owner)
            frame_view(owner, reset=True)
        elif name in ("append", "replace"):
            format = field(owner, "format") or "pixelblaze"
            path = chooser(load=True, title="Open scan (original coordinates preserved)", fileTypes=["json", "csv", "js", "map"])
            if not path:
                return
            scan = import_scan(Path(path), format=format, name=field(owner, "objectname") or Path(path).name)
            chosen = parse_indices(field(owner, "scanrange")) or None
            if name == "append":
                session.append(scan, source_start=int(field(owner, "sourcestart")), scan_indices=chosen)
            else:
                if not confirm("Partial rescan must already share this object's original coordinate frame. IDs and other LEDs stay unchanged. Continue?"):
                    return
                session.replace_selected(parse_indices(field(owner, "localrange")), scan, scan_indices=chosen)
            frame_view(owner)
        elif name == "select":
            index = int(field(owner, "objectno")) - 1
            if not 0 <= index < len(session.current.scene.objects):
                raise SceneError("object number is out of range")
            session.select(session.current.scene.objects[index].object_id)
        elif name == "transform":
            session.transform(_transform_fields(owner))
        elif name == "route":
            session.bind_route(field(owner, "controller"), int(field(owner, "port")))
        elif name == "count":
            value = field(owner, "expectedcount")
            session.commit(replace(session.current, scene=replace(session.current.scene, expected_count=int(value) if value else None)))
        elif name == "undo":
            session.undo()
        elif name == "redo":
            session.redo()
        elif name == "frame":
            frame_view(owner, reset=True)
        elif name in ("exportscene", "exportpb"):
            from .layout_workspace import export_workspace
            text = export_workspace(session.current, layout_fixture_td.history(owner).current) if name == "exportscene" else export_pixelblaze_3d(session.current.scene)
            path = chooser(load=False, title="Export draft scene" if name == "exportscene" else "Export 3D Pixelblaze array (keep scene JSON for IDs)", fileTypes=["json"])
            if not path:
                return
            target = Path(path)
            if target.exists() and not confirm("Overwrite selected export file? Active LEDs remain unchanged."):
                return
            temporary = target.with_name(target.name + ".layout-tmp")
            if temporary.exists():
                raise SceneError("temporary export file already exists; choose a different target")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
        elif name == "scan":
            target = owner.op("/project1/guided_scan/ui_panel")
            if target is None:
                raise SceneError("Guided scan UI is not installed yet; run its isolated builder after review")
            runtime = owner.op("/project1/guided_scan/runtime")
            if runtime is not None and hasattr(runtime.module, "stage_scene"):
                runtime.module.stage_scene(session.current.scene, session.selected_object_id)
            target.openViewer()
        elif name.startswith("mode_"):
            write_field(owner, "mode", name[5:])
        else:
            raise SceneError("unknown editor action: " + name)
        refresh(owner)
        status(owner, notice or name.upper() + " | draft only; active map and outputs unchanged")
    except Exception as error:
        status(owner, "BLOCKED — " + str(error))


def drag(owner, phase, *, camera=False):
    session = editor(owner)
    viewport = owner.op("ui_panel/viewport")
    uv = (float(viewport.panel.u), float(viewport.panel.v))
    try:
        if phase == "start":
            start_transform = session.current.scene.object(session.selected_object_id).transform if session.selected_object_id else Transform()
            owner.store("layout_drag", (uv, start_transform, owner.fetch("view_angles", (25, 15))))
        elif phase == "update":
            start = owner.fetch("layout_drag", None)
            if start is None:
                return
            first, transform, angles = start
            du, dv = uv[0] - first[0], uv[1] - first[1]
            if camera:
                owner.store("view_angles", (angles[0] + du * 180, max(-85, min(85, angles[1] + dv * 180))))
                _camera(owner)
                return
            mode, axis = field(owner, "mode") or "move", field(owner, "axis") or "z"
            if mode == "move":
                # Explicit user XY plane, independent of camera orientation.
                span = owner.fetch("view_span", 1.0)
                x, y, z = transform.translation
                updated = replace(transform, translation=(x + dv * span, y + du * span, z))
            else:
                updated = nudge(transform, "right" if du + dv >= 0 else "left", mode=mode,
                                axis=axis, step=max(1e-12, abs(du + dv)) * (180 if mode == "rotate" else 2))
            session.transform(updated, preview=True)
            refresh(owner, fields=False, save=False)
        elif phase == "end":
            if not camera:
                session.finish_gesture()
                refresh(owner)
            owner.store("layout_drag", None)
    except Exception as error:
        session.cancel_gesture()
        owner.store("layout_drag", None)
        refresh(owner, fields=False, save=False)
        status(owner, "DRAG BLOCKED — " + str(error))


def key(owner, key_name, ctrl=False):
    session = editor(owner)
    key_name = str(key_name).lower()
    if owner.fetch("layout_view", "3d") == "2d":
        from .layout_fixture_td import key as fixture_key
        return fixture_key(owner, key_name, ctrl=ctrl)
    try:
        if key_name == "escape":
            session.cancel_gesture()
            owner.store("layout_drag", None)
        elif ctrl and key_name == "z":
            session.undo()
        elif ctrl and key_name == "y":
            session.redo()
        elif not ctrl and key_name in {"up", "down", "left", "right", "pageup", "pagedown"}:
            obj = session.current.scene.object(session.selected_object_id)
            session.transform(nudge(obj.transform, key_name, mode=field(owner, "mode") or "move",
                                    axis=field(owner, "axis") or "z", step=float(field(owner, "step") or "0.01")))
        refresh(owner)
    except Exception as error:
        status(owner, "KEY BLOCKED — " + str(error))
