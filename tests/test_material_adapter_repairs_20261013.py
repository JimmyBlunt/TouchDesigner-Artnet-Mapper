"""Permanent offline acceptance for semantic adapter repairs (no GPU access)."""

import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pixelblaze_mapper.madmapper_td_adapter import (
    ADAPTER_VERSION, adapt_material, prepared_shader_is_current,
)


class MaterialRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.audio_path = self.enterContext(patch('pixelblaze_mapper.madmapper_td_adapter._audio_texture_path',return_value=None))

    def adapt(self, fragment, vertex=None, metadata=None, roots=(), input_values=None):
        source = '/*' + json.dumps(metadata or {}) + '*/\n' + fragment
        path = self.root / 'fixture.fs'
        path.write_text(source, encoding='utf-8')
        if vertex is not None:
            (self.root / 'fixture.vs').write_text(vertex, encoding='utf-8')
        before = {p: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        result = adapt_material(path, roots,input_values=input_values)
        self.assertEqual(before, {p: p.read_bytes() for p in before}, 'source assets must not be rewritten')
        return result

    def assertBlocked(self, result, reason):
        self.assertFalse(result.adaptable)
        self.assertIsNone(result.shader)
        self.assertTrue(any(reason in item for item in result.reasons), result.reasons)

    def test_multiline_function_in_arguments_are_not_surface_inputs(self):
        body = '''vec4 fog(in vec3 rgb,
        in float distance,
        in vec3 rayOrigin) {return vec4(rgb*distance+rayOrigin,1);}
        vec4 materialColorForPixel(vec2 uv){return fog(vec3(uv,0),1.,vec3(0));}'''
        result = self.adapt(body)
        self.assertTrue(result.adaptable, result.reasons)
        self.assertIn(body, result.shader)

    def test_real_fragment_interfaces_still_require_vertex_support(self):
        for declaration in ('in vec3 light;', 'flat in vec3 light[8];',
                            'layout(location=0) in vec3 light;',
                            'in Data {vec3 light;} data;', 'in vec3 light, other;'):
            with self.subTest(declaration=declaration):
                result = self.adapt(declaration+'\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}')
                self.assertBlocked(result, 'vertex/surface varyings')

    def test_uniform_vertex_preserves_calculation_inputs_and_arrays(self):
        metadata = {'INPUTS': [{'NAME':'strength','TYPE':'float','DEFAULT':2.},
                               {'NAME':'tint','TYPE':'color','DEFAULT':[1,0,0,1]}],
                    'GENERATORS':[{'NAME':'phase','TYPE':'time_base','PARAMS':{'speed':'strength'}}]}
        vertex = '''flat out vec3 lights[2];
        void materialVsFunc(vec2 unused, in vec2 alsoUnused){
          lights[0]=tint.rgb*sin(phase); lights[1]=vec3(strength);
        }'''
        fragment = '''flat in vec3 lights[ 2 ];
        vec4 materialColorForPixel(vec2 uv){return vec4(lights[0]+lights[1],1);}'''
        result = self.adapt(fragment,vertex,metadata)
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('vec3 lights[2];',result.shader)
        self.assertNotIn('flat in',result.shader)
        self.assertNotIn('flat out',result.shader)
        self.assertIn('lights[0]=tint.rgb*sin(phase); lights[1]=vec3(strength);',result.shader)
        self.assertIn('float phase = uTDTime * (strength);',result.shader)
        self.assertEqual(['strength','tint'],[p.name for p in result.schema])
        self.assertEqual({'strength':'uMMParam000','tint':'uMMParam001'},result.bindings)
        self.assertLess(result.shader.index('materialVsFunc(vec2(0.0), vec2(0.0));'),
                        result.shader.index('fragColor = TDOutputSwizzle'))

    def test_empty_companion_is_safe(self):
        result = self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(uv,0,1);}',
                            'void materialVsFunc(vec2 unused){}')
        self.assertTrue(result.adaptable,result.reasons)

    def test_coordinate_dependent_vertex_is_blocked(self):
        result = self.adapt('in vec2 coord;\nvec4 materialColorForPixel(vec2 uv){return vec4(coord,0,1);}',
                            'out vec2 coord;\nvoid materialVsFunc(vec2 uv){coord=uv;}')
        self.assertBlocked(result,'requires a MadMapper vertex shader')

    def test_vertex_builtins_and_surface_branches_are_blocked_in_includes(self):
        for expression in ('float(gl_VertexID)', 'gl_Position.x', 'SURFACE_IS_quad'):
            with self.subTest(expression=expression):
                (self.root/'helper.glsl').write_text('float helper(){return '+expression+';}',encoding='utf-8')
                result = self.adapt('in float x;\nvec4 materialColorForPixel(vec2 uv){return vec4(x);}',
                    '#include "helper.glsl"\nout float x;\nvoid materialVsFunc(vec2 unused){x=helper();}')
                self.assertBlocked(result,'requires a MadMapper vertex shader')

    def test_vertex_argument_hidden_by_include_macro_is_not_treated_as_unused(self):
        (self.root/'helper.glsl').write_text('#define GET uv',encoding='utf-8')
        result = self.adapt('in vec2 x;\nvec4 materialColorForPixel(vec2 p){return vec4(x,0,1);}',
                            '#include "helper.glsl"\nout vec2 x;\nvoid materialVsFunc(vec2 uv){x=GET;}')
        self.assertBlocked(result,'requires a MadMapper vertex shader')

    def test_unrelated_library_argument_names_do_not_block_uniform_vertex(self):
        (self.root/'helper.glsl').write_text('float noise(vec2 uv){return sin(uv.x);}',encoding='utf-8')
        result=self.adapt('in float x;\nvec4 materialColorForPixel(vec2 uv){return vec4(x);}',
            '#include "helper.glsl"\nout float x;\nvoid materialVsFunc(vec2 uv){x=noise(vec2(1));}')
        self.assertTrue(result.adaptable,result.reasons)

    def test_vertex_argument_in_include_inside_entry_body_is_blocked(self):
        (self.root/'body.glsl').write_text('x=uv;',encoding='utf-8')
        result=self.adapt('in vec2 x;\nvec4 materialColorForPixel(vec2 p){return vec4(x,0,1);}',
            'out vec2 x;\nvoid materialVsFunc(vec2 uv){\n#include "body.glsl"\n}')
        self.assertBlocked(result,'requires a MadMapper vertex shader')

    def test_mismatched_interfaces_remain_blocked(self):
        for declaration in ('in vec3 missing;', 'in vec4 light;', 'in vec3 light[2];'):
            with self.subTest(declaration=declaration):
                result = self.adapt(declaration+'\nvec4 materialColorForPixel(vec2 uv){return vec4(1);}',
                                  'out vec3 light;\nvoid materialVsFunc(vec2 unused){light=vec3(1);}')
                self.assertBlocked(result,'vertex/surface varyings')

    def test_vertex_only_metadata_retains_native_controls_and_generators(self):
        meta = {'INPUTS':[{'NAME':'speed','TYPE':'float','DEFAULT':2}],
                'GENERATORS':[{'NAME':'phase','TYPE':'time_base','PARAMS':{'speed':'speed'}}]}
        result = self.adapt('in float x;\nvec4 materialColorForPixel(vec2 uv){return vec4(x);}',
            '/*'+json.dumps(meta)+'*/\nout float x;\nvoid materialVsFunc(vec2 unused){x=phase;}')
        self.assertTrue(result.adaptable,result.reasons)
        self.assertEqual(['speed'],[p.name for p in result.schema])
        self.assertIn('float phase = uTDTime * (speed);',result.shader)

    def test_conflicting_metadata_blocks_instead_of_choosing_different_controls(self):
        result = self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(1);}',
            '/*{"INPUTS":[{"NAME":"x","TYPE":"bool"}]}*/\nvoid materialVsFunc(vec2 unused){}',
            {'INPUTS':[{'NAME':'x','TYPE':'float'}]})
        self.assertBlocked(result,'conflicting fragment/vertex metadata: INPUTS')

    def test_lowering_does_not_fake_audio_feedback_or_generators(self):
        for metadata,reason in (
            ({'INPUTS':[{'NAME':'fft','TYPE':'audioFFT'}]},'requires audiofft input'),
            ({'RASTERISATION_SETTINGS':{'REQUIRES_LAST_FRAME':True}},'previous-frame feedback'),
            ({'GENERATORS':[{'NAME':'phase','TYPE':'animator'}]},'unsupported generator: animator'),
        ):
            with self.subTest(reason=reason):
                result = self.adapt('in float x;\nvec4 materialColorForPixel(vec2 uv){return vec4(x);}',
                    '/*'+json.dumps(metadata)+'*/\nout float x;\nvoid materialVsFunc(vec2 unused){x=phase;}')
                self.assertBlocked(result,reason)

    def test_unknown_vertex_signature_and_multiple_companions_are_blocked(self):
        fragment='vec4 materialColorForPixel(vec2 uv){return vec4(1);}'
        self.assertBlocked(self.adapt(fragment,'void materialVsFunc(out vec2 coord){}'),'vertex shader')
        (self.root/'second.vs').write_text('void materialVsFunc(){}',encoding='utf-8')
        self.assertBlocked(self.adapt(fragment,'void materialVsFunc(){}'),'vertex shader')

    def test_generator_roots_iterable_remains_available_after_vertex_validation(self):
        library=self.root/'Libraries'
        library.mkdir()
        (library/'math.glsl').write_text('float helper(){return 1.;}',encoding='utf-8')
        result=self.adapt('#include "math.glsl"\nvec4 materialColorForPixel(vec2 uv){return vec4(helper());}',
            'void materialVsFunc(vec2 unused){}',roots=(p for p in [self.root]))
        self.assertTrue(result.adaptable,result.reasons)

    def test_repaired_contract_invalidates_old_prepared_shaders(self):
        self.assertEqual(6,ADAPTER_VERSION)
        self.assertFalse(prepared_shader_is_current('// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 4'))
        self.assertFalse(prepared_shader_is_current('// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 5'))

    def test_render_size_tracks_actual_output_dimensions(self):
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(gl_FragCoord.xy/RENDERSIZE,0,1);}')
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('#define RENDERSIZE uTDOutputInfo.res.zw',result.shader)
        self.assertNotIn('#define RENDERSIZE vec2(512.0, 512.0)',result.shader)

    def test_source_repair_uses_original_hash_before_stripping_comments_and_keeps_warning(self):
        from pixelblaze_mapper.material_shader_repairs import REPAIRS,SourceRepair
        fragment='// reviewed original\nvec4 materialColorForPixel(vec2 uv){return vec4(1.);}'
        source='/*{}*/\n'+fragment
        repair=SourceRepair(hashlib.sha256(source.encode()).hexdigest(),'test-only exact repair',(('return vec4(1.);','return vec4(2.);'),))
        with patch.dict(REPAIRS,{'fixture.fs':repair}):
            result=self.adapt(fragment)
            changed=self.adapt(fragment+'\n')
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('return vec4(2.);',result.shader)
        self.assertTrue(any('test-only exact repair' in warning for warning in result.warnings))
        self.assertIn('return vec4(1.);',changed.shader)
        self.assertFalse(changed.warnings)

    def test_glass_garden_unroll_preserves_three_original_update_sequences(self):
        from pixelblaze_mapper.material_shader_repairs import REPAIRS
        rule=REPAIRS['Glass Garden.fs']
        old,new=next(pair for pair in rule.replacements if pair[0].startswith('for (int i'))
        statements=[line.strip() for line in old.splitlines()[1:-1]]
        self.assertEqual([line.strip() for line in new.splitlines()],statements*3)
        self.assertEqual(statements[0],'len = length(co);')
        self.assertTrue(statements[-1].startswith('co.y +='))
        self.assertNotIn('for (',new)

    def test_audio_file_inputs_bind_real_texture_and_preserve_live_smoothing_references(self):
        audio=self.root/'selected.mp3'; audio.write_bytes(b'fixture path; runtime validates decoding')
        self.audio_path.return_value=str(audio)
        metadata={'INPUTS':[
            {'NAME':'bins','TYPE':'int','DEFAULT':128,'MIN':1,'MAX':512},
            {'NAME':'attack','TYPE':'float','DEFAULT':0.2},
            {'NAME':'decay','TYPE':'float','DEFAULT':0.1},
            {'NAME':'release','TYPE':'float','DEFAULT':0.5},
            {'NAME':'fft','TYPE':'audioFFT','SIZE':'bins','ATTACK':'attack','DECAY':'decay','RELEASE':'release'},
            {'NAME':'wave','TYPE':'audio'},
        ]}
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(fft,uv)+texture(wave,uv);}',metadata=metadata,
                          input_values={'bins':64,'attack':0.3})
        self.assertTrue(result.adaptable,result.reasons)
        self.assertEqual(['bins','attack','decay','release'],[p.name for p in result.schema])
        fft=result.textures[0]
        self.assertEqual('audio_file',fft['source'])
        self.assertEqual(str(audio),fft['resolved_path'])
        self.assertEqual(('bins','attack','decay','release'),tuple(fft[k] for k in ('SIZE','ATTACK','DECAY','RELEASE')))
        self.assertEqual({'bins':64,'attack':0.3,'decay':0.1,'release':0.5},fft['_parameter_values'])
        self.assertEqual(result.bindings,fft['_parameter_uniforms'])
        self.assertIn('#define fft sTD2DInputs[0]',result.shader)
        self.assertIn('#define wave sTD2DInputs[1]',result.shader)

    def test_configured_audio_only_resolves_audio_not_external_image_inputs(self):
        self.audio_path.return_value=str(self.root/'selected.mp3')
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(fft,uv);}',metadata={'INPUTS':[
            {'NAME':'fft','TYPE':'audioFFT','SIZE':16}, {'NAME':'camera','TYPE':'image'}]})
        self.assertBlocked(result,'requires image input: camera')
        self.assertFalse(any('requires audiofft' in reason for reason in result.reasons))

    def test_invalid_audio_control_references_and_sizes_stay_blocked(self):
        self.audio_path.return_value=str(self.root/'selected.mp3')
        for field,value in (('SIZE',0),('SIZE',[]),('ATTACK','missing'),('RELEASE',-1),('DECAY',float('inf'))):
            with self.subTest(field=field,value=value):
                result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(fft,uv);}',metadata={'INPUTS':[
                    dict(NAME='fft',TYPE='audioFFT',**{field:value})]})
                self.assertBlocked(result,'audio '+field)

    def test_audio_sampler_index_follows_2d_assets_and_ignores_cube_count(self):
        self.audio_path.return_value=str(self.root/'selected.mp3')
        (self.root/'picture.png').write_bytes(b'fixture')
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(fft,uv)+texture(sky,vec3(uv,1))+texture(picture,uv);}',
            metadata={'IMPORTED':[self.cube('sky'),{'NAME':'picture','PATH':'picture.png'}],
                      'INPUTS':[{'NAME':'fft','TYPE':'audioFFT'}]})
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('#define sky sTDCubeInputs[0]',result.shader)
        self.assertIn('#define picture sTD2DInputs[0]',result.shader)
        self.assertIn('#define fft sTD2DInputs[1]',result.shader)

    def cube(self,name):
        faces=[name+suffix+'.png' for suffix in ('_px','_nx','_py','_ny','_pz','_nz')]
        for face in faces:
            (self.root/face).write_bytes(b'fixture asset; decoding belongs to runtime')
        return {'NAME':name,'TYPE':'cube','PATH':faces}

    def test_cube_faces_keep_order_and_sampler_indices_are_per_texture_type(self):
        a,b=self.cube('a'),self.cube('b')
        (self.root/'image.png').write_bytes(b'fixture')
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(a,vec3(uv,1))+texture(image,uv)+texture(b,vec3(uv,1));}',
            metadata={'IMPORTED':[a,{'NAME':'image','PATH':'image.png'},b]})
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('#define a sTDCubeInputs[0]',result.shader)
        self.assertIn('#define b sTDCubeInputs[1]',result.shader)
        self.assertIn('#define image sTD2DInputs[0]',result.shader)
        self.assertEqual([str((self.root/face).resolve()) for face in a['PATH']],result.textures[0]['resolved_paths'])
        self.assertEqual(result.textures[0]['resolved_paths'][0],result.textures[0]['resolved_path'])
        self.assertEqual('cube',result.textures[0]['TYPE'])

    def test_cube_missing_face_stays_blocked(self):
        cube=self.cube('sky')
        (self.root/cube['PATH'][3]).unlink()
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(sky,vec3(uv,1));}',metadata={'IMPORTED':[cube]})
        self.assertBlocked(result,'missing texture: sky_ny.png')

    def test_cube_malformed_face_list_and_3d_assets_stay_blocked(self):
        for kind,path,reason in (
            ('cube',['a.png']*5,'six ordered face paths'),
            ('cube',{'px':'a.png'},'six ordered face paths'),
            ('cube',['a.png']*5+[None],'six ordered face paths'),
            ('3d','volume.png','requires cube/3D texture'),
        ):
            with self.subTest(kind=kind,path=path):
                result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(sky,vec3(uv,1));}',metadata={'IMPORTED':[{'NAME':'sky','TYPE':kind,'PATH':path}]})
                self.assertBlocked(result,reason)

    def test_cube_does_not_satisfy_missing_external_image_input(self):
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return texture(sky,vec3(uv,1));}',
            metadata={'IMPORTED':[self.cube('sky')],'INPUTS':[{'NAME':'live_image','TYPE':'image'}]})
        self.assertBlocked(result,'requires image input: live_image')

    def test_legacy_texture_overloads_keep_arguments_and_use_modern_builtins(self):
        calls = {
            'textureCube(sky,direction)': 'texture(sky,direction)',
            'textureCube(sky,direction,bias)': 'texture(sky,direction,bias)',
            'texture2D(image,uv)': 'texture(image,uv)',
            'textureCubeLod(sky,direction,level)': 'textureLod(sky,direction,level)',
            'texture2DLod(image,uv,level)': 'textureLod(image,uv,level)',
            'textureCubeGradEXT(sky,direction,dx,dy)': 'textureGrad(sky,direction,dx,dy)',
            'texture2DGradEXT(image,uv,dx,dy)': 'textureGrad(image,uv,dx,dy)',
        }
        for old,new in calls.items():
            with self.subTest(call=old):
                (self.root/'legacy.glsl').write_text('vec4 legacy(){return '+old+';}',encoding='utf-8')
                result=self.adapt('#include "legacy.glsl"\nvec4 materialColorForPixel(vec2 uv){return legacy();}')
                self.assertTrue(result.adaptable,result.reasons)
                self.assertIn('return '+new+';',result.shader)
                self.assertNotIn(old,result.shader)

    def test_texture_rewrite_does_not_touch_similarly_named_identifiers(self):
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){float textureCubeCount=1.;return vec4(textureCubeCount);}')
        self.assertTrue(result.adaptable,result.reasons)
        self.assertIn('float textureCubeCount=1.',result.shader)

    def test_stateless_generators_keep_live_inputs_and_dependency_order(self):
        metadata={'INPUTS':[{'NAME':'gain','TYPE':'float','DEFAULT':2.}],
                  'GENERATORS':[
                      {'NAME':'product','TYPE':'multiplier','PARAMS':{'value1':'passthrough','value2':0.5}},
                      {'NAME':'passthrough','TYPE':'pass_thru','PARAMS':{'input_value':'clock'}},
                      {'NAME':'clock','TYPE':'time_base','PARAMS':{'speed':'gain'}},
                  ]}
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(product);}',metadata=metadata)
        self.assertTrue(result.adaptable,result.reasons)
        self.assertEqual({'gain':'uMMParam000'},result.bindings)
        self.assertIn('float clock = uTDTime * (gain);',result.shader)
        self.assertIn('float passthrough = float(clock);',result.shader)
        self.assertIn('float product = (float(passthrough)) * (0.5) * (1.0) * (1.0);',result.shader)
        self.assertLess(result.shader.index('float clock ='),result.shader.index('float passthrough ='))
        self.assertLess(result.shader.index('float passthrough ='),result.shader.index('float product ='))

    def test_stateless_generator_rejects_missing_vector_external_and_stateful_dependencies(self):
        cases=(
            ({'NAME':'result','TYPE':'pass_thru','PARAMS':{'input_value':'missing'}},'requires scalar input'),
            ({'NAME':'result','TYPE':'pass_thru','PARAMS':{'input_value':'color'}},'requires scalar input'),
            ({'NAME':'result','TYPE':'pass_thru','PARAMS':{'input_value':'/custom/BPM/bpm'}},'requires external channel'),
            ({'NAME':'result','TYPE':'multiplier','PARAMS':{'value1':2},'FILTERS':[]},'unsupported generator FILTERS'),
            ({'NAME':'result','TYPE':'multiplier','PARAMS':[]},'invalid generator parameters'),
        )
        for generator,reason in cases:
            with self.subTest(generator=generator):
                result=self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(result);}',metadata={
                    'INPUTS':[{'NAME':'color','TYPE':'color','DEFAULT':[1,1,1,1]}],
                    'GENERATORS':[generator]})
                self.assertBlocked(result,reason)

    def test_stateless_generator_cycles_block_instead_of_freezing_defaults(self):
        result=self.adapt('vec4 materialColorForPixel(vec2 uv){return vec4(a);}',metadata={'GENERATORS':[
            {'NAME':'a','TYPE':'pass_thru','PARAMS':{'input_value':'b'}},
            {'NAME':'b','TYPE':'multiplier','PARAMS':{'value1':'a'}},
        ]})
        self.assertBlocked(result,'cyclic generator dependency')


if __name__=='__main__':
    unittest.main()
