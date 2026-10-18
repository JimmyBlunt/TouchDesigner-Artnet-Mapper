"""Real receive-time replay and bounded host work for large-library browsing."""
import unittest
from unittest.mock import patch

from pixelblaze_mapper.mk2_workflow import Controller
from tests import test_mk2_favorites as favorites_fixture
from tests.test_mk2_favorites import button
from tests.test_mk2_runtime import FakeSurface


class BrowserSpeedTests(unittest.TestCase):
    def controller(self):
        c = Controller()
        c.set_context(dict(catalog=[dict(id=str(i), label=str(i)) for i in range(635)]))
        c.screen = 'browse'
        return c

    def replay(self, c, times, direction=1):
        positions = []
        for timestamp in times:
            self.assertEqual(c.dispatch(dict(type='wheel', delta=direction, timestamp=timestamp)), [])
            positions.append(c.browse_index)
        return positions

    def test_actual_mk2_fast_trace_accelerates_despite_jitter(self):
        c = self.controller()
        # Physical MK2 receive-time trace, 2026-10-15. Previous pairwise
        # threshold/reset logic failed to sustain fast movement on this burst.
        positions = self.replay(c, [0, .031, .187, .218, .281, .359, .437])
        self.assertGreaterEqual(positions[-1], 30)
        self.assertLess(positions[-1], 80)
        self.assertEqual(positions[:2], [1, 2])

    def test_speed_increases_distance_and_slow_turns_remain_exact(self):
        distances = []
        for interval in (.4, .14, .075, .035):
            c = self.controller()
            distances.append(self.replay(c, [i*interval for i in range(8)])[-1])
        self.assertEqual(distances[0], 8)
        self.assertEqual(sorted(set(distances)), distances)
        self.assertGreaterEqual(distances[-1], 80)

    def test_reversal_pause_and_slowdown_restore_single_detents(self):
        for ending in ('reverse','pause','slow'):
            c = self.controller()
            self.replay(c, [0,.04,.08,.12])
            before = c.browse_index
            self.replay(c, [.16] if ending == 'reverse' else [.6] if ending == 'pause' else [.35],
                        -1 if ending == 'reverse' else 1)
            self.assertEqual(c.browse_index-before, -1 if ending == 'reverse' else 1)


class BrowserBurstRuntimeTests(unittest.TestCase):
    setUp = favorites_fixture.FavoritesManagerTests.setUp

    def prepare(self):
        m = self.manager
        self.library._items = [dict(id='m%d'%i, label='%03d'%i) for i in range(635)]
        m.refresh_catalog()
        config = m.controller.export_config(); config['hardware'] = True
        m.controller.set_context(dict(config=config))
        button(m, 'browse')
        m.worker = FakeSurface()
        m.host.requests.clear()
        return m

    def test_twelve_received_events_publish_one_final_frame_with_two_host_reads(self):
        m = self.prepare()
        for i in range(12):
            m.events.put((dict(type='wheel',delta=1),m.version,99.1+i*.07))
        with patch('pixelblaze_mapper.mk2_runtime.time.monotonic',return_value=100.), \
             patch.object(m,'update_surface',wraps=m.update_surface) as publish:
            m.tick()
        self.assertEqual(m.events.qsize(),0)
        self.assertEqual(publish.call_count,1)
        self.assertEqual(len(m.host.requests),2)
        self.assertEqual(m.host.requests[-1],m.controller.browse_selected_id())
        self.assertEqual(m.worker.snapshot['controller']['browse_index'],m.controller.browse_index)
        self.assertGreaterEqual(m.controller.browse_index,70)
        self.assertFalse(m.host.commands)

    def test_press_after_burst_loads_final_selection_in_original_queue_order(self):
        m = self.prepare()
        # Slow timestamps keep expected selection at m1 after two entries.
        for i,t in enumerate((99.1,99.5)):
            m.events.put((dict(type='wheel',delta=1),m.version,t))
        m.events.put((dict(type='wheel_press'),m.version,99.9))
        with patch('pixelblaze_mapper.mk2_runtime.time.monotonic',return_value=100.):
            m.tick()
        self.assertEqual(m.host.commands[-1]['action'],'load_material')
        self.assertEqual(m.host.commands[-1]['material_id'],'m2')
        self.assertEqual(m.controller.browse_index,2)


if __name__ == '__main__':
    unittest.main()
