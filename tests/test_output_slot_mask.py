import ast
from types import SimpleNamespace as NS
from pathlib import Path
import unittest
from pixelblaze_mapper.output_slot_mask import channels, pixels, install_source, ranges_for, MASK_PATH
from tests.test_guided_scan_live import _artnet_510_sender_source

class MaskTests(unittest.TestCase):
    def test_only_reserved_slots_zero_and_input_unchanged(self):
        rgb=[[1]*3744,[.5]*3744,[.25]*3744]
        result=channels(rgb,[[1643,1695]])
        for original,masked in zip(rgb,result):
            self.assertEqual(masked[:1643],original[:1643])
            self.assertEqual(masked[1643:1696],[0]*53)
            self.assertEqual(masked[1696:],original[1696:])
        self.assertEqual(rgb[0],[1]*3744)
    def test_calibration_mask(self):
        result=pixels([(1,1,1)]*3744,[[1643,1695]])
        self.assertEqual(result[1643:1696],[(0,0,0)]*53)
    def test_td_noniterable_channel(self):
        from types import SimpleNamespace
        result=channels([SimpleNamespace(vals=[1,2,3])]*3,[[1,1]])
        self.assertEqual(result,[[1,0,3]]*3)
    def test_invalid_ranges_rejected(self):
        for ranges in ([[-1,2]],[[2,4]],[[2,1]]):
            with self.assertRaises(ValueError): channels([[1]*4]*3,ranges)
    def test_install_is_idempotent_compiles(self):
        source=install_source(_artnet_510_sender_source())
        compile(source,'sender','exec')
        self.assertEqual(install_source(source),source)

    def test_mask_dat_strictly_rejects_malformed_rows_and_stale_cached_lengths(self):
        mask = NS(text='index\tenabled\n0\t1\n1\t0\n')
        op = lambda path: mask if path == MASK_PATH else None
        self.assertEqual(ranges_for(op, 2), ((1, 1),))
        for text in ('index\tenabled\n0\t1\n1\t0\t', 'index\tenabled\n0\t1\n1\t0 \n',
                     '\nindex\tenabled\n0\t1\n1\t0', 'index\tenabled\n0\t1\n0\t0',
                     'index\tenabled\n0\tTrue\n1\t0', 'index\tenabled\n0\t1'):
            mask.text = text
            with self.subTest(text=text), self.assertRaises(ValueError): ranges_for(op, 2)
        mask.text = 'index\tenabled\n0\t1\n1\t0\n'
        with self.assertRaises(ValueError): ranges_for(op, 3)
        with self.assertRaises(ValueError): ranges_for(op, True)

    def test_applied_mask_supersedes_historical_ranges_including_no_gaps(self):
        mask = NS(text='index\tenabled\n0\t1\n1\t1')
        owner = NS(fetch=lambda key, default: [[0, 1]])
        op = lambda path: mask if path == MASK_PATH else owner
        self.assertEqual(ranges_for(op, 2), ())
        self.assertEqual(ranges_for(lambda path: None if path == MASK_PATH else owner, 2), ((0, 1),))

    def test_calibration_refreshes_changed_mask_and_stops_before_send_on_malformed_mask(self):
        source = install_source(_artnet_510_sender_source())
        tree = ast.parse(source)
        tree.body = [item for item in tree.body if isinstance(item, ast.FunctionDef)
                     and item.name in ('set_calibration', '_refresh_calibration_mask', 'tick')]
        mask = NS(text='index\tenabled\n0\t1\n1\t1')
        source_node = NS(numSamples=2)
        config = {'name': 'test', 'rate': 30, 'target': '127.0.0.1', 'port': 6454, 'universe': 0}
        packed, sent, stopped = [], [], []
        def pack(values):
            packed.append(values)
            return {'test': (bytes([round(v * 255) for pixel in values for v in pixel]) + bytes(504),)}
        ns = {'op': lambda path: mask if path == MASK_PATH else source_node if path == 'source_select' else None,
              'calibration_source': lambda *args, **kwargs: [(1., 1., 1.), (.5, .5, .5)],
              'load_coordinates': lambda: None, 'load_measurement_coordinates': lambda: None,
              'build_router_plan': lambda config: NS(pack_pixels=pack), '_router_config': lambda: None,
              'time': NS(monotonic=lambda: 20., perf_counter=lambda: 20.),
              '_enabled': True, '_socket': NS(sendto=lambda data, target: sent.append(data)),
              '_controllers': lambda enabled: [config], '_target_override': None, '_port_override': None,
              '_packet': lambda universe, payload: payload, '_last_send': 0., '_last_error': '',
              '_mode': 'live', '_calibration_mask_signature': None,
              **{key: 0 for key in ('_tick_count', '_rate_skips', '_send_count', '_packet_count', '_send_ms_last',
                                    '_send_ms_total', '_send_ms_max', '_send_interval_ema')}}
        def stop():
            ns['_enabled'] = False
            stopped.append(True)
        ns['stop'] = stop
        exec(compile(tree, '<masked sender>', 'exec'), ns)
        ns['set_calibration']()
        ns['_refresh_calibration_mask']()
        self.assertEqual(len(packed), 1)
        mask.text = 'index\tenabled\n0\t1\n1\t0'
        ns['tick']()
        self.assertEqual(len(packed), 2)
        self.assertEqual(sent[-1][3:6], bytes(3))
        mask.text = 'index\tenabled\n0\t1\n1\tbroken'
        ns['_last_send'] = 0
        ns['tick']()
        self.assertEqual(len(sent), 1)
        self.assertFalse(ns['_enabled'])
        self.assertTrue(stopped)
        self.assertIn('strict 0/1', ns['_last_error'])

    def test_native_and_shared_payloads_match_under_sparse_mask(self):
        from pixelblaze_mapper.output_slot_mask import install_native_source
        from pixelblaze_mapper.multi_controller import default_router_config, build_router_plan
        from pixelblaze_mapper.realtime_packer import compile_router_packer
        from tests.test_realtime_packer import channels as make_channels
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / 'pixelblaze_mapper/build_multi_controller_output.py').read_text(encoding='utf-8'))
        factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_pack_callbacks')
        factory_ns = {'LOCAL_ROOT': str(root)}
        exec(compile(ast.Module(body=[factory], type_ignores=[]), '<factory>', 'exec'), factory_ns)
        native_source = install_native_source(factory_ns['_pack_callbacks']('WS2812_NODE'))
        native_tree = ast.parse(native_source)
        native_tree.body = [n for n in native_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'onCook']
        shared_tree = ast.parse(install_source(_artnet_510_sender_source()))
        shared_tree.body = [n for n in shared_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_live_frames']
        rgb = make_channels()
        source = NS(numSamples=3744, numChans=3, cook=lambda force: None)
        class Input:
            numSamples, numChans = 3744, 3
            def __getitem__(self, index): return rgb[index]
            def cook(self, force): pass
        source = Input()
        mask = NS(text='index\tenabled\n' + '\n'.join('%d\t%d' % (i, not 1643 <= i <= 1695) for i in range(3744)))
        packer = compile_router_packer(build_router_plan(default_router_config()))
        ns = {'op': lambda path: mask if path == MASK_PATH else source if path == 'source_select' else None,
              'time': NS(perf_counter=lambda: 1.), '_controller_packer': lambda: packer.controller('WS2812_NODE'),
              '_compiled_router': lambda: packer, '_latest_frames': (),
              **{k: 0 for k in ('_pack_count', '_pack_ms_last', '_pack_ms_total', '_pack_ms_max')}}
        class Output:
            inputs = [source]
            numSamples = 0
            def clear(self): self.channels = []
            def appendChan(self, name):
                channel = NS(name=name, vals=[])
                self.channels.append(channel)
                return channel
        output = Output()
        exec(compile(native_tree, '<native>', 'exec'), ns)
        exec(compile(shared_tree, '<shared>', 'exec'), ns)
        ns['onCook'](output)
        shared = ns['_live_frames']([{'name': 'WS2812_NODE'}])['WS2812_NODE']
        self.assertEqual(tuple(bytes(c.vals) for c in output.channels), shared)
        self.assertTrue(all(len(frame) == 510 for frame in shared))
        mask.text = 'broken mask'
        with self.assertRaises(ValueError): ns['onCook'](output)
        self.assertEqual(output.channels, [])
        self.assertEqual(ns['_latest_frames'], ())

    def test_sparse_contract_checks_actual_native_callbacks_and_gate_bypasses(self):
        from tests.test_native_dmx_gate import NativeDmxGateTests, Parameter
        from pixelblaze_mapper.output_slot_mask import assert_sparse_contract, CONTRACT
        harness = NativeDmxGateTests()
        harness.setUp()
        harness.install()
        project, router = harness.project, harness.router
        sender = router.create('text', 'artnet_510_sender_callbacks')
        sender.text = CONTRACT + '\nCALIBRATION_SOURCE_MASK_V1'
        for sink, source, _ in harness.pairs:
            callback = source.parent().create('text', source.name + '_callbacks')
            callback.text = CONTRACT
            source.par.callbacks = Parameter(callback.path)
        owner = NS(children=list(router.children.values()), op=router.op)
        def op(path):
            if path == '/project1/multi_controller_output': return owner
            return project.op(path.removeprefix('/project1/'))
        self.assertTrue(assert_sparse_contract(op))
        sink, source, _ = harness.pairs[0]
        actual = source.parent().create('text', 'unmasked_callbacks')
        actual.text = 'def onCook(scriptOp): pass'
        previous = source.par.callbacks.val
        source.par.callbacks.val = actual.path
        with self.assertRaisesRegex(ValueError, 'Unmasked native packer'): assert_sparse_contract(op)
        source.par.callbacks.val = previous
        sink.inputs[0].par.chops.expr = "'/project1/merge2'"
        with self.assertRaisesRegex(ValueError, 'unreviewed source'): assert_sparse_contract(op)
