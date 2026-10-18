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
uniform vec4 uMMParam007; // native input: mat_boundary
float mat_boundary = uMMParam007.x;
uniform vec4 uMMParam008; // native input: mat_line
float mat_line = uMMParam008.x;
uniform vec4 uMMParam009; // native input: mat_size
float mat_size = uMMParam009.x;
uniform vec4 uMMParam010; // native input: mat_gain
float mat_gain = uMMParam010.x;
uniform vec4 uMMParam011; // native input: mat_seed
float mat_seed = uMMParam011.x;
uniform vec4 uMMParam012; // native input: mat_p1_thick
float mat_p1_thick = uMMParam012.x;
uniform vec4 uMMParam013; // native input: mat_p1_variation
float mat_p1_variation = uMMParam013.x;
uniform vec4 uMMParam014; // native input: mat_p2_contrast
float mat_p2_contrast = uMMParam014.x;
uniform vec4 uMMParam015; // native input: mat_p2_backdrop
float mat_p2_backdrop = uMMParam015.x;
uniform vec4 uMMParam016; // native input: mat_p2_circles
float mat_p2_circles = uMMParam016.x;
uniform vec4 uMMParam017; // native input: mat_p2_variation
float mat_p2_variation = uMMParam017.x;
uniform vec4 uMMParam018; // native input: mat_speed
float mat_speed = uMMParam018.x;
uniform vec4 uMMParam019; // native input: mat_bpm_sync
bool mat_bpm_sync = uMMParam019.x > 0.5;
uniform vec4 uMMParam020; // native input: mat_reverse
bool mat_reverse = uMMParam020.x > 0.5;
uniform vec4 uMMParam021; // native input: mat_offset
float mat_offset = uMMParam021.x;
uniform vec4 uMMParam022; // native input: mat_offset_scale
float mat_offset_scale = uMMParam022.x;
uniform vec4 uMMParam023; // native input: mat_strob
float mat_strob = uMMParam023.x;
uniform vec4 uMMParam024; // native input: mat_restart
int mat_restart = int(round(uMMParam024.x));
uniform vec4 uMMParam025; // native input: mat_front_color
vec4 mat_front_color = uMMParam025;
uniform vec4 uMMParam026; // native input: mat_back_color
vec4 mat_back_color = uMMParam026;
uniform vec4 uMMParam027; // native input: mat_back_mode
int mat_back_mode = int(round(uMMParam027.x));
uniform vec4 uMMParam028; // native input: mat_back_thresh
float mat_back_thresh = uMMParam028.x;
uniform vec4 uMMParam029; // native input: mat_back_sensitivity
float mat_back_sensitivity = uMMParam029.x;
uniform vec4 uMMParam030; // native input: mat_lock_aspect
bool mat_lock_aspect = uMMParam030.x > 0.5;
float mat_time_source = uTDTime * (mat_speed);

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
** Code of this function is from TGM'MM_LIBRARY_s shader pack
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

vec2 matRot2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

float mat_luma(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

float mat_luma(vec4 color) {
  return dot(color.rgb, vec3(0.299, 0.587, 0.114));
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
    uv *= mat_scale;

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




#define t mat_time + 5.
#define screen(a, b) (a + b - a*b) * mat_gain
#define s(t, b, g) smoothstep(t+b*t, t-b*t, abs(g-mat_boundary) )


vec2 hash22(vec2 p)
{
    p *= 733.424;
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973) * mat_seed);
    p3 += dot(p3, p3.yzx+33.33);
    return fract((p3.xx+p3.yz)*p3.zy) * mat_p1_variation;
}

vec3 hash33(vec3 p3)
{
    p3 *= 733.424;
    p3 = fract(p3 * vec3(.1031, .1030, .0973) * mat_seed);
    p3 += dot(p3, p3.yxz+33.33);
    return fract((p3.xxy + p3.yxx)*p3.zyx) * mat_p2_variation;
}

float hash12(vec2 p)
{
    vec3 p3  = fract(vec3(p.xyx) * .1031 * mat_seed);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z) * mat_p1_variation;
}

float hash13(vec3 p3)
{
    p3  = fract(p3 * .1031 * mat_seed);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}


vec3 voronoi2d(vec2 p, float s) {
    vec2 gv = fract(p)-.5;
    vec2 iv = floor(p);
    vec2 id;

    vec2 o;
    float res = 8.;

    for(int y=-1; y<=1; y++)
    for(int x=-1; x<=1; x++)
    {
        o = vec2(x, y);

        vec2 n = hash22(iv+o);
        vec2 p = o+.5*sin(t*n);
        float d = dot(gv-p, gv-p)/s;

        if(hash12(n)>.5 ? d<1. : 1.<res) {
            res = d;
            id = iv+p;
        }
    }
    res = sqrt(res);
    return vec3(res, id*float(res<1.) );
}

vec4 voronoi3d(vec3 p, float s) {
    vec3 gv = fract(p)-.5;
    vec3 iv = floor(p);
    vec3 id;

    vec3 o;
    float res = 8.;

    for(int z=-1; z<=1; z++)
    for(int y=-1; y<=1; y++)
    for(int x=-1; x<=1; x++)
    {
        vec3 o = vec3(x, y, z);

        vec3 n = hash33(iv+o);
        vec3 p = o+.5*sin(t*n);
        float d = dot(gv-p, gv-p)/s;

        if(hash13(n)>.5 / mat_p2_circles ? d<1. : 1.<res) {
            res = d;
            id = iv+p;
        }
    }
    res = sqrt(res);
    return vec4(res, id*float(res<1.) );
}

float getCol(vec2 coord) {

    vec2 uv = coord - vec2(0.5);
    float x = coord.x;
    uv *= 8.;

    float size = 1. * mat_size;

    float v;

    if(x<mat_boundary) {

        v = voronoi2d(uv, size).x;
        v = step(.9 / mat_p1_thick, v)*float(v<1.);
    } else {
        v = voronoi3d(vec3(uv, 0), size).w*.5*mat_p2_contrast+.5 ;
    }


    return screen(v, s(.0025, .2, x ) * mat_line );
}


vec4 materialColorForPixel(vec2 texCoord)
{
    vec4 out_color; 
    vec2 uv = texCoord - vec2(0.5);

    uv = transformUV(uv);

    uv += vec2(0.5);


    float v;

    #ifdef AA
        
        const float S = .125;
        const float L = .375;
        v  = getCol(uv + vec2( S,-L) );
        v += getCol(uv + vec2( L, S) );
        v += getCol(uv + vec2(-S,-L) );
        v += getCol(uv + vec2(-L,-S) );
        v *= .25;

    #else
       v = getCol(uv);

    #endif
        out_color = vec4(v);



    
    if (mat_back_mode == 1) {
        
        if (mat_luma(out_color.rgb) < mat_back_thresh) {
            out_color = mat_back_color;
        } else {
            out_color = mat_front_color;
        }
    } else {
        
        out_color = mix(mat_back_color, mat_front_color, mat_luma(out_color.rgb) * mat_back_sensitivity + mat_back_thresh);
    }

    return out_color;
}


void main()
{

    fragColor = TDOutputSwizzle(materialColorForPixel(mapMadMapperUV(vUV.st)));
}
