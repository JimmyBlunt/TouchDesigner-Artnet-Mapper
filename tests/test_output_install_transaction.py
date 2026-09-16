"""Reproducible installer fault injection on fake native graph/parameter objects."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

from tests.test_native_dmx_gate import Node as BaseNode, Parameter
from tools.install_completion_output import install_output

try:
    import numpy
except ImportError:
    numpy = None

ROOT = Path(__file__).resolve().parents[1]


class Children(dict):
    def __iter__(self): return iter(self.values())


class Parameters(NS):
    def __setattr__(self, name, value):
        previous = self.__dict__.get(name)
        if isinstance(previous, Parameter) and not isinstance(value, Parameter):
            previous.val = value
        else:
            super().__setattr__(name, value)


class Node(BaseNode):
    def __init__(self, name, kind='base', parent=None):
        super().__init__(name, kind, parent)
        self.children = Children()
        self.par = Parameters(**vars(self.par), callbacks=Parameter())
        self._text, self.fail_write_once, self.refuse_text = '# original ' + name, False, None
        self.rows = []
        self.family = 'DAT' if kind in ('text', 'table') else 'CHOP'
    @property
    def text(self): return self._text
    @text.setter
    def text(self, value):
        if value == self.refuse_text: raise RuntimeError('refused restoration')
        self._text = value
        if self.fail_write_once:
            self.fail_write_once = False
            raise RuntimeError('partial callback write')
    def create(self, kind, name):
        if name in self.children: raise RuntimeError('name collision')
        node = Node(name, kind, self)
        self.children[name] = node
        return node
    def __getitem__(self, key):
        row, col = key
        return self.rows[row][col]


@unittest.skipIf(numpy is None, 'Installer compiles NumPy-backed legacy callback')
class OutputInstallTransactionTests(unittest.TestCase):
    def setUp(self):
        self.project = Node('project1')
        self.router = self.project.create('base', 'multi_controller_output')
        for name in ('artnet_510_sender_callbacks', 'ui_callbacks', 'pack_test_callbacks'):
            self.router.create('text', name)
        config = self.router.create('table', 'controller_config')
        config.rows = [['name'], ['test']]
        config.numRows, config.numCols = 2, 1
        pack = self.router.create('script', 'pack_test')
        pack.par.callbacks = self.router.op('pack_test_callbacks').path
        for name, kind in (('esp_artnet_live_pack_callbacks', 'text'), ('esp_artnet_live_pack', 'script'),
                           ('esp_artnet_out', 'dmxout'), ('dmxout1', 'dmxout'), ('merge1', 'merge'), ('merge2', 'merge'),
                           ('shuffle1', 'shuffle'), ('math2', 'math'), ('select1', 'select'), ('select2', 'select'),
                           ('rename2', 'rename'), ('rename1', 'rename'), ('lookup1', 'lookup'), ('Universe_Config', 'constant')):
            self.project.create(kind, name)
        self.project.op('esp_artnet_live_pack_callbacks').text = json.loads(
            (ROOT / 'docs/completion-20260910/legacy-output-before.json').read_text())['pack']
        self.project.op('esp_artnet_live_pack').par.callbacks = '/project1/esp_artnet_live_pack_callbacks'
        connections = {'esp_artnet_out': ('esp_artnet_live_pack',), 'dmxout1': ('merge1',),
                       'shuffle1': ('merge2',), 'merge1': ('math2', 'select2'), 'math2': ('select1',),
                       'select1': ('rename2',), 'select2': ('rename2',), 'rename2': ('lookup1',),
                       'lookup1': ('Universe_Config', 'rename1'), 'rename1': ('shuffle1',)}
        for name, sources in connections.items(): self.project.op(name).inputs = [self.project.op(s) for s in sources]
        self.namespace = {'op': self.op, 'textDAT': 'text', 'scriptCHOP': 'script', 'constantCHOP': 'constant', 'selectCHOP': 'select'}
        self.fail_verification = False
        self.snapshot_calls = 0
    def op(self, path):
        return self.project if path == '/project1' else self.project.op(path.removeprefix('/project1/'))
    def snapshot(self):
        self.snapshot_calls += 1
        return {'hashes': {'routing': 'unchanged'}, 'errors': ['injected error'] if self.fail_verification and self.snapshot_calls % 2 == 0 else [],
                'sender': {'enabled': False}, 'native': {'esp': False, 'legacy': False}}
    def graph(self):
        nodes = list(self.project.children.values()) + list(self.router.children.values())
        return {node.path: {'text': node.text, 'inputs': [n.path for n in node.inputs],
                            'shape': deepcopy(node.storage)} for node in nodes}
    def install(self): return install_output(self.namespace, ROOT, snapshot=self.snapshot)

    def test_success_and_repeat_install_are_reproducible(self):
        result = self.install()
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(len(result['created_nodes']), 6)
        self.assertIn('legacy_source_mask', self.project.op('shuffle1').inputs[0].path)
        again = self.install()
        self.assertEqual(again['created_nodes'], [])
        self.assertEqual(again['callback_changes'], [])

    def test_unreviewed_legacy_baseline_fails_before_first_callback_write(self):
        self.project.op('esp_artnet_live_pack_callbacks').text = '# changed by user'
        before = self.graph()
        with self.assertRaisesRegex(ValueError, 'outside the reviewed'): self.install()
        self.assertEqual(self.graph(), before)

    def test_partial_callback_write_restores_all_texts_and_wires(self):
        before = self.graph()
        self.router.op('ui_callbacks').fail_write_once = True
        with self.assertRaisesRegex(RuntimeError, 'changes restored'): self.install()
        self.assertEqual(self.graph(), before)

    def test_gate_failure_removes_new_mask_and_restores_earlier_callbacks(self):
        before = self.graph()
        self.project.op('dmxout1').fail_connect = True
        with self.assertRaisesRegex(RuntimeError, 'changes restored'): self.install()
        self.assertEqual(self.graph(), before)

    def test_verification_failure_rolls_back_completed_install(self):
        before = self.graph()
        self.fail_verification = True
        with self.assertRaisesRegex(RuntimeError, 'changes restored'): self.install()
        self.assertEqual(self.graph(), before)

    def test_existing_gate_shape_is_restored_after_late_failure(self):
        self.install()
        self.project.op('esp_artnet_live_pack').rate = 90
        idle = self.project.op('esp_artnet_out_idle_black')
        self.assertEqual(idle.par.rate.eval(), 60)
        before = self.graph()
        self.fail_verification = True
        with self.assertRaisesRegex(RuntimeError, 'changes restored'): self.install()
        self.assertEqual(self.graph(), before)
        self.assertEqual(idle.par.rate.eval(), 60)

    def test_owned_name_collision_fails_before_mutation(self):
        self.project.create('text', 'legacy_source_mask_callbacks')
        before = self.graph()
        with self.assertRaisesRegex(ValueError, 'name collision'): self.install()
        self.assertEqual(self.graph(), before)

    def test_rollback_failure_is_explicit(self):
        node = self.router.op('ui_callbacks')
        node.refuse_text = node.text
        self.fail_verification = True
        with self.assertRaisesRegex(RuntimeError, 'ROLLBACK FAILED'): self.install()
