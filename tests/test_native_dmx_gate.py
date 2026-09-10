"""Offline graph contract; native TD cooking/byte parity require an isolated test."""
import unittest
from types import SimpleNamespace

from pixelblaze_mapper.native_dmx_gate import (
    KNOWN, SHAPE_KEY, install_known_sink_gates, install_sink_gates,
)


class Parameter:
    def __init__(self, value=0):
        self.val = value
        self.mode = 'ParMode.CONSTANT'
        self._expr = ''
        self.sequence = SimpleNamespace(numBlocks=1)

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, value):
        self._expr = value
        self.mode = 'ParMode.EXPRESSION'

    def eval(self):
        return self.val


class Connector:
    def __init__(self, node, index=0):
        self.node, self.index = node, index

    def disconnect(self):
        if len(self.node.inputs) > self.index:
            self.node.inputs[self.index] = None
            while self.node.inputs and self.node.inputs[-1] is None:
                self.node.inputs.pop()

    def connect(self, other):
        if other.node.fail_connect:
            other.node.fail_connect = False
            raise RuntimeError('simulated connection failure')
        while len(other.node.inputs) <= other.index:
            other.node.inputs.append(None)
        other.node.inputs[other.index] = self.node


class Node:
    def __init__(self, name, kind='base', parent=None):
        self.name, self.type, self._parent = name, kind, parent
        self.path = parent.path + '/' + name if parent else '/' + name
        self.children, self.storage = {}, {}
        self.inputs, self.comment, self.viewer = [], '', True
        self.rate, self.numSamples, self.numChans = 60, 510, 10
        self.data = [[i] * 510 for i in range(10)]
        self.fail_connect = False
        names = ('active', 'const0name', 'const0value', 'single', 'startunit',
                 'endunit', 'start', 'end', 'rate', 'timeslice', 'chops',
                 'srselect', 'scope', 'channames', 'renamefrom', 'renameto',
                 'filterdigits', 'stripdigits', 'align', 'autoprefix')
        self.par = SimpleNamespace(**{key: Parameter() for key in names})
        self.inputConnectors = [Connector(self, index) for index in range(3)]
        self.outputConnectors = [Connector(self)]

    def parent(self):
        return self._parent

    def create(self, kind, name):
        result = Node(name, kind, self)
        self.children[name] = result
        return result

    def op(self, path):
        result = self
        for part in path.split('/'):
            result = result.children.get(part)
            if result is None:
                break
        return result

    def chans(self):
        return [SimpleNamespace(name='Universe%d' % i) for i in range(self.numChans)]

    def store(self, key, value):
        self.storage[key] = value

    def fetch(self, key, default=None):
        return self.storage.get(key, default)

    def destroy(self):
        del self._parent.children[self.name]


class NativeDmxGateTests(unittest.TestCase):
    def setUp(self):
        self.project = Node('project1')
        self.router = self.project.create('base', 'multi_controller_output')
        self.pairs = []
        for (sink_path, source_path), count in zip(KNOWN, (10, 24, 10)):
            parent = self.router if '/' in sink_path else self.project
            sink = parent.create('dmxout', sink_path.split('/')[-1])
            source = parent.create('script', source_path.split('/')[-1])
            source.numChans = count
            source.data = [[i] * 510 for i in range(count)]
            sink.inputs = [source]
            self.pairs.append((sink, source, count))
        self.router.storage = {'routing-config-sentinel': ['unchanged']}

    def install(self):
        return install_known_sink_gates(self.project, constant_type='constant', select_type='select')

    def idle(self, sink):
        return sink.parent().op(sink.name + '_idle_black')

    def test_idle_black_shape_and_live_branch_are_exactly_scoped(self):
        report = self.install()
        self.assertEqual(len(report['created']), 6)
        self.assertFalse(report['active_parameters_changed'])
        for sink, source, count in self.pairs:
            gate = sink.inputs[0]
            idle = self.idle(sink)
            self.assertEqual(gate.inputs, [])
            self.assertEqual(gate.type, 'select')
            self.assertEqual(idle.par.const0name.val, 'Universe[0-%d]' % (count - 1))
            self.assertEqual((idle.par.start.val, idle.par.end.val, idle.par.const0value.val), (0, 509, 0))
            self.assertEqual((idle.par.startunit.val, idle.par.endunit.val), ('samples', 'samples'))
            self.assertEqual(idle.par.rate.val, source.rate)
            self.assertEqual(gate.par.srselect.val, 'err')
            self.assertFalse(gate.par.timeslice.val)
            self.assertEqual(gate.par.chops.expr, "%r if op(%r).par.active.eval() else %r" % (source.path, sink.path, idle.path))
            self.assertEqual(gate.par.channames.val, '*')
            self.assertEqual(gate.par.align.val, 'none')
            self.assertEqual(source.inputs, [])
        self.assertEqual(self.router.storage, {'routing-config-sentinel': ['unchanged']})

    def test_gate_decision_reads_actual_active_and_live_source_not_a_snapshot(self):
        self.install()
        sink, source, _ = self.pairs[0]
        gate = sink.inputs[0]
        calls = []
        def resolve(path):
            calls.append(path)
            if path != sink.path:
                raise AssertionError('Expression must not resolve either source')
            return sink
        namespace = {'op': resolve}
        sink.par.active.val = False
        self.assertEqual(eval(gate.par.chops.expr, namespace), self.idle(sink).path)
        source.data[0][0] = 231
        sink.par.active.val = True  # offline fake only; no hardware operator
        self.assertEqual(eval(gate.par.chops.expr, namespace), source.path)
        selected = {source.path: source}[eval(gate.par.chops.expr, namespace)]
        self.assertEqual(selected.data[0][0], 231)
        source.data[0][0] = 17
        self.assertEqual(selected.data[0][0], 17)
        self.assertEqual(calls, [sink.path] * 3)

    def test_active_value_expression_and_mode_remain_untouched(self):
        before = []
        for index, (sink, _, _) in enumerate(self.pairs):
            sink.par.active.val = bool(index)
            sink.par.active.expr = "op('my_control')['value']"
            before.append(vars(sink.par.active).copy())
        self.install()
        self.assertEqual(before, [vars(sink.par.active) for sink, _, _ in self.pairs])

    def test_second_install_is_noop_and_owned_shape_can_refresh(self):
        self.install()
        result = self.install()
        self.assertEqual(result['created'], [])
        self.assertEqual(result['updated_shapes'], [])
        sink, source, count = self.pairs[1]
        source.numChans = 28
        result = self.install()
        self.assertEqual(result['updated_shapes'], [self.idle(sink).path])
        self.assertEqual(self.idle(sink).fetch(SHAPE_KEY), {'count': 28, 'rate': 60.0})

    def test_last_sink_unknown_wiring_refuses_entire_batch_before_writes(self):
        self.pairs[-1][0].inputs = [self.router.create('constant', 'user_data')]
        with self.assertRaisesRegex(RuntimeError, 'Unknown sink wiring'):
            self.install()
        self.assertIs(self.pairs[0][0].inputs[0], self.pairs[0][1])
        self.assertFalse(any(name.endswith('_demand_gate') for name in self.project.children))

    def test_collision_and_edited_owned_nodes_are_not_overwritten(self):
        sink = self.pairs[-1][0]
        self.router.create('constant', sink.name + '_idle_black')
        with self.assertRaisesRegex(RuntimeError, 'collision'):
            self.install()
        self.router.children.pop(sink.name + '_idle_black')
        self.install()
        self.idle(sink).par.const0value.val = 1
        with self.assertRaisesRegex(RuntimeError, 'Modified gate parameter'):
            self.install()
        self.assertEqual(self.idle(sink).par.const0value.val, 1)

    def test_wired_select_or_modified_source_expression_refuses_rerun(self):
        self.install()
        sink, source, _ = self.pairs[0]
        gate = sink.inputs[0]
        gate.inputs = [source]
        with self.assertRaisesRegex(RuntimeError, 'Modified gate wiring'):
            self.install()
        self.assertEqual(gate.inputs, [source])
        gate.inputs = []
        gate.par.chops.expr = repr(source.path)
        with self.assertRaisesRegex(RuntimeError, 'Modified gate demand expression'):
            self.install()
        self.assertEqual(gate.par.chops.expr, repr(source.path))

    def test_wrong_shape_missing_node_and_wrong_owner_refuse(self):
        self.pairs[-1][1].numSamples = 512
        with self.assertRaisesRegex(ValueError, '510-sample'):
            self.install()
        self.pairs[-1][1].numSamples = 510
        self.pairs[-1][1].numChans = 0
        with self.assertRaisesRegex(ValueError, 'Positive explicit'):
            self.install()
        self.project.path = '/wrong'
        with self.assertRaisesRegex(ValueError, '/project1'):
            self.install()

    def test_construction_failure_restores_wires_and_removes_created_helpers(self):
        self.pairs[-1][0].fail_connect = True
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            self.install()
        for sink, source, _ in self.pairs:
            self.assertEqual(sink.inputs, [source])
            self.assertIsNone(sink.parent().op(sink.name + '_idle_black'))
            self.assertIsNone(sink.parent().op(sink.name + '_demand_gate'))

    def test_explicit_plan_capacity_used_without_reading_source_channels(self):
        sink, source, _ = self.pairs[1]
        source.numChans = 0  # a new builder packer has not cooked yet
        install_sink_gates([(sink, source, 24)], constant_type='constant', select_type='select')
        self.assertEqual(self.idle(sink).par.const0name.val, 'Universe[0-23]')


if __name__ == '__main__':
    unittest.main()
