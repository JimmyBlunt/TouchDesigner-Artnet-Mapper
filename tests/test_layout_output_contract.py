"""Only the reviewed lookup endpoint may vary with active source capacity."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from pixelblaze_mapper.build_layout_apply import _output_parameter_contract


def parameter(value, *, name='index2', expression='me.inputs[1].numSamples-1',
              mode='ParMode.EXPRESSION', bind=None):
    return SimpleNamespace(name=name, style='Float', expr=expression, mode=mode,
                           bindExpr=bind, eval=Mock(return_value=value))


def contract(par, *, path='/project1/lookup1', resolve=lambda path: None):
    return _output_parameter_contract(SimpleNamespace(path=path, pars=lambda: [par]), resolve)


class LayoutOutputContractTests(unittest.TestCase):
    def test_canonical_endpoint_survives_panel3_source_capacity_growth(self):
        before = parameter(4482 * 3 - 1)
        after = parameter(5362 * 3 - 1)
        self.assertEqual(contract(before), contract(after))
        data, references = contract(after)
        self.assertEqual(data['index2'], {
            'value': None, 'expression': 'me.inputs[1].numSamples-1',
            'bind_expression': None, 'mode': 'ParMode.EXPRESSION'})
        self.assertEqual(references, {})
        # Reading the derived endpoint can demand-cook a temporarily stale
        # legacy branch. Structural capture must not need that evaluated value.
        before.eval.assert_not_called()
        after.eval.assert_not_called()

    def test_changed_expression_mode_or_binding_is_still_a_contract_change(self):
        baseline = contract(parameter(13445))
        for options in ({'expression': 'me.inputs[1].numSamples-2'},
                        {'expression': 'me.inputs[0].numSamples-1'},
                        {'mode': 'ParMode.CONSTANT'},
                        {'mode': 'ParMode.BIND'},
                        {'bind': 'op("other").par.index2'}):
            with self.subTest(options=options):
                self.assertNotEqual(baseline, contract(parameter(13445, **options)))

    def test_exception_does_not_extend_to_other_nodes_or_parameters(self):
        for path, name in (('/project1/other_lookup', 'index2'),
                           ('/project1/lookup1', 'index1')):
            with self.subTest(path=path, name=name):
                before, after = parameter(13445, name=name), parameter(16085, name=name)
                self.assertNotEqual(contract(before, path=path), contract(after, path=path))
                before.eval.assert_called_once()
                after.eval.assert_called_once()

    def test_constant_or_unreviewed_expression_values_remain_bound(self):
        for options in ({'mode': 'ParMode.CONSTANT'},
                        {'expression': 'op("other").numSamples-1'}):
            with self.subTest(options=options):
                self.assertNotEqual(contract(parameter(13445, **options)),
                                    contract(parameter(16085, **options)))

    def test_other_expression_driven_controls_and_referenced_dat_content_remain_bound(self):
        gain_before = parameter(.5, name='gain', expression='op("level")[0]')
        gain_after = parameter(.9, name='gain', expression='op("level")[0]')
        self.assertNotEqual(contract(gain_before), contract(gain_after))
        dat = SimpleNamespace(path='/project1/config', type='table', family='DAT', text='before')
        selector = parameter(dat.path, name='table', expression=None, mode='ParMode.CONSTANT')
        before = contract(selector, resolve=lambda path: dat)
        dat.text = 'after'
        after = contract(selector, resolve=lambda path: dat)
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1], after[1])


if __name__ == '__main__':
    unittest.main()
