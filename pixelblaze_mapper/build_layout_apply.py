"""Explicit reversible workspace apply; builder only creates dormant new nodes.

No output is started or stopped. Apply requires every known sender already OFF.
Routes/material TOPs are preserved. No disk files or project saves are made.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from pixelblaze_mapper.fixture_scene import export_sampling_uv
from pixelblaze_mapper.layout_scene import SceneError, export_pixelblaze_3d
from pixelblaze_mapper.layout_workspace import export_workspace
from pixelblaze_mapper.routing_transaction import build_router_plan, router_from_rows, table_rows, write_rows

ROOT = Path(r'C:/Users/jbhtz/TouchDesignerLocal/PixelblazeMapper')
OWNER_PATH = '/project1/layout_apply'
MAP = '/project1/pixelblaze_mapper/map_active'
UV = '/project1/pixelblaze_mapper/effect_panel_uv'
ROUTER = '/project1/multi_controller_output'
ARCHIVE_TABLES = ('active_workspace', 'active_map_3d', 'active_fixture_output', 'active_settings')


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def workspace_hash(document, fixtures):
    return digest(json.loads(export_workspace(document, fixtures)))


@dataclass(frozen=True)
class LayoutApplyPlan:
    workspace_revision: str
    base_active_hash: str
    mode: str
    projection: str
    source_count: int
    workspace_json: str
    map_rows: tuple
    map_3d_rows: tuple
    fixture_output_rows: tuple
    uv_rows: tuple
    preserve_routing: bool = True


def prepare_layout(document, fixtures, *, mode, projection='YX', source_count,
                   base_active_hash, preserve_routing=False, active_map_rows=None):
    """Validate everything before acquiring the live adapter's write lock.

    Route bindings in the document remain DRAFT INTENT. Caller must explicitly
    confirm preserving the live routing; this adapter never applies those routes.
    """
    if preserve_routing is not True:
        raise SceneError('Explicit confirmation to preserve existing live routing is required')
    if mode not in ('3d', '2d') or projection not in ('XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY'):
        raise SceneError('Choose mode 3d/2d and an explicit XYZ-axis projection')
    if type(source_count) is not int or source_count <= 0 or not isinstance(base_active_hash, str) or not base_active_hash:
        raise SceneError('Need a valid current output count and active-state hash')
    points = json.loads(export_pixelblaze_3d(document.scene))
    if len(points) != source_count:
        raise SceneError('Draft LED count differs from current output; routing/count changes are a separate operation')
    # Bind full workspace, even when a stale fixture draft is unused in 3D mode.
    workspace = export_workspace(document, fixtures)
    map_3d = (('index', 'tx', 'ty', 'tz'),) + tuple((i, *point) for i, point in enumerate(points))
    fixture_rows = (('index', 'led_id', 'object_id', 'local_index', 'x', 'y'),)
    if mode == '2d':
        fixtures.validate_source_scene(document.scene)
        checked = replace(fixtures, expected_count=source_count)
        uvs = json.loads(export_sampling_uv(checked, bounds='reject'))
        output = sorted(((led, point, fixture.object_id) for fixture in fixtures.fixtures
                         for led, point in fixture.output_points()), key=lambda row: row[0].source_index)
        # The 2D OUTPUT canvas is a separate representation, not permission to
        # flatten or reposition the installation's authoritative physical XYZ.
        if active_map_rows is None:
            raise SceneError('2D apply requires an explicit current physical-map snapshot')
        map_rows = tuple(tuple(value for value in row) for row in active_map_rows)
        if len(map_rows) != source_count + 1 or map_rows[0] != ('index', 'tx', 'ty', 'tz'):
            raise SceneError('Current physical map has an unexpected schema/count')
        for i, row in enumerate(map_rows[1:]):
            if len(row) != 4 or str(row[0]) != str(i) or any(not isfinite(float(v)) for v in row[1:]):
                raise SceneError('Current physical map is malformed or reordered')
        map_3d = map_rows
        fixture_rows += tuple((led.source_index, led.led_id, object_id, led.local_index, *point) for led, point, object_id in output)
    else:
        map_rows = map_3d
        axes = tuple('XYZ'.index(axis) for axis in projection)
        uvs = [tuple(point[axis] for axis in axes) for point in points]
        if any(not isfinite(v) or not 0 <= v <= 1 for point in uvs for v in point):
            raise SceneError('Projected 3D UV outside 0..1; use explicit fixture UV placement instead of silent normalization/clamping')
    object_by_source = {led.source_index: obj.object_id for obj in document.scene.objects for led in obj.leds}
    groups = {object_id: i for i, object_id in enumerate(sorted(set(object_by_source.values())))}
    # Explicit workspace mapping wins in global/panel/hybrid and Show consumers.
    # No implicit per-panel refit can change a user's chosen material rectangle.
    uv_rows = (('index', 'panel_id', 'panel', 'global_u', 'global_v', 'local_u', 'local_v'),) + tuple(
        (i, groups[object_by_source[i]], object_by_source[i], *uv, *uv) for i, uv in enumerate(uvs))
    return LayoutApplyPlan(workspace_hash(document, fixtures), base_active_hash, mode, projection,
        source_count, workspace, map_rows, map_3d, fixture_rows, uv_rows)


def apply_plan(plan, document, fixtures, adapter):
    """Injected transaction: validate, lock, snapshot, write, verify, rollback."""
    expected = prepare_layout(document, fixtures, mode=plan.mode, projection=plan.projection,
        source_count=plan.source_count, base_active_hash=plan.base_active_hash, preserve_routing=plan.preserve_routing,
        active_map_rows=plan.map_rows if plan.mode == '2d' else None)
    if expected != plan:
        raise SceneError('Prepared workspace or payload changed; prepare again')
    adapter.assert_outputs_off()
    with adapter.lock():
        if adapter.active_hash() != plan.base_active_hash:
            raise SceneError('Active mapping/routing changed since prepare')
        adapter.preflight(plan)
        snapshot = adapter.capture()
        if adapter.active_hash() != plan.base_active_hash:
            raise SceneError('Active mapping changed during snapshot; nothing written')
        try:
            adapter.write(plan)
            adapter.assert_outputs_off()
            if adapter.verify(plan, snapshot) is not True:
                raise SceneError('Live map/UV verification failed')
            adapter.remember(snapshot, plan)
        except Exception as error:
            try:
                adapter.restore(snapshot)
                adapter.assert_outputs_off()
            except Exception as recovery:
                raise SceneError('Apply failed: %s; ROLLBACK FAILED: %s' % (error, recovery)) from recovery
            raise SceneError('Apply rolled back: ' + str(error)) from error
    return plan


POSITION_CALLBACK = '''def onCook(scriptOp):
    table = op('/project1/pixelblaze_mapper/map_active')
    count = table.numRows - 1
    if count <= 0 or any(int(table[i+1, 'index']) != i for i in range(count)):
        raise RuntimeError('Active layout indices are incomplete or unordered')
    scriptOp.clear()
    scriptOp.numSamples = count
    for axis in ('tx', 'ty', 'tz'):
        scriptOp.appendChan(axis).vals = [float(table[i+1, axis]) for i in range(count)]
'''


class TouchDesignerLayoutAdapter:
    """Synchronous TD-main-thread adapter. No background/concurrent writers."""
    def __init__(self, owner):
        self.owner = owner

    def node(self, path):
        node = self.owner.op(path)
        if node is None:
            raise SceneError('Required operator missing: ' + path)
        return node

    def lock(self):
        from contextlib import contextmanager
        @contextmanager
        def held():
            if self.owner.fetch('applying', False):
                raise SceneError('Another layout transaction is active')
            self.owner.store('applying', True)
            try:
                yield
            finally:
                self.owner.store('applying', False)
        return held()

    def assert_outputs_off(self):
        sender = self.node(ROUTER + '/artnet_510_sender_callbacks')
        if sender.module.status().get('enabled'):
            raise SceneError('Stop LED output explicitly before applying a layout')
        for path in (ROUTER + '/dmxout_ws2812_node', ROUTER + '/dmxout_apa102_esp', '/project1/dmxout1', '/project1/esp_artnet_out'):
            node = self.owner.op(path)
            if node is not None and node.par['active'] is not None and bool(node.par.active.eval()):
                raise SceneError('Native output must be OFF: ' + path)

    def capture(self):
        texts = {path: self.node(path).text for path in (MAP, UV, ROUTER + '/controller_config', ROUTER + '/segment_config',
            '/project1/effect_sample_uv_callbacks', '/project1/read_LED_map')}
        texts.update({self.owner.path + '/' + name: self.node(self.owner.path + '/' + name).text for name in ARCHIVE_TABLES})
        texts[self.owner.path + '/position_callbacks'] = self.node(self.owner.path + '/position_callbacks').text
        bindings = {}
        for path, name in (('/project1/LedMap', 'callbacks'), ('/project1/effect_sample_uv', 'callbacks'), ('/project1/topto1', 'top')):
            par = self.node(path).par[name]
            bindings[path + '|' + name] = (str(par.eval()), par.expr, str(par.mode))
        links = {path: [node.path for node in self.node(path).inputs] for path in (
            '/project1/pixelblaze_mapper/map_active_out', '/project1/selectDat', '/project1/evaluate1',
            '/project1/null4', '/project1/effect_sample_uv', '/project1/topto1')}
        # Legacy display callbacks can shift raw XYZ. In 2D mode the ACTUAL
        # downstream geometry, not merely its source table, must stay identical.
        downstream_xyz = {path: {axis: [float(self.node(path)[axis][i]) for i in range(self.node(path).numSamples)]
                                for axis in ('tx', 'ty', 'tz')}
                          for path in ('/project1/LedMap', '/project1/null4')}
        return {'texts': texts, 'bindings': bindings, 'links': links, 'downstream_xyz': downstream_xyz}

    def active_hash(self):
        return digest(self.capture())

    def preflight(self, plan):
        map_table = self.node(MAP)
        if map_table.numRows != plan.source_count + 1:
            raise SceneError('Current mapping count changed')
        if plan.mode == '2d' and table_rows(map_table) != [[str(v) for v in row] for row in plan.map_rows]:
            raise SceneError('2D mode cannot replace physical-map coordinates')
        plan_router = router_from_rows(table_rows(self.node(ROUTER + '/controller_config')),
            table_rows(self.node(ROUTER + '/segment_config')), source_pixels=plan.source_count)
        build_router_plan(plan_router)
        expected = {'/project1/pixelblaze_mapper/map_active_out': [MAP],
            '/project1/selectDat': ['/project1/pixelblaze_mapper/map_active_out'],
            '/project1/evaluate1': ['/project1/selectDat'], '/project1/null4': ['/project1/LedMap'],
            '/project1/effect_sample_uv': ['/project1/null4'], '/project1/topto1': ['/project1/effect_sample_uv']}
        for path, inputs in expected.items():
            if [node.path for node in self.node(path).inputs] != inputs:
                raise SceneError('Canonical connection changed: ' + path)
        if str(self.node('/project1/topto1').par.top.eval()) != '/project1/res1':
            raise SceneError('Global material source must remain res1')
        if str(self.node('/project1/effect_sample_uv').par.callbacks.eval()) != '/project1/effect_sample_uv_callbacks':
            raise SceneError('Unexpected UV sampler callback binding')
        for path in ('/project1/null4', '/project1/effect_sample_uv', '/project1/topto1', '/project1/math1'):
            if self.node(path).numSamples != plan.source_count:
                raise SceneError('Current downstream LED count differs: ' + path)
        for path in ('/project1/LedMap', '/project1/effect_sample_uv'):
            if str(self.node(path).par.callbacks.mode) != 'ParMode.CONSTANT':
                raise SceneError('Callback expressions require explicit integration review')
        if self.node(self.owner.path + '/position_callbacks').text != POSITION_CALLBACK:
            raise SceneError('Position callback differs from reviewed source')

    def write(self, plan):
        if plan.mode == '3d':
            write_rows(self.node(MAP), plan.map_rows)
        write_rows(self.node(UV), plan.uv_rows)
        self.node(self.owner.path + '/active_workspace').text = plan.workspace_json
        write_rows(self.node(self.owner.path + '/active_map_3d'), plan.map_3d_rows)
        write_rows(self.node(self.owner.path + '/active_fixture_output'), plan.fixture_output_rows)
        self.node(self.owner.path + '/active_settings').text = json.dumps({'mode': plan.mode, 'projection': plan.projection,
            'workspace_revision': plan.workspace_revision, 'source_count': plan.source_count,
            'routes': 'preserved', 'global_and_local_uv': 'explicit-workspace', 'output_enabled': False})
        if plan.mode == '3d':
            self.node('/project1/LedMap').par.callbacks = self.owner.path + '/position_callbacks'
        self._cook()

    def _cook(self):
        # Existing UV callback and Show callbacks use the shared effect_panel_uv.
        for path in ('/project1/LedMap', '/project1/null4', '/project1/effect_sample_uv',
                     '/project1/show_control/show_global_uv', '/project1/show_control/slot_a_uv',
                     '/project1/show_control/slot_b_uv', '/project1/topto1', '/project1/math1', '/project1/LED_PREVIEW_OUT'):
            node = self.owner.op(path)
            if node is not None:
                node.cook(force=True)
                if node.errors(recurse=False):
                    raise SceneError('Cook failed: ' + path + ': ' + str(node.errors(recurse=False)))

    def verify(self, plan, snapshot):
        current = self.capture()
        for path in (ROUTER + '/controller_config', ROUTER + '/segment_config', '/project1/effect_sample_uv_callbacks', '/project1/read_LED_map'):
            if current['texts'][path] != snapshot['texts'][path]:
                return False
        if current['links'] != snapshot['links']:
            return False
        for key, binding in snapshot['bindings'].items():
            if (plan.mode == '2d' or key != '/project1/LedMap|callbacks') and current['bindings'][key] != binding:
                return False
        if plan.mode == '2d':
            if current['downstream_xyz'] != snapshot['downstream_xyz']:
                return False
        elif current['bindings']['/project1/LedMap|callbacks'][0] != self.owner.path + '/position_callbacks':
            return False
        if table_rows(self.node(MAP)) != [[str(v) for v in row] for row in plan.map_rows]:
            return False
        if table_rows(self.node(UV)) != [[str(v) for v in row] for row in plan.uv_rows]:
            return False
        xyz = self.node('/project1/null4')
        uv = self.node('/project1/effect_sample_uv')
        if xyz.numSamples != plan.source_count or uv.numSamples != plan.source_count:
            return False
        for index in range(plan.source_count):
            if plan.mode == '3d' and any(abs(float(xyz[axis][index]) - float(plan.map_rows[index+1][col+1])) > 1e-5 for col, axis in enumerate(('tx', 'ty', 'tz'))):
                return False
            if any(abs(float(uv[axis][index]) - float(plan.uv_rows[index+1][col+3])) > 1e-5 for col, axis in enumerate(('tx', 'ty'))):
                return False
        return all(self.node(path).numSamples == plan.source_count for path in ('/project1/topto1', '/project1/math1'))

    def restore(self, snapshot):
        for path, text in snapshot['texts'].items():
            # Routing tables were never written; restoring them would wrongly
            # overwrite an unrelated concurrent routing edit. Fail visibly.
            if path.startswith(ROUTER + '/'):
                if self.node(path).text != text:
                    raise SceneError('Routing changed concurrently; manual recovery required')
                continue
            self.node(path).text = text
        old = snapshot['bindings']['/project1/LedMap|callbacks']
        self.node('/project1/LedMap').par.callbacks = old[0]
        self._cook()
        if self.capture() != snapshot:
            raise SceneError('Rollback did not restore exact active state')

    def remember(self, snapshot, plan):
        self.owner.store('last_snapshot', snapshot)
        self.owner.store('last_applied_hash', self.active_hash())


def prepare_current(owner, *, mode, projection='YX', preserve_routing=False):
    from pixelblaze_mapper.layout_session_storage import prepare_apply_save
    prepare_apply_save(owner)
    from pixelblaze_mapper.layout_scene_td import editor
    from pixelblaze_mapper.layout_fixture_td import history
    ui = owner.op('/project1/layout_scene_editor')
    document, fixtures = editor(ui).current, history(ui).current
    adapter = TouchDesignerLayoutAdapter(owner)
    adapter.assert_outputs_off()
    count = adapter.node(MAP).numRows - 1
    plan = prepare_layout(document, fixtures, mode=mode, projection=projection, source_count=count,
        base_active_hash=adapter.active_hash(), preserve_routing=preserve_routing,
        active_map_rows=table_rows(adapter.node(MAP)))
    adapter.preflight(plan)
    owner.store('prepared_plan', plan)
    return plan


def apply_current(owner):
    from pixelblaze_mapper.layout_scene_td import editor
    from pixelblaze_mapper.layout_fixture_td import history
    plan = owner.fetch('prepared_plan', None)
    if not isinstance(plan, LayoutApplyPlan):
        raise SceneError('Prepare the current workspace first')
    ui = owner.op('/project1/layout_scene_editor')
    result = apply_plan(plan, editor(ui).current, history(ui).current, TouchDesignerLayoutAdapter(owner))
    owner.store('prepared_plan', None)
    return result


def revert_last(owner):
    adapter = TouchDesignerLayoutAdapter(owner)
    adapter.assert_outputs_off()
    with adapter.lock():
        snapshot = owner.fetch('last_snapshot', None)
        if snapshot is None or adapter.active_hash() != owner.fetch('last_applied_hash', None):
            raise SceneError('No unchanged last apply to revert; external changes require review')
        adapter.restore(snapshot)
        owner.store('last_snapshot', None)
        owner.store('prepared_plan', None)
    return True


def build():
    project = op('/project1')
    owner = project.op('layout_apply') or project.create(baseCOMP, 'layout_apply')
    for name in ARCHIVE_TABLES:
        if owner.op(name) is None:
            owner.create(tableDAT if name in ('active_map_3d', 'active_fixture_output') else textDAT, name)
    callback = owner.op('position_callbacks')
    if callback is None:
        callback = owner.create(textDAT, 'position_callbacks')
        callback.text = POSITION_CALLBACK
    elif callback.text != POSITION_CALLBACK:
        raise SceneError('Existing position callback differs; explicit migration required')
    runtime = owner.op('runtime') or owner.create(textDAT, 'runtime')
    runtime.text = """from pixelblaze_mapper.build_layout_apply import prepare_current, apply_current, revert_last
OWNER = op('/project1/layout_apply')
def prepare(mode, projection='YX', preserve_routing=False):
    return prepare_current(OWNER, mode=mode, projection=projection, preserve_routing=preserve_routing)
def apply():
    return apply_current(OWNER)
def revert():
    return revert_last(OWNER)
def prepare_save():
    from pixelblaze_mapper.layout_session_storage import prepare_apply_save
    return prepare_apply_save(OWNER)
"""
    from pixelblaze_mapper.layout_session_storage import prepare_apply_save
    prepare_apply_save(owner)
    return owner


if globals().get('__name__') == '__main__' and 'op' in globals():
    build()
