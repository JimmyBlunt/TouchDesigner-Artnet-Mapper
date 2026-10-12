from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import ast
import unittest

from pixelblaze_mapper import mk2_td as mk2, mk2_hooks, show_automation as auto, show_editor as editor
from pixelblaze_mapper.madmapper_parameters import parameter_schema, default_values
from pixelblaze_mapper.show_sequencer import Show, ShowSequencer


class Par:
    def __init__(self,value,lo=0,hi=4):
        self.val,self.normMin,self.normMax=value,lo,hi
    def eval(self):
        return self.val


class Fixture:
    def __init__(self):
        self.state={'recording':'0','recording_new':'0','selected':'0'}
        self.library_state={'selected_id':'one','active_id':'one'}
        self.active='one'
        self.schema=parameter_schema({'INPUTS':[
            {'NAME':'mat_gain','TYPE':'float','MIN':0,'MAX':5,'DEFAULT':1},
            {'NAME':'colour','TYPE':'color','DEFAULT':[.1,.2,.3,1]},
            {'NAME':'enabled','TYPE':'bool','DEFAULT':True},
            {'NAME':'mode','TYPE':'long','VALUES':['a','b','c'],'DEFAULT':0,'FLAGS':'generate_as_define'},
        ]})
        self.native={'one':default_values(self.schema),'two':default_values(self.schema)}
        self.controls=NS(par=NS(Source=Par('imported'),Speed=Par(1)))
        for key,name,_,lo,hi in mk2.CORE:
            setattr(self.controls.par,name,Par(.5 if key in ('focus_x','focus_y','width') else 1,lo,hi))
        self.switch=NS(choose=Mock(side_effect=lambda mode:setattr(self.controls.par.Source,'val','show' if mode=='show' else 'imported')))
        self.controls.op=lambda name:NS(module=self.switch)
        self.library=NS(_items=[dict(id=id,label=id.title(),groups=['Test']) for id in ('one','two')],
            _state=lambda k,d='':self.library_state.get(k,d),_set_state=lambda k,v:self.library_state.update({k:v}),
            _parameter_context=lambda item:(NS(schema=self.schema),self.native[item['id']]),
            activate_selected=Mock(side_effect=self.activate_shader),set_material_parameter=Mock(side_effect=self.set_native))
        self.runtime=NS(activate=Mock(side_effect=self.activate_state))
        cue=editor.new_cue('madmapper:one',editor.parameters_from_player(self.player_values()),name='One')
        self.document=dict(schema_version=2,name='Show',loop=True,cues=[cue])
        self.sequence=ShowSequencer(Show.from_dict(self.document))
        self.data=auto.empty()
        self.imported={cue['id']:dict(material_id='one',values=deepcopy(self.native['one']))}
        self.transport=NS(runtime=lambda:self.sequence,command=Mock(side_effect=self.command),
            _get=lambda k,d=0:dict(cue_index=self.sequence.cue_index,elapsed=self.sequence.elapsed,outgoing_slot='A').get(k,d))
        self.recorder=None
        self.editor=NS(_library=lambda:self.library,_library_item=lambda id:next(p for p in self.library._items if p['id']==id),
            current_material=lambda:('madmapper',self.active),player_values=self.player_values,
            _state=lambda k,d='':self.state.get(k,d),_set_state=lambda k,v:self.state.update({k:v}),
            show=lambda:deepcopy(self.document),automation_data=lambda:deepcopy(self.data),imported_data=lambda:deepcopy(self.imported),
            _write_automation=self.write_automation,start_recording=Mock(side_effect=self.start),stop_recording=Mock(side_effect=self.stop),
            _take=lambda:self.recorder,_effect_label=lambda name:name)
        self.owner=NS(op=lambda name:NS(module=self.editor if name=='editor_callbacks' else self.transport))
        self.timeline=NS(write=Mock(side_effect=self.write))
        self.host=mk2.Host(self.owner,resolve=lambda path:self.controls if path.endswith('controls') else NS(module=self.runtime),timeline_host=self.timeline)

    def player_values(self):
        return {k:p.eval() for k,p in vars(self.controls.par).items()}
    def activate_shader(self):
        self.library_state['active_id']=self.library_state['selected_id']
        return True
    def activate_state(self,key):
        self.active=key.partition(':')[2]
        self.controls.par.Source.val='imported'
    def set_native(self,name,component,value):
        if component is None:self.native[self.active][name]=value
        else:
            data=list(self.native[self.active][name]);data[component]=value;self.native[self.active][name]=data
    def command(self,name):
        getattr(self.sequence,name)()
    def write_automation(self,data):
        self.data=deepcopy(data)
    def write(self,show,data):
        old=self.sequence
        self.document=deepcopy(show);self.data=deepcopy(data)
        self.sequence=ShowSequencer(Show.from_dict(show));self.sequence.elapsed=old.elapsed;self.sequence.state=old.state
    def start(self,as_new_cue=False):
        if as_new_cue:
            cue=editor.new_cue('madmapper:'+self.active,editor.parameters_from_player(self.player_values()),name='New')
            self.document=editor.append_cue(self.document,cue)
            self.sequence=ShowSequencer(Show.from_dict(self.document));self.sequence.seek(len(self.document['cues'])-1,0)
        self.sequence.elapsed=0;self.sequence.play()
        cue=self.sequence.cue.id
        self.state.update(recording='1',recording_new='1' if as_new_cue else '0',record_cue=cue)
        self.recorder=auto.Recorder.from_state(auto.new_take(cue))
    def stop(self,reason=''):
        self.state['recording']='0'
        self.data=auto.merge(self.data,self.state['record_cue'],self.recorder.result())


class TDAdapterTests(unittest.TestCase):
    def setUp(self):self.f=Fixture();self.h=self.f.host
    def tearDown(self):mk2._host=None

    def test_first_eight_bind_real_master_not_material_speed(self):
        descriptors=self.h.context()['active_material']['parameters']
        self.assertEqual([p['id'] for p in descriptors[:8]],['global_master_speed','scale','width','focus_x','focus_y','zoom','intensity','contrast'])
        self.h.execute(dict(action='set_parameter',material_id='one',parameter_id='global_master_speed',value=2.5))
        self.assertEqual(self.f.controls.par.Globalmasterspeed.eval(),2.5)
        self.assertEqual(self.f.controls.par.Speed.eval(),1)

    def test_unclamped_factory_normal_range_does_not_limit_scale(self):
        par=self.f.controls.par.Scale
        par.val=4.;par.normMin=0.;par.normMax=1.;par.min=0.;par.max=1.;par.clampMin=False;par.clampMax=False
        descriptor=next(p for p in self.h.context()['active_material']['parameters'] if p['id']=='scale')
        self.assertGreater(descriptor['max'],4)
        self.h.execute(dict(action='set_parameter',material_id='one',parameter_id='scale',value=4+descriptor['step']))
        self.assertAlmostEqual(par.val,4.1)

    def test_typed_native_components_and_confirmed_only_load(self):
        self.h.context('two')
        self.f.library.activate_selected.assert_not_called()
        self.h.execute(dict(action='set_parameter',material_id='one',parameter_id='mat__colour__component_1',value=.7))
        self.assertEqual(self.f.native['one']['colour'],[.1,.7,.3,1])
        self.h.execute(dict(action='set_parameter',material_id='one',parameter_id='mat__enabled',value=.1))
        self.f.library.set_material_parameter.assert_called_with('enabled',None,0)
        before=deepcopy(self.f.native)
        with self.assertRaises(ValueError):self.h.execute(dict(action='set_parameter',material_id='two',parameter_id='mat_gain',value=2))
        self.assertEqual(self.f.native,before)

    def test_invalid_preset_never_publishes_or_mutates(self):
        for values in ({'unknown':1},{'scale':float('nan')}):
            with self.assertRaises(ValueError):self.h.execute(dict(action='load_material',material_id='two',values=values))
        self.f.library.activate_selected.assert_not_called()
        self.assertEqual(self.f.active,'one')

    def test_load_changes_shader_and_active_identity_and_restores_on_failure(self):
        self.h.execute(dict(action='load_material',material_id='two',values={'scale':3}))
        self.assertEqual(self.f.active,'two');self.assertEqual(self.f.controls.par.Scale.eval(),3)
        self.f.library.activate_selected.return_value=False
        self.f.library.activate_selected.side_effect=None
        with self.assertRaises(ValueError):self.h.execute(dict(action='load_material',material_id='one'))
        self.assertEqual(self.f.active,'two');self.assertEqual(self.f.library_state['selected_id'],'two')

    def test_step_routes_actual_source_and_recording_blocks_mode_and_load(self):
        self.h.execute(dict(action='set_mode',mode='show'))
        self.assertEqual(self.h.context()['mode'],'show')
        self.h.execute(dict(action='record_start',kind='automation'))
        for command in (dict(action='set_mode',mode='material'),dict(action='load_material',material_id='two')):
            with self.assertRaises(ValueError):self.h.execute(command)

    def test_show_encoder_locked_without_recording_and_compile_time_locked_during(self):
        self.f.controls.par.Source.val='show'
        command=dict(action='set_parameter',material_id='one',parameter_id='scale',value=2)
        with self.assertRaises(ValueError):self.h.execute(command)
        self.h.execute(dict(action='record_start',kind='automation'))
        self.h.execute(command)
        self.assertEqual(mk2.live_values(self.f.sequence.cue.id),{'scale':2})
        self.assertEqual(self.f.controls.par.Scale.eval(),1)
        with self.assertRaises(ValueError):self.h.execute(dict(command,parameter_id='mat__mode'))
        self.assertEqual(mk2.live_values('different-cue'),{})

    def test_live_show_context_is_automated_not_editor_controls(self):
        cue=self.f.sequence.cue.id
        self.f.data=auto.merge(self.f.data,cue,{'scale':[[0,2],[10,4]]})
        self.f.sequence.elapsed=5
        snapshot=self.h.context()
        self.assertEqual(next(p['value'] for p in snapshot['show']['parameters'] if p['id']=='scale'),3)
        self.assertEqual(next(p['value'] for p in snapshot['active_material']['parameters'] if p['id']=='scale'),1)
        self.f.sequence.play();self.f.sequence.pause();self.assertEqual(self.h.context()['show']['state'],'paused')

    def test_on_air_material_identity_does_not_follow_browser_selection(self):
        self.f.active='two';self.f.controls.par.Source.val='show'
        snapshot=self.h.context()
        self.assertEqual(snapshot['active_material']['id'],'two')
        self.assertEqual(snapshot['show']['material']['id'],'one')

    def test_core_cue_label_resolves_to_real_player_menu_identity(self):
        self.f.document['cues'][0]['effect']='Fluid Noise'
        self.f.editor._catalog=lambda:{'fluid_noise':dict(label='Fluid Noise',index=3)}
        self.f.sequence=ShowSequencer(Show.from_dict(self.f.document))
        snapshot=self.h.context()
        self.assertEqual(snapshot['show']['material_id'],'core:fluid_noise')
        self.assertEqual(snapshot['show']['material']['id'],'core:fluid_noise')
        self.assertEqual(len(snapshot['show']['parameters']),8)

    def test_clip_changes_validate_and_use_transport_preserving_writer(self):
        cue=self.f.sequence.cue.id
        self.f.sequence.play();self.f.sequence.elapsed=2
        self.h.execute(dict(action='set_show_field',cue_id=cue,field='duration',value=30))
        self.assertEqual(self.f.sequence.elapsed,2)
        self.assertEqual(self.f.document['cues'][0]['duration'],30)
        with self.assertRaises(ValueError):self.h.execute(dict(action='set_show_field',cue_id='stale',field='duration',value=9))
        with self.assertRaises(ValueError):self.h.execute(dict(action='set_show_field',cue_id=cue,field='transition',value='unknown'))
        self.assertEqual(self.f.timeline.write.call_count,1)

    def test_overdub_replaces_only_touched_tracks_and_removes_only_their_edit(self):
        self.f.controls.par.Source.val='show'
        cue=self.f.sequence.cue.id
        self.f.data=auto.merge(self.f.data,cue,{'scale':[[0,2],[4,3]],'width':[[0,.1],[4,.8]]})
        self.f.data['edits']={cue:{'scale':dict(points=[[0,4],[4,5]],mode='linear',enabled=True),
                                      'width':dict(points=[[0,.2],[4,.7]],mode='linear',enabled=True)}}
        old=deepcopy(self.f.data)
        self.h.execute(dict(action='record_start',kind='automation'))
        self.assertTrue(self.f.sequence.state.value=='playing')
        self.assertEqual(self.f.sequence.elapsed,0)
        self.h.execute(dict(action='set_parameter',material_id='one',parameter_id='scale',value=6))
        self.f.sequence.elapsed=1;self.h.sample(1)
        self.h.execute(dict(action='record_stop'))
        self.assertEqual(self.f.data['tracks'][cue]['width'],old['tracks'][cue]['width'])
        self.assertEqual(self.f.data['tracks'][cue]['scale'][-1],[1.,6.])
        self.assertNotIn('scale',self.f.data['edits'][cue])
        self.assertEqual(self.f.data['edits'][cue]['width'],old['edits'][cue]['width'])
        self.assertEqual(mk2.live_values(cue),{})

    def test_new_cue_uses_existing_recorder_and_all_eight_recordable(self):
        self.f.controls.par.Source.val='show'
        self.h.execute(dict(action='record_start',kind='new_cue'))
        self.f.editor.start_recording.assert_called_once_with(as_new_cue=True)
        cue=self.f.sequence.cue.id
        for key,_,_,lo,hi in mk2.CORE:
            self.h.execute(dict(action='set_parameter',material_id='one',parameter_id=key,value=(hi+lo)*.75))
        self.f.sequence.elapsed=1;self.h.sample(1)
        self.h.execute(dict(action='record_stop'))
        self.assertTrue(set(row[0] for row in mk2.CORE).issubset(self.f.data['tracks'][cue]))

    def test_vector_bool_round_trip_and_show_tone_no_double_core_application(self):
        schema=self.f.schema
        flattened={'mat__colour__component_1':.9,'mat__enabled':.1}
        expanded=mk2.expand_native(schema,flattened,self.f.native['one'])
        self.assertEqual(expanded['mat__colour'],[.1,.9,.3,1])
        self.assertIs(expanded['mat__enabled'],False)
        self.f.controls.par.Source.val='show'
        cue=self.f.sequence.cue.id
        self.f.data=auto.merge(self.f.data,cue,{'intensity':[[0,.5]],'contrast':[[0,2]]})
        self.assertEqual(mk2.show_value('intensity',1),.5)
        self.f.document['cues'][0]['effect']='Fill'
        self.assertEqual(mk2.show_value('intensity',1),1)

    def test_one_recorded_tone_control_preserves_other_cue_value_not_browser(self):
        self.f.controls.par.Source.val='show'
        self.f.document['cues'][0]['parameters']['contrast']=2.5
        self.f.controls.par.Contrast.val=.2
        cue=self.f.sequence.cue.id
        # Existing shows without a new tone lane keep their previous pipeline.
        self.assertEqual(mk2.show_value('contrast',.2),.2)
        self.assertEqual(mk2.show_import_tone(0),0)
        self.f.data=auto.merge(self.f.data,cue,{'intensity':[[0,.7]]})
        self.assertEqual(mk2.show_value('contrast',.2),2.5)
        self.assertEqual(mk2.show_import_tone(0),1)

    def test_master_phase_is_continuous_and_does_not_write_player(self):
        self.f.controls.par.Source.val='show'
        self.f.data=auto.merge(self.f.data,self.f.sequence.cue.id,{'global_master_speed':[[0,2]]})
        with patch.object(mk2.time,'monotonic',side_effect=[10,11,12]):
            self.assertEqual(mk2.show_phase(100),100)
            self.assertEqual(mk2.show_phase(101),102)
            self.assertEqual(mk2.show_phase(102),104)
        self.assertEqual(self.f.controls.par.Globalmasterspeed.eval(),1)

    def test_generated_editor_records_stops_and_replays_native_vector_and_core(self):
        """Execute shipped DAT functions plus installed hooks, not a fake recorder."""
        from pixelblaze_mapper.build_show_editor import EDITOR_RUNTIME
        from pixelblaze_mapper.show_timeline import install_editor_source
        source=install_editor_source(EDITOR_RUNTIME)
        before,tail=source.split(mk2_hooks.MARKER,1)
        wanted={'stop_recording','_write_uniforms','_effective_parameters','_imported_overrides'}
        # Use the actual original implementation of each; the outer MIDI layer
        # is tested separately and mk2_td's overrides bypass the MIDI gate.
        functions={}
        for node in ast.parse(before).body:
            if isinstance(node,ast.FunctionDef) and node.name in wanted:
                functions.setdefault(node.name,node)
        owner=NS(op=self.f.owner.op,unstore=Mock())
        scope=dict(automation=auto,editor=editor,OWNER=owner,TAKE_KEY='take',STATE_KEY='state',
            _state=self.f.editor._state,_set_state=self.f.editor._set_state,_take=self.f.editor._take,
            _write_automation=self.f.write_automation,automation_data=self.f.editor.automation_data,
            _cached_automation=self.f.editor.automation_data,_cached_show=self.f.editor.show,
            imported_data=self.f.editor.imported_data,_slot_cue_index=lambda slot:0,
            _store_state_in_cue=Mock(),_message=Mock(),_empty_reason=lambda:'empty',
            _material_phase=lambda:0,record_tick=Mock(),drive_imported_slots=Mock(),
            live_imported_values=lambda:{},_live_monitor=lambda values:values)
        exec(compile(ast.Module(body=list(functions.values()),type_ignores=[]),'<actual TD callbacks>','exec'),scope)
        exec(compile(tail,'<installed MK2 callbacks>','exec'),scope)
        self.f.editor.stop_recording=scope['stop_recording']
        self.f.controls.par.Source.val='show'
        cue=self.f.sequence.cue.id
        self.f.data=auto.merge(self.f.data,cue,{'width':[[0,.2],[5,.8]]})
        self.h.execute(dict(action='record_start',kind='automation'))
        for parameter,value in [('scale',3),('mat__colour__component_2',.9),('mat__enabled',0),('global_master_speed',2)]:
            self.h.execute(dict(action='set_parameter',material_id='one',parameter_id=parameter,value=value))
        self.f.sequence.elapsed=1
        scope['record_tick'](1)
        scope['stop_recording']('cue-ended')
        self.assertIsNone(self.h.take)
        self.assertEqual(self.f.data['tracks'][cue]['width'],[[0.,.2],[5.,.8]])
        # The playback path reconstructs vector components against THIS cue's
        # stored material values and writes the actual shader uniform slots.
        renderer=NS(name='slot_a_import',par=NS())
        for p in self.f.schema:
            for component in 'xyzw':setattr(renderer.par,'vec%dvalue%s'%(p.index+3,component),Par(-1))
        values=scope['_imported_overrides']('a',cue)
        scope['_write_uniforms'](renderer,NS(schema=self.f.schema),values)
        self.assertAlmostEqual(renderer.par.vec4valuez.val,.9)
        self.assertAlmostEqual(renderer.par.vec4valuex.val,.1)
        self.assertEqual(renderer.par.vec5valuex.val,0)
        self.assertEqual(renderer.par.vec6valuex.val,-1) # compile-time define untouched
        self.assertEqual(scope['_effective_parameters'](self.f.document['cues'][0],True)['scale'],3)
        self.assertEqual(scope['_effective_parameters'](self.f.document['cues'][0],False)['scale'],1)

    def test_hook_idempotence_and_missing_interface_refused(self):
        names=('record_tick','stop_recording','_store_state_in_cue','_effective_parameters','_write_uniforms','_material_phase')
        source='\n'.join('def '+name+'(*args,**kwargs): pass' for name in names)
        result=mk2_hooks.install_editor_source(source)
        self.assertEqual(mk2_hooks.install_editor_source(result),result)
        with self.assertRaises(ValueError):mk2_hooks.install_editor_source('')


if __name__=='__main__':unittest.main()
