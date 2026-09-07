"""Read-only active-table snapshot to immutable scene; no disk/hardware calls."""
from hashlib import sha256
import json
from uuid import NAMESPACE_URL, uuid5

from .layout_scene import Scene, Scan, SceneObject, LedBinding, SceneError, new_id
from .layout_scene_adapter import LayoutDocument
from .routing_transaction import router_from_rows, build_router_plan, table_rows

MAP_PATH = "/project1/pixelblaze_mapper/map_active"
ROUTER_PATH = "/project1/multi_controller_output"


def _stable(namespace, value):
    return str(uuid5(NAMESPACE_URL, namespace + ":" + value))


def snapshot_document(map_rows, controller_rows=None, segment_rows=None, *, namespace=MAP_PATH):
    """Preserve authoritative row/global-index order. Never infer physical ports.

    Valid, disjoint router SOURCE ranges form objects; destination/reverse do not
    reorder coordinates. Invalid/missing router data falls back to one explicitly
    ungrouped object. Stable LED IDs derive from the explicit source namespace and
    global index, not coordinate values. They are not claimed as recovered scan IDs.
    """
    rows = tuple(tuple(str(v) for v in row) for row in map_rows)
    if not rows or rows[0] != ("index", "tx", "ty", "tz") or len(rows) < 2:
        raise SceneError("Active map requires nonempty index,tx,ty,tz rows")
    points = []
    try:
        for index, row in enumerate(rows[1:]):
            if len(row) != 4 or row[0] != str(index):
                raise SceneError("Active source indices must be ordered 0..N-1; no silent renumbering")
            points.append(tuple(float(v) for v in row[1:]))
    except (TypeError, ValueError) as error:
        raise SceneError("Invalid active map coordinates/index: " + str(error)) from error
    count = len(points)
    warnings, groups = [], []
    if controller_rows is None or segment_rows is None:
        warnings.append("Routing tables missing: active coordinates loaded as one ungrouped object")
    else:
        try:
            router = router_from_rows(controller_rows, segment_rows, source_pixels=count)
            build_router_plan(router)
            claimed = set()
            for segment in sorted(router.segments, key=lambda s: (s.source_start, s.name)):
                indices = tuple(range(segment.source_start, segment.source_start + segment.count))
                if set(indices) & claimed:
                    raise SceneError("overlapping routing source ranges")
                claimed.update(indices)
                groups.append((segment.name + " [" + segment.controller + "]", indices,
                               (("route_segment", segment.name), ("route_controller", segment.controller),
                                ("destination_start", str(segment.destination_start)), ("reverse", str(segment.reverse)))))
        except (ValueError, KeyError, TypeError) as error:
            groups = []
            warnings.append("Routing grouping disabled: " + str(error) + "; all source LEDs retained ungrouped")
    used = {i for _, indices, _ in groups for i in indices}
    leftovers = tuple(i for i in range(count) if i not in used)
    if leftovers:
        groups.append(("Unmapped" if groups else "Active snapshot (ungrouped)", leftovers, ()))
    metadata = [(("source_operator", MAP_PATH), ("source_index", str(i))) for i in range(count)]
    for _, indices, provenance in groups:
        for i in indices:
            metadata[i] += provenance
    digest = sha256(json.dumps([rows, metadata], separators=(",", ":")).encode("utf-8")).hexdigest()
    scan = Scan(_stable(namespace, "scan:" + digest), "Active map snapshot", tuple(points),
                source_format="touchdesigner-active-map", row_metadata=tuple(metadata), warnings=tuple(warnings))
    objects = []
    for name, indices, _ in groups:
        object_id = _stable(namespace, "object:" + name + ":" + ",".join(map(str, indices)))
        leds = tuple(LedBinding(_stable(namespace, "led:" + str(source)), local, source, scan.scan_id, source)
                     for local, source in enumerate(indices))
        objects.append(SceneObject(object_id, name, leds))
    scene = Scene(new_id(), "Active snapshot", (scan,), tuple(objects), expected_count=count)
    scene.validate_output()
    return LayoutDocument(scene), tuple(warnings)


def read_active_snapshot(owner):
    """Double read detects changing inputs; does not write/cook any active node."""
    paths = (MAP_PATH, ROUTER_PATH + "/controller_config", ROUTER_PATH + "/segment_config")
    def capture():
        return tuple(table_rows(owner.op(path)) if owner.op(path) is not None else None for path in paths)
    before = capture()
    if before[0] is None:
        raise SceneError("Authoritative active map is missing: " + MAP_PATH)
    result = snapshot_document(*before)
    if capture() != before:
        raise SceneError("Active mapping/routing changed during snapshot; retry without changing the draft")
    return result
