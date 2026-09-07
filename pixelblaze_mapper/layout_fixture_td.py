"""Independent 2D fixture canvases; draft-only, never binds a live sampler."""
from dataclasses import replace
from pathlib import Path
import json

from .layout_scene import SceneError
from .layout_scene_adapter import object_color, scene_revision, parse_indices


def project_selection(scene, object_id, *, projection="YX", local_indices=None, fixture_id=None):
    """Explicit local subset; preserve original LED bindings and canonical order."""
    from .fixture_scene import project_fixture
    fixture = project_fixture(scene, object_id, projection=projection, fixture_id=fixture_id)
    if local_indices is None:
        return fixture
    indices = tuple(local_indices)
    if not indices or any(type(i) is not int or i < 0 for i in indices) or len(set(indices)) != len(indices):
        raise SceneError("2D local LED selection must be nonempty, unique nonnegative indices")
    wanted = set(indices)
    if not wanted <= {led.local_index for led in fixture.leds}:
        raise SceneError("2D local LED selection contains indices outside this object")
    pairs = [(led, point) for led, point in zip(fixture.leds, fixture.local_points) if led.local_index in wanted]
    ids = {led.led_id for led, _ in pairs}
    return replace(fixture, leds=tuple(led for led, _ in pairs), local_points=tuple(point for _, point in pairs),
                   missing_ids=tuple(id for id in fixture.missing_ids if id in ids))


def history(owner):
    from .fixture_scene import FixtureHistory, FixtureScene, import_fixture_json
    from .layout_session_storage import FIXTURE_KEY, fixture_snapshot, restore_fixtures, persist_fixtures
    from .layout_scene_td import editor
    value = owner.fetch("fixture_history", None)
    if value is not None and type(value) is not FixtureHistory:
        value = restore_fixtures(fixture_snapshot(value, owner.fetch("fixture_preview", None)))
        owner.store("fixture_drag", None)
        owner.store("fixture_preview", None)
        owner.store("fixture_history", value)
        persist_fixtures(owner, value)
    elif value is None:
        dat = owner.op("fixture_document")
        scene = editor(owner).current.scene
        source = import_fixture_json(dat.text) if dat is not None and dat.text.strip() else FixtureScene(scene.scene_id, scene_revision(scene), (), scene.expected_count if scene.expected_count is not None else sum(len(o.leds) for o in scene.objects))
        durable = owner.fetch(FIXTURE_KEY, None)
        value = restore_fixtures(durable) if durable is not None else FixtureHistory(source)
        persist_fixtures(owner, value)
        owner.store("fixture_history", value)
    return value


def current(owner):
    return owner.fetch("fixture_preview", None) or history(owner).current


def selected(owner):
    from .layout_scene_td import editor
    model = current(owner)
    id = owner.fetch("selected_fixture_id", None)
    if id and any(f.fixture_id == id and f.object_id == editor(owner).selected_object_id for f in model.fixtures):
        return model.fixture(id)
    matches = [f for f in model.fixtures if f.object_id == editor(owner).selected_object_id]
    if not matches:
        raise SceneError("project the selected object's 2D fixture first")
    return matches[0]


def frame_output(owner):
    points = [point for fixture in current(owner).fixtures for _, point in fixture.output_points()]
    if not points:
        bounds = (0.5, 0.5, 1.0)
    else:
        lo = [min(p[a] for p in points) for a in range(2)]
        hi = [max(p[a] for p in points) for a in range(2)]
        bounds = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, max(hi[0] - lo[0], hi[1] - lo[1], 1e-9) * 1.1)
    owner.store("fixture_output_frame", bounds)


def refresh(owner, *, save=True):
    from .fixture_scene import export_fixture_json
    from .layout_scene_td import editor
    model = current(owner)
    from .layout_session_storage import persist_fixtures, serialized
    persist_fixtures(owner, history(owner), owner.fetch("fixture_preview", None))
    if save:
        text = serialized("fixture", history(owner).current)
        if owner.op("fixture_document").text != text:
            owner.op("fixture_document").text = text
    for domain in ("output", "uv"):
        owner.op("fixture_" + domain + "_instances").cook(force=True)
    out_of_bounds = sum(not (0 <= p[0] <= 1 and 0 <= p[1] <= 1)
                        for f in model.fixtures for _, p in f.sample_uv())
    scene = editor(owner).current.scene
    stale = " | SOURCE GEOMETRY CHANGED: reproject only if intended" if model.scene_revision != scene_revision(scene) else ""
    owner.op("ui_panel/fixtures_uv/info").par.text = (
        f"MATERIAL UV ONLY | {out_of_bounds} samples outside0..1\n"
        "Drag changes sample placement, not fixture output or3D.\n"
        "Draft edits need separate Prepare / Apply." + stale)
    selection = next((f for f in model.fixtures if f.fixture_id == owner.fetch("selected_fixture_id", None)), None)
    selected_text = ("Selected " + selection.fixture_id[:8] + " | local " + str(min(l.local_index for l in selection.leds)) + ".." + str(max(l.local_index for l in selection.leds)) + " | " + str(len(selection.leds)) + " LEDs") if selection else "Click a fixture to select its exact stored range"
    owner.op("ui_panel/fixtures_output/info").par.text = (
        f"OUTPUT FIXTURE LAYOUT ONLY | {len(model.fixtures)} fixtures\n"
        + selected_text + "\n"
        "Drag changes output only, not material UV or 3D.\n"
        "LED IDs stay linked; routing remains draft intent.")


def cook(owner, script_op, domain):
    model = current(owner)
    center_u, center_v, span = owner.fetch("fixture_output_frame", (.5, .5, 1.0))
    arrays = {name: [] for name in ("tx", "ty", "tz", "r", "g", "b", "a")}
    for fixture in model.fixtures:
        points = fixture.output_points() if domain == "output" else fixture.sample_uv()
        color = object_color(fixture.object_id)
        for led, point in points:
            u, v = point
            if domain == "output":
                u, v = (u - center_u) / span + .5, (v - center_v) / span + .5
            alpha = 0 if led.led_id in fixture.missing_ids else 1
            for key, value in zip(arrays, (u, v, 0, *color, alpha)):
                arrays[key].append(value)
    script_op.clear()
    script_op.numSamples = max(1, len(arrays["tx"]))
    for key, values in arrays.items():
        script_op.appendChan(key).vals = values or [0.0]


def _commit(owner, scene):
    history(owner).commit(scene)
    owner.store("fixture_preview", None)
    refresh(owner)


def action(owner, name, chooser, confirm):
    from .fixture_scene import FixtureScene, FixtureHistory, Transform2D, add_fixture, replace_transform, export_sampling_uv
    from .layout_scene_td import editor, field, status
    model = current(owner)
    if name in ("view3d", "view2d"):
        mode = "2d" if name == "view2d" else "3d"
        owner.store("layout_view", mode)
        owner.op("ui_panel/viewport").par.display = mode == "3d"
        for domain in ("output", "uv"):
            owner.op("ui_panel/fixtures_" + domain).par.display = mode == "2d"
        owner.op("ui_panel/btn_transform").par.enable = mode == "3d"
        for prefix in "trs":
            for axis in "xyz":
                owner.op("ui_panel/" + prefix + axis).par.enable = mode == "3d"
        owner.op("ui_panel/axes").par.text = ("2D: click a colored fixture then drag, or use arrows. Mode selects move / rotate / scale.\nThe last clicked canvas receives keys. Ctrl+Z/Y affects only the 2D draft.\n3D numeric transforms are disabled here. UV square is exactly 0..1; FIT UV is explicit." if mode == "2d" else
            "USER AXES: X = HEIGHT | Y = RIGHT | Z = BACK\nLMB: selected object XY / chosen rotate-scale axis. RMB: orbit.\nViewport keys: arrows X/Y, Page Up/Down Z; Ctrl+Z/Y undo/redo; Escape cancels drag.")
        status(owner, ("2D FIXTURES | output arrangement and material UV are independent drafts" if mode == "2d" else "3D LAYOUT | X height/Y right/Z back | original scans preserved"))
        refresh(owner)
    elif name == "project2d":
        scene = editor(owner).current.scene
        object_id = editor(owner).selected_object_id
        indices = parse_indices(field(owner, "fixturerange")) or None
        fixture = project_selection(scene, object_id, projection=(field(owner, "projection") or "YX").upper(), local_indices=indices)
        stale = (model.scene_id, model.scene_revision) != (scene.scene_id, scene_revision(scene))
        if stale:
            if model.fixtures and not confirm("3D source changed. Start a fresh 2D workspace? This resets ALL fixture transforms. Export the workspace first to keep them."):
                return
            model = FixtureScene(scene.scene_id, scene_revision(scene), (), scene.expected_count if scene.expected_count is not None else sum(len(o.leds) for o in scene.objects))
        wanted = {led.local_index for led in fixture.leds}
        prior = next((f for f in model.fixtures if f.object_id == object_id and {led.local_index for led in f.leds} == wanted), None)
        if prior and not confirm("Reproject this exact fixture LED range and reset its two 2D transforms? Other fixtures and 3D stay unchanged."):
            return
        if prior:
            fixture = replace(fixture, fixture_id=prior.fixture_id)
            updated = replace(model, scene_revision=scene_revision(scene), fixtures=tuple(fixture if f.fixture_id == prior.fixture_id else f for f in model.fixtures))
        else:
            # FixtureScene validates duplicate LED/source/local ownership. No
            # existing range is trimmed, split or regrouped automatically.
            updated = add_fixture(replace(model, scene_revision=scene_revision(scene)), fixture)
        if prior or stale:
            # Explicit reprojection replaces frozen geometry, hence starts a new
            # history baseline after confirmation, never impersonates a transform.
            owner.store("fixture_history", FixtureHistory(updated))
            owner.store("fixture_preview", None)
        else:
            _commit(owner, updated)
        owner.store("selected_fixture_id", fixture.fixture_id)
        frame_output(owner)
        refresh(owner)
        action(owner, "view2d", chooser, confirm)
    elif name == "fituv":
        fixture = selected(owner)
        points = [p for led, p in zip(fixture.leds, fixture.local_points) if led.led_id not in fixture.missing_ids]
        if not points:
            raise SceneError("fixture has no valid points to fit")
        lo = [min(p[a] for p in points) for a in range(2)]
        hi = [max(p[a] for p in points) for a in range(2)]
        span = max(hi[0] - lo[0], hi[1] - lo[1]) or 1.0
        transform = Transform2D(translation=(.5 - (lo[0] + hi[0]) / (2 * span), .5 - (lo[1] + hi[1]) / (2 * span)), scale=(1 / span, 1 / span))
        _commit(owner, replace_transform(model, fixture.fixture_id, domain="uv", transform=transform))
        status(owner, "FIT MATERIAL UV | local shape contained in0..1 | output fixture and3D unchanged")
    elif name == "exportuv":
        source_scene = editor(owner).current.scene
        model.validate_source_scene(source_scene)
        model = replace(model, expected_count=source_scene.expected_count if source_scene.expected_count is not None else sum(len(o.leds) for o in source_scene.objects))
        text = export_sampling_uv(model, bounds="reject")
        path = chooser(load=False, title="Export dense sampling UV draft (does not bind output)", fileTypes=["json"])
        if path:
            target = Path(path)
            if target.exists() and not confirm("Overwrite selected sampling UV export?"):
                return
            temporary = target.with_name(target.name + ".layout-tmp")
            if temporary.exists():
                raise SceneError("temporary export exists; choose a different target")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
            status(owner, "SAMPLING UV EXPORTED | NOT connected to live sampler")


def _pick(owner, domain, uv):
    from .layout_scene_td import editor
    cx, cy, span = owner.fetch("fixture_output_frame", (.5, .5, 1.0))
    best = (.07, None)
    for fixture in current(owner).fixtures:
        for _, (u, v) in (fixture.output_points() if domain == "output" else fixture.sample_uv()):
            if domain == "output":
                u, v = (u - cx) / span + .5, (v - cy) / span + .5
            distance = ((u - uv[0]) ** 2 + (v - uv[1]) ** 2) ** .5
            if distance < best[0]:
                best = distance, fixture
    if best[1] is not None:
        editor(owner).select(best[1].object_id)
        owner.store("selected_fixture_id", best[1].fixture_id)


def drag(owner, domain, phase):
    from .fixture_scene import replace_transform
    from .layout_scene_td import field, status, refresh as refresh3d
    viewport = owner.op("ui_panel/fixtures_" + domain + "/viewport")
    uv = (float(viewport.panel.u), float(viewport.panel.v))
    try:
        if phase == "start":
            _pick(owner, domain, uv)
            fixture = selected(owner)
            start = fixture.output_transform if domain == "output" else fixture.uv_transform
            owner.store("fixture_domain", domain)
            owner.store("fixture_drag", (uv, start, fixture.fixture_id))
        elif phase == "update":
            gesture = owner.fetch("fixture_drag", None)
            if gesture is None:
                return
            first, transform, fixture_id = gesture
            du, dv = uv[0] - first[0], uv[1] - first[1]
            mode = field(owner, "mode") or "move"
            if mode == "move":
                span = owner.fetch("fixture_output_frame", (.5, .5, 1.0))[2] if domain == "output" else 1
                updated = replace(transform, translation=(transform.translation[0] + du * span, transform.translation[1] + dv * span))
            elif mode == "rotate":
                updated = replace(transform, rotation=transform.rotation + (du + dv) * 180)
            elif mode == "scale":
                factor = max(.01, 1 + du + dv)
                updated = replace(transform, scale=tuple(v * factor for v in transform.scale))
            else:
                raise SceneError("2D mode must be move, rotate or scale")
            owner.store("fixture_preview", replace_transform(history(owner).current, fixture_id, domain=domain, transform=updated))
            refresh(owner, save=False)
        elif phase == "end":
            preview = owner.fetch("fixture_preview", None)
            if preview is not None:
                _commit(owner, preview)
            owner.store("fixture_drag", None)
            refresh3d(owner)
            status(owner, "2D " + domain.upper() + " EDIT | other coordinate domain and3D unchanged")
    except Exception as error:
        owner.store("fixture_preview", None)
        owner.store("fixture_drag", None)
        refresh(owner, save=False)
        status(owner, "2D EDIT BLOCKED — " + str(error))


def key(owner, key_name, ctrl=False):
    from .fixture_scene import replace_transform
    from .layout_scene_td import field, status
    try:
        if key_name == "escape":
            owner.store("fixture_preview", None)
            owner.store("fixture_drag", None)
        elif ctrl and key_name in ("z", "y"):
            getattr(history(owner), "undo" if key_name == "z" else "redo")()
        elif not ctrl and key_name in ("left", "right", "up", "down"):
            fixture = selected(owner)
            domain = owner.fetch("fixture_domain", "output")
            transform = fixture.output_transform if domain == "output" else fixture.uv_transform
            step = float(field(owner, "step") or ".01")
            if step <= 0:
                raise SceneError("step must be positive")
            delta = step if key_name in ("right", "up") else -step
            mode = field(owner, "mode") or "move"
            if mode == "move":
                values = list(transform.translation)
                values[0 if key_name in ("left", "right") else 1] += delta
                changed = replace(transform, translation=tuple(values))
            elif mode == "rotate":
                changed = replace(transform, rotation=transform.rotation + delta)
            elif mode == "scale":
                changed = replace(transform, scale=tuple(v + delta for v in transform.scale))
            else:
                raise SceneError("2D mode must be move, rotate or scale")
            _commit(owner, replace_transform(history(owner).current, fixture.fixture_id, domain=domain, transform=changed))
        refresh(owner)
    except Exception as error:
        status(owner, "2D KEY BLOCKED — " + str(error))
