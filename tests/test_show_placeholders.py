"""Offline graph tests: placeholder repair never rewires the real Show graph."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pixelblaze_mapper import build_show_sequencer as builder


class Node:
    def __init__(self, path, kind='base'):
        self.path, self.type = path, kind
        self.isTOP = kind in ('null', 'constant', 'glsl')
        self.children = {}
        self.inputs = []
        self.par = SimpleNamespace()
        self.comment = ''
        self.created = []
        self.inputConnectors = [self]
        self.outputConnectors = [SimpleNamespace(connect=self.connect)]

    def op(self, path):
        parts = path.split('/', 1)
        node = self.children.get(parts[0])
        return node.op(parts[1]) if node and len(parts) == 2 else node

    def add(self, name, kind):
        node = Node(self.path + '/' + name, kind)
        self.children[name] = node
        return node

    def create(self, kind, name):
        self.created.append(name)
        return self.add(name, kind)

    def connect(self, target):
        if self.path.rsplit('/', 1)[0] != target.path.rsplit('/', 1)[0]:
            raise AssertionError('cross-network wiring')
        target.inputs.append(self)


class ShowPlaceholderTests(unittest.TestCase):
    def setUp(self):
        self.owner = Node('/project1/show_control')
        self.targets = []
        for parent, names in [('slot_a_adapter', ['material_top_in']),
                              ('slot_b_adapter', ['material_top_in']),
                              ('transition_adapter', ['slot_a_in', 'slot_b_in', 'show_preview_out'])]:
            container = self.owner.add(parent, 'base')
            self.targets.extend(container.add(name, 'null') for name in names)
        self.real = self.owner.add('show_preview_out', 'null')
        self.real.inputs = [self.owner.add('show_transition_mixer', 'glsl')]
        self.owner.storage = {'production_connected': 1, 'transport': 'stopped'}

    def repair(self):
        with patch.object(builder, 'constantTOP', 'constant', create=True):
            return builder.repair_placeholder_inputs(self.owner)

    def test_five_known_empty_placeholders_get_three_shared_black_sources(self):
        report = self.repair()
        self.assertEqual(len(report['repaired']), 5)
        sources = {id(node.inputs[0]): node.inputs[0] for node in self.targets}
        self.assertEqual(len(sources), 3)
        for source in sources.values():
            self.assertEqual((source.par.colorr, source.par.colorg, source.par.colorb, source.par.alpha), (0, 0, 0, 0))
            self.assertEqual((source.par.resolutionw, source.par.resolutionh), (1, 1))
            self.assertEqual(source.par.outputresolution, 'custom')
        for node in self.targets:
            self.assertIn('UNCONNECTED PLACEHOLDER', node.comment)
        self.assertEqual(self.owner.storage, {'production_connected': 1, 'transport': 'stopped'})
        self.assertEqual(self.real.inputs[0].type, 'glsl')
        self.assertFalse(report['production_changed'])

    def test_existing_wiring_preserved_and_second_run_is_noop(self):
        custom = Node('/project1/show_control/slot_a_adapter/user_source', 'constant')
        self.targets[0].inputs = [custom]
        first = self.repair()
        self.assertEqual(len(first['repaired']), 4)
        self.assertIs(self.targets[0].inputs[0], custom)
        second = self.repair()
        self.assertEqual(second['repaired'], [])
        self.assertEqual(len(second['preserved_wired']), 5)

    def test_source_name_collision_fails_before_any_graph_write(self):
        adapter = self.owner.op('transition_adapter')
        adapter.add('unconnected_placeholder_black', 'constant')
        with self.assertRaisesRegex(RuntimeError, 'collision'):
            self.repair()
        self.assertTrue(all(not node.inputs for node in self.targets))
        self.assertTrue(all(not parent.created for parent in self.owner.children.values()))

    def test_wrong_owner_is_rejected(self):
        self.owner.path = '/project1/another_show'
        with self.assertRaisesRegex(ValueError, 'show_control'):
            self.repair()

    def test_user_replacement_node_type_is_not_touched(self):
        self.targets[0].type = 'glsl'
        report = self.repair()
        self.assertEqual(len(report['repaired']), 4)
        self.assertEqual(report['skipped'], ['slot_a_adapter/material_top_in'])
        self.assertEqual(self.targets[0].inputs, [])

    def test_modified_owned_black_source_is_not_silently_reset(self):
        self.repair()
        source = self.targets[0].inputs[0]
        source.par.colorr = .5
        self.targets[0].inputs.clear()
        with self.assertRaisesRegex(RuntimeError, 'modified'):
            self.repair()
        self.assertEqual(source.par.colorr, .5)
        self.assertEqual(self.targets[0].inputs, [])


if __name__ == '__main__':
    unittest.main()
