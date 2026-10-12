"""Seeded, reproducible long-running simulations of mixed controller actions."""
from copy import deepcopy
import json
import random
import unittest

from pixelblaze_mapper.mk2_workflow import Controller, validate_config


class MixedWorkflowSimulationTests(unittest.TestCase):
    def simulate(self, seed, steps=750):
        rng = random.Random(seed)
        now = [0.0]
        materials = [dict(id=f'm{i}', label=f'Material {i}', parameters=[
            dict(id=f'p{j}', label=f'Parameter {j}', value=.5, min=0, max=1,
                 step=.05, type='float', section='td' if j<8 else 'native')
            for j in range(count)]) for i, count in enumerate((8, 19, 70))]
        ctx = dict(mode='material', active_material=deepcopy(materials[0]),
                   catalog=deepcopy(materials), materials={m['id']:m for m in materials},
                   recording=False, transitions=['cut','crossfade','wipe'],
                   show=dict(id='c1', material=deepcopy(materials[1]),
                             parameters=deepcopy(materials[1]['parameters']), duration=10,
                             elapsed=0, transition='crossfade', transition_duration=1))
        c = Controller(clock=lambda:now[0])
        c.set_context(ctx)
        actions = set()
        for step in range(steps):
            now[0] += rng.choice((.01,.1,1,20.01))
            before = c.snapshot()
            command_list = c.tick()
            event_type = rng.randrange(8)
            if event_type < 3:
                name = rng.choice(('step','scene','browse','top','group','pad',
                                   'play','previous','next','restart','rec','erase'))
                index = rng.randrange(16 if name=='pad' else 8) if name in ('pad','top','group') else 0
                command_list += c.dispatch(dict(type='button', name=name, index=index, down=True))
                # Sometimes hold a key across events, including auto-repeat.
                if rng.randrange(4):
                    command_list += c.dispatch(dict(type='button', name=name, index=index, down=False))
            elif event_type == 3:
                command_list += c.dispatch(dict(type='wheel', delta=rng.choice((-127,-3,-1,1,3,127))))
            elif event_type == 4:
                command_list += c.dispatch(dict(type='wheel_press'))
            elif event_type == 5:
                command_list += c.dispatch(dict(type='encoder', index=rng.randrange(8),delta=rng.choice((-127,-1,1,127))))
            elif event_type == 6:
                for name,index in list(c.held):
                    command_list += c.dispatch(dict(type='button',name=name,index=index,down=False))
            else:
                ctx['mode'] = rng.choice(('material','show'))
                if rng.randrange(2):
                    ctx['recording'] = False  # Host reports automatic clip end.
                c.set_context(ctx)

            for command in command_list:
                action = command['action']
                actions.add(action)
                if action == 'set_mode':
                    ctx['mode'] = command['mode']
                elif action == 'load_material':
                    ctx['active_material'] = deepcopy(next(m for m in materials if m['id']==command['material_id']))
                elif action == 'set_parameter':
                    self.assertTrue(0 <= command['value'] <= 1, (seed,step,command))
                    for params in (ctx['active_material']['parameters'], ctx['show']['parameters']):
                        for p in params:
                            if p['id']==command['parameter_id']:
                                p['value'] = command['value']
                elif action == 'set_show_field':
                    self.assertTrue(before['show']['editing'], (seed,step))
                    ctx['show'][command['field']] = command['value']
                elif action == 'record_start':
                    self.assertEqual(c.mode, 'show', (seed,step))
                    ctx['recording'] = command['kind']
                elif action == 'record_stop':
                    ctx['recording'] = False
                elif action == 'persist_config':
                    prior = c.export_config()
                    validate_config(command['config'])
                    success = rng.randrange(5) != 0
                    c.dispatch(dict(type='command_result',request_id=command['request_id'],success=success,error='Simulated disk error'))
                    self.assertEqual(c.export_config(),command['config'] if success else prior)
            c.set_context(ctx)
            view = c.snapshot()
            with self.subTest(seed=seed,step=step,screen=view['screen']):
                self.assertIn(view['mode'],('material','show'))
                self.assertTrue(0<=view['bank']<8)
                self.assertTrue(0<=view['pad_index']<16)
                self.assertEqual(len(view['cards']),16)
                self.assertLessEqual(len(view['parameter_pages']),8)
                self.assertTrue(0<=view['show']['progress']<=1)
                self.assertGreaterEqual(view['show']['remaining'],0)
                self.assertEqual(c.export_config(),validate_config(json.loads(json.dumps(c.export_config(),allow_nan=False))))
                json.dumps(view,allow_nan=False)
        return actions

    def test_reproducible_mixed_navigation_and_external_changes(self):
        actions = set()
        for seed in (2,17,93,415,20261012):
            actions.update(self.simulate(seed))
        self.assertTrue({'set_mode','set_parameter','record_start','record_stop','transport'} <= actions)

    def test_empty_library_and_empty_show_stay_navigable(self):
        c = Controller()
        for mode in ('material','show'):
            c.set_context(dict(mode=mode,active_material={},show={},catalog=[]))
            for name in ('browse','scene','group','pad','top'):
                for index in (0,7,15):
                    for down in (True,False):
                        c.dispatch(dict(type='button',name=name,index=index,down=down))
                    c.dispatch(dict(type='wheel',delta=127))
                    c.dispatch(dict(type='wheel_press'))
                    self.assertEqual(len(c.snapshot()['cards']),16)


if __name__ == '__main__':
    unittest.main()
