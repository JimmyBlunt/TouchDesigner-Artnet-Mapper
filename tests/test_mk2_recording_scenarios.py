"""Connected, device-independent MK2 acceptance scenarios.

Controller events -> actual Host -> generated TD editor functions -> Recorder
-> persisted automation -> actual shader-uniform writer. Only TD operators,
the external clock and shader compilation are represented by in-memory fakes.
"""
import ast
from copy import deepcopy
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from tests.test_mk2_td import Fixture, Par
from pixelblaze_mapper import mk2_td, mk2_hooks, show_automation as auto, show_editor as editor
from pixelblaze_mapper.mk2_workflow import Controller
from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
from pixelblaze_mapper.show_timeline import install_editor_source
from pixelblaze_mapper.show_sequencer import ShowValidationError


class ConnectedRig:
    def __init__(self):
        self.f=Fixture()
        self.host=self.f.host
        self.storage={}
        self.messages=[]
        self.owner=NS(op=self.f.owner.op,store=lambda k,v:self.storage.update({k:v}),
                      fetch=lambda k,d=None:self.storage.get(k,d),unstore=lambda k:self.storage.pop(k,None))
        self.host.owner=self.owner
        self.f.transport._set=self.transport_set
        self.f.editor._state=lambda key,default='':str(self.f.state.get(key,default))
        self.f.library.parameter_snapshot=lambda:dict(material_id=self.f.active,label=self.f.active.title(),
             parameters=[dict(p.to_dict(),value=self.f.native[self.f.active][p.name]) for p in self.f.schema])
        self.install_editor()
        self.controller=Controller()
        self.refresh()

    def transport_set(self,key,value):
        if key=='cue_index':self.f.sequence.cue_index=int(value)
        elif key=='elapsed':self.f.sequence.elapsed=float(value)

    def write_show(self,document):
        # Model the actual transport runtime's table-backed index restoration;
        # its reconstruction deliberately pauses a previously playing show.
        index=self.f.sequence.cue_index
        self.f.write(document,self.f.data)
        self.f.sequence.cue_index=min(index,len(document['cues'])-1)
        self.f.sequence.elapsed=min(self.f.sequence.elapsed,self.f.sequence.cue.duration)
        self.f.sequence.pause()

    def install_editor(self):
        """Re-execute shipped callbacks against the same simulated COMP storage."""
        source=install_editor_source(EDITOR_RUNTIME)
        before,tail=source.split(mk2_hooks.MARKER,1)
        # Exercise the MK2 recording wrappers in this deliberately partial
        # fixture; the overlap suite executes the full editor hook chain.
        tail=tail.split('# SHOW_OVERLAP_EDITOR_V1',1)[0]
        selected={'_apply','start_recording','_arm','_disarm','_require_matching_material','_take',
                  'stop_recording','_store_state_in_cue','_live_state','_trim_new_cue','_remove_cue',
                  '_write_uniforms','_effective_parameters','_imported_overrides'}
        functions={}
        for node in ast.parse(before).body:
            if isinstance(node,ast.FunctionDef) and node.name in selected:
                functions.setdefault(node.name,node)
        f=self.f
        scope=dict(automation=auto,editor=editor,OWNER=self.owner,TAKE_KEY='take',STATE_KEY='live',RECORD_LIMIT=900.,ROW_COUNT=10,
            IMPORTED_CORE=('scale','width','zoom','focus_x','focus_y','hybrid_mix'),IMPORT_PREFIX=editor.IMPORT_PREFIX,
            ShowValidationError=ShowValidationError,
            current_material=lambda:('show','default') if f.controls.par.Source.eval()=='show' else ('madmapper',f.active),
            _state=f.editor._state,_set_state=f.editor._set_state,show=f.editor.show,write=self.write_show,
            _write_automation=f.write_automation,automation_data=f.editor.automation_data,
            _cached_automation=f.editor.automation_data,_cached_show=f.editor.show,
            imported_data=f.editor.imported_data,_write_imported=lambda data:setattr(f,'imported',deepcopy(data)),
            player_values=f.player_values,live_imported_values=lambda:{},
            _library=lambda:f.library,_library_item=f.editor._library_item,
            selected=lambda:int(f.state.get('selected',0)),unresolved=lambda show:[],
            _slot_cue_index=lambda slot:f.sequence.cue_index,_message=self.messages.append,
            _empty_reason=lambda:'Kein Regler bewegt',_material_phase=lambda:0.,record_tick=Mock(),
            drive_imported_slots=Mock(),_live_monitor=lambda values:values)
        exec(compile(ast.Module(body=list(functions.values()),type_ignores=[]),'<shipped TD editor>','exec'),scope)
        exec(compile(tail,'<installed MK2 editor hooks>','exec'),scope)
        self.scope=scope
        for name in ('current_material','start_recording','stop_recording','_take'):
            setattr(f.editor,name,scope[name])

    def refresh(self):
        c=self.controller
        target=None
        if c.screen=='browse':
            items=self.host._catalog_items()
            target=items[min(c.browse_index,len(items)-1)]['id']
        c.set_context(self.host.context(target))

    def send(self,event):
        self.refresh()
        commands=self.controller.dispatch(event)
        for command in commands:
            if command['action']=='persist_config':
                self.controller.dispatch(dict(type='command_result',request_id=command['request_id'],success=True))
            elif command['action']!='flash_pad':
                self.host.execute(command)
        self.refresh()
        return commands

    def down(self,name,index=0):return self.send(dict(type='button',name=name,index=index,down=True))
    def up(self,name,index=0):return self.send(dict(type='button',name=name,index=index,down=False))
    def press(self,name,index=0):
        commands=self.down(name,index)
        return commands+self.up(name,index)
    def encoder(self,index,delta):return self.send(dict(type='encoder',index=index,delta=delta))
    def step_show(self):
        if self.host.context()['mode']!='show':self.press('step')
    def overdub(self,reverse=False):
        self.step_show()
        first,second=('rec','erase') if reverse else ('erase','rec')
        self.down(first);self.down(second);self.up(second);self.up(first)
    def tick(self,seconds):
        self.f.sequence.elapsed=seconds
        self.scope['record_tick'](seconds)
        self.refresh()
    def uniforms(self):
        renderer=NS(name='slot_a_import',par=NS())
        for p in self.f.schema:
            for suffix in 'xyzw':setattr(renderer.par,'vec%dvalue%s'%(p.index+3,suffix),Par(-1))
        values=self.scope['_imported_overrides']('a',self.f.sequence.cue.id)
        self.scope['_write_uniforms'](renderer,NS(schema=self.f.schema),values)
        return renderer.par


class RecordingWorkflowScenarios(unittest.TestCase):
    def setUp(self):self.r=ConnectedRig()
    def tearDown(self):mk2_td._host=None

    def test_g01_g02_m03_step_external_source_and_browser_activation(self):
        r=self.r
        r.press('step')
        self.assertEqual(r.controller.mode,'show')
        self.assertEqual(r.controller.context['show']['material']['id'],'one')
        self.assertEqual(r.f.editor.current_material(),('madmapper','one'))
        r.press('browse')
        self.assertEqual(r.controller.screen,'home')
        r.press('step');r.press('browse')
        self.assertEqual(r.controller.screen,'browse')
        r.send(dict(type='wheel',delta=1))
        self.assertEqual(r.f.active,'one')
        r.send(dict(type='wheel_press'))
        self.assertEqual(r.f.active,'two')
        # External UI change, not an optimistic controller-mode toggle.
        r.f.controls.par.Source.val='show';r.refresh()
        self.assertEqual(r.controller.mode,'show')
        self.assertEqual(r.controller.context['active_material']['id'],'two')
        self.assertEqual(r.controller.context['show']['material']['id'],'one')

    def test_s06_s07_s09_encoder_lock_and_new_cue_full_record_stop_replay(self):
        r=self.r;r.step_show()
        before=deepcopy(r.f.document)
        self.assertEqual(r.encoder(1,20),[])
        self.assertEqual(r.f.document,before)
        r.down('rec')
        self.assertFalse(r.host.recording)
        r.up('rec')
        self.assertTrue(r.host.recording)
        self.assertEqual(len(r.f.document['cues']),2)
        cue=r.f.sequence.cue.id
        self.assertEqual(r.f.document['cues'][-1]['duration'],900)
        r.encoder(0,100);r.encoder(1,10)
        r.press('top',1)
        r.encoder(3,20);r.encoder(5,-1)
        r.tick(2.25)
        r.press('rec')
        self.assertFalse(r.host.recording)
        self.assertEqual(len(r.f.document['cues']),2)
        self.assertEqual(r.f.document['cues'][-1]['duration'],2.8)
        tracks=r.f.data['tracks'][cue]
        self.assertEqual(tracks['global_master_speed'][-1][1],2.)
        self.assertEqual(tracks['scale'][-1][1],2.)
        self.assertAlmostEqual(tracks['mat__colour__component_2'][-1][1],.5)
        self.assertEqual(tracks['mat__enabled'][-1][1],0.)
        self.assertAlmostEqual(r.uniforms().vec4valuez.val,.5)
        self.assertEqual(r.uniforms().vec5valuex.val,0.)
        with patch.object(mk2_td.time,'monotonic',side_effect=[10.,11.]):
            self.assertEqual(mk2_td.show_phase(100.),100.)
            self.assertEqual(mk2_td.show_phase(101.),102.)
        self.assertEqual(r.f.controls.par.Globalmasterspeed.eval(),1.)

    def test_s08_overdub_both_chord_orders_only_touched_parameter_curves(self):
        r=self.r;cue=r.f.sequence.cue.id
        r.f.data=auto.merge(r.f.data,cue,{'scale':[[0,1],[3,2]],'width':[[0,.1],[3,.9]]})
        r.f.data['edits']={cue:{'scale':dict(points=[[0,1],[3,4]],mode='linear',enabled=True),
                                    'width':dict(points=[[0,.2],[3,.8]],mode='linear',enabled=True)}}
        before=deepcopy(r.f.data)
        for reverse in (False,True):
            r.overdub(reverse)
            self.assertEqual(r.f.sequence.elapsed,0)
            self.assertEqual(r.controller.context['recording'],'automation')
            r.encoder(1,10);r.tick(1)
            r.down('erase');r.press('rec');r.up('erase')
            self.assertFalse(r.host.recording)
            self.assertEqual(len(r.f.document['cues']),1)
            self.assertEqual(r.f.data['tracks'][cue]['width'],before['tracks'][cue]['width'])
            self.assertEqual(r.f.data['edits'][cue]['width'],before['edits'][cue]['width'])
            self.assertNotIn('scale',r.f.data['edits'][cue])

    def test_s09_automatic_end_keeps_take_bound_to_original_cue(self):
        r=self.r
        next_cue=editor.new_cue('madmapper:two',editor.parameters_from_player(r.f.player_values()),name='Two')
        r.f.write(editor.append_cue(r.f.document,next_cue),r.f.data)
        first=r.f.sequence.cue.id
        r.overdub();r.encoder(1,5);r.tick(1)
        r.f.sequence.next()
        r.scope['record_tick'](.1);r.refresh()
        self.assertFalse(r.host.recording)
        self.assertIsNone(r.host.take)
        self.assertIn('scale',r.f.data['tracks'][first])
        self.assertNotIn(r.f.sequence.cue.id,r.f.data['tracks'])
        self.assertEqual(mk2_td.live_values(first),{})

    def test_g07_callback_reload_preserves_active_take_and_runtime_values(self):
        r=self.r;r.overdub();r.encoder(1,5);r.tick(.5)
        state_before=deepcopy(r.storage['take'])
        r.install_editor()
        self.assertEqual(r.storage['take'],state_before)
        r.encoder(1,5);r.tick(1);r.press('rec')
        values=r.f.data['tracks'][r.f.sequence.cue.id]['scale']
        self.assertEqual(values,[[0.,1.],[.5,1.5],[1.,2.]])

    def test_g07_full_host_recreation_preserves_overdub_and_untouched_tracks(self):
        r=self.r;cue=r.f.sequence.cue.id
        r.f.data=auto.merge(r.f.data,cue,{'width':[[0,.2],[5,.6]]})
        r.overdub();r.encoder(1,5);r.tick(.5)
        r.host=mk2_td.Host(r.owner,resolve=r.f.host.resolve,timeline_host=r.f.timeline)
        r.f.host=r.host
        self.assertEqual(r.host.take['kind'],'automation')
        self.assertEqual(r.host.values,{'scale':1.5})
        r.refresh();r.encoder(1,5);r.tick(1);r.press('rec')
        self.assertEqual(r.f.data['tracks'][cue]['width'],[[0.,.2],[5.,.6]])
        self.assertEqual(r.f.data['tracks'][cue]['scale'],[[0.,1.],[.5,1.5],[1.,2.]])
        self.assertNotIn(mk2_td.TAKE_STORAGE_KEY,r.storage)

    def test_g07_full_host_recreation_preserves_new_cue_length_and_native_take(self):
        r=self.r;r.step_show();r.press('rec');r.press('top',1);r.encoder(3,10);r.tick(.5)
        cue=r.f.sequence.cue.id
        r.host=mk2_td.Host(r.owner,resolve=r.f.host.resolve,timeline_host=r.f.timeline)
        r.f.host=r.host
        self.assertEqual(r.host.take['kind'],'new_cue')
        r.refresh();r.encoder(3,10);r.tick(2);r.press('rec')
        self.assertEqual(len(r.f.document['cues']),2)
        self.assertEqual(r.f.document['cues'][-1]['duration'],2.5)
        self.assertAlmostEqual(r.f.data['tracks'][cue]['mat__colour__component_2'][-1][1],.5)
        self.assertAlmostEqual(r.uniforms().vec4valuez.val,.5)
        self.assertNotIn(mk2_td.TAKE_STORAGE_KEY,r.storage)

    def test_s07_empty_new_cue_removed_and_unrelated_automation_preserved(self):
        r=self.r;first=r.f.sequence.cue.id
        r.f.data=auto.merge(r.f.data,first,{'width':[[0,.2],[5,.6]]})
        before=deepcopy(r.f.data)
        r.step_show();r.press('rec');r.tick(1);r.press('rec')
        self.assertEqual(len(r.f.document['cues']),1)
        self.assertEqual(r.f.data,before)
        self.assertFalse(r.host.recording)

    def test_g08_native_load_failure_rolls_back_source_cache_and_parameters(self):
        r=self.r;r.step_show()
        failed=[False]
        def native(name,component,value):
            if r.f.active=='two' and not failed[0]:
                failed[0]=True;raise ValueError('simulated shader rejection')
            return r.f.set_native(name,component,value)
        r.f.library.set_material_parameter.side_effect=native
        with self.assertRaises(ValueError):
            r.host.execute(dict(action='load_material',material_id='two',values={'scale':3,'mat_gain':2}))
        r.refresh()
        self.assertEqual(r.f.controls.par.Source.eval(),'show')
        self.assertEqual(r.controller.context['active_material']['id'],'one')
        self.assertEqual(r.f.controls.par.Scale.eval(),1)
        self.assertEqual(r.controller.context['show']['material']['id'],'one')

    def test_s04_show_wheel_changes_immediately_before_edit_exit(self):
        r=self.r;r.step_show()
        initial=r.f.document['cues'][0]['duration']
        r.send(dict(type='wheel_press'))
        r.send(dict(type='wheel',delta=10))
        self.assertTrue(r.controller.show_editing)
        self.assertEqual(r.f.document['cues'][0]['duration'],initial+1)
        r.send(dict(type='wheel_press'))
        r.send(dict(type='wheel',delta=1)) # transition type
        old=r.f.document['cues'][0]['transition']
        r.send(dict(type='wheel_press'));r.send(dict(type='wheel',delta=1))
        self.assertNotEqual(r.f.document['cues'][0]['transition'],old)
        r.send(dict(type='wheel_press'));r.send(dict(type='wheel',delta=1)) # transition duration
        r.send(dict(type='wheel_press'));r.send(dict(type='wheel',delta=10))
        self.assertGreaterEqual(r.f.document['cues'][0]['transition_duration'],1)

    def test_s10_transport_and_mode_navigation_locked_only_during_recording(self):
        r=self.r
        second=editor.new_cue('madmapper:two',editor.parameters_from_player(r.f.player_values()),name='Two')
        r.f.write(editor.append_cue(r.f.document,second),r.f.data)
        r.step_show();r.press('play');r.press('next')
        self.assertEqual(r.f.sequence.cue_index,1)
        r.press('previous');self.assertEqual(r.f.sequence.cue_index,0)
        r.f.sequence.elapsed=4;r.press('restart')
        self.assertEqual((r.f.sequence.cue_index,r.f.sequence.elapsed),(0,0))
        r.overdub()
        for name in ('step','next','previous','restart','play','browse','scene'):
            self.assertEqual(r.press(name),[])
        self.assertTrue(r.host.recording)
        r.press('rec');r.press('next')
        self.assertEqual(r.f.sequence.cue_index,1)

    def test_s09_callback_sampling_error_disarms_without_erasing_untouched_curve(self):
        r=self.r;cue=r.f.sequence.cue.id
        r.f.data=auto.merge(r.f.data,cue,{'width':[[0,.1],[5,.7]]})
        original=deepcopy(r.f.data['tracks'][cue]['width'])
        r.overdub();r.encoder(1,5);r.tick(1)
        with patch.object(r.host,'sample',side_effect=ValueError('simulated clock failure')):
            r.scope['record_tick'](2)
        r.refresh()
        self.assertFalse(r.host.recording)
        self.assertIsNone(r.host.take)
        self.assertEqual(r.f.data['tracks'][cue]['width'],original)
        self.assertTrue(any('simulated clock failure' in message for message in r.messages))


if __name__=='__main__':unittest.main()
