// PIXELBLAZE_MADMAPPER_ADAPTER_VERSION 6
// Prepared from a MadMapper material for TouchDesigner GLSL TOP.
out vec4 fragColor;
uniform vec4 uTDMaterial0; // phase, scale, width, frame zoom
uniform vec4 uTDMaterial1; // focus x, focus y, reserved, reserved
uniform vec4 uTDCoordinate; // mode, panel columns, panel rows, hybrid mix
#define uTDTime uTDMaterial0.x
#define TIME uTDTime
#define TIMEDELTA (1.0 / 60.0)
#define FRAMEINDEX int(uTDTime * 60.0)
#define RENDERSIZE uTDOutputInfo.res.zw
#define DATE vec4(0.0)
#define IMG_NORM_PIXEL(image, coord) texture(image, coord)
#define isf_FragNormCoord vUV.st
#define IMG_PIXEL(image, coord) texture(image, (coord) / vec2(textureSize(image, 0)))
#define IMG_SIZE(image) vec2(textureSize(image, 0))
#define texture2D texture

vec2 mapMadMapperUV(vec2 uv)
{
    vec2 focus = clamp(uTDMaterial1.xy, vec2(0.0), vec2(1.0));
    float zoom = clamp(uTDMaterial0.w, 0.25, 8.0);
    float scale = max(uTDMaterial0.y, 0.01) / 4.0;
    float width = clamp(uTDMaterial0.z, 0.01, 1.0);
    vec2 framed = focus + (uv - vec2(0.5)) / zoom;
    framed = focus + (framed - focus) * vec2(scale * (0.5 / width), scale);
    // True global/panel-local/hybrid selection happens in the downstream
    // per-LED sampler, where the physical panel ID is available.
    return framed;
}

uniform vec4 uMMParam000; // native input: mat_scale
float mat_scale = uMMParam000.x;
uniform vec4 uMMParam001; // native input: mat_rotate
float mat_rotate = uMMParam001.x;
uniform vec4 uMMParam002; // native input: mat_shift_amount
vec2 mat_shift_amount = uMMParam002.xy;
uniform vec4 uMMParam003; // native input: mat_shift_scale
float mat_shift_scale = uMMParam003.x;
uniform vec4 uMMParam004; // native input: mat_shift_type
int mat_shift_type = int(round(uMMParam004.x));
uniform vec4 uMMParam005; // native input: mat_mirror_x
bool mat_mirror_x = uMMParam005.x > 0.5;
uniform vec4 uMMParam006; // native input: mat_mirror_y
bool mat_mirror_y = uMMParam006.x > 0.5;
uniform vec4 uMMParam007; // native input: mat_fov
float mat_fov = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_distort1
float mat_distort1 = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_distort2
float mat_distort2 = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_distort3
float mat_distort3 = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_thickness
float mat_thickness = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_hole_size
float mat_hole_size = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_iterations
int mat_iterations = int(round(uMMParam013.x));
uniform vec4 uMMParam014; // native input: mat_spin_speed
float mat_spin_speed = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_spin_bpm_sync
bool mat_spin_bpm_sync = uMMParam015.x > 0.5;
uniform vec4 uMMParam016; // native input: mat_spin_reverse
bool mat_spin_reverse = uMMParam016.x > 0.5;
uniform vec4 uMMParam017; // native input: mat_spin_offset
float mat_spin_offset = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_spin_offset_scale
float mat_spin_offset_scale = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_spin_strob
float mat_spin_strob = uMMParam019.x;
uniform vec4 uMMParam020; // native input: mat_spin_restart
int mat_spin_restart = int(round(uMMParam020.x));
uniform vec4 uMMParam021; // native input: mat_speed
float mat_speed = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam022.x > 0.5;
uniform vec4 uMMParam023; // native input: mat_reverse
bool mat_reverse = uMMParam023.x > 0.5;
uniform vec4 uMMParam024; // native input: mat_offset
float mat_offset = uMMParam024.x;
uniform vec4 uMMParam025; // native input: mat_offset_scale
float mat_offset_scale = uMMParam025.x;
uniform vec4 uMMParam026; // native input: mat_strob
float mat_strob = uMMParam026.x;
uniform vec4 uMMParam027; // native input: mat_restart
int mat_restart = int(round(uMMParam027.x));
uniform vec4 uMMParam028; // native input: mat_fog_alpha
bool mat_fog_alpha = uMMParam028.x > 0.5;
uniform vec4 uMMParam029; // native input: mat_front_color
vec4 mat_front_color = uMMParam029;
uniform vec4 uMMParam030; // native input: mat_back_color
vec4 mat_back_color = uMMParam030;
uniform vec4 uMMParam031; // native input: mat_brightness
float mat_brightness = uMMParam031.x;
uniform vec4 uMMParam032; // native input: mat_contrast
float mat_contrast = uMMParam032.x;
uniform vec4 uMMParam033; // native input: mat_saturation
float mat_saturation = uMMParam033.x;
uniform vec4 uMMParam034; // native input: mat_hue_shift
float mat_hue_shift = uMMParam034.x;
uniform vec4 uMMParam035; // native input: mat_invert
bool mat_invert = uMMParam035.x > 0.5;
uniform vec4 uMMParam036; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam036.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);
float mat_spin_time_source = uTDTime * (mat_spin_speed);

// BEGIN MadCommon.glsl
/*
MadCommon Glsl Library

Copyright (c) 2016, Garage Cube, All rights reserved.
Copyright (c) 2016, Simon Geilfus, All rights reserved.

Portions of code from Romain Dura see corresponding licence

Redistribution and use in source and binary forms, with or without modification, are permitted provided that
the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and
 the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/

//! Constants
#define PI 3.1415926535897932384626433832795

//! Returns the luminance of a RGB color
float luma( vec3 color );

//! Returns the luminance of a RGB color
float luminance( vec3 color );

//! Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range );

//! Luminance based rgb8/linear conversion
vec3 rgbToLinear( vec3 color, vec3 range );

//! Contrast, saturation, brightness, For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness );

//! Returns HSV values for RGB input color
vec3 rgb2hsv( vec3 color );

//! Returns RGB values for HSV input color
vec3 hsv2rgb( vec3 color );

//! Returns the Hue value for RGB input color
float rgb2hue( vec3 color );

//! Usefull shortcuts
#define saturate(x) clamp( x, 0.0, 1.0 )
#define lerp(x,y,t) mix( x, y, t )

// Implementation

// Luminance
float luma( vec3 color )
{
    // Rec 709 Coefficients
    return dot( color, vec3( 0.2126729, 0.7151522, 0.0721750 ) );
}
float luminance( vec3 color )
{
    return dot( color, vec3( 0.299, 0.587, 0.114 ) );
}

// Luminance based rgb8/linear conversion
vec3 linearToRgb( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) - vec3( luminance( color ) ) / range );
}

vec3 rgbToLinear( vec3 color, vec3 range )
{
    return ( color ) / ( vec3( 1.0 ) + vec3( luminance( color ) ) / range );
}

// RGB <-> HSV Conversion functions
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    //vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    //vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    vec4 p = c.g < c.b ? vec4(c.bg, K.wz) : vec4(c.gb, K.xy);
    vec4 q = c.r < p.x ? vec4(p.xyw, c.r) : vec4(c.r, p.yzx);
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float rgb2hue(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return abs(q.z + (q.w - q.y) / (6.0 * d + e));
}

/*
** Copyright (c) 2012, Romain Dura romain@shazbits.com
** 
** Permission to use, copy, modify, and/or distribute this software for any 
** purpose with or without fee is hereby granted, provided that the above 
** copyright notice and this permission notice appear in all copies.
** 
** THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES 
** WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF 
** MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY 
** SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
** WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
** ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR 
** IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
*/


/*
** Contrast, saturation, brightness
** Code of this function is from TGM's shader pack
** http://irrlicht.sourceforge.net/phpBB2/viewtopic.php?t=21057
*/

// For all settings: 1.0 = 100% 0.5=50% 1.5 = 150%
vec3 applyContrastSaturationBrightness( vec3 color, float contrast, float saturation, float brightness )
{
    // Increase or decrease theese values to adjust r, g and b color channels seperately
    const float AvgLumR = 0.5;
    const float AvgLumG = 0.5;
    const float AvgLumB = 0.5;
    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    
    vec3 AvgLumin = vec3(AvgLumR, AvgLumG, AvgLumB);
    vec3 brtColor = color * brightness;
    vec3 intensity = vec3(dot(brtColor, LumCoeff));
    vec3 satColor = mix( intensity, brtColor, saturation );
    vec3 conColor = mix( AvgLumin, satColor, contrast );
    return conColor;
}
// END MadCommon.glsl

float mat_time = mat_time_source - mat_offset * 8. * mat_offset_scale;
float mat_spin_time = mat_spin_time_source - mat_spin_offset * 8. * mat_spin_offset_scale;

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
}

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec2 mirrorUV(vec2 uv) {
    uv += vec2(0.5);
    if (mat_mirror_x) {
        if (uv.x > 0.5)   {
            uv.x = 1.0-uv.x;
        }
    }
    if (mat_mirror_y) {
        if (uv.y > 0.5) {
            uv.y = 1.0-uv.y;
        }
    }
    uv -= vec2(0.5);
    return uv;
}

vec2 transformUV(vec2 uv) {

    if (mat_lock_aspect) {
        uv.x *= RENDERSIZE.x / RENDERSIZE.y;
    }
    uv *= mat_scale * 2.5;

    uv = mirrorUV(uv);

    vec2 uv_shift = mat_shift_amount * mat_shift_scale;
    uv_shift += vec2(0.5);
    uv_shift.x = 1.-uv_shift.x;
    uv_shift -= vec2(0.5);

    
    if (mat_shift_type == 0) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, -1. * 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    uv += vec2(0.5);
    uv = matRot2D(uv, 2*PI*mat_rotate / 360);
    uv -= vec2(0.5);

    
    if (mat_shift_type == 1) {

        
        uv_shift += vec2(0.5);
        uv_shift = matRot2D(uv_shift, 2*PI*(mat_rotate) / 360);
        uv_shift -= vec2(0.5);
        uv += uv_shift;
    }

    return uv;
}


#define NEAR_CLIPPING_PLANE 0.1
#define FAR_CLIPPING_PLANE 100.0
#define MAX_MARCH_STEPS mat_iterations
#define EPSILON 0.01
#define DISTANCE_BIAS 0.7


#define SPIN_SPEED 0.6
#define MOVE_SPEED 2.5

#define BEAM_WIDTH 0.4 * mat_hole_size


mat2 rotmat(float a) {
    return mat2(cos(a), -sin(a), sin(a), cos(a));
}




float opS( float d1, float d2 ) {return max(-d1,d2);}

float sdBox( vec3 p, vec3 b )
{
  vec3 d = abs(p) - b;
  return min(max(d.x,max(d.y,d.z)),0.0) + length(max(d,0.0));
}

float opU( float d1, float d2 ) { return min(d1,d2);}



float sdBuilding(vec3 p) 
{

    vec3 b = vec3(0.0, 2.0, 0.0);
    vec3 b2 = vec3(1.1, 1.1, 1.1);

    vec3 translate = vec3(0.0, 0.0, 16.0);

    vec3 pos = p - translate;
    vec3 pos2 = pos;
    vec3 pos3 = pos;

    
    pos.xz *= rotmat(mat_spin_time * SPIN_SPEED);
    pos2.xz *= rotmat(mat_spin_time * SPIN_SPEED);
    pos3.xz *= rotmat(mat_spin_time * SPIN_SPEED);

    
    pos.y += mat_time * MOVE_SPEED;
    pos2.y += mat_time * MOVE_SPEED;
    pos3.y += mat_time * MOVE_SPEED;

    pos = mod(pos, b) - 0.5 * b;
    float distance_1 = sdBox(pos, vec3(5.5 * mat_thickness, 1.0, 3.5 * mat_thickness)); 

    pos2 = mod(pos2, b2) - 0.5 * b2;
    float distance_2 = sdBox(pos2, vec3(1.5, BEAM_WIDTH, BEAM_WIDTH)); 

    pos3 = mod(pos3, b2) - 0.5 * b2;
    float distance_3 = sdBox(pos3, vec3(BEAM_WIDTH, BEAM_WIDTH, 1.5)); 

    float distance_4 = opU(distance_2, distance_3); 

    float distance_5 = opS(distance_4, distance_1); 


    return distance_5;
}

float Bend( vec3 p ) 
{
    float c = cos( length(p) * 0.07 * mat_distort1) ;
    float s = sin( length(p) * 0.07 * mat_distort2);
    mat2  m = mat2(c,-s,s,c);
    vec3  q = vec3(m*p.xy,p.z) * mat_distort3;

    return sdBuilding(q);
}

vec2 sdScene(vec3 position) 
{

    vec3 translate = vec3(0.0, 0.0, 16.0) * mat_fov;

    vec3 pos = position - translate;

    float mat_id = 1.0;

    float distance_5 = Bend(pos);

    return vec2 (distance_5, mat_id);

}

vec2 raymarch(vec3 position, vec3 direction) 
{
    float depth = NEAR_CLIPPING_PLANE;

    for(int i = 0; i < MAX_MARCH_STEPS; i++)
    {
        vec2 result = sdScene(position + direction * depth);

        if(result.x < EPSILON)
        {
            return vec2(depth, result.y);
        }

        depth += result.x * DISTANCE_BIAS;

        if(depth > FAR_CLIPPING_PLANE)
            break;
    }
    return vec2(FAR_CLIPPING_PLANE, 0.0);
}


vec3 normal(vec3 ray_hit_position, float smoothness) 
{
    vec3 n;
    vec2 dn = vec2(smoothness, 0.0);
    float d = sdScene(ray_hit_position).x;
    n.x = sdScene(ray_hit_position + dn.xyy).x - d;
    n.y = sdScene(ray_hit_position + dn.yxy).x - d;
    n.z = sdScene(ray_hit_position + dn.yyx).x - d;
    return normalize(n);
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);


    vec3 camera = vec3(0.0, 0.0, 0.0);

    vec3 ray_direction = normalize(vec3(uv, 2.0));

    vec2 result = raymarch(camera, ray_direction);

    vec3 materialColor = vec3(0.0, 0.0, 0.0);

    if(result.x != FAR_CLIPPING_PLANE)
        materialColor = mat_front_color.rgb;


    float fog = pow(0.4 / (0.4 + result.x), 0.3);


    vec3 intersection = camera + ray_direction * result.x;
    vec3 nrml = normal(intersection, 0.001); 

    vec3 light_dir = normalize(vec3(0.1, 0.1, -1.0));

    float diffuse = dot(light_dir, nrml);

    diffuse = max(0.3, diffuse);

    vec3 light_color = vec3(1.6, 1.2, 0.7) * 2.55;
    vec3 ambient_color = vec3(0.2, 0.45, 0.5) * 1.6;

    vec3 diffuseLit = materialColor * (diffuse * light_color + ambient_color); 

    if(result.x == FAR_CLIPPING_PLANE)
    {
        out_color = mat_back_color;
    }
    else
    {
        if (mat_fog_alpha) {
             out_color = vec4(diffuseLit, 1.0) * fog;
        } else {
            out_color = vec4(diffuseLit * fog, 1.0);
        }

    }




    
    if (mat_invert) out_color.rgb=1-out_color.rgb;

    
    if (mat_hue_shift > 0.01 || mat_saturation != 0) {
        vec3 hsv = rgb2hsv(out_color.rgb);
        hsv.x = fract(0.9999999*(hsv.x+mat_hue_shift));
        hsv.y = max(hsv.y + mat_saturation, 0);
        out_color.rgb = hsv2rgb(hsv);
    }

    
    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
    const vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
    vec3 intensity = vec3(dot(out_color.rgb, LumCoeff));
    out_color.rgb = mix(AvgLumin, out_color.rgb, mat_contrast);

    
    out_color.rgb += mat_brightness;


    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
