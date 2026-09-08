"""Offline TD-bridge regressions: all launchers, cameras and sockets are fakes."""
import ast
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import guided_scan_live as bridge, scan_output_guard as guard
from pixelblaze_mapper import scan_capture
from pixelblaze_mapper.multi_controller import controller_rows, segment_rows
from pixelblaze_mapper.scan_routing import ScanRoutingSnapshot
from pixelblaze_mapper.scan_session import ScanSession, ScanTarget
from tests.test_routing_apply_regression import Table, embedded
from tests.test_scan_routing import six_universe_config


def _artnet_510_sender_source():
    # Builders may execute build() at import in TD; extract only pure factory.
    return embedded('build_multi_controller_output.py', '_artnet_510_sender_source')


class TextTable(Table):
    @property
    def text(self):
        return '\n'.join('\t'.join(row) for row in self.rows)

    @text.setter
    def text(self, value):
        self.rows = [line.split('\t') for line in str(value).split('\n')]


class Owner:
    def __init__(self):
        self.storage = {}
        self.children = {}

    def op(self, name):
        return self.children.get(name)

    def store(self, key, value):
        # A handle/thread/socket mistakenly persisted will fail immediately.
        json.dumps(value, allow_nan=False)
        self.storage[key] = copy.deepcopy(value)

    def fetch(self, key, default=None):
        return copy.deepcopy(self.storage.get(key, default))


class GuidedScanLiveTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for key, value in (('_probe', None), ('_capture', None), ('_token', None),
                           ('_signature', None), ('_last_poll', 0.0), ('_probe_stop_thread', None)):
            self.stack.enter_context(patch.object(bridge, key, value))
        self.stack.enter_context(patch.object(guard, '_token', None))
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.no_socket = self.stack.enter_context(patch('socket.socket', side_effect=AssertionError('No sockets in bridge tests')))
        self.no_process = self.stack.enter_context(patch('subprocess.Popen', side_effect=AssertionError('No process launch in bridge tests')))
        self.owner = Owner()
        state = ScanSession('session', 'scene', 'scene-revision', (
            ScanTarget('led517', 'object', 0, 517), ScanTarget('led785', 'object', 1, 785),
            ScanTarget('anchor1284', 'anchor-object', 0, 1284)), ('led517',), ('anchor1284',))
        self.owner.store('session', state.to_dict())
        self.sender_enabled = False
        self.sender = SimpleNamespace(text=_artnet_510_sender_source(),
            module=SimpleNamespace(status=lambda:{'enabled':self.sender_enabled}))
        self.native_flag = SimpleNamespace(value=False)
        self.native = SimpleNamespace(path='/project1/esp_artnet_out', type='dmxout',
                                      par=SimpleNamespace(active=SimpleNamespace(eval=lambda:self.native_flag.value)))
        config = six_universe_config()
        self.nodes = {
            bridge.OWNER:self.owner,
            bridge.ROUTER+'/controller_config':TextTable(controller_rows(config)),
            bridge.ROUTER+'/segment_config':TextTable(segment_rows(config)),
            bridge.ROUTER+'/artnet_510_sender_callbacks':self.sender,
            bridge.ROUTER+'/gico_port_config/settings':TextTable([['key','value'],['universes_per_port',6],['first_universe',1]]),
            bridge.ROUTER+'/gico_port_config/ports':TextTable([['port','pixel_count'],[1,517],[2,269],[3,398],[4,896]]),
            '/project1/math1':SimpleNamespace(numSamples=3744),
            '/project1':SimpleNamespace(findChildren=lambda:[self.native]),
            bridge.OWNER+'/worker_plan':SimpleNamespace(text=''),
            bridge.OWNER+'/dry_run':SimpleNamespace(text=''),
        }
        for key in ('status','routing_summary','camera_status'):
            self.nodes[bridge.OWNER+'/ui_panel/'+key] = SimpleNamespace(par=SimpleNamespace(text=''))
        for key, value in {'source_ids':'785,517','anchors':'1284','camera':'0','exposure':'-10',
                           'threshold':'160','workspace':self.temp,'views':''}.items():
            self.nodes[bridge.OWNER+'/ui_panel/'+key+'/string'] = TextTable([[value]])
        self.op = self.nodes.get
        self.handle = scan_capture.CaptureHandle(
            process=SimpleNamespace(poll=lambda:None), directory=Path(self.temp)/'not-launched')

    def change_field(self, name, value):
        self.nodes[bridge.OWNER+'/ui_panel/'+name+'/string'][0,0] = value

    def prepare(self):
        return bridge.prepare(self.op)

    def test_prepare_canonical_six_universe_routing_and_sparse_identity_no_hardware(self):
        summary = self.prepare()
        plan = self.owner.fetch('capture_plan')
        snapshot = ScanRoutingSnapshot.from_dict(plan['routing'])
        self.assertEqual(snapshot.source_indices, (785,517,1284))
        self.assertEqual(snapshot.config.source_pixel_count, 3744)
        self.assertEqual([t.wire_universe for t in snapshot.targets], [7,6,18])
        self.assertEqual(len(snapshot.black_frames()['WS2812_NODE']), 24)
        self.assertEqual(plan['identity'], {'517':'led517','785':'led785','1284':'anchor1284'})
        self.assertEqual(plan['scene_revision'], 'scene-revision')
        self.assertIn('Art-Net U0-U23 (ab 0)', summary)
        self.assertEqual(json.loads(self.nodes[bridge.OWNER+'/worker_plan'].text), plan)
        self.assertFalse(guard.active())
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()

    def test_prepared_bridge_manifest_is_accepted_by_real_launcher_validation(self):
        self.prepare()
        checked = scan_capture.validate_capture_manifest(self.owner.fetch('capture_plan'))
        self.assertEqual(checked['routing']['source_indices'], [785,517,1284])

    def test_td_none_field_is_empty_and_optional_anchors_prepare_without_none_id(self):
        # TD can return None for an empty field DAT cell. Do not stringify it.
        self.nodes[bridge.OWNER+'/ui_panel/anchors/string'].rows[0][0] = None
        self.nodes[bridge.OWNER+'/ui_panel/views/string'].rows[0][0] = None
        self.assertEqual(bridge._field(self.op,'anchors'),'')
        self.assertEqual(bridge._field(self.op,'views'),'')
        self.prepare()
        snapshot = ScanRoutingSnapshot.from_dict(self.owner.fetch('capture_plan')['routing'])
        self.assertEqual(snapshot.source_indices,(785,517))
        self.assertEqual(self.owner.fetch('session')['anchor_ids'],())

    def test_ui_selection_or_anchor_change_after_prepare_blocks_start(self):
        for name, value in (('source_ids','517'), ('anchors','')):
            with self.subTest(field=name):
                self.change_field('source_ids','785,517')
                self.change_field('anchors','1284')
                self.prepare()
                self.change_field(name,value)
                with patch.object(scan_capture, 'start_capture', return_value=self.handle) as launch:
                    try:
                        with self.assertRaisesRegex(RuntimeError, 'prepare|Prepare|scope'):
                            bridge.start(self.op, confirmed=True)
                    finally:
                        if bridge._token is not None:
                            guard.release(bridge._token)
                            bridge._token = None
                        bridge._capture = None
                    launch.assert_not_called()

    def test_actual_gico_settings_and_ports_invalidate_prepared_signature(self):
        for suffix in ('settings','ports'):
            with self.subTest(table=suffix):
                before = bridge._routing_signature(self.op)
                self.nodes[bridge.ROUTER+'/gico_port_config/'+suffix][1,1] = '99'
                self.assertNotEqual(bridge._routing_signature(self.op), before)

    def test_controller_segment_and_source_count_changes_block_start(self):
        self.prepare()
        self.nodes[bridge.ROUTER+'/controller_config'][1,'brightness'] = '.03'
        with patch.object(scan_capture,'start_capture') as launch:
            with self.assertRaisesRegex(RuntimeError,'Prepare'):
                bridge.start(self.op,confirmed=True)
            launch.assert_not_called()
        first = bridge._routing_signature(self.op)
        self.nodes[bridge.ROUTER+'/segment_config'][1,'count'] = '516'
        self.assertNotEqual(first,bridge._routing_signature(self.op))
        first = bridge._routing_signature(self.op)
        self.nodes['/project1/math1'].numSamples = 4000
        self.assertNotEqual(first,bridge._routing_signature(self.op))

    def test_layout_workspace_change_after_prepare_blocks_old_plan(self):
        layout = Owner()
        layout.store('workspace', {'scene':{'revision':'A'}})
        self.nodes['/project1/layout_scene_editor'] = layout
        self.prepare()
        layout.store('workspace', {'scene':{'revision':'B'}})
        with patch.object(scan_capture,'start_capture') as launch:
            with self.assertRaisesRegex(RuntimeError,'Prepare'):
                bridge.start(self.op,confirmed=True)
            launch.assert_not_called()

    def test_actual_layout_document_changes_invalidate_prepared_plan(self):
        from pixelblaze_mapper.layout_scene import Scene
        from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, document_json, scene_revision
        layout = Owner()
        self.nodes['/project1/layout_scene_editor'] = layout
        scene = Scene('scene', 'test')
        state = self.owner.fetch('session')
        state['scene_revision'] = scene_revision(scene)
        self.owner.store('session', state)
        for name in ('draft_document', 'fixture_document'):
            layout.children[name] = SimpleNamespace(text=document_json(LayoutDocument(scene)))
        for name in ('draft_document', 'fixture_document'):
            with self.subTest(document=name):
                layout.children['draft_document'].text = document_json(LayoutDocument(scene))
                self.prepare()
                layout.children[name].text = '{"revision":"B"}'
                with patch.object(scan_capture, 'start_capture') as launch:
                    with self.assertRaisesRegex(RuntimeError, 'Prepare'):
                        bridge.start(self.op, confirmed=True)
                    launch.assert_not_called()

    def test_changed_layout_before_prepare_requires_restaging(self):
        from pixelblaze_mapper.layout_scene import Scene
        from pixelblaze_mapper.layout_scene_adapter import LayoutDocument, document_json
        layout = Owner()
        layout.children['draft_document'] = SimpleNamespace(text=document_json(LayoutDocument(Scene('new-scene', 'changed'))))
        self.nodes['/project1/layout_scene_editor'] = layout
        with self.assertRaisesRegex(RuntimeError, 'stage the object'):
            self.prepare()
        self.no_process.assert_not_called()

    def test_active_shared_or_legacy_native_output_blocks_before_guard_or_launch(self):
        self.prepare()
        original = self.sender.text
        for shared,native in ((True,False),(False,True)):
            self.sender_enabled,self.native_flag.value = shared,native
            with self.subTest(shared=shared), patch.object(scan_capture,'start_capture') as launch:
                with self.assertRaisesRegex(RuntimeError,'output|active'):
                    bridge.start(self.op,confirmed=True)
                launch.assert_not_called()
                self.assertEqual(self.sender.text,original)
                self.assertFalse(guard.active())

    def test_confirmation_and_camera_or_workspace_change_block(self):
        self.prepare()
        with self.assertRaises(ValueError):
            bridge.start(self.op)
        with patch.object(scan_capture,'start_capture') as launch:
            self.change_field('threshold','161')
            with self.assertRaisesRegex(RuntimeError,'Camera/workspace'):
                bridge.start(self.op,confirmed=True)
            launch.assert_not_called()

    def test_start_keeps_handles_only_in_module_and_release_on_launch_error(self):
        self.prepare()
        with patch.object(scan_capture,'start_capture',side_effect=RuntimeError('launch failed')):
            with self.assertRaisesRegex(RuntimeError,'launch failed'):
                bridge.start(self.op,confirmed=True)
        self.assertFalse(guard.active())
        with patch.object(scan_capture,'start_capture',return_value=self.handle):
            bridge.start(self.op,confirmed=True)
        self.assertIs(bridge._capture,self.handle)
        self.assertTrue(guard.active())
        self.assertEqual(self.owner.fetch('capture_status'),{'state':'starting'})
        json.dumps(self.owner.storage,allow_nan=False)
        self.assertFalse(any(value is self.handle for value in self.owner.storage.values()))

    def test_idle_poll_does_not_access_graph_launchers_or_devices(self):
        with patch.object(scan_capture,'poll_capture') as capture_poll, \
             patch.object(bridge.camera_probe,'poll_camera_probe') as camera_poll, \
             patch.object(bridge.time,'monotonic',return_value=100):
            bridge.poll(Mock(side_effect=AssertionError('Idle poll should not inspect operators')))
        capture_poll.assert_not_called()
        camera_poll.assert_not_called()
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()

    def test_poll_detects_scope_change_stops_capture_and_releases_finished_lease(self):
        self.prepare()
        with patch.object(scan_capture,'start_capture',return_value=self.handle):
            bridge.start(self.op,confirmed=True)
        self.change_field('source_ids','517')
        self.handle.status.update(state='cancelled')
        self.handle.process.poll = lambda:0
        with patch.object(scan_capture,'stop_capture') as stop, \
             patch.object(scan_capture,'poll_capture',wraps=scan_capture.poll_capture) as poll, \
             patch.object(bridge.time,'monotonic',return_value=100):
            bridge.poll(self.op)
        stop.assert_called_once_with(self.handle)
        poll.assert_called_once_with(self.handle)
        self.assertFalse(guard.active())
        self.assertIsNone(bridge._token)
        reason = 'Routing/scope changed during scan'
        self.assertEqual(self.handle.status['application_abort_reason'],reason)
        self.assertEqual(self.owner.fetch('capture_status')['application_abort_reason'],reason)
        self.assertIn(reason,self.owner.fetch('message'))
        self.assertIn(reason,self.nodes[bridge.OWNER+'/ui_panel/status'].par.text)

    def test_sender_guard_is_idempotent_and_denies_real_live_entry_before_socket(self):
        source = bridge.guard_sender_source(_artnet_510_sender_source())
        self.assertEqual(bridge.guard_sender_source(source),source)
        self.assertEqual(source.count(bridge.MARKER),1)
        tree = ast.parse(source)
        chosen = [node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('stop','set_enabled')]
        socket_factory = Mock(side_effect=AssertionError('Guard must run before socket'))
        old_socket = Mock()
        namespace = {'_socket':old_socket,'_enabled':True,'_active_names':['WS2812_NODE'],
                     '_controllers':lambda value:[{'name':'WS2812_NODE','local':'10.0.0.125'}],
                     'socket':SimpleNamespace(socket=socket_factory,AF_INET=2,SOCK_DGRAM=2)}
        exec(compile(ast.Module(body=chosen,type_ignores=[]),'<guarded-live>','exec'),namespace)
        token = guard.acquire()
        with self.assertRaisesRegex(RuntimeError,'Guided Scan owns output'):
            namespace['set_enabled'](True)
        self.assertFalse(namespace['_enabled'])
        old_socket.close.assert_called_once()
        socket_factory.assert_not_called()
        self.assertTrue(namespace['set_enabled'](False))
        guard.release(token)
        with self.assertRaises(ValueError):
            bridge.guard_sender_source('def unreviewed(): pass')

    def test_guard_double_acquire_and_wrong_release_fail_closed(self):
        token = guard.acquire()
        with self.assertRaises(RuntimeError): guard.acquire()
        with self.assertRaises(RuntimeError): guard.release('wrong')
        self.assertTrue(guard.active())
        guard.release(token)
        self.assertFalse(guard.active())

    def test_install_sender_guard_is_idempotent_and_preserves_false_outputs(self):
        self.assertTrue(bridge.install_sender_guard(self.op))
        guarded = self.sender.text
        self.assertFalse(bridge.install_sender_guard(self.op))
        self.assertEqual(self.sender.text,guarded)
        self.assertFalse(self.sender_enabled)
        self.assertFalse(self.native_flag.value)
        self.no_socket.assert_not_called()
        self.no_process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
