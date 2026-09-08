import unittest
from types import SimpleNamespace as NS
from pixelblaze_mapper.routing_transaction import stop_outputs


class NativeStopTests(unittest.TestCase):
    def test_type_not_name_selects_outputs(self):
        native = NS(type='dmxout', name='custom_output', par=NS(active=True))
        helpers = [NS(type=t, name='dmxout_helper', par=NS()) for t in ('constant', 'select')]
        router = NS(op=lambda _: None, findChildren=lambda **_: [native, *helpers])
        stop_outputs(router)
        self.assertFalse(native.par.active)
        for node in helpers:
            self.assertFalse(hasattr(node.par, 'active'))
